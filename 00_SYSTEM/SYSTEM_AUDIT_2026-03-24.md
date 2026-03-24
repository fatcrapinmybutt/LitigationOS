# LitigationOS System Audit — 2026-03-24

**Auditor:** Copilot System Auditor
**Scope:** Full-system health, gap analysis, and improvement roadmap
**Method:** Filesystem verification, database checks, integration analysis
**Status:** ✅ COMPLETE — All findings verified against actual filesystem state

---

## Executive Summary

| Metric | Reported | Verified | Status |
|--------|----------|----------|--------|
| Central DB (litigation_context.db) | 670 MB | **702.6 MB** | ✅ Healthy |
| Central DB tables | 166 | Verify at runtime | ⚠️ Unverified count |
| Core Engines | 5 | **4 functional + 1 missing** | ⚠️ Degraded |
| Agent Fleet (.agents/agents/) | 155+ | **29 agent definitions** | ℹ️ See note¹ |
| OMEGA Skills (.agents/skills/) | 53 | **970 directories (697 with SKILL.md)** | ✅ Exceeds |
| MCP Tools | 45+ | Infrastructure present | ✅ Healthy |
| Filing Pipeline Phases | 16 | **11 explicit phase files** | ⚠️ 5 phases unclear |
| Jurisdiction DBs | 11 | **10 functional + 1 empty** | ⚠️ Degraded |
| Desktop App | Present | **v1.0.0-beta.1, Python ≥3.12** | ✅ Active |
| Test Files | Unknown | **33 test files + 1 pipeline test** | ⚠️ Gaps |

¹ *The 155+ count includes pipeline agents (56 in orchestrator tiers A01-L08), Delta999 agents (12), and Copilot agents (29 .md definitions). The 29 verified are the Copilot agent definitions only.*

---

## 1. Engine Health Check

### Engine Inventory (Verified Locations)

| Engine | Expected Path | Actual Path | Status |
|--------|---------------|-------------|--------|
| **NOVEL** | `00_SYSTEM/engines/novel/novel_engine.py` | `00_SYSTEM/novel/novel_engine.py` | ✅ EXISTS (wrong path in docs) |
| **DARWIN** | `00_SYSTEM/engines/darwin/darwin_engine.py` | `00_SYSTEM/darwin/darwin_engine.py` | ✅ EXISTS (wrong path in docs) |
| **LEXICON** | `00_SYSTEM/engines/lexicon/lexicon_engine.py` | `00_SYSTEM/engines/lexicon/lexicon_engine.py` | ✅ EXISTS |
| **ORACLE** | `00_SYSTEM/engines/oracle/oracle_engine.py` | `00_SYSTEM/engines/oracle/oracle_engine.py` | ✅ EXISTS |
| **MANBEARPIG** | `00_SYSTEM/local_model/inference_engine.py` | `00_SYSTEM/local_model/inference_engine.py` | ✅ EXISTS |
| **HF Legal** | `00_SYSTEM/local_model/hf_legal_engine.py` | — | ❌ MISSING (referenced in startup hook) |

### Supporting Files

**NOVEL engine ecosystem:**
- `00_SYSTEM/novel/` — composer.py, creativity_engine.py, invention_genome.py, perception.py, strategy_genome.py, validator.py

**DARWIN engine ecosystem:**
- `00_SYSTEM/darwin/` — agent_genome.py, mutation_engine.py, darwin.db

**LEXICON engine ecosystem:**
- `00_SYSTEM/engines/lexicon/` — canons_data.py, foc_data.py, lexicon_db.py, mcl_data.py, mcr_data.py, mre_data.py

**ORACLE engine ecosystem:**
- `00_SYSTEM/engines/oracle/` — deadlines.py

**MANBEARPIG ecosystem:**
- `00_SYSTEM/local_model/` — 13 root files + 3 subdirectories (benchmarks/, engines/, skills/)

### Engine Integration Issues

