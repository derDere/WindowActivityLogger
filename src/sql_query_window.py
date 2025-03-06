"""
SQL Query window for direct database access.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List, Any, Dict, TYPE_CHECKING
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageTk
from pygments import lex
from pygments.lexers import SqlLexer
from pygments.token import Token

# Import SQL constants
from sql_constants import (
    DEFAULT_QUERY, 
    DELETE_OLD_LOGS, 
    DELETE_DEMO_TITLES, 
    SELECT_PROJECTS, 
    SELECT_TITLES,
    SELECT_LOGS,
    SELECT_DEMO_LOGS,
    MERGE_SIMILAR_TITLES
)

if TYPE_CHECKING:
    from db_manager import DatabaseManager

class SQLText(tk.Text):
    """Text widget with SQL syntax highlighting"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tag_configure("keyword", foreground="#0000FF")
        self.tag_configure("string", foreground="#008000")
        self.tag_configure("number", foreground="#FF0000")
        self.tag_configure("comment", foreground="#808080")
        self.bind('<KeyRelease>', self._highlight)
        self.bind('<Enter>', self._highlight)

    def _highlight(self, event=None):
        """Apply syntax highlighting to the text"""
        text = self.get("1.0", tk.END)
        self.tag_remove("keyword", "1.0", tk.END)
        self.tag_remove("string", "1.0", tk.END)
        self.tag_remove("number", "1.0", tk.END)
        self.tag_remove("comment", "1.0", tk.END)

        for token, content in lex(text, SqlLexer()):
            if not content:
                continue
            current_index = self.search(content, "1.0", tk.END)
            while current_index:
                if token in Token.Keyword:
                    self.tag_add("keyword", current_index, f"{current_index}+{len(content)}c")
                elif token in Token.Literal.String:
                    self.tag_add("string", current_index, f"{current_index}+{len(content)}c")
                elif token in Token.Literal.Number:
                    self.tag_add("number", current_index, f"{current_index}+{len(content)}c")
                elif token in Token.Comment:
                    self.tag_add("comment", current_index, f"{current_index}+{len(content)}c")
                current_index = self.search(content, f"{current_index}+1c", tk.END)

class PanedWindowWithMinSize(ttk.PanedWindow):
    """PanedWindow with minimum size enforcement for panes"""
    def __init__(self, master=None, **kw):
        super().__init__(master, **kw)
        self._min_sizes = {}  # Maps pane widget to minimum size
        
    def add(self, child, min_size=0, **kw):
        """Add a child with minimum size constraint"""
        super().add(child, **kw)
        self._min_sizes[child] = min_size
        
    def _update_sash_position(self, sash_index):
        """Update sash position to respect minimum sizes"""
        if not self._min_sizes:
            return
            
        # Get current pane positions
        sashes = [self.sashpos(i) for i in range(len(self.panes()) - 1)]
        
        # Ensure minimum size for first pane
        if sash_index == 0 and len(self.panes()) > 0:
            first_pane = self.panes()[0]
            min_size = self._min_sizes.get(first_pane, 0)
            if sashes[0] < min_size:
                self.sashpos(0, min_size)
                
        # Ensure minimum size for middle panes
        if 0 < sash_index < len(self.panes()) - 1:
            pane = self.panes()[sash_index]
            min_size = self._min_sizes.get(pane, 0)
            if sashes[sash_index] - sashes[sash_index - 1] < min_size:
                self.sashpos(sash_index, sashes[sash_index - 1] + min_size)
                
        # Ensure minimum size for last pane
        if sash_index == len(self.panes()) - 2 and len(self.panes()) > 1:
            last_pane = self.panes()[-1]
            min_size = self._min_sizes.get(last_pane, 0)
            paned_height = self.winfo_height()
            if paned_height - sashes[-1] < min_size:
                self.sashpos(len(sashes) - 1, paned_height - min_size)

