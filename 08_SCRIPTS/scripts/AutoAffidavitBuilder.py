
import json
from pathlib import Path
from datetime import datetime

VIOLATION_MAP_PATH = Path("F:/OMNILITIGATION_SYSTEM/LegalViolations/violation_map.json")
AFFIDAVIT_OUTPUT_PATH = Path("F:/OMNILITIGATION_SYSTEM/AffidavitDrafts/")
AUTHOR = "Andrew J Pigors"

def generate_affidavit(file_path: str, violations: list) -> str:
    now = datetime.now().strftime("%B %d, %Y")
    body = f"""
STATE OF MICHIGAN
COUNTY OF MUSKEGON

AFFIDAVIT OF TRUTH

I, {AUTHOR}, being first duly sworn, depose and state as follows:

1. I am the affiant in this matter and make this affidavit voluntarily and based on personal knowledge.
2. I have reviewed the file located at:
   {file_path}
3. This file contains references to the following legal authorities, which I believe are relevant due to ongoing legal matters:
   - {"; ".join(violations)}

4. I affirm that the content referenced in this file is truthful, accurate, and forms part of my legal defense or claim in proceedings currently pending or anticipated.
5. I make this statement under penalty of perjury and pursuant to MCL 565.451a.

Subscribed and sworn to before me on this {now}.

___________________________________
{AUTHOR}, Affiant

"""
    return body

def main():
    print("🧾 Building affidavit drafts from violation map...")
    if not VIOLATION_MAP_PATH.exists():
        print("❌ Violation map not found.")
        return

    with open(VIOLATION_MAP_PATH, "r") as f:
        violations_data = json.load(f)

    AFFIDAVIT_OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

    for file_path, violations in violations_data.items():
        filename = Path(file_path).stem.replace(" ", "_") + "_affidavit.txt"
        affidavit_text = generate_affidavit(file_path, violations)
        output_file = AFFIDAVIT_OUTPUT_PATH / filename
        output_file.write_text(affidavit_text)

    print(f"✅ Draft affidavits saved to: {AFFIDAVIT_OUTPUT_PATH}")

if __name__ == "__main__":
    main()
