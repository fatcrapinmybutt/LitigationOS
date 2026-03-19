"""
Michigan Statute & Rule Parser — LitigationOS Legal AI
========================================================
Parses MCL, MCR, MRE references into structured objects with:
  - Section hierarchy (chapter, section, subsection)
  - Cross-references to related provisions
  - DB enrichment from mcr_rules.db and litigation_context.db
  - Applicability mapping to case lanes

Usage:
    from legal_ai.statute_parser import StatuteParser
    sp = StatuteParser()
    parsed = sp.parse("MCR 2.003(D)(1)")
    # → StatuteRef(system='MCR', chapter=2, section='003', subsection='(D)(1)', ...)
"""

from __future__ import annotations

import logging
import os
import re
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("legal_ai.statute_parser")

_HERE = Path(__file__).parent
_REPO = _HERE.parent.parent
_DB_PATH = _REPO / "litigation_context.db"
_MCR_DB_PATH = _REPO / "mcr_rules.db"


# ── Data Models ──────────────────────────────────────────────────

@dataclass
class StatuteRef:
    """A parsed statutory or rule reference."""
    raw_text: str
    system: str                  # MCL, MCR, MRE, USC, Const
    full_number: str             # e.g., "722.23" or "2.003"
    chapter: Optional[int] = None
    section: str = ""
    subsection: str = ""
    paragraph: str = ""
    title: str = ""              # descriptive title if known
    topic: str = ""              # subject area
    applicable_lanes: List[str] = field(default_factory=list)
    related_refs: List[str] = field(default_factory=list)
    db_enriched: bool = False
    full_text: str = ""          # actual rule/statute text if available
    confidence: float = 0.0


@dataclass
class StatuteParseResult:
    """Complete parse result for a text."""
    statutes: List[StatuteRef] = field(default_factory=list)
    rules: List[StatuteRef] = field(default_factory=list)
    evidence_rules: List[StatuteRef] = field(default_factory=list)
    federal: List[StatuteRef] = field(default_factory=list)
    constitutional: List[StatuteRef] = field(default_factory=list)
    total_found: int = 0
    parse_time_ms: float = 0.0
    warnings: List[str] = field(default_factory=list)


# ── Michigan Statute Knowledge Base ──────────────────────────────

MCL_TOPICS: Dict[str, Dict[str, Any]] = {
    "722": {"topic": "Child Custody", "lanes": ["A"], "key_sections": {
        "722.23": "Best Interest Factors (12 factors)",
        "722.25": "Grandparent Visitation",
        "722.27": "Custody Modification",
        "722.27a": "Parenting Time",
        "722.31": "Change of Domicile",
    }},
    "552": {"topic": "Divorce/Support", "lanes": ["A"], "key_sections": {
        "552.1": "Contempt Power",
        "552.13": "Friend of the Court",
        "552.14": "Child Support Guidelines",
        "552.17": "Spousal Support",
        "552.511": "Income Withholding",
    }},
    "554": {"topic": "Landlord-Tenant", "lanes": ["B"], "key_sections": {
        "554.601": "Security Deposits",
        "554.631": "Truth in Renting Act",
        "554.139": "Implied Warranty of Habitability",
    }},
    "600": {"topic": "Revised Judicature Act", "lanes": ["A", "B", "E"], "key_sections": {
        "600.2919a": "Conversion (Treble Damages)",
        "600.2950": "Personal Protection Orders",
        "600.5714": "Summary Proceedings (Eviction)",
        "600.5720": "Retaliatory Eviction",
        "600.2801": "Judgment Liens",
        "600.4011": "Garnishment",
    }},
    "750": {"topic": "Penal Code / RICO", "lanes": ["B"], "key_sections": {
        "750.159i": "Michigan RICO",
        "750.159j": "RICO Penalties",
        "750.159g": "Enterprise Definition",
    }},
    "125": {"topic": "Housing / Mobile Homes", "lanes": ["B"], "key_sections": {
        "125.2301": "Mobile Home Commission Act",
        "125.2319": "Mobile Home Resale Rights",
        "125.2331": "Retaliatory Action Prohibited",
        "125.534": "Housing Code Compliance",
    }},
    "445": {"topic": "Consumer Protection", "lanes": ["B"], "key_sections": {
        "445.903": "Consumer Protection Act (MCPA)",
        "445.911": "Treble Damages Under MCPA",
    }},
    "450": {"topic": "Business Entities", "lanes": ["B"], "key_sections": {
        "450.4802": "LLC Dissolution Effects",
        "450.4803": "Winding Up Dissolved LLC",
    }},
}

