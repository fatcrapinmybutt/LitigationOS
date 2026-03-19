#!/usr/bin/env python3
"""LLM Classifier Engine - Automated document classification via Ollama.

Classifies litigation documents into categories using local LLM (qwen2.5:7b).
Scores relevance, assigns lane designations, supports batch processing.

Usage:
    python llm_classifier_engine.py --file path/to/doc.pdf
    python llm_classifier_engine.py --dir path/to/docs/ --output-db
    python llm_classifier_engine.py --batch file_list.txt --output-db
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import argparse
import json
import os
import re
import sqlite3
import time
import traceback
from datetime import datetime
from pathlib import Path

DB = r'C:\Users\andre\LitigationOS\litigation_context.db'

CATEGORIES = [
    'FILING', 'EVIDENCE', 'AUTHORITY', 'CORRESPONDENCE',
    'COURT_ORDER', 'MOTION', 'BRIEF', 'EXHIBIT', 'ADMINISTRATIVE'
]

LANE_MAP = {
    'FILING': 'A', 'MOTION': 'A', 'BRIEF': 'A',
    'EVIDENCE': 'B', 'EXHIBIT': 'B',
    'AUTHORITY': 'C', 'COURT_ORDER': 'C',
    'CORRESPONDENCE': 'D', 'ADMINISTRATIVE': 'F',
}

CLASSIFICATION_PROMPT = """You are a litigation document classifier. Classify the document into exactly ONE category.

CATEGORIES (with disambiguation rules):
- FILING: Initiating documents — complaints, petitions, answers, counterclaims (NOT motions or briefs)
- MOTION: Requests for court action — motion to dismiss, motion for summary judgment, motion to compel (has "motion" in title or requests specific relief)
- BRIEF: Legal argument documents — memoranda of law, appellate briefs, response briefs (supports a motion or appeal with legal analysis)
- COURT_ORDER: Documents ISSUED BY A JUDGE — orders, judgments, opinions, rulings (bears judge signature or "IT IS ORDERED")
- EVIDENCE: Proof documents — photos, records, financial statements, communications used as exhibits
- EXHIBIT: Formally labeled exhibits with exhibit numbers/letters (e.g., "Exhibit A", "Plaintiff's Exhibit 3")
- AUTHORITY: Legal sources — case law citations, statutes, court rules referenced as authority
- CORRESPONDENCE: Party communications — letters, emails between parties/attorneys (NOT filed with court)
- ADMINISTRATIVE: Procedural records — docket entries, scheduling orders, case management

EXAMPLES:
Input: "MOTION TO MODIFY CUSTODY ... Plaintiff respectfully requests..." → {{"category": "MOTION", "confidence": 0.95, "relevance_score": 90, "reasoning": "Requests specific court relief to modify custody"}}
Input: "IT IS HEREBY ORDERED that defendant shall..." → {{"category": "COURT_ORDER", "confidence": 0.98, "relevance_score": 95, "reasoning": "Judge-issued order with directive language"}}
Input: "Dear Ms. Barnes, Attached please find..." → {{"category": "CORRESPONDENCE", "confidence": 0.90, "relevance_score": 60, "reasoning": "Attorney-to-attorney letter not filed with court"}}

If uncertain between two categories, pick the more specific one. Set confidence below 0.6 for ambiguous documents.

Respond ONLY with valid JSON (no markdown, no explanation):
{{"category": "CATEGORY_NAME", "confidence": 0.0-1.0, "relevance_score": 0-100, "reasoning": "one sentence"}}

