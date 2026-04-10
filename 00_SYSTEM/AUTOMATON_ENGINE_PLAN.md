# PLAN: AUTONOMOUS LEGAL INFERENCE ENGINE + DEEP-DIVE UI (v12.0)

> THEMANBEARPIG becomes a THINKING MACHINE — auto-derives causes of action from graph topology

## Prior Work Complete
- **P1 (Engine Fleet): COMPLETE** — 4/4 sub-tasks, commit 74093389b
- **5 Engines wired**: CORTEX, CHRONOS, ORACLE, PROMETHEUS, ATHENA — 49/49 PASS, v11.0.0 deployed
- **P2B KAL**: 20/30 done, 487 new evidence rows

## SESSION FOCUS: Build ENGINE 6 — AUTOMATON

### What It Does
A daemon thread inside THEMANBEARPIG.exe that autonomously:
1. Builds a NetworkX DiGraph from 2,529 nodes x 2,018 links
2. Runs 10 legal authority templates as graph-matching rules every 30 seconds
3. Auto-derives causes of action by walking paths between entities
4. Pushes discoveries to the JS frontend in real-time
5. Persists results to DB for cross-session continuity

### Authority Templates (Laws as Route Maps)
| Template | Graph Pattern | Auto-Derived COA |
|---|---|---|
| MCR 2.003(C)(1)(b) | JUDICIAL → ADVERSARY via PERSONAL link | Disqualification |
| MCL 722.23(j) | ADVERSARY → PT_DENIAL weapon x3+ | Factor (j) violation |
| 42 USC 1983 | JUDICIAL + ADVERSARY via 2+ CONSPIRACY paths | Federal civil rights |
| MCL 600.2911 | FALSE_ALLEGATION → HARM chain | Malicious prosecution |
| Mathews v Eldridge | EX_PARTE weapon + NO_NOTICE | Due process violation |
| MCR 3.707 | PPO_WEAPONIZATION x CUSTODY_INTERFERENCE | PPO abuse |
| Canon 2 | FORMER_PARTNER + SAME_ADDRESS + FOC | Appearance of impropriety |
| IIED | EXTREME_CONDUCT → SEVERE_DISTRESS | Intentional infliction |
| Conspiracy | 3+ actors via coordinated actions | Civil conspiracy |
| Evidence suppression | Systematic exclusion pattern | Evidence suppression |

## 6 Deliverables

### D1: automaton.py (~800 lines)
- `AuthorityTemplate` dataclass — legal authority as graph pattern
- `InferenceResult` dataclass — discovered patterns/COAs
- `GraphWalker` — NetworkX builder, template matching, path analysis
- `AutomatonEngine` — daemon thread, inference cycles, event emission
- 10 authority templates, 7 graph algorithms
- Thread-safe SQLite (check_same_thread=False + WAL)

### D2: Wire into adversary_blueprint.py (+200 lines)
- Import guard + lazy initializer
- 8 API methods: status, start/stop, results, coa_for_node, paths, templates, centrality, force_cycle

