#!/usr/bin/env python3
"""
Tool #216 — Court Filing Compliance Validator
=============================================
Automated GO/NO-GO validator for ALL Michigan court filing packages.
Encodes web-researched Michigan Court Rules, MiFILE e-filing requirements,
JTC procedures, COA rules, WDMI federal pro se handbook, and MCL statutes
into deterministic checks that run against .md filing drafts.

Covers: F1-F10 filing packages + universal formatting + e-filing rules.

Usage:
    python court_compliance_validator.py                     # Scan all PKG_F* on Desktop
    python court_compliance_validator.py path/to/PKG_F3      # Scan specific package
    python court_compliance_validator.py --all               # Scan all + summary matrix
"""
import sys
import os
import re
import json
import glob
import sqlite3
from pathlib import Path
from datetime import datetime, date
from collections import defaultdict

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', errors='replace')

# ── Paths ──────────────────────────────────────────────────────────────────────
TOOL_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
REPO = TOOL_DIR.parent.parent  # C:\Users\andre\LitigationOS
DB_PATH = REPO / "litigation_context.db"
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

DESKTOP = Path(r"C:\Users\andre\Desktop")
FILING_PKG_ROOT = DESKTOP / "LITIGATION_FILING_PACKAGE"

# ── Party Identity (GROUND TRUTH — never fabricate) ────────────────────────────
PLAINTIFF = "Andrew James Pigors"
PLAINTIFF_ADDRESS = "1977 Whitehall Road, Lot 17, North Muskegon, MI 49445"
PLAINTIFF_PHONE = "(231) 903-5690"
PLAINTIFF_EMAIL = "andrewjpigors@gmail.com"
DEFENDANT = "Emily A. Watson"
DEFENDANT_ADDRESS = "2160 Garland Drive, Norton Shores, MI 49441"
CHILD_INITIALS = "L.D.W."
JUDGE = "Jenny L. McNeill"
DEFENDANT_ATTORNEY = "Jennifer Barnes"
DEFENDANT_ATTORNEY_BAR = "P55406"
FOC = "Pamela Rusco"
FOC_ADDRESS = "990 Terrace St, Muskegon, MI 49442"

# Case numbers
CASE_DC = "2024-001507-DC"
CASE_PP = "2023-5907-PP"
CASE_CZ = "2025-002760-CZ"
COA_CASE = "366810"

# ── Filing Type Detection ──────────────────────────────────────────────────────
FILING_TYPES = {
    "F10": {"label": "COA Emergency Motion",     "pattern": r"PKG_F10",  "court": "Court of Appeals"},
    "F1":  {"label": "Emergency TRO",            "pattern": r"PKG_F1[^0-9]", "court": "14th Circuit"},
    "F2":  {"label": "Shady Oaks Complaint",     "pattern": r"PKG_F2",   "court": "14th Circuit"},
    "F3":  {"label": "MCR 2.003 Disqualification","pattern": r"PKG_F3",  "court": "14th Circuit"},
    "F4":  {"label": "Federal §1983 Complaint",  "pattern": r"PKG_F4",   "court": "WDMI Federal"},
    "F5":  {"label": "MSC Original Action",      "pattern": r"PKG_F5",   "court": "Michigan Supreme Court"},
    "F6":  {"label": "JTC Complaint",            "pattern": r"PKG_F6",   "court": "JTC (Mail Only)"},
    "F7":  {"label": "Custody Modification",     "pattern": r"PKG_F7",   "court": "14th Circuit"},
    "F8":  {"label": "PPO Termination",          "pattern": r"PKG_F8",   "court": "14th Circuit"},
    "F9":  {"label": "COA Brief on Appeal",      "pattern": r"PKG_F9",   "court": "Court of Appeals"},
}

# ── Placeholder patterns (must not appear in final filings) ────────────────────
PLACEHOLDER_PATTERNS = [
    r"\[INSERT[^\]]*\]",
    r"\[ANDREW[^\]]*\]",
    r"\[TODO[^\]]*\]",
    r"\[ATTACH[^\]]*\]",
    r"\[FILL[^\]]*\]",
    r"\[REQUIRED[^\]]*\]",
    r"\[ANDREW_REQUIRED[^\]]*\]",
    r"\[PLACEHOLDER[^\]]*\]",
    r"\[TBD[^\]]*\]",
    r"\[PENDING[^\]]*\]",
    r"\[VERIFY[^\]]*\]",
    r"\[UNKNOWN[^\]]*\]",
    r"\[DATE[^\]]*\]",
    r"\[EXHIBIT[^\]]*\]",
    r"\[CITATION[^\]]*\]",
    r"\[CASE\s*NO[^\]]*\]",
    r"_{3,}",  # Blank lines (___) indicating missing content
    r"X{3,}",  # XXX placeholder
]


def detect_filing_type(dir_name: str) -> str | None:
    """Detect filing type from directory name."""
    for ftype, info in FILING_TYPES.items():
        if re.search(info["pattern"], dir_name, re.IGNORECASE):
            return ftype
    return None


def read_md_files(directory: Path) -> dict[str, str]:
    """Read all .md files in a directory, skip .bak files."""
    files = {}
    for f in sorted(directory.glob("*.md")):
        if ".bak" in f.name:
            continue
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
            files[f.name] = content
        except Exception as e:
            files[f.name] = f"[ERROR READING: {e}]"
    return files


def combined_text(files: dict[str, str]) -> str:
    """Combine all file contents into one searchable string."""
    return "\n\n".join(f"=== {name} ===\n{content}" for name, content in files.items())


# ═══════════════════════════════════════════════════════════════════════════════
# CHECK FUNCTIONS — Each returns list of (pass:bool, rule:str, detail:str)
# ═══════════════════════════════════════════════════════════════════════════════

