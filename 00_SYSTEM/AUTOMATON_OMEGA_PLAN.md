# PLAN: AUTOMATON OMEGA — LEGAL REASONING AGI (v12.0)

> THEMANBEARPIG doesn't just DISPLAY data — it THINKS, REASONS, DISCOVERS, and PRODUCES.
> The world's first autonomous legal inference engine that derives causes of action from
> multi-dimensional evidence fusion, predicts adversary responses, and auto-generates
> court-ready filing skeletons. Nothing like this exists. Anywhere.

## Prior Work Complete
- **P1 (Engine Fleet): COMPLETE** — 4/4 sub-tasks, commit 74093389b
- **5 Engines wired**: CORTEX, CHRONOS, ORACLE, PROMETHEUS, ATHENA — 49/49 PASS, v11.0.0 deployed
- **P2B KAL**: 20/30 done, 487 new evidence rows
- **Data corpus**: 176K evidence, 168K authority chains, 27 COAs, 162 IRACi, 5.2K impeachment, 2.5K contradictions, 1.9K judicial violations, 222 cartel connections, 19.8K rules, 16.9K timeline events

## WHAT MAKES THIS ONE-OF-A-KIND (No System Like This Exists)

1. **Multi-Dimensional Inference**: Not just graph walking — fuses evidence, authority, temporal, adversary, judicial, and procedural dimensions simultaneously
2. **Constitutional Cascade**: State violation auto-elevates to federal §1983 when pattern matches 14th Amendment
3. **Adversary Prediction Loop**: Derived COA → ORACLE predicts counter → AUTOMATON pre-builds rebuttal chain
4. **Self-Calibrating Confidence**: Tracks prediction accuracy across cycles, adjusts scoring weights
5. **Filing Stack Auto-Assembly**: COA at 85%+ confidence → generates complete motion skeleton with exhibits, authorities, cross-exam scripts
6. **Compound Discovery**: Things NO single table reveals — cross-table fusion that finds connections spanning evidence + timeline + judicial + authority simultaneously
7. **Real-Time Push Intelligence**: Daemon discovers → JS visualizes → user acts. No polling, no refresh.

## THE 6 REASONING LAYERS (Not Just "Graph Walking")

### Layer 1: TOPOLOGICAL (Graph Structure Intelligence)
- NetworkX DiGraph from 2,529 typed nodes × 2,018 typed links × 20 layers
- **Centrality Analysis**: Who is the KEYSTONE? Remove them → conspiracy collapses
- **Community Detection**: Louvain algorithm → which actor clusters operate together?
- **Bridge Detection**: Which connections SPAN across lanes? (Cross-lane = multiplied damages)
- **Cycle Detection**: Feedback loops of abuse (file PPO → get custody → deny PT → file contempt → jail father → repeat)
- **Shortest Path Analysis**: Minimum-hop connection between any two entities

### Layer 2: TEMPORAL (Chronological Reasoning)
- CHRONOS feeds 16.9K time-ordered events
- **Escalation Detection**: Is the abuse pattern intensifying? Compute severity slope
- **Retaliation Timing**: Action A → Response B within N days? (Emily files → McNeill orders within 48hr)
- **Statute of Limitations Windows**: Each derived COA auto-calculates: still actionable? How long left?
- **Prejudice Accumulation**: Ongoing harm duration (250+ days separation) strengthens damages
- **Temporal Clustering**: Events that cluster in time suggest coordination

### Layer 3: DOCTRINAL (Legal Element Satisfaction)
- For each of 27 COAs + 18 legal theories, score element satisfaction 0-100%:
  - Count: how many evidence_quotes map to this element?
  - Weight: how strong is each piece of evidence? (relevance_score)
  - Authority: does authority_chains_v2 have supporting citations?
  - IRAC: do existing IRAC analyses cover this theory?
- **Gap Detection**: Which elements are below 70%? → prioritized evidence hunt list
- **Element Superposition**: One evidence item can satisfy elements of MULTIPLE COAs simultaneously

### Layer 4: ADVERSARIAL (Counter-Strategy Prediction)
- For each derived COA, ORACLE predicts opposing response
- **Counter-Rebuttal Chain**: COA → predicted counter → pre-built rebuttal → predicted re-counter → final killer argument
- **Weakness Identification**: Red-team our own position — where are WE vulnerable?
- **Win Probability**: Factor in judge tendencies (McNeill: 85% favors mother), evidence strength, authority completeness
- **Impeachment Leverage**: For each adverse witness needed, how impeachable are they? (5.2K impeachment items)

