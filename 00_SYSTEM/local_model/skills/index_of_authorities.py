#!/usr/bin/env python3
"""
MBP LitigationOS -- Index of Authorities Generator Skill
==========================================================
Generates the formal Index/Table of Authorities required by
MCR 7.212(B)(2) for Michigan appellate briefs.

Extracts all legal citations from document text, categorizes them
(Cases, Statutes, Court Rules, Constitutional Provisions, Other),
and formats a print-ready index with page references.

Usage:
    from skills.index_of_authorities import IndexOfAuthorities
    idx = IndexOfAuthorities()
    result = idx.generate_index(brief_text)
    print(result)
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parent.parent
        if "skills" in str(Path(__file__))
        else Path(__file__).resolve().parent
    ),
)
try:
    from cycle_method import cycle_json, cycle_print
except ImportError:
    cycle_json = lambda obj, **kw: print(json.dumps(obj, default=str))
    cycle_print = print

DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\LitigationOS\litigation_context.db",
)


# ── Data Classes ─────────────────────────────────────────────────────────────

@dataclass
class Citation:
    """A single legal citation extracted from text."""
    raw_text: str
    normalized: str
    category: str  # "cases", "statutes", "court_rules", "constitutional", "other"
    pages: List[int] = field(default_factory=list)

    def __hash__(self):
        return hash(self.normalized)

    def __eq__(self, other):
        if not isinstance(other, Citation):
            return NotImplemented
        return self.normalized == other.normalized


@dataclass
class IndexResult:
    """Result of index generation."""
    formatted_text: str
    citations: List[Citation]
    categories: Dict[str, List[Citation]]
    total_citations: int
    total_unique: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "formatted_text": self.formatted_text,
            "total_citations": self.total_citations,
            "total_unique": self.total_unique,
            "categories": {
                cat: [{"citation": c.normalized, "pages": c.pages} for c in cites]
                for cat, cites in self.categories.items()
            },
        }


# ── Citation Regex Patterns ──────────────────────────────────────────────────

# Michigan cases: *Case v Case*, Vol Mich/Mich App Page (Year)
# Also handles: People v Name, In re Name, etc.
_MI_CASE_RE = re.compile(
    r"(?:\*)?("
    r"(?:(?:People|In\s+re|In\s+the\s+Matter\s+of)\s+v?\s*)?"
    r"[A-Z][A-Za-z'\-]+(?:\s+v\.?\s+[A-Z][A-Za-z'\-]+)?"
    r")\s*(?:\*)?"
    r",?\s+(\d+)\s+(Mich(?:\s+App)?)\s+(\d+)"
    r"(?:\s*\((\d{4})\))?"
)

# Federal cases: *Case v Case*, Vol US/F.2d/F.3d/F.Supp/F.Supp.2d Page (Year)
_FED_CASE_RE = re.compile(
    r"(?:\*)?("
    r"[A-Z][A-Za-z'\-\.]+(?:\s+v\.?\s+[A-Z][A-Za-z'\-\.]+)?"
    r")\s*(?:\*)?"
    r",?\s+(\d+)\s+"
    r"(U\.?S\.?|F\.?\s*(?:2d|3d|4th)|F\.?\s*Supp\.?\s*(?:2d|3d)?|S\.?\s*Ct\.?|L\.?\s*Ed\.?\s*(?:2d)?)"
    r"\s+(\d+)"
    r"(?:\s*\((\d{4})\))?"
)

# MCR: MCR X.XXX(X)(x)
_MCR_RE = re.compile(
    r"\bMCR\s+(\d+\.\d+(?:\([A-Za-z0-9]+\))*(?:\([a-z]\))*)"
)

# MCL: MCL XXX.XXXX or MCL XXX.XXXXa
_MCL_RE = re.compile(
    r"\bMCL\s+(\d+\.\d+[a-z]?(?:\([A-Za-z0-9]+\))*)"
)

# MRE: MRE XXX(x)(x)
_MRE_RE = re.compile(
    r"\bMRE\s+(\d+(?:\([a-z]\))*(?:\(\d+\))*)"
)

# Michigan Constitution: Const 1963, art X, § X
_MI_CONST_RE = re.compile(
    r"\bConst\s+1963\s*,?\s*art(?:icle)?\s+(\d+|[IVX]+)\s*,?\s*§\s*(\d+)",
    re.IGNORECASE,
)

# US Constitution: US Const, Am XIV / Art I, § 8
_US_CONST_RE = re.compile(
    r"\bU\.?S\.?\s*Const(?:itution)?\s*,?\s*"
    r"(?:Am(?:end(?:ment)?)?\.?\s*([IVXLC]+|\d+)|"
    r"Art(?:icle)?\s*([IVXLC]+|\d+)(?:\s*,?\s*§\s*(\d+))?)",
    re.IGNORECASE,
)

# Federal statutes: 42 USC § 1983, 28 USC § 1343
_FED_STATUTE_RE = re.compile(
    r"\b(\d+)\s+U\.?S\.?C\.?\s*§\s*(\d+[a-z]?(?:\([a-z0-9]+\))*)"
)

# Catch-all: remaining *Italic Case v Case* patterns
_ITALIC_CASE_RE = re.compile(
    r"\*([A-Z][A-Za-z'\-\.\s]+?v\.?\s+[A-Z][A-Za-z'\-\.\s]+?)\*"
)


# ── Approximate page calculation ─────────────────────────────────────────────
_WORDS_PER_PAGE = 250  # double-spaced, 12pt


def _estimate_page(text: str, char_offset: int) -> int:
    """Estimate the page number for a character offset in the document."""
    preceding = text[:char_offset]
    word_count = len(preceding.split())
    return max(1, (word_count // _WORDS_PER_PAGE) + 1)


def _normalize_case_name(name: str) -> str:
    """Normalize a case name for deduplication and sorting."""
    name = re.sub(r"\s+", " ", name.strip())
    name = name.strip("*").strip()
    # Title case
    words = name.split()
    normalized = []
    for w in words:
        if w.lower() in ("v", "v.", "vs", "vs."):
            normalized.append("v")
        else:
            normalized.append(w)
    return " ".join(normalized)


def _get_db() -> Optional[sqlite3.Connection]:
    """Get read-only DB connection."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA query_only=ON")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception:
        return None


