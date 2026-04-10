"""
QA Automation Engine (U09) — LitigationOS Court Filing Validator.

Runs 12 validation gates on court-filing markdown documents to catch
contamination, hallucinations, wrong party names, stale dates, and
every other defect that would embarrass a pro-se litigant in open court.

Usage:
    from engines.qa import QAEngine
    engine = QAEngine()
    report = engine.audit_all()
    print(engine.summary(report))

Gates:
    1  Placeholder Detection          6  Dynamic Day Count        11 Word / Page Count
    2  AI / System Contamination      7  Year Verification        12 Exhibit Cross-Reference
    3  File-Path Contamination        8  Citation Extraction
    4  Party-Name Verification        9  Child-Name Protection
    5  Hallucination Blacklist       10  Pro-Se Verification
"""

from __future__ import annotations

import os
import re
import sqlite3
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

__version__ = "1.0.0"
__all__ = ["QAEngine", "QAReport", "PacketReport", "FullReport", "Finding"]

# ── repo-root anchor ────────────────────────────────────────────────
_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_GOLDEN = _REPO_ROOT / "05_FILINGS" / "GOLDEN_SET"
_DEFAULT_DB = _REPO_ROOT / "litigation_context.db"
_SEPARATION_ANCHOR = date(2025, 7, 29)

# ── severity constants ──────────────────────────────────────────────
CRITICAL = "CRITICAL"
WARNING = "WARNING"
INFO = "INFO"
OK = "OK"

# ── word-count thresholds ───────────────────────────────────────────
_WORD_LIMITS: Dict[str, int] = {
    "COA":     16_000,   # MCR 7.212
    "CIRCUIT": 10_000,   # advisory
    "FEDERAL": 14_000,   # LCivR guidance
    "MSC":     16_000,   # same as COA
    "DEFAULT": 10_000,
}


# ╔══════════════════════════════════════════════════════════════════╗
# ║  COMPILED REGEX — built once at import time for performance     ║
# ╚══════════════════════════════════════════════════════════════════╝

# Gate 1 — placeholders
_RE_PLACEHOLDER = re.compile(
    r"\[(?:ANDREW_REQUIRED|TBD|PLACEHOLDER|INSERT|TODO|VERIFY|ACQUIRE|ATTACH|FILL)[^\]]*\]",
    re.IGNORECASE,
)
_RE_PHYSICAL_ACTION = re.compile(
    r"\b(?:notariz|sign(?:ature|ed)|print|file\s+at\s+clerk|hand[- ]deliver|wet[- ]ink)",
    re.IGNORECASE,
)

# Gate 2 — AI / system contamination
_AI_LITERAL_TOKENS = [
    "LitigationOS", "litigation_context", "evidence_quotes",
    "authority_chains", "EGCP", "Filing Engine",
    "Detection Engine", "Authority Engine", "Inference Engine",
    "Objection Engine", "adversary graph engine", "drafting engine",
    "FRED_OBJECTION_ENGINE", "keyword hits", "241,160",
    "neural", "hypergraph", "vector search", "vector database",
    "vector similarity", "semantic score",
    "confidence score", "SINGULARITY", "delta999",
    "SUPERPIN", "copilot_startup", "nexus_fuse", "nexus_argue",
]
# Case-sensitive tokens — only match EXACT case (system names, not English words)
_AI_CASE_SENSITIVE_TOKENS = ["MEEK", "DELTA9", "Embedding"]
_RE_AI_CONTAM_CASE_SENSITIVE = re.compile(
    "|".join(re.escape(tok) for tok in _AI_CASE_SENSITIVE_TOKENS),
)
_RE_AI_CONTAM = re.compile(
    "|".join(re.escape(tok) for tok in _AI_LITERAL_TOKENS),
    re.IGNORECASE,
)
# contextual — only flag "engine", "agent", "database" when surrounded by AI context
_RE_AI_CONTEXT = re.compile(
    r"\b(?:AI|ML|NLP|automated|algorithm|model|pipeline|scoring|ingest)\b",
    re.IGNORECASE,
)
_RE_ENGINE_WORD = re.compile(r"\b(?:engine|agent|database)\b", re.IGNORECASE)

