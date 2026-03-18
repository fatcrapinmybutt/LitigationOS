# LitigationOS — Copilot Instructions (v18.0 CONVERGENCE)

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

### Verified Party Identity (NEVER fabricate names, bar numbers, or evidence)
Past sessions fabricated "Jane Berry", "Patricia Berry (SBN P35878)", "9 CPS investigations", and "91% alienation score" — none of which existed. These hallucinations appeared in 60+ files and could constitute perjury if filed in sworn documents. **The following table is the ONLY source of truth for party identity:**

| Role | Name | Details |
|------|------|---------|
| **Plaintiff** | Andrew James Pigors | 1977 Whitehall Road, Lot 17, North Muskegon, MI 49445 · (231) 903-5690 · andrewjpigors@gmail.com |
| **Defendant** | Emily A. Watson | 2160 Garland Drive, Norton Shores, MI 49441 (NOT "Emily Ann", NOT "Emily M.", NOT "Tiffany") |
| **Child** | L.D.W. | Use initials ONLY per MCR 8.119(H) — NEVER full name in filings |
| **Judge** | Hon. Jenny L. McNeill | 14th Circuit Court, Family Division (NOT "Amy McNeill") |
| **Emily's Attorney** | Jennifer Barnes (P55406) | Barnes Law Firm PLLC, 880 Jefferson St Ste B, Muskegon, MI 49440 — **WITHDREW** |
| **FOC** | Pamela Rusco | 990 Terrace St, Muskegon, MI 49442 |
| **Ronald Berry** | NON-ATTORNEY | Emily's boyfriend/domestic partner. No bar number. No "Esq." Never was Emily's attorney. |

**Hard rules:**
- **NEVER invent a party name.** If you don't know the name, insert `[UNKNOWN — VERIFY]` — never guess.
- **NEVER invent a bar number.** If you don't have it, query `litigation_context.db` or leave blank.
- **NEVER fabricate evidence statistics** (e.g., "9 CPS investigations"). If a stat isn't in the DB, don't cite it.
- **"Jane Berry" and "Patricia Berry" NEVER EXISTED.** Any occurrence is a hallucination to be purged.

### DB-First Before Any Placeholder (violation = user frustration)
The DB has hundreds of tables and millions of rows of real data. Past sessions left hundreds of `[ANDREW_REQUIRED]` placeholders in filings when the data was available in `litigation_context.db` the entire time. The user explicitly said: *"thats the whole point of this. to USE MY FILES ON MY DRIVES. come on man."*

**Before inserting ANY placeholder (`[ANDREW_REQUIRED]`, `[INSERT]`, `[ATTACH]`):**
1. Query `litigation_context.db` for the data (try: `docket_events`, `evidence_quotes`, `claims`, `deadlines`, `documents`, `judicial_violations`)
2. Search the filesystem (`rg`, `fd`, `grep`) across all 6 drives for existing content
3. Check `COMPLETE_FILING_DATA_SUMMARY.txt` and `QUICK_REFERENCE_FILING_PLACEHOLDERS.txt` in repo root
4. **Only if ALL three return nothing** → insert a placeholder with specific instructions on where to find the data

### Traceable Statistics (no inflated numbers — applies to ALL generated content)
Past sessions generated inflated or fabricated aggregate statistics that were embedded in sworn filings. The "91% alienation score" was pseudo-scientific. Duplicate counting inflated evidence counts.

**Rules (apply to filings, dashboards, analyses, summaries, and all generated documents):**
- Every statistic cited in ANY generated document MUST be traceable to a specific DB query (table + WHERE clause)
- Before citing a count (e.g., "305 interference incidents"), run `SELECT COUNT(*) FROM [table] WHERE [condition]` and note the query
- Never round up, extrapolate, or generate synthetic scores (e.g., "91% alienation") — use documented incident counts instead
- When aggregating across tables, check for and exclude duplicates before reporting totals
- Dashboard summaries and progress reports are NOT exempt — inflated progress numbers mislead the user just as much as inflated filing numbers

### Prior Work Discovery (BEFORE creating any document)
- **ALWAYS search before creating.** Before generating any filing, motion, brief, or document from scratch, search ALL drives for existing versions first:
  ```powershell
  fd --type f "motion" C:\Users\andre\LitigationOS\ I:\ F:\ G:\
  rg -l "disqualification" C:\Users\andre\LitigationOS\ --type md --type txt --type docx
  ```
