"""
control_plane_api.py

FastAPI control plane skeleton for LitigationOS Event Horizon.
Provides:
- /health
- /forms (list)
- /coverage (latest coverage file)
- /cyclepack (trigger build_cyclepack)

This is a scaffolding layer; extend with auth, job queue, and full query/search.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="LitigationOS Event Horizon Control Plane", version="0.1.0")

class Settings(BaseModel):
    vault_root: str
    sqlite_db: str

SETTINGS: Optional[Settings] = None

@app.post("/configure")
def configure(settings: Settings):
    global SETTINGS
    SETTINGS = settings
    return {"ok": True, "settings": SETTINGS.model_dump()}

@app.get("/health")
def health():
    return {"ok": True, "configured": SETTINGS is not None}

@app.get("/forms")
def list_forms(limit: int = 200):
    if SETTINGS is None:
        raise HTTPException(400, "Not configured. POST /configure first.")
    import sqlite3
    con = sqlite3.connect(SETTINGS.sqlite_db)
    rows = con.execute("SELECT form_id, form_code_guess, title_guess, jurisdiction_guess, revision_guess FROM forms LIMIT ?", (limit,)).fetchall()
    con.close()
    return {"forms": [{"form_id": r[0], "code": r[1], "title": r[2], "jur": r[3], "rev": r[4]} for r in rows]}

@app.get("/coverage")
def get_coverage():
    if SETTINGS is None:
        raise HTTPException(400, "Not configured. POST /configure first.")
    vault = Path(SETTINGS.vault_root)
    report_dir = vault / "90_REPORTS"
    candidates = sorted(report_dir.glob("coverage*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise HTTPException(404, "No coverage reports found.")
    return json.loads(candidates[0].read_text(encoding="utf-8"))

@app.post("/cyclepack")
def build_cyclepack(exclude_objects: bool = True):
    if SETTINGS is None:
        raise HTTPException(400, "Not configured. POST /configure first.")
    from subprocess import run
    vault = Path(SETTINGS.vault_root)
    out = vault / "90_REPORTS" / "CyclePack_ControlPlane.zip"
    cmd = ["python", "tooling/build_cyclepack.py", "--root", str(vault), "--out", str(out)]
    if exclude_objects:
        cmd += ["--exclude", "00_OBJECTS"]
    cp = run(cmd, capture_output=True, text=True)
    if cp.returncode != 0:
        raise HTTPException(500, cp.stderr[:2000])
    return {"ok": True, "cyclepack": str(out)}


# ------------------ Job Queue endpoints ------------------

from datetime import datetime as _dt
import sqlite3 as _sqlite3
import hashlib as _hashlib

def _now():
    return _dt.now().isoformat(timespec="seconds")

def _det_id(*parts: str, n: int = 24) -> str:
    return _hashlib.sha256("|".join(parts).encode("utf-8", errors="ignore")).hexdigest()[:n]

class EnqueueJob(BaseModel):
    job_type: str
    payload: dict = {}

@app.post("/jobs/enqueue")
def enqueue_job(req: EnqueueJob):
    if SETTINGS is None:
        raise HTTPException(400, "Not configured. POST /configure first.")
    con = _sqlite3.connect(SETTINGS.sqlite_db)
    con.execute("PRAGMA journal_mode=WAL;")
    jq = Path("tooling/job_queue.sql")
    if jq.exists():
        con.executescript(jq.read_text(encoding="utf-8"))
    job_id = _det_id(req.job_type, _now(), json.dumps(req.payload, sort_keys=True), n=24)
    con.execute(
        "INSERT OR REPLACE INTO jobs(job_id, created_at, updated_at, status, job_type, payload_json) VALUES(?,?,?,?,?,?)",
        (job_id, _now(), _now(), "queued", req.job_type, json.dumps(req.payload)),
    )
    con.commit()
    con.close()
    return {"ok": True, "job_id": job_id}

@app.get("/jobs")
def list_jobs(limit: int = 100):
    if SETTINGS is None:
        raise HTTPException(400, "Not configured. POST /configure first.")
    con = _sqlite3.connect(SETTINGS.sqlite_db)
    rows = con.execute(
        "SELECT job_id, created_at, updated_at, status, job_type, payload_json, result_json, error_text "
        "FROM jobs ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    con.close()
    out = []
    for r in rows:
        out.append({
            "job_id": r[0],
            "created_at": r[1],
            "updated_at": r[2],
            "status": r[3],
            "job_type": r[4],
            "payload": json.loads(r[5]) if r[5] else {},
            "result": json.loads(r[6]) if r[6] else None,
            "error": r[7],
        })
    return {"jobs": out}
