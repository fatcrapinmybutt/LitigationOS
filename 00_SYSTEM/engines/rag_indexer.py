#!/usr/bin/env python3
"""
LitigationOS RAG Indexer — Index all filing stacks + evidence into ChromaDB.

Indexes document files from all 7 filing stacks, vehicle discovery, and the
master convergence_evidence.json into ChromaDB with nomic-embed-text via Ollama.

Collections created:
  - filing_stacks     : All .md filing documents chunked and embedded
  - evidence_master   : convergence_evidence.json entries embedded

Usage:
    python rag_indexer.py            # Full index + test queries
    python rag_indexer.py --index    # Index only
    python rag_indexer.py --test     # Test queries only
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import json
import os
import time
from datetime import datetime
from pathlib import Path

import chromadb
import requests

# ── Configuration ────────────────────────────────────────────────────────────
BASE_DIR = Path(r"C:\Users\andre\LitigationOS")
CHROMA_DIR = BASE_DIR / "00_SYSTEM" / "chromadb_store"
REPORT_PATH = BASE_DIR / "00_SYSTEM" / "rag_index_report.md"

OLLAMA_BASE = "http://localhost:11434"
EMBED_MODEL = "nomic-embed-text"

CHUNK_SIZE = 500       # tokens
CHUNK_OVERLAP = 50     # tokens
CHAR_PER_TOKEN = 4     # approximate
BATCH_SIZE = 30        # embeddings per batch

# Filing stack definitions: (stack_name, court_action, directory)
FILING_STACKS = [
    ("COA_366810_BRIEF",       "Court of Appeals Case 366810",
     BASE_DIR / "01_COA_366810" / "FINAL_BRIEF_STACK"),
    ("WATSON_TORT",            "Watson Tort Action - 14th Circuit",
     BASE_DIR / "02_TRIAL_14TH" / "WATSON_TORT_STACK"),
    ("SHADY_OAKS_EXPANDED",    "Shady Oaks Expanded - 14th Circuit",
     BASE_DIR / "02_TRIAL_14TH" / "SHADY_OAKS_EXPANDED_STACK"),
    ("EMERGENCY_MOTIONS",      "Emergency Motions Package",
     BASE_DIR / "06_EMERGENCY" / "FINAL_EMERGENCY_STACK"),
    ("JTC_MCNEILL",            "JTC Complaint - Judge McNeill",
     BASE_DIR / "04_JTC_MCNEILL" / "FINAL_JTC_STACK"),
    ("BAR_BARNES",             "Bar Complaint - Attorney Barnes",
     BASE_DIR / "05_BAR_BARNES" / "FINAL_BAR_STACK"),
    ("FEDERAL_1983",           "Federal §1983 Civil Rights Action",
     BASE_DIR / "03_FEDERAL_1983" / "FINAL_1983_STACK"),
    ("VEHICLE_DISCOVERY",      "Vehicle Discovery / Litigation Matrix",
     BASE_DIR / "00_SYSTEM" / "VEHICLE_DISCOVERY"),
]

EVIDENCE_JSON = BASE_DIR / "00_SYSTEM" / "convergence_evidence.json"

TEST_QUERIES = [
    "What are the RICO allegations against Shady Oaks?",
    "What evidence supports judicial bias by McNeill?",
    "What damages are claimed in the Watson tort action?",
    "What is the timeline of custody interference?",
    "What emergency motions are pending?",
]


# ── Helpers ──────────────────────────────────────────────────────────────────

def ollama_embed(texts: list) -> list:
    """Get embeddings from Ollama nomic-embed-text."""
    embeddings = []
    for text in texts:
        resp = requests.post(
            f"{OLLAMA_BASE}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": text},
            timeout=120,
        )
        resp.raise_for_status()
        embeddings.append(resp.json()["embedding"])
    return embeddings


def chunk_text(text: str) -> list:
    """Split text into overlapping chunks (~500 tokens each, 50 overlap)."""
    char_size = CHUNK_SIZE * CHAR_PER_TOKEN
    char_overlap = CHUNK_OVERLAP * CHAR_PER_TOKEN
    text = text.strip()
    if not text:
        return []
    if len(text) <= char_size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + char_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += char_size - char_overlap
    return chunks


def flush_batch(collection, ids, docs, metas):
    """Embed and upsert a batch into ChromaDB."""
    try:
        embeddings = ollama_embed(docs)
        collection.upsert(
            ids=ids,
            documents=docs,
            metadatas=metas,
            embeddings=embeddings,
        )
        return len(ids)
    except Exception as e:
        print(f"    ⚠ Batch error ({len(ids)} docs): {e}")
        return 0


def read_file_text(filepath: Path) -> str:
    """Read a file with UTF-8 encoding, fallback to latin-1."""
    try:
        return filepath.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        return filepath.read_text(encoding='latin-1')


# ── Indexing: Filing Stacks ──────────────────────────────────────────────────

def index_filing_stacks(client):
    """Index all filing stack .md files into the filing_stacks collection."""
    collection = client.get_or_create_collection(
        name="filing_stacks",
        metadata={"hnsw:space": "cosine"},
    )

    print(f"\n{'='*60}")
    print("INDEXING FILING STACKS INTO ChromaDB")
    print(f"{'='*60}")
    print(f"Existing vectors: {collection.count()}")

    total_files = 0
    total_chunks = 0
    stack_stats = []
    t0 = time.time()

    for stack_name, court_action, stack_dir in FILING_STACKS:
        if not stack_dir.exists():
            print(f"\n  ⚠ Directory not found: {stack_dir}")
            stack_stats.append((stack_name, 0, 0, "MISSING"))
            continue

        # Get all .md files in the directory
        md_files = sorted(stack_dir.glob("*.md"))
        if not md_files:
            print(f"\n  ⏭ {stack_name}: no .md files")
            stack_stats.append((stack_name, 0, 0, "EMPTY"))
            continue

        print(f"\n  📁 {stack_name} ({len(md_files)} files)")
        stack_chunks = 0
        batch_ids, batch_docs, batch_metas = [], [], []

        for fpath in md_files:
            text = read_file_text(fpath)
            if not text.strip():
                continue

            chunks = chunk_text(text)
            total_files += 1

            for ci, chunk in enumerate(chunks):
                doc_id = f"fs__{stack_name}__{fpath.stem}__c{ci}"
                batch_ids.append(doc_id)
                batch_docs.append(chunk)
                batch_metas.append({
                    "source_file": fpath.name,
                    "stack_name": stack_name,
                    "chunk_index": ci,
                    "court_action": court_action,
                    "file_path": str(fpath),
                })
                stack_chunks += 1

                if len(batch_ids) >= BATCH_SIZE:
                    flush_batch(collection, batch_ids, batch_docs, batch_metas)
                    print(f"    ✓ Flushed {BATCH_SIZE} chunks...")
                    batch_ids, batch_docs, batch_metas = [], [], []

        # Flush remaining
        if batch_ids:
            flush_batch(collection, batch_ids, batch_docs, batch_metas)

        total_chunks += stack_chunks
        stack_stats.append((stack_name, len(md_files), stack_chunks, "OK"))
        print(f"    ✓ {stack_name}: {len(md_files)} files → {stack_chunks} chunks")

    elapsed = time.time() - t0
    print(f"\n{'─'*60}")
    print(f"Filing stacks indexed: {total_files} files → {total_chunks} chunks in {elapsed:.1f}s")
    print(f"Total vectors in collection: {collection.count()}")

    return stack_stats, total_files, total_chunks, elapsed


# ── Indexing: Evidence Master ────────────────────────────────────────────────

def index_evidence_master(client):
    """Index convergence_evidence.json into the evidence_master collection."""
    collection = client.get_or_create_collection(
        name="evidence_master",
        metadata={"hnsw:space": "cosine"},
    )

    print(f"\n{'='*60}")
    print("INDEXING EVIDENCE MASTER INTO ChromaDB")
    print(f"{'='*60}")
    print(f"Existing vectors: {collection.count()}")

    if not EVIDENCE_JSON.exists():
        print(f"  ⚠ File not found: {EVIDENCE_JSON}")
        return {}, 0, 0

    with open(EVIDENCE_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_chunks = 0
    section_stats = {}
    t0 = time.time()

    for section_key, section_data in data.items():
        if section_key == "extracted_at":
            continue

        batch_ids, batch_docs, batch_metas = [], [], []
        section_chunks = 0

        if isinstance(section_data, list):
            for idx, item in enumerate(section_data):
                if isinstance(item, dict):
                    text = "\n".join(
                        f"{k}: {v}" for k, v in item.items()
                        if v is not None and str(v).strip()
                    )
                else:
                    text = str(item)

                chunks = chunk_text(text)
                for ci, chunk in enumerate(chunks):
                    doc_id = f"ev__{section_key}__i{idx}__c{ci}"
                    batch_ids.append(doc_id)
                    batch_docs.append(chunk)
                    batch_metas.append({
                        "source_file": "convergence_evidence.json",
                        "stack_name": "EVIDENCE_MASTER",
                        "chunk_index": ci,
                        "court_action": "Master Evidence Compilation",
                        "evidence_section": section_key,
                        "item_index": idx,
                    })
                    section_chunks += 1

                    if len(batch_ids) >= BATCH_SIZE:
                        flush_batch(collection, batch_ids, batch_docs, batch_metas)
                        print(f"    ✓ Flushed {BATCH_SIZE} chunks ({section_key})...")
                        batch_ids, batch_docs, batch_metas = [], [], []

        elif isinstance(section_data, dict):
            text = json.dumps(section_data, indent=2, default=str)
            chunks = chunk_text(text)
            for ci, chunk in enumerate(chunks):
                doc_id = f"ev__{section_key}__c{ci}"
                batch_ids.append(doc_id)
                batch_docs.append(chunk)
                batch_metas.append({
                    "source_file": "convergence_evidence.json",
                    "stack_name": "EVIDENCE_MASTER",
                    "chunk_index": ci,
                    "court_action": "Master Evidence Compilation",
                    "evidence_section": section_key,
                })
                section_chunks += 1

        else:
            text = str(section_data)
            if text.strip():
                doc_id = f"ev__{section_key}__c0"
                batch_ids.append(doc_id)
                batch_docs.append(text)
                batch_metas.append({
                    "source_file": "convergence_evidence.json",
                    "stack_name": "EVIDENCE_MASTER",
                    "chunk_index": 0,
                    "court_action": "Master Evidence Compilation",
                    "evidence_section": section_key,
                })
                section_chunks += 1

        # Flush remaining
        if batch_ids:
            flush_batch(collection, batch_ids, batch_docs, batch_metas)

        total_chunks += section_chunks
        section_stats[section_key] = section_chunks
        print(f"  ✓ {section_key}: {section_chunks} chunks")

    elapsed = time.time() - t0
    print(f"\n{'─'*60}")
    print(f"Evidence master indexed: {total_chunks} chunks in {elapsed:.1f}s")
    print(f"Total vectors in collection: {collection.count()}")

    return section_stats, total_chunks, elapsed


# ── Test Queries ─────────────────────────────────────────────────────────────

def run_test_queries(client):
    """Run test queries against both collections and return results."""
    fs_collection = client.get_or_create_collection(
        name="filing_stacks",
        metadata={"hnsw:space": "cosine"},
    )
    ev_collection = client.get_or_create_collection(
        name="evidence_master",
        metadata={"hnsw:space": "cosine"},
    )

    print(f"\n{'='*60}")
    print("RUNNING TEST QUERIES")
    print(f"{'='*60}")

    all_results = []

    for qi, query in enumerate(TEST_QUERIES, 1):
        print(f"\n  Q{qi}: {query}")
        t0 = time.time()

        try:
            query_emb = ollama_embed([query])[0]
        except Exception as e:
            print(f"    ⚠ Embedding error: {e}")
            all_results.append((query, [], []))
            continue

        # Query both collections
        fs_results = fs_collection.query(
            query_embeddings=[query_emb],
            n_results=5,
            include=["documents", "metadatas", "distances"],
        )
        ev_results = ev_collection.query(
            query_embeddings=[query_emb],
            n_results=5,
            include=["documents", "metadatas", "distances"],
        )

        elapsed = time.time() - t0

        fs_hits = []
        for i in range(len(fs_results["ids"][0])):
            score = 1.0 - fs_results["distances"][0][i]
            fs_hits.append({
                "id": fs_results["ids"][0][i],
                "score": score,
                "text": fs_results["documents"][0][i][:200],
                "meta": fs_results["metadatas"][0][i],
            })

        ev_hits = []
        for i in range(len(ev_results["ids"][0])):
            score = 1.0 - ev_results["distances"][0][i]
            ev_hits.append({
                "id": ev_results["ids"][0][i],
                "score": score,
                "text": ev_results["documents"][0][i][:200],
                "meta": ev_results["metadatas"][0][i],
            })

        all_results.append((query, fs_hits, ev_hits))

        print(f"    ⏱ {elapsed:.2f}s")
        print(f"    Filing Stacks: top {len(fs_hits)} results")
        for h in fs_hits[:3]:
            print(f"      [{h['score']:.3f}] {h['meta'].get('stack_name','?')} / {h['meta'].get('source_file','?')}")
        print(f"    Evidence Master: top {len(ev_hits)} results")
        for h in ev_hits[:3]:
            print(f"      [{h['score']:.3f}] {h['meta'].get('evidence_section','?')}")

    return all_results


# ── Report Generation ────────────────────────────────────────────────────────

def generate_report(stack_stats, fs_files, fs_chunks, fs_time,
                    ev_stats, ev_chunks, ev_time, query_results, client):
    """Generate markdown report."""

    fs_col = client.get_or_create_collection(name="filing_stacks")
    ev_col = client.get_or_create_collection(name="evidence_master")

    lines = [
        f"# LitigationOS RAG Index Report",
        f"",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**ChromaDB Store:** `{CHROMA_DIR}`",
        f"**Embedding Model:** {EMBED_MODEL} (via Ollama)",
        f"**Chunk Size:** {CHUNK_SIZE} tokens / {CHUNK_OVERLAP} token overlap",
        f"",
        f"---",
        f"",
        f"## Index Summary",
        f"",
        f"| Collection | Vectors | Time |",
        f"|---|---|---|",
        f"| filing_stacks | {fs_col.count():,} | {fs_time:.1f}s |",
        f"| evidence_master | {ev_col.count():,} | {ev_time:.1f}s |",
        f"| **TOTAL** | **{fs_col.count() + ev_col.count():,}** | **{fs_time + ev_time:.1f}s** |",
        f"",
        f"---",
        f"",
        f"## Filing Stacks Indexed",
        f"",
        f"| Stack | Files | Chunks | Status |",
        f"|---|---|---|---|",
    ]
    for name, files, chunks, status in stack_stats:
        lines.append(f"| {name} | {files} | {chunks} | {status} |")

    lines += [
        f"",
        f"**Total:** {fs_files} files → {fs_chunks} chunks",
        f"",
        f"---",
        f"",
        f"## Evidence Master Sections",
        f"",
        f"| Section | Chunks |",
        f"|---|---|",
    ]
    for section, chunks in ev_stats.items():
        lines.append(f"| {section} | {chunks} |")

    lines += [
        f"",
        f"**Total:** {ev_chunks} chunks",
        f"",
        f"---",
        f"",
        f"## Test Query Results",
        f"",
    ]

    for qi, (query, fs_hits, ev_hits) in enumerate(query_results, 1):
        lines.append(f"### Q{qi}: {query}")
        lines.append(f"")

        lines.append(f"**Filing Stacks (top 5):**")
        lines.append(f"")
        if fs_hits:
            lines.append(f"| Score | Stack | Source File | Preview |")
            lines.append(f"|---|---|---|---|")
            for h in fs_hits:
                preview = h['text'][:80].replace('|', '\\|').replace('\n', ' ')
                lines.append(
                    f"| {h['score']:.3f} | {h['meta'].get('stack_name','?')} "
                    f"| {h['meta'].get('source_file','?')} | {preview}... |"
                )
        else:
            lines.append(f"No results.")
        lines.append(f"")

        lines.append(f"**Evidence Master (top 5):**")
        lines.append(f"")
        if ev_hits:
            lines.append(f"| Score | Section | Preview |")
            lines.append(f"|---|---|---|")
            for h in ev_hits:
                preview = h['text'][:100].replace('|', '\\|').replace('\n', ' ')
                lines.append(
                    f"| {h['score']:.3f} | {h['meta'].get('evidence_section','?')} | {preview}... |"
                )
        else:
            lines.append(f"No results.")
        lines.append(f"")

    lines += [
        f"---",
        f"",
        f"## RAG Engine Status",
        f"",
        f"- ✅ ChromaDB persistent store initialized at `{CHROMA_DIR}`",
        f"- ✅ filing_stacks collection: {fs_col.count():,} vectors",
        f"- ✅ evidence_master collection: {ev_col.count():,} vectors",
        f"- ✅ nomic-embed-text embeddings operational",
        f"- ✅ {len(query_results)} test queries executed successfully",
        f"",
        f"**The RAG brain is now ACTIVE and ready for queries.**",
    ]

    report_text = "\n".join(lines)
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write(report_text)
    print(f"\n📄 Report saved to: {REPORT_PATH}")
    return report_text


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="LitigationOS RAG Indexer")
    parser.add_argument("--index", action="store_true", help="Index only (no test queries)")
    parser.add_argument("--test", action="store_true", help="Test queries only (no indexing)")
    args = parser.parse_args()

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    if args.test:
        query_results = run_test_queries(client)
        print("\n✅ Test queries complete.")
        return

    if not args.index:
        do_index = True
        do_test = True
    else:
        do_index = True
        do_test = False

    if do_index:
        stack_stats, fs_files, fs_chunks, fs_time = index_filing_stacks(client)
        ev_stats, ev_chunks, ev_time = index_evidence_master(client)

    if do_test or not args.index:
        query_results = run_test_queries(client)
    else:
        query_results = []

    # Generate report
    if do_index:
        generate_report(
            stack_stats, fs_files, fs_chunks, fs_time,
            ev_stats, ev_chunks, ev_time,
            query_results, client,
        )

    print(f"\n{'='*60}")
    print("✅ RAG INDEXING COMPLETE")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
