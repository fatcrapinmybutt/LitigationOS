#!/usr/bin/env python3
"""
APEX Chat Intelligence Extraction Engine v1.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Streams ChatGPT conversation JSON files (1-1.5GB) in O(1) memory,
extracts litigation intelligence, and stores in chat_intelligence_brain.db.

Usage:
    python -I apex_chat_extractor.py --file conversations.json
    python -I apex_chat_extractor.py --manifest temp/_unique_manifest.json
    python -I apex_chat_extractor.py --dry-run --file conversations.json

Run with -I flag to prevent shadow module conflicts from repo root.
"""

import sys
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', errors='replace')

import argparse
import json
import os
import re
import sqlite3
import time
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    import ijson
except ImportError:
    print("FATAL: ijson not installed. Run: pip install ijson", file=sys.stderr)
    sys.exit(1)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Constants
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DEFAULT_DB = r"C:\Users\andre\LitigationOS\00_SYSTEM\brains\chat_intelligence_brain.db"
DEFAULT_MANIFEST = r"C:\Users\andre\LitigationOS\temp\_unique_manifest.json"
BATCH_SIZE = 5000
PROGRESS_INTERVAL = 100
MAX_TREE_NODES = 50000  # Safety limit for conversation tree traversal
SOURCE_PLATFORM = "chatgpt"
EXTRACTION_METHOD = "apex_chat_extractor_v1"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MEEK Lane Detection — Compiled Regex Patterns
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LANE_PATTERNS: dict[str, re.Pattern] = {
    "E": re.compile(
        r"McNeill|judicial\s*misconduct|JTC|judicial\s*tenure|"
        r"disqualif|recus[ae]l|bias\b|ex\s*parte|hostile\s*record|"
        r"abuse\s*of\s*discretion|MCR\s*2\.003",
        re.IGNORECASE,
    ),
    "D": re.compile(
        r"\bPPO\b|protection\s*order|personal\s*protection|"
        r"stalking|no[- ]?contact|restraining\s*order|"
        r"harassment\s*order|MCL\s*600\.2950",
        re.IGNORECASE,
    ),
    "F": re.compile(
        r"\bCOA\b|Court\s*of\s*Appeals|MSC\b|Supreme\s*Court|"
        r"366810|appellat[ei]|leave\s*to\s*appeal|"
        r"application\s*for\s*leave|peremptory\s*reversal|"
        r"MCR\s*7\.\d{3}",
        re.IGNORECASE,
    ),
    "A": re.compile(
        r"custody|parenting\s*time|best\s*interest|FOC\b|"
        r"L\.?D\.?W\.?|visitation|child\s*support|"
        r"2024-001507-DC|2023-5907-PP|"
        r"friend\s*of\s*the\s*court|Pamela\s*Rusco|"
        r"parental\s*alienat|withholding\s*parent|"
        r"MCL\s*722\.23|best\s*interest\s*factor",
        re.IGNORECASE,
    ),
    "B": re.compile(
        r"Shady\s*Oaks|eviction|mobile\s*home|Cricklewood|"
        r"1977\s*Whitehall|manufactured\s*housing|"
        r"2025-002760-CZ|lot\s*17|trailer\s*park|"
        r"sewage|water\s*shutoff|habitability|"
        r"title\s*interfere|property\s*remov",
        re.IGNORECASE,
    ),
}

