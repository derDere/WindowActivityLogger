"""
Window monitor thread for tracking active window titles.
"""
import ctypes
import threading
import time
from datetime import datetime
from typing import Callable, Optional

import win32api
import win32con
import win32gui
import win32process
import win32ts


class WindowMonitor:
    # Windows API constants
    WTS_CURRENT_SERVER_HANDLE = 0
    WTS_SESSIONSTATE_LOCKED = 0x00000001
    BATTERY_FLAG_CHARGING = 0x00000008
    WTS_SESSION_INFO = 24  # WTSSessionInfo constant from winuser.h

    def __init__(self, polling_interval: int = 30):
        """Initialize the window monitor.

        Args:
            polling_interval: Time between window title checks in seconds
        """
        self._polling_interval = max(1, polling_interval)  # Minimum 1 second
        self._thread: Optional[threading.Thread] = None
        self._is_running = False
        self._lock = threading.Lock()
        self._on_title_changed: Optional[Callable[[datetime, str, str], None]] = None
        self._last_title = ""

    def start(self) -> bool:
        """Start the monitoring thread.

        Returns:
            bool: True if started successfully, False otherwise
        """
        try:
            with self._lock:
                if self._is_running:
                    return True

                self._is_running = True
                self._thread = threading.Thread(
                    target=self._monitor_loop,
                    name="WindowMonitor",
                    daemon=True
                )
                self._thread.start()
                return True

        except Exception as e:
            print(f"Error starting window monitor: {e}")
            self._is_running = False
            return False

    def stop(self) -> None:
        """Stop the monitoring thread."""
        with self._lock:
            self._is_running = False

        if self._thread is not None:
            self._thread.join(timeout=self._polling_interval + 1)
            self._thread = None

    def set_title_changed_callback(self, callback: Callable[[datetime, str, str], None]) -> None:
        """Set the callback for title change events.

        Args:
            callback: Function to call when title changes, with parameters:
                     timestamp (datetime): When the change occurred
                     old_title (str): Previous window title
                     new_title (str): New window title
        """
        with self._lock:
            self._on_title_changed = callback

    def _monitor_loop(self) -> None:
        """Main monitoring loop running in separate thread."""
        while True:
            try:
                # Check if we should stop
                with self._lock:
                    if not self._is_running:
                        break

                # Skip if system is locked or in sleep mode
                if self._is_system_inactive():
                    time.sleep(self._polling_interval)
                    continue

                # Get current window title
                current_title = self._get_active_window_title()

                # Check if title changed
                with self._lock:
                    if current_title != self._last_title:
                        if self._on_title_changed is not None:
                            self._on_title_changed(
                                datetime.now(),
                                self._last_title,
                                current_title
                            )
                        self._last_title = current_title

                # Wait for next check
                time.sleep(self._polling_interval)

            except Exception as e:
                print(f"Error in monitor loop: {e}")
                time.sleep(self._polling_interval)

    def _get_active_window_title(self) -> str:
        """Get the current active window title.

        Returns:
            str: The title of the active window, or empty string if none
        """
        try:
            # Get foreground window handle
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return ""

            # Get window title
            title_length = win32gui.GetWindowTextLength(hwnd)
            title = win32gui.GetWindowText(hwnd)

            # Get process name for UWP apps (they often have generic titles)
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                handle = win32api.OpenProcess(
                    win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ,
                    False,
                    pid
                )
                if handle:
                    exe_name = win32process.GetModuleFileNameEx(handle, 0)
                    win32api.CloseHandle(handle)

                    # If it's a UWP app, append the exe name
                    if "WindowsApps" in exe_name:
                        base_name = exe_name.split("\\")[-1]
                        if base_name not in title:
                            title = f"{title} [{base_name}]"
            except:
                pass  # Ignore process name errors

            return title

        except Exception as e:
            print(f"Error getting window title: {e}")
            return ""

    def _is_system_inactive(self) -> bool:
        """Check if the system is locked or in sleep mode.

        Returns:
            bool: True if system is locked or sleeping, False otherwise
        """
        try:
            # Check if workstation is locked
            session_id = win32ts.WTSGetActiveConsoleSessionId()
            if session_id == 0xFFFFFFFF:  # No active session
                return True

            # Check if screen is locked using WTS session state
            session_info = win32ts.WTSQuerySessionInformation(
                self.WTS_CURRENT_SERVER_HANDLE,
                session_id,
                self.WTS_SESSION_INFO
            )
            if session_info and int(session_info) & self.WTS_SESSIONSTATE_LOCKED:
                return True

            # Check if system is in power saving mode
            status = win32api.GetSystemPowerStatus()
            if status.get('ACLineStatus', 1) == 0:  # On battery
                if status.get('BatteryFlag', 0) & self.BATTERY_FLAG_CHARGING:
                    return True

            return False

        except Exception as e:
            print(f"Error checking system state: {e}")
            return False
