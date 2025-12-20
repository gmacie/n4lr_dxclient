import flet as ft

PREFIXES = [
    "K","W","N","AA","AB","AC","AD","AE",
    "VE","VA","VO","VY",
    "JA","JR","JE","JH","JI",
    "VK","VL",
    "ZS",
    "G","M",
    "DL",
    "F",
    "I",
    "EA","EB","EC",
    "CT","CU",
    "PY","PP","PQ","PR","PS","PT",
    "LU","LW",
    "LZ",
    "XE",
    "ZL",
    "OH","OG","OF",
    "SM","7S","8S",
    "SP",
    "ON","OT",
    "PA","PB","PC","PD","PE","PF","PG","PH","PI",
    "OE",
    "OK",
    "OM",
    "UR",
]


class PrefixFilterWindow:
    """
    Scrollable popup dialog for prefix exclusions.
    Fully compatible with Flet 0.28+.
    """

    def __init__(self, page: ft.Page, on_apply, initial_blocked=None):
        self.page = page
        self.on_apply = on_apply
        self.blocked = set(initial_blocked or [])
        self.checkboxes = {}

        # Build checkbox list
        checkbox_controls = []
        for p in PREFIXES:
            cb = ft.Checkbox(label=p, value=(p in self.blocked))
            self.checkboxes[p] = cb
            checkbox_controls.append(cb)

        # Scrollable list
        scroll_area = ft.ListView(
            controls=checkbox_controls,
            spacing=4,
            expand=True,
        )

        # Dialog content container
        dialog_content = ft.Container(
            content=ft.Column(
                [scroll_area],
                expand=True,
            ),
            width=350,
            height=500,
            padding=10,
        )

        # Build dialog
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("DXCC Prefix Filters"),
            content=dialog_content,
            actions=[
                ft.TextButton("Cancel", on_click=self._cancel),
                ft.TextButton("Apply", on_click=self._apply),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    # ----------------------------------------------------------
    # OPEN THE WINDOW
    # ----------------------------------------------------------
    def open(self):
        # Flet 0.28+: dialogs MUST be mounted via page.overlay
        if self.dialog not in self.page.overlay:
            self.page.overlay.append(self.dialog)

        self.dialog.open = True
        self.page.update()

    # ----------------------------------------------------------
    def _apply(self, e):
        selected = {p for p, cb in self.checkboxes.items() if cb.value}
        self.on_apply(selected)
        self.dialog.open = False
        self.page.update()

    # ----------------------------------------------------------
    def _cancel(self, e):
        self.dialog.open = False
        self.page.update()
