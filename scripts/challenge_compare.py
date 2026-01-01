"""
challenge_compare.py - 2025-12-30
Challenge Data Comparison Report

Purpose:
  Compares challenge_data.json with LoTW expected values to find discrepancies
  Identifies paper QSLs, Maritime Mobile QSOs, and other differences

Usage:
  python scripts/challenge_compare.py

Output:
  - Band-by-band comparison with LoTW online
  - Invalid entities (DXCC 0, Maritime Mobile, etc.)
  - Single-slot entities (possible paper QSLs)
  - Summary explaining differences

Author: N4LR
Last modified: 2025-12-30
"""

import json
from pathlib import Path
from backend.dxcc_prefixes import get_prefix

def load_challenge_data():
    """Load challenge data from JSON"""
    challenge_file = Path("challenge_data.json")
    if not challenge_file.exists():
        print("ERROR: challenge_data.json not found")
        return None
    
    try:
        return json.loads(challenge_file.read_text())
    except Exception as e:
        print(f"Error loading challenge data: {e}")
        return None

def load_dxcc_mapping():
    """Load DXCC number -> country name mapping"""
    mapping_file = Path("dxcc_mapping.json")
    if mapping_file.exists():
        try:
            return json.loads(mapping_file.read_text())
        except:
            pass
    return {}

def generate_report():
    """Generate comparison report"""
    
    data = load_challenge_data()
    if not data:
        return
    
    dxcc_mapping = load_dxcc_mapping()
    
    print("=" * 80)
    print("CHALLENGE DATA COMPARISON REPORT")
    print("=" * 80)
    print()
    
    # Overall stats
    print(f"Total Entities: {data['total_entities']}")
    print(f"Total Slots: {data['total_challenge_slots']}")
    print()
    
    # Expected LoTW totals (from your screenshot)
    lotw_totals = {
        "160M": 120,
        "80M": 228,
        "60M": 0,  # LoTW doesn't count 60m
        "40M": 290,
        "30M": 284,
        "20M": 318,
        "17M": 302,
        "15M": 311,
        "12M": 288,
        "10M": 293,
        "6M": 109,
    }
    
    lotw_total = sum(lotw_totals.values())
    
    print("BAND COMPARISON (vs LoTW online):")
    print("-" * 80)
    print(f"{'Band':<10} {'Your Data':<12} {'LoTW Online':<15} {'Difference':<12}")
    print("-" * 80)
    
    your_totals = data.get("entities_by_band", {})
    
    for band in ["160M", "80M", "60M", "40M", "30M", "20M", "17M", "15M", "12M", "10M", "6M"]:
        your_count = your_totals.get(band, 0)
        lotw_count = lotw_totals.get(band, 0)
        diff = your_count - lotw_count
        
        status = ""
        if band == "60M":
            status = " (LoTW doesn't count 60m)"
        elif diff > 0:
            status = f" (+{diff})"
        elif diff < 0:
            status = f" ({diff})"
        
        print(f"{band:<10} {your_count:<12} {lotw_count:<15} {diff:<12} {status}")
    
    print("-" * 80)
    your_total_no_60m = sum(your_totals.get(b, 0) for b in ["160M", "80M", "40M", "30M", "20M", "17M", "15M", "12M", "10M", "6M"])
    print(f"{'TOTAL':<10} {your_total_no_60m:<12} {lotw_total:<15} {your_total_no_60m - lotw_total:<12}")
    print()
    
    # List entities with DXCC 0 or invalid
    print("\nINVALID ENTITIES (should be filtered):")
    print("-" * 80)
    
    invalid_found = False
    for band_entity_pair in data.get("raw_band_entity_pairs", []):
        if len(band_entity_pair) != 2:
            continue
        band, entity = band_entity_pair
        
        if entity <= 0 or entity > 999:
            country = dxcc_mapping.get(str(entity), f"Entity {entity}")
            prefix = get_prefix(entity)
            print(f"  {prefix:<8} {entity:<6} {band:<8} {country}")
            invalid_found = True
    
    if not invalid_found:
        print("  None found ✓")
    
    print()
    
    # Find entities with unusual slot counts (might indicate issues)
    print("\nENTITIES WITH 1 SLOT (might be paper QSLs or errors):")
    print("-" * 80)
    
    entity_counts = {}
    for band_entity_pair in data.get("raw_band_entity_pairs", []):
        if len(band_entity_pair) != 2:
            continue
        band, entity = band_entity_pair
        
        if entity not in entity_counts:
            entity_counts[entity] = []
        entity_counts[entity].append(band)
    
    single_slot_entities = [(e, bands) for e, bands in entity_counts.items() if len(bands) == 1]
    single_slot_entities.sort(key=lambda x: get_prefix(x[0]))
    
    if single_slot_entities:
        print(f"Found {len(single_slot_entities)} entities with only 1 band confirmed:")
        for entity, bands in single_slot_entities[:20]:  # Show first 20
            country = dxcc_mapping.get(str(entity), f"Entity {entity}")
            prefix = get_prefix(entity)
            print(f"  {prefix:<8} {entity:<6} {bands[0]:<8} {country[:40]}")
        
        if len(single_slot_entities) > 20:
            print(f"  ... and {len(single_slot_entities) - 20} more")
    else:
        print("  None found")
    
    print()
    print("=" * 80)
    print("SUMMARY:")
    print("-" * 80)
    print(f"Your total slots (excluding 60m): {your_total_no_60m}")
    print(f"LoTW online total: {lotw_total}")
    print(f"Difference: {your_total_no_60m - lotw_total}")
    print()
    print("Possible reasons for differences:")
    print("  • Paper QSL cards (ARRL desk-checked, not in LoTW)")
    print("  • LoTW updates since last sync")
    print("  • Deleted entities in old data")
    print("  • QSLs rejected by LoTW but accepted by ARRL")
    print("=" * 80)


if __name__ == "__main__":
    generate_report()
