from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
import os, json, time
from core.template_compiler import render_docx_from_text
from core import db

router = APIRouter()
DELIV_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../deliverables"))
TEMPLATE = """IN THE CIRCUIT COURT FOR {{ venue }}
CAPTION: {{ caption }}

MOTION TITLE: {{ motion_title }}

FACTS:
{{ facts }}

RELIEF REQUESTED:
{{ relief }}
"""

@router.post("/autofill")
async def autofill(form_id: str = Form(...), payload: str = Form("{}")):
    data = json.loads(payload or "{}")
    out_dir = os.path.join(DELIV_DIR, "forms"); os.makedirs(out_dir, exist_ok=True)
    out_docx = os.path.join(out_dir, f"{form_id}_{int(time.time())}.docx")
    render_docx_from_text(TEMPLATE, data, out_docx)
    db.put_event("FORM_GENERATED", {"form_id": form_id, "output": out_docx})
    return JSONResponse({"status":"ok","output": out_docx, "validity":{"form_version":"scaffold"}})
