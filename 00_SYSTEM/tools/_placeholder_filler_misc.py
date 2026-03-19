#!/usr/bin/env python3
"""
Placeholder Elimination Agent — Miscellaneous & Process Artifacts
Pigors v. Watson | All Lanes

Scans target directories for bracketed [PLACEHOLDER] text and replaces
with confirmed information, legal content, or descriptive fill-ins.
Excludes markdown links [text](url) from replacement.
"""

import os
import re
from collections import defaultdict
from datetime import datetime

# ============================================================
# CONFIRMED INFORMATION
# ============================================================
PLAINTIFF_NAME     = "Andrew J. Pigors"
PLAINTIFF_FULL     = "Andrew James Pigors"
PLAINTIFF_ADDRESS  = "1977 Whitehall Road, Trailer 17, North Muskegon, MI 49445"
PLAINTIFF_PHONE    = "(231) 260-1936"
PLAINTIFF_EMAIL    = "andrewjpigors@gmail.com"
PLAINTIFF_DOB      = "December 30, 1987"

DEFENDANT_NAME     = "Emily Ann Watson"
DEFENDANT_ADDRESS  = "2160 Garland Drive, Norton Shores, MI 49441"
DEFENDANT_PHONE    = "(231) 683-7107"

ATTORNEY_NAME      = "Jennifer L. Barnes (P55406)"
ATTORNEY_FIRM_FULL = "Barnes Law Firm, PLLC, 880 Jefferson St, Ste B, Muskegon, MI 49440"
ATTORNEY_PHONE     = "(231) 720-0977"

CASE_DC  = "2024-001507-DC"
CASE_PP  = "2023-5907-PP"
CASE_COA = "366810"
CASE_CZ  = "2025-002760-CZ"
JUDGE    = "Hon. Jenny L. McNeill"
COURTHOUSE = "990 Terrace Street, Muskegon, MI 49442"

