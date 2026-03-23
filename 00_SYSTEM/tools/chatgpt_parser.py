#!/usr/bin/env python3
"""ChatGPT Conversation JSON Parser & DB Ingestor for LitigationOS.

Parses ChatGPT export files (conversations.json) and ingests messages
into the brain_messages table in litigation_context.db.

Usage:
    python chatgpt_parser.py PATH_TO_JSON [--db litigation_context.db] [--limit N] [--dry-run]
"""
import sys, os, io, hashlib, sqlite3, argparse, time
from decimal import Decimal
from datetime import datetime, timezone

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Litigation-relevant keyword patterns for auto-tagging
LITIGATION_KEYWORDS = {
    'custody', 'court', 'judge', 'mcneill', 'watson', 'pigors', 'parenting',
    'ppo', 'motion', 'filing', 'evidence', 'hearing', 'order', 'contempt',
    'divorce', 'child', 'visitation', 'guardian', 'attorney', 'lawyer',
    'affidavit', 'deposition', 'subpoena', 'plaintiff', 'defendant',
    'appellant', 'appellee', 'brief', 'appeal', 'appellate', 'circuit',
    'family law', 'foc', 'friend of the court', 'mcr', 'michigan',
    'shady oaks', 'norton shores', 'muskegon', 'barnes', 'rusco',
    'berry', 'recusal', 'disqualification', 'sanctions', 'perjury',
    'jtc', 'judicial', 'misconduct', 'due process', 'ex parte',
    'parenting time', 'best interest', 'protection order', 'restraining',
    'garnishment', 'support', 'alimony', 'property', 'title',
    'complaint', 'petition', 'response', 'objection', 'stipulation',
    'mediation', 'settlement', 'trial', 'testimony', 'witness',
    'exhibit', 'docket', 'case number', 'scao', 'efiling',
    'incarceration', 'jail', 'bond', 'arrest', 'police',
    'cps', 'dhhs', 'protective services', 'investigation',
    'alienation', 'interference', 'withholding', 'obstruction',
    'fraud', 'conspiracy', 'retaliation', '1983', 'civil rights',
}

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS brain_messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT,
    conversation_title TEXT,
    role TEXT,
    content TEXT,
    timestamp REAL,
    timestamp_iso TEXT,
    source_file TEXT,
    source_type TEXT DEFAULT 'chatgpt',
    lane TEXT,
    litigation_relevant INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);
