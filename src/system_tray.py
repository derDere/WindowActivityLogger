"""
System tray interface for providing application controls.
"""
from pathlib import Path
from typing import Callable, Optional, Any
import threading
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
        self._on_show_sql_query: Optional[Callable[[], None]] = None
        self._on_show_db_management: Optional[Callable[[], None]] = None
        self._callback_lock = threading.Lock()

    def initialize(self) -> bool:
        """Initialize the system tray icon and menu."""
        try:
            # Load icon
            icon_path = Path(__file__).parent / "resources" / "icon_small.png"
            image = Image.open(icon_path)

            # Create menu
            menu = pystray.Menu(
                pystray.MenuItem("Show Report", self._handle_show_report),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Database Management", self._handle_show_db_management),
                pystray.MenuItem("Settings", self._handle_show_settings),
                pystray.MenuItem("SQL Query", self._handle_show_sql_query),
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
        with self._callback_lock:
            self._on_exit = callback

    def set_show_report_callback(self, callback: Callable[[], None]) -> None:
        """Set the callback for show report menu item."""
        with self._callback_lock:
            self._on_show_report = callback

    def set_show_settings_callback(self, callback: Callable[[], None]) -> None:
        """Set the callback for show settings menu item."""
        with self._callback_lock:
            self._on_show_settings = callback

    def set_show_sql_query_callback(self, callback: Callable[[], None]) -> None:
        """Set the callback for show SQL query menu item."""
        with self._callback_lock:
            self._on_show_sql_query = callback
            
    def set_show_db_management_callback(self, callback: Callable[[], None]) -> None:
        """Set the callback for show database management menu item."""
        with self._callback_lock:
            self._on_show_db_management = callback

    def _handle_exit(self, _icon: Icon, _item: MenuItem) -> None:
        """Handle exit menu item click."""
        with self._callback_lock:
            if self._on_exit:
                self._on_exit()  # Call exit callback first
            if self._icon:
                self._icon.stop()  # Then stop the icon

    def _handle_show_report(self, _icon: Icon, _item: MenuItem) -> None:
        """Handle show report menu item click."""
        with self._callback_lock:
            if self._on_show_report:
                self._on_show_report()

    def _handle_show_settings(self, _icon: Icon, _item: MenuItem) -> None:
        """Handle show settings menu item click."""
        with self._callback_lock:
            if self._on_show_settings:
                self._on_show_settings()

    def _handle_show_sql_query(self, _icon: Icon, _item: MenuItem) -> None:
        """Handle show SQL query menu item click."""
        with self._callback_lock:
            if self._on_show_sql_query:
                self._on_show_sql_query()
                
    def _handle_show_db_management(self, _icon: Icon, _item: MenuItem) -> None:
        """Handle show database management menu item click."""
        with self._callback_lock:
            if self._on_show_db_management:
                self._on_show_db_management()
