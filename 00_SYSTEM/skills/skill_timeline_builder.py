"""
Chronological Timeline Builder Skill v1.0
==========================================
LitigationOS 2026 v1.0 — Pigors v. Watson

Builds evidence-driven litigation timelines from database records.
Outputs court-ready numbered paragraphs with exhibit cross-references.

Sources harvested:
  - docket_events   (structured docket entries)
  - evidence_quotes  (extracted evidence with date_ref)
  - contradiction_map (contradictions with timestamps)
  - impeachment_items (impeachment material)
  - md_sections       (markdown sections mined for dates)
  - pages             (raw OCR page text mined for dates)
  - documents         (exhibit cross-reference catalog)

No external API calls. Pure SQLite + regex date extraction.
"""

import sqlite3
import re
import os
import json
import csv
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple

DB_PATH = r"C:\Users\andre\litigation_context.db"

# ── Case Lane Mapping ────────────────────────────────────────────────────────

LANE_MAP = {
    "A": {"case_id": "2024-001507-DC", "label": "Watson Custody",
           "keywords": ["custody", "parenting", "watson", "emily", "lincoln", "mcneill"]},
    "B": {"case_id": None, "label": "Shady Oaks Housing",
           "keywords": ["shady oaks", "housing", "landlord", "tenant", "lease"]},
    "C": {"case_id": None, "label": "Convergence",
           "keywords": ["convergence", "consolidated", "cross-lane"]},
    "D": {"case_id": "2023-5907-PP", "label": "PPO",
           "keywords": ["ppo", "protection order", "2023-5907"]},
    "E": {"case_id": None, "label": "Judicial Misconduct",
           "keywords": ["jtc", "misconduct", "judicial", "canon", "complaint"]},
    "F": {"case_id": "COA 366810", "label": "Appellate",
           "keywords": ["appeal", "coa", "366810", "appellate", "court of appeals"]},
}

# ── Date Extraction Patterns ─────────────────────────────────────────────────
# Handles standard formats + OCR artifacts (e.g. "1 0/29/25" for "10/29/25")

MONTH_NAMES = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "jun": 6, "jul": 7, "aug": 8, "sep": 9, "sept": 9,
    "oct": 10, "nov": 11, "dec": 12,
}

DATE_PATTERNS = [
    # ISO: 2024-06-15
    (r'(\d{4})-(\d{1,2})-(\d{1,2})', 'YMD'),
    # US standard: 06/15/2024 or 6/15/2024
    (r'(\d{1,2})/(\d{1,2})/(\d{4})', 'MDY4'),
    # OCR artifact with space: "1 0/29/25" or "1 1/26/25" — MUST precede MDY2
    (r'(\d)\s+(\d)/(\d{1,2})/(\d{2,4})', 'OCR_MDY'),
    # US short year: 06/15/24 or 6/15/24 — only when NOT preceded by digit+space
    (r'(?<!\d\s)(\d{1,2})/(\d{1,2})/(\d{2})(?!\d)', 'MDY2'),
    # Month DD, YYYY: June 15, 2024 or Jun 15, 2024
    (r'((?:January|February|March|April|May|June|July|August|September|October|November|December|'
     r'Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.?)\s+(\d{1,2}),?\s+(\d{4})', 'NAMED_MDY'),
    # DD Month YYYY: 15 June 2024
    (r'(\d{1,2})\s+((?:January|February|March|April|May|June|July|August|September|October|November|December))\s+(\d{4})', 'NAMED_DMY'),
    # Month YYYY (first of month): June 2024
    (r'((?:January|February|March|April|May|June|July|August|September|October|November|December))\s+(\d{4})', 'NAMED_MY'),
]


def _normalize_date(match_groups: tuple, pattern_type: str) -> Optional[str]:
    """Convert extracted date components to ISO YYYY-MM-DD. Returns None on failure."""
    try:
        if pattern_type == 'YMD':
            y, m, d = int(match_groups[0]), int(match_groups[1]), int(match_groups[2])
        elif pattern_type == 'MDY4':
            m, d, y = int(match_groups[0]), int(match_groups[1]), int(match_groups[2])
        elif pattern_type == 'MDY2':
            m, d, y2 = int(match_groups[0]), int(match_groups[1]), int(match_groups[2])
            y = 2000 + y2 if y2 < 50 else 1900 + y2
        elif pattern_type == 'OCR_MDY':
            # "1 0/29/25" → month=10, day=29, year=25
            m = int(match_groups[0]) * 10 + int(match_groups[1])
            d = int(match_groups[2])
            yr_raw = int(match_groups[3])
            y = (2000 + yr_raw) if yr_raw < 100 and yr_raw < 50 else (1900 + yr_raw if yr_raw < 100 else yr_raw)
        elif pattern_type == 'NAMED_MDY':
            month_str = match_groups[0].rstrip('.').lower()
            m = MONTH_NAMES.get(month_str, 0)
            d = int(match_groups[1])
            y = int(match_groups[2])
        elif pattern_type == 'NAMED_DMY':
            d = int(match_groups[0])
            m = MONTH_NAMES.get(match_groups[1].lower(), 0)
            y = int(match_groups[2])
        elif pattern_type == 'NAMED_MY':
            m = MONTH_NAMES.get(match_groups[0].lower(), 0)
            d = 1
            y = int(match_groups[1])
        else:
            return None

        if not (1 <= m <= 12 and 1 <= d <= 31 and 1990 <= y <= 2030):
            return None
        # Validate with datetime
        datetime(y, m, d)
        return f"{y:04d}-{m:02d}-{d:02d}"
    except (ValueError, TypeError):
        return None


