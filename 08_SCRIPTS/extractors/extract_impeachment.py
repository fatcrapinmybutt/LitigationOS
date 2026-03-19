#!/usr/bin/env python3
"""
extract_impeachment.py — Impeachment Extraction Engine
Scans evidence_quotes and chatgpt_conversations for NEW impeachment material.
Cross-references against existing impeachment_items and contradiction_map.

Usage: python extract_impeachment.py [--dry-run] [--verbose]
"""

import sqlite3
import hashlib
import re
import sys
import os
from datetime import datetime
from collections import defaultdict

DB_PATH = r"C:\Users\andre\litigation_context.db"

# Litigation-relevant keywords for scanning chatgpt_conversations
LITIGATION_KEYWORDS = [
    "custody", "parenting time", "visitation", "lincoln",
    "tiffany", "watson", "pigors", "mcneill",
    "court", "judge", "hearing", "order", "motion",
    "ppo", "protection order", "ex parte",
    "friend of court", "foc", "guardian",
    "mental health", "assessment", "evaluation",
    "anger", "abuse", "threat", "violent", "harass",
    "lied", "lying", "false", "never said",
    "contradict", "inconsistent", "changed",
    "alienat", "withhold", "denied access", "kept from",
    "supervised", "suspend", "emergency",
]

# Impeachment detection patterns
DATE_PATTERN = re.compile(
    r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2}|'
    r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s*\d{2,4})\b',
    re.IGNORECASE
)

CONTRADICTION_PHRASES = [
    r'\bnever\b.*\b(?:did|said|told|went|had)\b',
    r'\balways\b.*\b(?:did|said|told|went|had)\b',
    r'\bdidn[\'\u2019]t\b',
    r'\bnot true\b',
    r'\bthat[\'\u2019]s (?:a )?lie\b',
    r'\bfalse\b',
    r'\bI (?:never|always|didn[\'\u2019]t)\b',
    r'\bhe (?:never|always|didn[\'\u2019]t)\b',
    r'\bshe (?:never|always|didn[\'\u2019]t)\b',
    r'\bcontrary to\b',
    r'\bdespite (?:the|his|her|my)\b',
    r'\binconsistent\b',
    r'\bchanged (?:his|her|the) (?:story|statement|testimony)\b',
]

COMPILED_CONTRADICTION_PATTERNS = [re.compile(p, re.IGNORECASE) for p in CONTRADICTION_PHRASES]


def connect_db():
    """Connect to litigation_context.db with retry."""
    for attempt in range(3):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=30)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=5000")
            return conn
        except sqlite3.Error as e:
            if attempt < 2:
                import time
                time.sleep(2 ** attempt)
            else:
                raise RuntimeError(f"Failed to connect to DB after 3 attempts: {e}")


def get_existing_impeachment_hashes(conn):
    """Get hashes of existing impeachment items to avoid duplicates."""
    cur = conn.execute("SELECT statement FROM impeachment_items")
    hashes = set()
    for row in cur:
        h = hashlib.md5(row["statement"].encode("utf-8", errors="replace")).hexdigest()
        hashes.add(h)
    return hashes


def get_existing_quote_ids_in_impeachment(conn):
    """Get evidence_quote IDs already cross-referenced in impeachment_items."""
    cur = conn.execute(
        "SELECT DISTINCT transcript_doc_id FROM impeachment_items WHERE transcript_doc_id IS NOT NULL"
    )
    return {row["transcript_doc_id"] for row in cur}


def get_unprocessed_evidence_quotes(conn, existing_doc_ids):
    """Get evidence_quotes not yet in impeachment_items."""
    cur = conn.execute("SELECT * FROM evidence_quotes ORDER BY id")
    quotes = []
    for row in cur:
        quotes.append(dict(row))
    return quotes


def get_contradiction_map_texts(conn):
    """Load contradiction_map for cross-reference."""
    cur = conn.execute("SELECT source_a_text, source_b_text, contradiction_type, severity FROM contradiction_map")
    texts = []
    for row in cur:
        texts.append(dict(row))
    return texts


