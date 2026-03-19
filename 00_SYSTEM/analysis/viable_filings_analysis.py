#!/usr/bin/env python3
"""
viable_filings_analysis.py
==========================
Scans all court filings in 04_COURT_FILINGS, analyzes each for completeness,
cross-references the litigation DB, performs gap analysis per case lane,
and generates a Markdown report + DB table.

Usage:
    python viable_filings_analysis.py
"""

from __future__ import annotations

import hashlib
import os
import re
import sqlite3
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ── Paths ────────────────────────────────────────────────────────────
BASE = Path(r"C:\Users\andre\LitigationOS")
FILINGS_DIR = BASE / "04_COURT_FILINGS"
DB_PATH = Path(r"C:\Users\andre\litigation_context.db")
REPORT_PATH = BASE / "06_ANALYSIS" / "viable_filings_report.md"

# ── Constants ────────────────────────────────────────────────────────
FILING_TYPE_KEYWORDS = {
    "motion": r"\bmotion\b",
    "brief": r"\bbrief\b",
    "complaint": r"\bcomplaint\b",
    "affidavit": r"\baffidavit\b",
    "response": r"\bresponse\b",
    "petition": r"\bpetition\b",
    "application": r"\bapplication\b",
    "exhibit": r"\bexhibit\b",
    "order": r"\b(proposed.?order|order)\b",
    "memorandum": r"\b(memorandum|memo)\b",
    "grievance": r"\bgrievance\b",
    "referral": r"\breferral\b",
    "checklist": r"\bchecklist\b",
    "template": r"\btemplate\b",
    "narrative": r"\bnarrative\b",
    "timeline": r"\btimeline\b",
    "table_of_authorities": r"\btable.of.authorities\b",
    "foia": r"\bfoia\b",
    "ifp_affidavit": r"\bin.forma.pauperis\b",
    "proof_of_service": r"\bproof.of.service\b",
    "strategy": r"\bstrategy\b",
    "inventory": r"\binventory\b",
    "index": r"\b(master.?exhibit.?index|exhibit.?index)\b",
}

COURT_PATTERNS = {
    "14th_Circuit": [
        r"14th.*circuit", r"14TH_CIRCUIT", r"muskegon.*county",
        r"2024-001507-DC", r"2023-5907-PP",
    ],
    "COA": [
        r"court\s+of\s+appeals", r"\bCOA\b", r"02_COA", r"366810",
        r"MCR\s*7\.", r"leave\s+to\s+appeal",
    ],
    "JTC": [
        r"judicial\s+tenure", r"\bJTC\b", r"03_JTC", r"misconduct",
    ],
    "MSC": [
        r"supreme\s+court", r"\bMSC\b", r"04_MSC",
        r"superintending\s+control",
    ],
    "USDC": [
        r"district\s+court", r"\bUSDC\b", r"05_USDC",
        r"42\s*U\.?S\.?C", r"§\s*1983", r"western\s+district",
    ],
}

CITATION_PATTERNS = {
    "MCR": r"MCR\s+[\d]+\.[\d]+(?:\([A-Za-z0-9]+\))*",
    "MCL": r"MCL\s+[\d]+\.[\d]+[a-z]*(?:\([A-Za-z0-9]+\))*",
    "MRE": r"MRE\s+[\d]+",
    "case_law": (
        r"(?:\d+\s+(?:Mich(?:\s*App)?|NW2d|NW\.?2d|US|S\.?\s*Ct)"
        r"\s+\d+)|"
        r"(?:[A-Z][a-z]+\s+v\.?\s+[A-Z][a-z]+)"
    ),
    "USC": r"\d+\s+U\.?S\.?C\.?\s*§?\s*\d+",
    "CFR": r"\d+\s+C\.?F\.?R\.?\s*§?\s*[\d.]+",
    "canon": r"(?:Canon|CANON)\s+\d+",
}

PLACEHOLDER_PATTERNS = [
    r"\[TO\s+BE\s+\w+\]",
    r"\[INSERT\b[^\]]*\]",
    r"\[FILL\b[^\]]*\]",
    r"\[TBD\]",
    r"\[DATE\]",
    r"\[NAME\]",
    r"\[EMAIL\]",
    r"\[ADDRESS\]",
    r"\[CASE\s*NO[.\]]*\]",
    r"_{3,}",
    r"\[PLACEHOLDER\b[^\]]*\]",
    r"\[\s*\.\.\.\s*\]",
    r"\[PENDING\b[^\]]*\]",
]

