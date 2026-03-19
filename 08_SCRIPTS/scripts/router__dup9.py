from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse, PlainTextResponse
import datetime, os
from core import db
from core.validation import validate_payload

router = APIRouter()
DELIV_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../deliverables"))

def make_ics(deadlines):
    lines = ["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//LitigationOS//EN"]
    for d in deadlines:
        uid = f"{d['name'].replace(' ','_')}-{d['due']}@litigationos"
        lines += ["BEGIN:VEVENT", f"UID:{uid}", f"DTSTAMP:{datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}",
                  f"SUMMARY:{d['name']} ({d['rule']})", f"DTSTART;VALUE=DATE:{d['due'].replace('-','')}",
                  f"DESCRIPTION:Basis={d['basis']}", "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)

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
    payload = {"venue": venue, "posture": posture, "generated_at": datetime.datetime.now().isoformat(),
               "deadlines": deadlines, "checklist": checklist}
    validate_payload("procedure_checklist.schema.json", payload)
    ics = make_ics(deadlines)
    os.makedirs(DELIV_DIR, exist_ok=True)
    ics_path = os.path.join(DELIV_DIR, "deadlines.ics"); open(ics_path,"w",encoding="utf-8").write(ics)
    db.put_event("PROCEDURE_CHECKED", {"venue": venue, "posture": posture, "ics": ics_path})
    return JSONResponse({**payload, "ics": ics_path})
