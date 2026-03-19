
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List
from .base import Extractor, ExtractResult

class CSVExtractor(Extractor):
    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() == ".csv"

    def extract(self, path: Path) -> ExtractResult:
        rows = []
        with path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
            reader = csv.reader(f)
            for r in reader:
                rows.append(r)
        # Flatten into a line-based representation
        text_lines = []
        for i, r in enumerate(rows[:200000]):  # safety
            text_lines.append(f"ROW {i+1}: " + " | ".join([c.strip() for c in r]))
        text = "\n".join(text_lines)
        meta = {"type": "csv", "rows": len(rows)}
        quotes: List[Dict[str, Any]] = []
        return ExtractResult(text=text, meta=meta, quotes=quotes)
