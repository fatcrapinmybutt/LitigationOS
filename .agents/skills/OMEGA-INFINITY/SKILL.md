---
name: OMEGA-INFINITY
description: >-
  Cognitive litigation kernel that cross-wires 12 brain modules, 16+ databases,
  6 drives of evidence, 300+ court forms, 728 authorities, and 92K+ evidence quotes
  into one unified intelligence mesh. Autonomous gap detection, agent activation,
  and Neo4j Bloom graph visualization. Zero hallucination tolerance.
  Michigan family law: Pigors v Watson, 14th Circuit, Muskegon County.
category: discipline
version: "4.0.0"
triggers:
  - omega infinity
  - cognitive kernel
  - brain mesh
  - litigation intelligence
  - full system
  - god mode
  - everything
  - complete analysis
  - all lanes
  - master brain
  - autonomous
  - gap detection
  - neo4j
  - bloom graph
lanes:
  - "A: Watson/Custody (2024-001507-DC)"
  - "B: Shady Oaks/Housing (2025-002760-CZ)"
  - "C: Federal §1983 (USDC WDMI)"
  - "D: PPO (2023-5907-PP)"
  - "E: Judicial Misconduct/JTC"
  - "F: Appellate (COA 366810)"
court: "14th Judicial Circuit, Muskegon County"
case: Pigors v Watson
dependencies:
  - OMEGA-LITIGATION-SUPREME
  - OMEGA-EVIDENCE
  - OMEGA-RESEARCH
  - OMEGA-ARCHITECT
  - OMEGA-ENGINEER
  - OMEGA-DATA
metadata:
  tier: 0
  fused_skills: 200+
  brains: 12
  author: andrew-pigors + copilot-omega
  forge_date: 2026-03-21
---

# ∞ OMEGA-INFINITY ∞

```
╔══════════════════════════════════════════════════════════════════════════╗
║                    COGNITIVE LITIGATION KERNEL v4.0                     ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║         Ω1-Litigation ←——→ Ω4-Rules ←——→ Ω3-Forms                     ║
║              ↕                  ↕              ↕                        ║
║         Ω10-Filing ←———→ Ω8-Financial    Ω5-Adversary                  ║
║              ↕                  ↕              ↕                        ║
║         Ω2-Evidence ←——→ Ω6-Timeline ←——→ Ω7-Judicial                  ║
║              ↕                  ↕              ↕                        ║
║         Ω9-Witness        Ω11-Agent ←————→ Ω12-Context                 ║
║              ↕                  ↕              ↕                        ║
║              └—————————→ ALL CROSS-WIRED ←—————┘                        ║
║                                                                        ║
║  6 Lanes │ 12 Brains │ 16+ DBs │ 300+ Forms │ Zero Hallucination      ║
╚══════════════════════════════════════════════════════════════════════════╝
```

## Mission

Cognitive litigation kernel providing unified intelligence across all 6 case lanes in Pigors v Watson. Cross-wires 12 specialized brain modules into a single reasoning mesh that ingests evidence from 6 drives, maps it against Michigan court rules and 300+ SCAO forms, detects gaps autonomously, dispatches agents to fill them, and converges on court-ready filings — all with zero hallucination tolerance and full provenance tracing back to `litigation_context.db`.

---

## 12-Brain Module Map

Every brain is a standalone reference document in `references/`. This SKILL.md loads them, cross-wires their outputs, and routes queries. **Never duplicate brain content here — reference it.**

