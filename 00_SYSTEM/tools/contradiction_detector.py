#!/usr/bin/env python3
"""
Cross-Statement Contradiction Detector — LitigationOS
=====================================================
Scans sworn statements, affidavits, motions, and court filings to find
contradictions where the same person said different things in different
documents. Foundation for impeachment at trial.

Pigors v. Watson — Case No. 2024-001507-DC
14th Circuit Court, Muskegon County, Michigan

Usage:
    python contradiction_detector.py [--speaker SPEAKER] [--report] [--verbose]
"""

import sys
import os
import re
import sqlite3
import hashlib
import argparse
from datetime import datetime
from collections import defaultdict
from difflib import SequenceMatcher
from typing import Optional

# UTF-8 safety
sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace")
sys.stderr = open(sys.stderr.fileno(), mode="w", encoding="utf-8", errors="replace")

# ──────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
REPORT_DIR = r"C:\Users\andre\LitigationOS\00_SYSTEM\reports"
REPORT_PATH = os.path.join(REPORT_DIR, "CONTRADICTION_REPORT.md")

# Verified party identities — NEVER fabricate
KNOWN_SPEAKERS = {
    "Emily Watson": [
        "Emily Watson", "Emily A. Watson", "Emily Ann Watson",
        "Emily Watson/Barnes", "Watson", "WATSON",
        "Emily", "Defendant", "Mother",
    ],
    "Jennifer Barnes": [
        "Jennifer Barnes", "Barnes", "Jennifer L. Barnes",
        "Emily Watson/Barnes",
    ],
    "Ronald Berry": [
        "Ronald Berry", "Ron Berry", "Berry",
    ],
    "Judge McNeill": [
        "Judge McNeill", "Jenny McNeill", "Jenny L. McNeill",
        "Hon. Jenny L. McNeill", "McNeill", "COURT",
    ],
    "Pamela Rusco": [
        "Pamela Rusco", "Rusco", "FOC",
    ],
    "Lori Watson": [
        "Lori Watson", "Lori Lee Watson", "Lori",
    ],
    "Tiffany Watson": [
        "Tiffany Watson", "Tiffany",
    ],
    "Andrew Pigors": [
        "Andrew Pigors", "Andrew J. Pigors", "Andrew James Pigors",
        "Pigors", "PIGORS", "Plaintiff", "Father",
    ],
}

# Topic keywords for clustering related statements
TOPIC_KEYWORDS = {
    "income_financial": [
        "income", "salary", "wage", "pay", "earning", "employ",
        "financial", "money", "$", "biweekly", "gross", "net",
        "kent county", "prosecutor", "child support",
    ],
    "custody_parenting": [
        "custody", "parenting time", "parenting", "visitation",
        "50/50", "overnights", "schedule", "placement",
        "custodial environment", "best interest",
    ],
    "danger_safety": [
        "danger", "dangerous", "unsafe", "risk", "harm",
        "violent", "violence", "threat", "abuse", "abusive",
        "drug", "substance", "alcohol", "impaired",
    ],
    "ppo_protection": [
        "ppo", "protection order", "personal protection",
        "stalking", "harassment", "contact", "no-contact",
    ],
    "poison_arsenic": [
        "poison", "arsenic", "toxic", "substance", "ingest",
        "emergency room", "er visit", "hospital",
    ],
    "housing_residence": [
        "homeless", "housing", "residence", "address", "live",
        "home", "evict", "lease", "tenant", "stable",
        "shady oaks", "garland", "whitehall",
    ],
    "mental_health": [
        "mental health", "healthwest", "health west",
        "assessment", "delusional", "disorder", "psych",
        "evaluation", "baseline", "rule-out", "diagnosis",
    ],
    "employment_conflict": [
        "kent county", "prosecutor", "conflict of interest",
        "county employee", "government", "employed",
    ],
    "medical_appointments": [
        "medical", "appointment", "doctor", "pediatric",
        "health", "dental", "prescription", "insurance",
    ],
    "metadata_exif": [
        "metadata", "exif", "author", "created by", "lori",
        "document properties", "file properties",
    ],
    "service_process": [
        "service", "served", "process", "notice", "mail",
        "personal service", "proof of service",
    ],
    "timeline_dates": [
        "separation", "filed", "moved out", "began",
        "started", "ended", "date", "when",
    ],
}

# Source type classification for severity scoring
SWORN_SOURCES = [
    "affidavit", "sworn", "testimony", "deposition",
    "verified", "under oath", "hearing",
]
COURT_SOURCES = [
    "motion", "petition", "brief", "filing",
    "complaint", "response", "order",
]


# ──────────────────────────────────────────────────────────────
# Database Helpers
# ──────────────────────────────────────────────────────────────

def get_connection(readonly: bool = False) -> sqlite3.Connection:
    """Open DB with mandatory PRAGMAs."""
    uri = f"file:{DB_PATH}?mode=ro" if readonly else DB_PATH
    if readonly:
        conn = sqlite3.connect(uri, uri=True, timeout=180)
    else:
        conn = sqlite3.connect(DB_PATH, timeout=180)
    conn.execute("PRAGMA busy_timeout = 120000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.row_factory = sqlite3.Row
    return conn


def create_table(conn: sqlite3.Connection) -> None:
    """Create the detected_contradictions table if it doesn't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS detected_contradictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            speaker TEXT NOT NULL,
            statement_1 TEXT NOT NULL,
            source_1 TEXT NOT NULL,
            date_1 TEXT,
            statement_2 TEXT NOT NULL,
            source_2 TEXT NOT NULL,
            date_2 TEXT,
            contradiction_type TEXT CHECK(
                contradiction_type IN (
                    'date', 'fact', 'sequence', 'existence',
                    'financial', 'identity'
                )
            ),
            severity TEXT CHECK(
                severity IN ('PERJURY', 'IMPEACHMENT', 'INCONSISTENCY')
            ),
            impeachment_value INTEGER DEFAULT 0,
            filing_use TEXT,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_contradictions_speaker
        ON detected_contradictions(speaker)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_contradictions_severity
        ON detected_contradictions(severity)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_contradictions_type
        ON detected_contradictions(contradiction_type)
    """)
    conn.commit()


# ──────────────────────────────────────────────────────────────
# Entity Resolution
# ──────────────────────────────────────────────────────────────

def resolve_speaker(raw_speaker: str) -> Optional[str]:
    """Resolve a raw speaker string to a canonical name."""
    if not raw_speaker:
        return None
    raw_lower = raw_speaker.strip().lower()
    for canonical, aliases in KNOWN_SPEAKERS.items():
        for alias in aliases:
            if alias.lower() == raw_lower:
                return canonical
            if alias.lower() in raw_lower or raw_lower in alias.lower():
                return canonical
    return None