- Use existing drafts as starting points. Build on prior work — don't recreate from zero.
- If prior versions exist, diff them, merge the best content, then improve.

### Mega-Task Decomposition (prevents context overflow crashes)
- If a user request contains **>3 independent deliverables** (e.g., 12 filing packages), **STOP**.
- Decompose into sequential waves of **max 3 deliverables** each.
- Present the wave plan and get user confirmation before executing.
- 75% of past sessions crashed because the agent tried to process massive requests in one shot.

### Python Execution Safety (violation = SyntaxError cascade)
- **NEVER** run inline Python via PowerShell `python -c "..."` — backslashes, quotes, and f-strings WILL break.
- **ALWAYS** write Python to a temp `.py` file, execute it, then clean up.
- Every Python script MUST set UTF-8 stdout: `sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')`
- **USE THE TOOLKIT**: `python 00_SYSTEM/tools/safe_shell.py check|run|env-check|shadow-audit`
- For inline Python: use `spy "print(1+1)"` after dot-sourcing agent_profile.ps1

### Shell Session Management (violation = "Invalid shell ID" cascade)
- **ZERO-SHELL DEFAULT: Use `task` agents for ALL command execution (builds, tests, scripts, git).** Task agents get isolated pipes — if one crashes, main session survives. This is the ONLY proven EAGAIN prevention that works. 4 sessions, 8+ user complaints about EAGAIN — verbose rules don't help; behavioral default does.
- **PREFER COMMAND-RUNNER MCP** over the `powershell` tool for the rare cases you need a shell.
  - `exec_command(command)` — any shell command (unlimited, zero session pool cost)
  - `exec_python(script_path, args)` — Python scripts with shadow-module safety
  - `exec_git(args)` — git operations with --no-pager
  - `exec_pipeline_phase(phase)` — pipeline phases (noreply_pdfs, backup, ocr_evidence, autonomous, etc.)
  - `system_status()` — system health without shell
- **FALLBACK ONLY**: Use `powershell` tool for interactive/async needs (max 50 per session).
- **HARD LIMIT: Max 3 concurrent async shells** — sessions are finite OS resources
- **Chain related commands** with `&&` in one shell instead of creating separate shells
- **Always `stop_powershell`** completed async shells immediately after reading output
- **Use named shellIds** (`"build"`, `"test"`) — never rely on auto-generated IDs
- **Pre-flight cleanup**: Run `list_powershell` → stop all stale sessions → BEFORE any multi-step operation
- **Recovery**: If "Invalid shell ID" appears on a fresh shell → stop ALL sessions → wait 5s → retry
- Root cause: 20+ accumulated sessions exhaust the runtime's session pool. MCP is the permanent fix.

### DB Schema Verification (prevents column-name crashes)
- Before querying any table for the first time in a session, run `PRAGMA table_info(table_name)` to verify columns.
- **Never assume column names from this file** — the DB schema evolves faster than these instructions.
- Known corrections: `authority_chains.chain_complete` (not `is_complete`), `filing_readiness.vehicle_name` (not `vehicle`), `deadlines.due_date_iso` (not `deadline_date`), `claims.claim_id` (not `id`)
- Also check `schema_reference` table: `SELECT * FROM schema_reference WHERE table_name = 'X'`

### Retrieve Agent Results IMMEDIATELY (violation = lost work)
- **On EVERY `system_notification` of agent completion → call `read_agent` IMMEDIATELY in your next response.** Do not defer, do not batch, do not "get to it later."
- Context compaction can clear agent results at any time. If you don't read them before compaction, ALL work done by that agent is gone and must be re-run.
- Past sessions lost an entire 12-packet placeholder fill because agent-60 results were never retrieved.

### Autonomous Execution Protocol
- During long autonomous runs, write incremental progress reports to `00_SYSTEM\PROGRESS_LOG.md` after every agent completion.
- Update SQL `todos` table status after every subtask (not just at the end).
- If a run will take >20 minutes, break it into independent checkpoint-able waves of 3 agents max.
- On GOAWAY/503/timeout: current work is lost for that agent. The checkpoint file is the only recovery point.

---

## ⚡ AGENT ORCHESTRATION MODE — FULL FLEET ENABLED