MCR_TOPICS: Dict[str, Dict[str, Any]] = {
    "2.003": {"topic": "Disqualification of Judge", "lanes": ["E"],
              "related": ["MCR 2.003(C)(1)", "MCR 2.003(D)"]},
    "2.108": {"topic": "Service and Filing", "lanes": ["A", "B"]},
    "2.119": {"topic": "Motion Practice", "lanes": ["A", "B", "E"]},
    "2.612": {"topic": "Relief from Judgment", "lanes": ["A", "E"],
              "related": ["MCR 2.612(C)(1)(a-f)"]},
    "3.206": {"topic": "Domestic Relations", "lanes": ["A", "D"]},
    "3.207": {"topic": "Referees", "lanes": ["A"]},
    "3.303": {"topic": "Habeas Corpus", "lanes": ["A", "E"]},
    "7.204": {"topic": "Filing Appeal", "lanes": ["F"]},
    "7.205": {"topic": "Application for Leave", "lanes": ["F"]},
    "7.212": {"topic": "Briefs", "lanes": ["F"]},
    "7.304": {"topic": "Superintending Control / Mandamus", "lanes": ["E"]},
    "7.311": {"topic": "Emergency Application", "lanes": ["E"]},
    "8.119": {"topic": "Case Records (H - Minors)", "lanes": ["A"]},
}


# ── Parse Patterns ───────────────────────────────────────────────

MCL_PATTERN = re.compile(
    r"MCL\s+(\d+)\.(\d+[a-z]?)(?:\((\d+)\))?(?:\(([a-z])\))?",
    re.IGNORECASE,
)

MCR_PATTERN = re.compile(
    r"MCR\s+(\d+)\.(\d+)(?:\(([A-Z])\))?(?:\((\d+)\))?(?:\(([a-z])\))?",
    re.IGNORECASE,
)

MRE_PATTERN = re.compile(
    r"MRE\s+(\d+)(?:\(([a-z])\))?",
    re.IGNORECASE,
)

USC_PATTERN = re.compile(
    r"(\d+)\s+U\.?S\.?C\.?\s+[§]?\s*(\d+[a-z]?)(?:\(([a-z0-9]+)\))?",
    re.IGNORECASE,
)


# ── Statute Parser Engine ────────────────────────────────────────