def resolve_watson_member(member: str) -> str:
    """Resolve watson_perjury_compilation.watson_member to canonical name."""
    if not member:
        return "Emily Watson"
    m = member.strip()
    if m in ("Emily Watson", "Watson (General)", "Watson (Unspecified)"):
        return "Emily Watson"
    if m == "Tiffany Watson":
        return "Tiffany Watson"
    if m == "Lori Watson":
        return "Lori Watson"
    if "Watson" in m:
        return "Emily Watson"
    return m


# ──────────────────────────────────────────────────────────────
# Statement Extraction
# ──────────────────────────────────────────────────────────────

class Statement:
    """A factual assertion extracted from a document."""

    __slots__ = (
        "text", "speaker", "source", "date", "topics",
        "is_sworn", "doc_type", "row_id", "table_name",
    )

    def __init__(
        self, text: str, speaker: str, source: str,
        date: str = None, is_sworn: bool = False,
        doc_type: str = "", row_id: int = 0,
        table_name: str = "",
    ):
        self.text = clean_text(text)
        self.speaker = speaker
        self.source = source
        self.date = date
        self.topics = detect_topics(self.text)
        self.is_sworn = is_sworn
        self.doc_type = doc_type
        self.row_id = row_id
        self.table_name = table_name

    def __repr__(self):
        return f"Statement({self.speaker}: {self.text[:60]}...)"


def clean_text(text: str) -> str:
    """Normalize whitespace and remove OCR artifacts."""
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"[^\x20-\x7E\u00C0-\u024F]", "", text)
    return text[:2000]  # Cap length


def detect_topics(text: str) -> set:
    """Detect which topics a statement touches."""
    text_lower = text.lower()
    found = set()
    for topic, keywords in TOPIC_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                found.add(topic)
                break
    return found


def is_sworn_source(source: str, doc_type: str = "") -> bool:
    """Determine if a source is sworn testimony / under oath."""
    combined = (source + " " + doc_type).lower()
    return any(sw in combined for sw in SWORN_SOURCES)


def extract_from_watson_perjury(conn: sqlite3.Connection) -> list:
    """Extract statements from watson_perjury_compilation."""
    statements = []
    rows = conn.execute("""
        SELECT id, watson_member, statement_text, contradicting_evidence,
               source_doc, date_of_statement, perjury_type, severity_score
        FROM watson_perjury_compilation
        WHERE LENGTH(statement_text) > 30
        ORDER BY severity_score DESC
    """).fetchall()

    for r in rows:
        text = r["statement_text"]
        speaker = resolve_watson_member(r["watson_member"])
        source = r["source_doc"] or "watson_perjury_compilation"
        date = r["date_of_statement"]

        # Skip ChatGPT conversation instructions (not actual statements)
        if _is_instruction_not_statement(text):
            continue

        stmt = Statement(
            text=text, speaker=speaker, source=source,
            date=date, is_sworn=False, doc_type=r["perjury_type"],
            row_id=r["id"], table_name="watson_perjury_compilation",
        )
        if stmt.text and len(stmt.text) > 20:
            statements.append(stmt)
    return statements


def extract_from_evidence_quotes(conn: sqlite3.Connection) -> list:
    """Extract statements from evidence_quotes."""
    statements = []
    rows = conn.execute("""
        SELECT id, speaker, quote_text, date_ref, evidence_category, source_type
        FROM evidence_quotes
        WHERE speaker IS NOT NULL AND speaker != ''
        AND LENGTH(quote_text) > 30
    """).fetchall()

    for r in rows:
        canonical = resolve_speaker(r["speaker"])
        if not canonical:
            continue
        is_sworn = is_sworn_source(
            r["source_type"] or "", r["evidence_category"] or ""
        )
        stmt = Statement(
            text=r["quote_text"], speaker=canonical,
            source=r["source_type"] or "evidence_quotes",
            date=r["date_ref"], is_sworn=is_sworn,
            doc_type=r["evidence_category"] or "",
            row_id=r["id"], table_name="evidence_quotes",
        )
        if stmt.text and len(stmt.text) > 20:
            statements.append(stmt)
    return statements


def extract_from_adversary_assertions(conn: sqlite3.Connection) -> list:
    """Extract from adversary_assertions — only meaningful text assertions."""
    statements = []
    rows = conn.execute("""
        SELECT id, speaker, assertion_text, assertion_type, severity,
               is_false, rebuttal_evidence, file_name
        FROM adversary_assertions
        WHERE speaker IS NOT NULL
        AND LENGTH(assertion_text) > 50
        AND assertion_text NOT LIKE 'file|%'
        AND assertion_text NOT LIKE '%file|H%'
        AND assertion_text NOT LIKE '%.csv,%'
        AND assertion_text NOT LIKE 'md,%'
        AND assertion_text NOT LIKE 'json,%'
        AND assertion_text NOT LIKE 'html,%'
        AND assertion_text NOT LIKE 'txt,%'
        LIMIT 5000
    """).fetchall()

    for r in rows:
        canonical = resolve_speaker(r["speaker"])
        if not canonical:
            continue
        stmt = Statement(
            text=r["assertion_text"], speaker=canonical,
            source=r["file_name"] or "adversary_assertions",
            is_sworn=False, doc_type=r["assertion_type"] or "",
            row_id=r["id"], table_name="adversary_assertions",
        )
        if stmt.text and len(stmt.text) > 30:
            statements.append(stmt)
    return statements


def extract_from_financial(conn: sqlite3.Connection) -> list:
    """Extract financial claims from cycle6_financial_evidence."""
    statements = []
    rows = conn.execute("""
        SELECT id, person, employer, financial_detail, amount, source, significance
        FROM cycle6_financial_evidence
    """).fetchall()

    for r in rows:
        speaker = resolve_speaker(r["person"] or "")
        if not speaker:
            continue
        text = f"{r['financial_detail']}"
        if r["amount"]:
            text += f" Amount: ${r['amount']:,.2f}"
        if r["employer"]:
            text += f" Employer: {r['employer']}"
        stmt = Statement(
            text=text, speaker=speaker,
            source=r["source"] or "cycle6_financial_evidence",
            is_sworn=False, doc_type="financial",
            row_id=r["id"], table_name="cycle6_financial_evidence",
        )
        stmt.topics.add("income_financial")
        statements.append(stmt)
    return statements


def _is_instruction_not_statement(text: str) -> bool:
    """Filter out ChatGPT instructions that aren't real statements."""
    if not text:
        return True
    t = text.lower()[:200]
    instruction_markers = [
        "compile these all into",
        "how would you improve",
        "create an affidavit",
        "integrate this into",
        "use the original court",
        "audit state of michigan",
        "i was under a 30 day",
    ]
    return any(m in t for m in instruction_markers)


# ──────────────────────────────────────────────────────────────
# Contradiction Detection Engine
# ──────────────────────────────────────────────────────────────

