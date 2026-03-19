"""
skill_convergence_engine.py — Convergence Engine
==================================================
LitigationOS 2026 v2.0 — Pigors v. Watson

Multi-cycle quality improvement engine for court documents.
Iterates until convergence: quality >= 97%, zero placeholders, zero gaps.

Scoring dimensions:
  1. Citation density & accuracy (MCL/MCR/MRE/case law)
  2. IRAC structure (Issue/Rule/Application/Conclusion) — keyword + structural
  3. Document completeness (caption, parties, body, prayer, sig, CoS)
  4. Chess-mode defense anticipation — adversary-model-aware (v2)
  5. Placeholder elimination
  6. MCR format compliance
  7. Parental alienation theme integration
  8. Evidence density / record references — weighted record refs (v2)

v2.0 enhancements:
  - Quality tiers (CRITICAL / WORK / POLISH / NEAR / CONVERGED)
  - Memory-aware analysis via analyze_with_memory()
  - Adversary-model-backed chess mode scoring
  - Weighted record-reference evidence scoring
  - Improvement priority matrix (impact/effort ranking)
  - Structural IRAC block detection

Tracks every improvement cycle in convergence_cycles table.
Declares convergence when overall quality >= 97% AND zero placeholders.

No network calls. Pure SQLite + text analysis.
"""

import sqlite3
import re
import os
import sys
import json
from typing import Optional, Dict, List, Any, Tuple

DB_PATH = r"C:\Users\andre\litigation_context.db"
VEHICLES_ROOT = r"C:\Users\andre\LitigationOS\06_VEHICLES"

# Add parent to path for sibling skill imports
_SKILLS_DIR = os.path.dirname(os.path.abspath(__file__))
if _SKILLS_DIR not in sys.path:
    sys.path.insert(0, _SKILLS_DIR)

# ── Scoring Weights ─────────────────────────────────────────────────────────

DIMENSION_WEIGHTS = {
    "citation_score": 1.5,
    "irac_score": 1.3,
    "completeness_score": 1.2,
    "chess_mode_score": 1.0,
    "placeholder_score": 1.5,
    "mcr_compliance_score": 1.4,
    "parental_alienation_score": 0.8,
    "evidence_density_score": 0.8,
}

# ── Quality Tiers (v2.0) ────────────────────────────────────────────────────

QUALITY_TIERS = {
    "CRITICAL": (0, 60),
    "WORK": (60, 75),
    "POLISH": (75, 90),
    "NEAR": (90, 97),
    "CONVERGED": (97, 101),
}


def get_tier(score: float) -> str:
    """Map an overall score to a quality tier label."""
    for tier, (lo, hi) in QUALITY_TIERS.items():
        if lo <= score < hi:
            return tier
    return "CONVERGED"

# ── Improvement Priority Matrix (v2.0) ──────────────────────────────────────

IMPROVEMENT_PRIORITY = {
    "chess_mode_score": {"impact": 5, "effort": 3, "label": "HIGH IMPACT"},
    "evidence_density_score": {"impact": 5, "effort": 4, "label": "HIGH IMPACT"},
    "irac_score": {"impact": 4, "effort": 4, "label": "MEDIUM"},
    "citation_score": {"impact": 3, "effort": 2, "label": "QUICK WIN"},
    "placeholder_score": {"impact": 5, "effort": 1, "label": "QUICK WIN"},
    "mcr_compliance_score": {"impact": 3, "effort": 3, "label": "MEDIUM"},
    "parental_alienation_score": {"impact": 2, "effort": 2, "label": "QUICK WIN"},
    "completeness_score": {"impact": 4, "effort": 5, "label": "HEAVY LIFT"},
}

# ── Legal Bracket Terms (NOT placeholders) ──────────────────────────────────

LEGAL_BRACKET_OK = [
    "factor", "emphasis", "sic", "internal", "citation", "omitted",
    "him", "her", "father", "mother", "child", "complainant",
    "cleaned up", "alterations", "quotation marks", "footnote",
    "redacted", "sealed",
]

# ── MCR Citation Patterns ───────────────────────────────────────────────────

