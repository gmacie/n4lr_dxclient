# dxcc_challenge.py - 2025-12-30
# DXCC Challenge tracker and needed spot checker
"""
Loads challenge_data.json (created by lotw_challenge.py) and checks if spots are needed.
Works with DXCC entity numbers.
"""

import json
from pathlib import Path
from typing import Set, Tuple, Dict

# Path to saved challenge data
CHALLENGE_JSON = Path("challenge_data.json")

# Global challenge data
_worked_band_entity: Set[Tuple[str, int]] = set()  # (band, dxcc_num)
_is_initialized = False


def load_challenge_from_json():
    """Load challenge data from challenge_data.json"""
    global _worked_band_entity, _is_initialized
    
    if not CHALLENGE_JSON.exists():
        print("No saved challenge data found")
        return False
    
    print("Loading saved challenge data...")
    
    try:
        data = json.loads(CHALLENGE_JSON.read_text())
        
        # Extract worked band/entity pairs
        # Format: list of [band, entity] pairs
        raw_pairs = data.get("raw_band_entity_pairs", [])
        
        # Convert to set of tuples (band, dxcc_num)
        _worked_band_entity = set()
        for pair in raw_pairs:
            if len(pair) == 2:
                band, entity = pair
                _worked_band_entity.add((band, int(entity)))
        
        _is_initialized = True
        print(f"Loaded {len(_worked_band_entity)} band/entity slots from saved data")
        return True
        
    except Exception as e:
        print(f"Error loading challenge data: {e}")
        return False


def is_needed(dxcc_num_str: str, band: str) -> bool:
    """
    Check if a spot is needed for the challenge.
    
    Args:
        dxcc_num_str: DXCC entity number as string (e.g., "1" for Canada, "291" for USA)
        band: Band as string (e.g., "20M", "15M", "10M")
    
    Returns:
        True if this band/entity combination is needed (not yet worked)
    """
    if not _is_initialized or not _worked_band_entity:
        return False  # No challenge data loaded
    
    try:
        dxcc_num = int(dxcc_num_str)
    except (ValueError, TypeError):
        return False  # Invalid DXCC number
    
    # Normalize band (uppercase, add M if missing)
    band_norm = band.upper()
    if not band_norm.endswith('M'):
        band_norm += 'M'
    
    # Check if we've worked this combination
    is_worked = (band_norm, dxcc_num) in _worked_band_entity
    
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