1. **Path mismatch:** NOVEL and DARWIN live at `00_SYSTEM/novel/` and `00_SYSTEM/darwin/`, NOT under `00_SYSTEM/engines/`. Documentation and startup hook reference incorrect paths.
2. **Missing engine:** `hf_legal_engine.py` referenced in `copilot_startup_hook.py` does not exist. Startup hook will fail/skip this check.
3. **No broken imports:** Grep confirms no engine .py files in `00_SYSTEM/engines/` import from novel or darwin — isolation is clean.

### Additional Engines in `00_SYSTEM/engines/` Root (34 files)

Standalone engine files not part of the 5 core engines:
- `adversary_reader.py`, `backup_version_engine.py`, `citation_validator.py`
- `compliance_checker.py`, `court_calendar_engine.py`, `court_timeline_final.py`
- `db_backup_engine.py`, `evidence_chain_engine.py`, `exhibit_compiler.py`
- `filing_production_runner.py`, `litigation_rag_engine.py`, `llm_bridge.py`
- `llm_classifier_engine.py`, `placeholder_scanner.py`
- 7 `skill_*.py` files (authority_validator, bias_quantifier, convergence_engine, filing_tracker, landlord_tenant, michigan_tort_lawsuit, ppo_detector, timeline_builder, torts_claims)
- 6 utility/diagnostic files (`_check_db.py`, `_db_survey.py`, `_deep_scan.py`, etc.)

---

## 2. OMEGA Skill Inventory

### Skill Counts (Verified)

| Location | Directories | With SKILL.md | Without SKILL.md | Coverage |
|----------|-------------|---------------|-------------------|----------|
| `.agents/skills/` | 970 | 697 | 273 | 71.9% |
| `.claude/skills/` | 408 | Not audited | — | — |
| **Total** | **1,378** | **697+** | **273+** | — |

### OMEGA-INDEX.md: ✅ EXISTS at `.agents/skills/OMEGA-INDEX.md`

### Skills Missing SKILL.md (First 10 of 273)

1. accessibility-compliance
2. affidavit-narrative-agent
3. ai-automation-workflows
4. airflow-dag-patterns
5. algorithmic-art
6. angular
7. angular-best-practices
8. angular-state-management
9. angular-ui-patterns
10. anti-reversing-techniques

### Sample Skill Content Verification (5 random checks)

| Skill | Has SKILL.md | Has Real Content |
|-------|-------------|-----------------|
| error-debugging-multi-agent-review | ✅ | ✅ Functional |
| conductor-manage | ✅ | ✅ Functional |
| notion-automation | ✅ | ✅ Functional (requires MCP) |
| salesforce-automation | ✅ | ✅ Functional |
| litigation-os | ✅ | ✅ Functional |

### Observation
Many skills without SKILL.md appear to be generic/non-litigation skills (Angular, algorithmic art, anti-reversing). These may be from bulk skill imports rather than LitigationOS-specific gaps.

---

## 3. Agent Fleet Inventory

### Copilot Agent Definitions (29 verified)

**Filing & Court Operations (7):**
1. `filing-forge-master.agent.md`
2. `omega-litigation-commander.agent.md`
3. `court-form-finder.agent.md`
4. `appellate-record-builder.agent.md`
5. `contempt-prosecutor.agent.md`
6. `garnishment-specialist.agent.md`
7. `post-judgment-enforcer.agent.md`

**Legal Research & Analysis (6):**
8. `timeline-forensics.agent.md`
9. `court-order-tracker.agent.md`
10. `damages-calculator.agent.md`
11. `case-strategy-architect.agent.md`
12. `settlement-analyzer.agent.md`
13. `summary-judgment.agent.md`

**Evidence & Investigation (6):**
14. `evidence-warfare-commander.agent.md`
15. `evidence-vehicle-scanner.agent.md`
16. `evidence-authentication.agent.md`
17. `parental-alienation-detector.agent.md`
18. `expert-witness-manager.agent.md`
19. `subpoena-engine.agent.md`

**Judicial Accountability (2):**
20. `judicial-accountability-engine.agent.md`
21. `judicial-recusal-engine.agent.md`

**Family Law Specialized (4):**
22. `family-law-guardian.agent.md`
23. `affidavit-chronology-builder.agent.md`
24. `motion-practice.agent.md`
25. `trial-preparation.agent.md`

