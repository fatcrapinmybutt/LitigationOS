# COPILOT STARTUP STATE — LitigationOS GOLDEN MASTER v4.0
## Generated: 2026-03-13 | Distilled from 24 sessions, 143 checkpoints, 1,058 todos, 772-table DB deep mine, 2,542-line schema analysis, 767-file I: drive harvest deep analysis (17K lines)

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
| `claims` | 653 | Legal claims tracked (429 supported, 90 active) |

### 🔥 HIGH-VALUE ACTIONABLE TABLES (discovered in deep study — USE THESE)

| Table | Rows | Purpose | Key Columns |
|-------|------|---------|-------------|
| `victory_strategy` | 12 | **Ranked actions to undo** with evidence strength | action_to_undo, filing_vehicle, confidence, risk_level |
| `adversary_models` | 114 | **Anticipated attacks + rebuttals** per filing | attack_type, weakness_exploited, rebuttal_strategy, rebuttal_authority |
| `constitutional_violations` | 11 | **Documented 14th/1st/6th Amendment violations** | amendment, violation_type, controlling_caselaw, filing_target |
| `constitutional_brief_sections` | 6 | **Pre-drafted IRAC sections** for 6 rights | right_name, issue_text, rule_text, application_text, key_citations |
| `constitutional_rights_tracker` | 6 | **Violation counts per right** with remedies | right, violation_count, evidence_sources, remedy |
| `case_law_library` | 25 | **Indexed cases** with holdings + filing stacks | case_name, holding, relevance, filing_stacks |
| `risk_events` | 21 | **Risk types** with severity + cure packets | risk_type, severity, cure_packet, authority_ref |
| `witness_profiles` | 10 | **Witness data** with credibility scores | name, role, credibility_score |
| `cycle6_witnesses` | 9 | **Subpoena priorities** with evidence refs | name, priority, evidence_ref |
| `hearing_transcripts` | 311 | **Indexed hearing files** with key findings | hearing_date, hearing_type, key_findings |
| `hearing_calendar` | 4 | **Upcoming hearings** with filing deadlines | hearing_date, filing_deadline, service_deadline |
| `docket_events` | 221 | **Procedural history** (62 hearings, 30 orders, 24 ex parte) | event_date_iso, title, event_type, summary |
| `damages_quantification` | 18 | **Damages by harm category** with ranges | harm_category, low_estimate, mid_estimate, high_estimate |
| `damages_calculations` | 16 | **Damages by forum** with authorities | category, amount_low, amount_high, authority |
| `damages_itemization` | 15 | **Line-item damages** with evidence refs | category, amount, evidence_ref, legal_basis |
| `schema_reference` | 508 | **DB self-documentation** — maps column names | table_name, column_name, common_mistake, correct_usage |
| `andrew_messages` | 48K | **Andrew's ChatGPT messages** — canonical truth | message_text, conversation_title |
| `canonical_fact_index` | 41K | **Verified facts** with confidence scores | fact_text, confidence, source |
| `proposed_orders` | 16 | **Pre-drafted proposed orders** per motion | motion_path, order_text, relief_items |

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

### Claims Matrix (653 classified legal claims — 429 supported, 90 active, 44 active-critical)

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

## 14. SCHEMA QUICK REFERENCE (prevents the #1 query failure mode)

> Past sessions crashed repeatedly on wrong column names. ALWAYS run `PRAGMA table_info(table_name)` on first use.
> The `schema_reference` table (508 rows) self-documents the DB: `SELECT * FROM schema_reference WHERE table_name = 'X'`

