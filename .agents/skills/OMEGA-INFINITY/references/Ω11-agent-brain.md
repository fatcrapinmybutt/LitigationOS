# Ω11 Agent Fleet Brain — OMEGA-INFINITY Reference
> Module 11 of 12 · Cognitive Litigation Kernel v4.0
> Case: Pigors v Watson · 14th Circuit · Muskegon County

## Purpose

Govern the 155+ agent fleet: architecture, orchestration, spawning decisions, pipeline phase execution, EAGAIN prevention, and MCP server coordination. This brain is the control plane for all autonomous operations.

---

## 1. Fleet Architecture

### 1.1 Five Fleet Categories

```
┌─────────────────────────────────────────────────────────┐
│                   AGENT FLEET (155+)                    │
├───────────────┬──────┬──────────────────────────────────┤
│   CATEGORY    │ COUNT│        SCOPE                     │
├───────────────┼──────┼──────────────────────────────────┤
│ Delta9        │  56  │ Core pipeline (I/O + Intel)      │
│ Delta999      │  12  │ Advanced engines                 │
│ Copilot       │  64  │ .copilot/agents/ definitions     │
│ Superpower    │  13  │ Cross-cutting orchestration      │
│ Convergence   │  10  │ Phase 5-6 hardening              │
├───────────────┼──────┼──────────────────────────────────┤
│ TOTAL         │ 155+ │ Unified via Agent9999 base class │
└───────────────┴──────┴──────────────────────────────────┘
```

### 1.2 Delta9 Pipeline Agents (A01-L08)

Two parallel lanes converge:

**Lane 1 — I/O (Tiers 1-3): A01-A12**
| Agent | Phase | Function |
|-------|-------|----------|
| A01-A04 | Tier 1: Indexing | Drive scanning, file inventory, manifest generation |
| A05-A08 | Tier 2: Dedup | Content-based deduplication, cluster analysis |
| A09-A12 | Tier 3: Extraction | PDF/DOCX text extraction, OCR, atomization |

**Lane 2 — Intelligence (Tiers J/K/L): J01-L08**
| Agent | Phase | Function |
|-------|-------|----------|
| J01-J04 | Tier J: Judicial | Judge profiling, bias analysis, ruling patterns |
| K01-K04 | Tier K: Case Intel | Case strategy, adversary modeling, pattern detection |
| L01-L08 | Tier L: Legal Analysis | Rule audit, authority validation, gap analysis |

**Convergence: F01-F06**
| Agent | Function |
|-------|----------|
| F01-F02 | Filing assembly, brief generation |
| F03-F04 | Brain feed construction, knowledge merge |
| F05-F06 | Graph build, certification, CyclePack |

### 1.3 Delta999 Advanced Engines

| Engine | Module | Function |
|--------|--------|----------|
| Classifier | `phase3_classify.py` | Document classification via MEEK signals |
| Validator | `filing_compliance_auditor.py` | Filing compliance validation |
| Brief Engine | `filing_hardener.py` | Brief strengthening and hardening |
| Opposing Engine | `adversary_modeler.py` | Adversary strategy modeling |
| Settlement Engine | — | Settlement analysis |
| Assembly Engine | — | Filing package assembly |
| Deadline Engine | — | Deadline tracking and urgency scoring |
| DB Lock Manager | `db_lock_manager.py` | SQLite WAL concurrency control |
| Authority Validator | `authority_chain_validator.py` | Citation chain verification |
| Evidence Scanner | `evidence_vehicle_scanner.py` | Evidence-to-lane routing via MEEK |
| Court Form Agent | `court_form_agent.py` | SCAO form intelligence |
| XP System | `agent_xp.py` | Agent experience tracking |

### 1.4 Agent Contract

Every agent inherits from `Agent9999` in `agents/agent_base.py`:

