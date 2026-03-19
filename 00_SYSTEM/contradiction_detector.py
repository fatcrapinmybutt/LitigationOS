#!/usr/bin/env python3
"""
MBP LitigationOS — Contradiction Detection Enhancement
=======================================================
Cross-references existing contradictions (10,558 in contradiction_map) with
new evidence, finds new contradictions between Watson statements and the record,
scores by severity/legal significance, and generates a report.

Capabilities:
  - Query existing contradiction_map for known conflicts
  - Cross-reference evidence_quotes and impeachment_items for new contradictions
  - Score contradictions: severity (1-10), legal significance, court usability
  - Save new findings to contradiction_map table
  - Generate CONTRADICTION_REPORT.md in 05_ANALYSIS/

Usage:
    python contradiction_detector.py
    python contradiction_detector.py --speaker "Watson"
    python contradiction_detector.py --category "custody"
    python contradiction_detector.py --report-only

Example:
    python contradiction_detector.py --speaker "Watson" --min-severity 5
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\litigation_context.db",
)
ANALYSIS_DIR = Path(r"C:\Users\andre\LitigationOS\05_ANALYSIS")
REPORT_PATH = ANALYSIS_DIR / "CONTRADICTION_REPORT.md"

# ── Severity scoring keywords ───────────────────────────────────────
SEVERITY_KEYWORDS = {
    # High severity (8-10)
    "perjury": 10, "false statement": 10, "lied": 9, "fabricat": 9,
    "fraud": 9, "forged": 9, "falsif": 9,
    "sworn": 8, "under oath": 8, "testimony": 8, "deposition": 8,
    # Medium severity (5-7)
    "inconsistent": 7, "contradict": 7, "prior statement": 7,
    "changed story": 7, "different account": 6, "denied": 6,
    "claimed": 5, "alleged": 5, "asserted": 5,
    # Lower severity (1-4)
    "unclear": 3, "vague": 3, "approximate": 2, "may have": 2,
}

LEGAL_SIGNIFICANCE_PATTERNS = {
    "impeachment_mre_801": re.compile(r'\b(prior.?inconsistent|mre\s*801|hearsay.?exception)', re.I),
    "perjury_mcl_750": re.compile(r'\b(perjury|mcl\s*750\.423|false.?swearing)', re.I),
    "credibility_mre_608": re.compile(r'\b(credibility|character.?truthfulness|mre\s*608)', re.I),
    "fraud_on_court": re.compile(r'\b(fraud.?on.?court|mcr\s*2\.114|misrepresent)', re.I),
    "best_interest_factor_j": re.compile(r'\b(factor\s*j|facilitate|alienat|mcl\s*722\.23)', re.I),
    "contempt": re.compile(r'\b(contempt|violat.{0,10}order|disobey)', re.I),
}


def _safe_text(val: Any) -> str:
    """Safely convert DB value to string."""
    if val is None:
        return ""
    try:
        return str(val).strip()
    except Exception:
        return str(val).encode("utf-8", errors="replace").decode("utf-8", errors="replace").strip()


def _compute_severity(text_a: str, text_b: str) -> int:
    """Compute contradiction severity score (1-10) from keyword analysis."""
    combined = (text_a + " " + text_b).lower()
    max_score = 1
    for keyword, score in SEVERITY_KEYWORDS.items():
        if keyword in combined:
            max_score = max(max_score, score)
    return max_score


def _compute_legal_significance(text_a: str, text_b: str) -> List[str]:
    """Identify legal significance patterns."""
    combined = text_a + " " + text_b
    findings = []
    for label, pattern in LEGAL_SIGNIFICANCE_PATTERNS.items():
        if pattern.search(combined):
            findings.append(label)
    return findings


def _text_overlap(a: str, b: str, threshold: float = 0.3) -> bool:
    """Check if two texts have enough word overlap to be related."""
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a or not words_b:
        return False
    overlap = len(words_a & words_b)
    min_len = min(len(words_a), len(words_b))
    return (overlap / max(min_len, 1)) >= threshold


# ── Contradiction Detector ──────────────────────────────────────────
class ContradictionDetector:
    """Enhanced contradiction detection across litigation database."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    def _get_db(self) -> sqlite3.Connection:
        if self._conn is not None:
            try:
                self._conn.execute("SELECT 1")
                return self._conn
            except Exception:
                self._conn = None

        self._conn = sqlite3.connect(self.db_path, timeout=30)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA cache_size=-65536")
        return self._conn

    def get_existing_contradictions(
        self, speaker: Optional[str] = None, min_severity: int = 0
    ) -> List[Dict]:
        """Load existing contradictions from contradiction_map."""
        conn = self._get_db()
        sql = "SELECT * FROM contradiction_map WHERE 1=1"
        params = []

        if speaker:
            sql += " AND (source_a_text LIKE ? OR source_b_text LIKE ?)"
            params.extend([f"%{speaker}%", f"%{speaker}%"])
        if min_severity > 0:
            sql += " AND severity >= ?"
            params.append(str(min_severity))

        sql += " ORDER BY CAST(severity AS INTEGER) DESC LIMIT 500"

        try:
            rows = conn.execute(sql, params).fetchall()
            cols = [d[0] for d in conn.execute("PRAGMA table_info(contradiction_map)").fetchall()]
            col_names = [c[1] for c in conn.execute("PRAGMA table_info(contradiction_map)").fetchall()]
            return [dict(zip(col_names, row)) for row in rows]
        except Exception as e:
            print(f"  [WARN] Failed to load contradictions: {e}")
            return []

    def get_evidence_quotes(self, speaker: Optional[str] = None) -> List[Dict]:
        """Load evidence quotes, optionally filtered by speaker."""
        conn = self._get_db()
        sql = "SELECT id, quote_text, speaker, evidence_category, legal_significance FROM evidence_quotes WHERE quote_text IS NOT NULL"
        params = []

        if speaker:
            sql += " AND UPPER(speaker) LIKE UPPER(?)"
            params.append(f"%{speaker}%")

        try:
            rows = conn.execute(sql, params).fetchall()
            return [
                {"id": r[0], "quote_text": _safe_text(r[1]), "speaker": _safe_text(r[2]),
                 "category": _safe_text(r[3]), "significance": _safe_text(r[4])}
                for r in rows
            ]
        except Exception as e:
            print(f"  [WARN] Failed to load evidence quotes: {e}")
            return []

    def get_impeachment_items(self, speaker: Optional[str] = None) -> List[Dict]:
        """Load impeachment items."""
        conn = self._get_db()
        sql = "SELECT rowid, * FROM impeachment_items WHERE 1=1"
        params = []

        if speaker:
            sql += " AND UPPER(speaker) LIKE UPPER(?)"
            params.append(f"%{speaker}%")

        sql += " LIMIT 1000"

        try:
            rows = conn.execute(sql, params).fetchall()
            col_info = conn.execute("PRAGMA table_info(impeachment_items)").fetchall()
            col_names = ["rowid"] + [c[1] for c in col_info]
            return [dict(zip(col_names, row)) for row in rows]
        except Exception as e:
            print(f"  [WARN] Failed to load impeachment items: {e}")
            return []

    def detect_new_contradictions(
        self,
        speaker: Optional[str] = None,
        category: Optional[str] = None,
        min_severity: int = 0,
    ) -> List[Dict]:
        """
        Cross-reference evidence quotes with impeachment items to find
        new contradictions not already in contradiction_map.
        """
        print("  Loading evidence quotes...")
        quotes = self.get_evidence_quotes(speaker=speaker)
        print(f"    Found {len(quotes)} evidence quotes")

        print("  Loading impeachment items...")
        impeachments = self.get_impeachment_items(speaker=speaker)
        print(f"    Found {len(impeachments)} impeachment items")

        # Load existing contradiction hashes to avoid duplicates
        conn = self._get_db()
        existing_hashes = set()
        try:
            rows = conn.execute(
                "SELECT source_a_text, source_b_text FROM contradiction_map"
            ).fetchall()
            for r in rows:
                a = _safe_text(r[0])[:100].lower()
                b = _safe_text(r[1])[:100].lower()
                existing_hashes.add(f"{a}||{b}")
                existing_hashes.add(f"{b}||{a}")
        except Exception:
            pass

        print(f"    {len(existing_hashes)} existing contradiction signatures loaded")

        new_contradictions = []

        # Cross-reference quotes with impeachment items
        for quote in quotes:
            q_text = quote["quote_text"]
            if not q_text or len(q_text) < 20:
                continue

            for imp in impeachments:
                imp_statement = _safe_text(imp.get("statement", ""))
                imp_contra = _safe_text(imp.get("contradicting_text", ""))

                compare_text = imp_contra if imp_contra else imp_statement
                if not compare_text or len(compare_text) < 20:
                    continue

                # Check for topical overlap (related content)
                if not _text_overlap(q_text, compare_text):
                    continue

                # Check not already known
                hash_key = f"{q_text[:100].lower()}||{compare_text[:100].lower()}"
                if hash_key in existing_hashes:
                    continue

                severity = _compute_severity(q_text, compare_text)
                if severity < min_severity:
                    continue

                legal_sigs = _compute_legal_significance(q_text, compare_text)

                contradiction = {
                    "source_a_type": "evidence_quote",
                    "source_a_doc_id": quote.get("id"),
                    "source_a_text": q_text[:500],
                    "source_b_type": "impeachment_item",
                    "source_b_doc_id": imp.get("rowid"),
                    "source_b_text": compare_text[:500],
                    "contradiction_type": "cross_reference",
                    "severity": str(severity),
                    "legal_impact": ", ".join(legal_sigs) if legal_sigs else "general_inconsistency",
                    "speaker": quote.get("speaker", imp.get("speaker", "")),
                }

                new_contradictions.append(contradiction)
                existing_hashes.add(hash_key)

        print(f"    Found {len(new_contradictions)} new contradictions")
        return new_contradictions

    def save_contradictions(self, contradictions: List[Dict]) -> int:
        """Save new contradictions to contradiction_map table."""
        if not contradictions:
            return 0

        conn = self._get_db()
        saved = 0
        for c in contradictions:
            try:
                conn.execute(
                    """INSERT INTO contradiction_map
                       (source_a_type, source_a_doc_id, source_a_text,
                        source_b_type, source_b_doc_id, source_b_text,
                        contradiction_type, severity, legal_impact, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
                    (
                        c.get("source_a_type", ""),
                        c.get("source_a_doc_id"),
                        c.get("source_a_text", ""),
                        c.get("source_b_type", ""),
                        c.get("source_b_doc_id"),
                        c.get("source_b_text", ""),
                        c.get("contradiction_type", ""),
                        c.get("severity", ""),
                        c.get("legal_impact", ""),
                    ),
                )
                saved += 1
            except Exception as e:
                print(f"  [WARN] Failed to save contradiction: {e}")

        conn.commit()
        print(f"  Saved {saved} new contradictions to DB")
        return saved

    def generate_report(
        self,
        new_contradictions: List[Dict],
        existing: List[Dict],
    ) -> str:
        """Generate CONTRADICTION_REPORT.md content."""
        lines = [
            "# CONTRADICTION ANALYSIS REPORT",
            f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Database:** {self.db_path}",
            "",
            "## Summary",
            f"- **Existing contradictions in DB:** {len(existing):,}",
            f"- **New contradictions found:** {len(new_contradictions)}",
            "",
        ]

        # Severity distribution
        severity_dist = defaultdict(int)
        for c in new_contradictions:
            s = int(c.get("severity", 0))
            if s >= 8:
                severity_dist["CRITICAL (8-10)"] += 1
            elif s >= 5:
                severity_dist["HIGH (5-7)"] += 1
            else:
                severity_dist["MODERATE (1-4)"] += 1

        if severity_dist:
            lines.append("## Severity Distribution (New Findings)")
            lines.append("")
            lines.append("| Severity | Count |")
            lines.append("|----------|-------|")
            for sev, count in sorted(severity_dist.items(), reverse=True):
                lines.append(f"| {sev} | {count} |")
            lines.append("")

        # Legal significance summary
        sig_counts = defaultdict(int)
        for c in new_contradictions:
            for sig in (c.get("legal_impact", "") or "").split(", "):
                if sig:
                    sig_counts[sig] += 1

        if sig_counts:
            lines.append("## Legal Significance Categories")
            lines.append("")
            lines.append("| Category | Count | Court Use |")
            lines.append("|----------|-------|-----------|")
            sig_desc = {
                "impeachment_mre_801": "Prior inconsistent statement — MRE 801(d)(1)(A)",
                "perjury_mcl_750": "Potential perjury — MCL 750.423",
                "credibility_mre_608": "Credibility attack — MRE 608/609",
                "fraud_on_court": "Fraud on court — MCR 2.114",
                "best_interest_factor_j": "Best interest Factor J — MCL 722.23(j)",
                "contempt": "Contempt of court order",
                "general_inconsistency": "General inconsistency — impeachment material",
            }
            for sig, count in sorted(sig_counts.items(), key=lambda x: x[1], reverse=True):
                desc = sig_desc.get(sig, sig)
                lines.append(f"| {sig} | {count} | {desc} |")
            lines.append("")

        # Top contradictions (sorted by severity)
        top = sorted(new_contradictions, key=lambda x: int(x.get("severity", 0)), reverse=True)[:25]
        if top:
            lines.append("## Top New Contradictions")
            lines.append("")
            for i, c in enumerate(top, 1):
                speaker = c.get("speaker", "Unknown")
                sev = c.get("severity", "?")
                impact = c.get("legal_impact", "")
                lines.append(f"### {i}. Severity {sev}/10 — {speaker}")
                lines.append(f"**Legal Impact:** {impact}")
                lines.append("")
                lines.append(f"**Source A** ({c.get('source_a_type', '')}):")
                lines.append(f"> {c.get('source_a_text', '')[:300]}")
                lines.append("")
                lines.append(f"**Source B** ({c.get('source_b_type', '')}):")
                lines.append(f"> {c.get('source_b_text', '')[:300]}")
                lines.append("")
                lines.append("---")
                lines.append("")

        # Existing high-severity contradictions summary
        high_existing = [c for c in existing if int(c.get("severity", 0) or 0) >= 7][:10]
        if high_existing:
            lines.append("## Existing High-Severity Contradictions (Top 10)")
            lines.append("")
            for i, c in enumerate(high_existing, 1):
                lines.append(f"### E{i}. Severity {c.get('severity', '?')}/10")
                lines.append(f"**Type:** {c.get('contradiction_type', '')}")
                lines.append(f"> A: {_safe_text(c.get('source_a_text', ''))[:200]}")
                lines.append(f"> B: {_safe_text(c.get('source_b_text', ''))[:200]}")
                lines.append("")

        return "\n".join(lines)

    def run(
        self,
        speaker: Optional[str] = None,
        category: Optional[str] = None,
        min_severity: int = 0,
        save: bool = True,
        report: bool = True,
    ) -> Dict[str, Any]:
        """
        Full contradiction detection pipeline.

        Args:
            speaker: Filter by speaker name
            category: Filter by evidence category
            min_severity: Minimum severity threshold
            save: Whether to save new contradictions to DB
            report: Whether to generate CONTRADICTION_REPORT.md

        Returns:
            Summary dict with counts and paths
        """
        print(f"[1/4] Loading existing contradictions...")
        existing = self.get_existing_contradictions(speaker=speaker, min_severity=min_severity)
        print(f"  Loaded {len(existing)} existing contradictions")

        print(f"[2/4] Detecting new contradictions...")
        new_contradictions = self.detect_new_contradictions(
            speaker=speaker,
            category=category,
            min_severity=min_severity,
        )

        saved_count = 0
        if save and new_contradictions:
            print(f"[3/4] Saving {len(new_contradictions)} new contradictions to DB...")
            saved_count = self.save_contradictions(new_contradictions)
        else:
            print(f"[3/4] Skipping save (save={save}, new={len(new_contradictions)})")

        report_path = None
        if report:
            print(f"[4/4] Generating contradiction report...")
            report_text = self.generate_report(new_contradictions, existing)
            ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
            REPORT_PATH.write_text(report_text, encoding="utf-8")
            report_path = str(REPORT_PATH)
            print(f"  Report saved to {report_path}")

        summary = {
            "existing_count": len(existing),
            "new_found": len(new_contradictions),
            "saved_to_db": saved_count,
            "report_path": report_path,
            "speaker_filter": speaker,
            "min_severity": min_severity,
        }

        print(f"\n{'='*60}")
        print(f"CONTRADICTION DETECTION COMPLETE")
        print(f"{'='*60}")
        print(f"  Existing:   {len(existing):,}")
        print(f"  New found:  {len(new_contradictions)}")
        print(f"  Saved:      {saved_count}")
        if report_path:
            print(f"  Report:     {report_path}")
        print(f"{'='*60}")

        return summary

    def close(self) -> None:
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None


# ── CLI ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Enhanced contradiction detection for LitigationOS"
    )
    parser.add_argument("--speaker", type=str, default=None,
                        help="Filter by speaker name (e.g., 'Watson')")
    parser.add_argument("--category", type=str, default=None,
                        help="Filter by evidence category")
    parser.add_argument("--min-severity", type=int, default=0,
                        help="Minimum severity threshold (1-10)")
    parser.add_argument("--no-save", action="store_true",
                        help="Don't save new contradictions to DB")
    parser.add_argument("--report-only", action="store_true",
                        help="Only generate report from existing data")

    args = parser.parse_args()

    detector = ContradictionDetector()
    try:
        if args.report_only:
            existing = detector.get_existing_contradictions(
                speaker=args.speaker, min_severity=args.min_severity
            )
            report_text = detector.generate_report([], existing)
            ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
            REPORT_PATH.write_text(report_text, encoding="utf-8")
            print(f"Report saved to {REPORT_PATH}")
        else:
            detector.run(
                speaker=args.speaker,
                category=args.category,
                min_severity=args.min_severity,
                save=not args.no_save,
                report=True,
            )
    finally:
        detector.close()
