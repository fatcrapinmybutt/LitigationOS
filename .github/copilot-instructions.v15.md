# LitigationOS — Copilot Instructions (v15.0 APEX-CONVERGENCE)

## 🚨 NON-NEGOTIABLE RULES (read before ANYTHING else)

### EAGAIN Prevention (violation = system crash)
- **HARD LIMIT: Max 3 concurrent background agents** — no exceptions, no "just one more"
- Before spawning ANY sub-agent, count currently running agents. If 3 are running, WAIT.
- Every DB connection MUST use: `PRAGMA busy_timeout=60000; PRAGMA journal_mode=WAL; PRAGMA cache_size=-32000`
- Use `managed_db()` from `db_lock_manager.py` for ALL database access
- If you see `EAGAIN`, `SQLITE_BUSY`, or `database is locked` — STOP spawning agents, wait for current ones to finish

### User Preferences (non-negotiable)
- **NO HARD DELETIONS** — move files to `I:\` or Recycle Bin. Never `rm`, never `del`, never `os.remove()` on litigation files.
- **CONTENT-BASED DEDUP** — do NOT rely solely on file hashing. Open and compare actual document content (peek inside). Andrew explicitly said "no hashing — peek at the document to ensure they are the same."
- **ALL DUPLICATES → I:\ drive** — never delete duplicates. Move them to a dedup folder on `I:\`.
- **Save progress CONSTANTLY** — checkpoint to SQL todos + filesystem every 10 minutes or every 3 agent completions during autonomous runs. GOAWAY 503 errors kill agents after 27-40 minutes. If you don't checkpoint, work is LOST.

### Prior Work Discovery (BEFORE creating any document)
- **ALWAYS search before creating.** Before generating any filing, motion, brief, or document from scratch, search ALL drives for existing versions first:
  ```powershell
  fd --type f "motion" C:\Users\andre\LitigationOS\ I:\ F:\ G:\
  rg -l "disqualification" C:\Users\andre\LitigationOS\ --type md --type txt --type docx
  ```
- Use existing drafts as starting points. Build on prior work — don't recreate from zero.
- If prior versions exist, diff them, merge the best content, then improve. The user was frustrated when the agent rebuilt filing stacks from scratch that already existed on other drives.

### Autonomous Execution Protocol
- During long autonomous runs, write incremental progress reports to `00_SYSTEM\PROGRESS_LOG.md` after every agent completion.
- Update SQL `todos` table status after every subtask (not just at the end).
- If a run will take >20 minutes, break it into independent checkpoint-able waves of 3 agents max.
- On GOAWAY/503/timeout: current work is lost for that agent. The checkpoint file is the only recovery point.

### Mega-Task Decomposition (prevents context overflow crashes)
- If a user request contains **>3 independent deliverables** (e.g., 12 filing packages), **STOP**.
- Decompose into sequential waves of **max 3 deliverables** each.
- Present the wave plan and get user confirmation before executing.
- 75% of past sessions crashed because the agent tried to process massive requests in one shot.

### Python Execution Safety (violation = SyntaxError cascade)
- **NEVER** run inline Python via PowerShell `python -c "..."` — backslashes, quotes, and f-strings WILL break.
- **ALWAYS** write Python to a temp `.py` file, execute it, then clean up.
- Every Python script MUST set UTF-8 stdout: `sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')`
- Use `safe_python_exec.py` or `safe_exec.py` for quick runs.

### DB Schema Verification (prevents column-name crashes)
- Before querying any table for the first time in a session, run `PRAGMA table_info(table_name)` to verify columns.
- **Never assume column names from this file** — the DB schema evolves faster than these instructions.
- Known corrections: `authority_chains.chain_complete` (not `is_complete`), `filing_readiness.vehicle_name` (not `vehicle`), `deadlines.due_date_iso` (not `deadline_date`)

---

## ⚡ AGENT ORCHESTRATION MODE — FULL FLEET ENABLED

**Sub-agents and parallel execution are ENABLED and ENCOURAGED.**

1. **USE** the `task` tool to spawn sub-agents (explore, task, general-purpose, code-review, custom agents) for parallel work.
2. **USE** background mode for independent tasks that can run simultaneously.
3. **PRIORITIZE** efficiency: parallelize reads, audits, and independent operations.
4. **SELF-HEAL**: On error, retry with backoff. On crash, checkpoint and resume. On complexity, decompose and delegate.
5. **NEVER** lose data — move to Recycle Bin, never hard-delete. Backup before destructive ops.
6. **ALWAYS** log actions to the session SQL database for traceability.
7. The canonical system location is `C:\Users\andre\LitigationOS` — all paths resolve here.
8. The central database is `C:\Users\andre\LitigationOS\litigation_context.db` — pipeline writes, apps read. **Do not hardcode DB stats** — run startup hook or query DB for current counts.
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

