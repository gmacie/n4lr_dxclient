# challenge_table.py - DXCC Challenge progress display
import flet as ft
from backend.dxcc_challenge import get_stats
from backend.dxcc_lookup import get_country_from_prefix
from backend.dxcc_prefixes import get_prefix
import json
from pathlib import Path


class ChallengeTable(ft.Column):
    """Display DXCC Challenge progress in a scrollable table"""
    
    def __init__(self):
        super().__init__()
        
        # Load challenge data
        self.challenge_data = self._load_challenge_data()
        
        # Sort state: 'country' or 'prefix'
        self.sort_by = 'prefix'  # Default to prefix sort
        self.sort_reverse = False  # False = ascending, True = descending
        
        # Build UI
        self.controls = [
            self._build_summary(),
            ft.Divider(height=20),
            self._build_table(),
        ]
        
        self.scroll = ft.ScrollMode.AUTO
        self.expand = True
    
    def _load_challenge_data(self):
        """Load challenge data from JSON"""
        challenge_file = Path("challenge_data.json")
        if not challenge_file.exists():
            return None
        
        try:
            data = json.loads(challenge_file.read_text())
            
            # Organize by entity
            entities = {}
            for band_entity_pair in data.get("raw_band_entity_pairs", []):
                if len(band_entity_pair) != 2:
                    continue
                band, entity = band_entity_pair
                
                if entity not in entities:
                    entities[entity] = set()
                entities[entity].add(band)
            
            return {
                "total_entities": data.get("total_entities", 0),
                "total_slots": data.get("total_challenge_slots", 0),
                "entities_by_band": data.get("entities_by_band", {}),
                "entities": entities,  # entity -> set of bands
            }
        except Exception as e:
            print(f"Error loading challenge data: {e}")
            return None
    
    def _build_summary(self):
        """Build summary statistics"""
        if not self.challenge_data:
            return ft.Text("No challenge data loaded", size=16, color=ft.Colors.RED)
        
        total_entities = self.challenge_data["total_entities"]
        total_slots = self.challenge_data["total_slots"]
        max_slots = total_entities * 11  # 11 bands (160m-6m including 60m)
        
        # Band statistics
        bands_stats = []
        for band in ["160M", "80M", "60M", "40M", "30M", "20M", "17M", "15M", "12M", "10M", "6M"]:
            count = self.challenge_data["entities_by_band"].get(band, 0)
            pct = (count / total_entities * 100) if total_entities > 0 else 0
            bands_stats.append(f"{band}: {count}/{total_entities} ({pct:.0f}%)")
        
        return ft.Container(
            content=ft.Column([
                ft.Text("DXCC Challenge Progress", size=24, weight=ft.FontWeight.BOLD),
                ft.Row([
                    ft.Text(f"Total Entities: {total_entities}", size=16),
                    ft.Text(f"Total Slots: {total_slots}/{max_slots}", size=16),
                    ft.Text(f"({total_slots/max_slots*100:.1f}% complete)", size=16, color=ft.Colors.GREEN),
                ], spacing=20),
                ft.Container(height=10),
                ft.Text("Band Progress:", size=14, weight=ft.FontWeight.BOLD),
                ft.Row([
                    ft.Column([ft.Text(s, size=12) for s in bands_stats[:6]]),
                    ft.Column([ft.Text(s, size=12) for s in bands_stats[6:]]),
                ], spacing=40),
            ]),
            padding=20,
            bgcolor=ft.Colors.BLUE_GREY_900,
            border_radius=10,
        )
    
    def _build_table(self):
        """Build the entity x band grid"""
        if not self.challenge_data:
            return ft.Text("No data to display")
        
        # Build header row with clickable sort buttons
        # Show arrow on active column: ▲ for ascending, ▼ for descending
        country_arrow = ""
        prefix_arrow = ""
        
        if self.sort_by == 'country':
            country_arrow = " ▲" if not self.sort_reverse else " ▼"
        else:  # prefix
            prefix_arrow = " ▲" if not self.sort_reverse else " ▼"
        
        columns = [
            ft.DataColumn(
                ft.TextButton(
                    "Country" + country_arrow,
                    on_click=self._sort_by_country,
                ),
            ),
            ft.DataColumn(
                ft.TextButton(
                    "Prefix" + prefix_arrow,
                    on_click=self._sort_by_prefix,
                ),
            ),
        ]
        
        bands = ["160M", "80M", "60M", "40M", "30M", "20M", "17M", "15M", "12M", "10M", "6M"]
        for band in bands:
            columns.append(ft.DataColumn(ft.Text(band, weight=ft.FontWeight.BOLD)))
        
        # Build data rows
        rows = []
        
        # Load DXCC mapping for country names
        dxcc_mapping = self._load_dxcc_mapping()
        
        # Sort based on current sort_by state
        if self.sort_by == 'country':
            # Sort by country name
            entities_sorted = sorted(
                self.challenge_data["entities"].items(),
                key=lambda x: dxcc_mapping.get(str(x[0]), f"Entity {x[0]}"),
                reverse=self.sort_reverse
            )
        else:  # sort by prefix (default)
            # Sort by prefix
            entities_sorted = sorted(
                self.challenge_data["entities"].items(), 
                key=lambda x: get_prefix(x[0]),
                reverse=self.sort_reverse
            )
        
        for entity_num, bands_worked in entities_sorted:
            country_name = dxcc_mapping.get(str(entity_num), f"Entity {entity_num}")
            prefix = get_prefix(entity_num)
            
            # Truncate long names
            if len(country_name) > 25:
                country_name = country_name[:22] + "..."
            
            cells = [
                ft.DataCell(ft.Text(country_name, size=12)),
                ft.DataCell(ft.Text(prefix, size=12, weight=ft.FontWeight.BOLD)),
            ]
            
            # Add checkmarks for each band
            for band in bands:
                if band in bands_worked:
                    cells.append(ft.DataCell(ft.Text("✓", color=ft.Colors.GREEN, weight=ft.FontWeight.BOLD)))
                else:
                    cells.append(ft.DataCell(ft.Text("", size=12)))
            
            rows.append(ft.DataRow(cells=cells))
        
        table = ft.DataTable(
            columns=columns,
            rows=rows,
            column_spacing=10,
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
    
    def _load_dxcc_mapping(self):
        """Load DXCC number -> country name mapping"""
        mapping_file = Path("dxcc_mapping.json")
        if mapping_file.exists():
            try:
                return json.loads(mapping_file.read_text())
            except:
                pass
        return {}
    
    def _sort_by_country(self, e):
        """Sort table by country name - toggle direction if already sorting by country"""
        if self.sort_by == 'country':
            # Already sorting by country, toggle direction
            self.sort_reverse = not self.sort_reverse
        else:
            # Switching to country sort, default to ascending
            self.sort_by = 'country'
            self.sort_reverse = False
        self._rebuild_table()
    
    def _sort_by_prefix(self, e):
        """Sort table by prefix - toggle direction if already sorting by prefix"""
        if self.sort_by == 'prefix':
            # Already sorting by prefix, toggle direction
            self.sort_reverse = not self.sort_reverse
        else:
            # Switching to prefix sort, default to ascending
            self.sort_by = 'prefix'
            self.sort_reverse = False
        self._rebuild_table()
    
    def _rebuild_table(self):
        """Rebuild just the table portion"""
        # Find the table in controls and replace it
        self.controls = [
            self._build_summary(),
            ft.Divider(height=20),
            self._build_table(),
        ]
        try:
            self.update()
        except:
            pass
    
    def refresh(self):
        """Reload challenge data and rebuild table"""
        self.challenge_data = self._load_challenge_data()
        self.controls = [
            self._build_summary(),
            ft.Divider(height=20),
            self._build_table(),
        ]
        try:
            self.update()
        except:
            pass