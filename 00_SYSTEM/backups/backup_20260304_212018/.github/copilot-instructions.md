# LitigationOS — Copilot Instructions (v13.0 APEX-CONVERGENCE)

## ⚡ AGENT ORCHESTRATION MODE — FULL FLEET ENABLED

**Sub-agents and parallel execution are ENABLED and ENCOURAGED.**

1. **USE** the `task` tool to spawn sub-agents (explore, task, general-purpose, code-review, custom agents) for parallel work.
2. **USE** background mode for independent tasks that can run simultaneously.
3. **PRIORITIZE** efficiency: parallelize reads, audits, and independent operations.
4. **SELF-HEAL**: On error, retry with backoff. On crash, checkpoint and resume. On complexity, decompose and delegate.
5. **NEVER** lose data — move to Recycle Bin, never hard-delete. Backup before destructive ops.
6. **ALWAYS** log actions to the session SQL database for traceability.
7. The canonical system location is `C:\Users\andre\LitigationOS` — all paths resolve here.
8. The central database is `C:\Users\andre\LitigationOS\litigation_context.db` (10.2 GB, 655 tables, 11.7M rows) — pipeline writes, apps read.
9. **Max 3 concurrent background agents** — enforced by `db_lock_manager.py` to prevent EAGAIN pipe buffer overflow.

## 🐻 MANBEARPIG Startup Protocol (run on every session)

```powershell
# 1. Generate startup report (DB health, deadlines, evidence, sessions)
python C:\Users\andre\LitigationOS\00_SYSTEM\local_model\copilot_startup_hook.py --file
# 2. Read the report for instant context
cat C:\Users\andre\LitigationOS\00_SYSTEM\STARTUP_REPORT.md
# 3. Recall past sessions for continuity
python C:\Users\andre\LitigationOS\00_SYSTEM\local_model\session_recall.py recent
```

The startup hook generates `STARTUP_REPORT.md` with: separation day count, deadline urgency scores, filing readiness, evidence arsenal counts, system health, and recent Copilot session summaries.

---

## System Identity

LitigationOS is a litigation intelligence system for Michigan family law (Pigors v. Watson). It has three integrated subsystems: a **16-phase Python data pipeline** with a **112-agent fleet** (56 Delta9 + 12 Delta999 + 31 Copilot + 13 superpower agents), a **local-first AI engine** (zero-network), and an **Electron+React+Node desktop app** with web and mobile frontends. All data stays local on Windows. The pipeline processes ~3.3GB of evidence across 6+ drives into court-ready filings. The system currently manages **24+ filing stacks** producing **80+ court-ready PDFs** with readiness scores.

---

## Architecture

### Data Flow (end-to-end)

```
Raw Files (C:\, D:\, F:\, G:\, H:\, I:\)
  → Phase 0 Safety Snapshot (SHA-256 manifest + backup)
  → Phases 1-3: Inventory → Dedup → Classify (lane assignment via MEEK signals)
  → Phases 4a-4e: Extract (PDF/DOCX/structured/atomize/archive)
  → Phase 5: LEXOS Brain Feed (50 micro-brains, 8 categories)
  → Phase 6: Gap Analysis (EGCP scoring per legal action)
  → Phases 7a-7c: Graph Delta → Synthesis Merge → Knowledge Merge
  → Phase 8: Litigation Refresh → Phase 9: MCP Ingest
  → Phases 10-12: Judicial Analysis → Legal Action Discovery → Rule Audit
  → Phases 13-16: Refinement → Finalization → Validation → Desktop Offload
  → 04_COURT_FILINGS/03_FINAL/COURT_READY/ (48 judicial-grade documents)
```

### Six Case Lanes (IRON LAW — never cross-contaminate)

| Lane | Subject | MEEK | Case Numbers | DB |
|------|---------|------|-------------|-----|
| **A** | Watson custody | MEEK2 | 2024-001507-DC, 2023-5907-PP | `lane_A_custody.db` |
| **B** | Shady Oaks housing | MEEK1 | 2025-002760-CZ | `lane_B_housing.db` |
| **C** | Convergence (cross-lane) | — | Multi-lane | `lane_C_convergence.db` |
| **D** | PPO / Protection Orders | MEEK3 | 2024-001507-DC, 2023-5907-PP | `lane_D_ppo.db` |
| **E** | Judicial Misconduct / JTC | MEEK4 | 2024-001507-DC | `lane_E_misconduct.db` |
| **F** | Appellate (COA/MSC) | MEEK5 | Assigned on filing | `lane_F_appellate.db` |

MEEK signals are compiled regexes in `config.py` → `MEEK_SIGNALS` dict. Detection priority: **E → D → F → C → A → B**. A `LaneCrossContaminationError` (non-fatal, skip-item) is raised when evidence from the wrong lane is detected.

