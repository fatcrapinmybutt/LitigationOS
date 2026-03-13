#!/usr/bin/env python3
"""
harvest_to_startup.py — Deep analysis of 767 harvested legal documents.
Reads harvest_catalog.jsonl, fetches full text from I:\ texts directory,
groups by topic, and produces a comprehensive litigation analysis report.
"""

import sys
import os
import json
import re
import sqlite3
from collections import defaultdict, Counter
from datetime import datetime

# UTF-8 stdout
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', errors='replace')

# ── Paths ──────────────────────────────────────────────────────────────
JSONL_PATH = r"C:\Users\andre\LitigationOS\temp\harvest_catalog.jsonl"
TEXTS_DIR = r"I:\20260209_0430_HARVEST_000000006_FULL_SAFE\texts"
OUTPUT_PATH = r"C:\Users\andre\LitigationOS\temp\harvest_deep_analysis.txt"
DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

# ── Regex patterns ─────────────────────────────────────────────────────
RE_MCR = re.compile(r'MCR\s+\d+\.\d+(?:\([A-Za-z0-9]+\))?', re.IGNORECASE)
RE_MCL = re.compile(r'MCL\s+\d+\.\d+[a-z]?', re.IGNORECASE)
RE_DATE = re.compile(
    r'\b(?:'
    r'\d{1,2}/\d{1,2}/\d{2,4}'
    r'|\d{4}-\d{2}-\d{2}'
    r'|(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}'
    r')\b',
    re.IGNORECASE
)
RE_COURT_ORDER = re.compile(
    r'IT\s+IS\s+(?:HEREBY\s+)?ORDERED|ORDERED\s+THAT|ORDER\s+OF\s+THE\s+COURT',
    re.IGNORECASE
)
RE_AFFIDAVIT = re.compile(
    r'\baffidavit\b|\bsworn\b|\bnotarized\b|\bunder\s+oath\b|\bverification\b.*\bswear\b',
    re.IGNORECASE
)
RE_TESTIMONY = re.compile(
    r'\btestimony\b|\btestified\b|\btranscript\b|\bdeposition\b|\bhearing\b.*\brecord\b',
    re.IGNORECASE
)
RE_FINANCIAL = re.compile(
    r'\bchild\s+support\b|\$\s*\d+[\d,.]*|\bdamages\b|\bfiling\s+fee\b|\bcourt\s+costs?\b|\battorney\s+fees?\b',
    re.IGNORECASE
)
RE_EX_PARTE = re.compile(
    r'\bex\s+parte\b|\boff[- ]?the[- ]?record\b|\bprivate\s+communication\b|\bwithout\s+notice\b',
    re.IGNORECASE
)
RE_HEALTHWEST = re.compile(
    r'\bHealthWest\b|\bmental\s+health\s+assessment\b|\bpsychological\s+evaluation\b|\bmental\s+health\s+services\b',
    re.IGNORECASE
)
RE_BOND_250 = re.compile(
    r'\$\s*250\b.*\bbond\b|\bbond\b.*\$\s*250\b|\b250\s*(?:dollar)?\s*bond\b',
    re.IGNORECASE
)
RE_EMAIL_SENDER = re.compile(r'^From:\s*(.+)$', re.MULTILINE | re.IGNORECASE)
RE_EMAIL_RECIPIENT = re.compile(r'^To:\s*(.+)$', re.MULTILINE | re.IGNORECASE)
RE_EMAIL_SUBJECT = re.compile(r'^Subject:\s*(.+)$', re.MULTILINE | re.IGNORECASE)
RE_EMAIL_DATE = re.compile(r'^Date:\s*(.+)$', re.MULTILINE | re.IGNORECASE)
RE_DOLLAR_AMOUNT = re.compile(r'\$\s*[\d,]+\.?\d*')
RE_CASE_NUM = re.compile(r'\b\d{4}-\d{4,7}-[A-Z]{2}\b')


def read_file_text(file_name):
    """Read full text content of a file from the texts directory."""
    path = os.path.join(TEXTS_DIR, file_name)
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    except Exception as e:
        return f"[ERROR reading {file_name}: {e}]"


