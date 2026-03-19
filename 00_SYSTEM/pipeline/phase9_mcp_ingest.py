"""
OMEGA Phase 9: MCP Server Bulk Ingest
Read HIGH-priority PDFs from inventory.db, insert into the MCP server's
SQLite database (litigation_context.db) with FTS5 indexing.
"""
import hashlib
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from config import (
    SCANS_ROOT, MASTER_ROOT, sha256_file,
    get_cyclepack_dir, report_progress, CYCLE_TS,
)
from safety import write_phase_checkpoint, is_phase_done

# MCP server DB — matches db.py DB_PATH logic
MCP_DB_PATH = Path(os.environ.get("LITIGATION_DB_DIR", os.path.expanduser("~"))) / "litigation_context.db"

# Inventory database from Phase 1
INVENTORY_DB = None  # resolved at runtime from cycle_dir


def _find_inventory_db(cycle_dir: Path) -> Path | None:
    """Locate inventory.db — check cycle_dir first, then scans root."""
    candidates = [
        cycle_dir / "inventory.db",
        SCANS_ROOT / "tooling" / "inventory.db",
        SCANS_ROOT / "inventory.db",
        MASTER_ROOT / "inventory.db",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def _get_high_priority_pdfs(inv_db: Path) -> list[dict]:
    """Query inventory.db for HIGH-priority PDF paths."""
    conn = sqlite3.connect(str(inv_db), timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        # Try priority column first, fall back to classification
        try:
            rows = conn.execute("""
                SELECT file_path, file_name, sha256, size_bytes
                FROM files
                WHERE extension = '.pdf'
                  AND (priority = 'HIGH' OR classification = 'HIGH'
                       OR is_legal = 1 OR bucket_priority >= 7)
                ORDER BY size_bytes DESC
            """).fetchall()
        except sqlite3.OperationalError:
            # Simpler query if columns don't exist
            rows = conn.execute("""
                SELECT file_path, file_name, sha256, size_bytes
                FROM files
                WHERE extension = '.pdf'
                ORDER BY size_bytes DESC
            """).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def _ensure_mcp_schema(conn: sqlite3.Connection):
    """Ensure MCP tables exist (minimal subset needed for ingest)."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE NOT NULL,
            file_name TEXT NOT NULL,
            file_size_bytes INTEGER,
            modified_date TEXT,
            page_count INTEGER DEFAULT 0,
            sha256_hash TEXT,
            ingested_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            page_number INTEGER NOT NULL,
            text_content TEXT NOT NULL,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
            UNIQUE(document_id, page_number)
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts USING fts5(
            text_content,
            content='pages',
            content_rowid='id',
            tokenize='porter unicode61'
        );

        CREATE TRIGGER IF NOT EXISTS pages_ai AFTER INSERT ON pages BEGIN
            INSERT INTO pages_fts(rowid, text_content) VALUES (new.id, new.text_content);
        END;

        CREATE INDEX IF NOT EXISTS idx_documents_hash ON documents(sha256_hash);
        CREATE INDEX IF NOT EXISTS idx_pages_doc ON pages(document_id);
    """)


def _extract_pdf_text(pdf_path: str) -> list[dict]:
    """Extract text from PDF pages. Returns list of {page_number, text_content}."""
    pages: list[dict] = []
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        for i, page in enumerate(doc):
            text = page.get_text("text").strip()
            if text:
                pages.append({"page_number": i + 1, "text_content": text})
        doc.close()
    except ImportError:
        # Fallback: try pdfminer
        try:
            from pdfminer.high_level import extract_text
            text = extract_text(pdf_path)
            if text and text.strip():
                pages.append({"page_number": 1, "text_content": text.strip()})
        except ImportError:
            pass
    except (sqlite3.Error, FileNotFoundError, OSError) as e:
        print(f"[PHASE9] Warning: {e}", file=sys.stderr)
    return pages


def _is_already_ingested(conn: sqlite3.Connection, file_path: str, sha256: str | None) -> bool:
    """Check if document is already in MCP database."""
    if sha256:
        row = conn.execute(
            "SELECT id FROM documents WHERE sha256_hash = ? OR file_path = ?",
            (sha256, file_path),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT id FROM documents WHERE file_path = ?",
            (file_path,),
        ).fetchone()
    return row is not None


def run_mcp_ingest(cycle_dir: Path, dry_run: bool = False):
    if is_phase_done(cycle_dir, "phase9"):
        print("[PHASE9] Already complete, skipping", file=sys.stderr)
        return

    print("[PHASE9] MCP Bulk Ingest starting...", file=sys.stderr)
    start = time.time()

    # Find inventory DB
    inv_db = _find_inventory_db(cycle_dir)
    if not inv_db:
        print("[PHASE9] No inventory.db found — run Phase 1 first", file=sys.stderr)
        write_phase_checkpoint(cycle_dir, "phase9", {
            "status": "done", "reason": "no_inventory_db", "ingested": 0,
        })
        return

    print(f"[PHASE9] Using inventory: {inv_db}", file=sys.stderr)

    # Get HIGH-priority PDFs
    pdfs = _get_high_priority_pdfs(inv_db)
    print(f"[PHASE9] Found {len(pdfs)} PDF candidates", file=sys.stderr)

    if not pdfs:
        write_phase_checkpoint(cycle_dir, "phase9", {
            "status": "done", "reason": "no_pdfs", "ingested": 0,
        })
        return

    # Connect to MCP database
    mcp_db = str(MCP_DB_PATH)
    print(f"[PHASE9] MCP database: {mcp_db}", file=sys.stderr)

    stats = {
        "total_candidates": len(pdfs),
        "ingested": 0,
        "skipped_exists": 0,
        "skipped_no_text": 0,
        "skipped_not_found": 0,
        "errors": 0,
        "total_pages": 0,
    }

    # Setup ingest log
    cycle_dir.mkdir(parents=True, exist_ok=True)
    log_path = cycle_dir / "ingest_log.jsonl"

    if dry_run:
        print(f"[PHASE9] DRY RUN — would ingest {len(pdfs)} PDFs into {mcp_db}", file=sys.stderr)
        stats["dry_run"] = True
    else:
        mcp_conn = sqlite3.connect(mcp_db, timeout=60)
        mcp_conn.execute("PRAGMA journal_mode=WAL")
        mcp_conn.execute("PRAGMA busy_timeout=30000")
        mcp_conn.row_factory = sqlite3.Row
        _ensure_mcp_schema(mcp_conn)

        log_fh = open(str(log_path), "a", encoding="utf-8")

        for idx, pdf in enumerate(pdfs):
            fp = pdf["file_path"]
            fname = pdf["file_name"]
            sha = pdf.get("sha256")

            log_entry = {"path": fp, "status": "pending", "timestamp": datetime.now().isoformat()}

            if not os.path.isfile(fp):
                stats["skipped_not_found"] += 1
                log_entry["status"] = "not_found"
                log_fh.write(json.dumps(log_entry) + "\n")
                continue

            if _is_already_ingested(mcp_conn, fp, sha):
                stats["skipped_exists"] += 1
                log_entry["status"] = "already_exists"
                log_fh.write(json.dumps(log_entry) + "\n")
                continue

            try:
                # Compute SHA if missing
                if not sha:
                    sha = sha256_file(fp)

                # Extract text
                pages = _extract_pdf_text(fp)
                if not pages:
                    stats["skipped_no_text"] += 1
                    log_entry["status"] = "no_text"
                    log_fh.write(json.dumps(log_entry) + "\n")
                    continue

                # Get file metadata
                fstat = os.stat(fp)
                mod_date = datetime.fromtimestamp(fstat.st_mtime).isoformat()
                now = datetime.now(timezone.utc).isoformat()

                # Insert document
                cur = mcp_conn.execute(
                    """INSERT INTO documents
                       (file_path, file_name, file_size_bytes, modified_date, page_count, sha256_hash, ingested_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (fp, fname, fstat.st_size, mod_date, len(pages), sha, now),
                )
                doc_id = cur.lastrowid

                # Insert pages (FTS trigger handles indexing)
                mcp_conn.executemany(
                    "INSERT INTO pages (document_id, page_number, text_content) VALUES (?, ?, ?)",
                    [(doc_id, p["page_number"], p["text_content"]) for p in pages],
                )
                mcp_conn.commit()

                stats["ingested"] += 1
                stats["total_pages"] += len(pages)
                log_entry["status"] = "ingested"
                log_entry["doc_id"] = doc_id
                log_entry["pages"] = len(pages)

            except sqlite3.IntegrityError:
                stats["skipped_exists"] += 1
                log_entry["status"] = "duplicate"
            except Exception as e:
                stats["errors"] += 1
                log_entry["status"] = "error"
                log_entry["error"] = str(e)[:300]

            log_fh.write(json.dumps(log_entry) + "\n")

            if (idx + 1) % 50 == 0 or idx + 1 == len(pdfs):
                report_progress("phase9", idx + 1, len(pdfs))

        log_fh.close()
        mcp_conn.close()

    elapsed = round(time.time() - start, 1)
    stats["elapsed_seconds"] = elapsed

    # Write stats
    if not dry_run:
        stats_path = cycle_dir / "mcp_ingest_stats.json"
        stats_path.write_text(json.dumps(stats, indent=2), encoding="utf-8")
        print(f"[PHASE9] Stats written: {stats_path}", file=sys.stderr)

        write_phase_checkpoint(cycle_dir, "phase9", {
            "status": "done",
            "ingested": stats["ingested"],
            "skipped": stats["skipped_exists"] + stats["skipped_no_text"] + stats["skipped_not_found"],
            "errors": stats["errors"],
            "pages": stats["total_pages"],
            "elapsed": f"{elapsed:.0f}s",
        })

    print(f"[PHASE9] Complete in {elapsed:.0f}s — "
          f"{stats['ingested']} ingested, {stats['skipped_exists']} dupes, "
          f"{stats['errors']} errors, {stats['total_pages']} pages",
          file=sys.stderr)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Phase 9: MCP Server Bulk Ingest")
    parser.add_argument("--cycle-ts", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run_mcp_ingest(get_cyclepack_dir(args.cycle_ts or CYCLE_TS), args.dry_run)
