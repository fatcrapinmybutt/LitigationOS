from __future__ import annotations
from pathlib import Path
import json
from datetime import datetime
import zlib

ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT / "logs" / "replay_log.jsonl"

def _event_id(ts: str, event_type: str, payload: dict) -> str:
    seed = f"{ts}|{event_type}|{json.dumps(payload, sort_keys=True, default=str)}"
    return f"EVT-{zlib.crc32(seed.encode('utf-8')) & 0xFFFFFFFF:08X}"

def append_event(event_type: str, payload: dict, cycle_id: str | None = None) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().isoformat(timespec="seconds")
    row = {
        "ts": ts,
        "event_id": _event_id(ts, event_type, payload),
        "cycle_id": cycle_id,
        "event_type": event_type,
        "payload": payload
    }
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")

if __name__ == "__main__":
    append_event("bootstrap_test", {"ok": True}, cycle_id="CYCLE-TEST")
    print(f"Appended test event to {LOG_PATH}")