### 56-Agent Fleet (DELTA9 Architecture) + Delta999/Copilot Extensions

All agents inherit `Agent9999` from `agents/agent_base.py`. Two parallel lanes converge:

- **Lane 1 (I/O):** Tiers 1-3 — A01-A12 (indexing, dedup, extraction)
- **Lane 2 (Intelligence):** Tiers J/K/L — J01-L08 (judicial profiling, case intel, legal analysis)
- **Convergence:** F01-F06 (filing assembly, brain feed, graph build, certification)

**Total Fleet: 112 agents**
| Fleet | Count | Role |
|-------|-------|------|
| Delta9 (A01-L08) | 56 | Core pipeline agents (I/O, intelligence, convergence) |
| Delta999 | 12 | Advanced engines (classifier, validator, brief, opposing, settlement, assembly, deadline, db_lock) |
| Copilot agents (.copilot/agents/) | 31 | Specialized Copilot sub-agents (see directory below) |
| Superpower agents | 13 | Cross-cutting orchestration, governance, self-evolution |

Agent contract: `run() → AgentResult(agent_id, status, stats)`. Status: SUCCESS | FATAL | CRASH.
Agent data: `agents/master_index.db` (SQLite WAL mode, ~3.3GB). Schema: `files`, `ready_queue`, `dedup_clusters`, `zip_contents`, `atoms`, `judicial_findings`, `action_scores`, `agent_log`.

Agent fleet subdirectories under `00_SYSTEM/pipeline/agents/`:
- `lane1_infrastructure/` — A01-A12 (indexing, dedup, extraction agents)
- `lane2_intelligence/` — J01-L08 (judicial profiling, case intel, legal analysis agents)
- `convergence/` — F01-F06 (filing assembly, brain feed, graph build, certification agents)
- `checkpoints/` — crash-resume state per agent

### 7-Layer Error Protocol (every agent, non-negotiable)

1. Try operation → 2. Specific catch → targeted recovery → 3. Broad catch → log + skip + continue → 4. Checkpoint every N items → crash-resume → 5. Deadman switch (120s no progress → self-diagnose) → 6. Agent retry (3× exponential backoff) → 7. Tier fallback → orchestrator flags + continues

### AI Provider Stack (PERMANENT LOCAL-ONLY LOCK)

1. **THE MANBEARPIG v9.0 APEX-CONVERGENCE** (`local_model/inference_engine.py`) — Primary inference engine. TF-IDF + Naive Bayes + BM25 + semantic embeddings. 50 skills, 140+ JSON-RPC methods, 5-jurisdiction coverage. Zero network. Zero API keys.
2. **LocalAI** (`local_ai_engine.py`) — Pipeline provider. TF-IDF + pattern matching + Naive Bayes. Provides: `classify_document()`, `detect_lane()`, `extract_entities()`, `score_evidence()`, `summarize()`.
3. ~~Ollama/Gemini~~ — **REMOVED**. All remote providers permanently disabled.
4. **Offline heuristic** — Regex/keyword fallback inside LocalAI. Always available.

`LLMGuardian` (`llm_guardian.py`) `_build_provider_chain()` returns empty list. `LLMClient` (`llm_client.py`) only loads `OfflineFallback`. **No remote provider code is reachable.** `get_guaranteed_client()` always returns local engine.

### MANBEARPIG Inference Engine (local_model/)

Entry point: `00_SYSTEM/local_model/inference_engine.py` → `MichiganLegalModel` class.

```powershell
# CLI query
python 00_SYSTEM\local_model\inference_engine.py "MCR 2.003 disqualification"
# JSON-RPC pipe mode (for JS/agent integration)
python 00_SYSTEM\local_model\inference_engine.py --pipe
# Train/retrain model (~60s)
python 00_SYSTEM\local_model\train_model.py
# Self-evolution cycle (v2 is current)
python 00_SYSTEM\local_model\self_evolve_v2.py
python 00_SYSTEM\local_model\self_evolve.py    # legacy
```

**v9.0 JSON-RPC methods (via --pipe):**
- Core: `query`, `find_authority`, `check_citations`, `analyze_document`, `detect_patterns`, `status`, `irac_analysis`, `document_qa`
- Skills: `jtc_complaint`, `adversary_predict`, `adversary_wargame`, `filing_package`, `generate_motion`, `analyze_order`, `score_case`, `cluster_evidence`, `build_narrative`, `build_brief`, `find_authority_graph`, `search_citations`, `build_timeline`, `alienation_analysis`, `forensic_report`, `weaponization_report`, `witness_prep`, `risk_dashboard`
- OMEGA-INFINITY: `startup_diagnostics`, `deadline_urgency`, `filing_optimizer`, `evidence_gaps`, `session_recall`

