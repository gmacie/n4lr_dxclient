import flet as ft
from backend.message_bus import init_pubsub
from backend.cluster_async import run_cluster_monitor
from frontend.main_ui import MainUI


def main(page: ft.Page):

    # Initialize pubsub
    init_pubsub(page)

    # Make dialog available for prefix filters
    page.dialog = ft.AlertDialog(modal=True)

    # Drawer must exist before UI loads
    page.drawer = ft.NavigationDrawer(controls=[])

    page.theme_mode = ft.ThemeMode.LIGHT

    # --------------------------------------------------
    # Start backend monitor as a MANAGED background task
    # --------------------------------------------------
    # IMPORTANT: pass function, NOT coroutine!
    task = page.run_task(run_cluster_monitor)

    # Cancel background task when session closes
    def on_disconnect(e):
        try:
            task.cancel()
        except:
            pass

    page.on_disconnect = on_disconnect

    # Build UI
    ui = MainUI(page)
    page.add(ui)


if __name__ == "__main__":
    ft.app(target=main)
