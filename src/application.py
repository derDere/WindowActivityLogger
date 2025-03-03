"""
Main application class that coordinates all components of the Window Activity Logger.
"""
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config_manager import ConfigurationManager
from .db_manager import DatabaseManager
from .window_monitor import WindowMonitor
from .system_tray import SystemTrayInterface

class Application:
    def __init__(self):
        """Initialize the application and its components."""
        self._config_manager: Optional[ConfigurationManager] = None
        self._db_manager: Optional[DatabaseManager] = None
        self._window_monitor: Optional[WindowMonitor] = None
        self._tray_interface: Optional[SystemTrayInterface] = None
        self._is_running = False

    @property
    def configuration(self) -> ConfigurationManager:
        """Get the configuration manager.

        Returns:
            The application's configuration manager
        """
        if self._config_manager is None:
            raise RuntimeError("Configuration manager not initialized")
        return self._config_manager

    def initialize(self) -> bool:
        """Initialize all components of the application."""
        try:
            # Initialize and load configuration
            self._config_manager = ConfigurationManager()
            if not self._config_manager.load():
                return False

            # Initialize database manager
            self._db_manager = DatabaseManager(self)
            if not self._db_manager.initialize():
                return False

            # Initialize window monitor
            self._window_monitor = WindowMonitor(self)
            if not self._window_monitor.initialize():
                return False

            # Initialize system tray
            self._tray_interface = SystemTrayInterface()
            if not self._tray_interface.initialize():
                return False

            # Set up event handlers
            self._window_monitor.set_title_changed_callback(self._handle_window_title_changed)
            self._tray_interface.set_exit_callback(self._handle_exit_request)

            return True

        except Exception as e:
            print(f"Error initializing application: {e}")
            return False

    def start(self) -> None:
        """Start the application and all its components."""
        if self._window_monitor:
            self._window_monitor.start()
        self._is_running = True

    def stop(self) -> None:
        """Stop the application and all its components."""
        self._is_running = False
        if self._window_monitor:
            self._window_monitor.stop()
        if self._tray_interface:
            self._tray_interface.cleanup()
        if self._db_manager:
            self._db_manager.disconnect()

    def _handle_window_title_changed(self, timestamp: datetime, old_title: str, new_title: str) -> None:
        """Handle window title change events.

        Args:
            timestamp: When the title change occurred
            old_title: Previous window title
            new_title: New window title
        """
        if self._db_manager:
            self._db_manager.log_window_title(new_title, timestamp)

    def _handle_exit_request(self) -> None:
        """Handle application exit request from system tray."""
        self.stop()
