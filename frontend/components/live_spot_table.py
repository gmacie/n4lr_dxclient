import flet as ft
import time

try:
    from backend.dxcc_challenge import is_needed
    CHALLENGE_AVAILABLE = True
except:
    CHALLENGE_AVAILABLE = False
    print("DXCC Challenge module not available")


class LiveSpotTable(ft.Column):
    """Live DX spot table with basic filters."""
    
    def __init__(self):
        super().__init__()
        self.spots: list[dict] = []
        # Initialize with all bands selected by default
        self.filter_bands: list[str] = ["160M", "80M", "60M", "40M", "30M", "20M", "17M", "15M", "12M", "10M", "6M"]
        self.filter_grid: str = ""
        self.filter_dxcc: str = ""
        self.max_spots: int = 100  # Reduced from 500 for better performance
        
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
    
    # ---------------------------------------------------
    def add_spot(self, spot: dict):
        """Add spot to list and rebuild if enough time has passed"""
        self.spots.insert(0, spot)
        if len(self.spots) > self.max_spots:
            self.spots = self.spots[: self.max_spots]
        
        # Check if enough time has passed since last rebuild
        current_time = time.time()
        if current_time - self.last_rebuild_time >= self.rebuild_interval:
            self._rebuild_rows()
            self.last_rebuild_time = current_time
            self.needs_rebuild = False
        else:
            # Mark that we need a rebuild later
            self.needs_rebuild = True
    
    # ---------------------------------------------------
    def set_filters(self, bands: list[str], grid: str, dxcc: str):
        """Update filters and rebuild table with current spots"""
        self.filter_bands = [b.upper() for b in bands] if bands else []
        self.filter_grid = (grid or "").upper()
        self.filter_dxcc = (dxcc or "").upper()
        
        # Rebuild to apply new filters (don't clear - just re-filter existing spots)
        self._rebuild_rows()
    
    # ---------------------------------------------------
    def clear_spots(self):
        """Clear all spots from the table"""
        self.spots = []
        self.table.rows = []
        try:
            self.table.update()
        except:
            pass  # Control not yet added to page
    
    # ---------------------------------------------------
    def _passes_filters(self, s: dict) -> bool:
        band = str(s.get("band", "")).upper()
        grid = str(s.get("grid", "")).upper()
        dxcc = str(s.get("dxcc", "")).upper()
        
        # Band filter: if list is empty, show NOTHING; if list has items, show only those bands
        if len(self.filter_bands) == 0:
            return False  # No bands selected = show nothing
        
        if band not in self.filter_bands:
            return False  # This band is not in the selected list
        
        if self.filter_grid and not grid.startswith(self.filter_grid):
            return False
        
        if self.filter_dxcc and self.filter_dxcc not in dxcc:
            return False
        
        return True
    
    # ---------------------------------------------------
    def _rebuild_rows(self):
        rows: list[ft.DataRow] = []
        
        for s in self.spots:
            if not self._passes_filters(s):
                continue
            
            # Check if this spot is needed for DXCC Challenge
            needed = False
            if CHALLENGE_AVAILABLE:
                try:
                    needed = is_needed(s.get("dxcc", ""), s.get("band", ""))
                except:
                    pass
            
            # Create row with red background if needed
            row = ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(s.get("time", ""))),
                    ft.DataCell(ft.Text(s.get("band", ""))),
                    ft.DataCell(ft.Text(s.get("freq", ""))),
                    ft.DataCell(ft.Text(s.get("call", ""))),
                    ft.DataCell(ft.Text(s.get("dxcc", ""))),
                    ft.DataCell(ft.Text(s.get("grid", ""))),
                    ft.DataCell(ft.Text(s.get("spotter", ""))),
                    ft.DataCell(ft.Text(s.get("comment", ""))),
                ],
                color=ft.Colors.RED_100 if needed else None,  # Light red background for needed spots
            )
            rows.append(row)
        
        self.table.rows = rows
        try:
            self.table.update()
        except:
            pass  # Control not yet added to page