# Per-lane required filings
REQUIRED_FILINGS: Dict[str, Dict[str, List[str]]] = {
    "MEEK1": {
        "label": "Custody 2024-001507-DC",
        "required": [
            "Emergency Motion for Temporary Custody",
            "Motion to Restore Parenting Time",
            "Motion to Compel Discovery",
            "Motion for Contempt / Show Cause",
            "Motion to Disqualify Judge",
            "Motion for Reconsideration",
            "Motion to Set Aside Default",
            "Motion to Appoint GAL",
            "Motion for Change of Venue",
            "Motion for Sanctions",
            "Motion UCCJEA Emergency Jurisdiction",
            "Motion for Child Support Modification",
            "Motion Supervised Exchange",
            "Motion to Consolidate",
            "Motion for Writ of Mandamus",
            "Enhanced Alienation Brief",
            "Affidavit (Pigors)",
            "Proposed Orders Bundle",
            "Proof of Service",
            "In Forma Pauperis Affidavit",
        ],
    },
    "MEEK2": {
        "label": "PPO 2023-5907-PP",
        "required": [
            "Motion to Terminate/Modify PPO",
            "Response to Show Cause",
            "Affidavit in Support",
            "Brief Supporting Termination",
        ],
    },
    "MEEK3": {
        "label": "COA 366810",
        "required": [
            "Application for Leave to Appeal",
            "Motion for Immediate Consideration",
            "Emergency Motion / Stay",
            "Table of Authorities",
            "Affidavit (COA)",
            "Appendix / Record on Appeal",
            "Docketing Statement",
            "Proof of Service (COA)",
        ],
    },
    "MEEK4": {
        "label": "JTC/MSC",
        "required": [
            "JTC Formal Complaint",
            "JTC Enhanced Misconduct Brief",
            "JTC Affidavit (Pigors)",
            "MSC Petition Superintending Control",
            "MSC Table of Authorities",
            "MSC Affidavit (Pigors)",
            "Bar Complaint (Jennifer Barnes)",
            "FOC Grievance (Pamela Rusco)",
        ],
    },
    "MEEK5": {
        "label": "USDC Federal",
        "required": [
            "42 USC § 1983 Complaint",
            "Motion for TRO / Preliminary Injunction",
            "Affidavit (USDC)",
            "In Forma Pauperis Application (Federal)",
            "Civil Cover Sheet (JS-44)",
            "Summons / Service Documents",
        ],
    },
}


# ── Data classes ─────────────────────────────────────────────────────
@dataclass
class FilingAnalysis:
    filing_id: str = ""
    filename: str = ""
    rel_path: str = ""
    court: str = "UNKNOWN"
    filing_type: str = "unknown"
    title: str = ""
    citations: Dict[str, List[str]] = field(default_factory=dict)
    citations_count: int = 0
    has_caption: bool = False
    has_signature: bool = False
    has_cert_service: bool = False
    has_notice_hearing: bool = False
    has_proposed_order: bool = False
    has_verification: bool = False
    completeness_score: int = 0
    key_arguments: List[str] = field(default_factory=list)
    placeholders: List[str] = field(default_factory=list)
    word_count: int = 0
    is_draft: bool = False
    is_duplicate: bool = False
    gaps: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


# ── Helpers ──────────────────────────────────────────────────────────

def read_file(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            return path.read_text(encoding=enc)
        except (UnicodeDecodeError, UnicodeError):
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def detect_court(text: str, rel_path: str) -> str:
    combined = text + "\n" + rel_path
    scores: Dict[str, int] = defaultdict(int)
    for court, patterns in COURT_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, combined, re.IGNORECASE):
                scores[court] += 1
    if not scores:
        return "UNKNOWN"
    return max(scores, key=scores.get)


def detect_type(text: str, filename: str) -> str:
    combined = (filename + "\n" + text[:3000]).lower()
    for ftype, pat in FILING_TYPE_KEYWORDS.items():
        if re.search(pat, combined, re.IGNORECASE):
            return ftype
    return "unknown"


def extract_title(text: str, filename: str) -> str:
    for line in text.split("\n")[:30]:
        line = line.strip().lstrip("#").strip()
        if len(line) > 10 and not line.startswith(">") and not line.startswith("|"):
            if any(kw in line.upper() for kw in [
                "MOTION", "BRIEF", "COMPLAINT", "AFFIDAVIT", "APPLICATION",
                "PETITION", "RESPONSE", "EXHIBIT", "TABLE", "ORDER",
                "EMERGENCY", "GRIEVANCE", "REFERRAL", "NARRATIVE",
            ]):
                return line[:120]
    stem = Path(filename).stem.replace("_", " ").title()
    return stem[:120]


