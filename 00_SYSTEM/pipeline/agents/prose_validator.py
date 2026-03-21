"""
Pro Se Compliance Validator (G01)
=================================

Governance-tier agent that validates court filings against Michigan
pro se filing requirements.  Catches the formatting, caption, signature,
and service-proof errors that cause clerks to reject filings.

Compliance dimensions checked per document:
  1. Caption — court name, case number, verified party names
  2. Signature block — "Respectfully submitted", contact info
  3. Proof of service — certificate of service present & complete
  4. Page formatting — margins, font size, spacing (MCR 2.113)
  5. Filing requirements — signing (MCR 2.107), verification (MCR 2.114)
  6. Common rejections — missing case number, wrong court, no service proof
  7. Anti-hallucination — guard_output() on every generated string
  8. Lane detection — detect_lane() classifies each filing's case lane

Agent contract
--------------
    class ProSeValidator(Agent9999):
        AGENT_ID  = "G01"
        AGENT_NAME = "Pro Se Compliance Validator"
        TIER       = "G"   # Governance tier

        run() -> AgentResult
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .agent_base import Agent9999
from .agent_models import (
    AgentResult,
    AgentStats,
    FatalAgentError,
    SkipItemError,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

AGENT_ID = "G01-PROSE-VALIDATOR"
AGENT_NAME = "Pro Se Compliance Validator"
TIER = "G"

# Michigan Court Rule references used in validation messages
_MCR_CAPTION = "MCR 2.113(C)(1)"
_MCR_SIGNING = "MCR 2.107(A)"
_MCR_VERIFICATION = "MCR 2.114"
_MCR_SERVICE = "MCR 2.107(C)"
_MCR_FORMAT = "MCR 2.113(C)(1)"

# Known case numbers for this litigation
_KNOWN_CASE_NUMBERS = {
    "2024-001507-DC",
    "2023-5907-PP",
    "2025-002760-CZ",
}

# Formatting thresholds (MCR 2.113 defaults)
_MIN_MARGIN_INCHES = 1.0
_ACCEPTED_FONTS = {"times new roman", "arial", "courier new"}
_MIN_FONT_SIZE = 12
_MAX_FONT_SIZE = 14
_ACCEPTED_SPACING = {"double", "1.5"}
_DEFAULT_PAGE_LIMIT = 50  # motions; briefs may differ

# Filing extensions we scan
_FILING_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".md"}

# Regex helpers
_CASE_NUMBER_RE = re.compile(
    r"\b\d{4}-\d{4,6}-(?:DC|PP|CZ|DM|DO|FC|FH)\b", re.IGNORECASE
)
_COURT_NAME_RE = re.compile(
    r"(?i)(?:14th|fourteenth)\s+(?:judicial\s+)?circuit\s+court", re.IGNORECASE
)
_COUNTY_RE = re.compile(r"(?i)muskegon\s+county")
_SIGNATURE_RE = re.compile(
    r"(?i)respectfully\s+submitted", re.IGNORECASE
)
_SERVICE_CERT_RE = re.compile(
    r"(?i)certificate\s+of\s+service|proof\s+of\s+service", re.IGNORECASE
)
_SERVICE_METHOD_RE = re.compile(
    r"(?i)(?:first[- ]class\s+mail|personal\s+(?:delivery|service)|e-?(?:file|serve|mail)|hand[- ]deliver)",
    re.IGNORECASE,
)
_VERIFICATION_RE = re.compile(
    r"(?i)(?:under\s+(?:the\s+)?penalties?\s+of\s+perjury|sworn\s+and\s+subscribed|state\s+of\s+michigan.*county\s+of)",
    re.IGNORECASE,
)
_ADDRESS_RE = re.compile(r"\d{1,5}\s+\w+.*(?:road|rd|street|st|drive|dr|avenue|ave|lot)\b", re.IGNORECASE)
_PHONE_RE = re.compile(r"\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}")
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class ProSeValidator(Agent9999):
    """Governance-tier agent that validates filings for Michigan
    pro se compliance.  Writes results to ``prose_compliance`` in
    the agent master-index DB."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(agent_id=AGENT_ID, **kwargs)
        self.checkpoint_interval = 100
        self.item_timeout = 30
        self._results: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def _ensure_tables(self) -> None:
        """Create the prose_compliance results table if absent."""
        self._db_execute("""
            CREATE TABLE IF NOT EXISTS prose_compliance (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                document_path   TEXT,
                filing_type     TEXT,
                lane            TEXT,
                caption_ok      INTEGER,
                signature_ok    INTEGER,
                service_ok      INTEGER,
                formatting_ok   INTEGER,
                overall_score   REAL,
                issues_json     TEXT,
                checked_at      TEXT DEFAULT (datetime('now'))
            )
        """)
        self._db_execute("""
            CREATE INDEX IF NOT EXISTS idx_prose_compliance_path
                ON prose_compliance(document_path)
        """)
        self.db.commit()

    # ------------------------------------------------------------------
    # Preconditions
    # ------------------------------------------------------------------

    def _validate_preconditions(self) -> None:
        """Verify we have filings to check — either in central DB or on disk."""
        central = self._get_central_db()
        if central:
            try:
                row = central.execute(
                    "SELECT COUNT(*) AS cnt FROM documents"
                ).fetchone()
                if row and (row["cnt"] if isinstance(row, sqlite3.Row) else row[0]) > 0:
                    self._log("INFO", f"Central DB has filings to validate")
                    return
            except Exception:
                pass

        # Fallback: look for filing files on disk
        filing_dirs = [
            Path(r"C:\Users\andre\LitigationOS\Vault\50_FILINGS"),
            Path(r"C:\Users\andre\LitigationOS\Vault\60_COURT_PACKETS"),
        ]
        for d in filing_dirs:
            if d.is_dir() and any(d.rglob("*")):
                self._log("INFO", f"Found filing directory: {d}")
                return

        self._log("WARN", "No filings found in central DB or filesystem — will run with empty set")

    # ------------------------------------------------------------------
    # Work-item collection
    # ------------------------------------------------------------------

    def _get_work_items(self) -> list:
        """Collect filing documents from central DB, then supplement with
        filesystem scan for files not yet in the DB."""
        items: List[Dict[str, Any]] = []
        seen_paths: set = set()

        # --- Source 1: central litigation_context.db ---
        central = self._get_central_db()
        if central:
            try:
                cursor = central.execute("""
                    SELECT document_path, filing_type
                    FROM documents
                    WHERE document_path IS NOT NULL
                    ORDER BY rowid DESC
                    LIMIT 5000
                """)
                for row in cursor.fetchall():
                    path = row["document_path"] if isinstance(row, sqlite3.Row) else row[0]
                    ftype = (row["filing_type"] if isinstance(row, sqlite3.Row) else row[1]) or "unknown"
                    if path and path not in seen_paths:
                        seen_paths.add(path)
                        items.append({"path": path, "filing_type": ftype, "source": "db"})
            except Exception as exc:
                self._log("WARN", f"Central DB query failed: {exc}")

        # --- Source 2: filesystem fallback ---
        filing_dirs = [
            Path(r"C:\Users\andre\LitigationOS\Vault\50_FILINGS"),
            Path(r"C:\Users\andre\LitigationOS\Vault\60_COURT_PACKETS"),
        ]
        for d in filing_dirs:
            if not d.is_dir():
                continue
            for fp in d.rglob("*"):
                if fp.suffix.lower() in _FILING_EXTENSIONS and str(fp) not in seen_paths:
                    seen_paths.add(str(fp))
                    items.append({
                        "path": str(fp),
                        "filing_type": self._infer_filing_type(fp.name),
                        "source": "filesystem",
                    })

        self._log("INFO", f"Collected {len(items)} filing documents to validate")
        self.stats.total = len(items)
        return items

    # ------------------------------------------------------------------
    # Per-item processing
    # ------------------------------------------------------------------

    def _process_item(self, item: Any) -> None:
        """Run all compliance checks against a single filing document."""
        doc_path: str = item["path"]
        filing_type: str = item.get("filing_type", "unknown")

        content = self._read_content(doc_path)
        if not content:
            raise SkipItemError(f"No readable content: {doc_path}")

        # Lane detection (v3.0 feature)
        lane = self.detect_lane(content)

        # Run each compliance dimension
        caption_issues = self._check_caption(content)
        signature_issues = self._check_signature_block(content)
        service_issues = self._check_proof_of_service(content)
        formatting_issues = self._check_formatting(content)
        filing_req_issues = self._check_filing_requirements(content)
        rejection_issues = self._check_common_rejections(content, lane)

        all_issues: List[str] = (
            caption_issues + signature_issues + service_issues
            + formatting_issues + filing_req_issues + rejection_issues
        )

        # Anti-hallucination gate on collected issues
        all_issues = [self.guard_output(i) for i in all_issues]

        caption_ok = int(len(caption_issues) == 0)
        signature_ok = int(len(signature_issues) == 0)
        service_ok = int(len(service_issues) == 0)
        formatting_ok = int(len(formatting_issues) == 0)

        # Overall score: 100 minus penalty per issue (floor at 0)
        penalty_per_issue = 8
        overall_score = max(0.0, 100.0 - len(all_issues) * penalty_per_issue)

        issues_json = json.dumps(all_issues, ensure_ascii=False)

        # Persist to agent DB
        self._db_execute(
            """INSERT INTO prose_compliance
               (document_path, filing_type, lane,
                caption_ok, signature_ok, service_ok, formatting_ok,
                overall_score, issues_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                doc_path, filing_type, lane,
                caption_ok, signature_ok, service_ok, formatting_ok,
                overall_score, issues_json,
            ),
        )
        self.db.commit()

        self._results.append({
            "path": doc_path,
            "lane": lane,
            "score": overall_score,
            "issues": len(all_issues),
        })

        level = "WARN" if overall_score < 70 else "INFO"
        self._log(level, f"score={overall_score:.0f} issues={len(all_issues)} lane={lane} | {Path(doc_path).name}")

    # ------------------------------------------------------------------
    # Compliance check methods
    # ------------------------------------------------------------------

    def _check_caption(self, text: str) -> List[str]:
        """Validate caption block: court name, county, case number, party names."""
        issues: List[str] = []

        if not _COURT_NAME_RE.search(text):
            issues.append(f"[{_MCR_CAPTION}] Missing or incorrect court name — must reference 14th Circuit Court")

        if not _COUNTY_RE.search(text):
            issues.append(f"[{_MCR_CAPTION}] Missing 'Muskegon County' in caption")

        case_nums = _CASE_NUMBER_RE.findall(text)
        if not case_nums:
            issues.append(f"[{_MCR_CAPTION}] No case number found in filing")

        # Verify party names are the canonical verified names
        plaintiff = self.get_verified_party("plaintiff")
        defendant = self.get_verified_party("defendant")
        text_upper = text.upper()
        if plaintiff.upper() not in text_upper and "PIGORS" not in text_upper:
            issues.append(f"[{_MCR_CAPTION}] Plaintiff name '{plaintiff}' not found in caption")
        if defendant.upper() not in text_upper and "WATSON" not in text_upper:
            issues.append(f"[{_MCR_CAPTION}] Defendant name '{defendant}' not found in caption")

        return issues

    def _check_signature_block(self, text: str) -> List[str]:
        """Validate signature block: 'Respectfully submitted', name, address, phone, email."""
        issues: List[str] = []

        if not _SIGNATURE_RE.search(text):
            issues.append(f"[{_MCR_SIGNING}] Missing 'Respectfully submitted' closing")

        plaintiff = self.get_verified_party("plaintiff")
        if plaintiff.upper() not in text.upper():
            issues.append(f"[{_MCR_SIGNING}] Signature block missing filer name '{plaintiff}'")

        if not _ADDRESS_RE.search(text):
            issues.append(f"[{_MCR_SIGNING}] Signature block missing street address")

        if not _PHONE_RE.search(text):
            issues.append(f"[{_MCR_SIGNING}] Signature block missing phone number")

        if not _EMAIL_RE.search(text):
            issues.append(f"[{_MCR_SIGNING}] Signature block missing email address")

        return issues

    def _check_proof_of_service(self, text: str) -> List[str]:
        """Validate certificate / proof of service is present and complete."""
        issues: List[str] = []

        if not _SERVICE_CERT_RE.search(text):
            issues.append(f"[{_MCR_SERVICE}] No Certificate/Proof of Service found")
            return issues  # remaining checks pointless without the section

        if not _SERVICE_METHOD_RE.search(text):
            issues.append(f"[{_MCR_SERVICE}] Service method not specified (mail, e-file, hand delivery)")

        # Check that opposing party / attorney is named in service section
        defendant_atty = self.get_verified_party("defendant_attorney")
        service_section = self._extract_service_section(text)
        if service_section:
            svc_upper = service_section.upper()
            if "BARNES" not in svc_upper and "WATSON" not in svc_upper:
                issues.append(
                    f"[{_MCR_SERVICE}] Service recipient not identified — "
                    f"expected '{defendant_atty}' or defendant"
                )

        return issues

    def _check_formatting(self, text: str) -> List[str]:
        """Heuristic formatting checks based on MCR 2.113 requirements.

        Full formatting validation requires the source document metadata
        (margins, font, spacing).  For plain-text content we apply
        best-effort heuristics.
        """
        issues: List[str] = []

        lines = text.splitlines()

        # Page-count heuristic (~250 words/page, ~45 lines/page)
        estimated_pages = max(1, len(lines) // 45)
        if estimated_pages > _DEFAULT_PAGE_LIMIT:
            issues.append(
                f"[{_MCR_FORMAT}] Estimated {estimated_pages} pages — "
                f"exceeds typical {_DEFAULT_PAGE_LIMIT}-page limit"
            )

        # Line-length check: lines > 90 chars suggest < 1″ margins
        long_lines = sum(1 for ln in lines if len(ln.rstrip()) > 90)
        if lines and long_lines / max(len(lines), 1) > 0.25:
            issues.append(
                f"[{_MCR_FORMAT}] {long_lines} lines exceed 90 chars — "
                f"possible margin violation (minimum 1\" margins required)"
            )

        return issues

    def _check_filing_requirements(self, text: str) -> List[str]:
        """Check MCR 2.107 signing & MCR 2.114 verification requirements."""
        issues: List[str] = []

        # MCR 2.107: filing must be signed
        sign_patterns = [
            re.compile(r"(?i)/s/\s*\w+"),                # electronic signature
            re.compile(r"(?i)_{3,}\s*\n.*(?:pigors|plaintiff)", re.DOTALL),  # signature line
            re.compile(r"(?i)signed.*andrew", re.DOTALL),
        ]
        has_signature = any(p.search(text) for p in sign_patterns)
        if not has_signature and _SIGNATURE_RE.search(text):
            # Has "Respectfully submitted" but no actual signature indicator
            issues.append(
                f"[{_MCR_SIGNING}] Filing appears unsigned — "
                f"add '/s/ Andrew James Pigors' or physical signature line"
            )

        # MCR 2.114: verification statement (for verified complaints, affidavits)
        text_lower = text.lower()
        needs_verification = any(
            kw in text_lower
            for kw in ("verified complaint", "affidavit", "sworn statement", "verified motion")
        )
        if needs_verification and not _VERIFICATION_RE.search(text):
            issues.append(
                f"[{_MCR_VERIFICATION}] Document type requires verification statement "
                f"(oath/penalties of perjury) but none found"
            )

        return issues

    def _check_common_rejections(self, text: str, lane: str) -> List[str]:
        """Flag patterns that commonly cause clerk rejection of pro se filings."""
        issues: List[str] = []

        # Missing date
        date_re = re.compile(r"(?i)date[d:]?\s*[_\s]*(?:\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}|\w+\s+\d{1,2},?\s+\d{4})")
        if not date_re.search(text):
            issues.append("Missing date on filing — clerks may reject undated documents")

        # "Judge" addressed incorrectly
        if re.search(r"(?i)\bdear\s+judge\b", text):
            issues.append("Do not address the court with 'Dear Judge' — use 'TO THE HONORABLE COURT'")

        # Hallucination guard: check for known-bad names
        hallucinated = {"jane berry", "patricia berry", "tiffany watson", "amy mcneill", "emily ann watson"}
        text_lower = text.lower()
        for bad_name in hallucinated:
            if bad_name in text_lower:
                issues.append(
                    f"HALLUCINATION DETECTED: '{bad_name}' is a known fabricated name — "
                    f"purge immediately"
                )

        # Wrong court check
        wrong_courts = [
            re.compile(r"(?i)(?:61st|60th|27th|3rd)\s+(?:district|circuit)\s+court"),
        ]
        for wc in wrong_courts:
            if wc.search(text):
                issues.append("Filing references wrong court — must be 14th Circuit Court, Muskegon County")

        return issues

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _read_content(self, doc_path: str) -> Optional[str]:
        """Read text content from a filing document.

        Tries the agent base ``_read_file_content()`` first (handles PDF/DOCX
        extraction and the extracted_text cache).  Falls back to direct
        UTF-8 read for plain text files.
        """
        # Try base-class helper (works for indexed files with file_id)
        try:
            long = self.long_path(doc_path)
            if os.path.isfile(long):
                ext = os.path.splitext(long)[1].lower()
                if ext in (".txt", ".md"):
                    with open(long, "r", encoding="utf-8", errors="replace") as fh:
                        return fh.read()
                # For PDF / DOCX fall back to base-class extraction if available
                try:
                    content = self._read_file_content_from_path(long)
                    if content:
                        return content
                except Exception:
                    pass
                # Last-resort: try reading as text anyway
                with open(long, "r", encoding="utf-8", errors="replace") as fh:
                    return fh.read()
        except Exception as exc:
            self._log("WARN", f"Read failed for {doc_path}: {exc}")
        return None

    def _read_file_content_from_path(self, path: str) -> Optional[str]:
        """Extract text from PDF or DOCX if libraries available."""
        ext = os.path.splitext(path)[1].lower()
        if ext == ".pdf":
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(path)
                text_parts = [page.get_text() for page in doc]
                doc.close()
                return "\n".join(text_parts)
            except ImportError:
                pass
        elif ext in (".docx",):
            try:
                import docx
                doc = docx.Document(path)
                return "\n".join(p.text for p in doc.paragraphs)
            except ImportError:
                pass
        return None

    @staticmethod
    def _extract_service_section(text: str) -> Optional[str]:
        """Pull the proof-of-service section out of the full document text."""
        match = re.search(
            r"(?i)(certificate\s+of\s+service|proof\s+of\s+service)(.*)",
            text,
            re.DOTALL,
        )
        if match:
            # Grab up to ~2000 chars after header (service sections are short)
            return match.group(0)[:2000]
        return None

    @staticmethod
    def _infer_filing_type(filename: str) -> str:
        """Best-effort filing-type classification from file name."""
        name_lower = filename.lower()
        mapping = [
            ("motion", "motion"),
            ("brief", "brief"),
            ("petition", "petition"),
            ("response", "response"),
            ("reply", "reply"),
            ("affidavit", "affidavit"),
            ("complaint", "complaint"),
            ("order", "order"),
            ("notice", "notice"),
            ("exhibit", "exhibit"),
            ("proof_of_service", "proof_of_service"),
            ("certificate", "certificate"),
        ]
        for keyword, ftype in mapping:
            if keyword in name_lower:
                return ftype
        return "unknown"

    # ------------------------------------------------------------------
    # Finalize
    # ------------------------------------------------------------------

    def _finalize(self) -> None:
        """Summarise validation run and emit health report."""
        total = len(self._results)
        if total == 0:
            self._log("DONE", "No filings were validated in this run")
            return

        avg_score = sum(r["score"] for r in self._results) / total
        failing = sum(1 for r in self._results if r["score"] < 70)
        perfect = sum(1 for r in self._results if r["score"] == 100)

        self._log(
            "DONE",
            f"Validated {total} filings | avg_score={avg_score:.1f} | "
            f"passing={total - failing} failing={failing} perfect={perfect}",
        )

        # Store summary as agent memory for cross-recall
        self.remember(
            key="last_run_summary",
            value=json.dumps({
                "total": total,
                "avg_score": round(avg_score, 2),
                "failing": failing,
                "perfect": perfect,
                "timestamp": datetime.utcnow().isoformat(),
            }),
            category="compliance",
            confidence=1.0,
        )


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    print(f"=== {AGENT_NAME} ({AGENT_ID}) — Tier {TIER} ===")
    print(f"Starting at {datetime.now().isoformat()}")

    agent = ProSeValidator()
    result = agent.run()

    print(f"\n{'='*60}")
    print(f"Result: {result}")
    if result.error:
        print(f"Error:  {result.error}")
    print(f"{'='*60}")

    sys.exit(0 if result.status == "SUCCESS" else 1)