```python
class Agent9999:
    def run(self) -> AgentResult:
        """Execute agent's primary function."""
        ...

@dataclass
class AgentResult:
    agent_id: str          # Unique agent identifier
    status: str            # SUCCESS | FATAL | CRASH
    stats: dict            # items_processed, items_failed, duration, etc.
```

**Status definitions:**
- `SUCCESS` — Agent completed without fatal errors. Check stats for partial failures.
- `FATAL` — Unrecoverable error. Agent cannot proceed. Escalate to orchestrator.
- `CRASH` — Unexpected exception. Checkpoint data may exist for resume.

---

## 2. Active OMEGA v2.0 Agents (28)

### 2.1 Filing & Court Operations (7)

| Agent | File | Replaces | Use When |
|-------|------|----------|----------|
| **filing-forge-master** | filing-forge-master.agent.md | pre-filing-qa, filing-countdown, exhibit-formatter, service-tracker | Filing assembly, QA, Bates stamps, service tracking |
| **omega-litigation-commander** | omega-litigation-commander.agent.md | michigan-litigation-orchestrator | Complex multi-step filing workflows |
| **court-form-finder** | court-form-finder.agent.md | (original) | Michigan SCAO form identification |
| **appellate-record-builder** | appellate-record-builder.agent.md | (new) | COA/MSC record assembly, appendices |
| **contempt-prosecutor** | contempt-prosecutor.agent.md | (new) | Contempt motions, show cause |
| **garnishment-specialist** | garnishment-specialist.agent.md | (new) | Post-judgment garnishment |
| **post-judgment-enforcer** | post-judgment-enforcer.agent.md | (new) | Post-judgment enforcement |

### 2.2 Legal Research & Analysis (6)

| Agent | File | Use When |
|-------|------|----------|
| **timeline-forensics** | timeline-forensics.agent.md | Transcript analysis, chronology construction |
| **court-order-tracker** | court-order-tracker.agent.md | Track compliance with court orders |
| **damages-calculator** | damages-calculator.agent.md | Calculate damages, costs, mileage |
| **case-strategy-architect** | case-strategy-architect.agent.md | Litigation strategy and prioritization |
| **settlement-analyzer** | settlement-analyzer.agent.md | Settlement evaluation |
| **summary-judgment** | summary-judgment.agent.md | MSJ/SJ motions |

### 2.3 Evidence & Investigation (6)

| Agent | File | Use When |
|-------|------|----------|
| **evidence-warfare-commander** | evidence-warfare-commander.agent.md | Evidence triage, gap analysis, impeachment |
| **evidence-vehicle-scanner** | evidence-vehicle-scanner.agent.md | PDF scanning, MEEK lane routing |
| **evidence-authentication** | evidence-authentication.agent.md | Chain of custody, admissibility |
| **parental-alienation-detector** | parental-alienation-detector.agent.md | Alienation indicator documentation |
| **expert-witness-manager** | expert-witness-manager.agent.md | Expert selection, Daubert prep |
| **subpoena-engine** | subpoena-engine.agent.md | Subpoena drafting and tracking |

### 2.4 Judicial Accountability (2)

| Agent | File | Use When |
|-------|------|----------|
| **judicial-accountability-engine** | judicial-accountability-engine.agent.md | JTC complaints, misconduct documentation |
| **judicial-recusal-engine** | judicial-recusal-engine.agent.md | MCR 2.003 disqualification, bias documentation |

### 2.5 Family Law Specialized (4)

| Agent | File | Use When |
|-------|------|----------|
| **family-law-guardian** | family-law-guardian.agent.md | Custody, parenting time, GAL motions |
| **affidavit-chronology-builder** | affidavit-chronology-builder.agent.md | Affidavit mining, chronological narrative |
| **motion-practice** | motion-practice.agent.md | Draft/review any motion type |
| **trial-preparation** | trial-preparation.agent.md | Witness lists, exhibit lists, trial briefs |

### 2.6 System & Fleet Management (3)

