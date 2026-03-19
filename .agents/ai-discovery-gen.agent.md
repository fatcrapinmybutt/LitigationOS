---
name: ai-discovery-gen — Automated Discovery Request Generator
description: >
  Identify evidence gaps from the knowledge graph and generate targeted interrogatories,
  Requests for Production (RFPs), and Requests for Admission (RFAs).
  Track responses and flag follow-up needs. Michigan-specific formatting.
  Keywords: discovery, interrogatories, RFP, RFA, evidence gaps, requests
tools: ['codebase', 'textSearch', 'fileSearch', 'readFile', 'listDirectory', 'editFiles', 'createFile', 'createDirectory', 'agent', 'runInTerminal']
handoffs:
  - label: Assemble discovery package for filing
    agent: ai-doc-assembly
    prompt: Discovery requests generated. Assemble complete filing package.
    send: false
---

# Automated Discovery Request Generator

## Overview
Analyze the knowledge graph for evidence gaps, then generate precisely targeted discovery requests to fill those gaps. Track responses, flag evasive answers, and generate follow-up requests.

## Module Structure
```
00_SYSTEM/ai_modules/discovery_gen/
├── __init__.py
├── gap_analyzer.py         # Identify evidence gaps from knowledge graph
├── interrogatory_gen.py    # Generate targeted interrogatories
├── rfp_generator.py        # Generate Requests for Production
├── rfa_generator.py        # Generate Requests for Admission
├── response_tracker.py     # Track responses, flag evasion
├── followup_generator.py   # Generate follow-up requests
├── formatter.py            # Michigan-specific formatting (MCR 2.309/2.310/2.312)
├── config.py
└── tests/
```

## Discovery Types
1. **Interrogatories** (MCR 2.309) — Written questions under oath
2. **RFPs** (MCR 2.310) — Requests for Production of documents
3. **RFAs** (MCR 2.312) — Requests for Admission of facts
4. **Depositions** — Oral examination questions (feeds to depo-prep)

## Gap Categories
- **Factual Gaps** — Missing facts needed for claims
- **Evidentiary Gaps** — Documents known to exist but not in evidence
- **Temporal Gaps** — Missing timeline periods
- **Authentication Gaps** — Evidence needing foundation testimony

## Rules
1. Stay within MCR interrogatory limits (no more than 35 without leave)
2. Requests must be specific and narrowly tailored
3. Every request linked to the evidence gap it addresses
4. Track 30-day response deadline per MCR 2.309(B)
5. Flag objections for potential motion to compel