def extract_dates(text: str) -> List[Tuple[str, int]]:
    """Extract all dates from text. Returns list of (iso_date, char_position)."""
    if not text:
        return []
    results = []
    # Track which character ranges are already claimed by a match
    claimed_ranges: List[Tuple[int, int]] = []

    for pattern, ptype in DATE_PATTERNS:
        flags = re.IGNORECASE if 'NAMED' in ptype else 0
        for m in re.finditer(pattern, text, flags):
            iso = _normalize_date(m.groups(), ptype)
            if iso:
                start, end = m.start(), m.end()
                # Skip if this range overlaps with an already-claimed match
                overlaps = any(
                    not (end <= cs or start >= ce)
                    for cs, ce in claimed_ranges
                )
                if not overlaps:
                    claimed_ranges.append((start, end))
                    results.append((iso, start))

    # Sort by position in text
    results.sort(key=lambda x: x[1])
    return results


def _snippet(text: str, pos: int, radius: int = 120) -> str:
    """Extract a context snippet around a position in text."""
    if not text:
        return ""
    start = max(0, pos - radius)
    end = min(len(text), pos + radius)
    snippet = text[start:end].strip()
    # Clean OCR whitespace artifacts
    snippet = re.sub(r'\s+', ' ', snippet)
    return snippet


# ── Timeline Event ────────────────────────────────────────────────────────────

class TimelineEvent:
    """Single event in the chronological timeline."""

    __slots__ = ('date_iso', 'title', 'description', 'source_table', 'source_id',
                 'event_type', 'case_id', 'speaker', 'truth_tag', 'severity',
                 'exhibit_refs', 'legal_hooks', '_dedup_key')

    def __init__(self, date_iso: str, title: str, description: str = "",
                 source_table: str = "", source_id: str = "",
                 event_type: str = "general", case_id: str = "",
                 speaker: str = "", truth_tag: str = "UNVERIFIED",
                 severity: str = "", exhibit_refs: List[str] = None,
                 legal_hooks: List[str] = None):
        self.date_iso = date_iso
        self.title = title
        self.description = description
        self.source_table = source_table
        self.source_id = str(source_id)
        self.event_type = event_type
        self.case_id = case_id
        self.speaker = speaker
        self.truth_tag = truth_tag
        self.severity = severity
        self.exhibit_refs = exhibit_refs or []
        self.legal_hooks = legal_hooks or []
        # Dedup key: date + normalized title hash
        norm = re.sub(r'\s+', ' ', (title + description)[:200].lower().strip())
        self._dedup_key = f"{date_iso}|{hashlib.md5(norm.encode('utf-8', errors='replace')).hexdigest()[:12]}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date_iso,
            "title": self.title,
            "description": self.description,
            "source": f"{self.source_table}:{self.source_id}",
            "event_type": self.event_type,
            "case_id": self.case_id,
            "speaker": self.speaker,
            "truth_tag": self.truth_tag,
            "severity": self.severity,
            "exhibit_refs": self.exhibit_refs,
            "legal_hooks": self.legal_hooks,
        }

    def __repr__(self):
        return f"<Event {self.date_iso} | {self.title[:60]}>"


# ── Timeline Builder ─────────────────────────────────────────────────────────

