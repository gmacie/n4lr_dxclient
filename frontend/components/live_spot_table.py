import flet as ft
import time
from datetime import datetime, timedelta

try:
    from backend.lotw_users import is_lotw_user, get_upload_age_days
    LOTW_AVAILABLE = True
except:
    LOTW_AVAILABLE = False
    print("LoTW user lookup not available")

try:
    from backend.dxcc_challenge import is_needed
    CHALLENGE_AVAILABLE = True
except:
    CHALLENGE_AVAILABLE = False
    print("DXCC Challenge module not available")

try:
    from backend.dxcc_lookup import lookup_dxcc_from_prefix
    DXCC_LOOKUP_AVAILABLE = True
except:
    DXCC_LOOKUP_AVAILABLE = False
    print("DXCC lookup not available")

try:
    from backend.ffma_tracking import is_grid_needed
    FFMA_AVAILABLE = True
except:
    FFMA_AVAILABLE = False
    print("FFMA tracking module not available")

try:
    from backend.config import load_config
    CONFIG_AVAILABLE = True
except:
    CONFIG_AVAILABLE = False
    print("Config module not available")


class LiveSpotTable(ft.Column):
    """Live DX spot table with basic filters and separate needed spots buffer."""
    
    def __init__(self):
        super().__init__()
        
        # Two separate buffers
        self.regular_spots: list[dict] = []  # Regular spots (100 max)
        self.needed_spots: list[dict] = []   # Needed spots (kept longer)
        
        # Initialize with all bands selected by default
        self.filter_bands: list[str] = ["160M", "80M", "60M", "40M", "30M", "20M", "17M", "15M", "12M", "10M", "6M"]
        self.filter_grid: str = ""
        self.filter_dxcc: str = ""
        self.filter_lotw_only: bool = False
        self.filter_needed_only: bool = False
        
        # Buffer sizes
        self.max_regular_spots: int = 100
        self.needed_spot_minutes: int = 15  # Keep needed spots for 15 minutes
        
        # Load needed spot duration from config
        if CONFIG_AVAILABLE:
            try:
                config = load_config()
                self.needed_spot_minutes = config.getint('display', 'needed_spot_minutes', fallback=15)
            except:
                pass
        
        # Load blocked spotters from config
        self.blocked_spotters = []
        if CONFIG_AVAILABLE:
            try:
                from backend.config import get_blocked_spotters
                self.blocked_spotters = get_blocked_spotters()
            except:
                pass
        
        # Batching for performance - rebuild at most every N seconds
        self.last_rebuild_time: float = 0
        self.rebuild_interval: float = 2.0  # Rebuild every 2 seconds max
        self.needs_rebuild: bool = False
        
        self.table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Time")),
                ft.DataColumn(ft.Text("Band")),
                ft.DataColumn(ft.Text("Freq")),
                ft.DataColumn(ft.Text("Call")),
                ft.DataColumn(ft.Text("DXCC")),
                ft.DataColumn(ft.Text("Grid")),
                ft.DataColumn(ft.Text("Spotter")),
                ft.DataColumn(ft.Text("Comment")),
            ],
            rows=[],
            column_spacing=10,
            heading_row_height=32,
            data_row_max_height=32,
        )
        
        self._list_view = ft.ListView(
            controls=[self.table],
            expand=True,
            auto_scroll=False,
        )
        
        self.controls = [self._list_view]
        self.expand = True
    
    def set_needed_spot_duration(self, minutes: int):
        """Update how long to keep needed spots"""
        self.needed_spot_minutes = minutes
        self._clean_old_needed_spots()
        self._schedule_rebuild()
    
    def _clean_old_needed_spots(self):
        """Remove needed spots older than configured duration"""
        if not self.needed_spots:
            return
        
        cutoff_time = datetime.now() - timedelta(minutes=self.needed_spot_minutes)
        
        # Keep spots that have a timestamp and are newer than cutoff
        self.needed_spots = [
            spot for spot in self.needed_spots
            if spot.get('timestamp') and spot['timestamp'] > cutoff_time
        ]
    
    def add_spot(self, spot: dict):
        """Add spot to appropriate buffer and rebuild if enough time has passed"""
        
        
        # DEBUG - Print first spot to see what data we have
        if not hasattr(self, '_debug_printed'):
            print(f"\nDEBUG SPOT DATA:")
            print(f"  Call: {spot.get('call')}")
            print(f"  DXCC: '{spot.get('dxcc')}'")
            print(f"  Band: '{spot.get('band')}'")
            print(f"  Grid: '{spot.get('grid')}'")
            self._debug_printed = True
        
        # Add timestamp for age tracking
        spot['timestamp'] = datetime.now()
        
        # Check if this spot is needed for Challenge
        is_spot_needed_challenge = False
        if CHALLENGE_AVAILABLE and DXCC_LOOKUP_AVAILABLE:
            try:
                # Convert prefix to DXCC number
                dxcc_prefix = spot.get("dxcc", "")
                dxcc_num = lookup_dxcc_from_prefix(dxcc_prefix) if dxcc_prefix else None
                
                if dxcc_num:
                    is_spot_needed_challenge = is_needed(dxcc_num, spot.get("band", ""))
            except:
                pass
        
        # Check if this spot is needed for FFMA
        is_spot_needed_ffma = False
        if FFMA_AVAILABLE and spot.get("band", "").upper() == "6M":
            try:
                grid = spot.get("grid", "")
                if grid:
                    is_spot_needed_ffma = is_grid_needed(grid)
            except:
                pass
        
        # Add to appropriate buffer (either Challenge or FFMA needed goes to needed buffer)
        if is_spot_needed_challenge or is_spot_needed_ffma:
            # Remove any existing spot with same callsign+band from needed buffer
            call = spot.get("call", "")
            band = spot.get("band", "")
            self.needed_spots = [
                s for s in self.needed_spots
                if not (s.get("call") == call and s.get("band") == band)
            ]
            
            # Add new spot to needed spots buffer
            self.needed_spots.insert(0, spot)
            # Clean old needed spots
            self._clean_old_needed_spots()
        else:
            # Add to regular spots buffer
            self.regular_spots.insert(0, spot)
            if len(self.regular_spots) > self.max_regular_spots:
                self.regular_spots = self.regular_spots[:self.max_regular_spots]
        
        # Check if enough time has passed since last rebuild
        current_time = time.time()
        if current_time - self.last_rebuild_time >= self.rebuild_interval:
            self._rebuild_rows()
            self.last_rebuild_time = current_time
            self.needs_rebuild = False
        else:
            # Mark that we need a rebuild later
            self.needs_rebuild = True
    
    def set_filters(self, bands: list[str], grid: str, dxcc: str):
        """Update filters and rebuild table with current spots"""
        self.filter_bands = [b.upper() for b in bands] if bands else []
        self.filter_grid = (grid or "").upper()
        self.filter_dxcc = (dxcc or "").upper()
        
        # Rebuild to apply new filters (don't clear - just re-filter existing spots)
        self._rebuild_rows()
    
    def set_lotw_only(self, enabled: bool):
        """Toggle LoTW only filter"""
        self.filter_lotw_only = enabled
        self._schedule_rebuild()
    
    def set_needed_only(self, enabled: bool):
        """Toggle needed only filter"""
        self.filter_needed_only = enabled
        self._schedule_rebuild()
    
    def set_blocked_spotters(self, spotters_list):
        """Update blocked spotters list"""
        self.blocked_spotters = [s.upper() for s in spotters_list]
        self._schedule_rebuild()
    
    def _schedule_rebuild(self):
        """Schedule a rebuild immediately"""
        self._rebuild_rows()
    
    def clear_spots(self):
        """Clear all spots from both buffers"""
        self.regular_spots = []
        self.needed_spots = []
        self.table.rows = []
        try:
            self.table.update()
        except:
            pass  # Control not yet added to page
    
    def _passes_filters(self, s: dict) -> bool:
        band = str(s.get("band", "")).upper()
        grid = str(s.get("grid", "")).upper()
        dxcc = str(s.get("dxcc", "")).upper()
        call = str(s.get("call", ""))
        
        # Band filter: if list is empty, show NOTHING; if list has items, show only those bands
        if len(self.filter_bands) == 0:
            return False  # No bands selected = show nothing
        
        if band not in self.filter_bands:
            return False  # This band is not in the selected list
        
        if self.filter_grid and not grid.startswith(self.filter_grid):
            return False
        
        if self.filter_dxcc and self.filter_dxcc not in dxcc:
            return False
        
        if band not in self.filter_bands:
            return False  # This band is not in the selected list
        
        # Blocked spotters filter  # ADD THIS
        spotter = str(s.get("spotter", "")).upper()
        if spotter in self.blocked_spotters:
            return False  # Block this spotter
        
        if self.filter_grid and not grid.startswith(self.filter_grid):
            return False
        
        # LoTW Only filter
        if self.filter_lotw_only:
            if LOTW_AVAILABLE:
                try:
                    if not is_lotw_user(call):
                        return False
                except:
                    return False
            else:
                return False  # Can't filter if LoTW not available
        
        # Needed Only filter
        if self.filter_needed_only:
            if CHALLENGE_AVAILABLE and DXCC_LOOKUP_AVAILABLE:
                try:
                    dxcc_prefix = s.get("dxcc", "")
                    dxcc_num = lookup_dxcc_from_prefix(dxcc_prefix) if dxcc_prefix else None
                    
                    if not dxcc_num or not is_needed(dxcc_num, s.get("band", "")):
                        return False
                except:
                    return False
            else:
                return False  # Can't filter if Challenge not available
        
        return True
    
    def _rebuild_rows(self):
        """Rebuild table rows from both buffers, needed spots first"""
        rows: list[ft.DataRow] = []
        
        # Clean old needed spots before rebuilding
        self._clean_old_needed_spots()
        
        # Combine both buffers: needed spots first, then regular
        all_spots = self.needed_spots + self.regular_spots
        
        for s in all_spots:
            if not self._passes_filters(s):
                continue
        
            # Check if this spot is needed for DXCC Challenge
            needed_challenge = False
            if CHALLENGE_AVAILABLE and DXCC_LOOKUP_AVAILABLE:
                try:
                    # Convert prefix to DXCC number
                    dxcc_prefix = s.get("dxcc", "")
                    dxcc_num = lookup_dxcc_from_prefix(dxcc_prefix) if dxcc_prefix else None
                    
                    if dxcc_num:
                        needed_challenge = is_needed(dxcc_num, s.get("band", ""))
                except:
                    pass
            
            # Check if this spot is needed for FFMA (6m grids only)
            needed_ffma = False
            if FFMA_AVAILABLE and s.get("band", "").upper() == "6M":
                try:
                    grid = s.get("grid", "")
                    if grid:
                        needed_ffma = is_grid_needed(grid)
                except:
                    pass
            
            # Determine highlight color (Challenge takes priority)
            if needed_challenge:
                highlight_color = ft.Colors.AMBER_200  # Challenge - amber
                text_color = ft.Colors.BLACK
            elif needed_ffma:
                highlight_color = ft.Colors.CYAN_200  # FFMA - cyan
                text_color = ft.Colors.BLACK
            else:
                highlight_color = None
                text_color = None
        
            # Format callsign with LoTW indicator
            call = s.get("call", "")
            if LOTW_AVAILABLE and is_lotw_user(call):
                age_days = get_upload_age_days(call)
                if age_days and age_days <= 90:
                    # Active user - green +
                    call_display = ft.Row([
                        ft.Text("+", color=ft.Colors.GREEN, weight=ft.FontWeight.BOLD),
                        ft.Text(call, color=text_color, weight=ft.FontWeight.BOLD if (needed_challenge or needed_ffma) else None),
                    ], spacing=2)
                else:
                    # Inactive user - orange +
                    call_display = ft.Row([
                        ft.Text("+", color=ft.Colors.ORANGE, weight=ft.FontWeight.BOLD),
                        ft.Text(call, color=text_color, weight=ft.FontWeight.BOLD if (needed_challenge or needed_ffma) else None),
                    ], spacing=2)
            else:
                # Not a LoTW user
                call_display = ft.Text(call, color=text_color, weight=ft.FontWeight.BOLD if (needed_challenge or needed_ffma) else None)
        
            # Create row with appropriate background color
            row = ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(s.get("time", ""), color=text_color)),
                    ft.DataCell(ft.Text(s.get("band", ""), color=text_color)),
                    ft.DataCell(ft.Text(s.get("freq", ""), color=text_color)),
                    ft.DataCell(call_display),
                    ft.DataCell(ft.Text(s.get("dxcc", ""), color=text_color, weight=ft.FontWeight.BOLD if (needed_challenge or needed_ffma) else None)),
                    ft.DataCell(ft.Text(s.get("grid", ""), color=text_color)),
                    ft.DataCell(ft.Text(s.get("spotter", ""), color=text_color)),
                    ft.DataCell(ft.Text(s.get("comment", ""), color=text_color)),
                ],
                color=highlight_color,
            )
            rows.append(row)
    
        self.table.rows = rows
        try:
            self.table.update()
        except:
            pass