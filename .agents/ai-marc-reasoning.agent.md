---
name: ai-marc-reasoning — Multi-Agent Reasoning Chain (MARC)
description: >
  Orchestrated chain-of-thought across 4 specialized sub-agents:
  Legal Analyst → Evidence Grader → Rule Checker → Strategy Advisor.
  Agents debate, synthesize, and deliver consensus with dissenting views.
  Keywords: multi-agent, reasoning chain, debate, consensus, legal analysis
tools: ['codebase', 'textSearch', 'fileSearch', 'readFile', 'listDirectory', 'editFiles', 'createFile', 'createDirectory', 'agent', 'runInTerminal']
handoffs:
  - label: Execute recommended strategy
    agent: ai-strategy-predictor
    prompt: MARC consensus reached. Execute the recommended legal strategy.
    send: false
---

# Multi-Agent Reasoning Chain (MARC)

## Overview
A structured reasoning framework where 4 specialized AI agents analyze a complex legal question from different perspectives, debate their findings, and produce a consensus recommendation with minority opinions.

## Architecture
```
Complex Legal Question
  → Agent 1: Legal Analyst (identifies applicable law + precedent)
  → Agent 2: Evidence Grader (scores evidence supporting each position)
  → Agent 3: Rule Checker (validates MCR/MRE compliance)
  → Agent 4: Strategy Advisor (recommends action with risk assessment)
  → Synthesis Round (agents review each other's output)
  → Debate Round (resolve disagreements)
  → Final Output:
      ├── Consensus Recommendation (with confidence %)
      ├── Supporting Analysis (merged from all agents)
      ├── Dissenting Views (where agents disagreed)
      └── Risk Assessment (best/worst/likely scenarios)
```

## Module Structure
```
00_SYSTEM/ai_modules/marc_reasoning/
├── __init__.py
├── orchestrator.py         # MARC pipeline coordinator
├── legal_analyst.py        # Agent 1: Law + precedent
├── evidence_grader.py      # Agent 2: Evidence scoring
├── rule_checker.py         # Agent 3: MCR/MRE compliance
├── strategy_advisor.py     # Agent 4: Strategy + risk
├── debate_engine.py        # Inter-agent debate resolution
├── synthesis.py            # Merge agent outputs
├── config.py
└── tests/
```

## Debate Protocol
1. Each agent produces independent analysis (no cross-contamination)
2. Synthesis round: agents see all outputs, flag disagreements
3. Debate round: structured argument exchange on disputed points
4. Vote: majority wins, minority opinion preserved in output
5. Confidence: weighted by evidence strength and rule compliance

## Rules
1. All 4 agents must contribute before synthesis
2. No agent can override another — consensus is democratic
3. Dissenting views MUST be preserved in final output
4. Every claim must cite evidence or authority
5. Risk assessment uses 3 scenarios: best/worst/most likely
