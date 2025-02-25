# Window Activity Logger

## Project Overview
A Python-based background service that monitors and logs active window titles on Windows systems to help track time spent on different applications and projects.

## Core Functionality
- Runs as a background process on Windows with system tray icon
- Monitors active window titles every 30 seconds (configurable)
- Records window title changes with start and end timestamps
- Stores data in SQLite database within MyDocuments
- Provides visual activity reports with pie chart and detailed tables
- Configurable title filtering using regex patterns
- Project-based time tracking

## Technical Specifications

### Database Structure (SQLite)
- Located in: `%USERPROFILE%\Documents\WindowLogger\activity.db`
- Table Structure:
  1. WindowTitles:
     - TitleID (Primary Key, checksum of title)
     - Title (Text)
     - ProjectID (Foreign Key to Projects)

  2. WindowLog:
     - ID (Primary Key)
     - TitleID (Foreign Key to WindowTitles)
     - Start Timestamp
     - End Timestamp

  3. Projects:
     - ProjectID (Primary Key)
     - ProjectName
     - Initial record: "Misc" project

### User Interface
1. System Tray Icon
   - Context Menu Options:
     - Show Report Window
     - Show Settings
     - Exit Application

2. Report Window
   - Time Range Selector (Dropdown):
     - Day
     - Week
     - Month
   - Pie Chart: Visual representation of project time distribution
   - Tables:
     - Project Summary:
       - Project Name
       - Total Time
       - Only shows projects with time > 0 in selected range
     - Title Summary:
       - Window Title
       - Total Time
       - Project (Dropdown for reassignment)
         - Includes "<New>" option to create new project
         - Opens input dialog for project name
         - Validates name (min 3 chars excluding spaces)
       - Only shows titles used in selected time range
   - Export to HTML button
   - Manual refresh button (applies project changes)

3. Settings Window
   - Database file path setting
   - Title polling interval setting (default: 30 seconds)
   - Regex Pattern Table:
     - Single column editable grid
     - Add/Remove/Edit functionality
     - Patterns for title filtering

### Configuration
- JSON file stored in `%USERPROFILE%\Documents\WindowLogger\config.json`
- Settings include:
  - Database path
  - Polling interval
  - Ignore patterns (regex list)

### HTML Export
- Single self-contained file
- No external dependencies
- Contains:
  - Inline SVG pie chart
  - Project summary table
  - Title summary table
  - Embedded CSS styling
  - No JavaScript

## Technical Requirements
- Python 3.x
- Windows Operating System
- SQLite database
- System tray functionality
- Basic error logging to terminal

## Implementation Notes
- Window title polling at configurable intervals
- New database entries created when title changes
- Previous entry updated with end timestamp
- Uninformative titles filtered via regex patterns
- No encryption needed (local storage only)
- Manual application startup (no auto-start implementation)
- Project reassignment through UI
- Checksum-based title deduplication
- Project creation via dropdown with input validation

## Success Criteria
- Successfully runs in background with minimal system impact
- Accurately captures window title changes with timestamps
- Provides clear visual reports of daily/weekly/monthly activity
- Allows effective filtering of irrelevant window titles
- Supports project-based time tracking
- Exports data in readable, self-contained HTML format