### Layer 5: STRATEGIC (Filing Optimization)
- PROMETHEUS determines optimal filing SEQUENCE across all lanes
- **Cross-Lane Multiplier**: Filing A (disqualification) UNLOCKS Filing B (reconsideration) which ENABLES Filing C (federal §1983)
- **Deadline Awareness**: Which COAs must be filed NOW vs can strategically wait?
- **Judicial Routing**: McNeill patterns vs federal judge patterns vs JTC patterns → tailor filing for the decision-maker
- **Damages Cascade**: Each filed COA increases damages for unfiled COAs (compounding harm narrative)

### Layer 6: SYNTHESIS (Compound Intelligence)
- **Cross-Session Memory**: Results from inference cycle N feed cycle N+1 (persistent to DB)
- **Anomaly Detection**: Flag things that DON'T fit patterns (potential undiscovered evidence)
- **Convergence Tracking**: Overall case strength trajectory — improving or declining?
- **Novel Discovery Scoring**: How "new" is this finding? Seen before in prior cycles? First-time = high novelty
- **Confidence Calibration**: Track: "I predicted X with 78% confidence → new evidence confirms/denies" → adjust weights

## AUTHORITY TEMPLATES (20 Legal Route Maps — Expanded from 10)

| # | Template | Graph Pattern | Auto-Derived COA | Layer Fusion |
|---|---|---|---|---|
| 1 | MCR 2.003(C)(1)(b) | JUDICIAL → ADVERSARY via PERSONAL/FAMILY link | Disqualification (bias) | Topo + Judicial |
| 2 | MCR 2.003(C)(1)(a) | JUDICIAL node has PERSONAL_KNOWLEDGE edges to case facts | Disqualification (knowledge) | Topo + Evidence |
| 3 | MCL 722.23(j) | ADVERSARY → PT_DENIAL weapons ≥3 + ALIENATION indicators | Factor (j) — willingness to facilitate | Topo + Temporal |
| 4 | MCL 722.23(k) | ADVERSARY → FALSE_ALLEGATION + DV_PROJECTION pattern | Factor (k) — domestic violence | Evidence + Adversary |
| 5 | 42 USC §1983 | JUDICIAL + ADVERSARY via ≥2 CONSPIRACY paths + STATE_ACTION | Federal civil rights | ALL 6 layers |
| 6 | 42 USC §1985(3) | ≥3 actors connected through COORDINATED_ACTION edges in same timeframe | Federal conspiracy | Topo + Temporal |
| 7 | MCL 600.2911 | FALSE_ALLEGATION → POLICE_REPORT → NO_ARREST → HARM chain | Malicious prosecution | Evidence + Temporal |
| 8 | Mathews v Eldridge | EX_PARTE weapon + NO_NOTICE + LIBERTY_INTEREST | Due process violation | Doctrinal + Judicial |
| 9 | MCR 3.707 | PPO_WEAPONIZATION × CUSTODY_INTERFERENCE in timeline | PPO abuse / dissolution | Temporal + Doctrinal |
| 10 | Canon 2 + Canon 3 | FORMER_PARTNER + SAME_ADDRESS + FOC_PIPELINE links | Appearance of impropriety | Topo + Judicial |
| 11 | IIED Elements | EXTREME_CONDUCT → SEVERE_DISTRESS → OUTRAGEOUS pattern | Intentional infliction | Evidence + Temporal |
| 12 | Civil Conspiracy | ≥3 actors via COORDINATED actions + SHARED_BENEFIT | Civil conspiracy (state) | ALL 6 layers |
| 13 | Evidence Suppression | EXCLUDE_EVIDENCE edges from JUDICIAL to ≥3 EVIDENCE nodes | Evidentiary due process | Judicial + Doctrinal |
| 14 | False Imprisonment | CONTEMPT → JAIL → NO_DUE_PROCESS chain | False imprisonment / §1983 | Temporal + Doctrinal |
| 15 | Monell Liability | INSTITUTION → PATTERN_OF_FAVORABLE_TREATMENT → ADVERSARY | Institutional liability | Topo + Strategic |
| 16 | Abuse of Process | LEGAL_PROCESS → ULTERIOR_PURPOSE → HARM (not legitimate litigation goal) | Abuse of process | Evidence + Adversary |
| 17 | Fraud on Court | ADVERSARY → FALSE_STATEMENT → COURT_RELIED → ADVERSE_ORDER | Fraud on the court | Evidence + Temporal |
| 18 | Parental Alienation | ALIENATION_BEHAVIOR × 3+ over 6+ months + CHILD_HARM | MCL 722.23(j) + damages | Temporal + Evidence |
| 19 | Constitutional Cascade | ANY state violation + LIBERTY/PROPERTY interest → auto-check 14th Amend | §1983 elevation | Doctrinal + Strategic |
| 20 | Retaliation Pattern | FATHER_ACTION → ADVERSARY_RETALIATION within 7 days × 3+ | Retaliatory conduct | Temporal + Adversary |

