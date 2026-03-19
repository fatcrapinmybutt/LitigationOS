#!/usr/bin/env python3
"""
Authority Ingestion Engine — LitigationOS
==========================================
Reads real legal authority files (MCR, MRE, MCL, benchbooks, graph data)
scattered across the user's drives and builds a unified, searchable
SQLite authority database.

Usage:
    python authority_ingestion_engine.py ingest              # Ingest all sources
    python authority_ingestion_engine.py lookup MCR 2.003    # Look up a rule
    python authority_ingestion_engine.py search "disqualification"
    python authority_ingestion_engine.py violations          # List benchbook violations
    python authority_ingestion_engine.py report              # Ingestion stats
    python authority_ingestion_engine.py export [rule_ids..] # Export for document engine
"""

import csv
import hashlib
import json
import logging
import os
import re
import sqlite3
import sys
import textwrap
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DB_PATH = r"C:\Users\andre\LitigationOS\03_LEGAL_AUTHORITIES\authority_master.db"

BUNDLE = (
    r"C:\Users\andre\scans\discovery\fredprime-legal-system\LITIGATION_OS"
    r"\ALL_PC_EVIDENCE_EXTRACTED\Uncategorized\Benchbook_Rules_Lexvault_V7_bundle"
)

SOURCES = {
    "mcr_pages_jsonl": r"C:\Users\andre\scans\Documents\New folder\michigan-court-rules.pages.jsonl",
    "mcr_organized_json": r"C:\Users\andre\scans\Documents\MCR_organized.json",
    "benchbooks_json": (
        r"C:\Users\andre\scans\discovery\fredprime-legal-system"
        r"\LITIGATION_OS\judicial-benchbooks.json"
    ),
    "benchbook_violations_csv": r"C:\Users\andre\scans\discovery\Benchbook_Violation_Findings.csv.txt",
    "authorities_texts_jsonl": os.path.join(BUNDLE, "authorities_texts.jsonl"),
    "mcr_full_text": os.path.join(BUNDLE, "michigan-court-rules__295d085d57.txt"),
    "mre_full_text": os.path.join(BUNDLE, "michigan-rules-of-evidence__573f3f6b82.txt"),
    "mcr_chapter2": os.path.join(BUNDLE, "chapter 2MICHIGAN COURT RULES OF 1985 (1).txt"),
    "mcr_chapter3": os.path.join(BUNDLE, "chapter 3MICHIGAN COURT RULES OF 1985 (1).txt"),
    "authority_nodes_csv": os.path.join(BUNDLE, "authorities_nodes.csv"),
    "authority_edges_csv": os.path.join(BUNDLE, "authorities_edges.csv"),
    "nodes_mcr_csv": os.path.join(BUNDLE, "nodes_MCR.csv"),
    "citation_excerpts": r"C:\Users\andre\scans\Documents\New folder\mcr_citation_locked_excerpts.txt",
    "tons_of_rules_json": r"C:\Users\andre\scans\Documents\New folder\TONS OF COURT RULES AND LAWS.json",
    "authority_inventory_csv": r"C:\Users\andre\scans\Documents\Authority_sources_inventory__COURT_RULES_zip_.csv",
}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("authority_engine")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_file(filepath: str, mode: str = "r") -> str:
    """Read a text file, trying multiple encodings. Handles null-padded files."""
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            with open(filepath, mode, encoding=enc, errors="replace") as f:
                text = f.read()
            # Detect null-byte corrupted files
            if text and text[:100].count("\x00") > 50:
                log.warning("File appears null-padded/corrupted: %s", filepath)
                text = text.replace("\x00", "").strip()
                if not text:
                    return ""
            return text
        except (UnicodeDecodeError, UnicodeError):
            continue
    with open(filepath, mode, encoding="utf-8", errors="replace") as f:
        return f.read()


def _iter_jsonl(filepath: str) -> Generator[dict, None, None]:
    """Yield JSON objects from a JSONL file, skipping bad lines."""
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            with open(filepath, "r", encoding=enc, errors="replace") as f:
                for lineno, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        if lineno <= 3:
                            log.debug("Skipping bad JSONL line %d in %s", lineno, filepath)
            return
        except (UnicodeDecodeError, UnicodeError):
            continue


def _read_csv_rows(filepath: str) -> Generator[dict, None, None]:
    """Yield dicts from a CSV file (with header row)."""
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            with open(filepath, "r", encoding=enc, errors="replace", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    yield row
            return
        except (UnicodeDecodeError, UnicodeError):
            continue


def _file_size(path: str) -> int:
    try:
        return os.path.getsize(path)
    except OSError:
        return 0


def _normalize_rule_id(raw: str) -> str:
    """Normalize to canonical form like MCR_2.003, MRE_401, MCL_722.23."""
    raw = raw.strip()
    # Handle forms like "MCR 2.003", "Rule 2.003", "MRE 401"
    m = re.match(r"(?:MCR|Rule)\s+(\d+\.\d+\w*)", raw, re.IGNORECASE)
    if m:
        return f"MCR_{m.group(1)}"
    m = re.match(r"MRE\s+(\d+\w*)", raw, re.IGNORECASE)
    if m:
        return f"MRE_{m.group(1)}"
    m = re.match(r"MCL\s+([\d.]+\w*)", raw, re.IGNORECASE)
    if m:
        return f"MCL_{m.group(1)}"
    # Fallback: clean punctuation
    return re.sub(r"[^A-Za-z0-9_.]", "_", raw)


def _detect_rule_type(rule_id: str) -> str:
    """Infer rule type from the rule id."""
    uid = rule_id.upper()
    if uid.startswith("MCR"):
        return "MCR"
    if uid.startswith("MRE"):
        return "MRE"
    if uid.startswith("MCL"):
        return "MCL"
    if "CANON" in uid:
        return "CANON"
    if "BENCH" in uid:
        return "BENCHBOOK"
    return "OTHER"


def _extract_rule_number(rule_id: str) -> str:
    """Pull just the number portion from a rule id."""
    m = re.search(r"(\d[\d.]*\w*)", rule_id)
    return m.group(1) if m else rule_id


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS rules (
    id TEXT PRIMARY KEY,
    rule_type TEXT NOT NULL,
    rule_number TEXT NOT NULL,
    title TEXT,
    full_text TEXT,
    chapter TEXT,
    summary TEXT,
    source_file TEXT,
    source_page INTEGER,
    last_updated TEXT
);

CREATE TABLE IF NOT EXISTS authority_passages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id TEXT REFERENCES rules(id),
    passage_text TEXT NOT NULL,
    page_number INTEGER,
    section TEXT,
    source_file TEXT,
    source_sha256 TEXT
);

