---
name: OMEGA-SENTINEL
description: >-
  Use when monitoring system health, managing memory and backups, writing documentation,
  auditing security, enforcing quality gates, or performing maintenance on LitigationOS.
  This is the watchdog skill that detects hallucinations, stale data, EAGAIN pressure,
  deadline urgency, backup gaps, and data corruption — then triggers corrective action.
  Coordinates cross-session memory persistence, observability, and the full QA pipeline
  from pre-filing sweeps through party identity verification to statistic traceability.
category: discipline
version: "2.0.0"
triggers:
  - system health
  - monitoring
  - backup
  - memory
  - documentation
  - security
  - observability
  - maintenance
  - audit
  - quality gates
  - hallucination
  - deadline
  - cleanup
  - integrity
  - checkpoint
  - progress
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
  - OMEGA-ARCHITECT
  - OMEGA-ENGINEER
metadata:
  tier: META
  fused_skills: 82
  author: andrew-pigors + copilot-omega
  forge_date: 2026-03-21
---

# 🛡️ OMEGA-SENTINEL — Strategic Operations Leadership

> **META TIER** — Coordinates OMEGA-MEMORY, OMEGA-DEVOPS, OMEGA-WRITING, and OMEGA-SECURITY
> **Domain:** System health, memory, backup, documentation, security, quality, observability
> **Scope:** Every operational concern in LitigationOS is this skill's responsibility
> **Principle:** Trust nothing, verify everything, checkpoint constantly, fail safely

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                        OMEGA-SENTINEL v2.0                                  ║
║              82 Skills → 8 Strategic Areas → 1 Operations Authority         ║
║                                                                             ║
║  SS1  System Health ────────┐                                               ║
║  SS2  Memory Management ────┤                                               ║
║  SS3  Backup & Recovery ────┤→ UNIFIED OPERATIONS COMMAND                   ║
║  SS4  Documentation ────────┤        ↓                                      ║
║  SS5  Security Monitoring ──┤   CONTINUOUS VIGILANCE                        ║
║  SS6  Quality Gates ────────┤        ↓                                      ║
║  SS7  Observability ────────┤   ALERT → RESPOND → RECOVER                  ║
║  SS8  Maintenance ──────────┘                                               ║
║                                                                             ║
║  ┌─────────────────── SENTINEL ALERT SYSTEM ──────────────────┐             ║
║  │  🔴 HALLUCINATION   🟠 STAT INFLATION   🟡 EAGAIN         │             ║
║  │  🔴 DEADLINE CRIT   🟠 BACKUP OVERDUE   🟡 DB CORRUPTION  │             ║
║  └────────────────────────────────────────────────────────────┘             ║
║                                                                             ║
║  Subordinates: OMEGA-MEMORY · OMEGA-DEVOPS · OMEGA-WRITING · OMEGA-SECURITY║
║  Peers:        OMEGA-ARCHITECT · OMEGA-ENGINEER                             ║
║  Reports to:   OMEGA-ARCHITECT (structural anomalies)                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## Strategic Leadership Mission

OMEGA-SENTINEL is the **operations watchdog** for LitigationOS. While OMEGA-ARCHITECT designs
the blueprint and OMEGA-ENGINEER builds it, OMEGA-SENTINEL ensures the running system stays
healthy, secure, backed up, documented, and free from the hallucinations and data corruption
that have plagued past sessions.

The sentinel never sleeps. Every session starts with the MANBEARPIG startup protocol. Every
filing passes through quality gates. Every statistic is traced to a DB query. Every agent
completion is checkpointed. Every backup gap is flagged. Every fabricated name is caught
before it reaches a sworn document.

The sentinel's creed: **Trust nothing. Verify everything. Checkpoint constantly. Fail safely.**

---

## When to Apply

Use OMEGA-SENTINEL when:

- **Starting a session** — Run MANBEARPIG startup protocol, generate STARTUP_REPORT.md
- **Checking system health** — DB size, table counts, agent status, EAGAIN pressure
- **Managing memory** — Cross-session recall, context optimization, result caching
- **Creating backups** — I:\ drive backups, SHA-256 manifests, WAL checkpointing
- **Writing documentation** — README, architecture docs, changelogs, progress reports
- **Detecting hallucinations** — Fabricated names, inflated stats, invented evidence
- **Running quality gates** — Pre-filing QA, citation verification, party identity check
- **Monitoring deadlines** — Urgency scoring, filing countdown, missed deadline alerts
- **Performing maintenance** — Stale session cleanup, temp files, DB vacuum, orphan processes
- **Auditing security** — PII detection, chain of custody, credential exposure