## 8 DELIVERABLES (Expanded from 6)

### D1: automaton.py — THE REASONING ENGINE (~1,200 lines)
The core AGI. Self-contained Python module, no external dependencies except NetworkX + sqlite3.

```
Classes:
  AuthorityTemplate    — legal authority as multi-dimensional matching rule
  InferenceResult      — discovered pattern with confidence, evidence chain, filing skeleton
  ReasoningLayer       — abstract base for the 6 layers
  TopologicalLayer     — centrality, communities, bridges, cycles, paths
  TemporalLayer        — escalation, retaliation timing, SOL windows, clustering
  DoctrinalLayer       — element satisfaction scoring, gap detection, superposition
  AdversarialLayer     — counter-prediction, weakness ID, win probability
  StrategicLayer       — filing sequence, cross-lane multiplier, damages cascade
  SynthesisLayer       — cross-session memory, anomaly detection, confidence calibration
  GraphWalker          — NetworkX DiGraph builder from DB tables
  AutomatonEngine      — daemon thread orchestrator, cycle manager, event emitter

Key Methods:
  build_graph()        — construct DiGraph from evidence, timeline, judicial, cartel, adversary tables
  run_inference_cycle() — execute all 6 layers in sequence, produce InferenceResult list
  match_template(t)    — match single AuthorityTemplate against current graph state
  derive_coa(node)     — derive all applicable COAs for a specific node
  find_paths(a, b)     — all paths between two entities with legal significance
  constitutional_cascade(result) — check if state violation elevates to federal
  predict_counter(coa) — ORACLE-powered adversary prediction
  generate_filing_skeleton(coa) — PROMETHEUS-powered filing stack skeleton
  calibrate_confidence() — self-improving accuracy tracking
  persist_results()    — write discoveries to DB for cross-session continuity

Threading:
  daemon=True, 30-second cycles
  Thread-safe SQLite (check_same_thread=False + WAL + busy_timeout=60000)
  Event-driven push: callback → window.evaluate_js()
  Circuit breaker: if JS unresponsive for 3 cycles, pause and retry
```

### D2: Wire AUTOMATON into adversary_blueprint.py (+300 lines Python)
Full integration following proven pattern (import guard + lazy init + API methods).

```
12 New API Methods:
  automaton_status()          — running/paused/stopped, cycle count, last discovery time
  automaton_start()           — start daemon thread
  automaton_stop()            — graceful stop with state persist
  automaton_results(limit)    — latest N inference results with confidence scores
  automaton_coa_for_node(id)  — all derived COAs for a specific graph node
  automaton_paths(a, b)       — legal paths between two entities
  automaton_templates()       — list all 20 authority templates with match status
  automaton_centrality()      — top 20 most legally significant nodes
  automaton_force_cycle()     — trigger immediate inference cycle
  automaton_gaps()            — evidence gaps that would upgrade COA confidence
  automaton_filing_skeleton(coa_id) — generate complete filing skeleton for a COA
  automaton_compound_discoveries() — cross-table compound findings
```

### D3: Node Deep-Dive Modal — THE DOSSIER EXPERIENCE (+600 lines JS)
Full-screen slide-in panel with 6 tabs. Each tab fuses data from ALL 6 engines.