| Agent | File | Use When |
|-------|------|----------|
| **omega-dedup** | omega-dedup.agent.md | Content-based dedup (NO hashing — peek inside) |
| **self-evolving-fleet-manager** | self-evolving-fleet-manager.agent.md | Fleet monitoring, upgrade, evolution |
| **compliance-auditor** | compliance-auditor.agent.md | PII redaction, filing compliance |

All agent definitions located at: `C:\Users\andre\LitigationOS\.agents\agents\`

---

## 3. OMEGA Skill Tiers (1,382 Skills)

### 3.1 Tier Architecture

```
TIER 0 — SUPREME (1 skill):
  └─ OMEGA-LITIGATION-SUPREME (67 fused skills, 12 modules)
      Route ALL litigation tasks here FIRST.

TIER 1 — CORE LITIGATION (3 skills):
  ├─ OMEGA-EVIDENCE (10 fused)
  ├─ OMEGA-RESEARCH (12 fused)
  └─ OMEGA-LITIGATION (8 fused — deprecated, use SUPREME)

TIER 2 — AGENT INTELLIGENCE (3 skills):
  ├─ OMEGA-AGENT-ARCHITECT (21 fused)
  ├─ OMEGA-ORCHESTRATOR (17 fused)
  └─ OMEGA-MEMORY (13 fused)

TIER 3 — ENGINEERING (3 skills):
  ├─ OMEGA-CODE (41 fused)
  ├─ OMEGA-DATA (13 fused)
  └─ OMEGA-MCP (13 fused)

TIER 4 — OPERATIONS (3 skills):
  ├─ OMEGA-SECURITY (29 fused)
  ├─ OMEGA-DEVOPS (23 fused)
  └─ OMEGA-WRITING (17 fused)

META — COMPOSITE AGENTS (3):
  ├─ OMEGA-ARCHITECT (Agent + Orchestrator + MCP)
  ├─ OMEGA-ENGINEER (Code + Data + Security)
  └─ OMEGA-SENTINEL (Memory + DevOps + Writing)
```

### 3.2 Skill Location

All skills in: `C:\Users\andre\LitigationOS\.agents\skills\`

Each skill directory contains `SKILL.md` and optional supporting files (modules, references, gotchas).

---

## 4. Pipeline Phase Architecture (19 Phases)

### 4.1 Phase Execution Order

| Phase | Module | Description | Status |
|-------|--------|-------------|--------|
| 0.5 | `phase0_5_drive_ingest.py` | Full multi-drive evidence scan | pending |
| 1.0 | `phase1_inventory.py` | File inventory and manifest | — |
| 2.0 | `phase2_dedup.py` | Content-based deduplication | — |
| 3.0 | `phase3_classify.py` | Lane classification via MEEK signals | — |
| 4a | `phase4a_pdf_extract.py` | PDF text extraction and OCR | — |
| 4b | `phase4b_docx_extract.py` | DOCX text extraction | — |
| 4c | `phase4c_structured_extract.py` | Structured data extraction | — |
| 4d | `phase4d_atomize.py` | Document atomization | — |
| 4e | `phase4e_archive_extract.py` | Archive extraction (ZIP, etc.) | — |
| 5.0 | `phase5_brain_feed.py` | LEXOS Brain Feed (50 micro-brains, 8 categories) | — |
| 6.0 | `phase6_gap_analysis.py` | EGCP gap scoring per legal action | — |
| 7a | `phase7a_graph_delta.py` | Graph delta computation | — |
| 7b | `phase7b_synthesis_merge.py` | Synthesis merge across sources | — |
| 7c | `phase7c_knowledge_merge.py` | Knowledge graph merge | — |
| 8.0 | `phase8_litigation_refresh.py` | Litigation context DB refresh | — |
| 9.0 | `phase9_mcp_ingest.py` | MCP server data ingest | — |
| 10 | `phase10_judicial_analysis.py` | Judicial analysis and profiling | — |
| 11 | `phase11_legal_action_discovery.py` | Legal action discovery | — |
| 12 | `phase12_rule_audit.py` | Rule audit and compliance check | — |
| 13 | `phase13_refinement.py` | Filing refinement | — |
| 14 | `phase14_finalize.py` | Finalization | — |
| 15 | `phase15_validation.py` | Full validation pass | — |
| 16 | `phase16_desktop.py` | Desktop app offload | — |

### 4.2 Pipeline Registry Status

Track via `pipeline_registry` table:

```sql
SELECT phase_id, phase_name, phase_number, status,
       items_total, items_processed, items_failed,
       last_run_start, last_run_end
