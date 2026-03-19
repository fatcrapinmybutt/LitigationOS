from __future__ import annotations
from pathlib import Path
import json
from datetime import datetime
import zlib

ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT / "logs" / "replay_log.jsonl"

def _crc32_text(s: str) -> str:
    return format(zlib.crc32(s.encode("utf-8")) & 0xFFFFFFFF, "08X")

def append_event(event_type: str, payload: dict, *, cycle_id: str = "CYCLE-UNSET") -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().isoformat(timespec="seconds")
    seed = json.dumps({"ts": ts, "event_type": event_type, "payload": payload, "cycle_id": cycle_id}, sort_keys=True)
    row = {
        "ts": ts,
        "event_id": f"EV-{_crc32_text(seed)}",
        "cycle_id": cycle_id,
        "event_type": event_type,
        "payload": payload,
        "integrity_key": f"IK:{_crc32_text(seed)}:{len(seed)}"
    }
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")

if __name__ == "__main__":
    append_event("bootstrap_test", {"ok": True}, cycle_id="CYCLE-DEMO")
    print(f"Appended test event to {LOG_PATH}")
