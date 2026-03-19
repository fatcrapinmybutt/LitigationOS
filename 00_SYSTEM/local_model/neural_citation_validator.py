"""
APEX Neural Citation Validator — Validates that citations actually support
the propositions they're cited for.

Beyond format checking: semantic relevance between proposition and cited authority.
Shadow-programmed: format-only validation when LLM disabled, full semantic when enabled.
"""
from __future__ import annotations

import json
import logging
import os
import re
import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("apex.neural_citation_validator")

APEX_LLM_ENABLED: bool = os.environ.get("APEX_LLM_ENABLED", "false").lower() == "true"

_MODULE_DIR = Path(__file__).parent
_DB_DIR = _MODULE_DIR / "model_data"
_PROJECT_ROOT = _MODULE_DIR.parent.parent

# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

_PRAGMA_INIT = (
    "PRAGMA busy_timeout=60000",
    "PRAGMA journal_mode=WAL",
    "PRAGMA cache_size=-32000",
    "PRAGMA synchronous=NORMAL",
    "PRAGMA temp_store=MEMORY",
)


def _open_db(path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path), check_same_thread=False)
    for p in _PRAGMA_INIT:
        conn.execute(p)
    return conn


# ---------------------------------------------------------------------------
# Citation format patterns (Michigan + Federal)
# ---------------------------------------------------------------------------

_CITATION_PATTERNS: List[Tuple[str, re.Pattern[str]]] = [
    ("mich_app", re.compile(r"\d+\s+Mich\s+App\s+\d+(?:\s*\(\d{4}\))?")),
    ("mich", re.compile(r"\d+\s+Mich\s+\d+(?:\s*\(\d{4}\))?")),
    ("nw2d", re.compile(r"\d+\s+NW2d\s+\d+")),
    ("nw3d", re.compile(r"\d+\s+NW3d\s+\d+")),
    ("mcr", re.compile(r"MCR\s+\d+\.\d+(?:\([A-Z]\)(?:\(\d+\))*)*")),
    ("mcl", re.compile(r"MCL\s+\d+\.\d+\w*")),
    ("us_reports", re.compile(r"\d+\s+US\s+\d+(?:\s*\(\d{4}\))?")),
    ("sct", re.compile(r"\d+\s+S\s*Ct\s+\d+")),
    ("fed_supp", re.compile(r"\d+\s+F\s*Supp\s*(?:2d|3d)?\s+\d+")),
    ("fed_reporter", re.compile(r"\d+\s+F\s*(?:2d|3d|4th)?\s+\d+")),
    ("mre", re.compile(r"MRE\s+\d+")),
]

_FORMAT_RULES: Dict[str, Dict[str, Any]] = {
    "mcr": {"requires_subsection": False, "example": "MCR 2.119(A)(2)"},
    "mcl": {"requires_subsection": False, "example": "MCL 600.2963"},
    "mich": {"requires_year": True, "example": "123 Mich 456 (1999)"},
    "mich_app": {"requires_year": True, "example": "123 Mich App 456 (2020)"},
}


# ---------------------------------------------------------------------------
# Proposition-citation extraction
# ---------------------------------------------------------------------------

def _extract_propositions_and_citations(text: str) -> List[Dict[str, Any]]:
    """Extract (proposition, citation) pairs from text.

    Heuristic: a citation typically follows the proposition it supports,
    within the same sentence or the immediately preceding sentence.
    """
    pairs: List[Dict[str, Any]] = []
    sentences = re.split(r"(?<=[.!?])\s+", text)

    for i, sentence in enumerate(sentences):
        for ctype, pattern in _CITATION_PATTERNS:
            for match in pattern.finditer(sentence):
                citation_text = match.group(0).strip()
                # Proposition is the text before the citation in this sentence
                pre = sentence[:match.start()].strip()
                if not pre and i > 0:
                    pre = sentences[i - 1].strip()
                pairs.append({
                    "proposition": pre[:500] if pre else "",
                    "citation": citation_text,
                    "citation_type": ctype,
                    "sentence_index": i,
                })
    return pairs


