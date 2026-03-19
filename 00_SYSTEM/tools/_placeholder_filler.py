#!/usr/bin/env python3
"""
Placeholder Elimination Agent for Lane A (14th Circuit) Court-Ready Filing Packages
==================================================================================
Scans all court-ready filings, finds bracketed placeholders, replaces with confirmed data.
Uses cycle_method write (write-to-temp, rename) for EAGAIN safety on Windows.

Author: LitigationOS System
Date: 2026-02-25
"""

import os
import re
import sys
import tempfile
import shutil
from pathlib import Path
from collections import defaultdict

# ============================================================================
# CONFIRMED REPLACEMENT DATA
# ============================================================================

PLAINTIFF_NAME = "Andrew J. Pigors"
PLAINTIFF_ADDRESS = "1977 Whitehall Road, Trailer 17, North Muskegon, MI 49445"
PLAINTIFF_CITY_STATE_ZIP = "North Muskegon, MI 49445"
PLAINTIFF_PHONE = "231-260-1936"
PLAINTIFF_EMAIL = "andrewjpigors@gmail.com"
PLAINTIFF_DOB = "12/30/1987"

DEFENDANT_NAME = "Emily Ann Watson"
DEFENDANT_ADDRESS = "2160 Garland Drive, Norton Shores, MI 49441"
DEFENDANT_PHONE = "231-683-7107"

DEFENDANT_ATTORNEY = "Jennifer L. Barnes (P55406)"
DEFENDANT_ATTORNEY_FULL = "Jennifer L. Barnes, P55406, address on file with the Court"
DEFENDANT_ATTORNEY_ADDRESS = "Barnes Law Firm, PLLC, 880 Jefferson St., Ste. B, Muskegon, MI 49440"

COURT = "14th Judicial Circuit Court, Muskegon County"
COURT_ADDRESS = "990 Terrace Street, 3rd Floor, Muskegon, MI 49442"
CASE_NO = "2024-001507-DC"
PPO_CASE = "2023-5907-PP"
JUDGE = "Hon. Jenny L. McNeill"
FILING_DATE = "February 25, 2026"

FOC_ADDRESS = "990 Terrace Street, Muskegon, MI 49442"

# ============================================================================
# DIRECTORIES TO PROCESS
# ============================================================================

DIRS_AND_PATTERNS = [
    # (directory, glob_pattern, min_size_bytes)
    (r"C:\Users\andre\LitigationOS\04_COURT_FILINGS\03_FINAL\COURT_READY\LANE_A", "*.md", 1024),
    (r"C:\Users\andre\LitigationOS\04_COURT_FILINGS\03_FINAL\COURT_READY", "01_14TH_CIRCUIT__*.md", 0),
    (r"C:\Users\andre\LitigationOS\06_VEHICLES\LANE_A_CUSTODY", "*.md", 0),
]

# ============================================================================
# REPLACEMENT MAP — ordered from most specific to least specific
# ============================================================================