| Table | ✅ Correct Column | ❌ Common Mistake | Notes |
|-------|-------------------|-------------------|-------|
| `authority_chains` | `chain_complete` | `is_complete` | INTEGER, use `WHERE chain_complete = 1` |
| `authority_chains` | `filing_vehicle` | `action_name` | TEXT |
| `filing_readiness` | `vehicle_name` | `vehicle` | TEXT |
| `filing_readiness` | `total_score` | `readiness_score` | INTEGER |
| `claims` | `claim_id` | `id` | TEXT (not INTEGER) |
| `auth_rules` | `full_text` | `rule_text` | TEXT |
| `omega_scores` | `name` | `action_name` | TEXT |
| `docket_events` | `event_date_iso` | `event_date` | TEXT (ISO format) |
| `docket_events` | `title`, `summary` | `description` | Two separate columns |
| `judicial_violations` | `canon_number` | `category`, `violation_type` | TEXT |
| `impeachment_items` | `item_type` | `category` | Top types: TIMELINE_CONTRADICTION (7,189), PRIOR_INCONSISTENT_STATEMENT (3,538) |
| `evidence_quotes` | `quote_text` | `text`, `content` | TEXT |
| `evidence_quotes` | `source_type` | `type` | Values: PDF_COURT_DOC (308K), CHATGPT_REFERENCE (32) |
| `extracted_harms` | `category` | `harm_type` | TEXT |

### Filing Readiness Columns (COMPLETE — 15 columns)
`id, vehicle_name, best_source, best_source_path, authority_score, evidence_score, compliance_score, impeachment_score, total_score, gaps, strengths, attack_vectors, rebuttals_ready, status, created_at`

### Evidence Quotes Columns (COMPLETE — 12 columns)
`id, document_id, page_number, evidence_category, quote_text, quote_hash, quote_type, speaker, date_ref, legal_significance, created_at, source_type`

### Deadlines Columns (COMPLETE — 10 columns)
`deadline_id, case_id, title, due_date_iso, basis, basis_authority, risk_if_missed, status, created_at, updated_at`

---

## 15. FILING REQUIREMENTS BY COURT

| Court | Copies | Fee | Key Rules | Mandatory Forms | Service |
|-------|--------|-----|-----------|-----------------|---------|
| **MSC** | 13 | $375 (or MC 20 waiver) | MCR 7.305(B), 7.306 | MC 20 (fee waiver) | Serve all parties |
| **COA** | 5 | $375 (or MC 20 waiver) | MCR 7.212 (brief format) | Word count certificate | Serve all parties |
| **JTC** | 2 | **FREE** | MCR 9.200-9.252 | Notarized affidavit REQUIRED | Mail to JTC office |
| **14th Circuit** | 3 | $20/motion | MCR 2.119 (9+3=12 day service) | CC 377/380 (PPO); FOC 65/67 (PT) | MCR 2.107 |
| **USDC W.D. Mich** | 1 (e-file) | $405 (or IFP) | 28 USC §1915 (IFP) | JS 44 civil cover sheet; summons per defendant | Fed. R. Civ. P. 4 |

**UNIVERSAL RULES:**
- **Certificate of Service ALWAYS LAST** (MCR 2.107) — every filing, no exceptions
- **MCR 2.003(D):** Disqualification motions go to **CHIEF JUDGE**, not the challenged judge
- **SCAO forms MANDATORY:** FOC 65/67 for parenting time, CC 377/380 for PPO
- **Pro se signature block:** Andrew James Pigors, 1423 W. Norton Ave, Norton Shores, MI 49441, (231) 260-1936, andrewjpigors@gmail.com
- **Child reference:** L.D.W. (initials only per MCR 8.119(H))

---

## 16. CONSTITUTIONAL FRAMEWORK (ready for COA brief + §1983 complaint)

### 6 Constitutional Rights Violated (from `constitutional_rights_tracker`)

| Right | Amendment | Violation Count | Remedy | Filing Target |
|-------|-----------|-----------------|--------|---------------|
| Due Process — Right to Parent | 14th Amend | **15,677** | Restore PT; vacate ex parte orders; MSC superintending control | MSC, Emergency PT, COA, §1983 |
| Michigan Due Process | Art 1 § 17 | **8,895** | MSC superintending control; vacate deficient orders; reassignment | MSC, JTC, all circuit motions |
| Right to Petition / Access Courts | 1st Amend | **6,865** | Vacate $250 bond (Boddie); remove filing restrictions | MSC, §1983, reconsideration |
| Equal Protection | 14th Amend | **3,326** | Judicial disqualification MCR 2.003(C)(1); equal enforcement | MSC, JTC, reconsideration |
| Right to Confront Witnesses | 6th Amend (via 14th) | **2,314** | Vacate contempt findings; mandate right to be heard | COA, MSC, reconsideration |
| Family Integrity | 14th/9th Amend | **567+ days** | Immediate restoration; therapeutic reunification; compensatory PT | MSC, COA, §1983, emergency |

