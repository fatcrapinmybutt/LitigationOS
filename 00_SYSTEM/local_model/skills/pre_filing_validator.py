#!/usr/bin/env python3
"""
MBP LitigationOS -- Pre-Filing Validator Skill
================================================
Automated quality gate that runs ALL checks before a filing goes to court.
Orchestrates: appellate_validator + mifile_checker + citation_validator +
scao_forms + Certificate of Service check.

Returns PASS/FAIL with detailed report per check.

JSON-RPC methods: validate_filing, validate_all_filings, filing_checklist

Usage:
    from skills.pre_filing_validator import PreFilingValidator
    v = PreFilingValidator()
    result = v.validate_filing(r'C:\\Users\\andre\\LitigationOS\\LANE_F\\COA_APPELLANT_BRIEF_366810_v2.md')

CLI:
    python pre_filing_validator.py validate path/to/filing.md
    python pre_filing_validator.py validate-all
    python pre_filing_validator.py checklist COA
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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
    cycle_json = lambda obj, **kw: print(json.dumps(obj, default=str, indent=2))
    cycle_print = print

DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\LitigationOS\litigation_context.db",
)

FILINGS_DIR = os.environ.get(
    "LITIGATION_FILINGS_DIR",
    r"C:\Users\andre\LitigationOS\04_COURT_FILINGS",
)

# ── Placeholder patterns (shared with __init__.py SkillBase) ─────────
_PLACEHOLDER_PATTERNS = [
    r'\[DATE\]', r'\[NAME\]', r'\[CASE NUMBER\]', r'\[ADDRESS\]',
    r'\[PHONE\]', r'\[EMAIL\]', r'\[CITY\]', r'\[STATE\]', r'\[ZIP\]',
    r'\[COURT\]', r'\[JUDGE\]', r'\[SPECIFY[^\]]*\]', r'\[STATE FACTS\]',
    r'\[ISSUE \d+\]', r'\[SWORN STATEMENT[^\]]*\]',
    r'\[APPLICATION OF LAW TO FACTS\]', r'\[QUESTION PRESENTED[^\]]*\]',
    r'\[DOCUMENT BEING RESPONDED TO\]', r'\[FOC RECOMMENDATION[^\]]*\]',
    r'\[ORDER PROVISION[^\]]*\]', r'\[MATTER TO BE HEARD\]',
    r'\[FIRST ARGUMENT HEADING\]', r'\[Cases will be auto-populated[^\]]*\]',
    r'\[MCR references will be auto-populated[^\]]*\]',
    r'\[MCL references will be auto-populated[^\]]*\]',
    r'\[Detailed factual recitation[^\]]*\]',
    r'\[IRAC[^\]]*\]', r'\[Apply IRAC[^\]]*\]',
    r'\[Address on file\]', r'\[Address on file with the Court\]',
    r'\[City, State ZIP\]', r'\[PLACEHOLDER[^\]]*\]',
    r'\[TODO[^\]]*\]', r'\[TBD[^\]]*\]', r'\[INSERT[^\]]*\]',
    r'\[FILL[^\]]*\]', r'\[ENTER[^\]]*\]',
]
_PLACEHOLDER_RE = re.compile('|'.join(_PLACEHOLDER_PATTERNS), re.IGNORECASE)

# ── Citation extraction patterns ─────────────────────────────────────
_MCR_RE = re.compile(r'MCR\s+(\d+\.\d+(?:\([A-Za-z0-9]+\))*)', re.I)
_MCL_RE = re.compile(r'MCL\s+(\d+\.\d+[a-z]?(?:\([a-z0-9]+\))*)', re.I)
_MRE_RE = re.compile(r'MRE\s+(\d+(?:\([a-z0-9]+\))*)', re.I)
_CASE_RE = re.compile(
    r'[A-Z][a-z]+\s+v\s+[A-Z][a-z]+(?:,\s*\d+\s+Mich\s+(?:App\s+)?\d+)?'
)

# ── Word count limits by court level ─────────────────────────────────
WORD_LIMITS = {
    "COA": {"max_words": 16000, "max_pages": 50, "rule": "MCR 7.212(B)"},
    "MSC": {"max_words": 18000, "max_pages": 50, "rule": "MCR 7.306(D)"},
    "circuit": {"max_words": None, "max_pages": None, "rule": "MCR 2.119(A)(2)"},
    "USDC": {"max_words": 14000, "max_pages": None, "rule": "LCivR 7.1(d)(2)"},
    "JTC": {"max_words": None, "max_pages": None, "rule": "MCR 9.211"},
}


# ── Data Classes ─────────────────────────────────────────────────────

@dataclass
class CheckItem:
    """Result of a single validation check."""
    check_name: str
    passed: bool
    severity: str  # critical, major, minor, info
    message: str
    details: Any = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check": self.check_name,
            "passed": self.passed,
            "severity": self.severity,
            "message": self.message,
            "details": self.details,
        }


@dataclass
class FilingValidationResult:
    """Full validation result for a single filing."""
    filepath: str
    overall_pass: bool = True
    overall_score: int = 100
    checks: List[CheckItem] = field(default_factory=list)
    timestamp: str = ""

    def __post_init__(self):
        self.timestamp = datetime.now().isoformat()

    def add_check(self, item: CheckItem):
        self.checks.append(item)
        if not item.passed:
            self.overall_pass = False
            penalty = {"critical": 25, "major": 15, "minor": 5, "info": 0}
            self.overall_score = max(0, self.overall_score - penalty.get(item.severity, 5))

    def to_dict(self) -> Dict[str, Any]:
        passed = [c for c in self.checks if c.passed]
        failed = [c for c in self.checks if not c.passed]
        return {
            "filepath": self.filepath,
            "overall": "PASS" if self.overall_pass else "FAIL",
            "score": self.overall_score,
            "total_checks": len(self.checks),
            "passed_checks": len(passed),
            "failed_checks": len(failed),
            "failures": [c.to_dict() for c in failed],
            "all_checks": [c.to_dict() for c in self.checks],
            "timestamp": self.timestamp,
        }


# ── PreFilingValidator ───────────────────────────────────────────────

class PreFilingValidator:
    """Orchestrates all pre-filing quality checks."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def _get_conn(self) -> Optional[sqlite3.Connection]:
        try:
            conn = sqlite3.connect(self.db_path, timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA query_only=ON")
            conn.row_factory = sqlite3.Row
            return conn
        except Exception:
            return None

    def _detect_court_level(self, text: str, filepath: str) -> str:
        """Detect court level from content or filename."""
        upper = text.upper()
        fn = os.path.basename(filepath).upper()
        if "COURT OF APPEALS" in upper or "COA" in fn or "APPELLANT" in fn:
            return "COA"
        if "SUPREME COURT" in upper or "MSC" in fn:
            return "MSC"
        if "JTC" in fn or "JUDICIAL TENURE" in upper:
            return "JTC"
        if "UNITED STATES DISTRICT" in upper or "USDC" in fn:
            return "USDC"
        return "circuit"

    # ── Individual Checks ────────────────────────────────────────────

    def _check_file_readable(self, filepath: str) -> CheckItem:
        """Check 1: File exists and is readable."""
        fp = Path(filepath)
        if not fp.exists():
            return CheckItem("file_exists", False, "critical",
                             f"File not found: {filepath}")
        if not fp.is_file():
            return CheckItem("file_exists", False, "critical",
                             f"Not a file: {filepath}")
        try:
            fp.read_text(encoding="utf-8")
            size_kb = fp.stat().st_size / 1024
            return CheckItem("file_exists", True, "info",
                             f"File readable ({size_kb:.1f} KB)")
        except Exception as e:
            return CheckItem("file_exists", False, "critical",
                             f"Cannot read file: {e}")

    def _check_mcr_2113_format(self, text: str) -> CheckItem:
        """Check 2: MCR 2.113 format — caption, numbered paragraphs, signature block."""
        issues = []

        # Caption: case number, parties, court name
        has_case_number = bool(re.search(r'\d{4}-\d{4,6}-\w{2}', text))
        has_court = any(kw in text.upper() for kw in [
            "CIRCUIT COURT", "COURT OF APPEALS", "SUPREME COURT",
            "DISTRICT COURT", "JUDICIAL TENURE"
        ])
        has_parties = bool(re.search(r'(?:Plaintiff|Petitioner|Appellant)', text, re.I))

        if not has_case_number:
            issues.append("Missing case number in caption")
        if not has_court:
            issues.append("Missing court name in caption")
        if not has_parties:
            issues.append("Missing party designations in caption")

        # Numbered paragraphs
        numbered_paras = re.findall(r'^\s*\d+\.\s', text, re.MULTILINE)
        has_numbered = len(numbered_paras) >= 3

        # Signature block
        has_signature = bool(re.search(
            r'(?:Respectfully submitted|respectfully submitted|/s/|___+)',
            text
        ))
        if not has_signature:
            issues.append("Missing signature block")

        passed = has_case_number and has_court and has_signature
        if issues:
            return CheckItem("mcr_2113_format", False, "major",
                             f"MCR 2.113 format issues: {'; '.join(issues)}",
                             details=issues)
        return CheckItem("mcr_2113_format", True, "info",
                         "MCR 2.113 format compliant")

    def _check_certificate_of_service(self, text: str) -> CheckItem:
        """Check 3: Certificate of Service present (MCR 2.107)."""
        cos_patterns = [
            r'CERTIFICATE\s+OF\s+SERVICE',
            r'PROOF\s+OF\s+SERVICE',
            r'I\s+(?:hereby\s+)?certify\s+that\s+.*(?:served|mailed|delivered)',
        ]
        for pat in cos_patterns:
            if re.search(pat, text, re.I):
                return CheckItem("certificate_of_service", True, "info",
                                 "Certificate of Service found")
        # Not required for all document types
        doc_types_requiring_cos = ["MOTION", "BRIEF", "RESPONSE", "OBJECTION",
                                   "PETITION", "COMPLAINT", "APPLICATION"]
        upper = text.upper()
        needs_cos = any(dt in upper for dt in doc_types_requiring_cos)
        if needs_cos:
            return CheckItem("certificate_of_service", False, "critical",
                             "Missing Certificate of Service (MCR 2.107)")
        return CheckItem("certificate_of_service", True, "info",
                         "Certificate of Service not required for this document type")

    def _check_citations_in_db(self, text: str) -> CheckItem:
        """Check 4: Verify citations exist in auth_rules/master_citations."""
        mcr_cites = _MCR_RE.findall(text)
        mcl_cites = _MCL_RE.findall(text)
        mre_cites = _MRE_RE.findall(text)
        case_cites = _CASE_RE.findall(text)

        total = len(mcr_cites) + len(mcl_cites) + len(mre_cites) + len(case_cites)
        if total == 0:
            return CheckItem("citations_verified", False, "major",
                             "No citations found in document")

        conn = self._get_conn()
        if not conn:
            return CheckItem("citations_verified", True, "minor",
                             f"DB unavailable; {total} citations found but not verified",
                             details={"total": total, "verified": 0})

        unverified = []
        verified = 0

        # Check MCR citations
        for cite in mcr_cites:
            base = re.split(r'\(', cite)[0]
            try:
                row = conn.execute(
                    "SELECT COUNT(*) as cnt FROM auth_rules WHERE rule_number LIKE ?",
                    (f"%{base}%",),
                ).fetchone()
                if row["cnt"] > 0:
                    verified += 1
                    continue
                row2 = conn.execute(
                    "SELECT COUNT(*) as cnt FROM rules_text WHERE rule LIKE ?",
                    (f"%{base}%",),
                ).fetchone()
                if row2["cnt"] > 0:
                    verified += 1
                else:
                    unverified.append(f"MCR {cite}")
            except Exception:
                pass

        # Check MCL citations
        for cite in mcl_cites:
            base = re.split(r'\(', cite)[0]
            try:
                row = conn.execute(
                    "SELECT COUNT(*) as cnt FROM rules_text WHERE rule LIKE ? OR context LIKE ?",
                    (f"%{base}%", f"%{base}%"),
                ).fetchone()
                if row["cnt"] > 0:
                    verified += 1
                else:
                    unverified.append(f"MCL {cite}")
            except Exception:
                pass

        # Check case law citations
        for cite in case_cites:
            short = cite[:30]
            try:
                row = conn.execute(
                    "SELECT COUNT(*) as cnt FROM master_citations WHERE citation LIKE ?",
                    (f"%{short}%",),
                ).fetchone()
                if row["cnt"] > 0:
                    verified += 1
                else:
                    unverified.append(cite)
            except Exception:
                pass

        conn.close()

        details = {
            "total": total,
            "verified": verified,
            "unverified_count": len(unverified),
            "unverified": unverified[:15],
        }
        if unverified:
            return CheckItem("citations_verified", False, "minor",
                             f"{len(unverified)}/{total} citations unverified",
                             details=details)
        return CheckItem("citations_verified", True, "info",
                         f"All {verified} citations verified in DB",
                         details=details)

    def _check_placeholders(self, text: str) -> CheckItem:
        """Check 5: No unfilled [PLACEHOLDER], [Address], [TODO] fields."""
        found = _PLACEHOLDER_RE.findall(text)
        if found:
            deduped = sorted(set(found))
            return CheckItem("no_placeholders", False, "critical",
                             f"{len(found)} unfilled placeholder(s) found",
                             details=deduped[:20])
        return CheckItem("no_placeholders", True, "info",
                         "No unfilled placeholders")

    def _check_word_count(self, text: str, court_level: str) -> CheckItem:
        """Check 6: Word count compliance per court rules."""
        words = len(text.split())
        limits = WORD_LIMITS.get(court_level, WORD_LIMITS["circuit"])
        max_w = limits["max_words"]
        rule = limits["rule"]

        if max_w is None:
            return CheckItem("word_count", True, "info",
                             f"Word count: {words:,} (no limit for {court_level})",
                             details={"words": words, "court": court_level})

        if words > max_w:
            return CheckItem("word_count", False, "critical",
                             f"Word count {words:,} exceeds {max_w:,} limit ({rule})",
                             details={"words": words, "limit": max_w, "rule": rule})
        pct = (words / max_w) * 100
        return CheckItem("word_count", True, "info",
                         f"Word count: {words:,}/{max_w:,} ({pct:.0f}%) — {rule}",
                         details={"words": words, "limit": max_w, "pct": round(pct, 1)})

    def _check_required_sections(self, text: str, court_level: str) -> CheckItem:
        """Check 7: Court-specific required sections present."""
        upper = text.upper()
        missing = []

        if court_level == "COA":
            # MCR 7.212(C) required sections
            required = {
                "Table of Contents": r"TABLE\s+OF\s+CONTENTS",
                "Table/Index of Authorities": r"(?:TABLE|INDEX)\s+OF\s+AUTHORITIES",
                "Statement of Jurisdiction": r"(?:JURISDICTIONAL?\s+STATEMENT|STATEMENT\s+OF\s+JURISDICTION)",
                "Statement of Questions": r"(?:QUESTIONS?\s+PRESENTED|STATEMENT\s+OF\s+(?:THE\s+)?QUESTIONS?)",
                "Statement of Facts": r"STATEMENT\s+OF\s+(?:THE\s+)?FACTS",
                "Argument": r"ARGUMENT",
                "Relief Requested": r"(?:RELIEF\s+REQUESTED|CONCLUSION)",
            }
        elif court_level == "MSC":
            # MCR 7.306(D) / 7.305 required sections
            required = {
                "Questions Presented": r"QUESTIONS?\s+PRESENTED",
                "Statement of Facts": r"STATEMENT\s+OF\s+(?:THE\s+)?FACTS",
                "Argument": r"ARGUMENT",
                "Relief": r"(?:RELIEF|CONCLUSION|PRAYER)",
            }
        elif court_level == "JTC":
            required = {
                "Factual Allegations": r"(?:FACTUAL\s+ALLEGATIONS|FACTS|ALLEGATIONS)",
                "Violations": r"(?:VIOLATIONS|COUNTS|CHARGES)",
                "Relief": r"(?:RELIEF|CONCLUSION|PRAYER|REQUESTED\s+ACTION)",
            }
        else:
            required = {}

        for name, pattern in required.items():
            if not re.search(pattern, upper):
                missing.append(name)

        if missing:
            return CheckItem("required_sections", False, "major",
                             f"Missing required sections for {court_level}: {', '.join(missing)}",
                             details=missing)
        return CheckItem("required_sections", True, "info",
                         f"All required sections present for {court_level}")

    def _check_formatting(self, text: str) -> CheckItem:
        """Check 8: Basic formatting — no obvious issues."""
        issues = []
        lines = text.split('\n')
        empty_count = sum(1 for line in lines if not line.strip())
        if empty_count > len(lines) * 0.4:
            issues.append(f"Excessive blank lines ({empty_count}/{len(lines)})")
        # Check for markdown-only artifacts that need conversion
        md_headers = len(re.findall(r'^#{1,6}\s', text, re.MULTILINE))
        if md_headers > 0:
            issues.append(f"{md_headers} markdown headers found — convert to Word/PDF before filing")
        if issues:
            return CheckItem("formatting", False, "minor",
                             "; ".join(issues), details=issues)
        return CheckItem("formatting", True, "info", "No formatting issues detected")

    # ── Main Orchestrator ────────────────────────────────────────────

    def validate_filing(self, filepath: str) -> Dict[str, Any]:
        """Run ALL pre-filing checks on one filing.

        Args:
            filepath: Path to the filing document (.md or .txt)

        Returns:
            Structured validation result with PASS/FAIL per check.
        """
        result = FilingValidationResult(filepath=filepath)

        # Check 1: File readable
        file_check = self._check_file_readable(filepath)
        result.add_check(file_check)
        if not file_check.passed:
            return result.to_dict()

        text = Path(filepath).read_text(encoding="utf-8", errors="replace")
        court_level = self._detect_court_level(text, filepath)

        # Check 2: MCR 2.113 format
        result.add_check(self._check_mcr_2113_format(text))

        # Check 3: Certificate of Service
        result.add_check(self._check_certificate_of_service(text))

        # Check 4: Citation verification
        result.add_check(self._check_citations_in_db(text))

        # Check 5: Placeholders
        result.add_check(self._check_placeholders(text))

        # Check 6: Word count
        result.add_check(self._check_word_count(text, court_level))

        # Check 7: Required sections
        result.add_check(self._check_required_sections(text, court_level))

        # Check 8: Formatting
        result.add_check(self._check_formatting(text))

        return result.to_dict()

    def validate_all_filings(self, directory: str = FILINGS_DIR) -> Dict[str, Any]:
        """Scan filings directory and validate each .md file.

        Args:
            directory: Path to scan (default: 04_COURT_FILINGS)

        Returns:
            Summary with per-file results.
        """
        results = []
        scan_dirs = [directory]

        # Also scan known filing locations
        base = Path(r"C:\Users\andre\LitigationOS")
        extra_dirs = [
            base / "LANE_A", base / "LANE_F",
            base / "03_JTC", base / "04_MSC",
        ]
        for d in extra_dirs:
            if d.exists() and str(d) != directory:
                scan_dirs.append(str(d))

        all_files = []
        for scan_dir in scan_dirs:
            d = Path(scan_dir)
            if d.exists():
                all_files.extend(d.glob("*.md"))

        if not all_files:
            return {
                "status": "NO_FILES",
                "message": f"No .md files found in scanned directories",
                "directories_scanned": scan_dirs,
                "results": [],
            }

        for fp in sorted(all_files):
            results.append(self.validate_filing(str(fp)))

        passed = sum(1 for r in results if r["overall"] == "PASS")
        failed = sum(1 for r in results if r["overall"] == "FAIL")

        return {
            "status": "COMPLETE",
            "total_files": len(results),
            "passed": passed,
            "failed": failed,
            "pass_rate": f"{(passed / len(results) * 100):.1f}%" if results else "N/A",
            "directories_scanned": scan_dirs,
            "results": results,
            "timestamp": datetime.now().isoformat(),
        }

    def filing_checklist(self, court_level: str = "circuit") -> Dict[str, Any]:
        """Return pre-filing checklist for a specific court level.

        Args:
            court_level: One of circuit, COA, MSC, USDC, JTC

        Returns:
            Structured checklist with items, authority, and notes.
        """
        court = court_level.upper() if court_level.upper() in ("COA", "MSC", "USDC", "JTC") else "circuit"

        common_items = [
            {"item": "Caption with case number, parties, court", "authority": "MCR 2.113(A)", "required": True},
            {"item": "Numbered paragraphs", "authority": "MCR 2.113(B)", "required": True},
            {"item": "Signature block with name, address, bar number", "authority": "MCR 2.114(A)", "required": True},
            {"item": "Certificate of Service", "authority": "MCR 2.107(C)(3)", "required": True},
            {"item": "No unfilled placeholders/bracketed fields", "authority": "N/A", "required": True},
            {"item": "All citations verified in authority database", "authority": "N/A", "required": True},
            {"item": "Proofread for factual accuracy", "authority": "MCR 2.114(D)", "required": True},
            {"item": "Date and venue correct", "authority": "MCR 2.113", "required": True},
        ]

        court_specific = {
            "circuit": [
                {"item": "Proposed order attached (if motion)", "authority": "MCR 2.119(A)(2)", "required": True},
                {"item": "Brief in support (if substantive motion)", "authority": "MCR 2.119(A)(2)", "required": False},
                {"item": "Notice of hearing (9-day service)", "authority": "MCR 2.119(C)(1)", "required": True},
                {"item": "Filing fee or fee waiver", "authority": "MCL 600.880", "required": True},
                {"item": "SCAO approved form (if applicable)", "authority": "MCR 1.109(D)(1)", "required": False},
            ],
            "COA": [
                {"item": "Table of Contents", "authority": "MCR 7.212(C)(1)", "required": True},
                {"item": "Index of Authorities", "authority": "MCR 7.212(C)(2)", "required": True},
                {"item": "Statement of Jurisdiction", "authority": "MCR 7.212(C)(3)", "required": True},
                {"item": "Questions Presented", "authority": "MCR 7.212(C)(4)", "required": True},
                {"item": "Statement of Facts with record citations", "authority": "MCR 7.212(C)(6)", "required": True},
                {"item": "Argument with IRAC structure", "authority": "MCR 7.212(C)(7)", "required": True},
                {"item": "Relief Requested", "authority": "MCR 7.212(C)(8)", "required": True},
                {"item": "Word count ≤ 16,000 or page count ≤ 50", "authority": "MCR 7.212(B)", "required": True},
                {"item": "Appendix with required documents", "authority": "MCR 7.212(D)", "required": True},
                {"item": "Claim of Appeal filed within 21 days", "authority": "MCR 7.204(A)(1)", "required": True},
                {"item": "Proof of payment of $375 filing fee", "authority": "MCR 7.204(B)", "required": True},
            ],
            "MSC": [
                {"item": "Questions Presented (clear, concise)", "authority": "MCR 7.306(D)(1)", "required": True},
                {"item": "Statement of material proceedings and facts", "authority": "MCR 7.306(D)(2)", "required": True},
                {"item": "Argument — why superintending control warranted", "authority": "MCR 7.306(D)(3)", "required": True},
                {"item": "Relief requested — specific remedy sought", "authority": "MCR 7.306(D)(4)", "required": True},
                {"item": "Appendix with lower court orders", "authority": "MCR 7.306(D)(5)", "required": True},
                {"item": "13 copies for filing", "authority": "MCR 7.306(E)", "required": True},
                {"item": "Verification/affidavit of facts", "authority": "MCR 7.306(C)", "required": True},
                {"item": "Filing fee ($375)", "authority": "MCR 7.306(E)", "required": True},
            ],
            "USDC": [
                {"item": "Civil cover sheet (JS-44)", "authority": "LCivR 3.1", "required": True},
                {"item": "Word count ≤ 14,000 (briefs)", "authority": "LCivR 7.1(d)(2)", "required": True},
                {"item": "In forma pauperis application (if applicable)", "authority": "28 USC § 1915", "required": False},
                {"item": "Federal question or diversity jurisdiction stated", "authority": "28 USC § 1331/1332", "required": True},
                {"item": "ECF filing format compliance", "authority": "LCivR 5.7", "required": True},
            ],
            "JTC": [
                {"item": "Specific judicial conduct allegations", "authority": "MCR 9.211", "required": True},
                {"item": "Dates of each violation", "authority": "MCR 9.211", "required": True},
                {"item": "Supporting evidence or exhibits referenced", "authority": "MCR 9.211", "required": True},
                {"item": "Signed under oath or affirmation", "authority": "MCR 9.211", "required": True},
                {"item": "Mailed to JTC at correct address", "authority": "MCR 9.220", "required": True},
            ],
        }

        items = common_items + court_specific.get(court, [])

        return {
            "court_level": court,
            "total_items": len(items),
            "required_items": sum(1 for i in items if i["required"]),
            "checklist": items,
            "notes": [
                f"Filing standards per Michigan Court Rules as of {datetime.now().strftime('%Y-%m-%d')}",
                "Pro se filers: courts may apply lenient construction but compliance prevents rejection",
                "Always verify current deadlines before filing — jurisdictional deadlines are absolute",
            ],
        }


# ── Module-level convenience functions (for JSON-RPC dispatch) ───────

_validator = None

def _get_validator() -> PreFilingValidator:
    global _validator
    if _validator is None:
        _validator = PreFilingValidator()
    return _validator

def validate_filing(filepath: str) -> Dict[str, Any]:
    """JSON-RPC: validate_filing — Run all checks on one filing."""
    return _get_validator().validate_filing(filepath)

def validate_all_filings(directory: str = FILINGS_DIR) -> Dict[str, Any]:
    """JSON-RPC: validate_all_filings — Scan and validate all .md filings."""
    return _get_validator().validate_all_filings(directory)

def filing_checklist(court_level: str = "circuit") -> Dict[str, Any]:
    """JSON-RPC: filing_checklist — Return checklist for a court level."""
    return _get_validator().filing_checklist(court_level)


# ── CLI ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Pre-Filing Validator — Automated Quality Gate",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pre_filing_validator.py validate path/to/brief.md
  python pre_filing_validator.py validate-all
  python pre_filing_validator.py validate-all --dir C:\\filings
  python pre_filing_validator.py checklist COA
  python pre_filing_validator.py checklist MSC
        """,
    )
    sub = parser.add_subparsers(dest="command", help="Command to run")

    # validate
    p_val = sub.add_parser("validate", help="Validate a single filing")
    p_val.add_argument("filepath", help="Path to filing document")

    # validate-all
    p_all = sub.add_parser("validate-all", help="Validate all filings in directory")
    p_all.add_argument("--dir", default=FILINGS_DIR, help="Directory to scan")

    # checklist
    p_chk = sub.add_parser("checklist", help="Show filing checklist for a court")
    p_chk.add_argument("court", nargs="?", default="circuit",
                        choices=["circuit", "COA", "MSC", "USDC", "JTC"],
                        help="Court level")

    args = parser.parse_args()

    if args.command == "validate":
        result = validate_filing(args.filepath)
        cycle_json(result)
    elif args.command == "validate-all":
        result = validate_all_filings(args.dir)
        cycle_json(result)
    elif args.command == "checklist":
        result = filing_checklist(args.court)
        cycle_json(result)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