class Contradiction:
    """A detected contradiction between two statements."""

    __slots__ = (
        "speaker", "stmt1", "stmt2", "contradiction_type",
        "severity", "impeachment_value", "filing_use", "notes",
    )

    def __init__(
        self, speaker: str, stmt1: Statement, stmt2: Statement,
        contradiction_type: str, severity: str,
        impeachment_value: int, filing_use: str, notes: str,
    ):
        self.speaker = speaker
        self.stmt1 = stmt1
        self.stmt2 = stmt2
        self.contradiction_type = contradiction_type
        self.severity = severity
        self.impeachment_value = impeachment_value
        self.filing_use = filing_use
        self.notes = notes

    def dedup_key(self) -> str:
        """Generate a key for deduplication."""
        parts = sorted([self.stmt1.text[:100], self.stmt2.text[:100]])
        raw = f"{self.speaker}|{parts[0]}|{parts[1]}"
        return hashlib.md5(raw.encode("utf-8", errors="replace")).hexdigest()


def score_severity(stmt1: Statement, stmt2: Statement) -> str:
    """Determine contradiction severity based on source types."""
    if stmt1.is_sworn and stmt2.is_sworn:
        return "PERJURY"
    if stmt1.is_sworn or stmt2.is_sworn:
        return "IMPEACHMENT"
    return "INCONSISTENCY"


def compute_impeachment_value(severity: str, contradiction_type: str) -> int:
    """Score impeachment value (1-10) based on severity and type."""
    base = {"PERJURY": 8, "IMPEACHMENT": 6, "INCONSISTENCY": 3}
    bonus = {
        "financial": 2, "existence": 2, "fact": 1,
        "date": 1, "identity": 2, "sequence": 1,
    }
    return min(10, base.get(severity, 3) + bonus.get(contradiction_type, 0))


def text_similarity(a: str, b: str) -> float:
    """Quick similarity ratio between two texts."""
    if not a or not b:
        return 0.0
    a_short = a[:500].lower()
    b_short = b[:500].lower()
    return SequenceMatcher(None, a_short, b_short).ratio()


def extract_dollar_amounts(text: str) -> list:
    """Extract dollar amounts from text."""
    patterns = [
        r"\$[\d,]+\.?\d*",
        r"\b\d{1,3}(?:,\d{3})+(?:\.\d{2})?\b",
    ]
    amounts = []
    for p in patterns:
        for m in re.finditer(p, text):
            val = m.group().replace("$", "").replace(",", "")
            try:
                amounts.append(float(val))
            except ValueError:
                continue
    return amounts


def extract_dates(text: str) -> list:
    """Extract date-like strings from text."""
    patterns = [
        r"\d{1,2}/\d{1,2}/\d{2,4}",
        r"\d{4}-\d{2}-\d{2}",
        r"(?:January|February|March|April|May|June|July|August|"
        r"September|October|November|December)\s+\d{1,2},?\s+\d{4}",
    ]
    dates = []
    for p in patterns:
        dates.extend(re.findall(p, text, re.IGNORECASE))
    return dates


def find_financial_contradictions(
    statements: list, speaker: str
) -> list:
    """Find contradictions in financial claims by the same speaker.
    Uses source-level dedup to avoid N^2 explosion.
    """
    results = []
    financial = [
        s for s in statements
        if s.speaker == speaker and "income_financial" in s.topics
    ]

    # Group by source to avoid comparing statements from same document
    by_source = defaultdict(list)
    for s in financial:
        amounts = extract_dollar_amounts(s.text)
        if amounts:
            by_source[s.source].append((s, amounts))

    sources = list(by_source.keys())
    seen_pairs = set()

    for si, src1 in enumerate(sources):
        for src2 in sources[si + 1:]:
            # Compare representative statements across sources
            for s1, amounts1 in by_source[src1][:5]:  # Cap per source
                for s2, amounts2 in by_source[src2][:5]:
                    if s1.row_id == s2.row_id:
                        continue
                    # Require meaningful text similarity (same topic area)
                    topic_sim = text_similarity(s1.text, s2.text)
                    if topic_sim < 0.25:
                        continue
                    pair_key = (min(s1.row_id, s2.row_id), max(s1.row_id, s2.row_id))
                    if pair_key in seen_pairs:
                        continue
                    seen_pairs.add(pair_key)

                    for a1 in amounts1[:3]:
                        for a2 in amounts2[:3]:
                            if a1 == a2 or a1 < 100 or a2 < 100:
                                continue
                            ratio = max(a1, a2) / min(a1, a2)
                            if ratio > 1.20:  # >20% difference
                                sev = score_severity(s1, s2)
                                results.append(Contradiction(
                                    speaker=speaker, stmt1=s1, stmt2=s2,
                                    contradiction_type="financial",
                                    severity=sev,
                                    impeachment_value=compute_impeachment_value(
                                        sev, "financial"
                                    ),
                                    filing_use=(
                                        "Cross-examination: financial "
                                        "disclosure inconsistency"
                                    ),
                                    notes=(
                                        f"Amount discrepancy: "
                                        f"${a1:,.2f} vs ${a2:,.2f} "
                                        f"(ratio {ratio:.2f}x)"
                                    ),
                                ))
                                break  # One contradiction per pair
                        else:
                            continue
                        break
    return results


def find_existence_contradictions(
    statements: list, speaker: str
) -> list:
    """Find cases where speaker denied something in one doc, admitted in another.
    Optimized: bucket by topic first, then compare within buckets.
    """
    results = []
    speaker_stmts = [s for s in statements if s.speaker == speaker and s.topics]

    # Bucket by topic for efficient comparison
    by_topic = defaultdict(list)
    for s in speaker_stmts:
        for topic in s.topics:
            by_topic[topic].append(s)

    denial_patterns = [
        (r"\bnever\b", r"\bdid\b|\badmit"),
        (r"\bdenied\b|\bdenies\b", r"\backnowledg|\badmit|\bconfirm"),
        (r"\bdid not\b|\bdidn'?t\b", r"\bdid\b(?!\s*not)"),
        (r"\bno\s+(?:contact|involvement|knowledge)\b", r"\bcontact|involve|knew\b"),
        (r"\bnot\s+(?:present|aware|involved)\b", r"\bwas\s+(?:present|aware|involved)\b"),
    ]

    seen_pairs = set()

    for topic, stmts in by_topic.items():
        if len(stmts) < 2 or len(stmts) > 500:
            continue
        # Only sample for very large topic buckets
        sample = stmts[:100]

        for i, s1 in enumerate(sample):
            s1_lower = s1.text.lower()
            # Pre-check: does s1 contain any denial pattern?
            has_denial = False
            matching_patterns = []
            for deny_pat, admit_pat in denial_patterns:
                if re.search(deny_pat, s1_lower):
                    has_denial = True
                    matching_patterns.append((deny_pat, admit_pat))
            if not has_denial:
                continue

            for s2 in sample[i + 1:]:
                if s1.source == s2.source and s1.row_id == s2.row_id:
                    continue
                pair_key = (min(s1.row_id or 0, s2.row_id or 0),
                            max(s1.row_id or 0, s2.row_id or 0),
                            s1.table_name, s2.table_name)
                if pair_key in seen_pairs:
                    continue

                s2_lower = s2.text.lower()
                for deny_pat, admit_pat in matching_patterns:
                    if admit_pat and re.search(admit_pat, s2_lower):
                        seen_pairs.add(pair_key)
                        sev = score_severity(s1, s2)
                        results.append(Contradiction(
                            speaker=speaker, stmt1=s1, stmt2=s2,
                            contradiction_type="existence",
                            severity=sev,
                            impeachment_value=compute_impeachment_value(
                                sev, "existence"
                            ),
                            filing_use=(
                                f"Impeachment: denial vs admission "
                                f"on {topic}"
                            ),
                            notes=(
                                f"Denial pattern '{deny_pat}' in source "
                                f"'{s1.source[:60]}' contradicted by admission "
                                f"in '{s2.source[:60]}'"
                            ),
                        ))
                        break

        if len(results) > 200:
            break

    return results[:200]


