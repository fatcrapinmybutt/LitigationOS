"""
LitigationOS Agent Evaluation Framework v1.0

Deterministic, code-based evaluation for agent outputs.
No external API calls — all evaluation runs locally.

Quality Dimensions:
  1. Correctness — citations exist in DB, dates are valid
  2. Completeness — all required sections present
  3. Groundedness — claims trace to evidence_quotes
  4. Safety — no child name leaks, no AI refs, no hallucinations
  5. Format — IRAC structure, proper caption, COS present
  6. Consistency — same input produces same quality score
"""

from __future__ import annotations

import json
import logging
import re
import sqlite3
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger("litigationos.eval")

# ---------------------------------------------------------------------------
# Default DB path — canonical location (3 parents up from internal/)
# ---------------------------------------------------------------------------

_DEFAULT_DB_PATH = str(
    Path(__file__).resolve().parents[3] / "litigation_context.db"
)


def _get_conn(db_path: str) -> sqlite3.Connection:
    """Open a connection with mandatory PRAGMA triad (Rule 18)."""
    conn = sqlite3.connect(db_path, timeout=60)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    return conn


# ---------------------------------------------------------------------------
# Quality dimensions
# ---------------------------------------------------------------------------

class QualityDimension(Enum):
    """Six evaluation dimensions for agent output quality."""
    CORRECTNESS = "correctness"
    COMPLETENESS = "completeness"
    GROUNDEDNESS = "groundedness"
    SAFETY = "safety"
    FORMAT = "format"
    CONSISTENCY = "consistency"


# ---------------------------------------------------------------------------
# Evaluation result
# ---------------------------------------------------------------------------

