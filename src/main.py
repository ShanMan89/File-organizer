# src/main.py

import sys
import os
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QLocale, QTranslator
from app.gui.main_window import FileOrganizerGUI
from app.utils.translations import load_translations

def setup_logging():
    """Configures basic file logging for the application."""
    try:
        # Determine application root directory (assuming src/main.py structure)
        # Path(__file__) is src/main.py
        # .parent is src/
        # .parent.parent is the project root
        app_root_dir = Path(__file__).resolve().parent.parent
        
        log_dir = app_root_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / "file_organizer.log"
        
        # Get the root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO) # Set global logging level
        
        # Create file handler
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        
        # Create formatter
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
        file_handler.setFormatter(formatter)
        
        # Add handler to the root logger
        # Check if handler already exists to prevent duplication if setup_logging is called multiple times (e.g. in tests)
        if not any(isinstance(h, logging.FileHandler) and h.baseFilename == str(log_file) for h in root_logger.handlers):
            root_logger.addHandler(file_handler)
        
        logging.info("File Organizer application started. Logging configured.")
        
    except OSError as e:
        # If logging setup fails, print to console as a fallback
        print(f"Error setting up file logging: {e}", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred during logging setup: {e}", file=sys.stderr)


def main():
    # Setup logging as early as possible
    setup_logging()

    app = QApplication(sys.argv)

    # Load translations
    translator = QTranslator()
    locale = QLocale.system().name()
    
    # Attempt to load translations, log success or failure
    if load_translations(translator, locale):
        app.installTranslator(translator)
        logging.info(f"Translations for locale '{locale}' loaded and installed.")
    else:
        # This print is fine for now, but could also be a log message
        print(f"Translation for locale '{locale}' not found.")
        logging.warning(f"Translation for locale '{locale}' not found.")

    window = FileOrganizerGUI()
    window.show()
    logging.info("Main GUI window shown.")

    exit_code = app.exec()
    logging.info(f"Application exiting with code {exit_code}.")
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
