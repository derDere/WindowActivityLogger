"""
Database manager for handling SQLite operations and schema management.
"""
import contextlib
import hashlib
import os
import shutil
import sqlite3
import zlib
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Iterator, Any, Dict, TYPE_CHECKING, Set

if TYPE_CHECKING:
    from application import Application

class DatabaseManager:
    # SQL statements for schema creation
    _CREATE_TABLES_SQL = [
        """
        CREATE TABLE IF NOT EXISTS Projects (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            ProjectName TEXT NOT NULL UNIQUE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS WindowTitles (
            ID INTEGER PRIMARY KEY,  -- CRC32 hash of title
            Title TEXT NOT NULL UNIQUE,
            ProjectID INTEGER,
            FOREIGN KEY (ProjectID) REFERENCES Projects(ID)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS WindowLog (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            TitleID INTEGER NOT NULL,
            StartTimestamp DATETIME NOT NULL,
            EndTimestamp DATETIME,
            FOREIGN KEY (TitleID) REFERENCES WindowTitles(ID)
        )
        """
    ]

    # SQL for initial data
    _INITIAL_DATA_SQL = """
        INSERT OR IGNORE INTO Projects (ID, ProjectName) VALUES (1, 'Misc')
    """

    def __init__(self, app: 'Application'):
        """Initialize the database manager.

        Args:
            app: Parent application instance
        """
        self._app = app
        self._db_path = app.configuration.get_database_path()

    @contextlib.contextmanager
    def _get_connection(self) -> Iterator[sqlite3.Connection]:
        """Get a database connection within a context.

        Yields:
            A database connection that will be automatically closed
        """
        conn = None
        try:
            conn = sqlite3.connect(
                self._db_path,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            conn.row_factory = sqlite3.Row
            yield conn
        finally:
            if conn:
                conn.close()

    def _generate_title_id(self, title: str) -> int:
        """Generate a numeric ID for a window title using CRC32.

        Args:
            title: The window title to hash

        Returns:
            A positive 32-bit integer hash of the title
        """
        return zlib.crc32(title.encode()) & 0xFFFFFFFF

    def initialize(self) -> bool:
        """Initialize the database and create schema if needed.

        Returns:
            bool: True if initialization was successful, False otherwise
        """
        try:
            # Register for configuration updates
            self._app.configuration.add_update_handler(self._handle_config_update)

            # Create directory if it doesn't exist
            os.makedirs(self._db_path.parent, exist_ok=True)

            # Create schema and initial data
            with self._get_connection() as conn:
                # Create schema
                for sql in self._CREATE_TABLES_SQL:
                    conn.execute(sql)

                # Insert initial data
                conn.execute(self._INITIAL_DATA_SQL)

                # Set end timestamp of any existing open window logs
                current_time = datetime.now()
                conn.execute(
                    """
                    UPDATE WindowLog
                    SET EndTimestamp = ?
                    WHERE EndTimestamp IS NULL
                    """,
                    (current_time,)
                )

                conn.commit()
            return True

        except Exception as e:
            print(f"Error initializing database: {e}")
            return False

    def _handle_config_update(self) -> None:
        """Handle configuration updates."""
        try:
            new_path = self._app.configuration.get_database_path()
            if new_path != self._db_path:
                # Save the old path in case we need to restore it
                old_path = self._db_path
                self._db_path = new_path

                # If the new database exists, validate and repair if needed
                if new_path.exists():
                    if not self.validate_schema():
                        # Invalid schema, attempt backup and repair
                        if not self.backup_and_repair():
                            # If repair failed, restore old path and report error
                            self._db_path = old_path
                            print("Failed to repair database at new location, reverting to previous database")
                            return
                else:
                    # New database file, create directory and initialize
                    try:
                        os.makedirs(new_path.parent, exist_ok=True)
                        if not self.initialize():
                            # If initialization failed, restore old path
                            self._db_path = old_path
                            print("Failed to initialize new database, reverting to previous database")
                            return
                    except Exception as e:
                        self._db_path = old_path
                        print(f"Error creating new database: {e}")
                        return

        except Exception as e:
            print(f"Error handling configuration update: {e}")

    def log_window_title(self, title: str, timestamp: datetime) -> bool:
        """Log a window title change.

        Args:
            title: The window title to log
            timestamp: When the title was active

        Returns:
            bool: True if logging was successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                # Generate title ID (CRC32 hash)
                title_id = self._generate_title_id(title)

                # Insert or ignore title
                conn.execute(
                    "INSERT OR IGNORE INTO WindowTitles (ID, Title, ProjectID) VALUES (?, ?, 1)",
                    (title_id, title)
                )

                # Update end timestamp of previous log entry
                conn.execute(
                    """
                    UPDATE WindowLog
                    SET EndTimestamp = ?
                    WHERE EndTimestamp IS NULL
                    """,
                    (timestamp,)
                )

                # Insert new log entry
                conn.execute(
                    "INSERT INTO WindowLog (TitleID, StartTimestamp) VALUES (?, ?)",
                    (title_id, timestamp)
                )

                conn.commit()
                return True

        except Exception as e:
            print(f"Error logging window title: {e}")
            return False

    def get_title_summary(self, start_time: datetime, end_time: datetime) -> List[Tuple[str, float, int]]:
        """Get summary of window titles and their durations in seconds.

        Args:
            start_time: Start of the period to summarize
            end_time: End of the period to summarize

        Returns:
            List of tuples containing (title, duration_in_seconds)
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT
                        wt.Title,
                        SUM(
                            CASE
                                WHEN wl.EndTimestamp IS NULL THEN
                                    strftime('%s', ?) - strftime('%s', wl.StartTimestamp)
                                ELSE
                                    strftime('%s', wl.EndTimestamp) - strftime('%s', wl.StartTimestamp)
                            END
                        ) as duration,
                        wt.ProjectID
                    FROM WindowLog wl
                    JOIN WindowTitles wt ON wl.TitleID = wt.ID
                    WHERE wl.StartTimestamp <= ?
                    AND (wl.EndTimestamp >= ? OR wl.EndTimestamp IS NULL)
                    GROUP BY wt.Title
                    ORDER BY duration DESC
                    """,
                    (end_time, end_time, start_time)
                )
                return [(row['Title'], row['duration'], row["ProjectID"]) for row in cursor.fetchall()]

        except Exception as e:
            print(f"Error getting title summary: {e}")
            return []

    def get_project_summary(self, start_time: datetime, end_time: datetime) -> List[Tuple[int, str, float]]:
        """Get summary of projects and their durations in seconds.

        Args:
            start_time: Start of the period to summarize
            end_time: End of the period to summarize

        Returns:
            List of tuples containing (project_name, duration_in_seconds)
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT
                        p.ID,
                        p.ProjectName,
                        SUM(
                            CASE
                                WHEN wl.EndTimestamp IS NULL THEN
                                    strftime('%s', ?) - strftime('%s', wl.StartTimestamp)
                                ELSE
                                    strftime('%s', wl.EndTimestamp) - strftime('%s', wl.StartTimestamp)
                            END
                        ) as duration
                    FROM WindowLog wl
                    JOIN WindowTitles wt ON wl.TitleID = wt.ID
                    JOIN Projects p ON wt.ProjectID = p.ID
                    WHERE wl.StartTimestamp <= ?
                    AND (wl.EndTimestamp >= ? OR wl.EndTimestamp IS NULL)
                    GROUP BY p.ProjectName
                    HAVING duration > 0
                    ORDER BY duration DESC
                    """,
                    (end_time, end_time, start_time)
                )
                return [(row["ID"], row['ProjectName'], row['duration']) for row in cursor.fetchall()]

        except Exception as e:
            print(f"Error getting project summary: {e}")
            return []

    def assign_project(self, title_id: int, project_id: int) -> bool:
        """Assign a window title to a project.

        Args:
            title_id: Hash ID of the window title (numeric)
            project_id: ID of the project to assign

        Returns:
            bool: True if assignment was successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                conn.execute(
                    "UPDATE WindowTitles SET ProjectID = ? WHERE ID = ?",
                    (project_id, title_id)
                )
                conn.commit()
                return True

        except Exception as e:
            print(f"Error assigning project: {e}")
            return False

    def create_project(self, project_name: str) -> Optional[int]:
        """Create a new project.

        Args:
            project_name: Name of the project to create

        Returns:
            ProjectID if creation was successful, None otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO Projects (ProjectName) VALUES (?)",
                    (project_name,)
                )
                conn.commit()
                return cursor.lastrowid

        except Exception as e:
            print(f"Error creating project: {e}")
            return None

    def rename_project(self, project_id: int, new_name: str) -> bool:
        """Rename a project.

        Args:
            project_id: ID of the project to rename
            new_name: New name for the project

        Returns:
            bool: True if rename was successful, False otherwise
        """
        try:
            # Don't allow renaming the default project
            if project_id == 1:
                print("Cannot rename the default project")
                return False

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE Projects SET ProjectName = ? WHERE ID = ?",
                    (new_name, project_id)
                )
                conn.commit()
                return cursor.rowcount > 0

        except Exception as e:
            print(f"Error renaming project: {e}")
            return False

    def delete_project(self, project_id: int, delete_titles: bool = False) -> bool:
        """Delete a project and handle its window titles.

        Args:
            project_id: ID of the project to delete
            delete_titles: If True, delete all associated window titles,
                         if False, reassign them to the default project

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            # Don't allow deleting the default project
            if project_id == 1:
                print("Cannot delete the default project")
                return False

            with self._get_connection() as conn:
                cursor = conn.cursor()

                if delete_titles:
                    # First delete all window logs for titles in this project
                    cursor.execute(
                        """
                        DELETE FROM WindowLog
                        WHERE TitleID IN (
                            SELECT ID FROM WindowTitles WHERE ProjectID = ?
                        )
                        """,
                        (project_id,)
                    )

                    # Then delete all titles in this project
                    cursor.execute(
                        "DELETE FROM WindowTitles WHERE ProjectID = ?",
                        (project_id,)
                    )
                else:
                    # Reassign all titles to the default project (ID = 1)
                    cursor.execute(
                        "UPDATE WindowTitles SET ProjectID = 1 WHERE ProjectID = ?",
                        (project_id,)
                    )

                # Finally delete the project
                cursor.execute(
                    "DELETE FROM Projects WHERE ID = ?",
                    (project_id,)
                )

                conn.commit()
                return cursor.rowcount > 0

        except Exception as e:
            print(f"Error deleting project: {e}")
            return False

    def validate_schema(self) -> bool:
        """Validate database schema.

        Returns:
            bool: True if schema is valid, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Check each table exists with correct columns
                tables = {
                    "Projects": {"ID", "ProjectName"},
                    "WindowTitles": {"ID", "Title", "ProjectID"},
                    "WindowLog": {"ID", "TitleID", "StartTimestamp", "EndTimestamp"}
                }

                for table, expected_columns in tables.items():
                    # Get table info
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = {row['name'] for row in cursor.fetchall()}

                    # Check if all expected columns exist
                    if not expected_columns.issubset(columns):
                        return False

                # Verify foreign key constraints
                cursor.execute("PRAGMA foreign_key_check")
                if cursor.fetchone() is not None:
                    return False

                return True

        except Exception as e:
            print(f"Error validating schema: {e}")
            return False

    def backup_and_repair(self) -> bool:
        """Create backup of current database and repair schema.

        Returns:
            bool: True if backup and repair was successful, False otherwise
        """
        try:
            # Create backup with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self._db_path.with_name(f"{self._db_path.stem}_backup_{timestamp}{self._db_path.suffix}")

            if self._db_path.exists():
                shutil.copy2(self._db_path, backup_path)
                self._db_path.unlink()  # Remove invalid database

            # Reinitialize database
            return self.initialize()

        except Exception as e:
            print(f"Error during backup and repair: {e}")
            return False

    def get_projects(self) -> Dict[int, str]:
        """Get dictionary of project IDs to names.

        Returns:
            Dictionary mapping project IDs to their names, sorted by name
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT ID, ProjectName
                    FROM Projects
                    ORDER BY ProjectName
                    """
                )
                return {row['ID']: row['ProjectName'] for row in cursor.fetchall()}

        except Exception as e:
            print(f"Error getting projects: {e}")
            return {}

    def get_all_titles(self) -> List[Dict[str, Any]]:
        """Get all window titles with their project assignments.

        Returns:
            List of dictionaries containing title information
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT 
                        wt.ID, 
                        wt.Title, 
                        wt.ProjectID,
                        p.ProjectName,
                        COUNT(wl.ID) as LogCount,
                        MIN(wl.StartTimestamp) as FirstSeen,
                        MAX(IFNULL(wl.EndTimestamp, CURRENT_TIMESTAMP)) as LastSeen
                    FROM WindowTitles wt
                    JOIN Projects p ON wt.ProjectID = p.ID
                    LEFT JOIN WindowLog wl ON wt.ID = wl.TitleID
                    GROUP BY wt.ID, wt.Title, wt.ProjectID
                    ORDER BY wt.Title
                    """
                )
                
                result = []
                for row in cursor.fetchall():
                    result.append({
                        'id': row['ID'],
                        'title': row['Title'],
                        'project_id': row['ProjectID'],
                        'project_name': row['ProjectName'],
                        'log_count': row['LogCount'],
                        'first_seen': row['FirstSeen'],
                        'last_seen': row['LastSeen']
                    })
                return result

        except Exception as e:
            print(f"Error getting all titles: {e}")
            return []

    def delete_title(self, title_id: int) -> bool:
        """Delete a window title and all its log entries.

        Args:
            title_id: ID of the window title to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # First delete all associated log entries
                cursor.execute(
                    "DELETE FROM WindowLog WHERE TitleID = ?",
                    (title_id,)
                )
                
                # Then delete the title itself
                cursor.execute(
                    "DELETE FROM WindowTitles WHERE ID = ?",
                    (title_id,)
                )
                
                conn.commit()
                return cursor.rowcount > 0

        except Exception as e:
            print(f"Error deleting title: {e}")
            return False

    def merge_titles(self, title_ids: List[int]) -> bool:
        """Merge multiple window titles into a new one.

        Args:
            title_ids: List of title IDs to merge. The first one is the target.

        Returns:
            bool: True if merge was successful, False otherwise
        """
        if not title_ids or len(title_ids) < 2:
            print("At least two titles must be selected for merging")
            return False

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Get info about the titles to be merged
                title_ids_str = ','.join(['?'] * len(title_ids))
                cursor.execute(
                    f"""
                    SELECT ID, Title, ProjectID
                    FROM WindowTitles
                    WHERE ID IN ({title_ids_str})
                    """,
                    title_ids
                )
                titles_info = cursor.fetchall()
                
                if len(titles_info) < 2:
                    print("Not enough valid titles found for merging")
                    return False
                
                # First ID in the list is our target ID that we want to keep
                target_id = title_ids[0]
                
                # Get the target title's project ID
                target_project_id = None
                for row in titles_info:
                    if row['ID'] == target_id:
                        target_project_id = row['ProjectID']
                        break
                
                if target_project_id is None:
                    print(f"Target title ID {target_id} not found")
                    return False
                
                # IDs to remove (all except the target)
                ids_to_remove = title_ids[1:]
                to_remove_str = ','.join(['?'] * len(ids_to_remove))
                
                # Update all log entries from old titles to point to the target one
                if ids_to_remove:
                    cursor.execute(
                        f"""
                        UPDATE WindowLog
                        SET TitleID = ?
                        WHERE TitleID IN ({to_remove_str})
                        """,
                        [target_id] + ids_to_remove
                    )
                    
                    # Delete the old titles
                    cursor.execute(
                        f"""
                        DELETE FROM WindowTitles
                        WHERE ID IN ({to_remove_str})
                        """,
                        ids_to_remove
                    )
                
                conn.commit()
                return True

        except Exception as e:
            print(f"Error merging titles: {e}")
            return False

    def get_log_entries_count(self) -> Dict[int, int]:
        """Get the count of log entries for each window title.

        Returns:
            Dictionary mapping title ID to count of log entries
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT TitleID, COUNT(*) as count
                    FROM WindowLog
                    GROUP BY TitleID
                    """
                )
                return {row['TitleID']: row['count'] for row in cursor.fetchall()}

        except Exception as e:
            print(f"Error getting log entries count: {e}")
            return {}

    def get_titles_by_project(self, project_id: int) -> List[Dict[str, Any]]:
        """Get all titles assigned to a specific project.

        Args:
            project_id: ID of the project

        Returns:
            List of dictionaries containing title information
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT ID, Title
                    FROM WindowTitles
                    WHERE ProjectID = ?
                    ORDER BY Title
                    """,
                    (project_id,)
                )
                
                titles = []
                for row in cursor.fetchall():
                    titles.append({
                        'id': row['ID'],
                        'title': row['Title']
                    })
                return titles

        except Exception as e:
            print(f"Error getting titles by project: {e}")
            return []