LitigationOS is a litigation intelligence system for Michigan family law (Pigors v. Watson). It has three integrated subsystems: a **16-phase Python data pipeline** with a **155+ agent fleet** (Delta9 + Delta999 + Copilot + Superpower + Convergence agents), a **local-first AI engine** (zero-network), and an **Electron+React+Node desktop app** with web and mobile frontends. All data stays local on Windows. The pipeline processes ~3.3GB of evidence across 6+ drives into court-ready filings. The system currently manages **45+ filing stacks** producing **80+ court-ready PDFs** with readiness scores. Phase 5-6 engines are hardened with full error recovery, input validation, and graceful degradation.

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

**Total Fleet: 122 agents**
| Fleet | Count | Role |
|-------|-------|------|
| Delta9 (A01-L08) | 56 | Core pipeline agents (I/O, intelligence, convergence) |
| Delta999 | 12 | Advanced engines (classifier, validator, brief, opposing, settlement, assembly, deadline, db_lock) |
| Copilot agents (.copilot/agents/) | 31 | Specialized Copilot sub-agents (see directory below) |
| Superpower agents | 13 | Cross-cutting orchestration, governance, self-evolution |
| Convergence agents (Agent-152) | 10 | Phase 5-6 hardening, filing workflow, complaint prep, MCP v2 |

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

### MCP Server v2

`00_SYSTEM/mcp_server/` -- `litigation-context-mcp` v2. PyMuPDF + Pydantic. Install: `pip install -e 00_SYSTEM/mcp_server/`. **45 tools** across 9 categories:

**Core Tools (10):** `litigation_scan_drives`, `litigation_ingest_pdf`, `litigation_bulk_ingest`, `litigation_search` (FTS5), `litigation_list_documents`, `litigation_get_document`, `litigation_get_stats`, `litigation_upcoming_deadlines`, `litigation_filing_search`, `litigation_evidence_lookup`.

**Filing Tools (8):** `litigation_filing_readiness`, `litigation_filing_validate`, `litigation_filing_assemble`, `litigation_efiling_prep`, `litigation_brief_compliance`, `litigation_placeholder_scan`, `litigation_placeholder_resolve`, `litigation_filing_export`.

**Evidence Tools (7):** `litigation_evidence_chain`, `litigation_evidence_gaps`, `litigation_evidence_link`, `litigation_evidence_authenticate`, `litigation_bates_assign`, `litigation_exhibit_index`, `litigation_evidence_timeline`.

**Deadline Tools (5):** `litigation_deadline_dashboard`, `litigation_deadline_ics`, `litigation_deadline_urgency`, `litigation_deadline_add`, `litigation_deadline_update`.

**Analysis Tools (5):** `litigation_authority_index`, `litigation_citation_graph`, `litigation_impeachment_search`, `litigation_contradiction_find`, `litigation_judicial_bias_scan`.

**QA Tools (4):** `litigation_prefiling_qa`, `litigation_qa_sweep`, `litigation_signature_check`, `litigation_service_check`.

**Backup Tools (3):** `litigation_backup_create`, `litigation_backup_version`, `litigation_backup_report`.

**Calendar Tools (2):** `litigation_calendar_generate`, `litigation_calendar_sync`.

**System Tools (1):** `litigation_system_health`.

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

- **Central DB:** `C:\Users\andre\LitigationOS\litigation_context.db` (query `PRAGMA page_count` × `PRAGMA page_size` for current size)
- **Schema safety:** See **DB Schema Verification** in NON-NEGOTIABLE rules above. Also check `schema_reference` table: `SELECT * FROM schema_reference WHERE table_name = 'X'`
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

### Shell Safety
- See **Python Execution Safety** in NON-NEGOTIABLE rules above.
- **MAX 3 background agents at a time** — prevents EAGAIN pipe buffer overflow.
- Pipe large DB query results to files (`> output.txt`), not stdout.

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

- **Run `python 00_SYSTEM\local_model\copilot_startup_hook.py --file` for current counts.** Never cite statistics from this file — they go stale.
- **Parent-child separation since Aug 8, 2025** — calculate current day count from today's date.

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

## Reference Catalogs

Detailed reference material (agent directories, engine commands, tool registries, complaint workflows) is in `00_SYSTEM/REFERENCE_CATALOG.md`. Consult that file when you need specific agent names, engine commands, or tool lists.

---

*Version: v16.0 CHRONICLE-IMPROVED | Slimmed from 695 to ~350 lines | Reference catalogs extracted | Session-history-driven improvements*