def extract_citations(text: str) -> Dict[str, List[str]]:
    found: Dict[str, List[str]] = {}
    for ctype, pat in CITATION_PATTERNS.items():
        matches = re.findall(pat, text)
        if matches:
            found[ctype] = sorted(set(m.strip() for m in matches))
    return found


def find_placeholders(text: str) -> List[str]:
    results = []
    for pat in PLACEHOLDER_PATTERNS:
        for m in re.finditer(pat, text):
            results.append(m.group())
    return results


def check_formatting(text: str) -> dict:
    upper = text.upper()
    return {
        "has_caption": bool(
            re.search(r"STATE\s+OF\s+MICHIGAN", upper)
            or re.search(r"UNITED\s+STATES\s+DISTRICT\s+COURT", upper)
            or re.search(r"JUDICIAL\s+TENURE\s+COMMISSION", upper)
            or re.search(r"IN\s+THE\s+MATTER\s+OF", upper)
        ),
        "has_signature": bool(
            re.search(r"(?:respectfully\s+submitted|signature|/s/|___.*pro\s*se)", text, re.I)
        ),
        "has_cert_service": bool(
            re.search(
                r"(?:certificate\s+of\s+service|proof\s+of\s+service|"
                r"certif(?:y|ies)\s+(?:that\s+)?.*(?:served|mailed|delivered))",
                text, re.I,
            )
        ),
        "has_notice_hearing": bool(
            re.search(r"notice\s+of\s+hearing", text, re.I)
        ),
        "has_proposed_order": bool(
            re.search(r"proposed\s+order", text, re.I)
        ),
        "has_verification": bool(
            re.search(r"(?:verification|verified|sworn|notary|jurat)", text, re.I)
        ),
    }


def compute_completeness(a: FilingAnalysis) -> int:
    """Score 0-100 based on filing quality indicators."""
    score = 0

    # Skip non-filing types
    if a.filing_type in ("checklist", "template", "inventory", "strategy",
                         "timeline", "narrative", "index"):
        # Support docs scored differently
        if a.word_count > 200:
            score += 30
        if a.citations_count > 0:
            score += 20
        if not a.placeholders:
            score += 20
        if not a.is_draft:
            score += 15
        return min(score, 70)  # cap at 70 for support docs

    # Caption (15 pts)
    if a.has_caption:
        score += 15

    # Signature block (10 pts)
    if a.has_signature:
        score += 10

    # Certificate of service (10 pts)
    if a.has_cert_service:
        score += 10

    # Citations depth (20 pts)
    if a.citations_count >= 15:
        score += 20
    elif a.citations_count >= 8:
        score += 15
    elif a.citations_count >= 3:
        score += 10
    elif a.citations_count >= 1:
        score += 5

    # Substantive length (15 pts)
    if a.word_count >= 3000:
        score += 15
    elif a.word_count >= 1500:
        score += 12
    elif a.word_count >= 500:
        score += 8
    elif a.word_count >= 200:
        score += 4

    # No placeholders remaining (10 pts)
    if not a.placeholders:
        score += 10
    elif len(a.placeholders) <= 3:
        score += 5

    # Not draft (5 pts)
    if not a.is_draft:
        score += 5

    # Notice of hearing for motions (5 pts)
    if a.filing_type == "motion" and a.has_notice_hearing:
        score += 5
    elif a.filing_type != "motion":
        score += 5  # n/a bonus

    # Verification for affidavits (5 pts)
    if a.filing_type == "affidavit" and a.has_verification:
        score += 5
    elif a.filing_type != "affidavit":
        score += 5  # n/a bonus

    return min(score, 100)


def extract_key_arguments(text: str) -> List[str]:
    """Pull headings and key argument markers from filing."""
    args = []
    for line in text.split("\n"):
        stripped = line.strip()
        # Markdown headings (##, ###)
        if re.match(r"^#{2,4}\s+", stripped):
            heading = stripped.lstrip("#").strip()
            if len(heading) > 5 and not heading.upper().startswith(("TABLE OF", "---")):
                args.append(heading)
        # Numbered legal arguments
        m = re.match(r"^\d+\.\s+(.{20,120})", stripped)
        if m and any(kw in m.group(1).upper() for kw in [
            "VIOLAT", "DENIED", "FAILED", "DEPRIV", "CONSTITUTIONAL",
            "DUE PROCESS", "ABUSE", "BIAS", "BEST INTEREST", "JURISDICTION",
            "EMERGENCY", "IRREPARABLE", "EX PARTE", "WITHOUT",
        ]):
            args.append(m.group(1)[:120])
    return args[:20]