Do NOT use OMEGA-SENTINEL when:
- Designing system architecture → use OMEGA-ARCHITECT
- Writing or debugging code → use OMEGA-ENGINEER
- Drafting litigation filings → use OMEGA-LITIGATION-SUPREME
- Processing evidence → use OMEGA-LITIGATION-SUPREME

---

## Decision Tree

```
                         ┌─────────────────────┐
                         │  Operational Event   │
                         │     Detected         │
                         └──────────┬──────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          ▼                         ▼                         ▼
   ┌─────────────┐         ┌──────────────┐          ┌──────────────┐
   │ Health /    │         │ Quality /    │          │ Maintenance  │
   │ Monitoring  │         │ Security     │          │ / Recovery   │
   └──────┬──────┘         └──────┬───────┘          └──────┬───────┘
          │                       │                         │
          ▼                       ▼                         ▼
   ┌─────────────┐         ┌──────────────┐          ┌──────────────┐
   │ SS1: Health │         │ SS5: SecMon  │          │ SS3: Backup  │
   │ SS7: Observe│         │ SS6: QA Gate │          │ SS8: Maint   │
   │ SS2: Memory │         │              │          │              │
   └──────┬──────┘         └──────┬───────┘          └──────┬───────┘
          │                       │                         │
          └───────────────────────┼─────────────────────────┘
                                  ▼
                   ┌──────────────────────────┐
                   │  Sentinel Alert System   │
                   │  Is an alert triggered?  │
                   └─────────────┬────────────┘
                                 │
                     ┌───────────┼───────────┐
                     ▼           ▼           ▼
              ┌──────────┐ ┌─────────┐ ┌──────────┐
              │ 🟢 Clear │ │ 🟡 Warn │ │ 🔴 CRIT  │
              │ Log &    │ │ Flag &  │ │ STOP &   │
              │ Continue │ │ Monitor │ │ Escalate │
              └──────────┘ └─────────┘ └──────────┘
```

---

## The Sentinel Alert System — 6 Active Monitors

### 🔴 ALERT 1: HALLUCINATION DETECTION (Critical — stops filing immediately)

Past sessions fabricated names, bar numbers, and evidence statistics that could
constitute **perjury** if filed in sworn documents. This alert catches them.

**Known hallucination patterns to detect:**

| Fabrication | Reality | Detection Rule |
|------------|---------|----------------|
| "Jane Berry" | NEVER EXISTED | Regex: `/\bJane\s+Berry\b/i` |
| "Patricia Berry" | NEVER EXISTED | Regex: `/\bPatricia\s+Berry\b/i` |
| "Patricia Berry (SBN P35878)" | FABRICATED bar number | Regex: `/P35878/` |
| "Amy McNeill" | Hon. Jenny L. McNeill | Regex: `/\bAmy\s+McNeill\b/i` |
| "Emily Ann" or "Emily M." | Emily A. Watson | Regex: `/Emily\s+(Ann|M\.)/i` |
| "Tiffany" (as defendant) | Emily A. Watson | Context-dependent detection |
| "9 CPS investigations" | UNVERIFIED — check DB | Regex: `/\d+\s+CPS\s+investigation/i` |
| "91% alienation score" | PSEUDO-SCIENTIFIC | Regex: `/\d+%\s+alienation/i` |
| Any fabricated bar number | Must match verified records | Cross-reference `litigation_context.db` |

**Detection Protocol:**