def get_impeachment_statements(conn):
    """Load existing impeachment statements for cross-reference."""
    cur = conn.execute("SELECT speaker, statement, contradicting_text, item_type FROM impeachment_items")
    items = []
    for row in cur:
        items.append(dict(row))
    return items


def extract_dates(text):
    """Extract date references from text."""
    if not text:
        return []
    return DATE_PATTERN.findall(text)


def detect_contradiction_signals(text):
    """Check if text contains contradiction/impeachment signals."""
    if not text:
        return []
    signals = []
    for pattern in COMPILED_CONTRADICTION_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            signals.extend(matches)
    return signals


def normalize_text(text):
    """Normalize whitespace for comparison."""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip().lower()


def text_similarity(a, b):
    """Simple word-overlap similarity score."""
    if not a or not b:
        return 0.0
    words_a = set(normalize_text(a).split())
    words_b = set(normalize_text(b).split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)


def find_date_contradictions(quote, all_quotes):
    """Find quotes with same speaker but contradictory dates for same events."""
    contradictions = []
    q_dates = extract_dates(quote.get("quote_text", ""))
    q_speaker = quote.get("speaker")
    if not q_dates or not q_speaker:
        return contradictions

    q_text_norm = normalize_text(quote.get("quote_text", ""))

    for other in all_quotes:
        if other["id"] == quote["id"]:
            continue
        if other.get("speaker") != q_speaker:
            continue
        o_dates = extract_dates(other.get("quote_text", ""))
        if not o_dates:
            continue
        # Same speaker, overlapping topic (>20% word similarity), different dates
        sim = text_similarity(quote.get("quote_text", ""), other.get("quote_text", ""))
        if sim > 0.2:
            q_date_set = set(q_dates)
            o_date_set = set(o_dates)
            if q_date_set != o_date_set and len(q_date_set & o_date_set) == 0:
                contradictions.append({
                    "type": "TIMELINE_CONTRADICTION",
                    "other_quote": other,
                    "detail": f"Date mismatch: {q_dates} vs {o_dates}",
                })
    return contradictions


def find_statement_contradictions(quote, existing_impeachment, contradiction_texts):
    """Find contradictions between a quote and existing impeachment/contradiction data."""
    contradictions = []
    q_text = quote.get("quote_text", "")
    q_text_norm = normalize_text(q_text)
    q_speaker = quote.get("speaker")

    if not q_text or len(q_text_norm) < 20:
        return contradictions

    # Check against contradiction_map
    for cm in contradiction_texts:
        a_text = normalize_text(cm.get("source_a_text", ""))
        b_text = normalize_text(cm.get("source_b_text", ""))

        sim_a = text_similarity(q_text, cm.get("source_a_text", ""))
        sim_b = text_similarity(q_text, cm.get("source_b_text", ""))

        if sim_a > 0.3 or sim_b > 0.3:
            contradicting = cm.get("source_b_text") if sim_a > sim_b else cm.get("source_a_text")
            contradictions.append({
                "type": "CROSS_SPEAKER_CONTRADICTION",
                "contradicting_text": contradicting,
                "detail": f"Matches contradiction_map ({cm.get('contradiction_type', 'UNKNOWN')})",
                "severity": cm.get("severity", "MEDIUM"),
            })

    # Check for self-contradiction signals in the text
    signals = detect_contradiction_signals(q_text)
    if signals:
        contradictions.append({
            "type": "PRIOR_INCONSISTENT_STATEMENT",
            "contradicting_text": "; ".join(signals[:3]),
            "detail": f"Contains contradiction signals: {signals[:3]}",
            "severity": "MEDIUM",
        })

    return contradictions


