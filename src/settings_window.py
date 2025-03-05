"""
Settings window for managing application configuration.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional, List, TYPE_CHECKING
from pathlib import Path
import re

from config_manager import ConfigurationManager

if TYPE_CHECKING:
    from application import Application

class SettingsWindow:
    def __init__(self, config_manager: ConfigurationManager):
        """Initialize the settings window.
        
        Args:
            config_manager: Configuration manager instance
        """
        if getattr(config_manager, '_app', None) is None:
            raise ValueError("ConfigurationManager must be initialized with Application instance")
        self._config_manager = config_manager
        self._window: Optional[tk.Toplevel] = None
        self._db_path_var: Optional[tk.StringVar] = None
        self._interval_var: Optional[tk.StringVar] = None
        self._pattern_list: Optional[tk.Listbox] = None

    @property
    def _app(self) -> 'Application':
        """Get the application instance safely."""
        return self._config_manager._app

    def show(self) -> None:
        """Show the settings window."""
        if self._window is None:
            # Create new window using the application's root
            self._window = tk.Toplevel(self._app.root)
            self._window.title("[W.A.L.] - Settings")
            self._window.minsize(400, 300)
            self._window.protocol("WM_DELETE_WINDOW", self.hide)

            # Set window icon
            icon_path = Path(__file__).parent / "resources" / "icon.ico"
            if (icon_path.exists()):
                self._window.iconbitmap(str(icon_path))

            # Create widgets
            self._create_widgets()

            # Center window on screen
            self._window.update_idletasks()
            width = self._window.winfo_width()
            height = self._window.winfo_height()
            x = (self._window.winfo_screenwidth() - width) // 2
            y = (self._window.winfo_screenheight() - height) // 2
            self._window.geometry(f"{width}x{height}+{x}+{y}")
        else:
            self._window.lift()
            self._window.focus_force()

    def hide(self) -> None:
        """Hide the settings window."""
        if self._window:
            self._window.destroy()
            self._window = None
            self._db_path_var = None
            self._interval_var = None
            self._pattern_list = None

    def _create_widgets(self) -> None:
        """Create all window widgets."""
        main_frame = ttk.Frame(self._window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create sections
        self._create_database_section(main_frame)
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        self._create_polling_section(main_frame)
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        self._create_pattern_section(main_frame)

        # Save button at bottom
        save_frame = ttk.Frame(main_frame)
        save_frame.pack(fill=tk.X, pady=(10, 0))
        save_btn = ttk.Button(save_frame, text="Save", command=self._handle_save)
        save_btn.pack(side=tk.RIGHT)

    def _create_database_section(self, parent: ttk.Frame) -> None:
        """Create the database configuration section."""
        section = ttk.LabelFrame(parent, text="Database", padding="5")
        section.pack(fill=tk.X, pady=(0, 10))

        # Database path row
        path_frame = ttk.Frame(section)
        path_frame.pack(fill=tk.X)

        self._db_path_var = tk.StringVar(value=str(self._config_manager.get_database_path()))
        path_entry = ttk.Entry(path_frame, textvariable=self._db_path_var)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        browse_btn = ttk.Button(path_frame, text="Browse...", command=self._handle_browse_db)
        browse_btn.pack(side=tk.RIGHT)

    def _create_polling_section(self, parent: ttk.Frame) -> None:
        """Create the polling interval configuration section."""
        section = ttk.LabelFrame(parent, text="Polling Interval", padding="5")
        section.pack(fill=tk.X, pady=(0, 10))

        # Interval row
        interval_frame = ttk.Frame(section)
        interval_frame.pack(fill=tk.X)

        ttk.Label(interval_frame, text="Check window title every").pack(side=tk.LEFT)
        self._interval_var = tk.StringVar(value=str(self._config_manager.get_polling_interval()))
        interval_entry = ttk.Entry(interval_frame, textvariable=self._interval_var, width=5)
        interval_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(interval_frame, text="seconds").pack(side=tk.LEFT)

    def _create_pattern_section(self, parent: ttk.Frame) -> None:
        """Create the pattern management section."""
        section = ttk.LabelFrame(parent, text="Title Filter Patterns", padding="5")
        section.pack(fill=tk.BOTH, expand=True)

        # Help text
        ttk.Label(section, text="Titles matching these regex patterns will be ignored", wraplength=350).pack(fill=tk.X)

        # Pattern list with scrollbar
        list_frame = ttk.Frame(section)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self._pattern_list = tk.Listbox(list_frame, selectmode=tk.SINGLE)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self._pattern_list.yview)
        self._pattern_list.configure(yscrollcommand=scrollbar.set)

        self._pattern_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Load existing patterns
        for pattern in self._config_manager.get_regex_patterns():
            self._pattern_list.insert(tk.END, pattern)

        # Buttons
        btn_frame = ttk.Frame(section)
        btn_frame.pack(fill=tk.X, pady=(5, 0))

        add_btn = ttk.Button(btn_frame, text="Add", command=self._handle_add_pattern)
        add_btn.pack(side=tk.LEFT, padx=(0, 5))

        remove_btn = ttk.Button(btn_frame, text="Remove", command=self._handle_remove_pattern)
        remove_btn.pack(side=tk.LEFT)

    def _handle_browse_db(self) -> None:
        """Handle database path browse button click."""
        initial_dir = Path(self._db_path_var.get()).parent
        filepath = filedialog.asksaveasfilename(
            initialdir=initial_dir,
            title="[W.A.L.] - Select or Create Database File",
            filetypes=[
                ("SQLite Database", "*.db;*.sqlite"),
                ("All Files", "*.*")
            ],
            defaultextension=".db"
        )
        if filepath:
            self._db_path_var.set(filepath)

    def _handle_add_pattern(self) -> None:
        """Handle add pattern button click."""
        dialog = tk.Toplevel(self._window)
        dialog.title("[W.A.L.] - Add Pattern")
        dialog.transient(self._window)
        dialog.grab_set()

        # Set dialog icon
        icon_path = Path(__file__).parent / "resources" / "icon.ico"
        if icon_path.exists():
            dialog.iconbitmap(str(icon_path))

        # Center on parent
        dialog.geometry("300x150")
        dialog.update_idletasks()
        x = self._window.winfo_x() + (self._window.winfo_width() - dialog.winfo_width()) // 2
        y = self._window.winfo_y() + (self._window.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

        ttk.Label(dialog, text="Enter regex pattern:", padding="5").pack()
        pattern_var = tk.StringVar()
        entry = ttk.Entry(dialog, textvariable=pattern_var, width=40)
        entry.pack(padx=5, pady=5)

        def validate_and_add():
            pattern = pattern_var.get().strip()
            try:
                re.compile(pattern)
                self._pattern_list.insert(tk.END, pattern)
                dialog.destroy()
            except re.error:
                messagebox.showerror("[W.A.L.] - Invalid Pattern", "Please enter a valid regular expression")

        btn_frame = ttk.Frame(dialog, padding="5")
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        ttk.Button(btn_frame, text="OK", command=validate_and_add).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT)

        entry.focus_set()

    def _handle_remove_pattern(self) -> None:
        """Handle remove pattern button click."""
        selection = self._pattern_list.curselection()
        if selection:
            self._pattern_list.delete(selection[0])

    def _validate_settings(self) -> bool:
        """Validate all settings before saving.

        Returns:
            bool: True if settings are valid, False otherwise
        """
        try:
            # Validate database path
            db_path = Path(self._db_path_var.get())
            if not db_path.parent.exists():
                messagebox.showerror(
                    "[W.A.L.] - Invalid Path",
                    "Database directory does not exist"
                )
                return False

            # Validate polling interval
            try:
                interval = int(self._interval_var.get())
                if interval < 1:
                    raise ValueError()
            except ValueError:
                messagebox.showerror(
                    "[W.A.L.] - Invalid Interval",
                    "Polling interval must be a positive integer"
                )
                return False

            # Validate patterns
            patterns = list(self._pattern_list.get(0, tk.END))
            for pattern in patterns:
                try:
                    re.compile(pattern)
                except re.error:
                    messagebox.showerror(
                        "[W.A.L.] - Invalid Pattern",
                        f"Invalid regex pattern: {pattern}"
                    )
                    return False

            return True

        except Exception as e:
            messagebox.showerror("[W.A.L.] - Validation Error", str(e))
            return False

    def _handle_save(self) -> None:
        """Handle save button click."""
        if not self._validate_settings():
            return

        try:
            # Update configuration
            self._config_manager.set_database_path(Path(self._db_path_var.get()))
            self._config_manager.set_polling_interval(int(self._interval_var.get()))
            self._config_manager.set_regex_patterns(list(self._pattern_list.get(0, tk.END)))

            # Save config and notify handlers (this triggers _handle_config_changed in Application)
            if self._config_manager.save():
                # Hide window after successful save and update
                self.hide()
                messagebox.showinfo("[W.A.L.] - Success", "Settings saved successfully")
            else:
                messagebox.showerror("[W.A.L.] - Error", "Failed to save settings")

        except Exception as e:
            messagebox.showerror("[W.A.L.] - Error", f"Failed to save settings: {e}")
