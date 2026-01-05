# compare_ffma.py - 2026-01-02
# Compare LoTW FFMA list with parsed ffma_data.json to find missing grids

import json
from pathlib import Path

def parse_lotw_list(text):
    """Parse the LoTW FFMA list and extract grids with callsigns"""
    grids_with_calls = {}
    
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        
        # Split by tabs or spaces
        parts = line.split()
        if len(parts) >= 2:
            grid = parts[0].strip()
            call = parts[1].strip()
            
            # Valid grid format: 2 letters + 2 numbers
            if len(grid) == 4 and grid[:2].isalpha() and grid[2:].isdigit():
                if call and call != '':  # Has a callsign
                    grids_with_calls[grid] = call
    
    return grids_with_calls

def main():
    # Load the LoTW list
    lotw_file = Path("lotw_ffma_list.txt")
    if not lotw_file.exists():
        print("ERROR: lotw_ffma_list.txt not found")
        print("Create this file with the LoTW FFMA grid list (grid + callsign per line)")
        return
    
    lotw_text = lotw_file.read_text()
    lotw_grids = parse_lotw_list(lotw_text)
    
    # Load ffma_data.json
    ffma_file = Path("ffma_data.json")
    if not ffma_file.exists():
        print("ERROR: ffma_data.json not found")
        return
    
    ffma_data = json.loads(ffma_file.read_text())
    parsed_grids = set(ffma_data.get("worked_grids", {}).keys())
    
    # Compare
    lotw_set = set(lotw_grids.keys())
    
    print("="*80)
    print("FFMA GRID COMPARISON")
    print("="*80)
    print(f"LoTW shows you have: {len(lotw_grids)} grids")
    print(f"Parsed ffma_data.json: {len(parsed_grids)} grids")
    print(f"Missing from parsed data: {len(lotw_set - parsed_grids)} grids")
    print()
    
    # Missing grids
    missing = lotw_set - parsed_grids
    if missing:
        print("MISSING GRIDS (in LoTW but not in parsed data):")
        print("-"*80)
        for grid in sorted(missing):
            call = lotw_grids.get(grid, "?")
            print(f"  {grid}  {call}")
        print()
    
    # Extra grids (shouldn't happen)
    extra = parsed_grids - lotw_set
    if extra:
        print("EXTRA GRIDS (in parsed data but not in LoTW):")
        print("-"*80)
        for grid in sorted(extra):
            print(f"  {grid}")
        print()
    
    # Now search the ADIF for missing grids
    adif_file = Path("vucc_6m.adi")
    if adif_file.exists() and missing:
        print("="*80)
        print("SEARCHING ADIF FOR MISSING GRIDS")
        print("="*80)
        
        adif_text = adif_file.read_text(encoding='utf-8', errors='ignore').upper()
        
        for grid in sorted(missing):
            # Search for this grid in ADIF
            if f"<GRIDSQUARE:{len(grid)}>{grid}" in adif_text or f"GRIDSQUARE:6>{grid}" in adif_text:
                print(f"\n{grid} - FOUND IN ADIF")
                
                # Find the record
                grid_pos = adif_text.find(grid)
                if grid_pos > 0:
                    # Get surrounding context
                    start = max(0, grid_pos - 500)
                    end = min(len(adif_text), grid_pos + 500)
                    context = adif_text[start:end]
                    
                    # Extract key fields
                    import re
                    my_grid_match = re.search(r'<MY_GRIDSQUARE:\d+>([A-Z0-9]+)', context)
                    band_match = re.search(r'<BAND:\d+>([A-Z0-9]+)', context)
                    call_match = re.search(r'<CALL:\d+>([A-Z0-9]+)', context)
                    qsl_match = re.search(r'<QSL_RCVD:\d+>([YN])', context)
                    
                    print(f"  CALL: {call_match.group(1) if call_match else '?'}")
                    print(f"  BAND: {band_match.group(1) if band_match else '?'}")
                    print(f"  MY_GRIDSQUARE: {my_grid_match.group(1) if my_grid_match else '?'}")
                    print(f"  QSL_RCVD: {qsl_match.group(1) if qsl_match else '?'}")
            else:
                print(f"\n{grid} - NOT FOUND IN ADIF (might be paper QSL)")

if __name__ == "__main__":
    main()