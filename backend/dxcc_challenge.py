# dxcc_challenge.py - DXCC Challenge tracker and needed spot checker
"""
Loads LoTW DXCC challenge data and checks if spots are needed.
Works with DXCC entity numbers from LoTW ADIF files.
"""

import json
import re
from pathlib import Path
from typing import Set, Tuple, Dict, Optional
from backend.lotw_challenge_adif import parse_adif_file, save_summary, load_summary
from backend.dxcc_lookup import initialize as init_dxcc_lookup, lookup_dxcc_from_prefix

# Path to saved challenge data
CHALLENGE_JSON = Path("challenge_data.json")
DXCC_MAPPING_JSON = Path("dxcc_mapping.json")

# Global challenge data
_worked_band_entity: Set[Tuple[str, str]] = set()  # (band, dxcc_num)
_is_initialized = False


def load_challenge_from_adif(adif_path: Path) -> Dict:
    """
    Load challenge data from LoTW ADIF file.
    Returns summary dict with stats.
    """
    global _worked_band_entity, _is_initialized
    
    print(f"Loading challenge data from {adif_path}...")
    
    # Parse ADIF file
    summary = parse_adif_file(adif_path)
    
    # Extract worked band/entity pairs
    # summary.raw_band_entity_pairs is set of (band, dxcc_num) tuples
    _worked_band_entity = summary.raw_band_entity_pairs
    
    # Also extract DXCC mapping
    dxcc_to_country = extract_dxcc_mapping(adif_path)
    
    # Save for later
    save_summary(summary, CHALLENGE_JSON)
    save_dxcc_mapping(dxcc_to_country, DXCC_MAPPING_JSON)
    
    # Initialize DXCC lookup
    init_dxcc_lookup()
    _is_initialized = True
    
    print(f"Loaded {len(_worked_band_entity)} band/entity slots")
    print(f"Total entities: {summary.total_entities}")
    
    return {
        'total_entities': summary.total_entities,
        'total_slots': summary.total_challenge_slots,
        'bands': summary.entities_by_band,
    }


def extract_dxcc_mapping(adif_path: Path) -> Dict[str, str]:
    """Extract DXCC number -> country name mapping from ADIF file"""
    text = adif_path.read_text(encoding="utf-8", errors="ignore").lower()
    records = text.split("<eor>")
    
    dxcc_to_country = {}
    
    for record in records:
        # Extract DXCC number
        dxcc_match = re.search(r'<dxcc:(\d+):?[^>]*>(\d+)', record)
        country_match = re.search(r'<country:(\d+):?[^>]*>([^<]+)', record)
        
        if dxcc_match and country_match:
            dxcc_num = dxcc_match.group(2)
            country_name = country_match.group(2).strip().upper()
            if dxcc_num not in dxcc_to_country:
                dxcc_to_country[dxcc_num] = country_name
    
    return dxcc_to_country


def save_dxcc_mapping(mapping: Dict[str, str], path: Path):
    """Save DXCC mapping to JSON"""
    path.write_text(json.dumps(mapping, indent=2))


def load_challenge_from_json():
    """Load previously saved challenge data from JSON"""
    global _worked_band_entity, _is_initialized
    
    if not CHALLENGE_JSON.exists():
        print("No saved challenge data found")
        return False
    
    print("Loading saved challenge data...")
    summary = load_summary(CHALLENGE_JSON)
    _worked_band_entity = summary.raw_band_entity_pairs
    
    # Initialize DXCC lookup
    if init_dxcc_lookup():
        _is_initialized = True
    
    print(f"Loaded {len(_worked_band_entity)} band/entity slots from saved data")
    return True


def is_needed(dxcc_prefix: str, band: str) -> bool:
    """
    Check if a spot is needed for the challenge.
    
    Args:
        dxcc_prefix: VE7CC DXCC prefix (e.g., "IT9", "LA", "PA", "K")
        band: Band as string (e.g., "20m", "15m", "10m")
    
    Returns:
        True if this band/entity combination is needed
    """
    if not _is_initialized or not _worked_band_entity:
        return False  # No challenge data loaded
    
    # Look up DXCC entity number from prefix
    dxcc_num = lookup_dxcc_from_prefix(dxcc_prefix)
    if not dxcc_num:
        return False  # Unknown entity
    
    # Normalize band (uppercase, add M if missing)
    band_norm = band.upper()
    if not band_norm.endswith('M'):
        band_norm += 'M'
    
    # Check if we've worked this combination
    is_worked = (band_norm, str(dxcc_num)) in _worked_band_entity
    
    return not is_worked  # Return True if NOT worked (i.e., needed)


def get_stats() -> Dict:
    """Get challenge statistics"""
    if not _worked_band_entity:
        return {'loaded': False}
    
    # Count entities by band
    bands = {}
    entities = set()
    
    for band, entity in _worked_band_entity:
        entities.add(entity)
        if band not in bands:
            bands[band] = set()
        bands[band].add(entity)
    
    return {
        'loaded': True,
        'total_entities': len(entities),
        'total_slots': len(_worked_band_entity),
        'bands': {b: len(e) for b, e in bands.items()},
    }


# Load on module import if data exists
if CHALLENGE_JSON.exists():
    try:
        load_challenge_from_json()
    except Exception as e:
        print(f"Error loading challenge data: {e}")
