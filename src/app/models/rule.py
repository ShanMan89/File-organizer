# src/app/models/rule.py

from dataclasses import dataclass
from typing import List

@dataclass
class Rule:
    name: str
    extensions: List[str]