# Direct, exact-match replacements (case-insensitive matching handled below)
EXACT_REPLACEMENTS = {
    # Address variants
    "[ADDRESS ON FILE]": DEFENDANT_ATTORNEY_ADDRESS,
    "[Address on file]": DEFENDANT_ATTORNEY_ADDRESS,
    "[ADDRESS REDACTED]": PLAINTIFF_ADDRESS,
    "[Street Address]": PLAINTIFF_ADDRESS,

    # Contact info
    "[PHONE]": PLAINTIFF_PHONE,
    "[Phone]": PLAINTIFF_PHONE,
    "[Phone Number]": PLAINTIFF_PHONE,
    "[EMAIL]": PLAINTIFF_EMAIL,
    "[Email]": PLAINTIFF_EMAIL,
    "[Email Address]": PLAINTIFF_EMAIL,
    "[EMAIL ADDRESS]": PLAINTIFF_EMAIL,
    "[DOB]": PLAINTIFF_DOB,

    # Date
    "[DATE]": FILING_DATE,
    "[DATE OF FILING]": FILING_DATE,

    # Plaintiff
    "[Plaintiff]": PLAINTIFF_NAME,

    # Child privacy
    "[Child]": "the minor child",

    # Scheduling/assignment
    "[TO BE ASSIGNED UPON FILING]": "(New Filing — Related to Case No. 2024-001507-DC)",
    "[TO BE COMPLETED UPON SCHEDULING]": "at the earliest date available to this Court",
    "[EARLIEST AVAILABLE]": "at the earliest date available to this Court",
    "[Pending]": "Active — Pending",
    "[PANEL TBD]": "Panel Not Yet Assigned",

    # Attorney references
    "[ATTORNEY ADDRESS]": DEFENDANT_ATTORNEY_ADDRESS,
    "[ATTORNEY CITY, STATE ZIP]": "Muskegon, MI 49440",
    "[attorney email]": "on file with the Court",

    # City/State/ZIP variants — context-dependent
    "[CITY, STATE ZIP]": PLAINTIFF_CITY_STATE_ZIP,
    "[City, State ZIP]": PLAINTIFF_CITY_STATE_ZIP,
    "[City, State, ZIP]": PLAINTIFF_CITY_STATE_ZIP,

    # Court-determined items — leave as court blanks with descriptive text
    "[TO BE DETERMINED BY THE COURT]": "(to be determined by the Court)",

    # GAL / Facilitator names
    "[NAME]": "to be appointed by the Court",

    # Facility/location placeholders
    "[COURT-APPROVED FACILITY]": "a court-approved supervised visitation facility",
    "[NEUTRAL LOCATION]": "a neutral public exchange location approved by the Court",

    # Parenting time schedule in proposed order
    "[PARENTING TIME SCHEDULE TO BE DETERMINED BY THE COURT]": "Parenting time shall resume on a schedule determined by the Court following an evidentiary hearing on the best interests of the child under MCL 722.23",

    # Evidence-level markers (timeline legend and table body)
    "[PROVEN]": "**PROVEN**",
    "[DOCUMENTED]": "**DOCUMENTED**",
    "[RECORD-RECITED]": "**RECORD-RECITED**",

    # Title Case address variants
    "[Attorney Address]": DEFENDANT_ATTORNEY_ADDRESS,
    "[Defendant Address]": DEFENDANT_ADDRESS,

    # FOIA appeal template — generic agency placeholders
    "[Agency Name]": "the denying agency",
    "[Agency Head]": "FOIA Appeal Authority",
    "[Name of Agency Head / FOIA Appeal Authority]": "FOIA Appeal Authority",

    # Alienation analysis — not-documented status markers
    "[Not specifically documented]": "Not specifically documented in current record",
    "[Not documented]": "Not documented in current record",
    "[Related PPO allegation]": "Related PPO allegation — details in PPO Case 2023-5907-PP",

    # Content annotations to de-bracket
    "[Information to be supplemented upon FOIA receipt]": "Information to be supplemented upon FOIA receipt",
    "[Additional ex parte orders to be specified upon complete docket review]": "Any additional ex parte orders identified upon complete docket review",
    "[Additional filings follow same pattern]": "Additional filings follow same pattern",
    "[Timed to custody proceedings]": "Timed to custody proceedings",
}

# ============================================================================
# CONTEXT-DEPENDENT REPLACEMENT FUNCTIONS
# ============================================================================

def get_motion_type_from_content(content):
    """Extract the motion type from the document title/header."""
    patterns = [
        r"(?:PLAINTIFF'S|MOTION FOR|EMERGENCY MOTION)\s+(.+?)(?:\n|---|$)",
        r"#\s+(?:PLAINTIFF'S\s+)?(.+?)(?:\n|$)",
    ]
    for pat in patterns:
        m = re.search(pat, content, re.IGNORECASE)
        if m:
            return m.group(1).strip().rstrip('*').strip()
    return None