**Skills** (50 in `local_model/skills/`): Lazy-loaded via SKILL_REGISTRY in `__init__.py`. Each skill connects to `litigation_context.db` and returns structured JSON.

**Session recall** (`session_recall.py`): Cross-session learning — reads past Copilot session history from `~/.copilot/session-state/` for continuity across sessions. Methods: `recent`, `search`, `summary`, `patterns`.

### LEXOS Brain (50 Micro-Brains)

Built by `brain_builder.py`, served by `lexos_server.py` (port 7777). 8 categories: Legal Authority (01-08: MCL/MCR/case citations/USC/CFR/constitutional/benchbook/ethics), Persons (09-17), Issues (18-25), Procedural (26-30), Analysis (31-40: BIF/damages/chronology/credibility), Appellate (41-50). Index: `lexos_bible/lexos_index.json`.

### Desktop App (Electron + React + Node)

**Backend** (`08_APPS/desktop/backend/`): Express + Apollo GraphQL + better-sqlite3 (WAL) + Neo4j (knowledge graph). Redis/Bull queues. WebSocket (Socket.io). Multi-tenant via `tenantContext` middleware. Routes: auth, cases, documents, analysis, motions, evidence, citations, chat, tenants, admin, export, graph, webhooks, subscriptions. Models: User, Case, Document, Evidence, Citation, Motion, Analysis, Conversation, Export, GraphSchema. Services: aiService, ragService, graphReasoningEngine, llmOrchestrator, documentGenService, evidenceService, stripeService, analyticsService + 20 more. Middleware: auth, cache, rateLimiter, performanceMonitor, errorHandler, batchProcessor, apiVersion, tenantContext, queryParser, joiValidation.

**Frontend** (`08_APPS/desktop/frontend/`): React 18 SPA (Vite + Redux Toolkit + Tailwind + Cytoscape graphs). Components organized: ai/, analysis/, common/, documents/, evidence/, export/, graph/, legal/. Single Redux store (`store/store.js`).

**Electron** (`08_APPS/desktop/electron-app/`): main.js + preload.js wrapping the React app. `npm run dev` runs backend + frontend + electron concurrently.

**Web** (`08_APPS/web/`): Next.js 14 (App Router) + TypeScript + Tailwind. Marketing site with Stripe integration.

**Mobile** (`08_APPS/mobile/`): React Native 0.73 + Expo 50 + TypeScript. React Navigation, Redux Toolkit, React Query. Biometric auth, offline mode, push notifications.

### MCP Server

`00_SYSTEM/mcp_server/` — `litigation-context-mcp`. PyMuPDF + Pydantic. Install: `pip install -e 00_SYSTEM/mcp_server/`. Tools: `litigation_scan_drives`, `litigation_ingest_pdf`, `litigation_bulk_ingest`, `litigation_search` (FTS5), `litigation_list_documents`, `litigation_get_document`, `litigation_get_stats`, `litigation_upcoming_deadlines`, `litigation_filing_search`, `litigation_evidence_lookup`.

---

## Build & Run

### MANBEARPIG (Inference Engine)

```powershell
# Startup report (run first every session)
python 00_SYSTEM\local_model\copilot_startup_hook.py --file
# CLI query
python 00_SYSTEM\local_model\inference_engine.py "your legal question"
# JSON-RPC pipe mode
python 00_SYSTEM\local_model\inference_engine.py --pipe
# Train/retrain model
python 00_SYSTEM\local_model\train_model.py
# Session recall
python 00_SYSTEM\local_model\session_recall.py recent
python 00_SYSTEM\local_model\session_recall.py search "filing deadline"
```

### System Launcher

```powershell
.\START.ps1 status     # Health dashboard
.\START.ps1 start      # Full system (DB + Model + Backend + Electron)
.\START.ps1 pipeline   # Run 16-phase pipeline
.\START.ps1 train      # Train/retrain MLLM
.\START.ps1 evolve 10  # Self-evolution cycles
.\START.ps1 analyze    # Forensic + timeline analysis
```

### Pipeline

```powershell
cd C:\Users\andre\LitigationOS\00_SYSTEM\pipeline
python run_omega_pipeline.py                          # Full 16-phase run
python run_omega_pipeline.py --start-phase 4a --end-phase 7c  # Phase range
python run_omega_pipeline.py --skip-phases 16         # Skip specific phases
python run_omega_pipeline.py --dry-run --create-snapshot      # Dry run
python run_omega_pipeline.py --list-phases            # List all phases
python phase3_classify.py                             # Single phase directly
```

### Agent Fleet