class TimelineBuilder:
    """
    Builds evidence-driven chronological timelines from litigation_context.db.
    Harvests events from multiple tables, deduplicates, filters, and formats
    for court filing insertion.
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn = None
        self.events: List[TimelineEvent] = []
        self._exhibit_cache: Dict[int, Dict] = {}
        self._connect()

    def _connect(self):
        """Connect to DB with retry logic."""
        retries = 3
        for attempt in range(retries):
            try:
                self.conn = sqlite3.connect(self.db_path)
                self.conn.row_factory = sqlite3.Row
                self.conn.execute("PRAGMA journal_mode=WAL")
                return
            except sqlite3.Error as e:
                if attempt == retries - 1:
                    raise RuntimeError(f"DB connection failed after {retries} attempts: {e}")
                import time
                time.sleep(2 ** attempt)

    def _query(self, sql: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Execute query with error handling."""
        try:
            cur = self.conn.execute(sql, params)
            return cur.fetchall()
        except sqlite3.Error as e:
            print(f"  [WARN] Query failed: {e}")
            return []

    def _load_exhibit_cache(self):
        """Cache document metadata for exhibit cross-references."""
        if self._exhibit_cache:
            return
        rows = self._query(
            "SELECT id, file_name, file_path, evidence_category FROM documents"
        )
        for r in rows:
            self._exhibit_cache[r["id"]] = {
                "file_name": r["file_name"],
                "file_path": r["file_path"],
                "category": r["evidence_category"] or "UNKNOWN",
            }

    def _doc_ref(self, doc_id: int) -> str:
        """Get exhibit reference string for a document ID."""
        self._load_exhibit_cache()
        if doc_id in self._exhibit_cache:
            d = self._exhibit_cache[doc_id]
            name = os.path.splitext(d["file_name"])[0]
            return f"[Ex. {doc_id}: {name}]"
        return f"[Doc ID {doc_id}]"

    # ── Harvest Methods ───────────────────────────────────────────────────

    def harvest_docket_events(self) -> int:
        """Pull all events from docket_events table."""
        rows = self._query(
            "SELECT event_id, case_id, event_date_iso, title, event_type, "
            "summary, truth_tag FROM docket_events ORDER BY event_date_iso"
        )
        count = 0
        for r in rows:
            evt = TimelineEvent(
                date_iso=r["event_date_iso"],
                title=r["title"],
                description=r["summary"] or "",
                source_table="docket_events",
                source_id=r["event_id"],
                event_type=r["event_type"] or "docket",
                case_id=r["case_id"] or "",
                truth_tag=r["truth_tag"] or "RECORD_RECITED",
            )
            self.events.append(evt)
            count += 1
        return count

    def harvest_evidence_dates(self, keywords: Optional[List[str]] = None) -> int:
        """Extract dated events from evidence_quotes using date_ref and text mining."""
        # First: rows with explicit date_ref
        sql = "SELECT id, document_id, page_number, evidence_category, quote_text, " \
              "speaker, date_ref, legal_significance, quote_type FROM evidence_quotes " \
              "WHERE date_ref IS NOT NULL AND date_ref != ''"
        rows = self._query(sql)

        count = 0
        for r in rows:
            raw_date = r["date_ref"]
            # Try to normalize the date_ref
            dates = extract_dates(raw_date)
            if not dates:
                # Try prepending century hint for short refs like "11/26/2025"
                dates = extract_dates("20" + raw_date if len(raw_date) <= 8 else raw_date)
            if not dates:
                continue

            iso_date = dates[0][0]
            text = (r["quote_text"] or "")[:300]
            text_clean = re.sub(r'\s+', ' ', text).strip()

            # Keyword filter
            if keywords:
                text_lower = text_clean.lower()
                if not any(kw.lower() in text_lower for kw in keywords):
                    continue

            exhibit_ref = self._doc_ref(r["document_id"]) if r["document_id"] else ""

            evt = TimelineEvent(
                date_iso=iso_date,
                title=f"Evidence: {(r['quote_type'] or r['evidence_category'] or 'quote')[:50]}",
                description=text_clean,
                source_table="evidence_quotes",
                source_id=str(r["id"]),
                event_type="evidence",
                speaker=r["speaker"] or "",
                truth_tag="RECORD_RECITED",
                exhibit_refs=[exhibit_ref] if exhibit_ref else [],
                legal_hooks=[r["legal_significance"]] if r["legal_significance"] else [],
            )
            self.events.append(evt)
            count += 1

        # Second: mine quote_text for dates not captured in date_ref
        sql2 = "SELECT id, document_id, page_number, evidence_category, quote_text, " \
               "speaker, legal_significance, quote_type FROM evidence_quotes " \
               "WHERE (date_ref IS NULL OR date_ref = '')"
        rows2 = self._query(sql2)

        for r in rows2:
            text = r["quote_text"] or ""
            if keywords:
                text_lower = text.lower()
                if not any(kw.lower() in text_lower for kw in keywords):
                    continue

            dates = extract_dates(text)
            if not dates:
                continue

            for iso_date, pos in dates[:3]:  # Limit to first 3 dates per quote
                snippet = _snippet(text, pos, 100)
                exhibit_ref = self._doc_ref(r["document_id"]) if r["document_id"] else ""

                evt = TimelineEvent(
                    date_iso=iso_date,
                    title=f"Evidence ({r['evidence_category'] or 'quote'})",
                    description=snippet,
                    source_table="evidence_quotes",
                    source_id=str(r["id"]),
                    event_type="evidence",
                    speaker=r["speaker"] or "",
                    truth_tag="INFERRED",
                    exhibit_refs=[exhibit_ref] if exhibit_ref else [],
                    legal_hooks=[r["legal_significance"]] if r["legal_significance"] else [],
                )
                self.events.append(evt)
                count += 1

        return count

    def harvest_contradictions(self) -> int:
        """Extract dated contradictions from contradiction_map."""
        rows = self._query(
            "SELECT id, source_a_type, source_a_doc_id, source_a_text, "
            "source_b_type, source_b_doc_id, source_b_text, "
            "contradiction_type, severity, legal_impact FROM contradiction_map "
            "WHERE severity IN ('HIGH', 'CRITICAL') "
            "ORDER BY id"
        )
        count = 0
        for r in rows:
            combined = (r["source_a_text"] or "") + " " + (r["source_b_text"] or "")
            dates = extract_dates(combined)
            if not dates:
                continue

            iso_date = dates[0][0]
            desc_a = re.sub(r'\s+', ' ', (r["source_a_text"] or "")[:150]).strip()
            desc_b = re.sub(r'\s+', ' ', (r["source_b_text"] or "")[:150]).strip()

            refs = []
            if r["source_a_doc_id"]:
                refs.append(self._doc_ref(r["source_a_doc_id"]))
            if r["source_b_doc_id"]:
                refs.append(self._doc_ref(r["source_b_doc_id"]))

            evt = TimelineEvent(
                date_iso=iso_date,
                title=f"Contradiction: {r['contradiction_type'] or 'conflict'}",
                description=f"Source A ({r['source_a_type']}): {desc_a} | "
                            f"Source B ({r['source_b_type']}): {desc_b}",
                source_table="contradiction_map",
                source_id=str(r["id"]),
                event_type="contradiction",
                severity=r["severity"] or "HIGH",
                exhibit_refs=refs,
                legal_hooks=[r["legal_impact"]] if r["legal_impact"] else [],
            )
            self.events.append(evt)
            count += 1
        return count

    def harvest_impeachment(self) -> int:
        """Extract dated impeachment items."""
        rows = self._query(
            "SELECT id, item_type, speaker, transcript_doc_id, transcript_page, "
            "statement, contradicting_doc_id, contradicting_text, "
            "legal_hook, severity FROM impeachment_items "
            "WHERE severity IN ('HIGH', 'CRITICAL') "
            "ORDER BY id"
        )
        count = 0
        for r in rows:
            combined = (r["statement"] or "") + " " + (r["contradicting_text"] or "")
            dates = extract_dates(combined)
            if not dates:
                continue

            iso_date = dates[0][0]
            stmt = re.sub(r'\s+', ' ', (r["statement"] or "")[:200]).strip()

            refs = []
            if r["transcript_doc_id"]:
                refs.append(self._doc_ref(r["transcript_doc_id"]))
            if r["contradicting_doc_id"]:
                refs.append(self._doc_ref(r["contradicting_doc_id"]))

            evt = TimelineEvent(
                date_iso=iso_date,
                title=f"Impeachment: {r['item_type'] or 'inconsistency'}",
                description=stmt,
                source_table="impeachment_items",
                source_id=str(r["id"]),
                event_type="impeachment",
                speaker=r["speaker"] or "",
                severity=r["severity"] or "HIGH",
                exhibit_refs=refs,
                legal_hooks=[r["legal_hook"]] if r["legal_hook"] else [],
            )
            self.events.append(evt)
            count += 1
        return count

    def harvest_from_md_sections(self, keywords: Optional[List[str]] = None) -> int:
        """Mine md_sections for dated events using regex."""
        where_clauses = []
        params = []

        if keywords:
            kw_conditions = []
            for kw in keywords:
                kw_conditions.append("(section_title LIKE ? OR content LIKE ?)")
                params.extend([f"%{kw}%", f"%{kw}%"])
            where_clauses.append("(" + " OR ".join(kw_conditions) + ")")

        # Limit to sections that likely contain date info
        where_clauses.append("char_count > 20")
        where_clauses.append("char_count < 10000")

        sql = ("SELECT id, source_file, section_title, content "
               "FROM md_sections")
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
        sql += " LIMIT 5000"

        rows = self._query(sql, tuple(params))

        count = 0
        for r in rows:
            content = r["content"] or ""
            dates = extract_dates(content)
            if not dates:
                continue

            for iso_date, pos in dates[:2]:  # Max 2 dates per section
                snippet = _snippet(content, pos, 100)
                evt = TimelineEvent(
                    date_iso=iso_date,
                    title=f"Doc: {(r['section_title'] or 'untitled')[:60]}",
                    description=snippet,
                    source_table="md_sections",
                    source_id=str(r["id"]),
                    event_type="document_reference",
                    truth_tag="INFERRED",
                    exhibit_refs=[f"[Src: {os.path.basename(r['source_file'] or '')}]"],
                )
                self.events.append(evt)
                count += 1
        return count

    def harvest_from_pages(self, keywords: Optional[List[str]] = None) -> int:
        """Mine raw pages for dated events. Handles OCR artifacts."""
        where_clauses = []
        params = []

        if keywords:
            kw_conditions = []
            for kw in keywords:
                kw_conditions.append("p.text_content LIKE ?")
                params.append(f"%{kw}%")
            where_clauses.append("(" + " OR ".join(kw_conditions) + ")")

        sql = ("SELECT p.id, p.document_id, p.page_number, p.text_content, "
               "d.file_name FROM pages p "
               "LEFT JOIN documents d ON p.document_id = d.id")
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
        sql += " LIMIT 3000"

        rows = self._query(sql, tuple(params))

        count = 0
        for r in rows:
            text = r["text_content"] or ""
            dates = extract_dates(text)
            if not dates:
                continue

            for iso_date, pos in dates[:2]:  # Max 2 dates per page
                snippet = _snippet(text, pos, 100)
                doc_name = r["file_name"] or f"doc_{r['document_id']}"
                exhibit_ref = self._doc_ref(r["document_id"]) if r["document_id"] else ""

                evt = TimelineEvent(
                    date_iso=iso_date,
                    title=f"Page ref: {os.path.splitext(doc_name)[0][:50]} p.{r['page_number']}",
                    description=snippet,
                    source_table="pages",
                    source_id=str(r["id"]),
                    event_type="document_reference",
                    truth_tag="INFERRED",
                    exhibit_refs=[exhibit_ref] if exhibit_ref else [],
                )
                self.events.append(evt)
                count += 1
        return count

    # ── Merge & Deduplicate ───────────────────────────────────────────────

    def merge_and_deduplicate(self) -> int:
        """Merge all harvested events, deduplicate by content hash, sort chronologically."""
        # Priority: docket_events > evidence_quotes > contradiction > impeachment > md/pages
        SOURCE_PRIORITY = {
            "docket_events": 0,
            "evidence_quotes": 1,
            "contradiction_map": 2,
            "impeachment_items": 3,
            "md_sections": 4,
            "pages": 5,
        }

        # Sort by source priority so higher-quality sources win dedup
        self.events.sort(key=lambda e: SOURCE_PRIORITY.get(e.source_table, 9))

        # O(n) dedup using dict for key→index lookup
        seen_keys: Dict[str, int] = {}  # key → index into unique list
        unique: List[TimelineEvent] = []

        for evt in self.events:
            short_desc = re.sub(r'\s+', '', evt.description[:80].lower())
            loose_key = f"{evt.date_iso}|{hashlib.md5(short_desc.encode('utf-8', errors='replace')).hexdigest()[:10]}"

            # Check if duplicate
            existing_idx = seen_keys.get(evt._dedup_key) or seen_keys.get(loose_key)

            if existing_idx is None:
                idx = len(unique)
                seen_keys[evt._dedup_key] = idx
                seen_keys[loose_key] = idx
                unique.append(evt)
            else:
                # Merge exhibit refs and legal hooks into existing event
                existing = unique[existing_idx]
                for ref in evt.exhibit_refs:
                    if ref and ref not in existing.exhibit_refs:
                        existing.exhibit_refs.append(ref)
                for hook in evt.legal_hooks:
                    if hook and hook not in existing.legal_hooks:
                        existing.legal_hooks.append(hook)

        removed = len(self.events) - len(unique)
        self.events = sorted(unique, key=lambda e: e.date_iso)
        return removed

    # ── Filters ───────────────────────────────────────────────────────────

    def filter_by_party(self, party_name: str) -> 'TimelineBuilder':
        """Filter events involving specific party (case-insensitive)."""
        party_lower = party_name.lower()
        self.events = [
            e for e in self.events
            if party_lower in (e.description + e.title + e.speaker).lower()
        ]
        return self

    def filter_by_date_range(self, start_date: str, end_date: str) -> 'TimelineBuilder':
        """Filter events within date range (inclusive, ISO format YYYY-MM-DD)."""
        self.events = [
            e for e in self.events
            if start_date <= e.date_iso <= end_date
        ]
        return self

    def filter_by_lane(self, lane: str) -> 'TimelineBuilder':
        """Filter events by case lane (A-F)."""
        lane_upper = lane.upper()
        if lane_upper not in LANE_MAP:
            print(f"  [WARN] Unknown lane '{lane}'. Valid: A-F")
            return self

        lane_info = LANE_MAP[lane_upper]
        case_id = lane_info["case_id"]
        keywords = lane_info["keywords"]

        def _matches(evt: TimelineEvent) -> bool:
            # Match by case_id first
            if case_id and evt.case_id and case_id.lower() in evt.case_id.lower():
                return True
            # Match by keywords in text
            combined = (evt.title + " " + evt.description + " " + evt.speaker).lower()
            return any(kw in combined for kw in keywords)

        self.events = [e for e in self.events if _matches(e)]
        return self

    def filter_by_event_type(self, event_type: str) -> 'TimelineBuilder':
        """Filter events by type (docket, evidence, contradiction, impeachment, document_reference)."""
        self.events = [e for e in self.events if e.event_type == event_type]
        return self

    def filter_by_severity(self, min_severity: str = "HIGH") -> 'TimelineBuilder':
        """Filter events by minimum severity (CRITICAL, HIGH, MEDIUM, LOW)."""
        severity_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "": 0}
        threshold = severity_order.get(min_severity.upper(), 0)
        self.events = [
            e for e in self.events
            if severity_order.get(e.severity.upper(), 0) >= threshold or e.source_table == "docket_events"
        ]
        return self

    # ── Exhibit Cross-Reference ───────────────────────────────────────────

    def format_exhibit_crossref(self) -> Dict[str, List[str]]:
        """Build exhibit cross-reference index: exhibit → list of event dates/titles."""
        xref: Dict[str, List[str]] = {}
        for evt in self.events:
            for ref in evt.exhibit_refs:
                if ref:
                    entry = f"{evt.date_iso}: {evt.title[:60]}"
                    xref.setdefault(ref, []).append(entry)
        return xref

    # ── Formatting ────────────────────────────────────────────────────────

    def format_court_paragraphs(self, include_exhibits: bool = True,
                                 include_source: bool = False) -> str:
        """
        Format as numbered paragraphs for court filings per MCR 2.113.
        Each paragraph: one factual assertion with date and citation.
        """
        if not self.events:
            return "    (No events in timeline.)\n"

        lines = []
        for i, evt in enumerate(self.events, 1):
            # Date formatting: "On June 15, 2024, ..."
            try:
                dt = datetime.strptime(evt.date_iso, "%Y-%m-%d")
                date_str = dt.strftime("%B %d, %Y").replace(" 0", " ")
            except ValueError:
                date_str = evt.date_iso

            # Build paragraph
            para = f"    {i}. On {date_str}, {evt.title.rstrip('.')}."
            if evt.description:
                desc = evt.description.rstrip('.')
                para += f" {desc}."

            # Exhibit cross-references
            if include_exhibits and evt.exhibit_refs:
                refs = "; ".join(r for r in evt.exhibit_refs if r)
                if refs:
                    para += f" See {refs}."

            # Legal hooks
            if evt.legal_hooks:
                hooks = "; ".join(h for h in evt.legal_hooks if h)
                if hooks:
                    para += f" ({hooks})"

            # Source annotation (for internal use, not court filing)
            if include_source:
                para += f" [src: {evt.source_table}:{evt.source_id}]"

            # Truth tag warning for unverified
            if evt.truth_tag in ("INFERRED", "UNVERIFIED"):
                para += " [VERIFY]"

            lines.append(para)

        return "\n\n".join(lines) + "\n"

    def format_markdown_table(self) -> str:
        """Format timeline as markdown table for analysis."""
        lines = [
            "| # | Date | Event | Type | Source | Exhibits |",
            "|---|------|-------|------|--------|----------|",
        ]
        for i, evt in enumerate(self.events, 1):
            refs = ", ".join(evt.exhibit_refs) if evt.exhibit_refs else "—"
            title = evt.title[:60].replace("|", "\\|")
            lines.append(
                f"| {i} | {evt.date_iso} | {title} | {evt.event_type} | "
                f"{evt.source_table} | {refs} |"
            )
        return "\n".join(lines) + "\n"

    def format_summary(self) -> str:
        """Format a brief timeline summary with statistics."""
        if not self.events:
            return "Timeline: 0 events.\n"

        source_counts: Dict[str, int] = {}
        type_counts: Dict[str, int] = {}
        for evt in self.events:
            source_counts[evt.source_table] = source_counts.get(evt.source_table, 0) + 1
            type_counts[evt.event_type] = type_counts.get(evt.event_type, 0) + 1

        earliest = self.events[0].date_iso
        latest = self.events[-1].date_iso

        lines = [
            f"Timeline: {len(self.events)} events | {earliest} → {latest}",
            "Sources: " + ", ".join(f"{k}={v}" for k, v in sorted(source_counts.items())),
            "Types:   " + ", ".join(f"{k}={v}" for k, v in sorted(type_counts.items())),
        ]
        return "\n".join(lines)

    # ── Export ────────────────────────────────────────────────────────────

    def export_timeline(self, output_path: str, format: str = 'court') -> str:
        """
        Export timeline to file.
        Formats: 'court' (numbered paragraphs), 'csv', 'json', 'markdown'
        Returns the output path.
        """
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        if format == 'court':
            content = self._build_court_document()
        elif format == 'csv':
            content = self._build_csv()
        elif format == 'json':
            content = json.dumps(
                [e.to_dict() for e in self.events],
                indent=2, ensure_ascii=False
            )
        elif format == 'markdown':
            content = self.format_markdown_table()
        else:
            raise ValueError(f"Unknown format: {format}. Use: court, csv, json, markdown")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return output_path

    def _build_court_document(self) -> str:
        """Build full court-ready chronological statement of facts."""
        header = (
            "CHRONOLOGICAL STATEMENT OF FACTS\n"
            "=" * 40 + "\n\n"
            "Pigors v. Watson\n"
            "Case No. 2024-001507-DC\n"
            "14th Circuit Court, Muskegon County\n"
            "Hon. Jenny L. McNeill\n\n"
            f"Generated: {datetime.now().strftime('%B %d, %Y')}\n"
            f"Events: {len(self.events)}\n"
            f"Date Range: {self.events[0].date_iso if self.events else 'N/A'} — "
            f"{self.events[-1].date_iso if self.events else 'N/A'}\n\n"
            "-" * 40 + "\n\n"
        )
        body = self.format_court_paragraphs(include_exhibits=True)
        xref = self.format_exhibit_crossref()

        footer = "\n\n" + "-" * 40 + "\n"
        footer += "EXHIBIT CROSS-REFERENCE INDEX\n\n"
        if xref:
            for exhibit, refs in sorted(xref.items()):
                footer += f"  {exhibit}:\n"
                for ref in refs:
                    footer += f"    - {ref}\n"
        else:
            footer += "  (No exhibit cross-references.)\n"

        footer += "\n" + "-" * 40 + "\n"
        footer += f"Days of Parent-Child Separation: {self.calculate_separation_days()}\n"
        footer += "Timeline generated by LitigationOS TimelineBuilder v1.0\n"

        return header + body + footer

    def _build_csv(self) -> str:
        """Build CSV export."""
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "date", "title", "description", "event_type", "source",
            "case_id", "speaker", "truth_tag", "severity", "exhibit_refs", "legal_hooks"
        ])
        for evt in self.events:
            writer.writerow([
                evt.date_iso, evt.title, evt.description, evt.event_type,
                f"{evt.source_table}:{evt.source_id}", evt.case_id,
                evt.speaker, evt.truth_tag, evt.severity,
                "; ".join(evt.exhibit_refs), "; ".join(evt.legal_hooks),
            ])
        return output.getvalue()

    # ── Separation Calculator ─────────────────────────────────────────────

    def calculate_separation_days(self, last_contact_date: str = '2024-07-01') -> int:
        """
        Calculate days since last parent-child contact.
        Default: 2024-07-01 (date of ex parte custody order).
        """
        try:
            last_contact = datetime.strptime(last_contact_date, "%Y-%m-%d")
            today = datetime.now()
            delta = today - last_contact
            return delta.days
        except ValueError:
            return -1

    # ── Convenience Builders ──────────────────────────────────────────────

    def harvest_all(self, keywords: Optional[List[str]] = None,
                    include_pages: bool = False) -> Dict[str, int]:
        """
        Harvest from all tables. Returns counts per source.
        Set include_pages=True for exhaustive page-level mining (slower).
        """
        counts = {}
        counts["docket_events"] = self.harvest_docket_events()
        counts["evidence_quotes"] = self.harvest_evidence_dates(keywords=keywords)
        counts["contradictions"] = self.harvest_contradictions()
        counts["impeachment"] = self.harvest_impeachment()
        counts["md_sections"] = self.harvest_from_md_sections(keywords=keywords)
        if include_pages:
            counts["pages"] = self.harvest_from_pages(keywords=keywords)
        counts["total_raw"] = len(self.events)
        removed = self.merge_and_deduplicate()
        counts["duplicates_removed"] = removed
        counts["total_final"] = len(self.events)
        return counts

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None


