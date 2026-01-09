# challenge_table.py - Enhanced DXCC Challenge progress display with filters and sorting
import flet as ft
from backend.dxcc_challenge import get_stats
from backend.dxcc_lookup import get_country_from_prefix
from backend.dxcc_prefixes import get_prefix
from backend.file_paths import get_config_file
import json
from pathlib import Path

from backend.file_paths import (
    get_challenge_data_file,
    get_dxcc_entities_file,
    get_dxcc_overrides_file,
    get_dxcc_mapping_file
)

class ChallengeTable(ft.Column):
    """Display DXCC Challenge progress in a scrollable table with filters and sorting"""
    
    def __init__(self):
        super().__init__()
        
        # Load challenge data
        self.challenge_data = self._load_challenge_data()
        
        # Sort state: 'country' or 'prefix'
        self.sort_by = 'prefix'  # Default to prefix sort
        self.sort_reverse = False  # False = ascending, True = descending
        
        # Filter state
        self.selected_bands = {
            "160M": True,
            "80M": True,
            "60M": True,
            "40M": True,
            "30M": True,
            "20M": True,
            "17M": True,
            "15M": True,
            "12M": True,
            "10M": True,
            "6M": True,
        }
        self.show_needed_only = False
        
        # Build UI
        self.controls = [
            self._build_summary(),
            ft.Divider(height=10),
            self._build_filters(),
            ft.Divider(height=10),
            self._build_table(),
        ]
        
        self.scroll = ft.ScrollMode.AUTO
        self.expand = True
    
    def _load_challenge_data(self):
        """Load challenge data from JSON"""
        challenge_file = get_challenge_data_file()
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
                "raw_band_entity_pairs": data.get("raw_band_entity_pairs", []),
            }
        except Exception as e:
            print(f"Error loading challenge data: {e}")
            return None
    
    def _build_summary(self):
        """Build summary statistics"""
        if not self.challenge_data:
            return ft.Text("No challenge data loaded. Download from Settings tab.", size=16, color=ft.Colors.ORANGE_400)
    
        # Use 340 for max (all current DXCC entities), not just worked count
        all_entities = self._load_all_dxcc_entities()
        total_entities = len(all_entities)  # Should be 340
    
        # Safety check - prevent divide by zero
        if total_entities == 0:
            return ft.Text("DXCC entities not loaded. Check dxcc_entities.json", 
                          size=16, color=ft.Colors.RED)
    
        worked_entities = self.challenge_data.get("total_entities", 0)
        total_slots = self.challenge_data.get("total_slots", 0)
    
        # Safety check for empty challenge data
        if worked_entities == 0 and total_slots == 0:
            return ft.Container(
                content=ft.Column([
                    ft.Text("No Challenge data yet", size=18, color=ft.Colors.ORANGE),
                    ft.Text("Download from Settings tab to populate", size=14),
                ]),
                padding=20,
                bgcolor=ft.Colors.BLUE_GREY_900,
                border_radius=10,
            )
    
        # Calculate 60m slots (to exclude from main count)
        slots_60m = sum(1 for band, dxcc in self.challenge_data.get("raw_band_entity_pairs", []) if band == "60M")
        slots_no_60m = total_slots - slots_60m  # Subtract 60m, not 6m!
    
        max_slots_no_60m = total_entities * 10  # 10 bands (excludes 60m)
    
        # Total slots
        max_slots_total = total_entities * 11  # 11 bands (160m-6m including 60m)
    
        # Band statistics
        bands_stats = []
        for band in ["160M", "80M", "60M", "40M", "30M", "20M", "17M", "15M", "12M", "10M", "6M"]:
            count = self.challenge_data["entities_by_band"].get(band, 0)
            # Safety check for division
            pct = (count / total_entities * 100) if total_entities > 0 else 0
            bands_stats.append(f"{band}: {count}/{total_entities} ({pct:.0f}%)")
    
        return ft.Container(
            content=ft.Column([
                ft.Text("DXCC Challenge Progress", size=24, weight=ft.FontWeight.BOLD),

                ft.Row([
                    ft.Text(f"Total Entities: {worked_entities}/{total_entities}", size=18, weight=ft.FontWeight.BOLD),
                    ft.Text(f"({worked_entities/total_entities*100:.1f}%)" if total_entities > 0 else "(0.0%)", 
                        size=18, color=ft.Colors.GREEN),
                ], spacing=10),
                ft.Container(height=5),
            
                # Slots without 60m
                ft.Row([
                    ft.Text(f"Slots: {slots_no_60m}/{max_slots_no_60m}", size=16),
                    ft.Text("(excludes 60m)", size=12, color=ft.Colors.BLUE_GREY_400),
                ], spacing=10),
            
                # 60m slots
                ft.Text(f"60m Slots: {slots_60m}/{total_entities}", size=16),
            
                # Total slots
                ft.Row([
                    ft.Text(f"Total Slots: {total_slots}/{max_slots_total}", size=16),
                    ft.Text(f"({total_slots/max_slots_total*100:.1f}% complete)" if max_slots_total > 0 else "(0.0%)", 
                            size=16, color=ft.Colors.GREEN),
                ], spacing=10),
            
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
    
    def _build_filters(self):
        """Build band filter checkboxes and needed-only toggle"""
        
        # All/None buttons
        all_button = ft.ElevatedButton(
            text="All Bands",
            on_click=self._select_all_bands,
            height=32,
        )
        
        none_button = ft.ElevatedButton(
            text="No Bands",
            on_click=self._select_no_bands,
            height=32,
        )
        
        # Needed Only toggle
        self.needed_toggle = ft.Switch(
            label="Show Needed Only",
            value=self.show_needed_only,
            on_change=self._needed_toggle_changed,
        )
        
        # Band checkboxes - create all in one row
        band_row_controls = []
        for band in ["160M", "80M", "60M", "40M", "30M", "20M", "17M", "15M", "12M", "10M", "6M"]:
            check = ft.Checkbox(
                label=band,
                value=self.selected_bands[band],
                on_change=lambda e, b=band: self._band_filter_changed(b, e.control.value),
            )
            band_row_controls.append(check)
        
        return ft.Container(
            content=ft.Column([
                # Line 1: Buttons and toggle
                ft.Row([
                    all_button,
                    none_button,
                    ft.VerticalDivider(width=20),
                    self.needed_toggle,
                ], spacing=10),
                
                ft.Container(height=5),
                
                # Line 2: All band checkboxes in one row
                ft.Row(band_row_controls, spacing=8),
            ], spacing=0),
            padding=10,
            bgcolor=ft.Colors.BLUE_GREY_800,
            border_radius=10,
        )
    
    def _band_filter_changed(self, band, value):
        """Handle band filter checkbox change"""
        self.selected_bands[band] = value
        self._rebuild_table()
    
    def _select_all_bands(self, e):
        """Select all bands"""
        for band in self.selected_bands:
            self.selected_bands[band] = True
        self._rebuild_filters_and_table()
    
    def _select_no_bands(self, e):
        """Deselect all bands"""
        for band in self.selected_bands:
            self.selected_bands[band] = False
        self._rebuild_filters_and_table()
    
    def _needed_toggle_changed(self, e):
        """Handle needed-only toggle change"""
        self.show_needed_only = e.control.value
        self._rebuild_table()
    
    def _rebuild_filters_and_table(self):
        """Rebuild both filters and table (for All/None buttons)"""
        self.controls = [
            self._build_summary(),
            ft.Divider(height=10),
            self._build_filters(),
            ft.Divider(height=10),
            self._build_table(),
        ]
        try:
            self.update()
        except:
            pass
    
    def _build_table(self):
        """Build the entity x band grid with filters and sorting"""
        if not self.challenge_data:
            return ft.Container(
                content=ft.Column([
                    ft.Text("No Challenge data available", size=16, color=ft.Colors.ORANGE),
                    ft.Text("Download Challenge data from Settings tab", size=12),
                ]),
                padding=20
            )
        
        # Get selected bands
        selected_bands = [band for band, selected in self.selected_bands.items() if selected]
        
        if not selected_bands:
            return ft.Container(
                content=ft.Text("No bands selected. Select at least one band to display.", size=14, color=ft.Colors.ORANGE_400),
                padding=20,
            )
        
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
        
        # Add columns for selected bands only
        for band in selected_bands:
            columns.append(ft.DataColumn(ft.Text(band, weight=ft.FontWeight.BOLD)))
        
        # Load DXCC mapping for country names
        dxcc_mapping = self._load_dxcc_mapping()
        
        # Get ALL 340 current DXCC entities from dxcc_entities.json
        all_entities = self._load_all_dxcc_entities()
        
        # Create dict of worked entities for quick lookup
        worked_entities = self.challenge_data["entities"] if self.challenge_data else {}
        
        # Sort based on current sort_by state
        if self.sort_by == 'country':
            # Sort by country name
            entities_sorted = sorted(
                all_entities.items(),
                key=lambda x: x[1]["name"],
                reverse=self.sort_reverse
            )
        else:  # sort by prefix (default)
            # Sort by prefix
            entities_sorted = sorted(
                all_entities.items(), 
                key=lambda x: x[1]["prefix"],
                reverse=self.sort_reverse
            )
        
        # Build data rows with filters
        rows = []
        
        for entity_num_str, entity_data in entities_sorted:
            entity_num = int(entity_num_str)
            bands_worked = worked_entities.get(entity_num, set())
        
            # Apply "Needed Only" filter
            if self.show_needed_only:
                # Check if entity is missing ANY of the selected bands
                has_needed = False
                for band in selected_bands:
                    if band not in bands_worked:
                        has_needed = True
                        break
                
                if not has_needed:
                    continue  # Skip this entity - all selected bands worked
            
            country_name = entity_data["name"]
            prefix = entity_data["prefix"]
            
            # Truncate long names
            if len(country_name) > 25:
                country_name = country_name[:22] + "..."
            
            cells = [
                ft.DataCell(ft.Text(country_name, size=12)),
                ft.DataCell(ft.Text(prefix, size=12, weight=ft.FontWeight.BOLD)),
            ]
            
            # Add checkmarks for selected bands only
            for band in selected_bands:
                if band in bands_worked:
                    cells.append(ft.DataCell(ft.Text("✓", color=ft.Colors.GREEN, weight=ft.FontWeight.BOLD)))
                else:
                    cells.append(ft.DataCell(ft.Text("", size=12)))
            
            rows.append(ft.DataRow(cells=cells))
        
        # Show count
        count_text = ft.Text(
            f"Showing {len(rows)} entities" + (" (needed only)" if self.show_needed_only else ""),
            size=12,
            color=ft.Colors.BLUE_GREY_400,
        )
        
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
            content=ft.Column([
                count_text,
                ft.Container(height=5),
                ft.ListView(
                    controls=[table],
                    expand=True,
                ),
            ]),
            expand=True,
        )
    
    def _load_dxcc_mapping(self):
        """Load DXCC number -> country name mapping"""
        mapping_file = get_dxcc_mapping_file()
        if mapping_file.exists():
            try:
                return json.loads(mapping_file.read_text())
            except:
                pass
        return {}
        
    def _load_all_dxcc_entities(self):
        """Load all 340 current DXCC entities from dxcc_entities.json"""
        entities_file = get_dxcc_entities_file()
        if entities_file.exists():
            try:
                data = json.loads(entities_file.read_text(encoding='utf-8'))
                
                # Load name overrides
                overrides = self._load_name_overrides()
                
                # Filter to only current (not deleted) entities
                current = {}
                for dxcc_num, entity_data in data.items():
                    if entity_data.get("current", False):
                        # Apply name override if exists
                        if dxcc_num in overrides:
                            entity_data = entity_data.copy()  # Don't modify original
                            entity_data["name"] = overrides[dxcc_num]
                        current[dxcc_num] = entity_data
                
                return current
            except Exception as e:
                print(f"Error loading dxcc_entities.json: {e}")
        
        # Fallback to old method if file doesn't exist
        return self._load_dxcc_mapping_fallback()
    
    def _load_name_overrides(self):
        """Load DXCC name overrides (ARRL preferred names)"""
        override_file = get_dxcc_overrides_file()
        if override_file.exists():
            try:
                return json.loads(override_file.read_text(encoding='utf-8'))
            except Exception as e:
                print(f"Error loading name overrides: {e}")
        return {}
    
    def _load_dxcc_mapping_fallback(self):
        """Fallback to old dxcc_mapping.json format"""
        mapping_file = get_dxcc_mapping_file()
        if mapping_file.exists():
            try:
                mapping = json.loads(mapping_file.read_text())
                
                # Convert to entity format
                entities = {}
                for dxcc_num, name in mapping.items():
                    entities[dxcc_num] = {
                        "name": name,
                        "prefix": get_prefix(int(dxcc_num)),
                        "current": True
                    }
                return entities
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
        # Replace the table in controls
        self.controls[4] = self._build_table()
        try:
            self.update()
        except:
            pass
    
    def refresh(self):
        """Reload challenge data and rebuild table"""
        self.challenge_data = self._load_challenge_data()
        self.controls = [
            self._build_summary(),
            ft.Divider(height=10),
            self._build_filters(),
            ft.Divider(height=10),
            self._build_table(),
        ]
        try:
            self.update()
        except:
            pass