# COPILOT STARTUP STATE — LitigationOS GOLDEN MASTER v2.1
## Generated: 2026-03-13 | Distilled from 24 sessions, 143 checkpoints, 1,058 todos, 772-table DB deep mine

> **This file is the SINGLE SOURCE OF TRUTH for new Copilot sessions.**
> Read it top to bottom. It replaces all older startup/enhanced instruction files.
> Do NOT hardcode any number from this file into filings — always query the DB for live counts.

---

## 1. VERIFIED PARTY IDENTITY (NEVER fabricate — see HALLUCINATION GRAVEYARD below)

| Role | Name | Details |
|------|------|---------|
| **Plaintiff** | Andrew James Pigors | 1423 W. Norton Ave, Norton Shores, MI 49441 · (231) 260-1936 · andrewjpigors@gmail.com |
| **Defendant** | Emily A. Watson | 2160 Garland Drive, Norton Shores, MI 49441 (NOT "Emily Ann", NOT "Emily M.", NOT "Tiffany") |
| **Child** | L.D.W. | Initials ONLY per MCR 8.119(H) — NEVER full name in filings |
| **Judge** | Hon. Jenny L. McNeill | 14th Circuit Court, Family Division (NOT "Amy McNeill") |
| **Emily's Former Attorney** | Jennifer Barnes (P55406) | Barnes Law Firm PLLC, 880 Jefferson St Ste B, Muskegon, MI 49440 — **WITHDREW** |
| **FOC** | Pamela Rusco | 990 Terrace St, Muskegon, MI 49442 |
| **Ronald Berry** | NON-ATTORNEY | Emily's boyfriend/domestic partner. No bar number. Never was her attorney. |

**Separation date:** July 29, 2025. Calculate days dynamically: `(today - 2025-07-29).days`

### ☠️ HALLUCINATION GRAVEYARD (names/stats that NEVER existed)
- ❌ "Tiffany Watson" / "Tiffany A. Watson" — The defendant is **Emily A. Watson**
- ❌ "Jane Berry" / "Patricia Berry (SBN P35878)" — fabricated in 60+ files across prior sessions
- ❌ "91% alienation score" — pseudo-scientific, never cite
- ❌ "9 CPS investigations" — unverified, never cite unless DB confirms
- ❌ Hardcoded "329+ days" or "605+ days" — always CALCULATE from July 29, 2025

---

## 2. SYSTEM IDENTITY

| Property | Value |
|----------|-------|
| **System** | LitigationOS GOLDEN MASTER v0.9.0 (tagged 2026-03-12, commit 19cf09d) |
| **Architecture** | Michigan-first litigation intelligence · 16-phase pipeline · 155+ agent fleet |
| **Database** | `C:\Users\andre\LitigationOS\litigation_context.db` — **772 tables, 11.46 GB, 18.5M rows** |
| **Product App** | Python ≥3.12, CustomTkinter GUI, 539 tests passing, pip-installable |
| **Canonical Root** | `C:\Users\andre\LitigationOS` |
| **Network** | Copilot HAS internet access. Pipeline AI inference is local-only. |

> ⚠️ DB stats above are from 2026-03-13. Run `PRAGMA table_info()` before querying any table.
> Run `SELECT COUNT(*) FROM sqlite_master WHERE type='table'` for live table count.

---

## 3. CASE MATRIX (6 Lanes — NEVER cross-contaminate)

| Lane | Case | Court | Judge | Case Number | Status |
|------|------|-------|-------|-------------|--------|
| **A** | Watson Custody | 14th Circuit, Muskegon | Hon. Jenny L. McNeill | 2024-001507-DC | Active |
| **B** | Shady Oaks Housing | Van Buren County Circuit | TBD | 2025-002760-CZ | Active |
| **C** | Convergence | Cross-lane | Various | Multi-lane | Active |
| **D** | PPO / Protection Orders | 14th Circuit, Muskegon | Hon. Jenny L. McNeill | 2023-5907-PP | Active |
| **E** | Judicial Misconduct | JTC / MSC | Various | Multi | Active |
| **F** | Appellate (COA/MSC) | MI Court of Appeals | Panel TBD | COA 366810 | Active |

**Additional courts:** Michigan Supreme Court (MSC), USDC Western District of Michigan (§1983)

**MISSION:** Undo EVERYTHING Judge McNeill and Emily Watson have done. Hold ALL adversaries accountable. Every analysis, filing, and strategy advances this singular objective.

---

## 4. CRITICAL DEADLINES (23 tracked — query `deadlines` for live data)