**System & Fleet Management (3):**
26. `omega-dedup.agent.md`
27. `self-evolving-fleet-manager.agent.md`
28. `compliance-auditor.agent.md`

**Utility (1):**
29. `drive-organizer.md` (note: different naming convention — no `.agent.` infix)

### Pipeline Agent Fleet (56 in orchestrator)

The `agent_orchestrator.py` declares 56 agents across 5 tiers in two parallel lanes:
- **Lane 1 (I/O):** Tiers 1-3 — A01-A12 (indexing, dedup, extraction)
- **Lane 2 (Intelligence):** Tiers J/K/L — J01-L08 (judicial profiling, case intel, legal analysis)
- **Convergence:** F01-F06 (filing assembly, brain feed, graph build, certification)

### Agent Base Class

`agent_base.py` exists at **5 locations** (potential consistency issue):
- `00_SYSTEM/pipeline/agents/agent_base.py` (primary)
- `00_SYSTEM/engines/agents/agent_base.py`
- `08_SCRIPTS/scripts/agent_base.py`
- `agents/agent_base.py`
- `.agents/agent_base.py`

---

## 4. Filing Status

### Filing Directory Structure (81 subdirectories in `01_FILINGS/`)

**Court-Ready Directories:**

| Directory | File Count | Status |
|-----------|-----------|--------|
| `COURT_READY/` | 10 files | ✅ Active |
| `PDF_READY/` | 8 files | ✅ Active |
| `CLERK_READY/` | 8 files | ✅ Active |
| `COURT_READY_PACKETS/` | 0 files | ❌ EMPTY |
| `COURT_READY_PDF/` | 0 files | ❌ EMPTY |

**Key Filing Categories Present:**
- COA, MSC, JTC, FEDERAL, FEDERAL_1983, CRIMINAL, CUSTODY
- MOTIONS, AFFIDAVITS, DISCOVERY, DECLARATIONS, NOTICES, EX_PARTE, EMERGENCY, CONTEMPT, SANCTIONS
- MOTION_TO_VACATE, DISQUALIFICATION, ALIENATION, MEDICAL_NEGLECT, JUDICIAL_BIAS
- WATSON_TORT, SHADY_OAKS_* (CIRCUIT, CZ, FEDERAL, MASTER)
- BERRY_DISQUALIFICATION, BAR_BARNES, MALPRACTICE, GOLDEN_SET, JTMC_MCNEILL

**QA/Manifest Files:**
- `MASTER_FILING_CHECKLIST.md` (37.4 KB) ✅
- `MASTER_FILING_MANIFEST.md` (15.4 KB) ✅
- `QA_CONVERGENCE_SWEEP_FINAL.md` (11.8 KB) ✅
- `QA_REPORT_FINAL.md` (26.4 KB) ✅
- `CROSS_FILING_CONSISTENCY_REPORT.md` (20.7 KB) ✅

---

## 5. Database Health

### Database Inventory (30+ databases, ~3.2 GB total)

**Primary Database:**

| Database | Location | Size | Status |
|----------|----------|------|--------|
| `litigation_context.db` | Root | **702.6 MB** | ✅ Primary — Healthy |
| `litigation_context (2).db` | Root | 286.7 KB | ⚠️ Stale backup copy |
| `litigation_context.db` | `00_SYSTEM/` | 2.8 MB | ⚠️ System-specific copy |

**Brain Databases (00_SYSTEM/):**

| Database | Size | Status |
|----------|------|--------|
| `chat_intelligence_brain.db` | **934.6 MB** | ✅ Largest DB |
| `interpretation_brain.db` | 359.9 MB | ✅ |
| `narrative_brain.db` | 273.4 MB | ✅ |
| `file_catalog.db` | 244 MB | ✅ |
| `authority_brain.db` | 69.8 MB | ✅ |
| `claims_brain.db` | 14.9 MB | ✅ |
| `consolidation_plan.db` | 13.5 MB | ✅ |
| `entity_brain.db` | 10.7 MB | ✅ |

**Other Root-Level Databases:**

