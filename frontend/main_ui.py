# main_ui.py 12/20/2025

import flet as ft
import asyncio
import time

from backend.message_bus import register_callback, publish
from frontend.components.status_bar import build_status_bar
from frontend.components.live_spot_table import LiveSpotTable
from frontend.components.prefix_filter_window import PrefixFilterWindow


class MainUI(ft.Column):
    """Main N4LR DX monitor UI."""

    def __init__(self, page: ft.Page):
        super().__init__(expand=True)
        self.page = page

        self.blocked_prefixes: set[str] = set()
        self.recent_spot_times: list[float] = []
        self.prefix_filter_window: PrefixFilterWindow | None = None

        # hook pubsub callback
        register_callback(self._on_backend_msg)
        if self.page.pubsub:
            self.page.pubsub.subscribe(self._on_backend_msg)

        # status bar
        self.status_bar, self.set_status, self.set_rate = build_status_bar()

        # spot table
        self.table = LiveSpotTable()

        # filters
        self.band_dropdown = ft.Dropdown(
            label="Band",
            width=120,
            value="ALL",
            options=[
                ft.dropdown.Option("ALL"),
                ft.dropdown.Option("160m"),
                ft.dropdown.Option("80m"),
                ft.dropdown.Option("60m"),
                ft.dropdown.Option("40m"),
                ft.dropdown.Option("30m"),
                ft.dropdown.Option("20m"),
                ft.dropdown.Option("17m"),
                ft.dropdown.Option("15m"),
                ft.dropdown.Option("12m"),
                ft.dropdown.Option("10m"),
                ft.dropdown.Option("6m"),
            ],
            on_change=self._filters_changed,
        )

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

        self.prefix_button = ft.IconButton(
            icon=ft.Icons.FILTER_LIST,
            tooltip="DXCC Prefix Filters",
            on_click=self._open_prefix_window,
        )

        filter_row = ft.Row(
            [
                ft.Text("Filters:", weight=ft.FontWeight.BOLD),
                self.band_dropdown,
                self.grid_field,
                self.dxcc_field,
                self.prefix_button,
            ],
            spacing=20,
        )

        # Command input
        self.command_field = ft.TextField(
            label="Cluster Command",
            hint_text="e.g., set/filter doc/pass k,ve",
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

        self.controls = [
            self.status_bar,
            filter_row,
            command_row,
            ft.Divider(),
            self.table,
        ]

        # start spot rate timer
        self.page.run_task(self._spot_rate_timer)

    # ------------------------------------------------------------
    # COMMAND HANDLING
    # ------------------------------------------------------------
    def _send_command(self, e):
        """Send command to cluster"""
        cmd = self.command_field.value.strip()   
        #print(f"DEBUG: _send_command called with: '{cmd}'")  # <-- ADD THIS
        if not cmd:
            #print("DEBUG: Command was empty!")  # <-- ADD THIS
            return
    
        # Publish command to backend via message bus
        #print(f"DEBUG: Publishing command: {cmd}")  # <-- ADD THIS
        publish({"type": "cluster_command", "data": cmd})
    
        # Clear the field
        self.command_field.value = ""
        self.command_field.update()
        #print("DEBUG: Command sent and field cleared")  # <-- ADD THIS

    def _show_command_help(self, e):
        """Show dialog with common commands"""
        #print("DEBUG: Help button clicked!")  # <-- ADD THIS
        help_text = """Common VE7CC Cluster Commands:

FILTERS (reduce spot volume):
  set/filter doc/pass k,ve        - Only spots from US/Canada
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

        dialog = ft.AlertDialog(
            title=ft.Text("Cluster Commands"),
            content=ft.Container(
                content=ft.Text(help_text, selectable=True),
                width=600,
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda _: self._close_dialog()),
            ],
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def _close_dialog(self):
        #print("DEBUG: Closing dialog")  # <-- ADD THIS
        if self.page.dialog:
            self.page.dialog.open = False
            self.page.update()

    # ------------------------------------------------------------
    # BACKEND MESSAGE HANDLER
    # ------------------------------------------------------------
    def _on_backend_msg(self, msg: dict):
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

    # ------------------------------------------------------------
    # FILTERS
    # ------------------------------------------------------------
    def _filters_changed(self, e=None):
        self.table.set_filters(
            band=self.band_dropdown.value,
            grid=self.grid_field.value,
            dxcc=self.dxcc_field.value,
        )

    # ------------------------------------------------------------
    # PREFIX WINDOW
    # ------------------------------------------------------------
    def _open_prefix_window(self, e):
        if not self.prefix_filter_window:
            self.prefix_filter_window = PrefixFilterWindow(
                page=self.page,
                on_apply=self._apply_prefix_filter,
                initial_blocked=self.blocked_prefixes,
            )
        self.prefix_filter_window.open()

    def _apply_prefix_filter(self, prefixes: set[str]):
        self.blocked_prefixes = prefixes
        self._filters_changed()

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
    # SPOT RATE TIMER
    # ------------------------------------------------------------
    async def _spot_rate_timer(self):
        while True:
            now = time.time()
            self.recent_spot_times = [t for t in self.recent_spot_times if now - t <= 60]
            rate = len(self.recent_spot_times)
            self.set_rate(f"{rate}/min")
            await asyncio.sleep(10)
