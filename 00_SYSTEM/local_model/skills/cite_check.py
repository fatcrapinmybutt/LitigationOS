#!/usr/bin/env python3
"""
MBP LitigationOS -- Citation Check Skill
==========================================
Verify any legal citation against the litigation_context.db.
Returns {valid, found_in, full_text} for each citation checked.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent if 'skills' in str(Path(__file__)) else Path(__file__).resolve().parent))
try:
    from cycle_method import cycle_json, cycle_print
except ImportError:
    cycle_json = lambda obj, **kw: print(json.dumps(obj, default=str))
    cycle_print = print

DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\LitigationOS\litigation_context.db",
)


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


def check_citation(citation: str) -> Dict:
    """
    Verify a single citation against the DB.
    Returns: {valid: bool, found_in: str, full_text: str, citation: str}
    """
    result = {
        "citation": citation,
        "valid": False,
        "found_in": "",
        "full_text": "",
        "confidence": 0.0,
    }

    try:
        conn = _get_db()
        if not conn:
            return result

        clean = citation.strip()

        # Check MCR citations (e.g., MCR 2.003, 2.116(C)(10))
        mcr_match = re.search(r'(?:MCR\s*)?(\d+\.\d+)', clean, re.I)
        if mcr_match:
            rule_num = mcr_match.group(1)
            try:
                row = conn.execute(
                    "SELECT rule_number, title, substr(full_text, 1, 1000) as text "
                    "FROM auth_rules WHERE rule_number LIKE ? LIMIT 1",
                    (f"%{rule_num}%",),
                ).fetchone()
                if row:
                    result["valid"] = True
                    result["found_in"] = "auth_rules"
                    result["full_text"] = f"{row['rule_number']} - {row['title']}: {row['text']}"
                    result["confidence"] = 1.0
                    conn.close()
                    return result
            except Exception:
                pass

            # Fallback to court_rules
            try:
                row = conn.execute(
                    "SELECT rule, chapter, substr(context, 1, 800) as text "
                    "FROM court_rules WHERE rule LIKE ? LIMIT 1",
                    (f"%{rule_num}%",),
                ).fetchone()
                if row:
                    result["valid"] = True
                    result["found_in"] = "court_rules"
                    result["full_text"] = f"{row['rule']}: {row['text']}"
                    result["confidence"] = 0.9
                    conn.close()
                    return result
            except Exception:
                pass

        # Check MCL citations (e.g., MCL 722.23, 600.2950)
        mcl_match = re.search(r'(?:MCL\s*)?(\d+\.\d+)', clean, re.I)
        if mcl_match and 'MCL' in clean.upper():
            mcl_num = mcl_match.group(1)
            try:
                row = conn.execute(
                    "SELECT rule, chapter, substr(context, 1, 800) as text "
                    "FROM rules_text WHERE rule LIKE ? OR context LIKE ? LIMIT 1",
                    (f"%{mcl_num}%", f"%{mcl_num}%"),
                ).fetchone()
                if row:
                    result["valid"] = True
                    result["found_in"] = "rules_text"
                    result["full_text"] = f"{row['rule']}: {row['text']}"
                    result["confidence"] = 1.0
                    conn.close()
                    return result
            except Exception:
                pass

        # Check case law citations in master_citations
        try:
            row = conn.execute(
                "SELECT citation, cite_type, substr(context, 1, 800) as text "
                "FROM master_citations WHERE citation LIKE ? LIMIT 1",
                (f"%{clean[:30]}%",),
            ).fetchone()
            if row:
                result["valid"] = True
                result["found_in"] = "master_citations"
                result["full_text"] = f"{row['citation']}: {row['text']}"
                result["confidence"] = 0.8
                conn.close()
                return result
        except Exception:
            pass

        # Broad search in authority passages
        try:
            row = conn.execute(
                "SELECT section, substr(passage_text, 1, 600) as text "
                "FROM auth_authority_passages WHERE passage_text LIKE ? LIMIT 1",
                (f"%{clean[:20]}%",),
            ).fetchone()
            if row:
                result["valid"] = True
                result["found_in"] = "auth_authority_passages"
                result["full_text"] = f"{row['section']}: {row['text']}"
                result["confidence"] = 0.6
                conn.close()
                return result
        except Exception:
            pass

        conn.close()
    except Exception:
        pass

    return result


def check_all_citations(text: str) -> List[Dict]:
    """
    Extract and verify ALL citations from a block of text.
    Returns list of citation check results.
    """
    results = []
    try:
        # Pattern for MCR citations
        mcr_cites = re.findall(r'MCR\s+\d+\.\d+(?:\([A-Za-z0-9]+\))*', text, re.I)
        for c in mcr_cites:
            results.append(check_citation(c))

        # Pattern for MCL citations
        mcl_cites = re.findall(r'MCL\s+\d+\.\d+[a-z]?(?:\([a-z0-9]+\))*', text, re.I)
        for c in mcl_cites:
            results.append(check_citation(c))

        # Pattern for case law (Party v Party, Vol Mich App Page)
        case_cites = re.findall(
            r'[A-Z][a-z]+\s+v\s+[A-Z][a-z]+(?:,\s*\d+\s+Mich\s+(?:App\s+)?\d+)?',
            text
        )
        for c in case_cites:
            results.append(check_citation(c))

        # Pattern for MRE citations
        mre_cites = re.findall(r'MRE\s+\d+(?:\([a-z0-9]+\))*', text, re.I)
        for c in mre_cites:
            results.append(check_citation(c))

    except Exception:
        pass

    return results


# ── CLI ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) > 1:
        cite = " ".join(sys.argv[1:])
        result = check_citation(cite)
        cycle_json(result)
    else:
        print("Citation Check Skill")
        print("Usage: python cite_check.py 'MCR 2.003(C)(1)'")