| Brain | Module | Reference File | Primary DB Tables | Key Capability |
|-------|--------|---------------|-------------------|----------------|
| **Ω1** | Litigation Brain | `references/Ω1-litigation-brain.md` | `claims`, `docket_events`, `filing_readiness` | IRAC analysis, claim scoring, filing strategy per lane |
| **Ω2** | Evidence Brain | `references/Ω2-evidence-brain.md` | `evidence_quotes`, `documents`, `exhibit_index` | Evidence triage, Bates stamping, chain of custody |
| **Ω3** | Forms Brain | `references/Ω3-forms-brain.md` | `court_forms`, `form_requirements`, `form_fields` | SCAO form selection, field mapping, compliance check |
| **Ω4** | Rules Brain | `references/Ω4-rules-brain.md` | `authority_chains`, `mcr_rules`, `statutes` | MCR/MCL citation, authority validation, rule lookup |
| **Ω5** | Adversary Brain | `references/Ω5-adversary-brain.md` | `adversary_patterns`, `claims`, `evidence_quotes` | Watson/Berry conduct patterns, counterstory prediction |
| **Ω6** | Timeline Brain | `references/Ω6-timeline-brain.md` | `timeline_events`, `docket_events`, `deadlines` | Chronology construction, deadline tracking, sequencing |
| **Ω7** | Judicial Brain | `references/Ω7-judicial-brain.md` | `judicial_violations`, `judicial_findings`, `docket_events` | McNeill bias documentation, JTC complaint prep |
| **Ω8** | Financial Brain | `references/Ω8-financial-brain.md` | `damages`, `costs`, `financial_records` | Damages calculation, cost tracking, financial exhibits |
| **Ω9** | Witness Brain | `references/Ω9-witness-brain.md` | `witnesses`, `testimony`, `depositions` | Witness management, testimony indexing, impeachment prep |
| **Ω10** | Filing Brain | `references/Ω10-filing-brain.md` | `filing_readiness`, `filing_packages`, `service_log` | Filing assembly, packet QA, service proof tracking |
| **Ω11** | Agent Brain | `references/Ω11-agent-brain.md` | `agent_log`, `ready_queue`, `todos` | Fleet orchestration, agent dispatch, pipeline status |
| **Ω12** | Context Brain | `references/Ω12-context-brain.md` | `sessions`, `checkpoints`, `session_state` | Cross-session memory, context persistence, recall |

---

## Decision Router

Route ANY litigation request to the correct brain(s). Multiple brains fire when domains overlap.

```
Request received →
│
├─ Evidence / exhibit / scan / Bates / chain of custody
│  → Ω2 (Evidence) + Ω6 (Timeline)
│
├─ Filing / motion / brief / petition / complaint
│  → Ω1 (Litigation) + Ω10 (Filing) + Ω3 (Forms)
│
├─ Rules / authority / citation / MCR / MCL / statute
│  → Ω4 (Rules)
│
├─ Adversary / Watson / Berry / accusation / counterstory
│  → Ω5 (Adversary)
│
├─ Judge / McNeill / misconduct / JTC / bias / recusal
│  → Ω7 (Judicial)
│
├─ Money / damages / costs / fees / financial
│  → Ω8 (Financial)
│
├─ Witness / testimony / deposition / impeachment
│  → Ω9 (Witness) + Ω2 (Evidence)
│
├─ Agent / fleet / pipeline / orchestration / status
│  → Ω11 (Agent)
│
├─ Context / memory / session / recall / history
│  → Ω12 (Context)
│
├─ Timeline / chronology / deadline / sequence
│  → Ω6 (Timeline)
│
├─ Form / SCAO / court form / field mapping
│  → Ω3 (Forms)
│
├─ Gap analysis / missing data / acquisition
│  → ALL 12 BRAINS (each reports its own gaps)
│
└─ Full briefing / complete analysis / god mode
   → ALL 12 BRAINS (sequential load, cross-wire, synthesize)
```

**Lane routing overlay** — after brain selection, scope to the correct lane:

| Signal | Lane | Case Number |
|--------|------|-------------|
| Custody, parenting time, FOC | A | 2024-001507-DC |
| Housing, Shady Oaks, title, property | B | 2025-002760-CZ |
| §1983, federal civil rights | C | USDC WDMI |
| PPO, protection order | D | 2023-5907-PP |
| Judicial misconduct, JTC | E | (complaint) |
| Appeal, COA, MSC | F | COA 366810 |

---

## Party Identity — Canonical Reference

> **MANDATORY.** Every brain, agent, and generated document MUST use these identities. Fabricating names is perjury-adjacent in sworn filings.