FROM pipeline_registry
ORDER BY phase_number;
```

Current active pipelines (from DB):
- `ocr_mega_pipeline` — status: running
- `json_harvest_pipeline` — status: partial
- `ocr_crosswire` — status: completed
- `evidence_atom_extraction` — status: completed
- `context_persistence` — status: completed
- `albert_evidence_catalog` — status: completed
- `perjury_mining` — status: completed

### 4.3 Pipeline Execution

```powershell
# Full pipeline
python 00_SYSTEM\pipeline\run_omega_pipeline.py

# Phase range
python 00_SYSTEM\pipeline\run_omega_pipeline.py --start-phase 4a --end-phase 7c

# Single phase
python 00_SYSTEM\pipeline\phase3_classify.py

# Dry run
python 00_SYSTEM\pipeline\run_omega_pipeline.py --dry-run

# Agent orchestrator
python -m agents.agent_orchestrator               # Full fleet
python -m agents.agent_orchestrator --tier J       # Single tier
python -m agents.agent_orchestrator --agent J01    # Single agent
```

---

## 5. Orchestration via Copilot Task Tool

### 5.1 Agent Types Available

| Type | Model | Pipes | Use Case |
|------|-------|-------|----------|
| `explore` | Haiku | Isolated | Codebase exploration, file search, quick analysis |
| `task` | Haiku | Isolated | Builds, tests, scripts — brief summary on success |
| `general-purpose` | Sonnet | Isolated | Complex multi-step work, full toolset |
| `code-review` | — | Isolated | Code review with high signal-to-noise |
| Custom agents (28) | Varies | Isolated | Specialized litigation operations |

### 5.2 Agent Spawning Decision Tree

```
NEED: Run a command?
  ├─ Non-interactive → MCP exec_command (ZERO pipes, unlimited)
  └─ Interactive → PowerShell (LAST RESORT, max 2)

NEED: Explore codebase?
  └─ task(explore) → isolated pipes, fast, safe

NEED: Complex multi-step work?
  └─ task(general-purpose) → full Sonnet reasoning

NEED: Litigation-specific task?
  └─ task([custom-agent]) → specialized knowledge

NEED: Parallel investigation?
  └─ Launch up to 3 explore agents simultaneously

NEVER: Launch more than 3 agents concurrently
NEVER: Mix >2 shells with agents
ALWAYS: Read agent results immediately on completion
ALWAYS: Checkpoint every 3 agent completions
```

### 5.3 Background Agent Lifecycle

```
SPAWN → RUNNING → COMPLETED → READ → (optionally WRITE follow-up → IDLE → WRITE → RUNNING...)