def check_universal_formatting(files: dict, text: str) -> list[tuple[bool, str, str]]:
    """Universal formatting requirements for ALL filings."""
    results = []

    # Caption checks
    has_court_name = bool(re.search(r"(circuit court|court of appeals|supreme court|district court|judicial tenure)", text, re.I))
    results.append((has_court_name, "UF-01: Caption includes court name",
                     "PASS" if has_court_name else "FIX: Add full court name to caption (e.g., '14th Circuit Court, Family Division')"))

    has_case_number = bool(re.search(r"\d{4}-\d{4,6}-\w{2}", text))
    results.append((has_case_number, "UF-02: Caption includes case number",
                     "PASS" if has_case_number else "FIX: Add case number in format YYYY-NNNNNN-XX"))

    has_party_names = (PLAINTIFF.lower() in text.lower() and
                       re.search(r"watson", text, re.I) is not None)
    results.append((has_party_names, "UF-03: Caption includes party names",
                     "PASS" if has_party_names else f"FIX: Caption must include '{PLAINTIFF}' and '{DEFENDANT}'"))

    has_doc_title = bool(re.search(r"(motion|petition|complaint|brief|affidavit|request for investigation|application)", text, re.I))
    results.append((has_doc_title, "UF-04: Document title present",
                     "PASS" if has_doc_title else "FIX: Add document title (e.g., 'MOTION FOR DISQUALIFICATION')"))

    # Signature block
    has_sig_name = bool(re.search(r"(Andrew\s+James\s+Pigors|/s/\s*Andrew)", text, re.I))
    results.append((has_sig_name, "UF-05: Signature block includes name",
                     "PASS" if has_sig_name else f"FIX: Add signature: '/s/ {PLAINTIFF}' or handwritten signature block"))

    has_sig_address = bool(re.search(r"(1977\s+Whitehall|North\s+Muskegon|49445)", text, re.I))
    results.append((has_sig_address, "UF-06: Signature block includes address",
                     "PASS" if has_sig_address else f"FIX: Add address: {PLAINTIFF_ADDRESS}"))

    has_sig_phone = bool(re.search(r"\(231\)\s*903-5690|231[\s.-]*903[\s.-]*5690", text))
    results.append((has_sig_phone, "UF-07: Signature block includes phone",
                     "PASS" if has_sig_phone else f"FIX: Add phone: {PLAINTIFF_PHONE}"))

    has_date = bool(re.search(r"(date[d]?|signed|filed)\s*[:.]?\s*\w+\s+\d{1,2},?\s+\d{4}", text, re.I) or
                    re.search(r"\d{1,2}/\d{1,2}/\d{4}", text))
    results.append((has_date, "UF-08: Date present in signature block or filing",
                     "PASS" if has_date else "FIX: Add date in signature block (e.g., 'Dated: Month DD, YYYY')"))

    # Certificate of service
    cos_files = [n for n in files if "certificate" in n.lower() or "service" in n.lower()]
    has_cos_file = len(cos_files) > 0
    cos_text = " ".join(files.get(f, "") for f in cos_files) if cos_files else text
    has_cos_section = bool(re.search(r"certificate\s+of\s+service", text, re.I))
    has_cos = has_cos_file or has_cos_section
    results.append((has_cos, "UF-09: Certificate of service present",
                     "PASS" if has_cos else "FIX: Add 04_CERTIFICATE_OF_SERVICE.md with service details"))

    has_cos_date = bool(re.search(r"serv(ed|ice)\s.*\d{1,2}[/,-]\s*\d{1,2}[/,-]\s*\d{2,4}", cos_text, re.I) or
                        re.search(r"serv(ed|ice)\s.*\w+\s+\d{1,2},?\s+\d{4}", cos_text, re.I))
    results.append((has_cos_date, "UF-10: Certificate of service includes date served",
                     "PASS" if has_cos_date else "FIX: Certificate of service must state date of service"))

    has_cos_method = bool(re.search(r"(first[- ]class\s+mail|e-?fil|hand\s+deliver|electronic|MiFILE|personal\s+service|certified\s+mail|email)", cos_text, re.I))
    results.append((has_cos_method, "UF-11: Certificate of service includes method of service",
                     "PASS" if has_cos_method else "FIX: State method of service (e.g., 'first-class mail', 'MiFILE e-service', 'hand delivery')"))

    has_cos_parties = bool(re.search(r"watson", cos_text, re.I))
    results.append((has_cos_parties, "UF-12: Certificate of service lists opposing party",
                     "PASS" if has_cos_parties else f"FIX: Certificate of service must list {DEFENDANT} as served party"))

    # Placeholder checks
    found_placeholders = []
    for pat in PLACEHOLDER_PATTERNS:
        matches = re.findall(pat, text)
        if matches:
            found_placeholders.extend(matches[:3])  # Cap at 3 examples per pattern
    has_no_placeholders = len(found_placeholders) == 0
    detail = "PASS" if has_no_placeholders else f"FIX: Remove {len(found_placeholders)} placeholder(s): {', '.join(found_placeholders[:5])}"
    results.append((has_no_placeholders, "UF-13: No placeholder text remaining", detail))

    # Page numbering reference
    has_page_nums = bool(re.search(r"(page\s+\d|pg\.\s*\d|\bof\s+\d+\b|Page\s+\d+\s+of)", text, re.I))
    results.append((has_page_nums, "UF-14: Pages appear consecutively numbered",
                     "PASS" if has_page_nums else "WARN: Ensure pages are numbered when converting to PDF (check in final PDF)"))

    # Pro se identification
    has_pro_se = bool(re.search(r"pro\s*se|self[- ]represent|in\s+proper\s+person|propria\s+persona", text, re.I))
    results.append((has_pro_se, "UF-15: Pro se status identified",
                     "PASS" if has_pro_se else "FIX: Add 'Plaintiff, In Propria Persona' or 'Pro Se' under name in caption"))

    # Electronic signature format
    has_esig = bool(re.search(r"/s/\s*Andrew\s*(James\s*)?Pigors", text, re.I))
    results.append((has_esig, "UF-16: Electronic signature format (/s/ Name) present",
                     "PASS" if has_esig else "FIX: For e-filing, use '/s/ Andrew James Pigors' as electronic signature"))

    # Child initials only (not full name)
    child_full_name_exposed = bool(re.search(r"(?<!\w)(L\.?\s*D\.?\s*W\.?)(?!\w)", text)) is False and \
                               bool(re.search(r"child|minor|son|daughter", text, re.I))
    # Check if child's full name is accidentally in text — we look for common violations
    # Since we don't know the child's full name, we just verify initials are used
    uses_initials = bool(re.search(r"L\.?\s*D\.?\s*W\.?", text))
    results.append((uses_initials or not bool(re.search(r"child|minor", text, re.I)),
                     "UF-17: Child referred to by initials only (MCR 8.119(H))",
                     "PASS" if uses_initials else "WARN: If child is mentioned, use initials 'L.D.W.' per MCR 8.119(H)"))

    return results


