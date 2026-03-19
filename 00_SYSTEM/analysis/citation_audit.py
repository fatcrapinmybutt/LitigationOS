#!/usr/bin/env python3
"""
MBP LitigationOS — Deep Citation Audit
=======================================
Scans all .md files in 04_COURT_FILINGS, extracts every legal citation,
verifies against litigation_context.db (auth_rules, master_citations),
categorises each as VERIFIED / PARTIAL / UNVERIFIED / PHANTOM,
auto-fixes clear typos in-place, and writes a full audit report.

Usage:
    python citation_audit.py            # run full audit
    python citation_audit.py --dry-run  # report only, no in-place fixes
"""
from __future__ import annotations

import os
import re
import sqlite3
import sys
from collections import defaultdict
from difflib import get_close_matches
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ── Paths ──────────────────────────────────────────────────────────
FILINGS_DIR = Path(r"C:\Users\andre\LitigationOS\04_COURT_FILINGS")
DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\litigation_context.db",
)
REPORT_PATH = Path(r"C:\Users\andre\LitigationOS\06_ANALYSIS\citation_audit_report.md")

# ── Citation regex patterns ────────────────────────────────────────
# MCR X.XXX  (e.g. MCR 2.003, MCR 7.204(A)(1))
RE_MCR = re.compile(r'\bMCR\s+(\d{1,2}\.\d{2,4}(?:\([A-Za-z0-9]+\))*)', re.I)
# MCL XXX.XXX (e.g. MCL 722.23, MCL 600.2950a)
RE_MCL = re.compile(r'\bMCL\s+(\d{2,4}\.\d{1,6}[a-z]?(?:\([A-Za-z0-9]+\))*)', re.I)
# MRE XXX (e.g. MRE 803, MRE 401)
RE_MRE = re.compile(r'\bMRE\s+(\d{2,4}(?:\([A-Za-z0-9]+\))*)', re.I)
# Case citations: Name v Name, NNN Mich (App)? NNN (YYYY)
RE_CASE = re.compile(
    r'([A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+)*'
    r'\s+v\s+'
    r'[A-Z][A-Za-z\'\-]+(?:\s+[A-Za-z\'\-]+)*)'
    r'(?:,?\s*(\d{1,3}\s+Mich(?:\s+App)?\s+\d{1,4}))?'
    r'(?:\s*\((\d{4})\))?'
)
# Numeric Mich cite without case name: 123 Mich App 456
RE_MICH_CITE = re.compile(r'\b(\d{1,3}\s+Mich(?:\s+App)?\s+\d{1,4})\b')


# ── Category labels ───────────────────────────────────────────────
VERIFIED = "VERIFIED"
PARTIAL = "PARTIAL"
UNVERIFIED = "UNVERIFIED"
PHANTOM = "PHANTOM"

# Well-known Michigan statutes / rules that exist even if not in our DB.
# These should NEVER be auto-fixed by fuzzy matching.
KNOWN_VALID = {
    "MCL": {
        "722.23", "722.24", "722.25", "722.26", "722.27", "722.27b", "722.27c",
        "722.28", "722.31", "600.601", "600.605", "600.701", "600.705",
        "600.1561", "600.1629", "600.1701", "600.1715", "600.1721",
        "600.2301", "600.2921", "600.2963", "600.6301", "600.6304",
        "750.81", "750.81a", "750.136b", "750.145", "750.411h", "750.411i",
        "750.423", "750.520b", "750.520c", "750.520d",
        "552.501", "552.505", "552.507", "552.511", "552.517",
        "691.1401", "691.1407",
    },
    "MCR": {
        "1.105", "1.109", "2.003", "2.102", "2.103", "2.104", "2.105",
        "2.107", "2.110", "2.111", "2.112", "2.113", "2.114", "2.116",
        "2.119", "2.301", "2.302", "2.306", "2.309", "2.310", "2.313",
        "2.314", "2.316", "2.401", "2.403", "2.404", "2.405", "2.501",
        "2.506", "2.507", "2.508", "2.509", "2.510", "2.511", "2.512",
        "2.513", "2.514", "2.515", "2.516", "2.517", "2.612",
        "3.206", "3.210", "3.211", "3.214", "3.215", "3.302",
        "3.602", "3.606", "3.613", "3.615", "3.903", "3.915", "3.920",
        "3.921", "3.922", "3.925", "3.956", "3.961", "3.965", "3.972",
        "3.975", "3.977",
        "7.101", "7.201", "7.202", "7.203", "7.204", "7.205", "7.206",
        "7.208", "7.210", "7.211", "7.212", "7.215", "7.301", "7.302",
        "7.303", "7.305", "7.306", "7.307", "7.308",
    },
    "MRE": {
        "101", "102", "103", "104", "105", "106",
        "201", "301", "401", "402", "403", "404", "405", "406",
        "501", "601", "602", "611", "612", "613", "614", "615",
        "701", "702", "703", "704", "705",
        "801", "802", "803", "804", "805", "806",
        "901", "902", "903", "1001", "1002", "1003", "1004", "1005",
        "1006", "1007", "1008", "1101",
    },
}


