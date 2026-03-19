# -*- coding: utf-8 -*-
"""Engine 13: Redaction Engine — PII redaction per MCR 1.109(D)(9).

Michigan Court Rule 1.109(D)(9) requires redaction of:
  - Social Security Numbers: show last 4 only (XXX-XX-1234)
  - Dates of birth for minors: year only (XX/XX/2019)
  - Financial account numbers: last 4 only (XXXX-XXXX-XXXX-5678)
  - Minor children names: initials only in public filings

Case-specific:
  - Minor child: Lincoln D.W. → "LDW" in public filings

Redaction levels:
  - standard:  MCR 1.109(D)(9) minimum requirements
  - enhanced:  Extra safety — redact emails, phone numbers, addresses
  - sealed:    Maximum redaction — all PII plus party addresses, DOBs

Authority:
    MCR 1.109(D)(9) — Redaction requirements
    MCR 3.903(A)(2) — Minor protection
    MCR 8.119(H)    — Public access / confidential filings
"""
import sys
import os
import io
import re
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# ── UTF-8 fix for Windows console ───────────────────────────────────────────
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
elif sys.stdout is None or not hasattr(sys.stdout, "encoding") or sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer if sys.stdout else open(os.devnull, "w"), encoding="utf-8"
    )
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

# ── Case-specific constants ─────────────────────────────────────────────────
MINOR_CHILDREN = {
    "Lincoln D.W.": "LDW",
    "Lincoln D. W.": "LDW",
    "Lincoln Watson": "LDW",
    "Lincoln D. Watson": "LDW",
    "Lincoln Pigors": "LDW",
    "Lincoln D. Pigors": "LDW",
    "Lincoln": "LDW",  # context-dependent — flagged for review
}

# Names that should NEVER be redacted (parties to the case)
PARTY_NAMES = {
    "Andrew Pigors", "Tiffany Watson", "Jenny L. McNeill",
    "Jenny McNeill", "Ron Berry", "Emily Watson",
}

# ── Regex patterns for PII detection ────────────────────────────────────────
PII_PATTERNS: Dict[str, Dict] = {
    "ssn_full": {
        "pattern": re.compile(r"\b(\d{3})[-– ]?(\d{2})[-– ]?(\d{4})\b"),
        "description": "Social Security Number (full)",
        "authority": "MCR 1.109(D)(9)(a)",
        "levels": ["standard", "enhanced", "sealed"],
    },
    "dob_full": {
        "pattern": re.compile(
            r"\b(0[1-9]|1[0-2])[/\-](0[1-9]|[12]\d|3[01])[/\-]"
            r"(19\d{2}|20[0-2]\d)\b"
        ),
        "description": "Date of birth (MM/DD/YYYY or MM-DD-YYYY)",
        "authority": "MCR 1.109(D)(9)(b)",
        "levels": ["standard", "enhanced", "sealed"],
    },
    "dob_written": {
        "pattern": re.compile(
            r"\b(?:born\s+(?:on\s+)?|DOB[:\s]+|date\s+of\s+birth[:\s]+)"
            r"(\w+\s+\d{1,2},?\s+\d{4})",
            re.IGNORECASE,
        ),
        "description": "Date of birth (written form)",
        "authority": "MCR 1.109(D)(9)(b)",
        "levels": ["standard", "enhanced", "sealed"],
    },
    "financial_account": {
        "pattern": re.compile(r"\b(\d{4})[-– ]?(\d{4})[-– ]?(\d{4})[-– ]?(\d{4})\b"),
        "description": "Financial account number (16-digit)",
        "authority": "MCR 1.109(D)(9)(c)",
        "levels": ["standard", "enhanced", "sealed"],
    },
    "bank_account": {
        "pattern": re.compile(
            r"(?:account|acct)[#:\s]+(\d{4,})", re.IGNORECASE
        ),
        "description": "Bank account number",
        "authority": "MCR 1.109(D)(9)(c)",
        "levels": ["standard", "enhanced", "sealed"],
    },
    "routing_number": {
        "pattern": re.compile(
            r"(?:routing|ABA)[#:\s]+(\d{9})\b", re.IGNORECASE
        ),
        "description": "Bank routing number",
        "authority": "MCR 1.109(D)(9)(c)",
        "levels": ["enhanced", "sealed"],
    },
    "email": {
        "pattern": re.compile(
            r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Z|a-z]{2,}\b"
        ),
        "description": "Email address",
        "authority": "Privacy — enhanced redaction",
        "levels": ["enhanced", "sealed"],
    },
    "phone": {
        "pattern": re.compile(
            r"\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
        ),
        "description": "Phone number",
        "authority": "Privacy — enhanced redaction",
        "levels": ["enhanced", "sealed"],
    },
    "drivers_license": {
        "pattern": re.compile(
            r"(?:DL|driver'?s?\s*license)[#:\s]*([A-Z]\s?\d{3}\s?\d{3}\s?\d{3}\s?\d{3})",
            re.IGNORECASE,
        ),
        "description": "Driver's license number",
        "authority": "MCR 1.109(D)(9) — sealed level",
        "levels": ["sealed"],
    },
    "street_address": {
        "pattern": re.compile(
            r"\b\d{1,5}\s+(?:[A-Z][a-z]+\s+){1,3}"
            r"(?:St(?:reet)?|Ave(?:nue)?|Blvd|Dr(?:ive)?|Ln|Rd|Ct|Pl|Way)"
            r"\.?\b",
        ),
        "description": "Street address",
        "authority": "Privacy — sealed level",
        "levels": ["sealed"],
    },
}

