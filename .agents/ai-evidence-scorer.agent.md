---
name: ai-evidence-scorer — Evidence Strength Scorer with Explainability
description: >
  ML model scoring every exhibit on three axes: relevance (to specific claims),
  admissibility (MRE compliance), and impact (likely judicial weight).
  Each score includes plain-English explainable reasoning.
  Keywords: evidence scoring, relevance, admissibility, MRE, impact, explainability
tools: ['codebase', 'textSearch', 'fileSearch', 'readFile', 'listDirectory', 'editFiles', 'createFile', 'createDirectory', 'agent', 'runInTerminal']
handoffs:
  - label: Feed scores to MARC Reasoning
    agent: ai-marc-reasoning
    prompt: Evidence scores available. Use for multi-agent reasoning quality.
    send: false
  - label: Feed to Exhibit Optimizer
    agent: ai-exhibit-optimizer
    prompt: Evidence scores ready for exhibit package optimization.
    send: false
---

# Evidence Strength Scorer with Explainability

## Overview
Score every piece of evidence on relevance, admissibility, and judicial impact. Each score comes with plain-English reasoning so attorneys understand WHY a document scored high or low.

## Architecture
```
Evidence Document
  → Feature Extraction:
      ├── Content Features (topic, entities, dates, keywords)
      ├── Metadata Features (source, date, format, authentication)
      └── Legal Features (MCR/MRE compliance markers)
  → Three-Axis Scoring:
      ├── Relevance (0-100): connection to specific claims
      ├── Admissibility (0-100): MRE foundation, authentication, hearsay
      └── Impact (0-100): likely judicial weight
  → Explainability Engine (generate reasoning per score)
  → Composite Score: weighted average with configurable weights
  → Priority Ranking per claim
```

## Module Structure
```
00_SYSTEM/ai_modules/evidence_scorer/
├── __init__.py
├── feature_extractor.py    # Extract scoring features from documents
├── relevance_scorer.py     # Score relevance to claims
├── admissibility_scorer.py # Score MRE compliance
├── impact_scorer.py        # Score likely judicial weight
├── explainer.py            # Generate plain-English explanations
├── composite_ranker.py     # Weighted composite + priority ranking
├── config.py
└── tests/
```

## MRE Admissibility Checks
- Authentication (MRE 901/902)
- Hearsay exceptions (MRE 803/804)
- Relevance (MRE 401/402)
- Prejudice vs. probative (MRE 403)
- Best evidence rule (MRE 1001-1008)
- Privilege (MRE 501)

## Rules
1. Scores are per-claim — same evidence may score differently for different claims
2. Explainability is mandatory — no black-box scores
3. MRE check uses Michigan-specific rules, not Federal
4. Impact scoring factors in Judge McNeill's known tendencies (Lane E data)
5. All scores stored in `evidence_scores` table with claim_id foreign key