"""

CREATE_INDEXES_SQL = """
CREATE INDEX IF NOT EXISTS idx_brain_role ON brain_messages(role);
CREATE INDEX IF NOT EXISTS idx_brain_conv ON brain_messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_brain_relevant ON brain_messages(litigation_relevant);
CREATE INDEX IF NOT EXISTS idx_brain_timestamp ON brain_messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_brain_source ON brain_messages(source_file);
"""


def make_id(conversation_id: str, message_id: str) -> str:
    """Generate deterministic 16-char hex ID."""
    raw = f"{conversation_id}:{message_id}"
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]


def ts_to_iso(ts) -> str:
    """Convert Unix timestamp to ISO string."""
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat()
    except (ValueError, OSError, OverflowError, TypeError):
        return None


def is_litigation_relevant(text: str) -> bool:
    """Check if message content matches litigation keywords."""
    if not text:
        return False
    lower = text.lower()
    return any(kw in lower for kw in LITIGATION_KEYWORDS)


def detect_lane(text: str) -> str:
    """Detect case lane from content."""
    if not text:
        return None
    lower = text.lower()
    if any(k in lower for k in ('appeal', 'appellate', 'coa', 'msc', '366810')):
        return 'F'
    if any(k in lower for k in ('jtc', 'judicial misconduct', 'judicial tenure')):
        return 'E'
    if any(k in lower for k in ('ppo', 'protection order', 'restraining')):
        return 'D'
    if any(k in lower for k in ('shady oaks', 'housing', 'title', 'property', 'lockout')):
        return 'B'
    if any(k in lower for k in ('custody', 'parenting', 'visitation', 'foc', 'best interest')):
        return 'A'
    return None


def setup_db(db_path: str) -> sqlite3.Connection:
    """Open DB with proper PRAGMAs and create table."""
    conn = sqlite3.connect(db_path, timeout=120)
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.executescript(CREATE_TABLE_SQL)
    conn.executescript(CREATE_INDEXES_SQL)
    conn.commit()
    return conn


def extract_messages_from_conversation(conv: dict, source_file: str):
    """Yield (row_tuple) for each valid message in a conversation."""
    conv_id = conv.get('id', '')
    conv_title = conv.get('title', '')
    create_time = conv.get('create_time')
    mapping = conv.get('mapping', {})

    for node_id, node in mapping.items():
        msg = node.get('message')
        if msg is None:
            continue

        author = msg.get('author', {})
        role = author.get('role', '')

        # Skip system messages and tool messages
        if role in ('system', 'tool', ''):
            continue

        content_obj = msg.get('content', {})
        parts = content_obj.get('parts', [])

        # Build content string from parts
        text_parts = []
        for p in parts:
            if isinstance(p, str) and p.strip():
                text_parts.append(p.strip())
            elif isinstance(p, dict):
                # Some parts are dicts (images, etc.) — skip or extract text
                if 'text' in p:
                    text_parts.append(str(p['text']).strip())

        content = '\n'.join(text_parts)
        if not content:
            continue

        msg_id = msg.get('id', node_id)
        msg_ts = msg.get('create_time', create_time)
        # ijson returns Decimal — SQLite needs float
        if isinstance(msg_ts, Decimal):
            msg_ts = float(msg_ts)
        row_id = make_id(conv_id, msg_id)
        ts_iso = ts_to_iso(msg_ts)
        relevant = 1 if is_litigation_relevant(content) else 0
        lane = detect_lane(content) if relevant else None

        yield (row_id, conv_id, conv_title, role, content,
               msg_ts, ts_iso, source_file, 'chatgpt', lane, relevant)


def parse_with_ijson(json_path: str, conn: sqlite3.Connection,
                     source_file: str, limit: int = None, dry_run: bool = False):
    """Stream-parse using ijson (memory efficient for huge files)."""
    import ijson

    batch = []
    conv_count = 0
    msg_count = 0
    relevant_count = 0
    skipped = 0
    start = time.time()

    print(f"[ijson] Streaming {json_path} ...")

    with open(json_path, 'r', encoding='utf-8') as f:
        # ijson parses array items one at a time
        for conv in ijson.items(f, 'item'):
            if limit and conv_count >= limit:
                break

            conv_count += 1
            for row in extract_messages_from_conversation(conv, source_file):
                msg_count += 1
                if row[10]:  # litigation_relevant
                    relevant_count += 1
                batch.append(row)

                if len(batch) >= 500:
                    if not dry_run:
                        _insert_batch(conn, batch)
                    batch.clear()

            if conv_count % 1000 == 0:
                elapsed = time.time() - start
                rate = conv_count / elapsed if elapsed > 0 else 0
                print(f"  [{conv_count} convos | {msg_count} msgs | "
                      f"{relevant_count} relevant | {rate:.0f} conv/s]")

    # Final batch
    if batch and not dry_run:
        _insert_batch(conn, batch)

    elapsed = time.time() - start
    return conv_count, msg_count, relevant_count, elapsed


def parse_with_json(json_path: str, conn: sqlite3.Connection,
                    source_file: str, limit: int = None, dry_run: bool = False):
    """Full-load parse using stdlib json (needs RAM >= 3x file size)."""
    import json

    print(f"[json] Loading {json_path} into memory ...")
    file_size = os.path.getsize(json_path)
    print(f"  File size: {file_size / (1024**3):.2f} GB — need ~{file_size * 3 / (1024**3):.1f} GB RAM")

    start = time.time()
    with open(json_path, 'r', encoding='utf-8') as f:
        conversations = json.load(f)

    load_time = time.time() - start
    print(f"  Loaded {len(conversations)} conversations in {load_time:.1f}s")

    batch = []
    conv_count = 0
    msg_count = 0
    relevant_count = 0

    for conv in conversations:
        if limit and conv_count >= limit:
            break

        conv_count += 1
        for row in extract_messages_from_conversation(conv, source_file):
            msg_count += 1
            if row[10]:
                relevant_count += 1
            batch.append(row)

            if len(batch) >= 500:
                if not dry_run:
                    _insert_batch(conn, batch)
                batch.clear()

        if conv_count % 1000 == 0:
            elapsed = time.time() - start
            print(f"  [{conv_count} convos | {msg_count} msgs | {relevant_count} relevant]")

    if batch and not dry_run:
        _insert_batch(conn, batch)

    elapsed = time.time() - start
    return conv_count, msg_count, relevant_count, elapsed


def _insert_batch(conn: sqlite3.Connection, batch: list):
    """Insert a batch of rows with INSERT OR IGNORE for idempotency."""
    conn.executemany(
        """INSERT OR IGNORE INTO brain_messages
           (id, conversation_id, conversation_title, role, content,
            timestamp, timestamp_iso, source_file, source_type, lane, litigation_relevant)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        batch
    )
    conn.commit()