def generate_gaps(a: FilingAnalysis) -> Tuple[List[str], List[str]]:
    """Generate gaps and recommendations for a filing."""
    gaps = []
    recs = []

    if a.filing_type in ("checklist", "template", "inventory", "index"):
        return gaps, recs

    if not a.has_caption:
        gaps.append("Missing proper Michigan court caption")
        recs.append("Add STATE OF MICHIGAN header with full case caption per MCR 2.113")

    if not a.has_signature and a.filing_type not in ("exhibit", "timeline", "template"):
        gaps.append("Missing signature block")
        recs.append("Add 'Respectfully submitted' block with /s/ signature per MCR 2.114")

    if not a.has_cert_service and a.filing_type in (
        "motion", "brief", "complaint", "response", "petition", "application"
    ):
        gaps.append("Missing Certificate of Service")
        recs.append("Add Certificate of Service per MCR 2.107(C)")

    if a.placeholders:
        gaps.append(f"{len(a.placeholders)} placeholder(s) remaining: {', '.join(a.placeholders[:5])}")
        recs.append("Fill all placeholder fields before filing")

    if a.is_draft:
        gaps.append("Document marked as DRAFT")
        recs.append("Remove DRAFT designation and finalize for filing")

    if a.citations_count < 3 and a.filing_type in ("motion", "brief", "complaint", "petition"):
        gaps.append(f"Insufficient citations ({a.citations_count})")
        recs.append("Add authority citations (MCR, MCL, case law) supporting each argument")

    if a.filing_type == "motion" and not a.has_notice_hearing:
        gaps.append("Missing Notice of Hearing")
        recs.append("Add Notice of Hearing per MCR 2.119(A)(2)")

    if a.filing_type == "affidavit" and not a.has_verification:
        gaps.append("Missing verification/jurat")
        recs.append("Add sworn verification with notary jurat")

    if a.word_count < 200 and a.filing_type in ("motion", "brief", "complaint"):
        gaps.append(f"Very short filing ({a.word_count} words)")
        recs.append("Expand substantive arguments")

    return gaps, recs


# ── DB cross-reference ───────────────────────────────────────────────

def cross_reference_db(analyses: List[FilingAnalysis]) -> Dict[str, list]:
    """Cross-reference filings against the litigation DB."""
    info: Dict[str, list] = {
        "citation_issues": [],
        "missing_forensic_refs": [],
        "rules_available": [],
    }
    if not DB_PATH.exists():
        print(f"  [WARN] DB not found at {DB_PATH}")
        return info

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Collect all MCR citations used across filings
    all_mcr = set()
    all_mcl = set()
    for a in analyses:
        for cite in a.citations.get("MCR", []):
            m = re.search(r"MCR\s+([\d.]+)", cite)
            if m:
                all_mcr.add(m.group(1))
        for cite in a.citations.get("MCL", []):
            m = re.search(r"MCL\s+([\d.]+)", cite)
            if m:
                all_mcl.add(m.group(1))

    # Check which MCR rules have full text available
    for rule_num in sorted(all_mcr):
        cur.execute(
            "SELECT id, title FROM auth_rules WHERE rule_number LIKE ? AND rule_type='MCR' LIMIT 1",
            (f"%{rule_num}%",),
        )
        row = cur.fetchone()
        if row:
            info["rules_available"].append(f"MCR {rule_num}: {row['title'] or 'available'}")

    # Check forensic findings not yet cited in any filing
    cur.execute("""
        SELECT finding_id, category, severity, description
        FROM forensic_judicial_analysis
        WHERE severity IN ('critical', 'high')
        ORDER BY CASE severity WHEN 'critical' THEN 0 ELSE 1 END, category
        LIMIT 50
    """)
    critical_findings = cur.fetchall()

    # Gather all filing text for searching
    all_text_upper = ""
    for a in analyses:
        all_text_upper += a.title.upper() + " "

    for f in critical_findings:
        desc_short = (f["description"] or "")[:60]
        cat = f["category"]
        # Check if any filing mentions this category
        cat_words = cat.replace("_", " ")
        if cat_words.upper() not in all_text_upper:
            info["missing_forensic_refs"].append(
                f"[{f['severity'].upper()}] {cat}: {desc_short}"
            )

    # Deduplicate
    info["missing_forensic_refs"] = sorted(set(info["missing_forensic_refs"]))[:30]

    conn.close()
    return info


