---
name: ai-knowledge-graph — Self-Evolving Knowledge Graph
description: >
  A knowledge graph that grows itself. Auto-discovers entities, relationships,
  and patterns from new evidence. Nightly evolution cycles. Morning reports
  with new connections, contradictions, and gaps closed.
  Keywords: knowledge graph, entities, relationships, evolution, Neo4j, discovery
tools: ['codebase', 'textSearch', 'fileSearch', 'readFile', 'listDirectory', 'editFiles', 'createFile', 'createDirectory', 'agent', 'runInTerminal']
handoffs:
  - label: Feed graph to Argument Builder
    agent: ai-argument-graph
    prompt: Knowledge graph entities and relationships ready for argument mapping.
    send: false
  - label: Feed gaps to Discovery Generator
    agent: ai-discovery-gen
    prompt: Knowledge graph gap analysis ready. Generate targeted discovery requests.
    send: false
---

# Self-Evolving Knowledge Graph

## Overview
A litigation knowledge graph that automatically grows as new evidence arrives. Entities (people, places, events, documents) and relationships (testified, filed, violated, contradicted) are extracted and linked. The graph evolves nightly, discovering patterns and flagging changes.

## Architecture
```
New Evidence Ingested
  → NER (Named Entity Recognition — local spaCy)
  → Relation Extraction (subject-verb-object triples)
  → Entity Dedup (fuzzy matching against existing nodes)
  → Relationship Scoring (confidence + evidence count)
  → Graph Update (append-only, versioned)
  → Nightly Evolution:
      ├── Pattern Discovery (community detection, centrality)
      ├── Gap Analysis (expected connections that don't exist)
      ├── Contradiction Scan (conflicting relationships)
      └── New Theory Proposals (unexpected clusters)
  → Morning Report:
      ├── New connections discovered
      ├── New contradictions found
      ├── Evidence gaps closed
      └── Suggested actions
```

## Module Structure
```
00_SYSTEM/ai_modules/knowledge_graph/
├── __init__.py
├── ner_extractor.py        # Named entity recognition (spaCy)
├── relation_extractor.py   # Subject-verb-object triple extraction
├── entity_dedup.py         # Fuzzy entity deduplication
├── graph_manager.py        # SQLite-backed graph (nodes, edges, versions)
├── evolution_engine.py     # Nightly discovery cycle
├── pattern_detector.py     # Community detection, centrality analysis
├── gap_analyzer.py         # Expected-but-missing connections
├── report_generator.py     # Morning evolution report
├── config.py
└── tests/
```

## Node Types
Person, Organization, Location, Event, Document, CourtOrder, Filing, Exhibit, Claim, Rule, Authority

## Edge Types
filed_by, testified_at, contradicts, supports, violates, references, authored, served_on, ordered_by, related_to

## Rules
1. Graph is append-only — nodes/edges never deleted, only marked inactive
2. Every node/edge has: source_document, extraction_date, confidence_score
3. Evolution runs are idempotent — re-running produces same additions
4. Graph stored in SQLite (nodes, edges, versions tables) — not external Neo4j
5. Morning report auto-generated at end of evolution cycle
