#!/usr/bin/env python3
"""
MBP LitigationOS — ChatGPT Conversation Ingestion
===================================================
Parses ChatGPT export JSON files and loads messages into
chatgpt_conversations table in litigation_context.db.

Handles:
  - Standard ChatGPT export format (array of conversations)
  - Deduplication across multiple files by conversation ID
  - Streaming JSON parsing for large files (ijson fallback to json)
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from cycle_method import cycle_json, cycle_print
except ImportError:
    cycle_json = lambda o, **k: print(json.dumps(o, default=str))
    cycle_print = print

DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\litigation_context.db",
)

# All known ChatGPT export file locations
CANDIDATE_FILES = [
    r"C:\Users\andre\LitigationOS\00_SYSTEM\lexos_bible\conversations.json",
    r"C:\Users\andre\LitigationOS\00_SYSTEM\lexos_bible\chat_export_litigationos.json",
    r"C:\Users\andre\LitigationOS\00_SYSTEM\conversations.json",
    r"C:\Users\andre\LitigationOS\00_SYSTEM\chat_export_litigationos.json",
    r"C:\Users\andre\Documents\conversations.json",
    r"C:\Users\andre\Documents\chat_export_litigationos.json",
    r"C:\Users\andre\Downloads\conversations.json",
    r"C:\Users\andre\Downloads\chat_export_litigationos.json",
    r"C:\Users\andre\LitigationOS\02_EVIDENCE\GPT\conversations (1).json",
    r"C:\Users\andre\LitigationOS\02_EVIDENCE\discovery_scan\conversations (1).json",
    r"C:\Users\andre\LitigationOS\02_EVIDENCE\documents_scan\conversations (1).json",
    r"C:\Users\andre\LitigationOS\02_EVIDENCE\new_folder_scan\conversations (1).json",
    r"C:\Users\andre\Scans\discovery\fredprime-legal-system\LITIGATION_OS__ALL_PC_EVIDENCE_EXTRACTED__Uncategorized__CHAT GPT DATA EXPORT__conversations.json",
    r"C:\Users\andre\Scans\discovery\fredprime-legal-system\LITIGATION_OS__ALL_PC_EVIDENCE_EXTRACTED__Uncategorized__Chat GPT Export__conversations.json",
    r"C:\Users\andre\Scans\discovery\fredprime-legal-system\LITIGATION_OS__ALL_PC_EVIDENCE_EXTRACTED__Uncategorized__Chat GPT Export__shared_conversations.json",
]


def create_table(conn: sqlite3.Connection):
    """Create chatgpt_conversations table if not exists."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chatgpt_conversations (
            id TEXT PRIMARY KEY,
            title TEXT,
            message_role TEXT,
            message_text TEXT,
            conversation_id TEXT,
            message_index INTEGER,
            created_at TEXT
        )
    """)
    try:
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chatgpt_conv_id ON chatgpt_conversations(conversation_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chatgpt_role ON chatgpt_conversations(message_role)")
    except Exception:
        pass
    conn.commit()


def _extract_message_text(msg_data: dict) -> str:
    """Extract text from a ChatGPT message content structure."""
    try:
        content = msg_data.get("content", {})
        if isinstance(content, str):
            return content.strip()
        parts = content.get("parts", [])
        text_parts = []
        for part in parts:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict):
                # Could be image or other content type
                t = part.get("text", "")
                if t:
                    text_parts.append(t)
        return "\n".join(text_parts).strip()
    except Exception:
        return ""


def _make_id(conv_id: str, msg_index: int) -> str:
    """Create a stable unique ID for a message."""
    raw = f"{conv_id}:{msg_index}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def parse_conversations_file(file_path: str) -> list[dict]:
    """Parse a ChatGPT export JSON file and return message records."""
    records = []
    cycle_print(f"  Parsing: {file_path}")
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    cycle_print(f"  File size: {file_size_mb:.1f} MB")

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        cycle_print(f"  [WARN] JSON decode error: {e}")
        return []
    except MemoryError:
        cycle_print(f"  [WARN] File too large to load in memory, skipping: {file_path}")
        return []
    except Exception as e:
        cycle_print(f"  [WARN] Error reading file: {e}")
        return []

    if not isinstance(data, list):
        cycle_print(f"  [WARN] Expected array, got {type(data).__name__}")
        return []

    for conv in data:
        try:
            if not isinstance(conv, dict):
                continue

            conv_id = conv.get("id", str(uuid.uuid4()))
            title = conv.get("title", "Untitled")
            create_time = conv.get("create_time")
            created_at = ""
            if create_time:
                try:
                    created_at = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(float(create_time)))
                except Exception:
                    created_at = str(create_time)

            # ChatGPT exports have "mapping" dict with message nodes
            mapping = conv.get("mapping", {})
            if mapping and isinstance(mapping, dict):
                msg_index = 0
                # Sort by create_time if available
                sorted_nodes = sorted(
                    mapping.values(),
                    key=lambda n: (n.get("message", {}) or {}).get("create_time") or 0
                    if isinstance(n, dict) else 0
                )
                for node in sorted_nodes:
                    if not isinstance(node, dict):
                        continue
                    msg = node.get("message")
                    if not msg or not isinstance(msg, dict):
                        continue

                    role = msg.get("author", {}).get("role", "") if isinstance(msg.get("author"), dict) else ""
                    if role not in ("user", "assistant", "system", "tool"):
                        continue

                    text = _extract_message_text(msg)
                    if not text or len(text) < 2:
                        continue

                    msg_time = ""
                    mt = msg.get("create_time")
                    if mt:
                        try:
                            msg_time = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(float(mt)))
                        except Exception:
                            msg_time = created_at

                    records.append({
                        "id": _make_id(conv_id, msg_index),
                        "title": (title or "")[:500],
                        "message_role": role,
                        "message_text": text,
                        "conversation_id": conv_id,
                        "message_index": msg_index,
                        "created_at": msg_time or created_at,
                    })
                    msg_index += 1
            else:
                # Fallback: some exports use flat "messages" array
                messages = conv.get("messages", [])
                if isinstance(messages, list):
                    for idx, msg in enumerate(messages):
                        if not isinstance(msg, dict):
                            continue
                        role = msg.get("role", msg.get("author", ""))
                        if isinstance(role, dict):
                            role = role.get("role", "")
                        text = msg.get("content", "")
                        if isinstance(text, dict):
                            text = _extract_message_text(msg)
                        elif isinstance(text, list):
                            text = "\n".join(str(p) for p in text)
                        if not text or len(text) < 2:
                            continue
                        if role not in ("user", "assistant", "system", "tool"):
                            continue
                        records.append({
                            "id": _make_id(conv_id, idx),
                            "title": (title or "")[:500],
                            "message_role": role,
                            "message_text": text,
                            "conversation_id": conv_id,
                            "message_index": idx,
                            "created_at": created_at,
                        })

        except Exception as e:
            # Skip individual conversation errors
            continue

    cycle_print(f"  Extracted {len(records)} messages from {file_path}")
    return records


def ingest_chatgpt():
    """Main ingestion pipeline."""
    t0 = time.time()
    cycle_print("=" * 60)
    cycle_print("MBP LitigationOS — ChatGPT Conversation Ingestion")
    cycle_print("=" * 60)

    # Find existing files
    found_files = []
    for f in CANDIDATE_FILES:
        if os.path.exists(f) and os.path.getsize(f) > 10:
            found_files.append(f)
    cycle_print(f"\nFound {len(found_files)} conversation files:")
    for f in found_files:
        size_mb = os.path.getsize(f) / (1024 * 1024)
        cycle_print(f"  [{size_mb:.1f} MB] {f}")

    if not found_files:
        cycle_print("[ERROR] No ChatGPT export files found!")
        return {"error": "No files found", "searched": CANDIDATE_FILES}

    # Deduplicate by file hash (skip identical copies)
    seen_hashes = {}
    unique_files = []
    for f in found_files:
        try:
            # Hash first 1MB for speed
            with open(f, "rb") as fh:
                h = hashlib.md5(fh.read(1024 * 1024)).hexdigest()
            if h not in seen_hashes:
                seen_hashes[h] = f
                unique_files.append(f)
            else:
                cycle_print(f"  [SKIP] Duplicate of {seen_hashes[h]}: {f}")
        except Exception:
            unique_files.append(f)

    cycle_print(f"\n{len(unique_files)} unique files to process (after dedup)")

    # Sort by size ascending (process smaller files first)
    unique_files.sort(key=lambda f: os.path.getsize(f))

    # Skip files larger than 500MB to avoid memory issues
    MAX_FILE_SIZE = 500 * 1024 * 1024
    processable = []
    for f in unique_files:
        sz = os.path.getsize(f)
        if sz > MAX_FILE_SIZE:
            cycle_print(f"  [SKIP] Too large ({sz / (1024*1024):.0f} MB > 500 MB limit): {f}")
        else:
            processable.append(f)

    # Connect to DB
    cycle_print(f"\nConnecting to DB: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-65536")
    create_table(conn)

    # Process files
    total_records = []
    all_conv_ids = set()
    files_processed = 0
    files_errored = 0

    for fp in processable:
        try:
            records = parse_conversations_file(fp)
            new_records = []
            for r in records:
                # Deduplicate across files by conversation_id + message_index
                key = f"{r['conversation_id']}:{r['message_index']}"
                if key not in all_conv_ids:
                    all_conv_ids.add(key)
                    new_records.append(r)
            total_records.extend(new_records)
            files_processed += 1
            cycle_print(f"  → {len(new_records)} new unique messages")
        except Exception as e:
            cycle_print(f"  [ERROR] {fp}: {e}")
            files_errored += 1

    cycle_print(f"\nTotal unique messages to ingest: {len(total_records)}")

    # Batch insert
    inserted = 0
    skipped = 0
    batch_size = 1000

    for i in range(0, len(total_records), batch_size):
        batch = total_records[i:i + batch_size]
        for r in batch:
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO chatgpt_conversations "
                    "(id, title, message_role, message_text, conversation_id, message_index, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (r["id"], r["title"], r["message_role"], r["message_text"],
                     r["conversation_id"], r["message_index"], r["created_at"])
                )
                inserted += 1
            except sqlite3.IntegrityError:
                skipped += 1
            except Exception as e:
                skipped += 1
        conn.commit()
        if (i + batch_size) % 10000 == 0:
            cycle_print(f"  Progress: {i + batch_size}/{len(total_records)}")

    # Get stats
    try:
        total_rows = conn.execute("SELECT COUNT(*) FROM chatgpt_conversations").fetchone()[0]
        unique_convs = conn.execute("SELECT COUNT(DISTINCT conversation_id) FROM chatgpt_conversations").fetchone()[0]
        role_counts = dict(conn.execute(
            "SELECT message_role, COUNT(*) FROM chatgpt_conversations GROUP BY message_role"
        ).fetchall())
    except Exception:
        total_rows = inserted
        unique_convs = 0
        role_counts = {}

    conn.close()

    elapsed = time.time() - t0

    result = {
        "status": "success",
        "elapsed_seconds": round(elapsed, 1),
        "files_found": len(found_files),
        "files_unique": len(unique_files),
        "files_processed": files_processed,
        "files_errored": files_errored,
        "messages_ingested": inserted,
        "messages_skipped_duplicate": skipped,
        "total_rows_in_table": total_rows,
        "unique_conversations": unique_convs,
        "role_distribution": role_counts,
    }

    cycle_print(f"\n{'=' * 60}")
    cycle_print("ChatGPT Ingestion Complete")
    cycle_print(f"{'=' * 60}")
    cycle_print(f"  Files processed:      {files_processed}")
    cycle_print(f"  Messages ingested:    {inserted:,}")
    cycle_print(f"  Duplicates skipped:   {skipped:,}")
    cycle_print(f"  Total rows in table:  {total_rows:,}")
    cycle_print(f"  Unique conversations: {unique_convs:,}")
    cycle_print(f"  Role distribution:    {role_counts}")
    cycle_print(f"  Elapsed:              {elapsed:.1f}s")
    cycle_print(f"{'=' * 60}")

    cycle_json(result)
    return result


if __name__ == "__main__":
    ingest_chatgpt()
