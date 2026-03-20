"""Case onboarding wizard engine.

Guides users through a structured intake process: upload evidence,
classify documents, detect parties, discover claims, suggest filings,
generate timelines, and assign deadlines.  Zero-to-case-ready in
30 minutes for a straightforward family-law case.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from pathlib import Path

    from litigationos.db.connection import DatabaseManager

logger = logging.getLogger(__name__)


# ── Intake stage enum ────────────────────────────────────────────────────────

class IntakeStage(str, Enum):
    """Stages of the onboarding wizard (in order)."""

    CASE_INFO = "case_info"
    PARTIES = "parties"
    EVIDENCE_UPLOAD = "evidence_upload"
    CLASSIFICATION = "classification"
    CLAIM_DETECTION = "claim_detection"
    FILING_SUGGESTIONS = "filing_suggestions"
    TIMELINE_BUILD = "timeline_build"
    DEADLINE_ASSIGNMENT = "deadline_assignment"
    REVIEW = "review"
    COMPLETE = "complete"

    @classmethod
    def ordered(cls) -> list["IntakeStage"]:
        return list(cls)

    def next(self) -> Optional["IntakeStage"]:
        stages = self.ordered()
        idx = stages.index(self)
        return stages[idx + 1] if idx + 1 < len(stages) else None


# ── Models ───────────────────────────────────────────────────────────────────

class IntakeParty(BaseModel):
    """Party detected or entered during onboarding."""

    name: str
    role: str = "unknown"          # plaintiff, defendant, judge, witness, attorney
    entity_type: str = "person"    # person, organization, government
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class IntakeEvidence(BaseModel):
    """Evidence item uploaded during onboarding."""

    file_path: str
    file_type: str = "unknown"
    classification: str = "unclassified"
    lane: Optional[str] = None       # A=custody, B=housing, etc.
    date_detected: Optional[str] = None
    summary: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DetectedClaim(BaseModel):
    """A legal claim detected from uploaded evidence."""

    claim_type: str               # e.g. "custody_modification", "contempt", "IIED"
    statutory_basis: Optional[str] = None  # e.g. "MCL 722.27"
    confidence: float = 0.0       # 0.0 - 1.0
    supporting_evidence: list[str] = Field(default_factory=list)
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SuggestedFiling(BaseModel):
    """Filing suggested by the onboarding analysis."""

    filing_type: str
    title: str
    court: str
    priority: str = "normal"       # emergency, high, normal, low
    estimated_readiness: int = 0   # 0-100
    deadline: Optional[str] = None
    rationale: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class IntakeSession(BaseModel):
    """Full onboarding session state — persisted between wizard steps."""

    session_id: Optional[int] = None
    stage: IntakeStage = IntakeStage.CASE_INFO
    case_title: str = ""
    case_type: str = ""
    jurisdiction: str = "MI"       # default Michigan
    court: str = ""
    case_number: Optional[str] = None
    parties: list[IntakeParty] = Field(default_factory=list)
    evidence: list[IntakeEvidence] = Field(default_factory=list)
    claims: list[DetectedClaim] = Field(default_factory=list)
    filings: list[SuggestedFiling] = Field(default_factory=list)
    timeline_events: list[dict] = Field(default_factory=list)
    deadlines: list[dict] = Field(default_factory=list)
    notes: str = ""
    created_at: Optional[datetime] = Field(default_factory=datetime.now)

    model_config = ConfigDict(from_attributes=True)

    @property
    def progress_pct(self) -> int:
        stages = IntakeStage.ordered()
        idx = stages.index(self.stage)
        return int((idx / (len(stages) - 1)) * 100)


# ── Claim detection rules ────────────────────────────────────────────────────

# Keyword → claim type mapping (jurisdiction-agnostic with MI defaults)
CLAIM_SIGNALS: list[dict] = [
    {"keywords": ["custody", "parenting time", "best interest", "visitation"],
     "claim_type": "custody_modification", "basis": "MCL 722.27", "lane": "A"},
    {"keywords": ["contempt", "violation of order", "willful noncompliance"],
     "claim_type": "contempt", "basis": "MCL 552.1 / MCR 3.606", "lane": "A"},
    {"keywords": ["alienation", "interference", "denied parenting", "withheld"],
     "claim_type": "parental_alienation", "basis": "MCL 722.23(j)", "lane": "A"},
    {"keywords": ["ex parte", "without notice", "no hearing", "one-sided"],
     "claim_type": "due_process_violation", "basis": "14th Amendment / MCR 3.207", "lane": "E"},
    {"keywords": ["disqualification", "bias", "impartial", "recusal"],
     "claim_type": "judicial_disqualification", "basis": "MCR 2.003", "lane": "E"},
    {"keywords": ["habitability", "mold", "sewage", "repairs", "unsafe"],
     "claim_type": "warranty_habitability", "basis": "MCL 554.139", "lane": "B"},
    {"keywords": ["eviction", "lockout", "retaliatory", "illegal entry"],
     "claim_type": "retaliatory_eviction", "basis": "MCL 600.5720", "lane": "B"},
    {"keywords": ["defamation", "false statement", "slander", "libel"],
     "claim_type": "defamation", "basis": "Common law", "lane": "A"},
    {"keywords": ["fraud", "misrepresentation", "deceived", "concealed"],
     "claim_type": "fraud", "basis": "MCL 566.34", "lane": "B"},
    {"keywords": ["1983", "civil rights", "constitutional", "color of law"],
     "claim_type": "section_1983", "basis": "42 USC § 1983", "lane": "E"},
    {"keywords": ["ppo", "personal protection", "stalking", "harassment"],
     "claim_type": "ppo_modification", "basis": "MCL 600.2950", "lane": "D"},
    {"keywords": ["appeal", "appellate", "error", "reversed", "remand"],
     "claim_type": "appeal", "basis": "MCR 7.203", "lane": "F"},
    {"keywords": ["RICO", "enterprise", "pattern", "racketeering"],
     "claim_type": "rico", "basis": "MCL 750.159i", "lane": "B"},
    {"keywords": ["conversion", "property", "stolen", "withheld belongings"],
     "claim_type": "conversion", "basis": "MCL 600.2919a", "lane": "A"},
    {"keywords": ["emotional distress", "outrageous", "extreme"],
     "claim_type": "iied", "basis": "Common law", "lane": "A"},
]


# ── Engine ───────────────────────────────────────────────────────────────────

class OnboardingEngine:
    """Guides case intake through structured stages.

    Each ``advance()`` call processes the current stage and moves to the next.
    State is persisted to SQLite so the wizard can be resumed across sessions.
    """

    TABLE_DDL = """
    CREATE TABLE IF NOT EXISTS intake_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stage TEXT NOT NULL DEFAULT 'case_info',
        data_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """

    def __init__(self, db: "DatabaseManager"):
        self._db = db
        self._ensure_table()

    def _ensure_table(self) -> None:
        try:
            self._db.execute(self.TABLE_DDL)
        except Exception:
            logger.debug("intake_sessions table may already exist")

    # ── Session persistence ──────────────────────────────────────────────────

    def create_session(self, session: IntakeSession) -> int:
        """Persist a new intake session and return its ID."""
        import json as _json

        data = session.model_dump_json()
        cursor = self._db.execute(
            "INSERT INTO intake_sessions (stage, data_json) VALUES (?, ?)",
            (session.stage.value, data),
        )
        session_id = cursor.lastrowid
        logger.info("Created intake session %d", session_id)
        return session_id

    def load_session(self, session_id: int) -> IntakeSession:
        """Load an existing intake session from the database."""
        import json as _json

        row = self._db.fetchone(
            "SELECT * FROM intake_sessions WHERE id = ?", (session_id,),
        )
        if row is None:
            raise LookupError(f"Intake session {session_id} not found")
        return IntakeSession.model_validate_json(dict(row)["data_json"])

    def save_session(self, session_id: int, session: IntakeSession) -> None:
        """Update an existing intake session."""
        self._db.execute(
            "UPDATE intake_sessions SET stage = ?, data_json = ?, "
            "updated_at = datetime('now') WHERE id = ?",
            (session.stage.value, session.model_dump_json(), session_id),
        )

    # ── Stage processors ─────────────────────────────────────────────────────

    def advance(self, session: IntakeSession) -> IntakeSession:
        """Process the current stage and advance to the next.

        Returns the session with ``stage`` moved forward. If already
        ``COMPLETE``, returns unchanged.
        """
        if session.stage == IntakeStage.COMPLETE:
            return session

        processor = {
            IntakeStage.CASE_INFO: self._process_case_info,
            IntakeStage.PARTIES: self._process_parties,
            IntakeStage.EVIDENCE_UPLOAD: self._process_evidence,
            IntakeStage.CLASSIFICATION: self._process_classification,
            IntakeStage.CLAIM_DETECTION: self._process_claims,
            IntakeStage.FILING_SUGGESTIONS: self._process_filings,
            IntakeStage.TIMELINE_BUILD: self._process_timeline,
            IntakeStage.DEADLINE_ASSIGNMENT: self._process_deadlines,
            IntakeStage.REVIEW: self._process_review,
        }.get(session.stage)

        if processor:
            session = processor(session)

        next_stage = session.stage.next()
        if next_stage:
            session.stage = next_stage
            logger.info("Advanced to stage %s (%d%%)", next_stage.value, session.progress_pct)

        return session

    def _process_case_info(self, session: IntakeSession) -> IntakeSession:
        """Validate case info fields are populated."""
        if not session.case_title:
            logger.warning("Case title is empty — wizard should prompt user")
        if not session.case_type:
            session.case_type = "civil"
        if not session.jurisdiction:
            session.jurisdiction = "MI"
        return session

    def _process_parties(self, session: IntakeSession) -> IntakeSession:
        """Ensure at least plaintiff + defendant exist."""
        roles = {p.role for p in session.parties}
        if "plaintiff" not in roles:
            logger.warning("No plaintiff detected — user should add one")
        if "defendant" not in roles:
            logger.warning("No defendant detected — user should add one")
        return session

    def _process_evidence(self, session: IntakeSession) -> IntakeSession:
        """Process uploaded evidence files (classification happens next stage)."""
        for ev in session.evidence:
            if ev.classification == "unclassified":
                ev.classification = self._quick_classify(ev.file_path)
        return session

    def _process_classification(self, session: IntakeSession) -> IntakeSession:
        """Refine evidence classification and assign lanes."""
        for ev in session.evidence:
            if not ev.lane:
                ev.lane = self._detect_lane(ev)
        return session

    def _process_claims(self, session: IntakeSession) -> IntakeSession:
        """Detect legal claims from evidence using keyword signals."""
        if session.claims:
            return session  # already detected

        evidence_text = " ".join(
            (ev.summary or ev.classification or "") for ev in session.evidence
        ).lower()

        for signal in CLAIM_SIGNALS:
            hits = sum(1 for kw in signal["keywords"] if kw.lower() in evidence_text)
            if hits >= 2:
                confidence = min(1.0, hits / len(signal["keywords"]))
                session.claims.append(DetectedClaim(
                    claim_type=signal["claim_type"],
                    statutory_basis=signal.get("basis"),
                    confidence=confidence,
                    description=f"Detected from {hits} keyword matches",
                ))
                logger.info("Detected claim: %s (%.0f%%)", signal["claim_type"], confidence * 100)

        return session

    def _process_filings(self, session: IntakeSession) -> IntakeSession:
        """Suggest filings based on detected claims."""
        if session.filings:
            return session

        filing_map = {
            "custody_modification": ("motion", "Motion to Modify Custody", "14th Circuit"),
            "contempt": ("motion", "Motion for Contempt", "14th Circuit"),
            "parental_alienation": ("motion", "Motion re: Parental Alienation", "14th Circuit"),
            "due_process_violation": ("complaint", "§1983 Complaint", "W.D. Michigan"),
            "judicial_disqualification": ("motion", "Motion to Disqualify", "14th Circuit"),
            "warranty_habitability": ("complaint", "Housing Complaint", "14th Circuit"),
            "retaliatory_eviction": ("complaint", "Retaliatory Eviction Complaint", "14th Circuit"),
            "defamation": ("complaint", "Defamation Complaint", "14th Circuit"),
            "fraud": ("complaint", "Fraud Complaint", "14th Circuit"),
            "section_1983": ("complaint", "Federal §1983 Complaint", "W.D. Michigan"),
            "ppo_modification": ("motion", "Motion to Modify PPO", "14th Circuit"),
            "appeal": ("brief", "Appellate Brief", "Court of Appeals"),
            "rico": ("complaint", "RICO Complaint", "14th Circuit"),
            "conversion": ("complaint", "Conversion Complaint", "14th Circuit"),
            "iied": ("complaint", "IIED Complaint", "14th Circuit"),
        }

        for claim in session.claims:
            if claim.claim_type in filing_map:
                ftype, title, court = filing_map[claim.claim_type]
                priority = "emergency" if claim.confidence >= 0.8 else "high" if claim.confidence >= 0.6 else "normal"
                session.filings.append(SuggestedFiling(
                    filing_type=ftype,
                    title=title,
                    court=court,
                    priority=priority,
                    estimated_readiness=int(claim.confidence * 80),
                    rationale=f"Based on {claim.claim_type} ({claim.statutory_basis})",
                ))

        return session

    def _process_timeline(self, session: IntakeSession) -> IntakeSession:
        """Build timeline from evidence dates."""
        for ev in session.evidence:
            if ev.date_detected:
                session.timeline_events.append({
                    "date": ev.date_detected,
                    "event": ev.summary or f"Evidence: {ev.classification}",
                    "source": ev.file_path,
                })
        session.timeline_events.sort(key=lambda e: e.get("date", ""))
        return session

    def _process_deadlines(self, session: IntakeSession) -> IntakeSession:
        """Assign deadlines based on suggested filings and court rules."""
        today = date.today()
        for i, filing in enumerate(session.filings):
            if filing.priority == "emergency":
                dl = today + timedelta(days=7)
            elif filing.priority == "high":
                dl = today + timedelta(days=14)
            else:
                dl = today + timedelta(days=30 + i * 7)
            session.deadlines.append({
                "filing": filing.title,
                "due_date": dl.isoformat(),
                "priority": filing.priority,
                "court": filing.court,
            })
        return session

    def _process_review(self, session: IntakeSession) -> IntakeSession:
        """Final review stage — just log summary."""
        logger.info(
            "Intake review: %d parties, %d evidence, %d claims, %d filings, %d deadlines",
            len(session.parties), len(session.evidence), len(session.claims),
            len(session.filings), len(session.deadlines),
        )
        return session

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _quick_classify(self, file_path: str) -> str:
        """Quick file classification by extension."""
        ext = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else ""
        return {
            "pdf": "court_document",
            "docx": "legal_document",
            "doc": "legal_document",
            "txt": "text_evidence",
            "png": "photo_evidence",
            "jpg": "photo_evidence",
            "jpeg": "photo_evidence",
            "csv": "financial_record",
            "xlsx": "financial_record",
            "eml": "email_evidence",
            "msg": "email_evidence",
        }.get(ext, "unknown")

    def _detect_lane(self, evidence: IntakeEvidence) -> Optional[str]:
        """Detect which case lane evidence belongs to based on content signals."""
        text = (evidence.summary or evidence.classification or "").lower()
        if any(kw in text for kw in ["custody", "parenting", "child", "visitation"]):
            return "A"
        if any(kw in text for kw in ["housing", "rent", "lease", "eviction", "mold"]):
            return "B"
        if any(kw in text for kw in ["ppo", "protection", "stalking"]):
            return "D"
        if any(kw in text for kw in ["judge", "misconduct", "bias", "ex parte"]):
            return "E"
        if any(kw in text for kw in ["appeal", "appellate", "coa"]):
            return "F"
        return None

    # ── Full workflow ────────────────────────────────────────────────────────

    def run_full_intake(self, session: IntakeSession) -> IntakeSession:
        """Run all stages sequentially (batch mode, non-interactive)."""
        while session.stage != IntakeStage.COMPLETE:
            session = self.advance(session)
        logger.info("Intake complete: %s", session.case_title)
        return session

    def generate_summary(self, session: IntakeSession) -> str:
        """Generate a human-readable intake summary."""
        lines = [
            f"# Case Intake Summary: {session.case_title}",
            f"**Type:** {session.case_type} | **Jurisdiction:** {session.jurisdiction}",
            f"**Court:** {session.court} | **Case #:** {session.case_number or 'TBD'}",
            f"**Progress:** {session.progress_pct}%",
            "",
            f"## Parties ({len(session.parties)})",
        ]
        for p in session.parties:
            lines.append(f"- **{p.name}** ({p.role}, {p.entity_type})")

        lines.append(f"\n## Evidence ({len(session.evidence)} items)")
        for ev in session.evidence:
            lines.append(f"- [{ev.lane or '?'}] {ev.classification}: {ev.file_path}")

        lines.append(f"\n## Claims Detected ({len(session.claims)})")
        for c in session.claims:
            lines.append(f"- **{c.claim_type}** ({c.statutory_basis}) — {c.confidence:.0%} confidence")

        lines.append(f"\n## Suggested Filings ({len(session.filings)})")
        for f in session.filings:
            lines.append(f"- [{f.priority.upper()}] {f.title} → {f.court} (readiness: {f.estimated_readiness}%)")

        lines.append(f"\n## Deadlines ({len(session.deadlines)})")
        for d in session.deadlines:
            lines.append(f"- {d['due_date']}: {d['filing']} ({d['priority']})")

        return "\n".join(lines)
