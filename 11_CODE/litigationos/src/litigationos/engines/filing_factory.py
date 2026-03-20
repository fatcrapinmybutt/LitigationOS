"""Autonomous Filing Factory — end-to-end filing generation pipeline.

Orchestrates the full filing lifecycle from draft creation through QA
validation and court-ready export.  Works alongside :class:`FilingEngine`
(CRUD / stack assembly) and :class:`DocumentEngine` (template rendering)
to provide a single ``generate_filing()`` entry-point that produces
complete, MCR-compliant court filings.

State machine::

    DRAFT → REVIEW → QA_PASS → READY → FILED → SERVED
                   ↓
               QA_FAIL → FIX → REVIEW  (loop)
"""

from __future__ import annotations

import enum
import hashlib
import logging
import re
import textwrap
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Sequence

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from litigationos.db.connection import DatabaseManager

logger = logging.getLogger(__name__)

# -- Enums & constants -------------------------------------------------------

class FilingType(str, enum.Enum):
    """Supported filing types."""
    MOTION = "motion"
    BRIEF = "brief"
    COMPLAINT = "complaint"
    AFFIDAVIT = "affidavit"
    PROPOSED_ORDER = "proposed_order"
    COS = "certificate_of_service"
    NOTICE = "notice"
    SUBPOENA = "subpoena"
    DEPOSITION_NOTICE = "deposition_notice"
    INTERROGATORIES = "interrogatories"
    RFP = "request_for_production"
    RFA = "request_for_admissions"
    EXHIBIT_INDEX = "exhibit_index"


class FilingStatus(str, enum.Enum):
    """Filing state-machine states."""
    DRAFT = "draft"
    REVIEW = "review"
    QA_PASS = "qa_pass"
    QA_FAIL = "qa_fail"
    FIX = "fix"
    READY = "ready"
    FILED = "filed"
    SERVED = "served"


# Allowed transitions: current → set of valid next states
_TRANSITIONS: dict[FilingStatus, set[FilingStatus]] = {
    FilingStatus.DRAFT:   {FilingStatus.REVIEW},
    FilingStatus.REVIEW:  {FilingStatus.QA_PASS, FilingStatus.QA_FAIL},
    FilingStatus.QA_PASS: {FilingStatus.READY},
    FilingStatus.QA_FAIL: {FilingStatus.FIX},
    FilingStatus.FIX:     {FilingStatus.REVIEW},
    FilingStatus.READY:   {FilingStatus.FILED},
    FilingStatus.FILED:   {FilingStatus.SERVED},
    FilingStatus.SERVED:  set(),
}

MCR_FORMAT = {
    "margin_inches": 1.0,
    "font": "Times New Roman",
    "font_size_pt": 12,
    "line_spacing": 2.0,
}

PAGE_LIMITS: dict[str, int] = {
    "motion": 20, "brief": 50, "complaint": 100, "affidavit": 20,
    "proposed_order": 5, "certificate_of_service": 3, "notice": 5,
    "subpoena": 10, "deposition_notice": 10, "interrogatories": 30,
    "request_for_production": 30, "request_for_admissions": 30,
    "exhibit_index": 20,
}

WORD_LIMITS: dict[str, int] = {"motion": 6_000, "brief": 16_000, "complaint": 30_000}

_PLACEHOLDER_RE = re.compile(
    r"\[ANDREW_REQUIRED\]|\[INSERT[^\]]*\]|\{\{[^}]+\}\}"
    r"|\[TODO[^\]]*\]|\[FILL[^\]]*\]|\[XX+\]",
    re.IGNORECASE,
)
_CITATION_RE = re.compile(r"\b(?:MCR|MCL|FRCP|FRE|USC|CFR)\s+\d+[\.\(\)a-zA-Z\d\-]*")

# -- Pydantic models ---------------------------------------------------------

