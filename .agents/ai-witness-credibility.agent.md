---
name: ai-witness-credibility — Witness Credibility Analyzer
description: >
  Score witness reliability across all statements, declarations, and testimony.
  Consistency tracking, contradiction flagging, bias indicators, and credibility
  timelines. Integrates with contradiction detection and deposition prep.
  Keywords: witness credibility, reliability, consistency, bias, testimony analysis
tools: ['codebase', 'textSearch', 'fileSearch', 'readFile', 'listDirectory', 'editFiles', 'createFile', 'createDirectory', 'agent', 'runInTerminal']
handoffs:
  - label: Feed credibility scores to MARC Reasoning
    agent: ai-marc-reasoning
    prompt: Witness credibility scores ready for multi-agent legal analysis.
    send: false
---

# Witness Credibility Analyzer

## Overview
Build comprehensive credibility profiles for every witness. Track consistency across all statements, flag contradictions, identify potential bias, and generate credibility scores with explanations.

## Module Structure
```
00_SYSTEM/ai_modules/witness_credibility/
├── __init__.py
├── statement_collector.py  # Gather all statements per witness
├── consistency_tracker.py  # Track statement consistency over time
├── bias_detector.py        # Identify potential bias indicators
├── credibility_scorer.py   # Generate credibility scores (0-100)
├── timeline_builder.py     # Credibility over time visualization
├── profile_generator.py    # Complete witness credibility profile
├── config.py
└── tests/
```

## Credibility Factors
1. **Internal Consistency** — Do their statements agree with each other?
2. **External Consistency** — Do their statements agree with other evidence?
3. **Specificity** — Vague vs. detailed recall (appropriate to timeframe)
4. **Bias Indicators** — Relationship to parties, financial interest, grudges
5. **Prior Record** — Known false statements, criminal history
6. **Corroboration** — Independent evidence supporting their claims

## Scoring
- 80-100: Highly credible — consistent, corroborated, unbiased
- 60-79: Generally credible — minor inconsistencies
- 40-59: Questionable — significant inconsistencies or bias indicators
- 20-39: Low credibility — major contradictions or clear bias
- 0-19: Not credible — proven false statements or extreme bias

## Rules
1. Every score factor must cite specific evidence
2. Scores update automatically when new evidence is ingested
3. Credibility timeline shows how score changed with each new statement
4. Bias indicators are flagged but not penalized without evidence
5. Profile output suitable for impeachment preparation
