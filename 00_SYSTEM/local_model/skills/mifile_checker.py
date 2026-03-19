"""
MiFILE Compliance Checker for Michigan E-Filing.

Checks documents for MiFILE e-filing compliance to prevent rejection.
Validates PDF format, file size, metadata, content requirements, and
court-filing standards.

Usage:
    from skills.mifile_checker import check_document, check_pdf, check_text

    result = check_document('path/to/filing.pdf')
    if not result.passed:
        for issue in result.issues:
            print(f"[{issue.severity}] {issue.description}")
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class Severity(str, Enum):
    """Issue severity levels."""
    ERROR = 'ERROR'       # Will cause rejection
    WARNING = 'WARNING'   # May cause issues
    INFO = 'INFO'         # Recommendation


@dataclass
class MiFileIssue:
    """A single compliance issue found during checking."""
    rule: str
    description: str
    severity: Severity
    location: Optional[str] = None
    suggestion: Optional[str] = None

    def __str__(self) -> str:
        loc = f' at {self.location}' if self.location else ''
        sug = f' — {self.suggestion}' if self.suggestion else ''
        return f'[{self.severity.value}] {self.rule}: {self.description}{loc}{sug}'


@dataclass
class MiFileResult:
    """Result of MiFILE compliance check."""
    passed: bool
    issues: List[MiFileIssue] = field(default_factory=list)
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    checks_performed: int = 0

    @property
    def errors(self) -> List[MiFileIssue]:
        """Return only ERROR-level issues."""
        return [i for i in self.issues if i.severity == Severity.ERROR]

    @property
    def warnings(self) -> List[MiFileIssue]:
        """Return only WARNING-level issues."""
        return [i for i in self.issues if i.severity == Severity.WARNING]

    def summary(self) -> str:
        """Human-readable summary of the check result."""
        status = 'PASSED' if self.passed else 'FAILED'
        err_count = len(self.errors)
        warn_count = len(self.warnings)
        info_count = len(self.issues) - err_count - warn_count
        parts = [f'MiFILE Check: {status}']
        parts.append(f'  Checks performed: {self.checks_performed}')
        if self.file_path:
            parts.append(f'  File: {self.file_path}')
        if self.file_size_bytes is not None:
            size_mb = self.file_size_bytes / (1024 * 1024)
            parts.append(f'  Size: {size_mb:.2f} MB')
        parts.append(f'  Errors: {err_count}, Warnings: {warn_count}, Info: {info_count}')
        if self.issues:
            parts.append('  Issues:')
            for issue in self.issues:
                parts.append(f'    {issue}')
        return '\n'.join(parts)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB
MIN_FONT_SIZE_PT = 12
MIN_MARGIN_INCHES = 1.0
REQUIRED_PAGE_WIDTH_IN = 8.5
REQUIRED_PAGE_HEIGHT_IN = 11.0

# Patterns for content checks
_CERT_OF_SERVICE_PATTERNS = [
    r'CERTIFICATE\s+OF\s+SERVICE',
    r'PROOF\s+OF\s+SERVICE',
    r'I\s+(?:hereby\s+)?certify\s+that.*served',
]

_SIGNATURE_PATTERNS = [
    r'_{10,}',                                 # Signature line
    r'Respectfully\s+submitted',
    r'/s/\s*\w+',                              # Electronic signature
    r'(?:Plaintiff|Defendant).*(?:Pro\s+Se)',
]

_DATE_PATTERNS = [
    r'Dated:\s*',
    r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
    r'\b(?:January|February|March|April|May|June|July|August|'
    r'September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
]

_DRAFT_PATTERNS = [
    r'\bDRAFT\b',
    r'\bWATERMARK\b',
    r'\bCONFIDENTIAL\s*-\s*DRAFT\b',
    r'\bFOR\s+REVIEW\s+ONLY\b',
]

_PAGE_NUMBER_PATTERNS = [
    r'(?:^|\n)\s*(?:Page\s+)?\d+\s+(?:of\s+\d+)?\s*(?:\n|$)',
    r'(?:^|\n)\s*-\s*\d+\s*-\s*(?:\n|$)',
]

_CASE_NUMBER_PATTERNS = [
    r'Case\s+No\.?\s*\S+',
    r'(?:No|Docket)\.\s*\S+',
    r'\d{4}-\d{4,6}-\w{2}',    # Michigan case number format
]


# ---------------------------------------------------------------------------
# PDF-specific checks
# ---------------------------------------------------------------------------
def _check_pdf_basic(pdf_path: str, issues: List[MiFileIssue]) -> int:
    """Run basic PDF checks (file-level, no parsing)."""
    checks = 0

    # Check 1: File exists and is PDF
    checks += 1
    if not os.path.isfile(pdf_path):
        issues.append(MiFileIssue(
            rule='FILE_EXISTS',
            description=f'File not found: {pdf_path}',
            severity=Severity.ERROR,
        ))
        return checks

    # Check 2: File extension
    checks += 1
    if not pdf_path.lower().endswith('.pdf'):
        issues.append(MiFileIssue(
            rule='PDF_FORMAT',
            description='File does not have .pdf extension',
            severity=Severity.ERROR,
            suggestion='MiFILE requires PDF format for all filings',
        ))

    # Check 3: File size
    checks += 1
    file_size = os.path.getsize(pdf_path)
    if file_size > MAX_FILE_SIZE_BYTES:
        size_mb = file_size / (1024 * 1024)
        issues.append(MiFileIssue(
            rule='FILE_SIZE',
            description=f'File is {size_mb:.1f} MB, exceeds 25 MB limit',
            severity=Severity.ERROR,
            suggestion='Split into multiple documents or reduce image resolution',
        ))
    elif file_size == 0:
        issues.append(MiFileIssue(
            rule='FILE_SIZE',
            description='File is empty (0 bytes)',
            severity=Severity.ERROR,
        ))

    # Check 4: PDF header
    checks += 1
    try:
        with open(pdf_path, 'rb') as f:
            header = f.read(1024)

        if not header.startswith(b'%PDF'):
            issues.append(MiFileIssue(
                rule='PDF_FORMAT',
                description='File does not appear to be a valid PDF',
                severity=Severity.ERROR,
                suggestion='Ensure the file is a properly generated PDF',
            ))

        # Check 5: Password protection
        checks += 1
        if b'/Encrypt' in header:
            issues.append(MiFileIssue(
                rule='NO_PASSWORD',
                description='PDF appears to be password-protected or encrypted',
                severity=Severity.ERROR,
                suggestion='Remove password protection before filing',
            ))

    except OSError as e:
        issues.append(MiFileIssue(
            rule='FILE_READ',
            description=f'Cannot read file: {e}',
            severity=Severity.ERROR,
        ))

    return checks


def _check_pdf_advanced(pdf_path: str, issues: List[MiFileIssue]) -> int:
    """Run advanced PDF checks using PyPDF2/pikepdf if available."""
    checks = 0

    try:
        import PyPDF2
    except ImportError:
        issues.append(MiFileIssue(
            rule='PDF_ANALYSIS',
            description='PyPDF2 not available — skipping advanced PDF checks',
            severity=Severity.INFO,
            suggestion='Install PyPDF2 for full PDF validation: pip install PyPDF2',
        ))
        return checks

    try:
        reader = PyPDF2.PdfReader(pdf_path)

        # Check: Text-selectable (not image-only)
        checks += 1
        has_text = False
        for page in reader.pages[:5]:  # Check first 5 pages
            text = page.extract_text() or ''
            if text.strip():
                has_text = True
                break
        if not has_text:
            issues.append(MiFileIssue(
                rule='TEXT_SELECTABLE',
                description='PDF appears to be image-only (no selectable text)',
                severity=Severity.ERROR,
                suggestion='Use OCR to create a text-selectable PDF',
            ))

        # Check: Page size
        checks += 1
        for i, page in enumerate(reader.pages):
            box = page.mediabox
            width_in = float(box.width) / 72.0
            height_in = float(box.height) / 72.0
            if abs(width_in - REQUIRED_PAGE_WIDTH_IN) > 0.5 or \
               abs(height_in - REQUIRED_PAGE_HEIGHT_IN) > 0.5:
                issues.append(MiFileIssue(
                    rule='PAGE_SIZE',
                    description=(
                        f'Page {i + 1} is {width_in:.1f}" x {height_in:.1f}", '
                        f'expected 8.5" x 11"'
                    ),
                    severity=Severity.WARNING,
                    location=f'Page {i + 1}',
                    suggestion='Reformat to standard letter size (8.5 x 11)',
                ))
                break  # Report only first occurrence

        # Check: Encryption
        checks += 1
        if reader.is_encrypted:
            issues.append(MiFileIssue(
                rule='NO_PASSWORD',
                description='PDF is encrypted/password-protected',
                severity=Severity.ERROR,
                suggestion='Remove encryption before filing via MiFILE',
            ))

    except Exception as e:
        issues.append(MiFileIssue(
            rule='PDF_ANALYSIS',
            description=f'Error analyzing PDF: {e}',
            severity=Severity.WARNING,
        ))

    return checks


# ---------------------------------------------------------------------------
# Text content checks
# ---------------------------------------------------------------------------
def _check_certificate_of_service(text: str, issues: List[MiFileIssue]) -> int:
    """Check for Certificate of Service."""
    for pattern in _CERT_OF_SERVICE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return 1
    issues.append(MiFileIssue(
        rule='CERT_OF_SERVICE',
        description='No Certificate of Service found',
        severity=Severity.WARNING,
        suggestion='Add Certificate of Service per MCR 2.107',
    ))
    return 1


def _check_signature_block(text: str, issues: List[MiFileIssue]) -> int:
    """Check for signature block."""
    for pattern in _SIGNATURE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return 1
    issues.append(MiFileIssue(
        rule='SIGNATURE',
        description='No signature block found',
        severity=Severity.ERROR,
        suggestion='Add signature block per MCR 2.113(E)',
    ))
    return 1


def _check_date_present(text: str, issues: List[MiFileIssue]) -> int:
    """Check for a date in the document."""
    for pattern in _DATE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return 1
    issues.append(MiFileIssue(
        rule='DATE_PRESENT',
        description='No date found in the document',
        severity=Severity.WARNING,
        suggestion='Add a date to the filing',
    ))
    return 1


def _check_no_draft_marks(text: str, issues: List[MiFileIssue]) -> int:
    """Check for DRAFT watermarks or stamps."""
    for pattern in _DRAFT_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            issues.append(MiFileIssue(
                rule='NO_DRAFT_MARKS',
                description=f'Document contains draft marking: "{match.group()}"',
                severity=Severity.ERROR,
                suggestion='Remove all DRAFT watermarks before filing',
            ))
            return 1
    return 1


def _check_case_number(text: str, issues: List[MiFileIssue]) -> int:
    """Check for case number in document."""
    for pattern in _CASE_NUMBER_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return 1
    issues.append(MiFileIssue(
        rule='CASE_NUMBER',
        description='No case number found in document',
        severity=Severity.WARNING,
        suggestion='Include case number in header/footer and caption',
    ))
    return 1


def _check_page_numbers(text: str, issues: List[MiFileIssue]) -> int:
    """Check for page numbers."""
    for pattern in _PAGE_NUMBER_PATTERNS:
        if re.search(pattern, text):
            return 1
    # Also check for simple standalone numbers that could be page numbers
    lines = text.strip().split('\n')
    for line in lines:
        stripped = line.strip()
        if stripped.isdigit() and 1 <= int(stripped) <= 999:
            return 1
    issues.append(MiFileIssue(
        rule='PAGE_NUMBERS',
        description='No page numbers detected',
        severity=Severity.WARNING,
        suggestion='Add page numbers to all pages',
    ))
    return 1


def _check_proper_party_names(text: str, issues: List[MiFileIssue]) -> int:
    """Check that party names in caption are not abbreviated."""
    # Look for common abbreviations in caption area (first ~500 chars)
    caption_area = text[:500]
    abbrev_patterns = [
        r'\b[A-Z]\.\s*[A-Z](?:igors|atson)',  # A. Pigors, E. Watson
        r'\bPlf\b',
        r'\bDef\b',
        r'\bDeft\b',
    ]
    for pattern in abbrev_patterns:
        match = re.search(pattern, caption_area)
        if match:
            issues.append(MiFileIssue(
                rule='PARTY_NAMES',
                description=f'Possible abbreviated party name in caption: "{match.group()}"',
                severity=Severity.WARNING,
                location='Caption',
                suggestion='Use full party names in the caption per MCR 2.113(C)',
            ))
            return 1
    return 1


def _check_redaction(text: str, issues: List[MiFileIssue]) -> int:
    """Check for improper redaction patterns."""
    # Black bar redaction typically shows as unicode block characters
    block_chars = ['█', '▓', '▒', '░', '■']
    for char in block_chars:
        if char in text:
            issues.append(MiFileIssue(
                rule='PROPER_REDACTION',
                description='Document may contain black-bar redaction',
                severity=Severity.WARNING,
                suggestion='Use proper PDF redaction tools that remove underlying text',
            ))
            return 1
    return 1


def _check_font_size_heuristic(text: str, issues: List[MiFileIssue]) -> int:
    """
    Heuristic check for tiny text (only meaningful for raw PDF text extraction).
    Checks for font-size indicators in extracted text.
    """
    # Look for font size specifications in PDF-extracted text
    tiny_font = re.search(r'/F\w+\s+(\d+(?:\.\d+)?)\s+Tf', text)
    if tiny_font:
        size = float(tiny_font.group(1))
        if size < MIN_FONT_SIZE_PT:
            issues.append(MiFileIssue(
                rule='FONT_SIZE',
                description=f'Font size {size}pt detected, minimum is {MIN_FONT_SIZE_PT}pt',
                severity=Severity.WARNING,
                suggestion=f'Use minimum {MIN_FONT_SIZE_PT}pt font throughout',
            ))
    return 1


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def check_document(file_path: str) -> MiFileResult:
    """
    Check a document file for MiFILE e-filing compliance.

    Runs all applicable checks based on file type. For PDFs, runs both
    file-level and content checks. For text files, runs content checks only.

    Args:
        file_path: Path to the document file.

    Returns:
        MiFileResult with pass/fail status and detailed issues.
    """
    issues: List[MiFileIssue] = []
    checks = 0
    file_size = None

    if os.path.isfile(file_path):
        file_size = os.path.getsize(file_path)

    if file_path.lower().endswith('.pdf'):
        checks += _check_pdf_basic(file_path, issues)
        checks += _check_pdf_advanced(file_path, issues)

        # Try to extract text for content checks
        text = _extract_pdf_text(file_path)
        if text:
            checks += _run_text_checks(text, issues)
    elif file_path.lower().endswith(('.txt', '.md', '.docx')):
        # For text-based files, read and check content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            checks += _run_text_checks(text, issues)

            # Warn that final filing must be PDF
            issues.append(MiFileIssue(
                rule='PDF_FORMAT',
                description=f'File is not PDF format ({Path(file_path).suffix})',
                severity=Severity.WARNING,
                suggestion='Convert to PDF before filing via MiFILE',
            ))
            checks += 1
        except OSError as e:
            issues.append(MiFileIssue(
                rule='FILE_READ',
                description=f'Cannot read file: {e}',
                severity=Severity.ERROR,
            ))
            checks += 1
    else:
        issues.append(MiFileIssue(
            rule='FILE_FORMAT',
            description=f'Unsupported file format: {Path(file_path).suffix}',
            severity=Severity.ERROR,
            suggestion='MiFILE accepts PDF files. Convert before filing.',
        ))
        checks += 1

    has_errors = any(i.severity == Severity.ERROR for i in issues)

    return MiFileResult(
        passed=not has_errors,
        issues=issues,
        file_path=file_path,
        file_size_bytes=file_size,
        checks_performed=checks,
    )


def check_pdf(pdf_path: str) -> MiFileResult:
    """
    Check a PDF file for MiFILE compliance.

    Convenience wrapper that enforces PDF-only input.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        MiFileResult with pass/fail status and detailed issues.

    Raises:
        ValueError: If the file does not have a .pdf extension.
    """
    if not pdf_path.lower().endswith('.pdf'):
        raise ValueError(f'Expected a .pdf file, got: {pdf_path}')
    return check_document(pdf_path)


def check_text(
    document_text: str,
    document_name: Optional[str] = None,
) -> MiFileResult:
    """
    Check document text content for MiFILE compliance.

    Runs all text-based content checks without requiring a file on disk.
    Useful for checking documents before PDF conversion.

    Args:
        document_text: The full text content of the document.
        document_name: Optional name for reporting purposes.

    Returns:
        MiFileResult with pass/fail status and detailed issues.
    """
    issues: List[MiFileIssue] = []
    checks = _run_text_checks(document_text, issues)

    has_errors = any(i.severity == Severity.ERROR for i in issues)

    return MiFileResult(
        passed=not has_errors,
        issues=issues,
        file_path=document_name,
        file_size_bytes=len(document_text.encode('utf-8')),
        checks_performed=checks,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _run_text_checks(text: str, issues: List[MiFileIssue]) -> int:
    """Run all text-based content checks."""
    checks = 0
    checks += _check_certificate_of_service(text, issues)
    checks += _check_signature_block(text, issues)
    checks += _check_date_present(text, issues)
    checks += _check_no_draft_marks(text, issues)
    checks += _check_case_number(text, issues)
    checks += _check_page_numbers(text, issues)
    checks += _check_proper_party_names(text, issues)
    checks += _check_redaction(text, issues)
    checks += _check_font_size_heuristic(text, issues)
    return checks


def _extract_pdf_text(pdf_path: str) -> Optional[str]:
    """Extract text from a PDF file if possible."""
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(pdf_path)
        pages_text = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)
        return '\n'.join(pages_text) if pages_text else None
    except ImportError:
        return None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        path = sys.argv[1]
        print(f'Checking: {path}\n')
        result = check_document(path)
        print(result.summary())
        sys.exit(0 if result.passed else 1)

    # Demo with sample text
    print('=== MiFILE Compliance Checker Demo ===\n')

    sample_good = """STATE OF MICHIGAN
IN THE 14th CIRCUIT COURT FOR THE COUNTY OF MUSKEGON

ANDREW PIGORS,                    Case No. 2024-001507-DC
    Plaintiff,                    Hon. Jenny L. McNeill

v.                                MOTION FOR RECONSIDERATION

EMILY WATSON,
    Defendant.
________________________________/

MOTION FOR RECONSIDERATION

    Plaintiff Andrew Pigors respectfully moves this Court for reconsideration.

Dated: January 15, 2026

Respectfully submitted,

________________________________
ANDREW PIGORS
Plaintiff, Pro Se

Page 1 of 3

CERTIFICATE OF SERVICE

    I hereby certify that on January 15, 2026, I served a true and correct
copy of the foregoing upon Defendant by first-class mail.
"""

    print('--- Good Document ---')
    result = check_text(sample_good, 'good_motion.txt')
    print(result.summary())
    print()

    sample_bad = """DRAFT — FOR REVIEW ONLY

A. Pigors v E. Watson

Motion for stuff

████████ redacted text ████████
"""

    print('--- Bad Document ---')
    result = check_text(sample_bad, 'bad_motion.txt')
    print(result.summary())