# Redaction level hierarchy
REDACTION_LEVELS = {
    "standard": {
        "description": "MCR 1.109(D)(9) minimum — SSN, DOB (minors), financial accounts, minor names",
        "authority": "MCR 1.109(D)(9)",
        "minor_names": True,
        "ssn": True,
        "dob_minors": True,
        "financial": True,
    },
    "enhanced": {
        "description": "Standard + emails, phones, routing numbers",
        "authority": "MCR 1.109(D)(9) + privacy best practices",
        "minor_names": True,
        "ssn": True,
        "dob_minors": True,
        "dob_all": True,
        "financial": True,
        "contact_info": True,
    },
    "sealed": {
        "description": "Maximum redaction — all PII, addresses, DL numbers",
        "authority": "MCR 8.119(H) — confidential filing",
        "minor_names": True,
        "ssn": True,
        "dob_all": True,
        "financial": True,
        "contact_info": True,
        "addresses": True,
        "identifiers": True,
    },
}

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS redaction_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file TEXT,
    pii_type TEXT NOT NULL,
    original_snippet TEXT,
    redacted_snippet TEXT,
    redaction_level TEXT DEFAULT 'standard',
    authority TEXT,
    line_number INTEGER,
    char_offset INTEGER,
    reviewed INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);
"""


# ── Database helpers ────────────────────────────────────────────────────────

def _get_db() -> Optional[sqlite3.Connection]:
    """Connect to litigation_context.db."""
    if not os.path.exists(DB_PATH):
        return None
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_table(conn: sqlite3.Connection) -> None:
    """Create redaction_log table if needed."""
    conn.execute(CREATE_TABLE_SQL)
    conn.commit()


# ── Core redaction functions ────────────────────────────────────────────────

def _redact_ssn(match: re.Match) -> str:
    """SSN → XXX-XX-{last4} per MCR 1.109(D)(9)(a)."""
    last4 = match.group(3)
    return f"XXX-XX-{last4}"


def _redact_dob(match: re.Match) -> str:
    """DOB → XX/XX/{year} per MCR 1.109(D)(9)(b)."""
    year = match.group(3)
    return f"XX/XX/{year}"


def _redact_financial_16(match: re.Match) -> str:
    """16-digit account → XXXX-XXXX-XXXX-{last4} per MCR 1.109(D)(9)(c)."""
    last4 = match.group(4)
    return f"XXXX-XXXX-XXXX-{last4}"


def _redact_bank_account(match: re.Match) -> str:
    """Bank account → last 4 digits."""
    full = match.group(1)
    last4 = full[-4:]
    prefix = "X" * (len(full) - 4)
    return f"Account #{prefix}{last4}"


def _redact_minor_names(text: str) -> Tuple[str, List[Dict]]:
    """Replace minor child names with initials per MCR 3.903(A)(2)."""
    redactions = []
    result = text
    # Sort by length descending so longer names match first
    for name, initials in sorted(MINOR_CHILDREN.items(), key=lambda x: -len(x[0])):
        pattern = re.compile(re.escape(name), re.IGNORECASE)
        for m in pattern.finditer(result):
            needs_review = (name == "Lincoln")  # single first name is ambiguous
            redactions.append({
                "pii_type": "minor_name",
                "original": m.group(),
                "redacted": initials,
                "authority": "MCR 1.109(D)(9); MCR 3.903(A)(2)",
                "offset": m.start(),
                "needs_review": needs_review,
            })
        result = pattern.sub(initials, result)
    return result, redactions


def redact_text(
    text: str,
    redaction_level: str = "standard",
    source_file: str = None,
    log_to_db: bool = True,
) -> Dict:
    """Redact PII from text per MCR 1.109(D)(9).

    Args:
        text: Input text to redact.
        redaction_level: 'standard', 'enhanced', or 'sealed'.
        source_file: Optional source filename for logging.
        log_to_db: Whether to log redactions to DB.

    Returns:
        dict with redacted_text, redaction_count, redactions list, and warnings.
    """
    if redaction_level not in REDACTION_LEVELS:
        return {
            "error": f"Invalid redaction level: {redaction_level}",
            "valid_levels": list(REDACTION_LEVELS.keys()),
        }

    level_config = REDACTION_LEVELS[redaction_level]
    redactions: List[Dict] = []
    result = text
    warnings: List[str] = []

    # 1. Redact minor child names (all levels)
    result, minor_redactions = _redact_minor_names(result)
    redactions.extend(minor_redactions)
    for r in minor_redactions:
        if r.get("needs_review"):
            warnings.append(
                f"⚠ Standalone 'Lincoln' redacted to 'LDW' — verify context"
            )

    # 2. Redact SSNs
    ssn_info = PII_PATTERNS["ssn_full"]
    if redaction_level in ssn_info["levels"]:
        for m in ssn_info["pattern"].finditer(result):
            redactions.append({
                "pii_type": "ssn",
                "original": m.group(),
                "redacted": _redact_ssn(m),
                "authority": ssn_info["authority"],
                "offset": m.start(),
            })
        result = ssn_info["pattern"].sub(_redact_ssn, result)

    # 3. Redact DOBs
    for key in ("dob_full", "dob_written"):
        dob_info = PII_PATTERNS[key]
        if redaction_level in dob_info["levels"]:
            if key == "dob_full":
                for m in dob_info["pattern"].finditer(result):
                    redactions.append({
                        "pii_type": "dob",
                        "original": m.group(),
                        "redacted": _redact_dob(m),
                        "authority": dob_info["authority"],
                        "offset": m.start(),
                    })
                result = dob_info["pattern"].sub(_redact_dob, result)
            else:
                for m in dob_info["pattern"].finditer(result):
                    redacted = "[DOB REDACTED]"
                    redactions.append({
                        "pii_type": "dob_written",
                        "original": m.group(),
                        "redacted": redacted,
                        "authority": dob_info["authority"],
                        "offset": m.start(),
                    })
                result = dob_info["pattern"].sub("[DOB REDACTED]", result)

    # 4. Redact financial accounts
    fin_info = PII_PATTERNS["financial_account"]
    if redaction_level in fin_info["levels"]:
        for m in fin_info["pattern"].finditer(result):
            redactions.append({
                "pii_type": "financial_account",
                "original": m.group(),
                "redacted": _redact_financial_16(m),
                "authority": fin_info["authority"],
                "offset": m.start(),
            })
        result = fin_info["pattern"].sub(_redact_financial_16, result)

    bank_info = PII_PATTERNS["bank_account"]
    if redaction_level in bank_info["levels"]:
        for m in bank_info["pattern"].finditer(result):
            redactions.append({
                "pii_type": "bank_account",
                "original": m.group(),
                "redacted": _redact_bank_account(m),
                "authority": bank_info["authority"],
                "offset": m.start(),
            })
        result = bank_info["pattern"].sub(_redact_bank_account, result)

    # 5. Enhanced-level: routing numbers, email, phone
    for key in ("routing_number", "email", "phone"):
        info = PII_PATTERNS[key]
        if redaction_level in info["levels"]:
            tag = f"[{key.upper()} REDACTED]"
            for m in info["pattern"].finditer(result):
                redactions.append({
                    "pii_type": key,
                    "original": m.group(),
                    "redacted": tag,
                    "authority": info["authority"],
                    "offset": m.start(),
                })
            result = info["pattern"].sub(tag, result)

    # 6. Sealed-level: DL, addresses
    for key in ("drivers_license", "street_address"):
        info = PII_PATTERNS[key]
        if redaction_level in info["levels"]:
            tag = f"[{key.upper()} REDACTED]"
            for m in info["pattern"].finditer(result):
                redactions.append({
                    "pii_type": key,
                    "original": m.group(),
                    "redacted": tag,
                    "authority": info["authority"],
                    "offset": m.start(),
                })
            result = info["pattern"].sub(tag, result)

    # Log to DB
    db_logged = 0
    if log_to_db and redactions:
        conn = _get_db()
        if conn:
            try:
                _ensure_table(conn)
                for r in redactions:
                    conn.execute(
                        """INSERT INTO redaction_log
                           (source_file, pii_type, original_snippet,
                            redacted_snippet, redaction_level, authority, char_offset)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (
                            source_file, r["pii_type"],
                            r["original"][:100], r["redacted"][:100],
                            redaction_level, r.get("authority", ""),
                            r.get("offset", 0),
                        ),
                    )
                conn.commit()
                db_logged = len(redactions)
            except Exception as e:
                warnings.append(f"DB logging failed: {e}")
            finally:
                conn.close()

    return {
        "redacted_text": result,
        "redaction_count": len(redactions),
        "redactions": redactions,
        "redaction_level": redaction_level,
        "level_description": level_config["description"],
        "authority": level_config["authority"],
        "db_logged": db_logged,
        "warnings": warnings,
    }