# ── Lane gap analysis ────────────────────────────────────────────────

def lane_gap_analysis(
    analyses: List[FilingAnalysis],
) -> Dict[str, Dict]:
    """For each case lane, determine which filings exist vs. needed."""
    results = {}
    # Build lookup: lowercase keywords -> analyses
    for lane_id, lane_info in REQUIRED_FILINGS.items():
        existing = []
        missing = []
        for req in lane_info["required"]:
            req_lower = req.lower()
            req_words = set(re.findall(r"\w+", req_lower))
            found = False
            for a in analyses:
                title_words = set(re.findall(r"\w+", (a.title + " " + a.filename).lower()))
                # Require majority of words to match
                overlap = req_words & title_words
                if len(overlap) >= max(2, len(req_words) * 0.4):
                    existing.append({"required": req, "file": a.rel_path, "score": a.completeness_score})
                    found = True
                    break
            if not found:
                missing.append(req)

        # Suggested additional filings per lane
        additional = []
        if lane_id == "MEEK1":
            additional = [
                "Motion for Psychological Evaluation (MCR 3.218)",
                "Motion for Parenting Time Makeup (MCL 722.27a(8))",
                "Motion for Attorney Fees (MCR 3.206(D))",
                "Motion to Seal / Protective Order",
                "Emergency Motion for Supervised Contact Pending Hearing",
            ]
        elif lane_id == "MEEK2":
            additional = [
                "Motion for Evidentiary Hearing on PPO",
                "Brief re: PPO Misuse as Custody Weapon",
                "Motion to Dismiss PPO (lack of statutory basis)",
            ]
        elif lane_id == "MEEK3":
            additional = [
                "Motion for Peremptory Reversal (MCR 7.211(C)(4))",
                "Motion for Stay Pending Appeal (MCR 7.209)",
                "Supplemental Brief on Appeal",
                "Reply Brief",
            ]
        elif lane_id == "MEEK4":
            additional = [
                "Supplemental JTC Complaint (new violations)",
                "Request for Investigation (Attorney General)",
                "SCAO Administrative Complaint",
            ]
        elif lane_id == "MEEK5":
            additional = [
                "Motion for TRO / Preliminary Injunction",
                "Memorandum in Support of TRO",
                "Motion for Appointment of Counsel",
                "Discovery Plan (FRCP 26(f))",
            ]

        results[lane_id] = {
            "label": lane_info["label"],
            "existing": existing,
            "missing": missing,
            "additional_recommended": additional,
            "coverage_pct": round(
                len(existing) / max(len(lane_info["required"]), 1) * 100
            ),
        }
    return results


# ── DB output ────────────────────────────────────────────────────────

def save_to_db(analyses: List[FilingAnalysis]):
    """Create filing_analysis table and insert results."""
    if not DB_PATH.exists():
        print(f"  [WARN] DB not found at {DB_PATH}, skipping DB write")
        return
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS filing_analysis (
            filing_id TEXT PRIMARY KEY,
            filename TEXT,
            rel_path TEXT,
            court TEXT,
            filing_type TEXT,
            title TEXT,
            completeness_score INTEGER,
            citations_count INTEGER,
            has_caption INTEGER,
            has_signature INTEGER,
            has_cert_service INTEGER,
            has_notice_hearing INTEGER,
            word_count INTEGER,
            is_draft INTEGER,
            placeholders_count INTEGER,
            gaps TEXT,
            recommendations TEXT,
            key_arguments TEXT,
            analyzed_at TEXT
        )
    """)
    cur.execute("DELETE FROM filing_analysis")  # fresh run

    for a in analyses:
        cur.execute("""
            INSERT OR REPLACE INTO filing_analysis VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            a.filing_id,
            a.filename,
            a.rel_path,
            a.court,
            a.filing_type,
            a.title,
            a.completeness_score,
            a.citations_count,
            int(a.has_caption),
            int(a.has_signature),
            int(a.has_cert_service),
            int(a.has_notice_hearing),
            a.word_count,
            int(a.is_draft),
            len(a.placeholders),
            "; ".join(a.gaps),
            "; ".join(a.recommendations),
            "; ".join(a.key_arguments[:10]),
            datetime.now().isoformat(),
        ))
    conn.commit()
    conn.close()
    print(f"  ✓ Saved {len(analyses)} rows to filing_analysis table")


# ── Report generation ────────────────────────────────────────────────

