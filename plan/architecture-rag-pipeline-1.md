---
goal: "Build RAG pipeline with vector search, cross-encoder reranking, and knowledge graph"
version: 1.0
date_created: 2026-03-12
last_updated: 2026-03-12
owner: Andrew Pigors
status: 'Planned'
tags: [architecture, ai, rag, retrieval]
---

# Introduction

![Status: Planned](https://img.shields.io/badge/status-Planned-blue)

Build a production-grade RAG pipeline that adds dense vector search, cross-encoder reranking, and knowledge graph traversal to the existing hybrid retriever (BM25 + FTS5 + LSI). Enables semantic legal queries with citation-grounded answers.

## 1. Requirements & Constraints

- **REQ-001**: Dense vector index over ≥100K documents
- **REQ-002**: Cross-encoder reranker rescoring top-50 to produce top-10
- **REQ-003**: Knowledge graph connecting cases, rules, parties, judges, events
- **REQ-004**: Corrective RAG: expand query and retry on low-quality retrieval
- **CON-001**: CPU-only — no GPU, embeddings generated offline in batch
- **CON-002**: Vector index <5 GB for 100K documents
- **CON-003**: Query latency <2 seconds (retrieval + reranking)
- **SEC-001**: All embeddings local — no API calls

## 2. Implementation Steps

### Implementation Phase 1 — Vector Index

- GOAL-001: Build dense vector index over litigation documents

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-001 | Choose vector store: chromadb local persistence vs custom SQLite ANN | | |
| TASK-002 | Create `00_SYSTEM/local_model/vector_indexer.py` — batch embedding generator | | |
| TASK-003 | Generate embeddings for top tables: evidence_quotes, auth_rules, master_citations | | |
| TASK-004 | Build vector index from embeddings (~100K documents) | | |
| TASK-005 | Implement incremental index update: new documents indexed within 60 seconds | | |
| TASK-006 | Benchmark: vector search returns relevant results for 20 test queries | | |

### Implementation Phase 2 — Cross-Encoder Reranker

- GOAL-002: Add cross-encoder reranking for precision improvement

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-007 | Export `cross-encoder/ms-marco-MiniLM-L-6-v2` to ONNX | | |
| TASK-008 | Create `00_SYSTEM/local_model/cross_encoder_reranker.py` — ONNX-based reranker | | |
| TASK-009 | Implement: take top-50 from sparse+dense → rescore with cross-encoder → return top-10 | | |
| TASK-010 | Benchmark: NDCG@10 improves ≥20% over BM25-only | | |

### Implementation Phase 3 — Knowledge Graph

- GOAL-003: Build entity-relationship knowledge graph for graph-enhanced retrieval

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-011 | Create KG tables: `kg_entities`, `kg_relationships`, `kg_document_links` (see spec) | | |
| TASK-012 | Populate entities: extract cases, rules, parties, judges from DB | | |
| TASK-013 | Populate relationships: cites, involves, presided_by, filed_in, related_to | | |
| TASK-014 | Create `00_SYSTEM/local_model/kg_retriever.py` — graph-enhanced retrieval | | |
| TASK-015 | Implement: query → entity extraction → graph traversal → related docs → merge with retrieval | | |

### Implementation Phase 4 — Corrective RAG & Integration

- GOAL-004: Build corrective feedback loop and integrate with MANBEARPIG

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-016 | Create `00_SYSTEM/local_model/corrective_rag_v2.py` — corrective retrieval | | |
| TASK-017 | Implement: score top-3 → if <0.5 → expand query → re-retrieve | | |
| TASK-018 | Integrate all retrievers into unified `RAGPipeline` class | | |
| TASK-019 | Implement RRF fusion: merge BM25 + dense + FTS5 + KG scores | | |
| TASK-020 | Wire `RAGPipeline` into `HybridRetriever` as enhanced backend | | |
| TASK-021 | Source attribution: attach exact document/page/paragraph citations to every answer | | |

### Implementation Phase 5 — Testing & Benchmarks

- GOAL-005: Comprehensive testing and retrieval quality benchmarks

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-022 | Create `testdata/rag/test_queries.json` — 50 queries with human relevance judgments | | |
| TASK-023 | Create `tests/test_rag_pipeline.py` — unit + integration tests | | |
| TASK-024 | Benchmark: NDCG@10 ≥ 0.7 on test set | | |
| TASK-025 | Benchmark: P90 latency <2 seconds | | |
| TASK-026 | Benchmark: KG enriches results for ≥30% of queries | | |

## 3. Alternatives

- **ALT-001**: Use Pinecone/Weaviate cloud — rejected: violates local-only constraint
- **ALT-002**: Use FAISS — considered: fast but complex to maintain, chromadb simpler
- **ALT-003**: Use Neo4j for knowledge graph — rejected: heavy dependency, SQLite is sufficient
- **ALT-004**: Skip cross-encoder, use bi-encoder only — rejected: bi-encoder lacks precision for top-10

## 4. Dependencies

- **DEP-001**: `sentence-transformers` — embedding generation
- **DEP-002**: ONNX Runtime — cross-encoder inference
- **DEP-003**: `chromadb` — local vector store (or custom SQLite ANN)
- **DEP-004**: `numpy` — vector operations
- **DEP-005**: Existing `hybrid_retriever.py`, `graph_rag.py`, `reranker.py` (reference)

## 5. Files

- **FILE-001**: `00_SYSTEM/local_model/vector_indexer.py` (NEW)
- **FILE-002**: `00_SYSTEM/local_model/cross_encoder_reranker.py` (NEW)
- **FILE-003**: `00_SYSTEM/local_model/kg_retriever.py` (NEW)
- **FILE-004**: `00_SYSTEM/local_model/corrective_rag_v2.py` (NEW)
- **FILE-005**: `00_SYSTEM/local_model/rag_pipeline.py` — unified pipeline (NEW)
- **FILE-006**: `00_SYSTEM/local_model/hybrid_retriever.py` (MODIFY — wire in RAG)
- **FILE-007**: `testdata/rag/test_queries.json` (NEW)
- **FILE-008**: `tests/test_rag_pipeline.py` (NEW)

## 6. Testing

- **TEST-001**: Vector search returns relevant results for 20 test queries
- **TEST-002**: Cross-encoder improves NDCG@10 by ≥20%
- **TEST-003**: Knowledge graph provides related entities for MCR queries
- **TEST-004**: Corrective RAG improves results for ≥70% of poor initial retrievals
- **TEST-005**: Full pipeline P90 latency <2 seconds

## 7. Risks & Assumptions

- **RISK-001**: Embedding 100K documents may take hours — mitigate with batch processing overnight
- **RISK-002**: chromadb local persistence may be slow on large indexes — mitigate with SQLite fallback
- **RISK-003**: Cross-encoder ONNX export may lose accuracy — mitigate with benchmark validation
- **ASSUMPTION-001**: `sentence-transformers` installs cleanly on Windows with Python 3.12
- **ASSUMPTION-002**: 100K documents fit in RAM during embedding batch

## 8. Related Specifications / Further Reading

- [spec/spec-architecture-rag-pipeline.md](/spec/spec-architecture-rag-pipeline.md)
- [spec/spec-architecture-manbearpig-v10.md](/spec/spec-architecture-manbearpig-v10.md)
- [plan/upgrade-manbearpig-v10-1.md](/plan/upgrade-manbearpig-v10-1.md)
