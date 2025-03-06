"""
Database management window for editing database entries.
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Optional, Dict, List, Set, Any, Callable
import datetime

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
        
        # UI elements
        self._projects_tree: Optional[ttk.Treeview] = None
        self._titles_tree: Optional[ttk.Treeview] = None
        self._projects_dict: Dict[int, str] = {}  # ID -> name
        self._selected_project_id: Optional[int] = None
        self._selected_title_ids: Set[int] = set()

    def show(self) -> None:
        """Show the database management window."""
        # If window already exists, bring it to front
        if self._window is not None:
            self._window.deiconify()
            self._window.lift()
            self._refresh_data()
            return

        # Create window
        self._window = tk.Toplevel()
        self._window.title("Database Management")
        self._window.minsize(800, 600)
        self._window.protocol("WM_DELETE_WINDOW", self._on_close)

        # Create UI
        self._create_ui()
        self._refresh_data()

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
        # Top frame for label and buttons
        top_frame = ttk.Frame(parent)
        top_frame.pack(fill=tk.X, pady=(10, 5))
        
        # Label
        header_label = ttk.Label(top_frame, text="Manage Projects", font=("", 12, "bold"))
        header_label.pack(side=tk.LEFT, padx=5)
        
        # Bottom frame split into project list and details
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Project list frame (left)
        list_frame = ttk.LabelFrame(main_frame, text="Projects")
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Create treeview with scrollbar
        tree_frame = ttk.Frame(list_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Projects treeview
        columns = ("id", "name", "titles")
        self._projects_tree = ttk.Treeview(
            tree_frame, 
            columns=columns, 
            show="headings",
            selectmode="browse",
            yscrollcommand=scrollbar.set
        )
        
        # Configure columns
        self._projects_tree.heading("id", text="ID")
        self._projects_tree.heading("name", text="Project Name")
        self._projects_tree.heading("titles", text="Titles")
        
        self._projects_tree.column("id", width=50, anchor=tk.CENTER)
        self._projects_tree.column("name", width=200)
        self._projects_tree.column("titles", width=80, anchor=tk.CENTER)
        
        self._projects_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self._projects_tree.yview)
        
        # Bind select event
        self._projects_tree.bind("<<TreeviewSelect>>", self._on_project_selected)
        
        # Buttons frame
        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Add button
        add_btn = ttk.Button(btn_frame, text="Add Project", command=self._on_add_project)
        add_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Rename button
        rename_btn = ttk.Button(btn_frame, text="Rename", command=self._on_rename_project)
        rename_btn.pack(side=tk.LEFT, padx=5)
        
        # Delete button
        delete_btn = ttk.Button(btn_frame, text="Delete", command=self._on_delete_project)
        delete_btn.pack(side=tk.LEFT, padx=5)
        
        # Project details frame (right)
        details_frame = ttk.LabelFrame(main_frame, text="Project Titles")
        details_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Create treeview for titles
        titles_frame = ttk.Frame(details_frame)
        titles_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar
        titles_scrollbar = ttk.Scrollbar(titles_frame)
        titles_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Titles list
        self._project_titles_list = tk.Listbox(
            titles_frame,
            yscrollcommand=titles_scrollbar.set
        )
        self._project_titles_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        titles_scrollbar.config(command=self._project_titles_list.yview)

    def _create_titles_tab(self, parent: ttk.Frame) -> None:
        """Create the window titles management tab.
        
        Args:
            parent: Parent frame for this tab
        """
        # Top frame for label and buttons
        top_frame = ttk.Frame(parent)
        top_frame.pack(fill=tk.X, pady=(10, 5))
        
        # Label
        header_label = ttk.Label(top_frame, text="Manage Window Titles", font=("", 12, "bold"))
        header_label.pack(side=tk.LEFT, padx=5)
        
        # Search frame
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Search label
        search_label = ttk.Label(search_frame, text="Search:")
        search_label.pack(side=tk.LEFT, padx=(0, 5))
        
        # Search entry
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", self._on_search_changed)
        search_entry = ttk.Entry(search_frame, textvariable=self._search_var, width=40)
        search_entry.pack(side=tk.LEFT, padx=5)
        
        # Project filter
        filter_label = ttk.Label(search_frame, text="Project:")
        filter_label.pack(side=tk.LEFT, padx=(15, 5))
        
        self._filter_project_var = tk.StringVar()
        self._filter_project_var.trace_add("write", self._on_project_filter_changed)
        self._filter_project_combo = ttk.Combobox(search_frame, textvariable=self._filter_project_var, state="readonly")
        self._filter_project_combo.pack(side=tk.LEFT, padx=5)
        
        # Main frame
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create treeview with scrollbar
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=(0, 5))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Titles treeview
        columns = ("id", "title", "project", "logs", "first_seen", "last_seen")
        self._titles_tree = ttk.Treeview(
            tree_frame, 
            columns=columns, 
            show="headings",
            selectmode="extended",
            yscrollcommand=scrollbar.set
        )
        
        # Configure columns
        self._titles_tree.heading("id", text="ID")
        self._titles_tree.heading("title", text="Window Title")
        self._titles_tree.heading("project", text="Project")
        self._titles_tree.heading("logs", text="Log Entries")
        self._titles_tree.heading("first_seen", text="First Seen")
        self._titles_tree.heading("last_seen", text="Last Seen")
        
        self._titles_tree.column("id", width=80, anchor=tk.CENTER)
        self._titles_tree.column("title", width=300)
        self._titles_tree.column("project", width=100)
        self._titles_tree.column("logs", width=80, anchor=tk.CENTER)
        self._titles_tree.column("first_seen", width=120, anchor=tk.CENTER)
        self._titles_tree.column("last_seen", width=120, anchor=tk.CENTER)
        
        self._titles_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self._titles_tree.yview)
        
        # Bind select event
        self._titles_tree.bind("<<TreeviewSelect>>", self._on_title_selected)
        
        # Button frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)
        
        # Delete button
        delete_btn = ttk.Button(btn_frame, text="Delete Selected", command=self._on_delete_titles)
        delete_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Reassign button
        reassign_btn = ttk.Button(btn_frame, text="Reassign to Project", command=self._on_reassign_titles)
        reassign_btn.pack(side=tk.LEFT, padx=5)
        
        # Merge button
        merge_btn = ttk.Button(btn_frame, text="Merge Selected", command=self._on_merge_titles)
        merge_btn.pack(side=tk.LEFT, padx=5)
        
        # Refresh button
        refresh_btn = ttk.Button(btn_frame, text="Refresh", command=self._refresh_data)
        refresh_btn.pack(side=tk.RIGHT, padx=5)

    def _refresh_data(self) -> None:
        """Refresh all data from the database."""
        self._refresh_projects()
        self._refresh_titles()

    def _refresh_projects(self) -> None:
        """Refresh projects data."""
        # Get projects from database
        self._projects_dict = self._db_manager.get_projects()
        
        # Update projects treeview
        if self._projects_tree:
            # Clear existing items
            for item in self._projects_tree.get_children():
                self._projects_tree.delete(item)
            
            # Get titles count by project
            titles_by_project = {}
            all_titles = self._db_manager.get_all_titles()
            
            for title in all_titles:
                project_id = title['project_id']
                titles_by_project[project_id] = titles_by_project.get(project_id, 0) + 1
            
            # Add projects to treeview
            for project_id, project_name in self._projects_dict.items():
                title_count = titles_by_project.get(project_id, 0)
                self._projects_tree.insert(
                    "", 
                    tk.END, 
                    iid=str(project_id),
                    values=(project_id, project_name, title_count)
                )
        
        # Update project filter combobox for titles tab
        if self._filter_project_combo:
            values = ["All Projects"] + list(self._projects_dict.values())
            self._filter_project_combo["values"] = values
            if not self._filter_project_var.get():
                self._filter_project_var.set("All Projects")

    def _refresh_titles(self) -> None:
        """Refresh titles data."""
        if not self._titles_tree:
            return
            
        # Clear existing items
        for item in self._titles_tree.get_children():
            self._titles_tree.delete(item)
        
        # Get all titles from database
        titles = self._db_manager.get_all_titles()
        
        # Apply search filter if any
        search_term = self._search_var.get().lower() if hasattr(self, "_search_var") else ""
        if search_term:
            titles = [t for t in titles if search_term in t['title'].lower()]
        
        # Apply project filter if any
        project_filter = self._filter_project_var.get() if hasattr(self, "_filter_project_var") else "All Projects"
        if project_filter != "All Projects":
            # Find project ID by name
            project_id = None
            for pid, pname in self._projects_dict.items():
                if pname == project_filter:
                    project_id = pid
                    break
            
            if project_id is not None:
                titles = [t for t in titles if t['project_id'] == project_id]
        
        # Add titles to treeview
        for title in titles:
            # Format timestamps
            first_seen = self._format_timestamp(title['first_seen'])
            last_seen = self._format_timestamp(title['last_seen'])
            
            self._titles_tree.insert(
                "", 
                tk.END, 
                iid=str(title['id']),
                values=(
                    title['id'], 
                    title['title'], 
                    title['project_name'], 
                    title['log_count'],
                    first_seen,
                    last_seen
                )
            )
    
    def _refresh_project_titles(self) -> None:
        """Refresh the titles list for the selected project."""
        # Clear the list
        if self._project_titles_list:
            self._project_titles_list.delete(0, tk.END)
            
            if self._selected_project_id is not None:
                # Get titles for this project
                titles = self._db_manager.get_titles_by_project(self._selected_project_id)
                
                # Add to listbox
                for title in titles:
                    self._project_titles_list.insert(tk.END, title['title'])

    def _format_timestamp(self, timestamp: str) -> str:
        """Format a timestamp string for display.
        
        Args:
            timestamp: The timestamp to format
            
        Returns:
            Formatted timestamp string
        """
        if not timestamp:
            return ""
            
        try:
            if isinstance(timestamp, str):
                dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                dt = timestamp
                
            return dt.strftime("%Y-%m-%d %H:%M")
        except Exception as e:
            print(f"Error formatting timestamp: {e}")
            return str(timestamp)

    def _on_project_selected(self, event) -> None:
        """Handle project selection in treeview."""
        selection = self._projects_tree.selection()
        if selection:
            # Get selected project ID
            self._selected_project_id = int(selection[0])
            
            # Refresh titles for this project
            self._refresh_project_titles()

    def _on_title_selected(self, event) -> None:
        """Handle title selection in treeview."""
        # Get selected title IDs
        selection = self._titles_tree.selection()
        self._selected_title_ids = {int(item) for item in selection}

    def _on_search_changed(self, *args) -> None:
        """Handle search entry changes."""
        # Refresh titles with new search term
        self._refresh_titles()

    def _on_project_filter_changed(self, *args) -> None:
        """Handle project filter changes."""
        # Refresh titles with new filter
        self._refresh_titles()

    def _on_add_project(self) -> None:
        """Add a new project."""
        # Show dialog to get project name
        project_name = simpledialog.askstring(
            "Add Project", 
            "Enter new project name:",
            parent=self._window
        )
        
        if project_name:
            # Create project in database
            project_id = self._db_manager.create_project(project_name)
            
            if project_id:
                # Refresh data
                self._refresh_data()
                
                # Select the new project
                if self._projects_tree:
                    self._projects_tree.selection_set(str(project_id))
                    self._projects_tree.see(str(project_id))
            else:
                messagebox.showerror(
                    "Error",
                    "Failed to create project. The name may already exist.",
                    parent=self._window
                )

    def _on_rename_project(self) -> None:
        """Rename the selected project."""
        if not self._selected_project_id:
            messagebox.showwarning(
                "No Selection",
                "Please select a project to rename.",
                parent=self._window
            )
            return
        
        # Check if this is the default project (ID=1)
        if self._selected_project_id == 1:
            messagebox.showwarning(
                "Cannot Rename",
                "The default 'Misc' project cannot be renamed.",
                parent=self._window
            )
            return
        
        # Get current name
        current_name = self._projects_dict.get(self._selected_project_id, "")
        
        # Show dialog to get new project name
        new_name = simpledialog.askstring(
            "Rename Project", 
            "Enter new project name:",
            parent=self._window,
            initialvalue=current_name
        )
        
        if new_name and new_name != current_name:
            # Rename in database
            success = self._db_manager.rename_project(self._selected_project_id, new_name)
            
            if success:
                # Refresh data
                self._refresh_data()
            else:
                messagebox.showerror(
                    "Error",
                    "Failed to rename project. The name may already exist.",
                    parent=self._window
                )

    def _on_delete_project(self) -> None:
        """Delete the selected project."""
        if not self._selected_project_id:
            messagebox.showwarning(
                "No Selection",
                "Please select a project to delete.",
                parent=self._window
            )
            return
        
        # Check if this is the default project (ID=1)
        if self._selected_project_id == 1:
            messagebox.showwarning(
                "Cannot Delete",
                "The default 'Misc' project cannot be deleted.",
                parent=self._window
            )
            return
        
        # Get project name
        project_name = self._projects_dict.get(self._selected_project_id, "")
        
        # Confirm deletion
        result = messagebox.askyesnocancel(
            "Delete Project",
            f"Are you sure you want to delete project '{project_name}'?\n\n"
            f"- Click 'Yes' to delete the project and reassign its titles to 'Misc'\n"
            f"- Click 'No' to delete the project AND all its window titles\n"
            f"- Click 'Cancel' to abort",
            parent=self._window
        )
        
        if result is None:  # Cancel
            return
            
        # Delete in database
        success = self._db_manager.delete_project(self._selected_project_id, not result)
        
        if success:
            # Refresh data
            self._refresh_data()
            
            # Clear selection
            self._selected_project_id = None
        else:
            messagebox.showerror(
                "Error",
                "Failed to delete project.",
                parent=self._window
            )

    def _on_delete_titles(self) -> None:
        """Delete selected window titles."""
        if not self._selected_title_ids:
            messagebox.showwarning(
                "No Selection",
                "Please select titles to delete.",
                parent=self._window
            )
            return
            
        # Confirm deletion
        count = len(self._selected_title_ids)
        result = messagebox.askyesno(
            "Delete Titles",
            f"Are you sure you want to delete {count} window title{'s' if count > 1 else ''}?\n\n"
            f"This will also delete ALL log entries for these titles.",
            parent=self._window
        )
        
        if not result:
            return
            
        # Delete each title
        success_count = 0
        for title_id in self._selected_title_ids:
            if self._db_manager.delete_title(title_id):
                success_count += 1
                
        # Report results
        if success_count == count:
            messagebox.showinfo(
                "Success",
                f"Successfully deleted {success_count} window title{'s' if success_count > 1 else ''}.",
                parent=self._window
            )
        else:
            messagebox.showwarning(
                "Partial Success",
                f"Deleted {success_count} out of {count} window titles.",
                parent=self._window
            )
            
        # Refresh data
        self._refresh_data()
        
        # Clear selection
        self._selected_title_ids = set()

    def _on_reassign_titles(self) -> None:
        """Reassign selected window titles to a different project."""
        if not self._selected_title_ids:
            messagebox.showwarning(
                "No Selection",
                "Please select titles to reassign.",
                parent=self._window
            )
            return
            
        # Create dialog for project selection
        dialog = tk.Toplevel(self._window)
        dialog.title("Select Project")
        dialog.transient(self._window)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        # Create dialog contents
        ttk.Label(dialog, text="Select target project:").pack(padx=10, pady=(10, 5))
        
        # Project dropdown
        project_var = tk.StringVar()
        project_combo = ttk.Combobox(dialog, textvariable=project_var, state="readonly")
        project_combo["values"] = list(self._projects_dict.values())
        project_combo.pack(padx=10, pady=5, fill=tk.X)
        project_combo.current(0)  # Select first project
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(
            btn_frame, 
            text="Cancel", 
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        def on_confirm():
            # Find project ID by name
            project_name = project_var.get()
            project_id = None
            for pid, pname in self._projects_dict.items():
                if pname == project_name:
                    project_id = pid
                    break
                    
            if project_id is not None:
                # Reassign each title
                success_count = 0
                for title_id in self._selected_title_ids:
                    if self._db_manager.assign_project(title_id, project_id):
                        success_count += 1
                
                # Report results and refresh
                count = len(self._selected_title_ids)
                if success_count == count:
                    messagebox.showinfo(
                        "Success",
                        f"Successfully reassigned {success_count} window title{'s' if success_count > 1 else ''}.",
                        parent=self._window
                    )
                else:
                    messagebox.showwarning(
                        "Partial Success",
                        f"Reassigned {success_count} out of {count} window titles.",
                        parent=self._window
                    )
                
                self._refresh_data()
            
            dialog.destroy()
            
        ttk.Button(
            btn_frame, 
            text="Reassign", 
            command=on_confirm
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Position dialog relative to main window
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        parent_x = self._window.winfo_x()
        parent_y = self._window.winfo_y()
        parent_width = self._window.winfo_width()
        parent_height = self._window.winfo_height()
        
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2
        dialog.geometry(f"{width}x{height}+{x}+{y}")

    def _on_merge_titles(self) -> None:
        """Merge selected window titles into a new one."""
        if len(self._selected_title_ids) < 2:
            messagebox.showwarning(
                "Insufficient Selection",
                "Please select at least two titles to merge.",
                parent=self._window
            )
            return
        
        # Get selected titles and their IDs in selection order
        selected_titles = []
        title_id_map = {}  # Maps title string to title ID
        
        for item_id in self._titles_tree.selection():
            title_id = int(item_id)
            values = self._titles_tree.item(item_id, "values")
            title = values[1]  # Title is second column
            selected_titles.append(title)
            title_id_map[title] = title_id
        
        # Get the target title (first selected title)
        target_title = selected_titles[0]
        target_id = title_id_map[target_title]
        
        # The other title IDs to be merged (excluding the target)
        merge_ids = [tid for tid in self._selected_title_ids if tid != target_id]
        
        # Show confirmation dialog
        result = messagebox.askyesno(
            "Merge Titles",
            f"Merge {len(merge_ids)} titles into '{target_title}'?\n\n"
            f"This will move all log entries to the title '{target_title}' and delete the other titles.",
            parent=self._window
        )
        
        if not result:
            return
            
        # Perform merge
        success = self._db_manager.merge_titles([target_id] + merge_ids)
        
        if success:
            messagebox.showinfo(
                "Success",
                f"Successfully merged {len(merge_ids)} titles into '{target_title}'.",
                parent=self._window
            )
            
            # Refresh data
            self._refresh_data()
            
            # Clear selection
            self._selected_title_ids = set()
        else:
            messagebox.showerror(
                "Error",
                "Failed to merge titles.",
                parent=self._window
            )

    def _on_close(self) -> None:
        """Handle window close event."""
        if self._window:
            self._window.withdraw()  # Hide window rather than destroying it