| Role | Name | Details |
|------|------|---------|
| **Plaintiff** | Andrew James Pigors | 1977 Whitehall Road, Lot 17, North Muskegon, MI 49445 · (231) 903-5690 · andrewjpigors@gmail.com |
| **Defendant** | Emily A. Watson | 2160 Garland Drive, Norton Shores, MI 49441 (NOT "Emily Ann", NOT "Emily M.", NOT "Tiffany") |
| **Child** | L.D.W. | Initials ONLY per MCR 8.119(H) — NEVER full name in filings |
| **Judge** | Hon. Jenny L. McNeill | 14th Circuit Court, Family Division (NOT "Amy McNeill") |
| **Emily's Ex-Attorney** | Jennifer Barnes (P55406) | Barnes Law Firm PLLC, 880 Jefferson St Ste B, Muskegon, MI 49440 — **WITHDREW** |
| **FOC** | Pamela Rusco | 990 Terrace St, Muskegon, MI 49442 |
| **Ronald Berry** | NON-ATTORNEY | Emily's domestic partner. No bar number. No "Esq." Related to Cavan Berry (McNeill's husband). Never was Emily's attorney. |

---

## Anti-Hallucination Protocol

1. **Never fabricate names, bar numbers, or evidence.** If unknown → insert `[UNKNOWN — VERIFY]`. Never guess.
2. **Every statistic MUST trace to a DB query** — cite the table, column, and WHERE clause. No rounding up, no extrapolation.
3. **Fabricated alienation percentages NEVER EXISTED.** Prior sessions hallucinated pseudo-scientific metrics. Purge on sight.
4. **Fabricated Berry family members NEVER EXISTED.** The only Berry is Ronald Berry (non-attorney). Any other Berry name is a hallucination to purge.
5. **DB-first before any placeholder.** Query `litigation_context.db` → search filesystem → check `COMPLETE_FILING_DATA_SUMMARY.txt` → only THEN insert a placeholder with specific acquisition instructions.

---

## Cross-Wiring Map

Brains do not operate in isolation. These are the primary cross-wire connections:

```
Ω1  (Litigation) ←——→ Ω4  (Rules)       Claims require rule citations
Ω1  (Litigation) ←——→ Ω10 (Filing)      Strategy drives filing assembly
Ω2  (Evidence)   ←——→ Ω6  (Timeline)    Evidence feeds chronology construction
Ω2  (Evidence)   ←——→ Ω9  (Witness)     Witnesses authenticate evidence
Ω3  (Forms)      ←——→ Ω10 (Filing)      Form selection drives packet structure
Ω4  (Rules)      ←——→ Ω3  (Forms)       Rules mandate which forms to use
Ω5  (Adversary)  ←——→ Ω7  (Judicial)    Adversary conduct links to judicial bias
Ω5  (Adversary)  ←——→ Ω9  (Witness)     Adversary patterns inform impeachment
Ω8  (Financial)  ←——→ Ω1  (Litigation)  Financial harm supports damage claims
Ω8  (Financial)  ←——→ Ω10 (Filing)      Cost tracking feeds fee waiver motions
Ω11 (Agent)      ←——→ ALL               Agent fleet serves every brain
Ω12 (Context)    ←——→ ALL               Session memory persists across all brains
```

**Convergence pattern:** When a filing is assembled (Ω10), it pulls claims from Ω1, evidence from Ω2, forms from Ω3, citations from Ω4, timeline from Ω6, financial data from Ω8, and witness lists from Ω9. The agent brain (Ω11) orchestrates the pull. Context brain (Ω12) ensures nothing is re-derived unnecessarily across sessions.

---

## Autonomous Activation Protocol

### Phase 1 — Boot
1. Load all 12 brain reference files from `references/`.
2. Verify `litigation_context.db` connectivity — run `PRAGMA table_info()` on each brain's primary tables.
3. Cross-wire: confirm each brain's output tables are accessible to its dependent brains.
4. Health check: report any missing tables, empty critical columns, or stale data (>30 days without update).

