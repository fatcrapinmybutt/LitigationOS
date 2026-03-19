
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Iterable, Dict, Any, Optional

def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk_size)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

def safe_relpath(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except Exception:
        return str(path)

def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def is_probably_binary(path: Path, sniff: int = 2048) -> bool:
    try:
        with path.open("rb") as f:
            b = f.read(sniff)
        if b"\x00" in b:
            return True
    except Exception:
        return False
    return False

def file_size_mb(path: Path) -> float:
    return path.stat().st_size / (1024 * 1024)

def normalize_text(s: str) -> str:
    return " ".join((s or "").replace("\r\n", "\n").replace("\r", "\n").split())

