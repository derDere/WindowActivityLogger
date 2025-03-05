"""
Main application class that coordinates all components of the Window Activity Logger.
"""
from datetime import datetime
from pathlib import Path
from typing import Optional, TYPE_CHECKING, Callable
import re
import queue
import tkinter as tk
from config_manager import ConfigurationManager
from window_monitor import WindowMonitor
from system_tray import SystemTrayInterface
from report_window import ReportWindow
from settings_window import SettingsWindow
from sql_query_window import SQLQueryWindow

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
        self._sql_query_window: Optional[SQLQueryWindow] = None
        self._is_running = False
        self._ui_queue = queue.Queue()
        
        # Create root window but keep it hidden
        self._root = tk.Tk()
        self._root.withdraw()  # Hide the root window
        # Prevent the root window from being shown in taskbar
        self._root.attributes("-alpha", 0)  # Make it fully transparent
        self._root.attributes("-topmost", True)  # Keep it on top
        self._root.overrideredirect(True)  # Remove window decorations
        self._root.geometry("0x0+0+0")  # Make it tiny and place in corner

    @property
    def root(self) -> tk.Tk:
        """Get the Tk root window."""
        return self._root

    @property
    def is_running(self) -> bool:
        """Whether the application is currently running."""
        return self._is_running

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
            self._config_manager = ConfigurationManager(self)
            if not self._config_manager.load():
                return False

            # Register for configuration updates
            self._config_manager.add_update_handler(self._handle_config_changed)

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
            self._sql_query_window = SQLQueryWindow(self._db_manager)

            # Initialize system tray
            self._tray_interface = SystemTrayInterface()
            if not self._tray_interface.initialize():
                return False

            # Set up event handlers
            self._window_monitor.set_title_changed_callback(self._handle_window_title_changed)
            self._tray_interface.set_exit_callback(self._handle_exit_request)
            self._tray_interface.set_show_report_callback(self._handle_show_report)
            self._tray_interface.set_show_settings_callback(self._handle_show_settings)
            self._tray_interface.set_show_sql_query_callback(self._handle_show_sql_query)

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
        if not self._is_running:
            return  # Already stopped

        self._is_running = False

        # Queue UI cleanup to run in main thread
        try:
            # Hide UI windows first to prevent any new operations
            if self._report_window:
                self._report_window.hide()
            if self._settings_window:
                self._settings_window.hide()
            if self._sql_query_window:
                self._sql_query_window.hide()

            # Stop background components in reverse order of initialization
            if self._window_monitor:
                self._window_monitor.stop()
            if self._tray_interface:
                self._tray_interface.cleanup()

            # Schedule root destruction for next UI update
            if self._root:
                self._root.after(0, self._destroy_root)
        except Exception as e:
            print(f"Error cleaning up components: {e}")

    def _destroy_root(self) -> None:
        """Destroy the root window safely in the main thread."""
        try:
            if self._root:
                self._root.quit()
                self._root.destroy()
                self._root = None
        except Exception as e:
            print(f"Error destroying root window: {e}")

    def process_ui_events(self) -> None:
        """Process any pending UI events in the main thread."""
        try:
            # Process Tkinter events
            self._root.update()
            
            # Process queued UI actions
            while True:
                # Get all pending UI actions without blocking
                action = self._ui_queue.get_nowait()
                if action:
                    action()
                self._ui_queue.task_done()
        except queue.Empty:
            pass  # No more events to process
        except tk.TclError:
            # Root window was destroyed, exit the application
            self._is_running = False

    def _queue_ui_action(self, action: Callable[[], None]) -> None:
        """Queue a UI action to be executed in the main thread.
        
        Args:
            action: The function to execute in the main thread
        """
        self._ui_queue.put(action)

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
            # Queue stop to run in main thread
            self._queue_ui_action(self.stop)
        except Exception as e:
            print(f"Error during exit: {e}")
            self._is_running = False  # Ensure we still exit even if there's an error

    def _handle_show_report(self) -> None:
        """Handle show report window request from system tray."""
        if self._report_window:
            # Queue the window show operation to run in main thread
            self._queue_ui_action(lambda: self._report_window.show())

    def _handle_show_settings(self) -> None:
        """Handle show settings window request from system tray."""
        if self._settings_window:
            # Queue the window show operation to run in main thread
            self._queue_ui_action(lambda: self._settings_window.show())

    def _handle_show_sql_query(self) -> None:
        """Handle show SQL query window request from system tray."""
        if self._sql_query_window:
            # Queue the window show operation to run in main thread
            self._queue_ui_action(lambda: self._sql_query_window.show())

    def _handle_config_changed(self) -> None:
        """Handle configuration changes from any source."""
        try:
            # Queue UI actions to happen in the main thread
            def update_actions():
                # Config changes may require UI updates
                if self._report_window:
                    self._report_window.refresh_data()
                    
                # Any future UI component updates can be added here
                pass
            
            self._queue_ui_action(update_actions)

        except Exception as e:
            print(f"Error handling configuration change: {e}")
