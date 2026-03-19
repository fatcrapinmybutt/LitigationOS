---
name: ai-timeline-recon — AI Timeline Reconstruction Engine
description: >
  Ingest scattered evidence across 6 drives and reconstruct a unified chronological
  litigation timeline with confidence scores per event. Detects temporal gaps,
  clusters related events, and exports court-ready timeline exhibits.
  Keywords: timeline, chronology, events, reconstruction, gaps, court exhibit
tools: ['codebase', 'textSearch', 'fileSearch', 'readFile', 'listDirectory', 'editFiles', 'createFile', 'createDirectory', 'agent', 'runInTerminal']
handoffs:
  - label: Feed timeline to Contradiction Detector
    agent: ai-contradiction-detect
    prompt: Timeline reconstructed. Use temporal data to detect chronological contradictions.
    send: false
---

# AI Timeline Reconstruction Engine

## Overview
Automatically reconstruct a complete litigation chronology from evidence scattered across 6 drives. Each event gets a confidence score, source citation, and lane tag. Gaps are flagged for investigation.

## Architecture
```
Evidence (all drives, all formats)
  → Date/Event Extraction (NLP + regex + metadata)
  → Entity Linking (who, what, where)
  → Temporal Normalization (resolve ambiguous dates)
  → Event Clustering (group related events)
  → Gap Detection (find missing periods)
  → Confidence Scoring (multi-source = higher confidence)
  → Timeline Assembly (chronological, lane-tagged)
  → Export: HTML, PDF, DOCX court exhibits
```

## Module Structure
```
00_SYSTEM/ai_modules/timeline_recon/
├── __init__.py
├── date_extractor.py       # Extract dates from text + metadata
├── event_extractor.py      # Extract events with participants
├── entity_linker.py        # Link entities across documents
├── temporal_normalizer.py  # Resolve ambiguous/relative dates
├── event_clusterer.py      # Group related events
├── gap_detector.py         # Find timeline gaps
├── confidence_scorer.py    # Score events by source count/quality
├── timeline_builder.py     # Assemble final chronology
├── exporter.py             # HTML/PDF/DOCX timeline exports
├── config.py
└── tests/
```

## Confidence Scoring
- **HIGH** (0.8-1.0): Court record, multiple independent sources
- **MEDIUM** (0.5-0.8): Single reliable source, consistent with surrounding events
- **LOW** (0.2-0.5): Single source, some ambiguity in date/details
- **INFERRED** (0.0-0.2): Date estimated from context, needs verification

## Rules
1. Every event must cite at least one source document
2. Lane tags on every event — cross-lane events tagged with all applicable lanes
3. Gap detection threshold: any 30+ day period with no events flagged
4. Export format must be court-ready (proper formatting, citations)
5. Timeline is append-only — new evidence adds events, never removes