Key rules:
1. read_agent IMMEDIATELY on completion notification
2. Cache results in session SQL if critical (compaction protection)
3. write_agent for iterative refinement (agent retains context)
4. Max 3 concurrent RUNNING agents
5. 0.5s cooldown between spawns
6. Up to 3 agents in one tool call (isolated pipes)
```

---

## 6. EAGAIN Prevention Protocol

### 6.1 The Three Pipe Categories

| Category | Tools | Risk | Budget |
|----------|-------|------|--------|
| **Zero-pipe** | view, edit, create, grep, glob, sql | ZERO | Unlimited |
| **Isolated-pipe** | task(explore), task(task), task(general-purpose) | Contained | 3 concurrent |
| **Shared-pipe** | powershell | CRITICAL | 2 concurrent |

### 6.2 Command Routing Hierarchy (v3.0)

```
PRIORITY 1: Zero-pipe tools ──── UNLIMITED, always prefer
PRIORITY 2: MCP exec_command ─── UNLIMITED, zero pipes
PRIORITY 3: Task agents ──────── 3 max, isolated pipes
PRIORITY 4: PowerShell ────────── 2 max, shared pipes (LAST RESORT)
```

### 6.3 Concurrency Limits

| Resource | Max | Cooldown | Notes |
|----------|-----|----------|-------|
| Background agents | 3 | 0.5s | Isolated pipes — safe to parallelize |
| Async shells | 2 | 2.0s | Shared pipes — ONLY EAGAIN vector |
| MCP commands | Unlimited | 0s | subprocess.run() — no pipe risk |
| Combined total | 5 | — | 3 agents + 2 shells absolute max |

### 6.4 Dynamic Throttle Levels

| Level | Name | Shells | Agents | MCP | Trigger |
|-------|------|--------|--------|-----|---------|
| L0 | MAXIMUM | 2 | 4 | ∞ | Normal operation |
| L1 | ELEVATED | 1 | 4 | ∞ | 1 shell timeout |
| L2 | WARNING | 1 | 3 | ∞ | Agent error or 2+ shell issues |
| L3 | CRITICAL | 0 | 2 | ∞ | write EAGAIN detected |
| L4 | EMERGENCY | 0 | 1 | ∞ | Multiple EAGAIN + invalid shells |
| L5 | DEAD | 0 | 0 | ∞ | Agents also failing |

MCP remains available at ALL levels — always recoverable.

### 6.5 Recovery Protocol

```
Step 1: FULL STOP — no new spawns
Step 2: list_powershell → stop ALL sessions
Step 3: list_agents → wait for completions
Step 4: Wait 3 seconds
Step 5: MCP exec_command("Write-Output 'alive'") — always works
Step 6: Test ONE shell → if works, resume at L2
Step 7: If shells dead → MCP + agents only (L3/L4)
Step 8: If agents dead → MCP-only (L5)
Step 9: If MCP dead → AUTONOMOS file-based (create scripts → user runs)
```

---

## 7. MCP Server Infrastructure

### 7.1 Three MCP Servers

| Server | Module | Purpose | Key Tools |
|--------|--------|---------|-----------|
| **command-runner** | `command_runner.py` | Shell replacement | exec_command, exec_python, exec_git, exec_pipeline_phase, system_status |
| **litigation-context** | `litigation_context_mcp/server.py` | 45 legal tools | search, filing_readiness, evidence_chain, deadline_dashboard, prefiling_qa |
| **agent-memory** | — | Persistent memory | store, retrieve, search |

### 7.2 MCP Tool Categories

| Category | Count | Key Tools |
|----------|-------|-----------|
| Core | 10 | scan_drives, ingest_pdf, bulk_ingest, search (FTS5), list_documents, get_document, get_stats |
| Filing | 8 | filing_readiness, filing_validate, filing_assemble, efiling_prep, brief_compliance, placeholder_scan |
| Evidence | 7 | evidence_chain, evidence_gaps, evidence_link, evidence_authenticate, bates_assign, exhibit_index |
| Deadline | 5 | deadline_dashboard, deadline_ics, deadline_urgency, deadline_add, deadline_update |
| Analysis | 5 | authority_index, citation_graph, impeachment_search, contradiction_find, judicial_bias_scan |
| QA | 4 | prefiling_qa, qa_sweep, signature_check, service_check |
| Backup | 3 | backup_create, backup_version, backup_report |
| Calendar | 2 | calendar_generate, calendar_sync |
| System | 1 | system_health |

All tools prefixed with `litigation_` (e.g., `litigation_deadline_dashboard`).

### 7.3 MCP Command Runner Priority Rule

```
GOOD:  exec_python("00_SYSTEM/scripts/noreply_pdf_processor.py", "--limit 50")
BAD:   powershell("python 00_SYSTEM/scripts/noreply_pdf_processor.py --limit 50")