def redact_file(filepath: str, redaction_level: str = "standard") -> Dict:
    """Redact PII from a file. Writes redacted version alongside original.

    Args:
        filepath: Path to the file to redact.
        redaction_level: Redaction level to apply.

    Returns:
        dict with output_path, stats, and any warnings.
    """
    if not os.path.exists(filepath):
        return {"error": f"File not found: {filepath}"}

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
    except UnicodeDecodeError:
        try:
            with open(filepath, "r", encoding="latin-1") as f:
                text = f.read()
        except Exception as e:
            return {"error": f"Cannot read file: {e}"}

    result = redact_text(
        text,
        redaction_level=redaction_level,
        source_file=os.path.basename(filepath),
        log_to_db=True,
    )

    if "error" in result:
        return result

    # Write redacted version
    base, ext = os.path.splitext(filepath)
    output_path = f"{base}_REDACTED{ext}"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result["redacted_text"])

    return {
        "input_file": filepath,
        "output_file": output_path,
        "redaction_count": result["redaction_count"],
        "redaction_level": redaction_level,
        "redactions": result["redactions"],
        "warnings": result["warnings"],
        "authority": "MCR 1.109(D)(9)",
    }


def check_pii_exposure(text: str) -> Dict:
    """Scan text for PII without redacting. Returns exposure report.

    Args:
        text: Text to scan.

    Returns:
        dict with found PII items, risk_level, and recommendations.
    """
    exposures: List[Dict] = []

    # Check all PII patterns
    for key, info in PII_PATTERNS.items():
        for m in info["pattern"].finditer(text):
            exposures.append({
                "type": key,
                "description": info["description"],
                "match": m.group()[:30] + ("..." if len(m.group()) > 30 else ""),
                "position": m.start(),
                "authority": info["authority"],
                "min_redaction_level": info["levels"][0],
            })

    # Check for minor child names
    for name in MINOR_CHILDREN:
        pattern = re.compile(re.escape(name), re.IGNORECASE)
        for m in pattern.finditer(text):
            exposures.append({
                "type": "minor_name",
                "description": f"Minor child name: {name}",
                "match": m.group(),
                "position": m.start(),
                "authority": "MCR 1.109(D)(9); MCR 3.903(A)(2)",
                "min_redaction_level": "standard",
            })

    # Determine risk level
    if not exposures:
        risk = "LOW"
        recommendation = "No PII detected. Safe for public filing."
    elif any(e["type"] in ("ssn_full", "financial_account") for e in exposures):
        risk = "CRITICAL"
        recommendation = (
            "CRITICAL PII exposure (SSN/financial). "
            "MUST redact before filing per MCR 1.109(D)(9)."
        )
    elif any(e["type"] == "minor_name" for e in exposures):
        risk = "HIGH"
        recommendation = (
            "Minor child name exposed. Redact to initials "
            "per MCR 1.109(D)(9) and MCR 3.903(A)(2)."
        )
    else:
        risk = "MODERATE"
        recommendation = "PII detected. Apply appropriate redaction level."

    return {
        "exposure_count": len(exposures),
        "exposures": exposures,
        "risk_level": risk,
        "recommendation": recommendation,
        "authority": "MCR 1.109(D)(9)",
    }