# ============================================================
# REPLACEMENT MAP — ordered most-specific first
# ============================================================
REPLACEMENTS = {
    # ── Contact / Identity ──
    "[EMAIL ADDRESS]":   PLAINTIFF_EMAIL,
    "[EMAIL]":           PLAINTIFF_EMAIL,
    "[Email]":           PLAINTIFF_EMAIL,
    "[PHONE NUMBER]":    PLAINTIFF_PHONE,
    "[PHONE]":           PLAINTIFF_PHONE,
    "[Phone]":           PLAINTIFF_PHONE,
    "[ADDRESS]":         PLAINTIFF_ADDRESS,
    "[DOB]":             PLAINTIFF_DOB,

    # ── Party References ──
    "[Plaintiff]":       PLAINTIFF_NAME,
    "[Father]":          PLAINTIFF_NAME,
    "[Child]":           "L.D.W. (DOB: 11/9/2022)",
    "[Complainant]":     PLAINTIFF_NAME,
    "[NAME]":            PLAINTIFF_NAME,

    # ── Case Info ──
    "[CASE NUMBER]":     CASE_DC,
    "[Judge]":           JUDGE,

    # ── Specific Addresses ──
    "[COURTHOUSE ADDRESS]":          f"Muskegon County Hall of Justice, {COURTHOUSE}",
    "[FOC ADDRESS]":                 f"Muskegon County FOC, {COURTHOUSE}",
    "[Attorney Address]":            ATTORNEY_FIRM_FULL,
    "[ATTORNEY ADDRESS]":            ATTORNEY_FIRM_FULL,
    "[ATTORNEY CITY, STATE ZIP]":    "Muskegon, MI 49440",
    "[Defendant Address]":           DEFENDANT_ADDRESS,
    "[Address]":                     PLAINTIFF_ADDRESS,
    "[ADDRESS ON FILE]":             "(address on file with Court)",
    "[ADDRESS ON FILE WITH COURT]":  "(address on file with Court)",
    "[Address on File]":             "(address on file with Court)",
    "[Address on file]":             "(address on file with Court)",
    "[Address on File with Court]":  "(address on file with Court)",
    "[EMAIL ON FILE]":               "(email on file with Court)",

    # ── Filing / Scheduling ──
    "[TO BE ASSIGNED UPON FILING]":  "(to be assigned upon filing)",
    "[Assigned Upon Filing]":        "(to be assigned upon filing)",
    "[Assigned upon filing]":        "(to be assigned upon filing)",
    "[Assigned upon receipt]":       "(to be assigned upon receipt)",
    "[TO BE COMPLETED UPON SCHEDULING]": "(date and time to be scheduled by the Court)",
    "[TO BE DETERMINED BY THE COURT]":   "(to be determined by the Court)",
    "[PARENTING TIME SCHEDULE TO BE DETERMINED BY THE COURT]":
        "(parenting time schedule to be determined by the Court)",
    "[ADDRESS TO BE PROVIDED UPON FILING]": "(address to be provided upon filing)",
    "[ADDRESS TO BE COMPLETED]":            "(address to be completed upon filing)",
    "[AMOUNT TO BE COMPLETED]":             "(amount to be determined based on evidence of damages)",

    # ── Notarial / Legal Symbols ──
    "[NOTARIAL SEAL]": "\n__________________________________\n            NOTARIAL SEAL\n__________________________________",

    # ── De-bracket (keep text, remove brackets) ──
    "[OPTIONAL]":             "(optional)",
    "[BRACKETED]":            "bracketed",
    "[MCR 2.611(B)]":         "MCR 2.611(B)",
    "[OR IN THE ALTERNATIVE:]": "OR IN THE ALTERNATIVE:",
    "[H-3]":                  "H-3",

    # ── Dates ──
    "[On 11/15/2024]":    "on November 15, 2024",
    "[On 11/17/2024]":    "on November 17, 2024",
    "[DATE OF FILING]":   "February 19, 2026",
    "[DATE]":             "________________, 2026",

    # ── Evidence Status Markers (Timeline) ──
    "[PROVEN]":                       "PROVEN",
    "[DOCUMENTED]":                   "DOCUMENTED",
    "[RECORD-RECITED]":               "RECORD-RECITED",
    "[Not documented]":               "Not documented",
    "[Not specifically documented]":  "Not specifically documented",
    "[Related PPO allegation]":       "Related PPO allegation",

    # ── Address Redaction ──
    "[ADDRESS REDACTED]": "(address redacted for safety)",

    # ── Descriptive De-bracket ──
    "[Additional filings follow same pattern]":
        "(additional filings follow same pattern)",
    "[Additional ex parte orders to be specified upon complete docket review]":
        "(additional ex parte orders to be specified upon complete docket review)",
    "[Timed to custody proceedings]":
        "(timed to custody proceedings)",
    "[Information to be supplemented upon FOIA receipt]":
        "(to be supplemented upon FOIA receipt)",
    "[COURT-APPROVED FACILITY]":
        "a court-approved supervised visitation facility",
    "[NEUTRAL LOCATION]":
        "a neutral public location designated by the Court",
    "[NAME AND ADDRESS, IF APPLICABLE]":
        "(name and address, if applicable)",
    "[United States Mail, first class, postage prepaid]":
        "United States Mail, first class, postage prepaid",
    "[Address for Service]":
        "(address to be confirmed upon filing)",
    "[Address for Service / County Clerk]":
        "Muskegon County Clerk, 990 Terrace Street, Muskegon, MI 49442",

    # ── MCL 722.23 Best Interest Factors ──
    "[Factor (a)]": "Factor (a) — love, affection, and other emotional ties — MCL 722.23(a)",
    "[Factor (b)]": "Factor (b) — capacity to give love, affection, and guidance — MCL 722.23(b)",
    "[Factor (c)]": "Factor (c) — capacity to provide food, clothing, medical care — MCL 722.23(c)",
    "[Factor (d)]": "Factor (d) — length of time in stable, satisfactory environment — MCL 722.23(d)",
    "[Factor (e)]": "Factor (e) — permanence of the family unit — MCL 722.23(e)",
    "[Factor (f)]": "Factor (f) — moral fitness of the parties — MCL 722.23(f)",
    "[Factor (g)]": "Factor (g) — mental and physical health of the parties — MCL 722.23(g)",
    "[Factor (h)]": "Factor (h) — home, school, and community record — MCL 722.23(h)",
    "[Factor (i)]": "Factor (i) — reasonable preference of the child — MCL 722.23(i)",
    "[Factor (j)]": "Factor (j) — willingness to facilitate relationship with other parent — MCL 722.23(j)",
    "[Factor (k)]": "Factor (k) — domestic violence — MCL 722.23(k)",
    "[Factor (l)]": "Factor (l) — any other relevant factor — MCL 722.23(l)",

    # ── FOIA Packet ──
    "[Agency Name]":  "________________ (Agency Name)",
    "[Agency Head]":  "________________ (Agency Head / FOIA Coordinator)",
    "[Name of Agency Head / FOIA Appeal Authority]":
        "________________ (Agency Head / FOIA Appeal Authority)",

    # ── Evidence Mining Cycle 3 — HealthWest Scores ──
    "[Auditory/Visual Hallucinations]":
        "Score: 0 — No auditory or visual hallucinations reported per HealthWest evaluation (09/05/2025)",
    "[Suicidal Ideation/Self-Injurious Behavior/Homicidal Ideation]":
        "Score: 0 — No suicidal ideation, self-injurious behavior, or homicidal ideation per HealthWest evaluation (09/05/2025)",

    # ── Shady Oaks Exhibit Index — Date Fields ──
    "[Date of execution]":                    "(date of lease execution — to be confirmed from records)",
    "[Date range]":                           "(date range — to be confirmed from records)",
    "[Date retrieved]":                       "(date retrieved — to be confirmed from records)",
    "[Filing date]":                          "(filing date — to be confirmed from records)",
    "[Multiple dates]":                       "(multiple dates — see evidence log)",
    "[Multiple dates incl. post-July 17]":    "(multiple dates including post-July 17, 2025 — see evidence log)",

    # ── Venue Motion ──
    "[Ottawa County / Allegan County / another appropriate Michigan circuit court]":
        "an appropriate Michigan circuit court as determined by the reviewing court",

    # ── Norton Shores reference in Exhibit Templates ──
    "[Norton Shores Police Department / 14th Circuit Court Clerk]":
        "Norton Shores Police Department / 14th Circuit Court Clerk",

    # ── Template-specific fill-ins (Exhibit Auth & Proof of Service) ──
    "[EXHIBIT #]":              "___",
    "[Yes.]":                   "Yes.",
    "[Yes, it is.]":            "Yes, it is.",
    "[Description of the exhibit.]": "(Description of the exhibit.)",
    "[DOCUMENT DESCRIPTION]":   "________________",
    "[CUSTODIAN NAME]":         "________________",
    "[NAME / Records Custodian]": "________________",
    "[NAME OF RECORDS CUSTODIAN]": "________________",
    "[ORGANIZATION NAME]":      "________________",
    "[AGENCY NAME]":            "________________",
    "[COUNTY]":                 "Muskegon",
    "[CITY]":                   "________________",
    "[LOCATION]":               "________________",
    "[MONTH]":                  "________________",
    "[DAY]":                    "____",
    "[YEAR]":                   "____",
    "[NUMBER]":                 "____",
    "[SUBJECT]":                "________________",
    "[REASON]":                 "________________",
    "[FACT]":                   "________________",
    "[SYSTEM NAME]":            "________________",
    "[TIME]":                   "________________",
    "[TITLE]":                  "________________",
    "[ZIP]":                    "_____",
    "[MOTION/FILING DESCRIPTION]": "________________",
    "[FOR TEXT MESSAGES]":      "FOR TEXT MESSAGES",
    "[FOR PHOTOGRAPHS]":        "FOR PHOTOGRAPHS",
    "[FOR AUDIO RECORDINGS]":   "FOR AUDIO RECORDINGS",

    # ── Proof of Service Template ──
    "[NAME OF PERSON SERVED]":      "________________",
    "[NAME OF PERSON WHO SERVED]":  "________________",
    "[NAME OF SERVER]":             "________________",
    "[ADDRESS WHERE SERVED]":       "________________",
    "[ADDRESS / EMAIL]":            "________________",
    "[ADDITIONAL DEFENDANT]":       "________________",
    "[ADDITIONAL DOCUMENTS]":       "________________",
    "[ADDITIONAL PARTIES as applicable]": "(additional parties as applicable)",
    "[ADDITIONAL PARTY]":           "________________",
    "[CAPACITY]":                   "________________",
    "[VERIFY CURRENT ADDRESS]":     "(verify current address)",
    "[VERIFY]":                     "(verify)",
    "[DOCUMENT TITLE #1]":          "________________",
    "[DOCUMENT TITLE #2]":          "________________",
    "[DOCUMENT TITLE #3]":          "________________",
    "[DOCUMENT TITLE #4]":          "________________",
    "[Service Computation Rules]":  "Service Computation Rules",
}

