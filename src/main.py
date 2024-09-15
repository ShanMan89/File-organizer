# src/main.py

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QLocale, QTranslator
from app.gui.main_window import FileOrganizerGUI
from app.utils.translations import load_translations

def main():
    app = QApplication(sys.argv)

    # Load translations
    translator = QTranslator()
    locale = QLocale.system().name()
    if load_translations(translator, locale):
        app.installTranslator(translator)
    else:
        print(f"Translation for locale '{locale}' not found.")

    window = FileOrganizerGUI()
    window.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    main()