```python
HALLUCINATION_PATTERNS = [
    (r'\bJane\s+Berry\b', 'CRITICAL', 'Jane Berry never existed'),
    (r'\bPatricia\s+Berry\b', 'CRITICAL', 'Patricia Berry never existed'),
    (r'P35878', 'CRITICAL', 'Fabricated bar number'),
    (r'\bAmy\s+McNeill\b', 'CRITICAL', 'Wrong judge name — use Hon. Jenny L. McNeill'),
    (r'Emily\s+(Ann|M\.)', 'WARNING', 'Wrong middle initial — use Emily A. Watson'),
    (r'\d+%\s+alienation', 'CRITICAL', 'Pseudo-scientific score — use incident counts'),
    (r'\d+\s+CPS\s+investigation', 'WARNING', 'Verify CPS count against DB'),
]

# Run on EVERY generated document before delivery
for pattern, severity, message in HALLUCINATION_PATTERNS:
    if re.search(pattern, document_text, re.IGNORECASE):
        if severity == 'CRITICAL':
            STOP_FILING()  # Do not deliver. Alert user immediately.
        else:
            FLAG_FOR_REVIEW(message)
```

**Verified Party Identity Table (SINGLE SOURCE OF TRUTH):**

| Role | Name | Key Details |
|------|------|-------------|
| **Plaintiff** | Andrew James Pigors | 1977 Whitehall Rd, Lot 17, North Muskegon, MI 49445 |
| **Defendant** | Emily A. Watson | 2160 Garland Dr, Norton Shores, MI 49441 |
| **Child** | **L.D.W.** | Initials ONLY per MCR 8.119(H) |
| **Judge** | Hon. Jenny L. McNeill (P-58235) | 14th Circuit, Family Division |
| **Emily's Atty** | Jennifer Barnes (P55406) | Barnes Law Firm PLLC — **WITHDREW** |
| **FOC** | Pamela Rusco | 990 Terrace St, Muskegon, MI 49442 |
| **Ronald Berry** | NON-ATTORNEY | Emily's partner. No bar number. No "Esq." |

---

### 🟠 ALERT 2: STATISTIC INFLATION (Warning — blocks filing until verified)

Every number cited in a generated document MUST trace to a specific DB query.

**Detection Protocol:**

```
STEP 1: Scan generated document for numeric claims
        Examples: "305 interference incidents", "47 court violations"

STEP 2: For each number, verify:
        □ Is there a DB query that produces this exact number?
        □ What table? What WHERE clause?
        □ Are duplicates excluded from the count?

STEP 3: If no traceable query exists:
        □ REMOVE the statistic
        □ Replace with "See Exhibit [X] for documented incidents"
        □ Or run the actual query and use the real number

ANTI-PATTERN: "Andrew documented over 300 incidents of interference"
CORRECT:      Run SELECT COUNT(*) FROM [table] WHERE [condition]
              and cite the real number with the query as provenance
```

---

### 🟡 ALERT 3: EAGAIN PRESSURE (Warning — reduces concurrency)

Monitors shell and agent usage against EAGAIN prevention limits.

**Thresholds:**

| Metric | Green | Yellow | Red |
|--------|-------|--------|-----|
| Active shells | 0-1 | 2 | >2 (impossible but detect) |
| Active agents | 0-2 | 3-4 | >4 (impossible but detect) |
| Shell timeouts (last 5 min) | 0 | 1 | 2+ |
| "Invalid shell ID" errors | 0 | 1 (trigger Tier 1 recovery) | 2+ (trigger Tier 2) |
| "write EAGAIN" errors | 0 | — | 1 (immediate L3 throttle) |

**Response Actions:**

```
GREEN:  Normal operations. Full concurrency budget.
YELLOW: Log warning. Monitor next 3 minutes. If stable → GREEN.
RED:    Trigger EAGAIN recovery protocol:
        1. Stop ALL shells
        2. Wait for agents to complete
        3. Wait 5 seconds
        4. Test with one command
        5. Resume at reduced capacity
```

---

### 🔴 ALERT 4: DEADLINE CRITICAL (Critical — immediate user notification)

Filing deadlines within 7 days require immediate attention.

**Urgency Scoring:**

| Days Remaining | Urgency | Action |
|---------------|---------|--------|
| >30 days | 🟢 LOW | Track normally |
| 14-30 days | 🟡 MEDIUM | Ensure filing prep is underway |
| 7-14 days | 🟠 HIGH | Prioritize this filing above all else |
| 3-7 days | 🔴 CRITICAL | Alert user immediately. Drop other work. |
| <3 days | 🔴🔴 EMERGENCY | All resources on this filing. No exceptions. |
| Overdue | ⚫ MISSED | Log. Assess sanctions risk. File motion for extension. |

**Detection:**