CREATE TABLE IF NOT EXISTS benchbook_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    benchbook_name TEXT,
    section TEXT,
    title TEXT,
    content TEXT,
    source_file TEXT
);

CREATE TABLE IF NOT EXISTS benchbook_violations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule TEXT,
    explanation TEXT,
    matching_text TEXT,
    judge TEXT,
    severity REAL,
    source_file TEXT
);

CREATE TABLE IF NOT EXISTS authority_nodes (
    id TEXT PRIMARY KEY,
    label TEXT,
    node_type TEXT,
    properties TEXT
);

CREATE TABLE IF NOT EXISTS authority_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT,
    target_id TEXT,
    edge_type TEXT,
    weight REAL
);

CREATE TABLE IF NOT EXISTS ingestion_stats (
    source_file TEXT PRIMARY KEY,
    file_size INTEGER,
    records_ingested INTEGER,
    ingestion_time TEXT,
    status TEXT
);
"""

FTS_SQL = """
DROP TABLE IF EXISTS rules_fts;
CREATE VIRTUAL TABLE rules_fts USING fts5(
    id, rule_number, title, full_text, summary,
    content='rules',
    content_rowid='rowid'
);
INSERT INTO rules_fts(id, rule_number, title, full_text, summary)
    SELECT id, rule_number, COALESCE(title,''), COALESCE(full_text,''), COALESCE(summary,'') FROM rules;

DROP TABLE IF EXISTS passages_fts;
CREATE VIRTUAL TABLE passages_fts USING fts5(
    rule_id, passage_text, section,
    content='authority_passages',
    content_rowid='id'
);
INSERT INTO passages_fts(rule_id, passage_text, section)
    SELECT COALESCE(rule_id,''), passage_text, COALESCE(section,'') FROM authority_passages;