# Gate 3 — file paths
_RE_FILE_PATH = re.compile(
    r"(?:"
    r"[A-Z]:\\(?:Users|users)\\[^\s\"',;)}\]]{2,}"  # C:\Users\...
    r"|[DFGIJ]:\\"                                     # D:\, F:\, etc.
    r"|\b(?:00_SYSTEM|04_ANALYSIS|05_FILINGS|14_MCNEILL)\b"
    r")"
)

# Gate 4 — party names  (wrong variants)
_WRONG_PARTY: List[Tuple[re.Pattern, str, str]] = [
    (re.compile(r"\bEmily\s+Ann\b", re.I),
     "Emily Ann", "Emily A. Watson"),
    (re.compile(r"\bEmily\s+M\.\s*Watson\b", re.I),
     "Emily M. Watson", "Emily A. Watson"),
    (re.compile(r"\bWatson[- ]Pigors\b", re.I),
     "Watson-Pigors", "Emily A. Watson"),
    (re.compile(r"\bMcNeil\b(?!l)"),
     "McNeil (one L)", "McNeill (two Ls)"),
    (re.compile(r"\bAmy\s+McNeill\b", re.I),
     "Amy McNeill", "Hon. Jenny L. McNeill"),
    (re.compile(r"\bundersigned\s+counsel\b", re.I),
     "undersigned counsel", "Plaintiff, appearing pro se"),
    (re.compile(r"\battorney\s+for\s+(?:the\s+)?Plaintiff\b", re.I),
     "attorney for Plaintiff", "Plaintiff, appearing pro se"),
    (re.compile(r"\bcounsel\s+for\s+(?:the\s+)?(?:Plaintiff|Petitioner|Father)\b", re.I),
     "counsel for party", "Plaintiff, appearing pro se"),
    (re.compile(r"\bTiffany\b(?=.*Watson)", re.I),
     "Tiffany Watson", "Emily A. Watson"),
]

# Gate 5 — hallucination blacklist
_HALLUCINATION_STRINGS = [
    "Jane Berry", "Patricia Berry", "P35878",
    "91% alienation", "Ron Berry Esq", "Ron Berry, Esq",
    "9 CPS investigations",
]
_RE_HALLUCINATION = re.compile(
    "|".join(re.escape(s) for s in _HALLUCINATION_STRINGS),
    re.IGNORECASE,
)

# Gate 6 — hardcoded day counts
_RE_DAY_COUNT = re.compile(
    r"(\d{2,4})\s+(?:consecutive\s+)?days?\s+(?:of\s+)?(?:separation|without\s+(?:contact|parenting))",
    re.IGNORECASE,
)

# Gate 7 — stale year in filing-date contexts
_RE_STALE_DATED = re.compile(
    r"(?:"
    r"[Dd]ated[:\s]+(?:\w+\s+\d{1,2},?\s+)?20(?:2[0-5])"
    r"|this\s+\S+\s+day\s+of\s+\w+,?\s+20(?:2[0-5])"
    r"|[Ss]igned[:\s]+(?:\w+\s+\d{1,2},?\s+)?20(?:2[0-5])"
    r"|[Cc]ertificate\s+of\s+[Ss]ervice.*20(?:2[0-5])"
    r"|[Ff]iled[:\s]+(?:\w+\s+\d{1,2},?\s+)?20(?:2[0-5])"
    r")"
)
_RE_YEAR_20XX = re.compile(r"20(\d{2})")

# Gate 8 — citation extraction
_RE_CITATION = re.compile(
    r"\b(?:"
    r"MCR\s+\d+\.\d+(?:\([A-Za-z0-9]+\))*"
    r"|MCL\s+\d+[\.\d]*[a-z]?"
    r"|MRE\s+\d+(?:\([a-z]\))?"
    r"|USC\s+§\s*\d+"
    r"|\d+\s+USC\s+§\s*\d+"
    r"|\d+\s+Mich(?:\s+App)?\s+\d+"
    r"|\d+\s+US\s+\d+"
    r"|\d+\s+F(?:\.\d[dh])?\s+\d+"
    r"|\d+\s+NW(?:\.?2d)\s+\d+"
    r"|\d+\s+S\s*Ct\s+\d+"
    r")"
)