1. **USE** the `task` tool to spawn sub-agents (explore, task, general-purpose, code-review, custom agents) for parallel work.
2. **USE** background mode for independent tasks that can run simultaneously.
3. **PRIORITIZE** efficiency: parallelize reads, audits, and independent operations.
4. **SELF-HEAL**: On error, retry with backoff. On crash, checkpoint and resume. On complexity, decompose and delegate.
5. **NEVER** lose data — move to Recycle Bin, never hard-delete. Backup before destructive ops.
6. **ALWAYS** log actions to the session SQL database for traceability.
7. The canonical system location is `C:\Users\andre\LitigationOS` — all paths resolve here.
8. The central database is `C:\Users\andre\LitigationOS\litigation_context.db` — pipeline writes, apps read. **Do not hardcode DB stats** — run startup hook or query DB for current counts.

## 🐻 MANBEARPIG Startup Protocol — MANDATORY ON EVERY SESSION

> **🚨 NON-NEGOTIABLE: Execute this protocol as your VERY FIRST ACTION in every new session.**
> Do NOT respond to the user's first message until this protocol completes.
> Do NOT skip steps. Do NOT defer to "later." Run it NOW.

**Step 1 — Generate startup report:**
```powershell
python C:\Users\andre\LitigationOS\00_SYSTEM\local_model\copilot_startup_hook.py --file
```

**Step 2 — Read the report (use `view` tool on this file):**
```
C:\Users\andre\LitigationOS\00_SYSTEM\STARTUP_REPORT.md
```

**Step 3 — Recall past sessions:**
```powershell
python C:\Users\andre\LitigationOS\00_SYSTEM\local_model\session_recall.py recent
```

**Step 4 — Load jurisdiction databases (if they exist):**
```powershell
python -c "import sqlite3,os,glob; dbs=glob.glob(r'C:\Users\andre\LitigationOS\databases\*.db'); print(f'{len(dbs)} jurisdiction DBs found:'); [print(f'  {os.path.basename(d)}: {os.path.getsize(d)//1024}KB') for d in dbs]"
```

**Step 5 — Report readiness to user:**
After completing steps 1-4, report: DB status, separation day count, deadline urgency, evidence arsenal size, and jurisdiction DB availability.

The startup hook generates `STARTUP_REPORT.md` with: separation day count, deadline urgency scores, filing readiness, evidence arsenal counts, system health, and recent Copilot session summaries.

### Startup Database Chain
On every session start, verify these databases are accessible:
- `litigation_context.db` — Central 12GB litigation database (790+ tables)
- `court_forms.db` — Michigan SCAO court form intelligence (39 forms)
- `databases/*.db` — Jurisdiction-specific databases (10 specialized DBs)
- Session SQL — Per-session tracking (todos, evidence, progress)

---

## System Identity

LitigationOS is a litigation intelligence system for Michigan family law (Pigors v. Watson). It has three integrated subsystems: a **16-phase Python data pipeline** with a **155+ agent fleet** (Delta9 + Delta999 + 64 Copilot + Superpower + Convergence agents), a **local-first AI engine** (zero-network), and a **pip-installable desktop app** with CustomTkinter GUI. All data stays local on Windows. The pipeline processes evidence across 6+ drives into court-ready filings. Central DB: `litigation_context.db` — run `python 00_SYSTEM\local_model\copilot_startup_hook.py --file` for current table count, size, and row counts. **Never hardcode DB statistics — they change constantly.**

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
  → Court-ready filings
