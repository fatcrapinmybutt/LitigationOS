
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any, List

@dataclass
class ExtractResult:
    text: str
    meta: Dict[str, Any]
    quotes: List[Dict[str, Any]]  # list of {text, locator}

class Extractor:
    def can_handle(self, path: Path) -> bool:
        raise NotImplementedError

    def extract(self, path: Path) -> ExtractResult:
        raise NotImplementedError
