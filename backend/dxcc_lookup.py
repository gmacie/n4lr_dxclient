# dxcc_lookup.py - Complete DXCC entity lookup from callsign prefixes
"""
Maps VE7CC cluster prefixes to DXCC entity numbers using CTY.DAT.
"""

import json
from pathlib import Path
from typing import Optional, Dict

CTY_FILE = Path("cty.dat")
DXCC_MAPPING_FILE = Path("dxcc_mapping.json")

# Global lookup tables
_prefix_to_country: Dict[str, str] = {}  # VE7CC prefix -> CTY country name
_country_to_dxcc: Dict[str, str] = {}    # CTY country -> DXCC entity number

# Manual overrides for country name differences between CTY.DAT and LoTW
CTY_TO_LOTW_OVERRIDES = {
    "United States": "UNITED STATES OF AMERICA",
    "Hawaii": "HAWAIIAN ISLANDS",
    "Alaska": "ALASKA", 
    "Sicily": "ITALY",
    "Sardinia": "ITALY",
    "England": "ENGLAND",
    "Scotland": "SCOTLAND",
    "Wales": "WALES",
    "Northern Ireland": "NORTHERN IRELAND",
    "Guantanamo Bay": "GUANTANAMO BAY",
    "Puerto Rico": "PUERTO RICO",
    "Virgin Islands": "VIRGIN ISLANDS",
    "US Virgin Islands": "VIRGIN ISLANDS",
    "European Russia": "EUROPEAN RUSSIA",
    "Asiatic Russia": "ASIATIC RUSSIA",
    "Kaliningrad": "KALININGRAD",
    # Add more as discovered
}


def load_cty_dat():
    """Parse CTY.DAT and build prefix -> country mapping"""
    global _prefix_to_country
    
    if not CTY_FILE.exists():
        print(f"ERROR: {CTY_FILE} not found!")
        print("Please download CTY.DAT from https://www.country-files.com/cty/cty.dat")
        return False
    
    print(f"Loading {CTY_FILE}...")
    content = CTY_FILE.read_text(encoding='utf-8', errors='ignore')
    lines = content.split('\n')
    
    current_country = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Main entity line (ends with colon, has 8 colon-separated parts)
        if line.count(':') >= 7 and line.endswith(':'):
            parts = line.split(':')
            current_country = parts[0].strip()
        
        # Prefix line (indented, contains prefixes)
        elif current_country:
            prefix_text = line.rstrip(';')
            prefixes = [p.strip() for p in prefix_text.split(',') if p.strip()]
            
            for prefix in prefixes:
                # Clean up special notations
                if prefix.startswith('='):
                    clean = prefix[1:]  # Exact callsign
                elif prefix.startswith('['):
                    clean = prefix.strip('[]')  # Bracket notation
                elif '(' in prefix:
                    clean = prefix.split('(')[0]  # Zone override
                else:
                    clean = prefix
                
                _prefix_to_country[clean.upper()] = current_country
    
    print(f"Loaded {len(_prefix_to_country)} prefix mappings")
    return True


def load_dxcc_mapping():
    """Load DXCC number -> country name mapping from LoTW data"""
    global _country_to_dxcc
    
    if not DXCC_MAPPING_FILE.exists():
        print(f"ERROR: {DXCC_MAPPING_FILE} not found!")
        print("Please load challenge data first to generate DXCC mapping")
        return False
    
    print(f"Loading {DXCC_MAPPING_FILE}...")
    dxcc_to_lotw = json.loads(DXCC_MAPPING_FILE.read_text())
    
    # Create reverse mapping: LoTW country name -> DXCC number
    lotw_to_dxcc = {v: k for k, v in dxcc_to_lotw.items()}
    
    # Build CTY country -> DXCC number mapping (with overrides)
    for cty_country in set(_prefix_to_country.values()):
        # Check if we have an override
        lotw_country = CTY_TO_LOTW_OVERRIDES.get(cty_country, cty_country.upper())
        
        # Look up DXCC number
        dxcc_num = lotw_to_dxcc.get(lotw_country)
        if dxcc_num:
            _country_to_dxcc[cty_country] = dxcc_num
    
    print(f"Mapped {len(_country_to_dxcc)} countries to DXCC numbers")
    return True


def initialize():
    """Load all lookup data"""
    if not load_cty_dat():
        return False
    if not load_dxcc_mapping():
        return False
    print("DXCC lookup initialized successfully")
    return True


def lookup_dxcc_from_prefix(prefix: str) -> Optional[str]:
    """
    Look up DXCC entity number from VE7CC prefix.
    
    Args:
        prefix: VE7CC prefix (e.g., "IT9", "LA", "PA", "K")
    
    Returns:
        DXCC entity number as string (e.g., "248", "266", "291") or None
    """
    if not _prefix_to_country or not _country_to_dxcc:
        print("WARNING: DXCC lookup not initialized")
        return None
    
    prefix = prefix.upper().strip()
    
    # Look up country name from prefix
    country = _prefix_to_country.get(prefix)
    if not country:
        # Try progressively shorter prefixes (e.g., "IT9" -> "IT")
        for length in range(len(prefix) - 1, 0, -1):
            short_prefix = prefix[:length]
            country = _prefix_to_country.get(short_prefix)
            if country:
                break
    
    if not country:
        return None
    
    # Look up DXCC number from country
    return _country_to_dxcc.get(country)


def get_country_from_prefix(prefix: str) -> Optional[str]:
    """Get country name from prefix"""
    return _prefix_to_country.get(prefix.upper())


def is_loaded() -> bool:
    """Check if lookup data is loaded"""
    return len(_prefix_to_country) > 0 and len(_country_to_dxcc) > 0


# Test function
if __name__ == "__main__":
    if initialize():
        test_prefixes = ["IT9", "LA", "PA", "K", "VE", "JA", "G", "W"]
        print("\nTest lookups:")
        for pfx in test_prefixes:
            country = get_country_from_prefix(pfx)
            dxcc = lookup_dxcc_from_prefix(pfx)
            print(f"  {pfx:10} -> {country if country else 'Unknown':20} -> DXCC {dxcc if dxcc else 'NOT FOUND'}")
