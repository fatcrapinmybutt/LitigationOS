#!/usr/bin/env python3
"""
MBP LitigationOS — Citation Verification Engine
================================================
Reads court documents, extracts all legal citations, and verifies each
against auth_rules and master_citations tables in litigation_context.db.

Supported citation types:
  - MCR X.XXX(X)(X)   — Michigan Court Rules
  - MCL XXX.XX(X)     — Michigan Compiled Laws
  - MRE XXX(X)        — Michigan Rules of Evidence
  - *Case v Case*     — Case law citations

Usage:
    python citation_checker.py --file path/to/document.md
    python citation_checker.py --all           # Check all .md in 04_COURT_FILINGS/
    python citation_checker.py --text "MCR 2.003(C)(1) requires..."

Example:
    python citation_checker.py --file "C:/Users/andre/LitigationOS/04_COURT_FILINGS/motion.md"
    # Output: verification report + saves to citation_verification_results table
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\litigation_context.db",
)
COURT_FILINGS_DIR = Path(r"C:\Users\andre\LitigationOS\04_COURT_FILINGS")

# ── Citation extraction patterns ────────────────────────────────────
CITATION_PATTERNS = {
    "MCR": re.compile(
        r'\bMCR\s+(\d+\.\d+(?:\([A-Za-z0-9]+\))*(?:\([a-z]\))*)',
        re.IGNORECASE,
    ),
    "MCL": re.compile(
        r'\bMCL\s+(\d+\.\d+[a-z]?(?:\([A-Za-z0-9]+\))*)',
        re.IGNORECASE,
    ),
    "MRE": re.compile(
        r'\bMRE\s+(\d+(?:\([A-Za-z0-9]+\))*)',
        re.IGNORECASE,
    ),
    "CASE": re.compile(
        r'\*([A-Z][A-Za-z\'\-]+(?:\s+(?:v|vs)\.?\s+[A-Z][A-Za-z\'\-]+))\*',
    ),
    "CASE_ITALIC": re.compile(
        r'_([A-Z][A-Za-z\'\-]+\s+(?:v|vs)\.?\s+[A-Z][A-Za-z\'\-]+)_',
    ),
}


def extract_citations(text: str) -> List[Dict[str, str]]:
    """Extract all citations from text, with type and raw match."""
    citations = []
    seen = set()

    for cite_type, pattern in CITATION_PATTERNS.items():
        for m in pattern.finditer(text):
            raw = m.group(0)
            extracted = m.group(1) if m.lastindex else m.group(0)

            # Normalize
            if cite_type in ("MCR", "MCL", "MRE"):
                normalized = f"{cite_type} {extracted}".upper().replace("  ", " ")
            elif cite_type in ("CASE", "CASE_ITALIC"):
                normalized = extracted.strip()
                cite_type = "CASE"
            else:
                normalized = extracted.strip()

            key = f"{cite_type}:{normalized}"
            if key not in seen:
                seen.add(key)
                # Get surrounding context (50 chars each side)
                start = max(0, m.start() - 50)
                end = min(len(text), m.end() + 50)
                context = text[start:end].replace("\n", " ").strip()

                citations.append({
                    "type": cite_type,
                    "citation": normalized,
                    "raw": raw,
                    "context": context,
                })

    return citations


def _normalize_for_search(citation: str) -> str:
    """Normalize citation for fuzzy DB lookup."""
    return re.sub(r'[^A-Za-z0-9.\s]', '', citation).strip().upper()


# ── Verification engine ─────────────────────────────────────────────
class CitationVerifier:
    """Verifies citations against the litigation database."""

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
        self._conn.row_factory = sqlite3.Row
        return self._conn

    def _ensure_results_table(self) -> None:
        """Create citation_verification_results table if needed."""
        conn = self._get_db()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS citation_verification_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT,
                citation TEXT,
                cite_type TEXT,
                status TEXT,
                matched_rule TEXT,
                matched_text TEXT,
                suggestions TEXT,
                context TEXT,
                verified_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()

    def verify_citation(self, citation: Dict[str, str]) -> Dict[str, Any]:
        """
        Verify a single citation against DB.
        Returns: {citation, type, status, matched_rule, matched_text, suggestions}
        Status: 'valid', 'invalid', 'not_found', 'close_match'
        """
        conn = self._get_db()
        cite_type = citation["type"]
        cite_text = citation["citation"]
        result = {
            "citation": cite_text,
            "type": cite_type,
            "status": "not_found",
            "matched_rule": None,
            "matched_text": None,
            "suggestions": [],
            "context": citation.get("context", ""),
        }

        try:
            if cite_type in ("MCR", "MCL", "MRE"):
                result = self._verify_rule_citation(conn, cite_text, cite_type, result)
            elif cite_type == "CASE":
                result = self._verify_case_citation(conn, cite_text, result)
        except Exception as e:
            result["status"] = "error"
            result["matched_text"] = str(e)

        return result

    def _verify_rule_citation(
        self, conn: sqlite3.Connection, cite_text: str, cite_type: str, result: Dict
    ) -> Dict:
        """Verify MCR/MCL/MRE citation."""
        # Extract the rule number portion
        parts = cite_text.split(maxsplit=1)
        if len(parts) < 2:
            return result
        rule_num = parts[1]

        # Exact match in auth_rules
        row = conn.execute(
            "SELECT rule_number, title, full_text FROM auth_rules WHERE UPPER(rule_number) = UPPER(?) LIMIT 1",
            (cite_text,),
        ).fetchone()

        if not row:
            row = conn.execute(
                "SELECT rule_number, title, full_text FROM auth_rules WHERE UPPER(rule_number) LIKE UPPER(?) LIMIT 1",
                (f"%{rule_num}%",),
            ).fetchone()

        if row:
            result["status"] = "valid"
            result["matched_rule"] = row["rule_number"]
            result["matched_text"] = (row["title"] or "")[:200]
            return result

        # Check master_citations
        mc_row = conn.execute(
            "SELECT citation, context FROM master_citations WHERE UPPER(citation) LIKE UPPER(?) LIMIT 1",
            (f"%{rule_num}%",),
        ).fetchone()

        if mc_row:
            result["status"] = "valid"
            result["matched_rule"] = mc_row["citation"]
            result["matched_text"] = (mc_row["context"] or "")[:200]
            return result

        # Close match search — strip subrules for base rule match
        base_rule = re.sub(r'\([^)]*\)', '', rule_num).strip()
        if base_rule != rule_num:
            close = conn.execute(
                "SELECT rule_number, title FROM auth_rules WHERE UPPER(rule_number) LIKE UPPER(?) LIMIT 5",
                (f"%{base_rule}%",),
            ).fetchall()

            if close:
                result["status"] = "close_match"
                result["suggestions"] = [r["rule_number"] for r in close]
                return result

        return result

    def _verify_case_citation(
        self, conn: sqlite3.Connection, cite_text: str, result: Dict
    ) -> Dict:
        """Verify case law citation."""
        # Search master_citations for case name
        search_term = f"%{cite_text}%"
        row = conn.execute(
            "SELECT citation, context FROM master_citations WHERE cite_type = 'case_law' AND citation LIKE ? LIMIT 1",
            (search_term,),
        ).fetchone()

        if row:
            result["status"] = "valid"
            result["matched_rule"] = row["citation"]
            result["matched_text"] = (row["context"] or "")[:200]
            return result

        # Broader search
        row = conn.execute(
            "SELECT citation, context FROM master_citations WHERE UPPER(citation) LIKE UPPER(?) LIMIT 1",
            (search_term,),
        ).fetchone()

        if row:
            result["status"] = "valid"
            result["matched_rule"] = row["citation"]
            result["matched_text"] = (row["context"] or "")[:200]
            return result

        # Try partial name match (first party name)
        first_party = cite_text.split(" v")[0].strip() if " v" in cite_text.lower() else cite_text
        if first_party and len(first_party) > 2:
            close = conn.execute(
                "SELECT DISTINCT citation FROM master_citations WHERE UPPER(citation) LIKE UPPER(?) LIMIT 5",
                (f"%{first_party}%",),
            ).fetchall()

            if close:
                result["status"] = "close_match"
                result["suggestions"] = [r["citation"] for r in close]
                return result

        return result

    def verify_document(self, file_path: str) -> Dict[str, Any]:
        """Verify all citations in a document."""
        path = Path(file_path)
        if not path.exists():
            return {"error": f"File not found: {file_path}"}

        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return {"error": f"Cannot read file: {e}"}

        citations = extract_citations(text)
        if not citations:
            return {
                "file": str(path),
                "total_citations": 0,
                "results": [],
                "summary": {"valid": 0, "invalid": 0, "not_found": 0, "close_match": 0},
            }

        results = []
        for cite in citations:
            v = self.verify_citation(cite)
            results.append(v)

        # Save to DB
        self._save_results(str(path), results)

        summary = {"valid": 0, "invalid": 0, "not_found": 0, "close_match": 0, "error": 0}
        for r in results:
            s = r.get("status", "not_found")
            summary[s] = summary.get(s, 0) + 1

        return {
            "file": str(path),
            "total_citations": len(results),
            "results": results,
            "summary": summary,
        }

    def verify_text(self, text: str) -> Dict[str, Any]:
        """Verify citations in raw text."""
        citations = extract_citations(text)
        results = [self.verify_citation(c) for c in citations]

        summary = {"valid": 0, "invalid": 0, "not_found": 0, "close_match": 0, "error": 0}
        for r in results:
            s = r.get("status", "not_found")
            summary[s] = summary.get(s, 0) + 1

        return {
            "total_citations": len(results),
            "results": results,
            "summary": summary,
        }

    def _save_results(self, file_path: str, results: List[Dict]) -> None:
        """Save verification results to DB."""
        try:
            self._ensure_results_table()
            conn = self._get_db()
            # Clear previous results for this file
            conn.execute(
                "DELETE FROM citation_verification_results WHERE file_path = ?",
                (file_path,),
            )
            for r in results:
                conn.execute(
                    """INSERT INTO citation_verification_results
                       (file_path, citation, cite_type, status, matched_rule,
                        matched_text, suggestions, context)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        file_path,
                        r.get("citation", ""),
                        r.get("type", ""),
                        r.get("status", "not_found"),
                        r.get("matched_rule", ""),
                        r.get("matched_text", ""),
                        json.dumps(r.get("suggestions", [])),
                        r.get("context", ""),
                    ),
                )
            conn.commit()
        except Exception as e:
            print(f"  [WARN] Failed to save results to DB: {e}")

    def verify_all_filings(self) -> List[Dict[str, Any]]:
        """Verify all .md files in 04_COURT_FILINGS/."""
        results = []
        md_files = list(COURT_FILINGS_DIR.rglob("*.md")) if COURT_FILINGS_DIR.exists() else []

        if not md_files:
            print(f"  No .md files found in {COURT_FILINGS_DIR}")
            return results

        print(f"  Found {len(md_files)} .md files to check")
        for i, f in enumerate(md_files, 1):
            print(f"  [{i}/{len(md_files)}] {f.name}...")
            r = self.verify_document(str(f))
            results.append(r)

        return results

    def close(self) -> None:
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None


