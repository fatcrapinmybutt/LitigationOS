
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

@dataclass
class LedgerEvent:
    ts: str
    level: str
    event: str
    detail: Dict[str, Any]

class RunLedger:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, level: str, event: str, **detail: Any) -> None:
        ev = LedgerEvent(ts=datetime.utcnow().isoformat() + "Z", level=level, event=event, detail=detail)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(ev), ensure_ascii=False) + "\n")

    def info(self, event: str, **detail: Any) -> None:
        self.log("INFO", event, **detail)

    def warn(self, event: str, **detail: Any) -> None:
        self.log("WARN", event, **detail)

    def error(self, event: str, **detail: Any) -> None:
        self.log("ERROR", event, **detail)