"""


# ---------------------------------------------------------------------------
# AuthorityIngestionEngine
# ---------------------------------------------------------------------------

class AuthorityIngestionEngine:
    """Reads all authority source files and builds the unified database."""

    def __init__(self, db_path: str = DB_PATH, sources: Optional[Dict[str, str]] = None):
        self.db_path = db_path
        self.sources = sources or SOURCES
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute("PRAGMA cache_size=-64000")  # 64 MB cache
        self.conn.executescript(SCHEMA_SQL)
        self.conn.commit()
        self._stats: Dict[str, Dict[str, Any]] = {}

    # ---- internal helpers --------------------------------------------------

    def _record_stat(self, source_file: str, count: int, status: str = "ok"):
        self._stats[source_file] = {
            "file_size": _file_size(source_file),
            "records_ingested": count,
            "ingestion_time": datetime.now(timezone.utc).isoformat(),
            "status": status,
        }

    def _upsert_rule(self, rule_id: str, rule_type: str, rule_number: str,
                     title: str = None, full_text: str = None, chapter: str = None,
                     summary: str = None, source_file: str = None, source_page: int = None):
        """Insert or update a rule, merging text if the rule already exists."""
        existing = self.conn.execute(
            "SELECT full_text FROM rules WHERE id = ?", (rule_id,)
        ).fetchone()
        if existing:
            # Merge: keep the longer full_text
            old_text = existing[0] or ""
            new_text = full_text or ""
            merged = new_text if len(new_text) > len(old_text) else old_text
            self.conn.execute(
                """UPDATE rules SET
                    full_text = ?,
                    title = COALESCE(?, title),
                    chapter = COALESCE(?, chapter),
                    summary = COALESCE(?, summary),
                    source_file = COALESCE(?, source_file),
                    source_page = COALESCE(?, source_page),
                    last_updated = ?
                   WHERE id = ?""",
                (merged, title, chapter, summary, source_file, source_page,
                 datetime.now(timezone.utc).isoformat(), rule_id),
            )
        else:
            self.conn.execute(
                """INSERT INTO rules (id, rule_type, rule_number, title, full_text, chapter,
                                      summary, source_file, source_page, last_updated)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (rule_id, rule_type, rule_number, title, full_text, chapter,
                 summary, source_file, source_page,
                 datetime.now(timezone.utc).isoformat()),
            )

    # ---- MCR pages JSONL (source #1) --------------------------------------

    def ingest_mcr_pages_jsonl(self, filepath: str = None):
        """Ingest michigan-court-rules.pages.jsonl — page-level passages."""
        filepath = filepath or self.sources.get("mcr_pages_jsonl")
        if not filepath or not os.path.isfile(filepath):
            log.warning("MCR pages JSONL not found: %s", filepath)
            return
        log.info("Ingesting MCR pages JSONL: %s", filepath)
        count = 0
        sha256 = None
        batch = []
        for rec in _iter_jsonl(filepath):
            text = rec.get("text", "")
            page = rec.get("page")
            sha256 = sha256 or rec.get("doc_sha256", "")
            if not text.strip():
                continue
            # Extract individual rules mentioned on this page
            rule_ids = re.findall(r"Rule\s+(\d+\.\d+\w*)", text)
            linked_rule = f"MCR_{rule_ids[0]}" if rule_ids else None
            batch.append((linked_rule, text, page, None, filepath, sha256))
            count += 1
            if len(batch) >= 500:
                self.conn.executemany(
                    "INSERT INTO authority_passages (rule_id, passage_text, page_number, section, source_file, source_sha256) VALUES (?,?,?,?,?,?)",
                    batch,
                )
                batch.clear()
        if batch:
            self.conn.executemany(
                "INSERT INTO authority_passages (rule_id, passage_text, page_number, section, source_file, source_sha256) VALUES (?,?,?,?,?,?)",
                batch,
            )
        self.conn.commit()
        self._record_stat(filepath, count)
        log.info("  -> %d passages from MCR pages JSONL", count)

    # ---- MCR organized JSON (source #2) -----------------------------------

    def ingest_mcr_organized_json(self, filepath: str = None):
        """Ingest MCR_organized.json — structured rule list with chapters."""
        filepath = filepath or self.sources.get("mcr_organized_json")
        if not filepath or not os.path.isfile(filepath):
            log.warning("MCR organized JSON not found: %s", filepath)
            return
        log.info("Ingesting MCR organized JSON: %s", filepath)
        raw = _read_file(filepath)
        data = json.loads(raw)
        if not isinstance(data, list):
            data = [data]
        count = 0
        for item in data:
            label = item.get("label", "")
            chapter = item.get("chapter", "")
            item_id = item.get("id", "")
            # Normalize: "MCR 2.105" -> "MCR_2.105"
            rule_id = _normalize_rule_id(label)
            rule_number = _extract_rule_number(label)
            self._upsert_rule(
                rule_id=rule_id,
                rule_type="MCR",
                rule_number=rule_number,
                title=label,
                chapter=chapter,
                source_file=filepath,
            )
            # Also store original id as a node for graph lookup
            if item_id and item_id != rule_id:
                self.conn.execute(
                    "INSERT OR IGNORE INTO authority_nodes (id, label, node_type, properties) VALUES (?,?,?,?)",
                    (item_id, label, "rule", json.dumps({"chapter": chapter, "forms_controlled": item.get("forms_controlled", [])})),
                )
            count += 1
        self.conn.commit()
        self._record_stat(filepath, count)
        log.info("  -> %d rules from MCR organized JSON", count)

    # ---- Benchbook JSON (source #3) ---------------------------------------

    def ingest_benchbook_json(self, filepath: str = None):
        """Ingest judicial-benchbooks.json — benchbook guidance database."""
        filepath = filepath or self.sources.get("benchbooks_json")
        if not filepath or not os.path.isfile(filepath):
            log.warning("Benchbooks JSON not found: %s", filepath)
            return
        log.info("Ingesting benchbooks JSON: %s", filepath)
        raw = _read_file(filepath)
        data = json.loads(raw)
        count = 0
        benchbooks = data.get("benchbooks", []) if isinstance(data, dict) else data
        for book in benchbooks:
            book_title = book.get("title", "Unknown Benchbook")
            chapters = book.get("chapters", [])
            for chap in chapters:
                chap_title = chap.get("title", "")
                sections = chap.get("sections", [])
                for sec in sections:
                    sec_id = sec.get("section", "")
                    sec_title = sec.get("title", "")
                    # Build content from key_points, practice_tips, factor_guidance
                    parts = []
                    for kp in sec.get("key_points", []):
                        parts.append(f"• {kp}")
                    for tip in sec.get("practice_tips", []):
                        parts.append(f"[TIP] {tip}")
                    for fg in sec.get("factor_guidance", []):
                        factor = fg.get("factor", "")
                        guidance = fg.get("guidance", "")
                        parts.append(f"[FACTOR] {factor}: {guidance}")
                    content = "\n".join(parts)
                    # Related rules -> create links
                    related_mcr = sec.get("related_mcr", [])
                    related_mcl = sec.get("related_mcl", [])
                    if related_mcr or related_mcl:
                        content += "\n\nRelated: " + ", ".join(related_mcr + related_mcl)
                    self.conn.execute(
                        "INSERT INTO benchbook_entries (benchbook_name, section, title, content, source_file) VALUES (?,?,?,?,?)",
                        (book_title, sec_id, sec_title, content, filepath),
                    )
                    count += 1
        self.conn.commit()
        self._record_stat(filepath, count)
        log.info("  -> %d benchbook entries", count)

    # ---- Benchbook violations CSV (source #4) -----------------------------

    def ingest_benchbook_violations_csv(self, filepath: str = None):
        """Ingest Benchbook_Violation_Findings.csv.txt."""
        filepath = filepath or self.sources.get("benchbook_violations_csv")
        if not filepath or not os.path.isfile(filepath):
            log.warning("Benchbook violations CSV not found: %s", filepath)
            return
        log.info("Ingesting benchbook violations CSV: %s", filepath)
        count = 0
        batch = []
        for row in _read_csv_rows(filepath):
            rule = row.get("rule", "").strip()
            explanation = row.get("explanation", "").strip()
            matching_text = row.get("matching_text", "").strip()
            judge = row.get("judge", "").strip() or None
            severity = None
            sev_raw = row.get("severity", "")
            if sev_raw:
                try:
                    severity = float(sev_raw)
                except ValueError:
                    pass
            batch.append((rule, explanation, matching_text, judge, severity, filepath))
            count += 1
            if len(batch) >= 1000:
                self.conn.executemany(
                    "INSERT INTO benchbook_violations (rule, explanation, matching_text, judge, severity, source_file) VALUES (?,?,?,?,?,?)",
                    batch,
                )
                batch.clear()
        if batch:
            self.conn.executemany(
                "INSERT INTO benchbook_violations (rule, explanation, matching_text, judge, severity, source_file) VALUES (?,?,?,?,?,?)",
                batch,
            )
        self.conn.commit()
        self._record_stat(filepath, count)
        log.info("  -> %d benchbook violations", count)

    # ---- Authorities texts JSONL (source #5 — 32 MB) ----------------------

    def ingest_authorities_texts_jsonl(self, filepath: str = None):
        """Ingest authorities_texts.jsonl — massive authority text store."""
        filepath = filepath or self.sources.get("authorities_texts_jsonl")
        if not filepath or not os.path.isfile(filepath):
            log.warning("Authorities texts JSONL not found: %s", filepath)
            return
        log.info("Ingesting authorities texts JSONL (large): %s", filepath)
        count = 0
        batch_passages = []
        batch_rules = []
        for rec in _iter_jsonl(filepath):
            rec_id = rec.get("id", "")
            title = rec.get("title", "")
            text = rec.get("text", "")
            source_url = rec.get("source_url", "")
            if not text.strip():
                continue
            # Try to detect rule references from the text or title
            rule_refs = re.findall(r"(?:MCR|Rule)\s+(\d+\.\d+\w*)", title + " " + text[:500])
            mre_refs = re.findall(r"MRE?\s+(\d+\w*)", title + " " + text[:500])
            mcl_refs = re.findall(r"MCL\s+([\d.]+\w*)", title + " " + text[:500])
            # If a single clear rule, upsert into rules table
            if rule_refs:
                primary_rule = f"MCR_{rule_refs[0]}"
                batch_rules.append((
                    primary_rule, "MCR", rule_refs[0], title, text, None, None, filepath, None,
                    datetime.now(timezone.utc).isoformat(),
                ))
            elif mre_refs:
                primary_rule = f"MRE_{mre_refs[0]}"
                batch_rules.append((
                    primary_rule, "MRE", mre_refs[0], title, text, None, None, filepath, None,
                    datetime.now(timezone.utc).isoformat(),
                ))
            elif mcl_refs:
                primary_rule = f"MCL_{mcl_refs[0]}"
                batch_rules.append((
                    primary_rule, "MCL", mcl_refs[0], title, text, None, None, filepath, None,
                    datetime.now(timezone.utc).isoformat(),
                ))
            else:
                primary_rule = rec_id if rec_id else None
            # Always store as a passage
            batch_passages.append((primary_rule, text[:50000], None, None, filepath, None))
            count += 1
            if len(batch_passages) >= 500:
                self.conn.executemany(
                    "INSERT INTO authority_passages (rule_id, passage_text, page_number, section, source_file, source_sha256) VALUES (?,?,?,?,?,?)",
                    batch_passages,
                )
                batch_passages.clear()
            if len(batch_rules) >= 500:
                for r in batch_rules:
                    try:
                        self.conn.execute(
                            """INSERT INTO rules (id, rule_type, rule_number, title, full_text, chapter, summary, source_file, source_page, last_updated)
                               VALUES (?,?,?,?,?,?,?,?,?,?)
                               ON CONFLICT(id) DO UPDATE SET
                                 full_text = CASE WHEN LENGTH(excluded.full_text) > LENGTH(COALESCE(rules.full_text,''))
                                             THEN excluded.full_text ELSE rules.full_text END,
                                 title = COALESCE(excluded.title, rules.title)""",
                            r,
                        )
                    except sqlite3.IntegrityError:
                        pass
                batch_rules.clear()
            if count % 5000 == 0:
                log.info("    ... %d authority text records processed", count)
        # Flush remaining
        if batch_passages:
            self.conn.executemany(
                "INSERT INTO authority_passages (rule_id, passage_text, page_number, section, source_file, source_sha256) VALUES (?,?,?,?,?,?)",
                batch_passages,
            )
        for r in batch_rules:
            try:
                self.conn.execute(
                    """INSERT INTO rules (id, rule_type, rule_number, title, full_text, chapter, summary, source_file, source_page, last_updated)
                       VALUES (?,?,?,?,?,?,?,?,?,?)
                       ON CONFLICT(id) DO UPDATE SET
                         full_text = CASE WHEN LENGTH(excluded.full_text) > LENGTH(COALESCE(rules.full_text,''))
                                     THEN excluded.full_text ELSE rules.full_text END,
                         title = COALESCE(excluded.title, rules.title)""",
                    r,
                )
            except sqlite3.IntegrityError:
                pass
        self.conn.commit()
        self._record_stat(filepath, count)
        log.info("  -> %d passages from authorities texts JSONL", count)

    # ---- MCR / MRE full text parsing (sources #6–9) -----------------------

    def _parse_rules_from_text(self, text: str, rule_type: str = "MCR",
                               chapter_hint: str = None) -> List[Dict]:
        """Parse rule bodies from a full-text court rules document.

        Detects rule headers like 'RULE X.XXX TITLE' and captures everything
        between consecutive headers as the rule body text.
        """
        rules = []
        if rule_type == "MRE":
            # MRE pattern: "Rule NNN  Title" (spaces, no dot in number)
            header_re = re.compile(
                r"^Rule\s+(\d+[A-Za-z]?)\s{2,}(.+?)$", re.MULTILINE
            )
        else:
            # MCR pattern: "RULE X.XXX TITLE" (uppercase or title case)
            header_re = re.compile(
                r"^(?:RULE|Rule)\s+(\d+\.\d+\w*)\s+(.+?)$", re.MULTILINE
            )
        matches = list(header_re.finditer(text))
        for i, m in enumerate(matches):
            rule_num = m.group(1).strip()
            title = m.group(2).strip()
            # Skip TOC entries (title ends with page numbers / dots)
            if re.search(r"\.\.\.\.*\s*\d+\s*$", title):
                continue
            if re.search(r"\s{3,}\d+\s*$", title):
                continue
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[start:end].strip()
            # Skip bodies that are too short (probably a TOC remnant)
            if len(body) < 30:
                continue
            # Remove page header/footer artifacts
            body = re.sub(
                r"(?:Chapter \d+\.\s+\w[\w ]+\n)?Page\s+\d+\n\s*Updated\s+\w+\s+\d+,\s+\d{4}\n?",
                "\n", body,
            )
            rule_id = f"{rule_type}_{rule_num}"
            rules.append({
                "id": rule_id,
                "rule_type": rule_type,
                "rule_number": rule_num,
                "title": title,
                "full_text": body,
                "chapter": chapter_hint,
            })
        return rules

    def ingest_mcr_full_text(self, filepath: str = None):
        """Ingest full MCR text file — parse individual rules."""
        filepath = filepath or self.sources.get("mcr_full_text")
        if not filepath or not os.path.isfile(filepath):
            log.warning("MCR full text not found: %s", filepath)
            return
        log.info("Ingesting MCR full text: %s", filepath)
        text = _read_file(filepath)
        rules = self._parse_rules_from_text(text, "MCR")
        count = 0
        for r in rules:
            self._upsert_rule(
                rule_id=r["id"],
                rule_type=r["rule_type"],
                rule_number=r["rule_number"],
                title=r["title"],
                full_text=r["full_text"],
                chapter=r.get("chapter"),
                source_file=filepath,
            )
            count += 1
        self.conn.commit()
        self._record_stat(filepath, count)
        log.info("  -> %d rules parsed from MCR full text", count)

    def ingest_mre_full_text(self, filepath: str = None):
        """Ingest full MRE text file — parse individual evidence rules."""
        filepath = filepath or self.sources.get("mre_full_text")
        if not filepath or not os.path.isfile(filepath):
            log.warning("MRE full text not found: %s", filepath)
            return
        log.info("Ingesting MRE full text: %s", filepath)
        text = _read_file(filepath)
        rules = self._parse_rules_from_text(text, "MRE")
        count = 0
        for r in rules:
            self._upsert_rule(
                rule_id=r["id"],
                rule_type=r["rule_type"],
                rule_number=r["rule_number"],
                title=r["title"],
                full_text=r["full_text"],
                source_file=filepath,
            )
            count += 1
        self.conn.commit()
        self._record_stat(filepath, count)
        log.info("  -> %d rules parsed from MRE full text", count)

    def ingest_mcr_chapter_text(self, filepath: str, chapter_hint: str = None):
        """Ingest a single MCR chapter text file."""
        if not filepath or not os.path.isfile(filepath):
            log.warning("MCR chapter text not found: %s", filepath)
            return
        log.info("Ingesting MCR chapter text: %s", filepath)
        text = _read_file(filepath)
        rules = self._parse_rules_from_text(text, "MCR", chapter_hint)
        count = 0
        for r in rules:
            self._upsert_rule(
                rule_id=r["id"],
                rule_type=r["rule_type"],
                rule_number=r["rule_number"],
                title=r["title"],
                full_text=r["full_text"],
                chapter=r.get("chapter"),
                source_file=filepath,
            )
            count += 1
        self.conn.commit()
        self._record_stat(filepath, count)
        log.info("  -> %d rules parsed from MCR chapter text", count)

    # ---- Authority graph (sources #10–12) ---------------------------------

    def ingest_authority_graph(self, nodes_csv: str = None, edges_csv: str = None,
                               nodes_mcr_csv: str = None):
        """Ingest authority graph CSVs (nodes + edges)."""
        nodes_csv = nodes_csv or self.sources.get("authority_nodes_csv")
        edges_csv = edges_csv or self.sources.get("authority_edges_csv")
        nodes_mcr_csv = nodes_mcr_csv or self.sources.get("nodes_mcr_csv")

        # --- Nodes ---
        node_count = 0
        for csv_path in (nodes_csv, nodes_mcr_csv):
            if not csv_path or not os.path.isfile(csv_path):
                log.warning("Authority nodes CSV not found: %s", csv_path)
                continue
            log.info("Ingesting authority nodes: %s", csv_path)
            batch = []
            for row in _read_csv_rows(csv_path):
                node_id = row.get("id", "").strip()
                label = row.get("label", "").strip()
                node_type = row.get("type", "").strip()
                if not node_id:
                    continue
                # Build properties from remaining columns
                props = {k: v for k, v in row.items()
                         if k not in ("id", "label", "type") and v}
                batch.append((node_id, label, node_type, json.dumps(props) if props else None))
                node_count += 1
                if len(batch) >= 2000:
                    self.conn.executemany(
                        "INSERT OR IGNORE INTO authority_nodes (id, label, node_type, properties) VALUES (?,?,?,?)",
                        batch,
                    )
                    batch.clear()
            if batch:
                self.conn.executemany(
                    "INSERT OR IGNORE INTO authority_nodes (id, label, node_type, properties) VALUES (?,?,?,?)",
                    batch,
                )
            self.conn.commit()
            self._record_stat(csv_path, node_count)
            log.info("  -> %d nodes ingested from %s", node_count, os.path.basename(csv_path))

        # --- Edges ---
        if not edges_csv or not os.path.isfile(edges_csv):
            log.warning("Authority edges CSV not found: %s", edges_csv)
            return
        log.info("Ingesting authority edges (large): %s", edges_csv)
        edge_count = 0
        batch = []
        for row in _read_csv_rows(edges_csv):
            src = (row.get("src") or "").strip()
            dst = (row.get("dst") or "").strip()
            relation = (row.get("relation") or "").strip()
            weight_raw = row.get("weight") or "1"
            try:
                weight = float(weight_raw) if weight_raw else 1.0
            except ValueError:
                weight = 1.0
            if not src or not dst:
                continue
            batch.append((src, dst, relation, weight))
            edge_count += 1
            if len(batch) >= 5000:
                self.conn.executemany(
                    "INSERT INTO authority_edges (source_id, target_id, edge_type, weight) VALUES (?,?,?,?)",
                    batch,
                )
                batch.clear()
                if edge_count % 50000 == 0:
                    log.info("    ... %d edges processed", edge_count)
        if batch:
            self.conn.executemany(
                "INSERT INTO authority_edges (source_id, target_id, edge_type, weight) VALUES (?,?,?,?)",
                batch,
            )
        self.conn.commit()
        self._record_stat(edges_csv, edge_count)
        log.info("  -> %d edges ingested", edge_count)

    # ---- Citation excerpts (source #13) -----------------------------------

    def ingest_citation_excerpts(self, filepath: str = None):
        """Ingest mcr_citation_locked_excerpts.txt — passage blocks."""
        filepath = filepath or self.sources.get("citation_excerpts")
        if not filepath or not os.path.isfile(filepath):
            log.warning("Citation excerpts not found: %s", filepath)
            return
        log.info("Ingesting citation excerpts: %s", filepath)
        text = _read_file(filepath)
        # Split on separator lines (dashes)
        blocks = re.split(r"-{20,}", text)
        count = 0
        for block in blocks:
            block = block.strip()
            if not block or len(block) < 20:
                continue
            # Try to extract rule references
            rule_refs = re.findall(r"Rule\s+(\d+\.\d+\w*)", block)
            linked_rule = f"MCR_{rule_refs[0]}" if rule_refs else None
            # Extract node/title info from header line
            node_m = re.match(r"Node:\s*(\S+)\s*\|\s*Title:\s*(.+?)(?:\n|$)", block)
            section = None
            if node_m:
                section = node_m.group(2).strip()
            self.conn.execute(
                "INSERT INTO authority_passages (rule_id, passage_text, page_number, section, source_file, source_sha256) VALUES (?,?,?,?,?,?)",
                (linked_rule, block[:50000], None, section, filepath, None),
            )
            count += 1
        self.conn.commit()
        self._record_stat(filepath, count)
        log.info("  -> %d citation excerpt passages", count)

    # ---- TONS OF COURT RULES AND LAWS (source #14) ------------------------

    def ingest_tons_of_rules_json(self, filepath: str = None):
        """Ingest TONS OF COURT RULES AND LAWS.json — may be JSONL or fragmented JSON."""
        filepath = filepath or self.sources.get("tons_of_rules_json")
        if not filepath or not os.path.isfile(filepath):
            log.warning("TONS OF COURT RULES JSON not found: %s", filepath)
            return
        log.info("Ingesting TONS OF COURT RULES JSON: %s", filepath)
        count = 0
        # Try as standard JSON first
        try:
            raw = _read_file(filepath)
            data = json.loads(raw)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        self._ingest_rule_dict(item, filepath)
                        count += 1
                self.conn.commit()
                self._record_stat(filepath, count)
                log.info("  -> %d records from TONS OF COURT RULES (JSON array)", count)
                return
            elif isinstance(data, dict):
                self._ingest_rule_dict(data, filepath)
                count = 1
                self.conn.commit()
                self._record_stat(filepath, count)
                return
        except (json.JSONDecodeError, ValueError):
            pass
        # Try as JSONL
        for rec in _iter_jsonl(filepath):
            if isinstance(rec, dict):
                self._ingest_rule_dict(rec, filepath)
                count += 1
        if count > 0:
            self.conn.commit()
            self._record_stat(filepath, count)
            log.info("  -> %d records from TONS OF COURT RULES (JSONL)", count)
            return
        # Fallback: try line-by-line parsing of fragmented JSON
        raw = _read_file(filepath)
        # Try to find JSON objects in the text via braces
        objects_found = 0
        for m in re.finditer(r'\{[^{}]{10,}\}', raw):
            try:
                obj = json.loads(m.group())
                self._ingest_rule_dict(obj, filepath)
                objects_found += 1
            except json.JSONDecodeError:
                continue
        if objects_found > 0:
            self.conn.commit()
            count = objects_found
            self._record_stat(filepath, count)
            log.info("  -> %d records from TONS OF COURT RULES (extracted objects)", count)
            return
        # Last resort: store the whole thing as a single passage
        self.conn.execute(
            "INSERT INTO authority_passages (rule_id, passage_text, page_number, section, source_file, source_sha256) VALUES (?,?,?,?,?,?)",
            (None, raw[:100000], None, "TONS_OF_RULES_RAW", filepath, None),
        )
        self.conn.commit()
        self._record_stat(filepath, 1, status="partial_raw_ingest")
        log.info("  -> stored as raw passage (non-standard format)")

    def _ingest_rule_dict(self, item: dict, filepath: str):
        """Ingest a single rule-like dict from any JSON source."""
        label = item.get("label", item.get("title", item.get("id", "")))
        text = item.get("text", item.get("content", item.get("full_text", "")))
        chapter = item.get("chapter", "")
        item_id = item.get("id", "")
        rule_id = _normalize_rule_id(label) if label else (_normalize_rule_id(item_id) if item_id else None)
        if not rule_id:
            return
        rule_type = _detect_rule_type(rule_id)
        rule_number = _extract_rule_number(rule_id)
        self._upsert_rule(
            rule_id=rule_id,
            rule_type=rule_type,
            rule_number=rule_number,
            title=label,
            full_text=text if text else None,
            chapter=chapter if chapter else None,
            source_file=filepath,
        )

    # ---- Authority inventory CSV (source #15) -----------------------------

    def ingest_authority_inventory(self, filepath: str = None):
        """Ingest Authority_sources_inventory CSV — metadata only."""
        filepath = filepath or self.sources.get("authority_inventory_csv")
        if not filepath or not os.path.isfile(filepath):
            log.warning("Authority inventory CSV not found: %s", filepath)
            return
        log.info("Ingesting authority inventory: %s", filepath)
        count = 0
        for row in _read_csv_rows(filepath):
            props = json.dumps({k: v for k, v in row.items() if v})
            row_id = row.get("id", row.get("filename", row.get("source", f"inv_{count}")))
            label = row.get("title", row.get("label", row.get("filename", "")))
            self.conn.execute(
                "INSERT OR IGNORE INTO authority_nodes (id, label, node_type, properties) VALUES (?,?,?,?)",
                (f"INV_{count}_{row_id}", label, "inventory", props),
            )
            count += 1
        self.conn.commit()
        self._record_stat(filepath, count)
        log.info("  -> %d inventory entries", count)

    # ---- Full-text search index -------------------------------------------

    def build_fts_index(self):
        """Build / rebuild the FTS5 full-text search indexes."""
        log.info("Building FTS indexes ...")
        self.conn.executescript(FTS_SQL)
        self.conn.commit()
        rules_count = self.conn.execute("SELECT COUNT(*) FROM rules_fts").fetchone()[0]
        passages_count = self.conn.execute("SELECT COUNT(*) FROM passages_fts").fetchone()[0]
        log.info("  -> rules_fts: %d rows, passages_fts: %d rows", rules_count, passages_count)

    # ---- Persist ingestion stats ------------------------------------------

    def _flush_stats(self):
        for src, info in self._stats.items():
            self.conn.execute(
                """INSERT OR REPLACE INTO ingestion_stats
                   (source_file, file_size, records_ingested, ingestion_time, status)
                   VALUES (?,?,?,?,?)""",
                (src, info["file_size"], info["records_ingested"],
                 info["ingestion_time"], info["status"]),
            )
        self.conn.commit()

    # ---- Master ingest ----------------------------------------------------

    def ingest_all(self):
        """Run all ingestion methods in priority order."""
        t0 = time.time()
        log.info("=" * 60)
        log.info("AUTHORITY INGESTION ENGINE — Starting full ingest")
        log.info("=" * 60)

        # STRUCTURED (priority 1)
        self.ingest_mcr_pages_jsonl()
        self.ingest_mcr_organized_json()
        self.ingest_benchbook_json()
        self.ingest_benchbook_violations_csv()

        # HEAVY TEXT (priority 2)
        self.ingest_authorities_texts_jsonl()
        self.ingest_mcr_full_text()
        self.ingest_mre_full_text()
        ch2 = self.sources.get("mcr_chapter2")
        ch3 = self.sources.get("mcr_chapter3")
        self.ingest_mcr_chapter_text(ch2, "Chapter 2 — Civil Procedure")
        self.ingest_mcr_chapter_text(ch3, "Chapter 3 — Special Proceedings")

        # GRAPH DATA (priority 3)
        self.ingest_authority_graph()

        # SUPPLEMENTARY (priority 4)
        self.ingest_citation_excerpts()
        self.ingest_tons_of_rules_json()
        self.ingest_authority_inventory()

        # Build FTS
        self.build_fts_index()

        # Create indexes for fast lookup
        self._create_indexes()

        # Persist stats
        self._flush_stats()

        elapsed = time.time() - t0
        log.info("=" * 60)
        log.info("INGESTION COMPLETE in %.1f seconds", elapsed)
        self.report()

    def _create_indexes(self):
        """Create performance indexes."""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_rules_type ON rules(rule_type)",
            "CREATE INDEX IF NOT EXISTS idx_rules_number ON rules(rule_number)",
            "CREATE INDEX IF NOT EXISTS idx_rules_chapter ON rules(chapter)",
            "CREATE INDEX IF NOT EXISTS idx_passages_rule ON authority_passages(rule_id)",
            "CREATE INDEX IF NOT EXISTS idx_passages_source ON authority_passages(source_file)",
            "CREATE INDEX IF NOT EXISTS idx_benchbook_name ON benchbook_entries(benchbook_name)",
            "CREATE INDEX IF NOT EXISTS idx_violations_rule ON benchbook_violations(rule)",
            "CREATE INDEX IF NOT EXISTS idx_violations_judge ON benchbook_violations(judge)",
            "CREATE INDEX IF NOT EXISTS idx_edges_source ON authority_edges(source_id)",
            "CREATE INDEX IF NOT EXISTS idx_edges_target ON authority_edges(target_id)",
            "CREATE INDEX IF NOT EXISTS idx_edges_type ON authority_edges(edge_type)",
        ]
        for sql in indexes:
            self.conn.execute(sql)
        self.conn.commit()

    # ---- Report -----------------------------------------------------------

    def report(self):
        """Print ingestion stats summary."""
        print("\n" + "=" * 70)
        print("AUTHORITY DATABASE REPORT")
        print("=" * 70)
        tables = [
            ("rules", "Rules"),
            ("authority_passages", "Authority Passages"),
            ("benchbook_entries", "Benchbook Entries"),
            ("benchbook_violations", "Benchbook Violations"),
            ("authority_nodes", "Authority Nodes"),
            ("authority_edges", "Authority Edges"),
        ]
        for table, label in tables:
            try:
                count = self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                print(f"  {label:.<40} {count:>8,}")
            except sqlite3.OperationalError:
                print(f"  {label:.<40}    N/A")
        # FTS
        for fts in ("rules_fts", "passages_fts"):
            try:
                count = self.conn.execute(f"SELECT COUNT(*) FROM {fts}").fetchone()[0]
                print(f"  FTS: {fts:.<38} {count:>8,}")
            except sqlite3.OperationalError:
                print(f"  FTS: {fts:.<38}    N/A")
        # Type breakdown
        print("\n  Rule types:")
        for row in self.conn.execute(
            "SELECT rule_type, COUNT(*) FROM rules GROUP BY rule_type ORDER BY COUNT(*) DESC"
        ):
            print(f"    {row[0]:.<30} {row[1]:>6,}")
        # Ingestion stats
        print("\n  Ingestion sources:")
        for row in self.conn.execute(
            "SELECT source_file, records_ingested, status FROM ingestion_stats ORDER BY records_ingested DESC"
        ):
            fname = os.path.basename(row[0])
            print(f"    {fname:.<50} {row[1]:>8,}  [{row[2]}]")
        # DB size
        db_size = _file_size(self.db_path)
        print(f"\n  Database size: {db_size / (1024*1024):.1f} MB")
        print(f"  Database path: {self.db_path}")
        print("=" * 70)

    def close(self):
        self.conn.close()


