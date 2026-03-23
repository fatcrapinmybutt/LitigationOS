"""Witness List & Deposition Prep Engine — MCR 2.301 / MCR 2.306 compliant.

Manages witness lists, deposition outlines, and testimony tracking across
all six litigation lanes (A–F) for Pigors v. Watson.

Usage::

    engine = WitnessEngine(db_path="litigation_context.db")
    witnesses = engine.list_witnesses(lane="A")
    outline = engine.generate_depo_outline(witness_id=3)
    doc = engine.generate_witness_list(filing_id="F7")
    linked = engine.get_witness_evidence(witness_id=3)
    ranked = engine.prioritize_witnesses()
"""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

_DEFAULT_DB = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")

# Verified party identity — SINGLE SOURCE OF TRUTH
# Ronald Berry is NON-ATTORNEY. Jennifer Barnes WITHDREW.
# L.D.W. initials only per MCR 8.119(H).
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
    "defendant_attorney": {
        "name": "Jennifer Barnes (P55406)",
        "firm": "Barnes Law Firm PLLC",
        "address": "880 Jefferson St Ste B, Muskegon, MI 49440",
        "status": "WITHDREW",
    },
    "foc": {
        "name": "Pamela Rusco",
        "title": "Friend of the Court",
        "address": "990 Terrace St, Muskegon, MI 49442",
    },
    "judge": {
        "name": "Hon. Jenny L. McNeill",
        "court": "14th Circuit Court, Family Division",
        "address": "990 Terrace St, Muskegon, MI 49442",
    },
    "ronald_berry": {
        "name": "Ronald Berry",
        "relationship": "Emily Watson's boyfriend/domestic partner",
        "note": "NON-ATTORNEY — no bar number, no 'Esq.'",
    },
}

# Lane definitions
LANE_DESCRIPTIONS: dict[str, str] = {
    "A": "Custody (2024-001507-DC, 2023-5907-PP)",
    "B": "Housing — Shady Oaks (2025-002760-CZ)",
    "C": "Convergence (cross-lane)",
    "D": "PPO / Protection Orders",
    "E": "Judicial Misconduct / JTC",
    "F": "Appellate (COA/MSC)",
}

# Filing → lane mapping
FILING_LANES: dict[str, str] = {
    "F1": "A", "F3": "A", "F7": "A",
    "F2": "B",
    "F4": "C",
    "F8": "D",
    "F5": "F", "F9": "F", "F10": "F",
    "F6": "E",
}

# Witness roles
VALID_ROLES = ("fact", "expert", "character", "hostile", "custodian")


