# status_bar.py - Status bar with cluster status and sun times with countdown
import flet as ft
from backend.sun_times import format_sun_times, get_sun_times
from datetime import datetime, timedelta


def build_status_bar(grid_square="EM50"):
    """
    Build status bar with cluster connection status and sunrise/sunset times with countdown.
    
    Args:
        grid_square: User's grid square for sun calculations
    
    Returns:
        (status_bar_row, set_status_func, set_rate_func, set_grid_func, set_solar_func)
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
    
    # Sun times with larger icons
    sun_label = ft.Row([
        ft.Icon(ft.Icons.WB_SUNNY, size=20, color=ft.Colors.ORANGE_300),
        ft.Text(sun_times['sunrise'], size=14, color=ft.Colors.ORANGE_200),
        ft.Icon(ft.Icons.NIGHTLIGHT, size=20, color=ft.Colors.INDIGO_300),
        ft.Text(sun_times['sunset'], size=14, color=ft.Colors.INDIGO_200),
    ], spacing=5)
    
    # Countdown label
    countdown_label = ft.Text(
        "",
        size=13,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.YELLOW_300,
    )
    
    # Calculate initial countdown
    _update_countdown(grid_square, countdown_label)
    
    # Solar data label (SFI, K, A)
    solar_label = ft.Text(
        "SFI:— A:— K:—",
        size=14,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.ORANGE_400,
    )
    
    # Build status bar row (sun times BEFORE solar data)
    status_bar = ft.Row(
        [
            status_label,
            ft.Container(width=20),
            rate_label,
            ft.Container(width=20),
            command_label,
            ft.Container(expand=True),  # Spacer
            sun_label,
            countdown_label,
            ft.Container(width=20),
            solar_label,
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
            pass
    
    def set_rate(rate_text: str):
        """Update spot rate"""
        rate_label.value = f"Rate: {rate_text}"
        try:
            rate_label.update()
        except:
            pass
    
    def set_grid(new_grid: str):
        """Update grid square and recalculate sun times"""
        sun_times = format_sun_times(new_grid)
        
        # Update sun time row contents
        sun_label.controls[1].value = sun_times['sunrise']
        sun_label.controls[3].value = sun_times['sunset']
        
        # Update countdown
        _update_countdown(new_grid, countdown_label)
        
        try:
            sun_label.update()
            countdown_label.update()
        except:
            pass
    
    def set_solar(sfi, a, k):
        """Update solar indices (SFI, K-index, A-index)"""
        solar_label.value = f"SFI:{sfi} A:{a} K:{k}"
        try:
            solar_label.update()
        except:
            pass
    
    return status_bar, set_status, set_rate, set_grid, set_solar


def _update_countdown(grid_square: str, countdown_widget: ft.Text):
    """Calculate and update countdown to next sunrise or sunset"""
    try:
        # Get sun times with full data
        sun_data = get_sun_times(grid_square)
        
        if not sun_data or 'sunrise' not in sun_data:
            countdown_widget.value = ""
            return
        
        # Get current time
        now = datetime.now()
        
        # Get sunrise and sunset (might be datetime objects or strings)
        sunrise_val = sun_data.get('sunrise', '')
        sunset_val = sun_data.get('sunset', '')
        
        # Handle datetime objects
        if isinstance(sunrise_val, datetime):
            sunrise_today = sunrise_val
        elif isinstance(sunrise_val, str) and sunrise_val and sunrise_val != '--:--':
            sunrise_parts = sunrise_val.split(':')
            sunrise_today = now.replace(
                hour=int(sunrise_parts[0]),
                minute=int(sunrise_parts[1]),
                second=0,
                microsecond=0
            )
        else:
            countdown_widget.value = ""
            return
        
        if isinstance(sunset_val, datetime):
            sunset_today = sunset_val
        elif isinstance(sunset_val, str) and sunset_val and sunset_val != '--:--':
            sunset_parts = sunset_val.split(':')
            sunset_today = now.replace(
                hour=int(sunset_parts[0]),
                minute=int(sunset_parts[1]),
                second=0,
                microsecond=0
            )
        else:
            countdown_widget.value = ""
            return
            
        # Remove timezone info to compare with naive datetime (ADD THIS)
        if sunrise_today.tzinfo is not None:
            sunrise_today = sunrise_today.replace(tzinfo=None)
        if sunset_today.tzinfo is not None:
            sunset_today = sunset_today.replace(tzinfo=None)
                
        # Determine which event is next
        if now < sunrise_today:
            # Before sunrise - countdown to sunrise
            delta = sunrise_today - now
            event = "Sunrise"
            color = ft.Colors.ORANGE_300
        elif now < sunset_today:
            # After sunrise, before sunset - countdown to sunset
            delta = sunset_today - now
            event = "Sunset"
            color = ft.Colors.INDIGO_300
        else:
            # After sunset - countdown to tomorrow's sunrise
            sunrise_tomorrow = sunrise_today + timedelta(days=1)
            delta = sunrise_tomorrow - now
            event = "Sunrise"
            color = ft.Colors.ORANGE_300
        
        # Format countdown
        hours = int(delta.total_seconds() // 3600)
        minutes = int((delta.total_seconds() % 3600) // 60)
        
        if hours > 0:
            countdown_widget.value = f"({event} in {hours}h {minutes}m)"
        else:
            countdown_widget.value = f"({event} in {minutes}m)"
        
        countdown_widget.color = color
        
    except Exception as e:
        print(f"Error calculating countdown: {e}")
        countdown_widget.value = ""


def update_countdown(status_bar_row, grid_square: str):
    """
    Update the countdown timer (call this periodically from main_ui timer)
    
    Args:
        status_bar_row: The status bar Row widget
        grid_square: Current grid square
    """
    try:
        # The countdown label is at index 7 in the row
        if isinstance(status_bar_row, ft.Row) and len(status_bar_row.controls) >= 8:
            countdown_widget = status_bar_row.controls[7]
            _update_countdown(grid_square, countdown_widget)
            countdown_widget.update()
    except Exception as e:
        print(f"Error updating countdown: {e}")