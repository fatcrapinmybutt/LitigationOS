# -*- coding: utf-8 -*-
"""
Filing Completeness Scorer — LitigationOS Legal AI Subsystem
=============================================================
Scores any court filing 0-100 across eight quality dimensions,
producing a letter grade and a filing-readiness determination.

Scoring Dimensions (weighted):
    1. Citation Completeness   (15%) — Legal citations present and verifiable
    2. Evidence Linkage        (15%) — Claims cite supporting evidence
    3. Placeholder Resolution  (15%) — All bracket/TODO markers resolved
    4. Signature/Verification  (10%) — Signature block, oath, certificate of service
    5. SCAO Form Compliance    (10%) — Required form numbers, case-number format
    6. Argument Completeness   (10%) — Arguments address all claim elements
    7. Service Planning        (10%) — Proof of service planned for all parties
    8. Formatting/Structure    (15%) — Caption, heading hierarchy, page numbering

Grade Scale:
    A  90-100  |  B  80-89  |  C  70-79  |  D  60-69  |  F  < 60

A filing is READY only when grade >= C **and** there are zero critical issues.

Usage:
    from legal_ai.completeness_scorer import CompletenessScorer

    scorer = CompletenessScorer()
    report = scorer.score_filing(text, filing_type="motion")
    print(report.overall_score, report.grade, report.filing_ready)

    # Score a file on disk
    report = scorer.score_file("path/to/motion.txt")

    # Batch scoring
    reports = scorer.score_batch(["file1.txt", "file2.txt"])
"""
from __future__ import annotations

import logging
import re
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("legal_ai.completeness_scorer")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DB_DEFAULT: Path = Path(__file__).resolve().parents[1] / "litigation_context.db"

# Dimension weights (must sum to 1.0)
_WEIGHTS: Dict[str, float] = {
    "citation_completeness": 0.15,
    "evidence_linkage": 0.15,
    "placeholder_resolution": 0.15,
    "signature_verification": 0.10,
    "scao_form_compliance": 0.10,
    "argument_completeness": 0.10,
    "service_planning": 0.10,
    "formatting_structure": 0.15,
}

# --- Regex patterns ---

# Placeholders / unresolved markers
_PLACEHOLDER_PATTERNS: List[re.Pattern[str]] = [
    re.compile(r"\[[A-Z][A-Z_]{2,}\]"),          # [PLACEHOLDER], [ANDREW_REQUIRED]
    re.compile(r"\{[A-Z][A-Z_]{2,}\}"),           # {PLACEHOLDER}
    re.compile(r"\[CITATION_NEEDED\]", re.I),
    re.compile(r"\bTODO\b"),
    re.compile(r"\bFIXME\b"),
    re.compile(r"\bTBD\b"),
    re.compile(r"\bXXX\b"),
    re.compile(r"_{3,}"),                          # Long underscore blanks
]

# Michigan legal citation patterns
_CITATION_PATTERNS: Dict[str, re.Pattern[str]] = {
    "mcl": re.compile(r"MCL\s+\d+\.\d+[a-z]?", re.I),
    "mcr": re.compile(r"MCR\s+\d+\.\d+[a-z]?", re.I),
    "mich_app": re.compile(r"\d+\s+Mich\s+App\s+\d+"),
    "mich": re.compile(r"\d+\s+Mich\s+\d+"),
    "nw2d": re.compile(r"\d+\s+NW\s*2d\s+\d+"),
    "fed_supp": re.compile(r"\d+\s+F\s*(?:Supp|\.)\s*(?:2d|3d)?\s+\d+"),
    "us": re.compile(r"\d+\s+U\.?S\.?\s+\d+"),
}

# Michigan case-number format: YYYY-NNNNNN-XX
_CASE_NUMBER_RE = re.compile(r"\b\d{4}-\d{6}-[A-Z]{2}\b")

# Signature / verification markers
_SIGNATURE_PATTERNS: Dict[str, re.Pattern[str]] = {
    "signature_line": re.compile(r"/s/\s*\w+", re.I),
    "respectfully": re.compile(r"Respectfully\s+submitted", re.I),
    "date_line": re.compile(r"Date:\s*\S+", re.I),
    "verification": re.compile(
        r"(?:under\s+(?:penalty\s+of\s+perjury|oath))|"
        r"(?:I\s+(?:swear|affirm|declare))",
        re.I,
    ),
}

# Service-related markers
_SERVICE_PATTERNS: List[re.Pattern[str]] = [
    re.compile(r"Certificate\s+of\s+Service", re.I),
    re.compile(r"Proof\s+of\s+Service", re.I),
    re.compile(r"I\s+hereby\s+certify", re.I),
    re.compile(r"served\s+(?:a\s+copy|upon|on)", re.I),
]