class SQLQueryWindow:
    def __init__(self, db_manager: 'DatabaseManager'):
        """Initialize the SQL query window.

        Args:
            db_manager: Database manager instance
        """
        self._db_manager = db_manager
        self._window: Optional[tk.Toplevel] = None
        self._query_text: Optional[tk.Text] = None
        self._result_notebook: Optional[ttk.Notebook] = None
        self._query_dropdown: Optional[ttk.Combobox] = None
        self._last_edited_query: str = DEFAULT_QUERY
        self._paned_window: Optional[PanedWindowWithMinSize] = None
        self._MIN_PANE_SIZE = 50  # Minimum size in pixels

    @property
    def _app(self):
        """Get the application instance safely."""
        return self._db_manager._app

    def show(self) -> None:
        """Show the SQL query window."""
        if self._window is None:
            self._window = tk.Toplevel(self._app.root)
            self._window.title("[W.A.L.] - SQL Query")
            self._window.minsize(800, 600)
            self._window.protocol("WM_DELETE_WINDOW", self.hide)

            # Set window icon
            icon_path = Path(__file__).parent / "resources" / "icon.ico"
            if (icon_path.exists()):
                self._window.iconbitmap(str(icon_path))

            # Create main container
            main_frame = ttk.Frame(self._window, padding="10")
            main_frame.pack(fill=tk.BOTH, expand=True)

            # Top frame for query input
            top_frame = ttk.Frame(main_frame)
            top_frame.pack(fill=tk.X, pady=(0, 10))

            # Execute button
            execute_btn = ttk.Button(top_frame, text="Execute Query", command=self._execute_query)
            execute_btn.pack(side=tk.LEFT, padx=(0, 10))

            # Predefined queries dropdown
            query_options = [
                "<Last>",
                "<Reset>",
                "<New>",
                "Show Tables",
                "Delete Old Logs",
                "Delete DEMO Titles",
                "Select Projects",
                "Select Titles", 
                "Select Logs",
                "Select DEMO Logs",
                "Merge Similar Titles"
            ]
            
            self._query_dropdown = ttk.Combobox(top_frame, values=query_options, state="readonly", width=20)
            self._query_dropdown.pack(side=tk.LEFT)
            self._query_dropdown.current(3)  # Default to "Show Tables"
            self._query_dropdown.bind("<<ComboboxSelected>>", self._on_query_selected)
            
            # Create vertically oriented paned window for resizable areas
            self._paned_window = PanedWindowWithMinSize(main_frame, orient=tk.VERTICAL)
            self._paned_window.pack(fill=tk.BOTH, expand=True)

            # Query frame (top pane)
            query_frame = ttk.Frame(self._paned_window)
            
            # Query text area with syntax highlighting
            self._query_text = SQLText(query_frame, wrap=tk.WORD)
            self._query_text.pack(fill=tk.BOTH, expand=True)
            self._query_text.insert("1.0", DEFAULT_QUERY)
            self._query_text._highlight()  # Initial highlighting
            
            # Results frame (bottom pane)
            results_frame = ttk.Frame(self._paned_window)
            
            # Result notebook for multiple result sets
            self._result_notebook = ttk.Notebook(results_frame)
            self._result_notebook.pack(fill=tk.BOTH, expand=True)
            
            # Add frames to paned window with minimum sizes and set initial weights
            # Use weight=1 for text box and weight=2 for results view to get 1/3 and 2/3 ratio
            self._paned_window.add(query_frame, min_size=self._MIN_PANE_SIZE, weight=1)
            self._paned_window.add(results_frame, min_size=self._MIN_PANE_SIZE, weight=2)
            
            # Set the initial position of the sash after the window is updated
            self._window.update_idletasks()
            total_height = self._paned_window.winfo_height()
            if total_height > 0:  # Ensure we have a valid height
                sash_pos = total_height // 3  # Position at 1/3 of the height
                self._paned_window.sashpos(0, sash_pos)
            
            # Bind sash movement to enforce minimum sizes
            self._paned_window.bind("<ButtonRelease-1>", self._on_sash_moved)
            
            # Initialize last_edited_query with the default
            self._last_edited_query = DEFAULT_QUERY
            
            # Track text modifications using a separate handler rather than <<Modified>> event
            # which doesn't work consistently across all platforms
            self._query_text.bind("<KeyRelease>", self._on_text_modified)

            # Center window
            self._window.update_idletasks()
            width = self._window.winfo_width()
            height = self._window.winfo_height()
            x = (self._window.winfo_screenwidth() - width) // 2
            y = (self._window.winfo_screenheight() - height) // 2
            self._window.geometry(f"{width}x{height}+{x}+{y}")
        else:
            self._window.lift()
            self._window.focus_force()
    
    def _on_sash_moved(self, event):
        """Handle sash movement to enforce minimum sizes"""
        if self._paned_window:
            for i in range(len(self._paned_window.panes()) - 1):
                self._paned_window._update_sash_position(i)

    def _on_text_modified(self, event=None):
        """Handle text modifications."""
        if self._query_text:
            # Save the current text as the last edited query
            current_text = self._query_text.get("1.0", tk.END).strip()
            self._last_edited_query = current_text

    def _on_query_selected(self, event=None):
        """Handle selection from the query dropdown."""
        if not self._query_text or not self._query_dropdown:
            return
        
        selected = self._query_dropdown.get()
        
        # Clear the current query
        self._query_text.delete("1.0", tk.END)
        
        # Set the query based on selection
        if selected == "<Last>":
            # Get the last query from configuration
            last_query = self._app.configuration.get_last_sql_query()
            if last_query:
                self._query_text.insert("1.0", last_query)
            else:
                self._query_text.insert("1.0", DEFAULT_QUERY)
        elif selected == "<Reset>":
            # Restore the last edited query
            self._query_text.insert("1.0", self._last_edited_query)
        elif selected == "<New>":
            # Create a new empty query with current date comment
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_query = f"/* New query created on {current_date} */\n\n"
            self._query_text.insert("1.0", new_query)
        elif selected == "Show Tables":
            self._query_text.insert("1.0", DEFAULT_QUERY)
        elif selected == "Delete Old Logs":
            self._query_text.insert("1.0", DELETE_OLD_LOGS)
        elif selected == "Delete DEMO Titles":
            self._query_text.insert("1.0", DELETE_DEMO_TITLES)
        elif selected == "Select Projects":
            self._query_text.insert("1.0", SELECT_PROJECTS)
        elif selected == "Select Titles":
            self._query_text.insert("1.0", SELECT_TITLES)
        elif selected == "Select Logs":
            self._query_text.insert("1.0", SELECT_LOGS)
        elif selected == "Select DEMO Logs":
            self._query_text.insert("1.0", SELECT_DEMO_LOGS)
        elif selected == "Merge Similar Titles":
            self._query_text.insert("1.0", MERGE_SIMILAR_TITLES)
            
        # Apply syntax highlighting
        self._query_text._highlight()
        
        # Reset selection to avoid auto-reselection
        self._query_dropdown.selection_clear()

    def hide(self) -> None:
        """Hide the SQL query window."""
        if self._window:
            self._window.destroy()
            self._window = None
            self._query_text = None
            self._result_notebook = None
            self._query_dropdown = None
            self._paned_window = None

    def _execute_query(self) -> None:
        """Execute the SQL query and display results."""
        if not self._query_text or not self._result_notebook:
            return

        # Clear previous results
        for tab in self._result_notebook.tabs():
            self._result_notebook.forget(tab)

        # Get query text
        query = self._query_text.get("1.0", tk.END).strip()
        if not query:
            return

        try:
            # Execute query using database connection
            with self._db_manager._get_connection() as conn:
                cursor = conn.cursor()
                
                # Start a transaction
                conn.execute("BEGIN")
                
                # Split and execute multiple statements
                statements = [stmt.strip() for stmt in query.split(';') if stmt.strip()]
                result_count = 0
                had_success = False
                
                for statement in statements:
                    try:
                        cursor.execute(statement)
                        had_success = True  # Mark that at least one statement succeeded
                        
                        # Check if the statement returns results
                        if cursor.description:
                            # Create new tab for results
                            result_frame = ttk.Frame(self._result_notebook)
                            self._result_notebook.add(result_frame, text=f"Result {result_count + 1}")
                            
                            # Create treeview for results
                            columns = [desc[0] for desc in cursor.description]
                            tree = ttk.Treeview(result_frame, columns=columns, show="headings")
                            
                            # Configure columns
                            for col in columns:
                                tree.heading(col, text=col)
                                tree.column(col, width=100)  # Default width
                            
                            # Add scrollbars
                            vsb = ttk.Scrollbar(result_frame, orient="vertical", command=tree.yview)
                            hsb = ttk.Scrollbar(result_frame, orient="horizontal", command=tree.xview)
                            tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
                            
                            # Grid layout
                            tree.grid(column=0, row=0, sticky="nsew")
                            vsb.grid(column=1, row=0, sticky="ns")
                            hsb.grid(column=0, row=1, sticky="ew")
                            result_frame.grid_columnconfigure(0, weight=1)
                            result_frame.grid_rowconfigure(0, weight=1)
                            
                            # Add data
                            rows = cursor.fetchall()
                            for row in rows:
                                values = tuple(row[col] for col in columns)
                                tree.insert("", "end", values=values)
                            
                            result_count += 1
                        else:
                            # Non-query statement, show success in result area
                            result_frame = ttk.Frame(self._result_notebook)
                            self._result_notebook.add(result_frame, text=f"[W.A.L.] - Result {result_count + 1}")
                            success_label = ttk.Label(result_frame, text="Query executed successfully", foreground="green", wraplength=600)
                            success_label.pack(padx=10, pady=10)
                            result_count += 1
                            
                    except Exception as e:
                        # Rollback on error
                        conn.rollback()
                        
                        # Create error tab
                        error_frame = ttk.Frame(self._result_notebook)
                        self._result_notebook.add(error_frame, text=f"[W.A.L.] - Error {result_count + 1}")
                        error_label = ttk.Label(error_frame, text=str(e), foreground="red", wraplength=600)
                        error_label.pack(padx=10, pady=10)
                        result_count += 1
                        continue  # Continue with next statement instead of raising

                # If at least one statement executed successfully, store the query
                if had_success and statements:
                    self._app.configuration.set_last_sql_query(query)
                    self._app.configuration.save()

                # Commit the transaction if we had any successes
                if had_success:
                    conn.commit()

        except Exception as e:
            # Handle any unexpected errors
            error_frame = ttk.Frame(self._result_notebook)
            self._result_notebook.add(error_frame, text=f"[W.A.L.] - Error")
            error_label = ttk.Label(error_frame, text=str(e), foreground="red", wraplength=600)
            error_label.pack(padx=10, pady=10)