def scan_chatgpt_for_litigation(conn, existing_hashes, verbose=False):
    """Scan chatgpt_conversations for litigation-relevant impeachment material."""
    new_items = []

    # Build keyword search: find messages with litigation-relevant content
    keyword_conditions = " OR ".join(
        "message_text LIKE '%" + kw.replace("'", "''") + "%'" for kw in LITIGATION_KEYWORDS
    )

    query = f"""
        SELECT id, title, message_role, message_text, conversation_id, message_index, created_at
        FROM chatgpt_conversations
        WHERE message_role = 'user'
        AND ({keyword_conditions})
        ORDER BY created_at
    """

    cur = conn.execute(query)
    rows = cur.fetchall()

    if verbose:
        print(f"  [chatgpt] Found {len(rows)} litigation-relevant user messages")

    for row in rows:
        msg = dict(row)
        text = msg.get("message_text", "")
        if not text or len(text) < 30:
            continue

        stmt_hash = hashlib.md5(text[:500].encode("utf-8", errors="replace")).hexdigest()
        if stmt_hash in existing_hashes:
            continue

        signals = detect_contradiction_signals(text)
        dates = extract_dates(text)

        # Look for statements about the case that could be impeachment material
        has_party_ref = any(
            kw in text.lower() for kw in ["tiffany", "watson", "mcneill", "judge", "court"]
        )
        has_denial = any(
            kw in text.lower() for kw in ["never", "didn't", "false", "lied", "not true"]
        )
        has_claim = any(
            kw in text.lower() for kw in [
                "custody", "parenting", "ppo", "order", "hearing",
                "alienat", "withhold", "denied", "suspend"
            ]
        )

        # Only extract if the message contains substantive litigation claims
        if has_party_ref and (has_denial or signals) and has_claim:
            # Determine the speaker context
            speaker = "PIGORS"  # ChatGPT user messages are from Andrew

            item_type = "PRIOR_INCONSISTENT_STATEMENT"
            if signals:
                item_type = "CREDIBILITY_FORENSIC"
            if dates and len(dates) > 1:
                item_type = "TIMELINE_CONTRADICTION"

            severity = "MEDIUM"
            if has_denial and has_party_ref:
                severity = "HIGH"

            legal_hook = None
            if "custody" in text.lower() or "parenting" in text.lower():
                legal_hook = "MCL 722.23 (best interest factors)"
            elif "ppo" in text.lower() or "protection" in text.lower():
                legal_hook = "MCL 600.2950 (PPO)"
            elif "ex parte" in text.lower():
                legal_hook = "MCR 2.003(C)(1) (ex parte)"
            elif "hearing" in text.lower():
                legal_hook = "MCR 2.119 (motion practice)"

            new_items.append({
                "item_type": item_type,
                "speaker": speaker,
                "transcript_doc_id": None,
                "transcript_page": None,
                "statement": text[:1000],
                "contradicting_source": f"chatgpt:{msg.get('conversation_id', '')}",
                "contradicting_doc_id": None,
                "contradicting_text": f"[ChatGPT conv: {msg.get('title', 'Unknown')} | msg #{msg.get('message_index', 0)} | {msg.get('created_at', '')}]",
                "legal_hook": legal_hook,
                "severity": severity,
            })
            existing_hashes.add(stmt_hash)

    return new_items