GOOD:  exec_git("status")
BAD:   powershell("git --no-pager status")

GOOD:  exec_command("Get-ChildItem *.pdf | Measure-Object")
BAD:   powershell("Get-ChildItem *.pdf | Measure-Object")
```

---

## 8. 7-Layer Error Protocol

Every agent implements this protocol (non-negotiable):

```
LAYER 1: Try operation
  └─ Execute primary function

LAYER 2: Specific catch
  └─ Known error type → targeted recovery (retry, skip, transform)

LAYER 3: Broad catch
  └─ Unknown error → log full trace + skip item + continue batch

LAYER 4: Checkpoint
  └─ Save progress every N items → crash-resume capability

LAYER 5: Deadman switch
  └─ 120s no progress → self-diagnose → alert orchestrator

LAYER 6: Agent retry
  └─ 3× exponential backoff (1s → 2s → 4s) before FATAL

LAYER 7: Tier fallback
  └─ Orchestrator flags failure → continues other agents → reports blocked
```

---

## 9. Agent-Related DB Tables

### 9.1 Pipeline Registry

```sql
-- pipeline_registry schema
CREATE TABLE pipeline_registry (
    phase_id TEXT PRIMARY KEY,
    phase_name TEXT NOT NULL,
    phase_number REAL,
    description TEXT,
    script_path TEXT,
    depends_on TEXT,
    status TEXT DEFAULT 'pending',    -- pending, running, completed, partial, failed
    last_run_start TEXT,
    last_run_end TEXT,
    items_total INTEGER DEFAULT 0,
    items_processed INTEGER DEFAULT 0,
    items_failed INTEGER DEFAULT 0,
    error_message TEXT,
    last_session_id TEXT,
    created_at TEXT DEFAULT datetime('now'),
    updated_at TEXT DEFAULT datetime('now')
);
```

### 9.2 Master Todos

```sql
-- master_todos schema
CREATE TABLE master_todos (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT,
    status TEXT DEFAULT 'pending',     -- pending, in_progress, done, blocked
    priority INTEGER DEFAULT 5,        -- 1=highest, 10=lowest
    deadline TEXT,
    lane TEXT,                         -- Case lane (A-F)
    assigned_agent TEXT,               -- Agent responsible
    depends_on TEXT,                   -- Dependencies
    blocking_reason TEXT,
    created_by_session TEXT,
    completed_by_session TEXT,
    created_at TEXT DEFAULT datetime('now'),
    started_at TEXT,
    completed_at TEXT,
    error_log TEXT
);
```

### 9.3 Agent Data (master_index.db)

Located at `00_SYSTEM/pipeline/agents/master_index.db`. Schema includes:
- `files` — Indexed file registry
- `ready_queue` — Items queued for processing
- `dedup_clusters` — Deduplication cluster results
- `zip_contents` — Archive content manifests
- `atoms` — Atomized document content
- `judicial_findings` — Judicial analysis results
- `action_scores` — Legal action scoring
- `agent_log` — Agent execution history

### 9.4 System Health Log

```sql
-- system_health_log schema
CREATE TABLE system_health_log (
    id INTEGER PRIMARY KEY,
    engine_name TEXT NOT NULL,
    status TEXT DEFAULT 'UNKNOWN',
    latency_ms REAL,
    last_check TEXT DEFAULT datetime('now'),
    error_message TEXT,
    version TEXT
);
```

---

## Key DB Queries

```sql
-- Q1: Pipeline status dashboard
SELECT phase_id, phase_name, status, items_processed, items_failed,
       last_run_start, last_run_end