# Formatting / structure markers
_CAPTION_PATTERNS: List[re.Pattern[str]] = [
    re.compile(r"STATE\s+OF\s+MICHIGAN", re.I),
    re.compile(r"(?:CIRCUIT|DISTRICT|PROBATE)\s+COURT", re.I),
    re.compile(r"(?:Plaintiff|Petitioner)", re.I),
    re.compile(r"(?:Defendant|Respondent)", re.I),
    re.compile(r"Case\s+No\.?\s*:?\s*\d{4}-\d{6}", re.I),
    re.compile(r"Hon(?:orable)?\.?\s+\w+", re.I),
]

_HEADING_RE = re.compile(
    r"^(?:[IVX]+\.|[A-Z]\.|(?:\d+\.)+)\s+[A-Z]",
    re.MULTILINE,
)

_PAGE_NUMBER_RE = re.compile(r"(?:Page|Pg\.?)\s+\d+\s+of\s+\d+", re.I)

# Filing-type keywords expected in arguments
_FILING_KEYWORDS: Dict[str, List[str]] = {
    "motion": [
        "relief requested",
        "grounds",
        "legal standard",
        "facts",
        "argument",
        "conclusion",
    ],
    "brief": [
        "statement of facts",
        "issues presented",
        "argument",
        "standard of review",
        "conclusion",
    ],
    "complaint": [
        "parties",
        "jurisdiction",
        "facts",
        "cause of action",
        "prayer for relief",
    ],
    "response": [
        "statement of facts",
        "argument",
        "conclusion",
        "denial",
    ],
    "affidavit": [
        "personal knowledge",
        "swear",
        "subscribed",
    ],
}


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class DimensionScore:
    """Score for a single quality dimension.

    Attributes:
        dimension_name: Human-readable name of the scoring dimension.
        score: Raw score from 0 to 100 for this dimension.
        max_points: Weight of this dimension as a percentage of the total.
        issues: List of specific problems found.
        recommendations: Suggested fixes for each issue.
    """

    dimension_name: str
    score: float
    max_points: float
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    @property
    def weighted_score(self) -> float:
        """Return the weighted contribution to the overall score."""
        return self.score * (self.max_points / 100.0)


@dataclass
class CompletenessReport:
    """Aggregate completeness report for a single filing.

    Attributes:
        filing_path: Path to the scored file (empty string for raw text).
        overall_score: Weighted composite score 0-100.
        dimensions: Per-dimension breakdown.
        grade: Letter grade A-F.
        critical_issues: Issues that block filing regardless of score.
        filing_ready: True only when grade >= C **and** no critical issues.
        scored_at: UTC timestamp of when scoring was performed.
    """

    filing_path: str = ""
    overall_score: float = 0.0
    dimensions: List[DimensionScore] = field(default_factory=list)
    grade: str = "F"
    critical_issues: List[str] = field(default_factory=list)
    filing_ready: bool = False
    scored_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the report to a plain dictionary."""
        return {
            "filing_path": self.filing_path,
            "overall_score": round(self.overall_score, 2),
            "grade": self.grade,
            "filing_ready": self.filing_ready,
            "critical_issues": list(self.critical_issues),
            "scored_at": self.scored_at,
            "dimensions": [
                {
                    "name": d.dimension_name,
                    "score": round(d.score, 2),
                    "weighted": round(d.weighted_score, 2),
                    "max_points": d.max_points,
                    "issues": list(d.issues),
                    "recommendations": list(d.recommendations),
                }
                for d in self.dimensions
            ],
        }


# ---------------------------------------------------------------------------
# Errors (extend LitigationOS hierarchy when available)
# ---------------------------------------------------------------------------

try:
    import sys as _sys

    _exceptions_dir = str(Path(__file__).resolve().parents[1])
    if _exceptions_dir not in _sys.path:
        _sys.path.insert(0, _exceptions_dir)
    from exceptions import ApplicationError as _AppBase  # type: ignore[import-untyped]
except ImportError:
    class _AppBase(Exception):  # type: ignore[no-redef]
        """Fallback base when exceptions.py is not on the path."""

        def __init__(
            self,
            message: str,
            code: Optional[str] = None,
            details: Optional[Dict[str, Any]] = None,
        ) -> None:
            super().__init__(message)
            self.code = code
            self.details = details or {}


class ScoringError(_AppBase):
    """Raised when the scoring engine encounters an unrecoverable error."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, code="SCORING_ERROR", **kwargs)