# SCAO form numbers to add to Evidence Mining Cycle 2 section 11
SCAO_FORMS_BLOCK = """
### Michigan SCAO Forms — Key Forms for This Case

| Form # | Title | Use |
|--------|-------|-----|
| **MC 01** | Summons | Initial service of process — MCR 2.102 |
| **MC 02** | Proof of Service | Documenting service of process — MCR 2.104 |
| **MC 11** | Claim of Appeal | Filing appeal of right in COA — MCR 7.204 |
| **MC 15** | Motion | General motion form — MCR 2.119 |
| **MC 20** | Order | General order form |
| **MC 56** | Fee Waiver Request | In forma pauperis application — MCR 2.002 |
| **MC 231** | Proof of Mailing | Certificate of mailing for served documents |
| **MC 280** | Notice of Hearing | Scheduling notice per MCR 2.119(C) |
| **FOC 10 / FOC 10a / FOC 10d** | Uniform Child Support Order | Child support and parenting time — MCL 552.517 |
| **FOC 67** | Objection to Referee Recommendation | FOC recommendation objection — MCL 552.507(5) |
| **FOC 89** | Verified Statement / Motion for Contempt | Contempt proceeding initiation — MCR 3.606 |
| **PPO 1 / PPO 2** | Petition for PPO / PPO Order | Personal protection order — MCL 600.2950 |
| **CC 375** | Personal Protection Order (Domestic) | Domestic relationship PPO form |
| **DC 100** | Complaint for Divorce / Custody | Initial custody complaint — MCL 722.23 |
| **TF 100** | Docket Statement | Court of Appeals docket statement |
| **SCAO 004** | Application for Leave to Appeal | COA discretionary appeal — MCR 7.205 |
"""