DOCUMENT CONTENT:
---
{content}
---
"""

MAX_RETRIES = 3
RETRY_BACKOFF = [2, 5, 10]


def get_db_connection():
    """Open DB connection with standard pragmas."""
    conn = sqlite3.connect(DB, timeout=120)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    return conn


def ensure_classification_table(conn):
    """Create classification_results table if not exists."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS classification_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT,
            file_name TEXT,
            category TEXT,
            confidence REAL,
            relevance_score INTEGER,
            suggested_lane TEXT,
            reasoning TEXT,
            model_used TEXT DEFAULT 'qwen2.5:7b',
            classified_at TEXT,
            raw_response TEXT
        )
    """)
    conn.commit()


def read_file_content(file_path, max_chars=4000):
    """Read file content, truncating to max_chars for LLM context."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = path.suffix.lower()
    if ext in ('.txt', '.md', '.csv', '.log', '.json'):
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read(max_chars)
    elif ext in ('.pdf',):
        # Try to extract text from PDF filename and any sidecar .txt
        txt_sidecar = path.with_suffix('.txt')
        if txt_sidecar.exists():
            with open(txt_sidecar, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read(max_chars)
        else:
            content = f"[PDF file: {path.name}, size: {path.stat().st_size} bytes. No text extraction available - classifying by filename and metadata.]"
    else:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read(max_chars)

    return content[:max_chars]


def call_ollama(content, retries=MAX_RETRIES):
    """Call Ollama with retry logic and exponential backoff."""
    try:
        import ollama
    except ImportError:
        print("[ERROR] ollama package not installed. Install with: pip install ollama")
        return None

    prompt = CLASSIFICATION_PROMPT.format(content=content[:3500])

    for attempt in range(retries):
        try:
            response = ollama.chat(
                model='qwen2.5:7b',
                messages=[{'role': 'user', 'content': prompt}],
                options={'temperature': 0.1, 'num_predict': 256}
            )
            raw_text = response['message']['content'].strip()
            return raw_text
        except Exception as e:
            wait_time = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
            print(f"  [RETRY {attempt+1}/{retries}] Ollama error: {e}. Waiting {wait_time}s...")
            time.sleep(wait_time)

    print("[ERROR] All Ollama retries exhausted.")
    return None


def parse_llm_response(raw_text):
    """Parse JSON from LLM response, handling common formatting issues."""
    if not raw_text:
        return None

    # Try direct JSON parse
    try:
        data = json.loads(raw_text)
        return data
    except json.JSONDecodeError:
        pass

    # Try extracting JSON from markdown code blocks
    json_match = re.search(r'\{[^{}]*\}', raw_text, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group())
            return data
        except json.JSONDecodeError:
            pass

    return None


def classify_document(file_path=None, text_content=None):
    """Classify a single document. Returns classification dict."""
    if file_path:
        print(f"[CLASSIFY] {Path(file_path).name}")
        content = read_file_content(file_path)
    elif text_content:
        print(f"[CLASSIFY] inline text ({len(text_content)} chars)")
        content = text_content[:4000]
    else:
        return {'error': 'No file_path or text_content provided'}

    raw_response = call_ollama(content)
    if not raw_response:
        return {
            'category': 'ADMINISTRATIVE',
            'confidence': 0.0,
            'relevance_score': 0,
            'suggested_lane': 'F',
            'reasoning': 'LLM classification failed - default assignment',
            'error': 'ollama_unavailable'
        }

    parsed = parse_llm_response(raw_response)
    if not parsed:
        return {
            'category': 'ADMINISTRATIVE',
            'confidence': 0.0,
            'relevance_score': 0,
            'suggested_lane': 'F',
            'reasoning': 'Could not parse LLM response',
            'raw_response': raw_response,
            'error': 'parse_failure'
        }

    # Validate and normalize
    category = parsed.get('category', 'ADMINISTRATIVE').upper()
    if category not in CATEGORIES:
        category = 'ADMINISTRATIVE'

    confidence = min(1.0, max(0.0, float(parsed.get('confidence', 0.5))))
    relevance = min(100, max(0, int(parsed.get('relevance_score', 50))))
    reasoning = str(parsed.get('reasoning', ''))
    lane = LANE_MAP.get(category, 'F')

    result = {
        'file_path': str(file_path) if file_path else None,
        'file_name': Path(file_path).name if file_path else None,
        'category': category,
        'confidence': round(confidence, 3),
        'relevance_score': relevance,
        'suggested_lane': lane,
        'reasoning': reasoning,
        'raw_response': raw_response
    }

    print(f"  -> {category} (conf={confidence:.2f}, rel={relevance}, lane={lane})")
    return result


def classify_directory(dir_path, extensions=None):
    """Classify all files in a directory."""
    if extensions is None:
        extensions = {'.txt', '.md', '.pdf', '.json', '.csv', '.log'}

    dir_path = Path(dir_path)
    if not dir_path.is_dir():
        print(f"[ERROR] Directory not found: {dir_path}")
        return []

    results = []
    files = sorted(f for f in dir_path.rglob('*') if f.is_file() and f.suffix.lower() in extensions)
    total = len(files)
    print(f"[BATCH] Found {total} files in {dir_path}")

    for i, fpath in enumerate(files, 1):
        print(f"[{i}/{total}] ", end='')
        result = classify_document(file_path=str(fpath))
        results.append(result)

    return results


def classify_batch_file(batch_file):
    """Classify files listed in a batch file (one path per line)."""
    batch_path = Path(batch_file)
    if not batch_path.exists():
        print(f"[ERROR] Batch file not found: {batch_file}")
        return []

    with open(batch_path, 'r', encoding='utf-8') as f:
        paths = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    results = []
    total = len(paths)
    print(f"[BATCH] Processing {total} files from {batch_file}")

    for i, fpath in enumerate(paths, 1):
        print(f"[{i}/{total}] ", end='')
        if os.path.exists(fpath):
            result = classify_document(file_path=fpath)
        else:
            result = {'file_path': fpath, 'error': 'file_not_found'}
            print(f"[SKIP] File not found: {fpath}")
        results.append(result)

    return results


def save_results_to_db(results):
    """Write classification results to the database."""
    conn = get_db_connection()
    ensure_classification_table(conn)
    now = datetime.now().isoformat()
    inserted = 0

    for r in results:
        if 'error' in r and r.get('category') is None:
            continue
        try:
            conn.execute("""
                INSERT INTO classification_results
                (file_path, file_name, category, confidence, relevance_score,
                 suggested_lane, reasoning, classified_at, raw_response)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r.get('file_path'), r.get('file_name'), r.get('category'),
                r.get('confidence'), r.get('relevance_score'),
                r.get('suggested_lane'), r.get('reasoning'),
                now, r.get('raw_response', '')
            ))
            inserted += 1
        except Exception as e:
            print(f"  [DB ERROR] {e}")

    conn.commit()
    conn.close()
    print(f"[DB] Saved {inserted} classification results to classification_results table.")
    return inserted


def print_summary(results):
    """Print classification summary to stdout."""
    if not results:
        print("[SUMMARY] No results to display.")
        return

    from collections import Counter
    cats = Counter(r.get('category', 'UNKNOWN') for r in results if 'error' not in r or r.get('category'))
    lanes = Counter(r.get('suggested_lane', '?') for r in results if r.get('suggested_lane'))
    errors = sum(1 for r in results if 'error' in r)

    print("\n" + "=" * 60)
    print("CLASSIFICATION SUMMARY")
    print("=" * 60)
    print(f"Total processed: {len(results)}")
    print(f"Errors: {errors}")
    print(f"\nBy Category:")
    for cat, count in cats.most_common():
        print(f"  {cat:<20s} {count:>4d}")
    print(f"\nBy Lane:")
    for lane, count in sorted(lanes.items()):
        print(f"  Lane {lane}: {count}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='LLM Classifier Engine - Classify litigation documents via Ollama'
    )
    parser.add_argument('--file', type=str, help='Single file to classify')
    parser.add_argument('--dir', type=str, help='Directory of files to classify')
    parser.add_argument('--batch', type=str, help='Batch file with list of paths')
    parser.add_argument('--text', type=str, help='Inline text to classify')
    parser.add_argument('--output-db', action='store_true', help='Write results to DB')
    parser.add_argument('--output-json', type=str, help='Write results to JSON file')

    args = parser.parse_args()

    if not any([args.file, args.dir, args.batch, args.text]):
        parser.print_help()
        print("\n[ERROR] Provide --file, --dir, --batch, or --text")
        sys.exit(1)

    print(f"[START] LLM Classifier Engine - {datetime.now().isoformat()}")
    results = []

    try:
        if args.file:
            result = classify_document(file_path=args.file)
            results.append(result)
        elif args.text:
            result = classify_document(text_content=args.text)
            results.append(result)
        elif args.dir:
            results = classify_directory(args.dir)
        elif args.batch:
            results = classify_batch_file(args.batch)

        print_summary(results)

        if args.output_db:
            save_results_to_db(results)

        if args.output_json:
            with open(args.output_json, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=True)
            print(f"[OUTPUT] JSON written to {args.output_json}")

        if len(results) == 1 and not args.output_json:
            print("\n[RESULT]")
            clean = {k: v for k, v in results[0].items() if k != 'raw_response'}
            print(json.dumps(clean, indent=2, ensure_ascii=True))

    except Exception as e:
        print(f"[FATAL] {e}")
        traceback.print_exc()
        sys.exit(1)

    print(f"[DONE] {datetime.now().isoformat()}")


if __name__ == '__main__':
    main()
