"""Harvest Engine configuration — drive map, MEEK patterns, adversary keywords, thresholds."""

import re
import os
from pathlib import Path

# ── Central DB path ──────────────────────────────────────────────────────────
REPO_ROOT = Path(os.environ.get("LITIGATIONOS_ROOT", r"C:\Users\andre\LitigationOS"))
CENTRAL_DB = REPO_ROOT / "litigation_context.db"
TEMP_DIR = Path(r"D:\LitigationOS_tmp")

# ── Drive topology ───────────────────────────────────────────────────────────
DRIVES = {
    "C": {"type": "NTFS", "role": "PRIMARY", "journal": "WAL"},
    "D": {"type": "NTFS", "role": "SECONDARY", "journal": "WAL"},
    "F": {"type": "NTFS", "role": "EVIDENCE", "journal": "WAL"},
    "G": {"type": "FAT32", "role": "SOURCE", "journal": "DELETE"},
    "I": {"type": "NTFS", "role": "ARCHIVE", "journal": "WAL"},
    "J": {"type": "exFAT", "role": "REFERENCE", "journal": "DELETE"},
}

# ── Supported file extensions ────────────────────────────────────────────────
EXTRACTABLE = {
    ".pdf", ".docx", ".doc", ".txt", ".md", ".csv", ".json", ".jsonl",
    ".html", ".htm", ".xml", ".rtf", ".eml", ".msg",
}
ARCHIVE_EXTS = {".zip", ".7z", ".rar", ".gz", ".tar"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif", ".heic"}
DB_EXTS = {".db", ".sqlite", ".sqlite3"}

# ── MEEK Lane Classification (compiled regex, single-pass) ───────────────────
# Detection priority: E → D → F → C → A → B
LANE_PATTERNS = {
    "E": re.compile(
        r"(?i)\b(?:mcneill|judicial\s*(?:misconduct|tenure|bias|complaint)|"
        r"jtc|canon|benchbook|ex\s*parte\s*(?:order|communication|hearing)|"
        r"disqualif|recus(?:al|e)|hoopes|ladas)\b"
    ),
    "D": re.compile(
        r"(?i)\b(?:ppo|personal\s*protection|protection\s*order|"
        r"5907|stalking|harassment|domestic\s*(?:violence|relationship)|"
        r"mcl\s*600\.2950|mcr\s*3\.70)\b"
    ),
    "F": re.compile(
        r"(?i)\b(?:coa|court\s*of\s*appeals|366810|appell(?:ant|ee|ate)|"
        r"mcr\s*7\.2|brief|appendix|claim\s*of\s*appeal)\b"
    ),
    "C": re.compile(
        r"(?i)\b(?:federal|§\s*1983|42\s*u\.?s\.?c|28\s*u\.?s\.?c|"
        r"civil\s*rights|conspiracy|frcp|qualified\s*immunity|monell)\b"
    ),
    "A": re.compile(
        r"(?i)\b(?:custody|parenting\s*time|001507|watson|"
        r"best\s*interest|mcl\s*722|foc|friend\s*of\s*(?:the\s*)?court|"
        r"visitation|child\s*support|established\s*custodial)\b"
    ),
    "B": re.compile(
        r"(?i)\b(?:shady\s*oaks|eviction|housing|trailer|002760|"
        r"habitability|landlord|tenant|rent|mobile\s*home|sewage)\b"
    ),
}

# ── Adversary actor patterns (frozenset for O(1) lookup) ─────────────────────
ADVERSARIES = {
    "Emily Watson": re.compile(
        r"(?i)\b(?:emily\s*(?:a\.?\s*)?watson|emily\s*(?:a\.?\s*)?pigors|"
        r"defendant|mother|ms\.?\s*watson|respondent)\b"
    ),
    "Judge McNeill": re.compile(
        r"(?i)\b(?:(?:judge|hon\.?)\s*(?:jenny\s*)?(?:l\.?\s*)?mcneill|"
        r"mcneill|the\s*court)\b"
    ),
    "Pamela Rusco": re.compile(
        r"(?i)\b(?:pamela?\s*rusco|rusco|foc\s*(?:referee|investigator)|"
        r"friend\s*of\s*(?:the\s*)?court)\b"
    ),
    "Ronald Berry": re.compile(
        r"(?i)\b(?:ronald?\s*berry|ron\s*berry|berry)\b"
    ),
    "Albert Watson": re.compile(
        r"(?i)\b(?:albert\s*watson|albert|mr\.?\s*watson)\b"
    ),
    "Jennifer Barnes": re.compile(
        r"(?i)\b(?:jennifer\s*barnes|barnes|p55406|attorney\s*for\s*defendant)\b"
    ),
    "Judge Hoopes": re.compile(
        r"(?i)\b(?:(?:judge|hon\.?)\s*(?:kenneth\s*)?hoopes|hoopes|chief\s*judge)\b"
    ),
    "Judge Ladas-Hoopes": re.compile(
        r"(?i)\b(?:(?:judge|hon\.?)\s*(?:maria\s*)?ladas|ladas[\s-]*hoopes)\b"
    ),
    "Cavan Berry": re.compile(
        r"(?i)\b(?:cavan\s*berry)\b"
    ),
    "Andrew Pigors": re.compile(
        r"(?i)\b(?:andrew\s*(?:j\.?\s*)?pigors|plaintiff|father|mr\.?\s*pigors)\b"
    ),
}

# ── Document type patterns ───────────────────────────────────────────────────
DOC_TYPES = {
    "order": re.compile(r"(?i)\b(?:order|it\s*is\s*(?:hereby\s*)?ordered|court\s*order)\b"),
    "motion": re.compile(r"(?i)\b(?:motion\s*(?:for|to)|moves?\s*(?:this\s*)?court)\b"),
    "brief": re.compile(r"(?i)\b(?:brief|memorandum|argument)\b"),
    "affidavit": re.compile(r"(?i)\b(?:affidavit|sworn|under\s*(?:oath|penalty\s*of\s*perjury))\b"),
    "notice": re.compile(r"(?i)\b(?:notice\s*(?:of|to)|hereby\s*notif)\b"),
    "complaint": re.compile(r"(?i)\b(?:complaint|comes?\s*now.*(?:alleges?|states?))\b"),
    "response": re.compile(r"(?i)\b(?:response|answer|reply|opposition)\b"),
    "judgment": re.compile(r"(?i)\b(?:judgment|opinion|decision|ruling|finding)\b"),
    "docket": re.compile(r"(?i)\b(?:docket|register\s*of\s*actions|case\s*(?:event|history))\b"),
    "subpoena": re.compile(r"(?i)\b(?:subpoena|duces\s*tecum|testificandum)\b"),
    "letter": re.compile(r"(?i)\b(?:dear\s|sincerely|regards)\b"),
    "email": re.compile(r"(?i)\b(?:from:|to:|subject:|sent:)\b"),
    "report": re.compile(r"(?i)\b(?:report|investigation|evaluation|assessment)\b"),
    "stipulation": re.compile(r"(?i)\b(?:stipulat(?:ion|ed)|agree(?:ment|d))\b"),
    "exhibit": re.compile(r"(?i)\b(?:exhibit\s*[a-z0-9]|attached\s*hereto)\b"),
    "proof_of_service": re.compile(r"(?i)\b(?:proof\s*of\s*service|certificate\s*of\s*(?:service|mailing))\b"),
}

# ── Legal authority extraction patterns ──────────────────────────────────────
AUTHORITY_PATTERNS = {
    "MCR": re.compile(r"\bMCR\s+(\d+\.\d+(?:\([A-Za-z0-9]+\))?)"),
    "MCL": re.compile(r"\bMCL\s+(\d+\.\d+[a-z]?(?:\([A-Za-z0-9]+\))?)"),
    "MRE": re.compile(r"\bMRE\s+(\d+(?:\([a-z]\))?)"),
    "USC": re.compile(r"\b(\d+)\s+U\.?S\.?C\.?\s+(?:§\s*)?(\d+[a-z]?)"),
    "FRCP": re.compile(r"\bFR(?:CP|Civ\.?P\.?)\s+(\d+(?:\([a-z]\))?)"),
    "case_law": re.compile(
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+v\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
        r"(?:,?\s*(\d+)\s+(?:Mich(?:\s+App)?|F\.?\s*(?:2d|3d|4th)|U\.?S\.?)\s+(\d+))?"
    ),
}

# ── Quote extraction patterns ────────────────────────────────────────────────
QUOTE_PATTERNS = [
    re.compile(r'"([^"]{20,500})"'),
    re.compile(r'"([^"\u201d]{20,500})["\u201d]'),
    re.compile(r'(?:stated|testified|said|wrote|declared|ordered)\s*(?:that\s+)?["\u201c]([^"\u201d]{20,500})["\u201d]'),
]

# ── Date extraction pattern ──────────────────────────────────────────────────
DATE_PATTERN = re.compile(
    r"\b(?:"
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+\d{1,2},?\s+\d{4}"
    r"|"
    r"\d{1,2}/\d{1,2}/\d{2,4}"
    r"|"
    r"\d{4}-\d{2}-\d{2}"
    r")\b"
)

# ── Processing thresholds ────────────────────────────────────────────────────
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB
MAX_TEXT_PER_PAGE = 50_000  # chars
MIN_TEXT_LENGTH = 20  # skip near-empty pages
BATCH_SIZE = 100  # DB commit batch
DEDUP_PEEK_CHARS = 500  # first N chars for content dedup

# ── MCR 8.119(H) child name protection ───────────────────────────────────────
CHILD_NAME_PATTERN = re.compile(
    r"(?i)\b(?:lincoln\s+david\s+watson|lincoln\s+watson|lincoln\s+pigors|"
    r"lincoln\s+david\s+pigors|lincoln\s+d\.?\s*w\.?)\b"
)
CHILD_INITIALS = "L.D.W."
