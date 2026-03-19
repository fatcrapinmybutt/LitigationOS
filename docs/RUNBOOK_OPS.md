# LitigationOS — Operations Runbook

> **Quick-reference for daily operations, emergency procedures, and system management.**
> Last updated: 2026-02-28 | See also: [`KNOWLEDGE_BASE_INDEX.md`](KNOWLEDGE_BASE_INDEX.md)

---

## Table of Contents

1. [Daily Operations](#1-daily-operations)
2. [Pipeline Operations](#2-pipeline-operations)
3. [Agent Fleet Operations](#3-agent-fleet-operations)
4. [MCP Server Management](#4-mcp-server-management)
5. [Emergency Procedures](#5-emergency-procedures)
6. [Common Error Recovery](#6-common-error-recovery)
7. [Backup & Restore](#7-backup--restore)
8. [Health Checks & Diagnostics](#8-health-checks--diagnostics)

---

## 1. Daily Operations

### Morning Startup Sequence

```powershell
# 1. Generate startup report (DB health, deadlines, evidence, sessions)
python 00_SYSTEM\local_model\copilot_startup_hook.py --file

# 2. Read the report
cat 00_SYSTEM\STARTUP_REPORT.md

# 3. Recall recent sessions for continuity
python 00_SYSTEM\local_model\session_recall.py recent
```

### Health Check

```powershell
# Quick system status
cd 00_SYSTEM\pipeline && python quick_status.py

# Full doctor check (CAS integrity, DB foreign keys, extraction paths, stack manifests)
python tooling/doctor_all.py --vault Vault --db litigation_context.db
```

### Deadline Review

```powershell
# View upcoming deadlines (MCP tool)
# Via MCP: litigation_deadline_dashboard

# Manual query against the database
python -c "
import sqlite3, sys
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
conn = sqlite3.connect('litigation_context.db')
conn.execute('PRAGMA busy_timeout=60000')
for r in conn.execute('SELECT * FROM deadlines WHERE status != ? ORDER BY due_date_iso LIMIT 20', ('completed',)):
    print(r)
conn.close()
"
```

### Daily Backup

```powershell
# Create safety snapshot (SHA-256 manifest + backup)
cd 00_SYSTEM\pipeline
python run_omega_pipeline.py --start-phase 0 --end-phase 0

# Or use MCP tool: litigation_backup_create
```

---

## 2. Pipeline Operations

### Full Pipeline Run

```powershell
cd C:\Users\andre\LitigationOS\00_SYSTEM\pipeline

# Full 24-phase run with safety snapshot
python run_omega_pipeline.py --create-snapshot

# Dry run (validate phase chain, no files written)
python run_omega_pipeline.py --dry-run

# List all available phases
python run_omega_pipeline.py --list-phases
```

### Partial Pipeline Runs

```powershell
# Run specific phase range
python run_omega_pipeline.py --start-phase 4a --end-phase 7c

# Skip specific phases
python run_omega_pipeline.py --skip-phases 16

# Single phase directly
python phase3_classify.py
```

### Pipeline Resume After Failure

Each phase checkpoints on completion. To resume:

```powershell
# 1. Check which phase failed
python quick_status.py

# 2. Resume from the failed phase
python run_omega_pipeline.py --start-phase <FAILED_PHASE>
```

### Pipeline Validation

```powershell
# Syntax check all modules
cd 00_SYSTEM\scripts && python syntax_check.py

# Integration test phases 1-3
python integration_test_phase123.py

# Full validation
cd 00_SYSTEM\pipeline && python validate.py
```

### Fix Failures (in order)

1. **OCR** → Ensure OCR queue is empty (`needs_ocr` documents have extraction rows)
2. **Instructions** → Recompile instruction atoms per form
3. **Requirements** → Verify `satisfied==1` for all requirements in stacks
4. **Stacks** → Run stack lint until PASS for each stack folder
5. **Lint** → MiFILE lint returns no ERROR for filing PDFs
6. **Satisfaction** → All PASS gates satisfied (see [`PASS_GATES.md`](PASS_GATES.md))
7. **Export** → CyclePack ZIP + manifest produced with valid hashes

---

## 3. Agent Fleet Operations

### Run Agents

```powershell
cd C:\Users\andre\LitigationOS\00_SYSTEM\pipeline

# Full fleet run (all 56 DELTA9 agents)
python -m agents.agent_orchestrator

# Single tier (e.g., judicial intelligence)
python -m agents.agent_orchestrator --tier J

# Single agent
python -m agents.agent_orchestrator --agent J01

# Dry run
python -m agents.agent_orchestrator --dry-run
```

### Agent Tiers

| Lane | Tiers | Agents | Role |
|------|-------|--------|------|
| **Lane 1 (I/O)** | 1-3 | A01-A12 | Indexing, dedup, extraction |
| **Lane 2 (Intel)** | J/K/L | J01-L08 | Judicial profiling, case intel, legal analysis |
| **Convergence** | F | F01-F06 | Filing assembly, brain feed, graph build, certification |

### Agent Contract

- Every agent: `run() → AgentResult(agent_id, status, stats)`
- Status values: `SUCCESS` | `FATAL` | `CRASH`
- Data store: `agents/master_index.db` (SQLite WAL mode)

### 7-Layer Error Protocol (every agent)

1. Try operation
2. Specific catch → targeted recovery
3. Broad catch → log + skip + continue
4. Checkpoint every N items → crash-resume
5. Deadman switch (120s no progress → self-diagnose)
6. Agent retry (3× exponential backoff)
7. Tier fallback → orchestrator flags + continues

---

## 4. MCP Server Management

### Server Setup

```powershell
# Install MCP server
pip install -e 00_SYSTEM\mcp_server\

# Server location: 00_SYSTEM/mcp_server/litigation_context_mcp/
# VS Code config: .vscode/mcp.json
```

### Server Configuration

- Workspace MCP config: `.vscode/mcp.json`
- Servers: `github`, `fetch`, `filesystem`, `litigationos`
- All tools prefixed with `litigation_` (47 total)

### Key MCP Tool Categories

| Category | Count | Key Tools |
|----------|-------|-----------|
| Core | 10 | `scan_drives`, `ingest_pdf`, `bulk_ingest`, `search`, `get_stats` |
| Filing | 8 | `filing_readiness`, `filing_validate`, `filing_assemble`, `efiling_prep` |
| Evidence | 7 | `evidence_chain`, `evidence_gaps`, `evidence_link`, `bates_assign` |
| Deadline | 5 | `deadline_dashboard`, `deadline_urgency`, `deadline_add` |
| Analysis | 5 | `authority_index`, `citation_graph`, `judicial_bias_scan` |
| QA | 4 | `prefiling_qa`, `qa_sweep`, `signature_check`, `service_check` |
| Backup | 3 | `backup_create`, `backup_version`, `backup_report` |
| System | 1 | `system_health` |

### Health Check

```powershell
# MCP health tool
# Via MCP: litigation_health

# Self-test
# Via MCP: litigation_self_test

# Full audit with scoring
# Via MCP: litigation_self_audit
```

---

## 5. Emergency Procedures

### 🚨 Filing Deadline Emergency

**Situation:** Court deadline approaching, filing incomplete.

```
1. STOP all non-essential pipeline work
2. Run: litigation_deadline_urgency (identify most critical deadline)
3. Run: litigation_filing_readiness (check what's ready)
4. Run: litigation_placeholder_scan → litigation_placeholder_resolve
5. Run: litigation_prefiling_qa (GO/NO-GO check)
6. If GO → litigation_filing_assemble → litigation_efiling_prep
7. If NO-GO → identify blockers, fix in priority order
8. Run: litigation_service_check + litigation_signature_check
9. File immediately
```

### 🚨 Database Corruption

**Symptoms:** `SQLITE_CORRUPT`, missing tables, inconsistent reads.

```powershell
# 1. STOP all pipeline operations immediately
# 2. Create emergency backup of current state
Copy-Item litigation_context.db litigation_context.db.EMERGENCY_BACKUP

# 3. Check integrity
python -c "
import sqlite3, sys
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
conn = sqlite3.connect('litigation_context.db')
result = conn.execute('PRAGMA integrity_check').fetchone()
print(f'Integrity: {result[0]}')
conn.close()
"

# 4. If corruption confirmed — restore from latest backup
# Backups location: 00_SYSTEM/backups/
# Via MCP: litigation_backup_report (list available backups)

# 5. If no clean backup — rebuild DB from CAS objects
# The Vault/00_OBJECTS directory is the source of truth.
# Rebuild by scanning CAS objects and re-deriving doc_ids.
```

### 🚨 Evidence Preservation Emergency

**Situation:** Evidence at risk of loss/tampering.

```
1. Create SHA-256 manifest of all evidence files immediately:
   python run_omega_pipeline.py --start-phase 0 --end-phase 0 --create-snapshot

2. Copy evidence to separate backup drive (I:\ preferred)

3. Document chain of custody:
   - Timestamp of preservation
   - SHA-256 hashes of preserved files
   - Location of originals and copies

4. Via MCP: litigation_evidence_authenticate (verify existing chain)
```

### 🚨 GOAWAY / 503 / Session Timeout

**Situation:** Agent or Copilot session killed mid-operation.

```
1. Check progress logs: 00_SYSTEM\PROGRESS_LOG.md
2. Check SQL todos table for last completed task
3. Check pipeline checkpoints for last completed phase
4. Resume from last checkpoint — DO NOT restart from scratch
5. If no checkpoint: check temp/ for intermediate outputs
```

---

## 6. Common Error Recovery

### EAGAIN (Pipe Buffer Overflow)

**Symptoms:** `write EAGAIN`, `Invalid shell ID` on fresh shells.

```
Root cause: Too many concurrent PowerShell sessions + agents.
Max allowed: 2 async shells + 2 background agents = 4 total.

RECOVERY:
1. FULL STOP — do not spawn anything new
2. list_powershell → stop ALL sessions
3. list_agents → wait for all to complete
4. Wait 5 seconds
5. Test with ONE simple command
6. If OK → resume with strict concurrency limits
7. If still failing → use task agents only (isolated pipes)
8. Nuclear option → AUTONOMOS file-based execution (create + view tools only)
```

**Prevention:**
- Chain commands with `&&` (one shell, multiple commands)
- Stop shells IMMEDIATELY after use
- Limit output to <100 lines per command
- Redirect large output to temp files, read with `view`

### Database Locked (SQLITE_BUSY)

**Symptoms:** `database is locked`, `SQLITE_BUSY` errors.

```
Root cause: Too many concurrent DB connections (max 3 allowed).

RECOVERY:
1. Wait — WAL mode allows concurrent reads, writes queue
2. Ensure PRAGMA busy_timeout=60000 on all connections
3. Use managed_db() context manager from db_lock_manager.py
4. Never open DB connections inside shell commands — use Python scripts
5. Check for orphan processes holding locks:
   Get-Process python | Select-Object Id, StartTime, CommandLine
```

**Required PRAGMAs (every connection):**
```sql
PRAGMA busy_timeout = 60000;
PRAGMA journal_mode = WAL;
PRAGMA cache_size = -32000;
PRAGMA temp_store = MEMORY;
PRAGMA synchronous = NORMAL;
```

### Import Errors / Shadow Modules

**Symptoms:** `ImportError`, wrong module loaded, `json.py` conflicts.

```
Root cause: Repo root contains 22 shadow modules (json.py, typing.py, numpy.py, etc.)
that override Python stdlib when CWD is the repo root.

FIX:
1. NEVER set CWD to repo root when running Python
2. Use safe wrappers:
   . 00_SYSTEM\tools\agent_profile.ps1
   srun script.py --arg       # safe run
   sspy file1.py file2.py     # syntax check
   spy "print(1+1)"           # safe inline Python
3. Or use safe_shell.py directly:
   python 00_SYSTEM\tools\safe_shell.py run script.py
4. Run shadow audit:
   python 00_SYSTEM\tools\safe_shell.py shadow-audit
```

### Python Execution Failures in PowerShell

**Symptoms:** `SyntaxError`, broken f-strings, quote escaping issues.

```
RULE: NEVER use python -c "..." in PowerShell.

FIX: Write Python to a temp .py file, execute it, clean up:
  1. Create temp script with create/edit tools
  2. Execute: python temp\script.py
  3. Clean up: Remove-Item temp\script.py

Or use agent_profile.ps1 wrappers:
  . 00_SYSTEM\tools\agent_profile.ps1
  spy "print(1+1)"   # handles temp file automatically
```

### Agent CRASH / FATAL Status

```
1. Check agent log: agents/master_index.db → agent_log table
2. Check the 7-layer error protocol output
3. Common causes:
   - DB locked → wait and retry
   - File not found → check drive mounts
   - Timeout → deadman switch triggered, check resource usage
4. Retry single agent: python -m agents.agent_orchestrator --agent <AGENT_ID>
5. If persistent → check agent data in master_index.db for corrupt state
```

---

## 7. Backup & Restore

### Backup Locations

| Type | Location | Frequency |
|------|----------|-----------|
| Safety Snapshots | `00_SYSTEM/backups/` | Every pipeline run (Phase 0) |
| CyclePack Exports | External drive | After each complete cycle |
| DB Backups | `I:\` drive | Daily recommended |
| CAS Objects | `Vault/00_OBJECTS/` | Source of truth (immutable) |

### Create Backup

```powershell
# Pipeline safety snapshot
cd 00_SYSTEM\pipeline && python run_omega_pipeline.py --start-phase 0 --end-phase 0

# MCP backup
# Via MCP: litigation_backup_create

# Manual DB backup
Copy-Item litigation_context.db "I:\backups\litigation_context_$(Get-Date -Format 'yyyyMMdd_HHmmss').db"
```

### Restore

```powershell
# 1. Stop all operations
# 2. List available backups
# Via MCP: litigation_backup_report

# 3. Restore DB from backup
Copy-Item "I:\backups\litigation_context_YYYYMMDD.db" litigation_context.db

# 4. Verify integrity
python -c "
import sqlite3; conn = sqlite3.connect('litigation_context.db')
print(conn.execute('PRAGMA integrity_check').fetchone())
conn.close()
"

# 5. Resume pipeline from appropriate phase
```

### Disaster Recovery

If indexes corrupt but CAS objects intact:
1. Rebuild DB by scanning `Vault/00_OBJECTS/`
2. Re-derive `doc_ids` from CAS hashes
3. Re-run extraction pipeline (Phases 4a-4e)
4. Always keep CyclePack exports externally backed up

---

## 8. Health Checks & Diagnostics

### Quick Diagnostics

```powershell
# System startup report
python 00_SYSTEM\local_model\copilot_startup_hook.py --file
cat 00_SYSTEM\STARTUP_REPORT.md

# Pipeline status
cd 00_SYSTEM\pipeline && python quick_status.py

# Full validation
python validate.py

# Doctor check (CAS integrity, DB FK consistency, lint reports)
python tooling/doctor_all.py --vault Vault --db litigation_context.db
```

### Database Health

```powershell
# Integrity check
# Via Python script (never inline -c):
# sqlite3 → PRAGMA integrity_check
# sqlite3 → PRAGMA quick_check (faster, less thorough)

# Table count
# SELECT COUNT(*) FROM sqlite_master WHERE type='table'

# DB size
# Get-Item litigation_context.db | Select-Object Length
```

### MANBEARPIG Inference Engine

```powershell
# CLI query test
python 00_SYSTEM\local_model\inference_engine.py "MCR 2.003 disqualification"

# JSON-RPC pipe mode
python 00_SYSTEM\local_model\inference_engine.py --pipe

# Train/retrain model (~60s)
python 00_SYSTEM\local_model\train_model.py

# Self-evolution cycle
python 00_SYSTEM\local_model\self_evolve_v2.py
```

### Memory & Resource Monitoring

Key memory consumers:
- **Connection Multiplexer**: 12 GB mmap + 128 MB cache (Tier 1)
- **Bloom Filter**: ~9.6 MB (3.7M citations, O(1) lookup)
- **Prefetch Cache**: 50 MB cap (9 categories, parallel load)
- **Standard DB connections**: 32 MB cache each (Tier 2)

Monitor with:
```powershell
# System memory
Get-Process python | Select-Object Id, WorkingSet64, VirtualMemorySize64 | Format-Table

# Total system memory usage
Get-CimInstance Win32_OperatingSystem | Select-Object TotalVisibleMemorySize, FreePhysicalMemory
```

---

## Quick Reference Card

```
╔══════════════════════════════════════════════════════════════╗
║                 LITIGATIONOS — QUICK OPS                    ║
╠══════════════════════════════════════════════════════════════╣
║ Startup:    python 00_SYSTEM\local_model\copilot_startup_   ║
║             hook.py --file                                   ║
║ Pipeline:   python run_omega_pipeline.py --create-snapshot   ║
║ Agents:     python -m agents.agent_orchestrator              ║
║ MCP:        pip install -e 00_SYSTEM\mcp_server\             ║
║ Backup:     Phase 0 snapshot OR litigation_backup_create     ║
║ Health:     python tooling/doctor_all.py --vault Vault       ║
║ Deadlines:  litigation_deadline_dashboard                    ║
║ Pre-file:   litigation_prefiling_qa                          ║
╠══════════════════════════════════════════════════════════════╣
║ CONCURRENCY LIMITS:                                          ║
║   Max 2 async shells + 2 background agents = 4 total         ║
║   Max 3 DB connections (use managed_db())                    ║
║   Output <100 lines per shell command                        ║
║   Chain commands with && (one shell, many commands)          ║
╠══════════════════════════════════════════════════════════════╣
║ EMERGENCY:                                                   ║
║   Filing deadline → litigation_filing_readiness first         ║
║   DB corrupt → Copy-Item + PRAGMA integrity_check            ║
║   EAGAIN → Stop ALL shells → wait 5s → test ONE              ║
║   Session died → Check PROGRESS_LOG.md + resume from ckpt    ║
╚══════════════════════════════════════════════════════════════╝
```

---

*See [`KNOWLEDGE_BASE_INDEX.md`](KNOWLEDGE_BASE_INDEX.md) for the full documentation map.*