def process_evidence_quotes(conn, existing_hashes, verbose=False):
    """Process evidence_quotes for new impeachment material."""
    new_items = []

    quotes = get_unprocessed_evidence_quotes(conn, set())
    contradiction_texts = get_contradiction_map_texts(conn)
    impeachment_stmts = get_impeachment_statements(conn)

    if verbose:
        print(f"  [evidence] Processing {len(quotes)} evidence quotes")
        print(f"  [evidence] Cross-referencing against {len(contradiction_texts)} contradiction_map entries")
        print(f"  [evidence] Cross-referencing against {len(impeachment_stmts)} impeachment_items")

    for quote in quotes:
        q_text = quote.get("quote_text", "")
        if not q_text or len(q_text) < 20:
            continue

        stmt_hash = hashlib.md5(q_text[:500].encode("utf-8", errors="replace")).hexdigest()
        if stmt_hash in existing_hashes:
            continue

        # 1. Date contradiction detection
        date_contras = find_date_contradictions(quote, quotes)

        # 2. Statement contradiction detection
        stmt_contras = find_statement_contradictions(quote, impeachment_stmts, contradiction_texts)

        # 3. Self-contained contradiction signals
        signals = detect_contradiction_signals(q_text)

        all_contras = date_contras + stmt_contras

        if all_contras:
            for contra in all_contras:
                c_type = contra.get("type", "CROSS_SPEAKER_CONTRADICTION")
                severity = contra.get("severity", "MEDIUM")
                c_text = contra.get("contradicting_text", contra.get("detail", ""))

                legal_hook = None
                if quote.get("evidence_category") == "TRANSCRIPT":
                    legal_hook = "MRE 801(d)(1) (prior inconsistent statement)"
                elif quote.get("evidence_category") == "EX_PARTE_ORDER":
                    legal_hook = "MCR 2.003(C)(1) (ex parte communication)"
                elif quote.get("evidence_category") == "PPO":
                    legal_hook = "MCL 600.2950 (PPO)"
                elif quote.get("evidence_category") == "JUDGE_ORDER":
                    legal_hook = "MCR 2.517 (findings of fact)"
                elif quote.get("evidence_category") == "CUSTODY_ORDER":
                    legal_hook = "MCL 722.27 (custody modification)"

                new_items.append({
                    "item_type": c_type,
                    "speaker": quote.get("speaker"),
                    "transcript_doc_id": quote.get("document_id"),
                    "transcript_page": quote.get("page_number"),
                    "statement": q_text[:1000],
                    "contradicting_source": quote.get("evidence_category"),
                    "contradicting_doc_id": quote.get("document_id"),
                    "contradicting_text": str(c_text)[:1000] if c_text else None,
                    "legal_hook": legal_hook,
                    "severity": severity,
                })
                existing_hashes.add(stmt_hash)
                break  # One impeachment item per quote to avoid spam

        elif signals and quote.get("speaker"):
            # Quote has contradiction signals but no direct match — still noteworthy
            legal_hook = "MRE 613 (prior inconsistent statements)" if quote.get("evidence_category") == "TRANSCRIPT" else None
            new_items.append({
                "item_type": "PRIOR_INCONSISTENT_STATEMENT",
                "speaker": quote.get("speaker"),
                "transcript_doc_id": quote.get("document_id"),
                "transcript_page": quote.get("page_number"),
                "statement": q_text[:1000],
                "contradicting_source": quote.get("evidence_category"),
                "contradicting_doc_id": None,
                "contradicting_text": f"Contradiction signals detected: {'; '.join(signals[:3])}",
                "legal_hook": legal_hook,
                "severity": "LOW",
            })
            existing_hashes.add(stmt_hash)

    return new_items