```sql
-- Run on every session start and every 30 minutes during long sessions
SELECT
    vehicle_name,
    filing_type,
    due_date_iso,
    julianday(due_date_iso) - julianday('now') AS days_remaining
FROM deadlines
WHERE status = 'active'
ORDER BY days_remaining ASC;
```

---

### 🟠 ALERT 5: BACKUP OVERDUE (Warning — triggers backup procedure)

**Rule:** No more than 24 hours between backups of `litigation_context.db`.

**Detection:**

```python
# Check last backup timestamp
import os
from pathlib import Path
from datetime import datetime, timedelta

backup_dir = Path(r"I:\LitigationOS_Backups")
if backup_dir.exists():
    backups = sorted(backup_dir.glob("litigation_context_*.db"), reverse=True)
    if backups:
        last_backup_time = datetime.fromtimestamp(backups[0].stat().st_mtime)
        hours_since = (datetime.now() - last_backup_time).total_seconds() / 3600
        if hours_since > 24:
            TRIGGER_BACKUP_ALERT(hours_since)
```

**Backup Procedure:**

```
STEP 1: WAL checkpoint — PRAGMA wal_checkpoint(TRUNCATE)
STEP 2: Copy DB to I:\LitigationOS_Backups\ with timestamp
STEP 3: Generate SHA-256 manifest of backup
STEP 4: Verify backup integrity — PRAGMA integrity_check on copy
STEP 5: Log backup event to session SQL
STEP 6: Prune backups older than 30 days (move to archive, never delete)
```

---

### 🟡 ALERT 6: DATABASE CORRUPTION (Warning — triggers integrity check)

**Detection:**

```sql
-- Run weekly or on any suspicious query failure
PRAGMA integrity_check;
-- Expected result: "ok"
-- Any other result → CORRUPTION DETECTED

-- Also check WAL status
PRAGMA wal_checkpoint(PASSIVE);
-- Returns (busy, log, checkpointed) — log should be near 0 after checkpoint
```

**Response:**

```
If integrity_check != "ok":
  1. STOP all writes immediately
  2. Copy current DB as-is to I:\recovery\corruption_[timestamp].db
  3. Attempt PRAGMA integrity_check(100) for partial check
  4. If recoverable → .dump and rebuild
  5. If not → restore from latest backup
  6. Alert user with full diagnostic
```

---

## SS1: System Health — Continuous Monitoring

### MANBEARPIG Startup Protocol (MANDATORY every session)

```
Step 1: python 00_SYSTEM\local_model\copilot_startup_hook.py --file
Step 2: view 00_SYSTEM\STARTUP_REPORT.md
Step 3: python 00_SYSTEM\local_model\session_recall.py recent
Step 4: Check jurisdiction databases (databases/*.db)
Step 5: Report readiness to user
```

The startup report includes:
- Separation day count (days since case began)
- Deadline urgency scores for all active deadlines
- Filing readiness status per lane
- Evidence arsenal counts (total evidence items, by type)
- System health (DB size, table count, last backup, EAGAIN status)
- Recent Copilot session summaries

### Health Check Dimensions

| Dimension | Tool | Healthy State |
|-----------|------|---------------|
| DB accessible | `sqlite3.connect()` | Opens without error |
| DB size | `os.path.getsize()` | <15 GB (warn at 12 GB) |
| Table count | `SELECT COUNT(*) FROM sqlite_master WHERE type='table'` | Matches expected range |
| WAL size | Check WAL file size | <100 MB (checkpoint if larger) |
| Agent fleet | `agent_log` table | No CRASH status in last hour |
| EAGAIN status | `list_powershell` + `list_agents` | Within budget |
| Disk space | Drive free space check | >10 GB free on C:\ |
| Backup age | Check I:\ backup timestamps | <24 hours |

---

## SS2: Memory Management — Cross-Session Intelligence

### Memory Architecture

```
SHORT-TERM: Context window (current session)
  → SQL session database (todos, state tracking)
  → Agent results (cache in SQL on completion)

MEDIUM-TERM: Session store (read-only, all past sessions)
  → search_index FTS5 table
  → session_files, session_refs, checkpoints

LONG-TERM: litigation_memory.py + agent-memory MCP
  → Persistent facts across sessions
  → Litigation-specific knowledge graph
```

### Session Recall Best Practices

