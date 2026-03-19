"""
Unified Citation Extractor — LitigationOS Legal AI
====================================================
Extracts, validates, and classifies legal citations from text using
a multi-engine pipeline: regex patterns → eyecite → DB cross-reference.

Supports:
  - Michigan: MCR x.xxx, MCL xxx.xx, MRE xxx, Mich/Mich App reporters
  - Federal: USC, F.3d, F.Supp., US Reports, S.Ct.
  - Validation against litigation_context.db authority tables
  - Confidence scoring per citation
  - Deduplication and canonical form normalization

Usage:
    from legal_ai.citation_extractor import CitationExtractor
    cx = CitationExtractor()
    results = cx.extract("MCR 2.003 requires disqualification per 449 Mich 123")
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

logger = logging.getLogger("legal_ai.citations")

_HERE = Path(__file__).parent
_REPO = _HERE.parent.parent
_DB_PATH = _REPO / "litigation_context.db"


# ── Data Models ──────────────────────────────────────────────────

@dataclass
class CitationMatch:
    """A single extracted citation with metadata."""
    raw_text: str
    canonical: str
    citation_type: str          # case, statute, rule, regulation, constitution
    jurisdiction: str           # michigan, federal, scotus, sixth_circuit
    reporter: str = ""
    volume: str = ""
    page: str = ""
    pin_cite: str = ""
    year: str = ""
    court: str = ""
    start_offset: int = 0
    end_offset: int = 0
    confidence: float = 0.0
    db_verified: bool = False
    is_good_law: Optional[bool] = None
    source_engine: str = ""     # regex, eyecite, combined


@dataclass
class ExtractionResult:
    """Complete citation extraction result."""
    citations: List[CitationMatch] = field(default_factory=list)
    unique_statutes: List[str] = field(default_factory=list)
    unique_rules: List[str] = field(default_factory=list)
    unique_cases: List[str] = field(default_factory=list)
    total_found: int = 0
    extraction_time_ms: float = 0.0
    engines_used: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# ── Citation Patterns ────────────────────────────────────────────

MICHIGAN_PATTERNS: List[Tuple[str, str, str, str]] = [
    # (pattern, citation_type, reporter, jurisdiction)
    (r"MCR\s+(\d+\.\d+(?:\([A-Za-z0-9]+\))*(?:\([A-Za-z0-9]+\))*)",
     "rule", "MCR", "michigan"),
    (r"MCL\s+(\d+\.\d+[a-z]?(?:\([0-9]+\))*(?:\([a-z]\))*)",
     "statute", "MCL", "michigan"),
    (r"MRE\s+(\d+(?:\([a-z]\))*)",
     "rule", "MRE", "michigan"),
    (r"(\d+)\s+Mich\s+App\s+(\d+)",
     "case", "Mich App", "michigan"),
    (r"(\d+)\s+Mich\s+(\d+)",
     "case", "Mich", "michigan"),
    (r"(\d+)\s+NW\.?\s*2d\s+(\d+)",
     "case", "NW2d", "michigan"),
]

FEDERAL_PATTERNS: List[Tuple[str, str, str, str]] = [
    (r"(\d+)\s+U\.?S\.?\s+(\d+)",
     "case", "US", "scotus"),
    (r"(\d+)\s+S\.?\s*Ct\.?\s+(\d+)",
     "case", "S.Ct.", "scotus"),
    (r"(\d+)\s+L\.?\s*Ed\.?\s*2d\s+(\d+)",
     "case", "L.Ed.2d", "scotus"),
    (r"(\d+)\s+F\.?\s*3d\s+(\d+)",
     "case", "F.3d", "sixth_circuit"),
    (r"(\d+)\s+F\.?\s*4th\s+(\d+)",
     "case", "F.4th", "sixth_circuit"),
    (r"(\d+)\s+F\.?\s*(?:Supp\.?\s*(?:2d|3d))\s+(\d+)",
     "case", "F.Supp.", "federal"),
    (r"(\d+)\s+USC?\s+[§]?\s*(\d+[a-z]?(?:\([a-z0-9]+\))*)",
     "statute", "USC", "federal"),
    (r"42\s+U\.?S\.?C\.?\s+[§]?\s*(\d{4}[a-z]?)",
     "statute", "42 USC", "federal"),
    (r"28\s+U\.?S\.?C\.?\s+[§]?\s*(\d{4}[a-z]?)",
     "statute", "28 USC", "federal"),
]

CONSTITUTION_PATTERNS: List[Tuple[str, str, str, str]] = [
    (r"((?:First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth|Tenth|"
     r"Eleventh|Twelfth|Thirteenth|Fourteenth|Fifteenth)\s+Amendment)",
     "constitution", "US Const.", "federal"),
    (r"(?:U\.?S\.?\s*Const\.?\s*(?:art\.?\s*[IVX]+|amend\.?\s*[IVXLC]+))",
     "constitution", "US Const.", "federal"),
    (r"(Const\s+1963,?\s*art\s+\d+,?\s*[§]?\s*\d+)",
     "constitution", "MI Const.", "michigan"),
]

# Known hallucinated citations — NEVER validate as good law
KNOWN_HALLUCINATED: Set[str] = {
    "282 Mich App 647",   # McCraney v Ford Motor Co (FABRICATED)
    "2012 Mich App LEXIS 1764",  # Cease v AAA Michigan (FABRICATED)
}


# ── Citation Extractor Engine ────────────────────────────────────

class CitationExtractor:
    """Multi-engine citation extractor with validation."""

    def __init__(
        self,
        db_path: Optional[str] = None,
        use_eyecite: bool = True,
        validate_against_db: bool = True,
    ):
        self.db_path = db_path or str(_DB_PATH)
        self._use_eyecite = use_eyecite
        self._validate = validate_against_db
        self._eyecite_available = False
        self._eyecite_mod = None
        self._init_eyecite()

    def _init_eyecite(self) -> None:
        """Lazy-load eyecite with graceful fallback."""
        if not self._use_eyecite:
            return
        try:
            import eyecite
            self._eyecite_mod = eyecite
            self._eyecite_available = True
            logger.info("eyecite v%s loaded", getattr(eyecite, "__version__", "?"))
        except ImportError:
            logger.warning("eyecite not installed — using regex-only extraction")

    def extract(self, text: str) -> ExtractionResult:
        """Extract all citations from text using all available engines."""
        t0 = time.perf_counter()
        result = ExtractionResult()
        seen_canonical: Set[str] = set()

        # Engine 1: Regex patterns (always available)
        regex_cites = self._extract_regex(text)
        for c in regex_cites:
            if c.canonical not in seen_canonical:
                seen_canonical.add(c.canonical)
                result.citations.append(c)
        if regex_cites:
            result.engines_used.append("regex")

        # Engine 2: eyecite (if available)
        if self._eyecite_available:
            ec_cites = self._extract_eyecite(text)
            for c in ec_cites:
                if c.canonical not in seen_canonical:
                    seen_canonical.add(c.canonical)
                    result.citations.append(c)
            if ec_cites:
                result.engines_used.append("eyecite")

        # Validate against DB
        if self._validate and result.citations:
            self._validate_citations(result)

        # Flag hallucinated citations
        for c in result.citations:
            if c.canonical in KNOWN_HALLUCINATED or c.raw_text in KNOWN_HALLUCINATED:
                c.is_good_law = False
                c.confidence = 0.0
                result.warnings.append(
                    f"HALLUCINATED citation detected: {c.raw_text}"
                )

        # Classify unique citations
        for c in result.citations:
            if c.citation_type == "statute":
                result.unique_statutes.append(c.canonical)
            elif c.citation_type == "rule":
                result.unique_rules.append(c.canonical)
            elif c.citation_type == "case":
                result.unique_cases.append(c.canonical)

        result.unique_statutes = sorted(set(result.unique_statutes))
        result.unique_rules = sorted(set(result.unique_rules))
        result.unique_cases = sorted(set(result.unique_cases))
        result.total_found = len(result.citations)
        result.extraction_time_ms = (time.perf_counter() - t0) * 1000

        return result

    # ── Regex Engine ─────────────────────────────────────────────

    def _extract_regex(self, text: str) -> List[CitationMatch]:
        """Extract citations via compiled regex patterns."""
        citations: List[CitationMatch] = []
        all_patterns = (
            MICHIGAN_PATTERNS + FEDERAL_PATTERNS + CONSTITUTION_PATTERNS
        )

        for pattern, cite_type, reporter, jurisdiction in all_patterns:
            for m in re.finditer(pattern, text, re.IGNORECASE):
                raw = m.group(0).strip()
                canonical = self._normalize_canonical(raw, cite_type, reporter)
                citations.append(CitationMatch(
                    raw_text=raw,
                    canonical=canonical,
                    citation_type=cite_type,
                    jurisdiction=jurisdiction,
                    reporter=reporter,
                    volume=m.group(1) if m.lastindex and m.lastindex >= 1 else "",
                    page=m.group(2) if m.lastindex and m.lastindex >= 2 else "",
                    start_offset=m.start(),
                    end_offset=m.end(),
                    confidence=0.85,
                    source_engine="regex",
                ))
        return citations

    # ── eyecite Engine ───────────────────────────────────────────

    def _extract_eyecite(self, text: str) -> List[CitationMatch]:
        """Extract citations via eyecite library."""
        if not self._eyecite_available or not self._eyecite_mod:
            return []

        citations: List[CitationMatch] = []
        try:
            found = self._eyecite_mod.get_citations(text)
            for cite in found:
                raw = str(cite)
                cite_type = "case"
                reporter = ""
                jurisdiction = "unknown"

                if hasattr(cite, "groups") and cite.groups:
                    reporter = str(getattr(cite.groups[0], "reporter", ""))

                # Determine jurisdiction from reporter
                if any(r in reporter.lower() for r in ["mich", "nw"]):
                    jurisdiction = "michigan"
                elif any(r in reporter.lower() for r in ["u.s.", "s.ct.", "l.ed."]):
                    jurisdiction = "scotus"
                elif any(r in reporter.lower() for r in ["f.3d", "f.4th", "f.2d"]):
                    jurisdiction = "sixth_circuit"

                canonical = self._normalize_canonical(raw, cite_type, reporter)
                citations.append(CitationMatch(
                    raw_text=raw,
                    canonical=canonical,
                    citation_type=cite_type,
                    jurisdiction=jurisdiction,
                    reporter=reporter,
                    confidence=0.90,
                    source_engine="eyecite",
                ))
        except Exception as exc:
            logger.warning("eyecite extraction error: %s", exc)

        return citations

    # ── DB Validation ────────────────────────────────────────────

    def _validate_citations(self, result: ExtractionResult) -> None:
        """Cross-reference citations against litigation_context.db."""
        if not os.path.exists(self.db_path):
            result.warnings.append(f"DB not found: {self.db_path}")
            return

        try:
            conn = sqlite3.connect(self.db_path, timeout=30)
            conn.execute("PRAGMA busy_timeout = 60000")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA cache_size = -32000")
            conn.row_factory = sqlite3.Row

            # Check which validation tables exist
            tables = {row[0] for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()}

            for cite in result.citations:
                cite.db_verified = self._check_db(conn, cite, tables)
                if cite.db_verified:
                    cite.confidence = min(1.0, cite.confidence + 0.10)

            conn.close()
        except sqlite3.Error as exc:
            result.warnings.append(f"DB validation error: {exc}")

    def _check_db(
        self,
        conn: sqlite3.Connection,
        cite: CitationMatch,
        tables: Set[str],
    ) -> bool:
        """Check if a citation exists in any authority table."""
        search_text = cite.canonical or cite.raw_text

        # Check master_citations table
        if "master_citations" in tables:
            try:
                row = conn.execute(
                    "SELECT 1 FROM master_citations WHERE citation_text LIKE ? LIMIT 1",
                    (f"%{search_text}%",),
                ).fetchone()
                if row:
                    return True
            except sqlite3.Error:
                pass

        # Check authority_library
        if "authority_library" in tables:
            try:
                row = conn.execute(
                    "SELECT 1 FROM authority_library WHERE citation LIKE ? LIMIT 1",
                    (f"%{search_text}%",),
                ).fetchone()
                if row:
                    return True
            except sqlite3.Error:
                pass

        # Check court_rules for MCR/MRE
        if cite.reporter in ("MCR", "MRE") and "court_rules" in tables:
            try:
                row = conn.execute(
                    "SELECT 1 FROM court_rules WHERE rule_number LIKE ? LIMIT 1",
                    (f"%{cite.volume}%",),
                ).fetchone()
                if row:
                    return True
            except sqlite3.Error:
                pass

        return False

    # ── Normalization ────────────────────────────────────────────

    @staticmethod
    def _normalize_canonical(
        raw: str, cite_type: str, reporter: str
    ) -> str:
        """Normalize citation to canonical form."""
        text = re.sub(r"\s+", " ", raw).strip()

        if cite_type == "rule" and reporter == "MCR":
            m = re.search(r"MCR\s+([\d.()A-Za-z]+)", text, re.IGNORECASE)
            return f"MCR {m.group(1)}" if m else text

        if cite_type == "statute" and reporter == "MCL":
            m = re.search(r"MCL\s+([\d.()a-z]+)", text, re.IGNORECASE)
            return f"MCL {m.group(1)}" if m else text

        if cite_type == "rule" and reporter == "MRE":
            m = re.search(r"MRE\s+([\d()a-z]+)", text, re.IGNORECASE)
            return f"MRE {m.group(1)}" if m else text

        if cite_type == "case":
            # Normalize common reporter formats
            text = re.sub(r"\s+", " ", text)
            return text

        return text

    # ── Batch Processing ─────────────────────────────────────────

    def extract_batch(
        self,
        texts: List[str],
        labels: Optional[List[str]] = None,
    ) -> Dict[str, ExtractionResult]:
        """Extract citations from multiple texts."""
        results: Dict[str, ExtractionResult] = {}
        for i, text in enumerate(texts):
            label = labels[i] if labels and i < len(labels) else f"doc_{i}"
            results[label] = self.extract(text)
        return results

    def extract_from_file(self, filepath: str) -> ExtractionResult:
        """Extract citations from a text file."""
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
            return self.extract(text)
        except (OSError, IOError) as exc:
            result = ExtractionResult()
            result.warnings.append(f"File read error: {exc}")
            return result

    # ── Statistics ────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Return engine status and capabilities."""
        return {
            "version": "1.0.0",
            "eyecite_available": self._eyecite_available,
            "db_validation": self._validate,
            "db_path": self.db_path,
            "db_exists": os.path.exists(self.db_path),
            "michigan_patterns": len(MICHIGAN_PATTERNS),
            "federal_patterns": len(FEDERAL_PATTERNS),
            "constitution_patterns": len(CONSTITUTION_PATTERNS),
            "known_hallucinated": len(KNOWN_HALLUCINATED),
        }
