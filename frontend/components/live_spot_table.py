import flet as ft

class LiveSpotTable(ft.Column):
    """Live DX spot table with basic filters."""

    def __init__(self):
        super().__init__()

        self.spots: list[dict] = []
        self.filter_band: str = "ALL"
        self.filter_grid: str = ""
        self.filter_dxcc: str = ""
        self.max_spots: int = 500

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
        self.spots.insert(0, spot)
        if len(self.spots) > self.max_spots:
            self.spots = self.spots[: self.max_spots]
        self._rebuild_rows()

    # ---------------------------------------------------
    def set_filters(self, band: str, grid: str, dxcc: str):
        self.filter_band = (band or "ALL").upper()
        self.filter_grid = (grid or "").upper()
        self.filter_dxcc = (dxcc or "").upper()
        self._rebuild_rows()

    # ---------------------------------------------------
    def _passes_filters(self, s: dict) -> bool:
        band = str(s.get("band", "")).upper()
        grid = str(s.get("grid", "")).upper()
        dxcc = str(s.get("dxcc", "")).upper()

        if self.filter_band != "ALL" and band != self.filter_band:
            return False
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

            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(s.get("time", ""))),
                        ft.DataCell(ft.Text(s.get("band", ""))),
                        ft.DataCell(ft.Text(s.get("freq", ""))),
                        ft.DataCell(ft.Text(s.get("call", ""))),
                        ft.DataCell(ft.Text(s.get("dxcc", ""))),
                        ft.DataCell(ft.Text(s.get("grid", ""))),
                        ft.DataCell(ft.Text(s.get("spotter", ""))),
                        ft.DataCell(ft.Text(s.get("comment", ""))),
                    ]
                )
            )

        self.table.rows = rows
        self.table.update()
