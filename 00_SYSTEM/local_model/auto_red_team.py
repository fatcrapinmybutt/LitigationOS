"""
APEX Auto Red-Team — Automated adversarial review of court filings.

Simulates opposing counsel attack on every filing before submission.
Shadow-programmed: rule-based attacks when LLM disabled, LLM adversarial
analysis when enabled.

Red-team attacks per filing type:
  1. Citation attacks   — good law? supports proposition?
  2. Logic attacks      — fallacies, non sequiturs, unsupported conclusions
  3. Evidence attacks   — admissibility, authentication, foundation
  4. Procedural attacks — service, timeliness, form, court
  5. Credibility attacks— fabricated claims, unsupported stats, exaggerations
  6. Counter-argument   — opposing counsel arguments, adverse precedent
  7. Damages attacks    — speculative, double-counted, unsupported multipliers

CRITICAL RULES (from prior sessions):
  - "91% alienation score"             → PROHIBITED (pseudo-scientific)
  - "9 CPS investigations"             → PROHIBITED (fabricated)
  - "Emily Ann Watson" / "Emily M."    → PROHIBITED (correct: Emily A. Watson)
  - Any statistic without [SOURCE] tag → FLAGGED
  - Any citation not verified against DB → FLAGGED
"""

from __future__ import annotations

import importlib.util
import json
import logging
import os
import re
import sqlite3
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Shadow gate — LLM features only activate when explicitly enabled
# ---------------------------------------------------------------------------
APEX_LLM_ENABLED: bool = (
    os.environ.get("APEX_LLM_ENABLED", "false").lower() == "true"
)

# ---------------------------------------------------------------------------
# Paths — anchored to this file, never repo root
# ---------------------------------------------------------------------------
_HERE: Path = Path(__file__).resolve().parent
_REPO: Path = _HERE.parent.parent
_DB_PATH: Path = _REPO / "litigation_context.db"
_MASTER_INDEX_DB: Path = _REPO / "00_SYSTEM" / "pipeline" / "agents" / "master_index.db"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
_log = logging.getLogger("apex.auto_red_team")
if not _log.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter(
        "%(asctime)s [%(name)s] %(levelname)s — %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    ))
    _log.addHandler(_h)
_log.setLevel(logging.DEBUG if APEX_LLM_ENABLED else logging.INFO)

# ---------------------------------------------------------------------------
# DB PRAGMAs (mandatory for all connections)
# ---------------------------------------------------------------------------
_DB_PRAGMAS: str = """
PRAGMA busy_timeout  = 60000;
PRAGMA journal_mode  = WAL;
PRAGMA cache_size    = -32000;
PRAGMA temp_store    = MEMORY;
PRAGMA synchronous   = NORMAL;
"""


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class Attack:
    """Single adversarial finding."""

    category: str = ""          # citation | logic | evidence | procedural | credibility | counter | damages
    severity: str = "warning"   # critical | warning | info
    title: str = ""
    detail: str = ""
    location: str = ""          # line number or paragraph reference
    rule: str = ""              # MCR / MCL / MRE reference
    suggestion: str = ""
    source: str = "rule"        # rule | llm | pattern

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v}


