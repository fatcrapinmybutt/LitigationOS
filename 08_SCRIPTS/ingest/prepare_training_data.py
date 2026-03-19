#!/usr/bin/env python3
"""
MBP LitigationOS — Training Data Preparation
=============================================
Extracts training corpus from litigation_context.db and formats as JSONL
for fine-tuning the Michigan Legal Language Model (MLLM).

Sources:
  - auth_rules (5,633 rows)  → MCR/MCL/MRE question-answer pairs
  - master_citations (160,030 rows) → citation-context pairs
  - evidence_quotes (405 rows) → evidence Q&A pairs
  - md_sections (213,417 rows) → section-based Q&A pairs

Output:
  - training_data/train.jsonl  (90%)
  - training_data/test.jsonl   (10%)
  - training_data/manifest.json (metadata)

Usage:
    python prepare_training_data.py
    python prepare_training_data.py --limit 10000
    python prepare_training_data.py --sources auth_rules,evidence_quotes

Example:
    python prepare_training_data.py --limit 50000
    # Produces ~50,000 JSONL lines in training_data/
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\litigation_context.db",
)
OUTPUT_DIR = Path(__file__).parent / "training_data"

# ── Category detection ──────────────────────────────────────────────
def _detect_category(text: str) -> str:
    """Detect legal category from text content."""
    text_upper = (text or "").upper()
    if "MCR " in text_upper or "COURT RULE" in text_upper:
        return "MCR"
    if "MCL " in text_upper or "COMPILED LAW" in text_upper:
        return "MCL"
    if "MRE " in text_upper or "RULE OF EVIDENCE" in text_upper:
        return "MRE"
    if " V " in text_upper or " V. " in text_upper:
        return "CASE"
    return "GENERAL"


def _safe_text(val: Any) -> str:
    """Safely convert DB value to string, handling encoding errors."""
    if val is None:
        return ""
    try:
        return str(val).strip()
    except Exception:
        return str(val).encode("utf-8", errors="replace").decode("utf-8", errors="replace").strip()


def _make_hash(text: str) -> str:
    """Create deduplication hash."""
    return hashlib.md5(text.encode("utf-8", errors="replace")).hexdigest()


# ── Extractors ──────────────────────────────────────────────────────
def extract_auth_rules(conn: sqlite3.Connection, limit: int = 0) -> List[Dict]:
    """Extract training pairs from auth_rules table."""
    examples = []
    sql = "SELECT rule_number, title, full_text, rule_type, summary FROM auth_rules WHERE full_text IS NOT NULL AND full_text != ''"
    if limit:
        sql += f" LIMIT {limit}"

    try:
        rows = conn.execute(sql).fetchall()
    except Exception as e:
        print(f"  [WARN] auth_rules query failed: {e}")
        return []

    for row in rows:
        rule_num = _safe_text(row[0])
        title = _safe_text(row[1])
        full_text = _safe_text(row[2])
        rule_type = _safe_text(row[3])
        summary = _safe_text(row[4])

        if not full_text or len(full_text) < 20:
            continue

        category = rule_type.upper() if rule_type else _detect_category(full_text)

        # Pair 1: "What does [rule] say?" → full text
        if rule_num:
            examples.append({
                "input": f"What does {rule_num} say about {title}?" if title else f"What does {rule_num} provide?",
                "output": full_text[:2000],
                "category": category,
                "source": "auth_rules",
            })

        # Pair 2: Title-based question → summary or text
        if title and (summary or full_text):
            answer = summary if summary and len(summary) > 20 else full_text[:1500]
            examples.append({
                "input": f"Explain the Michigan rule on {title.lower()}",
                "output": answer,
                "category": category,
                "source": "auth_rules",
            })

        # Pair 3: Rule type question
        if rule_type and rule_num:
            examples.append({
                "input": f"What is {rule_type} {rule_num}?",
                "output": f"{rule_num} — {title or 'Michigan legal rule'}. {(summary or full_text)[:1000]}",
                "category": category,
                "source": "auth_rules",
            })

    print(f"  auth_rules: {len(examples)} examples extracted")
    return examples


def extract_master_citations(conn: sqlite3.Connection, limit: int = 0) -> List[Dict]:
    """Extract training pairs from master_citations table."""
    examples = []
    sql = "SELECT citation, cite_type, context, source_file FROM master_citations WHERE context IS NOT NULL AND context != '' AND length(context) > 30"
    if limit:
        sql += f" LIMIT {limit}"

    try:
        rows = conn.execute(sql).fetchall()
    except Exception as e:
        print(f"  [WARN] master_citations query failed: {e}")
        return []

    seen = set()
    for row in rows:
        citation = _safe_text(row[0])
        cite_type = _safe_text(row[1])
        context = _safe_text(row[2])

        if not citation or not context:
            continue

        h = _make_hash(citation + context[:100])
        if h in seen:
            continue
        seen.add(h)

        category = _detect_category(citation)

        examples.append({
            "input": f"What does {citation} address?",
            "output": context[:1500],
            "category": category,
            "source": "master_citations",
        })

    print(f"  master_citations: {len(examples)} examples extracted")
    return examples


def extract_evidence_quotes(conn: sqlite3.Connection, limit: int = 0) -> List[Dict]:
    """Extract training pairs from evidence_quotes table."""
    examples = []
    sql = "SELECT quote_text, speaker, evidence_category, legal_significance FROM evidence_quotes WHERE quote_text IS NOT NULL AND quote_text != ''"
    if limit:
        sql += f" LIMIT {limit}"

    try:
        rows = conn.execute(sql).fetchall()
    except Exception as e:
        print(f"  [WARN] evidence_quotes query failed: {e}")
        return []

    for row in rows:
        quote = _safe_text(row[0])
        speaker = _safe_text(row[1])
        category_ev = _safe_text(row[2])
        significance = _safe_text(row[3])

        if not quote or len(quote) < 10:
            continue

        # Q&A pair about evidence
        q_parts = []
        if speaker:
            q_parts.append(f"by {speaker}")
        if category_ev:
            q_parts.append(f"regarding {category_ev}")
        qualifier = " ".join(q_parts) if q_parts else "in the record"

        examples.append({
            "input": f"What evidence exists {qualifier}?",
            "output": f'"{quote}"{" — Legal significance: " + significance if significance else ""}',
            "category": _detect_category(quote),
            "source": "evidence_quotes",
        })

        # Impeachment-style pair
        if speaker and significance:
            examples.append({
                "input": f"What did {speaker} say that is legally significant?",
                "output": f'"{quote}" — {significance}',
                "category": "EVIDENCE",
                "source": "evidence_quotes",
            })

    print(f"  evidence_quotes: {len(examples)} examples extracted")
    return examples


def extract_md_sections(conn: sqlite3.Connection, limit: int = 0) -> List[Dict]:
    """Extract training pairs from md_sections table."""
    examples = []
    sql = "SELECT section_title, content, source_file FROM md_sections WHERE content IS NOT NULL AND length(content) > 50 AND section_title IS NOT NULL AND section_title != ''"
    if limit:
        sql += f" LIMIT {limit}"

    try:
        rows = conn.execute(sql).fetchall()
    except Exception as e:
        print(f"  [WARN] md_sections query failed: {e}")
        return []

    seen = set()
    for row in rows:
        title = _safe_text(row[0])
        content = _safe_text(row[1])

        if not title or not content or len(content) < 50:
            continue

        h = _make_hash(title + content[:100])
        if h in seen:
            continue
        seen.add(h)

        category = _detect_category(content)

        examples.append({
            "input": f"Explain: {title}",
            "output": content[:2000],
            "category": category,
            "source": "md_sections",
        })

    print(f"  md_sections: {len(examples)} examples extracted")
    return examples


# ── Main pipeline ───────────────────────────────────────────────────
def prepare_training_data(
    limit: int = 0,
    sources: Optional[List[str]] = None,
    split_ratio: float = 0.9,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Main pipeline: extract, format, split, and save training data.

    Args:
        limit: Max examples per source (0 = unlimited)
        sources: List of source tables to use (default: all)
        split_ratio: Train/test split ratio (default 0.9)
        seed: Random seed for reproducibility

    Returns:
        Manifest dict with counts and paths
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[1/4] Connecting to DB: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA query_only=ON")

    all_sources = {
        "auth_rules": extract_auth_rules,
        "master_citations": extract_master_citations,
        "evidence_quotes": extract_evidence_quotes,
        "md_sections": extract_md_sections,
    }

    if sources:
        active_sources = {k: v for k, v in all_sources.items() if k in sources}
    else:
        active_sources = all_sources

    print(f"[2/4] Extracting from {len(active_sources)} sources...")
    all_examples = []
    source_counts = {}

    for name, extractor in active_sources.items():
        print(f"  Processing {name}...")
        examples = extractor(conn, limit=limit)
        source_counts[name] = len(examples)
        all_examples.extend(examples)

    conn.close()

    if not all_examples:
        print("[ERROR] No examples extracted!")
        return {"error": "No examples extracted"}

    # Deduplicate by input hash
    print(f"[3/4] Deduplicating {len(all_examples)} examples...")
    seen_hashes = set()
    unique = []
    for ex in all_examples:
        h = _make_hash(ex["input"])
        if h not in seen_hashes:
            seen_hashes.add(h)
            unique.append(ex)
    all_examples = unique
    print(f"  {len(all_examples)} unique examples after dedup")

    # Shuffle and split
    random.seed(seed)
    random.shuffle(all_examples)

    split_idx = int(len(all_examples) * split_ratio)
    train_set = all_examples[:split_idx]
    test_set = all_examples[split_idx:]

    # Save JSONL files
    print(f"[4/4] Saving {len(train_set)} train + {len(test_set)} test examples...")

    train_path = OUTPUT_DIR / "train.jsonl"
    test_path = OUTPUT_DIR / "test.jsonl"

    with open(train_path, "w", encoding="utf-8", errors="replace") as f:
        for ex in train_set:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    with open(test_path, "w", encoding="utf-8", errors="replace") as f:
        for ex in test_set:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    # Category distribution
    cat_dist = {}
    for ex in all_examples:
        cat = ex.get("category", "UNKNOWN")
        cat_dist[cat] = cat_dist.get(cat, 0) + 1

    manifest = {
        "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "db_path": DB_PATH,
        "total_examples": len(all_examples),
        "train_count": len(train_set),
        "test_count": len(test_set),
        "split_ratio": split_ratio,
        "source_counts": source_counts,
        "category_distribution": cat_dist,
        "train_path": str(train_path),
        "test_path": str(test_path),
        "seed": seed,
    }

    manifest_path = OUTPUT_DIR / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"Training Data Preparation Complete")
    print(f"{'='*60}")
    print(f"  Total examples: {len(all_examples):,}")
    print(f"  Train set:      {len(train_set):,}")
    print(f"  Test set:       {len(test_set):,}")
    print(f"  Categories:     {cat_dist}")
    print(f"  Output:         {OUTPUT_DIR}")
    print(f"{'='*60}")

    return manifest


# ── CLI ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Prepare MLLM training data from litigation_context.db"
    )
    parser.add_argument("--limit", type=int, default=0,
                        help="Max examples per source (0=unlimited)")
    parser.add_argument("--sources", type=str, default="",
                        help="Comma-separated source tables (default: all)")
    parser.add_argument("--split", type=float, default=0.9,
                        help="Train/test split ratio (default: 0.9)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed (default: 42)")

    args = parser.parse_args()
    sources = [s.strip() for s in args.sources.split(",") if s.strip()] or None

    result = prepare_training_data(
        limit=args.limit,
        sources=sources,
        split_ratio=args.split,
        seed=args.seed,
    )

    if "error" in result:
        sys.exit(1)
