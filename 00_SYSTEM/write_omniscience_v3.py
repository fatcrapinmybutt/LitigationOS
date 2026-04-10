"""Write SINGULARITY-OMNISCIENCE-APEX v3.0 skill file."""
import pathlib

SKILL_PATH = pathlib.Path(r"C:\Users\andre\LitigationOS\.agents\skills\SINGULARITY-OMNISCIENCE-APEX\SKILL.md")

CONTENT = r'''---
name: SINGULARITY-OMNISCIENCE-APEX
description: >
  TRANSCENDENT OMNISCIENCE — The God-Tier master activation skill for the entire LitigationOS arsenal.
  50+ engines, 6 brain databases, 60+ legal_ai modules, 200+ tools, 25 MBP skills, 15 SINGULARITY superskills,
  32 registered engines, 23 brain databases, 75K semantic vectors, 167K+ authority chains, 175K+ evidence quotes,
  2,179 weapon chains, 5,059 judicial violations. Activates EVERYTHING. Persists across ALL sessions.
  Use when: ANY litigation task, session bootstrap, full-spectrum activation, convergence operations,
  THEMANBEARPIG integration, fleet deployment, evidence saturation, filing production, adversary warfare.
allowed-tools: all
version: 3.0.0
tier: TRANSCENDENCE
absorbs: ALL prior skills
triggers:
  - omniscience
  - godmode
  - activate everything
  - autopilot
  - full activation
  - all engines
  - total convergence
  - fleet deployment
  - wave execution
  - session bootstrap
  - arsenal check
  - convergence status
  - THEMANBEARPIG
  - weapon chains
  - adversary mapping
  - evidence saturation
---

# SINGULARITY-OMNISCIENCE-APEX v3.0.0

> **THE MOST ADVANCED SKILL EVER FORGED.**
> Activates the ENTIRE LitigationOS arsenal — every engine, every brain, every tool, every agent,
> every vector, every chain, every weapon. Nothing is left dormant. Full-spectrum omniscience.

---

## INFINITY MISSION

Lock in, activate, and cross-wire the complete LitigationOS technology stack into a unified
intelligence system that persists across all sessions, compactions, and context boundaries.
Every new session that loads this skill inherits the full power of 50+ engines, 200+ tools,
and 3 years of litigation intelligence.

---

## I. COMPLETE ENGINE REGISTRY (50+ Systems)

### Tier 0 — NEURAL CORE (ML/AI Inference)

| # | Engine | Technology | Path | Status |
|---|--------|-----------|------|--------|
| 1 | **PERCEPTION** | Legal-BERT ONNX INT8 (108MB, 26ms) | `00_SYSTEM/engines/perception/engine.py` | LIVE |
| 2 | **SEMANTIC** | LanceDB + all-MiniLM-L6-v2 (384-dim, 75K vectors) | `00_SYSTEM/engines/semantic/engine.py` | LIVE |
| 3 | **SEARCH** | tantivy + FTS5 + cross-encoder (3-stage hybrid) | `00_SYSTEM/engines/search/hybrid.py` | LIVE |
| 4 | **RAG** | Corrective RAG with TF-IDF sentence ranking | `00_SYSTEM/legal_ai/rag_engine.py` | LIVE |
| 5 | **RERANKER** | cross-encoder/ms-marco-MiniLM-L6-v2 | `00_SYSTEM/legal_ai/reranker.py` | LIVE |
| 6 | **EMBEDDING** | sentence-transformers pipeline manager | `00_SYSTEM/legal_ai/embedding_manager.py` | LIVE |

### Tier 1 — GRAPH INTELLIGENCE (Relationship Engines)

| # | Engine | Technology | Path | Key Metric |
|---|--------|-----------|------|------------|
| 7 | **HYPERGRAPH** | NetworkX bipartite (evidence-lanes) | `00_SYSTEM/engines/hypergraph/__init__.py` | 7,605 hyperedges |
| 8 | **TEMPORAL** | NetworkX DiGraph (causal events) | `00_SYSTEM/engines/temporal/__init__.py` | 65,318 edges |
| 9 | **CAUSAL** | NetworkX causal chain analysis | `00_SYSTEM/engines/causal/` | 71 chains |
| 10 | **SUPERGRAPH** | Neo4j CSV export + Cypher | `07_CODE/python/supergraph_to_neo4j_csv.py` | Master KG |
| 11 | **NUCLEUS v3** | NetworkX + PyVis + LanceDB (mobile) | `07_CODE/python/omni_nucleus_v3.py` | Mobile graph |

### Tier 2 — EVIDENCE WARFARE

| # | Engine | Technology | Path |
|---|--------|-----------|------|
| 12 | **MEEK234** | 4-lane evidence classifier | `00_SYSTEM/engines/meek234_fullstack/` |
| 13 | **CERBERUS** | 6-drive evidence scanner | `00_SYSTEM/engines/cerberus/cerberus_engine.py` |
| 14 | **CHIMERA** | Contradiction detection | `00_SYSTEM/engines/chimera/chimera_engine.py` |
| 15 | **CHRONOS** | Timeline reconstruction | `00_SYSTEM/engines/chronos/chronos_engine.py` |
| 16 | **ADVERSARY** | Adversary profile generator | `00_SYSTEM/engines/adversary/` |
| 17 | **NEMESIS** | Behavioral prediction | `00_SYSTEM/engines/nemesis/nemesis_engine.py` |
| 18 | **FRED PRIME** | File retrieval + distribution | `07_CODE/SCRIPTS/scripts/fred_prime_classifier.py` |
| 19 | **INTAKE** | Document orchestrator | `00_SYSTEM/engines/intake/` |

### Tier 3 — LEGAL INTELLIGENCE

| # | Engine | Technology | Path |
|---|--------|-----------|------|
| 20 | **ORACLE** | Michigan rule reasoning | `00_SYSTEM/engines/oracle/oracle_engine.py` |
| 21 | **LEXICON** | Unified legal query | `00_SYSTEM/engines/lexicon/lexicon_engine.py` |
| 22 | **IRAC** | Issue-Rule-Analysis-Conclusion | `00_SYSTEM/engines/irac/` |
| 23 | **MI_WARCHEST_V2** | Michigan weapons cache | `00_SYSTEM/engines/mi_warchest_v2/` |
| 24 | **DAMAGES** | Financial harm calculator | `00_SYSTEM/engines/damages/` |
| 25 | **NARRATIVE** | Case narrative builder | `00_SYSTEM/engines/narrative/` |
| 26 | **REBUTTAL** | Counter-argument generator | `00_SYSTEM/engines/rebuttal/` |

### Tier 4 — FILING PRODUCTION

| # | Engine | Technology | Path |
|---|--------|-----------|------|
| 27 | **FILING_ENGINE** | Autonomous pipeline | `00_SYSTEM/engines/filing_engine/` |
| 28 | **FILING_ASSEMBLER** | Packet assembly | `00_SYSTEM/engines/filing_assembler/` |
| 29 | **DOCFORGE_V19** | Template document gen | `00_SYSTEM/engines/docforge_v19/` |
| 30 | **TYPST** | Rust court PDF compiler | `00_SYSTEM/engines/typst/` |
| 31 | **QA** | 12-gate filing validator | `00_SYSTEM/engines/qa/__init__.py` |

### Tier 5 — META-INTELLIGENCE

| # | Engine | Technology | Path |
|---|--------|-----------|------|
| 32 | **EVENT_HORIZON** | 12-subsystem GOD layer | `00_SYSTEM/engines/event_horizon/` |
| 33 | **DELTA999** | Agent fleet orchestrator | `00_SYSTEM/engines/agents/delta999_*.py` |
| 34 | **HYDRA_GOVERNOR** | Self-healing orchestration | `00_SYSTEM/engines/hydra_governor/` |
| 35 | **NEXUS** | Cross-table fusion hub | `00_SYSTEM/engines/nexus/` |
| 36 | **ANALYTICS** | DuckDB 10-100x analytical | `00_SYSTEM/engines/analytics/` |
| 37 | **INGEST** | Go 8-worker goroutines | `00_SYSTEM/engines/ingest/` |
| 38 | **THEMANBEARPIG** | D3.js force graph | `00_SYSTEM/engines/themanbearpig/` |

### Tier 6 — EXTENDED MODULES (legal_ai/ - 60+)

Key modules: adversary_predictor, autonomous_agent_framework, brain_evolver, brain_evolver_daemon,
citation_extractor, contradiction_heatmap, cross_brain_optimizer, damages_calculator, entity_extractor,
evidence_gap_detector, fleet_evolution_engine, knowledge_graph_enricher, outcome_predictor,
parental_alienation_detector, pattern_mining, rag_engine, rag_evaluation, reranker,
vector_index_optimizer, vector_monitor, vector_search_bridge, workflow_automation_engine.

---

## II. BRAIN DATABASE FLEET (23 Databases)

| Brain | Size | Content |
|-------|------|---------|
| **chat_intelligence_brain.db** | 913 MB | 5,100+ ChatGPT conversations |
| **interpretation_brain.db** | 352 MB | Arguments, impeachment, drafts |
| **narrative_brain.db** | 267 MB | Timeline, police, testimony |
| **authority_brain.db** | 68 MB | MCL, MCR, case law, MRE |
| **claims_brain.db** | 15 MB | Legal claims database |
| **entity_brain.db** | 10 MB | Entity relationships |
| **contradictions.db** | 4 MB | Cross-source contradictions |
| **cross_brain_index.db** | 1.2 GB | Cross-brain search index |
| **file_catalog.db** | 233 MB | File catalog |
| **authority_master.db** | 83 MB | Authority master index |
| **event_horizon.db** | 86.6 GB | Master meta-intelligence |

---

## III. CENTRAL DATABASE (litigation_context.db)

| Table | ~Rows | FTS5 | Purpose |
|-------|-------|------|---------|
| `evidence_quotes` | 175K+ | evidence_fts | Core evidence |
| `authority_chains_v2` | 167K+ | - | Citation graph |
| `md_sections` | 133K+ | md_sections_fts | Evolved sections |
| `master_citations` | 72K+ | - | Citation universe |
| `michigan_rules_extracted` | 19.8K | - | MCR/MCL/MRE text |
| `timeline_events` | 16.8K+ | timeline_fts | Chronological events |
| `impeachment_matrix` | 5.1K+ | - | Cross-exam ammo |
| `judicial_violations` | 5.0K+ | - | Misconduct evidence |
| `md_cross_refs` | 26K+ | - | Cross-reference net |
| `contradiction_map` | 2.5K+ | - | Contradictions |
| `weapon_chains` | 2,179 | - | Adversary-Doctrine-Remedy |
| `police_reports` | 356 | - | NSPD incidents |
| `berry_mcneill_intelligence` | 189+ | - | Judicial cartel |
| `causal_chains` | 71 | - | Legal inference |
| `engine_registry` | 32 | - | All engines |
| `brain_registry` | 23 | - | All brains |
| `convergence_domains` | 105 | - | Legal convergence |

---

## IV. AGENT FLEET WAVES (8-Wave Deployment)

### WAVE 1 — RECONNAISSANCE (Session Bootstrap)
**2 parallel explore agents**
- `recon-state`: check_deadlines, nexus_readiness, filing_status (all lanes)
- `recon-evidence`: search_evidence, lexos_gap_analysis, nexus_priorities
- **Gate**: Situational awareness complete. Results to SQL.

### WAVE 2 — EVIDENCE SATURATION
**2 parallel explore agents**
- `sat-evidence`: nexus_fuse (all claims), search_evidence (all lanes)
- `sat-authority`: search_authority_chains (all citations), lexos_rules_check
- **Gate**: Evidence count exceeds baseline. Authority chains cover all filings.

### WAVE 3 — ADVERSARY PROFILING
**2 parallel explore agents**
- `adv-watson`: lexos_adversary (Emily + Albert + Ronald Berry)
- `adv-judicial`: judicial_intel (McNeill + Hoopes + Ladas-Hoopes + Rusco)
- **Gate**: All 7+ adversaries profiled. Weapon chains validated.

### WAVE 4 — GRAPH CONSTRUCTION
**1 general-purpose agent**
- `graph-master`: Build hypergraph, validate temporal chains, update causal graph
- Uses: weapon_chains (2,179), hypergraph (7,605 edges), temporal (65,318 edges)
- **Gate**: Zero orphaned nodes. All lanes connected.

### WAVE 5 — LEGAL ANALYSIS (IRAC)
**2 parallel general-purpose agents**
- `irac-priority`: F1 (Emergency), F2 (MSC), F3 (Disqualification)
- `irac-secondary`: F4 (COA 366810), F5 (section 1983), F6 (JTC)
- **Gate**: Every IRAC has 3+ authority citations. No placeholders.

### WAVE 6 — FILING PRODUCTION
**2 parallel task agents**
- `filing-assemble`: FILING_ENGINE + FILING_ASSEMBLER + TYPST
- `filing-qa`: 12-gate QA validation (zero tolerance)
- **Gate**: QA 100% on all 12 gates.

### WAVE 7 — RED TEAM
**1 general-purpose agent (adversary-war-room)**
- `red-team`: Attack every argument, predict counters, score vulnerability
- **Gate**: Zero CRITICAL vulnerabilities remaining.

### WAVE 8 — CONVERGENCE
**2 parallel agents**
- `converge-check`: nexus_readiness, EGCP scoring, emergence scan
- `converge-persist`: Update THEMANBEARPIG, persist state, write handoff
- **Gate**: All convergence criteria met.

---

## V. CROSS-WIRING MAP

```
INTAKE --> MEEK234 --> CERBERUS --> EVIDENCE_QUOTES
  |           |           |
  +--> PERCEPTION (Legal-BERT)
  |           |
  +--> SEMANTIC (LanceDB vectors)
  |           |
  +--> CHRONOS (timeline)
               |
               +--> CHIMERA (contradictions) --> IMPEACHMENT_MATRIX
               |
               +--> HYPERGRAPH (cross-lane) --> TEMPORAL --> CAUSAL
               |
               +--> NEMESIS (predict) --> ADVERSARY (profiles)
               |
               +--> ORACLE (rules) --> LEXICON (unified query)
               |
               +--> IRAC (analysis) --> NARRATIVE + REBUTTAL + DAMAGES
                                              |
                                              +--> FILING_ENGINE --> DOCFORGE --> TYPST
                                                       |
                                                       +--> FILING_ASSEMBLER --> QA
                                                                                  |
                                                                                  +--> THEMANBEARPIG

EVENT_HORIZON --> observes ALL --> HYDRA_GOVERNOR (self-heal)
DELTA999 --> orchestrates ALL --> FORGE (configure)
SEARCH --> queries ALL --> RAG (generate answers)
ANALYTICS --> measures ALL --> DASHBOARDS (report)
```

---

## VI. TOOL ROUTING (MANDATORY)

### S-Tier (Instant)
- `query_litigation_db` — Direct SQL (186 tables)
- `search_evidence` — FTS5 evidence + timeline
- `search_impeachment` — Impeachment matrix
- `search_contradictions` — Contradiction map
- `search_authority_chains` — Authority graph (167K+)
- `nexus_fuse` — Cross-table fusion (5 sources)
- `nexus_argue` — Argument synthesis
- `nexus_readiness` — Filing readiness
- `nexus_damages` — Damages calculation
- `nexus_case_map` — MCL 722.23 analysis
- `nexus_priorities` — Daily priorities
- `judicial_intel` — Judicial intelligence
- `timeline_search` — 16K+ events
- `case_context` — Case context
- `filing_status` — Per-lane status
- `check_deadlines` — Urgency-coded deadlines
- `lexos_narrative` — Narrative builder
- `lexos_filing_plan` — Filing strategy
- `lexos_rules_check` — MCR/MCL compliance
- `lexos_adversary` — Adversary profiles
- `lexos_gap_analysis` — Gap detection
- `lexos_cross_connect` — Cross-lane fusion

### A-Tier (Fast)
- `exec_python` / `exec_git` / `exec_command`
- `grep` / `glob` / `view` / `edit` / `create`
- `sql` (session DB)
- `task` (parallel agents)

### B-Tier (Web)
- `web_search` / `web_fetch` (user authorized for research)

### FORBIDDEN
- `litigation_context-*` MCP tools (DEPRECATED)
- `powershell` (LAST RESORT only)

---

## VII. TECHNOLOGY STACK

### Compiled Languages
| Tool | Version | Purpose |
|------|---------|---------|
| Go | 1.26.1 | Ingest (8-worker goroutines) |
| Rust | 1.94.1 | tantivy, fd, bat, dust |
| Typst | 0.14.2 | Court PDF generation |

### Python ML/AI Stack
| Package | Purpose |
|---------|---------|
| torch 2.11.0 | ML backend (CPU) |
| sentence-transformers 5.3.0 | 384-dim embeddings |
| onnxruntime | Legal-BERT INT8 (26ms) |
| lancedb 0.30.0 | Vector DB (75K, sub-ms) |
| DuckDB 1.5.1 | 10-100x analytics |
| Polars 1.39.3 | 2-10x DataFrames |
| tantivy | Rust FTS, sub-ms BM25 |
| orjson 3.11.7 | 10x JSON |
| pypdfium2 4.30.0 | 5x PDF extraction |

### Rust CLI
| Tool | Purpose |
|------|---------|
| fd 10.4.2 | File finding (5x) |
| bat 0.26.1 | Syntax viewing |
| dust 1.2.4 | Disk analysis |
| just 1.48.1 | Task runner |

---

## VIII. SESSION BOOTSTRAP PROTOCOL

### Phase 1 — State Recovery
1. Read plan.md
2. Query todos: `SELECT * FROM todos WHERE status != 'done'`
3. Query session_handoff
4. Compute separation: `(today - 2025-07-29).days`
5. Query check_deadlines

### Phase 2 — Arsenal Activation
6. Query engine_registry
7. Query brain_registry
8. Verify litigation_context.db
9. Verify FTS5 indexes
10. Report readiness dashboard

### Phase 3 — Situational Awareness
11. nexus_priorities
12. nexus_readiness
13. lexos_gap_analysis
14. check_deadlines
15. judicial_intel

### Phase 4 — Wave Deployment
16. Deploy Wave 1 (Recon) agents
17. Cascade Waves 2-8 based on task
18. Persist all findings continuously
19. Update THEMANBEARPIG on convergence
20. Write session_handoff before close

---

## IX. WEAPON CHAINS SCHEMA

```sql
-- 2,179 rows mapping adversary actions to legal remedies
SELECT adversary, event_date, instance, weapon_type,
       effect_on_father, effect_on_child,
       doctrine, remedy, filing_stack, severity, lane
FROM weapon_chains
ORDER BY severity DESC, event_date;
```

Weapon types: FALSE_ALLEGATION, EX_PARTE, PARENTING_DENIAL, CONTEMPT_ABUSE,
PPO_WEAPONIZATION, JUDICIAL_BIAS, EVIDENCE_SUPPRESSION, PARENTAL_ALIENATION,
DUE_PROCESS_VIOLATION.

---

## X. THEMANBEARPIG INTEGRATION

13-layer D3.js force graph + pywebview:
1. Adversary nodes  2. Weapon clusters  3. Timeline edges  4. Evidence links
5. Doctrine nodes  6. Remedy paths  7. Effect radiants  8. Filing stacks
9. Impeachment chains  10. Causal chains  11. Cross-lane bridges
12. Severity heat map  13. Convergence indicators

25 MBP SINGULARITY Skills at `.agents/skills/SINGULARITY-MBP-*/SKILL.md`

---

## XI. CASE CONSTANTS

| Fact | Value |
|------|-------|
| Child | **L.D.W.** only |
| Defendant | **Emily A. Watson** |
| Judge | **Hon. Jenny L. McNeill** (TWO L's) |
| Former attorney | **Jennifer Barnes P55406 WITHDREW Mar 2026** |
| Separation | **Jul 29, 2025** compute dynamically |
| Trial date | **July 17, 2024** (NOT 2025) |
| Criminal | **100% SEPARATE** from Lanes A-F |
| MCL 722.27c | **DOES NOT EXIST** use MCL 722.23(j) |
| Ronald Berry | **NON-ATTORNEY** |

---

## XII. CONVERGENCE CRITERIA

System converges when ALL are TRUE:
- Evidence saturation >= 95% indexed
- Authority coverage >= 90% verified
- All adversaries have >= 10 impeachment items
- Zero orphaned graph nodes
- >= 2 filings at READY status
- Separation counter dynamically computed

---

## XIII. ANTI-DEGRADATION RULES

1. No deleting files (11_ARCHIVES/ only)
2. No MCP tools (local only)
3. No PowerShell when alternatives exist
4. No stubs (fully operational from first attempt)
5. No placeholder citations (DB-first)
6. No hardcoded counts (query live)
7. Error = Upgrade + Decompose
8. First attempt = apex quality
9. Persist continuously to DB
10. Checkpoint every 3 agent completions

---

*SINGULARITY-OMNISCIENCE-APEX v3.0.0*
*50+ engines. 23 brains. 75K vectors. 167K authority chains. 175K evidence quotes.*
*2,179 weapon chains. 5,059 judicial violations. 8 agent fleet waves.*
*ZERO API dependency. ZERO MCP. 100% LOCAL. FULL SPECTRUM OMNISCIENCE.*
'''

SKILL_PATH.write_text(CONTENT, encoding='utf-8')
print(f"Written {len(CONTENT)} chars to {SKILL_PATH}")
print(f"File size: {SKILL_PATH.stat().st_size} bytes")
print(f"Lines: {CONTENT.count(chr(10))}")
