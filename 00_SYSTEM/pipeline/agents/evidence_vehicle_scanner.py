"""
EVIDENCE VEHICLE SCANNER (E01) — PDF-to-Court-Vehicle Matching Engine

Scans local PDF files across all drives, extracts text content, and matches
harms/violations/instances/quotes/event patterns to their corresponding
court vehicle (case lane A-F). Evidence guides the classification — not
metadata, not filenames, but ACTUAL CONTENT.

Matching hierarchy:
  1. MEEK signal regex (highest confidence — compiled patterns from config)
  2. Case number detection (2024-001507-DC, 2023-5907-PP, etc.)
  3. Party name detection (Watson, McNeill, Shady Oaks, Berry, etc.)
  4. Harm category classification (custody, housing, PPO, misconduct, federal)
  5. Keyword density scoring (lowest confidence — fallback)

Output: evidence_vehicle_matches table in litigation_context.db
  - file_path, vehicle (lane A-F), confidence (0-100), match_reason
  - extracted_quotes (key passages that triggered the match)
  - harm_categories (list of harms detected)
  - event_dates (dates mentioned in the document)

v1.0 — Initial release
"""
import json
import os
import re
import sqlite3
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .agent_models import (
    AgentResult, AgentStats, FatalAgentError, SkipItemError,
    MASTER_INDEX_DB
)

try:
    from .agent_base import Agent9999
except ImportError:
    from agent_base import Agent9999

LITIGATION_DB = Path(os.environ.get(
    "LITIGATION_DB",
    r"C:\Users\andre\LitigationOS\litigation_context.db"
))

# ─── MEEK Signal Patterns (compiled for speed) ───
MEEK_SIGNALS = {
    "E": {  # Judicial Misconduct — highest priority
        "patterns": [
            r"(?i)judicial\s+misconduct",
            r"(?i)canon\s+[1-7]",
            r"(?i)JTC|judicial\s+tenure",
            r"(?i)mcneill.*(?:bias|ex\s+parte|refused|denied)",
            r"(?i)code\s+of\s+judicial\s+conduct",
            r"(?i)disqualif(?:y|ication)",
            r"(?i)MCR\s+2\.003",
            r"(?i)recus(?:e|al)",
        ],
        "case_numbers": [r"2024-001507-DC"],
        "lane": "E",
        "vehicle": "JTC/Judicial Misconduct",
    },
    "D": {  # PPO
        "patterns": [
            r"(?i)personal\s+protection\s+order",
            r"(?i)\bPPO\b",
            r"(?i)show\s+cause",
            r"(?i)contempt.*(?:PPO|protection)",
            r"(?i)MCL\s+600\.2950",
            r"(?i)no.contact\s+order",
        ],
        "case_numbers": [r"2023-5907-PP"],
        "lane": "D",
        "vehicle": "PPO/Protection Orders",
    },
    "F": {  # Appellate
        "patterns": [
            r"(?i)court\s+of\s+appeals",
            r"(?i)\bCOA\b",
            r"(?i)appellate",
            r"(?i)MCR\s+7\.\d{3}",
            r"(?i)supreme\s+court.*michigan",
            r"(?i)\bMSC\b",
            r"(?i)leave\s+to\s+appeal",
        ],
        "case_numbers": [r"366810", r"COA.*366810"],
        "lane": "F",
        "vehicle": "Appellate (COA/MSC)",
    },
    "C": {  # Convergence / Federal
        "patterns": [
            r"(?i)(?:42\s+U\.?S\.?C\.?\s*)?(?:§|section)\s*1983",
            r"(?i)§\s*1985",
            r"(?i)federal\s+civil\s+rights",
            r"(?i)due\s+process.*(?:14th|fourteenth)",
            r"(?i)under\s+color\s+of\s+(?:state\s+)?law",
            r"(?i)monell",
            r"(?i)qualified\s+immunity",
        ],
        "case_numbers": [],
        "lane": "C",
        "vehicle": "Federal §1983/Convergence",
    },
    "A": {  # Custody
        "patterns": [
            r"(?i)custody\s+(?:modif|order|hearing|evaluat|best\s+interest)",
            r"(?i)parenting\s+time",
            r"(?i)child\s+(?:custody|support|welfare)",
            r"(?i)MCL\s+722\.2[3-9]",
            r"(?i)best\s+interest\s+factor",
            r"(?i)UCCJEA",
            r"(?i)Friend\s+of\s+(?:the\s+)?Court|FOC",
            r"(?i)parental\s+alienat",
            r"(?i)withhold(?:ing)?\s+(?:child|parenting|custody)",
        ],
        "case_numbers": [r"2024-001507-DC"],
        "lane": "A",
        "vehicle": "Custody (Watson)",
    },
    "B": {  # Housing / Shady Oaks
        "patterns": [
            r"(?i)shady\s+oaks",
            r"(?i)(?:eviction|landlord|tenant|habitability|lease)",
            r"(?i)Homes\s+of\s+America",
            r"(?i)Truth\s+in\s+Renting",
            r"(?i)MCL\s+600\.5[67]",
            r"(?i)EGLE|sewage|water\s+shutoff",
            r"(?i)mobile\s+home.*(?:park|commission|act)",
            r"(?i)Kim\s+Davis|Nicole\s+Browley",
            r"(?i)rent\s+(?:increase|ledger|coerced|escalat)",
        ],
        "case_numbers": [r"2025-002760-CZ"],
        "lane": "B",
        "vehicle": "Housing/Shady Oaks",
    },
}

