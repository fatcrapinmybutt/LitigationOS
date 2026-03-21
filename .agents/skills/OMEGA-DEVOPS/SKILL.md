---
name: OMEGA-DEVOPS
description: >-
  Comprehensive DevOps skill for LitigationOS covering git workflow with
  commit conventions, build and test (975+ pytest suite), 16-phase pipeline
  operations, automated backup to I:\ drive, system health monitoring via
  startup hooks, release engineering with Inno Setup, database migration
  management, observability with progress logging, and EAGAIN prevention
  protocol for shell/agent session management. Invoke for ANY build, test,
  deploy, backup, monitoring, pipeline operation, or system health task.
category: operations
version: "2.0.0"
triggers:
  - git
  - CI/CD
  - deploy
  - monitor
  - backup
  - system health
  - build
  - test
  - release
  - installer
  - migration
  - pipeline
  - pytest
  - shell management
  - EAGAIN
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
  - run_omega_pipeline.py
  - copilot_startup_hook.py
  - safe_shell.py
  - db_lock_manager.py
  - litigation_context.db
metadata:
  tier: 4
  fused_skills: 23
  author: andrew-pigors + copilot-omega
  forge_date: 2026-03-21
---

# ⚙️ OMEGA-DEVOPS — Battle-Hardened Operations Engine

> **The operational backbone that keeps a 10 GB+ litigation system running across
> 6 drives, 155+ agents, 16 pipeline phases, and 975+ tests — without a single
> dropped deadline or lost evidence file.** Built from 200+ session crashes and
> hard-won EAGAIN recovery protocols.

---

## Forged from 23 Individual Skills

| # | Source Skill | Absorbed Capability |
|---|-------------|-------------------|
| 1 | git-advanced-workflows | Branch strategies, rebase, cherry-pick |
| 2 | git-pr-workflows-git-workflow | PR lifecycle management |
| 3 | git-pr-workflows-onboard | Repository onboarding patterns |
| 4 | git-pr-workflows-pr-enhance | PR quality improvement |
| 5 | git-pushing | Safe push protocols |
| 6 | github-actions-templates | CI/CD workflow templates |
| 7 | github-automation | Repository automation |
| 8 | github-workflow-automation | Workflow orchestration |
| 9 | gitlab-ci-patterns | CI pipeline patterns |
| 10 | gitops-workflow | GitOps deployment patterns |
| 11 | deployment-engineer | Deployment strategy and execution |
| 12 | deployment-pipeline-design | Pipeline architecture |
| 13 | deployment-procedures | Release procedures |
| 14 | deployment-validation-config-validate | Post-deploy validation |
| 15 | docker-expert | Containerization knowledge |
| 16 | observability-engineer | System observability design |
| 17 | observability-monitoring-monitor-setup | Monitoring infrastructure |
| 18 | observability-monitoring-slo-implement | Service level objectives |
| 19 | grafana-dashboards | Dashboard design and metrics |
| 20 | prometheus-configuration | Metrics collection |
| 21 | helm-chart-scaffolding | Package management patterns |
| 22 | terraform-specialist | Infrastructure as code |
| 23 | on-call-handoff-patterns | Operational handoff protocols |

---

## When to Apply

- **Building the project** — `pip install -e ".[dev]"`, pytest execution, syntax checks
- **Running tests** — full pytest suite, single file tests, coverage reports
- **Pipeline operations** — 16-phase pipeline execution, phase ranges, dry runs
- **Git operations** — commits, branches, PRs, diffs, status checks
- **Backup needed** — pre-filing snapshot, daily backup, disaster recovery
- **System health check** — startup hook, DB status, deadline urgency, drive space
- **Release preparation** — version bump, changelog, Inno Setup installer build
- **Database migration** — schema changes, column verification, backward compatibility
- **Shell session issues** — EAGAIN errors, invalid shell IDs, session pool exhaustion
- **Autonomous run management** — progress logging, checkpoint/resume, agent fleet orchestration

