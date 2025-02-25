# Components Overview

This document describes the main components of the Window Activity Logger system and their interactions.

## Core Components

### 1. Window Monitor Thread
- **Purpose**: Background thread that monitors active window titles
- **Key Functions**:
  - Runs in background thread with configurable interval
  - Detects window title changes and system states
  - Triggers title changed events with timestamps
  - Monitors system lock/hibernate/shutdown states
- **Properties**:
  - Interval (default: 30 seconds)
  - IsRunning
- **Methods**:
  - Start()
  - Stop()
  - GetCurrentWindowTitle() (private)
- **Events**:
  - OnTitleChanged(timestamp, oldTitle, newTitle)
- **Dependencies**: Windows API

### 2. Database Manager
- **Purpose**: Handles all database operations
- **Key Functions**:
  - Manages SQLite connections
  - Performs CRUD operations for window titles, logs, and projects
  - Handles title deduplication via checksums
  - Manages and validates database schema
  - Auto-repairs invalid database structure
- **Key Features**:
  - Database structure validation
  - Automatic backup of invalid databases
  - Schema recreation if validation fails
- **Dependencies**: SQLite

### 3. Configuration Manager
- **Purpose**: Manages application settings and configuration
- **Key Functions**:
  - Reads/writes config.json
  - Provides access to settings
  - Validates configuration changes
- **Location**: `%USERPROFILE%\Documents\WindowLogger\config.json`

### 4. System Tray Interface
- **Purpose**: Provides system tray presence and basic controls
- **Key Functions**:
  - Displays system tray icon
  - Handles context menu actions
  - Launches other UI components
- **Dependencies**: Window Monitor Thread

### 5. Application
- **Purpose**: Main application class connecting all components
- **Key Functions**:
  - Initializes all components
  - Manages component lifecycle
  - Handles inter-component communication
  - Coordinates startup and shutdown
- **Dependencies**: All other core components

## UI Components

### 1. Report Window
- **Purpose**: Displays activity statistics and allows project management
- **Type**: TkInter Window
- **Subcomponents**:
  - Time Range Selector
  - Project Summary View
  - Title Summary View
  - Project Assignment Controls
  - Export Controls
- **Dependencies**: Database Manager

### 2. Settings Window
- **Purpose**: Manages application configuration
- **Type**: TkInter Window
- **Subcomponents**:
  - Database Path Configuration
  - Polling Interval Settings
  - Regex Pattern Manager
- **Dependencies**: Configuration Manager

### 3. HTML Export Generator
- **Purpose**: Creates self-contained HTML reports
- **Key Functions**:
  - GetHtmlCode() function
  - Generates SVG charts
  - Formats data tables
  - Embeds styling
- **Properties**:
  - Database Manager reference
- **Dependencies**: Database Manager

## Component Interactions

### Application Class Integration
- Application class instantiates and connects all components
- Manages component lifecycle and dependencies
- Handles startup sequence:
  1. Initialize Configuration Manager
  2. Initialize Database Manager
  3. Start Window Monitor Thread
  4. Create UI Components
  5. Show System Tray Icon
  (6. Does not start with an open window just the system tray icon)

### Data Flow
1. Window Monitor Thread → Database Manager
   - Window title changes
   - Timestamps

2. Database Manager → Report Window
   - Activity summaries
   - Project assignments
   - Title listings

3. Configuration Manager → All Components
   - Settings distribution
   - Configuration updates

4. UI Components → Database Manager
   - Project assignments
   - Data queries

### State Management
- Window Monitor Thread maintains current window state
- Database Manager handles data persistence
- Configuration Manager maintains application settings
- UI Components reflect current data state

## Error Handling
- Each component implements its own error logging
- Errors are reported to terminal using print()
- No log files are created
- Print statements are used regardless of terminal visibility
- Database errors handled with rollback mechanisms

## Performance Considerations
- Lightweight background monitoring
- Efficient database operations through indexing
- Minimal UI updates to reduce resource usage
- Configurable polling intervals for performance tuning
