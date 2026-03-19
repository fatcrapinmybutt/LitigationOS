#!/usr/bin/env python3
"""
MBP LitigationOS — Document Q&A Module
=======================================
TF-IDF passage retrieval over litigation_context.db.
Searches pages, md_sections, evidence_quotes, and watsons_evidence_docs.

Usage:
    python document_qa.py "What does the FOC report say about overnights?"
    python document_qa.py --evidence "testimony about parenting time"
    python document_qa.py --filings "motion for reconsideration"
    python document_qa.py --summarize 1

JSON-RPC (pipe):
    {"method": "document_qa", "text": "...", "doc_id": null}
    {"method": "document_qa_evidence", "text": "..."}
    {"method": "document_qa_filings", "text": "..."}
    {"method": "document_qa_summarize", "doc_id": 1}
"""

from __future__ import annotations

import json
import math
import os
import re
import sqlite3
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\LitigationOS\litigation_context.db",
)

# ── Stop words ─────────────────────────────────────────────────────
_STOP = frozenset(
    "the a an is are was were be been have has had do does did will would "
    "could should may might shall can to of in for on with at by from as "
    "what how when where why which who about this that and or but not if "
    "my me i it its they them their he she his her we our you your so no "
    "than then also very just even more most some any all each".split()
)


def _tokenize(text: str) -> List[str]:
    """Lowercase alpha-numeric tokens, drop stop words and short tokens."""
    return [
        w for w in re.sub(r"[^a-z0-9\s]", " ", text.lower()).split()
        if len(w) > 2 and w not in _STOP
    ]


# ── TF-IDF helpers (pure Python — no sklearn dependency) ──────────
def _build_tfidf(corpus_tokens: List[List[str]]) -> tuple:
    """Return (vocab dict, idf dict, tfidf vectors as list[dict])."""
    n_docs = len(corpus_tokens)
    if n_docs == 0:
        return {}, {}, []

    # document frequency
    df: Counter = Counter()
    for tokens in corpus_tokens:
        df.update(set(tokens))

    # idf: log(N / df) with smoothing
    idf = {term: math.log((n_docs + 1) / (freq + 1)) + 1 for term, freq in df.items()}

    # tf-idf vectors (sparse dicts)
    vectors = []
    for tokens in corpus_tokens:
        tf = Counter(tokens)
        total = len(tokens) or 1
        vec = {t: (c / total) * idf.get(t, 0) for t, c in tf.items()}
        vectors.append(vec)

    return df, idf, vectors


def _query_vector(tokens: List[str], idf: dict) -> dict:
    tf = Counter(tokens)
    total = len(tokens) or 1
    return {t: (c / total) * idf.get(t, 0) for t, c in tf.items() if t in idf}