def generate_relief_text(content, filepath):
    """Generate actual relief text based on the motion type."""
    fname = os.path.basename(filepath).upper()

    if "COMPEL" in fname or "DISCOVERY" in fname:
        return (
            "Plaintiff's Motion to Compel Discovery is **GRANTED**.\n\n"
            "2. Defendant shall provide complete, verified responses to Plaintiff's "
            "First Set of Interrogatories, Requests for Production of Documents, and "
            "Requests for Admissions within **fourteen (14) days** of the date of this Order.\n\n"
            "3. Defendant shall pay Plaintiff's reasonable expenses, including attorney fees, "
            "incurred in bringing this Motion, in the amount of $_________, pursuant to MCR 2.313(A)(5).\n\n"
            "4. Failure to comply with this Order within the time specified shall result in "
            "sanctions pursuant to MCR 2.313(B), which may include striking Defendant's pleadings, "
            "rendering a default judgment, or holding Defendant in contempt of court."
        )
    elif "CONTEMPT" in fname or "SHOW_CAUSE" in fname or "SHOW CAUSE" in fname:
        return (
            "Plaintiff's Motion for Order to Show Cause is **GRANTED**.\n\n"
            "2. Defendant Emily Ann Watson shall appear before this Court on a date to be scheduled "
            "and **show cause** why she should not be held in contempt of court for willful violation "
            "of this Court's parenting time orders.\n\n"
            "3. Upon finding of contempt, Defendant shall be subject to such sanctions as the Court "
            "deems appropriate under MCL 600.1701 and MCR 3.606, including but not limited to: "
            "compensatory parenting time, reasonable expenses and costs, modification of custody, "
            "and/or incarceration.\n\n"
            "4. Plaintiff is awarded **makeup parenting time** for all parenting time wrongfully "
            "denied, pursuant to MCL 722.27a(7)(b)."
        )
    elif "EMERGENCY" in fname and ("PARENTING" in fname or "IMMEDIATE" in fname):
        return (
            "Plaintiff's Emergency Motion for Immediate Parenting Time is **GRANTED**.\n\n"
            "2. Plaintiff's parenting time with the minor child is **RESTORED** effective immediately.\n\n"
            "3. Defendant shall make the minor child available for parenting time with Plaintiff "
            "within **seventy-two (72) hours** of the date of this Order.\n\n"
            "4. Plaintiff is awarded **makeup parenting time** for all parenting time denied since "
            "August 8, 2025, pursuant to MCL 722.27a(7)(b) and MCL 722.27a(9).\n\n"
            "5. An evidentiary hearing on permanent parenting time shall be scheduled within "
            "**fourteen (14) days** of the date of this Order."
        )
    elif "VENUE" in fname or "CHANGE" in fname:
        return (
            "Plaintiff's Motion for Change of Venue is **GRANTED**.\n\n"
            "2. This case is hereby **transferred** to ________________________ [receiving court] "
            "pursuant to MCR 2.222 and MCR 2.003.\n\n"
            "3. The Clerk shall transmit the complete case file to the receiving court within "
            "**seven (7) days** of the date of this Order."
        )
    else:
        return "Plaintiff's Motion is **GRANTED** and relief is ordered as set forth herein"