| ID | Case | Deadline | Date | Authority | Status |
|----|------|----------|------|-----------|--------|
| DL-001 | COA-366810 | **COA Appellant Brief** | **2026-04-15** | MCR 7.212(A)(1) | 🔴 UPCOMING |
| DL-COA-APPENDIX | COA-366810 | COA Appendix with Brief | 2026-04-15 | MCR 7.212(D) | UPCOMING |
| DL-DISQUALIFY | 2024-001507 | Disqualification Motion | 2026-03-15 | MCR 2.003(D) | UPCOMING |
| DL-MSC-ORIGINAL | MSC | MSC Superintending Control | 2026-04-01 | MCR 7.305(B)/7.306 | UPCOMING |
| DL-CIVIL-CONSPIRACY | Convergence | Civil Conspiracy Complaint | 2026-04-30 | MCL 600.2910; 42 USC 1983 | UPCOMING |
| DL-SHADY-OAKS | Housing | Shady Oaks Housing Complaint | 2026-04-30 | MCL 600.5775; FHA | UPCOMING |
| DL-JTC-FOLLOWUP | JTC | JTC Complaint Follow-up | 2026-05-01 | MCR 9.200 | UPCOMING |
| DL-1983-FEDERAL | Federal | 42 USC 1983 Federal Complaint | 2026-05-15 | 42 USC 1983; 28 USC 1343 | UPCOMING |
| DL-003 | 2023-5907-PP | PPO Renewal Hearing | 2026-06-01 | MCL 600.2950 | UPCOMING |
| DL-URGENT-001 | 2024-001507 | **SEPARATION: Last saw son July 29, 2025** | OVERDUE | MCL 722.27a; 14th Amend | 🔴 OVERDUE |

> Run `SELECT * FROM deadlines ORDER BY due_date_iso` for all 23 deadlines with full basis/authority.

---

## 5. DATABASE — KEY TABLES (query for live counts, never cite stale numbers)

| Table | ~Rows | Purpose |
|-------|-------|---------|
| `master_citations` | 3.68M | Citation intelligence across all authorities |
| `master_csv_data` | 591K | Structured CSV data imports |
| `file_inventory` | 467K | File metadata across all drives |
| `disk_inventory_omega` | 249K | Drive scanning results |
| `chatgpt_conversations` | 171K | ChatGPT conversation data |
| `chatgpt_litigation_intel` | 169K | Extracted litigation intelligence |
| `drive_file_index` | 159K | 6-drive file index (C, D, F, G, H, I) |
| `master_timeline_parsed` | 132K | Parsed chronological events |
| `evidence_file_index` | 153K | Evidence file metadata |
| `mega_file_harvest` | 53K | Deep file harvest (5.9 GB text, 41K PDF pages) |
| `impeachment_items` | 15K | Witness impeachment material |
| `contradiction_map` | 10K | Detected contradictions |
| `filing_packages` | 29 | Court filing packages |
| `deadlines` | 23 | Active litigation deadlines |
| `vehicles` | 6 | Active litigation vehicles |
| `claims` | 57 | Legal claims tracked |

**70+ FTS5 full-text search indexes** available. Key ones: `evidence_quotes_fts`, `auth_rules_fts`, `pages_fts`, `rules_text_fts`, `md_sections_fts`, `master_csv_fts`

---

## 6. FILING READINESS — 24 Vehicles Tracked (query `filing_readiness` for live scores)

### Top-Priority Filings (scored out of 100)

| Vehicle | Score | Status | Lane | Key Gaps |
|---------|-------|--------|------|----------|
| EMERGENCY_MOTION_RESTORE_PT | **92** | READY | A | Needs notarized affidavit |
| COA_APPELLANT_BRIEF_366810 | **85** | READY | F | Needs fee waiver (due Apr 15) |
| MOTION_FOR_RECONSIDERATION | **85** | READY | A | Needs signature |
| MSC_SUPERINTENDING_CONTROL | **82** | READY | E | Needs 13 copies, notarization |
| JTC_FORMAL_COMPLAINT | **80** | READY | E | Needs signature and mailing |
| JUDICIAL_DISQUALIFICATION | **80** | READY | A/E | Needs evidence backing |
| MODIFY_TERMINATE_PPO | **80** | READY | D | 39 quotes, 11 impeachment items |
| CONTEMPT_SHOW_CAUSE | **75** | READY | A | 65 quotes, 13 impeachment items |
| MSC_APPLICATION | **72** | NEEDS_WORK | E/F | Physical assembly needed |
| 42USC1983_FEDERAL | **65** | NEEDS_WORK | Fed | Authority chain gaps |

### MSC Fleet (9 vehicles, evidence-ready, scores 81-100)