def main():
    parser = argparse.ArgumentParser(
        description='Parse ChatGPT export JSON and ingest into litigation_context.db')
    parser.add_argument('json_path', help='Path to conversations.json')
    parser.add_argument('--db', default='litigation_context.db',
                        help='Path to SQLite database (default: litigation_context.db)')
    parser.add_argument('--limit', type=int, default=None,
                        help='Max conversations to process (for testing)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Parse but do not write to DB')
    parser.add_argument('--force-stdlib', action='store_true',
                        help='Force stdlib json instead of ijson')
    args = parser.parse_args()

    if not os.path.exists(args.json_path):
        print(f"ERROR: File not found: {args.json_path}")
        sys.exit(1)

    file_size = os.path.getsize(args.json_path)
    source_file = os.path.basename(args.json_path)

    print(f"=" * 60)
    print(f"ChatGPT Parser — LitigationOS")
    print(f"=" * 60)
    print(f"Input:    {args.json_path}")
    print(f"Size:     {file_size / (1024**2):.1f} MB ({file_size / (1024**3):.2f} GB)")
    print(f"Database: {args.db}")
    print(f"Limit:    {args.limit or 'ALL'}")
    print(f"Dry run:  {args.dry_run}")
    print()

    # Setup database
    if not args.dry_run:
        conn = setup_db(args.db)
        # Check existing count
        existing = conn.execute(
            "SELECT COUNT(*) FROM brain_messages WHERE source_file = ?",
            (source_file,)
        ).fetchone()[0]
        if existing > 0:
            print(f"NOTE: {existing} messages already ingested from {source_file}")
            print(f"      Using INSERT OR IGNORE — duplicates will be skipped.")
            print()
    else:
        conn = setup_db(':memory:')

    # Choose parser
    use_ijson = False
    if not args.force_stdlib:
        try:
            import ijson
            use_ijson = True
            print(f"Parser:   ijson (streaming — memory efficient)")
        except ImportError:
            print(f"Parser:   json (stdlib — loading entire file into RAM)")
            if file_size > 500 * 1024 * 1024:
                print(f"WARNING:  File is {file_size / (1024**3):.1f} GB. "
                      f"Consider: pip install ijson")
    else:
        print(f"Parser:   json (stdlib — forced)")

    print(f"-" * 60)

    try:
        if use_ijson:
            conv_count, msg_count, relevant_count, elapsed = parse_with_ijson(
                args.json_path, conn, source_file, args.limit, args.dry_run)
        else:
            conv_count, msg_count, relevant_count, elapsed = parse_with_json(
                args.json_path, conn, source_file, args.limit, args.dry_run)
    except KeyboardInterrupt:
        print("\n\nInterrupted! Partial results committed.")
        conn.close()
        sys.exit(130)
    except Exception as e:
        print(f"\nERROR during parsing: {e}")
        import traceback
        traceback.print_exc()
        conn.close()
        sys.exit(1)

    # Final stats
    print(f"\n{'=' * 60}")
    print(f"COMPLETE")
    print(f"{'=' * 60}")
    print(f"Conversations: {conv_count:,}")
    print(f"Messages:      {msg_count:,}")
    print(f"Relevant:      {relevant_count:,} ({100*relevant_count/max(msg_count,1):.1f}%)")
    print(f"Time:          {elapsed:.1f}s")
    print(f"Rate:          {conv_count/max(elapsed,0.1):.0f} conv/s")

    if not args.dry_run:
        total = conn.execute("SELECT COUNT(*) FROM brain_messages").fetchone()[0]
        total_relevant = conn.execute(
            "SELECT COUNT(*) FROM brain_messages WHERE litigation_relevant = 1"
        ).fetchone()[0]
        print(f"\nDB Total:      {total:,} messages")
        print(f"DB Relevant:   {total_relevant:,} messages")

        # Role breakdown
        print(f"\nRole breakdown:")
        for row in conn.execute(
            "SELECT role, COUNT(*) as cnt FROM brain_messages GROUP BY role ORDER BY cnt DESC"
        ):
            print(f"  {row[0]}: {row[1]:,}")

        # Lane breakdown for relevant messages
        print(f"\nLane breakdown (relevant only):")
        for row in conn.execute(
            """SELECT COALESCE(lane, 'unclassified') as l, COUNT(*) as cnt
               FROM brain_messages WHERE litigation_relevant = 1
               GROUP BY lane ORDER BY cnt DESC"""
        ):
            print(f"  Lane {row[0]}: {row[1]:,}")

    conn.close()
    print(f"\nDone.")


if __name__ == '__main__':
    main()
