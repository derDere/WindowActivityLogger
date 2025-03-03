# Window Activity Logger

A Python-based background service that monitors and logs active window titles on Windows systems to help track time spent on different applications and projects.

## Features
- Background monitoring of active window titles
- System tray interface
- Project-based time tracking
- Visual activity reports with pie charts
- Configurable title filtering using regex patterns
- HTML report export functionality

## Requirements
- Windows Operating System
- Python 3.x
- Dependencies listed in requirements.txt

## Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Configuration
- Configuration file location: `%USERPROFILE%\Documents\WindowLogger\config.json`
- Database location: `%USERPROFILE%\Documents\WindowLogger\activity.db`

## Usage
1. Start the application:
   ```
   python main.py
   ```
2. The application will run in the system tray
3. Right-click the tray icon to:
   - View activity reports
   - Access settings
   - Exit the application

## Project Structure
- `/doc` - Project documentation
- `/src` - Source code
  - Core components
  - UI components
  - Database management
  - Configuration handling

## License
[Your chosen license]