# ---------------------------------------------------------------------------
# AuthorityLookup
# ---------------------------------------------------------------------------

class AuthorityLookup:
    """Fast lookup of rules, passages, and relationships."""

    def __init__(self, db_path: str = DB_PATH):
        if not os.path.isfile(db_path):
            raise FileNotFoundError(f"Authority database not found: {db_path}")
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def get_rule(self, rule_id: str) -> Optional[Dict]:
        """Get rule by ID (e.g. MCR_2.003)."""
        rule_id = _normalize_rule_id(rule_id)
        row = self.conn.execute("SELECT * FROM rules WHERE id = ?", (rule_id,)).fetchone()
        if row:
            return dict(row)
        # Fuzzy: try matching by rule_number
        num = _extract_rule_number(rule_id)
        row = self.conn.execute("SELECT * FROM rules WHERE rule_number = ?", (num,)).fetchone()
        return dict(row) if row else None

    def search_rules(self, query: str, limit: int = 20) -> List[Dict]:
        """Full-text search across all rules."""
        try:
            rows = self.conn.execute(
                """SELECT r.id, r.rule_type, r.rule_number, r.title, r.chapter,
                          SUBSTR(r.full_text, 1, 300) AS snippet, r.source_file
                   FROM rules_fts fts
                   JOIN rules r ON r.id = fts.id
                   WHERE rules_fts MATCH ?
                   ORDER BY rank
                   LIMIT ?""",
                (query, limit),
            ).fetchall()
            return [dict(r) for r in rows]
        except sqlite3.OperationalError:
            # Fallback to LIKE
            rows = self.conn.execute(
                """SELECT id, rule_type, rule_number, title, chapter,
                          SUBSTR(full_text, 1, 300) AS snippet, source_file
                   FROM rules
                   WHERE full_text LIKE ? OR title LIKE ?
                   LIMIT ?""",
                (f"%{query}%", f"%{query}%", limit),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_rule_text(self, rule_number: str) -> Optional[str]:
        """Get full text of a specific rule by number (e.g. '2.003')."""
        row = self.conn.execute(
            "SELECT full_text FROM rules WHERE rule_number = ?", (rule_number,)
        ).fetchone()
        if row:
            return row["full_text"]
        # Try with MCR prefix
        rule_id = f"MCR_{rule_number}"
        row = self.conn.execute(
            "SELECT full_text FROM rules WHERE id = ?", (rule_id,)
        ).fetchone()
        return row["full_text"] if row else None

    def find_related_rules(self, rule_id: str, depth: int = 1) -> List[Dict]:
        """Graph traversal for related rules via authority_edges."""
        rule_id = _normalize_rule_id(rule_id)
        # Find matching node IDs (the graph may use different ID schemes)
        node_ids = set()
        node_ids.add(rule_id)
        # Also search nodes by label
        label_search = rule_id.replace("_", " ")
        for row in self.conn.execute(
            "SELECT id FROM authority_nodes WHERE label LIKE ?", (f"%{label_search}%",)
        ):
            node_ids.add(row["id"])
        # Also try pattern like MCR-X.XXX@date
        num = _extract_rule_number(rule_id)
        for row in self.conn.execute(
            "SELECT id FROM authority_nodes WHERE id LIKE ?", (f"%{num}%",)
        ):
            node_ids.add(row["id"])
        results = []
        visited = set()
        frontier = list(node_ids)
        for _ in range(depth):
            next_frontier = []
            for nid in frontier:
                if nid in visited:
                    continue
                visited.add(nid)
                for row in self.conn.execute(
                    """SELECT target_id, edge_type, weight FROM authority_edges
                       WHERE source_id = ?
                       UNION
                       SELECT source_id, edge_type, weight FROM authority_edges
                       WHERE target_id = ?""",
                    (nid, nid),
                ):
                    related_id = row["target_id"] if row["target_id"] != nid else row["target_id"]
                    results.append({
                        "from": nid,
                        "related_id": row[0],
                        "edge_type": row["edge_type"],
                        "weight": row["weight"],
                    })
                    if row[0] not in visited:
                        next_frontier.append(row[0])
            frontier = next_frontier
        return results

    def get_benchbook_guidance(self, topic: str, limit: int = 10) -> List[Dict]:
        """Search benchbook entries by topic."""
        rows = self.conn.execute(
            """SELECT * FROM benchbook_entries
               WHERE content LIKE ? OR title LIKE ? OR section LIKE ?
               LIMIT ?""",
            (f"%{topic}%", f"%{topic}%", f"%{topic}%", limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_violations(self, judge: str = None, limit: int = 50) -> List[Dict]:
        """Get benchbook violations, optionally filtered by judge."""
        if judge:
            rows = self.conn.execute(
                "SELECT * FROM benchbook_violations WHERE judge LIKE ? ORDER BY severity DESC LIMIT ?",
                (f"%{judge}%", limit),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM benchbook_violations ORDER BY severity DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def cite_check(self, citation_text: str) -> Dict:
        """Verify a citation is valid — check if the rule exists in the database."""
        # Extract rule references from the citation
        mcr_refs = re.findall(r"MCR\s+(\d+\.\d+\w*)", citation_text)
        mre_refs = re.findall(r"MRE\s+(\d+\w*)", citation_text)
        mcl_refs = re.findall(r"MCL\s+([\d.]+\w*)", citation_text)
        results = {"valid": [], "not_found": [], "query": citation_text}
        for num in mcr_refs:
            rule_id = f"MCR_{num}"
            if self.conn.execute("SELECT 1 FROM rules WHERE id = ?", (rule_id,)).fetchone():
                results["valid"].append(rule_id)
            else:
                results["not_found"].append(rule_id)
        for num in mre_refs:
            rule_id = f"MRE_{num}"
            if self.conn.execute("SELECT 1 FROM rules WHERE id = ?", (rule_id,)).fetchone():
                results["valid"].append(rule_id)
            else:
                results["not_found"].append(rule_id)
        for num in mcl_refs:
            rule_id = f"MCL_{num}"
            if self.conn.execute("SELECT 1 FROM rules WHERE id = ?", (rule_id,)).fetchone():
                results["valid"].append(rule_id)
            else:
                results["not_found"].append(rule_id)
        return results

    def get_elements(self, rule_id: str) -> List[str]:
        """Extract sub-elements from rule text: (A), (B), (1), (2), etc."""
        rule = self.get_rule(rule_id)
        if not rule or not rule.get("full_text"):
            return []
        text = rule["full_text"]
        elements = []
        # Match patterns like (A), (B), (1), (2), (a), (b)
        for m in re.finditer(r"^\s*\(([A-Za-z0-9]+)\)\s+(.+?)(?=\n\s*\([A-Za-z0-9]+\)|\Z)",
                             text, re.MULTILINE | re.DOTALL):
            label = m.group(1)
            content = m.group(2).strip()
            # Truncate very long element text
            if len(content) > 500:
                content = content[:500] + "..."
            elements.append(f"({label}) {content}")
        return elements

    def export_for_engine(self, rule_ids: List[str] = None) -> List[Dict]:
        """Export rules for consumption by the document generation engine."""
        if rule_ids:
            placeholders = ",".join("?" * len(rule_ids))
            normalized = [_normalize_rule_id(r) for r in rule_ids]
            rows = self.conn.execute(
                f"SELECT * FROM rules WHERE id IN ({placeholders})",
                normalized,
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM rules ORDER BY rule_type, rule_number"
            ).fetchall()
        return [dict(r) for r in rows]

    def close(self):
        self.conn.close()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli_ingest():
    engine = AuthorityIngestionEngine()
    try:
        engine.ingest_all()
    finally:
        engine.close()


def _cli_lookup(args: List[str]):
    if len(args) < 2:
        print("Usage: lookup <type> <number>  (e.g. lookup MCR 2.003)")
        return
    rule_type = args[0].upper()
    rule_number = args[1]
    rule_id = f"{rule_type}_{rule_number}"
    lu = AuthorityLookup()
    try:
        rule = lu.get_rule(rule_id)
        if rule:
            print(f"\n{'=' * 70}")
            print(f"RULE: {rule['id']}")
            print(f"Type: {rule['rule_type']}  |  Number: {rule['rule_number']}")
            print(f"Title: {rule.get('title', 'N/A')}")
            print(f"Chapter: {rule.get('chapter', 'N/A')}")
            print(f"Source: {rule.get('source_file', 'N/A')}")
            print(f"{'=' * 70}")
            text = rule.get("full_text", "")
            if text:
                print(text[:3000])
                if len(text) > 3000:
                    print(f"\n... [{len(text) - 3000} more characters]")
            else:
                print("[No full text available]")
            # Show elements
            elements = lu.get_elements(rule_id)
            if elements:
                print(f"\nSub-elements ({len(elements)}):")
                for e in elements[:15]:
                    print(f"  {e[:120]}")
            # Show related rules
            related = lu.find_related_rules(rule_id)
            if related:
                print(f"\nRelated rules ({len(related)}):")
                for r in related[:10]:
                    print(f"  -> {r['related_id']} [{r['edge_type']}] (weight: {r['weight']})")
        else:
            print(f"Rule not found: {rule_id}")
            # Suggest similar
            results = lu.search_rules(rule_number, limit=5)
            if results:
                print("Did you mean:")
                for r in results:
                    print(f"  {r['id']} — {r.get('title', '')[:60]}")
    finally:
        lu.close()


def _cli_search(args: List[str]):
    if not args:
        print("Usage: search <query>")
        return
    query = " ".join(args)
    lu = AuthorityLookup()
    try:
        results = lu.search_rules(query, limit=25)
        if results:
            print(f"\nSearch results for '{query}' ({len(results)} found):\n")
            for r in results:
                snippet = (r.get("snippet") or "")[:80].replace("\n", " ")
                print(f"  {r['id']:<20} {r.get('title', ''):.<40} [{r['rule_type']}]")
                if snippet:
                    print(f"    {snippet}")
        else:
            print(f"No results for: {query}")
    finally:
        lu.close()


def _cli_violations(args: List[str]):
    judge = args[0] if args else None
    lu = AuthorityLookup()
    try:
        violations = lu.get_violations(judge=judge, limit=50)
        if violations:
            print(f"\nBenchbook violations ({len(violations)} found):\n")
            for v in violations:
                sev = f"[sev: {v['severity']:.1f}]" if v.get("severity") else ""
                print(f"  Rule: {v['rule']:<20} {sev}")
                print(f"    {v['explanation'][:100]}")
                if v.get("matching_text"):
                    print(f"    Match: {v['matching_text'][:80]}")
                print()
        else:
            print("No violations found.")
    finally:
        lu.close()


def _cli_report():
    engine = AuthorityIngestionEngine()
    try:
        engine.report()
    finally:
        engine.close()


def _cli_export(args: List[str]):
    lu = AuthorityLookup()
    try:
        rule_ids = args if args else None
        data = lu.export_for_engine(rule_ids)
        output = json.dumps(data, indent=2, default=str)
        if len(data) > 50 and not rule_ids:
            # Write to file instead of stdout
            out_path = os.path.join(
                os.path.dirname(DB_PATH), "authority_export.json"
            )
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"Exported {len(data)} rules to {out_path}")
        else:
            print(output)
    finally:
        lu.close()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1].lower()
    args = sys.argv[2:]

    commands = {
        "ingest": lambda: _cli_ingest(),
        "lookup": lambda: _cli_lookup(args),
        "search": lambda: _cli_search(args),
        "violations": lambda: _cli_violations(args),
        "report": lambda: _cli_report(),
        "export": lambda: _cli_export(args),
    }

    if cmd in commands:
        commands[cmd]()
    else:
        print(f"Unknown command: {cmd}")
        print(f"Available: {', '.join(commands.keys())}")


if __name__ == "__main__":
    main()
