from __future__ import annotations
import base64
import hashlib
from datetime import datetime
from typing import Any, Mapping

def _norm_value(v: Any) -> str:
    if v is None:
        return "~"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v).strip().lower()
    s = " ".join(s.split())
    # simple date normalization pass for YYYY-M-D patterns
    try:
        if len(s) >= 8 and s[4] == "-" and "-" in s:
            parts = s.split("-")
            if len(parts) == 3 and all(parts):
                y = int(parts[0]); m = int(parts[1]); d = int(parts[2])
                s = f"{y:04d}-{m:02d}-{d:02d}"
    except Exception:
        pass
    return s

def stable_kv_string(payload: Mapping[str, Any]) -> str:
    parts = []
    for k in sorted(payload.keys()):
        parts.append(f"{_norm_value(k)}={_norm_value(payload[k])}")
    return "|".join(parts)

def deterministic_id(prefix: str, payload: Mapping[str, Any], length: int = 20) -> str:
    raw = stable_kv_string(payload).encode("utf-8")
    digest = hashlib.sha256(raw).digest()
    b32 = base64.b32encode(digest).decode("ascii").rstrip("=")
    return f"{prefix}_{b32[:length]}"

if __name__ == "__main__":
    sample = {"case_id": "24-01507-DC", "date": "2026-2-7", "judge": "Jenny L. McNeill"}
    print(stable_kv_string(sample))
    print(deterministic_id("ORD", sample))
