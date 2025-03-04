"""
Main entry point for the Window Activity Logger application.
"""
import sys
import signal
import time
from pathlib import Path

from .application import Application

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
            app.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)

        # Start the application and keep it running
        app.start()
        while True:
            time.sleep(1)  # Sleep to prevent high CPU usage

        return 0

    except Exception as e:
        print(f"Unhandled error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
