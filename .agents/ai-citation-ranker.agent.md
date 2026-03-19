---
name: ai-citation-ranker — Legal Citation Authority Ranker
description: >
  Rank cited authorities by relevance, recency, jurisdiction match, and positional
  strength. Flag weak citations, suggest stronger alternatives, and identify
  opposing authorities. Builds on RAG brief generator's authority index.
  Keywords: citations, authority, case law, ranking, jurisdiction, legal research
tools: ['codebase', 'textSearch', 'fileSearch', 'readFile', 'listDirectory', 'editFiles', 'createFile', 'createDirectory', 'agent', 'runInTerminal']
handoffs:
  - label: Feed ranked citations to Brief Generator
    agent: ai-rag-brief-gen
    prompt: Citations ranked. Use top authorities in brief generation.
    send: false
---

# Legal Citation Authority Ranker

## Overview
Score and rank every legal citation by relevance to the specific legal issue, recency, jurisdictional authority, and how strongly it supports the position. Replace weak citations with stronger alternatives.

## Module Structure
```
00_SYSTEM/ai_modules/citation_ranker/
├── __init__.py
├── authority_parser.py     # Parse citations from text (case law, statutes, rules)
├── relevance_scorer.py     # Score relevance to specific legal issue
├── recency_scorer.py       # Score by how recent the authority is
├── jurisdiction_scorer.py  # Score by jurisdictional weight (MI > 6th Cir > other)
├── strength_scorer.py      # Score how strongly authority supports position
├── alternative_finder.py   # Find stronger alternative authorities
├── opposing_scanner.py     # Identify authorities opposing might cite
├── composite_ranker.py     # Weighted composite ranking
├── config.py
└── tests/
```

## Jurisdiction Hierarchy (Michigan)
1. **Michigan Supreme Court** — Binding, highest weight
2. **Michigan Court of Appeals (published)** — Binding
3. **Michigan Court of Appeals (unpublished)** — Persuasive only (MCR 7.215)
4. **6th Circuit Court of Appeals** — Persuasive, high weight
5. **U.S. Supreme Court** — Binding on federal questions
6. **Other state courts** — Persuasive only, low weight
7. **Secondary sources** — Treatises, law reviews — informational

## Rules
1. Scoring weights: Relevance 40%, Jurisdiction 25%, Recency 20%, Strength 15%
2. Flag any citation that has been overruled or distinguished
3. Michigan authorities always preferred over out-of-state
4. Unpublished opinions flagged with MCR 7.215 caveat
5. Opposing authority scan is mandatory — know what they'll cite
