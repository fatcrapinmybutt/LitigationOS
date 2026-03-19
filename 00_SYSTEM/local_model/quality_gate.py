#!/usr/bin/env python3
"""
APEX Quality Gate — Validates all outputs before delivery
═════════════════════════════════════════════════════════
Works 100 % without LLM using rule-based checks.
LLM adds optional neural verification when available.

Every agent output, filing draft, and document section should pass
through :meth:`QualityGate.validate` before being delivered to the
user or written to a court filing.  The gate enforces:

* **Prohibited patterns** — known factual errors, fabricated stats,
  wrong names, and privacy violations specific to Pigors v. Watson.
* **Filing requirements** — structural completeness per MCR rules.
* **Lane contamination** — ensures evidence stays in its case lane.
* **Citation format** — validates MCL / MCR / CFR / USC references.
* **Placeholders** — catches unresolved ``[TODO]``, ``[TBD]``,
  ``[ANDREW_REQUIRED]``, etc.
* **Optional LLM review** — when ``APEX_LLM_ENABLED=true``, the gate
  submits the text for neural compliance review.

Design invariants
─────────────────
* Same ``APEX_LLM_ENABLED`` flag as :mod:`ollama_provider`.
* Thread-safe — compiled regexes are immutable, instance methods use
  no shared mutable state.
* NEVER imports from the repo root (shadow modules).
* Uses ``Path(__file__).parent`` for sibling imports.
* Zero-crash: every public method is try/excepted.
* All DB connections use the mandatory PRAGMA set.

Usage::

    >>> gate = QualityGate()
    >>> result = gate.validate("Emily Ann Watson filed a motion...", filing_type="motion")
    >>> result["passed"]
    False
    >>> result["issues"][0]["message"]
    "WRONG NAME: Use 'Emily A. Watson'"
"""

from __future__ import annotations

import importlib.util
import logging
import os
import re
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ──────────────────────────────────────────────────────────────────────
# Global LLM gate — mirrors ollama_provider.py
# ──────────────────────────────────────────────────────────────────────
APEX_LLM_ENABLED: bool = (
    os.environ.get("APEX_LLM_ENABLED", "false").lower() == "true"
)