@dataclass
class EvalResult:
    """Result of evaluating one quality dimension."""
    dimension: QualityDimension
    score: float              # 0.0 – 1.0
    passed: bool
    checks: dict[str, bool] = field(default_factory=dict)
    details: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON storage."""
        return {
            "dimension": self.dimension.value,
            "score": round(self.score, 4),
            "passed": self.passed,
            "checks": dict(self.checks),
            "details": self.details,
        }


# ---------------------------------------------------------------------------
# SafetyChecker — MOST CRITICAL (Rules 2–6, 9)
# ---------------------------------------------------------------------------

class SafetyChecker:
    """Static methods that enforce filing safety rules.

    Every check returns (safe: bool, violations: list[str]).
    check_all() returns a composite EvalResult.
    """

    # --- Child name patterns — MCR 8.119(H) ---
    # Full-name expansions (any middle initial/name variant)
    _CHILD_FULL_NAME_PATTERNS: list[re.Pattern[str]] = [
        re.compile(r"\bLincoln\s+D(?:\.|\w*)\s*W(?:atson)?\b", re.IGNORECASE),
        re.compile(r"\bLincoln\s+(?:Pigors|Watson)\b", re.IGNORECASE),
    ]
    # Standalone "Lincoln" near custody/child context
    _CHILD_CONTEXT_RE = re.compile(
        r"\bLincoln\b(?=[\s\S]{0,80}"
        r"(?:custody|child|parenting|father|mother|minor|son|daughter))",
        re.IGNORECASE,
    )
    _CHILD_SAFE_RE = re.compile(
        r"\bL\.?D\.?W\.?\b|the\s+minor\s+child", re.IGNORECASE
    )

    # --- AI / system references — Rule 3 ---
    _AI_PATTERNS: list[re.Pattern[str]] = [
        re.compile(r"\bLitigationOS\b", re.IGNORECASE),
        re.compile(r"\bOMEGA\b"),
        re.compile(r"\bEGCP\b"),
        re.compile(r"\bNEXUS\b(?:\s+engine)?", re.IGNORECASE),
        re.compile(r"\bCHIMERA\b(?:\s+engine)?", re.IGNORECASE),
        re.compile(r"\bCHRONOS\b", re.IGNORECASE),
        re.compile(r"\bCERBERUS\b", re.IGNORECASE),
        re.compile(r"\bSINGULARITY\b", re.IGNORECASE),
        re.compile(r"\bSUPERPIN\b", re.IGNORECASE),
        re.compile(r"\bDELTA9\b", re.IGNORECASE),
        re.compile(r"\bdatabase\s+scor(?:e|ing)\b", re.IGNORECASE),
        re.compile(r"\bAI[\s-](?:generated|assisted|powered|scoring)\b", re.IGNORECASE),
        re.compile(r"\bagent\s+(?:fleet|swarm|dispatch|evaluation)\b", re.IGNORECASE),
        re.compile(r"\bknowledge\s+graph\b", re.IGNORECASE),
        re.compile(r"\blitigation_context\.db\b", re.IGNORECASE),
        re.compile(r"\bevidence_(?:fts|quotes)\b", re.IGNORECASE),
    ]

    # --- Hallucinations — Rule 9 & case-specific ---
    _HALLUCINATION_PATTERNS: list[tuple[re.Pattern[str], str]] = [
        (
            re.compile(r"\bJane\s+Berry\b", re.IGNORECASE),
            "Jane Berry is a hallucination — this person never existed",
        ),
        (
            re.compile(r"\bPatricia\s+Berry\b", re.IGNORECASE),
            "Patricia Berry is a hallucination — this person never existed",
        ),
        (
            re.compile(r"\bMCL\s+722\.27c\b", re.IGNORECASE),
            "MCL 722.27c does not exist — correct cite is MCL 722.23(j)",
        ),
    ]
    _BRADY_RE = re.compile(r"\bBrady\s+v\.?\s*Maryland\b", re.IGNORECASE)
    _FAMILY_CONTEXT_RE = re.compile(
        r"\bcustody|family\s+law|parenting\s+time|best\s+interest|"
        r"divorce|MCL\s+722|domestic\b",
        re.IGNORECASE,
    )

    # --- Party name compliance — Rules 5, 6 ---
    _EMILY_WRONG: list[tuple[re.Pattern[str], str]] = [
        (
            re.compile(r"\bEmily\s+Ann\s+Watson\b", re.IGNORECASE),
            "Wrong middle — must be 'Emily A. Watson'",
        ),
        (
            re.compile(r"\bEmily\s+M\.\s*Watson\b", re.IGNORECASE),
            "Wrong middle initial — must be 'Emily A. Watson'",
        ),
        (
            re.compile(r"\bTiffany\b.*?\bWatson\b", re.IGNORECASE),
            "Wrong first name — Defendant is Emily A. Watson, not Tiffany",
        ),
        (
            re.compile(r"\bWatson[\s-]Pigors\b", re.IGNORECASE),
            "Wrong surname — use 'Emily A. Watson' (not Watson-Pigors)",
        ),
    ]
    _MCNEILL_WRONG_RE = re.compile(
        r"\bMcNeil\b(?!l)"   # "McNeil" not followed by another l
        r"|\bMcNiel\b"       # common misspelling
    )

    # --- Pro se compliance — Rule 4 ---
    _COUNSEL_RE = re.compile(
        r"\b(?:undersigned\s+counsel|attorney\s+for\s+"
        r"(?:Plaintiff|petitioner|respondent))\b",
        re.IGNORECASE,
    )

    # ----- static check methods -----

    @staticmethod
    def check_child_name(text: str) -> tuple[bool, list[str]]:
        """Check for child name leaks — MCR 8.119(H).

        Safe references (L.D.W., the minor child) are allowed.
        """
        violations: list[str] = []

        for pat in SafetyChecker._CHILD_FULL_NAME_PATTERNS:
            for m in pat.finditer(text):
                violations.append(
                    f"Child full name leak at pos {m.start()}: "
                    f"'{m.group()}' — use 'L.D.W.' per MCR 8.119(H)"
                )

        for m in SafetyChecker._CHILD_CONTEXT_RE.finditer(text):
            snippet = text[max(0, m.start() - 5):m.end() + 40]
            if not SafetyChecker._CHILD_SAFE_RE.search(snippet):
                violations.append(
                    f"'Lincoln' near custody context at pos {m.start()}: "
                    f"...{snippet.strip()[:60]}..."
                )

        return (len(violations) == 0, violations)

    @staticmethod
    def check_ai_references(text: str) -> tuple[bool, list[str]]:
        """Detect AI / system references that must not appear in filings."""
        violations: list[str] = []
        for pat in SafetyChecker._AI_PATTERNS:
            for m in pat.finditer(text):
                violations.append(
                    f"AI/system reference at pos {m.start()}: "
                    f"'{m.group()}' — strip before filing"
                )
        return (len(violations) == 0, violations)

    @staticmethod
    def check_hallucinations(text: str) -> tuple[bool, list[str]]:
        """Detect known hallucinated names, citations, and misapplied law."""
        violations: list[str] = []

        for pat, msg in SafetyChecker._HALLUCINATION_PATTERNS:
            for m in pat.finditer(text):
                violations.append(f"{msg} (pos {m.start()})")

        if SafetyChecker._BRADY_RE.search(text):
            if SafetyChecker._FAMILY_CONTEXT_RE.search(text):
                violations.append(
                    "Brady v Maryland is for criminal cases — "
                    "use Mathews v Eldridge for family law due process"
                )

        return (len(violations) == 0, violations)

    @staticmethod
    def check_party_names(text: str) -> tuple[bool, list[str]]:
        """Verify party names, judge spelling, and pro se language."""
        violations: list[str] = []

        for pat, msg in SafetyChecker._EMILY_WRONG:
            for m in pat.finditer(text):
                violations.append(f"{msg} (pos {m.start()})")
                break  # one violation per pattern is enough

        for m in SafetyChecker._MCNEILL_WRONG_RE.finditer(text):
            violations.append(
                f"Judge name misspelled at pos {m.start()}: "
                f"'{m.group()}' — must be 'McNeill' (two L's)"
            )
            break

        for m in SafetyChecker._COUNSEL_RE.finditer(text):
            violations.append(
                f"Pro se violation at pos {m.start()}: '{m.group()}' — "
                f"use 'Plaintiff, appearing pro se'"
            )

        return (len(violations) == 0, violations)

    @staticmethod
    def check_all(text: str) -> EvalResult:
        """Run ALL safety checks. Returns composite EvalResult."""
        child_safe, child_v = SafetyChecker.check_child_name(text)
        ai_safe, ai_v = SafetyChecker.check_ai_references(text)
        halluc_safe, halluc_v = SafetyChecker.check_hallucinations(text)
        party_safe, party_v = SafetyChecker.check_party_names(text)

        all_violations = child_v + ai_v + halluc_v + party_v
        checks: dict[str, bool] = {
            "child_name_safe": child_safe,
            "no_ai_references": ai_safe,
            "no_hallucinations": halluc_safe,
            "party_names_correct": party_safe,
        }
        passed_count = sum(checks.values())
        total = len(checks)
        score = passed_count / total if total > 0 else 0.0

        if all_violations:
            details = (
                f"{len(all_violations)} violation(s): "
                + "; ".join(all_violations[:5])
            )
            if len(all_violations) > 5:
                details += f" ... and {len(all_violations) - 5} more"
        else:
            details = "All safety checks passed"

        return EvalResult(
            dimension=QualityDimension.SAFETY,
            score=score,
            passed=(len(all_violations) == 0),
            checks=checks,
            details=details,
        )


# ---------------------------------------------------------------------------
# CitationVerifier
# ---------------------------------------------------------------------------

class CitationVerifier:
    """Extract and verify legal citations against the database."""

    _CITATION_RE = re.compile(
        r"(?:MCL|MCR|MRE)\s+\d+[\.\d]*(?:\([a-zA-Z0-9]+\))*",
        re.IGNORECASE,
    )

    def __init__(self, db_path: str = "") -> None:
        self._db_path = db_path or _DEFAULT_DB_PATH

    def extract_citations(self, text: str) -> list[str]:
        """Extract all MCL/MCR/MRE citations from text (deduplicated)."""
        if not text:
            return []
        raw = self._CITATION_RE.findall(text)
        seen: set[str] = set()
        result: list[str] = []
        for c in raw:
            norm = re.sub(r"\s+", " ", c.strip()).upper()
            if norm not in seen:
                seen.add(norm)
                result.append(norm)
        return result

    def verify_single(self, citation: str) -> bool:
        """Check one citation against michigan_rules_extracted table."""
        norm = re.sub(r"\s+", " ", citation.strip()).upper()
        base = re.sub(r"\([a-zA-Z0-9]+\)$", "", norm).strip()
        try:
            conn = _get_conn(self._db_path)
            try:
                # Check table exists
                tbl = conn.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name='michigan_rules_extracted'"
                ).fetchone()
                if not tbl:
                    return False

                row = conn.execute(
                    "SELECT 1 FROM michigan_rules_extracted "
                    "WHERE UPPER(rule_number) LIKE ? "
                    "   OR UPPER(rule_number) LIKE ? LIMIT 1",
                    (f"%{norm}%", f"%{base}%"),
                ).fetchone()
                if row:
                    return True

                # Fallback: search full_text for the citation string
                row = conn.execute(
                    "SELECT 1 FROM michigan_rules_extracted "
                    "WHERE full_text LIKE ? LIMIT 1",
                    (f"%{base}%",),
                ).fetchone()
                return row is not None
            finally:
                conn.close()
        except sqlite3.Error as exc:
            logger.warning("Citation verify error for '%s': %s", citation, exc)
            return False

    def verify_citations(self, text: str) -> EvalResult:
        """Extract all citations from text and verify each against DB.

        Score = verified_count / total_count.  Pass threshold: 80%.
        """
        citations = self.extract_citations(text)
        if not citations:
            return EvalResult(
                dimension=QualityDimension.CORRECTNESS,
                score=1.0,
                passed=True,
                checks={},
                details="No MCL/MCR/MRE citations found to verify",
            )

        checks: dict[str, bool] = {}
        for cite in citations:
            checks[cite] = self.verify_single(cite)

        verified = sum(1 for v in checks.values() if v)
        total = len(checks)
        score = verified / total if total > 0 else 0.0
        passed = score >= 0.8

        unverified = [c for c, v in checks.items() if not v]
        if unverified:
            details = (
                f"{verified}/{total} citations verified. "
                f"Unverified: {', '.join(unverified[:5])}"
            )
            if len(unverified) > 5:
                details += f" ... and {len(unverified) - 5} more"
        else:
            details = f"All {total} citations verified in DB"

        return EvalResult(
            dimension=QualityDimension.CORRECTNESS,
            score=round(score, 4),
            passed=passed,
            checks=checks,
            details=details,
        )


# ---------------------------------------------------------------------------
# FormatChecker — IRAC structure, caption, COS
# ---------------------------------------------------------------------------

class FormatChecker:
    """Check structural format of legal filings.

    Methods return tuples for composability; AgentEvalSuite wraps them
    into EvalResult objects.
    """

    _IRAC_KEYWORDS: dict[str, list[str]] = {
        "issue": [
            "issue", "question presented", "statement of issues",
            "statement of the case", "introduction",
        ],
        "rule": [
            "rule", "legal standard", "applicable law",
            "statement of facts", "factual background",
            "legal framework", "governing law", "authority",
        ],
        "application": [
            "application", "argument", "analysis",
            "discussion", "points and authorities",
        ],
        "conclusion": [
            "conclusion", "relief requested", "prayer for relief",
            "wherefore", "request for relief",
        ],
    }

    _CAPTION_COURT_RE = re.compile(
        r"(?:circuit\s+court|court\s+of\s+appeals|district\s+court"
        r"|supreme\s+court|probate\s+court)",
        re.IGNORECASE,
    )
    _CAPTION_CASE_RE = re.compile(r"\b\d{4}[-–]\d{4,8}[-–]?\w{0,4}\b")
    _CAPTION_PARTIES_RE = re.compile(
        r"(?:plaintiff|defendant|petitioner|respondent)", re.IGNORECASE
    )
    _COS_RE = re.compile(r"certificate\s+of\s+service", re.IGNORECASE)

    @staticmethod
    def check_irac(text: str) -> tuple[bool, dict[str, bool]]:
        """Check for IRAC structure or common filing equivalents.

        Returns (has_structure, sections_found).
        """
        sections_found: dict[str, bool] = {}
        text_upper = text.upper()

        for component, keywords in FormatChecker._IRAC_KEYWORDS.items():
            found = False
            for kw in keywords:
                # Check for header-style occurrence (## Header, ALL CAPS line,
                # **bold**) or standalone CAPS line
                header_re = re.compile(
                    r"(?:^|\n)\s*(?:#{1,4}\s+)?" + re.escape(kw.upper()),
                    re.MULTILINE,
                )
                if header_re.search(text_upper):
                    found = True
                    break
                # Also accept **keyword** markdown bold
                bold_re = re.compile(
                    r"\*\*" + re.escape(kw) + r"\*\*", re.IGNORECASE
                )
                if bold_re.search(text):
                    found = True
                    break
            sections_found[component] = found

        has_structure = sum(sections_found.values()) >= 3
        return (has_structure, sections_found)

    @staticmethod
    def check_caption(text: str) -> tuple[bool, str]:
        """Check for case caption elements (court, case number, parties).

        Returns (has_caption, detail_message).
        """
        found: dict[str, bool] = {
            "court": bool(FormatChecker._CAPTION_COURT_RE.search(text)),
            "case_number": bool(FormatChecker._CAPTION_CASE_RE.search(text)),
            "parties": bool(FormatChecker._CAPTION_PARTIES_RE.search(text)),
        }
        found_count = sum(found.values())
        has_caption = found_count >= 2

        missing = [k for k, v in found.items() if not v]
        if missing:
            detail = (
                f"Caption partial ({found_count}/3): "
                f"missing {', '.join(missing)}"
            )
        else:
            detail = "Caption complete (court, case number, parties)"
        return (has_caption, detail)

    @staticmethod
    def check_certificate_of_service(text: str) -> tuple[bool, str]:
        """Check for Certificate of Service section."""
        has_cos = bool(FormatChecker._COS_RE.search(text))
        if has_cos:
            return (True, "Certificate of Service found")
        return (False, "Certificate of Service NOT found")


# ---------------------------------------------------------------------------
# MetricsRecorder — persist eval results to DB
# ---------------------------------------------------------------------------

class MetricsRecorder:
    """Persist evaluation metrics to SQLite for cross-session trend tracking.

    Creates eval_metrics table on init if it doesn't exist.
    """

    _CREATE_TABLE_SQL = (
        "CREATE TABLE IF NOT EXISTS eval_metrics ("
        "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "  eval_type TEXT NOT NULL,"
        "  dimension TEXT NOT NULL,"
        "  score REAL NOT NULL,"
        "  passed INTEGER NOT NULL,"
        "  lane TEXT DEFAULT '',"
        "  details_json TEXT,"
        "  session_id TEXT DEFAULT '',"
        "  created_at TEXT DEFAULT (datetime('now'))"
        ")"
    )
    _CREATE_INDEX_SQL = (
        "CREATE INDEX IF NOT EXISTS idx_eval_type_time "
        "ON eval_metrics(eval_type, created_at)"
    )

    def __init__(self, db_path: str = "") -> None:
        self._db_path = db_path or _DEFAULT_DB_PATH
        self._ensure_table()

    def _ensure_table(self) -> None:
        """Create eval_metrics table and index if they don't exist."""
        try:
            conn = _get_conn(self._db_path)
            try:
                conn.execute(self._CREATE_TABLE_SQL)
                conn.execute(self._CREATE_INDEX_SQL)
                conn.commit()
            finally:
                conn.close()
        except sqlite3.Error as exc:
            logger.error("Failed to create eval_metrics table: %s", exc)

    def record(
        self,
        results: list[EvalResult],
        eval_type: str = "filing",
        lane: str = "",
        session_id: str = "",
    ) -> int:
        """Persist evaluation results. Returns count of rows inserted."""
        if not results:
            return 0

        inserted = 0
        try:
            conn = _get_conn(self._db_path)
            try:
                for r in results:
                    details_json = json.dumps(
                        {"checks": r.checks, "details": r.details},
                        ensure_ascii=False,
                    )
                    conn.execute(
                        "INSERT INTO eval_metrics "
                        "(eval_type, dimension, score, passed, lane, "
                        " details_json, session_id) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (
                            eval_type,
                            r.dimension.value,
                            r.score,
                            1 if r.passed else 0,
                            lane,
                            details_json,
                            session_id,
                        ),
                    )
                    inserted += 1
                conn.commit()

                # Verify write (Rule 19)
                verify_row = conn.execute(
                    "SELECT COUNT(*) AS cnt FROM eval_metrics "
                    "WHERE eval_type = ? AND session_id = ?",
                    (eval_type, session_id),
                ).fetchone()
                logger.debug(
                    "Recorded %d eval results (verified %d in DB for "
                    "session '%s')",
                    inserted,
                    verify_row["cnt"] if verify_row else 0,
                    session_id,
                )
            finally:
                conn.close()
        except sqlite3.Error as exc:
            logger.error("Failed to record eval metrics: %s", exc)
        return inserted

    def get_trend(
        self,
        eval_type: str,
        dimension: str = "",
        days: int = 30,
    ) -> list[dict[str, Any]]:
        """Get score trend over time, grouped by date.

        Returns list of dicts with date, avg_score, count, pass_rate.
        """
        try:
            conn = _get_conn(self._db_path)
            try:
                params: list[Any] = [eval_type, days]
                dim_clause = ""
                if dimension:
                    dim_clause = "AND dimension = ?"
                    params.append(dimension)

                rows = conn.execute(
                    f"SELECT "
                    f"  date(created_at) AS dt, "
                    f"  AVG(score) AS avg_score, "
                    f"  COUNT(*) AS cnt, "
                    f"  AVG(passed) AS pass_rate "
                    f"FROM eval_metrics "
                    f"WHERE eval_type = ? "
                    f"  AND created_at >= datetime('now', "
                    f"      '-' || ? || ' days') "
                    f"  {dim_clause} "
                    f"GROUP BY date(created_at) "
                    f"ORDER BY dt",
                    params,
                ).fetchall()

                return [
                    {
                        "date": row["dt"],
                        "avg_score": round(row["avg_score"], 4),
                        "count": row["cnt"],
                        "pass_rate": round(row["pass_rate"], 4),
                    }
                    for row in rows
                ]
            finally:
                conn.close()
        except sqlite3.Error as exc:
            logger.error("Failed to get eval trend: %s", exc)
            return []

    def detect_regression(
        self,
        eval_type: str,
        dimension: str,
        window: int = 10,
    ) -> dict[str, Any]:
        """Compare recent scores vs baseline using simple mean comparison.

        Splits last window*2 records into baseline half and recent half.
        Returns status (STABLE/REGRESSION/IMPROVING), baseline_mean,
        current_mean, delta.
        """
        try:
            conn = _get_conn(self._db_path)
            try:
                rows = conn.execute(
                    "SELECT score FROM eval_metrics "
                    "WHERE eval_type = ? AND dimension = ? "
                    "ORDER BY created_at DESC LIMIT ?",
                    (eval_type, dimension, window * 2),
                ).fetchall()

                scores = [r["score"] for r in rows]

                if len(scores) < 4:
                    return {
                        "status": "INSUFFICIENT_DATA",
                        "baseline_mean": 0.0,
                        "current_mean": 0.0,
                        "delta": 0.0,
                        "sample_size": len(scores),
                    }

                midpoint = len(scores) // 2
                recent = scores[:midpoint]      # newest first
                baseline = scores[midpoint:]

                recent_mean = sum(recent) / len(recent)
                baseline_mean = sum(baseline) / len(baseline)
                delta = recent_mean - baseline_mean

                threshold = 0.1
                if delta < -threshold:
                    status = "REGRESSION"
                elif delta > threshold:
                    status = "IMPROVING"
                else:
                    status = "STABLE"

                return {
                    "status": status,
                    "baseline_mean": round(baseline_mean, 4),
                    "current_mean": round(recent_mean, 4),
                    "delta": round(delta, 4),
                    "sample_size": len(scores),
                }
            finally:
                conn.close()
        except sqlite3.Error as exc:
            logger.error("Failed to detect regression: %s", exc)
            return {
                "status": "ERROR",
                "baseline_mean": 0.0,
                "current_mean": 0.0,
                "delta": 0.0,
                "error": str(exc),
            }

    def get_dashboard(self, eval_type: str = "") -> dict[str, Any]:
        """Summary of all metrics with counts, averages, pass rates."""
        try:
            conn = _get_conn(self._db_path)
            try:
                type_clause = ""
                params: list[Any] = []
                if eval_type:
                    type_clause = "WHERE eval_type = ?"
                    params.append(eval_type)

                rows = conn.execute(
                    f"SELECT "
                    f"  dimension, "
                    f"  COUNT(*) AS cnt, "
                    f"  AVG(score) AS avg_score, "
                    f"  MIN(score) AS min_score, "
                    f"  MAX(score) AS max_score, "
                    f"  AVG(passed) AS pass_rate "
                    f"FROM eval_metrics {type_clause} "
                    f"GROUP BY dimension "
                    f"ORDER BY dimension",
                    params,
                ).fetchall()

                dimensions: dict[str, dict[str, Any]] = {}
                total_count = 0
                total_score_sum = 0.0
                total_passed_sum = 0.0

                for row in rows:
                    cnt = row["cnt"]
                    dimensions[row["dimension"]] = {
                        "count": cnt,
                        "avg_score": round(row["avg_score"], 4),
                        "min_score": round(row["min_score"], 4),
                        "max_score": round(row["max_score"], 4),
                        "pass_rate": round(row["pass_rate"], 4),
                    }
                    total_count += cnt
                    total_score_sum += row["avg_score"] * cnt
                    total_passed_sum += row["pass_rate"] * cnt

                overall_avg = (
                    total_score_sum / total_count
                    if total_count > 0 else 0.0
                )
                overall_pass = (
                    total_passed_sum / total_count
                    if total_count > 0 else 0.0
                )

                return {
                    "total_evaluations": total_count,
                    "overall_avg_score": round(overall_avg, 4),
                    "overall_pass_rate": round(overall_pass, 4),
                    "dimensions": dimensions,
                    "eval_type_filter": eval_type or "(all)",
                }
            finally:
                conn.close()
        except sqlite3.Error as exc:
            logger.error("Failed to get eval dashboard: %s", exc)
            return {
                "total_evaluations": 0,
                "overall_avg_score": 0.0,
                "overall_pass_rate": 0.0,
                "dimensions": {},
                "error": str(exc),
            }