```

### Event Horizon Factory (closed-loop)

Forms + rules + evidence → instruction atoms → requirements graph → AKN templates → filing stacks → lint → satisfaction → graph export → CyclePack. **PASS gates define done.** Fix failures in order: OCR → instructions → requirements → stacks → lint → satisfaction → export.

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

### Agent Fleet (155+)

All agents inherit `Agent9999` from `agents/agent_base.py`. Two parallel lanes converge:

- **Lane 1 (I/O):** Tiers 1-3 — A01-A12 (indexing, dedup, extraction)
- **Lane 2 (Intelligence):** Tiers J/K/L — J01-L08 (judicial profiling, case intel, legal analysis)
- **Convergence:** F01-F06 (filing assembly, brain feed, graph build, certification)

| Fleet | Count | Role |
|-------|-------|------|
| Delta9 (A01-L08) | 56 | Core pipeline agents (I/O, intelligence, convergence) |
| Delta999 | 12 | Advanced engines (classifier, validator, brief, opposing, settlement, assembly, deadline, db_lock) |
| Copilot agents (.copilot/agents/) | 64 | Specialized Copilot sub-agents (see directory below) |
| Superpower agents | 13 | Cross-cutting orchestration, governance, self-evolution |
| Convergence agents | 10 | Phase 5-6 hardening, filing workflow, complaint prep, MCP v2 |

Agent contract: `run() → AgentResult(agent_id, status, stats)`. Status: SUCCESS | FATAL | CRASH.
Agent data: `agents/master_index.db` (SQLite WAL mode). Schema: `files`, `ready_queue`, `dedup_clusters`, `zip_contents`, `atoms`, `judicial_findings`, `action_scores`, `agent_log`.

### 7-Layer Error Protocol (every agent, non-negotiable)

1. Try operation → 2. Specific catch → targeted recovery → 3. Broad catch → log + skip + continue → 4. Checkpoint every N items → crash-resume → 5. Deadman switch (120s no progress → self-diagnose) → 6. Agent retry (3× exponential backoff) → 7. Tier fallback → orchestrator flags + continues

### AI Provider Stack (PERMANENT LOCAL-ONLY LOCK)

1. **THE MANBEARPIG v9.0** (`local_model/inference_engine.py`) — Primary inference engine. TF-IDF + Naive Bayes + BM25 + semantic embeddings. 50 skills, 140+ JSON-RPC methods. Zero network. Zero API keys.
2. **LocalAI** (`local_ai_engine.py`) — Pipeline provider. TF-IDF + pattern matching + Naive Bayes. Provides: `classify_document()`, `detect_lane()`, `extract_entities()`, `score_evidence()`, `summarize()`.
3. ~~Ollama/Gemini~~ — **REMOVED**. All remote providers permanently disabled.
4. **Offline heuristic** — Regex/keyword fallback inside LocalAI. Always available.

`LLMGuardian` (`llm_guardian.py`) `_build_provider_chain()` returns empty list. `LLMClient` (`llm_client.py`) only loads `OfflineFallback`. **No remote provider code is reachable.**

### Product App (`11_CODE/litigationos/`)

Pip-installable Python package (Python ≥3.12). CustomTkinter GUI with 14 screens. 9 engines, 9 Pydantic models. SQLite via `DatabaseManager` from `litigationos.db.connection`. CLI entry: `litigationos` (via typer). Jurisdiction plugins (Michigan).

### MCP Server v2

`00_SYSTEM/mcp_server/` — `litigation-context-mcp` v2+. PyMuPDF + Pydantic. Install: `pip install -e 00_SYSTEM/mcp_server/`. Tools across 9 categories (run `litigation_system_health` for current tool count):

| Category | Count | Tools |
|----------|-------|-------|
| Core | 10 | scan_drives, ingest_pdf, bulk_ingest, search (FTS5), list_documents, get_document, get_stats, upcoming_deadlines, filing_search, evidence_lookup |
| Filing | 8 | filing_readiness, filing_validate, filing_assemble, efiling_prep, brief_compliance, placeholder_scan, placeholder_resolve, filing_export |
| Evidence | 7 | evidence_chain, evidence_gaps, evidence_link, evidence_authenticate, bates_assign, exhibit_index, evidence_timeline |
| Deadline | 5 | deadline_dashboard, deadline_ics, deadline_urgency, deadline_add, deadline_update |
| Analysis | 5 | authority_index, citation_graph, impeachment_search, contradiction_find, judicial_bias_scan |
| QA | 4 | prefiling_qa, qa_sweep, signature_check, service_check |
| Backup | 3 | backup_create, backup_version, backup_report |
| Calendar | 2 | calendar_generate, calendar_sync |
| System | 1 | system_health |

All tools are prefixed with `litigation_` (e.g., `litigation_deadline_dashboard`).

---

## Build, Test, & Run

### Product App (pytest)

```powershell
cd 11_CODE\litigationos
pip install -e ".[dev]"                                # Install with test deps
python -m pytest tests/ -q                             # All tests (run for current count)
python -m pytest tests/test_brief_compliance.py -v     # Single test file
python -m pytest tests/test_models.py::test_case -v    # Single test function
python -m pytest tests/ --cov=litigationos             # With coverage
```

### MANBEARPIG (Inference Engine)

```powershell
python 00_SYSTEM\local_model\inference_engine.py "MCR 2.003 disqualification"  # CLI query
python 00_SYSTEM\local_model\inference_engine.py --pipe   # JSON-RPC pipe mode
python 00_SYSTEM\local_model\train_model.py               # Train/retrain model (~60s)
python 00_SYSTEM\local_model\self_evolve_v2.py            # Self-evolution cycle
python 00_SYSTEM\local_model\session_recall.py recent     # Session recall
python 00_SYSTEM\local_model\session_recall.py search "filing deadline"
```

### Pipeline

```powershell
cd 00_SYSTEM\pipeline
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

