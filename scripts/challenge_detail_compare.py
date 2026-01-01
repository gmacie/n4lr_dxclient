"""
challenge_detail_compare.py - 2025-12-30
Detailed Band-by-Band Entity Comparison

Purpose:
  Shows exactly which entities differ between your data and LoTW online
  Identifies which specific entities account for slot differences
  
Usage:
  python scripts/challenge_detail_compare.py

Output:
  - Entity-by-entity breakdown for each band
  - Shows entities you have that LoTW doesn't show (pending credits)
  - Shows entities LoTW shows that you don't have (paper QSLs)

Author: N4LR
Last modified: 2025-12-30
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from backend.dxcc_prefixes import get_prefix

def load_challenge_data():
    """Load challenge data from JSON"""
    challenge_file = Path("challenge_data.json")
    if not challenge_file.exists():
        print("ERROR: challenge_data.json not found")
        print("Run: python backend\\lotw_challenge.py first")
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

def get_your_entities_by_band(data, use_credited=False):
    """Extract which entities you have on each band"""
    entities_by_band = {}
    
    # Choose which dataset to use
    if use_credited:
        pairs_key = "credited_band_entity_pairs"
    else:
        pairs_key = "raw_band_entity_pairs"
    
    for band_entity_pair in data.get(pairs_key, []):
        if len(band_entity_pair) != 2:
            continue
        band, entity = band_entity_pair
        
        if band not in entities_by_band:
            entities_by_band[band] = set()
        entities_by_band[band].add(entity)
    
    return entities_by_band

def generate_detailed_report():
    """Generate detailed band-by-band comparison"""
    
    data = load_challenge_data()
    if not data:
        return
    
    dxcc_mapping = load_dxcc_mapping()
    
    # Get both confirmed and credited entities
    confirmed_entities = get_your_entities_by_band(data, use_credited=False)
    credited_entities = get_your_entities_by_band(data, use_credited=True)
    
    # LoTW online shows CREDITED totals
    lotw_totals = {
        "160M": 120,
        "80M": 228,
        "40M": 290,
        "30M": 284,
        "20M": 318,
        "17M": 302,
        "15M": 311,
        "12M": 288,
        "10M": 293,
        "6M": 109,
    }
    
    print("=" * 100)
    print("DETAILED BAND-BY-BAND ENTITY COMPARISON")
    print("=" * 100)
    print()
    print("NOTE: LoTW online shows CREDITED entities (CREDIT_GRANTED)")
    print("      Your data shows CONFIRMED entities (QSL_RCVD=Y)")
    print()
    
    for band in ["160M", "80M", "40M", "30M", "20M", "17M", "15M", "12M", "10M", "6M"]:
        confirmed_set = confirmed_entities.get(band, set())
        credited_set = credited_entities.get(band, set())
        
        confirmed_count = len(confirmed_set)
        credited_count = len(credited_set)
        lotw_count = lotw_totals.get(band, 0)
        
        # Entities confirmed but NOT credited (pending)
        pending_entities = confirmed_set - credited_set
        
        # Skip if no differences
        if confirmed_count == credited_count == lotw_count:
            continue
        
        print(f"\n{'='*100}")
        print(f"BAND: {band}")
        print(f"Confirmed (QSL_RCVD): {confirmed_count}  |  Credited (CREDIT_GRANTED): {credited_count}  |  LoTW Online: {lotw_count}")
        print('='*100)
        
        # Show pending entities (confirmed but not credited)
        if pending_entities:
            print(f"\n⏳ PENDING CREDITS ({len(pending_entities)} entities):")
            print("   Confirmed in LoTW but ARRL has not granted credit yet")
            print("-" * 100)
            print(f"{'Prefix':<10} {'DXCC':<8} {'Country':<50}")
            print("-" * 100)
            
            entities_list = sorted(pending_entities, key=lambda e: get_prefix(e))
            for entity in entities_list:
                prefix = get_prefix(entity)
                country = dxcc_mapping.get(str(entity), f"Entity {entity}")
                print(f"{prefix:<10} {entity:<8} {country[:50]:<50}")
        
        # Show credited vs LoTW difference (paper QSLs)
        credited_vs_lotw = credited_count - lotw_count
        if credited_vs_lotw != 0:
            print(f"\n📄 CREDITED vs LoTW ONLINE: {credited_vs_lotw:+d}")
            if credited_vs_lotw < 0:
                print(f"   LoTW shows {abs(credited_vs_lotw)} MORE than your credited data")
                print("   Likely paper QSL cards (ARRL desk-checked, not in LoTW)")
            else:
                print(f"   You have {credited_vs_lotw} MORE credited than LoTW shows")
                print("   Possible sync issue - refresh LoTW online")
    
    print()
    print("=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print()
    
    total_pending = sum(len(confirmed_entities.get(b, set()) - credited_entities.get(b, set())) 
                       for b in ["160M", "80M", "40M", "30M", "20M", "17M", "15M", "12M", "10M", "6M"])
    
    print(f"Total PENDING credits (confirmed but not granted): {total_pending}")
    print()
    
    print("Bands with PENDING entities:")
    for band in ["160M", "80M", "40M", "30M", "20M", "17M", "15M", "12M", "10M", "6M"]:
        pending = len(confirmed_entities.get(band, set()) - credited_entities.get(band, set()))
        if pending > 0:
            print(f"  {band}: {pending} pending")
    
    print()
    print("=" * 100)


if __name__ == "__main__":
    generate_detailed_report()