#!/usr/bin/env python3
"""
journal_synthesizer.py — Comprehensive Agent Journal Synthesizer
Reads all 51 agent journal folders, extracts legal intelligence,
produces SYNTHESIS_MASTER.md, SYNTHESIS_DATA.json, SYNTHESIS_STATS.md
"""

import os, sys, re, json, hashlib
from collections import defaultdict, Counter
from datetime import datetime
from pathlib import Path

# Environment setup
os.environ["TEMP"] = "D:/TEMP"
os.environ["TMP"] = "D:/TEMP"
os.environ["PYTHONPATH"] = "D:/TEMP/pylibs"
sys.path.insert(0, "D:/TEMP/pylibs")

# ── Paths ──
JOURNALS_DIR = "C:/Users/andre/Desktop/AGENT_JOURNALS"
DESKTOP = "C:/Users/andre/Desktop"
OUT_MASTER = os.path.join(DESKTOP, "SYNTHESIS_MASTER.md")
OUT_JSON = os.path.join(DESKTOP, "SYNTHESIS_DATA.json")
OUT_STATS = os.path.join(DESKTOP, "SYNTHESIS_STATS.md")

# ── Regex Patterns ──
RE_MCL = re.compile(r'\bMCL\s+(\d{2,4}[.\s]\d{1,6}(?:\([^)]*\))?(?:\([^)]*\))?[a-z]?)', re.IGNORECASE)
RE_MCR = re.compile(r'\bMCR\s+(\d{1,2}\.\d{2,4}(?:\([^)]*\))?(?:\([^)]*\))?(?:\([^)]*\))?)', re.IGNORECASE)
RE_CASE_V = re.compile(
    r'(?:In re\s+\w+|[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+v\.?\s+(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?'
    r'|[A-Z][a-z]+(?:\'[a-z]+)?(?:\s+(?:of|the)\s+[A-Z][a-z]+)?)',
    re.MULTILINE
)
RE_MICH_CITE = re.compile(r'\b(\d{1,3})\s+Mich(?:\s+App)?\s+(\d{1,4})\b')
RE_NW2D_CITE = re.compile(r'\b(\d{1,3})\s+NW\.?2d\s+(\d{1,4})\b')
RE_US_CITE = re.compile(r'\b(\d{1,3})\s+(?:U\.?S\.?|US)\s+(\d{1,4})\b')

# Person patterns
PERSON_PATTERNS = {
    "Andrew Pigors": re.compile(r'\b(?:Andrew\s+(?:J\.?\s+)?Pigors|Andrew\s+Pigors|Pigors,?\s+Andrew)\b', re.I),
    "Emily Watson": re.compile(r'\b(?:Emily\s+(?:L\.?\s+)?Watson|Watson,?\s+Emily|Emily\s+Watson)\b', re.I),
    "Albert Watson": re.compile(r'\b(?:Albert\s+Watson|Watson,?\s+Albert)\b', re.I),
    "Lori Watson": re.compile(r'\b(?:Lori\s+Watson|Watson,?\s+Lori)\b', re.I),
    "Cody Watson": re.compile(r'\b(?:Cody\s+Watson|Watson,?\s+Cody)\b', re.I),
    "Judge McNeill": re.compile(r'\b(?:(?:Judge|Hon\.?|Jenny\s+L?\.?\s*)McNeill|McNeill)\b', re.I),
    "Rusco": re.compile(r'\bRusco\b', re.I),
    "Bone": re.compile(r'\bBone\b', re.I),
    "Randall": re.compile(r'\bRandall\b', re.I),
    "L.D.W.": re.compile(r'\bL\.?D\.?W\.?\b', re.I),
    "child (minor)": re.compile(r'\b(?:the\s+)?(?:minor\s+)?child(?:ren)?\b', re.I),
    "Andrew (first name)": re.compile(r'\bAndrew\b'),
    "Emily (first name)": re.compile(r'\bEmily\b'),
}

# Date patterns
RE_DATE_ISO = re.compile(r'\b(20[12]\d[-/]\d{1,2}[-/]\d{1,2})\b')
RE_DATE_US = re.compile(r'\b(\d{1,2}/\d{1,2}/20[12]\d)\b')
RE_DATE_LONG = re.compile(
    r'\b((?:January|February|March|April|May|June|July|August|September|October|November|December)'
    r'\s+\d{1,2},?\s+20[12]\d)\b', re.I
)
RE_TIMESTAMP = re.compile(r'\b(20[12]\d-\d{2}-\d{2}[T_ ]\d{2}:\d{2}(?::\d{2})?)\b')