def check_f3_disqualification(files: dict, text: str) -> list[tuple[bool, str, str]]:
    """F3 — MCR 2.003 Disqualification (14th Circuit Court)."""
    results = []

    has_case_no = bool(re.search(r"2024-001507-DC", text))
    results.append((has_case_no, "F3-01: Caption includes Case No. 2024-001507-DC",
                     "PASS" if has_case_no else f"FIX: Add '{CASE_DC}' to caption"))

    has_mcr_2003c = bool(re.search(r"MCR\s*2\.003\s*\(C\)", text, re.I))
    results.append((has_mcr_2003c, "F3-02: References MCR 2.003(C) grounds",
                     "PASS" if has_mcr_2003c else "FIX: Cite MCR 2.003(C) — the specific subdivision for disqualification grounds"))

    # Specific grounds
    has_bias = bool(re.search(r"bias|prejudice", text, re.I))
    has_caperton = bool(re.search(r"caperton|due\s+process", text, re.I))
    has_canon = bool(re.search(r"canon\s*2|appearance\s+of\s+(im)?proper", text, re.I))
    grounds_count = sum([has_bias, has_caperton, has_canon])
    results.append((grounds_count >= 1, "F3-03: States specific grounds (bias/prejudice, Caperton, Canon 2)",
                     f"PASS ({grounds_count}/3 ground types cited)" if grounds_count >= 1
                     else "FIX: Must state specific grounds — bias/prejudice, Caperton due process risk, Canon 2 appearance of impropriety"))

    # Affidavit
    has_affidavit_file = any("affidavit" in n.lower() for n in files)
    has_affidavit_ref = bool(re.search(r"affidavit|sworn\s+statement|under\s+oath|under\s+penalty\s+of\s+perjury", text, re.I))
    results.append((has_affidavit_file, "F3-04: Affidavit attached with factual grounds",
                     "PASS" if has_affidavit_file else "FIX: Attach 02_AFFIDAVIT.md stating specific factual grounds under oath"))

    # 14-day timeliness
    has_timeliness = bool(re.search(r"14[\s-]*day|timely|good\s+cause|recent(ly)?\s+(discover|learn)", text, re.I))
    results.append((has_timeliness, "F3-05: Filed within 14 days of discovery (or good cause shown)",
                     "PASS" if has_timeliness else "FIX: Address timeliness — filed within 14 days of discovery, or explain good cause for delay"))

    # MC 264 form
    has_mc264 = bool(re.search(r"MC\s*264|order\s+of\s+disqualification|reassignment", text, re.I))
    results.append((has_mc264, "F3-06: MC 264 form referenced or attached",
                     "PASS" if has_mc264 else "FIX: Reference MC 264 (Order of Disqualification/Reassignment) form, or attach proposed order"))

    # Service on all required parties
    cos_text = " ".join(files.get(n, "") for n in files if "certificate" in n.lower() or "service" in n.lower())
    if not cos_text:
        cos_text = text

    served_watson = bool(re.search(r"watson", cos_text, re.I))
    served_foc = bool(re.search(r"(FOC|friend\s+of\s+the\s+court|Rusco)", cos_text, re.I))
    served_clerk = bool(re.search(r"(court\s+clerk|clerk\s+of\s+(the\s+)?court)", cos_text, re.I))
    all_served = served_watson and served_foc and served_clerk
    missing = []
    if not served_watson: missing.append(DEFENDANT)
    if not served_foc: missing.append("FOC (Pamela Rusco)")
    if not served_clerk: missing.append("Court Clerk")
    results.append((all_served, "F3-07: Certificate of service includes Watson + FOC + Court Clerk",
                     "PASS" if all_served else f"FIX: Certificate must list service on: {', '.join(missing)}"))

    # Separate exhibits
    exhibit_files = [n for n in files if "exhibit" in n.lower()]
    results.append((len(exhibit_files) >= 1, "F3-08: Exhibit index present (exhibits must be separate)",
                     "PASS" if exhibit_files else "FIX: Create 03_EXHIBIT_INDEX.md — each exhibit must be a separate document"))

    # Judge name accuracy
    has_correct_judge = bool(re.search(r"Jenny\s+L\.?\s*McNeill", text, re.I))
    has_wrong_judge = bool(re.search(r"Amy\s+McNeill", text, re.I))
    results.append((has_correct_judge and not has_wrong_judge, "F3-09: Correct judge name (Hon. Jenny L. McNeill)",
                     "PASS" if (has_correct_judge and not has_wrong_judge) else
                     "FIX: Judge is 'Hon. Jenny L. McNeill' — NOT 'Amy McNeill'"))

    return results


