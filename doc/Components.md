# Components Overview

This document describes the main components of the Window Activity Logger system and their interactions.

## Core Components

### 1. Application (application.py)
- **Purpose**: Main application class coordinating all components
- **Key Functions**:
  - Initializes and manages component lifecycle
  - Processes UI events in main thread
  - Routes component communication
  - Handles configuration changes
- **Properties**:
  - root (Tk instance)
  - is_running
  - configuration
- **Methods**:
  - initialize()
  - start()
  - stop()
  - process_ui_events()
- **Dependencies**: All other components

### 2. Window Monitor (window_monitor.py)
- **Purpose**: Thread for monitoring active window titles
- **Key Functions**:
  - Polls active window at configurable interval
  - Detects UWP application names
  - Monitors system lock/sleep states
  - Provides thread-safe title change notifications
- **Properties**:
  - is_running
  - polling_interval
- **Methods**:
  - start()
  - stop()
  - set_title_changed_callback()
- **Dependencies**: Windows API (win32*)

### 3. Database Manager (db_manager.py)
- **Purpose**: Handles SQLite database operations
- **Key Functions**:
  - Manages database connections
  - Performs CRUD operations
  - Handles schema validation/repair
  - Provides data summaries
  - Manages projects and titles
- **Key Features**:
  - CRC32-based title deduplication
  - Automatic schema validation
  - Database backup/repair
  - Thread-safe operations
- **Dependencies**: SQLite3

### 4. Configuration Manager (config_manager.py)
- **Purpose**: Manages application settings
- **Key Functions**:
  - Reads/writes config.json
  - Validates settings
  - Notifies components of changes
  - Manages update handlers
- **Settings**:
  - Database path
  - Polling interval
  - Regex patterns
- **Location**: User's Documents folder

### 5. System Tray Interface (system_tray.py)
- **Purpose**: System tray presence
- **Key Functions**:
  - Shows tray icon
  - Provides context menu
  - Routes menu actions
  - Manages callbacks
- **Features**:
  - Thread-safe callback handling
  - Clean resource management
- **Dependencies**: pystray, PIL

## UI Components

### 1. Report Window (report_window.py)
- **Purpose**: Activity statistics display
- **Subcomponents**:
  - Time Range Selector
  - Project Distribution Chart
  - Project Summary Table
  - Title Summary Table
  - Project Assignment Controls
- **Features**:
  - Interactive project assignment
  - Real-time data updates
  - Flexible time ranges
  - Export functionality
- **Dependencies**: Database Manager, HTML Export Generator

### 2. Settings Window (settings_window.py)
- **Purpose**: Configuration interface
- **Subcomponents**:
  - Database Location Selector
  - Polling Interval Control
  - Pattern Management Grid
- **Features**:
  - Real-time validation
  - Pattern syntax checking
  - File path browsing
- **Dependencies**: Configuration Manager

### 3. SQL Query Window (sql_query_window.py)
- **Purpose**: Direct database access
- **Features**:
  - SQL syntax highlighting
  - Multi-query support
  - Result set tabs
  - Error handling
- **Dependencies**: Database Manager, Pygments

### 4. HTML Export Generator (html_export.py)
- **Purpose**: Report generation
- **Features**:
  - SVG chart generation
  - Responsive layout
  - Self-contained output
  - Clean styling
- **Dependencies**: Database Manager

## Component Interactions

### Startup Sequence
1. Application initializes Configuration Manager
2. Configuration Manager loads/validates settings
3. Database Manager initializes with configuration
4. Window Monitor starts with configuration
5. System Tray Interface created
6. UI components created but not shown
7. Application enters event loop

### Data Flow
1. Window Monitor → Application → Database Manager
   - Title changes with timestamps
   - System state changes

2. Database Manager → UI Components
   - Activity summaries
   - Project data
   - Query results

3. Configuration Manager → All Components
   - Settings updates via event system
   - Real-time configuration changes

4. UI Components → Database Manager
   - Project assignments
   - Data queries
   - Schema modifications

### State Management
- Application coordinates component states
- Database Manager ensures data consistency
- Configuration Manager maintains settings
- Window Monitor tracks system state
- UI Components reflect current data

## Error Handling
- Each component implements error recovery
- Database Manager provides backup/repair
- Configuration Manager validates changes
- Window Monitor handles system state errors
- UI Components show error messages
- All errors logged to terminal