# Priority order for detection: E → D → F → A → B (then C if 2+ match)
LANE_PRIORITY = ["E", "D", "F", "A", "B"]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Date Extraction Pattern
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DATE_PATTERN = re.compile(
    r"\b(?:"
    r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"            # MM/DD/YYYY or MM-DD-YY
    r"|(?:January|February|March|April|May|June"
    r"|July|August|September|October|November"
    r"|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug"
    r"|Sep|Oct|Nov|Dec)\.?\s+\d{1,2},?\s+\d{4}" # Month DD, YYYY
    r"|\d{4}-\d{2}-\d{2}"                        # ISO 8601
    r")\b",
    re.IGNORECASE,
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Legal Relevance Keywords
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RE_LEGAL_TERMS = re.compile(
    r"\bMCR\b|\bMCL\b|statute|motion|order\b|court\b|"
    r"filing|hearing|judgment|petition|brief|affidavit|"
    r"complaint|injunction|subpoena|contempt",
    re.IGNORECASE,
)
RE_CASE_NUMBERS = re.compile(
    r"\b\d{4}-\d{5,6}-[A-Z]{2}\b|366810|\b20\d{2}-\d{3,6}\b"
)
RE_PARTY_NAMES = re.compile(
    r"Pigors|Watson|McNeill|Barnes|Rusco|Berry",
    re.IGNORECASE,
)
RE_EVIDENCE_TERMS = re.compile(
    r"exhibit|affidavit|testimony|evidence|deposition|"
    r"declaration|sworn|notarized|certified|authentication",
    re.IGNORECASE,
)
RE_KEY_CLAIM_SENTENCE = re.compile(
    r"[^.!?]*(?:MCR|MCL|statute|motion|order|court|custody|"
    r"parenting|PPO|protection|appeal|misconduct|"
    r"violat|contempt|disqualif|recus|bias|"
    r"evidence|exhibit|affidavit|filed|ruling|"
    r"Pigors|Watson|McNeill)[^.!?]*[.!?]",
    re.IGNORECASE,
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Intelligence Extraction Functions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def detect_lanes(text: str) -> tuple[str, float]:
    """Detect MEEK case lanes from message content.
    Returns (lane_string, confidence).
    Lane C (Convergence) assigned when 2+ lanes match.
    """
    if not text:
        return ("", 0.0)

    matched = []
    for lane_id in LANE_PRIORITY:
        if LANE_PATTERNS[lane_id].search(text):
            matched.append(lane_id)

    if not matched:
        return ("", 0.0)
    if len(matched) >= 2:
        lanes_str = "C," + ",".join(matched)
        confidence = min(1.0, 0.3 * len(matched))
    else:
        lanes_str = matched[0]
        confidence = 0.5
    return (lanes_str, round(confidence, 2))


def extract_dates(text: str) -> list[str]:
    """Extract date references from text."""
    if not text:
        return []
    return DATE_PATTERN.findall(text)[:20]


def score_legal_relevance(text: str) -> float:
    """Score message for legal relevance (0.0 - 1.0)."""
    if not text:
        return 0.0
    score = 0.0
    if RE_LEGAL_TERMS.search(text):
        score += 0.3
    if RE_CASE_NUMBERS.search(text):
        score += 0.2
    if RE_PARTY_NAMES.search(text):
        score += 0.2
    if RE_EVIDENCE_TERMS.search(text):
        score += 0.2
    if DATE_PATTERN.search(text):
        score += 0.1
    return min(1.0, round(score, 2))


def extract_key_claims(text: str) -> list[str]:
    """Extract sentences containing legal keywords (max 5)."""
    if not text:
        return []
    matches = RE_KEY_CLAIM_SENTENCE.findall(text)
    seen = set()
    unique = []
    for m in matches:
        m = m.strip()
        if m and m not in seen and len(m) > 20:
            seen.add(m)
            unique.append(m)
            if len(unique) >= 5:
                break
    return unique


def extract_entities(text: str) -> dict[str, list[str]]:
    """Extract named entities from text (lightweight pattern-based)."""
    if not text:
        return {}
    entities: dict[str, list[str]] = {}

    # Party names
    parties = list({m.group() for m in RE_PARTY_NAMES.finditer(text)})
    if parties:
        entities["parties"] = parties

    # Case numbers
    cases = list({m.group() for m in RE_CASE_NUMBERS.finditer(text)})
    if cases:
        entities["case_numbers"] = cases

    # Court rules
    rules = list({m.group() for m in re.finditer(r"MCR\s*\d+\.\d+(?:\([A-Za-z0-9]+\))?", text)})
    if rules:
        entities["court_rules"] = rules

    # Statutes
    statutes = list({m.group() for m in re.finditer(r"MCL\s*\d+\.\d+[a-z]?", text)})
    if statutes:
        entities["statutes"] = statutes

    return entities


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Conversation Tree Walker
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def walk_conversation_tree(mapping: dict) -> list[dict]:
    """Walk the ChatGPT conversation tree depth-first to extract ordered messages.

    ChatGPT mapping structure:
      { UUID: { "id": UUID, "parent": UUID|null, "children": [UUID,...],
                "message": { "author": {"role": str}, "content": {"parts": [str,...]},
                             "create_time": float|null } } }
    """
    if not mapping or not isinstance(mapping, dict):
        return []

    # Find root node(s) — parent is null or sentinel "aaa..."
    roots = []
    for node_id, node in mapping.items():
        parent = node.get("parent")
        if parent is None or (isinstance(parent, str) and parent.startswith("aaa")):
            roots.append(node_id)

    if not roots:
        # Fallback: find nodes whose parent isn't in the mapping
        all_ids = set(mapping.keys())
        for node_id, node in mapping.items():
            parent = node.get("parent")
            if parent not in all_ids:
                roots.append(node_id)
                break

    if not roots:
        return []

    # BFS walk using deque for O(1) popleft (was O(n) with list.pop(0))
    from collections import deque
    messages = []
    visited = set()
    queue = deque(roots)

    while queue:
        node_id = queue.popleft()
        if node_id in visited or node_id not in mapping:
            continue
        visited.add(node_id)
        if len(visited) > MAX_TREE_NODES:
            break  # Safety limit for pathological trees

        node = mapping[node_id]
        msg = node.get("message")

        if msg and isinstance(msg, dict):
            author = msg.get("author", {})
            role = author.get("role", "unknown") if isinstance(author, dict) else "unknown"

            content_obj = msg.get("content", {})
            parts = content_obj.get("parts", []) if isinstance(content_obj, dict) else []

            # Join text parts, skip non-string parts (images, code outputs, etc.)
            text_parts = []
            for p in parts:
                if isinstance(p, str) and p.strip():
                    text_parts.append(p.strip())

            content = "\n".join(text_parts)
            create_time = msg.get("create_time")

            if content:  # Only include messages with actual content
                messages.append({
                    "role": role,
                    "content": content,
                    "create_time": create_time,
                })

        # Queue children for traversal (append to end for BFS order)
        children = node.get("children", [])
        if isinstance(children, list):
            queue.extend(children)

    return messages


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Database Layer
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def connect_db(db_path: str) -> sqlite3.Connection:
    """Open connection with APEX PRAGMAs."""
    conn = sqlite3.connect(db_path, timeout=120)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-50000")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA mmap_size=268435456")
    return conn


def ensure_schema(conn: sqlite3.Connection) -> list[str]:
    """Verify schema and add missing enrichment columns.
    Returns the list of actual column names.
    """
    existing = {r[1] for r in conn.execute("PRAGMA table_info(chat_intelligence)").fetchall()}

    # Add enrichment columns that the extractor needs but may be missing
    additions = {
        "message_index": "INTEGER",
        "legal_relevance_score": "REAL DEFAULT 0.0",
        "entities_json": "TEXT",
        "date_references": "TEXT",
        "key_claims": "TEXT",
    }
    for col_name, col_type in additions.items():
        if col_name not in existing:
            try:
                conn.execute(f"ALTER TABLE chat_intelligence ADD COLUMN {col_name} {col_type}")
                print(f"  + Added column: {col_name} ({col_type})")
            except sqlite3.OperationalError as e:
                if "duplicate column" not in str(e).lower():
                    print(f"  ! Could not add {col_name}: {e}", file=sys.stderr)

    conn.commit()

    # Return current column list
    return [r[1] for r in conn.execute("PRAGMA table_info(chat_intelligence)").fetchall()]


def log_extraction_start(conn: sqlite3.Connection, file_path: str, fingerprint: str) -> int:
    """Log extraction start in extraction_log. Returns log id."""
    cur = conn.execute(
        "INSERT INTO extraction_log (file_path, file_fingerprint, status, started_at) "
        "VALUES (?, ?, 'running', datetime('now'))",
        (file_path, fingerprint),
    )
    conn.commit()
    return cur.lastrowid


def log_extraction_complete(
    conn: sqlite3.Connection,
    log_id: int,
    msg_count: int,
    status: str = "complete",
    error: str = None,
):
    """Update extraction_log on completion."""
    conn.execute(
        "UPDATE extraction_log SET status=?, messages_extracted=?, "
        "completed_at=datetime('now'), error_message=? WHERE id=?",
        (status, msg_count, error, log_id),
    )
    conn.commit()


def check_already_extracted(conn: sqlite3.Connection, file_path: str) -> bool:
    """Check if file was already successfully extracted."""
    row = conn.execute(
        "SELECT id FROM extraction_log WHERE file_path=? AND status='complete'",
        (file_path,),
    ).fetchone()
    return row is not None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Core Streaming Processor
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Column order for INSERT — matches actual DB schema + enrichment columns
INSERT_SQL = (
    "INSERT OR IGNORE INTO chat_intelligence "
    "(source_platform, conversation_id, conversation_title, topic_cluster, "
    "content, content_type, is_user_truth, lanes, lane_confidence, "
    "timestamp_utc, file_source, extraction_method, "
    "message_index, legal_relevance_score, entities_json, "
    "date_references, key_claims) "
    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
)


def compute_file_fingerprint(file_path: str) -> str:
    """Compute SHA-256 of first 64KB for fast fingerprinting."""
    h = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            h.update(f.read(65536))
    except OSError:
        h.update(file_path.encode())
    return h.hexdigest()


def format_timestamp(epoch) -> Optional[str]:
    """Convert Unix epoch to ISO 8601 UTC string.
    Handles float, int, and Decimal (returned by ijson).
    """
    if epoch is None:
        return None
    try:
        epoch_f = float(epoch)
    except (TypeError, ValueError):
        return None
    if epoch_f <= 0:
        return None
    try:
        dt = datetime.fromtimestamp(epoch_f, tz=timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except (OSError, ValueError, OverflowError):
        return None


def infer_topic(title: str, messages: list[dict]) -> str:
    """Infer a topic cluster from conversation title and content."""
    text = (title or "").lower()
    # Sample a few messages for topic hints
    for msg in messages[:5]:
        text += " " + (msg.get("content", "") or "")[:200].lower()

    if any(w in text for w in ["custody", "parenting", "child", "foc", "best interest"]):
        return "family_law"
    if any(w in text for w in ["motion", "brief", "filing", "court", "hearing"]):
        return "court_filings"
    if any(w in text for w in ["evidence", "exhibit", "affidavit", "testimony"]):
        return "evidence"
    if any(w in text for w in ["appeal", "coa", "msc", "appellate"]):
        return "appellate"
    if any(w in text for w in ["ppo", "protection order", "stalking"]):
        return "protection_orders"
    if any(w in text for w in ["mcneill", "misconduct", "jtc", "bias", "recusal"]):
        return "judicial_misconduct"
    if any(w in text for w in ["shady oaks", "eviction", "mobile home", "housing"]):
        return "housing"
    if any(w in text for w in ["code", "python", "script", "sql", "database"]):
        return "technical"
    if any(w in text for w in ["strategy", "plan", "next step", "approach"]):
        return "strategy"
    return "general"


def process_file(
    file_path: str,
    conn: sqlite3.Connection,
    dry_run: bool = False,
) -> dict:
    """Stream-process a single ChatGPT conversations.json file.

    Returns stats dict: {conversations, messages, errors, elapsed}.
    """
    file_path = os.path.abspath(file_path)
    file_name = os.path.basename(file_path)
    fingerprint = compute_file_fingerprint(file_path)

    # Skip already-extracted files
    if not dry_run and check_already_extracted(conn, file_path):
        print(f"  SKIP (already extracted): {file_name}")
        return {"conversations": 0, "messages": 0, "errors": 0, "elapsed": 0, "skipped": True}

    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    print(f"\n{'━' * 70}")
    print(f"  Processing: {file_name}")
    print(f"  Size: {file_size_mb:.1f} MB | Fingerprint: {fingerprint[:16]}...")
    print(f"{'━' * 70}")

    stats = {"conversations": 0, "messages": 0, "errors": 0, "elapsed": 0, "skipped": False}
    batch: list[tuple] = []
    log_id = None

    if not dry_run:
        log_id = log_extraction_start(conn, file_path, fingerprint)

    # Pre-load already-extracted conversation IDs for resume capability
    existing_conv_ids = set()
    if not dry_run:
        try:
            rows = conn.execute(
                "SELECT DISTINCT conversation_id FROM chat_intelligence WHERE file_source = ?",
                (file_path,),
            ).fetchall()
            existing_conv_ids = {r[0] for r in rows}
            if existing_conv_ids:
                print(f"  Resume mode: {len(existing_conv_ids):,} conversations already extracted, will skip them")
        except Exception:
            pass

    start_time = time.time()

    try:
        with open(file_path, "rb") as f:
            # Stream each conversation object from the top-level array
            for conv_idx, conversation in enumerate(ijson.items(f, "item")):
                try:
                    stats["conversations"] += 1
                    conv_id = conversation.get("id") or conversation.get("title", f"conv_{conv_idx}")
                    title = conversation.get("title") or ""

                    # Skip already-extracted conversations (resume support)
                    if str(conv_id) in existing_conv_ids:
                        continue

                    mapping = conversation.get("mapping") or {}
                    conv_create = conversation.get("create_time")

                    # Walk conversation tree to get ordered messages
                    messages = walk_conversation_tree(mapping)

                    if not messages:
                        continue

                    topic = infer_topic(title, messages)

                    for msg_idx, msg in enumerate(messages):
                        content = msg["content"]
                        role = msg["role"]
                        create_time = msg.get("create_time") or conv_create

                        # Intelligence extraction
                        lanes_str, lane_conf = detect_lanes(content)
                        relevance = score_legal_relevance(content)
                        dates = extract_dates(content)
                        entities = extract_entities(content)
                        claims = extract_key_claims(content)

                        # If lane detection found something, boost confidence with relevance
                        if lanes_str:
                            lane_conf = round(max(lane_conf, relevance), 2)

                        is_user_truth = 1 if role == "user" else 0
                        timestamp = format_timestamp(create_time)

                        row = (
                            SOURCE_PLATFORM,        # source_platform
                            str(conv_id),           # conversation_id
                            title[:500],            # conversation_title
                            topic,                  # topic_cluster
                            content,                # content
                            role,                   # content_type (user/assistant/system/tool)
                            is_user_truth,          # is_user_truth
                            lanes_str or None,      # lanes
                            lane_conf or None,      # lane_confidence
                            timestamp,              # timestamp_utc
                            file_path,              # file_source
                            EXTRACTION_METHOD,      # extraction_method
                            msg_idx,                # message_index
                            relevance,              # legal_relevance_score
                            json.dumps(entities) if entities else None,  # entities_json
                            json.dumps(dates) if dates else None,       # date_references
                            json.dumps(claims) if claims else None,     # key_claims
                        )

                        batch.append(row)
                        stats["messages"] += 1

                        # Batch insert every BATCH_SIZE rows
                        if len(batch) >= BATCH_SIZE and not dry_run:
                            conn.executemany(INSERT_SQL, batch)
                            conn.commit()
                            batch.clear()

                except Exception as e:
                    stats["errors"] += 1
                    print(
                        f"  ! Error in conversation {conv_idx} of {file_name}: "
                        f"{type(e).__name__}: {e}",
                        file=sys.stderr,
                    )
                    continue

                # Progress reporting
                if stats["conversations"] % PROGRESS_INTERVAL == 0:
                    elapsed = time.time() - start_time
                    rate = stats["conversations"] / elapsed if elapsed > 0 else 0
                    print(
                        f"  ... {stats['conversations']:,} conversations | "
                        f"{stats['messages']:,} messages | "
                        f"{elapsed:.1f}s | {rate:.1f} conv/s"
                    )

    except ijson.IncompleteJSONError as e:
        print(f"  ! Truncated JSON in {file_name}: {e}", file=sys.stderr)
        stats["errors"] += 1
    except Exception as e:
        print(f"  ! Fatal error processing {file_name}: {type(e).__name__}: {e}", file=sys.stderr)
        stats["errors"] += 1

    # Flush remaining batch
    if batch and not dry_run:
        conn.executemany(INSERT_SQL, batch)
        conn.commit()
        batch.clear()

    elapsed = time.time() - start_time
    stats["elapsed"] = round(elapsed, 2)

    # Update extraction log
    if log_id is not None:
        status = "complete" if stats["errors"] == 0 else "complete_with_errors"
        log_extraction_complete(conn, log_id, stats["messages"], status)

    print(
        f"  ✓ Done: {stats['conversations']:,} conversations, "
        f"{stats['messages']:,} messages, "
        f"{stats['errors']} errors, "
        f"{elapsed:.1f}s"
    )
    return stats


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Manifest Loader
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def load_manifest(manifest_path: str) -> list[str]:
    """Load ChatGPT JSON file paths from manifest."""
    if not os.path.exists(manifest_path):
        print(f"FATAL: Manifest not found: {manifest_path}", file=sys.stderr)
        sys.exit(1)

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    files = []
    categories = manifest.get("categories", {})
    for category_key in ("chatgpt_json", "json"):
        entries = categories.get(category_key, [])
        for entry in entries:
            path = entry.get("path", "") if isinstance(entry, dict) else str(entry)
            # Normalize doubled backslashes from JSON
            path = path.replace("\\\\", "\\")
            if path and os.path.exists(path):
                files.append(path)
            elif path:
                print(f"  WARN: File not found, skipping: {path}", file=sys.stderr)

    return files


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Main
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def main():
    parser = argparse.ArgumentParser(
        description="APEX Chat Intelligence Extraction Engine — "
        "streams ChatGPT JSON into chat_intelligence_brain.db",
    )
    parser.add_argument(
        "--file", type=str, help="Process a single ChatGPT conversations.json file"
    )
    parser.add_argument(
        "--manifest",
        type=str,
        default=None,
        help=f"Process all chatgpt_json files from manifest (default: {DEFAULT_MANIFEST})",
    )
    parser.add_argument(
        "--db", type=str, default=DEFAULT_DB, help=f"SQLite database path (default: {DEFAULT_DB})"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Count conversations without inserting into database",
    )
    args = parser.parse_args()

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║    APEX Chat Intelligence Extraction Engine v1.0           ║")
    print("║    LitigationOS — Streaming O(1) Memory Parser             ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    # Determine files to process
    files_to_process = []
    if args.file:
        if not os.path.exists(args.file):
            print(f"FATAL: File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        files_to_process.append(os.path.abspath(args.file))
    else:
        manifest_path = args.manifest or DEFAULT_MANIFEST
        print(f"  Loading manifest: {manifest_path}")
        files_to_process = load_manifest(manifest_path)

    if not files_to_process:
        print("  No files to process. Use --file or --manifest.", file=sys.stderr)
        sys.exit(1)

    total_size = sum(os.path.getsize(f) for f in files_to_process) / (1024 * 1024)
    print(f"  Files queued: {len(files_to_process)}")
    print(f"  Total size:   {total_size:.1f} MB")
    print(f"  Database:     {args.db}")
    print(f"  Dry run:      {args.dry_run}")
    print()

    # Connect and prepare DB
    conn = connect_db(args.db)
    columns = ensure_schema(conn)
    print(f"  Schema verified: {len(columns)} columns in chat_intelligence")
    print(f"  Columns: {', '.join(columns)}")
    print()

    # Process each file
    grand_stats = {"conversations": 0, "messages": 0, "errors": 0, "files": 0, "skipped": 0}
    grand_start = time.time()

    for file_path in files_to_process:
        result = process_file(file_path, conn, dry_run=args.dry_run)
        if result.get("skipped"):
            grand_stats["skipped"] += 1
            continue
        grand_stats["files"] += 1
        grand_stats["conversations"] += result["conversations"]
        grand_stats["messages"] += result["messages"]
        grand_stats["errors"] += result["errors"]

    grand_elapsed = time.time() - grand_start

    # Final summary
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                   EXTRACTION COMPLETE                       ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print(f"║  Files processed: {grand_stats['files']:>6}  (skipped: {grand_stats['skipped']})         ║")
    print(f"║  Conversations:   {grand_stats['conversations']:>6,}                              ║")
    print(f"║  Messages stored: {grand_stats['messages']:>6,}                              ║")
    print(f"║  Errors:          {grand_stats['errors']:>6}                              ║")
    print(f"║  Total time:      {grand_elapsed:>6.1f}s                             ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    # Verify final row count
    if not args.dry_run:
        total_rows = conn.execute("SELECT COUNT(*) FROM chat_intelligence").fetchone()[0]
        print(f"\n  DB total rows: {total_rows:,}")

    conn.close()
    return 0 if grand_stats["errors"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