### Event Horizon Tooling

```powershell
python tooling/doctor_all.py --vault Vault --db litigation_context.db   # Health + coverage check
python tooling/pass_gate_check.py --vault Vault --case-id <id>          # PASS gate aggregation
```

### Phase 5-6 Engines (Hardened v2.0)

```powershell
python 00_SYSTEM\engines\court_calendar_engine.py           # Deadline dashboard + ICS export
python 00_SYSTEM\engines\evidence_chain_engine.py           # Chain of custody + gap analysis
python 00_SYSTEM\engines\authority_index_engine.py          # Citation graph + authority database
python 00_SYSTEM\engines\placeholder_resolver_v2.py         # Auto-fill placeholders from DB
python 00_SYSTEM\engines\brief_compliance_engine.py [path]  # MCR 7.212 validation
python 00_SYSTEM\engines\prefiling_qa_engine.py             # GO/NO-GO sweep across all stacks
python 00_SYSTEM\engines\efiling_prep_engine.py             # TrueFiling/MiFILE/PACER packet assembly
python 00_SYSTEM\engines\backup_version_engine.py           # Snapshot + version tracking
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

- **Central DB:** `C:\Users\andre\LitigationOS\litigation_context.db` — run `SELECT (page_count * page_size) / (1024*1024*1024.0) as size_gb FROM pragma_page_count(), pragma_page_size()` for current size. Never hardcode table counts or DB size.
- **Schema safety:** See **DB Schema Verification** in NON-NEGOTIABLE rules above. Also check `schema_reference` table.
- **Pipeline:** SQLite WAL mode everywhere. `PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL; PRAGMA busy_timeout=120000`. FTS5 for search. One DB per lane in `06_CASE_DATABASES/`. Agent fleet shares `agents/master_index.db`.
- **Product app:** `DatabaseManager` from `litigationos.db.connection` — SQLite WAL + foreign keys ON.
- **Thread-safe DB:** Agent base class uses thread-local storage (`threading.local()`) — main thread gets `_main_db`, worker threads get per-thread connections.

### EAGAIN Prevention (detailed)

```python
from db_lock_manager import managed_db
with managed_db("litigation_context.db") as conn:
    conn.execute("SELECT ...")
```
- Connection pooling — reuse connections within an agent's lifecycle, don't open/close per query
- Write serialization — only one writer per database at a time; reads can be concurrent under WAL
- Pre-flight check before spawning agents: count running agents via `list_agents()`. If >= 3, WAIT.

### Windows-Specific

- Use `long_path()` from config.py to prefix `\\?\` for Windows long-path support on all file operations.
- All drives lazy-detected via `_LazyDrives` proxy — zero cost at import, probes only on first access.
- Known drives: C, D, F, G, H, I (add in `_KNOWN_DRIVE_LETTERS`).
- POSIX signals unavailable — all timeouts use threading.

### Pydantic Contracts

`litigation_contracts.py` defines typed data contracts: `TruthTag`, `ProvenanceRef`, `AuthorityTriple`, `DeadlineItem`, `DocketEvent`, `ContradictionEdge`, `VehicleCandidate`. All structured outputs conform to these. Use `ConfigDict(extra="forbid")` on all models. Product models in `11_CODE/litigationos/src/litigationos/models/`.

### Legal Pattern Matching

Compiled regexes in config.py — use these, don't reinvent:
- `MCL_PATTERN` — Michigan Compiled Laws (`MCL 722.23`)
- `MCR_PATTERN` — Michigan Court Rules (`MCR 2.003`)
- `MRE_PATTERN` — Michigan Rules of Evidence (`MRE 901`)
- `CASE_CITE_PATTERN` — Case citations (`450 Mich App 204`)
- `USC_PATTERN` — Federal statutes (`42 USC §1983`)
- `CANON_PATTERN` — Judicial conduct canons

### Evidence Posture Tags

Every evidence atom gets a posture: `RECORD_FACT` | `EVIDENCE_FACT` | `SWORN_FACT` | `ALLEGATION` | `INFERENCE`. These control weight in legal analysis.

### Code Style

- **Python** (pipeline/agents/product): snake_case files and functions. Python 3.12+. Type hints. Pydantic `ConfigDict(extra="forbid")`.
- **Commits:** Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`). Branches: `feature/*`, `bugfix/*`, `docs/*`, `refactor/*`.