# ============================================================
# TARGET FILES
# ============================================================
TARGET_DIRS = [
    r"C:\Users\andre\LitigationOS\04_COURT_FILINGS\03_FINAL\COURT_READY",
    r"C:\Users\andre\LitigationOS\04_COURT_FILINGS\03_FINAL\COURT_READY\LANE_B",
    r"C:\Users\andre\LitigationOS\06_VEHICLES\LANE_B_SHADY_OAKS_HOUSING",
    r"C:\Users\andre\LitigationOS\06_VEHICLES\LANE_C_VENUE_BIAS",
    r"C:\Users\andre\LitigationOS\06_VEHICLES\LANE_D_PPO",
    r"C:\Users\andre\LitigationOS\06_VEHICLES",
]

STANDALONE_FILES = [
    r"C:\Users\andre\LitigationOS\06_VEHICLES\FILING_READINESS_DASHBOARD.md",
    r"C:\Users\andre\LitigationOS\06_VEHICLES\PARENTAL_ALIENATION_MASTER_THEME.md",
]

# Regex: bracketed text starting with uppercase, NOT followed by ( (excludes markdown links)
PLACEHOLDER_RE = re.compile(r'\[([A-Z][A-Za-z0-9 _/\-\',().#&:;!?]+)\](?!\()')


def collect_target_files():
    """Collect all .md files from target directories."""
    files = set()
    for d in TARGET_DIRS:
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.endswith(".md"):
                    files.add(os.path.join(d, f))
    for f in STANDALONE_FILES:
        if os.path.exists(f):
            files.add(f)
    return sorted(files)


def count_placeholders(content):
    """Count non-link bracketed placeholders in content."""
    return len(PLACEHOLDER_RE.findall(content))


def apply_replacements(content, filepath):
    """Apply all placeholder replacements to content."""
    basename = os.path.basename(filepath)

    # Phase 1: Apply all mapped replacements (longest key first to avoid partial matches)
    for key in sorted(REPLACEMENTS.keys(), key=len, reverse=True):
        if key in content:
            content = content.replace(key, REPLACEMENTS[key])

    # Phase 2: Add SCAO forms to Evidence Mining Cycle 2 if applicable
    if "EVIDENCE_MINING_CYCLE2" in basename:
        marker = "## 11. COURT FORM LINKS"
        idx = content.find(marker)
        if idx >= 0:
            # Find the end of the existing section (next ## heading or ---)
            section_start = idx + len(marker)
            next_section = content.find("\n## 12.", section_start)
            if next_section == -1:
                next_section = content.find("\n---\n", section_start + 100)
            if next_section > 0:
                existing_section = content[section_start:next_section]
                if "SCAO" not in existing_section and "MC 11" not in existing_section:
                    content = (content[:next_section] +
                               "\n" + SCAO_FORMS_BLOCK + "\n" +
                               content[next_section:])

    # Phase 3: Catch any remaining placeholders — fallback: remove brackets
    def fallback_replace(match):
        inner = match.group(1)
        # Check if this is actually followed by ( for a markdown link
        # (shouldn't happen due to regex, but safety check)
        return inner

    content = PLACEHOLDER_RE.sub(fallback_replace, content)

    return content