# Compile all patterns once
for lane_key, lane_data in MEEK_SIGNALS.items():
    lane_data["compiled"] = [re.compile(p) for p in lane_data["patterns"]]
    lane_data["compiled_cases"] = [re.compile(c) for c in lane_data["case_numbers"]]

# ─── Harm Category Patterns ───
HARM_CATEGORIES = {
    "custody_interference": [
        r"(?i)withhold(?:ing)?\s+(?:child|parenting|visitation)",
        r"(?i)denied?\s+(?:parenting\s+time|access|visitation)",
        r"(?i)parental\s+alienat",
        r"(?i)coaching.*child",
    ],
    "financial_fraud": [
        r"(?i)(?:undisclosed|hidden|concealed)\s+(?:income|assets|earnings)",
        r"(?i)child\s+support.*(?:fraud|misrepresent|false)",
        r"(?i)(?:arrears|arrearage).*(?:forg[aie]v|waiv|zeroed)",
    ],
    "judicial_abuse": [
        r"(?i)(?:ex\s+parte|without\s+notice|refused\s+to\s+(?:hear|consider|look))",
        r"(?i)(?:bias|prejudice|predetermin).*(?:judge|court|honor)",
        r"(?i)due\s+process\s+violat",
    ],
    "domestic_violence": [
        r"(?i)(?:assault|battery|threat|intimidat|stalk|harass).*(?:watson|berry|albert|cody)",
        r"(?i)false\s+(?:allegation|report|claim).*(?:abuse|violence|poison)",
    ],
    "housing_violation": [
        r"(?i)(?:uninhabitable|mold|sewage|water\s+shutoff|condemned)",
        r"(?i)(?:illegal|unlawful)\s+(?:eviction|rent\s+increase|entry)",
        r"(?i)(?:code|health|safety)\s+violat",
    ],
    "ppo_weaponization": [
        r"(?i)(?:weaponiz|misus|abuse).*(?:PPO|protection\s+order)",
        r"(?i)(?:false|fabricat|fraudulent).*(?:PPO|protection)",
        r"(?i)(?:birthday|appclose).*(?:violat|contempt)",
    ],
    "attorney_misconduct": [
        r"(?i)(?:ineffective|incompetent)\s+(?:assistance|counsel|representation)",
        r"(?i)(?:muted|silenced|refused\s+to\s+(?:speak|object|argue))",
        r"(?i)Martini.*(?:silent|muted|did\s+not|failed)",
    ],
    "police_misconduct": [
        r"(?i)(?:false|fabricat).*(?:arrest|report|charge)",
        r"(?i)(?:officer|police|deputy).*(?:refus|ignor|fail)",
        r"(?i)(?:evidence|report).*(?:suppress|destroy|lost)",
    ],
}

HARM_COMPILED = {
    cat: [re.compile(p) for p in patterns]
    for cat, patterns in HARM_CATEGORIES.items()
}

# Date extraction pattern
DATE_PATTERN = re.compile(
    r'\b(?:'
    r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|'
    r'Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
    r'\s+\d{1,2},?\s+\d{4}'
    r'|\d{1,2}/\d{1,2}/\d{4}'
    r'|\d{4}-\d{2}-\d{2}'
    r')\b'
)


