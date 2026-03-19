#!/usr/bin/env python3
"""
MBP LitigationOS — SCAO Form Filler Skill (a27 + m45)
=======================================================
Generate filled SCAO form content from case data for Michigan courts.

Supported forms:
    FOC 66  — Uniform Order Regarding Parenting Time
    MC 97   — Fee Waiver Request
    MC 280  — Proof of Service
    CC 381  — Verified Statement (custody change)
    FOC 87  — Objection to FOC Recommendation

Plaintiff: Andrew M. Pigors, pro se, Muskegon County
Case: 2024-001507-DC, 14th Circuit Court

Usage:
    from skills.scao_form_filler import SCAOFormFiller
    filler = SCAOFormFiller()
    foc66 = filler.fill_foc66()
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent
    if "skills" in str(Path(__file__)) else Path(__file__).resolve().parent))
try:
    from cycle_method import cycle_json, cycle_print
except ImportError:
    cycle_json = lambda obj, **kw: print(json.dumps(obj, default=str))
    cycle_print = print

DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\LitigationOS\litigation_context.db",
)

# ── Case constants ────────────────────────────────────────────────────

CASE_INFO = {
    "case_number": "2024-001507-DC",
    "court": "14th Circuit Court",
    "county": "Muskegon",
    "judge": "Hon. Jenny L. McNeill",
    "court_address": "990 Terrace Street, Muskegon, MI 49442",
    "court_phone": "(231) 724-6241",
}

PLAINTIFF = {
    "name": "Andrew M. Pigors",
    "role": "Plaintiff",
    "pro_se": True,
    "address_line1": "[Address Line 1]",
    "city": "Muskegon",
    "state": "MI",
    "zip": "49XXX",
    "phone": "[Phone]",
    "email": "[Email]",
    "dob": "[DOB]",
}

DEFENDANT = {
    "name": "Tiffany Watson (fka Pigors)",
    "role": "Defendant",
    "attorney": "Ronald E. Berry (P27889)",
    "attorney_address": "[Berry Address]",
    "city": "[City]",
    "state": "MI",
    "zip": "[Zip]",
}

CHILDREN = [
    {"name": "[Child Name]", "dob": "[Child DOB]", "age": "[Age]"},
]


def _get_db() -> Optional[sqlite3.Connection]:
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA query_only=ON")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception:
        return None


def _today() -> str:
    return datetime.now().strftime("%m/%d/%Y")


def _today_long() -> str:
    return datetime.now().strftime("%B %d, %Y")


def _get_court_addresses() -> Dict[str, Dict]:
    """Fetch court addresses from court_address_book."""
    conn = _get_db()
    if not conn:
        return {}
    try:
        rows = conn.execute(
            "SELECT entity_id, name, address_line1, address_line2, city, state, zip "
            "FROM court_address_book"
        ).fetchall()
        return {r["entity_id"]: dict(r) for r in rows}
    except Exception:
        return {}
    finally:
        conn.close()


class SCAOFormFiller:
    """Generate filled SCAO form content from case data."""

    def __init__(self):
        self.addresses = _get_court_addresses()

    def fill_foc66(self, parenting_schedule: Optional[Dict] = None) -> str:
        """
        FOC 66 — Uniform Order Regarding Parenting Time.

        Generates the text content for a parenting time order requesting
        restoration of regular parenting time per MCL 722.27a.

        Args:
            parenting_schedule: Optional dict with schedule details

        Returns:
            Filled form content as text
        """
        schedule = parenting_schedule or {
            "regular_weekday": "Every Wednesday, 3:00 PM to 8:00 PM",
            "regular_weekend": "Every other weekend, Friday 6:00 PM to Sunday 6:00 PM",
            "holidays_even": "Thanksgiving, Christmas Day, Father's Day",
            "holidays_odd": "Christmas Eve, New Year's Day, Memorial Day",
            "summer": "Four (4) consecutive weeks, with 30 days notice",
            "spring_break": "Alternating years, beginning even years with Father",
            "birthday": "Child's birthday: alternating years; Father's birthday: always",
        }

        lines = [
            "=" * 72,
            "SCAO FORM FOC 66 — UNIFORM ORDER REGARDING PARENTING TIME",
            "=" * 72,
            "",
            f"Court: {CASE_INFO['court']}, {CASE_INFO['county']} County",
            f"Case No.: {CASE_INFO['case_number']}",
            f"Judge: {CASE_INFO['judge']}",
            f"Date: {_today()}",
            "",
            "PARTIES:",
            f"  Plaintiff: {PLAINTIFF['name']}",
            f"  Defendant: {DEFENDANT['name']}",
            "",
            "CHILDREN:",
        ]
        for child in CHILDREN:
            lines.append(f"  Name: {child['name']}  DOB: {child['dob']}")

        lines.extend([
            "",
            "IT IS ORDERED:",
            "",
            "1. GENERAL PARENTING TIME",
            f"   The Plaintiff/Father shall have parenting time as follows:",
            "",
            f"   a. Weekday: {schedule['regular_weekday']}",
            f"   b. Weekend: {schedule['regular_weekend']}",
            "",
            "2. HOLIDAY PARENTING TIME",
            f"   a. Even years: {schedule['holidays_even']}",
            f"   b. Odd years: {schedule['holidays_odd']}",
            "",
            "3. SUMMER PARENTING TIME",
            f"   {schedule['summer']}",
            "",
            "4. SPRING BREAK",
            f"   {schedule['spring_break']}",
            "",
            "5. BIRTHDAY",
            f"   {schedule['birthday']}",
            "",
            "6. ADDITIONAL PROVISIONS",
            "   a. Neither party shall make disparaging remarks about the other",
            "      in the presence of the child(ren). MCL 722.23(j).",
            "   b. Both parties shall encourage the child(ren)'s relationship",
            "      with the other parent. MCL 722.23(j).",
            "   c. Transportation: Shared equally or as agreed.",
            "   d. Right of first refusal for childcare exceeding 4 hours.",
            "",
            "AUTHORITY: MCL 722.27a; MCR 3.207; FOC 66 (6/19)",
            "",
            f"Date: {'_' * 30}",
            f"Judge: {'_' * 30}",
            f"       {CASE_INFO['judge']}",
        ])
        return "\n".join(lines)

    def fill_mc97(
        self,
        monthly_income: float = 0.0,
        monthly_expenses: float = 0.0,
        reasons: Optional[List[str]] = None,
    ) -> str:
        """
        MC 97 — Fee Waiver Request.

        Args:
            monthly_income: Gross monthly income
            monthly_expenses: Total monthly expenses
            reasons: List of reasons for fee waiver

        Returns:
            Filled form content
        """
        reasons = reasons or [
            "Plaintiff is currently unemployed/underemployed due to ongoing litigation demands",
            "Custody litigation has consumed substantial financial resources",
            "Filing bond of $250 imposed by court creates unconstitutional barrier to access",
            "Boddie v Connecticut, 401 US 371 (1971) prohibits fee barriers in family law",
        ]

        lines = [
            "=" * 72,
            "SCAO FORM MC 97 — FEE WAIVER REQUEST",
            "=" * 72,
            "",
            f"Court: {CASE_INFO['court']}, {CASE_INFO['county']} County",
            f"Case No.: {CASE_INFO['case_number']}",
            f"Date: {_today()}",
            "",
            "APPLICANT INFORMATION:",
            f"  Name: {PLAINTIFF['name']}",
            f"  Address: {PLAINTIFF['address_line1']}",
            f"  City/State/Zip: {PLAINTIFF['city']}, {PLAINTIFF['state']} {PLAINTIFF['zip']}",
            f"  Phone: {PLAINTIFF['phone']}",
            "",
            "FINANCIAL INFORMATION:",
            f"  Monthly Income (gross): ${monthly_income:,.2f}",
            f"  Monthly Expenses: ${monthly_expenses:,.2f}",
            f"  Net Monthly: ${monthly_income - monthly_expenses:,.2f}",
            "",
            "  Sources of Income:",
            "    [ ] Employment   [ ] Unemployment   [ ] Social Security",
            "    [ ] SSI/SSD      [ ] Other: _______________________________",
            "",
            "  Public Assistance:",
            "    [ ] Food Assistance   [ ] Medicaid   [ ] FIP/TANF",
            "    [ ] SSI               [ ] Other: _______________",
            "",
            "REASONS FOR REQUEST:",
        ]
        for i, reason in enumerate(reasons, 1):
            lines.append(f"  {i}. {reason}")

        lines.extend([
            "",
            "I declare under penalty of perjury that the information above is true.",
            "",
            f"Date: {_today()}",
            "",
            "_______________________________",
            f"{PLAINTIFF['name']}, Pro Se",
            "",
            "AUTHORITY: MCR 2.002; Boddie v Connecticut, 401 US 371 (1971)",
            "NOTE: The $250 filing bond imposed in this case should be vacated",
            "as an unconstitutional barrier to court access.",
        ])
        return "\n".join(lines)

    def fill_mc280(
        self,
        document_served: str = "",
        service_date: str = "",
        service_method: str = "First-Class Mail",
        persons_served: Optional[List[Dict]] = None,
    ) -> str:
        """
        MC 280 — Proof of Service.

        Args:
            document_served: Title of document served
            service_date: Date of service
            service_method: Method (First-Class Mail, Email, Personal, MiFile)
            persons_served: List of dicts with name, address

        Returns:
            Filled form content
        """
        service_date = service_date or _today()
        persons_served = persons_served or [
            {"name": DEFENDANT['attorney'], "address": DEFENDANT.get('attorney_address', '[Address]')},
        ]

        lines = [
            "=" * 72,
            "SCAO FORM MC 280 — PROOF OF SERVICE",
            "=" * 72,
            "",
            f"Court: {CASE_INFO['court']}, {CASE_INFO['county']} County",
            f"Case No.: {CASE_INFO['case_number']}",
            f"Judge: {CASE_INFO['judge']}",
            "",
            f"Document Served: {document_served or '[Document Title]'}",
            f"Date of Service: {service_date}",
            f"Method of Service: {service_method}",
            "",
            "PERSONS SERVED:",
        ]
        for i, person in enumerate(persons_served, 1):
            lines.append(f"  {i}. {person['name']}")
            lines.append(f"     Address: {person['address']}")
            lines.append(f"     Method: {service_method}")
            lines.append("")

        lines.extend([
            "I declare that I served the above document(s) as stated above.",
            "",
            f"Date: {service_date}",
            "",
            "_______________________________",
            f"{PLAINTIFF['name']}, Pro Se",
            f"{PLAINTIFF['address_line1']}",
            f"{PLAINTIFF['city']}, {PLAINTIFF['state']} {PLAINTIFF['zip']}",
            "",
            "AUTHORITY: MCR 2.107; MCR 2.105",
        ])
        return "\n".join(lines)

    def fill_cc381(
        self,
        change_reasons: Optional[List[str]] = None,
        current_arrangement: str = "",
        requested_arrangement: str = "",
    ) -> str:
        """
        CC 381 — Verified Statement for custody/parenting time change.

        Args:
            change_reasons: List of reasons supporting change
            current_arrangement: Current custody arrangement description
            requested_arrangement: Requested arrangement

        Returns:
            Filled form content
        """
        change_reasons = change_reasons or [
            "All parenting time suspended via ex parte orders on Aug 8, 2025 without hearing",
            "567+ days of parent-child separation — severe harm to child's wellbeing",
            "No best-interest hearing conducted per MCL 722.23(a)-(l)",
            "Father has stable home, employment, and strong prior parenting relationship",
            "Mother's false allegations not supported by evidence (MRE 602, 801)",
        ]
        current_arrangement = current_arrangement or (
            "ALL parenting time suspended since August 8, 2025 per ex parte orders. "
            "No contact between Father and child(ren) for 567+ days."
        )
        requested_arrangement = requested_arrangement or (
            "Immediate restoration of regular parenting time per MCL 722.27a. "
            "Equal parenting time schedule (50/50) with gradual reintroduction if needed."
        )

        lines = [
            "=" * 72,
            "SCAO FORM CC 381 — VERIFIED STATEMENT",
            "(Motion Regarding Custody / Parenting Time)",
            "=" * 72,
            "",
            f"Court: {CASE_INFO['court']}, {CASE_INFO['county']} County",
            f"Case No.: {CASE_INFO['case_number']}",
            f"Judge: {CASE_INFO['judge']}",
            f"Date: {_today()}",
            "",
            "PLAINTIFF INFORMATION:",
            f"  Name: {PLAINTIFF['name']}",
            f"  Address: {PLAINTIFF['address_line1']}",
            f"  City/State/Zip: {PLAINTIFF['city']}, {PLAINTIFF['state']} {PLAINTIFF['zip']}",
            "",
            "DEFENDANT INFORMATION:",
            f"  Name: {DEFENDANT['name']}",
            f"  Attorney: {DEFENDANT['attorney']}",
            "",
            "CHILDREN:",
        ]
        for child in CHILDREN:
            lines.append(f"  Name: {child['name']}  DOB: {child['dob']}")

        lines.extend([
            "",
            "CURRENT ARRANGEMENT:",
            f"  {current_arrangement}",
            "",
            "REQUESTED ARRANGEMENT:",
            f"  {requested_arrangement}",
            "",
            "REASONS FOR CHANGE (verified under oath):",
        ])
        for i, reason in enumerate(change_reasons, 1):
            lines.append(f"  {i}. {reason}")

        lines.extend([
            "",
            "BEST INTEREST FACTORS (MCL 722.23):",
            "  (a) Love/affection: Father has strong bond; 567+ day separation is harmful",
            "  (b) Capacity: Father has stable home and employment",
            "  (c) Moral fitness: No substantiated allegations against Father",
            "  (d) Mental/physical health: Father is healthy and capable",
            "  (j) Willingness to facilitate: Father has always encouraged relationship",
            "       with Mother; Mother has blocked all contact for 567+ days",
            "",
            "VERIFICATION:",
            "I declare under the penalties of perjury that the statements above",
            "are true to the best of my information, knowledge, and belief.",
            "",
            f"Date: {_today()}",
            "",
            "_______________________________",
            f"{PLAINTIFF['name']}, Pro Se",
            "",
            "AUTHORITY: MCR 3.206(B); MCL 722.23; MCL 722.27; Vodvarka v Grasmeyer",
        ])
        return "\n".join(lines)

    def fill_foc87(
        self,
        recommendation_date: str = "",
        objection_reasons: Optional[List[str]] = None,
    ) -> str:
        """
        FOC 87 — Objection to FOC Recommendation.

        21-day deadline per MCL 552.507(5); MCR 3.208.

        Args:
            recommendation_date: Date of FOC recommendation
            objection_reasons: List of objection reasons

        Returns:
            Filled form content
        """
        recommendation_date = recommendation_date or "[Date of Recommendation]"
        objection_reasons = objection_reasons or [
            "FOC recommendation fails to apply all 12 best interest factors (MCL 722.23)",
            "FOC failed to consider Father's evidence and testimony",
            "FOC relied on unverified allegations from Mother without evidentiary basis",
            "FOC recommendation would maintain unconstitutional separation",
            "FOC did not consider documented pattern of parental alienation (Factor J)",
        ]

        lines = [
            "=" * 72,
            "SCAO FORM FOC 87 — OBJECTION TO",
            "FRIEND OF THE COURT RECOMMENDATION",
            "=" * 72,
            "",
            f"Court: {CASE_INFO['court']}, {CASE_INFO['county']} County",
            f"Case No.: {CASE_INFO['case_number']}",
            f"Judge: {CASE_INFO['judge']}",
            f"Date: {_today()}",
            "",
            f"Date of FOC Recommendation: {recommendation_date}",
            "⚠️  DEADLINE: 21 days from recommendation per MCL 552.507(5)",
            "",
            "OBJECTING PARTY:",
            f"  Name: {PLAINTIFF['name']}",
            f"  Role: {PLAINTIFF['role']} (Pro Se)",
            "",
            "I OBJECT to the Friend of the Court Recommendation for the",
            "following reasons:",
            "",
        ]
        for i, reason in enumerate(objection_reasons, 1):
            lines.append(f"  {i}. {reason}")

        lines.extend([
            "",
            "REQUESTED RELIEF:",
            "  1. De novo hearing on all custody/parenting time issues",
            "  2. Application of all 12 MCL 722.23 best interest factors",
            "  3. Consideration of Father's evidence and testimony",
            "  4. Immediate restoration of parenting time pending hearing",
            "",
            "I understand that I have the right to a de novo hearing on this",
            "objection per MCR 3.208(C) and MCL 552.507(5).",
            "",
            f"Date: {_today()}",
            "",
            "_______________________________",
            f"{PLAINTIFF['name']}, Pro Se",
            f"{PLAINTIFF['address_line1']}",
            f"{PLAINTIFF['city']}, {PLAINTIFF['state']} {PLAINTIFF['zip']}",
            "",
            "AUTHORITY: MCL 552.507(5); MCR 3.208(C); MCL 722.23",
        ])
        return "\n".join(lines)

    def list_forms(self) -> List[Dict[str, str]]:
        """Return available SCAO form templates."""
        return [
            {"form": "FOC 66", "title": "Uniform Order Regarding Parenting Time", "method": "fill_foc66"},
            {"form": "MC 97", "title": "Fee Waiver Request", "method": "fill_mc97"},
            {"form": "MC 280", "title": "Proof of Service", "method": "fill_mc280"},
            {"form": "CC 381", "title": "Verified Statement", "method": "fill_cc381"},
            {"form": "FOC 87", "title": "Objection to FOC Recommendation", "method": "fill_foc87"},
        ]


# ── JSON-RPC dispatch ─────────────────────────────────────────────────

def handle_rpc(method: str, params: Dict[str, Any] = None) -> Dict:
    params = params or {}
    filler = SCAOFormFiller()
    dispatch = {
        "fill_foc66": filler.fill_foc66,
        "fill_mc97": filler.fill_mc97,
        "fill_mc280": filler.fill_mc280,
        "fill_cc381": filler.fill_cc381,
        "fill_foc87": filler.fill_foc87,
        "list_forms": filler.list_forms,
    }
    fn = dispatch.get(method)
    if not fn:
        return {"error": f"Unknown method: {method}", "available": list(dispatch.keys())}
    try:
        result = fn(**params)
        return {"result": result, "method": method, "status": "ok"}
    except Exception as e:
        return {"error": str(e), "method": method}


if __name__ == "__main__":
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    filler = SCAOFormFiller()
    print("=== SCAO Form Filler Skill (a27 + m45) ===\n")
    print(f"Available forms: {[f['form'] for f in filler.list_forms()]}")
    print(f"Court addresses loaded: {len(filler.addresses)}")

    for form_info in filler.list_forms():
        fn = getattr(filler, form_info["method"])
        content = fn()
        print(f"\n{form_info['form']}: {len(content)} chars")

    print("\n[OK] SCAO Form Filler operational")