### D3: Node Deep-Dive Modal (+500 lines JS)
- Full-screen slide-in dossier: PROFILE, CONNECTIONS, LEGAL, TIMELINE, EVIDENCE, WEAPONS
- LEGAL tab = auto-derived COAs from AUTOMATON (the killer feature)
- Recursive drill-down (click connection → opens that node's modal)

### D4: CrossWire Relationship Cards (+200 lines JS)
- Click any link → relationship intelligence card
- Legal implications + "Derive COA" button

### D5: Inference Dashboard Panel (+300 lines JS)
- Bottom panel: cycle status, live discovery feed, pattern alert badges
- Top 5 strongest COAs with confidence scores

### D6: Rebuild + Deploy
- Update spec (add automaton.py + networkx), 10+ new tests, exe v12.0.0

## System Scorecard — Current vs Target

| Domain | Current | Target | Gap | Phase |
|--------|---------|--------|-----|-------|
| KRAKEN v2.3.0 | 9.5 | 9.5 | -- | Done |
| THEMANBEARPIG v10.0 | 9.0 | 9.0 | -- | Done |
| Extension Tools (7) | 9.0 | 9.5 | +0.5 | P4 |
| Database Corpus (4.7 GB) | 9.0 | 9.5 | +0.5 | P2 |
| Adversary Dossiers (25) | 8.5 | 9.0 | +0.5 | P2 |
| **Engine Fleet** | **4.0** | **9.0** | **+5.0** | **P1** |
| **Filing Pipeline** | **5.0** | **9.0** | **+4.0** | **P5** |
| **Total Legal Convergence** | **3.0** | **9.0** | **+6.0** | **P3** |
| **D3 Visualization Data** | **1.0** | **9.0** | **+8.0** | **P3** |
| **OVERALL** | **6.4** | **9.2** | **+2.8** | All |

> The 4 RED domains (Engine 4.0, D3 1.0, Convergence 3.0, Pipeline 5.0) are dragging the score.
> Fix those first -> system reaches 9.0 -> THEN produce court documents.

---

## PHASE 1: ENGINE FLEET HARDENING (4.0 -> 9.0)
> Priority: HIGHEST -- engines are the backbone. Nothing works if engines are broken.

### 1A. Test Infrastructure Repair
- Fix `run_all_tests.py` cp1252 Unicode crash -> ASCII-only output
- Create template smoke test: import + instantiate + basic operation
- Generate smoke tests for ALL 35 functional engines
- Wire into `scripts/verify.bat` for one-command validation
- **Score impact: 4.0 -> 6.5** (testable = trustable)

### 1B. Broken Engine Repair
- `ingest` engine: add `__init__.py`, verify Go pipeline integration
- `templates` engine: add `__init__.py` or merge into filing_framework
- Deprecate 4 stubs: docforge_v18, docforge_v19, mi_warchest_v2, ocr_embed_v2
- Clean deprecated code paths that reference non-existent engines
- **Score impact: 6.5 -> 7.5**

### 1C. Database Optimization
- Rebuild FTS5 indexes: evidence_fts, timeline_fts, md_sections_fts
- `ANALYZE` all hot tables (evidence_quotes, authority_chains_v2, timeline_events)
- Add composite indexes for multi-column WHERE patterns in hot queries
- WAL checkpoint on litigation_context.db
- Consolidate connection patterns to shared.get_db()
- **Score impact: 7.5 -> 8.5**

### 1D. Path, Module & Hygiene Audit
- Fix Rule 30 violations: hardcoded `C:\Users\andre\` paths -> shared.config
- Verify all engines use `shared.get_db()` not raw `sqlite3.connect()`
- Verify FTS5 safety protocol (Rule 15) across all query paths
- Shadow module audit (22 hijacking files at repo root)
- **Score impact: 8.5 -> 9.0**

---

## PHASE 2: EVIDENCE SATURATION (DB 9.0 -> 9.5, Dossiers 8.5 -> 9.0)
> Priority: HIGH -- more evidence = stronger filings when we get there.

### 2A. Process listofgoodfiles.txt via KRAKEN
- 10,524 curated files on Desktop -- untouched goldmine
- Run targeted KRAKEN rounds against this curated list
- Expected yield: ~3,000+ HIGH findings (curated = high quality)
- Auto-persist to evidence_quotes + timeline_events

### 2B. KAL Autonomous Rounds (20 rounds, self-evolving)
- Run 20-round KAL across all 7 drives
- Rotating focus: adversary -> judicial -> custody -> ppo -> housing -> legal
- Auto-persist to evidence_quotes + dossier expansion
- Self-evolution: track learning metrics, adaptive scoring

### 2C. Dossier Expansion Campaign
- Target thin dossiers: Kostrzewa (36 lines), VanDam (127), Brown (140)
- Cross-reference KRAKEN findings with dossier gaps
- Add verbatim quotes, pin cites, source paths
- Target: every dossier >=300 lines, avg 350+

### 2D. Critical Evidence Acquisition Hunt
- **NS2505044** (Albert premeditation admission) -- search all drives
- **HealthWest Evaluation** (Andrew cleared, excluded by McNeill)
- **Officer Randall Report** (Emily meth use admission)
- **AppClose 305+ incidents** (parenting time interference)
- These 4 are SMOKING GUNS -- finding any one is a major win

---

## PHASE 3: INTELLIGENCE AMPLIFICATION (D3 1.0 -> 9.0, Convergence 3.0 -> 9.0)
> Priority: HIGH -- these are the TWO LOWEST scores. Biggest bang for effort.

### 3A. Brain Refresh & Chain Recomputation
- Rebuild mbp_brain.db from 120K+ evidence_quotes + 168K authority_chains
- Recompute chains via `compute_chains.py`
- Run `brain_evolution.py` for cross-edge discovery
- Target: 300K+ nodes, 1M+ edges (from current 232K/770K)

### 3B. D3 Visualization Data Population
- `graph_data_v7.json` = STUB (1 node, 1 link) -- **this is why score is 1.0**
- Run `export_brain_d3.py` with full refreshed brain data
- Target: 2,500+ nodes x 2,000+ links x 20 layers
- Regenerate `THEMANBEARPIG_v7.html` for repo version
- Verify WebGL rendering with real data
- **Score impact: 1.0 -> 9.0** (single biggest score jump)

### 3C. Total Legal Convergence Waves 1-4
- **W1**: Parse 5,613 HTML files in `09_REFERENCE/` -> michigan_rules_extracted
- **W2**: Complete all 9 MCR chapters (MCR 1-9 fully covered)
- **W3**: MCL expansion: 68 -> 500+ statutes
- **W4**: 200+ verified case citations with pin cites
- Update convergence_domains, convergence_waves, convergence_todos tables
- **Score impact: 3.0 -> 8.0**

### 3D. Semantic Vector Index Refresh
- Current: 75K vectors in LanceDB
- Re-index with all latest evidence + authorities + rules
- Target: 150K+ vectors
- Verify cross-encoder reranking pipeline for search quality
- **Score impact: part of overall convergence 8.0 -> 9.0**

### 3E. Timeline Enrichment
- Current: 16.8K events
- Mine police_reports (356) for missing dates
- Extract dates from KRAKEN findings (Phase 2 output)
- Build per-lane master chronologies (A, B, D, E, F, CRIMINAL)
- Target: 20K+ events with lane-specific narratives

---

## PHASE 4: SYSTEM EVOLUTION & POLISH (Extensions 9.0 -> 9.5, final touches)
> Priority: MEDIUM -- polish what works, add missing capabilities.

### 4A. KRAKEN v3.0 Features
- Daemon mode: continuous background hunting
- `listofgoodfiles.txt` batch processor (direct file list input)
- Cross-file contradiction detection
- Filing-readiness auto-scoring after rounds

### 4B. Extension Expansion (4 new tools)
- `filing_forge` -- court PDFs from CLI via Typst
- `deadline_alert` -- overdue + critical deadline display
- `evidence_chain` -- claim -> evidence -> authority trace
- `qa_sweep` -- filing QA checks from CLI

### 4C. Agent Fleet Optimization
- Audit 50 agent definitions, merge redundant
- Add: COA-brief-writer, affidavit-generator agents
- Self-evolving fleet manager

### 4D. Cross-Lane Emergence Detection
- Entity overlap, authority completion, contradictions
- Cross-lane impeachment packages
- Novel strategy detection (novelty >=7)
- Generates strategic intelligence for Phase 5

---

## ======== 9.0 GATE CHECK ========
> Before entering Phase 5, verify ALL domains >= 9.0:
> Engine Fleet, D3 Viz, Legal Convergence, Evidence, Dossiers, DB, Extensions.
> If any domain < 9.0, iterate on that domain until it passes.

---

## PHASE 5: FILING PRODUCTION (Only after system >= 9.0)
> Priority: FINAL -- all infrastructure must be solid before generating court docs.

### 5A. Court-Ready PDF Generation Pipeline
- Activate Typst engine on all 9 GOLDEN_SET filings
- Generate court-formatted PDFs (Times New Roman 12pt, double-spaced, 1" margins)
- Compile complete packet families per filing type rules
- Validate MCR format compliance per lane

### 5B. Missing Affidavit Generation (5 filings)
- **F03** (Disqualification): Affidavit of bias -- MCR 2.003 specific facts
- **F06** (JTC): Supporting affidavit -- judicial violation chronology
- **F08** (PPO Termination): Changed circumstances affidavit
- **F09** (COA Brief): Appellate affidavit -- key record citations
- **F10** (COA Emergency): Emergency affidavit -- irreparable harm

### 5C. Exhibit Compilation & Bates Stamping
- Populate bates_registry table (currently EMPTY)
- Stamp all exhibit PDFs: `PIGORS-{LANE}-{NNNNNN}`
- Generate exhibit indices for each packet
- Cross-reference exhibits to affidavit paragraphs

### 5D. Service Proof & QA
- Update all COS: Barnes WITHDREW -> serve Emily directly at 2160 Garland Dr
- FOC: Pamela Rusco, 990 Terrace St, Muskegon, MI 49442
- Generate MC 12 for each packet
- Anti-hallucination sweep (Rule 3)
- Red team all filings -- adversarial vulnerability scan
- GO/NO-GO per filing

---

## PHASE 6: COMMERCIAL & PACKAGING (Post-9.0)
> Priority: LOWEST -- after everything else is solid.

### 6A. Commercial Packaging
- KRAKEN as standalone product
- Documentation, README, LICENSE
- Demo mode with sample data
- Privacy-safe packaging (child name sanitization)

---

## Execution Order (System-First)

```
PHASE 1 (IMMEDIATE) -- Engine Fleet Hardening
  1A -> 1B -> 1C -> 1D (sequential, each builds on prior)

PHASE 2 (PARALLEL with P1) -- Evidence Saturation
  2A || 2B -> 2C -> 2D (KAL + listofgoodfiles in parallel)

PHASE 3 (AFTER P1 engines stable) -- Intelligence
  3A -> 3B (brain -> D3, sequential)
  3C || 3D || 3E (convergence + vectors + timeline in parallel)

PHASE 4 (PARALLEL with P3) -- Evolution
  4A || 4B -> 4C -> 4D

========================================
  *** 9.0 GATE CHECK ***
  All domains must score >= 9.0
========================================

PHASE 5 (AFTER 9.0 GATE) -- Filing Production
  5A -> 5B -> 5C -> 5D (sequential, each builds on prior)

PHASE 6 (POST-FILING) -- Commercial
  6A (standalone)
```

## Success Metrics (9.0 Gate)

| Metric | Current | 9.0 Gate | Final Target |
|--------|---------|----------|--------------|
| Engine smoke tests passing | 1/37 | 35/37 | 37/37 |
| Broken engines fixed | 35/37 | 37/37 | 37/37 |
| D3 graph nodes | 1 | 2,500+ | 3,000+ |
| Evidence quotes | 120,347 | 140,000+ | 150,000+ |
| Authority chains | 168,261 | 190,000+ | 200,000+ |
| Michigan rules | 19,876 | 23,000+ | 25,000+ |
| Semantic vectors | 75K | 125K+ | 150K+ |
| Timeline events | 16,886 | 19,000+ | 20,000+ |
| Dossier avg lines | ~200 | 300+ | 350+ |
| GOLDEN_SET complete | 4/10 | -- | 10/10 |
| Court-ready PDFs | 0 | -- | 10+ |
| Filing QA pass rate | unknown | -- | 100% |

> Rows without 9.0 Gate values are Phase 5 items -- only tracked after gate passes.
