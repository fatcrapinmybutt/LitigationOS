# Local semantic layer (optional) — FIX11
Build stamp (local): 2026-01-20 07:31:40

This is an optional module intended to add:
- local embeddings
- local rerank
- auditable retrieval artifacts

It is OFF by default and does not affect core pipeline execution.

## Recommended free models (Hugging Face)
Embeddings:
- https://hf.co/BAAI/bge-small-en-v1.5  (license: MIT)

Reranker:
- https://hf.co/BAAI/bge-reranker-base (license: MIT)

## Install deps (optional)
From `F:\L3\sem\`:
`python -m pip install -r requirements_sem.txt`

## Build an embedding index (example)
`python sem_build.py --root F:\L3 --out F:\L3\sp\sem\index.jsonl --limit 5000`

## What it writes (auditable)
- `sp\sem\index.jsonl` : one row per chunk with {path, chunk_id, text_sha1, embedding_model, vec_sha1, chars}
- `sp\sem\runlog.jsonl`: queries/hits/scores (if/when you add search)

## Notes
- This module avoids any paid services.
- Model downloads occur on your machine (Hugging Face), not in this pack.
