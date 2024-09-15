# src/app/utils/translations.py

from PyQt6.QtCore import QTranslator
import os

def load_translations(translator: QTranslator, locale: str) -> bool:
    translation_file = os.path.join(os.path.dirname(__file__), '../../translations', f'translations_{locale}.qm')
    if translator.load(translation_file):
        return True
    return False
