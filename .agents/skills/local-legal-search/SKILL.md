---
name: local-legal-search
description: "Local legal search over 694-table litigation database. Uses MANBEARPIG TF-IDF + FTS5 + BM25. Zero network, zero cost. Replaces Tavily/Exa. Triggers: search, legal search, find authority, MCR, MCL, case law, statute, research, look up"
---

# Local Legal Search

Search the entire LitigationOS litigation database locally. No API keys. No cloud.

## Quick Start

```python
from sdk import inference

client = inference()

# Simple search
result = client.run({"app": "legal-search", "input": {"query": "MCR 2.003 disqualification"}})
print(result["output"]["response"])

# Authority search
result = client.run({"app": "authority-search", "input": {"topic": "parental alienation", "limit": 10}})

# Multi-jurisdiction
result = client.run({"app": "multi-juris", "input": {"topic": "ex parte communication", "jurisdictions": ["mi_circuit", "coa", "jtc"]}})
```

## Available Apps

| App ID | Description | MANBEARPIG Method |
|--------|-------------|-------------------|
| `legal-search` | Full-text + TF-IDF search | `model.query()` |
| `authority-search` | MCR, MCL, case law lookup | `model.find_authority()` |
| `citation-check` | Verify citations against DB | `model.check_citations()` |
| `multi-juris` | Cross-jurisdiction query | `model.multi_jurisdiction_query()` |
| `concepts` | Legal concept matching | `model.match_concepts()` |
| `entities` | Entity extraction (MCR, MCL, names) | `model.extract_entities()` |

## RAG Pipeline

```python
from sdk.rag_pipeline import RAGPipeline

rag = RAGPipeline()
result = rag.research("judicial disqualification for bias")
print(f"Found {len(result.sources)} sources, confidence: {result.confidence}")
```

## Architecture

```
User Query
  → FTS5 full-text search (694 tables, 10.22 GB)
  → TF-IDF cosine similarity (50K features, trigram)
  → BM25 scoring (HybridRetriever when available)
  → Legal concept KB matching
  → Authority chain lookup
  → Template response generation
  → Structured result with confidence score
```
