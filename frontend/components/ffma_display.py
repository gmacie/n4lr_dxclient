# ffma_table.py - ARRL FFMA (Fred Fish Memorial Award) progress display
import flet as ft
from backend.ffma_tracking import get_ffma_stats, load_ffma_grids
import json
from pathlib import Path

from backend.app_logging import get_logger

logger = get_logger(__name__)

class FFMADisplay(ft.Column):
    """Display FFMA progress - 488 grids on 6 meters"""
    
    def __init__(self):
        super().__init__()
        
        # Load FFMA data
        self.ffma_data = self._load_ffma_data()
        
        # Load FFMA grids
        #try:
        #print("DEBUG FFMA_TABLE: About to call load_ffma_grids()")
        
        self.ffma_grids = load_ffma_grids()
        
        # Build UI
        self.controls = [
            self._build_summary(),
            ft.Divider(height=20),
            self._build_table(),
        ]
        
        self.scroll = ft.ScrollMode.AUTO
        self.expand = True
    
    def _load_ffma_data(self):
        """Load FFMA data from JSON"""
        stats = get_ffma_stats()
        logger.info("DEBUG: _load_ffma_data {stats}")
        return stats
    
    def _build_summary(self):
        """Build summary statistics"""
        logger.info("DEBUG: Start _build_summary statistics")
        if not self.ffma_data:
            return ft.Text("No FFMA data loaded", size=16, color=ft.Colors.RED)
        
        total_worked = self.ffma_data.get("total_worked", 0)
        total_grids = self.ffma_data.get("total_ffma_grids", 488)
        completion_pct = self.ffma_data.get("completion_pct", 0)
        last_updated = self.ffma_data.get("last_updated", "Never")
        
        # Format timestamp
        if last_updated and last_updated != "Never":
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(last_updated)
                last_updated = dt.strftime("%Y-%m-%d %H:%M")
            except:
                pass
        
        return ft.Container(
            content=ft.Column([
                ft.Text("ARRL FFMA Progress (6 Meters)", size=24, weight=ft.FontWeight.BOLD),
                ft.Text("Fred Fish Memorial Award - 488 Grid Squares", size=14, color=ft.Colors.BLUE_GREY_400),
                ft.Container(height=10),
                ft.Row([
                    ft.Text(f"Worked: {total_worked}/{total_grids}", size=18, weight=ft.FontWeight.BOLD),
                    ft.Text(f"({completion_pct}% complete)", size=18, color=ft.Colors.GREEN),
                ], spacing=20),
                ft.Container(height=5),
                ft.Text(f"Last updated: {last_updated}", size=12, color=ft.Colors.BLUE_GREY_400),
            ]),
            padding=20,
            bgcolor=ft.Colors.BLUE_GREY_900,
            border_radius=10,
        )
    
    def _build_table(self):
        """Build the grid table"""
        logger.info("DEBUG: Start build_summary statistics")
        if not self.ffma_grids:
            logger.info("DEBUG: ERROR FFMA grid list loaded")
            return ft.Text("FFMA grid list not loaded", color=ft.Colors.RED)
        
        # Build header row
        columns = [
            ft.DataColumn(ft.Text("Grid", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Callsign", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Date", weight=ft.FontWeight.BOLD)),
        ]
        
        # Build data rows
        rows = []
        worked_grids = self.ffma_data.get("worked_grids", {})
        
        # Sort grids alphabetically
        sorted_grids = sorted(self.ffma_grids)
        
        for grid in sorted_grids:
            # Check if worked
            if grid in worked_grids:
                info = worked_grids[grid]
                callsign = info.get("call", "")
                date = info.get("date", "")
                
                # Format date (YYYY-MM-DD -> MM/DD/YY for compactness)
                if date and len(date) == 10:
                    try:
                        parts = date.split('-')
                        date = f"{parts[1]}/{parts[2]}/{parts[0][2:]}"
                    except:
                        pass
                
                # Worked - green background on grid cell only
                grid_cell = ft.DataCell(
                    ft.Container(
                        content=ft.Text(grid, size=12, color=ft.Colors.BLACK, weight=ft.FontWeight.BOLD),
                        bgcolor=ft.Colors.GREEN_400,
                        padding=5,
                        border_radius=3,
                    )
                )
                call_cell = ft.DataCell(ft.Text(callsign, size=12, weight=ft.FontWeight.BOLD))
                date_cell = ft.DataCell(ft.Text(date, size=11, color=ft.Colors.BLUE_GREY_400))
                row_color = None
            else:
                # Not worked yet - red text for grid
                grid_cell = ft.DataCell(ft.Text(grid, size=12, color=ft.Colors.RED_400, weight=ft.FontWeight.BOLD))
                call_cell = ft.DataCell(ft.Text("", size=12))
                date_cell = ft.DataCell(ft.Text("", size=11))
                row_color = None
            
            cells = [grid_cell, call_cell, date_cell]
            rows.append(ft.DataRow(cells=cells, color=row_color))
        
        table = ft.DataTable(
            columns=columns,
            rows=rows,
            column_spacing=20,
            heading_row_height=40,
            data_row_max_height=32,
            border=ft.border.all(1, ft.Colors.GREY_700),
            heading_row_color=ft.Colors.BLUE_GREY_800,
        )
        
        return ft.Container(
            content=ft.ListView(
                controls=[table],
                expand=True,
            ),
            expand=True,
        )
    
    def refresh(self):
        """Reload FFMA data and rebuild table"""
        logger.info("DEBUG: Reload FFMA data and rebuild table")
        self.ffma_data = self._load_ffma_data()
        self.ffma_grids = load_ffma_grids()
        self.controls = [
            self._build_summary(),
            ft.Divider(height=20),
            self._build_table(),
        ]
        try:
            self.update()
        except:
            pass