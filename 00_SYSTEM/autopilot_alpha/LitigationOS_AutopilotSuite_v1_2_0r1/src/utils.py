\
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_id(*parts: str) -> str:
    h = hashlib.sha1("||".join([p or "" for p in parts]).encode("utf-8")).hexdigest()
    return h[:24]


def normalize_space(s: str) -> str:
    return " ".join((s or "").strip().split())


def safe_json_loads(s: Any) -> Any:
    if s is None:
        return None
    if isinstance(s, (dict, list)):
        return s
    if not isinstance(s, str):
        return None
    t = s.strip()
    if not t:
        return None
    try:
        return json.loads(t)
    except Exception:
        return None


def parse_props_json_cell(cell: Any) -> Dict[str, Any]:
    outer = safe_json_loads(cell)
    if isinstance(outer, dict):
        if "props" in outer and isinstance(outer["props"], str):
            inner = safe_json_loads(outer["props"])
            if isinstance(inner, dict):
                out = dict(outer)
                out["props"] = inner
                return out
        return outer
    return {}


def expand_placeholders(paths: Iterable[str]) -> Tuple[str, ...]:
    out = []
    userprofile = os.environ.get("USERPROFILE", "")
    exe_dir = Path(getattr(os, "frozen", False) and os.path.dirname(os.path.abspath(os.sys.executable)) or Path(__file__).resolve().parent)
    script_dir = Path(__file__).resolve().parent
    for p in paths:
        p2 = p.replace("{USERPROFILE}", userprofile).replace("{EXE_DIR}", str(exe_dir)).replace("{SCRIPT_DIR}", str(script_dir))
        out.append(p2)
    return tuple(out)
