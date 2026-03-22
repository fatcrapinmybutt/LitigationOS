#!/usr/bin/env python3
"""
APEX Contradiction Detection Engine v1.0
Two-stage: bi-encoder retrieval → cross-encoder reranking
Finds contradictions in Watson's statements, court records, and testimony
"""
import sys
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

import sqlite3
import json
import numpy as np
from pathlib import Path
from datetime import datetime

from sentence_transformers import SentenceTransformer, CrossEncoder

BRAIN_DB = r'C:\Users\andre\LitigationOS\00_SYSTEM\brains\chat_intelligence_brain.db'
LIT_DB = r'C:\Users\andre\LitigationOS\litigation_context.db'
OUTPUT_DB = r'C:\Users\andre\LitigationOS\00_SYSTEM\brains\contradictions.db'


def setup_output_db():
    db = sqlite3.connect(OUTPUT_DB)
    db.execute('PRAGMA busy_timeout=60000')
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('''CREATE TABLE IF NOT EXISTS contradictions (
        id INTEGER PRIMARY KEY,
        text_a TEXT,
        text_b TEXT,
        source_a TEXT,
        source_b TEXT,
        lane TEXT,
        similarity_score REAL,
        contradiction_score REAL,
        category TEXT,
        analysis TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS embeddings_cache (
        rowid_ref INTEGER PRIMARY KEY,
        embedding BLOB,
        content_hash TEXT
    )''')
    db.execute('CREATE INDEX IF NOT EXISTS idx_contra_score ON contradictions(contradiction_score DESC)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_contra_lane ON contradictions(lane)')
    db.commit()
    return db


def load_high_value_statements(brain_db_path, limit=3000):
    """Load high-relevance user-truth statements for contradiction analysis"""
    db = sqlite3.connect(brain_db_path)
    db.execute('PRAGMA busy_timeout=60000')

    rows = db.execute("""
        SELECT rowid, content, lanes, source_platform, legal_relevance_score, timestamp_utc
        FROM chat_intelligence
        WHERE legal_relevance_score >= 0.6
        AND length(content) BETWEEN 50 AND 1000
        AND content NOT LIKE '%```%'
        ORDER BY legal_relevance_score DESC
        LIMIT ?
    """, (limit,)).fetchall()
    db.close()

    statements = []
    for rowid, content, lanes, platform, score, ts in rows:
        statements.append({
            'rowid': rowid,
            'content': content.strip(),
            'lanes': lanes or '',
            'platform': platform or '',
            'score': score,
            'timestamp': ts or ''
        })
    return statements


def stage1_encode(statements, model_name='all-MiniLM-L6-v2', batch_size=64):
    """Stage 1: Bi-encoder — encode all statements into 384-dim embeddings"""
    print(f"Stage 1: Encoding {len(statements)} statements with {model_name}...")
    model = SentenceTransformer(model_name)

    texts = [s['content'] for s in statements]
    embeddings = model.encode(
        texts, batch_size=batch_size, show_progress_bar=True,
        normalize_embeddings=True
    )
    print(f"  Encoded: {embeddings.shape}")
    return embeddings


def stage1_find_candidates(embeddings, statements, top_k=10, min_sim=0.5, max_sim=0.92):
    """Find semantically similar pairs (potential contradictions live in 0.5-0.92 similarity range)
    Too similar (>0.92) = likely duplicates, not contradictions
    Too dissimilar (<0.5) = unrelated topics"""
    print(f"Stage 1: Finding candidate pairs (sim {min_sim}-{max_sim})...")

    n = len(statements)
    candidates = []

    batch = 500
    for i in range(0, n, batch):
        end_i = min(i + batch, n)
        for j in range(i + 1, n, batch):
            end_j = min(j + batch, n)

            sims = np.dot(embeddings[i:end_i], embeddings[j:end_j].T)

            indices = np.where((sims >= min_sim) & (sims <= max_sim))

            for a_idx, b_idx in zip(indices[0], indices[1]):
                real_a = i + a_idx
                real_b = j + b_idx
                sim = float(sims[a_idx, b_idx])
                candidates.append((real_a, real_b, sim))

    # Sort by similarity descending
    candidates.sort(key=lambda x: x[2], reverse=True)

    # Take top_k per statement to avoid explosion
    seen = set()
    filtered = []
    counter = {}
    for a, b, sim in candidates:
        if a not in counter:
            counter[a] = 0
        if b not in counter:
            counter[b] = 0
        if counter[a] < top_k and counter[b] < top_k:
            pair = (min(a, b), max(a, b))
            if pair not in seen:
                seen.add(pair)
                filtered.append((a, b, sim))
                counter[a] += 1
                counter[b] += 1

    print(f"  Found {len(filtered)} candidate pairs")
    return filtered[:5000]


