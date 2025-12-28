# band_schedule_dialog.py - Band-specific time filter dialog
import flet as ft
from backend.message_bus import publish


class BandScheduleDialog:
    """Dialog for setting band-specific time filters"""
    
    def __init__(self, page):
        self.page = page
        
        # Band schedule data: band -> (start_time, stop_time, enabled)
        self.schedules = {
            "160m": ("2200", "1300", False),
            "80m": ("2200", "1300", False),
            "60m": ("2200", "1300", False),
            "40m": ("2200", "1300", False),
            "30m": ("", "", False),
            "20m": ("", "", False),
            "17m": ("", "", False),
            "15m": ("", "", False),
            "12m": ("", "", False),
            "10m": ("", "", False),
            "6m": ("", "", False),
        }
        
        self.band_rows = {}
        self.dialog = self._build_dialog()
    
    def _build_dialog(self):
        """Build the schedule dialog"""
        
        # Create rows for each band
        rows = []
        for band in ["160m", "80m", "60m", "40m", "30m", "20m", "17m", "15m", "12m", "10m", "6m"]:
            start_time, stop_time, enabled = self.schedules[band]
            
            enabled_cb = ft.Checkbox(value=enabled, on_change=lambda e, b=band: self._toggle_band(b, e))
            
            start_field = ft.TextField(
                value=start_time,
                hint_text="HH:MM",
                width=80,
                text_size=14,
                on_change=lambda e, b=band: self._update_start(b, e),
            )
            
            stop_field = ft.TextField(
                value=stop_time,
                hint_text="HH:MM",
                width=80,
                text_size=14,
                on_change=lambda e, b=band: self._update_stop(b, e),
            )
            
            self.band_rows[band] = {
                "enabled": enabled_cb,
                "start": start_field,
                "stop": stop_field,
            }
            
            rows.append(
                ft.Row([
                    ft.Container(ft.Text(band, size=14, weight=ft.FontWeight.BOLD), width=60),
                    enabled_cb,
                    ft.Text("Start:", size=12),
                    start_field,
                    ft.Text("Stop:", size=12),
                    stop_field,
                ], spacing=10)
            )
        
        content = ft.Column([
            ft.Text("Band Time Filters", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Text("Set time windows for each band (24-hour UTC format)", size=12, color=ft.Colors.BLUE_GREY_400),
            ft.Container(height=10),
            ft.Column(rows, spacing=8, scroll=ft.ScrollMode.AUTO, height=400),
            ft.Container(height=20),
            ft.Row([
                ft.ElevatedButton("Apply", on_click=self._apply_filters, icon=ft.Icons.CHECK),
                ft.ElevatedButton("Clear All", on_click=self._clear_all, icon=ft.Icons.CLEAR),
                ft.ElevatedButton("Close", on_click=self._close, icon=ft.Icons.CLOSE),
            ], spacing=10),
        ], scroll=ft.ScrollMode.AUTO)
        
        return ft.AlertDialog(
            title=ft.Text("⏰ Band Schedule"),
            content=ft.Container(content=content, width=500, height=600),
            modal=True,
        )
    
    def _toggle_band(self, band, e):
        """Toggle band schedule on/off"""
        start, stop, _ = self.schedules[band]
        self.schedules[band] = (start, stop, e.control.value)
    
    def _update_start(self, band, e):
        """Update start time"""
        _, stop, enabled = self.schedules[band]
        self.schedules[band] = (e.control.value, stop, enabled)
    
    def _update_stop(self, band, e):
        """Update stop time"""
        start, _, enabled = self.schedules[band]
        self.schedules[band] = (start, e.control.value, enabled)
    
    def _validate_time(self, time_str):
        """Validate HH:MM format"""
        if not time_str:
            return False
        
        parts = time_str.split(':')
        if len(parts) != 2:
            return False
        
        try:
            hour = int(parts[0])
            minute = int(parts[1])
            return 0 <= hour <= 23 and 0 <= minute <= 59
        except:
            return False
    
    def _apply_filters(self, e):
        """Send filter commands to cluster"""
        commands = []
        
        for band, (start, stop, enabled) in self.schedules.items():
            band_num = band.replace('m', '')  # "160m" -> "160"
            
            if enabled and start and stop:
                # Validate times
                if not self._validate_time(start) or not self._validate_time(stop):
                    self._show_error(f"Invalid time format for {band}. Use HH:MM (24-hour)")
                    return
                
                # Remove colons for cluster command (HH:MM -> HHMM)
                start_clean = start.replace(':', '')
                stop_clean = stop.replace(':', '')
                
                # Send filter command
                cmd = f"set/filter/{band_num} bandtime/pass {start_clean},{stop_clean}"
                commands.append(cmd)
            else:
                # Clear filter for this band
                cmd = f"set/filter/{band_num} nobandtime"
                commands.append(cmd)
        
        # Send all commands
        for cmd in commands:
            publish({"type": "cluster_command", "data": cmd})
            print(f"Band schedule: {cmd}")
        
        self._show_success(f"Applied {len([s for s in self.schedules.values() if s[2]])} band time filters")
        self._close(None)
    
    def _clear_all(self, e):
        """Clear all time filters"""
        for band in self.schedules:
            band_num = band.replace('m', '')
            cmd = f"set/filter/{band_num} nobandtime"
            publish({"type": "cluster_command", "data": cmd})
        
        # Reset UI
        for band in self.schedules:
            self.schedules[band] = ("", "", False)
            self.band_rows[band]["start"].value = ""
            self.band_rows[band]["stop"].value = ""
            self.band_rows[band]["enabled"].value = False
        
        try:
            for band in self.band_rows:
                self.band_rows[band]["start"].update()
                self.band_rows[band]["stop"].update()
                self.band_rows[band]["enabled"].update()
        except:
            pass
        
        self._show_success("Cleared all band time filters")
    
    def _close(self, e):
        """Close dialog"""
        self.dialog.open = False
        try:
            self.page.update()
        except:
            pass
    
    def _show_error(self, message):
        """Show error message"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED_400,
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def _show_success(self, message):
        """Show success message"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.GREEN_400,
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def show(self):
        """Show the dialog"""
        self.page.overlay.append(self.dialog)
        self.dialog.open = True
        self.page.update()
