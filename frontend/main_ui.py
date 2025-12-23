# main_ui.py 12/20/2025 - Added multi-select band checkboxes

import flet as ft
import asyncio
import time

from backend.message_bus import register_callback, publish
from backend.config import get_user_grid
from backend.solar import fetch_solar_data, get_solar_data
from frontend.components.status_bar import build_status_bar
from frontend.components.live_spot_table import LiveSpotTable
from frontend.components.settings_tab import SettingsTab

from backend.cluster_async import start_connection
from backend.config import get_user_grid, get_auto_connect


class MainUI(ft.Column):
    """Main N4LR DX monitor UI with tabs."""

    def __init__(self, page: ft.Page):
        super().__init__(expand=True)
        self.page = page
        self.connection_task = None  # ADD THIS LINE

        self.blocked_prefixes: set[str] = set()
        self.recent_spot_times: list[float] = []

        # Load user's grid for sun times
        user_grid = get_user_grid()

        # status bar with sun times and solar data
        self.status_bar, self.set_status, self.set_rate, self.set_grid, self.set_solar = build_status_bar(user_grid)

        # NOW hook pubsub callback (after status bar exists)
        register_callback(self._on_backend_msg)
        if self.page.pubsub:
            self.page.pubsub.subscribe(self._on_backend_msg)
        
        # Fetch solar data on startup
        self.page.run_task(self._fetch_solar_data_once)

        # spot table
        self.table = LiveSpotTable()

        # Band selection - checkboxes for multi-select (RIGHT SIDE PANEL)
        self.band_checkboxes = {}
        bands = ["160m", "80m", "60m", "40m", "30m", "20m", "17m", "15m", "12m", "10m", "6m"]
        
        # "All Bands" checkbox
        self.all_bands_checkbox = ft.Checkbox(
            label="All",
            value=True,
            on_change=self._all_bands_changed,
        )
        
        # "None" checkbox - unchecks all
        self.none_bands_checkbox = ft.Checkbox(
            label="None",
            value=False,
            on_change=self._none_bands_changed,
        )
        
        # Individual band checkboxes
        band_checkbox_controls = [
            ft.Text("Bands:", weight=ft.FontWeight.BOLD, size=14),
            ft.Row([self.all_bands_checkbox, self.none_bands_checkbox], spacing=5),
        ]
        for band in bands:
            cb = ft.Checkbox(
                label=band,
                value=True,
                on_change=self._band_checkbox_changed,
            )
            self.band_checkboxes[band] = cb
            band_checkbox_controls.append(cb)
        
        # Band filter panel (right side, fixed width)
        band_panel = ft.Container(
            content=ft.Column(
                band_checkbox_controls,
                spacing=5,
                scroll=ft.ScrollMode.AUTO,
            ),
            width=120,
            padding=10,
            bgcolor=ft.Colors.BLUE_GREY_900,
            border_radius=5,
        )

        # Other filters (top row)
        self.grid_field = ft.TextField(
            label="Grid",
            width=100,
            on_change=self._filters_changed,
        )

        self.dxcc_field = ft.TextField(
            label="DXCC substring",
            width=140,
            on_change=self._filters_changed,
        )
        
        # Quick filter buttons
        self.reject_kve_button = ft.ElevatedButton(
            text="Reject K,VE",
            tooltip="Quick reject US/Canada",
            on_click=self._quick_reject_kve,
        )
        
        self.reset_filters_button = ft.ElevatedButton(
            text="Reset Filters",
            tooltip="Clear all server filters",
            on_click=self._quick_reset_filters,
        )

        other_filters_row = ft.Row(
            [
                ft.Text("Filters:", weight=ft.FontWeight.BOLD),
                self.grid_field,
                self.dxcc_field,
                self.reject_kve_button,
                self.reset_filters_button,
            ],
            spacing=10,
        )

        # Command input
        self.command_field = ft.TextField(
            label="Cluster Command",
            hint_text="e.g., set/filter dxcty/reject k",
            width=400,
            on_submit=self._send_command,
        )

        self.send_button = ft.ElevatedButton(
            text="Send",
            on_click=self._send_command,
        )

        self.help_button = ft.IconButton(
            icon=ft.Icons.HELP_OUTLINE,
            tooltip="Show common commands",
            on_click=self._show_command_help,
        )

        command_row = ft.Row(
            [
                ft.Text("Command:", weight=ft.FontWeight.BOLD),
                self.command_field,
                self.send_button,
                self.help_button,
            ],
            spacing=10,
        )

        # Build Spots tab content with side-by-side layout
        # Left side: filters + command + spots table (scrollable, expand)
        # Right side: band checkboxes (fixed width, non-scrolling)
        
        left_side = ft.Column([
            other_filters_row,
            command_row,
            ft.Divider(),
            self.table,
        ], expand=True)
        
        spots_content = ft.Row([
            left_side,
            band_panel,
        ], expand=True)

        # Build Settings tab
        settings_tab_content = SettingsTab(
            page=self.page,
            on_settings_changed=self._on_settings_changed,
            initial_connection_state=get_auto_connect()
        )

        # Create tabs
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="Live Spots",
                    icon=ft.Icons.RADAR,
                    content=spots_content,
                ),
                ft.Tab(
                    text="Settings",
                    icon=ft.Icons.SETTINGS,
                    content=settings_tab_content,
                ),
            ],
            expand=True,
        )

        self.controls = [
            self.status_bar,
            self.tabs,
        ]

        # start spot rate timer
        self.page.run_task(self._spot_rate_timer)
        
        # Start cluster connection if auto-connect is enabled
        # Do this LAST, after UI is fully built
        #if get_auto_connect():
        #    async def delayed_auto_connect():
        #        await asyncio.sleep(0.5)  # Give UI time to render
        #        await start_connection()
        #    self.page.run_task(delayed_auto_connect)      
        
        # Start cluster connection if auto-connect is enabled
        if get_auto_connect():
            self.connection_task = self.page.run_task(start_connection)

    # ------------------------------------------------------------
    # BAND CHECKBOX HANDLERS
    # ------------------------------------------------------------
    def _all_bands_changed(self, e):
        """When 'All' checkbox is toggled, set all band checkboxes to match"""
        all_checked = self.all_bands_checkbox.value
        for cb in self.band_checkboxes.values():
            cb.value = all_checked
            cb.update()
        
        # Uncheck "None" when "All" is checked
        if all_checked:
            self.none_bands_checkbox.value = False
            self.none_bands_checkbox.update()
        
        self._filters_changed()
    
    def _none_bands_changed(self, e):
        """When 'None' checkbox is toggled, uncheck all bands"""
        if self.none_bands_checkbox.value:
            # Uncheck all bands
            for cb in self.band_checkboxes.values():
                cb.value = False
                cb.update()
            
            # Uncheck "All"
            self.all_bands_checkbox.value = False
            self.all_bands_checkbox.update()
            
            self._filters_changed()
    
    def _band_checkbox_changed(self, e):
        """When individual band checkbox changes, update 'All' and 'None' checkbox states"""
        # Check if all bands are selected
        all_selected = all(cb.value for cb in self.band_checkboxes.values())
        none_selected = not any(cb.value for cb in self.band_checkboxes.values())
        
        # Update "All" checkbox (without triggering its on_change)
        self.all_bands_checkbox.value = all_selected
        self.all_bands_checkbox.update()
        
        # Update "None" checkbox - uncheck if ANY band is checked
        self.none_bands_checkbox.value = none_selected
        self.none_bands_checkbox.update()
        
        self._filters_changed()
 
    # ------------------------------------------------------------
    # QUICK FILTER BUTTONS
    # ------------------------------------------------------------
    def _quick_reject_kve(self, e):
        """Quick button to reject K and VE spots"""
        publish({"type": "cluster_command", "data": "set/filter dxcty/reject k,ve"})

    def _quick_reset_filters(self, e):
        """Quick button to reset all server filters"""
        publish({"type": "cluster_command", "data": "set/nofilter"})
        # ------------------------------------------------------------
    
    # SETTINGS CHANGED HANDLER
    # ------------------------------------------------------------
    def _on_settings_changed(self, callsign, grid):
        """Called when user saves settings"""
        # Update sun times in status bar
        self.set_grid(grid)
        
        # Show notification
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(f"Settings saved! Grid: {grid}, Callsign: {callsign}"),
            action="OK",
        )
        self.page.snack_bar.open = True
        self.page.update()

    # ------------------------------------------------------------
    # COMMAND HANDLING
    # ------------------------------------------------------------
    def _send_command(self, e):
        """Send command to cluster"""
        cmd = self.command_field.value.strip()
        # print(f"DEBUG: _send_command called with: '{cmd}'")
        if not cmd:
            # print("DEBUG: Command was empty!")
            return
        
        # Publish command to backend via message bus
        # print(f"DEBUG: Publishing command: {cmd}")
        publish({"type": "cluster_command", "data": cmd})
        
        # Clear the field
        self.command_field.value = ""
        self.command_field.update()
        # print("DEBUG: Command sent and field cleared")

    def _show_command_help(self, e):
        """Show dialog with common commands"""
        print("DEBUG: Help button clicked!")
    
        help_text = """Common VE7CC Cluster Commands:

    FILTERS (reduce spot volume):
      set/filter doc/pass k,ve        - Only spots from US/Canada
      set/filter dxcty/reject k       - Reject US (K) spots
      set/filter dxcty/pass <prefix>  - Only spots for specific countries
      set/filter dxbm/pass 20,15,10   - Only specific bands
      set/nofilter                    - Reset all filters
      sh/filter                       - Show current filters

    DISPLAY OPTIONS:
      set/noskimmer   - Turn off skimmer spots
      set/skimmer     - Turn on skimmer spots
      set/nobeacon    - Turn off beacon spots
      set/grid        - Show grid squares
      set/dxs         - Show DX state/country
  
    INFORMATION:
      sh/dx           - Show last 30 spots
      sh/dx/100       - Show last 100 spots
      sh/dx <call>    - Show spots for specific call
      sh/mydx         - Show spots matching your filters
      sh/settings     - Show your current settings

    SPOT:
      dx <freq> <call> <comment>      - Send a DX spot

    Press Enter in command field or click Send to execute."""

        
        def close_bs(e):
            bs.open = False
            self.page.update()
    
        bs = ft.BottomSheet(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                    ft.Text("Cluster Commands", size=20, weight=ft.FontWeight.BOLD),
                    ft.IconButton(icon=ft.Icons.CLOSE, on_click=close_bs),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(),
                ft.Container(
                    content=ft.Text(help_text, selectable=True, size=13),
                    height=500,  # Fixed height
                ),
            ], scroll=ft.ScrollMode.AUTO),
            padding=20,
            height=600,  # Make it taller    
            ),
        )
    
        self.page.overlay.append(bs)
        bs.open = True
        self.page.update()
    
    def _close_dialog(self):
        # print("DEBUG: Closing dialog")
        if self.page.dialog:
            self.page.dialog.open = False
            self.page.update()
            
    # ------------------------------------------------------------
    # BACKEND MESSAGE HANDLER
    # ------------------------------------------------------------
    def _on_backend_msg(self, msg: dict):
        #print(f"DEBUG UI: Received message: {msg}")  # ADD THIS LINE
        if not isinstance(msg, dict):
            return

        mtype = msg.get("type")

        if mtype == "status":
            self.set_status(msg.get("data", ""))
            return

        if mtype == "spot":
            spot = msg.get("data", {})

            prefix = self._extract_prefix(spot.get("call", ""))
            if prefix in self.blocked_prefixes:
                return

            self.recent_spot_times.append(time.time())
            self.table.add_spot(spot)
            return
        
        # Forward cluster_command messages to backend
        if mtype == "cluster_command":
            from backend.cluster_async import command_queue
            cmd = msg.get("data", "")
            if cmd:
                try:
                    command_queue.put_nowait(cmd)
                except:
                    pass

    # ------------------------------------------------------------
    # FILTERS
    # ------------------------------------------------------------
    def _filters_changed(self, e=None):
        # Get selected bands
        selected_bands = []
        for band, cb in self.band_checkboxes.items():
            if cb.value:
                selected_bands.append(band)
        
        # If no bands selected, show nothing (or could default to all)
        if not selected_bands:
            selected_bands = []  # Empty list means show nothing
        
        self.table.set_filters(
            bands=selected_bands,
            grid=self.grid_field.value,
            dxcc=self.dxcc_field.value,
        )

    @staticmethod
    def _extract_prefix(call: str) -> str:
        call = call.upper()
        if "/" in call:
            call = call.split("/")[0]
        prefix = ""
        for ch in call:
            if ch.isalnum():
                prefix += ch
            else:
                break
        return prefix

    # ------------------------------------------------------------
    # SOLAR DATA
    # ------------------------------------------------------------
    async def _fetch_solar_data_once(self):
        """Fetch solar data on startup"""
        await asyncio.sleep(2)  # Wait for UI to load
        fetch_solar_data()
        self._update_solar_display()
        
        # Start periodic updates (every 15 minutes)
        self.page.run_task(self._solar_update_timer)
    
    async def _solar_update_timer(self):
        """Update solar data every 15 minutes"""
        while True:
            await asyncio.sleep(900)  # 15 minutes
            fetch_solar_data()
            self._update_solar_display()
    
    def _update_solar_display(self):
        """Update solar data in status bar"""
        data = get_solar_data()
        self.set_solar(data['sfi'], data['k'], data['a'])
    
    # ------------------------------------------------------------
    # SPOT RATE TIMER
    # ------------------------------------------------------------
    async def _spot_rate_timer(self):
        while True:
            now = time.time()
            self.recent_spot_times = [t for t in self.recent_spot_times if now - t <= 60]
            rate = len(self.recent_spot_times)
            self.set_rate(f"{rate}/min")
            await asyncio.sleep(10)
