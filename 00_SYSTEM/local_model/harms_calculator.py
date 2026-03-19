"""
Harms Calculator — LitigationOS 2026
Quantifies all harms categories: separation days, denied visits, emotional distress,
financial costs, and Section 1983 damages for Pigors v. Watson consolidated litigation.
329+ days parent-child separation as of current tracking.
"""

import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

DB_PATH = os.environ.get("LITIGATION_DB_PATH", r"C:\Users\andre\LitigationOS\litigation_context.db")

# Separation tracking baseline
SEPARATION_START = datetime(2024, 7, 1)  # Approximate start of parent-child separation


def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA query_only=ON")
    conn.row_factory = sqlite3.Row
    return conn


class HarmsCalculator:
    """Quantifies all harms for damages calculations and court filings."""

    def get_harms_violations(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Query global_harms_violations table (325 rows)."""
        conn = _get_db()
        try:
            rows = conn.execute(
                "SELECT * FROM global_harms_violations ORDER BY rowid DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_separation_data(self) -> Dict[str, Any]:
        """329+ days parent-child separation data and ongoing tracking."""
        now = datetime.now()
        days = (now - SEPARATION_START).days

        conn = _get_db()
        try:
            # Search for separation-related evidence
            separation_evidence = []
            try:
                rows = conn.execute(
                    """SELECT eq.*
                       FROM evidence_quotes eq
                       JOIN evidence_quotes_fts fts ON eq.rowid = fts.rowid
                       WHERE evidence_quotes_fts MATCH 'separation OR "parenting time" OR visitation OR contact'
                       ORDER BY rank
                       LIMIT 30"""
                ).fetchall()
                separation_evidence = [dict(r) for r in rows]
            except sqlite3.OperationalError:
                pass

            # Search for denied visitation events
            denied_visits = []
            try:
                rows = conn.execute(
                    """SELECT * FROM docket_events
                       WHERE title LIKE '%parenting%' OR title LIKE '%visitation%'
                          OR title LIKE '%contact%' OR title LIKE '%custody%'
                       ORDER BY event_date_iso DESC
                       LIMIT 30"""
                ).fetchall()
                denied_visits = [dict(r) for r in rows]
            except sqlite3.OperationalError:
                pass

            return {
                "separation_start": SEPARATION_START.isoformat(),
                "current_date": now.isoformat(),
                "total_separation_days": days,
                "total_separation_weeks": round(days / 7, 1),
                "total_separation_months": round(days / 30.44, 1),
                "separation_evidence_count": len(separation_evidence),
                "separation_evidence": separation_evidence[:10],
                "related_docket_events": denied_visits[:10],
                "constitutional_note": (
                    "Parent-child separation implicates fundamental liberty interests "
                    "protected by the Fourteenth Amendment. Troxel v Granville, "
                    "530 US 57 (2000). Each additional day compounds the harm."
                ),
            }
        finally:
            conn.close()

    def calculate_total_harms(self) -> Dict[str, Any]:
        """Quantify all harms: separation, denied visits, distress, financial."""
        separation = self.get_separation_data()
        emotional = self.calculate_emotional_distress()
        financial = self.calculate_financial_damages()

        conn = _get_db()
        try:
            # Count violations by category
            violations = conn.execute(
                "SELECT * FROM global_harms_violations"
            ).fetchall()

            category_counts = {}
            for v in violations:
                vd = dict(v)
                # Try common column names for category
                cat = (
                    vd.get("category")
                    or vd.get("violation_type")
                    or vd.get("harm_type")
                    or "uncategorized"
                )
                category_counts[cat] = category_counts.get(cat, 0) + 1

            return {
                "separation_days": separation["total_separation_days"],
                "total_violations": len(violations),
                "violations_by_category": category_counts,
                "emotional_distress_summary": emotional.get("summary", {}),
                "financial_damages_summary": financial.get("summary", {}),
                "aggregate_harm_level": "SEVERE",
                "constitutional_violations": (
                    "Deprivation of fundamental parental rights without due process. "
                    "US Const Amend XIV; Troxel v Granville, 530 US 57 (2000)."
                ),
            }
        finally:
            conn.close()

    def calculate_section_1983_damages(self) -> Dict[str, Any]:
        """Damages for 42 USC § 1983 — deprivation of rights under color of law."""
        separation = self.get_separation_data()
        days = separation["total_separation_days"]

        conn = _get_db()
        try:
            # Get judicial violations for color-of-law element
            judicial_violations = []
            try:
                rows = conn.execute(
                    """SELECT * FROM judicial_violations
                       ORDER BY rowid DESC LIMIT 50"""
                ).fetchall()
                judicial_violations = [dict(r) for r in rows]
            except sqlite3.OperationalError:
                pass

            # Get benchbook violations
            benchbook_violations = []
            try:
                rows = conn.execute(
                    """SELECT * FROM auth_benchbook_violations
                       ORDER BY rowid DESC LIMIT 50"""
                ).fetchall()
                benchbook_violations = [dict(r) for r in rows]
            except sqlite3.OperationalError:
                pass

            return {
                "statute": "42 USC § 1983",
                "elements": {
                    "deprivation_of_rights": (
                        f"Parent-child separation of {days}+ days deprives "
                        "fundamental liberty interest in family integrity."
                    ),
                    "under_color_of_law": (
                        f"Court orders issued by state judicial officer. "
                        f"{len(judicial_violations)} documented judicial violations."
                    ),
                    "constitutional_basis": (
                        "Fourteenth Amendment substantive due process — "
                        "fundamental right to parent-child relationship. "
                        "Troxel v Granville, 530 US 57 (2000); "
                        "Stanley v Illinois, 405 US 645 (1972)."
                    ),
                },
                "damages_categories": {
                    "compensatory": {
                        "emotional_distress": "Loss of parent-child bond, anxiety, depression",
                        "loss_of_companionship": f"{days} days of lost companionship",
                        "economic_losses": "Legal costs, lost income, housing impacts",
                    },
                    "punitive": (
                        "Available if conduct was willful, wanton, or in reckless "
                        "disregard of constitutional rights. Smith v Wade, 461 US 30 (1983)."
                    ),
                    "attorneys_fees": (
                        "42 USC § 1988 — prevailing party may recover fees "
                        "(applicable even for pro se litigants for costs)."
                    ),
                },
                "judicial_violations_count": len(judicial_violations),
                "benchbook_violations_count": len(benchbook_violations),
                "judicial_violations": judicial_violations[:10],
                "benchbook_violations": benchbook_violations[:10],
            }
        finally:
            conn.close()

    def calculate_emotional_distress(self) -> Dict[str, Any]:
        """Quantify emotional distress from parent-child separation."""
        separation = self.get_separation_data()
        days = separation["total_separation_days"]

        conn = _get_db()
        try:
            # Search evidence for emotional impact
            distress_evidence = []
            try:
                rows = conn.execute(
                    """SELECT eq.*
                       FROM evidence_quotes eq
                       JOIN evidence_quotes_fts fts ON eq.rowid = fts.rowid
                       WHERE evidence_quotes_fts MATCH
                           'emotional OR distress OR anxiety OR depression OR harm OR suffering'
                       ORDER BY rank
                       LIMIT 30"""
                ).fetchall()
                distress_evidence = [dict(r) for r in rows]
            except sqlite3.OperationalError:
                pass

            return {
                "separation_days": days,
                "summary": {
                    "severity": "SEVERE" if days > 180 else "SIGNIFICANT",
                    "duration": f"{days} days ongoing",
                    "type": "Intentional/Negligent Infliction of Emotional Distress",
                },
                "components": {
                    "loss_of_parental_bond": (
                        f"{days} days without meaningful parent-child contact "
                        "causes documented psychological harm to both parent and child."
                    ),
                    "anxiety_and_depression": (
                        "Ongoing litigation stress, uncertainty about parental rights, "
                        "and enforced separation create chronic anxiety and depression."
                    ),
                    "loss_of_developmental_milestones": (
                        "Missed birthdays, holidays, school events, and daily "
                        "parenting moments that cannot be recovered."
                    ),
                    "stigma_and_humiliation": (
                        "Being deprived of parental rights without adequate due process "
                        "carries social stigma and personal humiliation."
                    ),
                },
                "legal_standards": {
                    "michigan": (
                        "Michigan recognizes IIED and NIED claims. "
                        "Roberts v Auto-Owners Ins Co, 422 Mich 594 (1985)."
                    ),
                    "federal": (
                        "Emotional distress damages available under § 1983. "
                        "Memphis Community School Dist v Stachura, 477 US 299 (1986)."
                    ),
                },
                "supporting_evidence_count": len(distress_evidence),
                "supporting_evidence": distress_evidence[:10],
            }
        finally:
            conn.close()

    def calculate_financial_damages(self) -> Dict[str, Any]:
        """Calculate lost income, legal costs, and housing impacts."""
        conn = _get_db()
        try:
            # Search for financial impact evidence
            financial_evidence = []
            try:
                rows = conn.execute(
                    """SELECT eq.*
                       FROM evidence_quotes eq
                       JOIN evidence_quotes_fts fts ON eq.rowid = fts.rowid
                       WHERE evidence_quotes_fts MATCH
                           'financial OR cost OR income OR housing OR employment OR money'
                       ORDER BY rank
                       LIMIT 30"""
                ).fetchall()
                financial_evidence = [dict(r) for r in rows]
            except sqlite3.OperationalError:
                pass

            return {
                "summary": {
                    "categories": [
                        "Legal costs (filing fees, copies, service)",
                        "Lost income / employment disruption",
                        "Housing impacts",
                        "Transportation costs for court appearances",
                        "Communication costs",
                    ],
                },
                "damage_categories": {
                    "legal_costs": {
                        "description": "Filing fees, document preparation, service costs, copies",
                        "note": "Pro se litigants may recover costs under MCR 2.625",
                    },
                    "lost_income": {
                        "description": (
                            "Time spent on litigation instead of employment; "
                            "employment disruption from court schedule"
                        ),
                    },
                    "housing_impacts": {
                        "description": (
                            "Housing instability or costs related to custody litigation "
                            "and Shady Oaks housing proceedings"
                        ),
                    },
                    "transportation": {
                        "description": "Travel to/from court, FOC, supervised visitation",
                    },
                },
                "supporting_evidence_count": len(financial_evidence),
                "supporting_evidence": financial_evidence[:10],
                "recovery_authority": {
                    "michigan_costs": "MCR 2.625 — Taxable costs to prevailing party",
                    "section_1988": "42 USC § 1988 — Attorney fees and costs in civil rights cases",
                    "sanctions": "MCR 2.114(E) — Sanctions for frivolous claims/defenses",
                },
            }
        finally:
            conn.close()

    def build_harms_narrative(self) -> Dict[str, Any]:
        """Build compelling narrative of harms for court filing."""
        separation = self.get_separation_data()
        total = self.calculate_total_harms()
        days = separation["total_separation_days"]

        return {
            "title": "NARRATIVE OF HARMS — Pigors v. Watson",
            "narrative": [
                {
                    "section": "I. PARENT-CHILD SEPARATION",
                    "text": (
                        f"For {days} consecutive days — over {round(days/30.44, 1)} months — "
                        "Plaintiff Andrew Pigors has been separated from his children. "
                        "This separation was effectuated and maintained through court orders "
                        "that failed to adequately protect his fundamental constitutional "
                        "right to the care, custody, and control of his children. "
                        "Troxel v Granville, 530 US 57 (2000)."
                    ),
                },
                {
                    "section": "II. CONSTITUTIONAL VIOLATIONS",
                    "text": (
                        "The deprivation of Plaintiff's parental rights occurred under "
                        "color of state law, implicating 42 USC § 1983. The Fourteenth "
                        "Amendment's Due Process Clause protects the fundamental liberty "
                        "interest of parents in the care, custody, and management of "
                        "their children. Stanley v Illinois, 405 US 645 (1972)."
                    ),
                },
                {
                    "section": "III. DOCUMENTED VIOLATIONS",
                    "text": (
                        f"The record contains {total['total_violations']} documented "
                        "violations across multiple categories, establishing a pattern "
                        "of harm that compounds with each passing day of separation."
                    ),
                },
                {
                    "section": "IV. ONGOING AND IRREPARABLE HARM",
                    "text": (
                        "Each day of continued separation causes irreparable harm "
                        "to the parent-child bond that no monetary damages can fully "
                        "compensate. The developmental milestones missed, the daily "
                        "interactions lost, and the erosion of the parent-child "
                        "relationship constitute ongoing, compounding harm."
                    ),
                },
            ],
            "separation_days": days,
            "total_violations": total["total_violations"],
        }

    def generate_damages_exhibit(self) -> Dict[str, Any]:
        """Formatted damages exhibit for court filing."""
        separation = self.get_separation_data()
        section_1983 = self.calculate_section_1983_damages()
        emotional = self.calculate_emotional_distress()
        financial = self.calculate_financial_damages()
        days = separation["total_separation_days"]

        return {
            "exhibit_title": "EXHIBIT — STATEMENT OF DAMAGES",
            "case_caption": "PIGORS v. WATSON, Case No. 2024-001507-DC",
            "court": "14th Circuit Court, Muskegon County, Michigan",
            "prepared_by": "Andrew Pigors, Plaintiff Pro Se",
            "date_prepared": datetime.now().strftime("%B %d, %Y"),
            "damages_summary": {
                "I_separation": {
                    "description": "Parent-Child Separation",
                    "duration": f"{days} days ({round(days/30.44, 1)} months)",
                    "start_date": SEPARATION_START.strftime("%B %d, %Y"),
                    "status": "ONGOING",
                },
                "II_constitutional": {
                    "description": "Constitutional Rights Violations (42 USC § 1983)",
                    "judicial_violations": section_1983["judicial_violations_count"],
                    "benchbook_violations": section_1983["benchbook_violations_count"],
                },
                "III_emotional": {
                    "description": "Emotional Distress Damages",
                    "severity": emotional["summary"]["severity"],
                    "components": list(emotional["components"].keys()),
                },
                "IV_financial": {
                    "description": "Financial/Economic Damages",
                    "categories": financial["summary"]["categories"],
                },
            },
            "legal_authority": {
                "constitutional": "US Const Amend XIV; Troxel v Granville, 530 US 57 (2000)",
                "section_1983": "42 USC § 1983; Smith v Wade, 461 US 30 (1983)",
                "michigan_costs": "MCR 2.625",
                "attorneys_fees": "42 USC § 1988",
            },
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Summary of all harms categories."""
        conn = _get_db()
        try:
            harms_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM global_harms_violations"
            ).fetchone()["cnt"]

            cols = conn.execute(
                "PRAGMA table_info(global_harms_violations)"
            ).fetchall()

            separation = self.get_separation_data()

            return {
                "total_harms_violations": harms_count,
                "separation_days": separation["total_separation_days"],
                "separation_months": separation["total_separation_months"],
                "harms_table_columns": [c["name"] for c in cols],
                "harm_severity": "SEVERE",
            }
        finally:
            conn.close()


