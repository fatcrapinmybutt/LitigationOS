#!/usr/bin/env python3
"""
litigationos_mcp_server.py

A local MCP server for LitigationOS Event Horizon Δ∞. Exposes tools/resources for Copilot Agent mode.

Dependencies:
  pip install "mcp[cli]"  (or uv add "mcp[cli]")

Run (stdio transport in VS Code via mcp.json):
  python mcp_servers/litigationos_mcp_server.py

This server is local-only. It never returns verbatim court-form instruction text; it returns pointers/hashes.
"""

from __future__ import annotations

import json
import os
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("LitigationOS Event Horizon", json_response=True)

def now() -> str:
    return datetime.now().isoformat(timespec="seconds")

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def env_path(key: str, default: str) -> Path:
    return Path(os.environ.get(key, default)).expanduser().resolve()

VAULT = env_path("LITOS_VAULT", "Vault")
DB    = env_path("LITOS_DB", str(VAULT / "formos_v2.db"))
CONFIG= env_path("LITOS_CONFIG", "config/formos_config.json")

def connect() -> sqlite3.Connection:
    con = sqlite3.connect(str(DB))
    con.execute("PRAGMA journal_mode=WAL;")
    return con

@mcp.tool()
def vault_status() -> dict:
    """Return Vault and DB status (paths + existence)."""
    return {
        "vault": str(VAULT),
        "vault_exists": VAULT.exists(),
        "db": str(DB),
        "db_exists": DB.exists(),
        "config": str(CONFIG),
        "config_exists": CONFIG.exists(),
        "time": now(),
    }

@mcp.tool()
def list_reports(limit: int = 200) -> dict:
    """List recent files under Vault/90_REPORTS (paths + bytes)."""
    root = VAULT / "90_REPORTS"
    items = []
    if root.exists():
        for p in sorted(root.rglob("*"), key=lambda x: x.stat().st_mtime, reverse=True):
            if p.is_file():
                items.append({"path": str(p.relative_to(VAULT)).replace("\\", "/"), "bytes": p.stat().st_size})
                if len(items) >= limit:
                    break
    return {"ok": True, "count": len(items), "items": items}

@mcp.tool()
def read_pass_status() -> dict:
    """Read PASS_STATUS.json if present."""
    p = VAULT / "90_REPORTS" / "PASS_STATUS.json"
    if not p.exists():
        return {"ok": False, "error": "PASS_STATUS.json not found", "path": str(p)}
    return json.loads(p.read_text(encoding="utf-8", errors="ignore"))

@mcp.tool()
def db_counts() -> dict:
    """Basic row counts for core tables (forms/documents/instructions/requirements/stacks/evidence)."""
    if not DB.exists():
        return {"ok": False, "error": "DB missing", "db": str(DB)}
    con = connect()
    tables = ["forms", "documents", "form_instructions", "requirements", "evidence_atoms", "stack_manifests", "requirement_satisfaction", "jobs"]
    out = {}
    for t in tables:
        try:
            row = con.execute(f"SELECT COUNT(1) FROM {t}").fetchone()
            out[t] = int(row[0]) if row else 0
        except Exception:
            out[t] = None
    con.close()
    return {"ok": True, "counts": out}

@mcp.tool()
def enqueue_job(job_type: str, payload_json: str = "{}") -> dict:
    """Enqueue a job into the local SQLite jobs table (compatible with tooling/job_worker.py)."""
    payload = json.loads(payload_json or "{}")
    con = connect()
    con.executescript((Path("tooling") / "job_queue.sql").read_text(encoding="utf-8"))
    job_id = hashlib.sha256((job_type + "|" + now() + "|" + json.dumps(payload, sort_keys=True)).encode("utf-8")).hexdigest()[:24]
    con.execute(
        "INSERT OR REPLACE INTO jobs(job_id, created_at, updated_at, status, job_type, payload_json) VALUES(?,?,?,?,?,?)",
        (job_id, now(), now(), "queued", job_type, json.dumps(payload)),
    )
    con.commit()
    con.close()
    return {"ok": True, "job_id": job_id, "job_type": job_type, "payload": payload}

@mcp.resource("litigationos://report/{relpath}")
def get_report(relpath: str) -> str:
    """Return report content for small JSON/text files under Vault/90_REPORTS (safe subtree)."""
    rel = Path(relpath).as_posix().lstrip("/")
    p = (VAULT / rel).resolve()
    if not str(p).startswith(str(VAULT.resolve())):
        return "ERROR: unsafe path"
    if "90_REPORTS" not in p.parts:
        return "ERROR: only 90_REPORTS allowed"
    if not p.exists() or not p.is_file():
        return "ERROR: not found"
    if p.stat().st_size > 512_000:
        return "ERROR: file too large"
    return p.read_text(encoding="utf-8", errors="ignore")

if __name__ == "__main__":
    # stdio is fine for VS Code mcp.json "command":"python"
    mcp.run()