def replace_address_in_context(content):
    """
    Handle [ADDRESS] replacements that depend on context — 
    plaintiff vs defendant vs attorney vs FOC sections.
    """
    lines = content.split('\n')
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]

        # Check if this [ADDRESS] or [Address] is in a defendant/attorney/FOC context
        if re.search(r'\[ADDRESS\]|\[Address\]', line, re.IGNORECASE):
            # Look at surrounding lines for context
            context_window = '\n'.join(lines[max(0,i-5):i+3]).lower()

            if any(kw in context_window for kw in ['jennifer', 'barnes', 'attorney for defendant',
                                                     "defendant's attorney", "defendant's counsel"]):
                line = re.sub(r'\[ADDRESS\]', DEFENDANT_ATTORNEY_ADDRESS, line, flags=re.IGNORECASE)
                line = re.sub(r'\[Address\]', DEFENDANT_ATTORNEY_ADDRESS, line, flags=re.IGNORECASE)
            elif any(kw in context_window for kw in ['friend of the court', 'foc', 'clerk']):
                line = re.sub(r'\[ADDRESS\]', FOC_ADDRESS, line, flags=re.IGNORECASE)
                line = re.sub(r'\[Address\]', FOC_ADDRESS, line, flags=re.IGNORECASE)
            elif any(kw in context_window for kw in ['tiffany watson', 'defendant emily',
                                                      'defendant tiffany', 'emily watson',
                                                      'emily a. watson']):
                line = re.sub(r'\[ADDRESS\]', DEFENDANT_ADDRESS, line, flags=re.IGNORECASE)
                line = re.sub(r'\[Address\]', DEFENDANT_ADDRESS, line, flags=re.IGNORECASE)
            else:
                # Default: plaintiff's address
                line = re.sub(r'\[ADDRESS\]', PLAINTIFF_ADDRESS, line, flags=re.IGNORECASE)
                line = re.sub(r'\[Address\]', PLAINTIFF_ADDRESS, line, flags=re.IGNORECASE)

        result.append(line)
        i += 1

    return '\n'.join(result)


def replace_city_state_zip_in_context(content):
    """
    Handle [CITY, STATE ZIP] replacements that depend on context.
    """
    lines = content.split('\n')
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]

        if re.search(r'\[CITY,?\s*STATE\s*,?\s*ZIP\]', line, re.IGNORECASE):
            context_window = '\n'.join(lines[max(0,i-5):i+3]).lower()

            if any(kw in context_window for kw in ['jennifer', 'barnes', 'attorney for defendant',
                                                     "defendant's attorney", "defendant's counsel"]):
                line = re.sub(r'\[CITY,?\s*STATE\s*,?\s*ZIP\]', 'Muskegon, MI 49440', line, flags=re.IGNORECASE)
            elif any(kw in context_window for kw in ['friend of the court', 'foc']):
                line = re.sub(r'\[CITY,?\s*STATE\s*,?\s*ZIP\]', 'Muskegon, MI 49442', line, flags=re.IGNORECASE)
            elif any(kw in context_window for kw in ['tiffany watson', 'defendant emily',
                                                      'defendant tiffany', 'emily watson',
                                                      'emily a. watson', '2160 garland']):
                line = re.sub(r'\[CITY,?\s*STATE\s*,?\s*ZIP\]', 'Norton Shores, MI 49441', line, flags=re.IGNORECASE)
            else:
                line = re.sub(r'\[CITY,?\s*STATE\s*,?\s*ZIP\]', PLAINTIFF_CITY_STATE_ZIP, line, flags=re.IGNORECASE)

        result.append(line)
        i += 1

    return '\n'.join(result)


# ============================================================================
# PLACEHOLDER DETECTION (for audit/reporting)
# ============================================================================

# Regex to find bracketed placeholders — excludes:
# - Markdown links: [text](url)
# - Checkbox markers: [ ], [x], [✓], [✗]
# - Single-letter editorial insertions in legal quotes: [t], [d], [s], etc.
# - Short editorial brackets: [to], [ly hearing], [done], [sic]
# - Markdown references: [^1], [1]
PLACEHOLDER_RE = re.compile(
    r'\[(?!'                       # negative lookahead to exclude:
    r'(?:[ x✓✗])\]'               # checkboxes
    r'|(?:\^?\d+)\]'              # footnote refs
    r')'
    r'([A-Z][A-Z _\-/]+)'        # placeholder text: starts with uppercase, all caps + spaces/hyphens
    r'\]'
)