def load_existing_quotes(db_path):
    """Load existing evidence_quotes from litigation_context.db for dedup."""
    quotes = set()
    if not os.path.exists(db_path):
        return quotes
    try:
        conn = sqlite3.connect(db_path, timeout=30)
        conn.execute("PRAGMA busy_timeout=60000")
        conn.execute("PRAGMA journal_mode=WAL")
        cursor = conn.execute("SELECT quote_text FROM evidence_quotes WHERE quote_text IS NOT NULL")
        for row in cursor:
            text = row[0].strip()[:200].lower() if row[0] else ""
            if text:
                quotes.add(text)
        conn.close()
        print(f"  Loaded {len(quotes)} existing evidence quotes for dedup check.")
    except Exception as e:
        print(f"  Warning: Could not load evidence_quotes: {e}")
    return quotes


def extract_notable_quotes(text, max_quotes=5):
    """Extract notable legal quotes from text content."""
    quotes = []
    patterns = [
        (r'(?:"|")(.{40,200}?)(?:"|")', "quoted"),
        (r'(?:ORDERED|ORDER)[:\s]+(.{30,200}?)(?:\.|;|\n)', "order"),
        (r'(?:find|finding|found)[s]?\s+(?:that\s+)?(.{30,200}?)(?:\.|;|\n)', "finding"),
    ]
    for pat, qtype in patterns:
        for m in re.finditer(pat, text, re.IGNORECASE):
            q = m.group(1).strip()
            if len(q) > 30 and q not in quotes:
                quotes.append(q)
                if len(quotes) >= max_quotes:
                    return quotes
    return quotes


