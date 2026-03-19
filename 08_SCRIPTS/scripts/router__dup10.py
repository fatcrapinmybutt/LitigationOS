from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
import os, hashlib, datetime, csv, exifread, mimetypes, json
from core import db
from core.validation import validate_payload

router = APIRouter()
CASES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../cases"))
os.makedirs(CASES_DIR, exist_ok=True)

def sha256_bytes(b:bytes)->str:
    h = hashlib.sha256(); h.update(b); return h.hexdigest()

@router.post("/audit")
async def audit(file: UploadFile = File(...), queue_deep: bool = Form(False)):
    content = await file.read()
    name = file.filename
    sha = sha256_bytes(content)
    mime = file.content_type or mimetypes.guess_type(name)[0] or "application/octet-stream"
    size = len(content)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    stored = os.path.join(CASES_DIR, f"{ts}_{name}"); open(stored,"wb").write(content)

    exif = {}
    try:
        if mime.startswith("image/"):
            tags = exifread.process_file(open(stored, "rb"), details=False)
            exif = {k:str(v) for k,v in tags.items()}
    except Exception:
        exif = {}

    ledger = os.path.join(CASES_DIR, "evidence_ledger.csv")
    exists = os.path.exists(ledger)
    with open(ledger,"a",newline="",encoding="utf-8") as f:
        w=csv.writer(f)
        if not exists: w.writerow(["timestamp","filename","sha256","mime","size"])
        w.writerow([datetime.datetime.now().isoformat(), name, sha, mime, size])

    report = {
        "exhibit_id": sha[:12],
        "relevance_401":"likely", "prejudice_403":"low",
        "hearsay_801_803":"review", "auth_901_902":"needs_foundation",
        "best_evidence_1001_1006":"ok"
    }
    validate_payload("admissibility_report.schema.json", report)
    db.put_event("EVIDENCE_INGESTED", {"sha256": sha, "path": stored})

    # Optional deep OCR job
    job_id = None
    if queue_deep:
        job_id = db.create_job("OCR_DEEP", {"path": stored, "sha256": sha, "filename": name})
    return JSONResponse({"filename": name, "sha256": sha, "mime": mime, "size": size, "exif": exif,
                         "admissibility": report, "queued_job_id": job_id})