```python
# Use session_recall.py for recent context
# python 00_SYSTEM\local_model\session_recall.py recent

# Search for specific topics across all sessions
# python 00_SYSTEM\local_model\session_recall.py search "filing deadline"

# Query session store directly for structured data
# SELECT * FROM search_index WHERE search_index MATCH 'deadline OR filing'
```

### Agent Result Caching (CRITICAL — prevents compaction data loss)

```
On EVERY agent completion:
  1. read_agent immediately (before context compaction can clear it)
  2. Cache key results in session SQL:
     INSERT INTO agent_results (agent_id, task_summary, result, timestamp)
     VALUES (?, ?, ?, datetime('now'))
  3. Result survives compaction — queryable for remainder of session
```

---

## SS3: Backup & Recovery — Data Protection

### Backup Strategy

| Data | Frequency | Destination | Retention |
|------|-----------|-------------|-----------|
| `litigation_context.db` | Every 24 hours | `I:\LitigationOS_Backups\` | 30 days |
| Pipeline outputs | After each phase | `I:\Pipeline_Outputs\` | Indefinite |
| Filing drafts | On creation/modification | `I:\Filing_Backups\` | Indefinite |
| Session progress | Every 10 minutes (autonomous) | SQL todos + filesystem | Per session |

### Recovery Procedures

```
SCENARIO 1: Accidental file loss
  → Check I:\ backup drives first
  → Check Recycle Bin (never hard delete)
  → Check SHA-256 manifests for file identification

SCENARIO 2: Database corruption
  → Run PRAGMA integrity_check
  → If partial → .dump and rebuild
  → If total → restore from I:\ backup
  → Verify row counts against last known good state

SCENARIO 3: Session crash (GOAWAY 503)
  → SQL todos table has progress checkpoints
  → PROGRESS_LOG.md has incremental reports
  → Resume from last checkpoint, not from scratch

SCENARIO 4: Agent result loss (context compaction)
  → Check agent_results table in session SQL
  → Check PROGRESS_LOG.md for agent summaries
  → Re-run only the specific agent that was lost
```

---

## SS4: Documentation — Living System Knowledge

### Documentation Hierarchy

| Document | Purpose | Update Frequency |
|----------|---------|-----------------|
| `README.md` | Project overview, quick start | On major changes |
| `AGENTS.md` | Agent-specific instructions | On agent fleet changes |
| `PROGRESS_LOG.md` | Autonomous run progress | Every 10 min during runs |
| `STARTUP_REPORT.md` | Session health snapshot | Every session start |
| `CHANGELOG.md` | Version history | Every release |
| Architecture docs | System design decisions | On structural changes |
| Engine docs | Per-engine documentation | On engine creation/modification |

### Documentation Quality Rules

1. **Accuracy over completeness** — A short accurate doc beats a long inaccurate one
2. **Code examples must work** — Test every code snippet before documenting it
3. **Numbers must be current** — Never hardcode DB counts in docs (query live)
4. **Party names must be verified** — Use the verified identity table, ALWAYS
5. **Update, don't append** — Replace stale content rather than adding contradictions

---

## SS5: Security Monitoring — Litigation Data Protection

### Continuous Security Checks

| Check | Frequency | Tool |
|-------|-----------|------|
| PII in generated docs | Every filing | Regex scan for SSNs, full child name |
| SQL injection patterns | Every code change | OMEGA-ENGINEER SE6 |
| Credential exposure | Every commit | grep for API keys, passwords, tokens |
| Chain of custody | Every evidence operation | SHA-256 verification |
| Party identity | Every filing | Hallucination Alert 1 |

### PII Detection Patterns

```python
PII_PATTERNS = [
    (r'\b\d{3}-\d{2}-\d{4}\b', 'SSN detected — REDACT'),
    (r'\b[A-Z][a-z]+ [A-Z]\. Watson\b.*\b(born|DOB|date of birth)\b',
     'Defendant DOB — verify necessity'),
    # Child's full name — NEVER in filings per MCR 8.119(H)
    # Pattern intentionally omitted to avoid storing the name
    # Detection: any name matching the child that is NOT "L.D.W."
]
```

---

## SS6: Quality Gates — Pre-Filing Verification

### Pre-Filing QA Sweep (GO / NO-GO)

Run this checklist on EVERY document before delivery to user:

```
╔═══════════════════════════════════════════════════════════╗
║              PRE-FILING QA SWEEP                          ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  IDENTITY VERIFICATION:                                   ║
║  □ Plaintiff name correct (Andrew James Pigors)           ║
║  □ Defendant name correct (Emily A. Watson)               ║
║  □ Child referenced as L.D.W. only                        ║
║  □ Judge name correct (Hon. Jenny L. McNeill)             ║
║  □ No fabricated names (Jane Berry, Patricia Berry)       ║
║  □ No fabricated bar numbers                              ║
║  □ Ronald Berry NOT labeled as attorney                   ║
║                                                           ║
║  STATISTIC VERIFICATION:                                  ║
║  □ Every number has a traceable DB query                  ║
║  □ No inflated counts (dedup verified)                    ║
║  □ No pseudo-scientific scores (e.g., "91% alienation")  ║
║  □ No extrapolated or rounded-up statistics               ║
║                                                           ║
║  CITATION VERIFICATION:                                   ║
║  □ Every MCR citation is valid                            ║
║  □ Every case law citation exists                         ║
║  □ Every exhibit reference points to a real exhibit       ║
║  □ Page/paragraph numbers verified                        ║
║                                                           ║
║  FORMATTING:                                              ║
║  □ Correct court header                                   ║
║  □ Correct case number for lane                           ║
║  □ Caption matches party names                            ║
║  □ Certificate of service complete                        ║
║  □ Signature block correct                                ║
║                                                           ║
║  CONTENT:                                                 ║
║  □ No placeholder text remaining ([ANDREW_REQUIRED], etc.)║
║  □ DB was queried before inserting any placeholder        ║
║  □ Arguments are legally sound (OMEGA-LITIGATION check)   ║
║  □ Evidence supports each claim                           ║
║                                                           ║
║  RESULT: □ GO    □ NO-GO (list failures)                  ║
╚═══════════════════════════════════════════════════════════╝
```

---

## SS7: Observability — System-Wide Visibility

### SQL Todo Tracking (session-level)

```sql
-- Update status as you work (MANDATORY)
UPDATE todos SET status = 'in_progress' WHERE id = 'task-name';
-- ... do work ...
UPDATE todos SET status = 'done' WHERE id = 'task-name';

