"""
Main application class that coordinates all components of the Window Activity Logger.
"""
from datetime import datetime
from pathlib import Path
from typing import Optional, TYPE_CHECKING
import re
from config_manager import ConfigurationManager
from window_monitor import WindowMonitor
from system_tray import SystemTrayInterface
from report_window import ReportWindow
from settings_window import SettingsWindow

if TYPE_CHECKING:
    from db_manager import DatabaseManager

class Application:
    def __init__(self):
        """Initialize the application and its components."""
        self._config_manager: Optional[ConfigurationManager] = None
        self._db_manager: Optional['DatabaseManager'] = None
        self._window_monitor: Optional[WindowMonitor] = None
        self._tray_interface: Optional[SystemTrayInterface] = None
        self._report_window: Optional[ReportWindow] = None
        self._settings_window: Optional[SettingsWindow] = None
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

            # Import here to avoid circular dependency
            from db_manager import DatabaseManager

            # Initialize database manager
            self._db_manager = DatabaseManager(self)
            if not self._db_manager.initialize():
                return False

            # Initialize window monitor
            self._window_monitor = WindowMonitor(self)
            if not self._window_monitor.initialize():
                return False

            # Initialize UI components
            self._report_window = ReportWindow(self._db_manager)
            self._settings_window = SettingsWindow(self._config_manager)

            # Initialize system tray
            self._tray_interface = SystemTrayInterface()
            if not self._tray_interface.initialize():
                return False

            # Set up event handlers
            self._window_monitor.set_title_changed_callback(self._handle_window_title_changed)
            self._tray_interface.set_exit_callback(self._handle_exit_request)
            self._tray_interface.set_show_report_callback(self._handle_show_report)
            self._tray_interface.set_show_settings_callback(self._handle_show_settings)

            return True

        except Exception as e:
            print(f"Error initializing application: {e}")
            return False

    def start(self) -> None:
        """Start the application and all its components."""
        if not self._is_running:
            # Start core components
            if self._window_monitor:
                self._window_monitor.start()

            # Application starts minimized to system tray
            # No windows are shown initially
            self._is_running = True

    def stop(self) -> None:
        """Stop the application and all its components."""
        self._is_running = False

        # Hide UI windows
        if self._report_window:
            self._report_window.hide()
        if self._settings_window:
            self._settings_window.hide()

        # Stop core components
        if self._window_monitor:
            self._window_monitor.stop()
        if self._tray_interface:
            self._tray_interface.cleanup()

    def _handle_window_title_changed(self, timestamp: datetime, old_title: str, new_title: str) -> bool:
        """Handle window title change events.

        Args:
            timestamp: When the title change occurred
            old_title: Previous window title
            new_title: New window title

        Returns:
            bool: True if the title was accepted and should be remembered, False if it was filtered out
        """
        try:
            # Skip if title is empty
            if not new_title:
                return False

            # Check if title matches any ignore patterns
            for pattern in self.configuration.get_regex_patterns():
                if re.match(pattern, new_title):
                    return False

            # Update database if we have a valid title change
            if self._db_manager:
                self._db_manager.log_window_title(new_title, timestamp)
            return True

        except Exception as e:
            print(f"Error handling window title change: {e}")
            return False

    def _handle_exit_request(self) -> None:
        """Handle application exit request from system tray."""
        try:
            # Stop all components first
            self.stop()
            # Set a flag to stop the main loop
            self._is_running = False
        except Exception as e:
            print(f"Error during exit: {e}")
            # Ensure we still exit even if there's an error
            self._is_running = False

    def _handle_show_report(self) -> None:
        """Handle show report window request from system tray."""
        if self._report_window:
            self._report_window.show()
            self._report_window.refresh_data()

    def _handle_show_settings(self) -> None:
        """Handle show settings window request from system tray."""
        if self._settings_window:
            self._settings_window.show()