### Logging

`PipelineLogger` dual-outputs: stderr (human-readable) + JSONL file (machine-readable) in cyclepack dir. Progress via `report_progress()` — emits every 10,000 items + at completion.

### Engine Error Recovery Protocol

Each Phase 5-6 engine follows this recovery pattern:
1. **Input validation** — reject None, empty strings, invalid types at entry points
2. **DB availability check** — if `litigation_context.db` is missing, return sensible defaults
3. **Operation-level try/except** — each DB query, file read, and file write is individually wrapped
4. **Logging** — all errors via `logger.error()`, warnings via `logger.warning()`
5. **Graceful return** — on failure, return error dict/string instead of crashing
6. **Safe import** — no side effects at module level; all work happens in `run()` or explicit method calls

### Scoped Instructions

Additional conventions for specific directories are in `.github/instructions/`:
- `tooling.instructions.md` — CLI tools must support `--help`, return non-zero on failure, write JSON to `Vault/90_REPORTS/` with sha256 receipts.
- `services.instructions.md` — Endpoints fail closed, no path traversal, job triggers enqueue to DB, never expose verbatim court-form text.
- `docs.instructions.md` — Append-only docs, every subsystem documents purpose/inputs/outputs/failure modes. Reference PASS gates.

---

## Court Filing Production

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

### Filing Workflow

Court filings are organized in `01_FILINGS/` by case type (TRIAL_14TH, COA_366810, MSC_ACTION, JTC_MCNEILL, FEDERAL_1983, BAR_BARNES, EMERGENCY, ADMIN). Within each, filings progress through drafting → review → final → filed → served stages.

### SCAO Forms (required with custody filings)

- **FOC 30** (UCCJEA Affidavit) — **REQUIRED** with every custody filing
- **FOC 30A** (UCCJEA Supplement) — multi-state cases
- **FOC 2** (Motion Cover Page) — all Family Division motions
- **FOC 88** (Affidavit/Declaration) — sworn statements
- **MC 229** (Discovery Motion/Affidavit) — discovery enforcement
- **PCM 201** (Protected PII) — all filings with PII

### Key Support Files

- `MASTER_FILING_SEQUENCE.md` — 4-phase strategic filing order
- `MASTER_EXHIBIT_INDEX.md` — 63 exhibits, Bates-numbered PIGORS-0001 through PIGORS-0412
- `FINAL_FILING_INSTRUCTIONS.md` — Step-by-step per court
- `DEADLINE_TRACKER.md` — All statutory deadlines and response windows
- `LITIGATION_STRATEGY_MEMO.md` — **PRIVILEGED** — portfolio assessment (not for filing)
- `PROOF_OF_SERVICE_TEMPLATE.md` — MCR 2.104/2.105/2.107 service templates
- `EXHIBIT_AUTHENTICATION_TEMPLATES.md` — MRE 901/902 authentication forms

### Complaint Filing (9 Agency Types)

| # | Agency | Filing Method | Key Statute |
|---|--------|---------------|-------------|
| 1 | **14th Circuit Court** | MiFILE e-filing | MCR 2.113 |
| 2 | **Michigan Court of Appeals** | TrueFiling | MCR 7.212 |
| 3 | **Michigan Supreme Court** | TrueFiling | MCR 7.305 |
| 4 | **Judicial Tenure Commission** | Mail/Hand delivery | MCR 9.240 |
| 5 | **WDMI Federal Court** | PACER/CM/ECF | 42 USC 1983 |
| 6 | **HUD** | Online complaint | Fair Housing Act |
| 7 | **LARA** | Online/Mail | MCL 125.1501+ |
| 8 | **Attorney Grievance Commission** | Written complaint | MCR 9.104 |
| 9 | **DHHS/CPS** | Phone/Online | MCL 722.623 |

### Filing Production Pipeline

