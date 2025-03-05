"""
Main entry point for the Window Activity Logger application.
"""
import os
import sys
import signal
import time
from pathlib import Path

# Add the parent directory to Python path so modules can be found
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))

from application import Application

def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Create and initialize application
        app = Application()
        if not app.initialize():
            print("Failed to initialize application")
            return 1

        # Set up signal handlers
        def handle_signal(signum, frame):
            print("\nReceived exit signal, shutting down...")
            app.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)

        # Start the application and keep it running
        app.start()
        while app.is_running:  # Use property instead of protected member
            # Process any pending UI events
            app.process_ui_events()
            time.sleep(0.1)  # More responsive sleep interval

        # Clean exit
        app.stop()  # Ensure everything is stopped
        return 0

    except Exception as e:
        print(f"Unhandled error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