# ---------------------------------------------------------------------------
# Main scorer
# ---------------------------------------------------------------------------

class CompletenessScorer:
    """Score court filings 0-100 across eight quality dimensions.

    The scorer works on plain text (extracted from PDF/DOCX upstream).
    When a ``litigation_context.db`` is available it cross-references
    citations against ``caselaw_unified`` and evidence against
    ``evidence_quotes``; missing tables are silently skipped.

    Args:
        db_path: Optional override for the SQLite database path.
                 Defaults to ``00_SYSTEM/litigation_context.db``.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        self._db_path: Path = Path(db_path) if db_path else _DB_DEFAULT
        self._db_available: bool = self._db_path.exists()
        self._scores_computed: int = 0

        if not self._db_available:
            logger.warning(
                "Database not found at %s — DB-backed checks will be skipped.",
                self._db_path,
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score_filing(
        self,
        text: str,
        filing_type: str = "motion",
    ) -> CompletenessReport:
        """Score a filing's text and return a full completeness report.

        Args:
            text: The full plain-text content of the filing.
            filing_type: One of ``motion``, ``brief``, ``complaint``,
                         ``response``, or ``affidavit``.

        Returns:
            A :class:`CompletenessReport` with per-dimension scores,
            a composite score, letter grade, and readiness flag.

        Raises:
            ScoringError: If *text* is empty or scoring fails unexpectedly.
        """
        if not text or not text.strip():
            raise ScoringError("Cannot score an empty filing.")

        filing_type = filing_type.lower().strip()
        text_lower = text.lower()

        dimensions: List[DimensionScore] = [
            self._score_citations(text, text_lower),
            self._score_evidence_linkage(text, text_lower),
            self._score_placeholders(text),
            self._score_signatures(text, text_lower, filing_type),
            self._score_scao_compliance(text, text_lower),
            self._score_arguments(text, text_lower, filing_type),
            self._score_service(text, text_lower),
            self._score_formatting(text, text_lower),
        ]

        overall = sum(d.weighted_score for d in dimensions)
        overall = max(0.0, min(100.0, overall))
        grade = _letter_grade(overall)

        critical: List[str] = []
        for dim in dimensions:
            for issue in dim.issues:
                if _is_critical(issue):
                    critical.append(issue)

        filing_ready = grade in ("A", "B", "C") and len(critical) == 0

        self._scores_computed += 1

        return CompletenessReport(
            filing_path="",
            overall_score=overall,
            dimensions=dimensions,
            grade=grade,
            critical_issues=critical,
            filing_ready=filing_ready,
        )

    def score_file(self, file_path: str) -> CompletenessReport:
        """Read a file from disk and score its contents.

        Supports ``.txt``, ``.md``, and similar plain-text formats.
        For PDF/DOCX the caller should extract text first.

        Args:
            file_path: Path to the filing on disk.

        Returns:
            A :class:`CompletenessReport` with ``filing_path`` populated.

        Raises:
            ScoringError: If the file cannot be read.
        """
        p = Path(file_path)
        if not p.exists():
            raise ScoringError(f"File not found: {file_path}")

        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            raise ScoringError(f"Cannot read {file_path}: {exc}") from exc

        filing_type = _infer_filing_type(p.stem, text)
        report = self.score_filing(text, filing_type=filing_type)
        report.filing_path = str(p.resolve())
        return report

    def score_batch(self, file_paths: List[str]) -> List[CompletenessReport]:
        """Score multiple files and return reports in the same order.

        Files that fail to read produce a report with score 0 and the
        error recorded as a critical issue.

        Args:
            file_paths: List of paths to score.

        Returns:
            A list of :class:`CompletenessReport` objects, one per path.
        """
        results: List[CompletenessReport] = []
        for fp in file_paths:
            try:
                results.append(self.score_file(fp))
            except ScoringError as exc:
                results.append(
                    CompletenessReport(
                        filing_path=str(fp),
                        overall_score=0.0,
                        grade="F",
                        critical_issues=[str(exc)],
                        filing_ready=False,
                    )
                )
        return results

    def get_stats(self) -> Dict[str, Any]:
        """Return operational statistics for this scorer instance.

        Returns:
            Dictionary with engine metadata and database availability.
        """
        db_tables: List[str] = []
        if self._db_available:
            try:
                with self._connect() as conn:
                    rows = conn.execute(
                        "SELECT name FROM sqlite_master "
                        "WHERE type='table' ORDER BY name"
                    ).fetchall()
                    db_tables = [r[0] for r in rows]
            except sqlite3.Error:
                pass

        return {
            "scores_computed": self._scores_computed,
            "db_path": str(self._db_path),
            "db_available": self._db_available,
            "db_tables_found": db_tables,
            "dimensions": list(_WEIGHTS.keys()),
            "weights": dict(_WEIGHTS),
        }

    # ------------------------------------------------------------------
    # Database helpers
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        """Open a WAL-mode connection with standard LitigationOS PRAGMAs."""
        conn = sqlite3.connect(
            str(self._db_path),
            timeout=30.0,
        )
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=60000")
        conn.execute("PRAGMA cache_size=-32000")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.row_factory = sqlite3.Row
        return conn

    def _table_exists(self, conn: sqlite3.Connection, table: str) -> bool:
        """Check whether *table* exists in the connected database."""
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        ).fetchone()
        return row is not None

    def _verify_citations_in_db(
        self, citations: List[str]
    ) -> Tuple[int, int]:
        """Cross-reference extracted citations against the database.

        Returns:
            A tuple of (verified_count, total_count).
        """
        if not citations or not self._db_available:
            return 0, len(citations)

        verified = 0
        try:
            with self._connect() as conn:
                # Try multiple likely table names
                for table in ("caselaw_unified", "court_rules", "rules_text"):
                    if not self._table_exists(conn, table):
                        continue
                    cols = [
                        r[1]
                        for r in conn.execute(
                            f"PRAGMA table_info({table})"
                        ).fetchall()
                    ]
                    # Pick a text column to search
                    search_col = None
                    for candidate in ("citation", "rule", "context", "text_content"):
                        if candidate in cols:
                            search_col = candidate
                            break
                    if search_col is None:
                        continue

                    for cite in citations:
                        normalized = cite.strip()
                        row = conn.execute(
                            f"SELECT 1 FROM {table} "
                            f"WHERE {search_col} LIKE ? LIMIT 1",
                            (f"%{normalized}%",),
                        ).fetchone()
                        if row:
                            verified += 1
                    break  # Use first available table
        except sqlite3.Error as exc:
            logger.debug("DB citation check failed: %s", exc)

        return verified, len(citations)

    def _check_evidence_linkage_db(
        self, claim_refs: List[str]
    ) -> Tuple[int, int]:
        """Check whether referenced claims have evidence in the database.

        Returns:
            A tuple of (linked_count, total_count).
        """
        if not claim_refs or not self._db_available:
            return 0, len(claim_refs)

        linked = 0
        try:
            with self._connect() as conn:
                for table in ("evidence_quotes", "documents", "pages"):
                    if not self._table_exists(conn, table):
                        continue
                    cols = [
                        r[1]
                        for r in conn.execute(
                            f"PRAGMA table_info({table})"
                        ).fetchall()
                    ]
                    search_col = None
                    for candidate in ("claim_id", "text_content", "file_name"):
                        if candidate in cols:
                            search_col = candidate
                            break
                    if search_col is None:
                        continue

                    for ref in claim_refs:
                        row = conn.execute(
                            f"SELECT 1 FROM {table} "
                            f"WHERE {search_col} LIKE ? LIMIT 1",
                            (f"%{ref.strip()}%",),
                        ).fetchone()
                        if row:
                            linked += 1
                    break
        except sqlite3.Error as exc:
            logger.debug("DB evidence check failed: %s", exc)

        return linked, len(claim_refs)

    # ------------------------------------------------------------------
    # Dimension scorers (private)
    # ------------------------------------------------------------------

    def _score_citations(
        self, text: str, text_lower: str
    ) -> DimensionScore:
        """Dimension 1: Citation Completeness (15%).

        Checks that the filing contains legal citations and, when possible,
        verifies them against the litigation database.
        """
        issues: List[str] = []
        recommendations: List[str] = []

        all_citations: List[str] = []
        for name, pattern in _CITATION_PATTERNS.items():
            all_citations.extend(pattern.findall(text))

        if not all_citations:
            issues.append("CRITICAL: No legal citations found in filing.")
            recommendations.append(
                "Add Michigan citations (MCL, MCR, Mich App, NW2d)."
            )
            return DimensionScore(
                dimension_name="Citation Completeness",
                score=0.0,
                max_points=15.0,
                issues=issues,
                recommendations=recommendations,
            )

        unique_citations = list(dict.fromkeys(all_citations))
        score = min(100.0, len(unique_citations) * 15.0)

        # Check MCR presence specifically
        mcr_cites = _CITATION_PATTERNS["mcr"].findall(text)
        if not mcr_cites:
            issues.append("No Michigan Court Rules (MCR) citations found.")
            recommendations.append(
                "Include applicable MCR citations for procedural authority."
            )
            score = max(score - 15.0, 0.0)

        # DB verification
        verified, total = self._verify_citations_in_db(unique_citations)
        if total > 0 and verified == 0 and self._db_available:
            issues.append(
                f"None of {total} citations verified in database."
            )
            recommendations.append(
                "Verify citations against official reporters."
            )
            score = max(score - 10.0, 0.0)
        elif total > 0 and verified < total and self._db_available:
            unverified = total - verified
            issues.append(
                f"{unverified} of {total} citations not found in database."
            )
            recommendations.append(
                "Cross-check unverified citations for accuracy."
            )
            score = max(score - 5.0, 0.0)

        return DimensionScore(
            dimension_name="Citation Completeness",
            score=min(score, 100.0),
            max_points=15.0,
            issues=issues,
            recommendations=recommendations,
        )

    def _score_evidence_linkage(
        self, text: str, text_lower: str
    ) -> DimensionScore:
        """Dimension 2: Evidence Linkage (15%).

        Every factual claim should reference supporting evidence
        (exhibits, attachments, or testimony).
        """
        issues: List[str] = []
        recommendations: List[str] = []

        exhibit_refs = re.findall(
            r"(?:Exhibit|Ex\.?|Attachment)\s+[A-Z0-9]+", text, re.I
        )
        see_refs = re.findall(r"\((?:See|see)\s+[^)]+\)", text)
        record_refs = re.findall(r"(?:Tr|Record|R)\.\s+(?:at\s+)?\d+", text)
        all_refs = exhibit_refs + see_refs + record_refs

        # Count factual assertions (sentences with names / dates / facts)
        sentences = re.split(r"[.!?]+", text)
        factual = [
            s
            for s in sentences
            if re.search(r"\b(?:on|dated?|occurred|stated|testified|said)\b", s, re.I)
        ]

        if not all_refs and factual:
            issues.append(
                "CRITICAL: Factual assertions found but no evidence references."
            )
            recommendations.append(
                "Add exhibit references (Exhibit A, Ex. 1) for each factual claim."
            )
            return DimensionScore(
                dimension_name="Evidence Linkage",
                score=0.0,
                max_points=15.0,
                issues=issues,
                recommendations=recommendations,
            )

        if not factual:
            # No factual assertions detected — likely procedural filing
            score = 80.0
            if not all_refs:
                issues.append("No evidence references found (may be acceptable for procedural filings).")
                score = 70.0
        else:
            ratio = len(all_refs) / max(len(factual), 1)
            score = min(100.0, ratio * 100.0)
            if ratio < 0.3:
                issues.append(
                    f"Low evidence coverage: {len(all_refs)} references "
                    f"for {len(factual)} factual assertions."
                )
                recommendations.append(
                    "Add supporting exhibit or record citations for each factual claim."
                )

        # DB cross-check
        claim_refs = [r.strip() for r in exhibit_refs[:20]]
        linked, total = self._check_evidence_linkage_db(claim_refs)
        if total > 0 and linked < total and self._db_available:
            issues.append(
                f"{total - linked} of {total} exhibit references "
                "not found in evidence database."
            )
            recommendations.append(
                "Ensure all referenced exhibits are ingested into the system."
            )
            score = max(score - 10.0, 0.0)

        return DimensionScore(
            dimension_name="Evidence Linkage",
            score=min(score, 100.0),
            max_points=15.0,
            issues=issues,
            recommendations=recommendations,
        )

    def _score_placeholders(self, text: str) -> DimensionScore:
        """Dimension 3: Placeholder Resolution (15%).

        Scans for unresolved placeholder markers that indicate the filing
        is still in draft form.
        """
        issues: List[str] = []
        recommendations: List[str] = []
        found: List[str] = []

        for pattern in _PLACEHOLDER_PATTERNS:
            matches = pattern.findall(text)
            found.extend(matches)

        if not found:
            return DimensionScore(
                dimension_name="Placeholder Resolution",
                score=100.0,
                max_points=15.0,
                issues=issues,
                recommendations=recommendations,
            )

        unique = list(dict.fromkeys(found))
        count = len(found)

        # Each placeholder is a significant deduction
        score = max(0.0, 100.0 - (count * 20.0))

        # Any placeholder with CRITICAL or REQUIRED is a critical issue
        for ph in unique[:10]:
            ph_str = str(ph).strip()
            if re.search(r"(?:REQUIRED|CRITICAL|NEEDED)", ph_str, re.I):
                issues.append(f"CRITICAL: Unresolved required placeholder: {ph_str}")
            else:
                issues.append(f"Unresolved placeholder: {ph_str}")

        if count > 10:
            issues.append(f"... and {count - 10} more placeholders.")

        recommendations.append(
            f"Resolve all {count} placeholder(s) before filing."
        )

        return DimensionScore(
            dimension_name="Placeholder Resolution",
            score=score,
            max_points=15.0,
            issues=issues,
            recommendations=recommendations,
        )

    def _score_signatures(
        self, text: str, text_lower: str, filing_type: str
    ) -> DimensionScore:
        """Dimension 4: Signature / Verification (10%).

        Checks for signature block, date line, and (where required)
        verification under oath.
        """
        issues: List[str] = []
        recommendations: List[str] = []
        score = 100.0

        has_signature = bool(_SIGNATURE_PATTERNS["signature_line"].search(text))
        has_respectfully = bool(_SIGNATURE_PATTERNS["respectfully"].search(text))
        has_date = bool(_SIGNATURE_PATTERNS["date_line"].search(text))
        has_verification = bool(_SIGNATURE_PATTERNS["verification"].search(text))

        if not has_signature:
            issues.append("CRITICAL: No signature line (/s/ Name) found.")
            recommendations.append("Add a signature block: /s/ Andrew Pigors")
            score -= 40.0

        if not has_date:
            issues.append("No date line found.")
            recommendations.append("Add 'Date: YYYY-MM-DD' near the signature.")
            score -= 20.0

        if not has_respectfully:
            issues.append("Missing 'Respectfully submitted' closing.")
            recommendations.append(
                "Add 'Respectfully submitted,' before the signature block."
            )
            score -= 10.0

        # Affidavits and declarations require verification under oath
        if filing_type in ("affidavit", "declaration") and not has_verification:
            issues.append(
                "CRITICAL: Affidavit/declaration lacks verification under oath."
            )
            recommendations.append(
                "Add verification language: 'I declare under penalty of perjury...'"
            )
            score -= 30.0

        return DimensionScore(
            dimension_name="Signature / Verification",
            score=max(score, 0.0),
            max_points=10.0,
            issues=issues,
            recommendations=recommendations,
        )

    def _score_scao_compliance(
        self, text: str, text_lower: str
    ) -> DimensionScore:
        """Dimension 5: SCAO Form Compliance (10%).

        Michigan SCAO forms require specific case-number formats and
        standard identifying information.
        """
        issues: List[str] = []
        recommendations: List[str] = []
        score = 100.0

        # Case number format: YYYY-NNNNNN-XX
        case_numbers = _CASE_NUMBER_RE.findall(text)
        if not case_numbers:
            issues.append("CRITICAL: No Michigan case number (YYYY-NNNNNN-XX) found.")
            recommendations.append(
                "Include case number in format: 2024-001507-DC"
            )
            score -= 40.0

        # Verify case-number year is plausible (2000-2099)
        for cn in case_numbers:
            year = int(cn[:4])
            if year < 2000 or year > 2099:
                issues.append(f"Suspicious case-number year: {cn}")
                score -= 5.0

        # Court name
        has_court = bool(
            re.search(
                r"(?:Circuit|District|Probate|Family)\s+(?:Court|Division)",
                text,
                re.I,
            )
        )
        if not has_court:
            issues.append("No Michigan court name found in caption.")
            recommendations.append(
                "Include the full court name (e.g., 14th Circuit Court)."
            )
            score -= 15.0

        # County
        has_county = bool(
            re.search(r"County\s+of\s+\w+|(\w+)\s+County", text, re.I)
        )
        if not has_county:
            issues.append("No county designation found.")
            recommendations.append("Add 'County of Muskegon' (or applicable county).")
            score -= 10.0

        # Judge name must not be blank
        judge_match = re.search(
            r"Hon(?:orable)?\.?\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            text,
        )
        if not judge_match:
            blank_judge = re.search(r"Hon(?:orable)?\.?\s*:?\s*$", text, re.M)
            if blank_judge:
                issues.append("CRITICAL: Judge name line is blank.")
                recommendations.append("Fill in the assigned judge's name.")
                score -= 20.0
            else:
                issues.append("No judge designation (Hon.) found.")
                recommendations.append("Add 'Hon. [Judge Name]' to caption.")
                score -= 10.0

        # SCAO form number (e.g., MC 01, DC 100, CC 375)
        scao_form = re.search(
            r"\b(?:MC|DC|CC|FOC|COA|PC|JC)\s*\d{1,4}[a-z]?\b", text, re.I
        )
        if scao_form:
            score = min(score + 5.0, 100.0)  # Bonus for explicit form number

        return DimensionScore(
            dimension_name="SCAO Form Compliance",
            score=max(score, 0.0),
            max_points=10.0,
            issues=issues,
            recommendations=recommendations,
        )

    def _score_arguments(
        self, text: str, text_lower: str, filing_type: str
    ) -> DimensionScore:
        """Dimension 6: Argument Completeness (10%).

        Checks that the filing's legal arguments address the expected
        structural elements for its type.
        """
        issues: List[str] = []
        recommendations: List[str] = []

        keywords = _FILING_KEYWORDS.get(filing_type, _FILING_KEYWORDS["motion"])
        present = 0

        for kw in keywords:
            if kw.lower() in text_lower:
                present += 1

        total = len(keywords)
        ratio = present / max(total, 1)
        score = ratio * 100.0

        missing = [kw for kw in keywords if kw.lower() not in text_lower]
        if missing:
            issues.append(
                f"Missing expected sections for '{filing_type}': "
                + ", ".join(missing)
            )
            recommendations.append(
                f"Add sections: {', '.join(missing)}"
            )

        # Check for legal standard / standard of review
        if filing_type in ("motion", "brief"):
            has_standard = bool(
                re.search(
                    r"(?:legal\s+standard|standard\s+of\s+review|burden\s+of\s+proof)",
                    text_lower,
                )
            )
            if not has_standard:
                issues.append("No legal standard or standard of review stated.")
                recommendations.append(
                    "State the applicable legal standard or standard of review."
                )
                score = max(score - 10.0, 0.0)

        # Word count sanity — very short filings are suspect
        word_count = len(text.split())
        if word_count < 200:
            issues.append(
                f"Filing is very short ({word_count} words) — "
                "arguments may be incomplete."
            )
            recommendations.append(
                "Expand arguments to fully address all elements."
            )
            score = max(score - 15.0, 0.0)

        return DimensionScore(
            dimension_name="Argument Completeness",
            score=min(max(score, 0.0), 100.0),
            max_points=10.0,
            issues=issues,
            recommendations=recommendations,
        )

    def _score_service(
        self, text: str, text_lower: str
    ) -> DimensionScore:
        """Dimension 7: Service Planning (10%).

        Checks for certificate of service, named recipients, and
        service method.
        """
        issues: List[str] = []
        recommendations: List[str] = []

        has_service = any(p.search(text) for p in _SERVICE_PATTERNS)

        if not has_service:
            issues.append("CRITICAL: No Certificate of Service found.")
            recommendations.append(
                "Add a Certificate of Service listing all parties served."
            )
            return DimensionScore(
                dimension_name="Service Planning",
                score=0.0,
                max_points=10.0,
                issues=issues,
                recommendations=recommendations,
            )

        score = 60.0  # Base for having a service section

        # Service method
        methods = re.findall(
            r"(?:first[- ]class\s+mail|electronic|e-?mail|hand[- ]deliver|personal\s+service)",
            text_lower,
        )
        if methods:
            score += 15.0
        else:
            issues.append("Service method not specified.")
            recommendations.append(
                "Specify service method (e.g., first-class mail, electronic service)."
            )

        # Recipient names / addresses
        address_hint = bool(
            re.search(
                r"\d{3,5}\s+\w+\s+(?:St|Ave|Blvd|Dr|Rd|Ln|Ct)",
                text,
            )
        )
        if address_hint:
            score += 15.0
        else:
            issues.append("No recipient address detected in service certificate.")
            recommendations.append(
                "Include full mailing addresses for all served parties."
            )

        # Date of service
        service_date = re.search(
            r"(?:served|mailed|delivered)\s+(?:on\s+)?(?:\w+\s+\d{1,2},?\s+\d{4}|\d{1,2}/\d{1,2}/\d{4})",
            text_lower,
        )
        if service_date:
            score += 10.0
        else:
            issues.append("Date of service not specified.")
            recommendations.append("Include the date of service.")

        return DimensionScore(
            dimension_name="Service Planning",
            score=min(score, 100.0),
            max_points=10.0,
            issues=issues,
            recommendations=recommendations,
        )

    def _score_formatting(
        self, text: str, text_lower: str
    ) -> DimensionScore:
        """Dimension 8: Formatting / Structure (15%).

        Checks for proper caption, heading hierarchy, and page-numbering
        markers in the filing text.
        """
        issues: List[str] = []
        recommendations: List[str] = []
        score = 100.0

        # Caption elements
        caption_hits = sum(
            1 for p in _CAPTION_PATTERNS if p.search(text)
        )
        caption_ratio = caption_hits / max(len(_CAPTION_PATTERNS), 1)
        if caption_ratio < 0.5:
            missing_count = len(_CAPTION_PATTERNS) - caption_hits
            issues.append(
                f"Caption is incomplete — {missing_count} of "
                f"{len(_CAPTION_PATTERNS)} expected elements missing."
            )
            recommendations.append(
                "Ensure caption includes: State, Court, Parties, Case No., Judge."
            )
            score -= (1.0 - caption_ratio) * 30.0

        # Heading hierarchy
        headings = _HEADING_RE.findall(text)
        if not headings:
            issues.append("No structured headings (I., A., 1.) found.")
            recommendations.append(
                "Add numbered or lettered headings to organize arguments."
            )
            score -= 20.0

        # Page numbering
        has_page_nums = bool(_PAGE_NUMBER_RE.search(text))
        if not has_page_nums:
            issues.append("No page numbering markers found.")
            recommendations.append(
                "Add 'Page X of Y' footer markers."
            )
            score -= 10.0

        # Title / header
        first_500 = text[:500]
        title_patterns = [
            r"MOTION",
            r"BRIEF",
            r"COMPLAINT",
            r"RESPONSE",
            r"AFFIDAVIT",
            r"PETITION",
            r"ORDER",
        ]
        has_title = any(
            re.search(p, first_500, re.I) for p in title_patterns
        )
        if not has_title:
            issues.append("No filing title found in the first 500 characters.")
            recommendations.append(
                "Add a clear title (e.g., 'MOTION FOR ...')."
            )
            score -= 15.0

        # Line spacing / readability heuristic
        lines = text.split("\n")
        non_empty = [ln for ln in lines if ln.strip()]
        if len(non_empty) > 10:
            avg_len = sum(len(ln) for ln in non_empty) / len(non_empty)
            if avg_len > 200:
                issues.append(
                    "Very long lines detected — filing may lack proper formatting."
                )
                recommendations.append(
                    "Use line lengths under 80-120 characters for readability."
                )
                score -= 10.0

        return DimensionScore(
            dimension_name="Formatting / Structure",
            score=max(score, 0.0),
            max_points=15.0,
            issues=issues,
            recommendations=recommendations,
        )


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _letter_grade(score: float) -> str:
    """Convert a numeric 0-100 score to a letter grade."""
    if score >= 90.0:
        return "A"
    if score >= 80.0:
        return "B"
    if score >= 70.0:
        return "C"
    if score >= 60.0:
        return "D"
    return "F"


def _is_critical(issue_text: str) -> bool:
    """Return True if *issue_text* describes a critical filing defect."""
    return issue_text.startswith("CRITICAL:")


def _infer_filing_type(stem: str, text: str) -> str:
    """Best-effort inference of filing type from filename or content."""
    stem_lower = stem.lower()
    text_start = text[:1000].lower()

    type_map = [
        ("motion", ["motion"]),
        ("brief", ["brief", "memorandum"]),
        ("complaint", ["complaint"]),
        ("response", ["response", "answer", "reply"]),
        ("affidavit", ["affidavit", "declaration"]),
    ]
    for ftype, keywords in type_map:
        for kw in keywords:
            if kw in stem_lower or kw in text_start:
                return ftype
    return "motion"


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    sys.stdout = open(  # noqa: SIM115
        sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace"
    )

    if len(sys.argv) < 2:
        print("Usage: python completeness_scorer.py <file_path> [filing_type]")
        sys.exit(1)

    target = sys.argv[1]
    ftype = sys.argv[2] if len(sys.argv) > 2 else "motion"

    scorer = CompletenessScorer()

    if Path(target).is_file():
        report = scorer.score_file(target)
    else:
        report = scorer.score_filing(target, filing_type=ftype)

    print(f"\n{'=' * 60}")
    print(f"  Filing Completeness Report")
    print(f"{'=' * 60}")
    print(f"  File:   {report.filing_path or '(raw text)'}")
    print(f"  Score:  {report.overall_score:.1f}/100")
    print(f"  Grade:  {report.grade}")
    print(f"  Ready:  {'YES' if report.filing_ready else 'NO'}")
    print(f"{'=' * 60}")

    for dim in report.dimensions:
        bar = "█" * int(dim.score / 5) + "░" * (20 - int(dim.score / 5))
        print(f"  {dim.dimension_name:<28} {dim.score:5.1f}  {bar}")
        for issue in dim.issues:
            print(f"    ⚠ {issue}")
        for rec in dim.recommendations:
            print(f"    → {rec}")

    if report.critical_issues:
        print(f"\n  🚨 CRITICAL ISSUES ({len(report.critical_issues)}):")
        for ci in report.critical_issues:
            print(f"    • {ci}")

    print()
