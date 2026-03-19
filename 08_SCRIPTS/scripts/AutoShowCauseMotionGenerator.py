
import json
from pathlib import Path
from datetime import datetime

VIOLATION_MAP_PATH = Path("F:/OMNILITIGATION_SYSTEM/LegalViolations/violation_map.json")
MOTIONS_OUTPUT_PATH = Path("F:/OMNILITIGATION_SYSTEM/MotionsToShowCause/")
AUTHOR = "Andrew J Pigors"

def generate_motion(file_path: str, violations: list) -> str:
    now = datetime.now().strftime("%B %d, %Y")
    facts = f"The following legal provisions appear to have been violated: " + ", ".join(violations)
    stem = Path(file_path).stem.replace("_", " ")

    return f"""
STATE OF MICHIGAN
IN THE CIRCUIT COURT FOR THE COUNTY OF MUSKEGON

ANDREW J PIGORS,
  Plaintiff,

v.

[DEFENDANT PLACEHOLDER],
  Defendant.
_________________________________________/

MOTION FOR ORDER TO SHOW CAUSE

NOW COMES Plaintiff, Andrew J Pigors, in propria persona, and respectfully moves this Honorable Court to issue an Order to Show Cause based on the following:

1. That on or about the date(s) associated with the document entitled "{stem}", the Defendant(s) engaged in conduct that constitutes a violation of court rules and/or Michigan statutes.
2. {facts}
3. Said conduct constitutes a willful violation of duties established by law or prior court orders.

WHEREFORE, Plaintiff respectfully requests that this Court:

   A. Issue an Order requiring the Defendant(s) to appear and show cause why they should not be held in contempt or otherwise sanctioned;
   B. Schedule a hearing within 14 days pursuant to applicable procedural rules;
   C. Grant any other relief this Court deems just and proper.

Respectfully submitted,

_________________________
Andrew J Pigors
Pro Per

Dated: {now}
"""

def main():
    print("⚖️ Generating Motions to Show Cause...")
    if not VIOLATION_MAP_PATH.exists():
        print("❌ Violation map not found.")
        return

    with open(VIOLATION_MAP_PATH, "r") as f:
        violations_data = json.load(f)

    MOTIONS_OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

    for file_path, violations in violations_data.items():
        if not violations:
            continue
        stem = Path(file_path).stem.replace(" ", "_")
        motion_text = generate_motion(file_path, violations)
        motion_file = MOTIONS_OUTPUT_PATH / (stem + "_motion_show_cause.txt")
        motion_file.write_text(motion_text)

    print(f"✅ Show Cause Motions saved to: {MOTIONS_OUTPUT_PATH}")

if __name__ == "__main__":
    main()