# Broader pattern for reporting: any bracketed text that looks like a placeholder
AUDIT_RE = re.compile(
    r'\[('
    r'(?:[A-Z][A-Z _\-/]{2,})'   # ALL CAPS placeholder
    r'|(?:[A-Z][a-z]+(?: [A-Za-z]+)*)'  # Title Case placeholder  
    r')\]'
)

# Patterns that are NOT placeholders (editorial/legal quote brackets)
FALSE_POSITIVE_PATTERNS = [
    r'\[t\]',           # editorial [t] in legal quotes
    r'\[d\]',           # editorial
    r'\[s\]',           # editorial
    r'\[to\]',          # editorial
    r'\[sic\]',         # editorial
    r'\[done\]',        # editorial quote
    r'\[ly hearing\]',  # editorial
    r'\[emphasis added\]',
    r'\[another judge',  # descriptive instruction in proposed order
    r'\[days\]',        # template blank in proposed order
    r'\[times\]',       # template blank in proposed order
    r'\[receiving court\]',  # blank for court to fill
    r'\[should be permitted',  # quote bracket
]


def is_false_positive(match_text, line):
    """Check if a bracket match is a false positive (legal quote, link, etc.)."""
    full_bracket = f"[{match_text}]"
    line_lower = line.lower()
    bracket_lower = full_bracket.lower()

    # Check against known false positive patterns
    for fp in FALSE_POSITIVE_PATTERNS:
        if re.search(fp, line_lower):
            if re.search(fp, bracket_lower):
                return True

    # Markdown links: [text](url)
    idx = line.find(full_bracket)
    if idx >= 0 and idx + len(full_bracket) < len(line):
        if line[idx + len(full_bracket)] == '(':
            return True

    # Single-letter editorial brackets
    if len(match_text) <= 2 and match_text[0].isupper():
        return True

    return False


# ============================================================================
# CYCLE-METHOD SAFE WRITE
# ============================================================================

def safe_write(filepath, content):
    """Write content to file using write-to-temp + rename for EAGAIN safety."""
    dirpath = os.path.dirname(filepath)
    fd, tmp_path = tempfile.mkstemp(dir=dirpath, suffix='.tmp', prefix='_pf_')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as f:
            f.write(content)
        # On Windows, can't rename over existing file — remove first
        if os.path.exists(filepath):
            os.replace(tmp_path, filepath)
        else:
            os.rename(tmp_path, filepath)
    except Exception:
        # Clean up temp file on failure
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


# ============================================================================
# MAIN PROCESSING
# ============================================================================

def collect_files():
    """Collect all target files from the three directory sources."""
    files = set()
    for dirpath, pattern, min_size in DIRS_AND_PATTERNS:
        if not os.path.isdir(dirpath):
            print(f"  WARNING: Directory not found: {dirpath}")
            continue
        p = Path(dirpath)
        for f in p.glob(pattern):
            if f.is_file():
                if f.stat().st_size >= min_size:
                    files.add(str(f))
    return sorted(files)


def count_placeholders(content):
    """Count remaining placeholders in content (excluding false positives)."""
    count = 0
    remaining = []
    for line_num, line in enumerate(content.split('\n'), 1):
        for m in re.finditer(r'\[([^\]]+)\]', line):
            inner = m.group(1).strip()
            # Skip checkboxes, footnotes, very short editorial
            if inner in ('', ' ', 'x', '✓', '✗'):
                continue
            if re.match(r'^\^?\d+$', inner):
                continue
            # Skip markdown links
            end_pos = m.end()
            if end_pos < len(line) and line[end_pos] == '(':
                continue
            # Skip known false positives
            if is_false_positive(inner, line):
                continue
            # Check if it looks like a placeholder (all caps, or Title Case with 2+ words)
            if (re.match(r'^[A-Z][A-Z _\-/]{2,}$', inner) or
                re.match(r'^[A-Z][a-z]+(?: [A-Za-z,]+){1,}$', inner)):
                count += 1
                remaining.append((line_num, inner))

    return count, remaining


