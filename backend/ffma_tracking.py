# ffma_tracking.py - ARRL FFMA (Fred Fish Memorial Award) tracking for 6 meters
"""
Tracks worked grids for the FFMA award (488 grids on 6 meters)
Parses LoTW ADIF file to find confirmed 6m QSOs with grid squares
"""

from pathlib import Path
import json
from datetime import datetime

import sys

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = Path(sys._MEIPASS)
    except Exception:
        base_path = Path.cwd()
    return base_path / relative_path

# Official 488 FFMA grids (extracted from ARRL LOTW)
FFMA_GRIDS = None  # Loaded from ffma_grids.json


def load_ffma_grids():
    """Load the official 488 FFMA grids"""
    global FFMA_GRIDS
    
    if FFMA_GRIDS is not None:
        return FFMA_GRIDS
    
    grids_file = get_resource_path("ffma_grids.json")
    #grids_file = Path("ffma_grids.json")
    if grids_file.exists():
        try:
            FFMA_GRIDS = set(json.loads(grids_file.read_text()))
            print(f"Loaded {len(FFMA_GRIDS)} FFMA grids")
            return FFMA_GRIDS
        except Exception as e:
            print(f"Error loading FFMA grids: {e}")
    
    # Fallback: empty set
    FFMA_GRIDS = set()
    return FFMA_GRIDS


def normalize_grid(grid):
    """Normalize grid to 4-character format"""
    if not grid:
        return None
    
    grid = grid.strip().upper()
    
    # Take first 4 characters if 6-char grid
    if len(grid) >= 4:
        return grid[:4]
    
    return None


def is_ffma_grid(grid):
    """Check if a grid square is in the FFMA list"""
    grids = load_ffma_grids()
    normalized = normalize_grid(grid)
    return normalized in grids if normalized else False


def parse_lotw_adif_for_ffma(adif_file_path, home_grid=None):
    """
    Parse LoTW ADIF file for 6m confirmations with grids
    Returns dict: {grid: {"call": callsign, "date": qso_date}}
    """
    
    # Get home grid from config if not provided
    if home_grid is None:
        try:
            from backend.config import get_user_grid
            home_grid = get_user_grid()
        except:
            home_grid = None
    
    # Normalize home grid to 4 characters
    if home_grid:
        home_grid = home_grid.strip().upper()[:4]
        print(f"Filtering FFMA QSOs to only those from home grid: {home_grid}")
    
    adif_path = Path(adif_file_path)
    if not adif_path.exists():
        print(f"ADIF file not found: {adif_file_path}")
        return {}
    
    print(f"Parsing {adif_file_path} for FFMA (6m grids)...")
    
    try:
        text = adif_path.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        print(f"Error reading ADIF file: {e}")
        return {}
    
    # Load FFMA grids
    ffma_grids = load_ffma_grids()
    
    # Parse ADIF records
    worked_grids = {}
    skipped_other_grids = 0
    
    # Split by <EOR> or <eor>
    records = text.upper().split('<EOR>')
    
    for record in records:
        if not record.strip():
            continue
        
        # Extract fields
        fields = {}
        
        # Find all <FIELD:LENGTH>VALUE patterns
        import re
        matches = re.findall(r'<([^:>]+):(\d+)(?::([^>]+))?>([^<]*)', record)
        
        for match in matches:
            field_name = match[0].strip()
            field_len = int(match[1])
            field_value = match[3][:field_len] if len(match[3]) >= field_len else match[3]
            fields[field_name] = field_value.strip()
        
        # Check if this is a 6m QSO with a grid
        band = fields.get('BAND', '')
        grid = fields.get('GRIDSQUARE', '')
        vucc_grids = fields.get('VUCC_GRIDS', '')  # Multi-grid activations
        call = fields.get('CALL', '')
        qso_date = fields.get('QSO_DATE', '')
        my_grid = fields.get('MY_GRIDSQUARE', '') 
        
        # Only process 6m QSOs
        if band != '6M':
            continue
        
        # Filter by home grid if specified  # ADD THESE LINES
        if home_grid and my_grid:
            my_grid_4char = my_grid[:4] if len(my_grid) >= 4 else my_grid
            if my_grid_4char != home_grid:
                skipped_other_grids += 1
                continue
        
        # Parse date (YYYYMMDD format) - do this BEFORE grid processing
        try:
            if qso_date and len(qso_date) == 8:
                date_obj = datetime.strptime(qso_date, '%Y%m%d')
                date_str = date_obj.strftime('%Y-%m-%d')
            else:
                date_str = qso_date or 'Unknown'
        except:
            date_str = qso_date or 'Unknown'
        
        # Process all grids (VUCC_GRIDS takes priority if present)
        grids_to_process = []
        
        if vucc_grids:
            # Multi-grid activation: "CM79XX,CM89AX,CN70XA,CN80AA"
            grid_list = [g.strip() for g in vucc_grids.split(',')]
            grids_to_process = grid_list
        elif grid:
            # Single grid
            grids_to_process = [grid]
        
        # Process each grid
        for g in grids_to_process:
            norm_grid = normalize_grid(g)
            if not norm_grid:
                continue
            
            # Check if it's an FFMA grid
            if norm_grid not in ffma_grids:
                continue
            
            # Store the first/earliest QSO for each grid
            if norm_grid not in worked_grids:
                worked_grids[norm_grid] = {
                    "call": call,
                    "date": date_str,
                }
    
    if home_grid and skipped_other_grids > 0:
        print(f"Skipped {skipped_other_grids} QSOs from other grids (not {home_grid})")
    
    print(f"Found {len(worked_grids)} FFMA grids worked on 6m from {home_grid if home_grid else 'all grids'}")
    
    return worked_grids


