"""
Database management window for editing database entries.
"""
import tkinter as tk
from tkinter import ttk
from typing import Optional

from db_manager import DatabaseManager


class DatabaseManagementWindow:
    """Window for managing database entries like projects and window titles."""

    def __init__(self, parent, db_manager: DatabaseManager):
        """Initialize the database management window.

        Args:
            parent: The parent application or window
            db_manager: Database manager instance
        """
        self._parent = parent
        self._db_manager = db_manager
        self._window: Optional[tk.Toplevel] = None

    def show(self) -> None:
        """Show the database management window."""
        # If window already exists, bring it to front
        if self._window is not None:
            self._window.deiconify()
            self._window.lift()
            return

        # Create window
        self._window = tk.Toplevel()
        self._window.title("Database Management")
        self._window.minsize(600, 400)
        self._window.protocol("WM_DELETE_WINDOW", self._on_close)

        # Create UI
        self._create_ui()

    def _create_ui(self) -> None:
        """Create the user interface."""
        # Create a notebook (tabs)
        notebook = ttk.Notebook(self._window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Projects tab
        projects_frame = ttk.Frame(notebook)
        notebook.add(projects_frame, text="Projects")
        self._create_projects_tab(projects_frame)

        # Window Titles tab
        titles_frame = ttk.Frame(notebook)
        notebook.add(titles_frame, text="Window Titles")
        self._create_titles_tab(titles_frame)

    def _create_projects_tab(self, parent: ttk.Frame) -> None:
        """Create the projects management tab.
        
        Args:
            parent: Parent frame for this tab
        """
        # Label
        header_label = ttk.Label(parent, text="Manage Projects", font=("", 12, "bold"))
        header_label.pack(pady=(10, 20))

        # TODO: Add project list, add/rename/delete buttons, etc.
        placeholder = ttk.Label(parent, text="Project management functionality will be implemented here")
        placeholder.pack(pady=50)

    def _create_titles_tab(self, parent: ttk.Frame) -> None:
        """Create the window titles management tab.
        
        Args:
            parent: Parent frame for this tab
        """
        # Label
        header_label = ttk.Label(parent, text="Manage Window Titles", font=("", 12, "bold"))
        header_label.pack(pady=(10, 20))

        # TODO: Add window titles list, project assignment, filtering, etc.
        placeholder = ttk.Label(parent, text="Window title management functionality will be implemented here")
        placeholder.pack(pady=50)

    def _on_close(self) -> None:
        """Handle window close event."""
        if self._window:
            self._window.withdraw()  # Hide window rather than destroying it