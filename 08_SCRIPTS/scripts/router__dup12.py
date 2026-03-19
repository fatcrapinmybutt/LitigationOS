from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
import os, json, time, zipfile, datetime
from core.validation import validate_payload
from core import db

router = APIRouter()
DELIV_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../deliverables"))

@router.post("/export")
async def export(case_id: str = Form("DEMO"), tier: str = Form("Basic")):
    case_dir = os.path.join(DELIV_DIR, case_id); os.makedirs(case_dir, exist_ok=True)
    motion = os.path.join(case_dir, "motion.txt"); open(motion,"w",encoding="utf-8").write("Motion — scaffold\n")
    order = os.path.join(case_dir, "proposed_order.txt"); open(order,"w",encoding="utf-8").write("Proposed Order — scaffold\n")
    zip_path = os.path.join(case_dir, f"{case_id}_MiFILE_Pack.zip")
    with zipfile.ZipFile(zip_path,"w",zipfile.ZIP_DEFLATED) as z:
        z.write(motion, arcname="motion.txt"); z.write(order, arcname="proposed_order.txt")
    manifest = {"case_id": case_id, "tier": tier, "created_at": datetime.datetime.now().isoformat(),
                "files": ["motion.txt","proposed_order.txt"], "authorities":[]}
    validate_payload("package_manifest.schema.json", manifest)
    db.put_event("PACKAGE_BUILT", {"case_id": case_id, "zip": zip_path})
    return JSONResponse({"zip": zip_path, "manifest": manifest})