class CitationAuditor:
    """Audit and verify legal citations across court filings."""

    def __init__(self, db_path: str = DB_PATH, dry_run: bool = False):
        self.dry_run = dry_run
        self.conn = sqlite3.connect(db_path, timeout=30)
        self.conn.row_factory = sqlite3.Row
        self._rule_numbers: set[str] = set()
        self._rule_numbers_with_text: set[str] = set()
        self._mcl_numbers: set[str] = set()
        self._mre_numbers: set[str] = set()
        self._case_cites: set[str] = set()
        self._all_rule_numbers: list[str] = []  # for fuzzy matching
        self._load_known_citations()

    def _load_known_citations(self):
        """Pre-load all known rule numbers for fast lookup."""
        # auth_rules
        try:
            rows = self.conn.execute(
                "SELECT rule_number, rule_type, full_text FROM auth_rules"
            ).fetchall()
            for r in rows:
                rn = r["rule_number"] or ""
                rt = (r["rule_type"] or "").upper()
                has_text = bool(r["full_text"] and len(r["full_text"]) > 20)
                self._all_rule_numbers.append(rn)
                if rt == "MCR":
                    self._rule_numbers.add(rn)
                    if has_text:
                        self._rule_numbers_with_text.add(rn)
                elif rt == "MCL":
                    self._mcl_numbers.add(rn)
                    if has_text:
                        self._rule_numbers_with_text.add(rn)
                elif rt == "MRE":
                    self._mre_numbers.add(rn)
                    if has_text:
                        self._rule_numbers_with_text.add(rn)
        except Exception:
            pass

        # master_citations for case law
        try:
            rows = self.conn.execute(
                "SELECT DISTINCT citation FROM master_citations WHERE cite_type = 'CASE_LAW'"
            ).fetchall()
            for r in rows:
                self._case_cites.add((r["citation"] or "").strip())
        except Exception:
            pass

    def _strip_subsection(self, num: str) -> str:
        """Strip parenthetical subsections: 2.003(C)(1) -> 2.003"""
        return re.sub(r'\([^)]*\)', '', num).strip()

    def _check_mcr(self, num: str) -> Tuple[str, Optional[str]]:
        """Classify an MCR citation. Returns (category, suggestion)."""
        base = self._strip_subsection(num)
        if base in self._rule_numbers:
            if base in self._rule_numbers_with_text:
                return VERIFIED, None
            return PARTIAL, None
        # Known-valid rules not in our DB → UNVERIFIED, never PHANTOM
        if base in KNOWN_VALID["MCR"]:
            return UNVERIFIED, None
        # Tight fuzzy match (cutoff 0.92) — only obvious typos
        close = get_close_matches(base, list(self._rule_numbers), n=1, cutoff=0.92)
        if close:
            return PHANTOM, f"MCR {close[0]}"
        return UNVERIFIED, None

    def _check_mcl(self, num: str) -> Tuple[str, Optional[str]]:
        """Classify an MCL citation."""
        base = self._strip_subsection(num)
        # Direct match in auth_rules MCL
        if base in self._mcl_numbers:
            if base in self._rule_numbers_with_text:
                return VERIFIED, None
            return PARTIAL, None
        # Also check rules_text table
        try:
            row = self.conn.execute(
                "SELECT rule, context FROM rules_text WHERE rule LIKE ? LIMIT 1",
                (f"%{base}%",),
            ).fetchone()
            if row:
                if row["context"] and len(row["context"]) > 20:
                    return VERIFIED, None
                return PARTIAL, None
        except Exception:
            pass
        # Known-valid statutes not in our DB → UNVERIFIED, never PHANTOM
        if base in KNOWN_VALID["MCL"]:
            return UNVERIFIED, None
        close = get_close_matches(base, list(self._mcl_numbers), n=1, cutoff=0.92)
        if close:
            return PHANTOM, f"MCL {close[0]}"
        return UNVERIFIED, None

    def _check_mre(self, num: str) -> Tuple[str, Optional[str]]:
        """Classify an MRE citation."""
        base = self._strip_subsection(num)
        if base in self._mre_numbers:
            if base in self._rule_numbers_with_text:
                return VERIFIED, None
            return PARTIAL, None
        if base in KNOWN_VALID["MRE"]:
            return UNVERIFIED, None
        close = get_close_matches(base, list(self._mre_numbers), n=1, cutoff=0.92)
        if close:
            return PHANTOM, f"MRE {close[0]}"
        return UNVERIFIED, None

    def _check_case(self, cite_text: str) -> Tuple[str, Optional[str]]:
        """Classify a case citation against master_citations."""
        ct = cite_text.strip()
        if ct in self._case_cites:
            return VERIFIED, None
        # Partial match: search DB
        try:
            first_word = ct.split()[0] if ct else ""
            row = self.conn.execute(
                "SELECT citation, context FROM master_citations "
                "WHERE cite_type = 'CASE_LAW' AND citation LIKE ? LIMIT 1",
                (f"%{first_word}%",),
            ).fetchone()
            if row:
                return PARTIAL, None
        except Exception:
            pass
        return UNVERIFIED, None

    def scan_file(self, filepath: Path) -> List[dict]:
        """Extract and classify every citation in a single .md file."""
        try:
            text = filepath.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return []

        results: list[dict] = []

        # MCR
        for m in RE_MCR.finditer(text):
            num = m.group(1)
            cat, suggestion = self._check_mcr(num)
            results.append({
                "file": str(filepath),
                "type": "MCR",
                "citation": f"MCR {num}",
                "raw_num": num,
                "category": cat,
                "suggestion": suggestion,
                "offset": m.start(),
                "line": text[:m.start()].count('\n') + 1,
            })

        # MCL
        for m in RE_MCL.finditer(text):
            num = m.group(1)
            cat, suggestion = self._check_mcl(num)
            results.append({
                "file": str(filepath),
                "type": "MCL",
                "citation": f"MCL {num}",
                "raw_num": num,
                "category": cat,
                "suggestion": suggestion,
                "offset": m.start(),
                "line": text[:m.start()].count('\n') + 1,
            })

        # MRE
        for m in RE_MRE.finditer(text):
            num = m.group(1)
            cat, suggestion = self._check_mre(num)
            results.append({
                "file": str(filepath),
                "type": "MRE",
                "citation": f"MRE {num}",
                "raw_num": num,
                "category": cat,
                "suggestion": suggestion,
                "offset": m.start(),
                "line": text[:m.start()].count('\n') + 1,
            })

        # Case citations (Mich cites)
        for m in RE_MICH_CITE.finditer(text):
            cite = m.group(1).strip()
            cat, suggestion = self._check_case(cite)
            results.append({
                "file": str(filepath),
                "type": "CASE_LAW",
                "citation": cite,
                "raw_num": cite,
                "category": cat,
                "suggestion": suggestion,
                "offset": m.start(),
                "line": text[:m.start()].count('\n') + 1,
            })

        return results

    def auto_fix(self, filepath: Path, findings: List[dict]) -> int:
        """Fix PHANTOM citations in-place where a clear suggestion exists."""
        if self.dry_run:
            return 0

        phantoms = [f for f in findings if f["category"] == PHANTOM and f["suggestion"] and f["file"] == str(filepath)]
        if not phantoms:
            return 0

        try:
            text = filepath.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return 0

        fixes = 0
        # Sort by offset descending to preserve positions during replacement
        for p in sorted(phantoms, key=lambda x: x["offset"], reverse=True):
            old = p["citation"]
            new = p["suggestion"]
            # Only fix if the old citation appears exactly at the expected location
            if text[p["offset"]:p["offset"] + len(old)] == old:
                text = text[:p["offset"]] + new + text[p["offset"] + len(old):]
                fixes += 1
                p["fixed"] = True

        if fixes > 0:
            filepath.write_text(text, encoding="utf-8")

        return fixes

    def run_audit(self) -> dict:
        """Run the full audit across all .md files in FILINGS_DIR."""
        md_files = sorted(FILINGS_DIR.rglob("*.md"))
        all_findings: list[dict] = []
        files_scanned = 0
        total_fixes = 0

        for fp in md_files:
            findings = self.scan_file(fp)
            if findings:
                all_findings.extend(findings)
                fixed = self.auto_fix(fp, findings)
                total_fixes += fixed
            files_scanned += 1

        # Deduplicate by (citation, file)
        seen = set()
        unique: list[dict] = []
        for f in all_findings:
            key = (f["citation"], f["file"], f["line"])
            if key not in seen:
                seen.add(key)
                unique.append(f)

        # Aggregate stats
        by_category: dict[str, int] = defaultdict(int)
        by_type: dict[str, int] = defaultdict(int)
        for f in unique:
            by_category[f["category"]] += 1
            by_type[f["type"]] += 1

        return {
            "files_scanned": files_scanned,
            "total_citations": len(unique),
            "by_category": dict(by_category),
            "by_type": dict(by_type),
            "total_fixes": total_fixes,
            "findings": unique,
        }

    def generate_report(self, audit_result: dict) -> str:
        """Generate a markdown audit report."""
        findings = audit_result["findings"]
        lines: list[str] = []

        lines.append("# Citation Audit Report — LitigationOS Court Filings")
        lines.append("")
        lines.append(f"**Files scanned:** {audit_result['files_scanned']}")
        lines.append(f"**Total unique citations found:** {audit_result['total_citations']}")
        lines.append(f"**Auto-fixes applied:** {audit_result['total_fixes']}")
        lines.append("")

        # Summary table
        lines.append("## Summary by Category")
        lines.append("")
        lines.append("| Category | Count | Description |")
        lines.append("|----------|-------|-------------|")
        cat_desc = {
            VERIFIED: "In DB with full text",
            PARTIAL: "In DB but incomplete text",
            UNVERIFIED: "Not found in DB",
            PHANTOM: "Suspected typo / non-existent rule",
        }
        for cat in [VERIFIED, PARTIAL, UNVERIFIED, PHANTOM]:
            count = audit_result["by_category"].get(cat, 0)
            lines.append(f"| {cat} | {count} | {cat_desc.get(cat, '')} |")
        lines.append("")

        lines.append("## Summary by Citation Type")
        lines.append("")
        lines.append("| Type | Count |")
        lines.append("|------|-------|")
        for ctype, count in sorted(audit_result["by_type"].items()):
            lines.append(f"| {ctype} | {count} |")
        lines.append("")

        # PHANTOM citations (highest priority)
        phantoms = [f for f in findings if f["category"] == PHANTOM]
        if phantoms:
            lines.append("## ⚠️ PHANTOM Citations (Likely Errors)")
            lines.append("")
            lines.append("| Citation | Suggested Fix | File | Line | Fixed? |")
            lines.append("|----------|--------------|------|------|--------|")
            for p in phantoms:
                rel_file = Path(p["file"]).name
                fixed = "✅" if p.get("fixed") else "❌"
                lines.append(
                    f"| `{p['citation']}` | `{p['suggestion'] or 'N/A'}` "
                    f"| {rel_file} | {p['line']} | {fixed} |"
                )
            lines.append("")

        # UNVERIFIED citations
        unverified = [f for f in findings if f["category"] == UNVERIFIED]
        if unverified:
            lines.append("## ❓ UNVERIFIED Citations (Not in Database)")
            lines.append("")
            lines.append("| Citation | Type | File | Line |")
            lines.append("|----------|------|------|------|")
            # Group and limit
            shown = 0
            for u in unverified:
                if shown >= 200:
                    lines.append(f"| ... | ... | ... | ... |")
                    lines.append(f"| *({len(unverified) - 200} more omitted)* | | | |")
                    break
                rel_file = Path(u["file"]).name
                lines.append(f"| `{u['citation']}` | {u['type']} | {rel_file} | {u['line']} |")
                shown += 1
            lines.append("")

        # VERIFIED citations (summary only)
        verified = [f for f in findings if f["category"] == VERIFIED]
        if verified:
            lines.append("## ✅ VERIFIED Citations")
            lines.append("")
            # Deduplicate by citation text
            unique_verified = sorted(set(v["citation"] for v in verified))
            lines.append(f"**{len(unique_verified)} unique verified citations** across {len(verified)} occurrences:\n")
            for cite in unique_verified[:100]:
                lines.append(f"- `{cite}`")
            if len(unique_verified) > 100:
                lines.append(f"- *... and {len(unique_verified) - 100} more*")
            lines.append("")

        # PARTIAL citations
        partial = [f for f in findings if f["category"] == PARTIAL]
        if partial:
            lines.append("## 🔶 PARTIAL Citations (In DB, Incomplete Text)")
            lines.append("")
            unique_partial = sorted(set(p["citation"] for p in partial))
            for cite in unique_partial[:50]:
                lines.append(f"- `{cite}`")
            if len(unique_partial) > 50:
                lines.append(f"- *... and {len(unique_partial) - 50} more*")
            lines.append("")

        # Per-file breakdown
        lines.append("## Per-File Breakdown")
        lines.append("")
        by_file: dict[str, list[dict]] = defaultdict(list)
        for f in findings:
            by_file[f["file"]].append(f)
        for fp in sorted(by_file.keys()):
            ff = by_file[fp]
            rel = str(Path(fp).relative_to(FILINGS_DIR))
            cats = defaultdict(int)
            for f in ff:
                cats[f["category"]] += 1
            cat_str = ", ".join(f"{c}: {n}" for c, n in sorted(cats.items()))
            lines.append(f"- **{rel}** — {len(ff)} citations ({cat_str})")
        lines.append("")

        lines.append("---")
        lines.append("*Generated by LitigationOS Citation Audit Engine*")
        return "\n".join(lines)


