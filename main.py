#!/usr/bin/env python3
"""
N4LR DX Client - Main entry point
"""

import flet as ft
import sys

from backend.message_bus import init_pubsub

# Add src folder to path so we can import app modules
sys.path.insert(0, ".")

from frontend.main_ui import MainUI
from backend.cluster_async import start_connection
from backend.config import get_auto_connect


def main(page: ft.Page):
    """Main entry point for Flet app"""
    
    # Configure page
    page.title = "N4LR DX Client"
    page.window.width = 1400
    page.window.height = 900
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 10
    
    # Initialize message bus FIRST
    init_pubsub(page)  # <-- DO YOU HAVE THIS LINE?
    
    # Create main UI (it will auto-connect if configured)
    ui = MainUI(page)
    page.add(ui)


if __name__ == "__main__":
    ft.app(target=main)
