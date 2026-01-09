# band_schedule_dialog.py - Band-specific time filter dialog
# 01/06/2026 - Added logging and config persistence

from backend.app_logging import get_logger

logger = get_logger(__name__)

import flet as ft
from backend.message_bus import publish


class BandScheduleDialog:
    """Dialog for setting band-specific time filters"""
    
    def __init__(self, page):
        self.page = page
        
        # Load saved schedules from config
        self.schedules = self._load_schedules()
        
        self.band_rows = {}
        self.dialog = self._build_dialog()
    
    def _load_schedules(self):
        """Load band schedules from config"""
        from backend.config import load_config
        
        config = load_config()
        schedules = {}
        
        # Default values for low bands
        defaults = {
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
        
        for band in ["160m", "80m", "60m", "40m", "30m", "20m", "17m", "15m", "12m", "10m", "6m"]:
            start = config.get('band_schedule', f'{band}_start', fallback=defaults[band][0])
            stop = config.get('band_schedule', f'{band}_stop', fallback=defaults[band][1])
            enabled = config.getboolean('band_schedule', f'{band}_enabled', fallback=defaults[band][2])
            schedules[band] = (start, stop, enabled)
        
        return schedules
    
    def _save_schedules(self):
        """Save band schedules to config"""
        from backend.config import load_config, save_config
        
        config = load_config()
        if 'band_schedule' not in config:
            config['band_schedule'] = {}
        
        for band, (start, stop, enabled) in self.schedules.items():
            config['band_schedule'][f'{band}_start'] = start
            config['band_schedule'][f'{band}_stop'] = stop
            config['band_schedule'][f'{band}_enabled'] = str(enabled)
        
        save_config(config)
        logger.info("BAND SCHEDULE → Saved to config.ini")
    
    def _build_dialog(self):
        """Build the schedule dialog"""
        
        # Create rows for each band
        rows = []
        for band in ["160m", "80m", "60m", "40m", "30m", "20m", "17m", "15m", "12m", "10m", "6m"]:
            start_time, stop_time, enabled = self.schedules[band]
            
            enabled_cb = ft.Checkbox(value=enabled, on_change=lambda e, b=band: self._toggle_band(b, e))
            
            start_field = ft.TextField(
                value=start_time,
                hint_text="HHMM",
                width=80,
                text_size=14,
                on_change=lambda e, b=band: self._update_start(b, e),
            )
            
            stop_field = ft.TextField(
                value=stop_time,
                hint_text="HHMM",
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
            ft.Text("Set time windows for each band (24-hour UTC format: HHMM)", size=12, color=ft.Colors.BLUE_GREY_400),
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
        """Validate HHMM format (also accepts HH:MM)"""
        if not time_str:
            return False
        
        # Remove colon if present
        time_str = time_str.replace(':', '')
        
        # Should be 4 digits
        if len(time_str) != 4:
            return False
        
        try:
            hour = int(time_str[:2])
            minute = int(time_str[2:])
            return 0 <= hour <= 23 and 0 <= minute <= 59
        except:
            return False
    
    def _apply_filters(self, e):
        """Send filter commands to cluster"""
        logger.info("BAND SCHEDULE → Applying time filters")
        
        commands = []
        enabled_count = 0
        
        for band, (start, stop, enabled) in self.schedules.items():
            band_num = band.replace('m', '')  # "160m" -> "160"
            
            if enabled and start and stop:
                # Validate times
                if not self._validate_time(start) or not self._validate_time(stop):
                    self._show_error(f"Invalid time format for {band}. Use HHMM (e.g., 2200)")
                    logger.error(f"BAND SCHEDULE ✗ Invalid time format: {band} {start}-{stop}")
                    return
                
                # Remove colons for cluster command (HH:MM -> HHMM)
                start_clean = start.replace(':', '')
                stop_clean = stop.replace(':', '')
                
                # Send filter command
                cmd = f"set/filter/{band_num} bandtime/pass {start_clean},{stop_clean}"
                commands.append(cmd)
                enabled_count += 1
                logger.info(f"  {band}: ENABLED {start_clean}-{stop_clean} → {cmd}")
            else:
                # Clear filter for this band
                cmd = f"set/filter/{band_num} nobandtime"
                commands.append(cmd)
                logger.info(f"  {band}: DISABLED → {cmd}")
        
        logger.info(f"BAND SCHEDULE → Sending {len(commands)} commands ({enabled_count} enabled)")
        
        # Send all commands
        for cmd in commands:
            publish({"type": "cluster_command", "data": cmd})
        
        # Save to config
        self._save_schedules()
        
        logger.info(f"BAND SCHEDULE ✓ Applied {enabled_count} enabled filters")
        
        self._show_success(f"Applied {enabled_count} band time filter(s)")
        self._close(None)
    
    def _clear_all(self, e):
        """Clear all time filters"""
        logger.info("BAND SCHEDULE → Clearing all filters")
        
        for band in self.schedules:
            band_num = band.replace('m', '')
            cmd = f"set/filter/{band_num} nobandtime"
            logger.info(f"  {band}: CLEARING → {cmd}")
            publish({"type": "cluster_command", "data": cmd})
        
        # Reset UI and schedules
        for band in self.schedules:
            self.schedules[band] = ("", "", False)
            self.band_rows[band]["start"].value = ""
            self.band_rows[band]["stop"].value = ""
            self.band_rows[band]["enabled"].value = False
        
        # Save cleared state
        self._save_schedules()
        
        try:
            for band in self.band_rows:
                self.band_rows[band]["start"].update()
                self.band_rows[band]["stop"].update()
                self.band_rows[band]["enabled"].update()
        except:
            pass
        
        logger.info("BAND SCHEDULE ✓ Cleared all filters")
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