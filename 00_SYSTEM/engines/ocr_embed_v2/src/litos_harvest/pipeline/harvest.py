from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple
import sqlite3

from ..run_ledger import RunLedger
from ..scanner import iter_files
from ..utils import sha256_file, safe_relpath, ensure_dir, normalize_text
from ..chunking import chunk_text
from ..embeddings import make_embedder
from ..extractors.texts import TextExtractor
from ..extractors.csvs import CSVExtractor
from ..extractors.docx import DocxExtractor
from ..extractors.images import ImageOCRExtractor
from ..extractors.pdfs import PDFExtractor
from ..extractors.archives import is_zip, iter_zip_members
from ..index.fts_sqlite import init_db, upsert_doc, upsert_chunks
from ..index.qdrant_index import ensure_collection, upsert_points

def run_harvest(cfg: Dict[str, Any], scan_root: Path, run_id: str, out_dir: Path) -> None:
    ledger = RunLedger(out_dir / "run_ledger.jsonl")
    ledger.info("run_start", run_id=run_id, scan_root=str(scan_root))

    # outputs
    ensure_dir(out_dir)
    db_path = out_dir / "fts.sqlite"
    init_db(db_path)

    # extractors
    pdf_cfg = cfg.get("pdf") or {}
    ocr_cfg = cfg.get("ocr") or {}
    pdf_ex = PDFExtractor(
        ocr_enabled=bool(ocr_cfg.get("enabled", True)),
        ocr_lang=str(ocr_cfg.get("lang","eng")),
        min_chars_to_accept_text_layer=int(ocr_cfg.get("min_chars_to_accept_text_layer", 50)),
        render_dpi=int(pdf_cfg.get("render_dpi", 200)),
        max_pages_for_ocr=int(pdf_cfg.get("max_pages_for_ocr", 200)),
    )
    exts = [
        pdf_ex,
        DocxExtractor(),
        CSVExtractor(),
        TextExtractor(),
        ImageOCRExtractor(lang=str(ocr_cfg.get("lang","eng"))),
    ]

    include_exts = cfg.get("include_extensions") or []
    ignore_globs = cfg.get("ignore_globs") or []
    max_file_mb = float((cfg.get("run") or {}).get("max_file_mb", 200))
    max_files = int((cfg.get("run") or {}).get("max_files", 250000))

    # chunk/index config
    idx_cfg = cfg.get("index") or {}
    chunk_size = int(idx_cfg.get("chunk_size", 900))
    overlap = int(idx_cfg.get("chunk_overlap", 150))
    use_qdrant = bool(idx_cfg.get("qdrant", True))
    collection = str(idx_cfg.get("qdrant_collection", "litigationos_chunks"))
    embed_backend = str(idx_cfg.get("embedding_backend", "sentence_transformers"))
    embed_model = str(idx_cfg.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2"))
    ollama_url = "http://127.0.0.1:11434/api/embed"
    ollama_model = str(idx_cfg.get("ollama_embed_model", "embeddinggemma"))

    embedder = None
    qclient = None
    vector_size = None

    if use_qdrant:
        # lazy init embedder + qdrant on first chunk
        pass

    inv_rows: List[Dict[str, Any]] = []
    quote_rows: List[Dict[str, Any]] = []

    con = sqlite3.connect(str(db_path))
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")

    def _pick_extractor(p: Path):
        for ex in exts:
            if ex.can_handle(p):
                return ex
        return None

    # Walk real files
    for p, rel in iter_files(scan_root, include_exts, ignore_globs, max_file_mb, max_files):
        try:
            # Archive handling
            if is_zip(p) and bool((cfg.get("archives") or {}).get("include_zip", True)):
                ledger.info("zip_found", path=str(p))
                for member_name, raw in iter_zip_members(p):
                    # write member to temp file for extraction
                    # we keep it deterministic in out_dir/.tmp
                    tmp_dir = out_dir / ".tmp_zip"
                    ensure_dir(tmp_dir)
                    safe_name = member_name.replace("/", "__").replace("\\", "__")
                    tmp_path = tmp_dir / safe_name
                    try:
                        tmp_path.write_bytes(raw)
                    except Exception:
                        continue
                    ex = _pick_extractor(tmp_path)
                    if not ex:
                        continue
                    _process_file(tmp_path, f"{rel}::{member_name}", p, con, inv_rows, quote_rows,
                                  ex, chunk_size, overlap,
                                  use_qdrant, collection,
                                  idx_cfg, ledger,
                                  embed_backend, embed_model, ollama_url, ollama_model)
                continue

            ex = _pick_extractor(p)
            if not ex:
                continue
            _process_file(p, rel, None, con, inv_rows, quote_rows,
                          ex, chunk_size, overlap,
                          use_qdrant, collection,
                          idx_cfg, ledger,
                          embed_backend, embed_model, ollama_url, ollama_model)
        except Exception as e:
            ledger.error("file_failed", path=str(p), err=str(e))
            continue

    con.commit()
    con.close()

    # Write inventory
    _write_inventory(out_dir, inv_rows)
    _write_quotes(out_dir, quote_rows)
    _write_timeline(out_dir, inv_rows)
    _write_dashboard(out_dir, run_id, len(inv_rows))
    _write_next_prompt(out_dir, run_id)

    ledger.info("run_complete", docs=len(inv_rows))

def _process_file(p: Path, rel: str, parent_archive: Path | None,
                  con, inv_rows, quote_rows,
                  ex,
                  chunk_size, overlap,
                  use_qdrant, collection,
                  idx_cfg, ledger,
                  embed_backend, embed_model, ollama_url, ollama_model):

    mtime = p.stat().st_mtime if p.exists() else time.time()
    sha = sha256_file(p) if p.exists() else ""
    doc_id = sha[:16] + "_" + str(abs(hash(rel)) % (10**8))
    path_str = rel

    res = ex.extract(p)
    text = normalize_text(res.text)
    if not text:
        ledger.warn("no_text", path=path_str)
        return

    meta_json = json.dumps(res.meta, ensure_ascii=False)

    doc = {"doc_id": doc_id, "path": path_str, "sha256": sha, "mtime": mtime, "meta_json": meta_json}
    upsert_doc(con, doc)

    # Chunk
    chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
    chunk_rows = []
    for idx, c in enumerate(chunks):
        chunk_id = sha[:16] + f"_{idx:05d}"
        c.chunk_id = chunk_id
        chunk_rows.append({"chunk_id": chunk_id, "doc_id": doc_id, "path": path_str, "text": c.text})

    upsert_chunks(con, chunk_rows)

    inv_rows.append({
        "doc_id": doc_id,
        "path": path_str,
        "sha256": sha,
        "mtime": mtime,
        "chars": len(text),
        "meta_json": meta_json,
    })

    # minimal quote extraction: first 3 non-empty lines as snippets
    lines = [ln.strip() for ln in (res.text or "").splitlines() if ln.strip()]
    for i, ln in enumerate(lines[:3]):
        quote_rows.append({"doc_id": doc_id, "path": path_str, "quote": ln[:500], "locator": f"line:{i+1}"})

    # Qdrant indexing (lazy init)
    if use_qdrant:
        try:
            from qdrant_client import QdrantClient
            qurl = "http://127.0.0.1:6333"
            qclient = QdrantClient(url=qurl, prefer_grpc=False)
            # init embedder
            from ..embeddings import make_embedder
            embedder = make_embedder(embed_backend, embed_model, ollama_url, ollama_model)
            vecs = embedder.embed([c["text"] for c in chunk_rows[:128]])  # sample to learn size
            vsize = int(vecs.shape[1])
            ensure_collection(qclient, collection, vsize)

            # embed all chunks in batches
            B = 64
            for start in range(0, len(chunk_rows), B):
                batch = chunk_rows[start:start+B]
                vecs = embedder.embed([b["text"] for b in batch])
                points = []
                for j, b in enumerate(batch):
                    points.append({
                        "id": b["chunk_id"],
                        "vector": vecs[j].tolist(),
                        "payload": {"doc_id": b["doc_id"], "path": b["path"]}
                    })
                from ..index.qdrant_index import upsert_points
                upsert_points(qclient, collection, points)
        except Exception as e:
            ledger.warn("qdrant_failed", path=path_str, err=str(e))

def _write_inventory(out_dir: Path, rows: List[Dict[str, Any]]) -> None:
    import csv
    p = out_dir / "inventory.csv"
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["doc_id","path","sha256","mtime","chars","meta_json"])
        w.writeheader()
        for r in rows:
            w.writerow(r)