---

## Decision Tree

```
DevOps task received
│
├─ Is it source control? ────────────────────────────── → O1: Git Workflow
│   ├─ Commit? → Stage → commit with trailer → push
│   ├─ Branch? → Feature branch from main
│   ├─ PR? → Create with description → review → merge
│   └─ Always: --no-pager on every git command
│
├─ Is it build/test? ───────────────────────────────── → O2: Build & Test
│   ├─ Full suite? → pip install -e ".[dev]" && pytest tests/ -q
│   ├─ Single file? → pytest tests/test_X.py -v
│   ├─ Coverage? → pytest tests/ --cov=litigationos
│   └─ CRITICAL: Never CWD at repo root (shadow modules)
│
├─ Is it pipeline? ─────────────────────────────────── → O3: Pipeline Operations
│   ├─ Full run? → python run_omega_pipeline.py
│   ├─ Phase range? → --start-phase 4a --end-phase 7c
│   ├─ Single phase? → python phase3_classify.py
│   └─ Dry run? → --dry-run --create-snapshot
│
├─ Is it backup? ───────────────────────────────────── → O4: Backup & Recovery
│   ├─ Pre-filing? → Full snapshot with SHA-256 manifest
│   ├─ Daily? → Incremental to I:\ drive
│   ├─ DB backup? → WAL checkpoint → copy → verify
│   └─ Recovery? → Integrity check → restore → validate
│
├─ Is it monitoring? ──────────────────────────────── → O5: System Health
│   ├─ Startup? → copilot_startup_hook.py --file
│   ├─ Status? → Read STARTUP_REPORT.md
│   └─ Deadline? → Urgency scoring → countdown display
│
├─ Is it a release? ───────────────────────────────── → O6: Release Engineering
│   ├─ Version? → Update pyproject.toml + changelog
│   ├─ Installer? → Inno Setup compilation
│   └─ Package? → pip build → verify → distribute
│
├─ Is it DB migration? ────────────────────────────── → O7: Database Migrations
│   ├─ Schema check? → PRAGMA table_info(table_name)
│   ├─ New table? → CREATE IF NOT EXISTS + migration script
│   └─ Column change? → Migration script + backward compat
│
├─ Is it observability? ───────────────────────────── → O8: Observability
│   ├─ Progress? → Write to PROGRESS_LOG.md
│   ├─ Tracking? → SQL todos table updates
│   └─ Health? → system_status() check
│
└─ Is it session management? ──────────────────────── → O9: EAGAIN Prevention
    ├─ Shell issue? → list → stop all → wait → test one
    ├─ Agent budget? → list_agents → verify < 4 running
    └─ Routing? → MCP first → agents → shells (last resort)
```

---

## O1: Git Workflow — Disciplined Source Control

### Branch Strategy
```
main                    ← stable, always deployable
  └─ feature/xxx        ← feature branches (short-lived)
  └─ fix/xxx            ← bug fix branches
  └─ release/x.y.z      ← release preparation
```

### Commit Convention (MANDATORY)

Every commit MUST include the Co-authored-by trailer:

```
<type>(<scope>): <description>

<optional body>

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `build`

### Git Command Rules

```powershell
# ✅ ALWAYS use --no-pager
git --no-pager status
git --no-pager diff --stat
git --no-pager log --oneline -20
git --no-pager show HEAD -- file.py

# ✅ Chain related commands
git --no-pager status && git --no-pager diff --stat

# ❌ NEVER use pager (hangs in non-interactive)
git log              # opens less/more → hangs
git diff             # unbounded output → EAGAIN risk