### 11 Documented Constitutional Violations (from `constitutional_violations`)
Each has: amendment, clause, violation_type, controlling_caselaw (SCOTUS + Michigan), michigan_authority, filing_target, severity

### 6 Pre-Drafted IRAC Sections (from `constitutional_brief_sections`)
Ready-to-use for COA brief and §1983 complaint — each has Issue, Rule, Application (with DB-verified evidence quotes), and Conclusion:
1. **Due Process — Procedural** (Mathews v. Eldridge; Santosky v. Kramer)
2. **Due Process — Substantive / Right to Parent** (Troxel v. Granville; Stanley v. Illinois)
3. **Equal Protection — Disparate Treatment** (MCR 2.003(C)(1))
4. **First Amendment — Right to Petition** (Boddie v. Connecticut; California Motor Transport)
5. **Right to Family Integrity** (Moore v. East Cleveland; Meyer v. Nebraska; Pierce v. Society of Sisters)
6. **6th Amendment — Right to Confront** (applicable in civil contempt via Due Process)

### Key Controlling Cases
| Case | Holding | Use In |
|------|---------|--------|
| **Troxel v. Granville**, 530 U.S. 57 (2000) | Parental rights are fundamental; fit parents presumed to act in child's interest | COA, §1983, Emergency PT |
| **Santosky v. Kramer**, 455 U.S. 745 (1982) | Clear and convincing evidence required to terminate parental rights | COA, MSC |
| **Mathews v. Eldridge**, 424 U.S. 319 (1976) | Three-part due process balancing test | COA, §1983 |
| **Boddie v. Connecticut**, 401 U.S. 371 (1971) | Financial barriers cannot deny court access to indigent litigants | MSC, §1983 |
| **Vodvarka v. Grasmeyer**, 259 Mich App 499 (2003) | Proper cause/change of circumstances for custody modification | COA, 14th Circuit |

> Run `SELECT * FROM constitutional_violations` and `SELECT * FROM constitutional_brief_sections` for full content.
> Run `SELECT * FROM case_law_library` for all 25 indexed cases with holdings.

---

## 17. ADVERSARY MODELS (114 anticipated attacks — defense prep)

The `adversary_models` table (114 rows) maps attacks Emily/McNeill may make against EACH filing vehicle:

**Columns:** id, filing_vehicle, attack_type, attack_description, weakness_exploited, risk_level, rebuttal_strategy, rebuttal_evidence, rebuttal_authority, our_evidence_strength

### Sample Attack/Rebuttal Pairs
| Filing | Attack | Risk | Rebuttal Authority |
|--------|--------|------|--------------------|
| Emergency PT | "Father is a danger to child" | HIGH | HealthWest assessment clears Father; no founded CPS findings |
| Disqualification | "No actual bias shown" | MEDIUM | 1,127 judicial violations in DB; 43.6% ex parte rate |
| COA Brief | "Discretion of trial court" | MEDIUM | Constitutional violations override discretion (Troxel, Santosky) |
| §1983 Federal | "Judicial immunity" | HIGH | Exception: acts in clear absence of jurisdiction (Mireles v. Waco) |
| JTC Complaint | "Isolated incidents" | LOW | Pattern of 1,127 violations over 221 docket events = systemic |

> Run `SELECT filing_vehicle, attack_type, risk_level, rebuttal_strategy FROM adversary_models ORDER BY filing_vehicle` for full defense playbook.

---

## 18. VICTORY STRATEGY (12 ranked actions to undo — from `victory_strategy`)