def is_grid_worked(grid):
    """Check if a grid has been worked (uses cached data)"""
    if not hasattr(is_grid_worked, '_cache'):
        # Try to load from saved file
        data_file = Path("ffma_data.json")
        if data_file.exists():
            try:
                data = json.loads(data_file.read_text())
                is_grid_worked._cache = set(data.get("worked_grids", {}).keys())
            except:
                is_grid_worked._cache = set()
        else:
            is_grid_worked._cache = set()
    
    norm_grid = normalize_grid(grid)
    return norm_grid in is_grid_worked._cache if norm_grid else False


def is_grid_needed(grid):
    """Check if a grid is needed for FFMA"""
    if not is_ffma_grid(grid):
        return False
    
    return not is_grid_worked(grid)


def save_ffma_data(worked_grids, filename="ffma_data.json"):
    """Save worked grids to JSON file"""
    
    data = {
        "total_ffma_grids": 488,
        "worked_grids": worked_grids,
        "total_worked": len(worked_grids),
        "completion_pct": round(len(worked_grids) / 488 * 100, 1),
        "last_updated": datetime.now().isoformat(),
    }
    
    Path(filename).write_text(json.dumps(data, indent=2, sort_keys=True))
    print(f"Saved FFMA data: {len(worked_grids)}/488 grids ({data['completion_pct']}%)")
    
    # Update cache
    is_grid_worked._cache = set(worked_grids.keys())
    
    return data


def get_ffma_stats():
    """Get FFMA statistics"""
    data_file = Path("ffma_data.json")
    if data_file.exists():
        try:
            return json.loads(data_file.read_text())
        except:
            pass
    
    return {
        "total_ffma_grids": 488,
        "worked_grids": {},
        "total_worked": 0,
        "completion_pct": 0.0,
    }


if __name__ == "__main__":
    # Test - parse ADIF file if provided
    import sys
    
    if len(sys.argv) > 1:
        adif_file = sys.argv[1]
        print(f"\nProcessing {adif_file} for FFMA...")
        worked = parse_lotw_adif_for_ffma(adif_file)
        save_ffma_data(worked)
        
        print(f"\nSample worked grids:")
        for grid, info in list(worked.items())[:10]:
            print(f"  {grid}: {info['call']} on {info['date']}")
    else:
        print("Usage: python ffma_tracking.py <lotw_adif_file>")
        print("\nThis will parse your LoTW ADIF file for 6m confirmations")
        print("and create ffma_data.json with your worked FFMA grids.")