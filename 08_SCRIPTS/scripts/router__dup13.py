from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from core import db
from core.jobs_worker import task

router = APIRouter()

# Example task: deep OCR placeholder (hash path)
@task("OCR_DEEP")
def do_ocr(job_id, payload):
    db.log_job(job_id, "INFO", f"OCR_DEEP started on {payload.get('path')}")
    # placeholder work
    db.log_job(job_id, "INFO", "OCR completed (placeholder)")

@router.post("/jobs/submit")
async def submit_job(kind: str = Form(...), payload: str = Form("{}")):
    import json
    job_id = db.create_job(kind, json.loads(payload or "{}"))
    return {"job_id": job_id}

@router.get("/jobs/{job_id}")
def get_job(job_id: int):
    job, logs = db.get_job(job_id)
    return {"job": job, "logs": logs}

@router.get("/events/tail")
def events_tail(limit: int = 20):
    conn = db.get_conn()
    rows = conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return {"events": [dict(r) for r in rows][::-1]}