| Priority | Action to Undo | Filing Vehicle | Evidence Strength | Confidence |
|----------|---------------|----------------|-------------------|------------|
| **1** | Ex parte order suspending ALL PT (Aug 8, 2025) | MSC Superintending + Emergency PT | OVERWHELMING — 5 ex parte on single day; 24/55 orders (43.6%) ex parte | HIGH (95%) |
| **2** | $250 bond for new filings | MSC Superintending + §1983 | STRONG — Boddie directly on point; no statutory basis | VERY HIGH (98%) |
| **3** | Denial of motion to restore PT | MSC Mandamus + COA 366810 | STRONG — MCL 722.27a requires PT; no BIF hearing conducted | HIGH (90%) |

> Run `SELECT * FROM victory_strategy ORDER BY id` for all 12 actions with full risk/mitigation strategies.

---

## 19. DAMAGES FRAMEWORK ($277K–$1.74M quantified across 5 tables)

### Summary by Harm Category (from `damages_quantification`)

| Category | Low | Mid | High | Evidence |
|----------|-----|-----|------|----------|
| Lost Parenting Time (329+ days) | $13,522 | $24,675 | $39,480 | cycle6_statistics |
| Emotional Distress (parent-child separation) | $16,450 | $41,125 | $65,800 | 540 alienation indicators |
| Emotional Distress (child psychological harm) | $50,000 | — | $250,000 | MCL 722.23(a)-(l) |
| Wrongful Incarceration (59 days) | $8,850 | — | $17,700 | Jail records; MCL 691.1755 |
| Lost Employment (2 job losses) | $35,000 | — | $70,000 | Employment/termination records |
| Attorney Fees / Litigation Costs | $2,000 | — | $8,000 | docket_events |
| **Federal §1983** (all categories) | **$100,000** | — | **$500,000+** | 42 USC §1983; Troxel |

### 5 Damages Tables
| Table | Rows | Focus |
|-------|------|-------|
| `damages_quantification` | 18 | By harm category with low/mid/high estimates |
| `damages_calculations` | 16 | By forum with authorities |
| `damages_items` | 47 | Individual damage items |
| `financial_damages_comprehensive` | 45 | Comprehensive financial analysis |
| `damages_itemization` | 15 | Line-items with evidence refs and legal basis |

> Run `SELECT * FROM damages_quantification ORDER BY high_estimate DESC` for full breakdown.

---

## 20. WITNESS PROFILES & SUBPOENA PRIORITIES

### Key Witnesses (from `witness_profiles` + `cycle6_witnesses`)

| Name | Role | Priority | Key Evidence |
|------|------|----------|-------------|
| **Emily A. Watson** | Defendant/Mother | CRITICAL | Emp ID 13380, Kent Co Prosecutor's Office; DOB discrepancy (10/27/89 vs 10/4/94 — investigate) |
| **Andrew J. Pigors** | Plaintiff/Father | — | Credibility 0.85; HealthWest cleared |
| **Jennifer Barnes (P55406)** | Emily's former atty | HIGH | WITHDREW; credibility 0.9 |
| **Judge Jenny L. McNeill** | Trial judge | — | 1,127 violations; credibility 1.0 (as witness) |
| **Officer Tyler Ritchie** | NSPD | HIGH | Report NSPD-2023-08121 |
| **Lori Watson** | Emily's mother / Kent Co employee | HIGH | Emp ID 1190; payroll records |
| **Albert Watson** | Emily's father | MEDIUM | Witness to family dynamics |
| **Cody Watson** | Emily's brother | MEDIUM | Witness to family dynamics |
| **Lincoln D.W.** | Child (DOB: Nov 9, 2022) | — | Use initials only (MCR 8.119(H)) |
| **Pamela Rusco** | FOC | — | 990 Terrace St, Muskegon |

> ⚠️ DB has "Tiffany Watson" in some older records (docket_events DE-001, witness_profiles). This is STALE DATA — always use "Emily A. Watson."

---

## 21. DB QUERY COOKBOOK (benchmarks + fast patterns)