# ❌ NEVER run unbounded
git --no-pager log   # all history → pipe overflow
git --no-pager diff  # all changes → output flood
```

### Pre-Commit Checklist
1. `git --no-pager status` — verify only intended files staged
2. `git --no-pager diff --cached --stat` — review staged changes
3. Run affected tests — `pytest tests/test_affected.py -q`
4. Verify no PII in staged files — `grep -rn "SSN\|DOB\|REDACT" <staged files>`
5. Commit with Co-authored-by trailer

---

## O2: Build & Test — The Quality Gate

### Installation

```powershell
cd C:\Users\andre\LitigationOS\11_CODE\litigationos
pip install -e ".[dev]"     # Install with test dependencies
```

### Test Execution

```powershell
# Full suite (975+ tests — run for current count)
cd 11_CODE\litigationos && python -m pytest tests/ -q

# Single file
python -m pytest tests/test_brief_compliance.py -v

# Single function
python -m pytest tests/test_models.py::test_case -v

# With coverage
python -m pytest tests/ --cov=litigationos

# Quick syntax check (no imports — avoids shadow modules)
python C:\Users\andre\LitigationOS\00_SYSTEM\tools\safe_shell.py check file.py
```

### Shadow Module Avoidance (CRITICAL)

```
The repo root contains 22+ Python files that shadow standard library modules:
json.py, typing.py, tokenize.py, numpy.py, pandas.py, and 17 others.

RULE: NEVER set CWD to C:\Users\andre\LitigationOS\ when running Python.
ALWAYS cd into the script's own directory first, or use safe_shell.py.

✅ cd 11_CODE\litigationos && python -m pytest tests/ -q
✅ python 00_SYSTEM\tools\safe_shell.py run 00_SYSTEM\scripts\my_script.py
✅ cd 00_SYSTEM\pipeline && python run_omega_pipeline.py

❌ cd C:\Users\andre\LitigationOS && python -m pytest tests/ -q
❌ python -c "import json; print(json.__file__)"  # WILL import repo root json.py
```

### Safe Execution Toolkit

```powershell
# Dot-source the agent profile for convenience aliases
. C:\Users\andre\LitigationOS\00_SYSTEM\tools\agent_profile.ps1

sspy file1.py file2.py     # Syntax check (AST parse, no imports)
srun script.py --arg        # Safe run (avoids shadow modules)
spy "print(1+1)"            # Safe inline Python (temp file, not -c)
senv                         # Environment health check
sshadow                     # Shadow module audit
spreflight                  # Kill orphan processes + clean temp files
```

### Test Failure Response Protocol
1. Read full error output — identify failing test and assertion
2. Check if failure is pre-existing (`git stash && pytest <test> && git stash pop`)
3. If new failure — trace to your change and fix
4. If pre-existing — document in commit message, do not fix unrelated issues
5. Re-run full suite to verify fix doesn't break other tests

---

## O3: Pipeline Operations — 16-Phase Execution

### Phase Map

```
Phase 0:  Safety Snapshot (SHA-256 manifest + backup)
Phase 1:  Inventory (drive scanning, file discovery)
Phase 2:  Dedup (content-based deduplication — peek inside, not just hash)
Phase 3:  Classify (lane assignment via MEEK signals)
Phase 4a: Extract PDF (PyMuPDF text extraction)
Phase 4b: Extract DOCX (python-docx parsing)
Phase 4c: Extract Structured (CSV, JSON, DB records)
Phase 4d: Atomize (split into atomic evidence units)
Phase 4e: Archive (ZIP/RAR/7z extraction)
Phase 5:  LEXOS Brain Feed (50 micro-brains, 8 categories)
Phase 6:  Gap Analysis (EGCP scoring per legal action)
Phase 7a: Graph Delta (knowledge graph updates)
Phase 7b: Synthesis Merge (cross-evidence synthesis)
Phase 7c: Knowledge Merge (unified knowledge base)
Phase 8:  Litigation Refresh (filing readiness recalculation)
Phase 9:  MCP Ingest (tool refresh with new data)
Phase 10: Judicial Analysis (bias, pattern, consistency)
Phase 11: Legal Action Discovery (new claims from evidence)
Phase 12: Rule Audit (MCR compliance verification)
Phase 13: Refinement (evidence quality enhancement)
Phase 14: Finalization (filing package assembly)
Phase 15: Validation (pre-filing QA sweep)
Phase 16: Desktop Offload (GUI data refresh)
```

### Execution Commands

```powershell
cd 00_SYSTEM\pipeline

