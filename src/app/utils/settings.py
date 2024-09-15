# src/app/utils/settings.py

import json
import os
from typing import Any, Dict

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), '../../../settings.json')

def load_settings() -> Dict[str, Any]:
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_settings(settings: Dict[str, Any]) -> None:
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)