| Vehicle | Score | Damages |
|---------|-------|---------|
| MSC_SUPERINTENDING_CONTROL_FLEET | **100** | — |
| MSC_MANDAMUS_FLEET | **100** | — |
| MSC_EMERGENCY_APP_FLEET | **100** | — |
| JTC_COMPLAINT_FLEET | **98** | 1,127 violations |
| MSC_PROHIBITION_FLEET | **97** | — |
| MSC_DECLARATORY_FLEET | **97** | — |
| FEDERAL_1983_FLEET | **90** | $1.7M-$7.1M |
| MSC_HABEAS_CORPUS_FLEET | **89** | — |
| MSC_LEAVE_BYPASS_FLEET | **89** | — |

### Lane Readiness (from cycle6_filing_readiness)

| Lane | Readiness | Status |
|------|-----------|--------|
| E (Misconduct) | **95%** | JTC complaint filed, MSC ready |
| A (Custody) | **90%** | Briefs ready, motions need assembly |
| D (PPO) | **85%** | Evidence compiled |
| F (Appellate) | **80%** | Brief structured, due Apr 15 |
| C (Convergence) | **70%** | Strategy docs complete |
| B (Housing) | **RESERVED** | Separate lawsuit (Van Buren County) |

**GOLDEN_SET location:** `01_FILINGS/CLERK_READY/` and `04_COURT_FILINGS/`
> Run `SELECT * FROM filing_readiness` for live scores with detailed gaps/strengths.

---

## 7. DRIVE INVENTORY (6 drives, 159K+ indexed files, 32.8 GB)

| Drive | Files | Type | Content |
|-------|-------|------|---------|
| C: | 112K | System | LitigationOS repo, DB, system files |
| D: | 6K | Local | `THIS_IS_THE_ONE` case folders (5 lanes), extracted evidence |
| F: | 15K | Local | Litigation backups, document archives |
| G: | 9.4K | USB | Evidence archives, court documents |
| H: | 5.3K | USB | Additional evidence, backups |
| I: | 10.6K | External HD | Dedup targets, harvested files, session checkpoints |

**22-folder scaffold** deployed on D:, F:, G:, H: (2026-03-12): `_INDEX, 01_FILINGS..19_MISC, LitigationOS, SAFETY_SNAPSHOT`

---

## 8. AI & AGENT FLEET

### THE MANBEARPIG v9.0 OMEGA-INFINITY (Primary Inference Engine)
- **Location:** `00_SYSTEM/local_model/inference_engine.py`
- **Capabilities:** TF-IDF + Naive Bayes + BM25 + semantic embeddings, 50 skills, 140+ JSON-RPC methods
- **30 Python skills** in `local_model/skills/` — lazy-loaded via SKILL_REGISTRY
- **Run:** `python 00_SYSTEM\local_model\inference_engine.py "query"` or `--pipe` for JSON-RPC

### Agent Fleet (155+ agents)
| Fleet | Count | Role |
|-------|-------|------|
| Delta9 (A01-L08) | 56 | Core pipeline (I/O + intelligence + convergence) |
| Delta999 | 12 | Advanced engines (classifier, validator, assembly, deadline, db_lock) |
| Copilot agents | 64 | Specialized sub-agents (see `.copilot/agents/`) |
| Superpower agents | 13 | Cross-cutting orchestration, governance, self-evolution |
| Convergence agents | 10 | Phase 5-6 hardening, filing workflow, MCP v2 |

### MCP Servers
| Server | Purpose | Key Tools |
|--------|---------|-----------|
| **command-runner** | Shell replacement (zero session pool cost) | `exec_command`, `exec_python`, `exec_git` |
| **litigation-context** | 45 legal tools | `search`, `filing_readiness`, `evidence_chain`, `deadline_dashboard` |
| **agent-memory** | Persistent cross-session memory | `store`, `retrieve`, `search` |

### Copilot Session Store
The `session_store` SQL database contains history from ALL past sessions (24+). Use it to:
- Find what was done before: `SELECT * FROM search_index WHERE search_index MATCH 'keyword'`
- Avoid duplicating work: `SELECT * FROM session_files WHERE file_path LIKE '%pattern%'`
- Get session context: `SELECT * FROM checkpoints WHERE session_id = 'X'`

---

## 9. EVIDENCE ARSENAL (precise counts from DB — always re-query for live data)