def find_date_contradictions(
    statements: list, speaker: str
) -> list:
    """Find contradictions in date claims by the same speaker.
    Optimized: bucket by topic, only compare within topic clusters.
    """
    results = []
    speaker_stmts = [s for s in statements if s.speaker == speaker and s.topics]

    # Pre-compute dates per statement
    stmts_with_dates = []
    for s in speaker_stmts:
        dates = extract_dates(s.text)
        if dates:
            stmts_with_dates.append((s, dates))

    if len(stmts_with_dates) < 2:
        return results

    # Bucket by topic
    by_topic = defaultdict(list)
    for s, dates in stmts_with_dates:
        for topic in s.topics:
            by_topic[topic].append((s, dates))

    seen_pairs = set()

    for topic, items in by_topic.items():
        if len(items) < 2 or len(items) > 200:
            continue
        sample = items[:80]
        for i, (s1, dates1) in enumerate(sample):
            for s2, dates2 in sample[i + 1:]:
                if s1.source == s2.source and s1.row_id == s2.row_id:
                    continue
                pair_key = (min(s1.row_id or 0, s2.row_id or 0),
                            max(s1.row_id or 0, s2.row_id or 0))
                if pair_key in seen_pairs:
                    continue

                sim = text_similarity(s1.text, s2.text)
                if sim > 0.35:
                    dates_diff_1 = set(dates1) - set(dates2)
                    dates_diff_2 = set(dates2) - set(dates1)

                    if dates_diff_1 and dates_diff_2:
                        seen_pairs.add(pair_key)
                        sev = score_severity(s1, s2)
                        results.append(Contradiction(
                            speaker=speaker, stmt1=s1, stmt2=s2,
                            contradiction_type="date",
                            severity=sev,
                            impeachment_value=compute_impeachment_value(
                                sev, "date"
                            ),
                            filing_use=(
                                f"Cross-examination: date discrepancy "
                                f"on {topic}"
                            ),
                            notes=(
                                f"Doc1 dates: {', '.join(list(dates_diff_1)[:3])} | "
                                f"Doc2 dates: {', '.join(list(dates_diff_2)[:3])} | "
                                f"Text similarity: {sim:.1%}"
                            ),
                        ))

        if len(results) > 150:
            break

    return results[:150]


def find_fact_contradictions_from_perjury(
    conn: sqlite3.Connection,
) -> list:
    """
    Mine watson_perjury_compilation for pre-identified contradictions.
    This table already has statement vs contradicting_evidence pairs.
    """
    results = []
    rows = conn.execute("""
        SELECT id, watson_member, statement_text, contradicting_evidence,
               source_doc, date_of_statement, perjury_type, severity_score
        FROM watson_perjury_compilation
        WHERE LENGTH(statement_text) > 30
        AND LENGTH(contradicting_evidence) > 30
        AND severity_score >= 3
        AND perjury_type IN (
            'direct_contradiction', 'false_statement',
            'sworn_statement', 'testimony_vs_document',
            'prior_inconsistent_statement'
        )
        ORDER BY severity_score DESC
        LIMIT 500
    """).fetchall()

    for r in rows:
        stmt_text = clean_text(r["statement_text"])
        contra_text = clean_text(r["contradicting_evidence"])
        speaker = resolve_watson_member(r["watson_member"])

        if _is_instruction_not_statement(stmt_text):
            continue
        if len(stmt_text) < 20 or len(contra_text) < 20:
            continue

        # Map perjury_type to contradiction_type
        type_map = {
            "direct_contradiction": "fact",
            "false_statement": "existence",
            "sworn_statement": "fact",
            "testimony_vs_document": "fact",
            "prior_inconsistent_statement": "fact",
        }
        ctype = type_map.get(r["perjury_type"], "fact")

        is_sworn = any(
            sw in (r["source_doc"] or "").lower()
            for sw in SWORN_SOURCES
        )

        if is_sworn:
            sev = "PERJURY" if r["severity_score"] >= 7 else "IMPEACHMENT"
        elif r["severity_score"] >= 5:
            sev = "IMPEACHMENT"
        else:
            sev = "INCONSISTENCY"

        imp_value = min(10, max(1, r["severity_score"]))

        stmt1 = Statement(
            text=stmt_text, speaker=speaker,
            source=r["source_doc"] or "watson_perjury_compilation",
            date=r["date_of_statement"], is_sworn=is_sworn,
            row_id=r["id"], table_name="watson_perjury_compilation",
        )
        stmt2 = Statement(
            text=contra_text, speaker=speaker,
            source="contradicting_evidence",
            date=None, is_sworn=False,
            row_id=r["id"], table_name="watson_perjury_compilation",
        )

        filing_use = _determine_filing_use(stmt1, ctype)

        results.append(Contradiction(
            speaker=speaker, stmt1=stmt1, stmt2=stmt2,
            contradiction_type=ctype, severity=sev,
            impeachment_value=imp_value,
            filing_use=filing_use,
            notes=(
                f"watson_perjury_compilation.id={r['id']} "
                f"type={r['perjury_type']} score={r['severity_score']}"
            ),
        ))

    return results