# ── Main Class ───────────────────────────────────────────────────────────────

class IndexOfAuthorities:
    """Generates MCR 7.212(B)(2)-compliant Index of Authorities.

    Extracts all legal citations from appellate brief text,
    categorizes them, and produces a formatted index with page references.
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    # ── Extract all citations ────────────────────────────────────────

    def extract_citations(self, document_text: str) -> List[Citation]:
        """Extract all legal citations from document text.

        Args:
            document_text: Full text of the appellate brief.

        Returns:
            List of Citation objects with category, normalized text, and page locations.
        """
        citations_map: Dict[str, Citation] = {}

        # 1. Michigan cases
        for m in _MI_CASE_RE.finditer(document_text):
            name = _normalize_case_name(m.group(1))
            vol, reporter, page = m.group(2), m.group(3), m.group(4)
            year = m.group(5) or ""
            year_str = f" ({year})" if year else ""
            normalized = f"{name}, {vol} {reporter} {page}{year_str}"
            pg = _estimate_page(document_text, m.start())
            if normalized not in citations_map:
                citations_map[normalized] = Citation(
                    raw_text=m.group(0), normalized=normalized,
                    category="cases", pages=[pg],
                )
            elif pg not in citations_map[normalized].pages:
                citations_map[normalized].pages.append(pg)

        # 2. Federal cases
        for m in _FED_CASE_RE.finditer(document_text):
            name = _normalize_case_name(m.group(1))
            vol, reporter, page = m.group(2), m.group(3), m.group(4)
            year = m.group(5) or ""
            year_str = f" ({year})" if year else ""
            reporter_clean = reporter.replace(" ", "")
            normalized = f"{name}, {vol} {reporter_clean} {page}{year_str}"
            pg = _estimate_page(document_text, m.start())
            if normalized not in citations_map:
                citations_map[normalized] = Citation(
                    raw_text=m.group(0), normalized=normalized,
                    category="cases", pages=[pg],
                )
            elif pg not in citations_map[normalized].pages:
                citations_map[normalized].pages.append(pg)

        # 3. Catch italic case names not caught above
        for m in _ITALIC_CASE_RE.finditer(document_text):
            name = _normalize_case_name(m.group(1))
            # Skip if already captured with full citation
            already = any(name.lower() in k.lower() for k in citations_map)
            if already:
                continue
            pg = _estimate_page(document_text, m.start())
            normalized = name
            if normalized not in citations_map:
                citations_map[normalized] = Citation(
                    raw_text=m.group(0), normalized=normalized,
                    category="cases", pages=[pg],
                )
            elif pg not in citations_map[normalized].pages:
                citations_map[normalized].pages.append(pg)

        # 4. MCR
        for m in _MCR_RE.finditer(document_text):
            rule = f"MCR {m.group(1)}"
            pg = _estimate_page(document_text, m.start())
            if rule not in citations_map:
                citations_map[rule] = Citation(
                    raw_text=m.group(0), normalized=rule,
                    category="court_rules", pages=[pg],
                )
            elif pg not in citations_map[rule].pages:
                citations_map[rule].pages.append(pg)

        # 5. MCL
        for m in _MCL_RE.finditer(document_text):
            statute = f"MCL {m.group(1)}"
            pg = _estimate_page(document_text, m.start())
            if statute not in citations_map:
                citations_map[statute] = Citation(
                    raw_text=m.group(0), normalized=statute,
                    category="statutes", pages=[pg],
                )
            elif pg not in citations_map[statute].pages:
                citations_map[statute].pages.append(pg)

        # 6. MRE
        for m in _MRE_RE.finditer(document_text):
            rule = f"MRE {m.group(1)}"
            pg = _estimate_page(document_text, m.start())
            if rule not in citations_map:
                citations_map[rule] = Citation(
                    raw_text=m.group(0), normalized=rule,
                    category="court_rules", pages=[pg],
                )
            elif pg not in citations_map[rule].pages:
                citations_map[rule].pages.append(pg)

        # 7. Michigan Constitution
        for m in _MI_CONST_RE.finditer(document_text):
            art, sec = m.group(1), m.group(2)
            normalized = f"Const 1963, art {art}, § {sec}"
            pg = _estimate_page(document_text, m.start())
            if normalized not in citations_map:
                citations_map[normalized] = Citation(
                    raw_text=m.group(0), normalized=normalized,
                    category="constitutional", pages=[pg],
                )
            elif pg not in citations_map[normalized].pages:
                citations_map[normalized].pages.append(pg)

        # 8. US Constitution
        for m in _US_CONST_RE.finditer(document_text):
            amend = m.group(1)
            article = m.group(2)
            section = m.group(3)
            if amend:
                normalized = f"US Const, Am {amend}"
            elif article and section:
                normalized = f"US Const, Art {article}, § {section}"
            elif article:
                normalized = f"US Const, Art {article}"
            else:
                continue
            pg = _estimate_page(document_text, m.start())
            if normalized not in citations_map:
                citations_map[normalized] = Citation(
                    raw_text=m.group(0), normalized=normalized,
                    category="constitutional", pages=[pg],
                )
            elif pg not in citations_map[normalized].pages:
                citations_map[normalized].pages.append(pg)

        # 9. Federal statutes
        for m in _FED_STATUTE_RE.finditer(document_text):
            title, section = m.group(1), m.group(2)
            normalized = f"{title} USC § {section}"
            pg = _estimate_page(document_text, m.start())
            if normalized not in citations_map:
                citations_map[normalized] = Citation(
                    raw_text=m.group(0), normalized=normalized,
                    category="statutes", pages=[pg],
                )
            elif pg not in citations_map[normalized].pages:
                citations_map[normalized].pages.append(pg)

        # Sort pages for each citation
        for c in citations_map.values():
            c.pages.sort()

        return list(citations_map.values())

    # ── Categorize citations ─────────────────────────────────────────

    def categorize_citations(
        self, citations: List[Citation]
    ) -> Dict[str, List[Citation]]:
        """Group citations into MCR 7.212(B)(2) categories.

        Args:
            citations: List of Citation objects.

        Returns:
            Dict with keys: 'cases', 'statutes', 'court_rules',
            'constitutional', 'other'. Each value is a sorted list of Citations.
        """
        categories: Dict[str, List[Citation]] = {
            "cases": [],
            "statutes": [],
            "court_rules": [],
            "constitutional": [],
            "other": [],
        }

        for c in citations:
            cat = c.category if c.category in categories else "other"
            categories[cat].append(c)

        # Sort each category alphabetically by normalized text
        for cat in categories:
            categories[cat].sort(key=lambda x: x.normalized.lower())

        return categories

    # ── Generate formatted index ─────────────────────────────────────

    def generate_index(self, document_text: str) -> str:
        """Generate a complete, formatted Index of Authorities per MCR 7.212(B)(2).

        Args:
            document_text: Full text of the appellate brief.

        Returns:
            Formatted Index of Authorities text ready for inclusion in the brief.
        """
        citations = self.extract_citations(document_text)
        categories = self.categorize_citations(citations)

        lines: List[str] = []
        lines.append("")
        lines.append("INDEX OF AUTHORITIES")
        lines.append("")

        _SECTION_HEADERS = {
            "cases": "CASES",
            "statutes": "STATUTES",
            "court_rules": "COURT RULES",
            "constitutional": "CONSTITUTIONAL PROVISIONS",
            "other": "OTHER AUTHORITIES",
        }

        _SECTION_ORDER = ["cases", "statutes", "court_rules", "constitutional", "other"]

        for cat_key in _SECTION_ORDER:
            cites = categories.get(cat_key, [])
            if not cites:
                continue

            header = _SECTION_HEADERS[cat_key]
            lines.append(f"{header:<56s}Page(s)")
            lines.append("")

            for c in cites:
                page_str = ", ".join(str(p) for p in c.pages)
                cite_text = c.normalized
                # Format with dotted leaders
                leader_len = max(4, 60 - len(cite_text) - len(page_str))
                leader = " " + "." * leader_len + " "
                lines.append(f"{cite_text}{leader}{page_str}")

            lines.append("")

        return "\n".join(lines)

    # ── Full result with metadata ────────────────────────────────────

    def generate_index_result(self, document_text: str) -> IndexResult:
        """Generate Index of Authorities with full metadata.

        Args:
            document_text: Full text of the appellate brief.

        Returns:
            IndexResult with formatted text, citation list, categories, and counts.
        """
        citations = self.extract_citations(document_text)
        categories = self.categorize_citations(citations)
        formatted = self.generate_index(document_text)

        return IndexResult(
            formatted_text=formatted,
            citations=citations,
            categories=categories,
            total_citations=sum(len(c.pages) for c in citations),
            total_unique=len(citations),
        )

    # ── DB enrichment (optional) ─────────────────────────────────────

    def enrich_from_db(self, citations: List[Citation]) -> List[Citation]:
        """Attempt to enrich citations with full-text from litigation DB.

        Adds verified=True flag and full citation text from auth_rules
        or master_citations tables when available.

        Args:
            citations: List of Citation objects to enrich.

        Returns:
            Same list with enriched data where available.
        """
        conn = _get_db()
        if not conn:
            return citations

        try:
            for c in citations:
                if c.category == "court_rules":
                    # Try auth_rules
                    base = c.normalized.replace("MCR ", "").replace("MRE ", "")
                    base_num = re.split(r"\(", base)[0]
                    try:
                        row = conn.execute(
                            "SELECT rule_number, title FROM auth_rules "
                            "WHERE rule_number LIKE ? LIMIT 1",
                            (f"%{base_num}%",),
                        ).fetchone()
                        if row:
                            c.raw_text = f"{c.normalized} — {row['title']} [DB verified]"
                    except Exception:
                        pass
                elif c.category == "statutes":
                    base = c.normalized
                    try:
                        row = conn.execute(
                            "SELECT rule_number, title FROM auth_rules "
                            "WHERE rule_number LIKE ? LIMIT 1",
                            (f"%{base}%",),
                        ).fetchone()
                        if row:
                            c.raw_text = f"{c.normalized} — {row['title']} [DB verified]"
                    except Exception:
                        pass
        finally:
            conn.close()

        return citations


# ── Module-level convenience functions ───────────────────────────────────────

_default_generator: Optional[IndexOfAuthorities] = None


def _get_generator() -> IndexOfAuthorities:
    global _default_generator
    if _default_generator is None:
        _default_generator = IndexOfAuthorities()
    return _default_generator


def extract_citations(document_text: str) -> List[Citation]:
    """Extract all legal citations from text. See IndexOfAuthorities.extract_citations."""
    return _get_generator().extract_citations(document_text)


def generate_index(document_text: str) -> str:
    """Generate formatted Index of Authorities. See IndexOfAuthorities.generate_index."""
    return _get_generator().generate_index(document_text)


def categorize_citations(citations: List[Citation]) -> Dict[str, List[Citation]]:
    """Categorize citations. See IndexOfAuthorities.categorize_citations."""
    return _get_generator().categorize_citations(citations)


# ── CLI entry point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate MCR 7.212(B)(2) Index of Authorities from an appellate brief."
    )
    parser.add_argument("file", nargs="?", help="Brief file to process")
    parser.add_argument(
        "--json", "-j", action="store_true",
        help="Output as JSON instead of formatted text",
    )
    parser.add_argument(
        "--enrich", "-e", action="store_true",
        help="Enrich citations from litigation DB",
    )
    args = parser.parse_args()

    if not args.file:
        parser.error("Provide a brief file to process.")

    with open(args.file, "r", encoding="utf-8") as f:
        doc_text = f.read()

    gen = IndexOfAuthorities()
    result = gen.generate_index_result(doc_text)

    if args.enrich:
        gen.enrich_from_db(result.citations)

    if args.json:
        cycle_json(result.to_dict())
    else:
        print(result.formatted_text)
        print(f"\n--- {result.total_unique} unique authorities, "
              f"{result.total_citations} total references ---")