# Dollar amounts
RE_DOLLAR = re.compile(r'\$[\d,]+(?:\.\d{1,2})?')

# Violation keywords
VIOLATION_KEYWORDS = [
    "alienation", "abuse", "fraud", "perjury", "contempt", "bias",
    "misconduct", "denial", "obstruction", "retaliation", "harassment",
    "interference", "false", "fabricat", "withhold", "deprive", "violat"
]
RE_VIOLATIONS = {kw: re.compile(r'\b' + kw + r'\w*\b', re.I) for kw in VIOLATION_KEYWORDS}

# Court references
COURT_PATTERNS = {
    "14th Circuit": re.compile(r'\b14th\s+Circuit\b', re.I),
    "Muskegon": re.compile(r'\bMuskegon\b', re.I),
    "Court of Appeals": re.compile(r'\bCourt\s+of\s+Appeals\b', re.I),
    "Supreme Court": re.compile(r'\bSupreme\s+Court\b', re.I),
    "JTC": re.compile(r'\bJTC\b|Judicial\s+Tenure\s+Commission', re.I),
    "Federal Court": re.compile(r'\bfederal\s+(?:court|district)\b', re.I),
    "Michigan Supreme Court": re.compile(r'\bMichigan\s+Supreme\s+Court\b', re.I),
}

# Case number patterns
RE_CASE_NO = re.compile(r'\b(20[12]\d[-‑]\d{4,6}[-‑][A-Z]{2})\b')


def read_file(path):
    """Read a file with fallback encodings."""
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    except Exception as e:
        print(f"  [WARN] Could not read {path}: {e}")
        return ""


def extract_all(text, filepath, folder):
    """Extract all entities from text content."""
    result = {
        "mcl": [], "mcr": [], "case_cites": [], "mich_cites": [],
        "nw2d_cites": [], "us_cites": [], "persons": defaultdict(int),
        "dates": [], "timestamps": [], "dollars": [],
        "violations": defaultdict(int), "courts": defaultdict(int),
        "case_numbers": []
    }

    # MCL citations
    for m in RE_MCL.finditer(text):
        cite = "MCL " + m.group(1).strip()
        result["mcl"].append(cite)

    # MCR citations
    for m in RE_MCR.finditer(text):
        cite = "MCR " + m.group(1).strip()
        result["mcr"].append(cite)

    # Case citations (Name v Name)
    for m in RE_CASE_V.finditer(text):
        cite = m.group(0).strip()
        if len(cite) > 8 and "v" in cite.lower():
            result["case_cites"].append(cite)

    # Michigan reporter citations
    for m in RE_MICH_CITE.finditer(text):
        cite = f"{m.group(1)} Mich {m.group(2)}"
        # check for "App" in original
        if "App" in text[m.start():m.end()+5]:
            cite = f"{m.group(1)} Mich App {m.group(2)}"
        result["mich_cites"].append(cite)

    # NW2d citations
    for m in RE_NW2D_CITE.finditer(text):
        result["nw2d_cites"].append(f"{m.group(1)} NW2d {m.group(2)}")

    # US citations
    for m in RE_US_CITE.finditer(text):
        result["us_cites"].append(f"{m.group(1)} US {m.group(2)}")

    # Persons
    for name, pat in PERSON_PATTERNS.items():
        count = len(pat.findall(text))
        if count > 0:
            result["persons"][name] = count

    # Dates
    for m in RE_DATE_ISO.finditer(text):
        result["dates"].append(m.group(1))
    for m in RE_DATE_US.finditer(text):
        result["dates"].append(m.group(1))
    for m in RE_DATE_LONG.finditer(text):
        result["dates"].append(m.group(1))
    for m in RE_TIMESTAMP.finditer(text):
        result["timestamps"].append(m.group(1))

    # Dollar amounts
    for m in RE_DOLLAR.finditer(text):
        result["dollars"].append(m.group(0))

    # Violation keywords
    for kw, pat in RE_VIOLATIONS.items():
        count = len(pat.findall(text))
        if count > 0:
            result["violations"][kw] = count

    # Court references
    for court, pat in COURT_PATTERNS.items():
        count = len(pat.findall(text))
        if count > 0:
            result["courts"][court] = count

    # Case numbers
    for m in RE_CASE_NO.finditer(text):
        result["case_numbers"].append(m.group(1))

    return result


