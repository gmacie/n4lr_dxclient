# settings_tab.py - Settings configuration with cluster controls
import flet as ft
import asyncio

from backend.config import (
    get_user_callsign, get_user_grid, set_user_settings,
    get_cluster_servers, get_current_server, set_current_server,
    get_auto_connect, set_auto_connect,
    get_blocked_spotters, set_blocked_spotters
)
from backend.grid_utils import validate_grid
from backend.cluster_async import start_connection, stop_connection


class SettingsTab(ft.Column):
    """Settings tab for user configuration and cluster controls"""
    
    def __init__(self, page, on_settings_changed, initial_connection_state=False, challenge_table=None, ffma_table=None):
        super().__init__()
        self.page = page
        self.on_settings_changed = on_settings_changed
        self.is_connected = initial_connection_state  # Set based on auto-connect
        self.challenge_table = challenge_table  # Store reference for auto-refresh
        self.ffma_table = ffma_table  # Store FFMA table reference
        
        # User settings section
        self.callsign_field = ft.TextField(
            label="Callsign",
            hint_text="e.g., N4LR or N4LR-14",
            value=get_user_callsign(),
            width=200,
        )
        
        self.grid_field = ft.TextField(
            label="Grid Square",
            hint_text="e.g., EM50",
            value=get_user_grid(),
            width=150,
            on_change=self._validate_grid_input,
        )
        
        self.grid_help = ft.Text(
            "Enter your 4 or 6-character Maidenhead grid square",
            size=12,
            color=ft.Colors.BLUE_GREY_400,
        )
        
        self.save_button = ft.ElevatedButton(
            text="Save Settings",
            on_click=self._save_settings,
        )
        
        # Cluster server controls section
        servers = get_cluster_servers()
        current = get_current_server()
        
        self.server_dropdown = ft.Dropdown(
            label="Cluster Server",
            options=[ft.dropdown.Option(s) for s in servers],
            value=current,
            width=300,
            on_change=self._server_changed,
        )
        
        self.connect_button = ft.ElevatedButton(
            text="Disconnect" if initial_connection_state else "Connect",
            icon=ft.Icons.LINK_OFF if initial_connection_state else ft.Icons.LINK,
            on_click=self._toggle_connection,
        )
        
        self.auto_connect_checkbox = ft.Checkbox(
            label="Auto-connect on startup",
            value=get_auto_connect(),
            on_change=self._auto_connect_changed,
        )
        
        # Display settings section
        from backend.config import get_needed_spot_minutes
        self.needed_spot_slider = ft.Slider(
            min=5,
            max=60,
            divisions=11,  # 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60
            value=get_needed_spot_minutes(),
            label="{value} min",
            on_change=self._needed_spot_duration_changed,
            width=400,
        )
        
        self.needed_spot_label = ft.Text(
            f"Keep needed (amber) spots visible for: {get_needed_spot_minutes()} minutes",
            size=14,
        )
        
        self.needed_spot_label = ft.Text(
            f"Keep needed (amber) spots visible for: {get_needed_spot_minutes()} minutes",
            size=14,
        )
        
        # Grid chasing toggle
        from backend.config import get_grid_chasing_enabled
        self.grid_chasing_checkbox = ft.Checkbox(
            label="Enable grid chasing (amber highlights for rare grids)",
            value=get_grid_chasing_enabled(),
            on_change=self._grid_chasing_changed,
        )
        
        # Blocked spotters section
        blocked = get_blocked_spotters()
        self.blocked_spotters_field = ft.TextField(
            label="Blocked Spotters",
            hint_text="Enter callsigns separated by commas (e.g., RBN,K3LR-2,DX-SKIMMER)",
            value=', '.join(blocked) if blocked else '',
            width=500,
        )
        
        self.blocked_count_text = ft.Text(
            f"Currently blocking {len(blocked)} spotter(s)",
            size=12,
            color=ft.Colors.BLUE_GREY_400,
        )
        
        self.save_blocked_button = ft.ElevatedButton(
            text="Save Blocked List",
            on_click=self._save_blocked_spotters,
        )
        
        self.clear_blocked_button = ft.ElevatedButton(
            text="Clear All",
            on_click=self._clear_blocked_spotters,
        )
        
        # Watch List section
        from backend.config import get_watch_list
        watch_list = get_watch_list()
        
        self.watch_list_field = ft.TextField(
            label="Watch List",
            hint_text="Enter callsigns separated by commas (e.g., K1ABC,W2XYZ,VE3DXE)",
            value=', '.join(watch_list) if watch_list else '',
            width=500,
        )
        
        self.watch_count_text = ft.Text(
            f"Watching {len(watch_list)} callsign(s)",
            size=12,
            color=ft.Colors.BLUE_GREY_400,
        )
        
        self.save_watch_button = ft.ElevatedButton(
            text="Save Watch List",
            on_click=self._save_watch_list,
        )
        
        self.clear_watch_button = ft.ElevatedButton(
            text="Clear All",
            on_click=self._clear_watch_list,
        )
        
        # LoTW Users Database section
        from backend.lotw_users import get_cache_age_days, get_user_count
            
        cache_age = get_cache_age_days()
        user_count = get_user_count()
           
        if cache_age is not None:
            age_text = f"{cache_age} days old"
            age_color = ft.Colors.ORANGE if cache_age > 7 else ft.Colors.GREEN
        else:
            age_text = "No cache"
            age_color = ft.Colors.RED
            
        self.lotw_cache_text = ft.Text(
            f"LoTW Users: {user_count:,} ({age_text})",
            size=14,
            color=age_color,
        )
            
        self.lotw_update_button = ft.ElevatedButton(
            text="Update LoTW Users",
            on_click=self._update_lotw_users,
            icon=ft.Icons.DOWNLOAD,
        )
        
        # LoTW credentials section
        from backend.config import get_lotw_username, get_lotw_password, get_last_vucc_update
        
        # LoTW credentials section
        from backend.secure_credentials import get_lotw_credentials
        
        username, password = get_lotw_credentials()
        
        self.lotw_username_field = ft.TextField(
            label="LoTW Username",
            hint_text="Usually your callsign",
            value=username or "",
            width=200,
        )
        
        self.lotw_password_field = ft.TextField(
            label="LoTW Password",
            hint_text="Your LoTW password",
            value=password or "",
            password=True,
            can_reveal_password=True,
            width=200,
        )
        
        self.lotw_save_button = ft.ElevatedButton(
            text="Save Credentials",
            on_click=self._save_lotw_credentials,
        )
        
        self.lotw_download_button = ft.ElevatedButton(
            text="Download VUCC Data",
            icon=ft.Icons.DOWNLOAD,
            on_click=self._download_vucc_data,
        )
        
        last_update = get_last_vucc_update()
        self.lotw_status_text = ft.Text(
            f"Last updated: {last_update if last_update else 'Never'}",
            size=12,
            color=ft.Colors.BLUE_GREY_400,
        )
        
        # Challenge data download section
        from backend.config import get_last_challenge_update
        
        self.challenge_download_button = ft.ElevatedButton(
            text="Download Challenge Data",
            icon=ft.Icons.DOWNLOAD,
            on_click=self._download_challenge_data,
        )
        
        last_challenge_update = get_last_challenge_update()
        self.challenge_status_text = ft.Text(
            f"Last updated: {last_challenge_update if last_challenge_update else 'Never'}",
            size=12,
            color=ft.Colors.BLUE_GREY_400,
        )
        
        # Build layout
        self.controls = [
            ft.Text("User Settings", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            
            ft.Row([
                ft.Column([
                    self.callsign_field,
                    ft.Text(
                        "Use callsign with suffix (e.g., N4LR-14) for separate filter profiles",
                        size=12,
                        color=ft.Colors.BLUE_GREY_400,
                    ),
                ]),
                ft.Container(width=40),
                ft.Column([
                    self.grid_field,
                    self.grid_help,
                ]),
            ]),
            
            ft.Container(height=20),
            self.save_button,
            
            ft.Container(height=40),
            ft.Text("Cluster Connection", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            
            ft.Row([
                self.server_dropdown,
                self.connect_button,
            ], spacing=20),
            
            self.auto_connect_checkbox,
            
            ft.Container(height=20),
            ft.Text(
                "Note: Changing server will disconnect and reconnect",
                size=12,
                color=ft.Colors.ORANGE_400,
            ),
            
            ft.Container(height=40),
            ft.Text("Display Settings", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            
            ft.Container(height=40),
            ft.Text("Block Spotters", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            
            ft.Text(
                "Block spots from specific spotters (useful for RBN, Skimmers, or problem spotters)",
                size=12,
                color=ft.Colors.BLUE_GREY_400,
            ),
            
            ft.Container(height=10),
            
            self.blocked_spotters_field,
            self.blocked_count_text,
            
            ft.Row([
                self.save_blocked_button,
                self.clear_blocked_button,
            ], spacing=10),
            
            ft.Text(
                "Tip: Common blocks: RBN, DX-SKIMMER, or specific Skimmer callsigns like K3LR-2",
                size=12,
                color=ft.Colors.ORANGE_400,
            ),
            
            ft.Container(height=40),
            ft.Text("Watch List", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            
            ft.Text(
                "Highlight specific callsigns in RED when spotted (friends, rare DX, etc.)",
                size=12,
                color=ft.Colors.BLUE_GREY_400,
            ),
            
            ft.Container(height=10),
            
            self.watch_list_field,
            self.watch_count_text,
            
            ft.Row([
                self.save_watch_button,
                self.clear_watch_button,
            ], spacing=10),
            
            ft.Text(
                "💡 Tip: Add rare DX, friends, or targets you're hunting",
                size=12,
                color=ft.Colors.ORANGE_400,
            ),
            
            self.needed_spot_label,
            self.needed_spot_slider,
            ft.Text(
                "Needed spots (amber highlights) stay visible longer than regular spots",
                size=12,
                color=ft.Colors.BLUE_GREY_400,
            ),
            
            ft.Container(height=10),
            self.grid_chasing_checkbox,
            ft.Text(
                "When enabled, rare grids are highlighted in amber (needs 6m FFMA tracking)",
                size=12,
                color=ft.Colors.BLUE_GREY_400,
            ),
            
            ft.Container(height=40),
            ft.Text("LoTW User Database", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            
            ft.Text(
                "Updates LoTW user list and last upload dates (225k+ users)",
                size=12,
                color=ft.Colors.BLUE_GREY_400,
            ),
            
            ft.Container(height=10),
            
            self.lotw_cache_text,
            self.lotw_update_button,
            
            ft.Text(
                "Auto-updates weekly. Use button to force refresh.",
                size=12,
                color=ft.Colors.BLUE_GREY_400,
            ),
            
            ft.Container(height=40),
            ft.Text("LoTW Integration (FFMA)", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            
            ft.Text(
                "Enter your LoTW credentials to download VUCC confirmations for FFMA tracking",
                size=12,
                color=ft.Colors.BLUE_GREY_400,
            ),
            
            ft.Container(height=10),
            
            ft.Row([
                ft.Column([
                    self.lotw_username_field,
                ]),
                ft.Container(width=20),
                ft.Column([
                    self.lotw_password_field,
                ]),
            ]),
            
            ft.Container(height=10),
            
            ft.Row([
                self.lotw_save_button,
                self.lotw_download_button,
            ], spacing=10),
            
            self.lotw_status_text,
            
            
            ft.Text(
                "Credentials stored securely in Windows Credential Manager / macOS Keychain",
                size=12,
                color=ft.Colors.GREEN_400,
            ),
            ft.Text(
                "Download fetches 6m confirmations for FFMA.",
                size=12,
                color=ft.Colors.BLUE_GREY_400,
            ),
            
            ft.Container(height=40),
            ft.Text("Challenge Data (All Bands)", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            
            ft.Text(
                "Download DXCC Challenge confirmations from LoTW (includes 60m)",
                size=12,
                color=ft.Colors.BLUE_GREY_400,
            ),
            
            ft.Container(height=10),
            
            self.challenge_download_button,
            self.challenge_status_text,
            
            ft.Text(
                "Note: First download may be 15-22 MB. Subsequent updates are incremental (much smaller).",
                size=12,
                color=ft.Colors.ORANGE_400,
            ),
            
            ft.Container(height=5),
            
            ft.Text(
                "⚠️ Paper QSL cards (ARRL desk-checked) will NOT appear in LoTW downloads.",
                size=12,
                color=ft.Colors.YELLOW_600,
                italic=True,
            ),
        ]
        
        self.spacing = 10
        self.scroll = ft.ScrollMode.AUTO
    
    def _validate_grid_input(self, e):
        """Validate grid square as user types"""
        grid = self.grid_field.value.strip().upper()
        if grid and not validate_grid(grid):
            self.grid_help.value = "Invalid grid square format"
            self.grid_help.color = ft.Colors.RED_400
        else:
            self.grid_help.value = "Enter your 4 or 6-character Maidenhead grid square"
            self.grid_help.color = ft.Colors.BLUE_GREY_400
        self.grid_help.update()
    
    def _save_settings(self, e):
        """Save user settings"""
        callsign = self.callsign_field.value.strip().upper()
        grid = self.grid_field.value.strip().upper()
        
        # Validate callsign
        if not callsign:
            self._show_error("Callsign cannot be empty")
            return
        
        # Validate callsign suffix if present
        if '-' in callsign:
            suffix = callsign.split('-')[1]
            if not suffix.isdigit():
                self._show_error("Callsign suffix must be numeric (e.g., N4LR-14)")
                return
        
        # Validate grid
        if not grid:
            self._show_error("Grid square cannot be empty")
            return
        
        if not validate_grid(grid):
            self._show_error("Invalid grid square format")
            return
        
        # Save to config
        set_user_settings(callsign, grid)
        
        # Notify parent
        if self.on_settings_changed:
            self.on_settings_changed(callsign, grid)
    
    def _server_changed(self, e):
        """Handle server selection change"""
        new_server = self.server_dropdown.value
        set_current_server(new_server)
        
        # If currently connected, reconnect to new server
        if self.is_connected:
            self._reconnect_to_server(new_server)
    
    def _reconnect_to_server(self, server_str):
        """Disconnect and reconnect to new server"""
        parts = server_str.split(':')
        host = parts[0]
        port = int(parts[1]) if len(parts) > 1 else 23
        
        # Stop current connection
        stop_connection()
        
        # Start new connection after a delay
        async def delayed_reconnect():
            await asyncio.sleep(1)
            return start_connection(host, port)
        
        self.page.run_task(delayed_reconnect)
    
    def _toggle_connection(self, e):
        """Toggle cluster connection"""
        if self.is_connected:
            # Disconnect
            stop_connection()
            self.is_connected = False
            self.connect_button.text = "Connect"
            self.connect_button.icon = ft.Icons.LINK
            self.connect_button.update()
        else:
            # Connect
            server_str = self.server_dropdown.value
            parts = server_str.split(':')
            host = parts[0]
            port = int(parts[1]) if len(parts) > 1 else 23
            
            # Use page.run_task to start connection
            async def connect_task():
                await start_connection(host, port)
            
            self.page.run_task(connect_task)
            self.is_connected = True
            self.connect_button.text = "Disconnect"
            self.connect_button.icon = ft.Icons.LINK_OFF
            self.connect_button.update()
    
    def _auto_connect_changed(self, e):
        """Handle auto-connect checkbox change"""
        set_auto_connect(self.auto_connect_checkbox.value)
    
    def _needed_spot_duration_changed(self, e):
        """Handle needed spot duration slider change"""
        minutes = int(self.needed_spot_slider.value)
        self.needed_spot_label.value = f"Keep needed (amber) spots visible for: {minutes} minutes"
        self.needed_spot_label.update()
        
        # Save to config
        from backend.config import set_needed_spot_minutes
        set_needed_spot_minutes(minutes)
        
        # Notify main UI to update the spot table
        if hasattr(self.page, 'spot_table'):
            self.page.spot_table.set_needed_spot_duration(minutes)
            
    def _grid_chasing_changed(self, e):
        """Handle grid chasing checkbox change"""
        from backend.config import set_grid_chasing_enabled
        enabled = self.grid_chasing_checkbox.value
        set_grid_chasing_enabled(enabled)
        
        # Notify main UI to update the spot table
        if hasattr(self.page, 'spot_table'):
            self.page.spot_table.set_grid_chasing_enabled(enabled)
    
    def _save_lotw_credentials(self, e):
        """Save LoTW credentials to secure storage"""
        username = self.lotw_username_field.value.strip()
        password = self.lotw_password_field.value.strip()
        
        if not username or not password:
            self._show_error("Please enter both username and password")
            return
        
        from backend.secure_credentials import save_lotw_credentials
        
        success = save_lotw_credentials(username, password)
        
        if success:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("LoTW credentials saved securely to system keyring"),
                bgcolor=ft.Colors.GREEN_400,
            )
        else:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Failed to save credentials"),
                bgcolor=ft.Colors.RED_400,
            )
        
        self.page.snack_bar.open = True
        self.page.update()
    
    def _download_vucc_data(self, e):
        """Download VUCC data from LoTW with progress updates"""
        logger.info("FFMA DOWNLOAD - Starting VUCC download")
        from backend.config import get_lotw_username, get_lotw_password, set_last_vucc_update
        import threading
        
        username = get_lotw_username()
        password = get_lotw_password()
        
        if not username or not password:
            self._show_error("Please save LoTW credentials first")
            return
        
        # Show progress
        self.lotw_download_button.disabled = True
        self.lotw_download_button.text = "Downloading..."
        self.lotw_status_text.value = "Starting download..."
        self.lotw_status_text.update()
        self.lotw_download_button.update()
        
        def update_progress(message):
            self.lotw_status_text.value = message
            # Force immediate update from background thread
            if self.page:
                try:
                    import time
                    self.lotw_status_text.update()
                    time.sleep(2.0)  # Give UI time to refresh
                except:
                    pass
        
        # Run download in background thread
        def download_thread():
            try:
                from backend.lotw_vucc import download_and_parse_ffma
                from datetime import datetime
                
                success, result = download_and_parse_ffma(username, password, progress_callback=update_progress)
                
                if success:
                    # Update status
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                    set_last_vucc_update(timestamp)
                    self.lotw_status_text.value = f"Last updated: {timestamp}"
                    
                    # Show success
                    total = result.get('total_worked', 0)
                    pct = result.get('completion_pct', 0)
                    
                    self.page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"Success! {total}/488 FFMA grids ({pct}%)"),
                        bgcolor=ft.Colors.GREEN_400,
                    )
                    self.page.snack_bar.open = True
                    
                    # Auto-refresh FFMA table
                    if self.ffma_table:
                        try:
                            self.ffma_table.refresh()
                            print("FFMA table refreshed after download")
                        except Exception as e:
                            print(f"Error refreshing FFMA table: {e}")
                else:
                    self._show_error(f"Download failed: {result}")
            
            except Exception as ex:
                self._show_error(f"Error: {str(ex)}")
            
            finally:
                # Re-enable button
                self.lotw_download_button.disabled = False
                self.lotw_download_button.text = "Download VUCC Data"
                try:
                    self.page.update()
                except:
                    pass
        
        # Start thread
        thread = threading.Thread(target=download_thread, daemon=True)
        thread.start()
    
    def _download_challenge_data(self, e):
        """Download Challenge data from LoTW with progress updates"""
        from backend.config import get_lotw_username, get_lotw_password, set_last_challenge_update, get_last_challenge_update
        import threading
        
        username = get_lotw_username()
        password = get_lotw_password()
        
        if not username or not password:
            self._show_error("Please save LoTW credentials first")
            return
        
        # Show progress
        self.challenge_download_button.disabled = True
        self.challenge_download_button.text = "Downloading..."
        self.challenge_status_text.value = "Starting download..."
        self.challenge_status_text.update()
        self.challenge_download_button.update()
        
        # Progress callback to update UI
        def update_progress(message):
            self.challenge_status_text.value = message
            try:
                self.page.update()
            except:
                pass
        
        # Run download in background thread
        def download_thread():
            try:
                from backend.lotw_challenge import download_and_parse_challenge
                from backend.config import get_user_callsign
                from datetime import datetime
                
                # Get callsign for filtering
                callsign = get_user_callsign().split('-')[0]
                
                # Get last update date for incremental download
                last_update = get_last_challenge_update()
                since_date = last_update.split()[0] if last_update else None
                
                # Always start from 2000-01-01 for first download
                start_date = "2000-01-01" if not since_date else None
                
                success, result = download_and_parse_challenge(
                    username, password, since_date, start_date, callsign,
                    progress_callback=update_progress
                )
                
                if success:
                        # Update status
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                        set_last_challenge_update(timestamp)
                        self.challenge_status_text.value = f"Last updated: {timestamp}"
                    
                        # Show success
                        total_entities = result.get('total_entities', 0)
                        total_slots = result.get('total_challenge_slots', 0)
                    
                        self.page.snack_bar = ft.SnackBar(
                            content=ft.Text(f"Success! {total_entities} entities, {total_slots} slots"),
                            bgcolor=ft.Colors.GREEN_400,
                        )
                        self.page.snack_bar.open = True
                        self.page.update()
                    
                        # CRITICAL: Reload challenge data immediately
                        if self.challenge_table:
                            try:
                                # Force complete reload of challenge data
                                self.challenge_table.challenge_data = self.challenge_table._load_challenge_data()
                                self.challenge_table.refresh()
                                print("Challenge table reloaded after download")
                            except Exception as e:
                                print(f"Error reloading challenge table: {e}")
                                import logging
                                logging.error(f"Failed to reload challenge table: {e}", exc_info=True)    
            
            except Exception as ex:
                self._show_error(f"Error: {str(ex)}")
            
            finally:
                # Re-enable button
                self.challenge_download_button.disabled = False
                self.challenge_download_button.text = "Download Challenge Data"
                try:
                    self.page.update()
                except:
                    pass
        
        # Start thread
        thread = threading.Thread(target=download_thread, daemon=True)
        thread.start()
    
    def _save_blocked_spotters(self, e):
        """Save blocked spotters list"""
        text = self.blocked_spotters_field.value.strip()
        
        if not text:
            spotters = []
        else:
            spotters = [s.strip().upper() for s in text.split(',') if s.strip()]
        
        set_blocked_spotters(spotters)
        
        self.blocked_count_text.value = f"Currently blocking {len(spotters)} spotter(s)"
        self.blocked_count_text.update()
        
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(f"Saved {len(spotters)} blocked spotter(s)"),
            bgcolor=ft.Colors.GREEN_400,
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def _clear_blocked_spotters(self, e):
        """Clear all blocked spotters"""
        set_blocked_spotters([])
        self.blocked_spotters_field.value = ''
        self.blocked_count_text.value = "Currently blocking 0 spotter(s)"
        
        self.blocked_spotters_field.update()
        self.blocked_count_text.update()
        
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text("Cleared all blocked spotters"),
            bgcolor=ft.Colors.GREEN_400,
        )
        self.page.snack_bar.open = True
        self.page.update()
        
    def _save_watch_list(self, e):
        """Save watch list"""
        from backend.config import set_watch_list
        
        text = self.watch_list_field.value.strip()
        
        if not text:
            callsigns = []
        else:
            callsigns = [s.strip().upper() for s in text.split(',') if s.strip()]
        
        set_watch_list(callsigns)
        
        self.watch_count_text.value = f"Watching {len(callsigns)} callsign(s)"
        self.watch_count_text.update()
        
        # Refresh spot table with new watch list
        if hasattr(self.page, 'spot_table'):
            self.page.spot_table.refresh_watch_list()
        
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(f"Saved {len(callsigns)} callsign(s) to watch list"),
            bgcolor=ft.Colors.GREEN_400,
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def _clear_watch_list(self, e):
        """Clear watch list"""
        from backend.config import set_watch_list
        
        set_watch_list([])
        self.watch_list_field.value = ''
        self.watch_count_text.value = "Watching 0 callsign(s)"
        
        self.watch_list_field.update()
        self.watch_count_text.update()
        
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text("Cleared watch list"),
            bgcolor=ft.Colors.GREEN_400,
        )
        self.page.snack_bar.open = True
        self.page.update()
        
    def _update_lotw_users(self, e):
        """Download fresh LoTW user data"""
        import threading
        from backend.app_logging import get_logger
        
        logger = get_logger(__name__)
        
        self.lotw_update_button.disabled = True
        self.lotw_update_button.text = "Updating..."
        self.lotw_cache_text.value = "Downloading LoTW users..."
        
        try:
            self.lotw_update_button.update()
            self.lotw_cache_text.update()
        except:
            pass
        
        def update_thread():
            try:
                from backend.lotw_users import refresh_if_needed, get_user_count, get_cache_age_days
                
                logger.info("LOTW UPDATE → Downloading user list")
                refresh_if_needed(force=True)
                
                user_count = get_user_count()
                cache_age = get_cache_age_days()
                
                self.lotw_cache_text.value = f"LoTW Users: {user_count:,} ({cache_age} days old)"
                self.lotw_cache_text.color = ft.Colors.GREEN
                
                logger.info(f"LOTW UPDATE ✓ Downloaded {user_count:,} users")
                
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Success! {user_count:,} LoTW users updated"),
                    bgcolor=ft.Colors.GREEN_400,
                )
                self.page.snack_bar.open = True
                
            except Exception as ex:
                logger.error(f"LOTW UPDATE ✗ Failed: {ex}")
                
                self.lotw_cache_text.value = "Update failed"
                self.lotw_cache_text.color = ft.Colors.RED
                
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Update failed: {str(ex)}"),
                    bgcolor=ft.Colors.RED_400,
                )
                self.page.snack_bar.open = True
            
            finally:
                self.lotw_update_button.disabled = False
                self.lotw_update_button.text = "Update LoTW Users"
                
                try:
                    self.lotw_update_button.update()
                    self.lotw_cache_text.update()
                    self.page.update()
                except:
                    pass
        
        thread = threading.Thread(target=update_thread, daemon=True)
        thread.start()
    
    def _show_error(self, message):
        """Show error snackbar"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED_400,
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def set_connection_state(self, connected: bool):
        """Update UI based on connection state (called from main UI)"""
        self.is_connected = connected
        if connected:
            self.connect_button.text = "Disconnect"
            self.connect_button.icon = ft.Icons.LINK_OFF
        else:
            self.connect_button.text = "Connect"
            self.connect_button.icon = ft.Icons.LINK
        try:
            self.connect_button.update()
        except:
            pass
            
# Migrate old credentials from config.ini to secure storage
        self._migrate_old_credentials()

    def _migrate_old_credentials(self):
        """One-time migration from config.ini to secure storage"""
        from backend.config import load_config
        from backend.secure_credentials import save_lotw_credentials, credentials_exist
        
        # Only migrate if no secure credentials exist
        if credentials_exist():
            return
        
        config = load_config()
        old_user = config.get('lotw', 'username', fallback='')
        old_pass = config.get('lotw', 'password', fallback='')
        
        if old_user and old_pass:
            print("Migrating LoTW credentials to secure storage...")
            save_lotw_credentials(old_user, old_pass)
            
            # Clear from config.ini
            if 'lotw' in config:
                if 'username' in config['lotw']:
                    del config['lotw']['username']
                if 'password' in config['lotw']:
                    del config['lotw']['password']
                
                from backend.config import save_config
                save_config(config)
                
            print("Migration complete - credentials removed from config.ini")