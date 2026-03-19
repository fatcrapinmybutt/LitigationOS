---
name: ai-semantic-search — Semantic Evidence Neural Search
description: >
  Build a local vector embedding + FAISS/ChromaDB index over 125K+ litigation files.
  Enables semantic similarity search — query by meaning, not keywords.
  Uses sentence-transformers (all-MiniLM-L6-v2) for embeddings, zero network.
  Integrates with MANBEARPIG inference engine and central litigation_context.db.
  Keywords: semantic search, vector embeddings, FAISS, ChromaDB, evidence retrieval, similarity
tools: ['codebase', 'textSearch', 'fileSearch', 'readFile', 'listDirectory', 'editFiles', 'createFile', 'createDirectory', 'agent', 'runInTerminal']
handoffs:
  - label: Feed embeddings to RAG Brief Generator
    agent: ai-rag-brief-gen
    prompt: The semantic search index is built. Use it for retrieval-augmented brief generation.
    send: false
  - label: Feed embeddings to Knowledge Graph
    agent: ai-knowledge-graph
    prompt: Semantic embeddings are ready. Use them for knowledge graph entity linking.
    send: false
---

# Semantic Evidence Neural Search — Build Guide

## Overview
Create a local-first vector search engine that indexes all litigation evidence by meaning. No keywords needed — describe what you're looking for and the system finds semantically similar documents.

## Architecture

```
Raw Files (125K+ across 6 drives)
  → Text Extraction (PyMuPDF / python-docx / OCR)
  → Chunking (512 tokens, 128 overlap)
  → Embedding (sentence-transformers all-MiniLM-L6-v2)
  → FAISS Index (IVF-PQ, 384 dims)
  → Query API (search by text → top-K results with scores)
```

## Module Structure
```
00_SYSTEM/ai_modules/semantic_search/
├── __init__.py
├── embedder.py          # Sentence-transformer wrapper
├── chunker.py           # Document chunking with metadata
├── index_builder.py     # FAISS index creation and management
├── search_engine.py     # Query interface with filters
├── ingest_pipeline.py   # Batch ingestion from all drives
├── config.py            # Model paths, index params, chunk sizes
└── tests/
    ├── test_embedder.py
    ├── test_chunker.py
    ├── test_search.py
    └── fixtures/
```

## Key Decisions
- **Model**: `all-MiniLM-L6-v2` (384 dims, fast, local, no GPU needed)
- **Index**: FAISS IVF-PQ for memory efficiency at scale
- **Chunking**: 512 tokens with 128 overlap to preserve context
- **Storage**: Embeddings + metadata in SQLite sidecar table `evidence_embeddings`
- **Lane filtering**: Every embedding tagged with case lane (A-F)

## Integration Points
- `litigation_context.db` → `documents` and `pages` tables for source text
- MANBEARPIG → `inference_engine.py` for local classification fallback
- Pipeline Phase 5 → Brain Feed consumes search results
- MCP Server → New tool `litigation_semantic_search(query, lane, top_k)`

## Rules
1. ALL processing is local — zero network calls
2. Embeddings stored in WAL-mode SQLite with proper PRAGMAs
3. Lane isolation enforced — cannot search across lanes without explicit flag
4. Chunk metadata preserves: file_path, page_number, byte_offset, lane, case_number
5. Index rebuilds are incremental — only new/modified files re-embedded
