# Module Integration Guide — OMEGA-LITIGATION-SUPREME

## 12-Module Architecture Overview

OMEGA-LITIGATION-SUPREME fuses 67 skills into 12 modules that form a directed pipeline.
Understanding the data flow between modules is critical for correct invocation.

## Module Dependency Map

```
M11 Smart Router (ENTRY POINT)
  │
  ├──→ M7 DB Intelligence (INIT FIRST — provides data to all modules)
  │
  ├──→ M1 Evidence Pipeline ──→ M2 Contradiction Engine ──→ M3 Authority Validator
  │         │                         │                           │
  │         └─────────────────────────┴───────────────────────────┘
  │                                   │
  │                              M5 Strategic Command
  │                                   │
  │                              M4 Filing Factory ──→ M8 QA Gates ──→ M9 Court-Ready
  │                                   ↑
  │                              M6 Domain Specialists (custody, PPO, appellate, etc.)
  │                              M10 Adversary Intelligence
  │
  └──→ M12 Self-Evolution (FEEDBACK — runs after every output)
```

## Module Activation Guide

### M1: Evidence Pipeline
- **Invoke when**: Raw files need processing, evidence needs extraction/classification
- **Input**: File paths, drive scan results, raw document content
- **Output**: Structured evidence records with lane tags, Bates numbers, SHA-256 hashes
- **Feeds into**: M2 (for contradiction detection), M7 (for DB storage)

### M2: Contradiction Engine
- **Invoke when**: Looking for impeachment material, inconsistencies, timeline gaps
- **Input**: Evidence records from M1, witness statements, court transcripts
- **Output**: Contradiction pairs with confidence scores, impeachment briefs
- **Feeds into**: M5 (for strategic prioritization), M4 (for filing integration)

### M3: Authority Validator
- **Invoke when**: Citations need verification, authority chains need validation
- **Input**: Legal citations, statute references, case law citations
- **Output**: Validated citation chains with currency status, overruled flags
- **Feeds into**: M4 (only verified citations enter filings)

### M4: Filing Factory
- **Invoke when**: Assembling court-ready documents (motions, briefs, petitions)
- **Input**: Evidence from M1, contradictions from M2, authorities from M3, strategy from M5
- **Output**: Draft filings in proper MCR format with all required components
- **Feeds into**: M8 (MANDATORY QA before delivery)

### M5: Strategic Command
- **Invoke when**: Deciding what to file next, prioritizing claims, sequencing motions
- **Input**: Case state from M7, evidence gaps from M1, adversary intel from M10
- **Output**: Filing recommendations with priority scores, strategic sequencing plans
- **Feeds into**: M4 (drives filing selection and argument framing)

### M6: Domain Specialists
- **Invoke when**: Lane-specific legal expertise is needed
- **Sub-modules**:
  - D1: Custody (MCL 722.23 best-interest factors, Lane A)
  - D2: PPO/Protection Orders (MCL 600.2950, Lane D)
  - D3: Appellate (MCR 7.200 series, Lane F)
  - D4: Judicial Misconduct (MCR 9.100 series, Lane E)
  - D5: Housing (MTHA, Lane B)
  - D6: Federal §1983 (42 USC §1983, Lane C)
- **Output**: Domain-specific analysis, applicable standards, element checklists

### M7: DB Intelligence
- **Invoke when**: ALWAYS — must initialize before any other module
- **Role**: Connection management, schema verification, query optimization
- **PRAGMAs**: `busy_timeout=60000`, `journal_mode=WAL`, `cache_size=-32000`
- **Critical**: Run `PRAGMA table_info(table_name)` before first query to any table

### M8: QA Gates
- **Invoke when**: MANDATORY before any output delivery
- **Checks**: No hallucinated names, all citations verified, DB-first confirmed, traceable statistics, proper lane tagging, MCR format compliance
- **Blocks delivery if**: Any check fails — returns specific failure reasons

### M9: Court-Ready Output
- **Invoke when**: M8 passes all gates
- **Role**: Final formatting, PDF generation, exhibit indexing, service preparation

### M10: Adversary Intelligence
- **Invoke when**: Need to anticipate opposing arguments or analyze Emily Watson's patterns
- **Input**: Prior filings, court records, FOC reports
- **Output**: Predicted defense strategies, pattern analysis (with documented incident counts only)

### M11: Smart Router
- **Invoke when**: ALWAYS — this is the entry point for every task
- **Logic**: Parses natural language task → selects module chain → validates dependencies
- **Routing keywords**:
  - "analyze files/evidence" → M1 + M7
  - "find contradictions" → M2
  - "validate citations" → M3
  - "draft motion/brief" → M4
  - "what should I file next?" → M5
  - "custody/PPO/appeal question" → M6
  - "run QA check" → M8
  - "full pipeline" → M1→M2→M3→M5→M6→M4→M8→M9

### M12: Self-Evolution
- **Invoke when**: After EVERY output delivery
- **Role**: Logs quality scores, records gaps, updates lane intelligence
- **Critical**: Without M12 logging, the next session repeats prior mistakes