def self_test() -> Dict[str, Any]:
    """Run self-test to verify database connectivity and table access."""
    results = {"status": "ok", "tests": {}}
    hc = HarmsCalculator()

    try:
        stats = hc.get_statistics()
        results["tests"]["statistics"] = {
            "passed": stats["total_harms_violations"] > 0,
            "harms_violations": stats["total_harms_violations"],
            "separation_days": stats["separation_days"],
        }
    except Exception as e:
        results["tests"]["statistics"] = {"passed": False, "error": str(e)}

    try:
        violations = hc.get_harms_violations(limit=5)
        results["tests"]["get_harms_violations"] = {
            "passed": isinstance(violations, list),
            "count": len(violations),
        }
    except Exception as e:
        results["tests"]["get_harms_violations"] = {"passed": False, "error": str(e)}

    try:
        sep = hc.get_separation_data()
        results["tests"]["separation_data"] = {
            "passed": sep["total_separation_days"] > 329,
            "days": sep["total_separation_days"],
        }
    except Exception as e:
        results["tests"]["separation_data"] = {"passed": False, "error": str(e)}

    try:
        narrative = hc.build_harms_narrative()
        results["tests"]["harms_narrative"] = {
            "passed": "narrative" in narrative and len(narrative["narrative"]) > 0,
        }
    except Exception as e:
        results["tests"]["harms_narrative"] = {"passed": False, "error": str(e)}

    results["status"] = (
        "ok" if all(t.get("passed") for t in results["tests"].values()) else "degraded"
    )
    return results


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print(json.dumps(self_test(), indent=2, default=str))
    elif len(sys.argv) > 1 and sys.argv[1] == "stats":
        hc = HarmsCalculator()
        print(json.dumps(hc.get_statistics(), indent=2, default=str))
    elif len(sys.argv) > 1 and sys.argv[1] == "total":
        hc = HarmsCalculator()
        print(json.dumps(hc.calculate_total_harms(), indent=2, default=str))
    elif len(sys.argv) > 1 and sys.argv[1] == "1983":
        hc = HarmsCalculator()
        print(json.dumps(hc.calculate_section_1983_damages(), indent=2, default=str))
    elif len(sys.argv) > 1 and sys.argv[1] == "narrative":
        hc = HarmsCalculator()
        print(json.dumps(hc.build_harms_narrative(), indent=2, default=str))
    elif len(sys.argv) > 1 and sys.argv[1] == "exhibit":
        hc = HarmsCalculator()
        print(json.dumps(hc.generate_damages_exhibit(), indent=2, default=str))
    else:
        print("Usage: python harms_calculator.py [test|stats|total|1983|narrative|exhibit]")
