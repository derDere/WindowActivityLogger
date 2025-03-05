"""
SQL Query window for direct database access.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List, Any, Dict, TYPE_CHECKING
from pathlib import Path
from PIL import Image, ImageTk

if TYPE_CHECKING:
    from db_manager import DatabaseManager

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

    @property
    def _app(self):
        """Get the application instance safely."""
        return self._db_manager._app

    def show(self) -> None:
        """Show the SQL query window."""
        if self._window is None:
            self._window = tk.Toplevel(self._app.root)
            self._window.title("SQL Query")
            self._window.minsize(800, 600)
            self._window.protocol("WM_DELETE_WINDOW", self.hide)

            # Set window icon
            icon_path = Path(__file__).parent / "resources" / "icon.ico"
            if icon_path.exists():
                self._window.iconbitmap(str(icon_path))

            # Create main container
            main_frame = ttk.Frame(self._window, padding="10")
            main_frame.pack(fill=tk.BOTH, expand=True)

            # Top frame for query input
            top_frame = ttk.Frame(main_frame)
            top_frame.pack(fill=tk.X, pady=(0, 10))

            # Execute button
            execute_btn = ttk.Button(top_frame, text="Execute Query", command=self._execute_query)
            execute_btn.pack(side=tk.LEFT)

            # Query text area
            self._query_text = tk.Text(main_frame, height=10, wrap=tk.WORD)
            self._query_text.pack(fill=tk.X, pady=(0, 10))
            self._query_text.insert("1.0", """/* WARNING: Only modify these SQL queries if you know what you are doing.
   Incorrect queries could potentially damage your database. */

SELECT name FROM sqlite_master;""")

            # Result notebook for multiple result sets
            self._result_notebook = ttk.Notebook(main_frame)
            self._result_notebook.pack(fill=tk.BOTH, expand=True)

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

    def hide(self) -> None:
        """Hide the SQL query window."""
        if self._window:
            self._window.destroy()
            self._window = None
            self._query_text = None
            self._result_notebook = None

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
                
                # Split and execute multiple statements
                statements = [stmt.strip() for stmt in query.split(';') if stmt.strip()]
                result_count = 0
                
                for statement in statements:
                    try:
                        cursor.execute(statement)
                        
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
                                # Use the original column name from the result set
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
                            
                            # Add data - properly extract values from SQLite Row objects
                            rows = cursor.fetchall()
                            for row in rows:
                                # Convert SQLite Row to tuple of values
                                values = tuple(row[col] for col in columns)
                                tree.insert("", "end", values=values)
                            
                            result_count += 1
                    except Exception as e:
                        # Create error tab
                        error_frame = ttk.Frame(self._result_notebook)
                        self._result_notebook.add(error_frame, text=f"Error {result_count + 1}")
                        error_label = ttk.Label(error_frame, text=str(e), foreground="red", wraplength=600)
                        error_label.pack(padx=10, pady=10)
                        result_count += 1

                if result_count == 0:
                    # Show success message for non-query statements
                    messagebox.showinfo("Success", "Query executed successfully")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to execute query: {e}")