# Full 16-phase run
python run_omega_pipeline.py

# Phase range
python run_omega_pipeline.py --start-phase 4a --end-phase 7c

# Skip specific phases
python run_omega_pipeline.py --skip-phases 16

# Dry run (verify without executing)
python run_omega_pipeline.py --dry-run --create-snapshot

# List all phases
python run_omega_pipeline.py --list-phases

# Single phase directly
python phase3_classify.py
```

### Pipeline Validation

```powershell
# Syntax check all modules
cd 00_SYSTEM\scripts && python syntax_check.py

# Integration test phases 1-3
python integration_test_phase123.py

# Quick status
cd 00_SYSTEM\pipeline && python quick_status.py

# Full validation
python validate.py
```

### Pipeline Failure Recovery
1. Check which phase failed — review output log
2. Run that phase in isolation — `python phaseN_name.py`
3. Fix the issue — often a missing file or schema mismatch
4. Resume from the failed phase — `--start-phase N`
5. Never restart from Phase 0 unless data integrity is in question

---

## O4: Backup & Recovery — Never Lose a Filing

### Backup Architecture

```
SOURCE:    C:\Users\andre\LitigationOS\              ← active workspace
DEST:      I:\LitigationOS_Backup\                    ← backup drive
DEDUP:     I:\LitigationOS_Dedup\                     ← deduplicated files

Backup Types:
  SNAPSHOT   — full copy, pre-filing or pre-destructive-op
  INCREMENTAL — changed files only, daily
  DB_BACKUP  — WAL checkpoint + copy + integrity check
```

### Backup Protocol

```powershell
# Step 1: WAL checkpoint (flush pending writes to DB)
# Execute via Python, not inline:
# sqlite3 litigation_context.db "PRAGMA wal_checkpoint(TRUNCATE);"

# Step 2: Create SHA-256 manifest of all critical files
# python 00_SYSTEM/scripts/create_manifest.py

# Step 3: Copy to I:\ with verification
# robocopy with /MIR or custom backup script

# Step 4: Verify backup integrity
# Compare manifests, test DB opens, spot-check random files
```

### Recovery Protocol
1. **Identify scope** — which files/tables are affected?
2. **Locate backup** — find most recent intact backup on I:\
3. **Verify backup integrity** — `PRAGMA integrity_check` on DB, SHA-256 on files
4. **Restore** — copy from backup to working directory
5. **Validate** — run pipeline validation, check test suite
6. **Document** — log recovery in audit trail with before/after state

### CRITICAL RULE
**NEVER delete backups of filed court documents.** These are permanent record.
Retention: indefinite for any backup taken before a court filing.

---

## O5: System Health Monitoring — The Startup Protocol

### MANBEARPIG Startup (MANDATORY — every session)

```powershell
# Step 1: Generate startup report
python C:\Users\andre\LitigationOS\00_SYSTEM\local_model\copilot_startup_hook.py --file

# Step 2: Read report
# → view C:\Users\andre\LitigationOS\00_SYSTEM\STARTUP_REPORT.md

# Step 3: Session recall
python C:\Users\andre\LitigationOS\00_SYSTEM\local_model\session_recall.py recent

# Step 4: Jurisdiction DB check
# Verify databases/*.db files exist and are accessible
```

### Health Check Outputs

The startup report contains:
- **Separation day count** — days since separation (for deadline calculations)
- **Deadline urgency scores** — color-coded urgency for all active deadlines
- **Filing readiness** — which filings are ready, which have gaps
- **Evidence arsenal counts** — total evidence items per lane
- **System health** — DB size, table count, drive space, pipeline status
- **Recent session summaries** — what was done in last 3 sessions

### Monitoring Commands

```powershell
# DB statistics (query directly — never hardcode)
# Use: SELECT COUNT(*) FROM sqlite_master WHERE type='table';
# Use: SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size();