def generate_report(
    analyses: List[FilingAnalysis],
    lane_gaps: Dict[str, Dict],
    xref: Dict[str, list],
):
    """Generate comprehensive Markdown report."""
    lines: List[str] = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Deduplicate: only use primary court folder copies, skip 03_FINAL duplicates
    primary = [a for a in analyses if "03_FINAL" not in a.rel_path and "_PROCESS_ARTIFACTS" not in a.rel_path]
    dup_count = len(analyses) - len(primary)

    # Stats
    total = len(primary)
    avg_score = round(sum(a.completeness_score for a in primary) / max(total, 1), 1)
    court_counts: Dict[str, int] = defaultdict(int)
    type_counts: Dict[str, int] = defaultdict(int)
    for a in primary:
        court_counts[a.court] += 1
        type_counts[a.filing_type] += 1

    # Header
    lines.append(f"# Viable Filings Analysis Report")
    lines.append(f"")
    lines.append(f"**Generated:** {now}  ")
    lines.append(f"**Source:** `{FILINGS_DIR}`  ")
    lines.append(f"**Database:** `{DB_PATH}`  ")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    # Executive summary
    lines.append(f"## Executive Summary")
    lines.append(f"")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total unique filings analyzed | **{total}** |")
    lines.append(f"| Duplicate / mirror copies skipped | {dup_count} |")
    lines.append(f"| Average completeness score | **{avg_score}/100** |")
    lines.append(f"| Filings scoring ≥ 80 | {sum(1 for a in primary if a.completeness_score >= 80)} |")
    lines.append(f"| Filings scoring < 50 | {sum(1 for a in primary if a.completeness_score < 50)} |")
    lines.append(f"| Filings still marked DRAFT | {sum(1 for a in primary if a.is_draft)} |")
    lines.append(f"| Filings with placeholders | {sum(1 for a in primary if a.placeholders)} |")
    lines.append(f"| Total citations across all filings | {sum(a.citations_count for a in primary)} |")
    lines.append(f"")

    # Court distribution
    lines.append(f"### Filings by Court")
    lines.append(f"")
    lines.append(f"| Court | Count | Avg Score |")
    lines.append(f"|-------|-------|-----------|")
    for court in ["14th_Circuit", "COA", "JTC", "MSC", "USDC", "UNKNOWN"]:
        ct = [a for a in primary if a.court == court]
        if ct:
            cavg = round(sum(a.completeness_score for a in ct) / len(ct), 1)
            lines.append(f"| {court} | {len(ct)} | {cavg} |")
    lines.append(f"")

    # Type distribution
    lines.append(f"### Filings by Type")
    lines.append(f"")
    lines.append(f"| Type | Count |")
    lines.append(f"|------|-------|")
    for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
        lines.append(f"| {t} | {c} |")
    lines.append(f"")

    lines.append(f"---")
    lines.append(f"")

    # Detailed filing analysis
    lines.append(f"## Detailed Filing Analysis")
    lines.append(f"")

    for court in ["14th_Circuit", "COA", "JTC", "MSC", "USDC", "UNKNOWN"]:
        court_filings = sorted(
            [a for a in primary if a.court == court],
            key=lambda x: -x.completeness_score,
        )
        if not court_filings:
            continue

        lines.append(f"### {court}")
        lines.append(f"")

        for a in court_filings:
            score_emoji = "🟢" if a.completeness_score >= 75 else "🟡" if a.completeness_score >= 50 else "🔴"
            lines.append(f"#### {score_emoji} {a.title}")
            lines.append(f"")
            lines.append(f"- **File:** `{a.rel_path}`")
            lines.append(f"- **Type:** {a.filing_type} | **Score:** {a.completeness_score}/100 | **Words:** {a.word_count:,}")
            fmt_parts = []
            if a.has_caption:
                fmt_parts.append("✅ Caption")
            else:
                fmt_parts.append("❌ Caption")
            if a.has_signature:
                fmt_parts.append("✅ Signature")
            else:
                fmt_parts.append("❌ Signature")
            if a.has_cert_service:
                fmt_parts.append("✅ Cert of Service")
            else:
                fmt_parts.append("❌ Cert of Service")
            lines.append(f"- **Formatting:** {' | '.join(fmt_parts)}")

            # Citations summary
            cite_parts = []
            for ctype in ["MCR", "MCL", "MRE", "case_law", "USC"]:
                if ctype in a.citations:
                    cite_parts.append(f"{ctype}: {len(a.citations[ctype])}")
            lines.append(f"- **Citations ({a.citations_count}):** {', '.join(cite_parts) if cite_parts else 'None'}")

            if a.is_draft:
                lines.append(f"- ⚠️ **DRAFT** — not finalized")
            if a.placeholders:
                lines.append(f"- ⚠️ **Placeholders ({len(a.placeholders)}):** {', '.join(a.placeholders[:5])}")

            if a.gaps:
                lines.append(f"- **Gaps:** {'; '.join(a.gaps)}")
            if a.recommendations:
                lines.append(f"- **Recommendations:** {'; '.join(a.recommendations)}")

            lines.append(f"")

    lines.append(f"---")
    lines.append(f"")

    # GAP ANALYSIS
    lines.append(f"## Gap Analysis by Case Lane")
    lines.append(f"")

    for lane_id in ["MEEK1", "MEEK2", "MEEK3", "MEEK4", "MEEK5"]:
        lg = lane_gaps[lane_id]
        cov = lg["coverage_pct"]
        cov_emoji = "🟢" if cov >= 75 else "🟡" if cov >= 50 else "🔴"
        lines.append(f"### {cov_emoji} {lane_id} — {lg['label']} ({cov}% coverage)")
        lines.append(f"")

        if lg["existing"]:
            lines.append(f"**Existing filings ({len(lg['existing'])}):**")
            lines.append(f"")
            for e in lg["existing"]:
                sc = e["score"]
                em = "🟢" if sc >= 75 else "🟡" if sc >= 50 else "🔴"
                lines.append(f"- {em} {e['required']} — `{e['file']}` (score: {sc})")
            lines.append(f"")

        if lg["missing"]:
            lines.append(f"**⚠️ MISSING filings ({len(lg['missing'])}):**")
            lines.append(f"")
            for m in lg["missing"]:
                lines.append(f"- ❌ **{m}**")
            lines.append(f"")

        if lg["additional_recommended"]:
            lines.append(f"**💡 Additional recommended filings:**")
            lines.append(f"")
            for r in lg["additional_recommended"]:
                lines.append(f"- 📋 {r}")
            lines.append(f"")

        lines.append(f"---")
        lines.append(f"")

    # DB cross-reference findings
    lines.append(f"## Database Cross-Reference")
    lines.append(f"")

    if xref["rules_available"]:
        lines.append(f"### Authority Rules Available in DB ({len(xref['rules_available'])})")
        lines.append(f"")
        for r in xref["rules_available"][:20]:
            lines.append(f"- ✅ {r}")
        lines.append(f"")

    if xref["missing_forensic_refs"]:
        lines.append(f"### Forensic Findings Not Yet Referenced ({len(xref['missing_forensic_refs'])})")
        lines.append(f"")
        lines.append(f"These critical/high-severity findings from `forensic_judicial_analysis` could strengthen filings:")
        lines.append(f"")
        for f in xref["missing_forensic_refs"][:20]:
            lines.append(f"- ⚠️ {f}")
        lines.append(f"")

    # Quality issues
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"## Quality Issues Summary")
    lines.append(f"")

    issues = []
    for a in primary:
        if a.completeness_score < 50:
            issues.append((a.completeness_score, f"🔴 **{a.title}** ({a.rel_path}) — score {a.completeness_score}: {'; '.join(a.gaps[:3])}"))
    issues.sort()
    if issues:
        lines.append(f"### Low-Scoring Filings (< 50)")
        lines.append(f"")
        for _, desc in issues:
            lines.append(f"- {desc}")
        lines.append(f"")

    draft_filings = [a for a in primary if a.is_draft]
    if draft_filings:
        lines.append(f"### Filings Still in Draft")
        lines.append(f"")
        for a in draft_filings:
            lines.append(f"- ⚠️ {a.title} ({a.rel_path})")
        lines.append(f"")

    placeholder_filings = [a for a in primary if a.placeholders]
    if placeholder_filings:
        lines.append(f"### Filings with Unfilled Placeholders")
        lines.append(f"")
        for a in placeholder_filings:
            lines.append(f"- ⚠️ {a.title}: {len(a.placeholders)} placeholders")
        lines.append(f"")

    # Priority action items
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"## Priority Action Items")
    lines.append(f"")

    actions = []
    # Missing critical filings
    for lane_id, lg in lane_gaps.items():
        for m in lg["missing"]:
            actions.append(f"**[{lane_id}]** Draft: {m}")
    # Low-score filings
    for a in primary:
        if a.completeness_score < 50 and a.filing_type in ("motion", "brief", "complaint", "petition"):
            actions.append(f"**[QUALITY]** Improve: {a.title} (score: {a.completeness_score})")

    for i, act in enumerate(actions, 1):
        lines.append(f"{i}. {act}")

    lines.append(f"")
    lines.append(f"---")
    lines.append(f"*End of report*")

    return "\n".join(lines)