class WitnessEngine:
    """Manage witness lists and generate deposition prep materials."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path else _DEFAULT_DB
        self._ensure_table()
        logger.info("WitnessEngine ready  db=%s", self.db_path)

    # ------------------------------------------------------------------
    # Connection helpers
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

    def _ensure_table(self) -> None:
        conn = self._connect()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS witness_list (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    role TEXT,
                    lane TEXT,
                    filing_ids TEXT,
                    relevance_score REAL DEFAULT 0.0,
                    contact_info TEXT,
                    testimony_summary TEXT,
                    depo_questions TEXT,
                    subpoena_needed INTEGER DEFAULT 0,
                    availability TEXT,
                    notes TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_witness_lane
                    ON witness_list(lane)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_witness_role
                    ON witness_list(role)
            """)
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Core CRUD
    # ------------------------------------------------------------------

    def list_witnesses(self, lane: str | None = None) -> list[dict]:
        """Return all witnesses, optionally filtered by lane."""
        conn = self._connect()
        try:
            if lane:
                rows = conn.execute(
                    "SELECT * FROM witness_list WHERE lane = ? "
                    "ORDER BY relevance_score DESC",
                    (lane.upper(),),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM witness_list ORDER BY relevance_score DESC"
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def add_witness(
        self,
        name: str,
        role: str = "fact",
        lane: str = "A",
        relevance_score: float = 5.0,
        filing_ids: str = "",
        contact_info: str = "",
        testimony_summary: str = "",
        depo_questions: str = "[]",
        subpoena_needed: int = 0,
        availability: str = "",
        notes: str = "",
    ) -> int:
        """Add a witness and return the new row id."""
        if role not in VALID_ROLES:
            raise ValueError(
                f"Invalid role '{role}'. Must be one of {VALID_ROLES}"
            )
        lane = lane.upper()
        if lane not in LANE_DESCRIPTIONS:
            raise ValueError(
                f"Invalid lane '{lane}'. Must be one of {list(LANE_DESCRIPTIONS)}"
            )

        conn = self._connect()
        try:
            cur = conn.execute(
                """
                INSERT INTO witness_list
                    (name, role, lane, filing_ids, relevance_score,
                     contact_info, testimony_summary, depo_questions,
                     subpoena_needed, availability, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name, role, lane, filing_ids, relevance_score,
                    contact_info, testimony_summary, depo_questions,
                    subpoena_needed, availability, notes,
                ),
            )
            conn.commit()
            new_id = cur.lastrowid
            logger.info("Added witness id=%s name=%s lane=%s", new_id, name, lane)
            return new_id
        finally:
            conn.close()

    def get_witness(self, witness_id: int) -> dict | None:
        """Fetch a single witness by id."""
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT * FROM witness_list WHERE id = ?", (witness_id,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def update_witness(self, witness_id: int, **fields: Any) -> bool:
        """Update one or more fields on a witness row."""
        allowed = {
            "name", "role", "lane", "filing_ids", "relevance_score",
            "contact_info", "testimony_summary", "depo_questions",
            "subpoena_needed", "availability", "notes",
        }
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return False

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [witness_id]
        conn = self._connect()
        try:
            conn.execute(
                f"UPDATE witness_list SET {set_clause} WHERE id = ?", values
            )
            conn.commit()
            return True
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Evidence linkage
    # ------------------------------------------------------------------

    def get_witness_evidence(self, witness_id: int) -> list[dict]:
        """Find evidence_quotes mentioning a witness by name."""
        witness = self.get_witness(witness_id)
        if not witness:
            return []

        name = witness["name"]
        conn = self._connect()
        try:
            # Check if evidence_quotes table exists
            exists = conn.execute(
                "SELECT count(*) FROM sqlite_master "
                "WHERE type='table' AND name='evidence_quotes'"
            ).fetchone()[0]
            if not exists:
                return []

            # Search by name fragments for better matching
            name_parts = name.split()
            conditions = []
            params = []
            for part in name_parts:
                if len(part) > 2:
                    conditions.append("quote_text LIKE ?")
                    params.append(f"%{part}%")

            if not conditions:
                return []

            where = " AND ".join(conditions)
            rows = conn.execute(
                f"SELECT id, source_file, quote_text, page_number, "
                f"category, lane, relevance_score "
                f"FROM evidence_quotes WHERE {where} "
                f"ORDER BY relevance_score DESC LIMIT 50",
                params,
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_witness_impeachment(self, witness_id: int) -> list[dict]:
        """Find impeachment_matrix entries relevant to a witness."""
        witness = self.get_witness(witness_id)
        if not witness:
            return []

        name = witness["name"]
        conn = self._connect()
        try:
            exists = conn.execute(
                "SELECT count(*) FROM sqlite_master "
                "WHERE type='table' AND name='impeachment_matrix'"
            ).fetchone()[0]
            if not exists:
                return []

            last_name = name.split()[-1] if name.split() else name
            rows = conn.execute(
                "SELECT id, category, evidence_summary, cross_exam_question, "
                "impeachment_value, event_date "
                "FROM impeachment_matrix "
                "WHERE evidence_summary LIKE ? OR quote_text LIKE ? "
                "ORDER BY impeachment_value DESC LIMIT 30",
                (f"%{last_name}%", f"%{last_name}%"),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Prioritization
    # ------------------------------------------------------------------

    def prioritize_witnesses(self, lane: str | None = None) -> list[dict]:
        """Rank witnesses by relevance, impeachment value, and evidence count.

        Returns witnesses sorted by a composite priority score.
        """
        witnesses = self.list_witnesses(lane=lane)
        scored: list[dict] = []

        conn = self._connect()
        try:
            has_eq = conn.execute(
                "SELECT count(*) FROM sqlite_master "
                "WHERE type='table' AND name='evidence_quotes'"
            ).fetchone()[0]
            has_im = conn.execute(
                "SELECT count(*) FROM sqlite_master "
                "WHERE type='table' AND name='impeachment_matrix'"
            ).fetchone()[0]

            for w in witnesses:
                evidence_count = 0
                impeach_score = 0.0
                name_parts = w["name"].split()
                last_name = name_parts[-1] if name_parts else w["name"]

                if has_eq and len(last_name) > 2:
                    evidence_count = conn.execute(
                        "SELECT count(*) FROM evidence_quotes "
                        "WHERE quote_text LIKE ?",
                        (f"%{last_name}%",),
                    ).fetchone()[0]

                if has_im and len(last_name) > 2:
                    row = conn.execute(
                        "SELECT COALESCE(AVG(impeachment_value), 0) "
                        "FROM impeachment_matrix "
                        "WHERE evidence_summary LIKE ? OR quote_text LIKE ?",
                        (f"%{last_name}%", f"%{last_name}%"),
                    ).fetchone()
                    impeach_score = float(row[0]) if row else 0.0

                # Composite: base relevance + evidence density + impeachment
                composite = (
                    (w.get("relevance_score") or 0) * 0.4
                    + min(evidence_count / 10.0, 4.0)
                    + impeach_score * 0.3
                )
                scored.append({
                    **w,
                    "evidence_count": evidence_count,
                    "impeachment_avg": round(impeach_score, 2),
                    "priority_score": round(composite, 2),
                })
        finally:
            conn.close()

        scored.sort(key=lambda x: x["priority_score"], reverse=True)
        return scored

    # ------------------------------------------------------------------
    # Deposition outline generator
    # ------------------------------------------------------------------

    def generate_depo_outline(self, witness_id: int) -> str:
        """Generate a structured deposition outline for a witness.

        Sections:
        1. Background & relationship to parties
        2. Key factual questions
        3. Impeachment setup (if hostile)
        4. Document authentication
        5. Closing
        """
        witness = self.get_witness(witness_id)
        if not witness:
            raise ValueError(f"Witness id={witness_id} not found")

        name = witness["name"]
        role = witness.get("role", "fact")
        lane = witness.get("lane", "A")
        summary = witness.get("testimony_summary", "")
        stored_questions = []
        if witness.get("depo_questions"):
            try:
                stored_questions = json.loads(witness["depo_questions"])
            except (json.JSONDecodeError, TypeError):
                pass

        # Gather impeachment data for hostile witnesses
        impeachment_items = []
        if role in ("hostile", "fact"):
            impeachment_items = self.get_witness_impeachment(witness_id)

        lines: list[str] = []
        lines.append(f"# DEPOSITION OUTLINE — {name}")
        lines.append(f"**Role:** {role}  |  **Lane:** {lane} "
                      f"({LANE_DESCRIPTIONS.get(lane, '')})")
        lines.append(f"**Prepared:** {datetime.now().strftime('%B %d, %Y')}")
        lines.append(f"**Case:** Pigors v. Watson")
        lines.append("")

        # Section 1 — Background
        lines.append("## I. BACKGROUND & RELATIONSHIP TO PARTIES")
        lines.append("")
        bg_questions = self._background_questions(name, role, lane)
        for i, q in enumerate(bg_questions, 1):
            lines.append(f"{i}. {q}")
        lines.append("")

        # Section 2 — Key Factual Questions
        lines.append("## II. KEY FACTUAL QUESTIONS")
        lines.append("")
        if summary:
            lines.append(f"*Testimony focus: {summary}*")
            lines.append("")
        factual = self._factual_questions(name, role, lane, stored_questions)
        for i, q in enumerate(factual, 1):
            lines.append(f"{i}. {q}")
        lines.append("")

        # Section 3 — Impeachment Setup
        if role in ("hostile", "fact") and impeachment_items:
            lines.append("## III. IMPEACHMENT SETUP")
            lines.append("")
            lines.append(
                "*Lock witness into position before revealing contradictions.*"
            )
            lines.append("")
            for i, item in enumerate(impeachment_items[:10], 1):
                cross_q = item.get("cross_exam_question", "")
                ev = item.get("evidence_summary", "")[:120]
                if cross_q:
                    lines.append(f"{i}. {cross_q}")
                    lines.append(f"   — *Source: {ev}*")
                else:
                    lines.append(
                        f"{i}. Regarding: {ev} — establish witness's "
                        f"knowledge and lock into testimony."
                    )
            lines.append("")
        else:
            lines.append("## III. IMPEACHMENT SETUP")
            lines.append("")
            lines.append("*No impeachment items identified at this time.*")
            lines.append("")

        # Section 4 — Document Authentication
        lines.append("## IV. DOCUMENT AUTHENTICATION")
        lines.append("")
        doc_qs = self._document_auth_questions(name, role)
        for i, q in enumerate(doc_qs, 1):
            lines.append(f"{i}. {q}")
        lines.append("")

        # Section 5 — Closing
        lines.append("## V. CLOSING QUESTIONS")
        lines.append("")
        closing = self._closing_questions(name, role)
        for i, q in enumerate(closing, 1):
            lines.append(f"{i}. {q}")
        lines.append("")

        # Notes
        if witness.get("notes"):
            lines.append("---")
            lines.append(f"**Attorney Notes:** {witness['notes']}")
            lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Witness List Filing Document
    # ------------------------------------------------------------------

    def generate_witness_list(self, filing_id: str = "") -> str:
        """Generate a formatted witness list document for court filing.

        If filing_id is provided, filters to witnesses linked to that filing.
        Otherwise returns all witnesses.
        """
        if filing_id:
            lane = FILING_LANES.get(filing_id.upper(), None)
            all_witnesses = self.list_witnesses(lane=lane)
            # Further filter by filing_id in comma-separated list
            witnesses = [
                w for w in all_witnesses
                if not filing_id
                or filing_id.upper() in (w.get("filing_ids") or "").upper().split(",")
                or not w.get("filing_ids")  # include if no filing restriction
            ]
        else:
            witnesses = self.list_witnesses()

        lines: list[str] = []
        lines.append("# WITNESS LIST")
        lines.append(f"**Case:** Pigors v. Watson")
        if filing_id:
            lines.append(f"**Filing:** {filing_id.upper()}")
        lines.append(f"**Date:** {datetime.now().strftime('%B %d, %Y')}")
        lines.append("")
        lines.append("Plaintiff Andrew James Pigors, in propria persona, "
                      "designates the following witnesses:")
        lines.append("")

        for i, w in enumerate(witnesses, 1):
            role_label = (w.get("role") or "fact").capitalize()
            subpoena = " *(subpoena required)*" if w.get("subpoena_needed") else ""
            lines.append(f"### {i}. {w['name']}{subpoena}")
            lines.append(f"- **Role:** {role_label} witness")
            lines.append(
                f"- **Lane:** {w.get('lane', 'A')} "
                f"({LANE_DESCRIPTIONS.get(w.get('lane', 'A'), '')})"
            )
            if w.get("testimony_summary"):
                lines.append(
                    f"- **Expected testimony:** {w['testimony_summary']}"
                )
            if w.get("contact_info"):
                lines.append(f"- **Contact:** {w['contact_info']}")
            if w.get("availability"):
                lines.append(f"- **Availability:** {w['availability']}")
            if w.get("notes"):
                lines.append(f"- **Notes:** {w['notes']}")
            lines.append("")

        lines.append("---")
        lines.append(
            f"*Total witnesses: {len(witnesses)} | "
            f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}*"
        )
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Private: question generators
    # ------------------------------------------------------------------

    @staticmethod
    def _background_questions(
        name: str, role: str, lane: str
    ) -> list[str]:
        """Generate background/foundation questions."""
        qs = [
            f"Please state your full name for the record.",
            f"What is your current address?",
            f"What is your occupation and place of employment?",
            f"How do you know Andrew Pigors?",
            f"How do you know Emily Watson?",
            f"How long have you known the parties?",
        ]
        if role == "expert":
            qs.extend([
                "What are your professional qualifications and credentials?",
                "Have you been retained as an expert in this case?",
                "What materials did you review in forming your opinions?",
            ])
        if role == "hostile":
            qs.extend([
                "Are you aware this deposition is taken under oath?",
                "Do you have any interest in the outcome of this case?",
                "Have you discussed your testimony with anyone before today?",
            ])
        if lane == "A":
            qs.append(
                "What is your relationship with the minor child, "
                "referred to as L.D.W.?"
            )
        if lane == "B":
            qs.append(
                "Are you familiar with the property at "
                "Shady Oaks Mobile Home Community?"
            )
        return qs

    @staticmethod
    def _factual_questions(
        name: str,
        role: str,
        lane: str,
        stored: list[str],
    ) -> list[str]:
        """Generate key factual questions based on lane and role."""
        qs: list[str] = []

        # Include stored custom questions first
        qs.extend(stored)

        # Lane-specific questions
        if lane == "A":
            qs.extend([
                "Describe the parenting arrangement you have observed.",
                "Have you witnessed interactions between Andrew Pigors "
                "and L.D.W.?",
                "Have you observed any interference with parenting time?",
                "Describe any communications from Emily Watson regarding "
                "custody or parenting time.",
                "Are you aware of any periods where Andrew Pigors was "
                "denied access to L.D.W.?",
            ])
        elif lane == "B":
            qs.extend([
                "Describe the condition of the housing at Shady Oaks.",
                "Were you aware of any code violations at the property?",
                "Did you observe any habitability issues?",
                "Were tenants given proper notice of inspections or repairs?",
            ])
        elif lane == "D":
            qs.extend([
                "Describe any incidents you witnessed between the parties.",
                "Were law enforcement officers present during any incident?",
                "Are you familiar with any protective orders in this case?",
                "Have you reviewed communications on AppClose between "
                "the parties?",
            ])
        elif lane == "E":
            qs.extend([
                "Were you present at any hearings before "
                "Judge Jenny L. McNeill?",
                "Describe the judge's conduct during proceedings.",
                "Did you observe any procedural irregularities?",
                "Were any ex parte communications observed or reported?",
            ])
        elif lane == "F":
            qs.extend([
                "Are you familiar with the lower court record in this case?",
                "Were you present during trial court proceedings?",
            ])

        if role == "hostile":
            qs.extend([
                "Is it your testimony under oath that the events "
                "occurred as you described?",
                "Would you be surprised if documentary evidence "
                "contradicted your account?",
            ])
        elif role == "custodian":
            qs.extend([
                "Are you the custodian of records for your organization?",
                "Were these records made at or near the time of the "
                "events recorded?",
                "Are these records kept in the ordinary course of business?",
            ])

        return qs

    @staticmethod
    def _document_auth_questions(name: str, role: str) -> list[str]:
        """Questions to authenticate documents through the witness."""
        qs = [
            "I'm going to show you what has been marked as Exhibit ___. "
            "Do you recognize this document?",
            "Can you identify this document for the record?",
            "Did you author, receive, or participate in creating "
            "this document?",
            "Is this a true and accurate copy of the original?",
            "Were any alterations made to this document since it was "
            "originally created?",
        ]
        if role == "custodian":
            qs.extend([
                "Is this document maintained in the regular course of "
                "your organization's business?",
                "Was this record created at or near the time of the events "
                "it describes?",
            ])
        return qs

    @staticmethod
    def _closing_questions(name: str, role: str) -> list[str]:
        """Standard deposition closing questions."""
        return [
            "Is there anything you would like to add or correct "
            "from your testimony today?",
            "Have you given truthful answers to all questions asked?",
            "Is there any reason you could not testify at trial "
            "consistent with your deposition testimony?",
            "Do you have any documents relevant to this case that "
            "you have not yet produced?",
        ]