| Category | Count | Table | Notes |
|----------|-------|-------|-------|
| Evidence quotes | **308,704** | `evidence_quotes` | Categorized by speaker, type, legal significance |
| Violations | **100,995** | `master_violations_parsed` | 49 violation types across 377 files |
| Master citations | **3,684,757** | `master_citations` | MCL, MCR, case law, constitutional |
| Judicial violations | **1,127** | `judicial_violations` | Canon violations, ex parte, bias |
| Impeachment items | **15,171** | `impeachment_items` | Witness impeachment material |
| Contradictions | **10,672** | `contradiction_map` | Detected contradictions |
| Alienation tactics | **50** | `alienation_tactics` | Lombardo framework categories |
| Alienation evidence | **519 findings** | `parental_alienation_evidence` + cycle6 | 225 files processed |

### Most-Cited Authorities (from cycle6_statistics)

| Authority | Mentions | Purpose |
|-----------|----------|---------|
| MCR 3.207 (ex parte domestic orders) | **211** | Core procedural violation |
| MCR 2.119 (motion practice) | **199** | Motion procedural framework |
| MCL 722.27 (custody modification) | **189** | Custody change standard |
| MCR 2.003 (judicial disqualification) | **169** | Disqualification grounds |
| MCL 722.27a (parenting time) | **156** | Parenting time deprivation |
| Canon 3 (judicial conduct) | **146** | Misconduct basis |
| MCL 722.23 (best interest factors) | **133** | 9 of 12 favor Father |
| MCL 600.2950 (PPO) | **98** | PPO dissolution |

### Best Interest Factor Analysis (MCL 722.23) — 9 of 12 Favor Father

| Factor | Score | Key Evidence |
|--------|-------|-------------|
| (d) Moral fitness | **95/100** | Emily: false PPO, perjury documented |
| (e) Mental/physical health | **95/100** | HealthWest cleared Father |
| (i) Domestic violence | **90/100** | No DV by Father; fraudulent PPOs |
| (j) Willingness to facilitate | **100/100** | Father facilitates; Mother obstructs (ZERO consequences) |
| (k) False reporting | **95/100** | Emily perjury documented |

### Claims Matrix (27 classified legal claims in `cycle6_legal_claims`)

| Claim | Probability | Authority | Lane |
|-------|-------------|-----------|------|
| Ex parte suspension without findings | HIGH | MCR 3.207(B); Canon 3(A)(3) | A |
| Arbitrary reduction from 50/50 | HIGH | MCL 722.27; Vodvarka | A |
| Parental alienation by Mother/Watson family | HIGH | Pickering; MCL 722.23(j) | A |
| Fraudulent PPO procurement | 90%+ | MCL 600.2950; Crawford | D |
| Ex parte evidence review | HIGH | Canon 3(A)(4); MCR 3.207 | E |
| Procedural barriers ($250 bond) | HIGH | Canon 2(A); access to courts | E |
| Due process - PT deprivation without findings | HIGH | Troxel; Santosky; Mathews | A,E |
| 42 USC 1983 civil rights | MODERATE | 42 USC 1983; City of Canton | A,E |
| Emergency Custody (UCCJEA) | 87.1% | MCL 722.1203 | A |
| Motion to Compel Discovery | **95.3%** | MCR 2.313(A) — STRONGEST | A |
| Bias Standard (203 supporting facts) | Evidence-rich | MCR 2.003(C)(2) | A,E |
| Discovery Violations (383 supporting facts) | NEW | MCR 2.313 | A |

> **Emily Watson employment:** Kent County Prosecutor's Office (Emp ID 13380, ~9 years). Lori Watson (mother) also Kent County (Emp ID 1190). Both on biweekly payroll since 2018+.

---

## 10. LESSONS LEARNED (24 sessions, distilled)

### 🔴 FATAL MISTAKES TO NEVER REPEAT
1. **EAGAIN crashes** — Caused by >3 concurrent shells/agents. Max 2 shells + 2 agents = 4 total pipe-producing processes. See `.github/instructions/eagain-prevention.instructions.md`
2. **Placeholder proliferation** — Sessions left hundreds of `[ANDREW_REQUIRED]` when data was IN THE DB. Always query `litigation_context.db` FIRST. Andrew said: *"thats the whole point of this. to USE MY FILES ON MY DRIVES."*
3. **Name hallucinations** — "Jane Berry", "Tiffany Watson" propagated to 60+ files. See Graveyard above.
4. **Inflated statistics** — "91% alienation score" was pseudo-scientific. Every stat MUST trace to a specific SQL query.
5. **Mega-task context overflow** — >3 deliverables in one shot crashes sessions. Decompose into waves of 3.
6. **GOAWAY 503 timeout** — Kills agents after 27-40 min. Checkpoint every 10 min or every 3 agent completions.
7. **Lost agent results** — If you don't `read_agent` before context compaction, ALL work is gone. Read IMMEDIATELY.
8. **Inflammatory tone** — "textbook bias", "gratuitous cruelty", "Justice is blind" HURTS credibility with judges. Use measured, professional language.
9. **Shadow modules** — Repo root has `json.py`, `typing.py`, etc. that shadow stdlib. NEVER set CWD to repo root for Python. Use `safe_shell.py`.
10. **Ron Berry confusion** — He is NOT an attorney. No bar number. No "Esq." He is Emily's boyfriend who provided shadow help.

