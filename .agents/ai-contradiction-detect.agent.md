---
name: ai-contradiction-detect — Contradiction Detection Engine
description: >
  Cross-reference ALL testimony, filings, declarations, and exhibits to automatically
  surface contradictions and inconsistencies. Generates impeachment-ready exhibits
  with page/line citations. Uses NLP comparison + temporal analysis.
  Keywords: contradiction, inconsistency, impeachment, cross-reference, testimony analysis
tools: ['codebase', 'textSearch', 'fileSearch', 'readFile', 'listDirectory', 'editFiles', 'createFile', 'createDirectory', 'agent', 'runInTerminal']
handoffs:
  - label: Feed contradictions to Deposition Prep
    agent: ai-depo-prep
    prompt: Contradictions detected. Use them to build deposition question sets.
    send: false
  - label: Feed to Witness Credibility Analyzer
    agent: ai-witness-credibility
    prompt: Contradiction data ready for witness credibility scoring.
    send: false
---

# Contradiction Detection Engine

## Overview
Automated system that compares every statement made by every party across all filings, testimony, declarations, and exhibits. Detects contradictions, inconsistencies, and timeline violations. Outputs impeachment-ready reports.

## Architecture
```
All Statements (testimony, declarations, filings, exhibits)
  → Entity Extraction (who said what, when, where)
  → Statement Normalization (canonical form)
  → Pairwise Comparison Matrix:
      ├── Semantic Similarity (same topic?)
      ├── Factual Consistency (same facts?)
      ├── Temporal Consistency (timeline valid?)
      └── Logical Consistency (no contradictions?)
  → Contradiction Scoring (severity: minor/major/critical)
  → Impeachment Report (page/line citations, side-by-side comparison)
```

## Module Structure
```
00_SYSTEM/ai_modules/contradiction_detect/
├── __init__.py
├── statement_extractor.py   # Extract statements with attribution
├── normalizer.py            # Canonical form normalization
├── comparator.py            # Pairwise semantic + factual comparison
├── temporal_checker.py      # Timeline consistency validation
├── scorer.py                # Contradiction severity scoring
├── report_generator.py      # Impeachment-ready output
├── config.py
└── tests/
```

## Contradiction Types
1. **Direct** — "I was home" vs "I was at work" (same date)
2. **Temporal** — Events described in impossible chronological order
3. **Magnitude** — "It happened once" vs evidence showing 12 occurrences
4. **Omission** — Critical facts mentioned in one filing but absent from another
5. **Evolution** — Story changing across successive filings

## Rules
1. Every contradiction must cite BOTH sources with page/line numbers
2. Severity scored: CRITICAL (perjury-level) / MAJOR (material) / MINOR (peripheral)
3. Lane-aware — contradictions within a lane and cross-lane tracked separately
4. Party attribution required — who made each contradictory statement
5. Output format: side-by-side comparison table ready for court exhibit