class EvidenceVehicleScanner(Agent9999):
    """Scans PDF files and matches evidence to court vehicles (case lanes)."""

    agent_id = "E01"
    agent_name = "Evidence Vehicle Scanner"
    tier = "E"  # Evidence tier
    version = "1.0"

    def __init__(self, scan_paths: Optional[List[str]] = None, **kwargs):
        super().__init__(**kwargs)
        self.scan_paths = scan_paths or [
            r"C:\Users\andre\LitigationOS",
            r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE",
            r"D:\\",
            r"F:\\",
            r"G:\\",
        ]
        self.item_timeout = 60  # 60s per PDF
        self.parallel_workers = 2
        self._pdf_extractor = None
        self._init_pdf_extractor()

    def _init_pdf_extractor(self):
        """Initialize PDF text extraction (PyMuPDF preferred, pdfplumber fallback)."""
        try:
            import fitz  # PyMuPDF
            self._pdf_extractor = "pymupdf"
        except ImportError:
            try:
                import pdfplumber
                self._pdf_extractor = "pdfplumber"
            except ImportError:
                self._pdf_extractor = None

    def _extract_pdf_text(self, pdf_path: str, max_pages: int = 50) -> str:
        """Extract text from PDF using best available library."""
        text_parts = []
        try:
            if self._pdf_extractor == "pymupdf":
                import fitz
                doc = fitz.open(pdf_path)
                for i, page in enumerate(doc):
                    if i >= max_pages:
                        break
                    text_parts.append(page.get_text())
                doc.close()
            elif self._pdf_extractor == "pdfplumber":
                import pdfplumber
                with pdfplumber.open(pdf_path) as pdf:
                    for i, page in enumerate(pdf.pages):
                        if i >= max_pages:
                            break
                        text = page.extract_text()
                        if text:
                            text_parts.append(text)
            else:
                # Last resort: read raw bytes looking for text streams
                with open(pdf_path, "rb") as f:
                    raw = f.read(500_000)  # First 500KB
                try:
                    decoded = raw.decode("utf-8", errors="ignore")
                    # Extract text between BT/ET markers or readable ASCII
                    readable = re.findall(r'[\x20-\x7e]{20,}', decoded)
                    text_parts = readable[:100]
                except Exception:
                    pass
        except Exception as e:
            self.log(f"PDF extraction failed for {pdf_path}: {e}", level="WARN")
        return "\n".join(text_parts)

    def _extract_txt_content(self, file_path: str, max_bytes: int = 500_000) -> str:
        """Extract content from text-based files (txt, md, csv)."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read(max_bytes)
        except Exception:
            return ""

    def _classify_to_vehicles(self, text: str, file_path: str) -> List[Dict[str, Any]]:
        """Classify text content to court vehicles using MEEK signals."""
        matches = []
        text_lower = text.lower()

        # Priority order: E → D → F → C → A → B (per MEEK protocol)
        for lane_key in ["E", "D", "F", "C", "A", "B"]:
            lane_data = MEEK_SIGNALS[lane_key]
            score = 0
            reasons = []
            quotes = []

            # Check case numbers (highest confidence)
            for case_re in lane_data["compiled_cases"]:
                found = case_re.findall(text)
                if found:
                    score += 40
                    reasons.append(f"Case number: {found[0]}")

            # Check MEEK patterns
            for pattern in lane_data["compiled"]:
                found = pattern.findall(text)
                if found:
                    hit_count = min(len(found), 10)
                    score += 5 * hit_count
                    # Extract surrounding context as quote
                    for m in pattern.finditer(text):
                        start = max(0, m.start() - 80)
                        end = min(len(text), m.end() + 80)
                        snippet = text[start:end].strip().replace("\n", " ")
                        if len(snippet) > 20:
                            quotes.append(snippet[:200])
                    reasons.append(f"MEEK pattern ({hit_count} hits)")

            if score >= 10:
                matches.append({
                    "lane": lane_key,
                    "vehicle": lane_data["vehicle"],
                    "confidence": min(score, 100),
                    "reasons": reasons,
                    "quotes": quotes[:5],  # Top 5 quotes
                })

        return matches

    def _detect_harms(self, text: str) -> List[Dict[str, Any]]:
        """Detect harm categories in text content."""
        harms = []
        for category, patterns in HARM_COMPILED.items():
            hit_count = 0
            sample_quotes = []
            for pattern in patterns:
                found = list(pattern.finditer(text))
                if found:
                    hit_count += len(found)
                    for m in found[:2]:
                        start = max(0, m.start() - 60)
                        end = min(len(text), m.end() + 60)
                        sample_quotes.append(text[start:end].strip()[:200])
            if hit_count > 0:
                harms.append({
                    "category": category,
                    "hit_count": hit_count,
                    "confidence": min(hit_count * 15, 100),
                    "sample_quotes": sample_quotes[:3],
                })
        return harms

    def _extract_dates(self, text: str) -> List[str]:
        """Extract all dates from text."""
        return list(set(DATE_PATTERN.findall(text)))[:20]

    def _discover_files(self) -> List[str]:
        """Discover PDF and text evidence files across all scan paths."""
        files = []
        extensions = {".pdf", ".txt", ".md"}
        for scan_path in self.scan_paths:
            try:
                p = Path(scan_path)
                if not p.exists():
                    continue
                for ext in extensions:
                    for f in p.rglob(f"*{ext}"):
                        try:
                            if f.stat().st_size > 0 and f.stat().st_size < 100_000_000:
                                files.append(str(f))
                        except (PermissionError, OSError):
                            continue
            except Exception as e:
                self.log(f"Skipping {scan_path}: {e}", level="WARN")
        return files

    def _init_db_table(self, conn: sqlite3.Connection):
        """Create evidence_vehicle_matches table."""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS evidence_vehicle_matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                file_name TEXT,
                file_ext TEXT,
                file_size INTEGER,
                lane TEXT NOT NULL,
                vehicle TEXT NOT NULL,
                confidence INTEGER DEFAULT 0,
                match_reasons TEXT,
                extracted_quotes TEXT,
                harm_categories TEXT,
                event_dates TEXT,
                page_count INTEGER,
                scanned_at TEXT DEFAULT (datetime('now')),
                UNIQUE(file_path, lane)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_evm_lane 
            ON evidence_vehicle_matches(lane, confidence DESC)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_evm_harm 
            ON evidence_vehicle_matches(harm_categories)
        """)
        conn.commit()

    def setup(self) -> bool:
        """Initialize DB table and discover files."""
        try:
            with sqlite3.connect(str(LITIGATION_DB), timeout=60) as conn:
                conn.execute("PRAGMA busy_timeout=60000")
                conn.execute("PRAGMA journal_mode=WAL")
                self._init_db_table(conn)
            return True
        except Exception as e:
            self.log(f"Setup failed: {e}", level="ERROR")
            return False

    def get_items(self) -> List[str]:
        """Return list of files to scan."""
        return self._discover_files()

    def process_item(self, file_path: str) -> Dict[str, Any]:
        """Process a single file — extract text, classify to vehicles, detect harms."""
        fp = Path(file_path)
        ext = fp.suffix.lower()

        # Extract text
        if ext == ".pdf":
            text = self._extract_pdf_text(file_path)
        else:
            text = self._extract_txt_content(file_path)

        if len(text.strip()) < 50:
            raise SkipItemError(f"Insufficient text content in {fp.name}")

        # Classify to court vehicles
        vehicle_matches = self._classify_to_vehicles(text, file_path)
        if not vehicle_matches:
            raise SkipItemError(f"No court vehicle match for {fp.name}")

        # Detect harm categories
        harms = self._detect_harms(text)

        # Extract dates
        dates = self._extract_dates(text)

        # Write to DB
        with sqlite3.connect(str(LITIGATION_DB), timeout=60) as conn:
            conn.execute("PRAGMA busy_timeout=60000")
            conn.execute("PRAGMA journal_mode=WAL")
            for vm in vehicle_matches:
                try:
                    conn.execute("""
                        INSERT OR REPLACE INTO evidence_vehicle_matches
                        (file_path, file_name, file_ext, file_size, lane, vehicle,
                         confidence, match_reasons, extracted_quotes, harm_categories,
                         event_dates)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        file_path,
                        fp.name,
                        ext,
                        fp.stat().st_size if fp.exists() else 0,
                        vm["lane"],
                        vm["vehicle"],
                        vm["confidence"],
                        json.dumps(vm["reasons"]),
                        json.dumps(vm["quotes"]),
                        json.dumps([h["category"] for h in harms]),
                        json.dumps(dates),
                    ))
                except sqlite3.IntegrityError:
                    pass
            conn.commit()

        return {
            "file": fp.name,
            "vehicles": [f"{vm['lane']}({vm['confidence']}%)" for vm in vehicle_matches],
            "harms": [h["category"] for h in harms],
            "dates_found": len(dates),
        }

    def run(self) -> AgentResult:
        """Execute the evidence vehicle scan."""
        return self._run_standard()


if __name__ == "__main__":
    scanner = EvidenceVehicleScanner()
    result = scanner.run()
    print(f"\n{'='*60}")
    print(f"Evidence Vehicle Scanner: {result.status}")
    print(f"Processed: {result.stats.items_processed}")
    print(f"Skipped: {result.stats.items_skipped}")
    print(f"Errors: {result.stats.items_errored}")