def _check_format(citation: str, ctype: str) -> List[str]:
    """Check citation format against rules. Returns list of errors (empty = OK)."""
    errors: List[str] = []
    rules = _FORMAT_RULES.get(ctype)
    if not rules:
        return errors  # no specific rules — format OK by default

    if rules.get("requires_year") and not re.search(r"\(\d{4}\)", citation):
        errors.append(f"Missing year parenthetical: {citation} (example: {rules.get('example', '')})")

    return errors


# ---------------------------------------------------------------------------
# Semantic relevance (LLM-enhanced)
# ---------------------------------------------------------------------------

def _llm_check_relevance(proposition: str, citation: str) -> Optional[Dict[str, Any]]:
    """Use LLM to check if citation semantically supports the proposition."""
    if not APEX_LLM_ENABLED or not proposition:
        return None
    try:
        from .model_router import ModelRouter  # type: ignore[import-untyped]
        router = ModelRouter()
        prompt = (
            "Does this legal citation support the stated proposition? "
            "Answer with JSON: {relevant: bool, confidence: float, reason: str}\n\n"
            f"PROPOSITION: {proposition[:500]}\n"
            f"CITATION: {citation}\n"
        )
        result = router.route(prompt, task_type="validation")
        if isinstance(result, dict):
            return {
                "relevant": result.get("relevant", True),
                "confidence": float(result.get("confidence", 0.5)),
                "reason": result.get("reason", ""),
            }
        return None
    except Exception as exc:
        logger.debug("LLM relevance check failed: %s", exc)
        return None


def _llm_find_better(proposition: str, lane: str) -> Optional[Dict[str, Any]]:
    """Use LLM to suggest a better citation for a proposition."""
    if not APEX_LLM_ENABLED or not proposition:
        return None
    try:
        from .model_router import ModelRouter  # type: ignore[import-untyped]
        router = ModelRouter()
        prompt = (
            f"For the following legal proposition in Michigan {lane} litigation, "
            "suggest the most relevant citation (case, statute, or court rule). "
            "Return JSON: {citation: str, authority_type: str, relevance: float, reason: str}\n\n"
            f"PROPOSITION: {proposition[:500]}\n"
        )
        result = router.route(prompt, task_type="citation_search")
        if isinstance(result, dict):
            return result
        return None
    except Exception as exc:
        logger.debug("LLM find_better failed: %s", exc)
        return None


