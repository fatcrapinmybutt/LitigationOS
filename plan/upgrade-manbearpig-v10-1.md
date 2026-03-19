---
goal: "Upgrade MANBEARPIG from v9 to v10 with neural intent, ensemble scoring, and self-evolution v3"
version: 1.0
date_created: 2026-03-12
last_updated: 2026-03-12
owner: Andrew Pigors
status: 'Planned'
tags: [architecture, ai, upgrade]
---

# Introduction

![Status: Planned](https://img.shields.io/badge/status-Planned-blue)

Upgrade MANBEARPIG inference engine from v9.0 (TF-IDF + Naive Bayes + BM25) to v10.0 with neural intent classification, ensemble scoring, and self-evolution v3. All processing remains 100% offline. Backward-compatible with existing 140+ JSON-RPC methods.

## 1. Requirements & Constraints

- **REQ-001**: Neural intent classifier with ≥95% accuracy on 20+ categories
- **REQ-002**: Ensemble scoring fusing TF-IDF + BM25 + neural + semantic with RRF
- **REQ-003**: Self-evolution v3 with autonomous retraining triggered by quality thresholds
- **REQ-004**: Expand from 55 to 100+ skills with dependency resolution
- **CON-001**: CPU-only inference — no GPU requirement, <16 GB RAM
- **CON-002**: Model files <2 GB total
- **CON-003**: Zero network access — all local
- **CON-004**: P90 query latency <500ms
- **SEC-001**: No model telemetry or usage reporting

## 2. Implementation Steps

### Implementation Phase 1 — Neural Intent Classifier

- GOAL-001: Build and train a neural intent classifier to replace keyword-based routing

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-001 | Create training data: extract 5,000+ query-intent pairs from `litigation_context.db` query logs | | |
| TASK-002 | Define 20+ intent categories (motion_type, citation_lookup, deadline_query, evidence_search, etc.) | | |
| TASK-003 | Train sentence-transformer fine-tuned classifier using `all-MiniLM-L6-v2` | | |
| TASK-004 | Export trained model to ONNX format for fast CPU inference | | |
| TASK-005 | Create `00_SYSTEM/local_model/neural_intent_v2.py` — ONNX-based intent classifier | | |
| TASK-006 | Benchmark: achieve ≥95% accuracy on held-out 200-query test set | | |
| TASK-007 | Integrate into `inference_engine.py` as primary router (fall back to keyword on failure) | | |

### Implementation Phase 2 — Ensemble Scoring Framework

- GOAL-002: Build ensemble scorer that fuses multiple retrieval signals

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-008 | Refactor `ensemble_scorer.py` to support pluggable scorers with configurable weights | | |
| TASK-009 | Add dense vector scorer (cosine similarity from sentence embeddings) | | |
| TASK-010 | Add cross-encoder reranker (ONNX-exported `ms-marco-MiniLM-L-6-v2`) | | |
| TASK-011 | Implement RRF fusion: merge BM25, TF-IDF, dense, cross-encoder scores | | |
| TASK-012 | Add adaptive weight tuning: learn optimal weights from relevance feedback | | |
| TASK-013 | Benchmark: NDCG@10 improves ≥15% over v9 TF-IDF baseline | | |

### Implementation Phase 3 — Self-Evolution v3

- GOAL-003: Build autonomous model improvement with quality feedback loops

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-014 | Create quality feedback table: log query-answer-rating triples | | |
| TASK-015 | Build error pattern analyzer: identify systematic failure modes | | |
| TASK-016 | Build incremental retraining pipeline: update models from new feedback data | | |
| TASK-017 | Build shadow validation: test new model against old before swapping | | |
| TASK-018 | Implement quality gate: reject models that degrade accuracy | | |
| TASK-019 | Create evolution metrics dashboard in `evolution_state` table | | |

### Implementation Phase 4 — Skill Expansion & Testing

- GOAL-004: Expand skill library and comprehensive testing

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-020 | Implement 45 new skills to reach 100+ total (grouped by legal domain) | | |
| TASK-021 | Create `testdata/manbearpig_v10/test_queries.json` — 200-query test set | | |
| TASK-022 | Create `tests/test_manbearpig_v10.py` — unit tests for all new components | | |
| TASK-023 | Create benchmark suite: accuracy, latency, memory usage | | |
| TASK-024 | Run full regression: all 140+ JSON-RPC methods still pass | | |
| TASK-025 | Update `inference_engine.py` version string to v10.0 | | |

## 3. Alternatives

- **ALT-001**: Use Ollama for inference — rejected: violates zero-network/local-only constraint
- **ALT-002**: Use full BERT model — rejected: too large for CPU (3GB+), too slow (~2s per query)
- **ALT-003**: Keep TF-IDF only, improve features — rejected: ceiling on semantic understanding
- **ALT-004**: Use distilbert-base-uncased — considered: smaller than BERT, but MiniLM is better for classification

## 4. Dependencies

- **DEP-001**: ONNX Runtime ≥1.17 — neural model inference
- **DEP-002**: `sentence-transformers` ≥2.3 — embedding generation (training only)
- **DEP-003**: `scikit-learn` ≥1.3 — evaluation metrics
- **DEP-004**: `bm25s` — BM25 sparse retrieval
- **DEP-005**: `numpy` ≥1.24 — vector operations

## 5. Files

- **FILE-001**: `00_SYSTEM/local_model/inference_engine.py` — version bump + neural router integration (MODIFY)
- **FILE-002**: `00_SYSTEM/local_model/neural_intent_v2.py` — ONNX intent classifier (NEW)
- **FILE-003**: `00_SYSTEM/local_model/ensemble_scorer.py` — refactored ensemble (MODIFY)
- **FILE-004**: `00_SYSTEM/local_model/self_evolve_v3.py` — evolution v3 upgrade (MODIFY)
- **FILE-005**: `00_SYSTEM/local_model/model_data/intent_classifier.onnx` — trained model (NEW)
- **FILE-006**: `00_SYSTEM/local_model/model_data/cross_encoder.onnx` — reranker model (NEW)
- **FILE-007**: `testdata/manbearpig_v10/test_queries.json` — test dataset (NEW)
- **FILE-008**: `tests/test_manbearpig_v10.py` — test suite (NEW)

## 6. Testing

- **TEST-001**: Intent classifier achieves ≥95% accuracy on 200-query test set
- **TEST-002**: Ensemble NDCG@10 ≥ 0.15 improvement over TF-IDF baseline
- **TEST-003**: P90 latency <500ms on CPU (benchmark 100 sequential queries)
- **TEST-004**: All 140+ JSON-RPC methods pass regression tests
- **TEST-005**: Self-evolution cycle never degrades accuracy
- **TEST-006**: Model files total <2 GB

## 7. Risks & Assumptions

- **RISK-001**: ONNX Runtime CPU inference may be slower than expected — mitigate with model quantization
- **RISK-002**: Training data may be biased toward Pigors v Watson queries — mitigate with synthetic diverse queries
- **RISK-003**: Self-evolution could overfit to recent queries — mitigate with held-out validation set
- **ASSUMPTION-001**: 5,000+ query-intent pairs available in existing logs
- **ASSUMPTION-002**: MiniLM model fits in <500 MB as ONNX

## 8. Related Specifications / Further Reading

- [spec/spec-architecture-manbearpig-v10.md](/spec/spec-architecture-manbearpig-v10.md)
- [spec/spec-architecture-rag-pipeline.md](/spec/spec-architecture-rag-pipeline.md)
- [spec/spec-infrastructure-skill-framework.md](/spec/spec-infrastructure-skill-framework.md)