def _revert_known_bad_fixes(filings_dir: Path):
    """Revert known bad auto-fixes from a prior aggressive run.

    The prior run incorrectly replaced real statutes like MCL 722.23 with
    MCL 722.27a, and MCL 600.xxx with MCL 600.5701. This pass undoes those
    specific wrong substitutions by pattern-matching context.
    """
    # Map of (wrong replacement → original value → context hint)
    # We revert "MCL 722.27a" back to "MCL 722.23" where the surrounding
    # context mentions best interest factors (a)-(l)
    revert_count = 0
    for fp in sorted(filings_dir.rglob("*.md")):
        try:
            text = fp.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        original = text

        # Revert MCL 722.27a → MCL 722.23 where context is about best interest factors
        # Pattern: "MCL 722.27a" near factor letters or "best interest"
        # The prior script replaced "MCL 722.23(X)" with "MCL 722.27a" (losing subsection)
        # and "MCL 722.23" with "MCL 722.27a" in factor analysis contexts.
        # Since MCL 722.27a is the parenting-time statute and may appear legitimately,
        # we only revert where it appears in factor-analysis patterns.
        lines = text.split('\n')
        new_lines = []
        for line in lines:
            new_line = line
            # Pattern: "Factor (X) - MCL 722.27a" or "MCL 722.27a(X)" near factor text
            # Revert lines that discuss specific factors (a)-(l) with 722.27a
            if 'MCL 722.27a' in line or 'MCL 722.27a' in line:
                lower = line.lower()
                # Context: best interest factor discussion
                if any(hint in lower for hint in [
                    'best interest', 'factor (', 'factor(', 'factors',
                    'love, affection', 'emotional ties', 'custodial environment',
                    'moral fitness', 'mental and physical health',
                    'community record', 'preference of the child',
                    'willingness to facilitate', 'domestic violence',
                    '722.23', 'child custody act',
                ]):
                    new_line = line.replace('MCL 722.27a', 'MCL 722.23')
            new_lines.append(new_line)
        text = '\n'.join(new_lines)

        if text != original:
            fp.write_text(text, encoding="utf-8")
            changes = sum(1 for a, b in zip(original.split('\n'), text.split('\n')) if a != b)
            revert_count += changes

    return revert_count


def main():
    dry_run = "--dry-run" in sys.argv
    print(f"[CITATION AUDIT] Scanning {FILINGS_DIR} ...")
    print(f"[CITATION AUDIT] DB: {DB_PATH}")
    print(f"[CITATION AUDIT] Mode: {'DRY RUN' if dry_run else 'LIVE (will fix phantoms)'}")

    # Revert any bad fixes from prior aggressive runs
    reverted = _revert_known_bad_fixes(FILINGS_DIR)
    if reverted:
        print(f"[CITATION AUDIT] Reverted {reverted} bad fixes from prior run")

    auditor = CitationAuditor(dry_run=dry_run)
    result = auditor.run_audit()

    print(f"\n[RESULTS]")
    print(f"  Files scanned:    {result['files_scanned']}")
    print(f"  Total citations:  {result['total_citations']}")
    print(f"  By category:      {result['by_category']}")
    print(f"  By type:          {result['by_type']}")
    print(f"  Auto-fixes:       {result['total_fixes']}")

    report = auditor.generate_report(result)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"\n[REPORT] Written to {REPORT_PATH}")


if __name__ == "__main__":
    main()