```
1. Draft complaint (motion-drafter agent or manual)
2. Run brief_compliance_engine.py (MCR validation)
3. Run prefiling_qa_engine.py (GO/NO-GO check)
4. Run placeholder_resolver_v2.py (auto-fill known values)
5. Run efiling_prep_engine.py (packet assembly)
6. Review EFILING_CHECKLIST.md in packet directory
7. Convert MD → PDF via pandoc or doc_assembly_engine.py
8. Upload to appropriate e-filing system
9. File proof of service
```

---

## Evidence Intelligence

### Key Statistics

- **Run `python 00_SYSTEM\local_model\copilot_startup_hook.py --file` for current counts.** Never cite stale statistics — always query the DB.
- **Parent-child separation since Aug 8, 2025** — calculate current day count dynamically from today's date.

### Critical Evidence Sources

- `05_ANALYSIS/briefs/MEGA_INTELLIGENCE_BRIEF.md` — densest findings source
- `07_SPECS/strategy/MASTER_STRATEGY_ENHANCED.md` — Top arguments ranked, damage calcs, filing sequence
- `05_ANALYSIS/legal_output/05_LITOS_ENHANCED/pro_edge_evidence_matrix_enhanced.csv` — weighted evidence→claim edges
- `05_ANALYSIS/legal_output/07_METRICS/LEGAL_ELEMENTS_INDEX.md` — Element satisfaction per claim
- `05_ANALYSIS/legal_output/03_DECISION_TREES/` — Filing decision trees with step-by-step procedures

### Scan Roots

Pipeline indexes from `DRIVE_SCAN_ROOTS` in config.py. Primary: `C:\Users\andre\LitigationOS`, `C:\Users\andre\LITIGATIONOS_MASTER`, `C:\Users\andre\scans`. Secondary: D:\, F:\, G:\, H:\, I:\ (full drive scans).

### Active Working Directories (Multi-Root Workspace)

All drives below are mounted in the VS Code workspace and available for agent file operations, evidence searches, and dedup sweeps.

| Drive | Path | Purpose | Free |
|-------|------|---------|------|
| **C:** | `C:\Users\andre\LitigationOS` | Canonical home — DB, pipeline, agents, filings | Monitor |
| **D:** | `D:\` | Curated evidence sets, extracted packs, golden files | 15.6 GB |
| **F:** | `F:\` | Evidence archives, scanned documents, zips | 20.1 GB |
| **G:** | `G:\` | Supplemental evidence, exports, backups | 20.8 GB |
| **H:** | `H:\` | Recycle / staging area, overflow storage | 10.7 GB |
| **I:** | `I:\` | Dedup destination (ALL duplicates go here), GGUF models, large archives | ⚠️ 2.9 GB |

**Rules:**
- Agents MAY read/search ALL drives without permission.
- Agents MAY write to `I:\` (dedup) and `H:\` (staging) without permission.
- Agents MUST ask before writing to `D:\`, `F:\`, `G:\` (curated evidence).
- When searching for evidence or prior work, scan ALL 6 drives, not just C:.

---

## 🚨 Critical Deadlines

Run startup hook for current deadlines with countdowns. Key deadlines managed by `deadline_alert_engine.py` with escalating alerts at 90/60/30/14/7/3/1 day marks. MCP tool: `litigation_upcoming_deadlines`.

---

## Reference Catalogs

For full inventories of engines, agents, modules, and directory structure, see **`docs/REFERENCE_CATALOG.md`**. Key sections available there:
- Delta999 Engine Directory (8 engines)
- MANBEARPIG JSON-RPC Methods (50 skills)
- CLI Tools Available
- Copilot Agent Directory (64 agents — litigation-specific + general-purpose)
- Superpower Agents (13 cross-cutting)
- Engine Inventory (79 engines in 7 categories)
- MANBEARPIG Inference Engine (66 modules)
- Directory Structure and Filing Structure
- Convergence Workflow, QA Verdict Levels, Urgency Levels
- Docs Directory

---

*Version: v19.1 CHRONICLE | Evolved from v18.0 — zero-shell-default EAGAIN prevention, reference catalogs moved to docs/REFERENCE_CATALOG.md (~380 lines saved), all hardcoded statistics replaced with runtime queries, agent-result retrieval promoted to NON-NEGOTIABLE, traceable-statistics rule extended to all outputs | See docs/REFERENCE_CATALOG.md for full inventories*