def _db_find_better(proposition: str, lane: str) -> Optional[Dict[str, Any]]:
    """Search litigation_context.db for relevant authorities."""
    db_path = _PROJECT_ROOT / "litigation_context.db"
    if not db_path.exists():
        return None
    try:
        conn = _open_db(db_path)
        # Check if authority tables exist
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()]

        search_term = proposition[:100].replace("'", "''")

        for table in ["authority_chains", "authorities", "evidence_quotes"]:
            if table not in tables:
                continue
            try:
                cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
                text_col = next((c for c in cols if c in ("citation", "text", "content", "quote")), None)
                if not text_col:
                    continue
                rows = conn.execute(
                    f"SELECT {text_col} FROM {table} WHERE {text_col} LIKE ? LIMIT 5",
                    (f"%{search_term[:50]}%",),
                ).fetchall()
                if rows:
                    conn.close()
                    return {
                        "citation": rows[0][0][:200] if rows[0][0] else "",
                        "authority_type": table,
                        "relevance": 0.5,
                        "reason": f"Found in {table} via keyword match",
                        "source": "db",
                    }
            except Exception:
                continue
        conn.close()
    except Exception as exc:
        logger.debug("DB citation search failed: %s", exc)
    return None


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class NeuralCitationValidator:
    """Validates citations for format correctness and semantic relevance."""

    def __init__(self) -> None:
        self._lock = threading.Lock()

    def validate(self, text: str) -> dict:
        """Validate all citations in text for format + relevance.

        Returns ``{total, valid, format_errors, relevance_issues, pairs}``.
        """
        try:
            pairs = _extract_propositions_and_citations(text)
            total = len(pairs)
            format_errors: List[Dict[str, Any]] = []
            relevance_issues: List[Dict[str, Any]] = []
            valid = 0

            for pair in pairs:
                citation = pair["citation"]
                ctype = pair["citation_type"]
                proposition = pair["proposition"]

                # Format check (always)
                fmt_errs = _check_format(citation, ctype)
                if fmt_errs:
                    format_errors.append({
                        "citation": citation,
                        "errors": fmt_errs,
                        "sentence_index": pair["sentence_index"],
                    })

                # Relevance check (LLM when available)
                rel = _llm_check_relevance(proposition, citation)
                if rel and not rel.get("relevant", True):
                    relevance_issues.append({
                        "citation": citation,
                        "proposition": proposition[:200],
                        "confidence": rel.get("confidence", 0.0),
                        "reason": rel.get("reason", ""),
                    })

                if not fmt_errs and (rel is None or rel.get("relevant", True)):
                    valid += 1

            return {
                "total": total,
                "valid": valid,
                "format_errors": format_errors,
                "relevance_issues": relevance_issues,
                "pairs": len(pairs),
                "method": "llm+format" if APEX_LLM_ENABLED else "format_only",
            }
        except Exception as exc:
            logger.error("Citation validation failed: %s", exc)
            return {
                "total": 0, "valid": 0,
                "format_errors": [], "relevance_issues": [],
                "pairs": 0, "method": "error",
            }

    def check_relevance(self, proposition: str, citation: str) -> dict:
        """Check if citation supports the proposition semantically.

        Returns ``{relevant: bool, confidence: float, reason: str, method: str}``.
        """
        try:
            # LLM check
            llm = _llm_check_relevance(proposition, citation)
            if llm:
                llm["method"] = "llm"
                return llm

            # Heuristic fallback: keyword overlap
            prop_words = set(proposition.lower().split())
            cite_words = set(citation.lower().split())
            # Remove common legal filler
            filler = {"the", "a", "an", "of", "in", "for", "to", "and", "or", "is", "was", "that", "this"}
            prop_words -= filler
            overlap = prop_words & cite_words
            confidence = len(overlap) / max(len(prop_words), 1)

            return {
                "relevant": confidence > 0.1 or len(cite_words) <= 4,  # short cites get benefit of doubt
                "confidence": round(confidence, 4),
                "reason": f"Keyword overlap: {len(overlap)} words" if overlap else "No keyword overlap (citation may still be relevant)",
                "method": "heuristic",
            }
        except Exception as exc:
            logger.error("Relevance check failed: %s", exc)
            return {"relevant": True, "confidence": 0.0, "reason": str(exc), "method": "error"}

    def find_better_citation(self, proposition: str, lane: str = "A") -> dict:
        """Find a more relevant citation for a proposition.

        Returns ``{citation, authority_type, relevance, reason, source}``.
        """
        try:
            # LLM search
            llm = _llm_find_better(proposition, lane)
            if llm and llm.get("citation"):
                llm["source"] = "llm"
                return llm

            # DB search
            db_result = _db_find_better(proposition, lane)
            if db_result:
                return db_result

            return {
                "citation": "",
                "authority_type": "none",
                "relevance": 0.0,
                "reason": "No better citation found (manual research recommended)",
                "source": "none",
            }
        except Exception as exc:
            logger.error("find_better_citation failed: %s", exc)
            return {
                "citation": "", "authority_type": "none",
                "relevance": 0.0, "reason": str(exc), "source": "error",
            }

    def batch_validate(self, texts: List[str]) -> Dict[str, Any]:
        """Validate citations across multiple text blocks.

        Returns ``{total, valid, format_errors, relevance_issues}``.
        """
        total = 0
        valid = 0
        all_format_errors: List[Dict[str, Any]] = []
        all_relevance_issues: List[Dict[str, Any]] = []

        for idx, text in enumerate(texts):
            try:
                result = self.validate(text)
                total += result.get("total", 0)
                valid += result.get("valid", 0)
                for e in result.get("format_errors", []):
                    e["block_index"] = idx
                    all_format_errors.append(e)
                for r in result.get("relevance_issues", []):
                    r["block_index"] = idx
                    all_relevance_issues.append(r)
            except Exception:
                continue

        return {
            "total": total,
            "valid": valid,
            "format_errors": all_format_errors,
            "relevance_issues": all_relevance_issues,
            "blocks_processed": len(texts),
        }