CITE_PATTERNS = [
    r"MCL\s+\d+[.\d]*[a-z]*(?:\([a-z0-9]+\))*",
    r"MCR\s+\d+\.\d+(?:\([A-Z]\))?(?:\(\d+\))?(?:\([a-z]\))?",
    r"MRE\s+\d+(?:\([a-z]\))?(?:\(\d+\))?",
    r"\d+\s+Mich\s+App\s+\d+",
    r"\d+\s+Mich\s+\d+",
    r"\d+\s+NW\s*2d\s+\d+",
    r"US\s+Const\s+Amend\s+[IVXLCDM]+",
    r"Const\s+1963,?\s+art\s+\d+",
]

CITE_RE = re.compile("|".join(CITE_PATTERNS))

# ── Placeholder Detection ───────────────────────────────────────────────────

PLACEHOLDER_RE = re.compile(r"\[[A-Z][A-Za-z_ /]+\]")

# ── IRAC Marker Sets ────────────────────────────────────────────────────────

IRAC_MARKERS = {
    "issue": [
        "issue:", "the issue is", "question presented", "whether the",
        "the question before this court",
    ],
    "rule": [
        "rule:", "the governing rule", "pursuant to", "under mcl", "under mcr",
        "this court applies", "the standard is", "is governed by",
    ],
    "application": [
        "application:", "applying this", "in this case", "here,",
        "the facts show", "the record demonstrates", "on these facts",
    ],
    "conclusion": [
        "conclusion:", "therefore", "accordingly", "for these reasons",
        "this court should", "relief is warranted", "reversal is required",
    ],
}

# ── Completeness Sections ───────────────────────────────────────────────────

COMPLETENESS_SECTIONS = {
    "caption": ["state of michigan", "circuit court", "case no", "court of appeals"],
    "parties": ["plaintiff", "defendant", "appellant", "appellee"],
    "body": ["comes now", "states as follows", "respectfully shows"],
    "prayer": ["prayer for relief", "wherefore", "respectfully requests"],
    "signature": ["respectfully submitted", "/s/", "dated"],
    "certificate_of_service": ["certificate of service", "served", "copy of the"],
}

# ── Chess-Mode Markers ──────────────────────────────────────────────────────

CHESS_MARKERS = [
    "anticipat", "defendant may argue", "defense will likely",
    "rebuttal", "counter-argument", "however this fails",
    "this argument fails", "pre-empt", "forestall",
    "watson will likely", "watson may contend", "opposing counsel",
    "even if defendant", "even assuming arguendo",
]

# ── Alienation Theme Markers ────────────────────────────────────────────────

ALIENATION_MARKERS = [
    "parental alienation", "alienat", "329", "days",
    "separation", "factor j", "factor (j)", "mcl 722.23",
    "parent-child", "bonding", "withhold", "deny",
    "parenting time", "best interest", "custodial environment",
]

# ── Evidence Reference Markers ──────────────────────────────────────────────

EVIDENCE_MARKERS = [
    "exhibit", "attached hereto", "see attached", "evidence shows",
    "as documented", "the record reflects", "transcript at",
    "order dated", "hearing of", "testimony", "affidavit",
    "docket entry", "record at",
]

# ── Record Reference Patterns (v2.0) ────────────────────────────────────────

RECORD_REF_PATTERNS = [
    r"R\.\s*at\s+\d+",                                                # R. at 15
    r"Tr\.\s*at\s+\d+",                                               # Tr. at 42
    r"Exhibit\s+[A-Z0-9]+",                                           # Exhibit A, Exhibit 12
    r"Docket\s+Entry\s+\d+",                                          # Docket Entry 45
    r"\d+[a-z]?\s*Tr\s+\d+",                                          # 1a Tr 42
    r"(?:Hearing|Order)\s+(?:of|dated)\s+\d{1,2}/\d{1,2}/\d{2,4}",   # Hearing of 11/26/2025
]
RECORD_REF_RE = re.compile("|".join(RECORD_REF_PATTERNS))


# ═════════════════════════════════════════════════════════════════════════════
# ConvergenceEngine
# ═════════════════════════════════════════════════════════════════════════════