@dataclass
class RedTeamResult:
    """Aggregate red-team report for a filing."""

    filing_path: str = ""
    filing_type: str = ""
    lane: str = ""
    timestamp: str = ""
    score: int = 100            # starts at 100, deducted per attack
    attacks: List[Attack] = field(default_factory=list)
    critical: List[Attack] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    summary: str = ""
    method: str = "rule"        # rule | hybrid

    def to_dict(self) -> Dict[str, Any]:
        return {
            "filing_path": self.filing_path,
            "filing_type": self.filing_type,
            "lane": self.lane,
            "timestamp": self.timestamp,
            "score": self.score,
            "attack_count": len(self.attacks),
            "critical_count": len(self.critical),
            "attacks": [a.to_dict() for a in self.attacks],
            "critical": [a.to_dict() for a in self.critical],
            "suggestions": self.suggestions,
            "summary": self.summary,
            "method": self.method,
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _safe_connect(db_path: Path) -> Optional[sqlite3.Connection]:
    """Open a DB connection with mandatory PRAGMAs. Returns None on failure."""
    try:
        if not db_path.exists():
            _log.debug("DB not found: %s", db_path)
            return None
        conn = sqlite3.connect(str(db_path), timeout=60, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.executescript(_DB_PRAGMAS)
        return conn
    except Exception as exc:
        _log.error("DB connect failed for %s: %s", db_path, exc)
        return None


def _load_sibling(module_name: str) -> Any:
    """Import a sibling module without touching sys.path or repo root."""
    mod_path = _HERE / f"{module_name}.py"
    if not mod_path.exists():
        return None
    try:
        spec = importlib.util.spec_from_file_location(module_name, str(mod_path))
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception as exc:
        _log.debug("Failed to load sibling %s: %s", module_name, exc)
        return None


def _read_file(path: str) -> str:
    """Read a file with encoding fallbacks. Never crashes."""
    for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            return Path(path).read_text(encoding=enc)
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as exc:
            _log.debug("Cannot read %s: %s", path, exc)
            return ""
    return ""


# ---------------------------------------------------------------------------
# Citation regex
# ---------------------------------------------------------------------------
_CITE_MCL = re.compile(r"MCL\s+(\d+[\.\d]*[a-z]?(?:\(\d+\))?)", re.IGNORECASE)
_CITE_MCR = re.compile(r"MCR\s+(\d+\.\d+(?:\([A-Z]\))?(?:\(\d+\))?)", re.IGNORECASE)
_CITE_MRE = re.compile(r"MRE\s+(\d+(?:\.\d+)?)", re.IGNORECASE)
_CITE_CASE = re.compile(
    r"(\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+v\.?\s+"
    r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
    r"[,;]?\s*(\d+\s+(?:Mich(?:\s+App)?|NW2d|NW\s*2d)\s+\d+)?",
)
_CITE_USC = re.compile(r"(\d+)\s+U\.?S\.?C\.?\s+(?:§\s*)?(\d+)", re.IGNORECASE)

_STAT_NO_SOURCE = re.compile(
    r"\b(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*%"
    r"(?!.*\[(?:SOURCE|CITE|RECORD|EXHIBIT)])",
)

# Logic fallacy patterns
_FALLACY_PATTERNS: List[Tuple[re.Pattern, str, str]] = [
    (re.compile(r"\b(?:everyone|nobody|always|never)\s+(?:knows?|agrees?|does)", re.I),
     "appeal_to_popularity", "Absolute qualifier — 'everyone knows' is not evidence"),
    (re.compile(r"\b(?:obviously|clearly|undeniably|unquestionably)\b", re.I),
     "begging_the_question", "Asserting conclusion as self-evident without proof"),
    (re.compile(r"\bslippery\s+slope\b", re.I),
     "slippery_slope", "Slippery slope argument without causal chain"),
    (re.compile(r"\b(?:therefore|thus|hence|so)\b.*\b(?:must|will|shall)\b", re.I),
     "non_sequitur", "Conclusion may not follow from premises — verify logical chain"),
    (re.compile(r"\b(?:if|since)\s+.{5,60}(?:then|therefore)\s+.{5,60}(?:then|therefore)", re.I),
     "chain_reasoning", "Multi-step chain reasoning — verify each link"),
    (re.compile(r"\bstraw\s*man\b", re.I),
     "straw_man", "Possible straw man — misrepresenting opposing position"),
    (re.compile(r"\b(?:ad\s+hominem|character\s+attack)\b", re.I),
     "ad_hominem", "Ad hominem — attack on person rather than argument"),
    (re.compile(r"\b(?:because|since)\s+(?:I|we|he|she|they)\s+(?:feel|felt|believe)", re.I),
     "appeal_to_emotion", "Appeal to emotion — subjective feeling is not legal evidence"),
]

# Hearsay signal patterns
_HEARSAY_PATTERNS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\b(?:told|said|stated|informed|reported)\s+(?:me|him|her|them|us)\b", re.I),
     "Out-of-court statement offered for truth of matter — hearsay under MRE 801(c)"),
    (re.compile(r"\baccording\s+to\s+(?!(?:the\s+)?(?:court|record|exhibit|statute))", re.I),
     "Possible hearsay source — verify exception under MRE 803/804"),
    (re.compile(r"\b(?:I\s+was\s+told|I\s+heard|someone\s+said|they\s+told)\b", re.I),
     "Double hearsay — requires exception at each level under MRE 805"),
]

# Damages patterns
_DAMAGES_SPECULATIVE = re.compile(
    r"\b(?:estimated|approximately|roughly|about|projected|anticipated)\s+"
    r"(?:\$[\d,]+|\d+\s+(?:thousand|million|billion))",
    re.I,
)
_DAMAGES_MULTIPLIER = re.compile(
    r"\b(\d+)\s*[xX×]\s*(?:multiplier|multiple|times)\b",
)
_DAMAGES_EMOTIONAL = re.compile(
    r"\b(?:emotional\s+distress|pain\s+and\s+suffering|mental\s+anguish)"
    r"\s*(?:damages?)?\s*(?:of|:)?\s*\$?([\d,]+)",
    re.I,
)