def _cosine(a: dict, b: dict) -> float:
    if not a or not b:
        return 0.0
    keys = set(a) & set(b)
    if not keys:
        return 0.0
    dot = sum(a[k] * b[k] for k in keys)
    mag_a = math.sqrt(sum(v * v for v in a.values()))
    mag_b = math.sqrt(sum(v * v for v in b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


# ── Chunking ───────────────────────────────────────────────────────
def _chunk_text(text: str, target_words: int = 200, overlap_words: int = 40) -> List[str]:
    """Split text into overlapping ~target_words chunks."""
    words = text.split()
    if len(words) <= target_words:
        return [text] if words else []
    chunks = []
    start = 0
    while start < len(words):
        end = start + target_words
        chunks.append(" ".join(words[start:end]))
        start = end - overlap_words
    return chunks


class DocumentQA:
    """TF-IDF passage retrieval over the litigation context database."""

    def __init__(self, db_path: str = DB_PATH):
        self._db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    # ── DB connection ──────────────────────────────────────────────
    def _get_db(self) -> sqlite3.Connection:
        if self._conn:
            try:
                self._conn.execute("SELECT 1")
                return self._conn
            except Exception:
                self._conn = None
        self._conn = sqlite3.connect(self._db_path, timeout=30)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA query_only=ON")
        self._conn.row_factory = sqlite3.Row
        return self._conn

    # ── Passage loaders ────────────────────────────────────────────
    def _load_pages(
        self, doc_id: Optional[int] = None, file_path: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Load passages from pages table, chunked to ~200 words."""
        db = self._get_db()
        if doc_id is not None:
            rows = db.execute(
                "SELECT p.text_content, p.page_number, d.file_name, d.id AS doc_id "
                "FROM pages p JOIN documents d ON p.document_id = d.id "
                "WHERE d.id = ? ORDER BY p.page_number",
                (doc_id,),
            ).fetchall()
        elif file_path is not None:
            rows = db.execute(
                "SELECT p.text_content, p.page_number, d.file_name, d.id AS doc_id "
                "FROM pages p JOIN documents d ON p.document_id = d.id "
                "WHERE d.file_path LIKE ? OR d.file_name LIKE ? "
                "ORDER BY d.id, p.page_number",
                (f"%{file_path}%", f"%{file_path}%"),
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT p.text_content, p.page_number, d.file_name, d.id AS doc_id "
                "FROM pages p JOIN documents d ON p.document_id = d.id "
                "ORDER BY d.id, p.page_number"
            ).fetchall()

        passages = []
        for r in rows:
            for chunk in _chunk_text(r["text_content"]):
                passages.append({
                    "text": chunk,
                    "source_file": r["file_name"],
                    "page_number": r["page_number"],
                    "doc_id": r["doc_id"],
                    "source_table": "pages",
                })
        return passages

    def _load_md_sections(self, file_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        db = self._get_db()
        if file_filter:
            rows = db.execute(
                "SELECT content, source_file, section_title FROM md_sections "
                "WHERE source_file LIKE ? AND length(content) > 20 "
                "ORDER BY id LIMIT 50000",
                (f"%{file_filter}%",),
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT content, source_file, section_title FROM md_sections "
                "WHERE length(content) > 20 ORDER BY id LIMIT 50000"
            ).fetchall()

        passages = []
        for r in rows:
            for chunk in _chunk_text(r["content"]):
                passages.append({
                    "text": chunk,
                    "source_file": r["source_file"],
                    "section_title": r["section_title"],
                    "page_number": None,
                    "doc_id": None,
                    "source_table": "md_sections",
                })
        return passages

    def _load_watsons(self, file_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        db = self._get_db()
        if file_filter:
            rows = db.execute(
                "SELECT id, filename, content FROM watsons_evidence_docs "
                "WHERE content IS NOT NULL AND length(content) > 20 "
                "AND filename LIKE ? ORDER BY id",
                (f"%{file_filter}%",),
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT id, filename, content FROM watsons_evidence_docs "
                "WHERE content IS NOT NULL AND length(content) > 20 ORDER BY id"
            ).fetchall()

        passages = []
        for r in rows:
            for chunk in _chunk_text(r["content"]):
                passages.append({
                    "text": chunk,
                    "source_file": r["filename"],
                    "page_number": None,
                    "doc_id": r["id"],
                    "source_table": "watsons_evidence_docs",
                })
        return passages

    # ── Core search ────────────────────────────────────────────────
    def _rank_passages(
        self, question: str, passages: List[Dict[str, Any]], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """TF-IDF cosine similarity ranking of passages against question."""
        if not passages:
            return []

        q_tokens = _tokenize(question)
        if not q_tokens:
            return []

        corpus_tokens = [_tokenize(p["text"]) for p in passages]
        _df, idf, vectors = _build_tfidf(corpus_tokens)
        q_vec = _query_vector(q_tokens, idf)

        scored = []
        for i, vec in enumerate(vectors):
            score = _cosine(q_vec, vec)
            if score > 0:
                scored.append((score, i))

        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, idx in scored[:top_k]:
            p = passages[idx].copy()
            p["relevance_score"] = round(score, 4)
            results.append(p)
        return results

    # ── Public API ─────────────────────────────────────────────────
    def ask(
        self,
        question: str,
        doc_id: Optional[int] = None,
        file_path: Optional[str] = None,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        Ask a question about a specific document or search all docs.
        Loads from pages, watsons_evidence_docs, and (if searching all) md_sections.
        """
        t0 = time.time()
        passages: List[Dict[str, Any]] = []

        # Load from pages
        passages.extend(self._load_pages(doc_id=doc_id, file_path=file_path))

        # Load from watson evidence docs
        passages.extend(self._load_watsons(file_filter=file_path))

        # If broad search (no specific doc), include a keyword-filtered md_sections slice
        if doc_id is None and file_path is None:
            keywords = _tokenize(question)
            if keywords:
                # Use first 3 keywords as file filter to keep it manageable
                for kw in keywords[:3]:
                    passages.extend(self._load_md_sections(file_filter=kw))

        results = self._rank_passages(question, passages, top_k=top_k)
        elapsed = round((time.time() - t0) * 1000, 1)

        return {
            "question": question,
            "results": results,
            "result_count": len(results),
            "passages_searched": len(passages),
            "elapsed_ms": elapsed,
            "status": "ok",
        }

    def ask_evidence(self, question: str, top_k: int = 10) -> Dict[str, Any]:
        """Search evidence_quotes for relevant evidence."""
        t0 = time.time()
        db = self._get_db()
        rows = db.execute(
            "SELECT eq.id, eq.document_id, eq.evidence_category, eq.quote_text, "
            "eq.speaker, eq.legal_significance, eq.page_number, eq.quote_type, "
            "d.file_name "
            "FROM evidence_quotes eq "
            "LEFT JOIN documents d ON eq.document_id = d.id "
            "WHERE eq.quote_text IS NOT NULL"
        ).fetchall()

        # Build passages from quote_text + legal_significance
        passages = []
        meta = []
        for r in rows:
            combined = (r["quote_text"] or "") + " " + (r["legal_significance"] or "")
            passages.append({
                "text": combined,
                "source_file": r["file_name"] or "unknown",
                "page_number": r["page_number"],
                "doc_id": r["document_id"],
                "source_table": "evidence_quotes",
            })
            meta.append({
                "quote_id": r["id"],
                "speaker": r["speaker"],
                "category": r["evidence_category"],
                "quote_type": r["quote_type"],
                "legal_significance": r["legal_significance"],
            })

        ranked = self._rank_passages(question, passages, top_k=top_k)

        # Merge meta into results
        results = []
        for res in ranked:
            # Find the matching meta entry by text
            for i, p in enumerate(passages):
                if p["text"] == res["text"]:
                    merged = {**res, **meta[i]}
                    # Replace combined text with just the quote
                    rows_match = [
                        row for row in rows
                        if row["id"] == meta[i]["quote_id"]
                    ]
                    if rows_match:
                        merged["quote_text"] = rows_match[0]["quote_text"]
                    results.append(merged)
                    break

        elapsed = round((time.time() - t0) * 1000, 1)
        return {
            "question": question,
            "results": results,
            "result_count": len(results),
            "evidence_searched": len(passages),
            "elapsed_ms": elapsed,
            "status": "ok",
        }

    def ask_filings(self, question: str, top_k: int = 10) -> Dict[str, Any]:
        """Search across all court filings in md_sections."""
        t0 = time.time()
        passages = self._load_md_sections()
        results = self._rank_passages(question, passages, top_k=top_k)
        elapsed = round((time.time() - t0) * 1000, 1)

        return {
            "question": question,
            "results": results,
            "result_count": len(results),
            "sections_searched": len(passages),
            "elapsed_ms": elapsed,
            "status": "ok",
        }

    def summarize_document(self, doc_id: int) -> Dict[str, Any]:
        """
        Extractive summary: score passages by TF-IDF term importance,
        return top 10 most informative.
        """
        t0 = time.time()
        db = self._get_db()

        # Get document info
        doc = db.execute(
            "SELECT id, file_name, file_path, page_count FROM documents WHERE id = ?",
            (doc_id,),
        ).fetchone()
        if not doc:
            return {"error": f"Document {doc_id} not found", "status": "error"}

        # Load all passages for this document
        passages = self._load_pages(doc_id=doc_id)
        if not passages:
            # Fallback to watsons
            passages = self._load_watsons(file_filter=doc["file_name"])
        if not passages:
            return {
                "error": f"No text content found for document {doc_id}",
                "doc_name": doc["file_name"],
                "status": "error",
            }

        # Score each passage by information density (sum of TF-IDF weights)
        corpus_tokens = [_tokenize(p["text"]) for p in passages]
        _df, idf, vectors = _build_tfidf(corpus_tokens)

        scored = []
        for i, vec in enumerate(vectors):
            # Information density = sum of TF-IDF weights / word count
            density = sum(vec.values()) / (len(corpus_tokens[i]) or 1)
            word_count = len(passages[i]["text"].split())
            # Prefer passages with reasonable length (not too short)
            length_bonus = min(word_count / 100, 1.0)
            scored.append((density * length_bonus, i))

        scored.sort(key=lambda x: x[0], reverse=True)

        # Take top 10, reorder by page number for readability
        top_indices = [idx for _, idx in scored[:10]]
        top_indices.sort(key=lambda i: (passages[i].get("page_number") or 0, i))

        summary_passages = []
        for idx in top_indices:
            p = passages[idx].copy()
            p["density_score"] = round(scored[
                next(j for j, (_, i) in enumerate(scored) if i == idx)
            ][0], 4)
            summary_passages.append(p)

        elapsed = round((time.time() - t0) * 1000, 1)
        return {
            "doc_id": doc_id,
            "doc_name": doc["file_name"],
            "page_count": doc["page_count"],
            "summary_passages": summary_passages,
            "passage_count": len(summary_passages),
            "total_passages": len(passages),
            "elapsed_ms": elapsed,
            "status": "ok",
        }

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None


# ── CLI ────────────────────────────────────────────────────────────
def _print_results(data: dict):
    """Pretty-print Q&A results to terminal."""
    results = data.get("results") or data.get("summary_passages") or []
    if data.get("status") == "error":
        print(f"ERROR: {data.get('error')}", file=sys.stderr)
        return

    header = data.get("question") or f"Summary of doc {data.get('doc_id')}"
    print(f"\n{'='*72}")
    print(f"  Q: {header}")
    print(f"{'='*72}")

    if not results:
        print("  No results found.")
    else:
        for i, r in enumerate(results, 1):
            score = r.get("relevance_score") or r.get("density_score", 0)
            src = r.get("source_file", "?")
            page = r.get("page_number")
            loc = f"p.{page}" if page else r.get("section_title", "")
            print(f"\n  [{i}] score={score:.4f}  |  {src}  |  {loc}")
            if r.get("speaker"):
                print(f"      speaker: {r['speaker']}  category: {r.get('category','')}")
            text = r.get("quote_text") or r.get("text", "")
            # Truncate display to 300 chars
            display = text[:300].replace("\n", " ")
            if len(text) > 300:
                display += "..."
            print(f"      {display}")

    stats_parts = []
    for key in ("passages_searched", "sections_searched", "evidence_searched", "total_passages"):
        if key in data:
            stats_parts.append(f"{key}={data[key]}")
    stats_parts.append(f"elapsed={data.get('elapsed_ms', 0)}ms")
    print(f"\n  --- {' | '.join(stats_parts)} ---\n")


def main():
    qa = DocumentQA()

    if "--pipe" in sys.argv:
        # JSON-RPC mode — Cycle Method: 4KB chunks, zero EAGAIN
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        try:
            from cycle_method import cycle_json, cycle_print
        except ImportError:
            # Fallback if cycle_method not found
            def cycle_json(obj, **kw):
                sys.stdout.write(json.dumps(obj, default=str) + "\n")
                sys.stdout.flush()
            cycle_print = print

        def _safe_write(data_str):
            """Write to stdout using Cycle Method — zero EAGAIN."""
            obj = json.loads(data_str) if isinstance(data_str, str) else data_str
            cycle_json(obj)

        _safe_write(json.dumps({"ready": True, "module": "document_qa"}))
        for line in sys.stdin:
            try:
                line = line.strip()
                if not line:
                    continue
                req = json.loads(line)
                method = req.get("method", "ask")
                if method in ("ask", "document_qa"):
                    result = qa.ask(
                        req.get("text", ""),
                        doc_id=req.get("doc_id"),
                        file_path=req.get("file_path"),
                        top_k=req.get("top_k", 5),
                    )
                elif method in ("ask_evidence", "document_qa_evidence"):
                    result = qa.ask_evidence(req.get("text", ""), top_k=req.get("top_k", 10))
                elif method in ("ask_filings", "document_qa_filings"):
                    result = qa.ask_filings(req.get("text", ""), top_k=req.get("top_k", 10))
                elif method in ("summarize", "document_qa_summarize"):
                    result = qa.summarize_document(req.get("doc_id", 0))
                else:
                    result = {"error": f"Unknown method: {method}"}
                _safe_write(json.dumps(result, default=str))
            except json.JSONDecodeError:
                _safe_write(json.dumps({"error": "Invalid JSON"}))
            except Exception as e:
                _safe_write(json.dumps({"error": str(e)[:200]}))
        qa.close()
        return

    if "--evidence" in sys.argv:
        idx = sys.argv.index("--evidence")
        text = " ".join(sys.argv[idx + 1:])
        _print_results(qa.ask_evidence(text))
    elif "--filings" in sys.argv:
        idx = sys.argv.index("--filings")
        text = " ".join(sys.argv[idx + 1:])
        _print_results(qa.ask_filings(text))
    elif "--summarize" in sys.argv:
        idx = sys.argv.index("--summarize")
        doc_id = int(sys.argv[idx + 1]) if idx + 1 < len(sys.argv) else 1
        _print_results(qa.summarize_document(doc_id))
    elif len(sys.argv) > 1 and sys.argv[1] != "--help":
        text = " ".join(sys.argv[1:])
        _print_results(qa.ask(text))
    else:
        print("MBP LitigationOS — Document Q&A")
        print("Usage:")
        print('  python document_qa.py "your question"')
        print('  python document_qa.py --evidence "testimony about custody"')
        print('  python document_qa.py --filings "motion for reconsideration"')
        print("  python document_qa.py --summarize 1")
        print("  python document_qa.py --pipe   # JSON-RPC mode")

    qa.close()


if __name__ == "__main__":
    main()
