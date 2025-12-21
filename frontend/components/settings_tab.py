# settings_tab.py - Settings tab UI component
import flet as ft
from backend.config import get_user_callsign, get_user_grid, set_user_settings
from backend.grid_utils import validate_grid


class SettingsTab(ft.Container):
    """Settings tab for user configuration"""
    
    def __init__(self, page: ft.Page, on_settings_changed=None):
        super().__init__()
        self.page = page
        self.on_settings_changed = on_settings_changed
        
        # Load current settings
        current_callsign = get_user_callsign()
        current_grid = get_user_grid()
        
        # Callsign input
        self.callsign_field = ft.TextField(
            label="Callsign",
            hint_text="e.g., N4LR or N4LR-14",
            value=current_callsign,
            width=200,
            on_change=self._validate_inputs,
        )
        
        # Grid square input
        self.grid_field = ft.TextField(
            label="Grid Square",
            hint_text="e.g., EM50 or EM50vb",
            value=current_grid,
            width=200,
            on_change=self._validate_inputs,
            capitalization=ft.TextCapitalization.CHARACTERS,
        )
        
        # Validation message
        self.validation_text = ft.Text(
            "",
            color=ft.Colors.RED,
            size=12,
        )
        
        # Save button
        self.save_button = ft.ElevatedButton(
            text="Save Settings",
            on_click=self._save_settings,
            disabled=False,
        )
        
        # Status message
        self.status_text = ft.Text(
            "",
            color=ft.Colors.GREEN,
            size=12,
        )
        
        # Help text
        help_text = ft.Container(
            content=ft.Column([
                ft.Text("Callsign Settings", weight=ft.FontWeight.BOLD, size=16, color=ft.Colors.WHITE),
                ft.Text("Your callsign is used when logging into the cluster.", color=ft.Colors.WHITE70),
                ft.Text("You can append a number suffix (e.g., N4LR-14) to use different filter profiles.", color=ft.Colors.WHITE70),
                ft.Text("Note: Only numbers are allowed after the dash, not letters.", italic=True, size=11, color=ft.Colors.AMBER_200),
                ft.Divider(height=20),
                ft.Text("Grid Square Settings", weight=ft.FontWeight.BOLD, size=16, color=ft.Colors.WHITE),
                ft.Text("Your grid square is used to calculate sunrise/sunset times.", color=ft.Colors.WHITE70),
                ft.Text("Enter a 4-character (EM50) or 6-character (EM50vb) Maidenhead grid.", color=ft.Colors.WHITE70),
                ft.Text("You can find your grid at: https://www.levinecentral.com/ham/grid_square.php", 
                       italic=True, size=11, color=ft.Colors.BLUE_200),
            ], spacing=5),
            padding=20,
            bgcolor=ft.Colors.BLUE_GREY_800,
            border_radius=10,
            border=ft.border.all(1, ft.Colors.BLUE_GREY_600),
        )
        
        # Layout
        self.content = ft.Column([
            ft.Container(height=20),
            ft.Row([
                ft.Column([
                    self.callsign_field,
                    ft.Container(height=10),
                    self.grid_field,
                    ft.Container(height=10),
                    self.validation_text,
                    self.save_button,
                    self.status_text,
                ], spacing=10),
                ft.Container(width=40),
                help_text,
            ]),
        ], expand=True)
        
        self.expand = True
        self.padding = 20
    
    def _validate_inputs(self, e=None):
        """Validate callsign and grid inputs"""
        callsign = self.callsign_field.value.strip()
        grid = self.grid_field.value.strip().upper()
        
        errors = []
        
        # Validate callsign
        if not callsign:
            errors.append("Callsign is required")
        elif "-" in callsign:
            # Check suffix format
            parts = callsign.split("-")
            if len(parts) != 2:
                errors.append("Callsign can only have one dash")
            elif not parts[1].isdigit():
                errors.append("Suffix after dash must be a number (e.g., N4LR-14)")
        
        # Validate grid
        if not grid:
            errors.append("Grid square is required")
        else:
            valid, msg = validate_grid(grid)
            if not valid:
                errors.append(f"Grid: {msg}")
        
        # Update validation display
        if errors:
            self.validation_text.value = " | ".join(errors)
            self.validation_text.color = ft.Colors.RED
            self.save_button.disabled = True
        else:
            self.validation_text.value = "✓ Valid"
            self.validation_text.color = ft.Colors.GREEN
            self.save_button.disabled = False
        
        self.validation_text.update()
        self.save_button.update()
    
    def _save_settings(self, e):
        """Save settings to config file"""
        callsign = self.callsign_field.value.strip()
        grid = self.grid_field.value.strip().upper()
        
        # Save to config
        set_user_settings(callsign, grid)
        
        # Show success message
        self.status_text.value = "✓ Settings saved successfully!"
        self.status_text.color = ft.Colors.GREEN
        self.status_text.update()
        
        # Notify parent if callback provided
        if self.on_settings_changed:
            self.on_settings_changed(callsign, grid)
        
        # Clear success message after 3 seconds
        def clear_status():
            import time
            time.sleep(3)
            self.status_text.value = ""
            self.status_text.update()
        
        import threading
        threading.Thread(target=clear_status, daemon=True).start()
