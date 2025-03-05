"""
Report window for displaying activity statistics and managing projects.
"""
import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import showerror
from typing import Optional, Dict, List, Tuple, cast
from datetime import datetime, timedelta

from db_manager import DatabaseManager

# Time range options
TIME_RANGES = {
    "Day": timedelta(days=1),
    "Week": timedelta(days=7),
    "Month": timedelta(days=30)
}

class ReportWindow:
    def __init__(self, db_manager: DatabaseManager):
        """Initialize the report window."""
        self._db_manager = db_manager
        self._window: Optional[tk.Toplevel] = None
        self._time_range_var: Optional[tk.StringVar] = None
        self._project_tree: Optional[ttk.Treeview] = None
        self._title_tree: Optional[ttk.Treeview] = None

    def show(self) -> None:
        """Show the report window."""
        if self._window is None:
            # Create new window
            self._window = tk.Toplevel()
            self._window.title("Activity Report")
            self._window.minsize(800, 600)

            # Create widgets
            self._create_widgets()

            # Update data
            self.refresh_data()
        else:
            # Window exists, just bring it to front
            self._window.lift()
            self._window.focus_force()

    def hide(self) -> None:
        """Hide the report window."""
        if self._window:
            self._window.destroy()
            self._window = None
            self._time_range_var = None
            self._project_tree = None
            self._title_tree = None

    def refresh_data(self) -> None:
        """Refresh the displayed data."""
        if not self._window:
            return

        try:
            # Get time range
            range_name = self._time_range_var.get() if self._time_range_var else "Day"
            end_time = datetime.now()
            start_time = end_time - TIME_RANGES[range_name]

            # Update project summary
            project_data = self._db_manager.get_project_summary(start_time, end_time)
            self._update_project_tree(project_data)

            # Update title summary
            title_data = self._db_manager.get_title_summary(start_time, end_time)
            self._update_title_tree(title_data)

        except Exception as e:
            showerror("Error", f"Failed to refresh data: {e}")

    def _create_widgets(self) -> None:
        """Create all window widgets."""
        if not self._window:
            return

        # Create main frame with padding
        main_frame = ttk.Frame(self._window, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        self._window.columnconfigure(0, weight=1)
        self._window.rowconfigure(0, weight=1)

        # Create time range selector
        self._create_time_range_selector(main_frame)

        # Create project summary
        self._create_project_summary(main_frame)

        # Create title summary
        self._create_title_summary(main_frame)

        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)

    def _create_time_range_selector(self, parent: ttk.Frame) -> None:
        """Create the time range selector widget."""
        # Create frame
        frame = ttk.Frame(parent)
        frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        # Create label
        ttk.Label(frame, text="Time Range:").pack(side=tk.LEFT, padx=(0, 5))

        # Create combobox
        self._time_range_var = tk.StringVar(value="Day")
        combo = ttk.Combobox(
            frame,
            textvariable=self._time_range_var,
            values=list(TIME_RANGES.keys()),
            state="readonly",
            width=10
        )
        combo.pack(side=tk.LEFT)

        # Bind change event
        self._time_range_var.trace_add("write", self._handle_time_range_changed)

    def _create_project_summary(self, parent: ttk.Frame) -> None:
        """Create the project summary tree view."""
        # Create frame with label
        frame = ttk.LabelFrame(parent, text="Project Summary", padding="5")
        frame.grid(row=1, column=0, sticky="nsew", padx=(0, 5))

        # Create treeview
        self._project_tree = ttk.Treeview(
            frame,
            columns=("duration",),
            show="headings",
            selectmode="browse"
        )

        # Configure columns
        self._project_tree.heading("duration", text="Duration")
        self._project_tree.column("duration", width=100, anchor=tk.E)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self._project_tree.yview)
        self._project_tree.configure(yscrollcommand=scrollbar.set)

        # Pack widgets
        self._project_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_title_summary(self, parent: ttk.Frame) -> None:
        """Create the title summary tree view."""
        # Create frame with label
        frame = ttk.LabelFrame(parent, text="Window Titles", padding="5")
        frame.grid(row=1, column=1, sticky="nsew")

        # Create treeview
        self._title_tree = ttk.Treeview(
            frame,
            columns=("duration", "project"),
            show="headings",
            selectmode="browse"
        )

        # Configure columns
        self._title_tree.heading("duration", text="Duration")
        self._title_tree.heading("project", text="Project")
        self._title_tree.column("duration", width=100, anchor=tk.E)
        self._title_tree.column("project", width=150)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self._title_tree.yview)
        self._title_tree.configure(yscrollcommand=scrollbar.set)

        # Pack widgets
        self._title_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind double-click for project assignment
        self._title_tree.bind("<Double-1>", self._handle_project_assignment)

    def _format_duration(self, seconds: float) -> str:
        """Format duration in seconds to a readable string."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)

        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    def _update_project_tree(self, data: List[Tuple[str, float]]) -> None:
        """Update project summary tree with new data."""
        if not self._project_tree:
            return

        # Clear existing items
        for item in self._project_tree.get_children():
            self._project_tree.delete(item)

        # Add new items
        for project_name, duration in data:
            self._project_tree.insert(
                "",
                tk.END,
                values=(self._format_duration(duration), project_name)
            )

    def _update_title_tree(self, data: List[Tuple[str, float]]) -> None:
        """Update title summary tree with new data."""
        if not self._title_tree:
            return

        # Clear existing items
        for item in self._title_tree.get_children():
            self._title_tree.delete(item)

        # Add new items
        for title, duration in data:
            self._title_tree.insert(
                "",
                tk.END,
                values=(self._format_duration(duration), title)
            )

    def _handle_time_range_changed(self, *args) -> None:
        """Handle time range selection changes."""
        self.refresh_data()

    def _handle_project_assignment(self, event) -> None:
        """Handle project assignment changes."""
        if not self._title_tree:
            return

        # Get selected item
        selection = self._title_tree.selection()
        if not selection:
            return

        # Get title from selected item
        item = selection[0]
        title = cast(str, self._title_tree.item(item)["values"][1])

        # Show project selection dialog
        self._show_project_dialog(title)

    def _show_project_dialog(self, title: str) -> None:
        """Show dialog for assigning a window title to a project."""
        if not self._window:
            return

        # Create dialog
        dialog = tk.Toplevel(self._window)
        dialog.title("Assign Project")
        dialog.transient(self._window)
        dialog.grab_set()

        # Create widgets
        ttk.Label(dialog, text=f"Assign project for:\n{title}", padding="10").pack()

        # Get projects
        projects = self._db_manager.get_projects()
        project_names = list(projects.values())
        project_var = tk.StringVar(value=project_names[0] if project_names else "")

        # Create project selector
        project_frame = ttk.Frame(dialog, padding="10")
        project_frame.pack(fill=tk.X)

        ttk.Label(project_frame, text="Project:").pack(side=tk.LEFT, padx=(0, 5))
        project_combo = ttk.Combobox(
            project_frame,
            textvariable=project_var,
            values=project_names,
            state="readonly" if project_names else "normal",
            width=20
        )
        project_combo.pack(side=tk.LEFT)

        # Create buttons
        button_frame = ttk.Frame(dialog, padding="10")
        button_frame.pack(fill=tk.X)

        def handle_ok() -> None:
            project_name = project_var.get().strip()
            if project_name:
                try:
                    # Find project ID by name
                    project_id = next(id for id, name in projects.items() if name == project_name)
                    title_id = self._db_manager._generate_title_id(title)
                    self._db_manager.assign_project(title_id, project_id)
                    self.refresh_data()
                except Exception as e:
                    showerror("Error", f"Failed to assign project: {e}")
            dialog.destroy()

        def handle_cancel() -> None:
            dialog.destroy()

        ttk.Button(button_frame, text="OK", command=handle_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=handle_cancel).pack(side=tk.LEFT)

        # Center dialog
        dialog.update_idletasks()
        x = self._window.winfo_x() + (self._window.winfo_width() - dialog.winfo_width()) // 2
        y = self._window.winfo_y() + (self._window.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