### Performance Benchmarks
| Query | Time | Notes |
|-------|------|-------|
| `auth_rules` LIKE search | **0.6ms** | Fast — use for quick lookups |
| `auth_rules_fts` MATCH | **5.0ms** | FTS5 — better for multi-term |
| `evidence_quotes_fts` MATCH | **4.5ms** | FTS5 — good performance |
| `evidence_quotes` COUNT(*) | **146ms** | 308K rows — acceptable |
| `filing_readiness` full table | **0.8ms** | 24 rows — instant |
| `claims` JOIN `evidence_links` | **1.5ms** | Fast JOINs |
| `master_citations` COUNT(*) | **3,622ms** | ⚠️ SLOW (3.7M rows) — use mmap for 10.8x speedup |

### Connection Template (ALWAYS use this)
```python
import sqlite3
conn = sqlite3.connect(r"C:\Users\andre\LitigationOS\litigation_context.db", timeout=180)
conn.execute("PRAGMA busy_timeout = 180000")
conn.execute("PRAGMA journal_mode = WAL")
conn.execute("PRAGMA cache_size = -32000")  # 32 MB
conn.execute("PRAGMA temp_store = MEMORY")
conn.execute("PRAGMA synchronous = NORMAL")
```

### ❌ NEVER DO THIS
```python
# NEVER run get_robust_connection() on production DB — triggers PRAGMA integrity_check on 11.46 GB, hangs indefinitely
# NEVER run python -c "..." in PowerShell — use temp .py files
# NEVER set CWD to repo root for Python (shadow modules: json.py, typing.py, etc.)
# NEVER assume column names from memory — run PRAGMA table_info() first
```

### Fast Lookup Patterns
```sql
-- Filing readiness for a vehicle
SELECT * FROM filing_readiness WHERE vehicle_name = 'EMERGENCY_MOTION_RESTORE_PT';

-- Evidence for a specific claim
SELECT eq.quote_text, eq.speaker, eq.date_ref
FROM evidence_quotes eq
WHERE eq.evidence_category = 'court_order' AND eq.quote_type = 'RULING'
LIMIT 20;

-- Adversary attacks for a filing
SELECT attack_type, risk_level, rebuttal_strategy
FROM adversary_models WHERE filing_vehicle LIKE '%EMERGENCY%';

-- Constitutional violation + authority
SELECT amendment, violation_type, controlling_caselaw, filing_target
FROM constitutional_violations WHERE severity = 'CRITICAL';

-- Schema lookup (prevent query crashes)
SELECT column_name, column_type, common_mistake, correct_usage
FROM schema_reference WHERE table_name = 'filing_readiness';

-- Consolidated counts (single query, not N separate COUNT(*) calls)
SELECT
    (SELECT COUNT(*) FROM evidence_quotes) AS quotes,
    (SELECT COUNT(*) FROM judicial_violations) AS violations,
    (SELECT COUNT(*) FROM claims WHERE status = 'supported') AS supported_claims,
    (SELECT COUNT(*) FROM deadlines WHERE status = 'upcoming') AS upcoming_deadlines;
```

---

## 22. DOCKET EVENT TYPES (221 events in `docket_events`)

| Event Type | Count | Examples |
|------------|-------|---------|
| hearing | 62 | Evidentiary hearings, status conferences |
| order | 30 | Court orders |
| parenting_time | 21 | PT modifications, suspensions |
| evidentiary_hearing | 16 | Contested hearings |
| ex_parte_order | 24 | Ex parte orders (43.6% of all orders) |
| motion | 14 | Filed motions |
| contempt | 8 | Show cause, contempt findings |
| appeal | 5 | COA filings |
| ppo | 5 | PPO actions |

> Run `SELECT event_type, COUNT(*) FROM docket_events GROUP BY event_type ORDER BY COUNT(*) DESC` for live distribution.

---

## 23. HARVEST EVIDENCE ARSENAL (767 files — I: drive, 26.4 MB text)

Source: `I:\20260209_0430_HARVEST_000000006_FULL_SAFE\texts` — all 767 files read, cataloged, and cross-referenced.
Deep analysis: `temp\harvest_deep_analysis.txt` (17,067 lines, 778 KB). Catalog: `temp\harvest_catalog.jsonl`.