def insert_impeachment_items(conn, items, dry_run=False):
    """Insert new impeachment items into the database."""
    if dry_run:
        return len(items)

    inserted = 0
    for item in items:
        try:
            conn.execute(
                """INSERT INTO impeachment_items 
                   (item_type, speaker, transcript_doc_id, transcript_page, 
                    statement, contradicting_source, contradicting_doc_id,
                    contradicting_text, legal_hook, severity)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    item["item_type"],
                    item["speaker"],
                    item["transcript_doc_id"],
                    item["transcript_page"],
                    item["statement"],
                    item["contradicting_source"],
                    item["contradicting_doc_id"],
                    item["contradicting_text"],
                    item["legal_hook"],
                    item["severity"],
                ),
            )
            inserted += 1
        except sqlite3.IntegrityError:
            continue
        except sqlite3.Error as e:
            print(f"  [ERROR] Failed to insert item: {e}", file=sys.stderr)

    conn.commit()
    return inserted


def generate_report(evidence_items, chatgpt_items):
    """Generate summary report of findings."""
    all_items = evidence_items + chatgpt_items
    if not all_items:
        return "No new impeachment items found."

    # Category breakdown
    categories = defaultdict(int)
    for item in all_items:
        categories[item["item_type"]] += 1

    # Severity breakdown
    severities = defaultdict(int)
    for item in all_items:
        severities[item.get("severity", "MEDIUM")] += 1

    # Speaker breakdown (targets)
    speakers = defaultdict(int)
    for item in all_items:
        s = item.get("speaker") or "UNKNOWN"
        speakers[s] += 1

    report = []
    report.append("=" * 60)
    report.append("IMPEACHMENT EXTRACTION REPORT")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 60)
    report.append("")
    report.append(f"TOTAL NEW ITEMS: {len(all_items)}")
    report.append(f"  From evidence_quotes: {len(evidence_items)}")
    report.append(f"  From chatgpt_conversations: {len(chatgpt_items)}")
    report.append("")

    report.append("CATEGORIES:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        report.append(f"  {cat}: {count}")
    report.append("")

    report.append("SEVERITY:")
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        if sev in severities:
            report.append(f"  {sev}: {severities[sev]}")
    report.append("")

    report.append("TOP TARGETS:")
    for speaker, count in sorted(speakers.items(), key=lambda x: -x[1]):
        report.append(f"  {speaker}: {count}")
    report.append("")

    # Show top 5 highest-severity items
    critical_items = [i for i in all_items if i.get("severity") in ("CRITICAL", "HIGH")]
    if critical_items:
        report.append("TOP HIGH-SEVERITY FINDINGS:")
        for i, item in enumerate(critical_items[:5], 1):
            report.append(f"  [{i}] {item['item_type']} ({item.get('severity', 'N/A')})")
            report.append(f"      Speaker: {item.get('speaker', 'N/A')}")
            stmt = (item.get("statement", "") or "")[:120]
            report.append(f"      Statement: {stmt}...")
            report.append(f"      Legal Hook: {item.get('legal_hook', 'N/A')}")
            report.append("")

    report.append("=" * 60)
    return "\n".join(report)


def main():
    dry_run = "--dry-run" in sys.argv
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    print("=" * 60)
    print("LitigationOS — Impeachment Extraction Engine")
    print(f"Database: {DB_PATH}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print("=" * 60)
    print()

    # Verify DB exists
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}", file=sys.stderr)
        sys.exit(1)

    conn = connect_db()
    print("[1/5] Connected to database")

    # Get existing hashes to avoid duplicates
    existing_hashes = get_existing_impeachment_hashes(conn)
    print(f"[2/5] Loaded {len(existing_hashes)} existing impeachment item hashes")

    # Process evidence_quotes
    print("[3/5] Scanning evidence_quotes for new impeachment material...")
    evidence_items = process_evidence_quotes(conn, existing_hashes, verbose)
    print(f"       Found {len(evidence_items)} new items from evidence_quotes")

    # Scan chatgpt_conversations
    print("[4/5] Scanning chatgpt_conversations (139,693 messages) for litigation-relevant statements...")
    chatgpt_items = scan_chatgpt_for_litigation(conn, existing_hashes, verbose)
    print(f"       Found {len(chatgpt_items)} new items from chatgpt_conversations")

    # Insert new items
    total_new = evidence_items + chatgpt_items
    if total_new:
        print(f"[5/5] {'Would insert' if dry_run else 'Inserting'} {len(total_new)} new impeachment items...")
        inserted = insert_impeachment_items(conn, total_new, dry_run)
        print(f"       {'Would insert' if dry_run else 'Inserted'}: {inserted}")
    else:
        print("[5/5] No new impeachment items to insert.")

    # Generate report
    print()
    report = generate_report(evidence_items, chatgpt_items)
    print(report)

    # Final count
    cur = conn.execute("SELECT COUNT(*) FROM impeachment_items")
    total = cur.fetchone()[0]
    print(f"\nTotal impeachment_items in DB: {total}")

    conn.close()
    return 0 if not total_new else len(total_new)


if __name__ == "__main__":
    sys.exit(main())