# Pipeline status
cd 00_SYSTEM\pipeline && python quick_status.py

# System health via MCP
# litigation_system_health()
```

---

## O6: Release Engineering — Ship It

### Version Management
- Version defined in `11_CODE/litigationos/pyproject.toml`
- Follow semantic versioning: MAJOR.MINOR.PATCH
- Tag releases: `git tag -a vX.Y.Z -m "Release X.Y.Z"`

### Build Process

```powershell
cd 11_CODE\litigationos

# Build Python package
pip install build
python -m build

# Verify package
pip install dist/litigationos-X.Y.Z-py3-none-any.whl
litigationos --version
```

### Inno Setup Installer
- Installer script in project (creates Windows .exe installer)
- Desktop shortcut creation for `litigationos` CLI
- Start menu integration
- Uninstaller with clean removal

### Release Checklist
1. [ ] All tests pass (`pytest tests/ -q`)
2. [ ] Version bumped in `pyproject.toml`
3. [ ] Changelog updated
4. [ ] Git tag created
5. [ ] Package built and verified
6. [ ] Installer compiled (if desktop release)
7. [ ] Backup created pre-release

---

## O7: Database Migrations — Schema Evolution

### Schema Verification (ALWAYS FIRST)

```sql
-- Before querying ANY table for the first time in a session:
PRAGMA table_info(table_name);

-- Check schema_reference for documented columns:
SELECT * FROM schema_reference WHERE table_name = 'claims';
```

### Known Column Corrections
These have caused crashes in past sessions — verify before using:

| Table | Wrong Column | Correct Column |
|-------|-------------|---------------|
| authority_chains | is_complete | chain_complete |
| filing_readiness | vehicle | vehicle_name |
| deadlines | deadline_date | due_date_iso |
| claims | id | claim_id |

### Migration Script Template

```python
"""Migration: add_column_to_table
Created: YYYY-MM-DD
Purpose: Add new_column to existing_table
"""
import sqlite3