# ──────────────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────────────
_log = logging.getLogger("apex.quality_gate")
if not _log.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter(
        "%(asctime)s [%(name)s] %(levelname)s — %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    ))
    _log.addHandler(_h)
    _log.setLevel(logging.DEBUG if APEX_LLM_ENABLED else logging.INFO)

# ──────────────────────────────────────────────────────────────────────
# Path helpers
# ──────────────────────────────────────────────────────────────────────
_THIS_DIR: Path = Path(__file__).resolve().parent


def _load_sibling(module_name: str) -> Any:
    """Import a sibling module without touching the repo root."""
    mod_path = _THIS_DIR / f"{module_name}.py"
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
        _log.warning("Failed to import sibling %s: %s", module_name, exc)
        return None


# ╔══════════════════════════════════════════════════════════════════════╗
# ║                   PROHIBITED PATTERN REGISTRY                       ║
# ╚══════════════════════════════════════════════════════════════════════╝
# Each tuple: (compiled_regex, severity, correction_message)
# Severity levels: "error" (blocks filing), "warning" (flag but allow)

_PROHIBITED_RAW: List[Tuple[str, str, str]] = [
    # ── Name errors ──────────────────────────────────────────────
    (
        r"Emily\s+Ann\s+Watson",
        "error",
        "WRONG NAME: Use 'Emily A. Watson'",
    ),
    (
        r"Emily\s+M\.\s+Watson",
        "error",
        "WRONG NAME: Use 'Emily A. Watson'",
    ),
    (
        r"Tiffany\s+Watson",
        "error",
        "WRONG NAME: Use 'Emily A. Watson'",
    ),
    # ── Fabricated statistics ────────────────────────────────────
    (
        r"9\s+CPS\s+investigations",
        "error",
        "FABRICATED: CPS called ONCE by Andrew",
    ),
    (
        r"nine\s+(?:CPS|police)\s+investigations",
        "error",
        "FABRICATED: Use 'multiple investigations [ANDREW_REQUIRED]'",
    ),
    (
        r"91%\s+alienation",
        "error",
        "PSEUDO-SCIENTIFIC: Use '305 documented interference incidents'",
    ),
    (
        r"Gardner.*?alienation\s+score",
        "error",
        "PSEUDO-SCIENTIFIC: Use documented incidents + MCL 722.23(j)",
    ),
    # ── Privacy violations ───────────────────────────────────────
    (
        r"Lincoln\s+David\s+Watson",
        "error",
        "PRIVACY: Use 'L.D.W.' per MCR 8.119(H)",
    ),
    # ── Wrong facts ──────────────────────────────────────────────
    (
        r"(?<!\d)11\s+ex\s*parte",
        "error",
        "WRONG COUNT: Correct is 24 ex parte orders",
    ),
    (
        r"26\.8%",
        "error",
        "WRONG RATE: Correct ex parte rate is 18.26%",
    ),
    (
        r"Muskegon,?\s+MI\s+49445",
        "error",
        "WRONG ADDRESS: Use 'Laketon Township, MI 49445'",
    ),
    # ── Common hallucination markers ─────────────────────────────
    (
        r"As an AI(?:\s+language model)?",
        "warning",
        "LLM LEAK: Remove AI self-reference",
    ),
    (
        r"I (?:cannot|can't|don't have) access to",
        "warning",
        "LLM LEAK: Remove AI capability disclaimer",
    ),
]

# Pre-compile once at import time
_PROHIBITED_PATTERNS: List[Tuple[re.Pattern, str, str]] = []
for _pat, _sev, _msg in _PROHIBITED_RAW:
    try:
        _PROHIBITED_PATTERNS.append((re.compile(_pat, re.IGNORECASE), _sev, _msg))
    except re.error as _exc:
        _log.warning("Failed to compile pattern %r: %s", _pat, _exc)


# ╔══════════════════════════════════════════════════════════════════════╗
# ║                   FILING REQUIREMENTS REGISTRY                      ║
# ╚══════════════════════════════════════════════════════════════════════╝
_FILING_REQUIREMENTS: Dict[str, List[str]] = {
    "motion": [
        "caption",
        "relief_requested",
        "statement_of_facts",
        "argument",
        "conclusion",
        "signature",
        "certificate_of_service",
    ],
    "complaint": [
        "caption",
        "jurisdiction",
        "venue",
        "parties",
        "factual_allegations",
        "counts",
        "prayer_for_relief",
        "verification",
        "signature",
    ],
    "brief": [
        "caption",
        "table_of_contents",
        "table_of_authorities",
        "statement_of_issues",
        "statement_of_facts",
        "argument",
        "conclusion",
        "signature",
    ],
    "affidavit": [
        "caption",
        "affiant_identity",
        "factual_statements",
        "oath",
        "notary",
    ],
}

# Heuristic heading patterns for detecting filing sections
_SECTION_DETECTORS: Dict[str, re.Pattern] = {}
_SECTION_PATTERNS: Dict[str, str] = {
    "caption": r"(?:STATE\s+OF\s+MICHIGAN|CIRCUIT\s+COURT|DISTRICT\s+COURT|Case\s+No)",
    "relief_requested": r"(?:RELIEF\s+REQUESTED|WHEREFORE|respectfully\s+requests?)",
    "statement_of_facts": r"(?:STATEMENT\s+OF\s+FACTS|FACTUAL\s+BACKGROUND)",
    "argument": r"(?:ARGUMENT|LEGAL\s+ANALYSIS|DISCUSSION)",
    "conclusion": r"(?:CONCLUSION|SUMMARY)",
    "signature": r"(?:Respectfully\s+submitted|/s/|____+)",
    "certificate_of_service": r"(?:CERTIFICATE\s+OF\s+SERVICE|I\s+(?:hereby\s+)?certify)",
    "jurisdiction": r"(?:JURISDICTION|(?:this|the)\s+Court\s+has\s+jurisdiction)",
    "venue": r"(?:VENUE|venue\s+is\s+proper)",
    "parties": r"(?:PARTIES|Plaintiff\s+is|Defendant\s+is)",
    "factual_allegations": r"(?:FACTUAL\s+ALLEGATIONS|ALLEGATIONS\s+OF\s+FACT)",
    "counts": r"(?:COUNT\s+[IVX\d]+|CAUSE\s+OF\s+ACTION)",
    "prayer_for_relief": r"(?:PRAYER\s+FOR\s+RELIEF|WHEREFORE)",
    "verification": r"(?:VERIFICATION|under\s+penalty\s+of\s+perjury)",
    "table_of_contents": r"(?:TABLE\s+OF\s+CONTENTS)",
    "table_of_authorities": r"(?:TABLE\s+OF\s+AUTHORITIES)",
    "statement_of_issues": r"(?:STATEMENT\s+OF\s+(?:THE\s+)?ISSUES?\s+PRESENTED)",
    "affiant_identity": r"(?:affiant|deponent|declarant)\s+(?:states?|declares?)",
    "factual_statements": r"(?:\d+\.\s+(?:That|I\s+))",
    "oath": r"(?:sworn|affirm|under\s+oath|penalty\s+of\s+perjury)",
    "notary": r"(?:NOTARY|Notary\s+Public|My\s+commission\s+expires)",
}
for _k, _v in _SECTION_PATTERNS.items():
    try:
        _SECTION_DETECTORS[_k] = re.compile(_v, re.IGNORECASE | re.MULTILINE)
    except re.error:
        pass


# ╔══════════════════════════════════════════════════════════════════════╗
# ║                    LANE KEYWORD REGISTRY                            ║
# ╚══════════════════════════════════════════════════════════════════════╝
_LANE_KEYWORDS: Dict[str, List[str]] = {
    "A": ["custody", "parenting", "Watson", "L.D.W.", "best interest", "MCL 722"],
    "B": ["housing", "Shady Oaks", "habitability", "tenant", "MCL 125", "Truth in Renting"],
    "C": ["convergence", "cross-lane", "conspiracy", "coordinated"],
    "D": ["PPO", "protection order", "MCL 600.2950", "stalking"],
    "E": ["misconduct", "McNeill", "JTC", "MCR 9.2", "judicial"],
    "F": ["appellate", "COA", "MSC", "MCR 7.2", "appeal"],
}

# ╔══════════════════════════════════════════════════════════════════════╗
# ║                   CITATION FORMAT PATTERNS                          ║
# ╚══════════════════════════════════════════════════════════════════════╝
_CITATION_PATTERNS: Dict[str, re.Pattern] = {}
_CITE_RAW: Dict[str, str] = {
    "mcl": r"MCL\s+\d+\.\d+[a-z]?(?:\(\d+\))*",
    "mcr": r"MCR\s+\d+\.\d+(?:\([A-Z]\))?(?:\(\d+\))?",
    "usc": r"\d+\s+U\.?S\.?C\.?\s+(?:§\s*)?\d+",
    "cfr": r"\d+\s+C\.?F\.?R\.?\s+(?:§\s*)?\d+",
    "mich_case": r"\d+\s+Mich(?:\s+App)?\s+\d+",
    "nw2d": r"\d+\s+NW\s*2d\s+\d+",
    "fed_case": r"\d+\s+F\.?\s*(?:2d|3d|4th|Supp(?:\.\s*2d)?)\s+\d+",
}
for _k, _v in _CITE_RAW.items():
    try:
        _CITATION_PATTERNS[_k] = re.compile(_v, re.IGNORECASE)
    except re.error:
        pass

# Placeholder patterns
_PLACEHOLDER_RE = re.compile(
    r"\[(?:ANDREW_REQUIRED|TBD|TODO|FILL\s*IN|INSERT|PLACEHOLDER|CITE|XX+|___+)\]",
    re.IGNORECASE,
)


# ╔══════════════════════════════════════════════════════════════════════╗
# ║                        QUALITY GATE                                 ║
# ╚══════════════════════════════════════════════════════════════════════╝

class QualityGate:
    """Validates agent outputs — rule-based by default, LLM-enhanced when available.

    All public methods return structured dicts and never raise exceptions.

    Example::

        >>> gate = QualityGate()
        >>> r = gate.validate("Emily Ann Watson filed...", filing_type="motion")
        >>> r["passed"]
        False
    """

    # Expose registries as class attributes for external inspection
    PROHIBITED_PATTERNS = _PROHIBITED_RAW
    FILING_REQUIREMENTS = _FILING_REQUIREMENTS
    LANE_KEYWORDS = _LANE_KEYWORDS

    def __init__(self) -> None:
        self._router: Any = None
        _log.debug("QualityGate initialised (LLM %s)",
                    "enabled" if APEX_LLM_ENABLED else "disabled")

    # ── Lazy LLM loader ─────────────────────────────────────────

    def _get_router(self) -> Any:
        """Lazy-load ModelRouter for optional LLM verification."""
        if not APEX_LLM_ENABLED:
            return None
        if self._router is not None:
            return self._router
        try:
            mod = _load_sibling("model_router")
            if mod and hasattr(mod, "ModelRouter"):
                self._router = mod.ModelRouter()
        except Exception as exc:
            _log.warning("ModelRouter unavailable for QualityGate: %s", exc)
        return self._router

    # ── Primary validation entry point ───────────────────────────

    def validate(
        self,
        text: str,
        filing_type: Optional[str] = None,
        expected_lane: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Full validation suite.

        Parameters
        ----------
        text : str
            Document or filing text to validate.
        filing_type : str, optional
            One of ``motion``, ``complaint``, ``brief``, ``affidavit``.
        expected_lane : str, optional
            Expected case lane (``A``–``F``).

        Returns
        -------
        dict
            ``{'passed': bool, 'score': 0-100, 'issues': [...],
              'warnings': [...], 'llm_review': str}``
        """
        try:
            issues: List[Dict[str, Any]] = []
            warnings: List[Dict[str, Any]] = []

            # 1. Prohibited patterns (most critical)
            prohibited = self.check_prohibited_patterns(text)
            for item in prohibited:
                if item.get("severity") == "error":
                    issues.append(item)
                else:
                    warnings.append(item)

            # 2. Filing requirements
            if filing_type:
                missing = self.check_filing_requirements(text, filing_type)
                for item in missing:
                    issues.append(item)

            # 3. Lane contamination
            if expected_lane:
                contam = self.check_lane_contamination(text, expected_lane)
                for item in contam:
                    warnings.append(item)

            # 4. Citation format
            cite_issues = self.check_citations(text)
            for item in cite_issues:
                warnings.append(item)

            # 5. Placeholders
            placeholders = self.check_placeholders(text)
            for item in placeholders:
                issues.append(item)

            # 6. Basic length / emptiness checks
            if not text or not text.strip():
                issues.append({
                    "check": "emptiness",
                    "message": "Document is empty",
                    "severity": "error",
                })

            # 7. Compute score
            raw_score = self.score(text, filing_type=filing_type)

            # 8. Optional LLM review
            llm_review = ""
            if APEX_LLM_ENABLED and text.strip():
                llm_review = self._llm_review(text, filing_type)

            # Determine pass/fail
            has_blocking = any(i.get("severity") == "error" for i in issues)
            passed = (raw_score >= 70) and not has_blocking

            return {
                "passed": passed,
                "score": raw_score,
                "issues": issues,
                "warnings": warnings,
                "issue_count": len(issues),
                "warning_count": len(warnings),
                "llm_review": llm_review,
                "llm_used": bool(llm_review),
                "filing_type": filing_type,
                "expected_lane": expected_lane,
            }
        except Exception as exc:
            _log.error("validate() failed: %s", exc)
            return {
                "passed": False,
                "score": 0,
                "issues": [{"check": "internal", "message": str(exc), "severity": "error"}],
                "warnings": [],
                "issue_count": 1,
                "warning_count": 0,
                "llm_review": "",
                "llm_used": False,
                "error": str(exc),
            }

    # ── Individual check methods ─────────────────────────────────

    def check_prohibited_patterns(self, text: str) -> List[Dict[str, Any]]:
        """Check for known error patterns.

        Returns
        -------
        list of dict
            Each: ``{'check', 'pattern', 'message', 'severity', 'line_number', 'match'}``
        """
        results: List[Dict[str, Any]] = []
        if not text:
            return results
        try:
            lines = text.split("\n")
            for compiled, severity, message in _PROHIBITED_PATTERNS:
                for line_idx, line in enumerate(lines, 1):
                    for m in compiled.finditer(line):
                        results.append({
                            "check": "prohibited_pattern",
                            "pattern": compiled.pattern,
                            "message": message,
                            "severity": severity,
                            "line_number": line_idx,
                            "match": m.group(0),
                        })
        except Exception as exc:
            _log.warning("check_prohibited_patterns error: %s", exc)
        return results

    def check_filing_requirements(
        self, text: str, filing_type: str
    ) -> List[Dict[str, Any]]:
        """Check for required filing elements.

        Returns
        -------
        list of dict
            Each: ``{'check', 'section', 'message', 'severity'}``
        """
        results: List[Dict[str, Any]] = []
        if not text or not filing_type:
            return results
        try:
            required = _FILING_REQUIREMENTS.get(filing_type.lower(), [])
            for section in required:
                detector = _SECTION_DETECTORS.get(section)
                if detector:
                    if not detector.search(text):
                        results.append({
                            "check": "filing_requirement",
                            "section": section,
                            "message": f"Missing required section: {section}",
                            "severity": "error",
                            "filing_type": filing_type,
                        })
                else:
                    # No detector pattern — use simple keyword presence
                    keyword = section.replace("_", " ")
                    if keyword.lower() not in text.lower():
                        results.append({
                            "check": "filing_requirement",
                            "section": section,
                            "message": f"Missing required section: {section}",
                            "severity": "error",
                            "filing_type": filing_type,
                        })
        except Exception as exc:
            _log.warning("check_filing_requirements error: %s", exc)
        return results

    def check_lane_contamination(
        self, text: str, expected_lane: str
    ) -> List[Dict[str, Any]]:
        """Check for cross-lane contamination.

        Parameters
        ----------
        text : str
            Document text.
        expected_lane : str
            Expected lane (``A``–``F``).

        Returns
        -------
        list of dict
            Each: ``{'check', 'expected_lane', 'detected_lane', 'keyword',
                     'message', 'severity'}``
        """
        results: List[Dict[str, Any]] = []
        if not text or not expected_lane:
            return results
        try:
            expected_upper = expected_lane.upper()
            text_lower = text.lower()
            for lane, keywords in _LANE_KEYWORDS.items():
                if lane == expected_upper:
                    continue  # skip the expected lane
                # Skip lane C (convergence) — it's intentionally cross-lane
                if lane == "C":
                    continue
                for keyword in keywords:
                    if keyword.lower() in text_lower:
                        results.append({
                            "check": "lane_contamination",
                            "expected_lane": expected_upper,
                            "detected_lane": lane,
                            "keyword": keyword,
                            "message": (
                                f"Possible lane {lane} content in lane "
                                f"{expected_upper} document (keyword: '{keyword}')"
                            ),
                            "severity": "warning",
                        })
        except Exception as exc:
            _log.warning("check_lane_contamination error: %s", exc)
        return results

    def check_citations(self, text: str) -> List[Dict[str, Any]]:
        """Check citation format and flag potential issues.

        Verifies that citations match recognised formats (MCL, MCR,
        USC, CFR, Michigan case reporters, NW2d, Federal reporters).
        Reports any bare statute numbers without proper identifiers.

        Returns
        -------
        list of dict
            Each: ``{'check', 'message', 'severity', 'detail'}``
        """
        results: List[Dict[str, Any]] = []
        if not text:
            return results
        try:
            # Collect all recognised citations
            found_cites: List[str] = []
            for _name, pattern in _CITATION_PATTERNS.items():
                found_cites.extend(m.group(0) for m in pattern.finditer(text))

            # Check for bare section symbols without proper prefix
            bare_section = re.findall(r"(?<!\w)§\s*\d+\.\d+", text)
            for bare in bare_section:
                # See if this is part of a recognised citation
                is_covered = any(bare.strip() in c for c in found_cites)
                if not is_covered:
                    results.append({
                        "check": "citation_format",
                        "message": f"Bare section reference '{bare.strip()}' — add statute prefix (MCL, USC, etc.)",
                        "severity": "warning",
                        "detail": bare.strip(),
                    })

            # Check for incomplete case citations (e.g. "Smith v Jones" without reporter)
            case_name_re = re.compile(
                r"\b([A-Z][a-z]+)\s+v\.?\s+([A-Z][a-z]+)\b"
            )
            for m in case_name_re.finditer(text):
                # Look ahead for a reporter reference within 80 chars
                after = text[m.end():m.end() + 80]
                has_reporter = any(
                    p.search(after) for p in _CITATION_PATTERNS.values()
                )
                if not has_reporter:
                    results.append({
                        "check": "citation_format",
                        "message": (
                            f"Case reference '{m.group(0)}' may lack a reporter "
                            f"citation — add Mich App / NW2d / F.3d cite"
                        ),
                        "severity": "warning",
                        "detail": m.group(0),
                    })

        except Exception as exc:
            _log.warning("check_citations error: %s", exc)
        return results

    def check_placeholders(self, text: str) -> List[Dict[str, Any]]:
        """Find unresolved placeholders.

        Returns
        -------
        list of dict
            Each: ``{'check', 'placeholder', 'line_number', 'message', 'severity'}``
        """
        results: List[Dict[str, Any]] = []
        if not text:
            return results
        try:
            for line_idx, line in enumerate(text.split("\n"), 1):
                for m in _PLACEHOLDER_RE.finditer(line):
                    results.append({
                        "check": "placeholder",
                        "placeholder": m.group(0),
                        "line_number": line_idx,
                        "message": f"Unresolved placeholder: {m.group(0)}",
                        "severity": "error",
                    })
        except Exception as exc:
            _log.warning("check_placeholders error: %s", exc)
        return results

    def score(
        self, text: str, filing_type: Optional[str] = None
    ) -> int:
        """Overall quality score 0–100.

        Starts at 100 and deducts points for each issue found:
        - Prohibited pattern (error):   −15 each
        - Prohibited pattern (warning): −5 each
        - Missing filing section:        −10 each
        - Unresolved placeholder:        −10 each
        - Empty document:                −100

        Parameters
        ----------
        text : str
            Document text.
        filing_type : str, optional
            Filing type for structural checks.

        Returns
        -------
        int
            Quality score clamped to ``[0, 100]``.
        """
        try:
            if not text or not text.strip():
                return 0

            points = 100

            # Prohibited patterns
            for item in self.check_prohibited_patterns(text):
                if item.get("severity") == "error":
                    points -= 15
                else:
                    points -= 5

            # Filing requirements
            if filing_type:
                missing = self.check_filing_requirements(text, filing_type)
                points -= len(missing) * 10

            # Placeholders
            placeholders = self.check_placeholders(text)
            points -= len(placeholders) * 10

            # Very short document penalty
            if len(text.strip()) < 200:
                points -= 10

            return max(0, min(100, points))
        except Exception as exc:
            _log.warning("score() error: %s", exc)
            return 0

    # ── LLM-enhanced review (optional) ───────────────────────────

    def _llm_review(
        self, text: str, filing_type: Optional[str] = None
    ) -> str:
        """Submit text for neural compliance review via ModelRouter.

        Returns the LLM's review text, or an empty string on failure.
        """
        if not APEX_LLM_ENABLED:
            return ""
        router = self._get_router()
        if router is None:
            return ""
        try:
            ft_label = filing_type or "document"
            prompt = (
                f"Review this Michigan {ft_label} for legal compliance. "
                f"Flag any factual errors, missing elements, or MCR "
                f"violations. Be concise (3-5 bullet points max):\n\n"
                f"{text[:4000]}"
            )
            result = router.route(prompt, task_type="legal_reasoning")
            if isinstance(result, dict):
                return result.get("answer", "")
            return str(result) if result else ""
        except Exception as exc:
            _log.warning("LLM review failed: %s", exc)
            return ""

    # ── Utility ──────────────────────────────────────────────────

    def __repr__(self) -> str:
        return (
            f"<QualityGate patterns={len(_PROHIBITED_PATTERNS)} "
            f"filing_types={list(_FILING_REQUIREMENTS.keys())} "
            f"llm={'enabled' if APEX_LLM_ENABLED else 'disabled'}>"
        )


# ──────────────────────────────────────────────────────────────────────
# CLI entry point
# ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    sys.stdout = open(
        sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace"
    )
    import json as _json  # safe — running from __file__ dir

    gate = QualityGate()
    if len(sys.argv) > 1:
        # Validate a file
        fpath = Path(sys.argv[1])
        if fpath.exists():
            content = fpath.read_text(encoding="utf-8", errors="replace")
            ft = sys.argv[2] if len(sys.argv) > 2 else None
            lane = sys.argv[3] if len(sys.argv) > 3 else None
            result = gate.validate(content, filing_type=ft, expected_lane=lane)
            print(_json.dumps(result, indent=2, default=str))
        else:
            print(f"File not found: {fpath}")
    else:
        # Demo with a known-bad snippet
        demo = (
            "Emily Ann Watson filed a motion in Muskegon, MI 49445.\n"
            "There were 9 CPS investigations and a 91% alienation score.\n"
            "Lincoln David Watson was present at the hearing.\n"
            "[TODO] — complete argument section.\n"
        )
        result = gate.validate(demo, filing_type="motion", expected_lane="A")
        print(_json.dumps(result, indent=2, default=str))
