
import json
from pathlib import Path
from datetime import datetime

VIOLATION_MAP_PATH = Path("F:/OMNILITIGATION_SYSTEM/LegalViolations/violation_map.json")
AFFIDAVIT_PATH = Path("F:/OMNILITIGATION_SYSTEM/AffidavitDrafts/")
COMPLAINTS_OUTPUT_PATH = Path("F:/OMNILITIGATION_SYSTEM/VerifiedComplaints/")

COUNTY = "Muskegon"
AUTHOR = "Andrew J Pigors"

def generate_complaint(file_path: str, violations: list) -> str:
    now = datetime.now().strftime("%B %d, %Y")
    facts = f"On or about the date reflected in the document located at {file_path}, the Defendant(s) engaged in conduct or omissions that appear to violate: " + "; ".join(violations)

    complaint = f"""
STATE OF MICHIGAN
IN THE CIRCUIT COURT FOR THE COUNTY OF {COUNTY}

ANDREW J PIGORS,
  Plaintiff,

v.

[DEFENDANT PLACEHOLDER],
  Defendant.
_________________________________________/

VERIFIED COMPLAINT

Plaintiff, Andrew J Pigors, states the following:

1. Plaintiff is a resident of Muskegon County, Michigan.
2. Defendant is believed to be responsible for conduct described in the attached affidavit.
3. {facts}
4. These acts and omissions form the basis of a legal cause of action under Michigan law, including the rules and statutes cited.
5. Attached is a sworn affidavit made in support of this Complaint pursuant to MCL 565.451a.

WHEREFORE, Plaintiff respectfully requests that this Honorable Court:
   A. Accept this Verified Complaint;
   B. Issue any necessary orders for relief, sanctions, or hearings;
   C. Grant any further relief deemed just and proper.

Respectfully submitted,

_________________________
Andrew J Pigors
Pro Per

Dated: {now}
"""
    return complaint

def main():
    print("📄 Generating verified complaint drafts...")
    if not VIOLATION_MAP_PATH.exists():
        print("❌ Violation map not found.")
        return

    with open(VIOLATION_MAP_PATH, "r") as f:
        violations_data = json.load(f)

    COMPLAINTS_OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

    for file_path, violations in violations_data.items():
        stem = Path(file_path).stem.replace(" ", "_")
        complaint_text = generate_complaint(file_path, violations)
        complaint_file = COMPLAINTS_OUTPUT_PATH / (stem + "_complaint.txt")
        complaint_file.write_text(complaint_text)

    print(f"✅ Verified complaint drafts saved to: {COMPLAINTS_OUTPUT_PATH}")

if __name__ == "__main__":
    main()