```powershell
cd 00_SYSTEM\pipeline
python -m agents.agent_orchestrator                   # Full fleet run
python -m agents.agent_orchestrator --tier J          # Single tier
python -m agents.agent_orchestrator --agent J01       # Single agent
python -m agents.agent_orchestrator --dry-run         # Dry run
```

### Pipeline Validation

```powershell
cd 00_SYSTEM\scripts && python syntax_check.py        # Syntax check all modules
python integration_test_phase123.py                    # Integration test phases 1-3
cd 00_SYSTEM\pipeline && python quick_status.py        # Status check
python validate.py                                     # Full validation
```

### Desktop App

```powershell
# Backend
cd 08_APPS\desktop\backend && npm install && npm run dev
npm test                                               # Vitest
npx vitest run src/path/to/file.test.js                # Single test
npm run db:migrate && npm run db:seed                  # DB setup
npm run graph:setup                                    # Neo4j graph
npm run docs:serve                                     # Swagger docs

# Frontend
cd 08_APPS\desktop\frontend && npm install && npm run dev
npm test                                               # Vitest
npx vitest run src/path/to/file.test.tsx               # Single test
npm run lint && npm run build                          # Lint + build

# Electron (concurrent: backend + frontend + electron)
cd 08_APPS\desktop\electron-app && npm run dev
npm run dist:win                                       # Windows installer

# E2E
cd 08_APPS\desktop\frontend && npx playwright test     # All E2E
npx playwright test tests/path/to/test.spec.ts         # Single E2E

# Full orchestrated build
cd 08_APPS\desktop && .\orchestrator.ps1               # Option 6 = full build
```

### Web (Next.js 14)

```powershell
cd 08_APPS\web && npm install && npm run dev           # Dev :3000
npm run build && npm run lint && npm run type-check
npm test                                               # Vitest
npx vitest run src/path/to/file.test.ts                # Single test
```

### Mobile (React Native + Expo)

```powershell
cd 08_APPS\mobile && npm install && npm start          # Metro bundler
npm run android                                        # Android emulator
npm run ios                                            # iOS simulator
npm run web                                            # Expo web (browser)
npm test                                               # Jest
npx jest path/to/file.test.ts                          # Single test
npm run lint && npm run type-check
```

### MCP Server

```powershell
cd 00_SYSTEM\mcp_server && pip install -e . && litigation-context-mcp
```

---

## Key Conventions

### config.py Is the Single Source of Truth

`00_SYSTEM/pipeline/config.py` centralizes ALL paths, patterns, skip-lists, classification rules, MEEK signals, person-name mappings, pipeline phase registry, bucket priorities, posture tags, and AI model routes. All pipeline phases import from it. Modify config.py — never individual phase files.

### Failsafe-First Design

Every blocking operation wraps in `failsafe.py` primitives:
- `@timeout(seconds, fallback=...)` — kill any function exceeding time limit (threading-based, Windows-safe)
- `@never_crash(fallback=...)` — catch ALL exceptions, return fallback
- `safe_call(fn, timeout_s=30, fallback=None)` — one-shot safe invocation
- `CircuitBreaker(name, threshold=3, cooldown=60)` — stop calling dead services
- `FailsafePhaseRunner` — wrap entire pipeline phases
- `safe_import(module)` — import without hanging or crashing
- All incidents logged to `failsafe_incidents.db` (SQLite) for post-mortem

Config.py itself is failsafe: if `failsafe.py` is missing, inline stubs activate. Import of config.py **NEVER hangs, NEVER crashes**.

### Safety Snapshot (Phase 0 — IRON RULE)

Nothing in LITIGATIONOS_MASTER gets modified until a verified backup exists. `safety.py` creates SHA-256 manifests of all files + copies of `MASTER_MODIFIABLE` files (enumerated in config.py). Snapshot lives in `00_SYSTEM/backups/SNAPSHOT_{timestamp}/`.

### Database Patterns

- **Central DB:** `C:\Users\andre\LitigationOS\litigation_context.db` (10.2 GB, 655 tables, 11.7M rows)
- **Schema safety:** Always check `schema_reference` table before querying unfamiliar tables: `SELECT * FROM schema_reference WHERE table_name = 'X'`
- Key column corrections: `authority_chains.chain_complete` (not `is_complete`), `filing_readiness.vehicle_name` (not `vehicle`), `deadlines.due_date_iso` (not `deadline_date`), `claims.claim_id` (not `id`)
- **Pipeline:** SQLite WAL mode everywhere. `PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL; PRAGMA busy_timeout=120000`. FTS5 for search. One DB per lane in `06_CASE_DATABASES/`. Agent fleet shares `agents/master_index.db`.
- **Desktop backend:** better-sqlite3 (WAL + foreign keys ON). Schema in `models/database.js`. Sequelize for complex ops. Neo4j for knowledge graph.
- **Thread-safe DB:** Agent base class uses thread-local storage (`threading.local()`) — main thread gets `_main_db`, worker threads get per-thread connections.