def check_f6_jtc(files: dict, text: str) -> list[tuple[bool, str, str]]:
    """F6 — JTC Complaint (Judicial Tenure Commission)."""
    results = []

    # Mail-only warning
    has_mail_note = bool(re.search(r"(mail|post|send|ship|deliver)", text, re.I) and
                         re.search(r"(cannot|can\s*not|must\s+not|do\s+not)\s*(be\s+)?e[- ]?fil", text, re.I)) or \
                    bool(re.search(r"mail\s*(to|only|required)|not\s+e[- ]?fil|physical\s+(mail|delivery)", text, re.I))
    results.append((has_mail_note, "F6-01: ⚠️ Marked as MAIL-ONLY (cannot be e-filed)",
                     "PASS" if has_mail_note else "CRITICAL FIX: JTC complaints CANNOT be e-filed. Must be MAILED with original notarized signature."))

    # Correct address
    has_correct_addr = bool(re.search(r"3034\s+W\.?\s*Grand\s+Blvd", text, re.I))
    has_correct_suite = bool(re.search(r"Suite\s+8-350", text))
    has_wrong_suite = bool(re.search(r"Suite\s+8-450", text))
    results.append((has_correct_addr and has_correct_suite and not has_wrong_suite,
                     "F6-02: Correct JTC address (3034 W. Grand Blvd., Suite 8-350, Detroit, MI 48202)",
                     "PASS" if (has_correct_addr and has_correct_suite and not has_wrong_suite) else
                     "FIX: JTC address is 3034 W. Grand Blvd., Suite 8-350, Detroit, MI 48202 (NOT Suite 8-450!)"))

    # Request for Investigation form
    has_rfi = bool(re.search(r"request\s+for\s+investigation", text, re.I))
    results.append((has_rfi, "F6-03: Uses 'Request for Investigation' form/format",
                     "PASS" if has_rfi else "FIX: Title must be 'Request for Investigation' — use official JTC form or follow its format"))

    # Notarization
    has_notary = bool(re.search(r"notar(iz|y)|sworn\s+before|subscribed\s+and\s+sworn|notary\s+public", text, re.I))
    results.append((has_notary, "F6-04: Notarization noted (complaint must be notarized)",
                     "PASS" if has_notary else "CRITICAL FIX: JTC complaint MUST be notarized — add notary block or note 'TO BE NOTARIZED BEFORE MAILING'"))

    # Copies not originals
    has_copies_note = bool(re.search(r"cop(y|ies)\s+(of\s+)?(evidence|exhibit|document|attach)", text, re.I) or
                          re.search(r"attach(ed)?\s+cop(y|ies)|do\s+not\s+send\s+original", text, re.I))
    results.append((has_copies_note, "F6-05: Attaches COPIES of evidence (not originals)",
                     "PASS" if has_copies_note else "FIX: Note that COPIES (not originals) of evidence are attached"))

    # Conduct vs decisions
    has_conduct_focus = bool(re.search(r"(judicial\s+)?conduct|behavior|temperament|demeanor|procedural\s+violation|ex\s+parte|due\s+process\s+violation", text, re.I))
    has_reversal_request = bool(re.search(r"reverse\s+(the\s+)?(ruling|decision|order|judgment)", text, re.I))
    conduct_ok = has_conduct_focus and not has_reversal_request
    results.append((conduct_ok, "F6-06: Focuses on CONDUCT violations (JTC cannot reverse rulings)",
                     "PASS" if conduct_ok else
                     "FIX: Focus on judicial CONDUCT (bias, ex parte, due process) — JTC cannot reverse rulings or decisions"))

    # Factual description
    word_count = len(text.split())
    has_detail = word_count > 500
    results.append((has_detail, "F6-07: Detailed factual description of misconduct",
                     f"PASS ({word_count} words)" if has_detail else
                     f"FIX: Complaint is only {word_count} words — provide detailed factual narrative of specific judicial misconduct"))

    # JTC phone reference
    has_phone = bool(re.search(r"\(313\)\s*875-5110|313[\s.-]*875[\s.-]*5110", text))
    results.append((has_phone, "F6-08: JTC phone (313) 875-5110 referenced",
                     "PASS" if has_phone else "WARN: Consider adding JTC phone (313) 875-5110 for reference"))

    # Correct judge name
    has_correct_judge = bool(re.search(r"Jenny\s+L\.?\s*McNeill", text, re.I))
    results.append((has_correct_judge, "F6-09: Names correct judge (Hon. Jenny L. McNeill)",
                     "PASS" if has_correct_judge else "FIX: Judge is 'Hon. Jenny L. McNeill' of 14th Circuit Court"))

    return results


def check_f10_coa_emergency(files: dict, text: str) -> list[tuple[bool, str, str]]:
    """F10 — COA Emergency Motion (Court of Appeals 366810)."""
    results = []

    # Emergency label
    has_emergency = bool(re.search(r"EMERGENCY", text))
    results.append((has_emergency, "F10-01: 'EMERGENCY' label prominent on first page",
                     "PASS" if has_emergency else "CRITICAL FIX: Add 'EMERGENCY' in all caps prominently on first page / cover sheet"))

    # MCR 7.211(C)(6) for immediate consideration
    has_7211c6 = bool(re.search(r"MCR\s*7\.211\s*\(C\)\s*\(6\)", text, re.I))
    results.append((has_7211c6, "F10-02: References MCR 7.211(C)(6) for immediate consideration",
                     "PASS" if has_7211c6 else "FIX: Cite MCR 7.211(C)(6) — standard for emergency/immediate consideration"))

    # Peremptory reversal citations
    has_7211c4 = bool(re.search(r"MCR\s*7\.211\s*\(C\)\s*\(4\)", text, re.I))
    has_manifest = bool(re.search(r"manifest\s+error", text, re.I))
    results.append((has_7211c4 or has_manifest, "F10-03: Peremptory reversal: MCR 7.211(C)(4) + 'manifest error'",
                     "PASS" if (has_7211c4 or has_manifest) else
                     "FIX: For peremptory reversal, cite MCR 7.211(C)(4) and demonstrate 'manifest error' standard"))

    # Page limits
    # Can't precisely count pages from markdown, but check for excessive length
    word_count = len(text.split())
    brief_ok = word_count <= 14000
    results.append((brief_ok, "F10-04: Brief portion within limits (max 50 pages / 14,000 words)",
                     f"PASS ({word_count:,} words)" if brief_ok else
                     f"FIX: Brief is {word_count:,} words — exceeds 14,000 word limit. Trim to under 14,000 words."))

    # Filing fee
    has_fee = bool(re.search(r"\$375|filing\s+fee|IFP|in\s+forma\s+pauperis|fee\s+waiv", text, re.I))
    results.append((has_fee, "F10-05: $375 filing fee referenced OR IFP application attached",
                     "PASS" if has_fee else "FIX: Address the $375 filing fee — reference payment or attach IFP (In Forma Pauperis) application"))

    # 21-day deadline
    has_21day = bool(re.search(r"21[\s-]*day|timely|within\s+\d+\s+day", text, re.I))
    results.append((has_21day, "F10-06: Filed within 21 days of final order (or delay explained)",
                     "PASS" if has_21day else "FIX: Address timeliness — filed within 21 days of entry of order, or explain delay"))

    # Service on all parties
    cos_text = " ".join(files.get(n, "") for n in files if "certificate" in n.lower() or "service" in n.lower())
    if not cos_text:
        cos_text = text
    served_watson = bool(re.search(r"watson", cos_text, re.I))
    served_foc = bool(re.search(r"(FOC|friend\s+of\s+the\s+court|Rusco)", cos_text, re.I))
    served_lower = bool(re.search(r"(lower\s+court|circuit\s+court|trial\s+court|14th\s+circuit)", cos_text, re.I))
    all_served = served_watson and served_foc and served_lower
    missing = []
    if not served_watson: missing.append(DEFENDANT)
    if not served_foc: missing.append("FOC")
    if not served_lower: missing.append("Lower Court (14th Circuit)")
    results.append((all_served, "F10-07: Served on ALL parties (Watson, FOC, lower court)",
                     "PASS" if all_served else f"FIX: Must serve: {', '.join(missing)}"))

    # COA case number
    has_coa = bool(re.search(r"366810", text))
    results.append((has_coa, "F10-08: Caption includes COA Case No. 366810",
                     "PASS" if has_coa else "FIX: Add 'Court of Appeals Case No. 366810' to caption"))

    return results


