# status_bar.py - Status bar with cluster status and sun times
import flet as ft
from backend.sun_times import format_sun_times


def build_status_bar(grid_square="EM50"):
    """
    Build status bar with cluster connection status and sunrise/sunset times.
    
    Args:
        grid_square: User's grid square for sun calculations
    
    Returns:
        (status_bar_row, set_status_func, set_rate_func, set_grid_func)
    """
    
    # Calculate initial sun times
    sun_times = format_sun_times(grid_square)
    
    # Status label
    status_label = ft.Text(
        "Cluster: Connecting...",
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.ORANGE,
    )
    
    # Rate label
    rate_label = ft.Text(
        "Rate: 0/min",
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.GREEN,
    )
    
    # Command status label (for "Sent: ..." messages)
    command_label = ft.Text(
        "",
        size=14,
        color=ft.Colors.BLUE_500,
        italic=True,
    )
    
    # Solar data label (SFI, K, A)
    solar_label = ft.Text(
        "SFI:— A:— K:—",
        size=14,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.ORANGE_400,
    )
    
    # Sun times label
    sun_label = ft.Text(
        f"🌅 {sun_times['sunrise']} | 🌇 {sun_times['sunset']}",
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.BLUE_400,
    )
    
    # Build status bar row
    status_bar = ft.Row(
        [
            status_label,
            ft.Container(width=20),
            rate_label,
            ft.Container(width=20),
            command_label,
            ft.Container(expand=True),  # Spacer
            solar_label,
            ft.Container(width=20),
            sun_label,
        ],
        spacing=10,
    )
    
    def set_status(text: str):
        """Update cluster status text and color"""
        # If it's a "Sent: ..." message, put it in the command label
        if text.startswith("Sent:"):
            command_label.value = text
            try:
                command_label.update()
            except:
                pass
            return
        
        # Otherwise it's a cluster status message
        status_label.value = f"Cluster: {text}"
        
        # Color based on status
        if "connected" in text.lower():
            status_label.color = ft.Colors.GREEN
        elif "lost" in text.lower() or "retrying" in text.lower():
            status_label.color = ft.Colors.RED
        else:
            status_label.color = ft.Colors.ORANGE
        
        try:
            status_label.update()
        except:
            pass  # Control not yet added to page
    
    def set_rate(rate_text: str):
        """Update spot rate"""
        rate_label.value = f"Rate: {rate_text}"
        try:
            rate_label.update()
        except:
            pass  # Control not yet added to page
    
    def set_grid(new_grid: str):
        """Update grid square and recalculate sun times"""
        sun_times = format_sun_times(new_grid)
        sun_label.value = f"🌅 {sun_times['sunrise']} | 🌇 {sun_times['sunset']}"
        try:
            sun_label.update()
        except:
            pass  # Control not yet added to page
    
    def set_solar(sfi, a, k):
        """Update solar indices (SFI, K-index, A-index)"""
        solar_label.value = f"SFI:{sfi} A:{a} K:{k}"
        try:
            solar_label.update()
        except:
            pass  # Control not yet added to page
    
    return status_bar, set_status, set_rate, set_grid, set_solar