### Windows-Specific

- Use `long_path()` from config.py to prefix `\\?\` for Windows long-path support on all file operations.
- All drives lazy-detected via `_LazyDrives` proxy — zero cost at import, probes only on first access.
- Known drives: C, D, F, G, H, I (add in `_KNOWN_DRIVE_LETTERS`).
- POSIX signals unavailable — all timeouts use threading.

### Pydantic Contracts

`litigation_contracts.py` defines typed data contracts: `TruthTag`, `ProvenanceRef`, `AuthorityTriple`, `DeadlineItem`, `DocketEvent`, `ContradictionEdge`, `VehicleCandidate`. All structured outputs conform to these. Use `ConfigDict(extra="forbid")` on all models.

### Legal Pattern Matching

Compiled regexes in config.py — use these, don't reinvent:
- `MCL_PATTERN` — Michigan Compiled Laws (`MCL 722.23`)
- `MCR_PATTERN` — Michigan Court Rules (`MCR 2.003`)
- `MRE_PATTERN` — Michigan Rules of Evidence (`MRE 901`)
- `CASE_CITE_PATTERN` — Case citations (`450 Mich App 204`)
- `USC_PATTERN` — Federal statutes (`42 USC §1983`)
- `CANON_PATTERN` — Judicial conduct canons

### Shell Safety (MANDATORY for all Python execution)

- **NEVER** run inline Python via PowerShell `-c` with backslashes or quotes — write to .py file first
- **Every Python script MUST start with:** `sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')`
- **MAX 3 background agents at a time** — prevents EAGAIN pipe buffer overflow (enforced by db_lock_manager.py)
- Pipe large DB query results to files (`> output.txt`), not stdout
- Use `safe_python_exec.py` or `safe_exec.py` for quick runs

### Evidence Posture Tags

Every evidence atom gets a posture: `RECORD_FACT` | `EVIDENCE_FACT` | `SWORN_FACT` | `ALLEGATION` | `INFERENCE`. These control weight in legal analysis.

### Code Style