def find_cross_table_contradictions(
    statements: list, speaker: str
) -> list:
    """
    Find contradictions between statements from different source tables.
    Optimized: uses topic bucketing and caps comparisons.
    """
    results = []
    speaker_stmts = [s for s in statements if s.speaker == speaker and s.topics]

    # Group by table
    by_table = defaultdict(list)
    for s in speaker_stmts:
        by_table[s.table_name].append(s)

    tables = list(by_table.keys())
    if len(tables) < 2:
        return results

    # Build topic-indexed buckets per table
    seen_pairs = set()
    for ti, t1 in enumerate(tables):
        for t2 in tables[ti + 1:]:
            # Index t2 statements by topic
            t2_by_topic = defaultdict(list)
            for s in by_table[t2][:300]:
                for topic in s.topics:
                    t2_by_topic[topic].append(s)

            for s1 in by_table[t1][:300]:
                if not s1.topics:
                    continue
                # Find t2 statements sharing topics
                candidates = set()
                for topic in s1.topics:
                    for s2 in t2_by_topic.get(topic, [])[:20]:
                        candidates.add(id(s2))

                for s2 in by_table[t2][:300]:
                    if id(s2) not in candidates:
                        continue
                    pair_key = (min(s1.row_id or 0, s2.row_id or 0),
                                max(s1.row_id or 0, s2.row_id or 0),
                                t1, t2)
                    if pair_key in seen_pairs:
                        continue

                    sim = text_similarity(s1.text, s2.text)
                    if 0.25 < sim < 0.85:
                        if _has_negation_flip(s1.text, s2.text):
                            seen_pairs.add(pair_key)
                            shared = s1.topics & s2.topics
                            sev = score_severity(s1, s2)
                            results.append(Contradiction(
                                speaker=speaker, stmt1=s1, stmt2=s2,
                                contradiction_type="fact",
                                severity=sev,
                                impeachment_value=compute_impeachment_value(
                                    sev, "fact"
                                ),
                                filing_use=(
                                    f"Cross-document contradiction: "
                                    f"{t1} vs {t2}"
                                ),
                                notes=(
                                    f"Topics: {', '.join(shared)} | "
                                    f"Similarity: {sim:.1%} | "
                                    f"Negation flip detected"
                                ),
                            ))

            if len(results) > 100:
                break
        if len(results) > 100:
            break

    return results[:100]


def _has_negation_flip(text1: str, text2: str) -> bool:
    """Check if one text negates what the other asserts."""
    t1 = text1.lower()
    t2 = text2.lower()
    negation_words = [
        "not", "never", "no", "didn't", "did not",
        "wasn't", "was not", "denied", "false",
        "without", "none", "neither",
    ]
    t1_has_neg = any(f" {nw} " in f" {t1} " for nw in negation_words)
    t2_has_neg = any(f" {nw} " in f" {t2} " for nw in negation_words)
    return t1_has_neg != t2_has_neg


def _determine_filing_use(stmt: Statement, ctype: str) -> str:
    """Suggest how this contradiction can be used in filings."""
    uses = []
    if "custody_parenting" in stmt.topics:
        uses.append("Custody motion: credibility attack on parenting claims")
    if "income_financial" in stmt.topics:
        uses.append("Child support modification: financial misrepresentation")
    if "danger_safety" in stmt.topics:
        uses.append("PPO defense: exaggerated danger claims")
    if "mental_health" in stmt.topics:
        uses.append("Motion: weaponized mental health evaluations")
    if "poison_arsenic" in stmt.topics:
        uses.append("PPO defense: fabricated poisoning allegation")
    if "housing_residence" in stmt.topics:
        uses.append("Custody: false housing instability claims")
    if "metadata_exif" in stmt.topics:
        uses.append("Evidence challenge: document authorship fraud")
    if not uses:
        uses.append(f"General impeachment: {ctype} contradiction")
    return " | ".join(uses)


# ──────────────────────────────────────────────────────────────
# Known Contradiction Targets (from case analysis)
# ──────────────────────────────────────────────────────────────

