"""
Configuration manager for handling application settings and JSON configuration file.
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable


class ConfigurationManager:
    def __init__(self):
        """Initialize the configuration manager."""
        self._config_path = self._get_config_file_path()
        self._config: Dict[str, Any] = {
            "database_path": str(self._get_default_database_path()),
            "polling_interval": 30,  # Default 30 seconds
            "regex_patterns": []  # Default empty list
        }
        self._update_handlers: List[Callable[[], None]] = []

    def add_update_handler(self, handler: Callable[[], None]) -> None:
        """Add a handler to be called when configuration is updated.

        Args:
            handler: Function to call when configuration changes
        """
        if handler not in self._update_handlers:
            self._update_handlers.append(handler)

    def remove_update_handler(self, handler: Callable[[], None]) -> None:
        """Remove an update handler.

        Args:
            handler: Handler to remove
        """
        if handler in self._update_handlers:
            self._update_handlers.remove(handler)

    def _notify_update(self) -> None:
        """Notify all handlers of a configuration update."""
        for handler in self._update_handlers:
            try:
                handler()
            except Exception as e:
                print(f"Error in configuration update handler: {e}")

    def load(self) -> bool:
        """Load configuration from file.

        Returns:
            bool: True if configuration was loaded successfully, False otherwise
        """
        try:
            # Create config directory if it doesn't exist
            os.makedirs(self._config_path.parent, exist_ok=True)

            # If config file doesn't exist, create it with default values
            if not self._config_path.exists():
                return self.save()

            # Load existing config
            with open(self._config_path, 'r') as f:
                loaded_config = json.load(f)

            # Validate and merge with defaults
            if self._validate_loaded_config(loaded_config):
                self._config.update(loaded_config)
                return True

            print(f"Invalid configuration found in {self._config_path}, using defaults")
            return self.save()  # Save defaults if loaded config is invalid

        except Exception as e:
            print(f"Error loading configuration: {e}")
            return False

    def save(self) -> bool:
        """Save current configuration to file.

        Returns:
            bool: True if configuration was saved successfully, False otherwise
        """
        try:
            # Create config directory if it doesn't exist
            os.makedirs(self._config_path.parent, exist_ok=True)

            # Save config with pretty printing
            with open(self._config_path, 'w') as f:
                json.dump(self._config, f, indent=4)

            # Notify handlers of update
            self._notify_update()
            return True

        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False

    def get_database_path(self) -> Path:
        """Get the configured database path."""
        return Path(self._config["database_path"])

    def set_database_path(self, path: Path) -> None:
        """Set the database path in configuration.

        Args:
            path: New database path
        """
        self._config["database_path"] = str(path)

    def get_polling_interval(self) -> int:
        """Get the configured polling interval in seconds."""
        return self._config["polling_interval"]

    def set_polling_interval(self, interval: int) -> None:
        """Set the polling interval in configuration.

        Args:
            interval: New polling interval in seconds
        """
        if interval < 1:
            raise ValueError("Polling interval must be at least 1 second")
        self._config["polling_interval"] = interval

    def get_regex_patterns(self) -> List[str]:
        """Get the configured regex patterns for title filtering."""
        return self._config["regex_patterns"]

    def set_regex_patterns(self, patterns: List[str]) -> None:
        """Set the regex patterns in configuration.

        Args:
            patterns: List of regex patterns for title filtering
        """
        self._config["regex_patterns"] = patterns

    def validate_configuration(self) -> bool:
        """Validate the current configuration.

        Returns:
            bool: True if configuration is valid, False otherwise
        """
        try:
            # Validate database path
            db_path = Path(self._config["database_path"])
            if not db_path.parent.exists():
                return False

            # Validate polling interval
            if not isinstance(self._config["polling_interval"], int) or self._config["polling_interval"] < 1:
                return False

            # Validate regex patterns
            if not isinstance(self._config["regex_patterns"], list):
                return False

            # Validate each pattern is a string
            if not all(isinstance(pattern, str) for pattern in self._config["regex_patterns"]):
                return False

            return True

        except Exception:
            return False

    def _get_config_file_path(self) -> Path:
        """Get the path to the configuration file.

        Returns:
            Path to config.json in the WindowLogger directory under user's Documents
        """
        return Path(os.path.expandvars("%USERPROFILE%")) / "Documents" / "WindowLogger" / "config.json"

    def _get_default_database_path(self) -> Path:
        """Get the default path for the database file.

        Returns:
            Path to activity.db in the WindowLogger directory under user's Documents
        """
        return Path(os.path.expandvars("%USERPROFILE%")) / "Documents" / "WindowLogger" / "activity.db"

    def _validate_loaded_config(self, config: Dict[str, Any]) -> bool:
        """Validate loaded configuration data.

        Args:
            config: Configuration dictionary to validate

        Returns:
            bool: True if configuration is valid, False otherwise
        """
        required_keys = {"database_path", "polling_interval", "regex_patterns"}

        # Check all required keys exist
        if not all(key in config for key in required_keys):
            return False

        try:
            # Validate database path
            db_path = Path(config["database_path"])
            if not isinstance(config["database_path"], str):
                return False

            # Validate polling interval
            if not isinstance(config["polling_interval"], int) or config["polling_interval"] < 1:
                return False

            # Validate regex patterns
            if not isinstance(config["regex_patterns"], list):
                return False
            if not all(isinstance(pattern, str) for pattern in config["regex_patterns"]):
                return False

            return True

        except Exception:
            return False