def stage2_rerank(candidates, statements, batch_size=32):
    """Stage 2: Cross-encoder — score each candidate pair for contradiction"""
    print(f"Stage 2: Cross-encoder reranking {len(candidates)} pairs...")

    model = CrossEncoder('cross-encoder/nli-MiniLM2-L6-H768', max_length=512)

    pairs = []
    for a_idx, b_idx, sim in candidates:
        text_a = statements[a_idx]['content'][:400]
        text_b = statements[b_idx]['content'][:400]
        pairs.append([text_a, text_b])

    # Score all pairs — returns [contradiction, entailment, neutral] logits
    scores = model.predict(pairs, batch_size=batch_size, show_progress_bar=True)

    results = []
    for i, (a_idx, b_idx, sim) in enumerate(candidates):
        row_scores = scores[i]
        if hasattr(row_scores, '__len__') and len(row_scores) >= 3:
            exp_scores = np.exp(row_scores - np.max(row_scores))
            probs = exp_scores / exp_scores.sum()
            contra_prob = float(probs[0])  # contradiction label
        else:
            contra_prob = float(row_scores[0]) if row_scores[0] > 0 else 0.0

        if contra_prob >= 0.3:
            results.append({
                'a_idx': a_idx,
                'b_idx': b_idx,
                'similarity': sim,
                'contradiction_score': contra_prob,
                'text_a': statements[a_idx],
                'text_b': statements[b_idx]
            })

    results.sort(key=lambda x: x['contradiction_score'], reverse=True)
    print(f"  Found {len(results)} contradictions (score >= 0.3)")
    return results


def categorize_contradiction(text_a, text_b, lanes):
    """Categorize the type of contradiction"""
    combined = (text_a + ' ' + text_b).lower()

    if any(w in combined for w in ['custody', 'parenting', 'visitation', 'child']):
        return 'custody_contradiction'
    elif any(w in combined for w in ['judge', 'mcneill', 'court', 'hearing', 'order']):
        return 'judicial_contradiction'
    elif any(w in combined for w in ['ppo', 'protection', 'restraining', 'threat']):
        return 'ppo_contradiction'
    elif any(w in combined for w in ['shady oaks', 'housing', 'evict', 'property', 'rent']):
        return 'housing_contradiction'
    elif any(w in combined for w in ['police', 'arrest', 'cps', 'dhhs', 'report']):
        return 'agency_contradiction'
    elif any(w in combined for w in ['watson', 'emily', 'berry', 'albert']):
        return 'party_statement_contradiction'
    else:
        return 'general_contradiction'


def save_results(output_db, results, statements):
    """Save detected contradictions to output DB"""
    batch = []
    for r in results:
        a = r['text_a']
        b = r['text_b']
        lane = a.get('lanes', '') or b.get('lanes', '')
        category = categorize_contradiction(a['content'], b['content'], lane)

        batch.append((
            a['content'][:1000],
            b['content'][:1000],
            f"{a['platform']}:{a.get('rowid', '')}",
            f"{b['platform']}:{b.get('rowid', '')}",
            lane,
            r['similarity'],
            r['contradiction_score'],
            category,
            json.dumps({
                'a_score': a.get('score', 0),
                'b_score': b.get('score', 0),
                'a_ts': a.get('timestamp', ''),
                'b_ts': b.get('timestamp', '')
            }),
            datetime.now().isoformat()
        ))

    output_db.executemany("""INSERT INTO contradictions
        (text_a, text_b, source_a, source_b, lane, similarity_score,
         contradiction_score, category, analysis, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?)""", batch)
    output_db.commit()
    print(f"Saved {len(batch)} contradictions to {OUTPUT_DB}")


def print_category_breakdown(results, statements):
    """Print breakdown by contradiction category"""
    cats = {}
    for r in results:
        a = r['text_a']
        b = r['text_b']
        lane = a.get('lanes', '') or b.get('lanes', '')
        cat = categorize_contradiction(a['content'], b['content'], lane)
        if cat not in cats:
            cats[cat] = 0
        cats[cat] += 1

    print("\nCATEGORY BREAKDOWN:")
    print("-" * 40)
    for cat, count in sorted(cats.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat}: {count}")


def main():
    print("=" * 60)
    print("APEX Contradiction Detection Engine v1.0")
    print("Two-stage: bi-encoder -> cross-encoder")
    print("=" * 60)

    out_db = setup_output_db()

    statements = load_high_value_statements(BRAIN_DB, limit=2000)
    print(f"Loaded {len(statements)} high-value statements")

    if len(statements) < 10:
        print("Not enough statements for contradiction analysis")
        return

    # Stage 1: Encode + find candidates
    embeddings = stage1_encode(statements)
    candidates = stage1_find_candidates(embeddings, statements)

    if not candidates:
        print("No candidate pairs found")
        return

    # Stage 2: Cross-encoder reranking
    results = stage2_rerank(candidates, statements)

    if results:
        save_results(out_db, results, statements)

        print("\n" + "=" * 60)
        print(f"TOP CONTRADICTIONS (of {len(results)}):")
        print("=" * 60)
        for i, r in enumerate(results[:10], 1):
            print(f"\n#{i} -- Score: {r['contradiction_score']:.3f} (sim: {r['similarity']:.3f})")
            print(f"  A [{r['text_a']['platform']}]: {r['text_a']['content'][:150]}...")
            print(f"  B [{r['text_b']['platform']}]: {r['text_b']['content'][:150]}...")

        print_category_breakdown(results, statements)
    else:
        print("No contradictions detected above threshold.")

    out_db.close()
    print(f"\nDone! Results in: {OUTPUT_DB}")


if __name__ == '__main__':
    main()