FROM pipeline_registry
ORDER BY phase_number;

-- Q2: Active todos by priority
SELECT id, title, status, priority, lane, assigned_agent, deadline
FROM master_todos
WHERE status IN ('pending', 'in_progress')
ORDER BY priority ASC, deadline ASC;

-- Q3: System health check
SELECT engine_name, status, latency_ms, last_check, error_message
FROM system_health_log
ORDER BY last_check DESC;

-- Q4: Blocked items analysis
SELECT id, title, blocking_reason, depends_on, lane
FROM master_todos
WHERE status = 'blocked';

-- Q5: Pipeline completion rate
SELECT
    (SELECT COUNT(*) FROM pipeline_registry WHERE status = 'completed') AS completed,
    (SELECT COUNT(*) FROM pipeline_registry WHERE status = 'running') AS running,
    (SELECT COUNT(*) FROM pipeline_registry WHERE status = 'pending') AS pending,
    (SELECT COUNT(*) FROM pipeline_registry) AS total;
```

---

## 10. MEEK Signal Classification

### 10.1 Signal Definitions

MEEK signals are compiled regexes in `config.py` → `MEEK_SIGNALS` dict. They route evidence to case lanes.

| Signal | Lane | Pattern Focus |
|--------|------|---------------|
| MEEK1 | B (Housing) | Shady Oaks, landlord, property, lease, code violation |
| MEEK2 | A (Custody) | Custody, parenting time, visitation, L.D.W., child |
| MEEK3 | D (PPO) | PPO, protective order, stalking, harassment |
| MEEK4 | E (Misconduct) | Judge, McNeill, judicial, bias, misconduct, JTC |
| MEEK5 | F (Appellate) | Appeal, COA, MSC, appellate, affirm, reverse |

**Detection priority:** E → D → F → C → A → B

A `LaneCrossContaminationError` (non-fatal, skip-item) is raised when evidence from the wrong lane is detected.

---

## 11. Shadow Module Safety

### 11.1 The Problem

The repo root contains 22 files that shadow Python stdlib/third-party modules:
`json.py`, `typing.py`, `tokenize.py`, `numpy.py`, `pandas.py`, and 17 others.

### 11.2 The Rule

**NEVER set CWD to the repo root when running Python.** Use `safe_run()` or set CWD to the script's own directory.

```powershell
# Load agent profile for safe wrappers
. C:\Users\andre\LitigationOS\00_SYSTEM\tools\agent_profile.ps1
srun script.py --arg     # Safe run (avoids shadow modules)
spy "print(1+1)"          # Safe inline Python
sshadow                   # Shadow module audit
```

---

## Cross-Wiring Points

| Target Brain | Connection | Data Flow |
|-------------|-----------|-----------|
| **Ω9 Witness Brain** | subpoena-engine, evidence-warfare-commander | Agents execute witness operations defined by witness brain |
| **Ω10 Filing Brain** | filing-forge-master, compliance-auditor | Agents execute filing pipeline stages defined by filing brain |
| **Ω12 Context Brain** | Session persistence, agent result caching | Agent results flow into context persistence; session continuity survives restarts |
| **Ω1 Evidence Brain** | evidence-vehicle-scanner, evidence-authentication | Evidence agents process materials governed by evidence brain |
| **Ω6 Gap Brain** | gap analysis drives acquisition tasks | master_todos populated by gap analysis agents |

---

## Anti-Hallucination Rules

- **NEVER claim an agent exists that is not in the registry.** Check `.agents/agents/` for current list.
- **NEVER fabricate pipeline phase results.** Query `pipeline_registry` for actual status.
- **NEVER exceed concurrency limits.** 3 agents + 2 shells = 5 max. MCP unlimited.
- **NEVER hardcode DB statistics.** Run queries for current counts.
- **NEVER skip EAGAIN prevention.** Check list_powershell and list_agents BEFORE spawning.