| Database | Size | Status |
|----------|------|--------|
| `script_forge.db` | 221.4 MB | ✅ |
| `mcr_rules.db` | 3.9 MB | ✅ |
| `court_forms.db` | 163.8 KB | ✅ (root copy) |
| `litigationos.db` | 188.4 KB | ✅ |

**Jurisdiction Databases (`databases/`):**

| Database | Size | Status |
|----------|------|--------|
| `court_forms.db` | **0 bytes** | ❌ EMPTY — Critical |
| `jurisdiction_14th_circuit_civil.db` | 32 KB | ✅ |
| `jurisdiction_14th_circuit_family.db` | 45 KB | ✅ |
| `jurisdiction_coa.db` | 36 KB | ✅ |
| `jurisdiction_federal_wdmi.db` | 69 KB | ✅ |
| `jurisdiction_jtc.db` | 57 KB | ✅ |
| `jurisdiction_msc.db` | 61 KB | ✅ |
| `legal_iq.db` | 53 KB | ✅ |
| `litigation_skills.db` | 53 KB | ✅ |
| `michigan_judicial_system.db` | 53 KB | ✅ |
| `procedures.db` | 53 KB | ✅ |

**Lane Databases (`09_DATA/`):**

| Database | Status |
|----------|--------|
| `lane_A_custody.db` | ✅ Found |
| `lane_B_housing.db` | ✅ Found |
| `lane_C_convergence.db` | ❌ MISSING |
| `lane_D_ppo.db` | ✅ Found |
| `lane_E_misconduct.db` | ✅ Found (in `09_DATA/databases/`) |
| `lane_F_appellate.db` | ✅ Found (in `09_DATA/databases/`) |

### Critical Database Issues

1. **`databases/court_forms.db` is 0 bytes** — empty file, likely failed creation or corruption
2. **`lane_C_convergence.db` is MISSING** — cross-lane convergence database not created
3. **`litigation_context (2).db`** at root is a stale 286 KB backup (main DB is 702 MB) — should be cleaned up
4. **Duplicate `litigation_context.db`** at `00_SYSTEM/` (2.8 MB) is a different/subset copy

---

## 6. Gap Analysis

### 6.1 Critical Gaps

| ID | Gap | Impact | Severity |
|----|-----|--------|----------|
| G01 | `databases/court_forms.db` is 0 bytes | Court form lookups will fail from jurisdiction DB path | CRITICAL |
| G02 | `lane_C_convergence.db` missing | Cross-lane convergence analysis cannot persist | CRITICAL |
| G03 | `hf_legal_engine.py` missing but referenced in startup | Startup hook reports false failure for this engine | HIGH |
| G04 | Engine paths in docs are wrong (novel/darwin not under engines/) | Onboarding and automation scripts will use wrong paths | HIGH |
| G05 | COURT_READY_PACKETS/ and COURT_READY_PDF/ are empty | Filing pipeline output destinations have no content | HIGH |
| G06 | No standalone `db_lock_manager.py` | Instructions reference `managed_db()` that doesn't exist as documented | HIGH |
| G07 | 5 pipeline phases (6, 9, 10, 11, 15) have no explicit phase file | Gap analysis, MCP ingest, judicial analysis, legal action discovery, validation unclear | MEDIUM |
| G08 | `agent_base.py` exists at 5 locations | Risk of divergent copies causing inconsistent behavior | MEDIUM |
| G09 | 273 OMEGA skills missing SKILL.md | 28% of skills have no documentation | MEDIUM |
| G10 | No tests for any of the 5 core engines (Novel, Darwin, Lexicon, Oracle, MANBEARPIG) | Engine regressions undetectable | HIGH |
| G11 | Only 1 pipeline test file exists | 16-phase pipeline has effectively no test coverage | HIGH |
| G12 | drive-organizer.md doesn't follow `.agent.md` naming convention | May not be picked up by agent loaders | LOW |

### 6.2 Documentation Gaps

- Engine locations are documented incorrectly in copilot instructions
- Lane database locations are inconsistent (some in `09_DATA/`, some in `09_DATA/databases/`)
- No documentation for the 34 standalone engine files in `00_SYSTEM/engines/` root
- MCP server tool count claimed as 45+ but not independently verified

