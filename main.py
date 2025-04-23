# EyeProtector Main Application
# -*- coding: utf-8 -*-

import sys
import logging
from PySide6.QtWidgets import QApplication
from main_window import MainWindow # Import the main window class

# Configure basic logging for the main application entry point
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """Main function to start the application."""
    logging.info("EyeProtector Application Starting...")

    # Create the Qt Application instance
    app = QApplication(sys.argv)

    # Create and show the main window
    window = MainWindow()
    logging.info("MainWindow instance created.") # ADDED LOG
    logging.info("Attempting to show MainWindow...") # ADDED LOG
    window.show() # Restore the show call
    logging.info("MainWindow shown.") # ADDED LOG

    logging.info("Entering Qt event loop.")
    # Start the Qt event loop
    exit_code = app.exec() # Capture exit code
    logging.info(f"Exiting Qt event loop with code {exit_code}.") # ADDED LOG
    sys.exit(exit_code) # Exit with the code

if __name__ == "__main__":
    main()