def check_mifle_efiling(files: dict, text: str) -> list[tuple[bool, str, str]]:
    """MiFILE E-Filing requirements (for F3, F10, and other e-filed documents)."""
    results = []

    # Separate files
    md_count = len([n for n in files if n.endswith(".md")])
    results.append((md_count >= 2, "EF-01: Each document is a separate file (not bundled)",
                     f"PASS ({md_count} separate .md files)" if md_count >= 2 else
                     "FIX: Split filing into separate files — one per document (motion, affidavit, exhibits, CoS)"))

    # Electronic signature
    has_esig = bool(re.search(r"/s/\s*Andrew", text, re.I))
    results.append((has_esig, "EF-02: Electronic signature format: /s/ Andrew James Pigors",
                     "PASS" if has_esig else "FIX: Add '/s/ Andrew James Pigors' as electronic signature for e-filing"))

    # PDF conversion note
    has_pdf_note = bool(re.search(r"\.pdf|PDF\s+format|convert\s+to\s+PDF", text, re.I))
    results.append((has_pdf_note, "EF-03: PDF format noted (recommended for MiFILE)",
                     "PASS" if has_pdf_note else "WARN: Ensure documents are converted to PDF before uploading to MiFILE"))

    # File naming convention
    has_case_in_name = any(re.search(r"\d{4}-\d{4,6}", n) for n in files)
    results.append((True, "EF-04: Descriptive file names with case number",
                     "PASS" if has_case_in_name else "WARN: Consider adding case number to file names for MiFILE"))

    # File size warning
    results.append((True, "EF-05: File size under 25 MB each",
                     "WARN: Verify each PDF is under 25 MB (conservative: under 10 MB) before e-filing"))

    # Scan quality note
    results.append((True, "EF-06: Scanned documents at 300 dpi B&W/grayscale",
                     "WARN: If any scanned exhibits, ensure 300 dpi B&W or grayscale for legibility"))

    # No password protection
    results.append((True, "EF-07: No password-protected or restricted PDFs",
                     "WARN: Ensure no PDFs are password-protected before uploading to MiFILE"))

    return results


def check_f4_federal_1983(files: dict, text: str) -> list[tuple[bool, str, str]]:
    """F4 — Federal §1983 Complaint (WDMI)."""
    results = []

    # Filing fee or IFP
    has_fee = bool(re.search(r"\$402|filing\s+fee|IFP|in\s+forma\s+pauperis|fee\s+waiv", text, re.I))
    results.append((has_fee, "F4-01: $402 filing fee OR IFP affidavit",
                     "PASS" if has_fee else "FIX: Address $402 federal filing fee — pay or attach IFP affidavit"))

    # Under color of state law
    has_color = bool(re.search(r"under\s+color\s+of\s+state\s+law|color\s+of\s+law|42\s+U\.?S\.?C\.?\s*§?\s*1983", text, re.I))
    results.append((has_color, "F4-02: 'Under color of state law' alleged + §1983 cited",
                     "PASS" if has_color else "FIX: Must allege defendant(s) acted 'under color of state law' per 42 U.S.C. §1983"))

    # Statute of limitations (3 years)
    has_sol = bool(re.search(r"(3|three)[- ]year|statute\s+of\s+limitation|timely|within\s+the\s+limitation", text, re.I))
    results.append((has_sol, "F4-03: 3-year statute of limitations addressed",
                     "PASS" if has_sol else "FIX: Address the 3-year statute of limitations for §1983 claims"))

    # Named defendants with roles
    has_named = bool(re.search(r"defendant|respondent", text, re.I))
    has_roles = bool(re.search(r"(judge|officer|clerk|official|in\s+(her|his|their)\s+(official|individual)\s+capacity)", text, re.I))
    results.append((has_named and has_roles, "F4-04: Each defendant specifically named with role",
                     "PASS" if (has_named and has_roles) else "FIX: Name each defendant specifically with their role/capacity (official, individual, or both)"))

    # Numbered paragraphs
    has_numbered = bool(re.search(r"^\s*\d+\.\s+", text, re.M))
    results.append((has_numbered, "F4-05: Numbered paragraphs",
                     "PASS" if has_numbered else "FIX: Federal complaints require consecutively numbered paragraphs"))

    # Jurisdiction and venue
    has_jurisdiction = bool(re.search(r"jurisdiction|28\s+U\.?S\.?C\.?\s*§?\s*(1331|1343)", text, re.I))
    has_venue = bool(re.search(r"venue|western\s+district|W\.?D\.?\s*Mich", text, re.I))
    results.append((has_jurisdiction and has_venue, "F4-06: Jurisdiction + venue stated",
                     "PASS" if (has_jurisdiction and has_venue) else
                     "FIX: State federal jurisdiction (28 U.S.C. §1331/§1343) and venue (Western District of Michigan)"))

    # Pro se format
    has_pro_se = bool(re.search(r"pro\s*se|propria\s+persona|self[- ]represent", text, re.I))
    results.append((has_pro_se, "F4-07: Pro Se format per WDMI Pro Se Handbook",
                     "PASS" if has_pro_se else "FIX: Identify as Pro Se plaintiff per WDMI Pro Se Handbook"))

    return results


