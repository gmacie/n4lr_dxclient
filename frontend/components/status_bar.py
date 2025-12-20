import flet as ft

def build_status_bar():
    backend_status = ft.Text("Backend: Idle", size=12, color=ft.Colors.YELLOW_700)
    cluster_status = ft.Text("Cluster: Disconnected", size=12, color=ft.Colors.RED_500)
    spot_rate = ft.Text("Rate: 0/min", size=12, color=ft.Colors.CYAN_400)

    bar = ft.Container(
        content=ft.Row(
            [
                backend_status,
                ft.VerticalDivider(),
                cluster_status,
                ft.VerticalDivider(),
                spot_rate,
            ],
            spacing=15,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=8,
        bgcolor=ft.Colors.BLACK12,
    )

    def set_status(text: str | None):
        backend_status.value = text or ""
        t = (text or "").lower()

        if "connected" in t:
            cluster_status.value = "Cluster: Connected"
            cluster_status.color = ft.Colors.GREEN_400
        elif "connecting" in t:
            cluster_status.value = "Cluster: Connecting..."
            cluster_status.color = ft.Colors.AMBER_300
        elif "lost" in t or "retrying" in t:
            cluster_status.value = "Cluster: Disconnected"
            cluster_status.color = ft.Colors.RED_500

        backend_status.update()
        cluster_status.update()

    def set_rate(text: str):
        spot_rate.value = f"Rate: {text}"
        spot_rate.update()

    return bar, set_status, set_rate
