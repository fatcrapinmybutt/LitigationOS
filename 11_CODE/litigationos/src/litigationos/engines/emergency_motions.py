"""Emergency Motion Template Engine — MCR 3.310, MCL 722.27, MCR 7.209.

Generates court-ready emergency motion documents for immediate custody
changes, ex parte TROs, stays pending appeal, and PPO modifications.
All output is Michigan-compliant markdown ready for PDF conversion.

Usage::

    engine = EmergencyMotionEngine()
    tro = engine.generate_ex_parte_tro()
    custody = engine.generate_emergency_custody_change()
    stay = engine.generate_stay_pending_appeal()
    types = engine.list_emergency_types()
    reqs = engine.check_emergency_requirements("ex_parte_tro")
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_DB = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")

# ---------------------------------------------------------------------------
# Verified party identity — SINGLE SOURCE OF TRUTH
# ---------------------------------------------------------------------------
PARTIES: dict[str, dict[str, str]] = {
    "plaintiff": {
        "name": "Andrew James Pigors",
        "address": "1977 Whitehall Road, Lot 17, North Muskegon, MI 49445",
        "phone": "(231) 903-5690",
        "email": "andrewjpigors@gmail.com",
    },
    "defendant": {
        "name": "Emily A. Watson",
        "address": "2160 Garland Drive, Norton Shores, MI 49441",
    },
    "child": {
        "initials": "L.D.W.",
        "note": "Initials only per MCR 8.119(H)",
    },
    "judge": {
        "name": "Hon. Jenny L. McNeill",
        "court": "14th Circuit Court, Family Division",
        "address": "990 Terrace St, Muskegon, MI 49442",
    },
    "foc": {
        "name": "Pamela Rusco",
        "title": "Friend of the Court",
        "address": "990 Terrace St, Muskegon, MI 49442",
    },
    "defendant_attorney": {
        "name": "Jennifer Barnes (P55406)",
        "firm": "Barnes Law Firm PLLC",
        "address": "880 Jefferson St Ste B, Muskegon, MI 49440",
        "status": "WITHDREW",
    },
}

CASE_INFO: dict[str, str] = {
    "case_number": "2024-001507-DC",
    "court": "14th Circuit Court, Family Division, Muskegon County",
    "judge": "Hon. Jenny L. McNeill",
}

# Ex parte order date used to compute separation days
_EX_PARTE_ORDER_DATE = date(2025, 8, 8)

# ---------------------------------------------------------------------------
# Emergency motion type definitions
# ---------------------------------------------------------------------------
EMERGENCY_TYPES: dict[str, dict[str, Any]] = {
    "ex_parte_tro": {
        "title": "Ex Parte Motion for Temporary Restraining Order",
        "authority": ["MCR 3.310", "MCL 722.27", "MCL 722.23"],
        "description": (
            "Emergency TRO to restrain interference with parenting time "
            "and prevent further alienation of the parent-child bond."
        ),
        "requirements": [
            "Verified complaint or affidavit showing irreparable harm",
            "Specific facts showing immediate danger or harm to child",
            "Evidence that notice to adverse party is impracticable",
            "Bond may be required under MCR 3.310(D)",
            "Hearing must be scheduled within 14 days — MCR 3.310(B)(2)(b)",
        ],
        "court_rules": {
            "MCR 3.310(A)": "Standards for issuance of TRO",
            "MCR 3.310(B)(2)(a)": "Ex parte TRO without notice",
            "MCR 3.310(B)(2)(b)": "14-day hearing requirement",
            "MCL 722.27(1)(c)": "Court authority to modify custody",
            "MCL 722.23": "Best interest factors",
        },
    },
    "emergency_custody_change": {
        "title": "Emergency Motion to Modify Custody",
        "authority": ["MCL 722.27(1)(c)", "MCL 722.23", "MCR 3.207(B)"],
        "description": (
            "Emergency modification of custody where the child's current "
            "environment poses an immediate danger to well-being."
        ),
        "requirements": [
            "Showing of proper cause or change of circumstances",
            "Clear and convincing evidence of immediate danger",
            "Best interest analysis under MCL 722.23",
            "Established custodial environment analysis",
            "Compliance with MCR 3.207(B) — verified statement",
        ],
        "court_rules": {
            "MCL 722.27(1)(c)": "Modification authority",
            "MCL 722.23": "Best interest factors (a)-(l)",
            "MCR 3.207(B)": "Verified statement requirement",
            "Vodvarka v Grasmeyer": "Change of circumstances standard",
        },
    },
    "stay_pending_appeal": {
        "title": "Emergency Motion for Stay Pending Appeal",
        "authority": ["MCR 7.209", "MCR 7.211(C)(6)"],
        "description": (
            "Motion to preserve the status quo during appellate review "
            "by staying enforcement of the trial court's order."
        ),
        "requirements": [
            "Filed first in the trial court — MCR 7.209(A)(1)",
            "Likelihood of success on the merits",
            "Irreparable harm absent the stay",
            "Balance of hardships favors movant",
            "Stay would not harm the public interest",
        ],
        "court_rules": {
            "MCR 7.209(A)": "Stay pending appeal — trial court",
            "MCR 7.209(B)": "Stay pending appeal — appellate court",
            "MCR 7.211(C)(6)": "Emergency motions in COA",
        },
    },
    "emergency_ppo_modification": {
        "title": "Emergency Motion to Modify Personal Protection Order",
        "authority": ["MCL 600.2950a", "MCR 3.310"],
        "description": (
            "Emergency modification of PPO terms where current order "
            "causes undue hardship or changed circumstances warrant relief."
        ),
        "requirements": [
            "Filing in court that issued the PPO",
            "Specific facts showing changed circumstances",
            "Evidence that current terms cause undue hardship",
            "Proposed modified terms",
            "Service on protected party",
        ],
        "court_rules": {
            "MCL 600.2950a": "PPO modification authority",
            "MCR 3.707": "Personal protection order procedures",
        },
    },
}


class EmergencyMotionEngine:
    """Generate emergency motion documents with DB-backed evidence counts.

    Parameters
    ----------
    db_path : str | Path | None
        Path to ``litigation_context.db``.  Falls back to the default
        LitigationOS database path when *None*.
    """

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path else _DEFAULT_DB
        self._ensure_tables()
        logger.info("EmergencyMotionEngine ready  db=%s", self.db_path)

    # ------------------------------------------------------------------
    # DB helpers
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=60)
        conn.execute("PRAGMA busy_timeout = 60000")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA cache_size = -32000")
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_tables(self) -> None:
        if not self.db_path.exists():
            logger.warning("DB not found at %s — template-only mode", self.db_path)
            return
        conn = self._connect()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS emergency_motion_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    motion_type TEXT NOT NULL,
                    case_number TEXT NOT NULL,
                    generated_at TEXT DEFAULT (datetime('now')),
                    filed_at TEXT,
                    status TEXT DEFAULT 'draft',
                    notes TEXT
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def _safe_count(self, table: str, where: str = "") -> int:
        """Return ``COUNT(*)`` from *table* or 0 if unavailable."""
        if not self.db_path.exists():
            return 0
        conn = self._connect()
        try:
            sql = f"SELECT COUNT(*) FROM [{table}]"
            if where:
                sql += f" WHERE {where}"
            return conn.execute(sql).fetchone()[0]
        except Exception:
            return 0
        finally:
            conn.close()

    def _query_evidence_counts(self) -> dict[str, int]:
        """Fetch evidence counts used in emergency motion arguments."""
        if not self.db_path.exists():
            return {}
        conn = self._connect()
        try:
            row = conn.execute("""
                SELECT
                    (SELECT COUNT(*) FROM alienation_timeline) AS alienation,
                    (SELECT COUNT(*) FROM judicial_bias_chronology) AS bias,
                    (SELECT COUNT(*) FROM evidence_quotes) AS quotes,
                    (SELECT COUNT(*) FROM judicial_violations) AS violations,
                    (SELECT COUNT(*) FROM documents) AS documents,
                    (SELECT COUNT(*) FROM docket_events) AS docket
            """).fetchone()
            return {
                "alienation_events": row["alienation"],
                "judicial_bias_events": row["bias"],
                "evidence_quotes": row["quotes"],
                "judicial_violations": row["violations"],
                "documents": row["documents"],
                "docket_events": row["docket"],
            }
        except Exception as exc:
            logger.warning("Evidence count query failed: %s", exc)
            return {}
        finally:
            conn.close()

    def _query_best_interest_factors(self) -> list[dict[str, Any]]:
        """Return best-interest factor analysis from DB."""
        if not self.db_path.exists():
            return []
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT * FROM best_interest_summary ORDER BY rowid"
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception as exc:
            logger.warning("Best interest query failed: %s", exc)
            return []
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Shared formatting helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _separation_days() -> int:
        return (date.today() - _EX_PARTE_ORDER_DATE).days

    @staticmethod
    def _caption() -> str:
        p = PARTIES["plaintiff"]
        d = PARTIES["defendant"]
        separator = "\\_" * 25 + "/\n"
        return (
            "# STATE OF MICHIGAN\n\n"
            "# IN THE CIRCUIT COURT FOR THE COUNTY OF MUSKEGON\n\n"
            "# FAMILY DIVISION\n\n"
            "---\n\n"
            f"{p['name'].upper()},\n"
            f"{p['address']}\n"
            f"Phone: {p['phone']}\n"
            f"Email: {p['email']}\n\n"
            "&nbsp;&nbsp;&nbsp;&nbsp;*Plaintiff, Pro Se*,\n\n"
            f"v. &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            f" **Case No. {CASE_INFO['case_number']}**\n"
            f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            f"&nbsp;&nbsp;&nbsp;&nbsp;"
            f" **{CASE_INFO['judge']}**\n\n"
            f"{d['name'].upper()},\n"
            f"{d['address']}\n\n"
            "&nbsp;&nbsp;&nbsp;&nbsp;*Defendant*.\n\n"
            f"{separator}\n"
            "---\n"
        )

    @staticmethod
    def _verification() -> str:
        p = PARTIES["plaintiff"]
        today_str = date.today().strftime("%B %d, %Y")
        return (
            "---\n\n"
            "## VERIFICATION\n\n"
            f"I, {p['name']}, declare under penalty of perjury "
            "pursuant to MCL 600.1561 that the foregoing statements "
            "are true and correct to the best of my knowledge, "
            "information, and belief.\n\n"
            f"Dated: {today_str}\n\n"
            "\\__________________________________________\n"
            f"{p['name']}\n"
            f"{p['address']}\n"
            f"Phone: {p['phone']}\n"
            f"Email: {p['email']}\n"
            "*Plaintiff, Pro Se*\n"
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def list_emergency_types(self) -> list[dict[str, Any]]:
        """Return metadata for all supported emergency motion types."""
        result = []
        for type_id, info in EMERGENCY_TYPES.items():
            result.append({
                "id": type_id,
                "title": info["title"],
                "authority": info["authority"],
                "description": info["description"],
            })
        return result

    def check_emergency_requirements(self, motion_type: str) -> dict[str, Any]:
        """Return checklist of requirements for *motion_type*.

        Returns
        -------
        dict
            ``type``, ``title``, ``requirements`` list, ``court_rules``
            mapping, and ``evidence_available`` counts from the DB.
        """
        if motion_type not in EMERGENCY_TYPES:
            raise ValueError(
                f"Unknown motion type: {motion_type!r}. "
                f"Valid: {list(EMERGENCY_TYPES)}"
            )
        info = EMERGENCY_TYPES[motion_type]
        return {
            "type": motion_type,
            "title": info["title"],
            "requirements": info["requirements"],
            "court_rules": info["court_rules"],
            "evidence_available": self._query_evidence_counts(),
        }

    def generate_emergency_motion(
        self,
        motion_type: str,
        facts: list[str] | None = None,
        relief_requested: list[str] | None = None,
    ) -> str:
        """Generate a generic emergency motion document.

        Parameters
        ----------
        motion_type : str
            One of the keys in :data:`EMERGENCY_TYPES`.
        facts : list[str] | None
            Specific factual statements for the motion body.
        relief_requested : list[str] | None
            Specific relief items for the prayer.

        Returns
        -------
        str
            Court-ready markdown document.
        """
        if motion_type not in EMERGENCY_TYPES:
            raise ValueError(
                f"Unknown motion type: {motion_type!r}. "
                f"Valid: {list(EMERGENCY_TYPES)}"
            )
        info = EMERGENCY_TYPES[motion_type]
        facts = facts or ["[INSERT SPECIFIC FACTS]"]
        relief_requested = relief_requested or ["[INSERT SPECIFIC RELIEF REQUESTED]"]

        doc = self._caption()
        doc += f"\n# {info['title'].upper()}\n\n---\n\n"

        # Introduction
        p = PARTIES["plaintiff"]
        doc += (
            f"**NOW COMES** Plaintiff, {p['name']}, appearing *pro se*, "
            "and respectfully moves this Honorable Court pursuant to "
            f"**{', '.join(info['authority'])}** for entry of the relief "
            "described herein.\n\n"
        )

        # Facts
        doc += "## I. STATEMENT OF FACTS\n\n"
        for i, fact in enumerate(facts, 1):
            doc += f"{i}. {fact}\n\n"

        # Legal standard
        doc += "## II. LEGAL STANDARD\n\n"
        for rule, desc in info["court_rules"].items():
            doc += f"- **{rule}** — {desc}\n"
        doc += "\n"

        # Relief
        doc += "## III. RELIEF REQUESTED\n\n"
        doc += "WHEREFORE, Plaintiff respectfully requests that this Court:\n\n"
        for i, item in enumerate(relief_requested, 1):
            doc += f"{i}. {item}\n"
        doc += "\nAnd for such other and further relief as this Court deems just.\n"

        doc += self._verification()
        self._log_generation(motion_type)
        return doc

    def generate_ex_parte_tro(self) -> str:
        """Generate the pre-built Ex Parte TRO for *Pigors v. Watson*.

        This is the F1 filing package main document.  All evidence counts
        come from the database — nothing is fabricated.
        """
        counts = self._query_evidence_counts()
        factors = self._query_best_interest_factors()
        sep_days = self._separation_days()
        today_str = date.today().strftime("%B %d, %Y")
        p = PARTIES["plaintiff"]
        d = PARTIES["defendant"]
        child = PARTIES["child"]["initials"]

        doc = self._caption()

        # Title
        doc += (
            "\n# EX PARTE MOTION FOR TEMPORARY RESTRAINING ORDER\n"
            "## Pursuant to MCR 3.310\n\n---\n\n"
        )

        # I. Introduction
        doc += "## I. INTRODUCTION\n\n"
        doc += (
            f"Plaintiff, {p['name']}, appearing *pro se*, respectfully "
            "moves this Court on an emergency ex parte basis, pursuant to "
            "**MCR 3.310**, for entry of a Temporary Restraining Order "
            f"restraining Defendant, {d['name']}, from interfering with "
            f"Plaintiff's parenting time with the minor child, {child}.\n\n"
            "This motion is brought on an emergency basis because the "
            f"minor child has been separated from the Plaintiff-Father for "
            f"**{sep_days} consecutive days** following an ex parte order "
            "entered on August 8, 2025, which suspended all parenting time "
            "without the hearing required by MCR 3.310(B)(2)(b). Every day "
            "of continued separation causes irreparable harm to the "
            "parent-child bond that cannot be remedied by monetary damages.\n\n"
        )

        # II. Statement of facts
        doc += "## II. STATEMENT OF FACTS\n\n"
        doc += (
            f"1. Plaintiff and Defendant are parents of {child}, "
            "a minor child who is the subject of the above-captioned custody "
            "proceeding.\n\n"
            "2. On **August 8, 2025**, the Court entered an ex parte order "
            "suspending all of Plaintiff's parenting time with "
            f"{child}.\n\n"
            "3. Pursuant to **MCR 3.310(B)(2)(b)**, when a TRO is issued "
            "without notice, a hearing must be scheduled within **14 days** "
            "of the order's entry. No such hearing was held within the "
            "required timeframe.\n\n"
            f"4. As of {today_str}, **{sep_days} days** have elapsed since "
            "the ex parte order was entered, during which Plaintiff has had "
            f"no contact with {child}.\n\n"
        )

        # Evidence-backed facts
        if counts.get("alienation_events", 0) > 0:
            doc += (
                f"5. The litigation database documents **"
                f"{counts['alienation_events']:,} alienation-related events** "
                "demonstrating a sustained pattern of interference with the "
                "parent-child relationship. *(Source: ``alienation_timeline`` "
                "table)*\n\n"
            )
        if counts.get("judicial_bias_events", 0) > 0:
            doc += (
                f"6. The record reflects **{counts['judicial_bias_events']:,} "
                "documented instances** of procedural irregularities in this "
                "case. *(Source: ``judicial_bias_chronology`` table)*\n\n"
            )
        doc += (
            "7. The cumulative effect of the above separation — combined with "
            "the absence of required procedural safeguards — has caused and "
            f"continues to cause irreparable harm to {child} and to "
            "Plaintiff's constitutionally protected parental rights.\n\n"
        )

        # III. Legal standard
        doc += "## III. LEGAL STANDARD\n\n"
        doc += "### A. Temporary Restraining Orders — MCR 3.310\n\n"
        doc += (
            "Under **MCR 3.310(A)**, a court may issue a TRO to preserve "
            "the status quo where the moving party demonstrates:\n\n"
            "1. **Irreparable injury** will result absent the TRO;\n"
            "2. The **harm to the movant** outweighs the harm to the "
            "opposing party;\n"
            "3. The movant has shown a **likelihood of success** on the "
            "merits; and\n"
            "4. The **public interest** will not be adversely affected.\n\n"
        )
        doc += "### B. Best Interest of the Child — MCL 722.23\n\n"
        doc += (
            "All custody determinations must be guided by the best interest "
            "of the child under **MCL 722.23**, which enumerates factors "
            "(a) through (l). The evidence in this case demonstrates:\n\n"
        )
        if factors:
            for f in factors:
                factor_id = f.get("factor_id", f.get("factor", ""))
                label = f.get("factor_label", f.get("description", ""))
                direction = f.get("advantage_direction", f.get("direction", ""))
                ev_count = f.get("evidence_count", "")
                line = f"- **Factor {factor_id}** ({label})"
                if direction:
                    line += f" — *{direction}*"
                if ev_count:
                    line += f" ({ev_count:,} evidence items)" if isinstance(ev_count, int) else f" ({ev_count} evidence items)"
                doc += line + "\n"
            doc += "\n"
        else:
            doc += (
                "- Best interest factor analysis available in "
                "``best_interest_summary`` table of the litigation database.\n\n"
            )

        doc += "### C. Constitutional Protections\n\n"
        doc += (
            "The United States Supreme Court has recognized that parents "
            "have a **fundamental liberty interest** in the care, custody, "
            "and control of their children. *Troxel v. Granville*, 530 U.S. "
            "57, 65 (2000). The Michigan Supreme Court has similarly held "
            "that a parent's right to the custody of their child is a "
            "fundamental right. *Heltzel v. Heltzel*, 248 Mich App 1, 28 "
            "(2001).\n\n"
        )

        # IV. Argument
        doc += "## IV. ARGUMENT\n\n"

        doc += "### A. Immediate and Irreparable Harm\n\n"
        doc += (
            f"Plaintiff has been completely separated from {child} for "
            f"**{sep_days} consecutive days**. Child development research "
            "consistently demonstrates that prolonged separation from a "
            "bonded parent causes measurable psychological harm. "
            "This harm compounds daily and cannot be undone by any later "
            "award of parenting time or monetary compensation.\n\n"
            "The original ex parte order of August 8, 2025 required a "
            "hearing within 14 days under MCR 3.310(B)(2)(b). The failure "
            "to conduct that hearing has transformed a temporary emergency "
            f"measure into an indefinite suspension of Plaintiff's parental "
            "rights — a result neither authorized nor contemplated by the "
            "court rules.\n\n"
        )

        doc += "### B. Likelihood of Success on the Merits\n\n"
        doc += (
            "Plaintiff is likely to succeed on the merits because:\n\n"
            "1. The ex parte order was entered without the procedural "
            "safeguards required by MCR 3.310(B)(2)(b);\n"
            "2. No hearing was held within the mandatory 14-day window;\n"
        )
        if counts.get("evidence_quotes", 0) > 0:
            doc += (
                f"3. The evidentiary record contains **"
                f"{counts['evidence_quotes']:,} catalogued evidence items** "
                "supporting Plaintiff's parenting capability; and\n"
            )
        doc += (
            "4. The best interest analysis under MCL 722.23 favors "
            "restoration of Plaintiff's parenting time.\n\n"
        )

        doc += "### C. Balance of Hardships\n\n"
        doc += (
            "The balance of hardships overwhelmingly favors Plaintiff. "
            "Plaintiff faces the **complete loss** of a parental "
            f"relationship with {child}. Defendant, by contrast, would "
            "face only the obligation to comply with a reasonable parenting "
            "time schedule — an obligation already imposed by prior court "
            "orders. The requested TRO does not prevent Defendant from "
            "exercising her own custodial rights.\n\n"
        )

        doc += "### D. Public Interest\n\n"
        doc += (
            "Michigan's public policy strongly favors maintaining the "
            "parent-child relationship. **MCL 722.27a(1)** declares that "
            "\"it is in the best interests of a child to have a strong "
            "relationship with both of the child's parents.\" Granting "
            "this TRO advances that public policy.\n\n"
        )

        # V. Relief requested
        doc += "## V. RELIEF REQUESTED\n\n"
        doc += (
            "WHEREFORE, Plaintiff respectfully requests that this "
            "Honorable Court:\n\n"
            "1. **Issue a Temporary Restraining Order** pursuant to "
            "MCR 3.310, restraining Defendant from interfering with "
            f"Plaintiff's parenting time with {child};\n\n"
            "2. **Establish a temporary parenting time schedule** providing "
            f"Plaintiff with regular and meaningful contact with {child}, "
            "including but not limited to alternating weekends and midweek "
            "parenting time;\n\n"
            "3. **Order a hearing within 14 days** of the issuance of this "
            "TRO, in compliance with MCR 3.310(B)(2)(b), to determine "
            "whether a preliminary injunction should issue;\n\n"
            "4. **Enter an order prohibiting either party from removing "
            f"{child} from the jurisdiction** of this Court without prior "
            "written consent of the other party or further order of the "
            "Court;\n\n"
            "5. **Grant such other and further relief** as this Court deems "
            "just and equitable.\n\n"
        )

        doc += self._verification()

        self._log_generation("ex_parte_tro")
        return doc

    def generate_emergency_custody_change(self) -> str:
        """Generate Emergency Motion to Modify Custody for *Pigors v. Watson*."""
        counts = self._query_evidence_counts()
        factors = self._query_best_interest_factors()
        sep_days = self._separation_days()
        today_str = date.today().strftime("%B %d, %Y")
        p = PARTIES["plaintiff"]
        d = PARTIES["defendant"]
        child = PARTIES["child"]["initials"]

        doc = self._caption()
        doc += (
            "\n# EMERGENCY MOTION TO MODIFY CUSTODY\n"
            "## Pursuant to MCL 722.27(1)(c) and MCR 3.207(B)\n\n---\n\n"
        )

        doc += "## I. INTRODUCTION\n\n"
        doc += (
            f"Plaintiff, {p['name']}, respectfully moves this Court for an "
            "emergency modification of custody pursuant to "
            "**MCL 722.27(1)(c)** and **MCR 3.207(B)**. Proper cause and "
            "a change in circumstances exist to warrant modification, and "
            f"the current custody arrangement is causing ongoing harm to "
            f"{child}.\n\n"
        )

        doc += "## II. CHANGE OF CIRCUMSTANCES\n\n"
        doc += (
            f"1. On August 8, 2025, this Court entered an ex parte order "
            "suspending all of Plaintiff's parenting time. As of "
            f"{today_str}, **{sep_days} days** have passed without any "
            f"contact between Plaintiff and {child}.\n\n"
            "2. The suspension was imposed without the hearing required by "
            "MCR 3.310(B)(2)(b), violating Plaintiff's due process "
            "rights.\n\n"
        )
        if counts.get("alienation_events", 0) > 0:
            doc += (
                f"3. The evidentiary record documents **"
                f"{counts['alienation_events']:,} alienation-related events** "
                "demonstrating a pattern of deliberate interference with the "
                "parent-child relationship. *(Source: ``alienation_timeline`` "
                "table)*\n\n"
            )

        doc += "## III. BEST INTEREST ANALYSIS — MCL 722.23\n\n"
        if factors:
            for f in factors:
                fid = f.get("factor_id", f.get("factor", ""))
                label = f.get("factor_label", f.get("description", ""))
                direction = f.get("advantage_direction", f.get("direction", ""))
                doc += f"- **Factor {fid}** ({label}) — *{direction}*\n"
            doc += "\n"
        else:
            doc += (
                "Factor analysis is available in the ``best_interest_summary`` "
                "table.\n\n"
            )

        doc += "## IV. ESTABLISHED CUSTODIAL ENVIRONMENT\n\n"
        doc += (
            "Plaintiff contends that the prolonged, court-ordered separation "
            "has disrupted any established custodial environment that "
            "previously existed with Defendant, and that the current "
            f"arrangement is detrimental to {child}'s welfare.\n\n"
        )

        doc += "## V. RELIEF REQUESTED\n\n"
        doc += (
            "WHEREFORE, Plaintiff respectfully requests:\n\n"
            f"1. That custody of {child} be modified to grant Plaintiff "
            "primary physical custody, or in the alternative, joint "
            "physical custody with a substantially equal parenting time "
            "schedule;\n\n"
            "2. That the Court schedule an evidentiary hearing on this "
            "motion on an expedited basis;\n\n"
            "3. That the Court appoint a guardian ad litem to represent "
            f"the interests of {child}; and\n\n"
            "4. Such other and further relief as the Court deems just.\n\n"
        )

        doc += self._verification()
        self._log_generation("emergency_custody_change")
        return doc

    def generate_stay_pending_appeal(self) -> str:
        """Generate Emergency Motion for Stay Pending Appeal."""
        sep_days = self._separation_days()
        counts = self._query_evidence_counts()
        p = PARTIES["plaintiff"]
        child = PARTIES["child"]["initials"]

        doc = self._caption()
        doc += (
            "\n# EMERGENCY MOTION FOR STAY PENDING APPEAL\n"
            "## Pursuant to MCR 7.209\n\n---\n\n"
        )

        doc += "## I. INTRODUCTION\n\n"
        doc += (
            f"Plaintiff, {p['name']}, respectfully moves this Court "
            "for a stay of the order entered on August 8, 2025, pending "
            "appeal to the Michigan Court of Appeals, pursuant to "
            "**MCR 7.209**.\n\n"
        )

        doc += "## II. STANDARD FOR STAY\n\n"
        doc += (
            "Under **MCR 7.209**, a stay pending appeal may be granted "
            "where the movant demonstrates:\n\n"
            "1. A **likelihood of success** on the merits of the appeal;\n"
            "2. **Irreparable harm** absent a stay;\n"
            "3. The **balance of hardships** favors a stay; and\n"
            "4. The **public interest** supports a stay.\n\n"
        )

        doc += "## III. ARGUMENT\n\n"
        doc += (
            "**Likelihood of success:** The ex parte order violated "
            "MCR 3.310(B)(2)(b) by failing to schedule a hearing within "
            "14 days.\n\n"
            f"**Irreparable harm:** Plaintiff has been separated from "
            f"{child} for **{sep_days} days**. Each additional day of "
            "separation causes compounding, irreversible harm to the "
            "parent-child bond.\n\n"
            "**Balance of hardships:** A stay would merely restore the "
            "status quo ante — parenting time that existed before the "
            "August 8, 2025 order.\n\n"
            "**Public interest:** Michigan public policy favors "
            "maintaining parent-child relationships. MCL 722.27a(1).\n\n"
        )

        doc += "## IV. RELIEF REQUESTED\n\n"
        doc += (
            "WHEREFORE, Plaintiff requests:\n\n"
            "1. A stay of the August 8, 2025 ex parte order pending "
            "resolution of Plaintiff's appeal;\n\n"
            "2. Restoration of Plaintiff's parenting time schedule "
            "during the pendency of the appeal; and\n\n"
            "3. Such other relief as the Court deems just.\n\n"
        )

        doc += self._verification()
        self._log_generation("stay_pending_appeal")
        return doc

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _log_generation(self, motion_type: str) -> None:
        """Record that a motion was generated in the DB log."""
        if not self.db_path.exists():
            return
        try:
            conn = self._connect()
            try:
                conn.execute(
                    "INSERT INTO emergency_motion_log "
                    "(motion_type, case_number) VALUES (?, ?)",
                    (motion_type, CASE_INFO["case_number"]),
                )
                conn.commit()
            finally:
                conn.close()
        except Exception as exc:
            logger.warning("Failed to log motion generation: %s", exc)