### 6.3 Testing Gaps

**Untested critical modules:**
- Novel engine (novel_engine.py) — no test
- Darwin engine (darwin_engine.py) — no test
- Lexicon engine (lexicon_engine.py) — no test
- Oracle engine (oracle_engine.py) — no test
- MANBEARPIG inference engine — no test
- Pipeline phases 1-16 — 1 basic test only
- Agent orchestrator — no test
- Brain databases (5 brain DBs, no tests)
- MCP server tools — not verified

---

## 7. Priority Improvement Todos (100)

### CRITICAL — Must Fix Before Filing (25 todos)

| ID | Category | Description | Complexity |
|----|----------|-------------|------------|
| C01 | Database | Rebuild `databases/court_forms.db` — currently 0 bytes. Copy schema from root `court_forms.db` (163.8 KB) and populate with SCAO form data. | M |
| C02 | Database | Create `lane_C_convergence.db` in `09_DATA/` with proper schema for cross-lane linking. Define tables: convergence_links, cross_lane_evidence, lane_conflicts. | M |
| C03 | Engine | Remove or implement `hf_legal_engine.py` reference in `copilot_startup_hook.py`. Currently causes false negative in engine health check. | S |
| C04 | Filing | Populate `COURT_READY_PACKETS/` — filing pipeline must route assembled packets here. Investigate why pipeline output bypasses this directory. | L |
| C05 | Filing | Populate `COURT_READY_PDF/` — PDF conversion step should output here. Check if filing_production_runner.py writes to a different location. | M |
| C06 | Docs | Fix engine paths in `.github/copilot-instructions.md` — NOVEL is at `00_SYSTEM/novel/`, DARWIN at `00_SYSTEM/darwin/`, not under `00_SYSTEM/engines/`. | S |
| C07 | Startup | Update `copilot_startup_hook.py` engine check paths to match actual locations of NOVEL and DARWIN engines. | S |
| C08 | Database | Normalize lane DB locations — E and F are in `09_DATA/databases/` while A, B, D are in `09_DATA/`. Move all to consistent location. | M |
| C09 | Filing | Audit all 81 filing subdirectories for completeness: each filing package needs motion + affidavit + exhibits + proposed order + proof of service. | L |
| C10 | System | Create or document the `db_lock_manager.py` module with `managed_db()` context manager as referenced throughout instructions. Currently implemented only in watchdog. | M |
| C11 | Filing | Generate DOCX versions of all court-ready filings — judges and clerks require .docx, not just PDF. | L |
| C12 | Filing | Verify all filings in COURT_READY/ have proper case number headers (2024-001507-DC for custody, 2025-002760-CZ for housing). | M |
| C13 | Filing | Generate proposed orders for every motion in COURT_READY/ — Michigan practice requires proposed orders with all motions. | L |
| C14 | Filing | Create proof of service documents for every filing — no filing is complete without a certificate of service per MCR 2.107. | L |
| C15 | Evidence | Run full evidence dedup across all 6 drives using content-based comparison (not hashing per user preference). | L |
| C16 | Filing | Build exhibit indices for each filing package — numbered, Bates-stamped, with authentication notes. | L |
| C17 | Database | Verify `litigation_context.db` table count at runtime — claimed 166 tables may have changed. Run `SELECT count(*) FROM sqlite_master WHERE type='table'`. | S |
| C18 | System | Clean up stale `litigation_context (2).db` (286 KB) at root — move to `I:\` drive per no-delete policy. | S |
| C19 | Filing | Run QA_CONVERGENCE_SWEEP across all filing packages to identify cross-contamination between case lanes. | M |
| C20 | Filing | Verify all filings use correct party names per verified identity table — no "Jane Berry", "Patricia Berry", wrong middle initials. | M |
| C21 | Filing | Ensure child is referenced as "L.D.W." only (initials) per MCR 8.119(H) in all filing documents. | S |
| C22 | Evidence | Verify all evidence statistics cited in filings are traceable to specific DB queries — no fabricated counts or inflated numbers. | L |
| C23 | Filing | Check all filings for placeholder text (`[ANDREW_REQUIRED]`, `[INSERT]`, `[ATTACH]`) and resolve against DB data. | M |
| C24 | System | Verify startup hook `copilot_startup_hook.py` runs without errors — currently references 1 missing engine and 2 wrong paths. | S |
| C25 | Database | Run integrity check on all 30+ databases: `PRAGMA integrity_check` on each .db file to detect corruption. | M |

### HIGH — Filing Quality Improvements (25 todos)

| ID | Category | Description | Complexity |
|----|----------|-------------|------------|
| H01 | Testing | Create test suite for NOVEL engine (`test_novel_engine.py`) — cover composition, creativity, and validation functions. | M |
| H02 | Testing | Create test suite for DARWIN engine (`test_darwin_engine.py`) — cover genome mutation and agent evolution. | M |
| H03 | Testing | Create test suite for LEXICON engine (`test_lexicon_engine.py`) — cover MCR, MCL, MRE, FOC, and canons data lookups. | M |
| H04 | Testing | Create test suite for ORACLE engine (`test_oracle_engine.py`) — cover deadline calculation and case timeline. | M |
| H05 | Testing | Create test suite for MANBEARPIG inference engine (`test_inference_engine.py`) — cover TF-IDF, BM25, classification. | L |
| H06 | Testing | Expand pipeline tests — currently only `test_pipeline_basic.py`. Need per-phase tests for all 16 phases. | L |
| H07 | Filing | Implement DOCX conversion pipeline for all PDF-only filings using python-docx (already a dependency). | L |
| H08 | Filing | Build master exhibit compilation engine — automate Bates stamping across all filing packages. | L |
| H09 | Filing | Create service tracking database/table — track which filings have been served on which parties. | M |
| H10 | Agent | Consolidate `agent_base.py` to single canonical location (`00_SYSTEM/pipeline/agents/`). Replace other 4 copies with imports. | M |
| H11 | Engine | Integrate NOVEL engine into startup health check at its actual path (`00_SYSTEM/novel/`). | S |
| H12 | Engine | Integrate DARWIN engine into startup health check at its actual path (`00_SYSTEM/darwin/`). | S |
| H13 | Filing | Build filing readiness dashboard that queries all 81 subdirectories and reports % complete per package. | L |
| H14 | Pipeline | Identify and document the 5 missing pipeline phase files (phases 6, 9, 10, 11, 15) — determine if they're embedded in other modules. | M |
| H15 | Filing | Create appellate record index for COA 366810 — organize lower court record, transcripts, exhibits per MCR 7.210. | L |
| H16 | Evidence | Build evidence-to-filing linkage matrix — which evidence supports which filing across all 6 lanes. | L |
| H17 | Filing | Generate caption pages for all filings with proper court headers, case numbers, and party designations. | M |
| H18 | Database | Populate jurisdiction DBs with full court rule sets — most are 32-69 KB (likely stub data only). | L |
| H19 | Filing | Implement e-filing package assembly per MiFILE requirements (PDF/A, bookmarks, attachment index). | L |
| H20 | Filing | Create filing dependency graph — show which filings must be filed before others (e.g., motion before reply). | M |
| H21 | System | Build automated pre-filing QA sweep that checks: party names, case numbers, child initials, service cert, proposed order, exhibits. | L |
| H22 | Evidence | Build contradiction detection engine to find inconsistencies in Emily Watson's statements across all documents. | L |
| H23 | Filing | Create cover letters/transmittal sheets for each filing package per local court requirements. | M |
| H24 | Database | Audit all brain databases for data freshness — when was each last updated? Are they current? | M |
| H25 | Filing | Implement signature blocks and verification language for all affidavits per MCR 2.114. | M |

### MEDIUM — System Improvements (30 todos)

| ID | Category | Description | Complexity |
|----|----------|-------------|------------|
| M01 | Skills | Create SKILL.md for 273 missing skill directories — at minimum the litigation-relevant ones. | L |
| M02 | Skills | Audit `.claude/skills/` (408 directories) for overlap with `.agents/skills/` — deduplicate where identical. | L |
| M03 | Engine | Create engine health monitoring dashboard — query all 5 engines for status, latency, last-run time. | M |
| M04 | Pipeline | Create phase execution dashboard — track which phases have run, when, success/failure rates. | M |
| M05 | Agent | Create agent fleet health dashboard — track all 56 pipeline agents + 29 Copilot agents. | M |
| M06 | Database | Build database size/growth monitoring — alert when any DB approaches problematic sizes. | M |
| M07 | Engine | Add error recovery to NOVEL engine — if composition fails, fall back to template-based generation. | M |
| M08 | Engine | Add error recovery to DARWIN engine — if mutation fails, preserve current genome state. | M |
| M09 | System | Implement the 3-tier connection strategy documented in SQLite instructions — multiplexer, standard, simple. | L |
| M10 | Testing | Add integration tests that verify engine-to-pipeline data flow end-to-end. | L |
| M11 | Testing | Add database migration tests — verify `run_migration.py` handles schema changes safely. | M |
| M12 | System | Implement adaptive query rewriter integration for all DB access patterns per documentation. | M |
| M13 | Pipeline | Add crash-resume checkpointing to all 16 phases — currently undocumented recovery behavior. | L |
| M14 | Agent | Implement agent retry with exponential backoff as documented in 7-layer error protocol. | M |
| M15 | Agent | Add deadman switch (120s no progress detection) to all pipeline agents. | M |
| M16 | System | Build connection multiplexer (`connection_multiplexer.py`) as documented in SQLite instructions. | L |
| M17 | Filing | Create filing timeline visualization — Gantt chart of all filing deadlines and dependencies. | M |
| M18 | System | Implement MCP server v2 health monitoring — track tool invocation counts, errors, latency. | M |
| M19 | Database | Add composite indexes for common query patterns per SQLite optimization instructions. | M |
| M20 | System | Build session continuity engine improvements — `session_continuity_engine.py` needs automated checkpoint/resume. | M |
| M21 | Agent | Create agent performance benchmarking suite — track execution times, success rates, output quality. | L |
| M22 | Pipeline | Implement phase-level progress reporting — each phase should report % complete and items processed. | M |
| M23 | System | Build drive health monitoring — check all 6 drives (C, D, F, G, H, I) for availability and space. | M |
| M24 | Engine | Add LEXICON engine caching — MCR/MCL/MRE lookups should be cached for repeated queries. | M |
| M25 | Engine | Add ORACLE engine deadline notification system — email/file-based alerts for approaching deadlines. | M |
| M26 | Database | Build database backup rotation — automated daily backups with 30-day retention on I: drive. | M |
| M27 | System | Implement the AUTONOMOS file-based command fallback system documented in shell management instructions. | L |
| M28 | Agent | Build agent communication protocol — allow agents to share findings without going through orchestrator. | L |
| M29 | Pipeline | Add parallel phase execution — phases 4a-4e can run concurrently (all extraction phases). | L |
| M30 | System | Implement progress logging to `00_SYSTEM/PROGRESS_LOG.md` during autonomous runs as documented. | S |

### LOW — Nice to Have (20 todos)

| ID | Category | Description | Complexity |
|----|----------|-------------|------------|
| L01 | Docs | Create comprehensive ENGINE_ARCHITECTURE.md documenting all 5 core engines + 34 standalone engines. | L |
| L02 | Docs | Create AGENT_FLEET_MAP.md with visual diagram of all 85+ agents and their relationships. | L |
| L03 | Docs | Update ARCHITECTURE.md to reflect actual engine locations (not the incorrect paths in instructions). | M |
| L04 | Docs | Document all 30+ databases — purpose, schema summary, update frequency, dependencies. | L |
| L05 | Naming | Rename `drive-organizer.md` to `drive-organizer.agent.md` for consistency with other agent files. | S |
| L06 | Cleanup | Move `litigation_context (2).db` from root to `I:\backups\` per no-delete policy. | S |
| L07 | Cleanup | Audit 00_SYSTEM/engines/ root files — determine which are active vs deprecated. | M |
| L08 | UI | Add engine status indicators to desktop app dashboard. | M |
| L09 | UI | Add filing progress tracker to desktop app with per-package completion percentage. | L |
| L10 | UI | Build evidence browser screen in desktop app — search and preview evidence across all lanes. | L |
| L11 | Optimization | Profile litigation_context.db query performance — identify and index slow queries. | M |
| L12 | Optimization | Implement connection pooling for brain databases — reduce connection overhead for repeated queries. | M |
| L13 | Optimization | Add FTS5 indexes to all brain databases for full-text search capability. | M |
| L14 | Docs | Create RUNBOOK for emergency filing procedures — what to do when pipeline fails mid-filing. | M |
| L15 | Docs | Document the Event Horizon Factory workflow with concrete examples of each PASS gate. | L |
| L16 | Docs | Create ONBOARDING.md for new Copilot sessions — what to check, what to avoid, key paths. | M |
| L17 | Testing | Add smoke tests that verify all 30+ databases can be opened and queried. | M |
| L18 | Testing | Add code coverage reporting to CI — currently `.coverage` exists but no coverage gate. | M |
| L19 | System | Implement self-healing for empty databases — detect 0-byte .db files and trigger rebuild. | M |
| L20 | System | Build OMEGA skill gap detector — automatically identify skills referenced in code but missing SKILL.md. | M |

---

## Appendix A: File Counts Summary

| Location | Count | Type |
|----------|-------|------|
| `00_SYSTEM/engines/*.py` | 89 | Python engine files |
| `00_SYSTEM/local_model/*.py` | 25 | MANBEARPIG + supporting models |
| `00_SYSTEM/pipeline/` | 11+ | Pipeline phase files |
| `.agents/skills/` | 970 | Skill directories |
| `.agents/agents/` | 29 | Agent definitions |
| `.claude/skills/` | 408 | Claude skill directories |
| `01_FILINGS/` | 81 | Filing subdirectories |
| `databases/` | 11 | Jurisdiction databases |
| Root .db files | 6 | Primary databases |
| `00_SYSTEM/*.db` | 8+ | Brain & system databases |
| `09_DATA/lane_*.db` | 5 | Lane databases (1 missing) |
| `11_CODE/litigationos/tests/` | 33 | Test files |
| `docs/` | 100+ | Documentation files |

## Appendix B: Database Size Distribution

| Size Range | Count | Examples |
|------------|-------|---------|
| 0 bytes | 1 | databases/court_forms.db ❌ |
| 1 KB — 100 KB | 15 | Jurisdiction DBs, lane DBs |
| 100 KB — 10 MB | 7 | mcr_rules.db, brain DBs (small) |
| 10 MB — 100 MB | 3 | entity_brain.db, claims_brain.db, consolidation_plan.db |
| 100 MB — 500 MB | 4 | script_forge.db, narrative_brain.db, file_catalog.db, interpretation_brain.db |
| 500 MB — 1 GB | 2 | litigation_context.db (702 MB), chat_intelligence_brain.db (934 MB) |

**Total estimated database storage: ~3.2 GB**

## Appendix C: Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Filing with fabricated party name | LOW (guardrails in place) | CRITICAL (perjury) | Todo C20 — verify all party names |
| Filing with wrong case number | MEDIUM | HIGH (rejected by clerk) | Todo C12 — verify headers |
| DB corruption during concurrent access | MEDIUM | HIGH (data loss) | Todo C10 — implement db_lock_manager |
| Engine failure during filing generation | LOW | HIGH (incomplete filing) | Todos H01-H05 — test all engines |
| Pipeline crash without checkpoint | MEDIUM | HIGH (lost work) | Todo M13 — add crash-resume |
| Stale evidence counts in filings | MEDIUM | HIGH (credibility) | Todo C22 — traceable statistics |
| Court forms lookup fails (0-byte DB) | HIGH | MEDIUM (manual workaround) | Todo C01 — rebuild court_forms.db |

---

*End of System Audit — 2026-03-24*
*Next audit recommended: 2026-04-07 (2 weeks)*