```
Tab A: PROFILE — identity card, threat gauge, credibility ring, top 5 quotes
Tab B: CONNECTIONS — interactive mini-graph (PixiJS sub-renderer), recursive drill-down
Tab C: LEGAL — auto-derived COAs from AUTOMATON (THE KILLER FEATURE)
  - Each COA shows: elements satisfied (green) / missing (red)
  - Evidence chain visualization (which quotes prove which elements)
  - "Generate Filing" button → automaton_filing_skeleton()
  - Confidence meter + predicted adversary counter
Tab D: TIMELINE — CHRONOS-powered entity timeline, escalation sparkline
Tab E: EVIDENCE VAULT — searchable gallery, sort by relevance/date/severity
Tab F: WEAPONS ARRAY — PROMETHEUS arsenal, cross-exam scripts, rebuttals

UI:
  - Slide-in from right (60% width), semi-transparent backdrop
  - Animated tab transitions
  - Close with ESC, click-outside, or X button
  - Responsive within the pywebview window
  - Each connection in Tab B is CLICKABLE → opens THAT node's modal (recursion)
```

### D4: CrossWire Intelligence System (+250 lines JS)
Click any LINK between nodes → relationship intelligence panel.

```
Components:
  - Relationship card: what connects A↔B, evidence supporting it, legal implications
  - "Derive COA" button: walks paths between these two nodes specifically
  - "Constitutional Cascade" indicator: if relationship implies federal violation
  - Conspiracy path tracer: if >1 path exists between them
  - Mini-timeline of their interactions (filtered CHRONOS data)
  - Strength indicator: how many evidence items support this connection
```

### D5: Inference Theater — LIVE REASONING DASHBOARD (+400 lines JS)
Collapsible bottom panel showing AUTOMATON thinking in real-time.

```
Sections:
  - Status Bar: cycle count, last run time, discoveries today, confidence trend
  - Live Feed: scrolling list of discoveries as they happen (newest first)
    - Each entry: timestamp, COA name, confidence %, affected nodes, "View" button
  - Top 5 Strongest COAs: ranked cards with confidence gauges
  - Gap Alert Panel: "Evidence X would upgrade COA Y from 72% to 91%"
  - Compound Discoveries: cross-table findings that span multiple dimensions
  - Constitutional Cascade Alerts: state→federal elevation opportunities

Visual Effects:
  - "Neural pathway" animations on the graph when a discovery is made
  - Confidence auras on nodes (blue→green→yellow→red intensity)
  - Gap pulse: missing evidence nodes pulse like a heartbeat
  - Cross-wire lightning: animated bolt when cross-lane connection found
  - Whisper alerts: text slides in from edge with new discovery
```

### D6: ROOMS Navigation System (+350 lines JS)
Transform the exe from a single-page graph into a multi-room command center.

```
Room 1: NEXUS (current graph + D3/D4/D5 enhancements) — Keyboard: 1
Room 2: WAR ROOM — filing Kanban (DRAFT→QA→READY→FILED), deadline tickers, EGCP gauges
Room 3: DOSSIER ROOM — adversary grid with threat/evidence/impeachment badges
Room 4: CHRONICLE — horizontal mega-timeline 2023-2026, actor swimlanes, density heatmap
Room 5: ARSENAL — authority citation graph (force-directed), coverage heat map
Room 6: SITUATION ROOM — case health dashboard, separation counter, filing progress

Navigation:
  - Top bar with room icons (always visible)
  - Keyboard shortcuts (1-6)
  - Room transitions: smooth crossfade (200ms)
  - Each room remembers its scroll/zoom state
  - AUTOMATON feed visible in ALL rooms (bottom-right mini-panel)
```

### D7: Auto-Filing Skeleton Generator (+200 lines Python)
When AUTOMATON derives a high-confidence COA, auto-generate filing skeleton.

```
Output per COA:
  - Motion outline: relief requested, grounds, IRAC structure
  - Exhibit list: specific evidence_quotes with Bates numbers
  - Authority chain: primary citation → supporting citations → pin cites
  - Cross-exam script: top 10 questions per adverse witness (from impeachment_matrix)
  - Predicted counter-arguments + pre-built rebuttals
  - Filing readiness score
  - Estimated damages range
  - Recommended court + filing sequence position
```

### D8: Rebuild + Deploy as v12.0.0
```
Updates:
  - THEMANBEARPIG.spec: add automaton.py + networkx to hiddenimports
  - test_all_engines.py: add 15+ AUTOMATON tests (inference cycle, template matching, COA derivation, gap detection, constitutional cascade, compound discovery)
  - Total tests: 49 existing + 15 new = 64+ tests, ALL PASS
  - Rebuild exe, deploy to Desktop
  - Save all source files to Desktop + D:\LitigationOS_tmp
```

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