def generate_redaction_log(source_file: str = None, limit: int = 100) -> Dict:
    """Retrieve redaction log entries from DB.

    Args:
        source_file: Optional filter by source file.
        limit: Max entries to return.

    Returns:
        dict with log entries and summary statistics.
    """
    conn = _get_db()
    if conn is None:
        return {"error": "Database not available", "entries": []}

    try:
        _ensure_table(conn)
        if source_file:
            rows = conn.execute(
                "SELECT * FROM redaction_log WHERE source_file = ? "
                "ORDER BY created_at DESC LIMIT ?",
                (source_file, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM redaction_log ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()

        entries = [dict(r) for r in rows]

        # Summary stats
        stats = conn.execute(
            "SELECT pii_type, COUNT(*) as cnt FROM redaction_log "
            "GROUP BY pii_type ORDER BY cnt DESC"
        ).fetchall()

        total = conn.execute(
            "SELECT COUNT(*) FROM redaction_log"
        ).fetchone()[0]

        return {
            "entries": entries,
            "total_redactions": total,
            "by_type": {r["pii_type"]: r["cnt"] for r in stats},
            "entry_count": len(entries),
        }
    except Exception as e:
        return {"error": str(e), "entries": []}
    finally:
        conn.close()


# ── CLI ─────────────────────────────────────────────────────────────────────

def main() -> int:
    """CLI entry point for testing."""
    print("=" * 60)
    print("ENGINE 13: REDACTION ENGINE — MCR 1.109(D)(9)")
    print("PII Redaction for Michigan Court Filings")
    print("=" * 60)

    # Test text with various PII
    test_text = (
        "Plaintiff Andrew Pigors, SSN 123-45-6789, resides at "
        "456 Main Street, Muskegon, MI 49441. His son Lincoln D. Watson, "
        "born on 06/15/2019, has been separated from his father for 567 days. "
        "Defendant Tiffany Watson, account 4111-2222-3333-4444, "
        "phone (231) 555-0199, email tiffany@example.com. "
        "Routing #072000326. Account #9876543210."
    )

    print("\n--- Original Text ---")
    print(f"  {test_text[:120]}...")

    # Test standard redaction
    print("\n--- Standard Redaction (MCR minimum) ---")
    result = redact_text(test_text, "standard", log_to_db=False)
    if "error" in result:
        print(f"  ERROR: {result['error']}")
        return 1
    print(f"  Redacted: {result['redacted_text'][:120]}...")
    print(f"  Count: {result['redaction_count']} redactions")
    for r in result["redactions"]:
        print(f"    [{r['pii_type']}] {r['original'][:30]} → {r['redacted'][:30]}")

    # Test enhanced redaction
    print("\n--- Enhanced Redaction ---")
    result_enh = redact_text(test_text, "enhanced", log_to_db=False)
    print(f"  Count: {result_enh['redaction_count']} redactions")
    extra = result_enh["redaction_count"] - result["redaction_count"]
    print(f"  Additional vs standard: {extra}")

    # Test sealed redaction
    print("\n--- Sealed Redaction ---")
    result_sealed = redact_text(test_text, "sealed", log_to_db=False)
    print(f"  Count: {result_sealed['redaction_count']} redactions")
    print(f"  Text: {result_sealed['redacted_text'][:120]}...")

    # Test PII exposure check
    print("\n--- PII Exposure Check ---")
    exposure = check_pii_exposure(test_text)
    print(f"  Risk level: {exposure['risk_level']}")
    print(f"  Exposures found: {exposure['exposure_count']}")
    print(f"  Recommendation: {exposure['recommendation']}")

    # Test clean text
    print("\n--- Clean Text Check ---")
    clean = "This is a filing with no PII content whatsoever."
    clean_check = check_pii_exposure(clean)
    print(f"  Risk level: {clean_check['risk_level']}")
    assert clean_check["risk_level"] == "LOW", "Clean text should be LOW risk"
    assert clean_check["exposure_count"] == 0, "Clean text should have 0 exposures"

    # Verify minor name redaction
    print("\n--- Minor Name Redaction ---")
    minor_text = "Lincoln D. Watson visited the park with Lincoln."
    minor_result = redact_text(minor_text, "standard", log_to_db=False)
    print(f"  Before: {minor_text}")
    print(f"  After:  {minor_result['redacted_text']}")
    assert "Lincoln" not in minor_result["redacted_text"], "Minor name should be redacted"
    assert "LDW" in minor_result["redacted_text"], "Should use initials"

    # Verify SSN redaction keeps last 4
    print("\n--- SSN Redaction Verify ---")
    ssn_text = "SSN: 123-45-6789"
    ssn_result = redact_text(ssn_text, "standard", log_to_db=False)
    print(f"  Before: {ssn_text}")
    print(f"  After:  {ssn_result['redacted_text']}")
    assert "6789" in ssn_result["redacted_text"], "SSN last 4 should be preserved"
    assert "123-45" not in ssn_result["redacted_text"], "SSN first digits should be redacted"

    # Verify party names are NOT redacted
    print("\n--- Party Name Preservation ---")
    assert "Andrew Pigors" in result["redacted_text"], "Party names must not be redacted"

    # Test redaction log
    print("\n--- Redaction Log (DB) ---")
    log = generate_redaction_log()
    if "error" in log and "not available" not in log.get("error", ""):
        print(f"  Log error: {log['error']}")
    else:
        print(f"  Total log entries: {log.get('total_redactions', 'N/A')}")

    print(f"\n  Redaction levels available:")
    for level, config in REDACTION_LEVELS.items():
        print(f"    {level}: {config['description']}")

    print("\n[redaction_engine] All tests passed. ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
