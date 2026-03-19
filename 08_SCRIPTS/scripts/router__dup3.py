from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
import datetime
from core import db

router = APIRouter()

@router.post("/check")
async def check(venue: str = Form("Muskegon-14th-Circuit"), posture: str = Form("trial")):
    today = datetime.date.today()
    deadlines = [
        {"name":"Serve Motion","rule":"MCR 2.107","due": str(today + datetime.timedelta(days=7)), "basis":"local+MCR"},
        {"name":"File Proof of Service","rule":"MCR 2.107(D)","due": str(today + datetime.timedelta(days=8)), "basis":"dependent"},
    ]
    checklist = [
        {"step":"File Motion","rule":"MCR 2.119","status":"verify"},
        {"step":"Attach Exhibits","rule":"MRE 901-902","status":"pending"},
        {"step":"Prepare Proposed Order","rule":"MCR 2.602","status":"pending"},
    ]
    db.put_event("PROCEDURE_CHECKED", {"venue": venue, "posture": posture})
    return JSONResponse({"venue": venue, "posture": posture, "generated_at": datetime.datetime.now().isoformat(),
                         "deadlines": deadlines, "checklist": checklist})