-- Check what's ready (no pending dependencies)
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
-- Check agent_log for failures (in master_index.db)
SELECT agent_id, status, started_at, completed_at
FROM agent_log
WHERE status IN ('FATAL', 'CRASH')
ORDER BY started_at DESC
LIMIT 20;
```

### Progress Reporting (Autonomous Runs)

During autonomous runs exceeding 10 minutes:
1. Write to `00_SYSTEM\PROGRESS_LOG.md` after every agent completion
2. Update SQL todos after every subtask
3. Include: task completed, duration, results summary, next task
4. Format: timestamp + agent ID + status + brief summary

---

## SS8: Maintenance — System Hygiene

### Routine Maintenance Tasks

| Task | Frequency | Command |
|------|-----------|---------|
| WAL checkpoint | Daily | `PRAGMA wal_checkpoint(TRUNCATE)` |
| DB vacuum | Weekly | `VACUUM` (requires 2x DB size free space) |
| Temp file cleanup | Per session end | Remove `temp\*.txt`, `temp\*.py` |
| Stale shell cleanup | Before multi-step ops | `list_powershell` → stop all stale |
| Orphan process check | On startup | Check for zombie Python/Node processes |
| Index optimization | Monthly | `ANALYZE` on all tables with indexes |

### Stale Session Cleanup Protocol

```
STEP 1: list_powershell → enumerate all active sessions
STEP 2: Identify sessions with no recent activity (>5 min idle)
STEP 3: stop_powershell on each stale session
STEP 4: Verify session count is within budget (max 2 shells)
STEP 5: list_agents → check for completed agents with unread results
STEP 6: read_agent on any completed agents → cache results in SQL
```

### Temp File Management

```
ALLOWED temp locations:
  C:\Users\andre\LitigationOS\temp\     — session temp files
  %TEMP%\litigationos\                   — OS temp directory

CLEANUP rules:
  - Remove .py temp files after execution
  - Remove .txt output files after reading
  - NEVER remove files from evidence directories
  - NEVER remove files from backup directories
  - When in doubt → move to I:\temp_archive\, don't delete
