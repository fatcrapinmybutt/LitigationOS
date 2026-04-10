#!/usr/bin/env python3
"""
Phase 4 — Extract ALL attachments from Starred.mbox
Saves to J:\\LitigationOS_CENTRAL\\EMAIL_ATTACHMENTS\\<sender>/<date>_<filename>
Tracks in litigation_context.db email_attachments table.
"""

import mailbox
import email
import email.utils
import email.header
import os
import re
import sqlite3
import hashlib
import time
import unicodedata
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
MBOX_PATH = r"C:\Users\andre\LitigationOS\10_EXTERNAL\Starred.mbox"
OUTPUT_DIR = Path(r"J:\LitigationOS_CENTRAL\EMAIL_ATTACHMENTS")
DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

# Skip these content types — they are inline message parts, not real attachments
SKIP_CONTENT_TYPES = frozenset({
    "text/plain", "text/html", "multipart/mixed", "multipart/alternative",
    "multipart/related", "multipart/signed", "multipart/report",
    "message/delivery-status", "message/rfc822",
})

# ── Helpers ───────────────────────────────────────────────────────────────────

def sanitize_filename(name: str) -> str:
    """Make a filename safe for Windows filesystem."""
    if not name:
        return "unnamed_attachment"
    # Decode RFC 2047 encoded headers
    try:
        decoded_parts = email.header.decode_header(name)
        decoded = ""
        for part, charset in decoded_parts:
            if isinstance(part, bytes):
                decoded += part.decode(charset or "utf-8", errors="replace")
            else:
                decoded += part
        name = decoded
    except Exception:
        pass
    # Normalize unicode
    name = unicodedata.normalize("NFKD", name)
    # Remove or replace illegal Windows filename chars
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)
    # Collapse whitespace and dots
    name = re.sub(r'\s+', ' ', name).strip()
    name = re.sub(r'\.{2,}', '.', name)
    # Truncate to 200 chars (leave room for prefix)
    if len(name) > 200:
        stem, ext = os.path.splitext(name)
        name = stem[:200 - len(ext)] + ext
    return name or "unnamed_attachment"


def sanitize_sender(sender_raw: str) -> str:
    """Extract a clean folder name from sender string."""
    if not sender_raw:
        return "unknown_sender"
    # Decode RFC 2047
    try:
        decoded_parts = email.header.decode_header(sender_raw)
        decoded = ""
        for part, charset in decoded_parts:
            if isinstance(part, bytes):
                decoded += part.decode(charset or "utf-8", errors="replace")
            else:
                decoded += part
        sender_raw = decoded
    except Exception:
        pass
    # Try to get just the name portion
    name, addr = email.utils.parseaddr(sender_raw)
    if name:
        folder = name.strip()
    elif addr:
        folder = addr.split("@")[0]
    else:
        folder = sender_raw.strip()
    # Sanitize for filesystem
    folder = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', folder)
    folder = re.sub(r'\s+', ' ', folder).strip()
    folder = folder[:100] or "unknown_sender"
    return folder


