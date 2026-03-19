#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
litigationos_common.py — shared utilities for LitigationOS scripts (Windows-first, portable).

Design goals:
- Deterministic, local-first paths; consistent location discovery via LITIGATIONOS_HOME or config file.
- Robust logging; safe writes; minimal dependencies.
- No network calls. All I/O is local filesystem.

Config discovery order:
1) Env var LITIGATIONOS_HOME -> root
2) Env var LITIGATIONOS_CONFIG -> JSON config path
3) %APPDATA%\\LitigationOS\\litigationos_paths.json (Windows) or ~/.litigationos/litigationos_paths.json
4) Search upward from the running script for: lit_paths.json OR litigationos_paths.json OR .litigationos_root marker

The config file schema (JSON):
{
  "litigationos_home": "D:/LitigationOS",
  "default_out_root": "F:/LitigationOS/HarvestOut",
  "scan_roots": ["F:/", "D:/", "E:/", "Q:/", "Z:/", "X:/"],
  "rclone_roots": ["gdrive:/EDS-USB", "gdrive:/Litigation_OS$", "gdrive:/LITIGATION_INTAKE"],
  "paths_file": "D:/LitigationOS/drivesANDpaths.txt"
}
"""
from __future__ import annotations

import os
import json
import csv
import re
import sys
import time
import shutil
import hashlib
import logging
import datetime as _dt
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Any, Dict, List, Tuple

ASCII_SAFE_RE = re.compile(r"[^A-Za-z0-9._\-]+")

def now_utc_iso() -> str:
    return _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def safe_ascii_filename(name: str, max_len: int = 180) -> str:
    name = name.strip().replace(" ", "_")
    name = ASCII_SAFE_RE.sub("_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    if not name:
        name = "artifact"
    if len(name) > max_len:
        base, dot, ext = name.rpartition(".")
        if dot:
            base = base[: max_len - (len(ext) + 1)]
            name = f"{base}.{ext}"
        else:
            name = name[:max_len]
    return name

def sha256_file(path: Path, max_bytes: Optional[int] = None) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        total = 0
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
            total += len(chunk)
            if max_bytes is not None and total >= max_bytes:
                break
    return h.hexdigest()

def ensure_dir(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p

def atomic_write_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    ensure_dir(path.parent)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding=encoding)
    tmp.replace(path)

def atomic_write_bytes(path: Path, data: bytes) -> None:
    ensure_dir(path.parent)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)

def default_config_path() -> Path:
    if os.name == "nt":
        appdata = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(appdata) / "LitigationOS" / "litigationos_paths.json"
    return Path.home() / ".litigationos" / "litigationos_paths.json"

def _search_upward_for_markers(start: Path) -> Optional[Path]:
    markers = ["litigationos_paths.json", "lit_paths.json", ".litigationos_root"]
    cur = start.resolve()
    for _ in range(0, 10):
        for m in markers:
            cand = cur / m
            if cand.exists():
                return cand
        if cur.parent == cur:
            break
        cur = cur.parent
    return None

def load_paths_config(script_path: Optional[Path] = None) -> Dict[str, Any]:
    # 1) LITIGATIONOS_HOME
    home = os.environ.get("LITIGATIONOS_HOME")
    if home:
        return {"litigationos_home": home}

    # 2) LITIGATIONOS_CONFIG
    cfg_env = os.environ.get("LITIGATIONOS_CONFIG")
    if cfg_env and Path(cfg_env).exists():
        try:
            return json.loads(Path(cfg_env).read_text(encoding="utf-8"))
        except Exception:
            return {"_config_error": f"Failed to parse {cfg_env}"}

    # 3) default config path
    cfg = default_config_path()
    if cfg.exists():
        try:
            return json.loads(cfg.read_text(encoding="utf-8"))
        except Exception:
            return {"_config_error": f"Failed to parse {str(cfg)}"}

    # 4) upward search near script
    if script_path:
        marker = _search_upward_for_markers(script_path.parent)
        if marker:
            if marker.name == ".litigationos_root":
                # marker file means "this directory is the home"
                return {"litigationos_home": str(marker.parent)}
            if marker.suffix.lower() == ".json":
                try:
                    return json.loads(marker.read_text(encoding="utf-8"))
                except Exception:
                    return {"_config_error": f"Failed to parse {str(marker)}"}

    return {}

def write_paths_config(cfg: Dict[str, Any], out_path: Optional[Path] = None) -> Path:
    out_path = out_path or default_config_path()
    ensure_dir(out_path.parent)
    atomic_write_text(out_path, json.dumps(cfg, ensure_ascii=False, indent=2))
    return out_path

def resolve_litigationos_home(script_path: Optional[Path] = None) -> Optional[Path]:
    cfg = load_paths_config(script_path)
    home = cfg.get("litigationos_home")
    if home:
        return Path(home)
    return None

def load_paths_file(paths_file: Path) -> List[str]:
    """Read a drives/paths file with one path per line. Supports quotes and comments (# or //)."""
    out: List[str] = []
    if not paths_file.exists():
        return out
    for raw in paths_file.read_text(encoding="utf-8", errors="replace").splitlines():
        s = raw.strip()
        if not s:
            continue
        if s.startswith("#") or s.startswith("//"):
            continue
        # remove surrounding quotes
        if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
            s = s[1:-1].strip()
        out.append(s)
    return out

def configure_logging(log_path: Path, verbose: bool = False, quiet: bool = False) -> logging.Logger:
    ensure_dir(log_path.parent)
    logger = logging.getLogger("LitigationOS")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    file_handler = logging.FileHandler(str(log_path), encoding="utf-8")
    file_handler.setFormatter(fmt)
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    if not quiet:
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(fmt)
        ch.setLevel(logging.DEBUG if verbose else logging.INFO)
        logger.addHandler(ch)

    logger.debug("Logger initialized")
    return logger

def iter_files(roots: Iterable[Path], include_ext: Optional[set[str]] = None, exclude_dirs: Optional[List[str]] = None) -> Iterable[Path]:
    exclude_dirs = exclude_dirs or []
    exclude_dirs_lower = {d.lower() for d in exclude_dirs}
    for root in roots:
        if not root.exists():
            continue
        if root.is_file():
            if include_ext is None or root.suffix.lower() in include_ext:
                yield root
            continue
        for p in root.rglob("*"):
            try:
                if p.is_dir():
                    if p.name.lower() in exclude_dirs_lower:
                        # skip subtree by not descending: rglob doesn't allow prune; filter file yields only
                        continue
                if p.is_file():
                    if include_ext is None or p.suffix.lower() in include_ext:
                        yield p
            except Exception:
                continue

def write_manifest(manifest_json: Path, files: List[Path], base_dir: Optional[Path] = None, hash_max_bytes: Optional[int] = None) -> Tuple[Path, Path]:
    base_dir = base_dir or manifest_json.parent
    rows = []
    for f in files:
        try:
            rel = str(f.relative_to(base_dir))
        except Exception:
            rel = str(f)
        st = f.stat()
        rows.append({
            "path": rel,
            "bytes": st.st_size,
            "mtime_iso": _dt.datetime.utcfromtimestamp(st.st_mtime).replace(microsecond=0).isoformat() + "Z",
            "sha256": sha256_file(f, max_bytes=hash_max_bytes),
        })
    atomic_write_text(manifest_json, json.dumps({
        "generated_at_utc": now_utc_iso(),
        "hash_max_bytes": hash_max_bytes,
        "entries": rows
    }, ensure_ascii=False, indent=2))
    manifest_csv = manifest_json.with_suffix(".csv")
    ensure_dir(manifest_csv.parent)
    with manifest_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["path","bytes","mtime_iso","sha256"])
        w.writeheader()
        w.writerows(rows)
    return manifest_json, manifest_csv

def platform_hint() -> str:
    return f"platform={sys.platform} python={sys.version.split()[0]} os_name={os.name}"