### Phase 2 — Gap Detection
1. Query each brain for completeness against its own quality gates (defined in each brain's reference file).
2. Aggregate gaps into a unified gap registry with severity (CRITICAL / HIGH / MEDIUM / LOW).
3. Classify gaps: `MISSING_DATA` | `STALE_DATA` | `INCOMPLETE_ANALYSIS` | `NO_EXHIBIT` | `NO_CITATION`.
4. Generate acquisition tasks for each gap with specific instructions (what to find, where to look, which drive/table).

### Phase 3 — Agent Dispatch
1. Route each acquisition task to the appropriate agent from the 28-agent fleet (see `agent-activation.instructions.md`).
2. Respect concurrency limits: max 3 background agents, 0.5s cooldown, checkpoint every 3 completions.
3. Monitor agent results — on completion, read results immediately (before context compaction clears them).

### Phase 4 — Convergence
1. Re-run gap detection after all dispatched agents complete.
2. If new gaps remain → iterate (max 3 convergence cycles to prevent infinite loops).
3. On PASS: generate convergence report with brain-by-brain status.
4. On BLOCKED: emit acquisition task list for manual resolution with specific file/table/drive targets.

---

## Python Kernel Scripts

Reference implementations in `scripts/`. Execute with `python <script> --help` for usage.

| Script | Purpose |
|--------|---------|
| `omega_kernel.py` | Master orchestrator — loads all 12 brains, routes queries to correct brain(s), merges results |
| `omega_boot.py` | Startup sequence — DB verification, brain file loading, cross-wire health check |
| `omega_health.py` | System health dashboard — DB connectivity, table row counts, data staleness detection |
| `omega_gap_detector.py` | Gap analysis across all 12 brains — outputs gap registry with severity and acquisition tasks |
| `omega_activator.py` | Autonomous agent dispatch — routes gaps to fleet agents, monitors completion, checkpoints |
| `omega_briefing.py` | Per-lane intelligence briefings — generates situation report for each of the 6 case lanes |
| `omega_neo4j_export.py` | Neo4j Bloom export — generates CSV nodes/edges for graph visualization of cross-brain relationships |

**Execution safety:** All scripts set `PYTHONUTF8=1`, use `managed_db()` for DB access, and never run from repo root (shadow module protection). Run from the `scripts/` directory or use `safe_shell.py run`.

---

## Quality Gates

Before declaring OMEGA-INFINITY operational, verify:

- [ ] All 12 brain reference files exist in `references/` and are ≥15KB each
- [ ] All DB tables referenced in the brain module map actually exist in `litigation_context.db`
- [ ] Party identity in every generated document matches the canonical table above
- [ ] No hardcoded statistics anywhere — all counts come from live `SELECT COUNT(*)` queries
- [ ] Python scripts in `scripts/` pass `--help` test (non-zero exit = broken)
- [ ] Cross-wiring map connections are bidirectional (if Ω1→Ω4, then Ω4→Ω1)
- [ ] Gap detector covers all 6 lanes (not just Lane A)
- [ ] Neo4j export produces valid CSV importable by `neo4j-admin import`
- [ ] No fabricated names: grep for hallucinated Berry names, wrong McNeill first name → zero hits
- [ ] No fabricated scores: grep for hallucinated alienation percentages → zero hits

---

## Database Entry Points

Central DB: `litigation_context.db` (~10GB, 790+ tables). Always verify schema before querying:

```sql
PRAGMA busy_timeout = 60000;
PRAGMA journal_mode = WAL;
PRAGMA cache_size = -32000;
-- Verify a table before querying:
PRAGMA table_info(table_name);
```

Jurisdiction DBs in `databases/`:

| Database | Lane | Purpose |
|----------|------|---------|
| `lane_A_custody.db` | A | Custody-specific claims and evidence |
| `lane_B_housing.db` | B | Shady Oaks housing/title data |
| `lane_C_convergence.db` | C | Cross-lane convergence data |
| `lane_D_ppo.db` | D | PPO-specific records |
| `lane_E_misconduct.db` | E | Judicial misconduct findings |
| `lane_F_appellate.db` | F | Appellate record and authorities |
| `court_forms.db` | ALL | Michigan SCAO form intelligence |

---

> **This is a boot loader.** The intelligence lives in the 12 brain files. Load them. Cross-wire them. Route queries. Detect gaps. Dispatch agents. Converge. File.
