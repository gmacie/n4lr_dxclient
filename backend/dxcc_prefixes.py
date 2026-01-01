# dxcc_prefixes.py - Map DXCC numbers to common prefixes
"""
Extracts DXCC entity prefixes directly from CTY.DAT.
Creates a mapping of DXCC number -> primary prefix (e.g., 1 -> VE, 6 -> K)
"""

from pathlib import Path
import json
import re

# Manual overrides for entities that don't match between LoTW and CTY.DAT
MANUAL_OVERRIDES = {
    "10": "PA",      # Amsterdam & Saint Paul Islands
    "20": "BS7",     # Scarborough Reef
    "23": "KH1",     # Baker & Howland Islands
    "24": "KG4",     # Guantanamo Bay
    "26": "Z6",      # Kosovo
    "28": "KZ5",     # Canal Zone (deleted)
    "32": "EA9",     # Ceuta & Melilla
    "34": "VQ9",     # Chagos Islands
    "35": "ZL7",     # Chatham Islands
    "36": "VK9X",    # Christmas Island
    "37": "FO",      # Clipperton Island
    "38": "VK9C",    # Cocos (Keeling) Islands
    "40": "CU",      # Azores
    "41": "XX9",     # Ducie Island
    "42": "FP",      # Saint Pierre & Miquelon
    "43": "P5",      # DPR of Korea
    "44": "T31",     # Central Kiribati (Canton & Enderbury)
    "45": "VK9N",    # Norfolk Island
    "46": "JD/o",    # Ogasawara
    "47": "VK9M",    # Mellish Reef
    "48": "ZK3",     # Tokelau Islands
    "49": "VK9W",    # Willis Island
    "50": "ZL9",     # Auckland & Campbell Islands
    "51": "VK",      # Heard Island
    "52": "VP8/s",   # South Sandwich Islands
    "53": "VK0H",    # Macquarie Island
    "54": "VP8",     # Falkland Islands
    "55": "XR0",     # San Felix & San Ambrosio
    "56": "CE9",     # Juan Fernandez Islands
    "57": "3Y",      # Peter 1 Island
    "58": "3Y",      # Bouvet
    "59": "TI9",     # Cocos Island
    "60": "FO",      # Marquesas Islands
    "61": "ZK1",     # South Cook Islands
    "62": "ZK1",     # North Cook Islands
    "63": "FO",      # Austral Islands
    "64": "VP6",     # Pitcairn Island
    "65": "FO",      # Tuamotu Archipelago
    "66": "T33",     # Banaba Island (Ocean Island)
    "67": "H40",     # Temotu Province
    "68": "VK9L",    # Lord Howe Island
    "69": "T2",      # Tuvalu
    "70": "VK4",     # Mellish Reef
    "131": "FT5Z",   # Kerguelen Islands
    "133": "FT5X",   # Kermadec Island
    "134": "KH5K",   # Kingman Reef
    "136": "VK9",    # Cocos (Keeling) Islands
    "137": "SV/a",   # Mount Athos
    "138": "KH7K",   # Kure Island
    "139": "JD/m",   # Minami Torishima
    "151": "4K2",    # Malyj Vysotskij Island
    "201": "VY0",    # Prince Edward & Marion Islands
    "85": "PJ",      # Bonaire, Curacao (Neth Antilles)
    "97": "J6",      # Saint Lucia
    "98": "J8",      # Saint Vincent
    "99": "FR",      # Glorioso Island
    "213": "FS",     # Saint Martin
    "218": "OK",     # Czechoslovakia (deleted)
    "226": "HZ",     # Saudi Arabia/Iraq Neutral Zone (deleted)
    "229": "Y2",     # German Democratic Republic (deleted)
    "230": "DL",     # Federal Republic of Germany
    "246": "1A",     # Sovereign Military Order of Malta
    "250": "ZD7",    # Saint Helena
    "255": "PJ",     # Sint Maarten, Saba, Saint Eustatius
    "293": "3W",     # Viet Nam
    "516": "FJ",     # Saint Barthelemy
}



def parse_cty_dat():
    """Parse CTY.DAT and extract all DXCC entities with their prefixes"""
    
    cty_file = Path("cty.dat")
    if not cty_file.exists():
        print("ERROR: cty.dat not found")
        return {}
    
    text = cty_file.read_text(encoding='utf-8', errors='ignore')
    
    # Parse each country - look for header lines with 8+ colons
    # Format: Country Name: CQ: ITU: Continent: Lat: Lon: GMT: DXCC_PREFIX:
    
    entities = {}  # dxcc_prefix -> country_name
    
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        
        # Check if this is a header line (has 8+ colons and ends with colon)
        if line.count(':') >= 8 and line.endswith(':'):
            # Parse this header
            parts = line.split(':')
            if len(parts) >= 8:
                country_name = parts[0].strip()
                dxcc_prefix = parts[7].strip()
                
                # Special handling for deleted entities (marked with * or =)
                if dxcc_prefix.startswith('*') or dxcc_prefix.startswith('='):
                    dxcc_prefix = dxcc_prefix[1:]
                
                if country_name and dxcc_prefix:
                    entities[dxcc_prefix] = country_name
    
    return entities