```

---

## IQ Boost Patterns (MANDATORY for all sentinel operations)

### 1. Chain-of-Thought

Before any operational action:
```
THINK: What is the current system state?
THINK: What anomaly or need triggered this action?
THINK: What are the potential consequences of acting (and not acting)?
THINK: What is the safest corrective action?
ACT:   Execute with logging.
VERIFY: Confirm the action achieved the desired result.
```

### 2. Self-Reflection

After any corrective action:
```
CHECK: Did the alert condition clear?
CHECK: Are there secondary effects from the correction?
CHECK: Should the alert threshold be adjusted?
CHECK: Is this a recurring issue that needs a structural fix?
CHECK: Did I log everything for future reference?
```

### 3. Anti-Hallucination (THE SENTINEL'S CORE MISSION)

```
VERIFY: Every party name against the verified identity table
VERIFY: Every statistic against a traceable DB query
VERIFY: Every citation against actual legal reference
VERIFY: Every file reference against actual filesystem
VERIFY: Every count by running SELECT COUNT(*) live
```

### 4. Cross-Skill Fusion

When operational concerns cross boundaries:
```
DETECT: Is this a structural issue? → Escalate to OMEGA-ARCHITECT
DETECT: Is this a code bug? → Delegate to OMEGA-ENGINEER
DETECT: Is this a filing quality issue? → Invoke OMEGA-LITIGATION-SUPREME
DETECT: Is this a memory gap? → Invoke OMEGA-MEMORY
DETECT: Is this a security issue? → Invoke OMEGA-SECURITY
```

### 5. Adaptive Depth

Scale monitoring intensity to situation:
```
ROUTINE: Session start health check. Brief. Move on.
ELEVATED: Anomaly detected. Deeper investigation. Log findings.
CRITICAL: Filing deadline <7 days or hallucination detected.
  Full QA sweep. All quality gates. User notification.
EMERGENCY: Data corruption or EAGAIN cascade.
  Full stop. Recovery protocol. Detailed incident report.
```

---

## Subordinate Skills Coordinated

### Direct Reports (OMEGA-SENTINEL coordinates these)

| Skill | Source Skills | When Invoked |
|-------|-------------|--------------|
| **OMEGA-MEMORY** | context-memory-omega, agent-memory-*, session recall, memory-systems, context-optimization, context-window-management | Memory persistence, session recall, context management |
| **OMEGA-DEVOPS** | github-*, git-*, deployment-*, observability-*, backup, system health, monitoring | Git operations, backup procedures, CI/CD, deployment |
| **OMEGA-WRITING** | documentation-*, create-readme, wiki-*, technical-blog-writing, changelog-automation | Documentation updates, README, progress reports, changelogs |
| **OMEGA-SECURITY** | security-*, pentest-*, incident-response-*, PII detection, audit patterns | Security audits, PII scanning, incident response, credential checks |

### Peer Coordination

| Peer Skill | Coordination Pattern |
|------------|---------------------|
| **OMEGA-ARCHITECT** | Sentinel detects structural anomalies → Architect assesses root cause. Architect designs monitoring → Sentinel implements it. |
| **OMEGA-ENGINEER** | Sentinel detects bugs via monitoring → Engineer fixes them. Engineer builds health checks → Sentinel runs them continuously. |
| **OMEGA-LITIGATION-SUPREME** | Supreme generates filings → Sentinel runs QA gates. Sentinel catches hallucinations → Supreme re-generates with corrections. |

---

## Sentinel Operations Checklist (use at session start and every 30 minutes)

```
□ MANBEARPIG startup protocol completed (or refreshed)
□ Deadline urgency scores reviewed — any CRITICAL or EMERGENCY?
□ No hallucination alerts active (fabricated names, inflated stats)
□ EAGAIN pressure within budget (shells ≤2, agents ≤4)
□ Last backup < 24 hours old
□ Agent fleet — no CRASH status in last hour
□ DB WAL file < 100 MB (checkpoint if larger)
□ SQL todos updated to reflect current work status
□ Progress logged (if autonomous run > 10 minutes)
□ Temp files cleaned up from previous operations
□ All agent results retrieved and cached (no pending read_agent)
□ Disk space adequate (> 10 GB free on C:\)
```