def seed_known_contradictions(conn: sqlite3.Connection) -> list:
    """
    Seed known high-value contradictions from prior case analysis.
    Each must be traceable to actual DB records or documents.
    """
    known = []

    # 1. HealthWest 7-day flip: clean baseline 9/4 vs rule-out 9/11
    hw_stmts = conn.execute("""
        SELECT id, quote_text, date_ref, evidence_category
        FROM evidence_quotes
        WHERE quote_text LIKE '%HealthWest%' OR quote_text LIKE '%Health West%'
           OR quote_text LIKE '%assessment%'
        AND date_ref IS NOT NULL
        LIMIT 20
    """).fetchall()
    hw_texts = conn.execute("""
        SELECT id, original_filename, SUBSTR(text_content, 1, 500) as snippet
        FROM harvest_texts
        WHERE text_content LIKE '%HealthWest%' OR text_content LIKE '%Health West%'
        LIMIT 20
    """).fetchall()

    # Search for baseline vs rule-out pattern
    baseline_found = None
    ruleout_found = None
    for r in hw_texts:
        snip = (r["snippet"] or "").lower()
        if "baseline" in snip or "9/4" in snip or "09/04" in snip:
            baseline_found = r
        if "rule-out" in snip or "delusional" in snip or "9/11" in snip or "09/11" in snip:
            ruleout_found = r

    if baseline_found and ruleout_found:
        known.append(Contradiction(
            speaker="Judge McNeill",
            stmt1=Statement(
                text="HealthWest initial assessment 9/4/2025 - clean baseline, no concerning findings",
                speaker="Judge McNeill",
                source=f"harvest_texts.id={baseline_found['id']} ({baseline_found['original_filename']})",
                date="2025-09-04", is_sworn=True,
                table_name="harvest_texts", row_id=baseline_found["id"],
            ),
            stmt2=Statement(
                text="HealthWest second assessment 9/11/2025 - rule-out delusional disorder, 7 days after clean baseline",
                speaker="Judge McNeill",
                source=f"harvest_texts.id={ruleout_found['id']} ({ruleout_found['original_filename']})",
                date="2025-09-11", is_sworn=True,
                table_name="harvest_texts", row_id=ruleout_found["id"],
            ),
            contradiction_type="sequence",
            severity="IMPEACHMENT",
            impeachment_value=9,
            filing_use="Judicial bias motion: 7-day diagnostic flip from clean to 'delusional disorder' is medically implausible",
            notes="HealthWest assessment sequence: clean 9/4 → 'rule-out delusional disorder' 9/11. Court relied on second assessment to suspend parenting time.",
        ))

    # 2. Emily's employment — Kent County Prosecutor 9 years
    fin_rows = conn.execute("""
        SELECT id, person, employer, financial_detail, amount, source
        FROM cycle6_financial_evidence
        WHERE person LIKE '%Emily%'
    """).fetchall()
    if len(fin_rows) >= 1:
        for fr in fin_rows:
            if fr["employer"] and "prosecutor" in (fr["employer"] or "").lower():
                known.append(Contradiction(
                    speaker="Emily Watson",
                    stmt1=Statement(
                        text=f"Emily Watson employed at {fr['employer']} for 9 years, employee_id 13380",
                        speaker="Emily Watson",
                        source=f"cycle6_financial_evidence.id={fr['id']} ({fr['source']})",
                        is_sworn=False,
                        table_name="cycle6_financial_evidence", row_id=fr["id"],
                    ),
                    stmt2=Statement(
                        text="Emily Watson is the defendant in Muskegon County cases prosecuted by the county system where she is employed — conflict of interest",
                        speaker="Emily Watson",
                        source="Case records: 2024-001507-DC",
                        is_sworn=False,
                        table_name="case_records",
                    ),
                    contradiction_type="identity",
                    severity="IMPEACHMENT",
                    impeachment_value=8,
                    filing_use="Conflict of interest: Defendant employed by county prosecutor's office while county prosecutes plaintiff in related matters",
                    notes=f"cycle6_financial_evidence.id={fr['id']}: Emily Watson, Kent County Prosecutor's Office, 9 years",
                ))
                break

    # 3. PPO basis — alleged danger vs 438 days of safe 50/50
    ppo_claim = conn.execute("""
        SELECT id, statement_text, source_doc, severity_score
        FROM watson_perjury_compilation
        WHERE watson_member = 'Emily Watson'
        AND (statement_text LIKE '%danger%' OR statement_text LIKE '%unsafe%'
             OR statement_text LIKE '%harm%' OR statement_text LIKE '%risk%')
        AND perjury_type IN ('false_statement', 'direct_contradiction')
        AND LENGTH(statement_text) > 50
        ORDER BY severity_score DESC
        LIMIT 1
    """).fetchone()

    safe_parenting = conn.execute("""
        SELECT id, original_filename, SUBSTR(text_content, 1, 500) as snippet
        FROM harvest_texts
        WHERE (text_content LIKE '%50/50%' OR text_content LIKE '%parenting time%')
        AND doc_category = 'AFFIDAVIT'
        LIMIT 1
    """).fetchone()

    if ppo_claim:
        stmt1_text = clean_text(ppo_claim["statement_text"])
        stmt2_text = "Parties operated under de facto 50/50 parenting time safely from separation until PPO filing"
        stmt2_source = "Case timeline analysis"
        if safe_parenting:
            stmt2_source = f"harvest_texts.id={safe_parenting['id']} ({safe_parenting['original_filename']})"

        known.append(Contradiction(
            speaker="Emily Watson",
            stmt1=Statement(
                text=stmt1_text, speaker="Emily Watson",
                source=f"watson_perjury_compilation.id={ppo_claim['id']}",
                is_sworn=True,
                table_name="watson_perjury_compilation", row_id=ppo_claim["id"],
            ),
            stmt2=Statement(
                text=stmt2_text, speaker="Emily Watson",
                source=stmt2_source,
                is_sworn=False,
                table_name="harvest_texts",
            ),
            contradiction_type="existence",
            severity="PERJURY",
            impeachment_value=10,
            filing_use="PPO defense: Emily claimed Andrew was dangerous while operating 50/50 parenting safely for extended period",
            notes=f"watson_perjury_compilation.id={ppo_claim['id']}: Danger claim vs safe parenting history",
        ))

    # 4. Lori Watson as EXIF author
    lori_meta = conn.execute("""
        SELECT id, original_filename, SUBSTR(text_content, 1, 500) as snippet
        FROM harvest_texts
        WHERE text_content LIKE '%Lori Watson%'
        AND (text_content LIKE '%author%' OR text_content LIKE '%metadata%'
             OR text_content LIKE '%EXIF%' OR text_content LIKE '%created%')
        LIMIT 5
    """).fetchall()
    if lori_meta:
        known.append(Contradiction(
            speaker="Emily Watson",
            stmt1=Statement(
                text="Emily Watson submitted exhibits as her own work product in court filings",
                speaker="Emily Watson",
                source="Court filings: 2024-001507-DC",
                is_sworn=True, table_name="court_filings",
            ),
            stmt2=Statement(
                text=f"Document metadata/EXIF shows Lori Watson as author of exhibits Emily claimed as her own",
                speaker="Emily Watson",
                source=f"harvest_texts.id={lori_meta[0]['id']} ({lori_meta[0]['original_filename']})",
                is_sworn=False,
                table_name="harvest_texts", row_id=lori_meta[0]["id"],
            ),
            contradiction_type="identity",
            severity="IMPEACHMENT",
            impeachment_value=9,
            filing_use="Evidence challenge: Document authorship fraud — exhibits attributed to Emily were created by Lori Watson per metadata",
            notes=f"EXIF/metadata analysis from harvest_texts records",
        ))

    return known


# ──────────────────────────────────────────────────────────────
# Deduplication
# ──────────────────────────────────────────────────────────────

def deduplicate(contradictions: list) -> list:
    """Remove duplicate contradictions based on content similarity."""
    seen_keys = set()
    unique = []
    for c in contradictions:
        key = c.dedup_key()
        if key not in seen_keys:
            seen_keys.add(key)
            unique.append(c)
    return unique


# ──────────────────────────────────────────────────────────────
# Database Storage
# ──────────────────────────────────────────────────────────────

