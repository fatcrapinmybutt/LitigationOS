"""
FeedbackAgent: records outcome signals to drive strategy calibration.

This pack emits a simple outcome log schema. You can append:
- filing accepted/rejected
- hearing outcome
- order entered
- sanctions granted/denied

Outcome logs can later be used to recalibrate heuristics.
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional
import datetime
import uuid
import json
from pathlib import Path

def uuid_str() -> str:
    return str(uuid.uuid4())

def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat()

@dataclass(frozen=True)
class OutcomeSignal:
    outcome_id: str
    case_id: str
    meek_track: str
    observed_time: str
    outcome_type: str
    description: str
    related_artifact_id: Optional[str] = None
    related_order_pin_id: Optional[str] = None
    delta_score: Optional[float] = None  # positive is good

def append_outcome(path: Path, signal: OutcomeSignal) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(signal), ensure_ascii=False) + "\n")
