# main_ui.py 12/7/2025

import flet as ft
import asyncio
import time

from backend.message_bus import register_callback
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

        self.controls = [
            self.status_bar,
            filter_row,
            ft.Divider(),
            self.table,
        ]

        # start spot rate timer
        self.page.run_task(self._spot_rate_timer)

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
