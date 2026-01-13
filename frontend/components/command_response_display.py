# command_response_display.py - Compact horizontal command/response display
import flet as ft
from collections import deque
from datetime import datetime


class CommandResponseDisplay(ft.Container):
    """Compact horizontal display showing last few cluster command responses"""
    
    def __init__(self):
        super().__init__()
        
        # Store last 10 messages
        self.message_history = deque(maxlen=10)
        
        # Scrollable message display (horizontal)
        self.message_display = ft.ListView(
            spacing=2,
            auto_scroll=True,
            height=80,  # Compact height - about 4-5 lines
        )
        
        # Clear button
        clear_button = ft.IconButton(
            icon=ft.Icons.CLEAR_ALL,
            icon_size=16,
            tooltip="Clear command history",
            on_click=self._clear_history,
        )
        
        # Build container
        self.content = ft.Column([
            ft.Row([
                ft.Text("Cluster Responses:", size=11, weight=ft.FontWeight.BOLD),
                clear_button,
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(height=1),
            self.message_display,
        ], spacing=2)
        
        self.bgcolor = ft.Colors.BLUE_GREY_900
        self.border = ft.border.all(1, ft.Colors.BLUE_GREY_700)
        self.border_radius = 5
        self.padding = 5
        self.expand = False
    
    def add_command(self, command: str):
        """Add a sent command to the display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Add to history
        self.message_history.append({
            "type": "command",
            "text": command.strip(),
            "time": timestamp,
        })
        
        # Add to UI - compact format
        self.message_display.controls.append(
            ft.Text(
                f"{timestamp} → {command.strip()}",
                size=10,
                color=ft.Colors.CYAN_300,
                no_wrap=False,
            )
        )
        
        # Keep only last 10 items
        if len(self.message_display.controls) > 10:
            self.message_display.controls.pop(0)
        
        try:
            self.update()
        except:
            pass
    
    def add_response(self, response: str):
        """Add a server response to the display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Skip empty responses
        if not response.strip():
            return
        
        # Skip login prompts and dividers
        response_lower = response.lower()
        if any(skip in response_lower for skip in ["please enter", "login:", "----", "de n4lr"]):
            return
        
        # Add to history
        self.message_history.append({
            "type": "response",
            "text": response.strip(),
            "time": timestamp,
        })
        
        # Color code based on content
        if "filter" in response_lower or "set" in response_lower:
            color = ft.Colors.GREEN_300  # Success messages
        elif "error" in response_lower or "failed" in response_lower:
            color = ft.Colors.RED_300  # Errors
        else:
            color = ft.Colors.BLUE_GREY_300  # Info
        
        # Add to UI - compact format
        self.message_display.controls.append(
            ft.Text(
                f"{timestamp} ← {response.strip()}",
                size=10,
                color=color,
                no_wrap=False,
            )
        )
        
        # Keep only last 10 items
        if len(self.message_display.controls) > 10:
            self.message_display.controls.pop(0)
        
        try:
            self.update()
        except:
            pass
    
    def _clear_history(self, e):
        """Clear the message history"""
        self.message_history.clear()
        self.message_display.controls.clear()
        try:
            self.update()
        except:
            pass