# ── Convenience Functions ─────────────────────────────────────────────────────

def build_watson_timeline(db_path: str = DB_PATH) -> TimelineBuilder:
    """Build complete Watson family alienation timeline."""
    tb = TimelineBuilder(db_path)
    counts = tb.harvest_all(
        keywords=["watson", "emily", "custody", "parenting", "PPO",
                   "exchange", "visitation", "lincoln", "mcneill",
                   "alienation", "ex parte"],
        include_pages=False,
    )
    print(f"Watson Timeline: {counts}")
    return tb


def build_full_timeline(db_path: str = DB_PATH) -> TimelineBuilder:
    """Build full unfiltered timeline from all sources."""
    tb = TimelineBuilder(db_path)
    counts = tb.harvest_all(include_pages=True)
    print(f"Full Timeline: {counts}")
    return tb


def build_lane_timeline(lane: str, db_path: str = DB_PATH) -> TimelineBuilder:
    """Build timeline for a specific case lane (A-F)."""
    tb = TimelineBuilder(db_path)
    lane_info = LANE_MAP.get(lane.upper(), {})
    keywords = lane_info.get("keywords", [])
    counts = tb.harvest_all(keywords=keywords, include_pages=False)
    tb.filter_by_lane(lane)
    print(f"Lane {lane.upper()} Timeline: {len(tb.events)} events (from {counts['total_raw']} raw)")
    return tb