class CaptionInfo(BaseModel):
    """Court caption details for document headers."""
    court_name: str
    case_number: str
    judge_name: Optional[str] = None
    plaintiff: str
    defendant: str
    filing_title: str
    case_type: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class QAIssue(BaseModel):
    """A single QA finding."""
    severity: str  # "error", "warning", "info"
    category: str
    message: str
    location: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class QAReport(BaseModel):
    """Complete QA pipeline result."""
    filing_id: int
    status: str  # "pass", "fail"
    score: int = 0
    issues: list[QAIssue] = Field(default_factory=list)
    checked_at: Optional[datetime] = Field(default_factory=datetime.now)
    model_config = ConfigDict(from_attributes=True)

    @property
    def errors(self) -> list[QAIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[QAIssue]:
        return [i for i in self.issues if i.severity == "warning"]


class FilingSpec(BaseModel):
    """Input specification for generating a filing."""
    case_id: int
    filing_type: FilingType
    court: str
    title: str
    caption: Optional[CaptionInfo] = None
    body_text: Optional[str] = None
    exhibit_ids: list[int] = Field(default_factory=list)
    template_name: Optional[str] = None
    template_vars: dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

# -- Dataclasses -------------------------------------------------------------

@dataclass
class GeneratedFiling:
    """Output of the filing factory pipeline."""
    filing_id: int
    case_id: int
    filing_type: str
    status: FilingStatus
    title: str
    body: str
    caption_text: str
    cos_text: str
    word_count: int
    page_estimate: int
    sha256: str
    qa_report: Optional[QAReport] = None
    file_path: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """Serialise to a plain dict."""
        return {
            "filing_id": self.filing_id, "case_id": self.case_id,
            "filing_type": self.filing_type, "status": self.status.value,
            "title": self.title, "body": self.body,
            "caption_text": self.caption_text, "cos_text": self.cos_text,
            "word_count": self.word_count, "page_estimate": self.page_estimate,
            "sha256": self.sha256,
            "qa_report": self.qa_report.model_dump() if self.qa_report else None,
            "file_path": self.file_path, "created_at": self.created_at,
        }


@dataclass
class PacketManifest:
    """Manifest for a complete filing packet."""
    packet_id: str
    case_id: int
    filings: list[GeneratedFiling] = field(default_factory=list)
    exhibit_paths: list[str] = field(default_factory=list)
    assembled_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def all_passed(self) -> bool:
        """True when every filing in the packet passed QA."""
        return all(
            f.qa_report is not None and f.qa_report.status == "pass"
            for f in self.filings
        )

    def to_dict(self) -> dict:
        return {
            "packet_id": self.packet_id, "case_id": self.case_id,
            "filings": [f.to_dict() for f in self.filings],
            "exhibit_paths": self.exhibit_paths,
            "assembled_at": self.assembled_at, "all_passed": self.all_passed,
        }

# -- Caption & COS generators ------------------------------------------------

_CAPTION_TPL = textwrap.dedent("""\
    STATE OF MICHIGAN
    IN THE {court_name}

    {plaintiff},
        Plaintiff,
                                    Case No. {case_number}
    v.                              Hon. {judge_name}

    {defendant},
        Defendant.
    ______________________________________/

    {filing_title}
""")

_COS_TPL = textwrap.dedent("""\
    CERTIFICATE OF SERVICE

    I hereby certify that on {date}, I served a true copy of the foregoing
    {filing_title} upon the following parties by {method}:

    {parties}

    ____________________________
    {signer}
    Date: {date}
""")


def build_caption(caption: CaptionInfo) -> str:
    """Render a Michigan court caption block."""
    return _CAPTION_TPL.format(
        court_name=caption.court_name.upper(),
        plaintiff=caption.plaintiff,
        defendant=caption.defendant,
        case_number=caption.case_number,
        judge_name=caption.judge_name or "____________________",
        filing_title=caption.filing_title.upper(),
    )


def build_cos(
    filing_title: str,
    parties: Sequence[str],
    signer: str,
    method: str = "electronic filing (MiFile)",
) -> str:
    """Render a Certificate of Service."""
    party_block = "\n    ".join(parties) if parties else "[NO PARTIES LISTED]"
    return _COS_TPL.format(
        date=datetime.now().strftime("%B %d, %Y"),
        filing_title=filing_title,
        method=method,
        parties=party_block,
        signer=signer,
    )

# -- QA pipeline (quality gates) ---------------------------------------------

class QAPipeline:
    """Built-in quality gates for filing validation."""

    def run(self, filing: GeneratedFiling, spec: FilingSpec) -> QAReport:
        """Execute all quality checks and return a :class:`QAReport`."""
        issues: list[QAIssue] = []
        issues.extend(self._check_placeholders(filing.body))
        issues.extend(self._check_citations(filing.body))
        issues.extend(self._check_party_names(filing, spec))
        issues.extend(self._check_case_number(filing, spec))
        issues.extend(self._check_limits(filing))
        issues.extend(self._check_structure(filing))

        errors = [i for i in issues if i.severity == "error"]
        total = 6
        score = int(((total - len(errors)) / total) * 100)
        status = "pass" if not errors else "fail"
        report = QAReport(filing_id=filing.filing_id, status=status, score=score, issues=issues)
        logger.info("QA %s filing %d — score=%d, errors=%d", status.upper(),
                     filing.filing_id, score, len(errors))
        return report

    @staticmethod
    def _check_placeholders(text: str) -> list[QAIssue]:
        """Detect unresolved placeholders."""
        return [
            QAIssue(severity="error", category="placeholder",
                    message=f"Unresolved placeholder: {m.group()!r}",
                    location=f"char {m.start()}")
            for m in _PLACEHOLDER_RE.finditer(text)
        ]

    @staticmethod
    def _check_citations(text: str) -> list[QAIssue]:
        """Verify citation formatting (structural, not hallucination)."""
        issues: list[QAIssue] = []
        cites = _CITATION_RE.findall(text)
        if not cites and len(text) > 500:
            issues.append(QAIssue(severity="warning", category="citation",
                                  message="No citations found in filing >500 chars."))
        for c in cites:
            if re.match(r"^(MCR|MCL|FRCP|FRE|USC|CFR)\s*$", c.strip()):
                issues.append(QAIssue(severity="error", category="citation",
                                      message=f"Incomplete citation: {c.strip()!r}"))
        return issues

    @staticmethod
    def _check_party_names(filing: GeneratedFiling, spec: FilingSpec) -> list[QAIssue]:
        """Ensure caption party names appear consistently in the body."""
        issues: list[QAIssue] = []
        if spec.caption is None:
            return issues
        for party in (spec.caption.plaintiff, spec.caption.defendant):
            token = party.strip().split()[-1] if party.strip() else ""
            if token and token.lower() not in filing.body.lower():
                issues.append(QAIssue(
                    severity="warning", category="party_name",
                    message=f"Party '{party}' (token '{token}') not in body."))
        return issues

    @staticmethod
    def _check_case_number(filing: GeneratedFiling, spec: FilingSpec) -> list[QAIssue]:
        """Validate that the case number appears in the caption."""
        if spec.caption and spec.caption.case_number:
            if spec.caption.case_number not in filing.caption_text:
                return [QAIssue(severity="error", category="case_number",
                                message=f"Case number {spec.caption.case_number!r} missing from caption.")]
        return []

    @staticmethod
    def _check_limits(filing: GeneratedFiling) -> list[QAIssue]:
        """Check word and page count against per-type limits."""
        issues: list[QAIssue] = []
        wl = WORD_LIMITS.get(filing.filing_type)
        if wl and filing.word_count > wl:
            issues.append(QAIssue(
                severity="error", category="word_limit",
                message=f"Word count {filing.word_count:,} exceeds {wl:,} limit."))
        pl = PAGE_LIMITS.get(filing.filing_type)
        if pl and filing.page_estimate > pl:
            issues.append(QAIssue(
                severity="error", category="page_limit",
                message=f"Estimated {filing.page_estimate} pages exceeds {pl}-page limit."))
        return issues

    @staticmethod
    def _check_structure(filing: GeneratedFiling) -> list[QAIssue]:
        """Caption presence, COS presence, and line-length heuristics."""
        issues: list[QAIssue] = []
        if not filing.caption_text or len(filing.caption_text.strip()) < 20:
            issues.append(QAIssue(severity="error", category="caption",
                                  message="Caption block is missing or too short."))
        if not filing.cos_text or "CERTIFICATE OF SERVICE" not in filing.cos_text.upper():
            issues.append(QAIssue(severity="error", category="cos",
                                  message="Certificate of Service is missing or malformed."))
        long = [i for i, ln in enumerate(filing.body.split("\n"), 1) if len(ln) > 120]
        if long:
            issues.append(QAIssue(severity="warning", category="formatting",
                                  message=f"{len(long)} line(s) exceed 120 chars (e.g. {long[:3]})."))
        return issues

# -- Filing Factory (main engine) --------------------------------------------

class FilingFactory:
    """Autonomous filing generation pipeline.

    End-to-end orchestrator that generates, validates, and exports
    court-ready filings.  Integrates with :class:`QAPipeline` for
    quality gates and persists results to the ``filings`` table.
    """

    def __init__(self, db: "DatabaseManager") -> None:
        self._db = db
        self._qa = QAPipeline()

    # -- Primary API ---------------------------------------------------------

    def generate_filing(self, spec: FilingSpec) -> GeneratedFiling:
        """Generate a complete court-ready filing from *spec*.

        Args:
            spec: Describes what to generate (case, type, body/template).

        Returns:
            A :class:`GeneratedFiling` with QA results attached.

        Raises:
            ValueError: If caption info is missing and cannot be inferred.
        """
        logger.info("Generating %s for case %d: %s",
                     spec.filing_type.value, spec.case_id, spec.title)

        caption_info = spec.caption or self._load_caption_from_db(spec)
        caption_text = build_caption(caption_info)
        body = self._render_body(spec)
        parties = self._load_parties(spec.case_id)
        cos_text = build_cos(spec.title, parties, caption_info.plaintiff)

        word_count = len(body.split())
        page_estimate = max(1, word_count // 300)
        full = f"{caption_text}\n\n{body}\n\n{cos_text}"
        sha = hashlib.sha256(full.encode("utf-8")).hexdigest()
        filing_id = self._persist_filing(spec, word_count)

        filing = GeneratedFiling(
            filing_id=filing_id, case_id=spec.case_id,
            filing_type=spec.filing_type.value, status=FilingStatus.DRAFT,
            title=spec.title, body=body, caption_text=caption_text,
            cos_text=cos_text, word_count=word_count,
            page_estimate=page_estimate, sha256=sha,
        )
        filing = self.validate_filing(filing, spec)
        logger.info("Generated filing %d (%s) — %d words, QA %s",
                     filing.filing_id, spec.filing_type.value,
                     word_count, filing.status.value)
        return filing

    def validate_filing(self, filing: GeneratedFiling, spec: FilingSpec) -> GeneratedFiling:
        """Run QA pipeline and advance the state machine accordingly."""
        self._transition(filing, FilingStatus.REVIEW)
        report = self._qa.run(filing, spec)
        filing.qa_report = report
        self._transition(filing, FilingStatus.QA_PASS if report.status == "pass"
                         else FilingStatus.QA_FAIL)
        self._db.execute(
            "UPDATE filings SET status = ?, compliance_score = ? WHERE id = ?",
            (filing.status.value, report.score, filing.filing_id),
        )
        return filing

    def assemble_packet(
        self,
        filings: Sequence[GeneratedFiling],
        *,
        exhibit_paths: Optional[list[str]] = None,
    ) -> PacketManifest:
        """Bundle filings into a court-submission packet with exhibits."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        case_id = filings[0].case_id if filings else 0
        manifest = PacketManifest(
            packet_id=f"PKT-{case_id}-{ts}", case_id=case_id,
            filings=list(filings), exhibit_paths=exhibit_paths or [],
        )
        logger.info("Assembled packet %s — %d filing(s), all_passed=%s",
                     manifest.packet_id, len(filings), manifest.all_passed)
        return manifest

    def export_filing(self, filing: GeneratedFiling, output_dir: str | Path,
                      fmt: str = "markdown") -> Path:
        """Export a filing to disk as markdown (``.md``) or text (``.txt``).

        Raises:
            ValueError: If *fmt* is not ``"markdown"`` or ``"text"``.
        """
        if fmt not in ("markdown", "text"):
            raise ValueError(f"Unsupported format '{fmt}'.")
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        safe = re.sub(r"[^\w\-]+", "_", filing.title)[:80]
        ext = ".md" if fmt == "markdown" else ".txt"
        fp = out / f"{filing.filing_type}_{safe}{ext}"
        sep = "---" if fmt == "markdown" else ("=" * 60)
        fp.write_text("\n\n".join([filing.caption_text, sep, filing.body, sep,
                                   filing.cos_text]), encoding="utf-8")
        filing.file_path = str(fp)
        self._db.execute("UPDATE filings SET file_path = ? WHERE id = ?",
                         (str(fp), filing.filing_id))
        logger.info("Exported filing %d → %s", filing.filing_id, fp)
        return fp

    def advance(self, filing: GeneratedFiling, target: FilingStatus) -> GeneratedFiling:
        """Advance a filing to *target* status, persisting the change.

        Covers mark-ready, mark-filed, mark-served, and send-to-fix in
        a single method.  The state machine enforces valid transitions.

        Args:
            filing: The filing to advance.
            target: Desired next status.

        Returns:
            The filing with updated status.

        Raises:
            ValueError: If the transition is invalid.
        """
        self._transition(filing, target)
        extra = ""
        if target == FilingStatus.FILED:
            extra = ", filed_date = datetime('now')"
        elif target == FilingStatus.SERVED:
            extra = ", served_date = datetime('now')"
        self._db.execute(
            f"UPDATE filings SET status = ?{extra} WHERE id = ?",
            (filing.status.value, filing.filing_id),
        )
        logger.info("Filing %d → %s", filing.filing_id, target.value)
        return filing

    # -- State machine -------------------------------------------------------

    @staticmethod
    def _transition(filing: GeneratedFiling, target: FilingStatus) -> None:
        """Enforce the filing state machine."""
        allowed = _TRANSITIONS.get(filing.status, set())
        if target not in allowed:
            raise ValueError(
                f"Invalid transition: {filing.status.value} → {target.value}. "
                f"Allowed: {sorted(s.value for s in allowed)}"
            )
        filing.status = target

    # -- Internal helpers ----------------------------------------------------

    def _load_caption_from_db(self, spec: FilingSpec) -> CaptionInfo:
        """Derive caption info from the cases/parties tables."""
        case_row = self._db.fetchone("SELECT * FROM cases WHERE id = ?", (spec.case_id,))
        if case_row is None:
            raise ValueError(f"Case {spec.case_id} not found. Provide caption explicitly.")
        case = dict(case_row)
        rows = self._db.fetchall(
            "SELECT name, role FROM parties WHERE case_id = ? ORDER BY role, name",
            (spec.case_id,),
        )
        plaintiff, defendant = "Unknown Plaintiff", "Unknown Defendant"
        for r in rows:
            p = dict(r)
            role = p.get("role", "").lower()
            if role in ("plaintiff", "petitioner"):
                plaintiff = p["name"]
            elif role in ("defendant", "respondent"):
                defendant = p["name"]
        return CaptionInfo(
            court_name=spec.court,
            case_number=case.get("case_number") or "____-______-__",
            judge_name=case.get("judge_name"),
            plaintiff=plaintiff, defendant=defendant,
            filing_title=spec.title, case_type=case.get("case_type"),
        )

    def _render_body(self, spec: FilingSpec) -> str:
        """Return filing body from provided text, template, or placeholder."""
        if spec.body_text:
            return spec.body_text
        if spec.template_name:
            row = self._db.fetchone("SELECT content FROM templates WHERE name = ?",
                                    (spec.template_name,))
            if row is None:
                raise ValueError(f"Template '{spec.template_name}' not found.")
            try:
                import jinja2
                env = jinja2.Environment(undefined=jinja2.StrictUndefined, autoescape=False)
                return env.from_string(dict(row)["content"]).render(**spec.template_vars)
            except ImportError:
                logger.warning("Jinja2 unavailable; returning raw template.")
                return dict(row)["content"]
        return f"[Body for {spec.filing_type.value}: {spec.title}]\n\n[ANDREW_REQUIRED]"

    def _load_parties(self, case_id: int) -> list[str]:
        """Load opposing party names for COS generation."""
        rows = self._db.fetchall(
            "SELECT name FROM parties WHERE case_id = ? "
            "AND role IN ('defendant','respondent','opposing_counsel') ORDER BY name",
            (case_id,),
        )
        return [dict(r)["name"] for r in rows] or ["[NO PARTIES ON FILE]"]

    def _persist_filing(self, spec: FilingSpec, word_count: int) -> int:
        """Insert a new filing record and return its ID."""
        notes = f"Court: {spec.court}"
        if spec.notes:
            notes += f"\n{spec.notes}"
        conn = self._db.connect()
        try:
            cur = conn.execute(
                "INSERT INTO filings "
                "(case_id, title, filing_type, status, word_count, notes, created_at) "
                "VALUES (?, ?, ?, 'draft', ?, ?, datetime('now'))",
                (spec.case_id, spec.title, spec.filing_type.value, word_count, notes),
            )
            conn.commit()
            return cur.lastrowid  # type: ignore[return-value]
        except Exception:
            conn.rollback()
            logger.exception("Failed to persist filing for case %d", spec.case_id)
            raise
        finally:
            conn.close()