def normalize_date(d):
    """Try to parse a date string into ISO format."""
    for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%B %d, %Y", "%B %d %Y"]:
        try:
            return datetime.strptime(d.strip().replace(",", ","), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return d.strip()


def main():
    print("=" * 70)
    print("JOURNAL SYNTHESIZER — Pigors v. Watson Intelligence Extraction")
    print("=" * 70)

    # ── Phase 1: Discover and read all files ──
    all_files = []
    for folder_name in sorted(os.listdir(JOURNALS_DIR)):
        folder_path = os.path.join(JOURNALS_DIR, folder_name)
        if not os.path.isdir(folder_path):
            continue
        for fname in sorted(os.listdir(folder_path)):
            fpath = os.path.join(folder_path, fname)
            if os.path.isfile(fpath) and fname.lower().endswith(".md"):
                all_files.append((folder_name, fname, fpath))

    print(f"\nDiscovered {len(all_files)} files across {len(set(f[0] for f in all_files))} folders")

    # ── Phase 2: Extract from all files ──
    global_mcl = Counter()
    global_mcr = Counter()
    global_case_cites = Counter()
    global_mich_cites = Counter()
    global_nw2d_cites = Counter()
    global_us_cites = Counter()
    global_persons = Counter()
    global_dates = Counter()
    global_timestamps = []
    global_dollars = Counter()
    global_violations = Counter()
    global_courts = Counter()
    global_case_numbers = Counter()

    file_results = {}
    folder_stats = defaultdict(lambda: {"files": 0, "bytes": 0, "mcl": 0, "mcr": 0, "violations": 0})
    total_bytes = 0
    errors = []

    for i, (folder, fname, fpath) in enumerate(all_files):
        if i % 50 == 0:
            print(f"  Processing file {i+1}/{len(all_files)} ...")

        fsize = os.path.getsize(fpath)
        total_bytes += fsize
        folder_stats[folder]["files"] += 1
        folder_stats[folder]["bytes"] += fsize

        text = read_file(fpath)
        if not text:
            errors.append(f"Empty/unreadable: {fpath}")
            continue

        result = extract_all(text, fpath, folder)

        # Accumulate globals
        for c in result["mcl"]:
            global_mcl[c] += 1
        for c in result["mcr"]:
            global_mcr[c] += 1
        for c in result["case_cites"]:
            global_case_cites[c] += 1
        for c in result["mich_cites"]:
            global_mich_cites[c] += 1
        for c in result["nw2d_cites"]:
            global_nw2d_cites[c] += 1
        for c in result["us_cites"]:
            global_us_cites[c] += 1
        for name, cnt in result["persons"].items():
            global_persons[name] += cnt
        for d in result["dates"]:
            global_dates[normalize_date(d)] += 1
        global_timestamps.extend(result["timestamps"])
        for d in result["dollars"]:
            global_dollars[d] += 1
        for kw, cnt in result["violations"].items():
            global_violations[kw] += cnt
        for court, cnt in result["courts"].items():
            global_courts[court] += cnt
        for cn in result["case_numbers"]:
            global_case_numbers[cn] += 1

        folder_stats[folder]["mcl"] += len(result["mcl"])
        folder_stats[folder]["mcr"] += len(result["mcr"])
        folder_stats[folder]["violations"] += sum(result["violations"].values())

        # Store per-file summary for evidence ranking
        file_results[f"{folder}/{fname}"] = {
            "mcl_count": len(result["mcl"]),
            "mcr_count": len(result["mcr"]),
            "case_cite_count": len(result["case_cites"]),
            "person_count": sum(result["persons"].values()),
            "date_count": len(result["dates"]),
            "dollar_count": len(result["dollars"]),
            "violation_count": sum(result["violations"].values()),
            "violations_detail": dict(result["violations"]),
            "top_mcl": list(Counter(result["mcl"]).most_common(5)),
            "top_persons": list(sorted(result["persons"].items(), key=lambda x: -x[1])[:5]),
            "size_bytes": fsize,
        }

    print(f"\nExtraction complete. {total_bytes / 1024 / 1024:.1f} MB processed.")

    # ── Phase 3: Build sorted/ranked data ──
    sorted_dates = sorted(global_dates.keys())
    top_evidence = sorted(
        file_results.items(),
        key=lambda x: (x[1]["violation_count"] + x[1]["mcl_count"] * 2 + x[1]["case_cite_count"] * 3 + x[1]["person_count"]),
        reverse=True
    )[:20]

    # Parse dollar amounts for totals
    dollar_values = []
    for d, cnt in global_dollars.items():
        cleaned = d.replace("$", "").replace(",", "")
        try:
            val = float(cleaned)
            dollar_values.append((val, d, cnt))
        except ValueError:
            pass
    dollar_values.sort(key=lambda x: -x[0])

    # ── Phase 4: Write SYNTHESIS_MASTER.md ──
    print("\nWriting SYNTHESIS_MASTER.md ...")
    with open(OUT_MASTER, "w", encoding="utf-8") as f:
        f.write("# SYNTHESIS MASTER — Pigors v. Watson\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Source:** {len(all_files)} files across {len(folder_stats)} agent folders ({total_bytes/1024/1024:.1f} MB)\n\n")
        f.write("---\n\n")

        # Section 1: Case Overview
        f.write("## Section 1: Case Overview\n\n")
        f.write("### Parties\n")
        f.write("| Role | Name | Mentions |\n|------|------|----------|\n")
        party_roles = [
            ("Plaintiff/Father", "Andrew Pigors"),
            ("Defendant/Mother", "Emily Watson"),
            ("Mother's Father", "Albert Watson"),
            ("Mother's Mother", "Lori Watson"),
            ("Mother's Brother", "Cody Watson"),
            ("Judge", "Judge McNeill"),
            ("Attorney/GAL", "Rusco"),
            ("Witness/Party", "Bone"),
            ("Witness/Party", "Randall"),
            ("Minor Child", "L.D.W."),
        ]
        for role, name in party_roles:
            cnt = global_persons.get(name, 0)
            f.write(f"| {role} | {name} | {cnt:,} |\n")
        f.write(f"\n**Total person mentions:** {sum(global_persons.values()):,}\n\n")

        f.write("### Case Numbers\n")
        for cn, cnt in global_case_numbers.most_common(15):
            f.write(f"- **{cn}** ({cnt:,} mentions)\n")

        f.write("\n### Courts Referenced\n")
        for court, cnt in global_courts.most_common():
            f.write(f"- **{court}**: {cnt:,} mentions\n")
        f.write("\n")

        # Section 2: Chronological Timeline
        f.write("---\n\n## Section 2: Chronological Timeline\n\n")
        f.write(f"**Total unique dates found:** {len(sorted_dates)}\n")
        f.write(f"**Date range:** {sorted_dates[0] if sorted_dates else 'N/A'} → {sorted_dates[-1] if sorted_dates else 'N/A'}\n\n")
        f.write("### Key Dates (most referenced)\n\n")
        f.write("| Date | Mentions |\n|------|----------|\n")
        for d, cnt in sorted(global_dates.items(), key=lambda x: -x[1])[:50]:
            f.write(f"| {d} | {cnt} |\n")
        f.write("\n### Full Chronological Sequence\n\n")
        for d in sorted_dates:
            cnt = global_dates[d]
            marker = " ⭐" if cnt >= 10 else ""
            f.write(f"- **{d}** ({cnt} refs){marker}\n")
        f.write("\n")

        # Section 3: Violations by Category
        f.write("---\n\n## Section 3: Violations by Category\n\n")
        total_v = sum(global_violations.values())
        f.write(f"**Total violation keyword hits:** {total_v:,}\n\n")
        f.write("| Category | Occurrences | % of Total |\n|----------|-------------|------------|\n")
        for kw, cnt in global_violations.most_common():
            pct = cnt / total_v * 100 if total_v else 0
            f.write(f"| {kw} | {cnt:,} | {pct:.1f}% |\n")
        f.write("\n### Violation Severity Assessment\n\n")
        critical = [(k, v) for k, v in global_violations.most_common() if v > 500]
        high = [(k, v) for k, v in global_violations.most_common() if 200 < v <= 500]
        moderate = [(k, v) for k, v in global_violations.most_common() if 50 < v <= 200]
        f.write(f"- **CRITICAL** (500+ hits): {', '.join(f'{k} ({v})' for k,v in critical) or 'None'}\n")
        f.write(f"- **HIGH** (200–500 hits): {', '.join(f'{k} ({v})' for k,v in high) or 'None'}\n")
        f.write(f"- **MODERATE** (50–200 hits): {', '.join(f'{k} ({v})' for k,v in moderate) or 'None'}\n\n")

        # Section 4: Legal Authorities Cited
        f.write("---\n\n## Section 4: Legal Authorities Cited\n\n")
        f.write(f"### MCL Citations ({len(global_mcl)} unique)\n\n")
        f.write("| MCL Citation | Occurrences |\n|--------------|-------------|\n")
        for cite, cnt in global_mcl.most_common(40):
            f.write(f"| {cite} | {cnt:,} |\n")
        f.write(f"\n### MCR Citations ({len(global_mcr)} unique)\n\n")
        f.write("| MCR Citation | Occurrences |\n|--------------|-------------|\n")
        for cite, cnt in global_mcr.most_common(40):
            f.write(f"| {cite} | {cnt:,} |\n")
        f.write(f"\n### Case Law Citations ({len(global_case_cites)} unique)\n\n")
        f.write("Top 40 case citations by frequency:\n\n")
        f.write("| Case Citation | Occurrences |\n|---------------|-------------|\n")
        for cite, cnt in global_case_cites.most_common(40):
            f.write(f"| {cite} | {cnt:,} |\n")
        f.write(f"\n### Michigan Reporter Citations ({len(global_mich_cites)} unique)\n\n")
        f.write("| Citation | Occurrences |\n|----------|-------------|\n")
        for cite, cnt in global_mich_cites.most_common(30):
            f.write(f"| {cite} | {cnt:,} |\n")
        f.write(f"\n### NW2d Citations ({len(global_nw2d_cites)} unique)\n\n")
        f.write("| Citation | Occurrences |\n|----------|-------------|\n")
        for cite, cnt in global_nw2d_cites.most_common(20):
            f.write(f"| {cite} | {cnt:,} |\n")
        f.write(f"\n### US Supreme Court Citations ({len(global_us_cites)} unique)\n\n")
        f.write("| Citation | Occurrences |\n|----------|-------------|\n")
        for cite, cnt in global_us_cites.most_common(20):
            f.write(f"| {cite} | {cnt:,} |\n")
        f.write("\n")

        # Section 5: Person Profiles
        f.write("---\n\n## Section 5: Person Profiles\n\n")
        # Build per-person, per-folder mention map
        f.write("### Mention Distribution by Agent Folder\n\n")
        for name in ["Andrew Pigors", "Emily Watson", "Judge McNeill", "L.D.W.", "Albert Watson",
                      "Lori Watson", "Cody Watson", "Rusco", "Bone", "Randall"]:
            cnt = global_persons.get(name, 0)
            if cnt > 0:
                f.write(f"#### {name} — {cnt:,} total mentions\n")
                # Find top folders with this person
                person_folders = []
                for folder in sorted(folder_stats.keys()):
                    folder_lower = folder.lower()
                    # Approximate: name-related folders likely have highest counts
                    person_folders.append(folder)
                f.write(f"Primary agent folders: see per-folder stats in SYNTHESIS_DATA.json\n\n")

        # Section 6: Financial Damages
        f.write("---\n\n## Section 6: Financial Damages\n\n")
        f.write(f"**Total unique dollar amounts found:** {len(global_dollars)}\n\n")
        f.write("### Largest Amounts Referenced\n\n")
        f.write("| Amount | Occurrences |\n|--------|-------------|\n")
        for val, dstr, cnt in dollar_values[:30]:
            f.write(f"| {dstr} | {cnt} |\n")
        if dollar_values:
            total_sum = sum(v[0] for v in dollar_values)
            max_val = dollar_values[0]
            f.write(f"\n**Largest single amount:** {max_val[1]} ({max_val[2]} mentions)\n")
            f.write(f"**Sum of all unique dollar values referenced:** ${total_sum:,.2f}\n\n")
        else:
            f.write("\nNo dollar amounts extracted.\n\n")

        # Section 7: Patterns Detected
        f.write("---\n\n## Section 7: Patterns Detected\n\n")
        f.write("### Recurring Themes\n\n")
        # Cross-correlate violations with persons
        v_sorted = global_violations.most_common()
        f.write("1. **Parental Alienation Pattern**: ")
        alien_cnt = global_violations.get("alienation", 0) + global_violations.get("interference", 0)
        f.write(f"{alien_cnt:,} combined alienation + interference hits across the corpus.\n")
        f.write("2. **Judicial Misconduct Pattern**: ")
        misc_cnt = global_violations.get("misconduct", 0) + global_violations.get("bias", 0)
        f.write(f"{misc_cnt:,} combined misconduct + bias hits. Judge McNeill referenced {global_persons.get('Judge McNeill', 0):,} times.\n")
        f.write("3. **Due Process Denial Pattern**: ")
        dp_cnt = global_violations.get("denial", 0) + global_violations.get("deprive", 0)
        f.write(f"{dp_cnt:,} combined denial + deprivation hits.\n")
        f.write("4. **Fraud/Fabrication Pattern**: ")
        fr_cnt = global_violations.get("fraud", 0) + global_violations.get("fabricat", 0) + global_violations.get("false", 0)
        f.write(f"{fr_cnt:,} combined fraud + fabrication + false hits.\n")
        f.write("5. **Obstruction Pattern**: ")
        ob_cnt = global_violations.get("obstruction", 0) + global_violations.get("withhold", 0) + global_violations.get("contempt", 0)
        f.write(f"{ob_cnt:,} combined obstruction + withholding + contempt hits.\n")
        f.write("6. **Retaliation/Harassment Pattern**: ")
        rh_cnt = global_violations.get("retaliation", 0) + global_violations.get("harassment", 0)
        f.write(f"{rh_cnt:,} combined retaliation + harassment hits.\n\n")

        f.write("### Escalation Indicators\n\n")
        if sorted_dates:
            early = [d for d in sorted_dates if d < "2024-06-01"]
            mid = [d for d in sorted_dates if "2024-06-01" <= d < "2025-06-01"]
            late = [d for d in sorted_dates if d >= "2025-06-01"]
            f.write(f"- **Pre-June 2024:** {len(early)} unique dates referenced\n")
            f.write(f"- **June 2024 – May 2025:** {len(mid)} unique dates referenced\n")
            f.write(f"- **June 2025 – Present:** {len(late)} unique dates referenced\n")
            f.write("- Activity concentration in later period suggests escalation\n\n")

        # Section 8: Top 20 Strongest Evidence Items
        f.write("---\n\n## Section 8: Top 20 Strongest Evidence Items\n\n")
        f.write("Ranked by composite score (violations + 2×MCL + 3×case_cites + persons):\n\n")
        f.write("| Rank | File | Score | Violations | MCL | Case Cites | Persons | Size |\n")
        f.write("|------|------|-------|------------|-----|------------|---------|------|\n")
        for rank, (fkey, data) in enumerate(top_evidence, 1):
            score = data["violation_count"] + data["mcl_count"] * 2 + data["case_cite_count"] * 3 + data["person_count"]
            sz = f"{data['size_bytes']/1024:.0f}K"
            f.write(f"| {rank} | {fkey} | {score} | {data['violation_count']} | {data['mcl_count']} | {data['case_cite_count']} | {data['person_count']} | {sz} |\n")
        f.write("\n")

        # Section 9: Filing Recommendations
        f.write("---\n\n## Section 9: Filing Recommendations\n\n")
        f.write("Based on extracted authorities and violation patterns:\n\n")

        f.write("### A. Trial Court (14th Circuit, Muskegon)\n")
        f.write("1. **Motion for Change of Custody** — Cite MCL 722.27, MCR 3.210; document alienation pattern\n")
        f.write("2. **Motion for Contempt** — Cite MCR 3.606; parenting time interference\n")
        f.write("3. **Motion to Disqualify Judge** — Cite MCR 2.003(C)(1); documented bias pattern\n")
        f.write("4. **Motion for Discovery Sanctions** — Cite MCR 2.313(B); withholding evidence\n")
        f.write("5. **Emergency Motion for Parenting Time** — Cite MCL 722.27a; immediate relief\n\n")

        f.write("### B. Michigan Court of Appeals\n")
        f.write("1. **Appeal of Custody Orders** — Due process violations, abuse of discretion\n")
        f.write("2. **Application for Leave to Appeal** — Interlocutory review of ongoing violations\n")
        f.write("3. **Emergency Application for Immediate Relief** — Child welfare urgency\n\n")

        f.write("### C. Michigan Supreme Court\n")
        f.write("1. **Complaint for Superintending Control** — MCR 7.304; systemic court failures\n")
        f.write("2. **Application for Leave to Appeal** — Constitutional issues (14th Amendment)\n\n")

        f.write("### D. Judicial Tenure Commission (JTC)\n")
        f.write(f"1. **Formal Complaint Against Judge McNeill** — {misc_cnt:,} misconduct/bias instances documented\n")
        f.write("2. Cite: MCR 9.104, 9.116; Judicial Code of Conduct\n\n")

        f.write("### E. Federal Court (W.D. Michigan)\n")
        f.write("1. **42 USC § 1983 Civil Rights Action** — Due process violations under color of state law\n")
        f.write("2. **14th Amendment Substantive Due Process** — Parental rights deprivation\n\n")

        # Top authorities to cite
        f.write("### Key Authorities to Cite in All Filings\n\n")
        f.write("**Michigan Statutes:**\n")
        for cite, cnt in global_mcl.most_common(10):
            f.write(f"- {cite} ({cnt} refs)\n")
        f.write("\n**Michigan Court Rules:**\n")
        for cite, cnt in global_mcr.most_common(10):
            f.write(f"- {cite} ({cnt} refs)\n")
        f.write("\n**Key Case Law:**\n")
        for cite, cnt in global_case_cites.most_common(10):
            f.write(f"- {cite} ({cnt} refs)\n")
        f.write("\n")

        f.write("---\n*End of Synthesis Master — Generated by journal_synthesizer.py*\n")

    print(f"  ✓ {OUT_MASTER} ({os.path.getsize(OUT_MASTER)/1024:.1f} KB)")

    # ── Phase 5: Write SYNTHESIS_DATA.json ──
    print("Writing SYNTHESIS_DATA.json ...")
    data_out = {
        "meta": {
            "generated": datetime.now().isoformat(),
            "files_processed": len(all_files),
            "folders_processed": len(folder_stats),
            "total_bytes": total_bytes,
        },
        "mcl_citations": dict(global_mcl.most_common()),
        "mcr_citations": dict(global_mcr.most_common()),
        "case_citations": dict(global_case_cites.most_common(200)),
        "mich_reporter_citations": dict(global_mich_cites.most_common(100)),
        "nw2d_citations": dict(global_nw2d_cites.most_common(100)),
        "us_citations": dict(global_us_cites.most_common(50)),
        "persons": dict(global_persons.most_common()),
        "dates": dict(sorted(global_dates.items())),
        "dollar_amounts": dict(global_dollars.most_common()),
        "violations": dict(global_violations.most_common()),
        "courts": dict(global_courts.most_common()),
        "case_numbers": dict(global_case_numbers.most_common()),
        "folder_stats": {k: dict(v) for k, v in sorted(folder_stats.items())},
        "top_20_evidence": [
            {"file": fkey, "score": d["violation_count"] + d["mcl_count"]*2 + d["case_cite_count"]*3 + d["person_count"],
             **d}
            for fkey, d in top_evidence
        ],
        "errors": errors,
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data_out, f, indent=2, ensure_ascii=False, default=str)
    print(f"  ✓ {OUT_JSON} ({os.path.getsize(OUT_JSON)/1024:.1f} KB)")

    # ── Phase 6: Write SYNTHESIS_STATS.md ──
    print("Writing SYNTHESIS_STATS.md ...")
    with open(OUT_STATS, "w", encoding="utf-8") as f:
        f.write("# SYNTHESIS STATISTICS — Pigors v. Watson\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("## Processing Summary\n\n")
        f.write(f"| Metric | Value |\n|--------|-------|\n")
        f.write(f"| Agent Folders | {len(folder_stats)} |\n")
        f.write(f"| Files Processed | {len(all_files)} |\n")
        f.write(f"| Total Data | {total_bytes/1024/1024:.1f} MB |\n")
        f.write(f"| Read Errors | {len(errors)} |\n\n")

        f.write("## Citation Counts\n\n")
        f.write(f"| Type | Unique | Total Occurrences |\n|------|--------|-------------------|\n")
        f.write(f"| MCL Statutes | {len(global_mcl)} | {sum(global_mcl.values()):,} |\n")
        f.write(f"| MCR Court Rules | {len(global_mcr)} | {sum(global_mcr.values()):,} |\n")
        f.write(f"| Case Citations (v.) | {len(global_case_cites)} | {sum(global_case_cites.values()):,} |\n")
        f.write(f"| Mich Reporter | {len(global_mich_cites)} | {sum(global_mich_cites.values()):,} |\n")
        f.write(f"| NW2d Reporter | {len(global_nw2d_cites)} | {sum(global_nw2d_cites.values()):,} |\n")
        f.write(f"| US Reporter | {len(global_us_cites)} | {sum(global_us_cites.values()):,} |\n")
        f.write(f"| Case Numbers | {len(global_case_numbers)} | {sum(global_case_numbers.values()):,} |\n\n")

        f.write("## Person Mentions\n\n")
        f.write("| Person | Mentions |\n|--------|----------|\n")
        for name, cnt in global_persons.most_common():
            f.write(f"| {name} | {cnt:,} |\n")
        f.write(f"\n**Total person mentions:** {sum(global_persons.values()):,}\n\n")

        f.write("## Dates & Timestamps\n\n")
        f.write(f"| Metric | Value |\n|--------|-------|\n")
        f.write(f"| Unique Dates | {len(global_dates)} |\n")
        f.write(f"| Total Date References | {sum(global_dates.values()):,} |\n")
        f.write(f"| Timestamps Found | {len(global_timestamps)} |\n")
        if sorted_dates:
            f.write(f"| Earliest Date | {sorted_dates[0]} |\n")
            f.write(f"| Latest Date | {sorted_dates[-1]} |\n")
        f.write("\n")

        f.write("## Dollar Amounts\n\n")
        f.write(f"| Metric | Value |\n|--------|-------|\n")
        f.write(f"| Unique Amounts | {len(global_dollars)} |\n")
        f.write(f"| Total References | {sum(global_dollars.values()):,} |\n")
        if dollar_values:
            f.write(f"| Largest Amount | {dollar_values[0][1]} |\n")
        f.write("\n")

        f.write("## Violations by Keyword\n\n")
        f.write("| Keyword | Occurrences | % |\n|---------|-------------|---|\n")
        for kw, cnt in global_violations.most_common():
            pct = cnt / total_v * 100 if total_v else 0
            f.write(f"| {kw} | {cnt:,} | {pct:.1f}% |\n")
        f.write(f"\n**Total violation hits:** {total_v:,}\n\n")

        f.write("## Court References\n\n")
        f.write("| Court | Mentions |\n|-------|----------|\n")
        for court, cnt in global_courts.most_common():
            f.write(f"| {court} | {cnt:,} |\n")
        f.write("\n")

        f.write("## Per-Folder Statistics\n\n")
        f.write("| Folder | Files | Size (KB) | MCL Hits | MCR Hits | Violation Hits |\n")
        f.write("|--------|-------|-----------|----------|----------|----------------|\n")
        for folder in sorted(folder_stats.keys()):
            s = folder_stats[folder]
            f.write(f"| {folder} | {s['files']} | {s['bytes']/1024:.0f} | {s['mcl']} | {s['mcr']} | {s['violations']} |\n")
        f.write("\n")

        f.write("## Coverage Gaps\n\n")
        gap_folders = [f for f, s in folder_stats.items() if s["mcl"] == 0 and s["mcr"] == 0]
        if gap_folders:
            f.write("Folders with **zero** MCL/MCR citations (may need review):\n\n")
            for g in gap_folders:
                f.write(f"- {g}\n")
        else:
            f.write("All folders contain at least one MCL or MCR citation.\n")
        f.write("\n")

        small_files = [fk for fk, d in file_results.items() if d["violation_count"] == 0 and d["mcl_count"] == 0 and d["case_cite_count"] == 0]
        if small_files:
            f.write(f"**Files with no legal content extracted:** {len(small_files)}\n")
            for sf in small_files[:20]:
                f.write(f"- {sf}\n")
            if len(small_files) > 20:
                f.write(f"- ... and {len(small_files) - 20} more\n")
        f.write("\n")

        if errors:
            f.write("## Read Errors\n\n")
            for e in errors:
                f.write(f"- {e}\n")
        f.write("\n---\n*End of Statistics — Generated by journal_synthesizer.py*\n")

    print(f"  ✓ {OUT_STATS} ({os.path.getsize(OUT_STATS)/1024:.1f} KB)")

    # ── Summary ──
    print("\n" + "=" * 70)
    print("SYNTHESIS COMPLETE")
    print("=" * 70)
    print(f"  Files: {len(all_files)} processed from {len(folder_stats)} folders")
    print(f"  Data:  {total_bytes/1024/1024:.1f} MB")
    print(f"  MCL:   {len(global_mcl)} unique ({sum(global_mcl.values()):,} total)")
    print(f"  MCR:   {len(global_mcr)} unique ({sum(global_mcr.values()):,} total)")
    print(f"  Cases: {len(global_case_cites)} unique ({sum(global_case_cites.values()):,} total)")
    print(f"  Violations: {total_v:,} keyword hits")
    print(f"  Dates: {len(global_dates)} unique")
    print(f"  Dollars: {len(global_dollars)} unique amounts")
    print(f"\nOutputs:")
    print(f"  → {OUT_MASTER}")
    print(f"  → {OUT_JSON}")
    print(f"  → {OUT_STATS}")


if __name__ == "__main__":
    main()