def parse_date(date_str: str) -> str:
    """Parse email date header to YYYY-MM-DD, fallback to 'unknown_date'."""
    if not date_str:
        return "unknown_date"
    try:
        parsed = email.utils.parsedate_to_datetime(date_str)
        return parsed.strftime("%Y-%m-%d")
    except Exception:
        pass
    # Fallback: try to extract any date-like pattern
    m = re.search(r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+(\d{4})', date_str, re.I)
    if m:
        try:
            dt = datetime.strptime(f"{m.group(1)} {m.group(2)} {m.group(3)}", "%d %b %Y")
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass
    return "unknown_date"


def unique_path(target: Path) -> Path:
    """If target exists, append _1, _2, ... suffix to stem."""
    if not target.exists():
        return target
    stem = target.stem
    ext = target.suffix
    parent = target.parent
    n = 1
    while True:
        candidate = parent / f"{stem}_{n}{ext}"
        if not candidate.exists():
            return candidate
        n += 1


def get_email_id(msg) -> str:
    """Get a stable email identifier from Message-ID or hash."""
    mid = msg.get("Message-ID", "")
    if mid:
        return mid.strip().strip("<>")
    # Fallback: hash of from+date+subject
    raw = f"{msg.get('From','')}{msg.get('Date','')}{msg.get('Subject','')}".encode("utf-8", errors="replace")
    return hashlib.sha256(raw).hexdigest()[:32]


# ── DB Setup ──────────────────────────────────────────────────────────────────

def setup_db(db_path: str) -> sqlite3.Connection:
    """Connect with mandatory PRAGMAs and create table."""
    conn = sqlite3.connect(db_path, timeout=120)
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS email_attachments (
            attachment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id TEXT,
            original_filename TEXT,
            saved_path TEXT,
            file_size INTEGER,
            mime_type TEXT,
            content_type TEXT,
            extracted_at TEXT
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_email_att_email_id
        ON email_attachments(email_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_email_att_mime
        ON email_attachments(mime_type)
    """)
    conn.commit()
    return conn


# ── Main Extraction ───────────────────────────────────────────────────────────

def extract_attachments():
    print(f"{'='*72}")
    print(f"  Phase 4 — Email Attachment Extractor")
    print(f"  MBOX : {MBOX_PATH}")
    print(f"  Output: {OUTPUT_DIR}")
    print(f"  DB   : {DB_PATH}")
    print(f"{'='*72}\n")

    # Verify MBOX
    if not os.path.isfile(MBOX_PATH):
        print(f"ERROR: MBOX not found at {MBOX_PATH}")
        return

    # Create output dir (J: is exFAT, no special perms needed)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Open DB
    conn = setup_db(DB_PATH)

    # Check for prior run — count existing rows
    prior_count = conn.execute("SELECT COUNT(*) FROM email_attachments").fetchone()[0]
    if prior_count > 0:
        print(f"  ⚠ Found {prior_count:,} existing rows in email_attachments table.")
        print(f"  Skipping files already on disk; inserting only new extractions.\n")

    # Load existing saved_paths for dedup
    existing_paths = set()
    for row in conn.execute("SELECT saved_path FROM email_attachments"):
        existing_paths.add(row[0])

    # Open MBOX
    t0 = time.perf_counter()
    print("  Opening MBOX... ", end="", flush=True)
    mbox = mailbox.mbox(MBOX_PATH)
    total_msgs = len(mbox)
    print(f"{total_msgs:,} messages found.\n")

    # Stats
    extracted_count = 0
    skipped_zero = 0
    skipped_dup = 0
    skipped_inline = 0
    errors = 0
    emails_with_attachments = 0
    total_bytes = 0
    by_extension = defaultdict(int)
    by_sender = defaultdict(int)
    size_by_ext = defaultdict(int)

    batch_rows = []
    BATCH_SIZE = 500

    def flush_batch():
        nonlocal batch_rows
        if not batch_rows:
            return
        conn.executemany("""
            INSERT INTO email_attachments
                (email_id, original_filename, saved_path, file_size, mime_type, content_type, extracted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, batch_rows)
        conn.commit()
        batch_rows = []

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for i, msg in enumerate(mbox):
        if (i + 1) % 200 == 0:
            elapsed = time.perf_counter() - t0
            print(f"  Processing message {i+1:,}/{total_msgs:,}  |  "
                  f"attachments: {extracted_count:,}  |  "
                  f"{elapsed:.1f}s elapsed", flush=True)

        eid = get_email_id(msg)
        sender_raw = msg.get("From", "unknown")
        date_str = msg.get("Date", "")
        sender_folder = sanitize_sender(sender_raw)
        date_prefix = parse_date(date_str)

        msg_had_attachment = False

        for part in msg.walk():
            content_type = part.get_content_type() or ""
            content_disp = str(part.get("Content-Disposition") or "")

            # Skip multipart containers and inline text
            if part.get_content_maintype() == "multipart":
                continue

            # Determine if this is an attachment
            is_attachment = False
            filename = part.get_filename()

            if filename:
                is_attachment = True
            elif "attachment" in content_disp.lower():
                is_attachment = True
                filename = "unnamed_attachment"
            elif content_type.lower() not in SKIP_CONTENT_TYPES:
                # Some attachments lack Content-Disposition but have non-text types
                if part.get_content_maintype() in ("image", "application", "audio", "video"):
                    is_attachment = True
                    # Try to derive filename from content-type name param
                    ct_name = part.get_param("name")
                    if ct_name:
                        if isinstance(ct_name, tuple):
                            ct_name = ct_name[2]  # (charset, language, value)
                        filename = str(ct_name)
                    else:
                        ext_map = {
                            "application/pdf": ".pdf",
                            "image/jpeg": ".jpg",
                            "image/png": ".png",
                            "image/gif": ".gif",
                            "application/msword": ".doc",
                            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
                            "application/vnd.ms-excel": ".xls",
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
                            "application/zip": ".zip",
                            "application/octet-stream": ".bin",
                        }
                        ext = ext_map.get(content_type.lower(), ".bin")
                        filename = f"unnamed_attachment{ext}"

            if not is_attachment:
                continue

            # Get payload
            try:
                payload = part.get_payload(decode=True)
            except Exception as e:
                errors += 1
                continue

            if payload is None:
                skipped_inline += 1
                continue

            if len(payload) == 0:
                skipped_zero += 1
                continue

            # Clean filename
            safe_name = sanitize_filename(filename or "unnamed_attachment")
            ext = os.path.splitext(safe_name)[1].lower() or ".bin"

            # Build output path: sender_folder/YYYY-MM-DD_filename
            target_dir = OUTPUT_DIR / sender_folder
            target_dir.mkdir(parents=True, exist_ok=True)
            target_file = target_dir / f"{date_prefix}_{safe_name}"
            target_file = unique_path(target_file)

            # Check if we already extracted this exact path in a prior run
            rel_path = str(target_file)
            if rel_path in existing_paths:
                skipped_dup += 1
                continue

            # Write file
            try:
                target_file.write_bytes(payload)
            except Exception as e:
                errors += 1
                continue

            file_size = len(payload)
            mime_main = part.get_content_maintype() or ""
            mime_sub = part.get_content_subtype() or ""
            mime_type = f"{mime_main}/{mime_sub}" if mime_main else content_type

            # Track stats
            extracted_count += 1
            total_bytes += file_size
            by_extension[ext] += 1
            by_sender[sender_folder] += 1
            size_by_ext[ext] += file_size
            msg_had_attachment = True

            batch_rows.append((
                eid,
                filename or "unnamed",
                str(target_file),
                file_size,
                mime_type,
                content_type,
                now_str,
            ))

            if len(batch_rows) >= BATCH_SIZE:
                flush_batch()

        if msg_had_attachment:
            emails_with_attachments += 1

    # Final flush
    flush_batch()

    elapsed = time.perf_counter() - t0

    # ── Verify DB ─────────────────────────────────────────────────────────────
    new_count = conn.execute("SELECT COUNT(*) FROM email_attachments").fetchone()[0]
    inserted = new_count - prior_count

    # ── Report ────────────────────────────────────────────────────────────────
    print(f"\n{'='*72}")
    print(f"  EXTRACTION COMPLETE")
    print(f"{'='*72}")
    print(f"  Total messages scanned   : {total_msgs:,}")
    print(f"  Emails with attachments  : {emails_with_attachments:,}")
    print(f"  Attachments extracted    : {extracted_count:,}")
    print(f"  Total size extracted     : {total_bytes / (1024*1024):.1f} MB")
    print(f"  Skipped (zero-byte)      : {skipped_zero:,}")
    print(f"  Skipped (inline/no data) : {skipped_inline:,}")
    print(f"  Skipped (duplicate path) : {skipped_dup:,}")
    print(f"  Errors                   : {errors:,}")
    print(f"  DB rows before           : {prior_count:,}")
    print(f"  DB rows after            : {new_count:,}")
    print(f"  DB rows inserted         : {inserted:,}")
    print(f"  Elapsed                  : {elapsed:.1f}s")

    if extracted_count != inserted and prior_count == 0:
        print(f"\n  ⚠ MISMATCH: extracted {extracted_count} files but inserted {inserted} DB rows!")

    # By file type
    print(f"\n  {'─'*50}")
    print(f"  BY FILE TYPE:")
    for ext, count in sorted(by_extension.items(), key=lambda x: -x[1]):
        sz = size_by_ext[ext] / (1024 * 1024)
        print(f"    {ext:12s}  {count:6,} files  ({sz:8.1f} MB)")

    # Top senders
    print(f"\n  {'─'*50}")
    print(f"  TOP 25 SENDERS:")
    for sender, count in sorted(by_sender.items(), key=lambda x: -x[1])[:25]:
        print(f"    {sender:40s}  {count:5,} attachments")

    print(f"\n{'='*72}")
    print(f"  Output directory: {OUTPUT_DIR}")
    print(f"  DB table: email_attachments ({new_count:,} rows)")
    print(f"{'='*72}\n")

    conn.close()


if __name__ == "__main__":
    extract_attachments()