class ConvergenceEngine:
    """Multi-cycle quality improvement engine for court documents."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.convergence_threshold = 97.0
        self.max_cycles = 10
        self._error_log: List[str] = []

    # ── Connection helper ────────────────────────────────────────────────

    def _connect(self) -> sqlite3.Connection:
        """Connect to litigation_context.db with retry."""
        last_err = None
        for attempt in range(3):
            try:
                conn = sqlite3.connect(self.db_path, timeout=10)
                conn.execute("SELECT 1")
                return conn
            except sqlite3.Error as e:
                last_err = e
                import time
                time.sleep(2 ** attempt)
        self._error_log.append(f"DB connect failed after 3 retries: {last_err}")
        raise last_err

    # ── Primary Analysis ─────────────────────────────────────────────────

    def analyze(self, file_path: str) -> Dict[str, Any]:
        """Full quality analysis of a court document."""
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        scores = {
            "citation_score": self._score_citations(content),
            "irac_score": self._score_irac(content),
            "completeness_score": self._score_completeness(content),
            "chess_mode_score": self._score_chess_mode(content),
            "placeholder_score": self._score_placeholders(content),
            "mcr_compliance_score": self._score_mcr_compliance(content),
            "parental_alienation_score": self._score_alienation_theme(content),
            "evidence_density_score": self._score_evidence_density(content),
        }

        # Weighted overall score
        weighted_sum = sum(scores[k] * DIMENSION_WEIGHTS[k] for k in scores)
        weight_total = sum(DIMENSION_WEIGHTS[k] for k in scores)
        overall = round(weighted_sum / weight_total, 1)

        placeholders = self._find_placeholders(content)
        improvements = self._identify_improvements(content, scores)
        citations = CITE_RE.findall(content)

        return {
            "file": os.path.basename(file_path),
            "path": file_path,
            "scores": scores,
            "overall": overall,
            "converged": overall >= self.convergence_threshold and len(placeholders) == 0,
            "tier": get_tier(overall),
            "placeholders": placeholders,
            "placeholder_count": len(placeholders),
            "improvements": improvements,
            "word_count": len(content.split()),
            "citation_count": len(citations),
            "unique_citations": len(set(citations)),
        }

    # ── Memory-Aware Analysis (v2.0) ─────────────────────────────────────

    def analyze_with_memory(self, file_path: str, memory_pack: Dict = None) -> Dict[str, Any]:
        """Enhanced analysis using memory pack for DB-backed scoring."""
        # Run standard analysis first
        result = self.analyze(file_path)

        if memory_pack:
            # Re-score chess mode with adversary models
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            adversary = memory_pack.get("adversary_rebuttals", [])
            if adversary:
                result["scores"]["chess_mode_score"] = self._score_chess_mode_v2(content, adversary)

            # Score evidence utilization (how much of the memory pack evidence is actually cited)
            evidence = memory_pack.get("evidence", [])
            if evidence:
                cited = sum(1 for e in evidence if any(
                    kw.lower() in content.lower()
                    for kw in str(e.get("quote_text", "")).split()[:5]
                ))
                result["evidence_utilization"] = round(cited / max(len(evidence), 1) * 100, 1)

            # Recalculate overall with updated scores
            scores = result["scores"]
            weighted_sum = sum(scores[k] * DIMENSION_WEIGHTS[k] for k in scores)
            weight_total = sum(DIMENSION_WEIGHTS[k] for k in scores)
            result["overall"] = round(weighted_sum / weight_total, 1)
            result["converged"] = result["overall"] >= self.convergence_threshold and result["placeholder_count"] == 0

        # Add / update quality tier
        result["tier"] = get_tier(result["overall"])

        return result

    # ── Scoring Functions ────────────────────────────────────────────────

    def _score_citations(self, text: str) -> float:
        """Citation density and variety (0-100)."""
        citations = CITE_RE.findall(text)
        word_count = max(len(text.split()), 1)
        density = len(citations) / (word_count / 1000)
        variety_bonus = min(15, len(set(citations)) * 1.5)
        raw = density * 8 + variety_bonus
        return round(min(100, max(0, raw)), 1)

    def _score_irac(self, text: str) -> float:
        """IRAC structure presence — keyword + structural detection (0-100)."""
        text_lower = text.lower()

        # --- Original keyword scoring (v1.0) ---
        keyword_score = 0.0
        for component, markers in IRAC_MARKERS.items():
            hits = sum(1 for m in markers if m in text_lower)
            if hits >= 2:
                keyword_score += 25
            elif hits == 1:
                keyword_score += 18

        # --- Structural IRAC block detection (v2.0) ---
        structural_bonus = 0.0
        # Check for section headers containing IRAC labels
        irac_header_re = re.compile(
            r"^[\s#*]*(?:(?:\d+\.?\s*)?(?:I\.|II\.|III\.|IV\.|A\.|B\.)?)\s*"
            r"(issue|rule|application|analysis|conclusion|relief)"
            r"\b",
            re.IGNORECASE | re.MULTILINE,
        )
        header_hits = set(m.group(1).lower() for m in irac_header_re.finditer(text))
        # Normalize "analysis" → "application"
        if "analysis" in header_hits:
            header_hits.add("application")
        irac_components_found = header_hits & {"issue", "rule", "application", "conclusion", "relief"}
        if len(irac_components_found) >= 3:
            structural_bonus = 20.0
        elif len(irac_components_found) >= 2:
            structural_bonus = 10.0

        # Check for numbered argument sections that follow IRAC flow
        numbered_section_re = re.compile(
            r"(?:^|\n)\s*(?:[IVXLC]+\.|[A-Z]\.|[\d]+\.)\s*\S",
            re.MULTILINE,
        )
        numbered_sections = len(numbered_section_re.findall(text))
        if numbered_sections >= 4:
            structural_bonus += 5.0

        return round(min(100, keyword_score + structural_bonus), 1)

    def _score_completeness(self, text: str) -> float:
        """Document section completeness (0-100)."""
        text_lower = text.lower()
        found = 0
        for section, markers in COMPLETENESS_SECTIONS.items():
            if any(m in text_lower for m in markers):
                found += 1
        return round(found / len(COMPLETENESS_SECTIONS) * 100, 1)

    def _score_chess_mode(self, text: str) -> float:
        """Defense anticipation / adversarial reasoning (0-100)."""
        text_lower = text.lower()
        hits = sum(1 for m in CHESS_MARKERS if m in text_lower)
        return round(min(100, hits * 10), 1)

    def _score_chess_mode_v2(self, text: str, adversary_models: List[Dict] = None) -> float:
        """Adversary-model-aware chess mode scoring (v2.0).

        Runs v1 keyword check, then awards bonus points for each adversary
        attack vector whose rebuttal_strategy keywords appear in the document.
        """
        base = self._score_chess_mode(text)
        if not adversary_models:
            return base

        text_lower = text.lower()
        bonus = 0.0
        for model in adversary_models:
            rebuttal = str(model.get("rebuttal_strategy", "")).lower()
            if not rebuttal:
                continue
            # Check if any substantive keyword (4+ chars) from the rebuttal appears
            keywords = [w for w in rebuttal.split() if len(w) >= 4]
            if keywords and any(kw in text_lower for kw in keywords):
                bonus += 5.0

        return round(min(100, base + bonus), 1)

    def _score_placeholders(self, text: str) -> float:
        """Placeholder elimination score (100 = clean, 0 = many)."""
        placeholders = self._find_placeholders(text)
        if not placeholders:
            return 100.0
        return round(max(0, 100 - len(placeholders) * 10), 1)

    def _score_mcr_compliance(self, text: str) -> float:
        """MCR format compliance (0-100)."""
        text_lower = text.lower()
        checks = {
            "numbered_paragraphs": bool(re.search(r"^\s*\d+\.\s", text, re.MULTILINE)),
            "caption_present": "state of michigan" in text_lower or "court of appeals" in text_lower,
            "verification_or_affirmation": (
                "penalties of perjury" in text_lower
                or "verification" in text_lower
                or "affirm" in text_lower
            ),
            "certificate_of_service": "certificate of service" in text_lower,
            "court_rule_citation": bool(re.search(r"MCR\s+\d+\.\d+", text)),
            "case_number": bool(re.search(r"(?:Case|Docket)\s*(?:No|#)\.?\s*[\d\-]+", text, re.IGNORECASE)),
            "proper_title": bool(re.search(
                r"(?:MOTION|BRIEF|AFFIDAVIT|APPLICATION|COMPLAINT|ORDER|PETITION)",
                text,
            )),
        }
        return round(sum(checks.values()) / len(checks) * 100, 1)

    def _score_alienation_theme(self, text: str) -> float:
        """Parental alienation theme integration (0-100)."""
        text_lower = text.lower()
        hits = sum(1 for m in ALIENATION_MARKERS if m in text_lower)
        return round(min(100, hits * 7), 1)

    def _score_evidence_density(self, text: str) -> float:
        """Evidence reference density — keyword + weighted record refs (v2.0).

        Old keyword markers count 1 point each; actual record reference
        patterns (R. at, Tr. at, Exhibit X, etc.) count 3 points each.
        """
        text_lower = text.lower()
        keyword_hits = sum(1 for m in EVIDENCE_MARKERS if m in text_lower)
        record_hits = len(RECORD_REF_RE.findall(text))
        word_count = max(len(text.split()), 1)
        raw = (keyword_hits * 1 + record_hits * 3) / (word_count / 1000 + 1) * 10
        return round(min(100, max(0, raw)), 1)

    # ── Placeholder Detection ────────────────────────────────────────────

    def _find_placeholders(self, text: str) -> List[str]:
        """Find all remaining placeholder brackets (excluding legal terms)."""
        all_brackets = PLACEHOLDER_RE.findall(text)
        return [
            p for p in all_brackets
            if not any(ok in p.lower() for ok in LEGAL_BRACKET_OK)
        ]

    # ── Improvement Identification ───────────────────────────────────────

    def _identify_improvements(self, text: str, scores: Dict[str, float]) -> List[str]:
        """Generate specific, actionable improvement recommendations, sorted by priority."""
        raw: List[Tuple[str, str]] = []  # (dimension_key, message)

        if scores["citation_score"] < 80:
            raw.append((
                "citation_score",
                "ADD CITATIONS: Insert MCL/MCR/case law references — "
                f"current density score {scores['citation_score']}%",
            ))
        if scores["irac_score"] < 75:
            raw.append((
                "irac_score",
                "STRENGTHEN IRAC: Add explicit Issue/Rule/Application/Conclusion sections",
            ))
        if scores["completeness_score"] < 83:
            missing = self._find_missing_sections(text)
            raw.append((
                "completeness_score",
                f"COMPLETE DOCUMENT: Add missing sections — {', '.join(missing)}",
            ))
        if scores["chess_mode_score"] < 60:
            raw.append((
                "chess_mode_score",
                "ADD CHESS MODE: Anticipate defendant arguments and pre-rebut "
                "(\"Watson may argue...\", \"This argument fails because...\")",
            ))
        if scores["placeholder_score"] < 100:
            placeholders = self._find_placeholders(text)
            raw.append((
                "placeholder_score",
                f"ELIMINATE PLACEHOLDERS ({len(placeholders)}): "
                + ", ".join(placeholders[:5])
                + ("..." if len(placeholders) > 5 else ""),
            ))
        if scores["mcr_compliance_score"] < 85:
            raw.append((
                "mcr_compliance_score",
                "FIX MCR COMPLIANCE: Ensure caption, numbering, CoS, case number, title",
            ))
        if scores["parental_alienation_score"] < 70:
            raw.append((
                "parental_alienation_score",
                "INJECT ALIENATION THEME: Reference 329+ days separation, "
                "Factor J, MCL 722.23, parent-child bond",
            ))
        if scores["evidence_density_score"] < 50:
            raw.append((
                "evidence_density_score",
                "ADD EVIDENCE REFS: Reference specific exhibits, transcripts, "
                "docket entries, and record page numbers",
            ))

        # Sort by impact/effort ratio (highest first) using IMPROVEMENT_PRIORITY
        def _priority_key(item: Tuple[str, str]) -> float:
            dim = item[0]
            pri = IMPROVEMENT_PRIORITY.get(dim, {"impact": 1, "effort": 5})
            return -(pri["impact"] / max(pri["effort"], 1))

        raw.sort(key=_priority_key)

        # Format with priority label
        improvements: List[str] = []
        for dim, msg in raw:
            label = IMPROVEMENT_PRIORITY.get(dim, {}).get("label", "")
            prefix = f"[{label}] " if label else ""
            improvements.append(f"{prefix}{msg}")

        return improvements

    def _find_missing_sections(self, text: str) -> List[str]:
        """Identify which required sections are absent."""
        text_lower = text.lower()
        missing = []
        for section, markers in COMPLETENESS_SECTIONS.items():
            if not any(m in text_lower for m in markers):
                missing.append(section)
        return missing

    # ── Cross-Validation Against DB ──────────────────────────────────────

    def verify_citations_against_db(self, text: str) -> Dict[str, Any]:
        """Cross-check extracted citations against auth_rules and master_citations."""
        citations = CITE_RE.findall(text)
        if not citations:
            return {"total": 0, "verified": 0, "unverified": [], "rate": 0.0}

        verified = []
        unverified = []
        try:
            conn = self._connect()
            for cite in set(citations):
                # Search auth_rules
                cur = conn.execute(
                    "SELECT COUNT(*) FROM auth_rules WHERE full_text LIKE ?",
                    (f"%{cite}%",),
                )
                if cur.fetchone()[0] > 0:
                    verified.append(cite)
                    continue
                # Fallback: master_citations
                cur = conn.execute(
                    "SELECT COUNT(*) FROM master_citations WHERE citation LIKE ?",
                    (f"%{cite}%",),
                )
                if cur.fetchone()[0] > 0:
                    verified.append(cite)
                else:
                    unverified.append(cite)
            conn.close()
        except Exception as e:
            self._error_log.append(f"Citation verification error: {e}")
            return {"total": len(set(citations)), "verified": 0, "unverified": list(set(citations)), "rate": 0.0, "error": str(e)}

        total = len(set(citations))
        return {
            "total": total,
            "verified": len(verified),
            "unverified": unverified,
            "rate": round(len(verified) / max(total, 1) * 100, 1),
        }

    # ── Cycle Logging ────────────────────────────────────────────────────

    def log_cycle(
        self,
        file_path: str,
        cycle_num: int,
        quality_before: float,
        quality_after: float,
        improvements: List[str],
        placeholders_before: int,
        placeholders_after: int,
    ) -> int:
        """Log a convergence cycle to the database. Returns cycle_id."""
        conn = self._connect()
        conn.execute(
            """CREATE TABLE IF NOT EXISTS convergence_cycles (
                cycle_id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_path TEXT NOT NULL,
                cycle_number INTEGER NOT NULL,
                improvements_made TEXT,
                quality_before REAL,
                quality_after REAL,
                placeholders_before INTEGER,
                placeholders_after INTEGER,
                converged INTEGER DEFAULT 0,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        cur = conn.execute(
            """INSERT INTO convergence_cycles
               (document_path, cycle_number, improvements_made,
                quality_before, quality_after,
                placeholders_before, placeholders_after, converged)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                file_path,
                cycle_num,
                json.dumps(improvements),
                quality_before,
                quality_after,
                placeholders_before,
                placeholders_after,
                1 if (quality_after >= self.convergence_threshold and placeholders_after == 0) else 0,
            ),
        )
        cycle_id = cur.lastrowid
        conn.commit()
        conn.close()
        return cycle_id

    def get_cycle_history(self, file_path: str) -> List[Dict]:
        """Retrieve all convergence cycles for a document."""
        conn = self._connect()
        rows = conn.execute(
            """SELECT cycle_id, cycle_number, quality_before, quality_after,
                      placeholders_before, placeholders_after, converged, completed_at
               FROM convergence_cycles
               WHERE document_path = ?
               ORDER BY cycle_number""",
            (file_path,),
        ).fetchall()
        conn.close()
        return [
            {
                "cycle_id": r[0], "cycle": r[1],
                "q_before": r[2], "q_after": r[3],
                "ph_before": r[4], "ph_after": r[5],
                "converged": bool(r[6]), "at": r[7],
            }
            for r in rows
        ]

    # ── Batch Analysis ───────────────────────────────────────────────────

    def batch_analyze(
        self, directory: str, extensions: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Analyze all documents in a directory tree."""
        if extensions is None:
            extensions = [".md"]
        results: List[Dict[str, Any]] = []
        for root, _dirs, files in os.walk(directory):
            for f in files:
                if any(f.endswith(ext) for ext in extensions):
                    fpath = os.path.join(root, f)
                    try:
                        result = self.analyze(fpath)
                        results.append(result)
                    except Exception as e:
                        self._error_log.append(f"Error analyzing {fpath}: {e}")
                        results.append({"file": f, "path": fpath, "error": str(e), "overall": 0})
        # Sort worst-first so worst scores are at top
        return sorted(results, key=lambda x: x.get("overall", 0))

    # ── Summary Report ───────────────────────────────────────────────────

    def summary_report(self, results: List[Dict]) -> Dict[str, Any]:
        """Generate aggregate summary from batch results."""
        valid = [r for r in results if "error" not in r]
        if not valid:
            return {"total": len(results), "errors": len(results), "valid": 0}

        scores = [r["overall"] for r in valid]
        converged = [r for r in valid if r.get("converged")]
        needs_work = [r for r in valid if not r.get("converged")]

        return {
            "total_documents": len(results),
            "valid_analyzed": len(valid),
            "errors": len(results) - len(valid),
            "converged_count": len(converged),
            "needs_work_count": len(needs_work),
            "avg_quality": round(sum(scores) / len(scores), 1),
            "min_quality": round(min(scores), 1),
            "max_quality": round(max(scores), 1),
            "total_placeholders": sum(r.get("placeholder_count", 0) for r in valid),
            "total_citations": sum(r.get("citation_count", 0) for r in valid),
        }


# ═════════════════════════════════════════════════════════════════════════════
# Self-Test
# ═════════════════════════════════════════════════════════════════════════════

def self_test() -> bool:
    """Run convergence analysis on all LitigationOS vehicle filings."""
    # Ensure UTF-8 output on Windows consoles
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    print("=" * 78)
    print("  CONVERGENCE ENGINE v2.0 — SELF-TEST")
    print("  LitigationOS 2026 — Pigors v. Watson")
    print("=" * 78)

    engine = ConvergenceEngine()

    # Verify DB connectivity
    try:
        conn = engine._connect()
        conn.close()
        print("\n[OK] Database connected: litigation_context.db")
    except Exception as e:
        print(f"\n[FAIL] Database connection failed: {e}")
        return False

    # Scan all vehicle lanes
    vehicles_root = VEHICLES_ROOT
    if not os.path.isdir(vehicles_root):
        print(f"[FAIL] Vehicles directory not found: {vehicles_root}")
        return False

    print(f"[OK] Vehicles root: {vehicles_root}\n")

    all_results = engine.batch_analyze(vehicles_root)

    # Print per-document scores
    print("-" * 78)
    print(f"  {'FILE':<50} {'SCORE':>6}  {'STATUS'}")
    print("-" * 78)

    lane_buckets: Dict[str, List[Dict]] = {}
    for r in sorted(all_results, key=lambda x: x.get("path", "")):
        # Determine lane from path
        path = r.get("path", "")
        lane = "UNKNOWN"
        for part in path.replace("\\", "/").split("/"):
            if part.startswith("LANE_"):
                lane = part
                break
        if lane == "UNKNOWN" and "06_VEHICLES" in path:
            lane = "ROOT"

        lane_buckets.setdefault(lane, []).append(r)

        if "error" in r:
            print(f"  {r['file']:<50} {'ERR':>6}  {r['error'][:40]}")
            continue

        status = "✓ CONVERGED" if r["converged"] else f"✗ NEEDS WORK ({len(r['improvements'])} items)"
        tier = r.get("tier", get_tier(r["overall"]))
        print(f"  {r['file']:<50} {r['overall']:>5.1f}%  [{tier}] {status}")

        # Show dimension breakdown
        for dim, val in r["scores"].items():
            bar = "█" * int(val / 5) + "░" * (20 - int(val / 5))
            label = dim.replace("_score", "").replace("_", " ").title()
            print(f"    {label:<28} {bar} {val:>5.1f}%")

        if r["placeholders"]:
            print(f"    Placeholders ({r['placeholder_count']}): {r['placeholders'][:5]}")
        if r["improvements"]:
            for imp in r["improvements"][:3]:
                print(f"    → {imp}")
        print()

    # Lane summaries
    print("=" * 78)
    print("  LANE SUMMARY")
    print("=" * 78)
    for lane in sorted(lane_buckets):
        docs = lane_buckets[lane]
        valid = [d for d in docs if "error" not in d]
        if not valid:
            print(f"  {lane}: {len(docs)} docs — all errors")
            continue
        avg = round(sum(d["overall"] for d in valid) / len(valid), 1)
        conv = sum(1 for d in valid if d.get("converged"))
        print(f"  {lane}: {len(valid)} docs — avg {avg}% — {conv}/{len(valid)} converged")

    # Aggregate summary
    summary = engine.summary_report(all_results)
    print()
    print("=" * 78)
    print("  AGGREGATE SUMMARY")
    print("=" * 78)
    print(f"  Total documents analyzed : {summary['total_documents']}")
    print(f"  Successfully scored      : {summary['valid_analyzed']}")
    print(f"  Errors                   : {summary['errors']}")
    print(f"  Converged (>= 97%, 0 PH): {summary['converged_count']}")
    print(f"  Needs work               : {summary['needs_work_count']}")
    print(f"  Average quality          : {summary['avg_quality']}%")
    print(f"  Min quality              : {summary['min_quality']}%")
    print(f"  Max quality              : {summary['max_quality']}%")
    print(f"  Total placeholders found : {summary['total_placeholders']}")
    print(f"  Total citations found    : {summary['total_citations']}")
    print()

    # Tier distribution (v2.0)
    valid_results = [r for r in all_results if "error" not in r]
    tier_counts: Dict[str, int] = {}
    for r in valid_results:
        t = r.get("tier", get_tier(r["overall"]))
        tier_counts[t] = tier_counts.get(t, 0) + 1
    print("  ── QUALITY TIER DISTRIBUTION ──")
    for tier_name in QUALITY_TIERS:
        count = tier_counts.get(tier_name, 0)
        bar = "█" * count
        print(f"    {tier_name:<12} {count:>3}  {bar}")
    print()

    # Improvement priority summary (v2.0)
    all_dims_needing_work: Dict[str, int] = {}
    for r in valid_results:
        for dim, score_val in r.get("scores", {}).items():
            if dim in IMPROVEMENT_PRIORITY:
                thresh = {"citation_score": 80, "irac_score": 75, "completeness_score": 83,
                          "chess_mode_score": 60, "placeholder_score": 100,
                          "mcr_compliance_score": 85, "parental_alienation_score": 70,
                          "evidence_density_score": 50}.get(dim, 80)
                if score_val < thresh:
                    all_dims_needing_work[dim] = all_dims_needing_work.get(dim, 0) + 1
    if all_dims_needing_work:
        print("  ── IMPROVEMENT PRIORITY ORDER ──")
        sorted_dims = sorted(
            all_dims_needing_work.items(),
            key=lambda x: -(IMPROVEMENT_PRIORITY[x[0]]["impact"] / max(IMPROVEMENT_PRIORITY[x[0]]["effort"], 1)),
        )
        for dim, cnt in sorted_dims:
            pri = IMPROVEMENT_PRIORITY[dim]
            label = dim.replace("_score", "").replace("_", " ").title()
            print(f"    [{pri['label']:<12}] {label:<28} — {cnt} docs need work")
        print()

    if engine._error_log:
        print(f"  Errors encountered: {len(engine._error_log)}")
        for err in engine._error_log[:5]:
            print(f"    ! {err}")
        print()

    print("=" * 78)
    print("  CONVERGENCE ENGINE SELF-TEST PASSED")
    print("=" * 78)
    return True


if __name__ == "__main__":
    success = self_test()
    sys.exit(0 if success else 1)