def _write_quotes(out_dir: Path, rows: List[Dict[str, Any]]) -> None:
    import json
    p = out_dir / "quotes.jsonl"
    with p.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def _write_timeline(out_dir: Path, inv_rows: List[Dict[str, Any]]) -> None:
    # very simple: file mtime as date
    import csv
    from datetime import datetime
    p = out_dir / "timeline.csv"
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["when_utc","path","doc_id","sha256"])
        w.writeheader()
        for r in sorted(inv_rows, key=lambda x: x["mtime"]):
            when = datetime.utcfromtimestamp(float(r["mtime"])).isoformat() + "Z"
            w.writerow({"when_utc": when, "path": r["path"], "doc_id": r["doc_id"], "sha256": r["sha256"]})

def _write_dashboard(out_dir: Path, run_id: str, doc_count: int) -> None:
    dash = out_dir / "DASHBOARD.md"
    dash.write_text(f"""# Harvest Dashboard — {run_id}

Docs indexed: **{doc_count}**

## Key outputs
- inventory.csv — all harvested documents
- timeline.csv — rough chronological spine (file mtimes)
- quotes.jsonl — quick snippets for LLM targeting
- fts.sqlite — keyword search index (FTS5)
- NEXT_PROMPT.md — paste into Gemini/Copilot/ChatGPT for synthesis

## Notes
- If Qdrant is running, semantic vectors were also upserted into the local collection.
- If OCR was unavailable, PDFs without text layers may be partially missing. Install Tesseract and re-run.
""", encoding="utf-8")

def _write_next_prompt(out_dir: Path, run_id: str) -> None:
    p = out_dir / "NEXT_PROMPT.md"
    p.write_text(f"""# NEXT_PROMPT — LitigationOS synthesis kickoff (run {run_id})

You have a harvested record index in this folder.

1) Read `DASHBOARD.md`.
2) Use `inventory.csv`, `timeline.csv`, and `quotes.jsonl` to build a **case-accurate narrative**.
3) Identify:
   - negative connotations / prejudicial phrasing to rebut
   - due process defects, notice defects, preservation gaps
   - Michigan-vehicle candidates: trial motions / COA / MSC / JTC
4) Produce a PACK PLAN:
   - CASE_STATE (<=25 lines)
   - VehicleMap (2–3 best paths)
   - Required record items and acquisition plan (subpoenas/transcripts/ROA)
   - Draft stack outline (motions/briefs/orders) with Michigan-only authority triples + pinpoints
Hard rule: no invented facts; all facts must cite a harvested artifact (path+page/line if possible) or be tagged UNKNOWN.
""", encoding="utf-8")