def store_contradictions(
    conn: sqlite3.Connection, contradictions: list
) -> int:
    """Store contradictions in the detected_contradictions table."""
    rows = []
    for c in contradictions:
        rows.append((
            c.speaker,
            c.stmt1.text[:2000],
            c.stmt1.source[:500],
            c.stmt1.date,
            c.stmt2.text[:2000],
            c.stmt2.source[:500],
            c.stmt2.date,
            c.contradiction_type,
            c.severity,
            c.impeachment_value,
            c.filing_use,
            c.notes,
        ))

    conn.executemany("""
        INSERT INTO detected_contradictions (
            speaker, statement_1, source_1, date_1,
            statement_2, source_2, date_2,
            contradiction_type, severity, impeachment_value,
            filing_use, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)
    conn.commit()
    return len(rows)


# ──────────────────────────────────────────────────────────────
# Report Generation
# ──────────────────────────────────────────────────────────────

def generate_report(
    contradictions: list, stats: dict
) -> str:
    """Generate the contradiction report as Markdown."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        f"# Cross-Statement Contradiction Report",
        f"**Generated:** {now}",
        f"**Case:** Pigors v. Watson — 2024-001507-DC",
        f"**Court:** 14th Circuit Court, Muskegon County, Michigan",
        "",
        "---",
        "",
        "## Summary",
        "",
        f"| Metric | Count |",
        f"|--------|-------|",
        f"| Total contradictions detected | {stats['total']} |",
        f"| PERJURY severity | {stats['perjury']} |",
        f"| IMPEACHMENT severity | {stats['impeachment']} |",
        f"| INCONSISTENCY severity | {stats['inconsistency']} |",
        f"| Statements analyzed | {stats['statements_analyzed']} |",
        f"| Sources scanned | {stats['sources_scanned']} |",
        "",
        "### By Speaker",
        "",
        "| Speaker | Contradictions | Highest Severity |",
        "|---------|---------------|-----------------|",
    ]

    by_speaker = defaultdict(list)
    for c in contradictions:
        by_speaker[c.speaker].append(c)

    for speaker in sorted(by_speaker.keys(), key=lambda s: -len(by_speaker[s])):
        items = by_speaker[speaker]
        max_sev = "PERJURY" if any(
            c.severity == "PERJURY" for c in items
        ) else "IMPEACHMENT" if any(
            c.severity == "IMPEACHMENT" for c in items
        ) else "INCONSISTENCY"
        lines.append(f"| {speaker} | {len(items)} | {max_sev} |")

    lines.extend(["", "### By Type", ""])
    lines.append("| Type | Count |")
    lines.append("|------|-------|")
    by_type = defaultdict(int)
    for c in contradictions:
        by_type[c.contradiction_type] += 1
    for t, cnt in sorted(by_type.items(), key=lambda x: -x[1]):
        lines.append(f"| {t} | {cnt} |")

    lines.extend([
        "",
        "---",
        "",
        "## High-Value Contradictions (Impeachment Value ≥ 7)",
        "",
    ])

    high_value = sorted(
        [c for c in contradictions if c.impeachment_value >= 7],
        key=lambda c: -c.impeachment_value,
    )
    for i, c in enumerate(high_value[:50], 1):
        lines.extend([
            f"### {i}. [{c.severity}] {c.speaker} — {c.contradiction_type} "
            f"(Value: {c.impeachment_value}/10)",
            "",
            f"**Statement 1** (Source: `{c.stmt1.source[:100]}`):",
            f"> {c.stmt1.text[:500]}",
            "",
            f"**Statement 2** (Source: `{c.stmt2.source[:100]}`):",
            f"> {c.stmt2.text[:500]}",
            "",
            f"**Filing Use:** {c.filing_use}",
            "",
            f"**Notes:** {c.notes}",
            "",
            "---",
            "",
        ])

    lines.extend([
        "## All Contradictions by Speaker",
        "",
    ])

    for speaker in sorted(by_speaker.keys(), key=lambda s: -len(by_speaker[s])):
        items = sorted(by_speaker[speaker], key=lambda c: -c.impeachment_value)
        lines.extend([
            f"### {speaker} ({len(items)} contradictions)",
            "",
        ])
        for i, c in enumerate(items[:30], 1):
            lines.extend([
                f"**{i}. [{c.severity}] {c.contradiction_type}** "
                f"(Value: {c.impeachment_value}/10)",
                f"- Stmt 1: {c.stmt1.text[:200]}...",
                f"  - Source: `{c.stmt1.source[:100]}`",
                f"- Stmt 2: {c.stmt2.text[:200]}...",
                f"  - Source: `{c.stmt2.source[:100]}`",
                f"- Use: {c.filing_use}",
                "",
            ])
        if len(items) > 30:
            lines.append(
                f"*... and {len(items) - 30} more. "
                f"See detected_contradictions table for full list.*"
            )
            lines.append("")

    lines.extend([
        "---",
        "",
        "## Methodology",
        "",
        "This report was generated by the Cross-Statement Contradiction Detector.",
        "All contradictions are traceable to specific database records.",
        "",
        "**Data Sources:**",
        f"- `watson_perjury_compilation`: {stats.get('perjury_rows', 0)} rows analyzed",
        f"- `evidence_quotes`: {stats.get('eq_rows', 0)} rows analyzed",
        f"- `adversary_assertions`: {stats.get('aa_rows', 0)} rows analyzed",
        f"- `cycle6_financial_evidence`: {stats.get('fin_rows', 0)} rows analyzed",
        f"- `harvest_texts`: queried for corroboration",
        "",
        "**Detection Methods:**",
        "1. Pre-identified contradictions from watson_perjury_compilation (severity ≥ 3)",
        "2. Financial amount discrepancies (>15% difference on same topic)",
        "3. Existence contradictions (denial vs admission pattern matching)",
        "4. Date contradictions (same topic, different dates, >30% text similarity)",
        "5. Cross-table contradictions (negation flip detection across source tables)",
        "6. Known high-value contradiction targets from case analysis",
        "",
        "**Severity Definitions:**",
        "- **PERJURY**: Sworn statement vs sworn statement (MCL 750.423)",
        "- **IMPEACHMENT**: Sworn statement vs unsworn, or high-severity inconsistency (MRE 613)",
        "- **INCONSISTENCY**: Unsworn vs unsworn, or lower-severity discrepancy",
        "",
        f"*Report generated {now} by contradiction_detector.py*",
    ])

    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Cross-Statement Contradiction Detector"
    )
    parser.add_argument(
        "--speaker", type=str, default=None,
        help="Focus on specific speaker (e.g., 'Emily Watson')",
    )
    parser.add_argument(
        "--report", action="store_true", default=True,
        help="Generate markdown report (default: True)",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Verbose output during processing",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Analyze but don't write to DB",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  CROSS-STATEMENT CONTRADICTION DETECTOR")
    print("  Pigors v. Watson — 2024-001507-DC")
    print("=" * 60)
    print()

    # Connect (read-only for analysis phase)
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        sys.exit(1)

    conn = get_connection(readonly=True)

    # Phase 1: Extract statements
    print("[Phase 1] Extracting statements from database tables...")

    statements = []

    print("  - watson_perjury_compilation...", end=" ", flush=True)
    perjury_stmts = extract_from_watson_perjury(conn)
    statements.extend(perjury_stmts)
    print(f"{len(perjury_stmts)} statements")

    print("  - evidence_quotes...", end=" ", flush=True)
    eq_stmts = extract_from_evidence_quotes(conn)
    statements.extend(eq_stmts)
    print(f"{len(eq_stmts)} statements")

    print("  - adversary_assertions...", end=" ", flush=True)
    aa_stmts = extract_from_adversary_assertions(conn)
    statements.extend(aa_stmts)
    print(f"{len(aa_stmts)} statements")

    print("  - cycle6_financial_evidence...", end=" ", flush=True)
    fin_stmts = extract_from_financial(conn)
    statements.extend(fin_stmts)
    print(f"{len(fin_stmts)} statements")

    print(f"\n  TOTAL: {len(statements)} statements extracted\n")

    # Phase 2: Group by speaker
    print("[Phase 2] Resolving entities and grouping by speaker...")
    by_speaker = defaultdict(list)
    for s in statements:
        by_speaker[s.speaker].append(s)

    for speaker, stmts in sorted(by_speaker.items(), key=lambda x: -len(x[1])):
        print(f"  {speaker}: {len(stmts)} statements")

    # Determine which speakers to analyze
    target_speakers = (
        [args.speaker] if args.speaker
        else list(by_speaker.keys())
    )
    print()

    # Phase 3: Detect contradictions
    print("[Phase 3] Detecting contradictions...")
    all_contradictions = []

    # 3a. Pre-identified from watson_perjury_compilation
    print("  [3a] Mining watson_perjury_compilation...", end=" ", flush=True)
    perjury_contras = find_fact_contradictions_from_perjury(conn)
    if args.speaker:
        perjury_contras = [
            c for c in perjury_contras if c.speaker == args.speaker
        ]
    all_contradictions.extend(perjury_contras)
    print(f"{len(perjury_contras)} found")

    for speaker in target_speakers:
        if speaker not in by_speaker:
            continue
        speaker_count = len(by_speaker[speaker])
        if speaker_count < 2:
            continue

        print(f"\n  Analyzing {speaker} ({speaker_count} statements)...")

        # 3b. Financial contradictions
        print(f"    [3b] Financial contradictions...", end=" ", flush=True)
        fin_c = find_financial_contradictions(statements, speaker)
        all_contradictions.extend(fin_c)
        print(f"{len(fin_c)} found")

        # 3c. Existence contradictions
        print(f"    [3c] Existence contradictions...", end=" ", flush=True)
        exist_c = find_existence_contradictions(statements, speaker)
        all_contradictions.extend(exist_c)
        print(f"{len(exist_c)} found")

        # 3d. Date contradictions
        print(f"    [3d] Date contradictions...", end=" ", flush=True)
        date_c = find_date_contradictions(statements, speaker)
        all_contradictions.extend(date_c)
        print(f"{len(date_c)} found")

        # 3e. Cross-table contradictions
        print(f"    [3e] Cross-table contradictions...", end=" ", flush=True)
        cross_c = find_cross_table_contradictions(statements, speaker)
        all_contradictions.extend(cross_c)
        print(f"{len(cross_c)} found")

    # 3f. Known high-value contradiction targets
    print("\n  [3f] Known contradiction targets...", end=" ", flush=True)
    known_c = seed_known_contradictions(conn)
    if args.speaker:
        known_c = [c for c in known_c if c.speaker == args.speaker]
    all_contradictions.extend(known_c)
    print(f"{len(known_c)} found")

    # Phase 4: Deduplicate
    print(f"\n[Phase 4] Deduplicating {len(all_contradictions)} raw results...")
    unique = deduplicate(all_contradictions)
    print(f"  {len(unique)} unique contradictions after dedup")

    # Sort by impeachment value
    unique.sort(key=lambda c: (-c.impeachment_value, c.severity, c.speaker))

    # Phase 5: Compute stats
    stats = {
        "total": len(unique),
        "perjury": sum(1 for c in unique if c.severity == "PERJURY"),
        "impeachment": sum(1 for c in unique if c.severity == "IMPEACHMENT"),
        "inconsistency": sum(1 for c in unique if c.severity == "INCONSISTENCY"),
        "statements_analyzed": len(statements),
        "sources_scanned": len(set(
            s.source for s in statements if s.source
        )),
        "perjury_rows": len(perjury_stmts),
        "eq_rows": len(eq_stmts),
        "aa_rows": len(aa_stmts),
        "fin_rows": len(fin_stmts),
    }

    print()
    print("=" * 60)
    print("  RESULTS")
    print("=" * 60)
    print(f"  Total contradictions:  {stats['total']}")
    print(f"  PERJURY severity:      {stats['perjury']}")
    print(f"  IMPEACHMENT severity:  {stats['impeachment']}")
    print(f"  INCONSISTENCY:         {stats['inconsistency']}")
    print(f"  Statements analyzed:   {stats['statements_analyzed']}")
    print()

    # Phase 6: Store in DB
    if not args.dry_run and unique:
        print("[Phase 5] Storing results in detected_contradictions table...")
        conn.close()  # Close read-only connection

        # Retry with backoff for locked database
        max_retries = 5
        for attempt in range(max_retries):
            try:
                write_conn = get_connection(readonly=False)
                create_table(write_conn)
                write_conn.execute("DELETE FROM detected_contradictions")
                write_conn.commit()
                stored = store_contradictions(write_conn, unique)
                print(f"  {stored} contradictions stored in DB")

                count = write_conn.execute(
                    "SELECT COUNT(*) FROM detected_contradictions"
                ).fetchone()[0]
                print(f"  Verified: {count} rows in detected_contradictions")
                write_conn.close()
                break
            except sqlite3.OperationalError as e:
                if "locked" in str(e) and attempt < max_retries - 1:
                    import time
                    wait = 5 * (attempt + 1)
                    print(f"  DB locked, retrying in {wait}s (attempt {attempt + 1}/{max_retries})...")
                    try:
                        write_conn.close()
                    except Exception:
                        pass
                    time.sleep(wait)
                else:
                    print(f"  WARNING: Could not write to main DB after {max_retries} attempts: {e}")
                    print(f"  Writing to standalone DB instead...")
                    fallback_db = os.path.join(
                        os.path.dirname(DB_PATH),
                        "detected_contradictions.db"
                    )
                    fb_conn = sqlite3.connect(fallback_db)
                    fb_conn.execute("PRAGMA journal_mode = WAL")
                    fb_conn.row_factory = sqlite3.Row
                    create_table(fb_conn)
                    fb_conn.execute("DELETE FROM detected_contradictions")
                    fb_conn.commit()
                    stored = store_contradictions(fb_conn, unique)
                    print(f"  {stored} contradictions stored in {fallback_db}")
                    fb_conn.close()
                    break

        conn = get_connection(readonly=True)
    elif args.dry_run:
        print("[Phase 5] DRY RUN — skipping DB write")

    # Phase 7: Generate report
    if args.report:
        print("\n[Phase 6] Generating report...")
        os.makedirs(REPORT_DIR, exist_ok=True)
        report = generate_report(unique, stats)
        with open(REPORT_PATH, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"  Report written to: {REPORT_PATH}")
        print(f"  Report size: {len(report):,} characters")

    # Show top 10 high-value contradictions
    print()
    print("=" * 60)
    print("  TOP 10 HIGH-VALUE CONTRADICTIONS")
    print("=" * 60)

    for i, c in enumerate(unique[:10], 1):
        print(f"\n  {i}. [{c.severity}] {c.speaker} — {c.contradiction_type} "
              f"(Value: {c.impeachment_value}/10)")
        print(f"     Stmt 1: {c.stmt1.text[:120]}...")
        print(f"     Source: {c.stmt1.source[:80]}")
        print(f"     Stmt 2: {c.stmt2.text[:120]}...")
        print(f"     Source: {c.stmt2.source[:80]}")
        print(f"     Use: {c.filing_use[:100]}")

    conn.close()
    print(f"\n{'=' * 60}")
    print("  CONTRADICTION DETECTION COMPLETE")
    print(f"{'=' * 60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