### Topic Distribution
| Topic | Files | Key Content |
|-------|-------|-------------|
| **Custody** | 183 | Court orders, custody judgment, FIG conference, PT schedules, best interest factors, police narratives |
| **Housing** | 161 | Shady Oaks eviction, lock-change, sewage, Cricklewood MHP, EGLE violations, affidavits |
| **PPO** | 100 | PPO extensions, show cause orders, contempt, violation hearings, docket sheets |
| **General** | 96 | Mixed administrative, court forms, scheduling orders |
| **Judicial Misconduct** | 89 | JTC complaint, canon violations, disqualification motion, bench warrant orders |
| **Evidence** | 74 | Exhibit indexes, affidavits, police reports, ChatGPT export analysis tools |
| **Financial** | 46 | Child support calculations, FOC UCSOMs, deviation orders, $50/month CS |
| **Appellate** | 18 | COA briefs, MSC applications, supervisory orders, proposed orders |

### Cross-Cutting Evidence (critical for filings)
| Category | Files | Key Finding |
|----------|-------|-------------|
| **Court Orders** | 83 | Actual "IT IS ORDERED" text — custody judgment, PT suspensions, $250 bond, HealthWest order |
| **Affidavits** | 90 | 10+ Andrew Pigors affidavits (custody mod, flight risk, alienation, bias, refutations, housing, PPO) |
| **Ex Parte Evidence** | 165 | Massive — 165 files document ex parte handling. Emily's emergency motion, McNeill's suspension order, chambers-only HealthWest directives |
| **HealthWest Records** | 114 | Two complete evaluations (08/05/2025 & 09/11/2025), Case #02508341, DeAugustine/Gansen clinicians, PHQ-9, C-SSRS, CANS, consent forms, release packets |
| **Testimony/Transcripts** | 70 | PPO Oct 30 2024 transcript pages, hearing testimony references |
| **Financial Data** | 143 | CS calculations, deviation at $50/month, FOC forms, $3,480 arrears, Kent County payroll (Emily Emp ID 13380) |
| **$250 Bond** | 8 | May 16, 2025 order imposing filing bond — documented in JTC complaint, court orders, ex parte filings |

### Party Mentions (across all 767 files)
| Party | Files Mentioned | Context |
|-------|----------------|---------|
| **Pigors** | 466 (61%) | Plaintiff in virtually all documents |
| **Watson** | 355 (46%) | Emily A. Watson as defendant/petitioner |
| **McNeill** | 188 (24%) | Judge — orders, ex parte handling, JTC complaint |
| **Rusco** | 48 (6%) | FOC secretary — email correspondence, HealthWest transmittal |
| **Barnes** | 33 (4%) | Jennifer Barnes P55406 — withdrew as Emily's attorney |
| **Berry** | 14 (2%) | Ronald Berry — Emily's partner (NON-attorney) |

### High-Value Files (top 10 by legal term density)
| File | Size | Hits | Topic |
|------|------|------|-------|
| `master_nodes.csv.txt` | 8.0 MB | 87,947 | Graph DB export — authority hubs, violation nodes, evidence links |
| `massiveeee_evidence_atoms.csv.txt` | 2.0 MB | 25,571 | Evidence atom CSV — structured evidence with case numbers + lanes |
| `MindEye2_nodes_combined.csv.txt` | 7.9 MB | 17,801 | MindEye graph nodes — motion generators, adversary models |
| `Comprehensive_Overview_MEEK1_MEEK4.docx.txt` | 84 KB | 877 | Complete legal overview of all 4 MEEK actions |
| `000ZIPS_doc_index.csv.txt` | 33 KB | 479 | Master index of all ZIP-extracted documents |
| `CASE_CHRONOLOGY_PROCEEDING_MAP.html.txt` | 37 KB | 358 | Full case chronology with graph-extracted anchors |
| `Verified_Chronology_Procedural_Violations.pdf.txt` | 25 KB | 285 | Pin-cited chronology of every MCR violation |
| `SCANNEDMergeddocketsnotices.pdf.txt` | 12 KB | 218 | Merged docket sheets — complete PPO record |
| `AffidavitAndrew_FLIGHTRISK_.docx.txt` | 27 KB | 129 | International flight risk affidavit (non-Hague concerns) |
| `Response_to_show_cause_.docx.txt` | 12 KB | 118 | Show cause response — AppClose not harassment |