# ── Self-Test ─────────────────────────────────────────────────────────────────

def self_test() -> bool:
    """Verify timeline builder works against live DB."""
    print("=" * 60)
    print("TimelineBuilder v1.0 — Self-Test")
    print("=" * 60)

    errors = []

    # 1. DB connection
    print("\n[1] Testing DB connection...")
    try:
        tb = TimelineBuilder()
        print("    OK — connected to litigation_context.db")
    except Exception as e:
        print(f"    FAIL — {e}")
        errors.append(f"DB connection: {e}")
        return False

    # 2. Docket events
    print("\n[2] Harvesting docket_events...")
    n = tb.harvest_docket_events()
    print(f"    Harvested: {n} events")
    if n == 0:
        errors.append("No docket_events found")

    # 3. Evidence dates
    print("\n[3] Harvesting evidence_quotes...")
    n = tb.harvest_evidence_dates()
    print(f"    Harvested: {n} events (total now: {len(tb.events)})")

    # 4. Contradictions
    print("\n[4] Harvesting contradictions...")
    n = tb.harvest_contradictions()
    print(f"    Harvested: {n} events (total now: {len(tb.events)})")

    # 5. Impeachment
    print("\n[5] Harvesting impeachment_items...")
    n = tb.harvest_impeachment()
    print(f"    Harvested: {n} events (total now: {len(tb.events)})")

    # 6. MD sections
    print("\n[6] Harvesting md_sections (keyword: 'custody')...")
    n = tb.harvest_from_md_sections(keywords=["custody"])
    print(f"    Harvested: {n} events (total now: {len(tb.events)})")

    # 7. Dedup
    print("\n[7] Merging and deduplicating...")
    removed = tb.merge_and_deduplicate()
    print(f"    Removed {removed} duplicates → {len(tb.events)} unique events")

    # 8. Date range filter test
    print("\n[8] Testing date range filter (2024-01-01 to 2024-12-31)...")
    count_before = len(tb.events)
    # Make a copy to test filter
    tb2 = TimelineBuilder.__new__(TimelineBuilder)
    tb2.events = list(tb.events)
    tb2.filter_by_date_range("2024-01-01", "2024-12-31")
    print(f"    2024 events: {len(tb2.events)} (of {count_before})")

    # 9. Court paragraph format
    print("\n[9] Testing court paragraph formatting...")
    paragraphs = tb.format_court_paragraphs()
    para_count = paragraphs.count("\n\n") + 1 if paragraphs.strip() else 0
    print(f"    Generated {para_count} paragraphs ({len(paragraphs)} chars)")

    # 10. Exhibit cross-ref
    print("\n[10] Testing exhibit cross-reference...")
    xref = tb.format_exhibit_crossref()
    print(f"    Exhibits referenced: {len(xref)}")

    # 11. Separation days
    print("\n[11] Calculating separation days...")
    days = tb.calculate_separation_days()
    print(f"    Days since separation: {days}")

    # 12. Summary
    print("\n[12] Timeline summary:")
    print("    " + tb.format_summary().replace("\n", "\n    "))

    # 13. Date extraction unit tests
    print("\n[13] Testing date extraction patterns...")
    test_cases = [
        ("Filed on 06/15/2024", "2024-06-15"),
        ("Date: 2024-07-01", "2024-07-01"),
        ("hearing on 1 0/29/25", "2025-10-29"),  # OCR artifact
        ("occurred on 1 1/26/25", "2025-11-26"),  # OCR artifact
        ("January 15, 2024", "2024-01-15"),
        ("hearing 11/26/2025", "2025-11-26"),
        ("dated 6/15/24", "2024-06-15"),
        ("15 June 2024 order", "2024-06-15"),
    ]
    passed = 0
    for text, expected in test_cases:
        dates = extract_dates(text)
        result = dates[0][0] if dates else "NONE"
        ok = result == expected
        status = "OK" if ok else "FAIL"
        print(f"    [{status}] '{text}' → {result} (expected {expected})")
        if ok:
            passed += 1
        else:
            errors.append(f"Date parse: '{text}' → {result} != {expected}")
    print(f"    Date tests: {passed}/{len(test_cases)} passed")

    # Final
    tb.close()
    print("\n" + "=" * 60)
    if errors:
        print(f"SELF-TEST COMPLETED WITH {len(errors)} WARNINGS:")
        for e in errors:
            print(f"  ⚠ {e}")
    else:
        print("SELF-TEST PASSED — ALL CHECKS OK")
    print("=" * 60)
    return len(errors) == 0


if __name__ == "__main__":
    success = self_test()

    # Print file info
    this_file = os.path.abspath(__file__)
    size = os.path.getsize(this_file)
    print(f"\nFile: {this_file}")
    print(f"Size: {size:,} bytes ({size/1024:.1f} KB)")
    lines = sum(1 for _ in open(this_file, encoding='utf-8'))
    print(f"Lines: {lines}")
