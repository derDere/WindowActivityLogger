"""
System tray interface for providing application controls.
"""
from pathlib import Path
from typing import Callable, Optional, Any
import pystray
from PIL import Image

# Type aliases to avoid forward reference issues
Icon = Any  # pystray.Icon
MenuItem = Any  # pystray.MenuItem

class SystemTrayInterface:
    def __init__(self):
        """Initialize the system tray interface."""
        self._icon: Optional[Icon] = None
        self._on_exit: Optional[Callable[[], None]] = None
        self._on_show_report: Optional[Callable[[], None]] = None
        self._on_show_settings: Optional[Callable[[], None]] = None

    def initialize(self) -> bool:
        """Initialize the system tray icon and menu."""
        try:
            # Load icon
            icon_path = Path(__file__).parent / "resources" / "icon.ico"
            image = Image.open(icon_path)

            # Create menu
            menu = pystray.Menu(
                pystray.MenuItem("Show Report", self._handle_show_report),
                pystray.MenuItem("Settings", self._handle_show_settings),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Exit", self._handle_exit)
            )

            # Create system tray icon
            self._icon = pystray.Icon(
                "Window Logger",
                image,
                "Window Logger",
                menu
            )

            # Start icon in a separate thread
            if self._icon:  # Type guard for None check
                self._icon.run_detached()
            return True

        except Exception as e:
            print(f"Error initializing system tray: {e}")
            return False

    def cleanup(self) -> None:
        """Remove the system tray icon and cleanup resources."""
        try:
            if self._icon:
                self._icon.stop()
                self._icon = None

        except Exception as e:
            print(f"Error cleaning up system tray: {e}")

    def set_exit_callback(self, callback: Callable[[], None]) -> None:
        """Set the callback for exit menu item."""
        self._on_exit = callback

    def set_show_report_callback(self, callback: Callable[[], None]) -> None:
        """Set the callback for show report menu item."""
        self._on_show_report = callback

    def set_show_settings_callback(self, callback: Callable[[], None]) -> None:
        """Set the callback for show settings menu item."""
        self._on_show_settings = callback

    def _handle_exit(self, _icon: Icon, _item: MenuItem) -> None:
        """Handle exit menu item click."""
        if self._icon:
            self._icon.stop()  # Stop the icon first
        if self._on_exit:
            self._on_exit()

    def _handle_show_report(self, _icon: Icon, _item: MenuItem) -> None:
        """Handle show report menu item click."""
        if self._on_show_report:
            self._on_show_report()

    def _handle_show_settings(self, _icon: Icon, _item: MenuItem) -> None:
        """Handle show settings menu item click."""
        if self._on_show_settings:
            self._on_show_settings()