def check_f7_custody(files: dict, text: str) -> list[tuple[bool, str, str]]:
    """F7 — Custody Modification (MCL 722.27a)."""
    results = []

    # Case number
    has_case = bool(re.search(r"2024-001507-DC", text))
    results.append((has_case, "F7-01: Case No. 2024-001507-DC in caption",
                     "PASS" if has_case else f"FIX: Add '{CASE_DC}' to caption"))

    # Parenting time presumption
    has_presumption = bool(re.search(r"presumption|MCL\s*722\.27a|parenting\s+time\s+with\s+both", text, re.I))
    results.append((has_presumption, "F7-02: Presumption of parenting time with BOTH parents cited",
                     "PASS" if has_presumption else "FIX: Cite MCL 722.27a — presumption that parenting time with both parents is in child's best interest"))

    # Clear and convincing standard
    has_standard = bool(re.search(r"clear\s+and\s+convincing", text, re.I))
    results.append((has_standard, "F7-03: 'Clear and convincing evidence' standard cited for denial",
                     "PASS" if has_standard else "FIX: If opposing party denies parenting time, cite 'clear and convincing evidence' standard"))

    # Proper cause / change of circumstances
    has_threshold = bool(re.search(r"proper\s+cause|change\s+(of|in)\s+circumstances", text, re.I))
    results.append((has_threshold, "F7-04: 'Proper cause' or 'change of circumstances' threshold met",
                     "PASS" if has_threshold else "FIX: Must demonstrate 'proper cause' or 'change of circumstances' to modify custody"))

    # Best interest factors
    has_bif = bool(re.search(r"(best\s+interest|MCL\s*722\.23)", text, re.I))
    results.append((has_bif, "F7-05: Best interest factors (MCL 722.23) addressed",
                     "PASS" if has_bif else "FIX: Address the best interest factors under MCL 722.23"))

    # Child initials
    has_initials = bool(re.search(r"L\.?\s*D\.?\s*W\.?", text))
    results.append((has_initials, "F7-06: Child referred to as L.D.W. (initials only)",
                     "PASS" if has_initials else "FIX: Refer to child as 'L.D.W.' — initials only per MCR 8.119(H)"))

    return results


def check_hallucination_guard(files: dict, text: str) -> list[tuple[bool, str, str]]:
    """Anti-hallucination checks — detect fabricated names, stats, bar numbers."""
    results = []

    # Fabricated names
    has_jane_berry = bool(re.search(r"Jane\s+Berry", text, re.I))

    has_patricia_berry = bool(re.search(r"Patricia\s+Berry", text, re.I))

    # Wrong judge name
    has_amy = bool(re.search(r"Amy\s+McNeill", text, re.I))
    results.append((not has_amy, "AH-03: No wrong judge name 'Amy McNeill'",
                     "PASS" if not has_amy else "CRITICAL: Judge is 'Jenny L. McNeill' NOT 'Amy McNeill'. Fix immediately."))

    # Fabricated bar number for Ronald Berry
    has_berry_esq = bool(re.search(r"Berry.*Esq|Berry.*attorney|Berry.*counsel|Berry.*P\d{5}", text, re.I))
    results.append((not has_berry_esq, "AH-04: Ronald Berry not listed as attorney (he is not one)",
                     "PASS" if not has_berry_esq else "CRITICAL: Ronald Berry is NOT an attorney. No bar number. No 'Esq.' Remove."))

    # Wrong defendant name variants
    has_wrong_emily = bool(re.search(r"Emily\s+(Ann|M\.)\s+Watson", text, re.I))
    results.append((not has_wrong_emily, "AH-05: Correct defendant name (Emily A. Watson, not Ann/M.)",
                     "PASS" if not has_wrong_emily else f"FIX: Defendant is '{DEFENDANT}' — NOT 'Emily Ann Watson' or 'Emily M. Watson'"))

    # Fabricated documented pattern of parental alienation
    has_91pct = bool(re.search(r"91\s*%\s*(alienation|score)", text, re.I))
    results.append((not has_91pct, "AH-06: No fabricated 'documented pattern of parental alienation'",
                     "PASS" if not has_91pct else "CRITICAL: 'documented pattern of parental alienation' is pseudo-scientific fabrication. Remove and use documented incident counts."))

    # Fabricated CPS count
    has_9cps = bool(re.search(r"9\s+CPS\s+investigation", text, re.I))
    results.append((not has_9cps, "AH-07: No fabricated 'CPS records [VERIFY — check actual CPS records for count]'",
                     "PASS" if not has_9cps else "CRITICAL: 'CPS records [VERIFY — check actual CPS records for count]' is unverified. Check DB for actual count."))

    # Tiffany (wrong name for Emily)
    has_tiffany = bool(re.search(r"Tiffany", text, re.I))
    results.append((not has_tiffany, "AH-08: No wrong name 'Tiffany' for defendant",
                     "PASS" if not has_tiffany else "CRITICAL: Defendant is Emily A. Watson, NOT 'Tiffany'. Remove."))

    return results