def migrate(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")

    # Check if column already exists (idempotent)
    columns = [row[1] for row in conn.execute("PRAGMA table_info(existing_table)")]
    if 'new_column' not in columns:
        conn.execute("ALTER TABLE existing_table ADD COLUMN new_column TEXT DEFAULT ''")
        conn.commit()
        print("Migration applied: new_column added to existing_table")
    else:
        print("Migration skipped: new_column already exists")

    conn.close()

if __name__ == "__main__":
    migrate(r"C:\Users\andre\LitigationOS\litigation_context.db")
```

### Migration Rules
- **Always idempotent** — safe to run multiple times
- **Always check column existence** before ALTER TABLE
- **Always use WAL mode** and busy_timeout in migration scripts
- **Always backup before migration** — snapshot to I:\
- **Never drop columns** in production (SQLite doesn't support it cleanly)

---

## O8: Observability — See Everything

### Progress Logging (Autonomous Runs)

```markdown
# PROGRESS_LOG.md format:
## [TIMESTAMP] Agent/Phase Completed
- **Agent**: agent_id
- **Status**: SUCCESS/FATAL/CRASH
- **Duration**: Xs
- **Items processed**: N
- **Next**: next_agent_or_phase
```

Write to `00_SYSTEM\PROGRESS_LOG.md` after:
- Every agent completion
- Every pipeline phase completion
- Every 10 minutes during autonomous runs
- Every checkpoint/resume event

### SQL Todo Tracking

```sql
-- Update status as you work (MANDATORY):
UPDATE todos SET status = 'in_progress', updated_at = datetime('now') WHERE id = 'task-id';

-- After completion:
UPDATE todos SET status = 'done', updated_at = datetime('now') WHERE id = 'task-id';

-- Check what's ready:
SELECT t.* FROM todos t
WHERE t.status = 'pending'
AND NOT EXISTS (
    SELECT 1 FROM todo_deps td
    JOIN todos dep ON td.depends_on = dep.id
    WHERE td.todo_id = t.id AND dep.status != 'done'
);
```

### Agent Fleet Monitoring

```sql
-- Query agent_log for fleet status:
SELECT agent_id, status, start_time, end_time,
       items_processed, errors
FROM agent_log
ORDER BY start_time DESC
LIMIT 20;
```

### Checkpoint Protocol (GOAWAY/503 Protection)
- GOAWAY errors kill agents after 27-40 minutes
- **Checkpoint every 10 minutes** to SQL + filesystem
- **Checkpoint every 3 agent completions**
- Recovery: read last checkpoint → resume from that point
- Never rely on in-memory state surviving more than 20 minutes

---

## O9: EAGAIN Prevention — Session Survival

### Command Routing Hierarchy (MANDATORY)

```
PRIORITY 1: Zero-pipe tools (view/edit/create/grep/glob/sql)
  → UNLIMITED. No pipes. Always prefer.

PRIORITY 2: MCP command-runner (exec_command/exec_python/exec_git)
  → UNLIMITED. subprocess.run() — outside pipe pool.

PRIORITY 3: Task agents (explore/task/general-purpose/code-review)
  → Max 4 concurrent. ISOLATED pipes — safe to expand.

PRIORITY 4: PowerShell (async/sync shells)
  → Max 2 concurrent. SHARED pipes — LAST RESORT.
```

### Shell Session Rules

```
1. HARD LIMIT: Max 2 concurrent async shells
2. Chain commands with && — one shell, multiple commands
3. Stop completed shells IMMEDIATELY after reading output
4. Use named shellIds ("build", "test", "git1") — never auto-generated
5. Pre-flight cleanup before multi-step ops: list → stop stale → verify < 2
6. Output cap: 200 lines max per command (redirect large output to file)
```

### Agent Budget Rules

```
1. Max 4 parallel background agents (isolated pipes)
2. 0.5-second cooldown between spawns
3. Can dispatch 3 agents in one tool call
4. Agent + shell in same turn is OK (different pipe pools)
5. Checkpoint every 3 agent completions
6. Read agent results IMMEDIATELY on completion notification
```

### Recovery When EAGAIN Strikes

```
STEP 1: FULL STOP — no new shells or agents
STEP 2: list_powershell → stop ALL sessions
STEP 3: Wait 3 seconds
STEP 4: Test MCP exec_command — should always work
STEP 5: If MCP works → continue via MCP + agents (skip shells)
STEP 6: Test ONE shell → if works, resume at L2 throttle
STEP 7: If all pipes dead → MCP-only mode (still fully functional)
STEP 8: If MCP dead → AUTONOMOS file-based execution (create → user runs)
```

### Dynamic Throttle Levels

| Level | Shells | Agents | MCP | Trigger |
|-------|--------|--------|-----|---------|
| L0 MAXIMUM | 2 | 4 | ∞ | No symptoms |
| L1 ELEVATED | 1 | 4 | ∞ | 1 shell timeout |
| L2 WARNING | 1 | 3 | ∞ | Agent error or 2+ shell issues |
| L3 CRITICAL | 0 | 2 | ∞ | write EAGAIN detected |
| L4 EMERGENCY | 0 | 1 | ∞ | Multiple EAGAIN + invalid shells |
| L5 DEAD | 0 | 0 | ∞ | Agents also failing |

**MCP is ALWAYS available at every level — you are never truly stuck.**

---

## Cross-Module Integration Patterns

### O1 + O2: Pre-Commit Quality Gate
```
Code change ready
  → O2: Run affected tests (pytest -q)
  → O2: Syntax check (safe_shell.py check)
  → O1: Stage changes (git add)
  → O1: Verify staged diff (git --no-pager diff --cached)
  → O1: Commit with Co-authored-by trailer
  → O2: Run full suite to catch regressions
```

### O3 + O5: Pipeline Health Monitoring
```
Pipeline run initiated
  → O5: Check system health (startup hook)
  → O4: Create pre-run backup snapshot
  → O3: Execute pipeline phases
  → O8: Log progress after each phase
  → O5: Verify DB integrity post-run
  → O8: Update SQL todos with completion status
```

### O4 + O7: Safe Database Migration
```
Schema change needed
  → O4: Backup database to I:\
  → O7: Verify current schema (PRAGMA table_info)
  → O7: Write idempotent migration script
  → O7: Execute migration
  → O7: Verify new schema
  → O2: Run tests to validate
  → O4: Create post-migration backup
```

---

## LitigationOS-Specific Operations Invariants

1. **--no-pager on EVERY git command** — non-interactive environment
2. **Never CWD at repo root for Python** — 22+ shadow modules will corrupt imports
3. **safe_shell.py for ALL Python execution** — wraps CWD management
4. **Co-authored-by trailer on EVERY commit** — `Copilot <223556219+Copilot@users.noreply.github.com>`
5. **Checkpoint every 10 minutes** during autonomous runs — GOAWAY kills at 27-40 min
6. **PRAGMA table_info BEFORE first query** to any table — schema evolves faster than docs
7. **managed_db() for ALL DB access** — max 3 connections, WAL mode, busy_timeout=60000
8. **Backup before ANY destructive operation** — snapshot to I:\ first
9. **MCP-first command routing** — shells are last resort, not first choice
10. **Read agent results IMMEDIATELY** — context compaction erases unread results

---

## Quick Reference Card

```
╔════════════════════════════════════════════════════════════════╗
║           OMEGA-DEVOPS v2.0 — QUICK REFERENCE                  ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║  GIT (O1):                                                     ║
║    ALWAYS: --no-pager on every command                         ║
║    ALWAYS: Co-authored-by trailer on every commit              ║
║    Chain: git --no-pager status && git --no-pager diff --stat  ║
║                                                                ║
║  BUILD & TEST (O2):                                            ║
║    Install: cd 11_CODE\litigationos && pip install -e ".[dev]" ║
║    Test:    python -m pytest tests/ -q                         ║
║    Safety:  NEVER CWD at repo root (shadow modules!)           ║
║    Toolkit: srun, spy, sspy, sshadow, spreflight               ║
║                                                                ║
║  PIPELINE (O3):                                                ║
║    Full:    cd 00_SYSTEM\pipeline && python run_omega_pipeline  ║
║    Range:   --start-phase 4a --end-phase 7c                    ║
║    Dry run: --dry-run --create-snapshot                        ║
║                                                                ║
║  BACKUP (O4):                                                  ║
║    Dest:    I:\ drive (always)                                 ║
║    Before:  Every filing, every destructive op                 ║
║    Verify:  SHA-256 manifest + DB integrity_check              ║
║    NEVER:   Delete filed court document backups                ║
║                                                                ║
║  HEALTH (O5):                                                  ║
║    Startup: copilot_startup_hook.py --file                     ║
║    Report:  STARTUP_REPORT.md                                  ║
║    Recall:  session_recall.py recent                           ║
║                                                                ║
║  EAGAIN (O9):                                                  ║
║    Route:   MCP → agents → shells (last resort)                ║
║    Shells:  Max 2, stop IMMEDIATELY after use                  ║
║    Agents:  Max 4, isolated pipes, 0.5s cooldown               ║
║    Recover: Stop all → wait 3s → test MCP → resume             ║
║                                                                ║
║  GOLDEN RULE: Backup first, test after, checkpoint always.     ║
╚════════════════════════════════════════════════════════════════╝
```