# ===================================================================
# Main class
# ===================================================================
class AutoRedTeam:
    """
    Automated adversarial review of court filings.

    Simulates opposing counsel attack vectors against a filing.
    Rule-based when APEX_LLM_ENABLED is false; hybrid rule + LLM
    when enabled.
    """

    # -------------------------------------------------------------------
    # Prohibited patterns — ABSOLUTE red lines from prior sessions
    # -------------------------------------------------------------------
    PROHIBITED_PATTERNS: List[Tuple[re.Pattern, str]] = [
        (re.compile(r"91\s*%?\s*alienation\s*score", re.I),
         "FABRICATED: '91% alienation score' is pseudo-scientific. "
         "Use '305 documented interference incidents' + MCL 722.23(j)"),
        (re.compile(r"(?:9|nine)\s+CPS\s+investigations?", re.I),
         "FABRICATED: '9 CPS investigations' never happened. "
         "Andrew called CPS ONCE + filed police reports"),
        (re.compile(r"Emily\s+(?:Ann|M\.?|Tiffany)\s+Watson", re.I),
         "WRONG NAME: Must be 'Emily A. Watson' per court records"),
        (re.compile(r"Lincoln\s+(?:David\s+)?Watson(?!\s+\()", re.I),
         "CHILD NAME EXPOSED: Must use 'L.D.W.' per MCR 8.119(H)"),
        (re.compile(r"nine\s+police\s+investigations?", re.I),
         "UNVERIFIED: Exact count unconfirmed. "
         "Use 'multiple investigations [ANDREW_REQUIRED]'"),
    ]

    # -------------------------------------------------------------------
    # Evidence admissibility rules
    # -------------------------------------------------------------------
    EVIDENCE_RULES: List[Dict[str, str]] = [
        {"check": "hearsay",
         "description": "Flag statements that may be inadmissible hearsay without exception"},
        {"check": "authentication",
         "description": "Flag exhibits without foundation or authentication"},
        {"check": "relevance",
         "description": "Flag evidence that may be excluded under MRE 401-403"},
        {"check": "privilege",
         "description": "Flag potentially privileged communications"},
        {"check": "best_evidence",
         "description": "Flag copies without best evidence rule compliance (MRE 1002)"},
    ]

    # -------------------------------------------------------------------
    # Procedural checklists per filing type
    # -------------------------------------------------------------------
    PROCEDURAL_CHECKS: Dict[str, List[str]] = {
        "motion": [
            "MCR 2.119 format",
            "brief in support attached",
            "proposed order attached",
            "proof of service",
        ],
        "complaint": [
            "jurisdiction stated",
            "parties identified",
            "counts numbered",
            "prayer for relief",
            "verification",
        ],
        "appellate_brief": [
            "MCR 7.212 sections",
            "word count compliant",
            "table of authorities",
            "appendix",
        ],
        "affidavit": [
            "jurat/notarization",
            "personal knowledge",
            "competency statement",
        ],
        "emergency_motion": [
            "MCR 2.119(F) compliance",
            "irreparable harm shown",
            "immediate hearing request",
        ],
    }

    # -------------------------------------------------------------------
    # Severity deduction weights
    # -------------------------------------------------------------------
    _DEDUCTIONS: Dict[str, int] = {
        "critical": 15,
        "warning": 5,
        "info": 1,
    }

    def __init__(self, db_path: Optional[str] = None) -> None:
        self._lock = threading.Lock()
        self.db_path: Path = Path(db_path) if db_path else _DB_PATH
        self._inference: Any = None     # lazy: MichiganLegalModel
        self._grounding: Any = None     # lazy: CitationGrounding
        self._conn: Optional[sqlite3.Connection] = None

    # -------------------------------------------------------------------
    # Lazy loaders (thread-safe, never crash)
    # -------------------------------------------------------------------
    def _get_inference(self) -> Any:
        if self._inference is not None:
            return self._inference
        with self._lock:
            if self._inference is not None:
                return self._inference
            try:
                mod = _load_sibling("inference_engine")
                if mod is not None:
                    self._inference = mod.MichiganLegalModel()
            except Exception as exc:
                _log.debug("MANBEARPIG load failed: %s", exc)
        return self._inference

    def _get_grounding(self) -> Any:
        if self._grounding is not None:
            return self._grounding
        with self._lock:
            if self._grounding is not None:
                return self._grounding
            try:
                mod = _load_sibling("citation_grounding")
                if mod is not None:
                    self._grounding = mod.CitationGrounding(str(self.db_path))
            except Exception as exc:
                _log.debug("CitationGrounding load failed: %s", exc)
        return self._grounding

    def _get_conn(self) -> Optional[sqlite3.Connection]:
        if self._conn is not None:
            return self._conn
        self._conn = _safe_connect(self.db_path)
        return self._conn

    # ===================================================================
    # PUBLIC API
    # ===================================================================

    def red_team(
        self,
        filing_path: str,
        filing_type: Optional[str] = None,
        lane: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Full red-team review of a filing.

        Returns dict with: score, attacks, critical, suggestions, summary.
        """
        result = RedTeamResult(
            filing_path=filing_path,
            filing_type=filing_type or self._detect_type(filing_path),
            lane=lane or "",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        try:
            text = _read_file(filing_path)
            if not text.strip():
                result.summary = "Empty or unreadable filing — cannot red-team."
                result.score = 0
                return result.to_dict()

            # Run all attack vectors
            all_attacks: List[Attack] = []
            all_attacks.extend(self.attack_credibility(text))
            all_attacks.extend(self.attack_citations(text))
            all_attacks.extend(self.attack_logic(text))
            all_attacks.extend(self.attack_evidence(text))
            all_attacks.extend(self.attack_procedure(text, result.filing_type))
            all_attacks.extend(self.attack_damages(text))

            # LLM-enhanced counter-argument (shadow-gated)
            if APEX_LLM_ENABLED:
                try:
                    all_attacks.extend(self._llm_counter_arguments(text, result.filing_type))
                    result.method = "hybrid"
                except Exception as exc:
                    _log.debug("LLM counter-arguments failed: %s", exc)

            # Classify and score
            for atk in all_attacks:
                result.attacks.append(atk)
                if atk.severity == "critical":
                    result.critical.append(atk)
                deduction = self._DEDUCTIONS.get(atk.severity, 1)
                result.score = max(0, result.score - deduction)

            # Build suggestions
            result.suggestions = self._build_suggestions(all_attacks)
            result.summary = self._build_summary(result)

            # Persist to DB
            self._persist_result(result)

        except Exception as exc:
            _log.error("Red-team review failed for %s: %s", filing_path, exc)
            result.summary = f"Red-team review encountered error: {exc}"
            result.score = 0

        return result.to_dict()

    # -------------------------------------------------------------------
    # Attack: Citations
    # -------------------------------------------------------------------
    def attack_citations(self, text: str) -> List[Attack]:
        """Attack all citations: format, existence, good law, relevance."""
        attacks: List[Attack] = []
        try:
            attacks.extend(self._check_mcl_citations(text))
            attacks.extend(self._check_mcr_citations(text))
            attacks.extend(self._check_case_citations(text))
            attacks.extend(self._check_usc_citations(text))
            attacks.extend(self._check_unsourced_stats(text))
        except Exception as exc:
            _log.error("Citation attack failed: %s", exc)
        return attacks

    def _check_mcl_citations(self, text: str) -> List[Attack]:
        """Verify MCL citations exist in DB."""
        attacks: List[Attack] = []
        conn = self._get_conn()
        for m in _CITE_MCL.finditer(text):
            cite = m.group(1)
            found = False
            if conn is not None:
                try:
                    row = conn.execute(
                        "SELECT 1 FROM authorities WHERE citation LIKE ? LIMIT 1",
                        (f"%MCL {cite}%",),
                    ).fetchone()
                    found = row is not None
                except Exception:
                    pass
            if not found:
                attacks.append(Attack(
                    category="citation",
                    severity="warning",
                    title=f"MCL {cite} — not verified in DB",
                    detail=f"MCL {cite} not found in authorities table. Verify it exists and supports the proposition.",
                    location=f"char {m.start()}",
                    rule=f"MCL {cite}",
                    suggestion=f"Verify MCL {cite} in Michigan Legislature website and add to authorities table.",
                ))
        return attacks

    def _check_mcr_citations(self, text: str) -> List[Attack]:
        """Verify MCR citations exist in DB."""
        attacks: List[Attack] = []
        conn = self._get_conn()
        for m in _CITE_MCR.finditer(text):
            cite = m.group(1)
            found = False
            if conn is not None:
                try:
                    row = conn.execute(
                        "SELECT 1 FROM authorities WHERE citation LIKE ? LIMIT 1",
                        (f"%MCR {cite}%",),
                    ).fetchone()
                    found = row is not None
                except Exception:
                    pass
            if not found:
                attacks.append(Attack(
                    category="citation",
                    severity="warning",
                    title=f"MCR {cite} — not verified in DB",
                    detail=f"MCR {cite} not found in authorities table. Opposing counsel may challenge.",
                    location=f"char {m.start()}",
                    rule=f"MCR {cite}",
                    suggestion=f"Confirm MCR {cite} text and add to authorities table.",
                ))
        return attacks

    def _check_case_citations(self, text: str) -> List[Attack]:
        """Verify case citations and check for pinpoint cites."""
        attacks: List[Attack] = []
        grounding = self._get_grounding()
        for m in _CITE_CASE.finditer(text):
            case_name = f"{m.group(1)} v {m.group(2)}"
            reporter = m.group(3) or ""
            if not reporter.strip():
                attacks.append(Attack(
                    category="citation",
                    severity="warning",
                    title=f"{case_name} — missing reporter citation",
                    detail="Case cited without reporter volume/page. Opposing counsel will challenge.",
                    location=f"char {m.start()}",
                    suggestion=f"Add full reporter citation for {case_name} (e.g., '123 Mich App 456').",
                ))
            if grounding is not None:
                try:
                    result = grounding.verify(case_name)
                    if isinstance(result, dict) and not result.get("verified", True):
                        attacks.append(Attack(
                            category="citation",
                            severity="critical",
                            title=f"{case_name} — not verified as good law",
                            detail=result.get("detail", "Citation not found in grounding database."),
                            location=f"char {m.start()}",
                            suggestion="Verify case is still good law. Check for reversals or overrulings.",
                        ))
                except Exception:
                    pass
        return attacks

    def _check_usc_citations(self, text: str) -> List[Attack]:
        """Flag USC citations that may need verification."""
        attacks: List[Attack] = []
        for m in _CITE_USC.finditer(text):
            title, section = m.group(1), m.group(2)
            attacks.append(Attack(
                category="citation",
                severity="info",
                title=f"{title} USC § {section} — federal citation in state filing",
                detail="Federal statute cited — ensure it applies in Michigan state court context.",
                location=f"char {m.start()}",
                rule=f"{title} USC § {section}",
                suggestion="Verify federal preemption or supplemental jurisdiction basis.",
            ))
        return attacks

    def _check_unsourced_stats(self, text: str) -> List[Attack]:
        """Flag statistics without source tags."""
        attacks: List[Attack] = []
        for m in _STAT_NO_SOURCE.finditer(text):
            attacks.append(Attack(
                category="credibility",
                severity="warning",
                title=f"Unsourced statistic: {m.group(0).strip()}",
                detail="Percentage/statistic without [SOURCE] tag. Opposing counsel will demand foundation.",
                location=f"char {m.start()}",
                suggestion="Add [SOURCE] tag or remove statistic. Unsourced numbers destroy credibility.",
            ))
        return attacks

    # -------------------------------------------------------------------
    # Attack: Logic
    # -------------------------------------------------------------------
    def attack_logic(self, text: str) -> List[Attack]:
        """Find logical fallacies, unsupported conclusions, non sequiturs."""
        attacks: List[Attack] = []
        try:
            for pattern, fallacy_type, description in _FALLACY_PATTERNS:
                for m in pattern.finditer(text):
                    context = text[max(0, m.start() - 40):m.end() + 40].strip()
                    attacks.append(Attack(
                        category="logic",
                        severity="warning",
                        title=f"Potential {fallacy_type.replace('_', ' ')}",
                        detail=f"{description}. Context: '...{context}...'",
                        location=f"char {m.start()}",
                        suggestion="Rephrase to eliminate rhetorical device. Use evidence and citations instead.",
                    ))

            # Check for conclusions without supporting citations
            sentences = re.split(r'[.!?]+', text)
            conclusion_words = re.compile(
                r"\b(?:therefore|thus|hence|accordingly|consequently|it\s+follows)\b", re.I,
            )
            for i, sent in enumerate(sentences):
                if conclusion_words.search(sent) and not (_CITE_MCL.search(sent) or
                        _CITE_MCR.search(sent) or _CITE_CASE.search(sent)):
                    trimmed = sent.strip()[:80]
                    if trimmed:
                        attacks.append(Attack(
                            category="logic",
                            severity="warning",
                            title="Conclusion without citation",
                            detail=f"Sentence {i + 1} draws a conclusion without legal authority: '{trimmed}...'",
                            location=f"sentence {i + 1}",
                            suggestion="Add supporting citation or rephrase as factual statement with record cite.",
                        ))
        except Exception as exc:
            _log.error("Logic attack failed: %s", exc)
        return attacks

    # -------------------------------------------------------------------
    # Attack: Evidence
    # -------------------------------------------------------------------
    def attack_evidence(self, text: str) -> List[Attack]:
        """Challenge evidence admissibility, authentication, foundation."""
        attacks: List[Attack] = []
        try:
            # Hearsay detection
            for pattern, description in _HEARSAY_PATTERNS:
                for m in pattern.finditer(text):
                    context = text[max(0, m.start() - 30):m.end() + 30].strip()
                    attacks.append(Attack(
                        category="evidence",
                        severity="warning",
                        title="Potential hearsay",
                        detail=f"{description}. Context: '...{context}...'",
                        location=f"char {m.start()}",
                        rule="MRE 801(c), 802",
                        suggestion="Identify applicable hearsay exception (MRE 803/804) or rephrase.",
                    ))

            # Exhibit references without authentication language
            exhibit_refs = re.finditer(
                r"\b(?:Exhibit|Ex\.?)\s+([A-Z0-9]+)\b", text, re.I,
            )
            auth_language = re.compile(
                r"\b(?:attached\s+hereto|true\s+and\s+(?:correct|accurate)\s+copy|"
                r"authenticated|certified|foundation|personal\s+knowledge)\b",
                re.I,
            )
            for m in exhibit_refs:
                exhibit_id = m.group(1)
                surrounding = text[max(0, m.start() - 200):m.end() + 200]
                if not auth_language.search(surrounding):
                    attacks.append(Attack(
                        category="evidence",
                        severity="warning",
                        title=f"Exhibit {exhibit_id} — no authentication language",
                        detail="Exhibit referenced without foundation or authentication. Opposing counsel will object.",
                        location=f"char {m.start()}",
                        rule="MRE 901(a)",
                        suggestion=f"Add authentication: 'Exhibit {exhibit_id}, a true and correct copy of...'",
                    ))

            # Best evidence rule — copies
            copy_refs = re.finditer(
                r"\b(?:copy|screenshot|printout|scan)\s+of\b", text, re.I,
            )
            for m in copy_refs:
                surrounding = text[max(0, m.start() - 100):m.end() + 100]
                if not re.search(r"\b(?:original|best\s+evidence|MRE\s+100[2-8])\b", surrounding, re.I):
                    attacks.append(Attack(
                        category="evidence",
                        severity="info",
                        title="Best evidence rule concern",
                        detail="Reference to copy/screenshot without best evidence justification.",
                        location=f"char {m.start()}",
                        rule="MRE 1002-1004",
                        suggestion="Explain why original is unavailable or why copy is admissible under MRE 1003.",
                    ))
        except Exception as exc:
            _log.error("Evidence attack failed: %s", exc)
        return attacks

    # -------------------------------------------------------------------
    # Attack: Procedural
    # -------------------------------------------------------------------
    def attack_procedure(self, text: str, filing_type: str) -> List[Attack]:
        """Check procedural compliance for the filing type."""
        attacks: List[Attack] = []
        try:
            ftype = (filing_type or "").lower().strip()
            checklist = self.PROCEDURAL_CHECKS.get(ftype, [])

            # If filing type not recognized, try to detect it
            if not checklist:
                ftype = self._detect_type_from_text(text)
                checklist = self.PROCEDURAL_CHECKS.get(ftype, [])

            text_lower = text.lower()
            for requirement in checklist:
                # Build search terms from the requirement
                search_terms = self._requirement_to_terms(requirement)
                found = any(term in text_lower for term in search_terms)
                if not found:
                    attacks.append(Attack(
                        category="procedural",
                        severity="critical" if "proof of service" in requirement.lower() else "warning",
                        title=f"Missing: {requirement}",
                        detail=f"Filing type '{ftype}' requires '{requirement}' — not detected in text.",
                        rule=requirement.split()[0] if requirement.startswith("MCR") else "",
                        suggestion=f"Add required element: {requirement}.",
                    ))

            # Universal procedural checks
            if not re.search(r"\b(?:proof\s+of\s+service|certificate\s+of\s+service|"
                             r"I\s+(?:hereby\s+)?certif)", text, re.I):
                attacks.append(Attack(
                    category="procedural",
                    severity="critical",
                    title="No proof of service detected",
                    detail="Every filing must include proof of service. MCR 2.107.",
                    rule="MCR 2.107",
                    suggestion="Attach Certificate of Service with method, date, and party addresses.",
                ))

            # Check for signature block
            if not re.search(r"(?:Respectfully\s+submitted|/s/|___+\s*\n)", text, re.I):
                attacks.append(Attack(
                    category="procedural",
                    severity="warning",
                    title="No signature block detected",
                    detail="Filing appears to lack a signature block.",
                    rule="MCR 2.114",
                    suggestion="Add signature block with name, address, bar number (or pro se designation).",
                ))

            # Check for case number
            if not re.search(r"\b(?:Case\s+No\.?|File\s+No\.?|Docket)\s*:?\s*\d", text, re.I):
                attacks.append(Attack(
                    category="procedural",
                    severity="critical",
                    title="No case number detected",
                    detail="Filing must include case number in caption.",
                    suggestion="Add case number to caption block.",
                ))

        except Exception as exc:
            _log.error("Procedural attack failed: %s", exc)
        return attacks

    # -------------------------------------------------------------------
    # Attack: Credibility
    # -------------------------------------------------------------------
    def attack_credibility(self, text: str) -> List[Attack]:
        """
        Find fabricated claims, unsupported stats, exaggerations.
        Uses PROHIBITED_PATTERNS — these are ABSOLUTE red lines.
        """
        attacks: List[Attack] = []
        try:
            # Prohibited patterns — always critical
            for pattern, message in self.PROHIBITED_PATTERNS:
                for m in pattern.finditer(text):
                    matched = text[m.start():m.end()]
                    attacks.append(Attack(
                        category="credibility",
                        severity="critical",
                        title=f"PROHIBITED: {matched}",
                        detail=message,
                        location=f"char {m.start()}",
                        suggestion="Remove immediately. This WILL be attacked by opposing counsel.",
                        source="pattern",
                    ))

            # Superlatives and absolutes
            superlative_re = re.compile(
                r"\b(?:worst|best|most\s+egregious|unprecedented|never\s+before|"
                r"most\s+extreme|absolute(?:ly)?|total(?:ly)?|complete(?:ly)?)\b",
                re.I,
            )
            for m in superlative_re.finditer(text):
                context = text[max(0, m.start() - 30):m.end() + 30].strip()
                attacks.append(Attack(
                    category="credibility",
                    severity="info",
                    title=f"Superlative: '{m.group()}'",
                    detail=f"Absolute language weakens credibility. Context: '...{context}...'",
                    location=f"char {m.start()}",
                    suggestion="Replace with specific, measurable language backed by evidence.",
                ))

            # Unverified numerical claims
            big_numbers = re.compile(r"\b(\d{3,})\s+(?:incidents?|violations?|times?|occasions?|days?)\b", re.I)
            for m in big_numbers.finditer(text):
                surrounding = text[max(0, m.start() - 100):m.end() + 100]
                if not re.search(r"\[(?:SOURCE|CITE|RECORD|EXHIBIT)]", surrounding):
                    attacks.append(Attack(
                        category="credibility",
                        severity="warning",
                        title=f"Large numerical claim: {m.group(0).strip()}",
                        detail="Large number claim without source tag. Opposing counsel will demand foundation.",
                        location=f"char {m.start()}",
                        suggestion="Add [SOURCE] tag with specific record reference or exhibit number.",
                    ))
        except Exception as exc:
            _log.error("Credibility attack failed: %s", exc)
        return attacks

    # -------------------------------------------------------------------
    # Attack: Damages
    # -------------------------------------------------------------------
    def attack_damages(self, text: str) -> List[Attack]:
        """Challenge damages: speculative, double-counted, unsupported multipliers."""
        attacks: List[Attack] = []
        try:
            # Speculative damages language
            for m in _DAMAGES_SPECULATIVE.finditer(text):
                attacks.append(Attack(
                    category="damages",
                    severity="warning",
                    title=f"Speculative damages: {m.group(0).strip()[:60]}",
                    detail="Damages described with speculative language. Must be reasonably certain.",
                    location=f"char {m.start()}",
                    suggestion="Replace speculative qualifier with documented/calculated amount and methodology.",
                ))

            # Unsupported multipliers
            for m in _DAMAGES_MULTIPLIER.finditer(text):
                multiplier = m.group(1)
                attacks.append(Attack(
                    category="damages",
                    severity="warning",
                    title=f"{multiplier}x multiplier — legal basis required",
                    detail=f"Damages multiplier of {multiplier}x requires statutory or common law authority.",
                    location=f"char {m.start()}",
                    suggestion="Cite statutory basis for multiplier (e.g., treble damages under specific MCL).",
                ))

            # Emotional distress without specifics
            for m in _DAMAGES_EMOTIONAL.finditer(text):
                amount = m.group(1) if m.lastindex and m.lastindex >= 1 else ""
                attacks.append(Attack(
                    category="damages",
                    severity="warning",
                    title="Emotional distress damages claim",
                    detail=f"Emotional distress damages{' of $' + amount if amount else ''} "
                           "require specific manifestations (physical symptoms, treatment, duration).",
                    location=f"char {m.start()}",
                    rule="MCL 600.2913a",
                    suggestion="Document: (1) specific symptoms, (2) duration, (3) treatment sought, (4) impact on daily life.",
                ))

            # Double-counting detection — look for the same dollar amount appearing multiple times
            dollar_amounts = re.findall(r"\$([\d,]+(?:\.\d{2})?)", text)
            seen_amounts: Dict[str, int] = {}
            for amt in dollar_amounts:
                normalized = amt.replace(",", "")
                seen_amounts[normalized] = seen_amounts.get(normalized, 0) + 1
            for amt, count in seen_amounts.items():
                if count > 1 and float(amt) > 100:
                    attacks.append(Attack(
                        category="damages",
                        severity="warning",
                        title=f"Potential double-counting: ${amt} appears {count} times",
                        detail="Same dollar amount appears multiple times. Verify no double-counting.",
                        suggestion="Ensure each damages amount is counted only once in total calculation.",
                    ))

        except Exception as exc:
            _log.error("Damages attack failed: %s", exc)
        return attacks

    # -------------------------------------------------------------------
    # Report generation
    # -------------------------------------------------------------------
    def generate_report(
        self,
        results: Dict[str, Any],
        output_path: Optional[str] = None,
    ) -> str:
        """Generate red-team report in markdown format."""
        try:
            lines: List[str] = []
            lines.append("# 🔴 APEX Red-Team Report")
            lines.append("")
            lines.append(f"**Filing:** {results.get('filing_path', 'Unknown')}")
            lines.append(f"**Type:** {results.get('filing_type', 'Unknown')}")
            lines.append(f"**Lane:** {results.get('lane', 'N/A')}")
            lines.append(f"**Timestamp:** {results.get('timestamp', 'N/A')}")
            lines.append(f"**Method:** {results.get('method', 'rule')}")
            lines.append("")

            score = results.get("score", 0)
            if score >= 80:
                grade = "✅ PASS"
            elif score >= 60:
                grade = "⚠️ CONDITIONAL"
            else:
                grade = "🛑 FAIL — DO NOT FILE"
            lines.append(f"## Score: {score}/100 — {grade}")
            lines.append("")

            # Critical issues first
            critical = results.get("critical", [])
            if critical:
                lines.append(f"## 🚨 CRITICAL ISSUES ({len(critical)})")
                lines.append("")
                for i, c in enumerate(critical, 1):
                    title = c.get("title", "Unknown")
                    detail = c.get("detail", "")
                    suggestion = c.get("suggestion", "")
                    lines.append(f"### {i}. {title}")
                    lines.append(f"- **Detail:** {detail}")
                    if c.get("rule"):
                        lines.append(f"- **Rule:** {c['rule']}")
                    if suggestion:
                        lines.append(f"- **Fix:** {suggestion}")
                    lines.append("")

            # All attacks by category
            attacks = results.get("attacks", [])
            if attacks:
                categories: Dict[str, List[Dict]] = {}
                for a in attacks:
                    cat = a.get("category", "other")
                    categories.setdefault(cat, []).append(a)

                category_names = {
                    "credibility": "🎭 Credibility Attacks",
                    "citation": "📚 Citation Attacks",
                    "logic": "🧠 Logic Attacks",
                    "evidence": "⚖️ Evidence Attacks",
                    "procedural": "📋 Procedural Attacks",
                    "damages": "💰 Damages Attacks",
                    "counter": "🗡️ Counter-Arguments",
                }

                for cat, cat_attacks in categories.items():
                    cat_name = category_names.get(cat, f"📌 {cat.title()} Attacks")
                    lines.append(f"## {cat_name} ({len(cat_attacks)})")
                    lines.append("")
                    for a in cat_attacks:
                        sev_icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(
                            a.get("severity", "info"), "⚪"
                        )
                        lines.append(f"- {sev_icon} **{a.get('title', '')}**")
                        if a.get("detail"):
                            lines.append(f"  - {a['detail']}")
                        if a.get("suggestion"):
                            lines.append(f"  - 💡 {a['suggestion']}")
                    lines.append("")

            # Suggestions
            suggestions = results.get("suggestions", [])
            if suggestions:
                lines.append("## 💡 Top Suggestions")
                lines.append("")
                for s in suggestions:
                    lines.append(f"- {s}")
                lines.append("")

            # Summary
            if results.get("summary"):
                lines.append("## Summary")
                lines.append("")
                lines.append(results["summary"])
                lines.append("")

            report_text = "\n".join(lines)

            if output_path:
                try:
                    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                    Path(output_path).write_text(report_text, encoding="utf-8")
                    _log.info("Red-team report written to %s", output_path)
                except Exception as exc:
                    _log.error("Failed to write report to %s: %s", output_path, exc)

            return report_text

        except Exception as exc:
            _log.error("Report generation failed: %s", exc)
            return f"# Red-Team Report\n\nError generating report: {exc}"

    # ===================================================================
    # INTERNAL HELPERS
    # ===================================================================

    def _detect_type(self, filing_path: str) -> str:
        """Detect filing type from filename."""
        name = Path(filing_path).stem.lower()
        type_map = {
            "motion": "motion",
            "complaint": "complaint",
            "brief": "appellate_brief",
            "affidavit": "affidavit",
            "emergency": "emergency_motion",
            "declaration": "affidavit",
            "petition": "complaint",
            "response": "motion",
            "reply": "motion",
            "answer": "motion",
        }
        for keyword, ftype in type_map.items():
            if keyword in name:
                return ftype
        return "motion"  # default

    def _detect_type_from_text(self, text: str) -> str:
        """Detect filing type from content."""
        text_lower = text[:2000].lower()
        if "emergency" in text_lower and "motion" in text_lower:
            return "emergency_motion"
        if "affidavit" in text_lower or "jurat" in text_lower:
            return "affidavit"
        if any(w in text_lower for w in ("complaint", "counts", "prayer for relief")):
            return "complaint"
        if any(w in text_lower for w in ("table of authorities", "mcr 7.212", "statement of questions")):
            return "appellate_brief"
        if "motion" in text_lower:
            return "motion"
        return "motion"

    def _requirement_to_terms(self, requirement: str) -> List[str]:
        """Convert a procedural requirement to search terms."""
        req_lower = requirement.lower()
        term_map: Dict[str, List[str]] = {
            "mcr 2.119 format": ["mcr 2.119", "motion format"],
            "brief in support attached": ["brief in support", "memorandum", "supporting brief"],
            "proposed order attached": ["proposed order", "order granting"],
            "proof of service": ["proof of service", "certificate of service", "i hereby certif"],
            "jurisdiction stated": ["jurisdiction", "venue"],
            "parties identified": ["plaintiff", "defendant", "petitioner", "respondent"],
            "counts numbered": ["count i", "count 1", "first cause", "second cause"],
            "prayer for relief": ["prayer for relief", "wherefore", "requests this court"],
            "verification": ["verification", "verified", "under penalty of perjury"],
            "mcr 7.212 sections": ["mcr 7.212", "statement of questions", "statement of facts"],
            "word count compliant": ["word count", "words", "contains"],
            "table of authorities": ["table of authorities", "authorities cited"],
            "appendix": ["appendix", "addendum"],
            "jurat/notarization": ["jurat", "notary", "notarized", "sworn to"],
            "personal knowledge": ["personal knowledge", "personally known"],
            "competency statement": ["competent", "over the age of"],
            "mcr 2.119(f) compliance": ["mcr 2.119(f)", "2.119(f)", "emergency"],
            "irreparable harm shown": ["irreparable harm", "irreparable injury", "immediate harm"],
            "immediate hearing request": ["immediate hearing", "expedited hearing", "emergency hearing"],
        }
        return term_map.get(req_lower, [req_lower])

    def _build_suggestions(self, attacks: List[Attack]) -> List[str]:
        """Build prioritized suggestion list from attacks."""
        suggestions: List[str] = []
        critical = [a for a in attacks if a.severity == "critical"]
        warnings = [a for a in attacks if a.severity == "warning"]

        if critical:
            suggestions.append(
                f"FIX {len(critical)} CRITICAL issue(s) before filing — "
                "these will result in sanctions or dismissal."
            )
        if warnings:
            suggestions.append(
                f"Address {len(warnings)} warning(s) to strengthen filing."
            )

        # Category-specific advice
        cats = {a.category for a in attacks}
        if "credibility" in cats:
            suggestions.append("Run credibility scrub: remove all prohibited patterns and unsourced claims.")
        if "citation" in cats:
            suggestions.append("Verify all citations against Westlaw/LexisNexis or DB authorities table.")
        if "evidence" in cats:
            suggestions.append("Review all exhibit references for authentication and foundation language.")
        if "procedural" in cats:
            suggestions.append("Complete procedural checklist for this filing type before submission.")
        if "logic" in cats:
            suggestions.append("Review argument structure — ensure each conclusion cites authority.")
        if "damages" in cats:
            suggestions.append("Document damages methodology with specifics; remove speculative language.")

        return suggestions

    def _build_summary(self, result: RedTeamResult) -> str:
        """Build human-readable summary."""
        total = len(result.attacks)
        crit = len(result.critical)
        score = result.score

        if score >= 80:
            verdict = "Filing is generally sound"
        elif score >= 60:
            verdict = "Filing has significant weaknesses"
        else:
            verdict = "Filing should NOT be submitted without major revisions"

        parts = [f"{verdict}. Score: {score}/100."]
        parts.append(f"Found {total} issue(s) ({crit} critical).")

        if crit > 0:
            crit_cats = {a.category for a in result.critical}
            parts.append(f"Critical areas: {', '.join(sorted(crit_cats))}.")

        return " ".join(parts)

    def _llm_counter_arguments(self, text: str, filing_type: str) -> List[Attack]:
        """LLM-powered counter-argument generation (shadow-gated)."""
        attacks: List[Attack] = []
        if not APEX_LLM_ENABLED:
            return attacks

        inference = self._get_inference()
        if inference is None:
            return attacks

        try:
            prompt = (
                f"As opposing counsel, identify the 3 strongest counter-arguments "
                f"against this {filing_type}. For each, cite Michigan authority.\n\n"
                f"{text[:3000]}"
            )
            result = inference.query(prompt)
            if isinstance(result, dict) and result.get("answer"):
                attacks.append(Attack(
                    category="counter",
                    severity="info",
                    title="LLM Counter-Arguments",
                    detail=str(result["answer"])[:500],
                    source="llm",
                    suggestion="Review and prepare responses to these counter-arguments.",
                ))
        except Exception as exc:
            _log.debug("LLM counter-argument generation failed: %s", exc)

        return attacks

    def _persist_result(self, result: RedTeamResult) -> None:
        """Save red-team result to DB for audit trail."""
        conn = self._get_conn()
        if conn is None:
            return
        try:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS red_team_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filing_path TEXT,
                    filing_type TEXT,
                    lane TEXT,
                    score INTEGER,
                    attack_count INTEGER,
                    critical_count INTEGER,
                    method TEXT,
                    summary TEXT,
                    full_result TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                )""",
            )
            conn.execute(
                """INSERT INTO red_team_results
                   (filing_path, filing_type, lane, score, attack_count, critical_count,
                    method, summary, full_result)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    result.filing_path,
                    result.filing_type,
                    result.lane,
                    result.score,
                    len(result.attacks),
                    len(result.critical),
                    result.method,
                    result.summary,
                    json.dumps(result.to_dict(), default=str),
                ),
            )
            conn.commit()
        except Exception as exc:
            _log.debug("Failed to persist red-team result: %s", exc)


# -----------------------------------------------------------------------
# CLI entry point
# -----------------------------------------------------------------------
def main() -> None:
    """CLI: python auto_red_team.py <filing_path> [--type TYPE] [--lane LANE] [--output PATH]"""
    import argparse

    # UTF-8 stdout
    if hasattr(sys.stdout, "fileno"):
        try:
            sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="APEX Auto Red-Team — adversarial filing review")
    parser.add_argument("filing", help="Path to the filing to red-team")
    parser.add_argument("--type", dest="filing_type", default=None, help="Filing type override")
    parser.add_argument("--lane", default=None, help="Case lane (A-F)")
    parser.add_argument("--output", default=None, help="Output report path")
    parser.add_argument("--json", action="store_true", help="Output as JSON instead of markdown")
    parser.add_argument("--db", default=None, help="Override DB path")

    args = parser.parse_args()

    rt = AutoRedTeam(db_path=args.db)
    results = rt.red_team(args.filing, filing_type=args.filing_type, lane=args.lane)

    if args.json:
        print(json.dumps(results, indent=2, default=str))
    else:
        report = rt.generate_report(results, output_path=args.output)
        print(report)

    sys.exit(0 if results.get("score", 0) >= 60 else 1)


if __name__ == "__main__":
    main()