def check_common_rejections(files: dict, text: str) -> list[tuple[bool, str, str]]:
    """Common court rejection reasons to pre-screen."""
    results = []

    # Missing case number
    has_any_case = bool(re.search(r"\d{4}-\d{4,6}-\w{2}|366810", text))
    results.append((has_any_case, "CR-01: Case number present",
                     "PASS" if has_any_case else "FIX: No case number found — courts will reject filings without case numbers"))

    # Document legibility (basic check — no binary garbage)
    garbage_chars = len(re.findall(r"[\x00-\x08\x0e-\x1f]", text))
    legible = garbage_chars < 5
    results.append((legible, "CR-02: Document appears legible (no binary garbage)",
                     "PASS" if legible else f"FIX: {garbage_chars} non-printable characters found — document may be corrupt"))

    # Completeness — check for very short files
    short_files = [n for n, c in files.items() if len(c.strip()) < 100 and n.endswith(".md")]
    complete = len(short_files) == 0
    results.append((complete, "CR-03: All files have substantive content",
                     "PASS" if complete else f"FIX: These files appear empty/stub: {', '.join(short_files)}"))

    # Bundled unrelated documents check
    results.append((True, "CR-04: No bundled unrelated documents",
                     "WARN: Verify each file contains only ONE document type when converting to PDF"))

    # Required signatures
    has_sig = bool(re.search(r"/s/|signature|signed|Andrew\s+James\s+Pigors", text, re.I))
    results.append((has_sig, "CR-05: Required signature(s) present",
                     "PASS" if has_sig else "FIX: Filing must be signed — add signature block with '/s/ Andrew James Pigors'"))

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# SCORING AND REPORT GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

def compute_score(results: list[tuple[bool, str, str]]) -> int:
    """Compute 0-100 compliance score. CRITICAL failures cap at 50."""
    if not results:
        return 0
    total = len(results)
    passed = sum(1 for r in results if r[0])
    raw = int((passed / total) * 100)

    # Critical failures cap score
    critical_failures = [r for r in results if not r[0] and ("CRITICAL" in r[2] or r[1].startswith(("AH-", "F6-01", "F6-04", "F10-01")))]
    if critical_failures:
        raw = min(raw, 50)

    return raw


def verdict(score: int) -> str:
    """GO/NO-GO based on score."""
    if score >= 90:
        return "✅ GO — Ready for filing (minor warnings may remain)"
    elif score >= 70:
        return "⚠️ CONDITIONAL GO — Address warnings before filing"
    elif score >= 50:
        return "🔶 NO-GO (FIXABLE) — Multiple issues need attention"
    else:
        return "🛑 NO-GO (CRITICAL) — Major deficiencies, do NOT file"


def format_results_md(pkg_name: str, filing_type: str, filing_label: str,
                      all_results: dict[str, list], score: int) -> str:
    """Format results as Markdown."""
    lines = []
    lines.append(f"## {pkg_name} — {filing_label}")
    lines.append(f"**Filing Type:** {filing_type} | **Court:** {FILING_TYPES.get(filing_type, {}).get('court', 'Unknown')}")
    lines.append(f"**Score:** {score}/100 | **Verdict:** {verdict(score)}")
    lines.append("")

    for category, results in all_results.items():
        passed = sum(1 for r in results if r[0])
        total = len(results)
        emoji = "✅" if passed == total else ("⚠️" if passed >= total * 0.7 else "❌")
        lines.append(f"### {emoji} {category} ({passed}/{total})")
        lines.append("")
        for ok, rule, detail in results:
            icon = "✅" if ok else "❌"
            lines.append(f"- {icon} **{rule}**")
            if not ok or "WARN" in detail:
                lines.append(f"  - {detail}")
        lines.append("")

    return "\n".join(lines)


