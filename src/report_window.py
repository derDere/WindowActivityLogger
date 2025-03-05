"""
Report window for displaying activity statistics and managing projects.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, Dict, List, Tuple, cast
from datetime import datetime, timedelta
from pathlib import Path
from PIL import Image, ImageTk

from db_manager import DatabaseManager
from html_export import HTMLExportGenerator

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
        self._active_combo: Optional[ttk.Combobox] = None  # Track active combobox
        self._html_generator = HTMLExportGenerator(db_manager)

    @property
    def _app(self):
        """Get the application instance safely."""
        return self._db_manager._app

    def show(self) -> None:
        """Show the report window."""
        if self._window is None:
            self._window = tk.Toplevel(self._app.root)
            self._window.title("[W.A.L.] - Activity Report")
            self._window.minsize(800, 600)
            self._window.protocol("WM_DELETE_WINDOW", self.hide)

            # Set window icon
            icon_path = Path(__file__).parent / "resources" / "icon.ico"
            if icon_path.exists():
                self._window.iconbitmap(str(icon_path))

            # Create and pack the main container with padding
            main_frame = ttk.Frame(self._window, padding="10")
            main_frame.pack(fill=tk.BOTH, expand=True)

            # 1. Menu bar at top
            self._create_menu_bar(main_frame)

            # 2. Pie chart area (placeholder)
            self._create_pie_chart(main_frame)

            # 3. Project summary table
            self._create_project_table(main_frame)

            # 4. Title summary table with project assignments
            self._create_title_table(main_frame)

            # Center window
            self._window.update_idletasks()
            width = self._window.winfo_width()
            height = self._window.winfo_height()
            x = (self._window.winfo_screenwidth() - width) // 2
            y = (self._window.winfo_screenheight() - height) // 2
            self._window.geometry(f"{width}x{height}+{x}+{y}")

            # Initial data load
            self.refresh_data()
        else:
            self._window.lift()
            self._window.focus_force()
            self.refresh_data()

    def hide(self) -> None:
        """Hide the report window."""
        if self._window:
            self._window.destroy()
            self._window = None
            self._time_range_var = None
            self._project_tree = None
            self._title_tree = None

    def _create_menu_bar(self, parent: ttk.Frame) -> None:
        """Create the menu bar with reload button and time span dropdown."""
        menu_frame = ttk.Frame(parent)
        menu_frame.pack(fill=tk.X, pady=(0, 10))

        # Left side controls
        left_frame = ttk.Frame(menu_frame)
        left_frame.pack(side=tk.LEFT)

        # Reload button
        reload_btn = ttk.Button(left_frame, text="Reload", command=self.refresh_data)
        reload_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Time span dropdown
        ttk.Label(left_frame, text="Time Range:").pack(side=tk.LEFT, padx=(0, 5))
        self._time_range_var = tk.StringVar(value="Day")
        time_combo = ttk.Combobox(
            left_frame,
            textvariable=self._time_range_var,
            values=list(TIME_RANGES.keys()),
            state="readonly",
            width=10
        )
        time_combo.pack(side=tk.LEFT)
        self._time_range_var.trace_add("write", lambda *args: self.refresh_data())

        # Right side controls
        right_frame = ttk.Frame(menu_frame)
        right_frame.pack(side=tk.RIGHT)

        # Export button
        export_btn = ttk.Button(right_frame, text="Export to HTML", command=self._handle_export)
        export_btn.pack(side=tk.RIGHT)

    def _create_pie_chart(self, parent: ttk.Frame) -> None:
        """Create the pie chart area."""
        self.chart_frame = ttk.LabelFrame(parent, text="Project Distribution", padding="5")
        self.chart_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Create canvas for pie chart (400x400 pixels)
        self.chart_canvas = tk.Canvas(self.chart_frame, width=400, height=400, bg='white')
        self.chart_canvas.pack(pady=10)
        self.chart_image = None  # Store reference to prevent garbage collection

    def _update_pie_chart(self, start_time: datetime, end_time: datetime) -> None:
        """Update the pie chart with new data."""
        if not hasattr(self, 'chart_canvas') or not self.chart_canvas.winfo_exists():
            return

        try:
            # Generate chart image
            pil_image = self._html_generator.generate_project_chart_png(start_time, end_time)
            
            # Convert PIL image to Tkinter PhotoImage
            self.chart_image = ImageTk.PhotoImage(pil_image)
            
            # Clear canvas and display new image
            self.chart_canvas.delete("all")
            self.chart_canvas.create_image(
                200, 200,  # Center of canvas
                image=self.chart_image,
                anchor=tk.CENTER
            )
        except Exception as e:
            print(f"Error updating pie chart: {e}")
            # Show error message in canvas
            self.chart_canvas.delete("all")
            self.chart_canvas.create_text(
                200, 200,
                text="Error generating chart",
                fill="red",
                anchor=tk.CENTER
            )

    def _create_project_table(self, parent: ttk.Frame) -> None:
        """Create the project summary table."""
        project_frame = ttk.LabelFrame(parent, text="Project Summary", padding="5")
        project_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Create treeview with scrollbar
        self._project_tree = ttk.Treeview(
            project_frame,
            columns=("id", "name", "time"),
            show="headings",
            selectmode="none"
        )

        # Configure columns
        self._project_tree.heading("id", text="ID")
        self._project_tree.heading("name", text="Project Name")
        self._project_tree.heading("time", text="Time")
        
        self._project_tree.column("id", width=50, anchor=tk.E)
        self._project_tree.column("name", width=200)
        self._project_tree.column("time", width=100, anchor=tk.E)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(project_frame, orient=tk.VERTICAL, command=self._project_tree.yview)
        self._project_tree.configure(yscrollcommand=scrollbar.set)

        # Pack widgets
        self._project_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_title_table(self, parent: ttk.Frame) -> None:
        """Create the title summary table with project assignments."""
        title_frame = ttk.LabelFrame(parent, text="Window Titles", padding="5")
        title_frame.pack(fill=tk.BOTH, expand=True)

        # Create table
        columns = ("title", "time", "project")
        self._title_tree = ttk.Treeview(
            title_frame,
            columns=columns,
            show="headings",
            selectmode="none"
        )

        # Configure columns
        self._title_tree.heading("title", text="Window Title")
        self._title_tree.heading("time", text="Time")
        self._title_tree.heading("project", text="Project")

        self._title_tree.column("title", width=300)
        self._title_tree.column("time", width=100, anchor=tk.E)
        self._title_tree.column("project", width=150)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(title_frame, orient=tk.VERTICAL, command=self._title_tree.yview)
        self._title_tree.configure(yscrollcommand=scrollbar.set)

        # Pack widgets
        self._title_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Add project combobox for each row on single click
        self._title_tree.bind('<Button-1>', self._handle_title_click)
        self._window.bind('<FocusOut>', self._check_combo_focus)

    def _check_combo_focus(self, event) -> None:
        """Safely check focus and destroy combo if needed."""
        if not self._active_combo:
            return
            
        try:
            focused = self._window.focus_get()
            # If we can't get focus info or focus is outside our window, destroy combo
            if not focused or not str(focused).startswith(str(self._window)):
                self._active_combo.destroy()
                self._active_combo = None
        except KeyError:
            # Ignore KeyError from popup windows
            pass
        except Exception as e:
            print(f"Focus check error: {e}")

    def _handle_title_click(self, event) -> None:
        """Handle clicks in the title table to show project combobox."""
        if not self._title_tree:
            return

        # Get clicked region
        region = self._title_tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        # Get clicked column and item
        column = self._title_tree.identify_column(event.x)
        item = self._title_tree.identify_row(event.y)
        
        if not item or column != "#3":  # #3 is the project column
            if self._active_combo:
                self._active_combo.destroy()
                self._active_combo = None
            return

        # Get cell position
        bbox = self._title_tree.bbox(item, "project")
        if not bbox:
            return

        # Get title from row
        row_values = self._title_tree.item(item)["values"]
        if not row_values or len(row_values) < 3:
            return
        title = row_values[0]
        current_project = row_values[2]

        # If clicking on the same combo, just return
        if self._active_combo and self._active_combo.winfo_exists():
            old_title = getattr(self._active_combo, '_title', None)
            if old_title == title:
                return
            self._active_combo.destroy()

        # Create and position combobox
        combo = ttk.Combobox(self._title_tree, width=20, state="readonly")
        combo._title = title  # Store title for reference
        self._active_combo = combo
        
        # Get all projects
        projects = self._db_manager.get_projects()
        project_names = list(projects.values())
        project_names.append("<New>")
        combo["values"] = project_names

        # Set current value
        combo.set(current_project)

        # Position combobox over cell
        combo.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])
        
        def on_select(event=None):
            new_project = combo.get()
            if new_project == "<New>":
                combo.destroy()
                self._active_combo = None
                self._handle_new_project(title)
            else:
                # Find project ID by name
                project_id = next(
                    (id for id, name in projects.items() if name == new_project),
                    1  # Default to Misc if not found
                )
                title_id = self._db_manager._generate_title_id(title)
                if self._db_manager.assign_project(title_id, project_id):
                    combo.destroy()
                    self._active_combo = None
                    self.refresh_data()

        combo.bind('<<ComboboxSelected>>', on_select)
        
        # Show dropdown immediately
        combo.focus_set()
        self._title_tree.after(10, combo.event_generate, '<Button-1>')

    def refresh_data(self) -> None:
        """Refresh all displayed data."""
        if not self._window:
            return

        try:
            # Get time range
            range_name = self._time_range_var.get() if self._time_range_var else "Day"
            end_time = datetime.now()
            start_time = end_time - TIME_RANGES[range_name]

            # Update pie chart
            self._update_pie_chart(start_time, end_time)

            # Update project summary
            self._update_project_data(start_time, end_time)

            # Update title summary
            self._update_title_data(start_time, end_time)

        except Exception as e:
            messagebox.showerror("[W.A.L.] - Error", f"Failed to refresh data: {e}")

    def _format_duration(self, seconds: float) -> str:
        """Format duration in seconds to a readable string."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)

        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    def _update_project_data(self, start_time: datetime, end_time: datetime) -> None:
        """Update the project summary table."""
        if not self._project_tree:
            return

        # Clear existing items
        for item in self._project_tree.get_children():
            self._project_tree.delete(item)

        # Get and display project data
        project_data = self._db_manager.get_project_summary(start_time, end_time)
        for project_id, name, duration in project_data:
            self._project_tree.insert(
                "",
                tk.END,
                values=(project_id, name, self._format_duration(duration))
            )

    def _update_title_data(self, start_time: datetime, end_time: datetime) -> None:
        """Update the title summary table."""
        if not self._title_tree:
            return

        # Clear existing items
        for item in self._title_tree.get_children():
            self._title_tree.delete(item)

        # Get and display title data
        title_data = self._db_manager.get_title_summary(start_time, end_time)
        projects = self._db_manager.get_projects()
        
        for title, duration, project_id in title_data:
            self._title_tree.insert(
                "",
                tk.END,
                values=(
                    title,
                    self._format_duration(duration),
                    projects.get(project_id, "Misc")
                )
            )

    def _handle_new_project(self, title: str) -> None:
        """Handle creation of a new project."""
        if not self._window:
            return

        dialog = tk.Toplevel(self._window)
        dialog.title("[W.A.L.] - New Project")
        dialog.transient(self._window)
        dialog.grab_set()

        # Set dialog icon
        icon_path = Path(__file__).parent / "resources" / "icon.ico"
        if (icon_path.exists()):
            dialog.iconbitmap(str(icon_path))

        ttk.Label(dialog, text="Enter project name:").pack(pady=5)
        name_var = tk.StringVar()
        entry = ttk.Entry(dialog, textvariable=name_var)
        entry.pack(pady=5)

        def handle_ok():
            name = name_var.get().strip()
            if len(name) >= 3:
                if project_id := self._db_manager.create_project(name):
                    title_id = self._db_manager._generate_title_id(title)
                    if self._db_manager.assign_project(title_id, project_id):
                        dialog.destroy()
                        self.refresh_data()
            else:
                messagebox.showerror(
                    "[W.A.L.] - Invalid Name",
                    "Project name must be at least 3 characters long"
                )

        ttk.Button(dialog, text="OK", command=handle_ok).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5, pady=5)

        # Center dialog on parent window
        dialog.update_idletasks()
        x = self._window.winfo_x() + (self._window.winfo_width() - dialog.winfo_width()) // 2
        y = self._window.winfo_y() + (self._window.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

    def _handle_export(self) -> None:
        """Handle export button click."""
        try:
            # Get time range for report
            range_name = self._time_range_var.get() if self._time_range_var else "Day"
            end_time = datetime.now()
            start_time = end_time - TIME_RANGES[range_name]

            # Get save location
            file_name = f"activity_report_{start_time.strftime('%Y%m%d')}_{end_time.strftime('%Y%m%d')}.html"
            filepath = filedialog.asksaveasfilename(
                title="[W.A.L.] - Export Report",
                initialfile=file_name,
                defaultextension=".html",
                filetypes=[("HTML files", "*.html"), ("All files", "*.*")]
            )
            if not filepath:
                return  # User cancelled

            # Generate and save report
            report_html = self._html_generator.generate_report(start_time, end_time)
            Path(filepath).write_text(report_html, encoding='utf-8')

            # Show success message
            messagebox.showinfo(
                "[W.A.L.] - Export Complete",
                f"Report has been saved to:\n{filepath}"
            )

        except Exception as e:
            messagebox.showerror("[W.A.L.] - Export Error", f"Failed to export report: {e}")
