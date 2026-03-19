
from pathlib import Path
from datetime import datetime

COMPLAINTS_PATH = Path("F:/OMNILITIGATION_SYSTEM/VerifiedComplaints/")
ORDERS_OUTPUT_PATH = Path("F:/OMNILITIGATION_SYSTEM/ProposedOrders/")

def generate_order(stem: str) -> str:
    now = datetime.now().strftime("%B %d, %Y")
    return f"""
STATE OF MICHIGAN
IN THE CIRCUIT COURT FOR THE COUNTY OF MUSKEGON

ORDER REGARDING VERIFIED COMPLAINT

At a session of said Court held on {now}, in the County of Muskegon, State of Michigan:

PRESENT: Hon. ____________________________

The Court, having reviewed the Verified Complaint and Affidavit filed by Plaintiff Andrew J Pigors regarding {stem.replace('_', ' ')}, and being otherwise fully advised in the premises:

IT IS HEREBY ORDERED that:

1. The Verified Complaint is accepted for filing.
2. A hearing shall be scheduled within the time prescribed by law.
3. The Defendant(s) shall file a written response prior to the hearing.
4. Plaintiff shall serve all filings and this Order on the Defendant(s) consistent with MCR 2.107.

IT IS SO ORDERED.

_______________________________
Circuit Court Judge

Dated: {now}
"""

def main():
    print("📜 Generating Proposed Orders...")
    ORDERS_OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

    for complaint_file in COMPLAINTS_PATH.glob("*_complaint.txt"):
        stem = complaint_file.stem.replace("_complaint", "")
        order_text = generate_order(stem)
        order_file = ORDERS_OUTPUT_PATH / (stem + "_proposed_order.txt")
        order_file.write_text(order_text)

    print(f"✅ Proposed Orders saved to: {ORDERS_OUTPUT_PATH}")

if __name__ == "__main__":
    main()