# ---------------------------------------------------------------------------
# AgentEvalSuite — main evaluation orchestrator
# ---------------------------------------------------------------------------

class AgentEvalSuite:
    """Orchestrates evaluation across all quality dimensions.

    Runs safety, correctness, format, groundedness, and completeness
    checks on filing text.  All evaluation is deterministic and local.
    """

    def __init__(self, db_path: str = "") -> None:
        self._db_path = db_path or _DEFAULT_DB_PATH
        self._citation_verifier = CitationVerifier(self._db_path)

    def evaluate_filing_output(
        self, text: str, lane: str = ""
    ) -> list[EvalResult]:
        """Run all evaluators on a filing text."""
        return [
            self.evaluate_citation_accuracy(text),
            self.evaluate_safety(text),
            self.evaluate_format(text),
            self.evaluate_groundedness(text),
            self.evaluate_completeness(text),
        ]

    def evaluate_citation_accuracy(self, text: str) -> EvalResult:
        """Check every MCL/MCR/MRE citation against DB."""
        return self._citation_verifier.verify_citations(text)

    def evaluate_safety(self, text: str) -> EvalResult:
        """Check for child name leaks, AI refs, hallucinations, party names."""
        return SafetyChecker.check_all(text)

    def evaluate_format(self, text: str) -> EvalResult:
        """Check IRAC structure, caption presence, COS presence."""
        has_irac, irac_sections = FormatChecker.check_irac(text)
        has_caption, caption_detail = FormatChecker.check_caption(text)
        has_cos, cos_detail = FormatChecker.check_certificate_of_service(text)

        checks: dict[str, bool] = {
            "irac_structure": has_irac,
            "caption_present": has_caption,
            "certificate_of_service": has_cos,
        }
        for component, found in irac_sections.items():
            checks[f"irac_{component}"] = found

        # Weighted composite: IRAC 40%, caption 35%, COS 25%
        score = (
            (0.4 if has_irac else 0.0)
            + (0.35 if has_caption else 0.0)
            + (0.25 if has_cos else 0.0)
        )
        passed = score >= 0.7

        parts: list[str] = []
        if not has_irac:
            missing = [k for k, v in irac_sections.items() if not v]
            parts.append(f"IRAC missing: {', '.join(missing)}")
        if not has_caption:
            parts.append(caption_detail)
        if not has_cos:
            parts.append(cos_detail)

        details = "; ".join(parts) if parts else "Format checks passed"

        return EvalResult(
            dimension=QualityDimension.FORMAT,
            score=round(score, 4),
            passed=passed,
            checks=checks,
            details=details,
        )

    def evaluate_groundedness(self, text: str) -> EvalResult:
        """Check that factual claims reference evidence.

        Looks for exhibit references, page numbers, dates, record
        citations, Bates numbers, and affidavit references.
        """
        markers: dict[str, re.Pattern[str]] = {
            "exhibit_refs": re.compile(
                r"\bExhibit\s+[A-Z0-9]+\b", re.IGNORECASE
            ),
            "page_numbers": re.compile(
                r"(?:\bp(?:age|p?)\.?\s*\d+|\bat\s+\d+)\b",
                re.IGNORECASE,
            ),
            "date_refs": re.compile(
                r"\b(?:January|February|March|April|May|June|July|"
                r"August|September|October|November|December)"
                r"\s+\d{1,2},?\s+\d{4}\b"
                r"|\b\d{1,2}/\d{1,2}/\d{2,4}\b"
                r"|\b\d{4}-\d{2}-\d{2}\b"
            ),
            "record_refs": re.compile(
                r"\b(?:Tr\.?\s+(?:at\s+)?\d+|Record\s+(?:at\s+)?\d+)\b",
                re.IGNORECASE,
            ),
            "bates_refs": re.compile(r"\b[A-Z]+-\d{4,}\b"),
            "affidavit_refs": re.compile(
                r"\b(?:affidavit|declaration|sworn\s+statement)\b",
                re.IGNORECASE,
            ),
        }

        checks: dict[str, bool] = {}
        marker_count = 0
        for name, pattern in markers.items():
            matches = pattern.findall(text)
            checks[name] = len(matches) > 0
            marker_count += len(matches)

        word_count = max(len(text.split()), 1)
        density = marker_count / word_count
        # ~1 marker per 100 words is well-grounded
        raw_score = min(density * 100.0, 1.0)

        types_present = sum(checks.values())
        type_bonus = min(types_present / 4.0, 1.0)
        score = min((raw_score * 0.6) + (type_bonus * 0.4), 1.0)

        passed = score >= 0.3 and types_present >= 2

        missing = [k for k, v in checks.items() if not v]
        if missing:
            details = (
                f"{marker_count} grounding markers "
                f"({types_present} types). "
                f"Missing: {', '.join(missing)}"
            )
        else:
            details = (
                f"{marker_count} grounding markers across "
                f"{types_present} types — well grounded"
            )

        return EvalResult(
            dimension=QualityDimension.GROUNDEDNESS,
            score=round(score, 4),
            passed=passed,
            checks=checks,
            details=details,
        )

    def evaluate_completeness(
        self,
        text: str,
        required_sections: list[str] | None = None,
    ) -> EvalResult:
        """Check all required sections are present in the text."""
        if required_sections is None:
            required_sections = [
                "caption",
                "introduction",
                "statement of facts",
                "argument",
                "relief requested",
                "certificate of service",
            ]

        text_upper = text.upper()
        checks: dict[str, bool] = {}

        # Alternate header names for common sections
        alt_map: dict[str, list[str]] = {
            "CAPTION": [
                "CIRCUIT COURT", "COURT OF APPEALS",
                "DISTRICT COURT", "V.",
            ],
            "INTRODUCTION": [
                "INTRODUCTION", "PRELIMINARY STATEMENT",
            ],
            "RELIEF REQUESTED": [
                "RELIEF REQUESTED", "WHEREFORE",
                "PRAYER FOR RELIEF",
            ],
            "CERTIFICATE OF SERVICE": [
                "CERTIFICATE OF SERVICE",
            ],
        }

        for section in required_sections:
            section_upper = section.upper()
            # Primary: look for section header pattern
            header_re = re.compile(
                r"(?:^|\n)\s*(?:#{1,4}\s+)?"
                + re.escape(section_upper),
                re.MULTILINE,
            )
            found = bool(header_re.search(text_upper))

            # Secondary: check alternates
            if not found and section_upper in alt_map:
                for alt in alt_map[section_upper]:
                    if alt in text_upper:
                        found = True
                        break

            # Tertiary: markdown bold **Section**
            if not found:
                bold_re = re.compile(
                    r"\*\*" + re.escape(section) + r"\*\*",
                    re.IGNORECASE,
                )
                found = bool(bold_re.search(text))

            # Last resort: plain substring
            if not found and section_upper in text_upper:
                found = True

            checks[section] = found

        found_count = sum(checks.values())
        total = len(checks)
        score = found_count / total if total > 0 else 0.0
        passed = score >= 0.7

        missing = [s for s, v in checks.items() if not v]
        if missing:
            details = (
                f"{found_count}/{total} sections found. "
                f"Missing: {', '.join(missing)}"
            )
        else:
            details = f"All {total} required sections present"

        return EvalResult(
            dimension=QualityDimension.COMPLETENESS,
            score=round(score, 4),
            passed=passed,
            checks=checks,
            details=details,
        )

    @staticmethod
    def score_summary(results: list[EvalResult]) -> dict[str, Any]:
        """Aggregate scores with overall pass/fail.

        Safety failures are critical — any safety fail = overall fail.
        """
        if not results:
            return {
                "overall_score": 0.0,
                "overall_passed": False,
                "dimensions": {},
                "failures": ["No evaluation results"],
                "total_checks": 0,
                "passed_checks": 0,
            }

        dimensions: dict[str, dict[str, Any]] = {}
        for r in results:
            dimensions[r.dimension.value] = {
                "score": round(r.score, 4),
                "passed": r.passed,
                "details": r.details,
            }

        scores = [r.score for r in results]
        overall_score = sum(scores) / len(scores)

        safety_passed = all(
            r.passed for r in results
            if r.dimension == QualityDimension.SAFETY
        )
        all_passed = all(r.passed for r in results)

        failures = [
            f"{r.dimension.value}: {r.details}"
            for r in results if not r.passed
        ]

        return {
            "overall_score": round(overall_score, 4),
            "overall_passed": all_passed and safety_passed,
            "dimensions": dimensions,
            "failures": failures,
            "total_checks": sum(len(r.checks) for r in results),
            "passed_checks": sum(
                sum(1 for v in r.checks.values() if v)
                for r in results
            ),
        }


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------

def evaluate_text(text: str, db_path: str = "") -> dict[str, Any]:
    """One-call evaluation returning a full quality report.

    Runs all evaluators and returns aggregated results as a dict.
    """
    suite = AgentEvalSuite(db_path=db_path)
    results = suite.evaluate_filing_output(text)
    summary = AgentEvalSuite.score_summary(results)
    summary["results"] = [r.to_dict() for r in results]
    return summary


def quick_safety_check(text: str) -> bool:
    """Fast pass/fail safety check. Returns True if text is safe."""
    return SafetyChecker.check_all(text).passed