def build_dxcc_number_to_prefix_mapping():
    """Build DXCC number -> prefix mapping using both CTY.DAT and dxcc_mapping.json"""
    
    # Get all entities from CTY.DAT
    cty_entities = parse_cty_dat()
    print(f"Parsed {len(cty_entities)} entities from CTY.DAT")
    
    # Load dxcc_mapping.json (DXCC number -> country name from LoTW)
    mapping_file = Path("dxcc_mapping.json")
    if not mapping_file.exists():
        print("ERROR: dxcc_mapping.json not found")
        return {}
    
    lotw_mapping = json.loads(mapping_file.read_text())
    print(f"Loaded {len(lotw_mapping)} entities from dxcc_mapping.json")
    
    # Create reverse lookup: normalize country names for matching
    def normalize(name):
        """Normalize country name for matching"""
        # Uppercase, remove extra spaces, remove common words
        n = name.upper().strip()
        n = re.sub(r'\s+', ' ', n)  # Collapse multiple spaces
        # Remove parenthetical info
        n = re.sub(r'\([^)]*\)', '', n).strip()
        return n
    
    # Build lookup from normalized CTY names to prefixes
    cty_normalized = {}
    for prefix, country in cty_entities.items():
        norm = normalize(country)
        cty_normalized[norm] = prefix
    
    # Now match LoTW DXCC numbers to CTY prefixes
    dxcc_to_prefix = {}
    unmatched = []
    
    for dxcc_num, lotw_country in lotw_mapping.items():
        # Check manual overrides first
        if dxcc_num in MANUAL_OVERRIDES:
            dxcc_to_prefix[dxcc_num] = MANUAL_OVERRIDES[dxcc_num]
            continue
        
        lotw_norm = normalize(lotw_country)
        
        # Try exact match first
        if lotw_norm in cty_normalized:
            dxcc_to_prefix[dxcc_num] = cty_normalized[lotw_norm]
            continue
        
        # Try partial match
        matched = False
        for cty_norm, prefix in cty_normalized.items():
            # Check significant word overlap
            lotw_words = set(lotw_norm.split())
            cty_words = set(cty_norm.split())
            
            # Skip very short words
            lotw_words = {w for w in lotw_words if len(w) > 2}
            cty_words = {w for w in cty_words if len(w) > 2}
            
            if not lotw_words or not cty_words:
                continue
            
            # If 60% or more words match, it's a match
            overlap = lotw_words & cty_words
            if len(overlap) >= max(1, min(len(lotw_words), len(cty_words)) * 0.6):
                dxcc_to_prefix[dxcc_num] = prefix
                matched = True
                break
        
        if not matched:
            unmatched.append(f"{dxcc_num}: {lotw_country}")
    
    print(f"\nMatched {len(dxcc_to_prefix)} out of {len(lotw_mapping)} entities")
    print(f"  - {len([d for d in dxcc_to_prefix if d in MANUAL_OVERRIDES])} from manual overrides")
    print(f"  - {len([d for d in dxcc_to_prefix if d not in MANUAL_OVERRIDES])} from automatic matching")
    
    if unmatched:
        print(f"\nUnmatched entities ({len(unmatched)}):")
        for item in unmatched[:10]:  # Show first 10
            print(f"  {item}")
        if len(unmatched) > 10:
            print(f"  ... and {len(unmatched) - 10} more")
    
    return dxcc_to_prefix


def get_prefix(dxcc_num):
    """Get prefix for a DXCC number (uses cached mapping)"""
    if not hasattr(get_prefix, '_cache'):
        # Load from file if it exists, otherwise build it
        cache_file = Path("dxcc_prefixes.json")
        if cache_file.exists():
            try:
                get_prefix._cache = json.loads(cache_file.read_text())
            except:
                get_prefix._cache = build_dxcc_number_to_prefix_mapping()
        else:
            get_prefix._cache = build_dxcc_number_to_prefix_mapping()
    
    return get_prefix._cache.get(str(dxcc_num), str(dxcc_num))


def save_mapping(filename="dxcc_prefixes.json"):
    """Save the mapping to a JSON file for faster loading"""
    mapping = build_dxcc_number_to_prefix_mapping()
    Path(filename).write_text(json.dumps(mapping, indent=2, sort_keys=True))
    print(f"\nSaved {len(mapping)} DXCC -> prefix mappings to {filename}")
    return mapping


if __name__ == "__main__":
    # Test and save
    print("Building DXCC prefix mapping from CTY.DAT...\n")
    mapping = save_mapping()
    
    # Show some examples
    print("\nExamples:")
    test_dxccs = ["1", "6", "100", "248", "291", "110"]
    for dxcc in test_dxccs:
        prefix = mapping.get(dxcc, "???")
        country = ""
        try:
            lotw_map = json.loads(Path("dxcc_mapping.json").read_text())
            country = lotw_map.get(dxcc, "")
        except:
            pass
        print(f"  DXCC {dxcc:>3}: {prefix:6} ({country})")