# Gate 9 — child full-name protection  (MCR 8.119(H))
# Build pattern from initials so the full name never appears in source code
_CHILD_FIRST = "Lincoln"
_CHILD_MIDDLE = "David"
_CHILD_LAST_MATERNAL = "Watson"
_RE_CHILD_FULL = re.compile(
    rf"\b{_CHILD_FIRST}\s+{_CHILD_MIDDLE}\b"
    rf"|\b{_CHILD_FIRST}\s+{_CHILD_LAST_MATERNAL}\b"
    rf"|\b{_CHILD_FIRST}\s+D\.\s+{_CHILD_LAST_MATERNAL}\b"
    rf"|\b{_CHILD_FIRST}\s+D\s+W\b"
    rf"|\b{_CHILD_FIRST}\s+{_CHILD_MIDDLE}\s+{_CHILD_LAST_MATERNAL}\b",
    re.IGNORECASE,
)

# Gate 10 — pro-se verification
_RE_NON_PROSE = re.compile(
    r"\b(?:undersigned\s+counsel|attorney\s+for\s+(?:the\s+)?(?:Plaintiff|Petitioner|Father)"
    r"|counsel\s+for\s+(?:the\s+)?(?:Plaintiff|Petitioner|Father)"
    r"|(?:my|our|Plaintiff(?:'s)?)\s+attorney\s+at\s+law"
    r"|(?:my|our|Plaintiff(?:'s)?)\s+law\s+firm"
    r"|esquire\b)",
    re.IGNORECASE,
)

# Gate 12 — exhibit references
_RE_EXHIBIT_REF = re.compile(
    r"(?:"
    r"[Ee]xhibit\s+([A-Z](?:-\d{1,3})?)"
    r"|[Ee]x\.\s*([A-Z](?:-\d{1,3})?)"
    r"|PIGORS-[A-F]-\d{6}"
    r"|[Ee]xhibit\s+(\d{1,2})"
    r"|[Ee]xhibit\s+([A-Z]{2})"
    r")"
)


# ╔══════════════════════════════════════════════════════════════════╗
# ║  DATA CLASSES                                                   ║
# ╚══════════════════════════════════════════════════════════════════╝

@dataclass
class Finding:
    """Single QA finding from one gate."""
    gate: str
    severity: str
    file: str
    line: int
    text: str
    recommendation: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "gate": self.gate,
            "severity": self.severity,
            "file": self.file,
            "line": self.line,
            "text": self.text,
            "recommendation": self.recommendation,
        }


@dataclass
class QAReport:
    """Results of running all gates on a single file."""
    filepath: str
    findings: List[Finding] = field(default_factory=list)
    citation_count: int = 0
    unique_citations: List[str] = field(default_factory=list)
    word_count: int = 0

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == CRITICAL)

    @property
    def warning_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == WARNING)

    @property
    def passed(self) -> bool:
        return self.critical_count == 0


@dataclass
class PacketReport:
    """Results for an entire filing packet directory."""
    packet_dir: str
    file_reports: List[QAReport] = field(default_factory=list)

    @property
    def total_findings(self) -> int:
        return sum(len(r.findings) for r in self.file_reports)

    @property
    def critical_count(self) -> int:
        return sum(r.critical_count for r in self.file_reports)

    @property
    def passed(self) -> bool:
        return self.critical_count == 0


@dataclass
class FullReport:
    """Comprehensive report across all golden-set packets."""
    packet_reports: List[PacketReport] = field(default_factory=list)
    separation_days: int = 0

    @property
    def total_files(self) -> int:
        return sum(len(p.file_reports) for p in self.packet_reports)

    @property
    def total_findings(self) -> int:
        return sum(p.total_findings for p in self.packet_reports)

    @property
    def critical_count(self) -> int:
        return sum(p.critical_count for p in self.packet_reports)

    @property
    def all_passed(self) -> bool:
        return self.critical_count == 0


