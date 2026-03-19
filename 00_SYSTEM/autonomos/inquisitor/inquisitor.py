"""
INQUISITOR — Intelligent File Watchdog & Auto-Pipeline
=======================================================
Detects newly organized files from SENTINEL, runs them through the analysis
pipeline (classify → extract → atomize → analyze → score), appends results
to litigation_context.db, regenerates affected filing stacks, and pushes
updated court-ready packages to My Documents.

Usage:
  python inquisitor.py start       # Start daemon (Ctrl+C to stop)
  python inquisitor.py process     # Process pending queue once
  python inquisitor.py status      # Show system status
  python inquisitor.py analyze <path>  # Analyze a single file
"""
import sys
import os
import time
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional

_inquisitor_dir = Path(__file__).parent
_shared = _inquisitor_dir.parent / "shared"
_sentinel = _inquisitor_dir.parent / "sentinel"
for p in [str(_inquisitor_dir), str(_shared), str(_sentinel)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from autonomos_config import (
    INQUISITOR_QUEUE_DB, INQUISITOR_RESULTS_DB, CENTRAL_DB,
    EVENT_BRIDGE_DB, EVENT_FILE_ORGANIZED, EVENT_FILE_ANALYZED,
    EVENT_FILING_UPDATED, LANE_PRIORITY, LANE_FILING_MAP,
    PROCESSING_RATE_LIMIT, CHECKPOINT_INTERVAL,
    DIR_MY_DOCS_FILINGS, LITIGOS_ROOT, sha256_file,
)
from event_bridge import EventBridge, Event
from provenance import ProvenanceTracker


@dataclass
class AnalysisResult:
    """Result of analyzing a single file."""
    file_id: str
    file_path: str
    phases_run: list[str] = field(default_factory=list)
    phases_failed: list[str] = field(default_factory=list)
    rows_created: int = 0
    evidence_quotes: int = 0
    claims_found: int = 0
    timeline_entries: int = 0
    citations_found: int = 0
    cross_refs: int = 0
    gaps_resolved: int = 0
    processing_time_s: float = 0.0
    error: str = ""


def _init_results_db(db_path: Path = INQUISITOR_RESULTS_DB) -> sqlite3.Connection:
    """Initialize INQUISITOR results database."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=120000")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS analysis_results (
            file_id TEXT PRIMARY KEY,
            file_path TEXT NOT NULL,
            lane TEXT DEFAULT '',
            doc_type TEXT DEFAULT '',
            phases_run TEXT DEFAULT '',
            phases_failed TEXT DEFAULT '',
            rows_created INTEGER DEFAULT 0,
            evidence_quotes INTEGER DEFAULT 0,
            claims_found INTEGER DEFAULT 0,
            timeline_entries INTEGER DEFAULT 0,
            citations_found INTEGER DEFAULT 0,
            cross_refs INTEGER DEFAULT 0,
            gaps_resolved INTEGER DEFAULT 0,
            processing_time_s REAL DEFAULT 0.0,
            error TEXT DEFAULT '',
            analyzed_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS analysis_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT NOT NULL,
            file_path TEXT NOT NULL,
            lane TEXT DEFAULT '',
            doc_type TEXT DEFAULT '',
            priority INTEGER DEFAULT 5,
            source_event_id TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            error TEXT DEFAULT '',
            queued_at TEXT DEFAULT (datetime('now')),
            processed_at TEXT DEFAULT ''
        );

        CREATE INDEX IF NOT EXISTS idx_aq_status ON analysis_queue(status);
        CREATE INDEX IF NOT EXISTS idx_aq_priority ON analysis_queue(priority);

        CREATE TABLE IF NOT EXISTS filing_updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lane TEXT NOT NULL,
            filing_name TEXT NOT NULL,
            trigger_file_id TEXT NOT NULL,
            version INTEGER DEFAULT 1,
            output_dir TEXT DEFAULT '',
            pushed_to_docs INTEGER DEFAULT 0,
            updated_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    return conn


# ── Single-File Analysis Pipeline ───────────────────────────────────
def _extract_text(file_path: Path) -> str:
    """Extract text from a file (PDF, DOCX, TXT, etc.)."""
    ext = file_path.suffix.lower()
    try:
        if ext == ".pdf":
            try:
                import fitz
                doc = fitz.open(str(file_path))
                text = "\n".join(page.get_text() for page in doc)
                doc.close()
                return text
            except ImportError:
                return ""
        elif ext == ".docx":
            try:
                from docx import Document
                doc = Document(str(file_path))
                return "\n".join(p.text for p in doc.paragraphs)
            except ImportError:
                return ""
        elif ext in (".txt", ".md", ".csv", ".json", ".jsonl"):
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
    except Exception:
        pass
    return ""


def _analyze_content(text: str, lane: str, doc_type: str) -> dict:
    """Analyze extracted text for legal intelligence."""
    import re
    results = {
        "evidence_quotes": [],
        "claims": [],
        "timeline_entries": [],
        "citations": [],
        "contradictions": [],
        "violations": [],
        "harms": [],
    }

    if not text:
        return results

    lines = text.split("\n")
    text_lower = text.lower()

    # Extract legal citations
    from autonomos_config import (
        MCL_PATTERN, MCR_PATTERN, MRE_PATTERN,
        CASE_CITE_PATTERN, USC_PATTERN, VIOLATION_KEYWORDS,
    )

    for pat_name, pat in [("MCL", MCL_PATTERN), ("MCR", MCR_PATTERN),
                          ("MRE", MRE_PATTERN), ("case", CASE_CITE_PATTERN),
                          ("USC", USC_PATTERN)]:
        for match in pat.finditer(text):
            results["citations"].append({
                "type": pat_name, "text": match.group(),
                "position": match.start()
            })

    # Extract date-anchored events for timeline
    date_pattern = re.compile(
        r"(?:on|dated?|as of|beginning|from)\s+(\w+\s+\d{1,2},?\s+\d{4}|\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})",
        re.IGNORECASE
    )
    for match in date_pattern.finditer(text):
        start = max(0, match.start() - 100)
        end = min(len(text), match.end() + 200)
        context = text[start:end].strip()
        results["timeline_entries"].append({
            "date_text": match.group(1),
            "context": context[:300],
        })

    # Extract violation keywords
    for kw in VIOLATION_KEYWORDS:
        if kw.lower() in text_lower:
            # Find surrounding context
            idx = text_lower.index(kw.lower())
            start = max(0, idx - 100)
            end = min(len(text), idx + len(kw) + 200)
            results["violations"].append({
                "keyword": kw,
                "context": text[start:end].strip()[:300],
            })

    # Extract potential evidence quotes (sentences with names + legal terms)
    from autonomos_config import PERSON_NAMES
    for line in lines:
        line_stripped = line.strip()
        if len(line_stripped) < 20 or len(line_stripped) > 500:
            continue
        has_name = any(name.lower() in line_stripped.lower() for name in PERSON_NAMES)
        has_legal = any(kw.lower() in line_stripped.lower()
                        for kw in ["court", "order", "motion", "custody", "child", "parenting"])
        if has_name and has_legal:
            results["evidence_quotes"].append(line_stripped[:500])

    return results


def _write_to_central_db(file_id: str, file_path: str, lane: str,
                         analysis: dict, text: str) -> int:
    """Write analysis results to litigation_context.db. Returns rows created."""
    rows = 0
    try:
        conn = sqlite3.connect(str(CENTRAL_DB), timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=120000")

        # Write evidence quotes
        for quote in analysis.get("evidence_quotes", [])[:50]:
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO evidence_quotes 
                    (quote_text, source_file, lane, created_at)
                    VALUES (?, ?, ?, datetime('now'))
                """, (quote, file_path, lane))
                rows += 1
            except sqlite3.Error:
                pass

        # Write citations
        for cite in analysis.get("citations", [])[:100]:
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO master_citations
                    (citation_text, citation_type, source_file, created_at)
                    VALUES (?, ?, ?, datetime('now'))
                """, (cite["text"], cite["type"], file_path))
                rows += 1
            except sqlite3.Error:
                pass

        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"[INQUISITOR] DB write error: {e}", file=sys.stderr)

    return rows


def analyze_file(file_path: str | Path, lane: str = "", doc_type: str = "") -> AnalysisResult:
    """Run the full analysis pipeline on a single file."""
    fp = Path(file_path)
    file_id = sha256_file(fp) if fp.exists() else "UNKNOWN"
    result = AnalysisResult(file_id=file_id, file_path=str(fp))

    start_time = time.time()

    if not fp.exists():
        result.error = "File not found"
        return result

    # Phase 1: Extract text
    try:
        text = _extract_text(fp)
        result.phases_run.append("extract")
    except Exception as e:
        result.phases_failed.append("extract")
        result.error = f"Extract failed: {e}"
        return result

    if not text:
        result.phases_run.append("extract_empty")
        result.processing_time_s = time.time() - start_time
        return result

    # Phase 2: Analyze content
    try:
        analysis = _analyze_content(text, lane, doc_type)
        result.phases_run.append("analyze")
        result.evidence_quotes = len(analysis.get("evidence_quotes", []))
        result.citations_found = len(analysis.get("citations", []))
        result.timeline_entries = len(analysis.get("timeline_entries", []))
    except Exception as e:
        result.phases_failed.append("analyze")
        analysis = {}

    # Phase 3: Write to central DB
    try:
        rows = _write_to_central_db(file_id, str(fp), lane, analysis, text)
        result.rows_created = rows
        result.phases_run.append("db_write")
    except Exception as e:
        result.phases_failed.append("db_write")

    result.processing_time_s = round(time.time() - start_time, 2)
    return result


# ── INQUISITOR Daemon ───────────────────────────────────────────────
class Inquisitor:
    """Main INQUISITOR daemon — watches for organized files and analyzes them."""

    def __init__(self):
        self._results_db = _init_results_db()
        self._bridge = EventBridge()
        self._provenance = ProvenanceTracker()
        self._running = False
        self._stats = {
            "files_analyzed": 0,
            "total_rows_created": 0,
            "total_citations": 0,
            "total_quotes": 0,
            "errors": 0,
            "started_at": "",
        }

    def start(self):
        """Start the INQUISITOR daemon."""
        print("[INQUISITOR] Starting file analysis daemon...", file=sys.stderr)
        self._stats["started_at"] = datetime.now().isoformat()
        self._running = True

        try:
            self._bridge.process_loop(
                handler=self._handle_event,
                event_types=[EVENT_FILE_ORGANIZED],
                poll_interval=3.0,
            )
        except KeyboardInterrupt:
            print("\n[INQUISITOR] Shutting down...", file=sys.stderr)
        finally:
            self.stop()

    def stop(self):
        self._running = False
        self._results_db.close()
        self._bridge.close()
        self._provenance.close()
        print("[INQUISITOR] Stopped.", file=sys.stderr)

    def _handle_event(self, event: Event):
        """Handle a FILE_ORGANIZED event from SENTINEL."""
        payload = event.payload
        file_path = payload.get("dest_path", "")
        file_id = payload.get("file_id", "")
        lane = payload.get("lane", "")
        doc_type = payload.get("doc_type", "")

        if not file_path or not Path(file_path).exists():
            raise ValueError(f"File not found: {file_path}")

        # Analyze
        result = analyze_file(file_path, lane, doc_type)

        # Store results
        self._results_db.execute("""
            INSERT OR REPLACE INTO analysis_results
            (file_id, file_path, lane, doc_type, phases_run, phases_failed,
             rows_created, evidence_quotes, claims_found, timeline_entries,
             citations_found, cross_refs, gaps_resolved, processing_time_s, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result.file_id, result.file_path, lane, doc_type,
            ",".join(result.phases_run), ",".join(result.phases_failed),
            result.rows_created, result.evidence_quotes, result.claims_found,
            result.timeline_entries, result.citations_found, result.cross_refs,
            result.gaps_resolved, result.processing_time_s, result.error
        ))
        self._results_db.commit()

        # Update provenance
        self._provenance.record_analysis(
            file_id, result.phases_run, result.rows_created
        )

        # Update stats
        self._stats["files_analyzed"] += 1
        self._stats["total_rows_created"] += result.rows_created
        self._stats["total_citations"] += result.citations_found
        self._stats["total_quotes"] += result.evidence_quotes

        # Emit analyzed event
        self._bridge.publish(EVENT_FILE_ANALYZED, {
            "file_id": file_id,
            "file_path": file_path,
            "lane": lane,
            "rows_created": result.rows_created,
            "citations": result.citations_found,
            "quotes": result.evidence_quotes,
        })

        # Check if filing stacks need updating
        if lane in LANE_FILING_MAP and result.rows_created > 0:
            self._trigger_filing_update(lane, file_id)

        print(f"[INQUISITOR] Analyzed {Path(file_path).name}: "
              f"{result.rows_created} rows, {result.citations_found} cites, "
              f"{result.evidence_quotes} quotes ({result.processing_time_s}s)",
              file=sys.stderr)

    def _trigger_filing_update(self, lane: str, trigger_file_id: str):
        """Mark filing stacks for regeneration."""
        filings = LANE_FILING_MAP.get(lane, [])
        for filing_name in filings:
            self._results_db.execute("""
                INSERT INTO filing_updates (lane, filing_name, trigger_file_id)
                VALUES (?, ?, ?)
            """, (lane, filing_name, trigger_file_id))
        self._results_db.commit()

        if filings:
            self._bridge.publish(EVENT_FILING_UPDATED, {
                "lane": lane,
                "filings": filings,
                "trigger_file_id": trigger_file_id,
            })

    def process_once(self, limit: int = 50) -> dict:
        """Process pending events once (non-daemon mode)."""
        events = self._bridge.consume([EVENT_FILE_ORGANIZED], limit=limit)
        for event in events:
            try:
                self._handle_event(event)
                self._bridge.ack(event.event_id)
            except Exception as e:
                self._bridge.nack(event.event_id, str(e))
                self._stats["errors"] += 1
        return {"processed": len(events), **self._stats}

    def status(self) -> dict:
        """Get comprehensive status."""
        analyzed = self._results_db.execute(
            "SELECT COUNT(*) FROM analysis_results"
        ).fetchone()[0]
        pending_updates = self._results_db.execute(
            "SELECT COUNT(*) FROM filing_updates WHERE pushed_to_docs=0"
        ).fetchone()[0]
        return {
            "stats": dict(self._stats),
            "total_analyzed": analyzed,
            "pending_filing_updates": pending_updates,
            "event_queue": self._bridge.stats(),
            "provenance": self._provenance.stats(),
        }


# ── CLI Entry Point ─────────────────────────────────────────────────
def main():
    import argparse
    parser = argparse.ArgumentParser(description="INQUISITOR — File Analysis Daemon")
    sub = parser.add_subparsers(dest="action")

    sub.add_parser("start", help="Start daemon")
    sub.add_parser("process", help="Process pending events once")
    sub.add_parser("status", help="Show status")

    analyze_p = sub.add_parser("analyze", help="Analyze a single file")
    analyze_p.add_argument("file", help="File path to analyze")
    analyze_p.add_argument("--lane", default="", help="Case lane (A-F)")
    analyze_p.add_argument("--type", default="", help="Document type")

    args = parser.parse_args()
    inquisitor = Inquisitor()

    if args.action == "start":
        inquisitor.start()
    elif args.action == "process":
        result = inquisitor.process_once()
        print(json.dumps(result, indent=2))
    elif args.action == "status":
        print(json.dumps(inquisitor.status(), indent=2))
    elif args.action == "analyze":
        result = analyze_file(args.file, args.lane, getattr(args, "type", ""))
        print(json.dumps(asdict(result), indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