# ── Main ─────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("  VIABLE FILINGS ANALYSIS")
    print("=" * 70)
    print()

    # 1. Scan files
    print("[1/6] Scanning filings...")
    filing_files: List[Path] = []
    for ext in ("*.md", "*.txt"):
        filing_files.extend(FILINGS_DIR.rglob(ext))
    print(f"  Found {len(filing_files)} files")

    # 2. Analyze each filing
    print("[2/6] Analyzing filings...")
    analyses: List[FilingAnalysis] = []
    for fpath in sorted(filing_files):
        text = read_file(fpath)
        rel = str(fpath.relative_to(FILINGS_DIR))
        fname = fpath.name
        fid = hashlib.md5(rel.encode()).hexdigest()[:12]

        a = FilingAnalysis()
        a.filing_id = fid
        a.filename = fname
        a.rel_path = rel
        a.court = detect_court(text, rel)
        a.filing_type = detect_type(text, fname)
        a.title = extract_title(text, fname)
        a.citations = extract_citations(text)
        a.citations_count = sum(len(v) for v in a.citations.values())
        fmt = check_formatting(text)
        a.has_caption = fmt["has_caption"]
        a.has_signature = fmt["has_signature"]
        a.has_cert_service = fmt["has_cert_service"]
        a.has_notice_hearing = fmt["has_notice_hearing"]
        a.has_proposed_order = fmt["has_proposed_order"]
        a.has_verification = fmt["has_verification"]
        a.word_count = len(text.split())
        a.is_draft = bool(re.search(r"\bDRAFT\b", text, re.I))
        a.placeholders = find_placeholders(text)
        a.key_arguments = extract_key_arguments(text)
        a.is_duplicate = "03_FINAL" in rel and any(
            other.filename == fname and "03_FINAL" not in other.rel_path
            for other in analyses
        )
        a.gaps, a.recommendations = generate_gaps(a)
        a.completeness_score = compute_completeness(a)

        analyses.append(a)

    print(f"  Analyzed {len(analyses)} files")

    # 3. Cross-reference DB
    print("[3/6] Cross-referencing database...")
    xref = cross_reference_db(analyses)
    print(f"  Rules available: {len(xref['rules_available'])}")
    print(f"  Unreferenced forensic findings: {len(xref['missing_forensic_refs'])}")

    # 4. Lane gap analysis
    print("[4/6] Running gap analysis per case lane...")
    lane_gaps = lane_gap_analysis(analyses)
    for lid, lg in lane_gaps.items():
        print(f"  {lid} ({lg['label']}): {lg['coverage_pct']}% coverage, {len(lg['missing'])} missing")

    # 5. Save to DB
    print("[5/6] Saving to database...")
    save_to_db(analyses)

    # 6. Generate report
    print("[6/6] Generating report...")
    report = generate_report(analyses, lane_gaps, xref)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"  ✓ Report saved to {REPORT_PATH}")

    # Print summary
    primary = [a for a in analyses if "03_FINAL" not in a.rel_path and "_PROCESS_ARTIFACTS" not in a.rel_path]
    total = len(primary)
    avg_score = round(sum(a.completeness_score for a in primary) / max(total, 1), 1)

    print()
    print("=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    print(f"  Total unique filings:    {total}")
    print(f"  Avg completeness score:  {avg_score}/100")
    print()
    print("  Filings per court:")
    court_counts: Dict[str, int] = defaultdict(int)
    for a in primary:
        court_counts[a.court] += 1
    for court, cnt in sorted(court_counts.items(), key=lambda x: -x[1]):
        print(f"    {court:20s} {cnt}")
    print()
    print("  Top gaps (missing filings):")
    gap_count = 0
    for lid in ["MEEK1", "MEEK2", "MEEK3", "MEEK4", "MEEK5"]:
        for m in lane_gaps[lid]["missing"]:
            gap_count += 1
            if gap_count <= 10:
                print(f"    [{lid}] {m}")
    if gap_count > 10:
        print(f"    ... and {gap_count - 10} more")
    print()
    print(f"  Report: {REPORT_PATH}")
    print(f"  DB:     {DB_PATH} → filing_analysis table")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