### ✅ PATTERNS THAT WORK
1. **Zero-pipe orchestration** — Main session uses `view/edit/grep/glob/sql` (zero pipes). ALL execution delegated to `task` agents (isolated pipes). Session becomes immune to EAGAIN.
2. **Wave-based autonomous execution** — Max 3 deliverables per wave, checkpoint between waves.
3. **DB-first research** — Query `litigation_context.db` before generating any content. 772 tables = most answers are already there.
4. **Session store continuity** — Query `session_store` to find prior work before starting fresh.
5. **Task agents for commands** — `task(task)` for builds/tests, `task(explore)` for codebase questions. Never raw `powershell` for heavy work.

---

## 11. BUILD, TEST & RUN (Quick Reference)

```powershell
# Product App
cd 11_CODE\litigationos && pip install -e ".[dev]" && python -m pytest tests/ -q

# MANBEARPIG Inference
python 00_SYSTEM\local_model\inference_engine.py "MCR 2.003 disqualification"
python 00_SYSTEM\local_model\copilot_startup_hook.py --file  # Generate startup report
python 00_SYSTEM\local_model\session_recall.py recent         # Session recall

# Pipeline
cd 00_SYSTEM\pipeline && python run_omega_pipeline.py --list-phases

# Safe Python execution (avoids shadow module crashes)
python 00_SYSTEM\tools\safe_shell.py check file.py   # Syntax check
python 00_SYSTEM\tools\safe_shell.py run script.py    # Safe run
```

---

## 12. STARTUP CHECKLIST (run on every new session)

1. **Read this file** — you're doing it now ✅
2. **Calculate separation days** — `(today - 2025-07-29).days` → inject into urgency framing
3. **Check deadlines** — `SELECT * FROM deadlines ORDER BY rowid` (23 active)
4. **Verify DB accessible** — `SELECT COUNT(*) FROM sqlite_master WHERE type='table'` → expect ~772
5. **Query session store** — `SELECT * FROM search_index WHERE search_index MATCH 'relevant topic'` for prior work
6. **Identify case lane(s)** — Route to A-F based on user request
7. **Load relevant authority** — Use FTS5 indexes for fast lookups
8. **NEVER cite stale numbers** — Every statistic must come from a live DB query
9. **NEVER invent party names** — If unknown, insert `[UNKNOWN — VERIFY]`
10. **NEVER insert placeholder without checking DB first** — Search all 772 tables before `[ANDREW_REQUIRED]`

---

## 13. KEY FILE PATHS

| Resource | Path |
|----------|------|
| **This File** | `COPILOT_STARTUP_STATE.md` |
| **Copilot Instructions** | `.github/copilot-instructions.md` (v14.0) |
| **EAGAIN Prevention** | `.github/instructions/eagain-prevention.instructions.md` |
| **Shell Management** | `.github/instructions/shell-management.instructions.md` |
| **Agent Activation** | `.github/instructions/agent-activation.instructions.md` |
| **Database** | `litigation_context.db` (11.46 GB, 772 tables, 18.5M rows) |
| **Backup DB** | `D:\BACKUP\litigation_context_v0.9.0_backup.db` |
| **Inference Engine** | `00_SYSTEM/local_model/inference_engine.py` |
| **Pipeline** | `00_SYSTEM/pipeline/run_omega_pipeline.py` |
| **MCP Server** | `00_SYSTEM/mcp_server/` |
| **Filing Packages** | `01_FILINGS/CLERK_READY/` |
| **Court Filings** | `04_COURT_FILINGS/` |
| **Analysis Catalogue** | `05_ANALYSIS/CATALOGUE/` (9 volumes) |
| **Product App** | `11_CODE/litigationos/` |
| **Agent Profile** | `00_SYSTEM/tools/agent_profile.ps1` |
| **Safe Shell** | `00_SYSTEM/tools/safe_shell.py` |

---
*LitigationOS GOLDEN MASTER v2.1 | Distilled from 24 sessions across 2026-02-19 to 2026-03-13 | 143 checkpoints | 772-table DB deep mine*