def main():
    start_time = datetime.now()
    print(f"═══ Harvest Deep Analysis — {start_time.strftime('%Y-%m-%d %H:%M:%S')} ═══")
    print(f"JSONL: {JSONL_PATH}")
    print(f"Texts: {TEXTS_DIR}")
    print(f"Output: {OUTPUT_PATH}")
    print()

    # ── Step 1: Load JSONL catalog ─────────────────────────────────────
    print("[1/6] Loading harvest catalog...")
    records = []
    with open(JSONL_PATH, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                records.append(rec)
            except json.JSONDecodeError as e:
                print(f"  Warning: Line {i+1} invalid JSON: {e}")
    print(f"  Loaded {len(records)} records.")

    # ── Step 2: Read ALL file contents ─────────────────────────────────
    print("[2/6] Reading full text content for all files...")
    file_contents = {}
    read_ok = 0
    read_fail = 0
    total_bytes_read = 0
    for idx, rec in enumerate(records):
        fn = rec.get("file_name", "")
        if not fn:
            read_fail += 1
            continue
        text = read_file_text(fn)
        if text and not text.startswith("[ERROR"):
            file_contents[fn] = text
            total_bytes_read += len(text.encode('utf-8', errors='replace'))
            read_ok += 1
        else:
            file_contents[fn] = text or ""
            read_fail += 1
        if (idx + 1) % 100 == 0:
            print(f"  Read {idx+1}/{len(records)} files...")
    print(f"  Successfully read: {read_ok}, Failed: {read_fail}, Total bytes: {total_bytes_read:,}")

    # ── Step 3: Group by topic ─────────────────────────────────────────
    print("[3/6] Grouping by topic...")
    topics = defaultdict(list)
    for rec in records:
        topic = rec.get("topic", "general")
        topics[topic].append(rec)
    for t in sorted(topics.keys()):
        print(f"  {t}: {len(topics[t])} files")

    # ── Step 4: Cross-cutting analysis ─────────────────────────────────
    print("[4/6] Running cross-cutting analysis on all files...")
    court_orders = []
    affidavits = []
    testimony_refs = []
    financial_docs = []
    ex_parte_docs = []
    healthwest_docs = []
    bond_250_docs = []
    email_files = []
    all_legal_authorities = Counter()
    all_dates = set()
    all_case_numbers = set()
    all_dollar_amounts = Counter()

    for rec in records:
        fn = rec.get("file_name", "")
        text = file_contents.get(fn, "")
        if not text or text.startswith("[ERROR"):
            continue

        # Court orders
        if RE_COURT_ORDER.search(text):
            matches = RE_COURT_ORDER.findall(text)
            court_orders.append((fn, rec.get("topic", ""), len(matches), text))

        # Affidavits
        if RE_AFFIDAVIT.search(text):
            matches = RE_AFFIDAVIT.findall(text)
            affidavits.append((fn, rec.get("topic", ""), len(matches), text))

        # Testimony/transcripts
        if RE_TESTIMONY.search(text):
            matches = RE_TESTIMONY.findall(text)
            testimony_refs.append((fn, rec.get("topic", ""), len(matches)))

        # Financial data
        if RE_FINANCIAL.search(text):
            amounts = RE_DOLLAR_AMOUNT.findall(text)
            financial_docs.append((fn, rec.get("topic", ""), amounts))
            for amt in amounts:
                all_dollar_amounts[amt] += 1

        # Ex parte
        if RE_EX_PARTE.search(text):
            ex_parte_docs.append((fn, rec.get("topic", ""), text))

        # HealthWest
        if RE_HEALTHWEST.search(text):
            healthwest_docs.append((fn, rec.get("topic", ""), text))

        # $250 bond
        if RE_BOND_250.search(text):
            bond_250_docs.append((fn, rec.get("topic", ""), text))

        # Legal authorities
        for m in RE_MCR.findall(text):
            all_legal_authorities[m.upper().strip()] += 1
        for m in RE_MCL.findall(text):
            all_legal_authorities[m.upper().strip()] += 1

        # Dates
        for d in RE_DATE.findall(text):
            all_dates.add(d)

        # Case numbers from JSONL + text
        for cn in rec.get("case_numbers", []):
            all_case_numbers.add(cn)
        for cn in RE_CASE_NUM.findall(text):
            all_case_numbers.add(cn)

        # Email files
        if fn.endswith('.eml.txt') or '.eml' in fn.lower():
            sender = RE_EMAIL_SENDER.search(text)
            recipient = RE_EMAIL_RECIPIENT.search(text)
            subject = RE_EMAIL_SUBJECT.search(text)
            edate = RE_EMAIL_DATE.search(text)
            email_files.append({
                "file": fn,
                "from": sender.group(1).strip() if sender else "[not found]",
                "to": recipient.group(1).strip() if recipient else "[not found]",
                "subject": subject.group(1).strip() if subject else "[not found]",
                "date": edate.group(1).strip() if edate else "[not found]",
            })

    print(f"  Court orders: {len(court_orders)}")
    print(f"  Affidavits: {len(affidavits)}")
    print(f"  Testimony/transcript refs: {len(testimony_refs)}")
    print(f"  Financial docs: {len(financial_docs)}")
    print(f"  Ex parte evidence: {len(ex_parte_docs)}")
    print(f"  HealthWest mentions: {len(healthwest_docs)}")
    print(f"  $250 bond refs: {len(bond_250_docs)}")
    print(f"  Email files: {len(email_files)}")
    print(f"  Unique legal authorities: {len(all_legal_authorities)}")
    print(f"  Unique dates: {len(all_dates)}")
    print(f"  Unique case numbers: {len(all_case_numbers)}")

    # ── Step 5: Dedup against existing DB ──────────────────────────────
    print("[5/6] Checking for NEW evidence not in litigation_context.db...")
    existing_quotes = load_existing_quotes(DB_PATH)
    new_evidence_files = []
    for rec in records:
        fn = rec.get("file_name", "")
        text = file_contents.get(fn, "")
        if not text or text.startswith("[ERROR") or len(text.strip()) < 50:
            continue
        snippet = text.strip()[:200].lower()
        if snippet not in existing_quotes:
            new_evidence_files.append((fn, rec.get("topic", ""), rec.get("total_term_hits", 0), len(text)))
    print(f"  Files with potentially NEW evidence: {len(new_evidence_files)} / {len(records)}")

    # ── Step 6: Write comprehensive report ─────────────────────────────
    print("[6/6] Writing report...")
    out_lines = []
    W = out_lines.append  # shorthand

    W("=" * 100)
    W(f"  HARVEST DEEP ANALYSIS REPORT — {len(records)} Documents")
    W(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    W(f"  Source: {JSONL_PATH}")
    W(f"  Texts: {TEXTS_DIR}")
    W("=" * 100)
    W("")

    # ── SECTION A: Per-Topic Analysis ──────────────────────────────────
    W("╔" + "═" * 98 + "╗")
    W("║  SECTION A: PER-TOPIC ANALYSIS" + " " * 67 + "║")
    W("╚" + "═" * 98 + "╝")
    W("")

    topic_order = ["custody", "housing", "PPO", "judicial_misconduct",
                   "appellate", "evidence", "financial", "general"]
    # Include any topics not in the predefined order
    for t in sorted(topics.keys()):
        if t not in topic_order:
            topic_order.append(t)

    for topic in topic_order:
        if topic not in topics:
            continue
        recs = topics[topic]
        W("─" * 100)
        W(f"  TOPIC: {topic.upper()} ({len(recs)} files)")
        W("─" * 100)
        W("")

        # Sort by total_term_hits descending
        recs_sorted = sorted(recs, key=lambda r: r.get("total_term_hits", 0), reverse=True)

        # List all files
        W(f"  {'#':<4} {'File Name':<65} {'Size':>10} {'Hits':>6}")
        W(f"  {'─'*4} {'─'*65} {'─'*10} {'─'*6}")
        total_size = 0
        total_hits = 0
        for i, rec in enumerate(recs_sorted):
            fn = rec.get("file_name", "?")
            sz = rec.get("size_bytes", 0)
            hits = rec.get("total_term_hits", 0)
            total_size += sz
            total_hits += hits
            display_fn = fn[:63] + ".." if len(fn) > 65 else fn
            W(f"  {i+1:<4} {display_fn:<65} {sz:>10,} {hits:>6}")
        W(f"  {'':4} {'TOTALS':<65} {total_size:>10,} {total_hits:>6}")
        W("")

        # Collect topic-level stats
        topic_case_nums = set()
        topic_dates = set()
        topic_parties = Counter()
        for rec in recs:
            for cn in rec.get("case_numbers", []):
                topic_case_nums.add(cn)
            for d in rec.get("dates_found", []):
                topic_dates.add(d)
            pm = rec.get("party_mentions", {})
            if isinstance(pm, dict):
                for party, count in pm.items():
                    topic_parties[party] += count

        W(f"  TOPIC SUMMARY:")
        W(f"    Unique case numbers: {', '.join(sorted(topic_case_nums)) if topic_case_nums else '(none detected)'}")
        W(f"    Unique dates found:  {len(topic_dates)}")
        if topic_dates:
            sorted_dates = sorted(topic_dates)
            display_dates = sorted_dates[:20]
            W(f"    Sample dates: {', '.join(display_dates)}")
            if len(sorted_dates) > 20:
                W(f"    ... and {len(sorted_dates) - 20} more dates")
        W(f"    Party mentions (top 10):")
        for party, cnt in topic_parties.most_common(10):
            W(f"      {party}: {cnt} mentions")
        W("")

        # Top 10 most important files — show first 2000 chars of content
        W(f"  ┌─ TOP {min(10, len(recs_sorted))} MOST IMPORTANT FILES (by legal term hits) ─┐")
        W("")
        for i, rec in enumerate(recs_sorted[:10]):
            fn = rec.get("file_name", "?")
            hits = rec.get("total_term_hits", 0)
            sz = rec.get("size_bytes", 0)
            text = file_contents.get(fn, "")

            W(f"  ┌── [{i+1}] {fn}")
            W(f"  │   Size: {sz:,} bytes | Term hits: {hits} | Topic: {topic}")
            W(f"  │   Case #s: {', '.join(rec.get('case_numbers', [])) or 'none'}")
            W(f"  │   Dates: {', '.join(rec.get('dates_found', [])[:5]) or 'none'}")

            # Term counts breakdown
            tc = rec.get("term_counts", {})
            if isinstance(tc, dict) and tc:
                top_terms = sorted(tc.items(), key=lambda x: x[1], reverse=True)[:10]
                W(f"  │   Top terms: {', '.join(f'{k}({v})' for k, v in top_terms)}")

            W(f"  │")

            # Notable quotes
            if text and not text.startswith("[ERROR"):
                quotes = extract_notable_quotes(text)
                if quotes:
                    W(f"  │   Notable quotes:")
                    for q in quotes[:3]:
                        wrapped = q[:150]
                        W(f'  │     → "{wrapped}..."' if len(q) > 150 else f'  │     → "{wrapped}"')
                W(f"  │")

            # First 2000 chars of content
            if text and not text.startswith("[ERROR"):
                preview = text[:2000]
                W(f"  │   ─── CONTENT (first 2000 chars) ───")
                for line in preview.split('\n'):
                    W(f"  │   {line.rstrip()}")
                if len(text) > 2000:
                    W(f"  │   ... [{len(text) - 2000:,} more characters]")
            else:
                W(f"  │   [Content not available: {text[:80] if text else 'empty'}]")

            W(f"  └{'─' * 95}")
            W("")
        W("")

    # ── SECTION B: Cross-Cutting Analysis ──────────────────────────────
    W("╔" + "═" * 98 + "╗")
    W("║  SECTION B: CROSS-CUTTING ANALYSIS" + " " * 63 + "║")
    W("╚" + "═" * 98 + "╝")
    W("")

    # B1: Court Orders
    W("─" * 100)
    W(f"  B1. COURT ORDERS ({len(court_orders)} files)")
    W("─" * 100)
    for fn, topic, count, text in sorted(court_orders, key=lambda x: x[2], reverse=True):
        W(f"    [{topic:>22}] {fn}")
        W(f"      Order language instances: {count}")
        # Extract order snippets
        for m in RE_COURT_ORDER.finditer(text):
            start = max(0, m.start() - 20)
            end = min(len(text), m.end() + 200)
            snippet = text[start:end].replace('\n', ' ').strip()
            W(f"      → {snippet[:200]}")
            break  # just first match per file
    W("")

    # B2: Affidavits
    W("─" * 100)
    W(f"  B2. AFFIDAVITS & SWORN STATEMENTS ({len(affidavits)} files)")
    W("─" * 100)
    for fn, topic, count, text in sorted(affidavits, key=lambda x: x[2], reverse=True):
        W(f"    [{topic:>22}] {fn}")
        # Extract key sworn statements
        for m in RE_AFFIDAVIT.finditer(text):
            start = max(0, m.start() - 30)
            end = min(len(text), m.end() + 200)
            snippet = text[start:end].replace('\n', ' ').strip()
            W(f"      → {snippet[:250]}")
            break
    W("")

    # B3: Testimony/Transcript References
    W("─" * 100)
    W(f"  B3. TESTIMONY & TRANSCRIPT REFERENCES ({len(testimony_refs)} files)")
    W("─" * 100)
    for fn, topic, count in sorted(testimony_refs, key=lambda x: x[2], reverse=True)[:50]:
        W(f"    [{topic:>22}] (×{count}) {fn}")
    W("")

    # B4: Financial Data
    W("─" * 100)
    W(f"  B4. FINANCIAL DATA ({len(financial_docs)} files)")
    W("─" * 100)
    for fn, topic, amounts in sorted(financial_docs, key=lambda x: len(x[2]), reverse=True)[:50]:
        unique_amts = sorted(set(amounts))[:10]
        W(f"    [{topic:>22}] {fn}")
        W(f"      Amounts found: {', '.join(unique_amts)}")
    W("")
    W(f"  Most common dollar amounts across all files:")
    for amt, cnt in all_dollar_amounts.most_common(25):
        W(f"    {amt}: appears {cnt} times")
    W("")

    # B5: Ex Parte Communications
    W("─" * 100)
    W(f"  B5. EX PARTE COMMUNICATIONS ({len(ex_parte_docs)} files)")
    W("─" * 100)
    if ex_parte_docs:
        for fn, topic, text in ex_parte_docs:
            W(f"    [{topic:>22}] {fn}")
            for m in RE_EX_PARTE.finditer(text):
                start = max(0, m.start() - 50)
                end = min(len(text), m.end() + 250)
                snippet = text[start:end].replace('\n', ' ').strip()
                W(f"      → {snippet[:300]}")
                break
    else:
        W("    (No ex parte evidence detected)")
    W("")

    # B6: HealthWest / Mental Health
    W("─" * 100)
    W(f"  B6. HEALTHWEST & MENTAL HEALTH ASSESSMENTS ({len(healthwest_docs)} files)")
    W("─" * 100)
    if healthwest_docs:
        for fn, topic, text in healthwest_docs:
            W(f"    [{topic:>22}] {fn}")
            for m in RE_HEALTHWEST.finditer(text):
                start = max(0, m.start() - 50)
                end = min(len(text), m.end() + 200)
                snippet = text[start:end].replace('\n', ' ').strip()
                W(f"      → {snippet[:250]}")
                break
    else:
        W("    (No HealthWest mentions detected)")
    W("")

    # B7: $250 Bond Requirement
    W("─" * 100)
    W(f"  B7. $250 BOND REQUIREMENT ({len(bond_250_docs)} files)")
    W("─" * 100)
    if bond_250_docs:
        for fn, topic, text in bond_250_docs:
            W(f"    [{topic:>22}] {fn}")
            for m in RE_BOND_250.finditer(text):
                start = max(0, m.start() - 50)
                end = min(len(text), m.end() + 200)
                snippet = text[start:end].replace('\n', ' ').strip()
                W(f"      → {snippet[:250]}")
                break
    else:
        W("    (No $250 bond references detected)")
    W("")

    # B8: New Evidence (not in DB)
    W("─" * 100)
    W(f"  B8. NEW EVIDENCE NOT IN litigation_context.db ({len(new_evidence_files)} files)")
    W("─" * 100)
    W(f"  (Files whose first 200 chars don't match any existing evidence_quotes)")
    W("")
    new_sorted = sorted(new_evidence_files, key=lambda x: x[2], reverse=True)
    for fn, topic, hits, length in new_sorted[:80]:
        W(f"    [{topic:>22}] (hits={hits}, len={length:,}) {fn}")
    if len(new_sorted) > 80:
        W(f"    ... and {len(new_sorted) - 80} more files")
    W("")

    # ── SECTION C: Summary Statistics ──────────────────────────────────
    W("╔" + "═" * 98 + "╗")
    W("║  SECTION C: SUMMARY STATISTICS" + " " * 67 + "║")
    W("╚" + "═" * 98 + "╝")
    W("")

    # C1: Legal Authorities
    W("─" * 100)
    W(f"  C1. UNIQUE LEGAL AUTHORITIES CITED ({len(all_legal_authorities)} total)")
    W("─" * 100)
    mcr_auths = {k: v for k, v in all_legal_authorities.items() if k.startswith("MCR")}
    mcl_auths = {k: v for k, v in all_legal_authorities.items() if k.startswith("MCL")}
    W(f"  Michigan Court Rules (MCR): {len(mcr_auths)}")
    for auth, cnt in sorted(mcr_auths.items(), key=lambda x: x[1], reverse=True):
        W(f"    {auth}: cited {cnt} times")
    W("")
    W(f"  Michigan Compiled Laws (MCL): {len(mcl_auths)}")
    for auth, cnt in sorted(mcl_auths.items(), key=lambda x: x[1], reverse=True):
        W(f"    {auth}: cited {cnt} times")
    W("")

    # C2: Unique Dates
    W("─" * 100)
    W(f"  C2. UNIQUE DATES REFERENCED ({len(all_dates)} total)")
    W("─" * 100)
    for d in sorted(all_dates):
        W(f"    {d}")
    W("")

    # C3: Case Numbers
    W("─" * 100)
    W(f"  C3. ALL CASE NUMBERS ({len(all_case_numbers)} unique)")
    W("─" * 100)
    for cn in sorted(all_case_numbers):
        W(f"    {cn}")
    W("")

    # C4: Email Files
    W("─" * 100)
    W(f"  C4. EMAIL FILES ({len(email_files)} found)")
    W("─" * 100)
    if email_files:
        for em in email_files:
            W(f"    File:    {em['file']}")
            W(f"    From:    {em['from']}")
            W(f"    To:      {em['to']}")
            W(f"    Subject: {em['subject']}")
            W(f"    Date:    {em['date']}")
            W("")
    else:
        W("    (No .eml.txt files found — checking for email-like content...)")
        # Check for files that might contain email headers
        email_like = []
        for rec in records:
            fn = rec.get("file_name", "")
            text = file_contents.get(fn, "")
            if text and RE_EMAIL_SENDER.search(text) and RE_EMAIL_RECIPIENT.search(text):
                sender = RE_EMAIL_SENDER.search(text)
                recipient = RE_EMAIL_RECIPIENT.search(text)
                subject = RE_EMAIL_SUBJECT.search(text)
                email_like.append({
                    "file": fn,
                    "from": sender.group(1).strip() if sender else "?",
                    "to": recipient.group(1).strip() if recipient else "?",
                    "subject": subject.group(1).strip() if subject else "?",
                })
        if email_like:
            W(f"    Found {len(email_like)} files with email headers:")
            for em in email_like[:30]:
                W(f"      {em['file']}")
                W(f"        From: {em['from']} → To: {em['to']}")
                W(f"        Subject: {em['subject']}")
                W("")
        else:
            W("    (No email-like content detected)")
    W("")

    # C5: Affidavit Key Statements
    W("─" * 100)
    W(f"  C5. AFFIDAVIT FILES — KEY SWORN STATEMENTS ({len(affidavits)} files)")
    W("─" * 100)
    for fn, topic, count, text in affidavits:
        W(f"    File: {fn} [{topic}]")
        # Try to extract the substance of the affidavit
        lines = text.split('\n')
        sworn_lines = []
        for j, line in enumerate(lines):
            if RE_AFFIDAVIT.search(line):
                # Grab context around the match
                start = max(0, j - 1)
                end = min(len(lines), j + 4)
                context = ' '.join(l.strip() for l in lines[start:end] if l.strip())
                sworn_lines.append(context[:300])
        for sl in sworn_lines[:3]:
            W(f"      → {sl}")
        W("")

    # ── SECTION D: Overall Summary ─────────────────────────────────────
    W("╔" + "═" * 98 + "╗")
    W("║  SECTION D: OVERALL SUMMARY" + " " * 70 + "║")
    W("╚" + "═" * 98 + "╝")
    W("")
    W(f"  Total files analyzed:           {len(records)}")
    W(f"  Files successfully read:        {read_ok}")
    W(f"  Files failed to read:           {read_fail}")
    W(f"  Total text bytes processed:     {total_bytes_read:,}")
    W(f"  Topics covered:                 {len(topics)}")
    for t in topic_order:
        if t in topics:
            W(f"    {t:<25} {len(topics[t]):>5} files")
    W(f"  Court orders detected:          {len(court_orders)}")
    W(f"  Affidavits detected:            {len(affidavits)}")
    W(f"  Testimony references:           {len(testimony_refs)}")
    W(f"  Financial documents:            {len(financial_docs)}")
    W(f"  Ex parte evidence:              {len(ex_parte_docs)}")
    W(f"  HealthWest mentions:            {len(healthwest_docs)}")
    W(f"  $250 bond references:           {len(bond_250_docs)}")
    W(f"  NEW evidence (not in DB):       {len(new_evidence_files)}")
    W(f"  Unique legal authorities:       {len(all_legal_authorities)}")
    W(f"  Unique dates:                   {len(all_dates)}")
    W(f"  Unique case numbers:            {len(all_case_numbers)}")
    W(f"  Email files:                    {len(email_files)}")
    W("")
    elapsed = (datetime.now() - start_time).total_seconds()
    W(f"  Analysis completed in {elapsed:.1f} seconds.")
    W("=" * 100)

    # ── Write to file ──────────────────────────────────────────────────
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out_lines))

    print(f"\n✓ Report written to: {OUTPUT_PATH}")
    print(f"  Report size: {os.path.getsize(OUTPUT_PATH):,} bytes")
    print(f"  Total lines: {len(out_lines)}")
    print(f"  Elapsed: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