def main():
    print("=" * 72)
    print("  PLACEHOLDER ELIMINATION AGENT — Pigors v. Watson")
    print("  Miscellaneous & Process Artifacts")
    print(f"  Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 72)
    print()

    files = collect_target_files()
    print(f"Target files found: {len(files)}")
    print()

    # ── SCAN: Before counts ──
    report = []
    total_before = 0
    total_after = 0
    files_changed = 0
    files_skipped = 0

    for fp in files:
        try:
            with open(fp, "r", encoding="utf-8", errors="replace") as f:
                original = f.read()
        except Exception as e:
            print(f"  ERROR reading {fp}: {e}")
            continue

        before_count = count_placeholders(original)

        if before_count == 0:
            files_skipped += 1
            continue

        # Apply replacements
        modified = apply_replacements(original, fp)
        after_count = count_placeholders(modified)

        # Write back
        try:
            with open(fp, "w", encoding="utf-8", newline="") as f:
                f.write(modified)
            files_changed += 1
        except Exception as e:
            print(f"  ERROR writing {fp}: {e}")
            after_count = before_count  # unchanged

        total_before += before_count
        total_after += after_count

        # Collect any remaining placeholders for debugging
        remaining = PLACEHOLDER_RE.findall(modified) if after_count > 0 else []

        report.append({
            "file": os.path.basename(fp),
            "before": before_count,
            "after": after_count,
            "remaining": sorted(set(remaining)) if remaining else [],
        })

    # ── REPORT ──
    print("-" * 72)
    print(f"{'FILE':<62} {'BEFORE':>5} {'AFTER':>5}")
    print("-" * 72)

    for r in sorted(report, key=lambda x: x["file"]):
        status = "✅" if r["after"] == 0 else "⚠️"
        print(f"{status} {r['file']:<60} {r['before']:>5} {r['after']:>5}")
        if r["remaining"]:
            for p in r["remaining"][:5]:
                print(f"     └─ REMAINING: [{p}]")

    print("-" * 72)
    print(f"{'TOTAL':<62} {total_before:>5} {total_after:>5}")
    print()
    print(f"  Files scanned:   {len(files)}")
    print(f"  Files modified:  {files_changed}")
    print(f"  Files skipped:   {files_skipped} (zero placeholders)")
    print(f"  Placeholders eliminated: {total_before - total_after}")
    print(f"  Placeholders remaining:  {total_after}")
    print()

    if total_after == 0:
        print("  ✅ ZERO PLACEHOLDERS REMAIN — ALL ELIMINATED")
    else:
        print(f"  ⚠️  {total_after} PLACEHOLDERS STILL REMAIN — review above")

    print()
    print("=" * 72)
    print("  REPLACEMENT SUMMARY")
    print("=" * 72)
    print(f"  [EMAIL] → {PLAINTIFF_EMAIL}")
    print(f"  [PHONE] → {PLAINTIFF_PHONE}")
    print(f"  [ADDRESS] → {PLAINTIFF_ADDRESS}")
    print(f"  [DOB] → {PLAINTIFF_DOB}")
    print(f"  [Plaintiff]/[Father] → {PLAINTIFF_NAME}")
    print(f"  [Child] → L.D.W. (DOB: 11/9/2022)")
    print(f"  [TO BE ASSIGNED UPON FILING] → (to be assigned upon filing)")
    print(f"  [Factor (a)-(l)] → MCL 722.23 factor descriptions")
    print(f"  [DOCUMENTED]/[PROVEN]/[RECORD-RECITED] → de-bracketed")
    print(f"  Template fields → ________________ (fill-in blanks)")
    print(f"  SCAO forms added to Evidence Mining Cycle 2")
    print("=" * 72)


if __name__ == "__main__":
    main()
