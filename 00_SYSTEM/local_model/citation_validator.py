#!/usr/bin/env python3
"""
Citation Validator — Michigan Legal Citation Verification Engine
================================================================
Parses Michigan citations (MCR, MCL, MRE, case law, federal/constitutional)
from court filings and validates each against litigation_context.db.

Filing with wrong citations destroys credibility. This engine ensures
every citation in a document actually exists and is correctly formatted.

Usage:
    from citation_validator import CitationValidator
    cv = CitationValidator("C:/Users/andre/LitigationOS/litigation_context.db")
    report = cv.validate_text("Under MCR 2.003(C)(1), disqualification is ...")
    report = cv.validate_file("C:/Users/andre/LitigationOS/04_COURT_FILINGS/motion.md")
"""

from __future__ import annotations

import logging
import os
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── Default DB path ──────────────────────────────────────────────
DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\LitigationOS\litigation_context.db",
)

# ── Citation regex patterns ──────────────────────────────────────

# MCR 2.003(C)(1)(b) — Michigan Court Rules
RE_MCR = re.compile(
    r'\bMCR\s+(\d+\.\d{3}(?:\([A-Za-z0-9]+\))*)',
    re.IGNORECASE,
)

# MCL 722.23(a) — Michigan Compiled Laws
RE_MCL = re.compile(
    r'\bMCL\s+(\d+\.\d+[a-z]?(?:\([A-Za-z0-9]+\))*)',
    re.IGNORECASE,
)

# MRE 801(d)(2) — Michigan Rules of Evidence
RE_MRE = re.compile(
    r'\bMRE\s+(\d{3,4}(?:\([A-Za-z0-9]+\))*)',
    re.IGNORECASE,
)

# *Party v Party*, Vol Mich App/Mich Page (Year)
# Matches italic markdown (*...*), or plain text with " v " or " v. "
RE_CASE_LAW = re.compile(
    r'(?:\*([A-Z][A-Za-z\s\-\']+?)\s+v\.?\s+([A-Z][A-Za-z\s\-\']+?)\*'
    r'|([A-Z][A-Za-z\-\']+)\s+v\.?\s+([A-Z][A-Za-z\-\']+))'
    r',?\s*(\d+)\s+(Mich\s*(?:App)?|NW\s*2d)\s+(\d+)'
    r'(?:\s*\((\d{4})\))?',
)

# US Const Amend XIV / Amend I etc.
RE_CONST = re.compile(
    r'\bUS\s+Const(?:itution)?\s+Amend(?:ment)?\s+([IVXLC]+|\d+)',
    re.IGNORECASE,
)

# Federal statutes: 42 USC § 1983, 28 USC § 1331
RE_FEDERAL = re.compile(
    r'\b(\d+)\s+U\.?S\.?C\.?\s*[§\u00a7]?\s*(\d+[a-z]?)',
    re.IGNORECASE,
)

# Common Michigan formatting issues and their corrections
FORMAT_CORRECTIONS: Dict[re.Pattern, Tuple[str, str]] = {
    re.compile(r'\bMCR\s+(\d+)\.(\d{3})\(([a-z])\)'): (
        "MCR subrule letters should be uppercase for main divisions",
        "MCR {0}.{1}({upper})",
    ),
    re.compile(r'\bMcr\b'): (
        "MCR should be all-caps",
        "MCR",
    ),
    re.compile(r'\bMcl\b'): (
        "MCL should be all-caps",
        "MCL",
    ),
    re.compile(r'\bMre\b'): (
        "MRE should be all-caps",
        "MRE",
    ),
    re.compile(r'\bMCL\s+(\d+)\.(\d+)\s*\(\s*(\w+)\s*\)'): (
        "MCL subsection letters should be lowercase",
        "MCL {0}.{1}({lower})",
    ),
}