class StatuteParser:
    """Parses Michigan and federal statutory references."""

    def __init__(
        self,
        db_path: Optional[str] = None,
        mcr_db_path: Optional[str] = None,
        enrich_from_db: bool = True,
    ):
        self.db_path = db_path or str(_DB_PATH)
        self.mcr_db_path = mcr_db_path or str(_MCR_DB_PATH)
        self._enrich = enrich_from_db

    def parse(self, text: str) -> StatuteParseResult:
        """Parse all statutory references from text."""
        t0 = time.perf_counter()
        result = StatuteParseResult()
        seen: Set[str] = set()

        # Parse MCL references
        for m in MCL_PATTERN.finditer(text):
            ref = self._parse_mcl(m)
            if ref.full_number not in seen:
                seen.add(ref.full_number)
                result.statutes.append(ref)

        # Parse MCR references
        for m in MCR_PATTERN.finditer(text):
            ref = self._parse_mcr(m)
            if ref.full_number not in seen:
                seen.add(ref.full_number)
                result.rules.append(ref)

        # Parse MRE references
        for m in MRE_PATTERN.finditer(text):
            ref = self._parse_mre(m)
            if ref.full_number not in seen:
                seen.add(ref.full_number)
                result.evidence_rules.append(ref)

        # Parse USC references
        for m in USC_PATTERN.finditer(text):
            ref = self._parse_usc(m)
            if ref.full_number not in seen:
                seen.add(ref.full_number)
                result.federal.append(ref)

        # Enrich from databases
        if self._enrich:
            all_refs = (result.statutes + result.rules +
                        result.evidence_rules + result.federal)
            self._enrich_from_db(all_refs)

        result.total_found = (
            len(result.statutes) + len(result.rules) +
            len(result.evidence_rules) + len(result.federal) +
            len(result.constitutional)
        )
        result.parse_time_ms = (time.perf_counter() - t0) * 1000
        return result

    # ── MCL Parser ───────────────────────────────────────────────

    def _parse_mcl(self, m: re.Match) -> StatuteRef:
        """Parse an MCL reference."""
        chapter = m.group(1)
        section = m.group(2)
        subsection = f"({m.group(3)})" if m.group(3) else ""
        paragraph = f"({m.group(4)})" if m.lastindex and m.lastindex >= 4 and m.group(4) else ""
        full_number = f"{chapter}.{section}"

        ref = StatuteRef(
            raw_text=m.group(0),
            system="MCL",
            full_number=full_number,
            chapter=int(chapter),
            section=section,
            subsection=subsection,
            paragraph=paragraph,
            confidence=0.90,
        )

        # Enrich from knowledge base
        topic_info = MCL_TOPICS.get(chapter, {})
        if topic_info:
            ref.topic = topic_info.get("topic", "")
            ref.applicable_lanes = topic_info.get("lanes", [])
            key_sections = topic_info.get("key_sections", {})
            full_key = f"{chapter}.{section}"
            if full_key in key_sections:
                ref.title = key_sections[full_key]
                ref.confidence = 0.95

        return ref

    # ── MCR Parser ───────────────────────────────────────────────

    def _parse_mcr(self, m: re.Match) -> StatuteRef:
        """Parse an MCR reference."""
        chapter = m.group(1)
        section = m.group(2)
        parts = []
        for i in range(3, (m.lastindex or 2) + 1):
            if m.group(i):
                parts.append(f"({m.group(i)})")
        subsection = "".join(parts)
        full_number = f"{chapter}.{section}"

        ref = StatuteRef(
            raw_text=m.group(0),
            system="MCR",
            full_number=full_number,
            chapter=int(chapter),
            section=section,
            subsection=subsection,
            confidence=0.90,
        )

        # Enrich from knowledge base
        topic_info = MCR_TOPICS.get(full_number, {})
        if topic_info:
            ref.topic = topic_info.get("topic", "")
            ref.applicable_lanes = topic_info.get("lanes", [])
            ref.related_refs = topic_info.get("related", [])
            ref.confidence = 0.95

        return ref

    # ── MRE Parser ───────────────────────────────────────────────

    def _parse_mre(self, m: re.Match) -> StatuteRef:
        """Parse an MRE reference."""
        rule_num = m.group(1)
        subsection = f"({m.group(2)})" if m.lastindex and m.lastindex >= 2 and m.group(2) else ""

        return StatuteRef(
            raw_text=m.group(0),
            system="MRE",
            full_number=rule_num,
            chapter=int(rule_num) // 100 if rule_num.isdigit() else None,
            section=rule_num,
            subsection=subsection,
            topic="Michigan Rules of Evidence",
            confidence=0.90,
        )

    # ── USC Parser ───────────────────────────────────────────────

    def _parse_usc(self, m: re.Match) -> StatuteRef:
        """Parse a USC reference."""
        title = m.group(1)
        section = m.group(2)
        subsection = f"({m.group(3)})" if m.lastindex and m.lastindex >= 3 and m.group(3) else ""

        ref = StatuteRef(
            raw_text=m.group(0),
            system="USC",
            full_number=f"{title} USC {section}",
            chapter=int(title),
            section=section,
            subsection=subsection,
            confidence=0.85,
        )

        # Known federal statutes
        if title == "42" and section == "1983":
            ref.title = "Civil Rights Act — Section 1983"
            ref.topic = "Civil Rights"
            ref.applicable_lanes = ["E", "A"]
            ref.confidence = 0.95
        elif title == "42" and section.startswith("360"):
            ref.title = "Fair Housing Act"
            ref.topic = "Housing Discrimination"
            ref.applicable_lanes = ["B"]
            ref.confidence = 0.95
        elif title == "18" and section.startswith("196"):
            ref.title = "Federal RICO"
            ref.topic = "Racketeering"
            ref.applicable_lanes = ["B"]
            ref.confidence = 0.95

        return ref

    # ── DB Enrichment ────────────────────────────────────────────

    def _enrich_from_db(self, refs: List[StatuteRef]) -> None:
        """Enrich parsed references with DB data."""
        # Try mcr_rules.db first
        if os.path.exists(self.mcr_db_path):
            self._enrich_from_mcr_db(refs)

        # Then litigation_context.db
        if os.path.exists(self.db_path):
            self._enrich_from_main_db(refs)

    def _enrich_from_mcr_db(self, refs: List[StatuteRef]) -> None:
        """Enrich MCR references from mcr_rules.db."""
        mcr_refs = [r for r in refs if r.system == "MCR"]
        if not mcr_refs:
            return

        try:
            conn = sqlite3.connect(self.mcr_db_path, timeout=30)
            conn.execute("PRAGMA busy_timeout = 60000")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.row_factory = sqlite3.Row

            # Check available tables
            tables = {row[0] for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()}

            for ref in mcr_refs:
                search = f"{ref.chapter}.{ref.section}" if ref.chapter else ref.full_number

                # Try court_rules table
                if "court_rules" in tables:
                    try:
                        row = conn.execute(
                            "SELECT * FROM court_rules WHERE rule_number LIKE ? LIMIT 1",
                            (f"%{search}%",),
                        ).fetchone()
                        if row:
                            cols = [desc[0] for desc in conn.execute(
                                "PRAGMA table_info(court_rules)"
                            ).fetchall()]
                            row_dict = dict(zip(
                                [c[1] for c in conn.execute("PRAGMA table_info(court_rules)").fetchall()],
                                row,
                            ))
                            ref.title = row_dict.get("title", row_dict.get("rule_title", ref.title))
                            ref.full_text = row_dict.get("full_text", row_dict.get("rule_text", ""))[:500]
                            ref.db_enriched = True
                            ref.confidence = min(1.0, ref.confidence + 0.05)
                    except sqlite3.Error:
                        pass

            conn.close()
        except sqlite3.Error as exc:
            logger.warning("mcr_rules.db enrichment error: %s", exc)

    def _enrich_from_main_db(self, refs: List[StatuteRef]) -> None:
        """Enrich all references from litigation_context.db."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=30)
            conn.execute("PRAGMA busy_timeout = 60000")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA cache_size = -32000")

            tables = {row[0] for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()}

            for ref in refs:
                search = ref.full_number

                # Check authority_library
                if "authority_library" in tables:
                    try:
                        row = conn.execute(
                            "SELECT citation, description FROM authority_library "
                            "WHERE citation LIKE ? LIMIT 1",
                            (f"%{search}%",),
                        ).fetchone()
                        if row:
                            if not ref.title and row[1]:
                                ref.title = row[1][:200]
                            ref.db_enriched = True
                    except sqlite3.Error:
                        pass

            conn.close()
        except sqlite3.Error as exc:
            logger.warning("litigation_context.db enrichment error: %s", exc)

    # ── Batch + Utility ──────────────────────────────────────────

    def parse_batch(
        self, texts: List[str], labels: Optional[List[str]] = None
    ) -> Dict[str, StatuteParseResult]:
        """Parse statutes from multiple texts."""
        results: Dict[str, StatuteParseResult] = {}
        for i, text in enumerate(texts):
            label = labels[i] if labels and i < len(labels) else f"doc_{i}"
            results[label] = self.parse(text)
        return results

    def get_lane_statutes(self, lane: str) -> Dict[str, List[str]]:
        """Get all known statutes applicable to a case lane."""
        result: Dict[str, List[str]] = {"MCL": [], "MCR": [], "USC": []}

        for chapter, info in MCL_TOPICS.items():
            if lane in info.get("lanes", []):
                for section, title in info.get("key_sections", {}).items():
                    result["MCL"].append(f"MCL {section} — {title}")

        for rule, info in MCR_TOPICS.items():
            if lane in info.get("lanes", []):
                result["MCR"].append(f"MCR {rule} — {info.get('topic', '')}")

        return result

    def get_stats(self) -> Dict[str, Any]:
        """Return parser status."""
        return {
            "version": "1.0.0",
            "mcl_chapters_known": len(MCL_TOPICS),
            "mcr_rules_known": len(MCR_TOPICS),
            "db_available": os.path.exists(self.db_path),
            "mcr_db_available": os.path.exists(self.mcr_db_path),
        }