### Legal Authority Coverage
- **5,190 unique legal authorities** cited across harvest files
- Top MCR citations: MCR 3.207(B) (493), MCR 3.203 (486), MCR 3.211 (455), MCR 2.003(C) (349)
- **1,185 unique dates** referenced (coverage: 2021 through 2026)
- **20 unique case numbers** including all 5 case lane variants

### ⚠️ NEW EVIDENCE: 760 of 767 files contain content NOT in `litigation_context.db`
This harvest is almost entirely unmined material. Only 7 files had content matching existing `evidence_quotes`.
Ingestion into the DB would dramatically expand the evidence base.

### Email Files Found (5 total)
| File | Key Content |
|------|-------------|
| `Healthwest_Exam.eml.txt` | Rusco/Pigors exchange re: HealthWest evaluation transmittal to chambers |
| `HealthWest_Lobby_Support_Specialist_Prescreen_Questions.eml.txt` | Barb Carriere prescreen — shows Andrew applied for HealthWest staff role |
| `PROVENANCE_INDEX...csv.txt` | References to additional .eml files in massiveeee.zip archive |

### HealthWest Assessment Details (from harvest — critical evidence)
- **Case #**: 02508341
- **DOB confirmed**: 12/30/1987 (Andrew)
- **Address at evaluation**: 1977 Whitehall Road Lot 17, Muskegon, MI 49445
- **1st Assessment**: 08/05/2025 (Service H0002, Brief screening to non-inpatient) — Clinician: Melissa DeAugustine LBSW
- **2nd Assessment**: 09/11/2025 — Clinician: Gansen
- **Key finding**: "seeking information only. He is not opening to HealthWest services. He is in agreement with this plan."
- **Diagnosis code**: F22 (Delusional disorder) — listed as "rule out" status
- **Critical**: Judge directed HealthWest eval be submitted to CHAMBERS email (not filed with clerk) — ex parte handling of merits evidence

---

## 24. KEY EVIDENCE QUOTES (harvest-sourced — verbatim, citable)

### Ex Parte Motion Text (Emily Watson, Aug 8, 2025)
> "NOW COMES Defendant, Emily Watson, files the Emergency Ex Parte Motion to Suspend Parenting Time"
> — Filed WITHOUT sworn affidavit or verification (MCR 3.207 violation)

### Court's Ex Parte Order
> "IT IS HEREBY ORDERED that Defendant's Ex Parte Motion to Suspend Plaintiff's Parenting Time is: Granted as follows: Suspend the Plaintiff's parenting time with minor child, Lincoln"
> — Signed by Hon. Jenny L. McNeill, August 2025

### HealthWest Chambers Directive
> "staff instructed me by email to submit my HealthWest evaluation directly to the judge's chambers email instead of filing it with the clerk, keeping this central piece of evidence out of the official court file"

### $250 Bond Order
> "It is further ordered that the Plaintiff must pay a bond of $250 (for each motion) before he may file another motion in this matter"
> — May 16, 2025 order (Boddie v. Connecticut violation — access to courts)

### Police Report (Emily's PPO Basis)
> "Emily can go tomorrow to get an Ex Parte order for full custody of her son. Emily said she is supposed to exchange her son with Andrew tomorrow and she does not feel comfortable with Andrew caring for the child."
> — Officer Randall 47437, Case NS2505044

### Affidavit of Parentage
> "In the affidavit it states the mother of the child has initial custody of the child until determined otherwise by the court. Andrew was shown this affidavit."
> — NSPD report confirming signed Affidavit of Parentage by both parties

---

*LitigationOS GOLDEN MASTER v4.0 | 24 sessions · 143 checkpoints · 772 tables · 2,542-line schema study · 508-row schema_reference · 767-file harvest deep analysis | Distilled 2026-02-19 through 2026-03-13*