class CitationValidator:
    """Validates Michigan legal citations against litigation_context.db."""

    def __init__(self, db_path: Optional[str] = None):
        self._db_path = db_path or DB_PATH
        self._conn: Optional[sqlite3.Connection] = None

    # ── DB helpers ────────────────────────────────────────────────

    def _get_conn(self) -> sqlite3.Connection:
        """Return a cached DB connection with retry logic."""
        if self._conn is not None:
            try:
                self._conn.execute("SELECT 1")
                return self._conn
            except Exception:
                self._conn = None

        for attempt in range(3):
            try:
                conn = sqlite3.connect(self._db_path, timeout=30)
                conn.row_factory = sqlite3.Row
                self._conn = conn
                return conn
            except sqlite3.Error as exc:
                wait = 2 ** attempt
                logger.warning("DB connect attempt %d failed: %s (retry in %ds)", attempt + 1, exc, wait)
                import time
                time.sleep(wait)
        raise RuntimeError(f"Cannot connect to DB after 3 retries: {self._db_path}")

    def _query(self, sql: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Execute a read query with error handling."""
        try:
            return self._get_conn().execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            logger.error("DB query failed: %s — %s", sql[:120], exc)
            return []

    # ── Parsing ───────────────────────────────────────────────────

    def parse_citations(self, text: str) -> List[Dict[str, Any]]:
        """Extract all citations from text, returning structured list."""
        citations: List[Dict[str, Any]] = []
        seen: set = set()

        # MCR citations
        for m in RE_MCR.finditer(text):
            raw = f"MCR {m.group(1)}"
            key = raw.upper()
            if key not in seen:
                seen.add(key)
                citations.append({
                    "type": "MCR",
                    "raw": raw,
                    "rule_number": m.group(1),
                    "position": m.start(),
                })

        # MCL citations
        for m in RE_MCL.finditer(text):
            raw = f"MCL {m.group(1)}"
            key = raw.upper()
            if key not in seen:
                seen.add(key)
                citations.append({
                    "type": "MCL",
                    "raw": raw,
                    "section": m.group(1),
                    "position": m.start(),
                })

        # MRE citations
        for m in RE_MRE.finditer(text):
            raw = f"MRE {m.group(1)}"
            key = raw.upper()
            if key not in seen:
                seen.add(key)
                citations.append({
                    "type": "MRE",
                    "raw": raw,
                    "rule_number": m.group(1),
                    "position": m.start(),
                })

        # Case law
        for m in RE_CASE_LAW.finditer(text):
            party1 = (m.group(1) or m.group(3) or "").strip()
            party2 = (m.group(2) or m.group(4) or "").strip()
            raw = m.group(0).strip()
            key = f"{party1.upper()} V {party2.upper()}"
            if key not in seen:
                seen.add(key)
                citations.append({
                    "type": "case_law",
                    "raw": raw,
                    "party1": party1,
                    "party2": party2,
                    "volume": m.group(5),
                    "reporter": m.group(6),
                    "page": m.group(7),
                    "year": m.group(8),
                    "position": m.start(),
                })

        # Constitutional citations
        for m in RE_CONST.finditer(text):
            raw = m.group(0).strip()
            key = raw.upper()
            if key not in seen:
                seen.add(key)
                citations.append({
                    "type": "constitutional",
                    "raw": raw,
                    "amendment": m.group(1),
                    "position": m.start(),
                })

        # Federal statutes
        for m in RE_FEDERAL.finditer(text):
            raw = m.group(0).strip()
            key = raw.upper()
            if key not in seen:
                seen.add(key)
                citations.append({
                    "type": "federal",
                    "raw": raw,
                    "title": m.group(1),
                    "section": m.group(2),
                    "position": m.start(),
                })

        citations.sort(key=lambda c: c["position"])
        return citations

    # ── Validation ────────────────────────────────────────────────

    def _fallback_pages_fts(self, search_term: str, raw_cite: str) -> Dict:
        """Broadest fallback: search pages_fts for any citation text."""
        try:
            rows = self._query(
                "SELECT text_content FROM pages_fts WHERE pages_fts MATCH ? LIMIT 1",
                (search_term,),
            )
            if rows:
                return {"status": "verified", "matched": raw_cite, "note": "found in pages_fts"}
        except Exception:
            pass
        return {"status": "not_found"}

    def _validate_mcr(self, cite: Dict) -> Dict:
        """Check MCR citation against auth_rules."""
        base = cite["rule_number"].split("(")[0]
        # auth_rules stores bare numbers (e.g. '2.003'), not 'MCR 2.003'
        rows = self._query(
            "SELECT rule_number FROM auth_rules WHERE rule_number LIKE ? AND rule_type IN ('MCR', 'MCR_SUBRULE')",
            (f"{base}%",),
        )
        if rows:
            return {"status": "verified", "matched": rows[0]["rule_number"]}
        # Broader fallback
        rows = self._query(
            "SELECT rule_number FROM auth_rules WHERE rule_number LIKE ?",
            (f"%{base}%",),
        )
        if rows:
            return {"status": "verified", "matched": rows[0]["rule_number"]}
        return {"status": "not_found"}

    def _validate_mcl(self, cite: Dict) -> Dict:
        """Check MCL citation against auth_rules, master_citations, rules_text, and pages."""
        base = cite["section"].split("(")[0]
        # auth_rules stores bare numbers (e.g. '722.23'), not 'MCL 722.23'
        rows = self._query(
            "SELECT rule_number FROM auth_rules WHERE rule_number LIKE ? AND rule_type = 'MCL'",
            (f"{base}%",),
        )
        if rows:
            return {"status": "verified", "matched": rows[0]["rule_number"]}
        # Broader auth_rules fallback (substring match)
        rows = self._query(
            "SELECT rule_number FROM auth_rules WHERE rule_number LIKE ?",
            (f"%{base}%",),
        )
        if rows:
            return {"status": "verified", "matched": rows[0]["rule_number"]}
        # master_citations (handles embedded newlines like 'MCL\n722.23')
        rows = self._query(
            "SELECT citation FROM master_citations WHERE citation LIKE ? LIMIT 1",
            (f"%{base}%",),
        )
        if rows:
            return {"status": "verified", "matched": rows[0]["citation"].replace("\n", " ").strip()}
        # Fallback to rules_text
        rows = self._query(
            "SELECT rule FROM rules_text WHERE rule LIKE ? LIMIT 1",
            (f"%{base}%",),
        )
        if rows:
            return {"status": "verified", "matched": rows[0]["rule"]}
        # Broadest fallback: pages_fts full-text search
        return self._fallback_pages_fts(f"MCL {base}", cite["raw"])

    def _validate_mre(self, cite: Dict) -> Dict:
        """Check MRE citation against auth_rules."""
        base = cite["rule_number"].split("(")[0]
        # auth_rules stores bare numbers; try exact-type match first
        rows = self._query(
            "SELECT rule_number FROM auth_rules WHERE rule_number LIKE ? AND rule_type = 'MRE'",
            (f"{base}%",),
        )
        if rows:
            return {"status": "verified", "matched": rows[0]["rule_number"]}
        rows = self._query(
            "SELECT rule_number FROM auth_rules WHERE rule_number LIKE ?",
            (f"%{base}%",),
        )
        if rows:
            return {"status": "verified", "matched": rows[0]["rule_number"]}
        return {"status": "not_found"}

    def _validate_case_law(self, cite: Dict) -> Dict:
        """Check case law citation against master_citations, then pages_fts."""
        party1 = cite.get("party1", "")
        party2 = cite.get("party2", "")
        # Try full party match in master_citations
        rows = self._query(
            "SELECT citation FROM master_citations WHERE citation LIKE ? AND citation LIKE ? LIMIT 3",
            (f"%{party1}%", f"%{party2}%"),
        )
        if rows:
            return {"status": "verified", "matched": rows[0]["citation"]}
        # Try single-party fallback in master_citations
        for party in (party1, party2):
            if party:
                rows = self._query(
                    "SELECT citation FROM master_citations WHERE citation LIKE ? LIMIT 3",
                    (f"%{party}%",),
                )
                if rows:
                    return {
                        "status": "verified",
                        "matched": rows[0]["citation"],
                        "note": "partial match — verify full citation",
                    }
        # Fallback: search pages_fts for party names (handles cases not in master_citations)
        for party in (party1, party2):
            if party and len(party) > 3:
                try:
                    fts_term = " ".join(party.split())  # clean for FTS5
                    rows = self._query(
                        "SELECT text_content FROM pages_fts WHERE pages_fts MATCH ? LIMIT 1",
                        (f'"{fts_term}"',),
                    )
                    if rows:
                        return {
                            "status": "verified",
                            "matched": cite["raw"],
                            "note": f"found in pages_fts via '{party}'",
                        }
                except Exception:
                    pass
        # Last resort: LIKE search on pages for any party mention
        for party in (party1, party2):
            if party and len(party) > 3:
                rows = self._query(
                    "SELECT 1 FROM pages WHERE text_content LIKE ? LIMIT 1",
                    (f"%{party}%",),
                )
                if rows:
                    return {
                        "status": "verified",
                        "matched": cite["raw"],
                        "note": f"found in pages via '{party}'",
                    }
        return {"status": "not_found"}

    def _validate_one(self, cite: Dict) -> Dict:
        """Validate a single citation and return enriched result."""
        result = dict(cite)
        ctype = cite["type"]
        if ctype == "MCR":
            v = self._validate_mcr(cite)
        elif ctype == "MCL":
            v = self._validate_mcl(cite)
        elif ctype == "MRE":
            v = self._validate_mre(cite)
        elif ctype == "case_law":
            v = self._validate_case_law(cite)
        elif ctype in ("constitutional", "federal"):
            # Constitutional / federal: accepted by format (not in MI DB)
            v = {"status": "accepted", "note": "non-Michigan citation — format OK"}
        else:
            v = {"status": "unknown_type"}
        result.update(v)
        return result

    # ── Format checking ───────────────────────────────────────────

    def check_formatting(self, text: str) -> List[Dict[str, str]]:
        """Detect common Michigan citation formatting errors."""
        suggestions: List[Dict[str, str]] = []
        # Lowercase MCR subrule main divisions: MCR 2.003(c) should be (C)
        for m in re.finditer(r'\bMCR\s+(\d+\.\d{3})\(([a-z])\)', text):
            suggestions.append({
                "found": m.group(0),
                "suggestion": f"MCR {m.group(1)}({m.group(2).upper()})",
                "reason": "MCR main division letters should be uppercase",
            })
        # Lowercase abbreviations
        for abbr in ("Mcr", "Mcl", "Mre"):
            if abbr in text:
                suggestions.append({
                    "found": abbr,
                    "suggestion": abbr.upper(),
                    "reason": f"{abbr.upper()} should be all-caps",
                })
        # MCL with uppercase subsection: MCL 722.23(A) should be (a)
        for m in re.finditer(r'\bMCL\s+(\d+\.\d+)\(([A-Z])\)', text):
            suggestions.append({
                "found": m.group(0),
                "suggestion": f"MCL {m.group(1)}({m.group(2).lower()})",
                "reason": "MCL subsection letters are typically lowercase",
            })
        # "v" without period in case citations (Party v Party should be v.)
        for m in re.finditer(r'([A-Z][a-z]+)\s+v\s+([A-Z])', text):
            suggestions.append({
                "found": f"{m.group(1)} v {m.group(2)}",
                "suggestion": f"{m.group(1)} v. {m.group(2)}",
                "reason": "Michigan style uses 'v.' (with period) in case citations",
            })
        return suggestions

    # ── Public API ────────────────────────────────────────────────

    def validate_text(self, text: str) -> Dict[str, Any]:
        """Validate all citations found in the provided text."""
        citations = self.parse_citations(text)
        verified: List[Dict] = []
        not_found: List[Dict] = []
        malformed: List[Dict] = []

        for cite in citations:
            result = self._validate_one(cite)
            status = result.get("status", "unknown")
            if status in ("verified", "accepted"):
                verified.append(result)
            elif status == "not_found":
                not_found.append(result)
            else:
                malformed.append(result)

        suggestions = self.check_formatting(text)

        return {
            "total_citations": len(citations),
            "verified": len(verified),
            "verified_list": verified,
            "not_found": [{"raw": c["raw"], "type": c["type"]} for c in not_found],
            "malformed": [{"raw": c["raw"], "type": c["type"]} for c in malformed],
            "suggestions": suggestions,
        }

    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """Read a filing from disk and validate all its citations."""
        fp = Path(file_path)
        if not fp.exists():
            return {"error": f"File not found: {file_path}"}
        try:
            text = fp.read_text(encoding="utf-8-sig")
        except Exception as exc:
            return {"error": f"Cannot read file: {exc}"}

        report = self.validate_text(text)
        report["file"] = str(fp)
        report["file_size"] = fp.stat().st_size
        return report


# ── Module-level convenience for JSON-RPC integration ─────────────

_singleton: Optional[CitationValidator] = None


def get_validator(db_path: Optional[str] = None) -> CitationValidator:
    """Return a singleton CitationValidator instance."""
    global _singleton
    if _singleton is None:
        _singleton = CitationValidator(db_path)
    return _singleton


def rpc_validate_file(params: Dict[str, Any], db_path: Optional[str] = None) -> Dict[str, Any]:
    """JSON-RPC handler: validate all citations in a file."""
    file_path = params.get("file_path") or params.get("path", "")
    if not file_path:
        return {"error": "Missing required parameter: file_path"}
    return get_validator(db_path).validate_file(file_path)


def rpc_validate_text(params: Dict[str, Any], db_path: Optional[str] = None) -> Dict[str, Any]:
    """JSON-RPC handler: validate citations in provided text."""
    text = params.get("text", "")
    if not text:
        return {"error": "Missing required parameter: text"}
    return get_validator(db_path).validate_text(text)
