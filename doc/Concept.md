# Window Activity Logger

## Project Overview
A Python-based background service that monitors and logs active window titles on Windows systems to help track time spent on different applications and projects.

## Core Functionality
- Runs as a background process on Windows with system tray icon
- Monitors active window titles at configurable intervals (default: 30 seconds)
- Records window title changes with start and end timestamps
- Stores data in SQLite database within user's Documents folder
- Provides visual activity reports with interactive pie chart and detailed tables
- Project-based time tracking with flexible project assignment
- Configurable title filtering using regex patterns
- Syntax-highlighted SQL query interface for direct database access
- HTML report export with embedded SVG charts

## Technical Specifications

### Database Structure (SQLite)
- Located in: `%USERPROFILE%\Documents\WindowLogger\activity.db`
- Table Structure:
  1. WindowTitles:
     - ID (Primary Key, CRC32 hash of title)
     - Title (Text, Unique)
     - ProjectID (Foreign Key to Projects)

  2. WindowLog:
     - ID (Primary Key, Autoincrement)
     - TitleID (Foreign Key to WindowTitles)
     - StartTimestamp (DateTime)
     - EndTimestamp (DateTime, Nullable)

  3. Projects:
     - ID (Primary Key, Autoincrement)
     - ProjectName (Text, Unique)
     - Initial record: "Misc" project (ID: 1)

### User Interface
1. System Tray Icon
   - Context Menu Options:
     - Show Report Window
     - Show Settings
     - Show SQL Query
     - Exit Application

2. Report Window
   - Time Range Selector (Dropdown):
     - Day
     - Week
     - Month
   - Interactive Pie Chart:
     - Project time distribution
     - Hover tooltips with details
     - Auto-hiding small slice labels
   - Project Summary Table:
     - Project Name
     - Total Time
     - Only shows active projects
   - Title Summary Table:
     - Window Title
     - Total Time
     - Project Assignment (Interactive dropdown)
     - Instant project creation
   - Export to HTML button
   - Manual refresh button

3. Settings Window
   - Database file path with browse button
   - Title polling interval setting
   - Regex Pattern Management:
     - Add/Remove patterns
     - Pattern validation
     - Real-time syntax checking

4. SQL Query Window
   - Syntax-highlighted SQL editor
   - Multi-query support (semicolon-separated)
   - Results displayed in scrollable grids
   - Error handling with detailed messages
   - Support for non-query statements

### Configuration
- JSON file stored in `%USERPROFILE%\Documents\WindowLogger\config.json`
- Settings:
  - Database path (string)
  - Polling interval (integer, seconds)
  - Ignore patterns (array of regex strings)

### HTML Export
- Self-contained single file
- Features:
  - Embedded SVG pie chart
  - Interactive tooltips
  - Responsive layout
  - Clean, modern styling
  - Project and title summaries
  - Timestamp range display

## Technical Requirements
- Python 3.10 or higher
- Windows Operating System
- Dependencies:
  - pywin32: Windows API access
  - pystray: System tray functionality
  - Pillow: Image handling and charts
  - pygments: SQL syntax highlighting

## Implementation Notes
- Event-driven architecture
- Thread-safe operations
- Efficient database queries with proper indexing
- Automated database repair/backup
- Smart window title detection for UWP apps
- Configurable runtime settings
- Project-based organization
- Data validation throughout
- Error handling and recovery