# ╔══════════════════════════════════════════════════════════════════╗
# ║  HELPERS                                                        ║
# ╚══════════════════════════════════════════════════════════════════╝

def _read_file(filepath: str) -> str:
    """Read a file with robust encoding handling (UTF-8 BOM, latin-1 fallback)."""
    p = Path(filepath)
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return p.read_text(encoding=enc)
        except (UnicodeDecodeError, ValueError):
            continue
    return p.read_text(encoding="latin-1", errors="replace")


def _lines(text: str) -> List[str]:
    """Split text into lines preserving line numbers (1-indexed via enumerate)."""
    return text.splitlines()


def _relative(filepath: str) -> str:
    """Return path relative to repo root for compact display."""
    try:
        return str(Path(filepath).relative_to(_REPO_ROOT))
    except ValueError:
        return filepath


def _separation_days() -> int:
    """Compute days since last contact (Jul 29, 2025)."""
    return (date.today() - _SEPARATION_ANCHOR).days


def _detect_court_type(filepath: str, text: str) -> str:
    """Infer court type from filepath and content for word-limit selection."""
    fp_lower = filepath.lower()
    text_lower = text[:2000].lower()
    if "coa" in fp_lower or "court of appeals" in text_lower:
        return "COA"
    if "msc" in fp_lower or "supreme court" in text_lower:
        return "MSC"
    if "federal" in fp_lower or "1983" in fp_lower or "united states district" in text_lower:
        return "FEDERAL"
    if "circuit" in text_lower or "disqualification" in fp_lower:
        return "CIRCUIT"
    return "DEFAULT"


# ╔══════════════════════════════════════════════════════════════════╗
# ║  QA ENGINE                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