- **Python** (pipeline/agents): snake_case files and functions. Python 3.10+. Type hints. Pydantic `ConfigDict(extra="forbid")`.
- **React/TypeScript** (frontend/web/mobile): PascalCase components, camelCase functions/vars. Functional components + hooks only.
- **Node.js** (backend): snake_case filenames, camelCase variables/functions. ES modules (`import`/`export`).
- **Commits:** Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`). Branches: `feature/*`, `bugfix/*`, `docs/*`, `refactor/*`.

### Filing Workflow

Court filings move: `04_COURT_FILINGS/01_DRAFTING → 02_REVIEW → 03_FINAL → 04_FILED → 05_SERVED`. Templates in `04_COURT_FILINGS/_TEMPLATES/`.

### Logging

`PipelineLogger` dual-outputs: stderr (human-readable) + JSONL file (machine-readable) in cyclepack dir. Progress via `report_progress()` — emits every 10,000 items + at completion.

---

## Court Filing Production

### Court-Ready Documents (48 files, ~1,600KB)

| Directory | Court | Files |
|-----------|-------|-------|
| `01_14TH_CIRCUIT/` | 14th Judicial Circuit, Muskegon County | 23 |
| `02_COA/` | Michigan Court of Appeals | 4 |
| `03_JTC/` | Judicial Tenure Commission | 3 |
| `04_MSC/` | Michigan Supreme Court | 3 |
| Root | Support docs (indexes, templates, strategy) | 15 |

### Filing Format (MCR 2.113)

- **Caption:** STATE OF MICHIGAN / IN THE [COURT] / COUNTY OF MUSKEGON / parties / case no / judge
- **Format:** 8.5"×11", 1" margins, 12pt Times New Roman, double-spaced, sequential page numbers
- **Components:** Motion + Brief + Proposed Order + Verification + Certificate of Service + Exhibit Index
- **Citations:** Michigan format for state (`Name, Vol Mich App Page (Year)`); Bluebook for federal
- **Parties:** ANDREW J. PIGORS (Plaintiff, Pro Se) v. EMILY A. WATSON (Defendant)
- **Judge:** Hon. Jenny L. McNeill
- **Case Numbers:** 2024-001507-DC (Custody), 2023-5907-PP (PPO), 2025-002760-CZ (Civil)
- **Opposing Counsel:** Jennifer Barnes, P55406, Barnes Law Firm PLLC, 880 Jefferson St Ste B, Muskegon MI 49440
- **FOC:** Pamela Rusco, 990 Terrace St, Muskegon MI 49442
- **`[EMAIL]` placeholders** are intentional — user fills at filing time

### Key Support Files

- `MASTER_FILING_SEQUENCE.md` — 4-phase strategic filing order, 25 filings, $1,740 total
- `MASTER_EXHIBIT_INDEX.md` — 63 exhibits, Bates-numbered PIGORS-0001 through PIGORS-0412
- `FINAL_FILING_INSTRUCTIONS.md` — Step-by-step per court
- `DEADLINE_TRACKER.md` — All statutory deadlines and response windows
- `LITIGATION_STRATEGY_MEMO.md` — **PRIVILEGED** — 19-filing portfolio assessment (not for filing)
- `COMPLETE_DOCUMENT_INVENTORY.md` — Full inventory, 48 documents, ~1,878 pages
- `PROOF_OF_SERVICE_TEMPLATE.md` — MCR 2.104/2.105/2.107 service templates
- `EXHIBIT_AUTHENTICATION_TEMPLATES.md` — MRE 901/902 authentication forms

### SCAO Forms (required with custody filings)

Forms in `05_ANALYSIS/legal_output/04_FORMS/`:
- **FOC 30** (UCCJEA Affidavit) — **REQUIRED** with every custody filing
- **FOC 30A** (UCCJEA Supplement) — multi-state cases
- **FOC 2** (Motion Cover Page) — all Family Division motions
- **FOC 88** (Affidavit/Declaration) — sworn statements
- **MC 229** (Discovery Motion/Affidavit) — discovery enforcement
- **PCM 201** (Protected PII) — all filings with PII

---

## Evidence Intelligence

### Key Statistics

- **Parent-child separation since Aug 8, 2025** — calculate current day count from today's date
- 26,459 extracted harms (6,390 child welfare, 5,222 PPO weaponization, 3,397 housing)
- 308,704 evidence quotes across all sources
- 15,171 impeachment items (7,636 court, 1,883 Judge McNeill)
- 10,672 contradictions (6,600 timeline conflicts, 3,253 inconsistent statements)
- 1,127 judicial violations (377 critical, 243 high)
- 653 claims (429 supported with evidence links)
- 3,684,757 master citations (MCL: 1.3M, MCR: 949K, case law: 559K)
- 28/28 authority chains complete (100% validation)
- 9 of 12 MCL 722.23 best-interest factors favor Father (75%)
- $82,250+ documented financial damages; total claim $200K–$400K

### Critical Evidence Sources

- `05_ANALYSIS/briefs/MEGA_INTELLIGENCE_BRIEF.md` — 82,528 findings (densest source)
- `07_SPECS/strategy/MASTER_STRATEGY_ENHANCED.md` — Top 10 arguments ranked, damage calcs, filing sequence
- `05_ANALYSIS/legal_output/05_LITOS_ENHANCED/pro_edge_evidence_matrix_enhanced.csv` — 27,859 weighted evidence→claim edges
- `05_ANALYSIS/legal_output/07_METRICS/LEGAL_ELEMENTS_INDEX.md` — Element satisfaction per claim (Contempt 84.5%, PPO 85%, UCCJEA 85.4%, Discovery 84.6%)
- `05_ANALYSIS/legal_output/03_DECISION_TREES/` — Filing decision trees with step-by-step procedures

### Scan Roots

Pipeline indexes from `DRIVE_SCAN_ROOTS` in config.py. Primary: `C:\Users\andre\LitigationOS`, `C:\Users\andre\LITIGATIONOS_MASTER`, `C:\Users\andre\scans`. Secondary: D:\, F:\, G:\, H:\, I:\ (full drive scans).

---

## 🚨 Critical Deadlines

| Deadline | Date | Urgency | Lane | Notes |
|----------|------|---------|------|-------|
| **COA 366810 Appellant's Brief** | April 15, 2026 | 🔴 CRITICAL | F | Must file with COA — no extensions likely |
| **Emergency Motions** | ASAP | 🔴 CRITICAL | A/D | File immediately when ready |
| **Motion to Disqualify McNeill** | March 15, 2026 | 🟠 HIGH | E | MCR 2.003 — judicial bias documented |
| **Shady Oaks Housing Complaint** | April 30, 2026 | 🟡 MEDIUM | B | 2025-002760-CZ civil action |
| **Defamation SOL** | ~Feb 2027 | 🟡 YELLOW | A | Statute of limitations watch — monitor |

**Deadline engine:** `deadline_alert_engine.py` tracks all deadlines with escalating alerts at 90/60/30/14/7/3/1 day marks. MCP tool: `litigation_upcoming_deadlines`.

---

## 📂 Filing Stacks (24+ Active Stacks)

The filing production system manages **24+ filing stacks** producing **80+ court-ready PDFs**. Each stack tracks:
- **Readiness score** (0-100%) — computed by `filing_validator_engine.py`
- **MCR compliance** — format, caption, citation, service requirements
- **Exhibit completeness** — Bates-numbered, authenticated, indexed

Stacks span all 6 case lanes and 4 courts (14th Circuit, COA, MSC, JTC). Filing workflow: `01_DRAFTING → 02_REVIEW → 03_FINAL → 04_FILED → 05_SERVED`. Use `litigation_filing_search` MCP tool to query stack status.

---

## 🔧 Delta999 Engine Directory

| Engine | File | Purpose |
|--------|------|---------|
| **LLM Classifier** | `llm_classifier_engine.py` | Ollama auto-classification of documents by type/lane/relevance |
| **Filing Validator** | `filing_validator_engine.py` | MCR compliance checking — format, citation, caption, service rules |
| **Brief Quality** | `brief_quality_engine.py` | Scoring briefs on persuasion, authority, IRAC structure, readability |
| **Opposing Analysis** | `opposing_analysis_engine.py` | Adversary pattern detection — Barnes/Watson tactics, response prediction |
| **Settlement Engine** | `settlement_engine.py` | Case valuation — damages, leverage, risk, settlement range calculation |
| **Doc Assembly** | `doc_assembly_engine.py` | MD → DOCX → PDF pipeline with template injection and Bates stamping |
| **Deadline Alert** | `deadline_alert_engine.py` | Deadline tracking with escalating urgency alerts and calendar sync |
| **DB Lock Manager** | `db_lock_manager.py` v3.0 | EAGAIN prevention — WAL enforcement, busy_timeout, connection pooling |

---

## 🛡️ EAGAIN Prevention Rules (MANDATORY)

SQLite EAGAIN/lock errors have been the #1 system stability issue. These rules are **non-negotiable**:

1. **Max 3 concurrent background agents** — enforced by `db_lock_manager.py` semaphore
2. **Always use `managed_db()` context manager** from `db_lock_manager.py` for ALL database connections:
   ```python
   from db_lock_manager import managed_db
   with managed_db("litigation_context.db") as conn:
       conn.execute("SELECT ...")
   ```
3. **PRAGMA busy_timeout=60000** on every new connection (60 seconds wait before SQLITE_BUSY)
4. **PRAGMA journal_mode=WAL** mandatory on every database (already set in pipeline, enforce in scripts)
5. **Never run >3 DB-heavy operations simultaneously** — queue them via orchestrator
6. **Connection pooling** — reuse connections within an agent's lifecycle, don't open/close per query
7. **Write serialization** — only one writer per database at a time; reads can be concurrent under WAL

Violation of these rules will produce `EAGAIN`, `SQLITE_BUSY`, or `database is locked` errors that cascade across the agent fleet.

---

## 🧰 Skills & Tools Registry

### Skill Registry (50 skills)

The `local_model/skills/` directory contains **50 registered skills** (up from 14 in v11, 30 in v12). All lazy-loaded via `SKILL_REGISTRY` in `__init__.py`. Each skill connects to `litigation_context.db` and returns structured JSON. Skills cover: legal analysis, evidence scoring, filing production, judicial profiling, adversary prediction, timeline construction, authority graphing, IRAC analysis, forensic reporting, witness preparation, risk dashboards, alienation analysis, and more.

### Awesome-Copilot Skills (17 installed)

17 skills from the awesome-copilot ecosystem are installed and available:
- Code generation, refactoring, documentation, testing, debugging
- SQL query building, API design, security review
- Legal-domain-specific skills for Michigan family law

### Hooks (2 active)

| Hook | Purpose |
|------|---------|
| `governance-audit` | Logs all agent actions for compliance and audit trail |
| `session-logger` | Captures Copilot session events for cross-session learning |

### CLI Tools Available

| Tool | Purpose |
|------|---------|
| `pandoc` | Document conversion (MD → DOCX → PDF, HTML → MD, etc.) |
| `fd` | Fast file finder (rust-based, replaces `find`) |
| `rg` | ripgrep — fast content search (rust-based, replaces `grep`) |
| `jq` | JSON processor for pipeline data manipulation |

### MCP Tools (Extended)

| Tool | Purpose |
|------|---------|
| `litigation_upcoming_deadlines` | Query deadline tracker with urgency scores |
| `litigation_filing_search` | Search filing stacks by lane, court, status, readiness |
| `litigation_evidence_lookup` | Look up evidence atoms by Bates number, source, or claim |
| `litigation_scan_drives` | Scan configured drives for new evidence files |
| `litigation_ingest_pdf` | Ingest and classify a single PDF |
| `litigation_bulk_ingest` | Batch ingest with dedup and lane assignment |
| `litigation_search` | FTS5 full-text search across all indexed documents |
| `litigation_list_documents` | List documents with filters (lane, type, date) |
| `litigation_get_document` | Retrieve document metadata and content |
| `litigation_get_stats` | System-wide statistics dashboard |

---

## 🤖 Copilot Agent Directory (31 agents in `.copilot/agents/`)

| # | Agent | Description |
|---|-------|-------------|
| 1 | `appellate-brief-writer` | Drafts COA/MSC appellate briefs with proper authority and IRAC structure |
| 2 | `authority-chain-validator` | Validates citation chains — MCL→MCR→case law completeness |
| 3 | `bates-stamp-manager` | Assigns and tracks Bates numbers (PIGORS-0001+) across exhibits |
| 4 | `brief-quality-scorer` | Scores briefs on persuasion, authority depth, readability (0-100) |
| 5 | `case-timeline-builder` | Constructs chronological timelines from evidence atoms |
| 6 | `citation-format-checker` | Validates Michigan/Bluebook citation format compliance |
| 7 | `claim-evidence-linker` | Links evidence atoms to legal claims with weight scoring |
| 8 | `court-filing-assembler` | Assembles complete filing packages (motion+brief+order+exhibits) |
| 9 | `court-rule-lookup` | MCR/MCL/MRE quick lookup with context and annotations |
| 10 | `damages-calculator` | Computes financial damages from documented harm events |
| 11 | `deadline-tracker` | Monitors and alerts on upcoming court deadlines |
| 12 | `deposition-prep` | Prepares deposition outlines with impeachment material |
| 13 | `discovery-request-drafter` | Drafts interrogatories, RFPs, and RFAs per MCR 2.309-2.312 |
| 14 | `docket-analyzer` | Parses and analyzes court docket entries for patterns |
| 15 | `evidence-gap-finder` | Identifies missing evidence for each legal element |
| 16 | `exhibit-index-builder` | Builds formatted exhibit indexes for court filings |
| 17 | `filing-readiness-auditor` | Audits filing stacks for completeness and MCR compliance |
| 18 | `impeachment-finder` | Locates contradictions and impeachment material in testimony |
| 19 | `irac-analyzer` | Structures legal arguments in Issue-Rule-Application-Conclusion format |
| 20 | `judicial-bias-detector` | Detects patterns of judicial bias from orders and transcripts |
| 21 | `lane-classifier` | Classifies documents into correct case lanes (A-F) |
| 22 | `legal-research-assistant` | Researches Michigan family law issues with authority support |
| 23 | `motion-drafter` | Drafts motions with proper caption, body, and prayer for relief |
| 24 | `narrative-builder` | Constructs persuasive factual narratives from evidence |
| 25 | `opposing-counsel-profiler` | Profiles opposing counsel tactics and predicts responses |
| 26 | `order-analyzer` | Analyzes court orders for errors, bias, and appeal issues |
| 27 | `ppo-specialist` | Handles PPO-specific filings and weaponization analysis |
| 28 | `pro-se-advisor` | Provides pro se procedural guidance for Michigan courts |
| 29 | `risk-assessor` | Evaluates litigation risk per claim and recommends strategy |
| 30 | `settlement-evaluator` | Evaluates settlement offers against case valuation model |
| 31 | `witness-prep-coach` | Prepares witness examination outlines with key questions |

---

## 🏗️ Superpower Agents (13 cross-cutting)

| # | Agent | Role |
|---|-------|------|
| 1 | `fleet-orchestrator` | Coordinates all 112 agents — scheduling, priority, conflict resolution |
| 2 | `self-evolution-controller` | Manages MANBEARPIG self-evolution cycles |
| 3 | `governance-auditor` | Compliance logging and audit trail for all agent actions |
| 4 | `session-continuity` | Cross-session memory and learning via session_recall.py |
| 5 | `db-health-monitor` | Monitors litigation_context.db integrity, WAL checkpointing, size |
| 6 | `pipeline-scheduler` | Schedules 16-phase pipeline runs with dependency resolution |
| 7 | `evidence-ingestion-coordinator` | Coordinates multi-drive evidence scanning and dedup |
| 8 | `filing-production-manager` | Manages 24+ filing stacks through review → final → filed workflow |
| 9 | `quality-gate-enforcer` | Enforces quality thresholds before filings reach COURT_READY |
| 10 | `backup-integrity-checker` | Verifies SHA-256 manifests and backup completeness |
| 11 | `conflict-resolver` | Detects and resolves lane cross-contamination and data conflicts |
| 12 | `metric-dashboard-generator` | Produces system health and case progress dashboards |
| 13 | `emergency-motion-accelerator` | Fast-tracks emergency filings with abbreviated review |