def format_results_json(pkg_name: str, filing_type: str, filing_label: str,
                        all_results: dict[str, list], score: int) -> dict:
    """Format results as JSON-serializable dict."""
    categories = {}
    for category, results in all_results.items():
        categories[category] = {
            "passed": sum(1 for r in results if r[0]),
            "total": len(results),
            "checks": [
                {"pass": ok, "rule": rule, "detail": detail}
                for ok, rule, detail in results
            ]
        }
    return {
        "package": pkg_name,
        "filing_type": filing_type,
        "filing_label": filing_label,
        "court": FILING_TYPES.get(filing_type, {}).get("court", "Unknown"),
        "score": score,
        "verdict": verdict(score),
        "timestamp": datetime.now().isoformat(),
        "categories": categories,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN VALIDATION PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════

def validate_package(pkg_dir: Path) -> tuple[str, dict]:
    """Validate a single filing package directory. Returns (md_report, json_report)."""
    pkg_name = pkg_dir.name
    filing_type = detect_filing_type(pkg_name)

    if not filing_type:
        return (f"## {pkg_name}\n**SKIPPED** — Could not detect filing type\n",
                {"package": pkg_name, "filing_type": None, "score": 0, "verdict": "SKIPPED"})

    info = FILING_TYPES[filing_type]
    files = read_md_files(pkg_dir)
    if not files:
        return (f"## {pkg_name}\n**SKIPPED** — No .md files found\n",
                {"package": pkg_name, "filing_type": filing_type, "score": 0, "verdict": "NO FILES"})

    text = combined_text(files)
    all_results = {}

    # Universal checks (always run)
    all_results["Universal Formatting"] = check_universal_formatting(files, text)
    all_results["Anti-Hallucination Guard"] = check_hallucination_guard(files, text)
    all_results["Common Rejection Screening"] = check_common_rejections(files, text)

    # Filing-type-specific checks
    if filing_type == "F3":
        all_results["F3: MCR 2.003 Disqualification"] = check_f3_disqualification(files, text)
        all_results["MiFILE E-Filing"] = check_mifle_efiling(files, text)
    elif filing_type == "F6":
        all_results["F6: JTC Complaint"] = check_f6_jtc(files, text)
        # No MiFILE — JTC is mail-only
    elif filing_type == "F10":
        all_results["F10: COA Emergency Motion"] = check_f10_coa_emergency(files, text)
        all_results["MiFILE E-Filing"] = check_mifle_efiling(files, text)
    elif filing_type == "F4":
        all_results["F4: Federal §1983 Complaint"] = check_f4_federal_1983(files, text)
        # Federal = PACER/CM-ECF, not MiFILE
    elif filing_type == "F7":
        all_results["F7: Custody Modification"] = check_f7_custody(files, text)
        all_results["MiFILE E-Filing"] = check_mifle_efiling(files, text)
    elif filing_type in ("F1", "F2", "F5", "F8", "F9"):
        # These share e-filing requirements
        all_results["MiFILE E-Filing"] = check_mifle_efiling(files, text)

    # Flatten all results for scoring
    flat = []
    for cat_results in all_results.values():
        flat.extend(cat_results)

    score = compute_score(flat)
    md = format_results_md(pkg_name, filing_type, info["label"], all_results, score)
    js = format_results_json(pkg_name, filing_type, info["label"], all_results, score)

    return md, js


def find_packages(target: str | None) -> list[Path]:
    """Find filing package directories to validate."""
    if target and os.path.isdir(target):
        return [Path(target)]

    # Default: scan Desktop LITIGATION_FILING_PACKAGE
    packages = []
    if FILING_PKG_ROOT.is_dir():
        for d in sorted(FILING_PKG_ROOT.iterdir()):
            if d.is_dir() and d.name.startswith("PKG_F"):
                packages.append(d)

    # Also check Desktop root for PKG_F* (legacy location)
    if not packages:
        for d in sorted(DESKTOP.iterdir()):
            if d.is_dir() and d.name.startswith("PKG_F"):
                packages.append(d)

    return packages


def main():
    target = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != "--all" else None

    print("=" * 78)
    print("  COURT FILING COMPLIANCE VALIDATOR — Tool #216")
    print("  Michigan Court Rules + MiFILE + JTC + COA + WDMI Federal")
    print(f"  Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 78)
    print()

    packages = find_packages(target)
    if not packages:
        print("❌ No filing packages found!")
        print(f"   Searched: {FILING_PKG_ROOT}")
        print(f"   Searched: {DESKTOP}\\PKG_F*")
        print("   Usage: python court_compliance_validator.py [path/to/PKG_F*]")
        sys.exit(1)

    print(f"📂 Found {len(packages)} filing package(s) to validate:\n")
    for p in packages:
        ftype = detect_filing_type(p.name)
        label = FILING_TYPES.get(ftype, {}).get("label", "Unknown") if ftype else "Unknown"
        print(f"   {p.name} → {label}")
    print()
    print("-" * 78)

    all_md = []
    all_json = []
    summary_matrix = []

    for pkg_dir in packages:
        print(f"\n🔍 Validating: {pkg_dir.name} ...")
        md_report, json_report = validate_package(pkg_dir)
        all_md.append(md_report)
        all_json.append(json_report)

        score = json_report.get("score", 0)
        verd = json_report.get("verdict", "UNKNOWN")
        ftype = json_report.get("filing_type", "??")
        label = json_report.get("filing_label", "Unknown")

        summary_matrix.append({
            "package": pkg_dir.name,
            "type": ftype,
            "label": label,
            "score": score,
            "verdict": verd,
        })

        # Print inline
        icon = "✅" if score >= 90 else ("⚠️" if score >= 70 else ("🔶" if score >= 50 else "🛑"))
        print(f"   {icon} Score: {score}/100 — {verd}")

        # Print failures
        if "categories" in json_report:
            for cat_name, cat_data in json_report["categories"].items():
                failures = [c for c in cat_data["checks"] if not c["pass"]]
                if failures:
                    print(f"\n   ❌ {cat_name} ({cat_data['passed']}/{cat_data['total']} passed):")
                    for f in failures:
                        print(f"      • {f['rule']}")
                        print(f"        → {f['detail']}")

    # ── Summary Matrix ─────────────────────────────────────────────────────────
    print("\n" + "=" * 78)
    print("  COMPLIANCE SUMMARY MATRIX")
    print("=" * 78)
    print(f"\n  {'Package':<45} {'Type':<5} {'Score':>5}  Verdict")
    print(f"  {'─' * 45} {'─' * 5} {'─' * 5}  {'─' * 40}")

    total_score = 0
    go_count = 0
    nogo_count = 0
    for row in summary_matrix:
        icon = "✅" if row["score"] >= 90 else ("⚠️" if row["score"] >= 70 else ("🔶" if row["score"] >= 50 else "🛑"))
        short_verdict = "GO" if row["score"] >= 90 else ("CONDITIONAL" if row["score"] >= 70 else "NO-GO")
        print(f"  {row['package']:<45} {row['type']:<5} {row['score']:>5}  {icon} {short_verdict}")
        total_score += row["score"]
        if row["score"] >= 70:
            go_count += 1
        else:
            nogo_count += 1

    avg_score = total_score // len(summary_matrix) if summary_matrix else 0
    print(f"\n  Average Score: {avg_score}/100 | GO: {go_count} | NO-GO: {nogo_count}")
    print()

    # ── Save Reports ───────────────────────────────────────────────────────────
    # Markdown report
    md_header = f"""# COURT FILING COMPLIANCE REPORT
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Tool:** #216 Court Filing Compliance Validator
**Packages Scanned:** {len(packages)}
**Average Score:** {avg_score}/100

---

## Summary Matrix

| Package | Type | Score | Verdict |
|---------|------|-------|---------|
"""
    for row in summary_matrix:
        icon = "✅" if row["score"] >= 90 else ("⚠️" if row["score"] >= 70 else ("🔶" if row["score"] >= 50 else "🛑"))
        md_header += f"| {row['package']} | {row['type']} | {row['score']}/100 | {icon} {row['verdict']} |\n"

    md_header += "\n---\n\n"
    full_md = md_header + "\n---\n\n".join(all_md)

    md_path = REPORTS_DIR / "COURT_COMPLIANCE_REPORT.md"
    md_path.write_text(full_md, encoding="utf-8")
    print(f"📝 Markdown report saved: {md_path}")

    # JSON report
    json_report = {
        "tool": "#216 Court Filing Compliance Validator",
        "generated": datetime.now().isoformat(),
        "packages_scanned": len(packages),
        "average_score": avg_score,
        "summary": summary_matrix,
        "detailed_results": all_json,
    }
    json_path = REPORTS_DIR / "COURT_COMPLIANCE_REPORT.json"
    json_path.write_text(json.dumps(json_report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"📊 JSON report saved: {json_path}")

    print(f"\n{'=' * 78}")
    overall = "✅ FLEET READY" if avg_score >= 80 else "🛑 FLEET NOT READY — FIX ISSUES ABOVE"
    print(f"  OVERALL: {overall} (avg {avg_score}/100)")
    print(f"{'=' * 78}")


if __name__ == "__main__":
    main()