def _print_report(report: Dict[str, Any]) -> None:
    """Print human-readable verification report."""
    print(f"\n{'='*60}")
    print(f"CITATION VERIFICATION REPORT")
    print(f"{'='*60}")

    if "file" in report:
        print(f"  File: {report['file']}")
    print(f"  Total citations: {report.get('total_citations', 0)}")

    summary = report.get("summary", {})
    print(f"\n  ✓ Valid:       {summary.get('valid', 0)}")
    print(f"  ≈ Close match: {summary.get('close_match', 0)}")
    print(f"  ✗ Not found:   {summary.get('not_found', 0)}")
    print(f"  ! Error:       {summary.get('error', 0)}")

    results = report.get("results", [])
    if results:
        print(f"\n  {'─'*56}")
        for r in results:
            status_icon = {"valid": "✓", "close_match": "≈", "not_found": "✗", "error": "!"}.get(r["status"], "?")
            print(f"  {status_icon} [{r['type']}] {r['citation']}")
            if r.get("matched_rule"):
                print(f"      → Matched: {r['matched_rule']}")
            if r.get("suggestions"):
                print(f"      → Suggestions: {', '.join(r['suggestions'][:3])}")

    print(f"{'='*60}")


# ── CLI ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Verify legal citations against litigation database"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", type=str, help="Path to .md document to verify")
    group.add_argument("--all", action="store_true", help="Verify all .md in 04_COURT_FILINGS/")
    group.add_argument("--text", type=str, help="Raw text to verify")

    args = parser.parse_args()

    verifier = CitationVerifier()

    try:
        if args.file:
            report = verifier.verify_document(args.file)
            _print_report(report)
        elif args.all:
            reports = verifier.verify_all_filings()
            for r in reports:
                _print_report(r)
            # Summary
            total = sum(r.get("total_citations", 0) for r in reports)
            valid = sum(r.get("summary", {}).get("valid", 0) for r in reports)
            print(f"\n  OVERALL: {valid}/{total} citations verified across {len(reports)} files")
        elif args.text:
            report = verifier.verify_text(args.text)
            _print_report(report)
    finally:
        verifier.close()
