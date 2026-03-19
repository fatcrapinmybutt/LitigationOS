---
name: ai-rag-brief-gen — RAG-Powered Brief & Motion Generator
description: >
  Retrieval-Augmented Generation engine that pulls from the 694-table litigation DB,
  court rules, evidence quotes, and authority chains to draft complete motions and briefs
  with pinpoint MCR citations and exhibit references. Local inference only.
  Keywords: RAG, brief generation, motion drafting, legal writing, MCR citations
tools: ['codebase', 'textSearch', 'fileSearch', 'readFile', 'listDirectory', 'editFiles', 'createFile', 'createDirectory', 'agent', 'runInTerminal']
handoffs:
  - label: Validate brief with Filing Guardian
    agent: ai-filing-guardian
    prompt: Brief is generated. Validate MCR compliance before filing.
    send: false
  - label: Rank citations with Authority Ranker
    agent: ai-citation-ranker
    prompt: Brief citations need ranking for strength and relevance.
    send: false
---

# RAG-Powered Brief & Motion Generator

## Overview
Generate complete legal briefs and motions by retrieving relevant evidence, rules, and authorities from the litigation database, then assembling them into structured legal documents with proper citations.

## Architecture
```
User Query ("Motion to disqualify under MCR 2.003")
  → Query Decomposition (extract legal issues, rules, facts needed)
  → Multi-Source Retrieval:
      ├── Semantic Search → relevant evidence chunks
      ├── Authority Index → applicable case law + statutes
      ├── Court Rules DB → MCR/MRE rules
      └── Evidence Quotes → supporting testimony/declarations
  → Context Assembly (ranked, deduplicated, lane-filtered)
  → Template Selection (motion, brief, response, reply)
  → MANBEARPIG Generation (structured sections)
  → Citation Injection (pinpoint page/line refs)
  → Output: Complete motion with exhibits list
```

## Module Structure
```
00_SYSTEM/ai_modules/rag_brief_gen/
├── __init__.py
├── query_decomposer.py    # Break legal question into retrieval queries
├── retriever.py            # Multi-source retrieval orchestrator
├── context_assembler.py    # Rank, dedup, filter retrieved context
├── template_engine.py      # Legal document templates (AKN format)
├── generator.py            # MANBEARPIG-powered text generation
├── citation_injector.py    # Add pinpoint citations to generated text
├── brief_builder.py        # End-to-end brief assembly pipeline
├── config.py               # Templates, retrieval params, generation settings
└── tests/
```

## Templates
- Motion (with points and authorities)
- Response to Motion
- Reply Brief
- Appellate Brief (COA format)
- Emergency Motion / Ex Parte
- Proposed Order

## Rules
1. Every factual claim MUST have a citation to evidence in the DB
2. Every legal argument MUST cite an MCR rule or case authority
3. Lane isolation — briefs only reference evidence from their assigned lane
4. No hallucinated citations — if no authority exists, flag as NEEDS_RESEARCH
5. Output includes confidence score per section (high/medium/low)