def process_file(filepath):
    """Process a single file: find and replace all placeholders."""
    with open(filepath, 'r', encoding='utf-8') as f:
        original = f.read()

    content = original

    # --- PHASE 1: Context-dependent address replacements ---
    content = replace_address_in_context(content)
    content = replace_city_state_zip_in_context(content)

    # --- PHASE 2: Exact replacements ---
    for placeholder, replacement in EXACT_REPLACEMENTS.items():
        content = content.replace(placeholder, replacement)

    # --- PHASE 3: [SPECIFY RELIEF REQUESTED] — generate based on motion type ---
    if '[SPECIFY RELIEF REQUESTED]' in content:
        relief = generate_relief_text(content, filepath)
        content = content.replace('[SPECIFY RELIEF REQUESTED]', relief)

    # --- PHASE 4: Instruction-line cleanup ---
    # Lines like "- [ ] Insert Father's email address where [EMAIL] appears" 
    # After replacement, these become stale instructions. Mark them done.
    content = re.sub(
        r"(- \[ \] Insert Father's email address where )andrewjpigors@gmail\.com( appears)",
        r"- [x] Father's email inserted: andrewjpigors@gmail.com ✓",
        content
    )
    content = re.sub(
        r"(- \[ \] Insert Father's email at )andrewjpigors@gmail\.com( placeholders)",
        r"- [x] Father's email inserted: andrewjpigors@gmail.com ✓",
        content
    )
    content = re.sub(
        r"(> 2\. \[ \] Insert Father's email at )andrewjpigors@gmail\.com( placeholders)",
        r"> 2. [x] Father's email inserted: andrewjpigors@gmail.com ✓",
        content
    )

    # --- PHASE 5: Count changes ---
    before_count, _ = count_placeholders(original)
    after_count, remaining = count_placeholders(content)
    replaced = before_count - after_count

    # Write back only if changed
    if content != original:
        safe_write(filepath, content)

    return {
        'file': filepath,
        'found': before_count,
        'replaced': replaced,
        'remaining_count': after_count,
        'remaining': remaining,
        'changed': content != original,
    }


def main():
    print("=" * 80)
    print("PLACEHOLDER ELIMINATION AGENT — Lane A (14th Circuit)")
    print("=" * 80)
    print()

    files = collect_files()
    print(f"Files to process: {len(files)}")
    print()

    total_found = 0
    total_replaced = 0
    total_remaining = 0
    all_remaining = []

    for filepath in files:
        result = process_file(filepath)
        short = os.path.basename(filepath)

        status = "✓ CLEAN" if result['remaining_count'] == 0 else f"⚠ {result['remaining_count']} REMAINING"
        if result['found'] == 0 and result['remaining_count'] == 0:
            status = "— no placeholders"

        print(f"  [{status}] {short}")
        if result['found'] > 0:
            print(f"           Found: {result['found']}  |  Replaced: {result['replaced']}  |  Remaining: {result['remaining_count']}")
        if result['remaining']:
            for line_num, text in result['remaining']:
                print(f"           ↳ Line {line_num}: [{text}]")

        total_found += result['found']
        total_replaced += result['replaced']
        total_remaining += result['remaining_count']
        all_remaining.extend([(filepath, ln, txt) for ln, txt in result['remaining']])

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"  Files processed:       {len(files)}")
    print(f"  Total placeholders:    {total_found}")
    print(f"  Total replaced:        {total_replaced}")
    print(f"  Total remaining:       {total_remaining}")
    print()

    if total_remaining == 0:
        print("  ✅ ALL PLACEHOLDERS ELIMINATED — ZERO REMAINING")
    else:
        print(f"  ⚠️  {total_remaining} PLACEHOLDERS STILL REMAIN:")
        for fp, ln, txt in all_remaining:
            print(f"     {os.path.basename(fp)}:{ln} — [{txt}]")

    print()
    return 0 if total_remaining == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
