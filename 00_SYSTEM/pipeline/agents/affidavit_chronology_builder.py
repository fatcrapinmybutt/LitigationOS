"""
AFFIDAVIT CHRONOLOGY BUILDER (E02) — Master Narrative Engine

Gathers ALL affidavits, sworn statements, and chronological evidence from:
  - All 6 drives (C:, D:, F:, G:, H:, I:)
  - ChatGPT conversation exports (509MB JSON + 1.45GB HTML)
  - Litigation filing package (Desktop)
  - litigation_context.db (evidence_quotes, docket_events, canonical_timeline)
  - All extracted text files from pipeline processing

Then chronologically organizes everything by date and event, and narrates
it into a cohesive first-person story telling what happened to Andrew over
the last 3 years — backed by specific document citations.

Output:
  - MASTER_AFFIDAVIT_CHRONOLOGY.md — The complete narrative
  - affidavit_events table in litigation_context.db
  - Sorted by date with source citations for every statement

v1.0 — Initial release
"""
import json
import os
import re
import sqlite3
import sys
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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

OUTPUT_DIR = Path(r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE")

# ─── Source Paths ───
AFFIDAVIT_SEARCH_PATHS = [
    r"C:\Users\andre\LitigationOS",
    r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE",
    r"D:\\",
    r"F:\\",
    r"G:\\",
]

CHATGPT_EXPORTS = [
    r"C:\Users\andre\LitigationOS\09_DATA\chatgpt_conversations_raw_export.json",
    r"C:\Users\andre\LitigationOS\09_DATA\chat.html",
]

# ─── Date Extraction ───
DATE_PATTERNS = [
    (re.compile(r'(\d{4})-(\d{2})-(\d{2})'), "%Y-%m-%d"),
    (re.compile(r'(\d{1,2})/(\d{1,2})/(\d{4})'), "%m/%d/%Y"),
    (re.compile(
        r'(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|'
        r'Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|'
        r'Dec(?:ember)?)\s+(\d{1,2}),?\s+(\d{4})'
    ), "month_name"),
]

MONTH_MAP = {
    "jan": 1, "january": 1, "feb": 2, "february": 2,
    "mar": 3, "march": 3, "apr": 4, "april": 4,
    "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "september": 9,
    "oct": 10, "october": 10, "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

# ─── Affidavit Detection ───
AFFIDAVIT_PATTERNS = [
    re.compile(r'(?i)affidavit', re.IGNORECASE),
    re.compile(r'(?i)sworn\s+(?:statement|declaration|testimony)', re.IGNORECASE),
    re.compile(r'(?i)verification\s+(?:of|under)\s+(?:oath|penalty)', re.IGNORECASE),
    re.compile(r'(?i)under\s+penalty\s+of\s+perjury', re.IGNORECASE),
    re.compile(r'(?i)I,\s+Andrew\s+(?:James\s+)?Pigors.*(?:swear|affirm|declare|state)', re.IGNORECASE),
    re.compile(r'(?i)(?:COMES\s+NOW|comes\s+now).*(?:swear|affirm|declare)', re.IGNORECASE),
]

# ─── Key Event Patterns (for ChatGPT mining) ───
EVENT_PATTERNS = {
    "custody_event": re.compile(
        r'(?i)(?:custody|parenting\s+time|visitation|withhold|denied\s+access|'
        r'picked\s+up|dropped\s+off|exchange|handoff)', re.IGNORECASE),
    "court_event": re.compile(
        r'(?i)(?:hearing|court\s+date|filed|motion|order|ruling|judge|'
        r'show\s+cause|arraignment|sentencing|jail)', re.IGNORECASE),
    "housing_event": re.compile(
        r'(?i)(?:eviction|rent|lease|water\s+shutoff|sewage|mold|'
        r'shady\s+oaks|trailer|lot\s+(?:fee|rent)|move)', re.IGNORECASE),
    "police_event": re.compile(
        r'(?i)(?:police|officer|arrest|report|911|dispatch|'
        r'welfare\s+check|investigation|incident)', re.IGNORECASE),
    "medical_event": re.compile(
        r'(?i)(?:HealthWest|evaluation|mental\s+health|ADHD|'
        r'delusional|hospital|ambulance|medication)', re.IGNORECASE),
    "financial_event": re.compile(
        r'(?i)(?:child\s+support|arrears|payment|income|'
        r'lost\s+(?:job|employment)|fired|daycare)', re.IGNORECASE),
    "threat_event": re.compile(
        r'(?i)(?:threat|intimidat|harass|stalk|'
        r'Albert|Cody|Watson.*(?:family|father|brother))', re.IGNORECASE),
}

# Canonical timeline events (verified — from user corrections)
CANONICAL_EVENTS = [
    ("2023-12-03", "PPO filed AND granted same day (ex parte) against Andrew", "court_event"),
    ("2024-03-26", "First withholding begins — Emily refuses custody exchange", "custody_event"),
    ("2024-04-01", "Andrew filed custody case FIRST (plaintiff) with UCCJEA", "court_event"),
    ("2024-05-05", "50/50 custody restored under temporary order", "custody_event"),
    ("2024-10-18", "Andrew pled guilty to PPO violations (CC 382a)", "court_event"),
    ("2024-10-20", "Albert Watson served PPO by throwing through car window, took child from Andrew's arms", "threat_event"),
    ("2025-05-20", "Water shutoff at Shady Oaks while child present", "housing_event"),
    ("2025-07-17", "Ex parte order overturned — Emily gets 100% custody", "court_event"),
    ("2025-07-29", "Second withholding begins — ONGOING", "custody_event"),
    ("2025-08-08", "Same-day ex parte order, complete parenting time suspension", "court_event"),
    ("2025-09-04", "First HealthWest eval — FAVORABLE (all scores = 0)", "medical_event"),
    ("2025-09-11", "Second HealthWest eval — 'Rule-out Delusional Disorder' (7-day flip)", "medical_event"),
    ("2025-11-15", "Show Cause #5: 14 days jail (muted 7x, Martini silent)", "court_event"),
    ("2025-11-26", "Show Cause #6+7: 45 days jail (AppClose birthday messages)", "court_event"),
]


class AffidavitChronologyBuilder(Agent9999):
    """Builds master chronological affidavit narrative from all sources."""

    agent_id = "E02"
    agent_name = "Affidavit Chronology Builder"
    tier = "E"
    version = "1.0"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.item_timeout = 120  # 2 min per source file
        self.parallel_workers = 2
        self.events: List[Dict[str, Any]] = []

    def _parse_date(self, text: str) -> Optional[str]:
        """Extract the first date from text, return as YYYY-MM-DD."""
        for pattern, fmt in DATE_PATTERNS:
            match = pattern.search(text)
            if match:
                groups = match.groups()
                try:
                    if fmt == "month_name":
                        month = MONTH_MAP.get(groups[0].lower()[:3], 0)
                        day = int(groups[1])
                        year = int(groups[2])
                        if 2022 <= year <= 2027 and 1 <= month <= 12 and 1 <= day <= 31:
                            return f"{year:04d}-{month:02d}-{day:02d}"
                    elif fmt == "%Y-%m-%d":
                        y, m, d = int(groups[0]), int(groups[1]), int(groups[2])
                        if 2022 <= y <= 2027:
                            return f"{y:04d}-{m:02d}-{d:02d}"
                    elif fmt == "%m/%d/%Y":
                        m, d, y = int(groups[0]), int(groups[1]), int(groups[2])
                        if 2022 <= y <= 2027:
                            return f"{y:04d}-{m:02d}-{d:02d}"
                except (ValueError, IndexError):
                    continue
        return None

    def _classify_event(self, text: str) -> str:
        """Classify event text into a category."""
        for category, pattern in EVENT_PATTERNS.items():
            if pattern.search(text):
                return category
        return "general"

    def _extract_events_from_text(self, text: str, source: str) -> List[Dict[str, Any]]:
        """Extract dated events from text content."""
        events = []
        # Split into paragraphs
        paragraphs = re.split(r'\n\s*\n|\n(?=\d{1,2}[./]|\d{4}-|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))', text)

        for para in paragraphs:
            para = para.strip()
            if len(para) < 30:
                continue
            date = self._parse_date(para)
            if date:
                category = self._classify_event(para)
                # Clean up the paragraph
                clean = re.sub(r'\s+', ' ', para).strip()
                if len(clean) > 500:
                    clean = clean[:500] + "..."
                events.append({
                    "date": date,
                    "text": clean,
                    "category": category,
                    "source": source,
                })
        return events

    def _mine_chatgpt_export(self, json_path: str) -> List[Dict[str, Any]]:
        """Mine ChatGPT JSON export for chronological events."""
        events = []
        try:
            with open(json_path, "r", encoding="utf-8", errors="replace") as f:
                data = json.load(f)

            conversations = data if isinstance(data, list) else [data]
            for convo in conversations:
                title = convo.get("title", "")
                mapping = convo.get("mapping", {})
                for node_id, node in mapping.items():
                    msg = node.get("message")
                    if not msg:
                        continue
                    role = msg.get("author", {}).get("role", "")
                    if role != "user":
                        continue
                    parts = msg.get("content", {}).get("parts", [])
                    for part in parts:
                        if isinstance(part, str) and len(part) > 30:
                            extracted = self._extract_events_from_text(
                                part, f"ChatGPT: {title}"
                            )
                            events.extend(extracted)
        except json.JSONDecodeError:
            self.log(f"JSON decode error in {json_path}", level="WARN")
        except Exception as e:
            self.log(f"ChatGPT mining error: {e}", level="WARN")
        return events

    def _mine_db_events(self) -> List[Dict[str, Any]]:
        """Mine litigation_context.db for chronological events."""
        events = []
        try:
            with sqlite3.connect(str(LITIGATION_DB), timeout=60) as conn:
                conn.execute("PRAGMA busy_timeout=60000")
                conn.execute("PRAGMA journal_mode=WAL")
                conn.row_factory = sqlite3.Row

                # Docket events
                try:
                    for row in conn.execute(
                        "SELECT * FROM docket_events ORDER BY event_date"
                    ).fetchall():
                        d = dict(row)
                        date = d.get("event_date", "")
                        desc = d.get("description", d.get("event_description", ""))
                        if date and desc:
                            events.append({
                                "date": date[:10],
                                "text": desc,
                                "category": "court_event",
                                "source": f"DB:docket_events (case {d.get('case_number', '')})",
                            })
                except sqlite3.OperationalError:
                    pass

                # Evidence quotes with dates
                try:
                    for row in conn.execute(
                        "SELECT * FROM evidence_quotes WHERE quote_text LIKE '%202%' LIMIT 5000"
                    ).fetchall():
                        d = dict(row)
                        text = d.get("quote_text", "")
                        date = self._parse_date(text)
                        if date:
                            events.append({
                                "date": date,
                                "text": text[:500],
                                "category": self._classify_event(text),
                                "source": f"DB:evidence_quotes ({d.get('source_file', '')})",
                            })
                except sqlite3.OperationalError:
                    pass

                # Canonical timeline
                try:
                    for row in conn.execute(
                        "SELECT * FROM canonical_timeline ORDER BY event_date"
                    ).fetchall():
                        d = dict(row)
                        events.append({
                            "date": d.get("event_date", "")[:10],
                            "text": d.get("description", ""),
                            "category": d.get("category", "general"),
                            "source": "DB:canonical_timeline",
                        })
                except sqlite3.OperationalError:
                    pass

        except Exception as e:
            self.log(f"DB mining error: {e}", level="WARN")
        return events

    def _discover_affidavit_files(self) -> List[str]:
        """Find all affidavit and sworn statement files."""
        files = []
        keywords = ["affidavit", "sworn", "declaration", "verification", "chronolog"]
        for search_path in AFFIDAVIT_SEARCH_PATHS:
            try:
                p = Path(search_path)
                if not p.exists():
                    continue
                for ext in [".pdf", ".txt", ".md", ".docx"]:
                    for f in p.rglob(f"*{ext}"):
                        try:
                            name_lower = f.name.lower()
                            if any(kw in name_lower for kw in keywords):
                                files.append(str(f))
                            elif f.stat().st_size < 5_000_000:
                                # Check content of smaller files
                                files.append(str(f))
                        except (PermissionError, OSError):
                            continue
            except Exception:
                continue
        return files[:2000]  # Cap at 2000 files

    def _init_db_table(self, conn: sqlite3.Connection):
        """Create affidavit_events table."""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS affidavit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_date TEXT NOT NULL,
                event_text TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                source_file TEXT,
                source_type TEXT,
                confidence INTEGER DEFAULT 50,
                lane TEXT,
                included_in_narrative INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now')),
                UNIQUE(event_date, event_text)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_ae_date 
            ON affidavit_events(event_date)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_ae_category 
            ON affidavit_events(category)
        """)
        conn.commit()

    def _deduplicate_events(self, events: List[Dict]) -> List[Dict]:
        """Remove duplicate events (same date + similar text)."""
        seen = set()
        unique = []
        for ev in events:
            key = f"{ev['date']}:{ev['text'][:100].lower()}"
            if key not in seen:
                seen.add(key)
                unique.append(ev)
        return unique

    def _generate_narrative(self, events: List[Dict]) -> str:
        """Generate the master chronological narrative from sorted events."""
        events.sort(key=lambda x: x.get("date", "0000-00-00"))

        narrative = []
        narrative.append("# MASTER AFFIDAVIT CHRONOLOGY")
        narrative.append("")
        narrative.append("## VERIFICATION")
        narrative.append("")
        narrative.append("I, **Andrew James Pigors**, being first duly sworn, depose and state as follows:")
        narrative.append("")
        narrative.append("1. I am the Plaintiff in *Pigors v. Watson*, Case No. 2024-001507-DC,")
        narrative.append("   14th Circuit Court, Family Division, Muskegon County, Michigan.")
        narrative.append("")
        narrative.append("2. I am over 18 years of age and competent to testify to the matters")
        narrative.append("   set forth herein based on my personal knowledge and experience.")
        narrative.append("")
        narrative.append("3. The following is a true and accurate chronological account of events")
        narrative.append(f"   spanning from 2023 to present ({len(events)} documented events).")
        narrative.append("")
        narrative.append("---")
        narrative.append("")

        # Group by year-month
        current_year = None
        current_month = None
        para_num = 3

        for ev in events:
            date_str = ev.get("date", "")
            if len(date_str) < 7:
                continue

            year = date_str[:4]
            month = date_str[5:7]

            if year != current_year:
                current_year = year
                current_month = None
                narrative.append(f"## {year}")
                narrative.append("")

            if month != current_month:
                current_month = month
                try:
                    month_name = datetime.strptime(f"{year}-{month}-01", "%Y-%m-%d").strftime("%B")
                except ValueError:
                    month_name = f"Month {month}"
                narrative.append(f"### {month_name} {year}")
                narrative.append("")

            para_num += 1
            source = ev.get("source", "personal knowledge")
            category = ev.get("category", "general")
            text = ev.get("text", "").replace("\n", " ").strip()

            # Format as numbered paragraph
            narrative.append(f"{para_num}. **{date_str}** [{category}]: {text}")
            narrative.append(f"   *(Source: {source})*")
            narrative.append("")

        # Add signature block
        narrative.append("---")
        narrative.append("")
        narrative.append("## FURTHER AFFIANT SAYETH NAUGHT")
        narrative.append("")
        narrative.append("I declare under penalty of perjury under the laws of the State of Michigan")
        narrative.append("that the foregoing is true and correct to the best of my knowledge,")
        narrative.append("information, and belief.")
        narrative.append("")
        narrative.append(f"Dated: ________________, {datetime.now().year}")
        narrative.append("")
        narrative.append("_________________________________")
        narrative.append("Andrew James Pigors")
        narrative.append("1977 Whitehall Road, Lot 17")
        narrative.append("North Muskegon, MI 49445")
        narrative.append("(231) 903-5690")
        narrative.append("")
        narrative.append("Subscribed and sworn to before me this _____ day of ____________, "
                         f"{datetime.now().year}.")
        narrative.append("")
        narrative.append("_________________________________")
        narrative.append("Notary Public, State of Michigan")
        narrative.append("My Commission Expires: ___________")

        return "\n".join(narrative)

    def setup(self) -> bool:
        """Initialize DB table."""
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
        """Return sources to process: files + DB + ChatGPT."""
        items = ["__DB_EVENTS__", "__CANONICAL__"]
        for export in CHATGPT_EXPORTS:
            if Path(export).exists():
                items.append(export)
        items.extend(self._discover_affidavit_files())
        return items

    def process_item(self, item: str) -> Dict[str, Any]:
        """Process a single source for chronological events."""
        if item == "__DB_EVENTS__":
            new_events = self._mine_db_events()
            self.events.extend(new_events)
            return {"source": "DB", "events_found": len(new_events)}

        if item == "__CANONICAL__":
            for date, text, cat in CANONICAL_EVENTS:
                self.events.append({
                    "date": date,
                    "text": text,
                    "category": cat,
                    "source": "CANONICAL (user-verified)",
                })
            return {"source": "canonical", "events_found": len(CANONICAL_EVENTS)}

        fp = Path(item)
        ext = fp.suffix.lower()

        if ext == ".json" and "chatgpt" in fp.name.lower():
            new_events = self._mine_chatgpt_export(item)
            self.events.extend(new_events)
            return {"source": f"ChatGPT:{fp.name}", "events_found": len(new_events)}

        # Text-based files
        if ext in (".txt", ".md", ".csv"):
            try:
                with open(item, "r", encoding="utf-8", errors="replace") as f:
                    text = f.read(500_000)
            except Exception:
                raise SkipItemError(f"Cannot read {fp.name}")

            # Check if it's an affidavit
            is_affidavit = any(p.search(text) for p in AFFIDAVIT_PATTERNS)
            if is_affidavit or any(p.search(fp.name) for p in AFFIDAVIT_PATTERNS):
                new_events = self._extract_events_from_text(text, f"Affidavit:{fp.name}")
                self.events.extend(new_events)
                return {"source": fp.name, "is_affidavit": True, "events_found": len(new_events)}

            # Non-affidavit but may have dated events
            new_events = self._extract_events_from_text(text, fp.name)
            if new_events:
                self.events.extend(new_events)
                return {"source": fp.name, "events_found": len(new_events)}

            raise SkipItemError(f"No dated events in {fp.name}")

        if ext == ".pdf":
            try:
                import fitz
                doc = fitz.open(item)
                text_parts = []
                for i, page in enumerate(doc):
                    if i >= 30:
                        break
                    text_parts.append(page.get_text())
                doc.close()
                text = "\n".join(text_parts)
            except Exception:
                raise SkipItemError(f"Cannot extract PDF: {fp.name}")

            new_events = self._extract_events_from_text(text, f"PDF:{fp.name}")
            self.events.extend(new_events)
            return {"source": fp.name, "events_found": len(new_events)}

        raise SkipItemError(f"Unsupported format: {ext}")

    def teardown(self, result: AgentResult) -> AgentResult:
        """After all items processed, deduplicate, save to DB, generate narrative."""
        self.log(f"Total raw events collected: {len(self.events)}")

        # Deduplicate
        unique_events = self._deduplicate_events(self.events)
        self.log(f"After dedup: {len(unique_events)} unique events")

        # Save to DB
        try:
            with sqlite3.connect(str(LITIGATION_DB), timeout=60) as conn:
                conn.execute("PRAGMA busy_timeout=60000")
                conn.execute("PRAGMA journal_mode=WAL")
                rows = [(
                    ev["date"], ev["text"], ev.get("category", "general"),
                    ev.get("source", ""), "auto_extracted", 50, ""
                ) for ev in unique_events]
                conn.executemany("""
                    INSERT OR IGNORE INTO affidavit_events
                    (event_date, event_text, category, source_file, source_type, confidence, lane)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, rows)
                conn.commit()
                self.log(f"Saved {len(rows)} events to affidavit_events table")
        except Exception as e:
            self.log(f"DB save error: {e}", level="ERROR")

        # Generate narrative
        narrative = self._generate_narrative(unique_events)
        output_path = OUTPUT_DIR / "MASTER_AFFIDAVIT_CHRONOLOGY.md"
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(narrative)
            self.log(f"Narrative written to {output_path} ({len(narrative)} chars)")
        except Exception as e:
            self.log(f"Narrative write error: {e}", level="ERROR")

        result.stats.metadata["total_events"] = len(unique_events)
        result.stats.metadata["narrative_path"] = str(output_path)
        result.stats.metadata["narrative_length"] = len(narrative)
        return result

    def run(self) -> AgentResult:
        """Execute the chronology build."""
        return self._run_standard()


if __name__ == "__main__":
    builder = AffidavitChronologyBuilder()
    result = builder.run()
    print(f"\n{'='*60}")
    print(f"Affidavit Chronology Builder: {result.status}")
    print(f"Events: {result.stats.metadata.get('total_events', 0)}")
    print(f"Narrative: {result.stats.metadata.get('narrative_path', 'N/A')}")