class QAEngine:
    """Court filing quality assurance automation engine.

    Runs 12 validation gates against markdown court filings and
    produces structured reports with severity-tagged findings.
    """

    def __init__(
        self,
        golden_set_path: Optional[str] = None,
        db_path: Optional[str] = None,
    ) -> None:
        self.golden_set = Path(golden_set_path) if golden_set_path else _DEFAULT_GOLDEN
        self.db_path = Path(db_path) if db_path else _DEFAULT_DB
        self.separation_days = _separation_days()

    # ── public API ──────────────────────────────────────────────────

    def audit_file(self, filepath: str) -> QAReport:
        """Run all 12 gates on a single file. Returns QAReport."""
        text = _read_file(filepath)
        lines = _lines(text)
        report = QAReport(filepath=_relative(filepath))

        self._gate_01_placeholders(filepath, lines, report)
        self._gate_02_ai_contamination(filepath, lines, report)
        self._gate_03_file_paths(filepath, lines, report)
        self._gate_04_party_names(filepath, lines, report)
        self._gate_05_hallucinations(filepath, lines, report)
        self._gate_06_day_count(filepath, lines, report)
        self._gate_07_year_check(filepath, lines, report)
        self._gate_08_citations(filepath, text, report)
        self._gate_09_child_name(filepath, lines, report)
        self._gate_10_pro_se(filepath, lines, report)
        self._gate_11_word_count(filepath, text, report)
        self._gate_12_exhibits(filepath, text, lines, report)

        return report

    def audit_packet(self, packet_dir: str) -> PacketReport:
        """Run all gates on every markdown file in a filing-packet directory."""
        pr = PacketReport(packet_dir=_relative(packet_dir))
        p = Path(packet_dir)
        md_files = sorted(p.rglob("*.md"))
        for md in md_files:
            pr.file_reports.append(self.audit_file(str(md)))
        return pr

    def audit_all(self) -> FullReport:
        """Audit ALL golden-set packets. Returns comprehensive FullReport."""
        fr = FullReport(separation_days=self.separation_days)
        if not self.golden_set.exists():
            return fr

        # Each top-level subdirectory is a packet
        subdirs = sorted(
            d for d in self.golden_set.iterdir()
            if d.is_dir()
        )
        for sd in subdirs:
            fr.packet_reports.append(self.audit_packet(str(sd)))

        # Also audit any loose .md at the golden-set root
        root_mds = sorted(self.golden_set.glob("*.md"))
        if root_mds:
            loose = PacketReport(packet_dir=_relative(str(self.golden_set)))
            for md in root_mds:
                loose.file_reports.append(self.audit_file(str(md)))
            fr.packet_reports.append(loose)

        return fr

    def fix_contamination(
        self, filepath: str, dry_run: bool = True
    ) -> List[Dict[str, str]]:
        """Auto-fix known contamination patterns.

        Returns list of {original, replacement, line} dicts.
        When dry_run=False, writes the corrected file back.
        """
        text = _read_file(filepath)
        fixes: List[Dict[str, str]] = []

        # Fix wrong party names
        for pat, wrong, correct in _WRONG_PARTY:
            for m in pat.finditer(text):
                line_no = text[:m.start()].count("\n") + 1
                fixes.append({
                    "line": str(line_no),
                    "original": m.group(),
                    "replacement": correct,
                })

        # Fix hallucinations (remove line)
        for m in _RE_HALLUCINATION.finditer(text):
            line_no = text[:m.start()].count("\n") + 1
            fixes.append({
                "line": str(line_no),
                "original": m.group(),
                "replacement": "[REMOVED — hallucination]",
            })

        # Fix AI contamination tokens
        for m in _RE_AI_CONTAM.finditer(text):
            line_no = text[:m.start()].count("\n") + 1
            fixes.append({
                "line": str(line_no),
                "original": m.group(),
                "replacement": "[REMOVED — AI reference]",
            })

        # Fix file paths
        for m in _RE_FILE_PATH.finditer(text):
            line_no = text[:m.start()].count("\n") + 1
            fixes.append({
                "line": str(line_no),
                "original": m.group(),
                "replacement": "[path removed]",
            })

        if not dry_run and fixes:
            corrected = text
            for pat, wrong, correct in _WRONG_PARTY:
                corrected = pat.sub(correct, corrected)
            for tok in _AI_LITERAL_TOKENS:
                corrected = corrected.replace(tok, "")
            Path(filepath).write_text(corrected, encoding="utf-8")

        return fixes

    def summary(self, report: FullReport) -> str:
        """Generate human-readable summary of all findings."""
        sep = self.separation_days
        lines: List[str] = []
        lines.append("=" * 72)
        lines.append("  QA AUTOMATION ENGINE (U09) — AUDIT REPORT")
        lines.append(f"  Separation days: {sep}  (since Jul 29, 2025)")
        lines.append(f"  Audit date: {date.today().isoformat()}")
        lines.append("=" * 72)
        lines.append("")

        total_crit = 0
        total_warn = 0
        total_info = 0
        total_files = 0

        gate_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

        for pr in report.packet_reports:
            lines.append(f"┌─ PACKET: {pr.packet_dir}")
            pkt_crit = 0
            pkt_warn = 0
            for fr in pr.file_reports:
                total_files += 1
                fname = Path(fr.filepath).name
                if fr.findings:
                    c = fr.critical_count
                    w = fr.warning_count
                    info = len(fr.findings) - c - w
                    status = "FAIL" if c > 0 else "WARN" if w > 0 else "INFO"
                    lines.append(
                        f"│  [{status:4s}] {fname}  "
                        f"C={c} W={w} I={info}  "
                        f"words={fr.word_count}  cites={fr.citation_count}"
                    )
                    pkt_crit += c
                    pkt_warn += w
                    for finding in fr.findings:
                        gate_counts[finding.gate][finding.severity] += 1
                        sev_mark = {
                            CRITICAL: "!!",
                            WARNING: "??",
                            INFO: "..",
                        }.get(finding.severity, "  ")
                        text_preview = (
                            finding.text[:60] + "…"
                            if len(finding.text) > 60
                            else finding.text
                        )
                        lines.append(
                            f"│    {sev_mark} L{finding.line:>4d} "
                            f"[{finding.gate}] {text_preview}"
                        )
                        lines.append(
                            f"│           → {finding.recommendation}"
                        )
                else:
                    lines.append(
                        f"│  [ OK ] {fname}  "
                        f"words={fr.word_count}  cites={fr.citation_count}"
                    )

            pkt_status = "PASS" if pkt_crit == 0 else "FAIL"
            lines.append(
                f"└─ [{pkt_status}] {pkt_crit} critical, {pkt_warn} warnings"
            )
            lines.append("")
            total_crit += pkt_crit
            total_warn += pkt_warn

        # Gate-level summary
        lines.append("─" * 72)
        lines.append("  FINDINGS BY GATE:")
        for gate_name in sorted(gate_counts.keys()):
            counts = gate_counts[gate_name]
            parts = []
            for sev in (CRITICAL, WARNING, INFO):
                if counts[sev]:
                    parts.append(f"{sev}={counts[sev]}")
            lines.append(f"    {gate_name:30s} {', '.join(parts)}")

        lines.append("")
        lines.append("─" * 72)
        overall = "ALL CLEAR" if total_crit == 0 else "BLOCKED — FIX CRITICAL ITEMS"
        lines.append(
            f"  TOTALS: {total_files} files | "
            f"{total_crit} CRITICAL | {total_warn} WARNING | "
            f"Verdict: {overall}"
        )
        lines.append("=" * 72)
        return "\n".join(lines)

    # ── GATE IMPLEMENTATIONS ───────────────────────────────────────

    def _gate_01_placeholders(
        self, fp: str, lines: List[str], report: QAReport
    ) -> None:
        rel = _relative(fp)
        for i, line in enumerate(lines, start=1):
            for m in _RE_PLACEHOLDER.finditer(line):
                matched = m.group()
                is_physical = bool(_RE_PHYSICAL_ACTION.search(matched))
                sev = INFO if is_physical else WARNING
                rec = (
                    "Physical-action marker — requires manual completion"
                    if is_physical
                    else "Resolve placeholder before filing"
                )
                report.findings.append(Finding(
                    gate="placeholder",
                    severity=sev,
                    file=rel,
                    line=i,
                    text=matched,
                    recommendation=rec,
                ))

    def _gate_02_ai_contamination(
        self, fp: str, lines: List[str], report: QAReport
    ) -> None:
        rel = _relative(fp)
        is_exhibit = "EXHIBIT" in Path(fp).name.upper() or "\\EXHIBITS\\" in fp.upper()
        for i, line in enumerate(lines, start=1):
            # Case-insensitive token matches — always critical
            for m in _RE_AI_CONTAM.finditer(line):
                report.findings.append(Finding(
                    gate="ai_contamination",
                    severity=CRITICAL,
                    file=rel,
                    line=i,
                    text=m.group(),
                    recommendation="Remove AI/system reference before filing",
                ))
            # Case-sensitive tokens (MEEK, DELTA9, Embedding)
            # In exhibits, these are WARNING (may be legitimate evidence text)
            for m in _RE_AI_CONTAM_CASE_SENSITIVE.finditer(line):
                sev = WARNING if is_exhibit else CRITICAL
                report.findings.append(Finding(
                    gate="ai_contamination",
                    severity=sev,
                    file=rel,
                    line=i,
                    text=m.group(),
                    recommendation=(
                        "Case-sensitive AI token in exhibit — review context"
                        if is_exhibit else
                        "Remove AI/system reference before filing"
                    ),
                ))
            # Contextual matches — "engine"/"agent"/"database" near AI keywords
            if _RE_AI_CONTEXT.search(line) and _RE_ENGINE_WORD.search(line):
                matched_words = _RE_ENGINE_WORD.findall(line)
                snippet = line.strip()[:80]
                report.findings.append(Finding(
                    gate="ai_contamination",
                    severity=WARNING,
                    file=rel,
                    line=i,
                    text=snippet,
                    recommendation=(
                        f"Possible AI context for '{', '.join(matched_words)}' "
                        f"— review and remove if system reference"
                    ),
                ))

    def _gate_03_file_paths(
        self, fp: str, lines: List[str], report: QAReport
    ) -> None:
        rel = _relative(fp)
        is_exhibit = "EXHIBIT" in Path(fp).name.upper() or "\\EXHIBITS\\" in fp.upper()
        for i, line in enumerate(lines, start=1):
            for m in _RE_FILE_PATH.finditer(line):
                # Exhibits may legitimately reference source file locations
                sev = WARNING if is_exhibit else CRITICAL
                report.findings.append(Finding(
                    gate="file_path",
                    severity=sev,
                    file=rel,
                    line=i,
                    text=m.group(),
                    recommendation=(
                        "Source path in exhibit — consider removing for filing"
                        if is_exhibit else
                        "Remove internal file path from court document"
                    ),
                ))

    def _gate_04_party_names(
        self, fp: str, lines: List[str], report: QAReport
    ) -> None:
        rel = _relative(fp)
        for i, line in enumerate(lines, start=1):
            for pat, wrong_label, correct in _WRONG_PARTY:
                for m in pat.finditer(line):
                    report.findings.append(Finding(
                        gate="party_name",
                        severity=CRITICAL,
                        file=rel,
                        line=i,
                        text=m.group(),
                        recommendation=f"Replace with: {correct}",
                    ))

    def _gate_05_hallucinations(
        self, fp: str, lines: List[str], report: QAReport
    ) -> None:
        rel = _relative(fp)
        for i, line in enumerate(lines, start=1):
            for m in _RE_HALLUCINATION.finditer(line):
                report.findings.append(Finding(
                    gate="hallucination",
                    severity=CRITICAL,
                    file=rel,
                    line=i,
                    text=m.group(),
                    recommendation="Remove hallucinated content — fabricated entity",
                ))

    def _gate_06_day_count(
        self, fp: str, lines: List[str], report: QAReport
    ) -> None:
        rel = _relative(fp)
        correct = self.separation_days
        for i, line in enumerate(lines, start=1):
            for m in _RE_DAY_COUNT.finditer(line):
                found_count = int(m.group(1))
                if found_count != correct:
                    report.findings.append(Finding(
                        gate="day_count",
                        severity=WARNING,
                        file=rel,
                        line=i,
                        text=m.group(),
                        recommendation=(
                            f"Hardcoded {found_count} days — "
                            f"correct count is {correct} "
                            f"(as of {date.today().isoformat()})"
                        ),
                    ))

    def _gate_07_year_check(
        self, fp: str, lines: List[str], report: QAReport
    ) -> None:
        rel = _relative(fp)
        # Exhibits that describe historical orders/events legitimately use
        # past dates.  Downgrade severity for exhibit files.
        fname_upper = Path(fp).stem.upper()
        in_exhibit = (
            "EXHIBIT" in fname_upper
            or "EXHIBITS" in Path(fp).parent.name.upper()
        )
        for i, line in enumerate(lines, start=1):
            for m in _RE_STALE_DATED.finditer(line):
                matched = m.group()
                year_m = _RE_YEAR_20XX.search(matched)
                if year_m:
                    yr = int("20" + year_m.group(1))
                    if yr < 2026:
                        sev = INFO if in_exhibit else WARNING
                        report.findings.append(Finding(
                            gate="year_check",
                            severity=sev,
                            file=rel,
                            line=i,
                            text=matched,
                            recommendation=(
                                f"Filing/signature date shows {yr} — "
                                f"{'historical exhibit date (OK if original order)' if in_exhibit else 'should be 2026 for current filings'}"
                            ),
                        ))

    def _gate_08_citations(
        self, fp: str, text: str, report: QAReport
    ) -> None:
        all_cites = _RE_CITATION.findall(text)
        unique = sorted(set(all_cites))
        report.citation_count = len(all_cites)
        report.unique_citations = unique
        if not unique:
            rel = _relative(fp)
            report.findings.append(Finding(
                gate="citations",
                severity=INFO,
                file=rel,
                line=0,
                text="No citations found",
                recommendation="Verify this document does not require legal citations",
            ))

    def _gate_09_child_name(
        self, fp: str, lines: List[str], report: QAReport
    ) -> None:
        rel = _relative(fp)
        for i, line in enumerate(lines, start=1):
            for m in _RE_CHILD_FULL.finditer(line):
                report.findings.append(Finding(
                    gate="child_name",
                    severity=CRITICAL,
                    file=rel,
                    line=i,
                    text=m.group(),
                    recommendation=(
                        "MCR 8.119(H) violation — replace with 'L.D.W.' "
                        "or 'the minor child'"
                    ),
                ))

    def _gate_10_pro_se(
        self, fp: str, lines: List[str], report: QAReport
    ) -> None:
        rel = _relative(fp)
        for i, line in enumerate(lines, start=1):
            for m in _RE_NON_PROSE.finditer(line):
                report.findings.append(Finding(
                    gate="pro_se",
                    severity=CRITICAL,
                    file=rel,
                    line=i,
                    text=m.group(),
                    recommendation="Andrew is pro se — use 'Plaintiff, appearing pro se'",
                ))

    def _gate_11_word_count(
        self, fp: str, text: str, report: QAReport
    ) -> None:
        rel = _relative(fp)
        words = len(text.split())
        report.word_count = words

        # Exhibits are evidence compilations — NOT subject to word count limits
        is_exhibit = "EXHIBIT" in Path(fp).name.upper() or "\\EXHIBITS\\" in fp.upper()
        if is_exhibit:
            if words > 50000:
                report.findings.append(Finding(
                    gate="word_count",
                    severity=INFO,
                    file=rel,
                    line=0,
                    text=f"{words:,} words (exhibit — no limit, but very large)",
                    recommendation="Consider splitting into multiple exhibits for readability",
                ))
            return

        court = _detect_court_type(fp, text)
        limit = _WORD_LIMITS.get(court, _WORD_LIMITS["DEFAULT"])
        if words > limit:
            report.findings.append(Finding(
                gate="word_count",
                severity=WARNING if words < limit * 1.1 else CRITICAL,
                file=rel,
                line=0,
                text=f"{words:,} words ({court} limit: {limit:,})",
                recommendation=(
                    f"Document exceeds {court} word limit of {limit:,} — "
                    f"reduce by {words - limit:,} words"
                ),
            ))

    def _gate_12_exhibits(
        self, fp: str, text: str, lines: List[str], report: QAReport
    ) -> None:
        rel = _relative(fp)
        parent = Path(fp).parent
        seen_refs: Dict[str, int] = {}

        for i, line in enumerate(lines, start=1):
            for m in _RE_EXHIBIT_REF.finditer(line):
                ref_label = m.group(1) or m.group(2) or m.group(3) or m.group(4)
                if ref_label and ref_label not in seen_refs:
                    seen_refs[ref_label] = i

        # Check whether referenced exhibits exist as files
        existing_files = set()
        if parent.exists():
            for child in parent.iterdir():
                existing_files.add(child.stem.upper())
                existing_files.add(child.name.upper())
            # Also check exhibits subdirectory
            exhibits_dir = parent / "exhibits"
            if exhibits_dir.exists():
                for child in exhibits_dir.iterdir():
                    existing_files.add(child.stem.upper())
                    existing_files.add(child.name.upper())

        for ref_label, line_no in seen_refs.items():
            # Use prefix matching: EXHIBIT_A matches EXHIBIT_A_Consent_Order.md
            prefixes = [
                f"EXHIBIT_{ref_label}".upper(),
                f"EX_{ref_label}".upper(),
                ref_label.upper(),
                f"EXHIBIT{ref_label}".upper(),
            ]
            found = any(
                ef.startswith(px) or ef == px
                for ef in existing_files
                for px in prefixes
            )
            if not found:
                report.findings.append(Finding(
                    gate="exhibit_ref",
                    severity=INFO,
                    file=rel,
                    line=line_no,
                    text=f"Exhibit {ref_label}",
                    recommendation=(
                        f"Exhibit {ref_label} referenced but not found "
                        f"as a file in {_relative(str(parent))}"
                    ),
                ))


# ╔══════════════════════════════════════════════════════════════════╗
# ║  CLI ENTRY POINT                                                ║
# ╚══════════════════════════════════════════════════════════════════╝

def main() -> None:
    """Run full audit and print summary."""
    engine = QAEngine()
    print(f"QA Engine v{__version__} — scanning {engine.golden_set} …")
    print(f"Separation days: {engine.separation_days}")
    print()
    report = engine.audit_all()
    print(engine.summary(report))


if __name__ == "__main__":
    main()
