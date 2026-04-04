---
description: Shell session management rules for Copilot agents in LitigationOS. Apply when running PowerShell commands, spawning sub-agents, or performing multi-step operations. CRITICAL — violations cause unrecoverable "Invalid shell ID" crashes and write EAGAIN.
applyTo: "**/*"
---

# Shell Session Management — ENFORCED Rules (v4.0)

> **SEE ALSO:** `eagain-prevention.instructions.md` — the master EAGAIN prevention protocol.
> This file's concurrency limits are aligned with that document's Three Laws.

Hard-won rules from 200+ stale session crashes. Violating these WILL cause "Invalid shell ID" errors
and `write EAGAIN` pipe buffer overflows that cannot be recovered without restarting the session.

## The Root Cause

PowerShell sessions are finite OS resources managed by the Copilot CLI runtime.
Each session opens 3 OS pipes (stdin/stdout/stderr) with 64 KB buffers on Windows.
When too many sessions exist concurrently, pipe buffers overflow → `write EAGAIN` →
session IDs become invalid → cascade failure kills ALL shells. The telltale signs:
- `"write EAGAIN"` in error output (pipe buffer full)
- `"Invalid shell ID: X"` on a shell you JUST created (pipe state corrupted)

Once either occurs, NO new shells can be created until ALL sessions are stopped and pipes reset.

## Prevention Rules (MANDATORY — Zero Tolerance)

### 1. HARD LIMIT: Max 2 Concurrent Async Shells (SHARED pipes — the ONLY EAGAIN vector)

> **v2.0 UPDATE:** Shells and agents have SEPARATE pipe budgets. Shells use SHARED pipes
> (direct EAGAIN risk). Agents use ISOLATED pipes (overflow kills only that agent).
> See `eagain-prevention.instructions.md` v2.0 for the engineering proof.

**Shell pre-spawn checklist (SHARED pipe budget):**
1. `list_powershell` → count active shells
2. Active shells must be < 2
3. Wait 2 seconds between shell spawns (shared pipes need buffer drain time)

**Agent pre-spawn checklist (ISOLATED pipe budget — separate from shells):**
1. `list_agents` → count RUNNING agents (exclude completed/idle)
2. Running agents must be < 3
3. Wait 1 second between agent spawns
4. Can spawn 2 agents in parallel (same tool call) — they don't share pipes
5. Can spawn 1 shell + 1 agent in same tool call — different pipe pools

### 2. Chain Related Commands — ALWAYS

Use `&&` to chain related commands in ONE shell. Creating separate shells for related
commands is the #1 cause of pool exhaustion:

```powershell
# CORRECT — one shell, three commands
cd C:\Users\andre\LitigationOS && git --no-pager status && git --no-pager diff --stat

# WRONG — three shells for one workflow (wastes 2 sessions)
# Shell 1: cd C:\Users\andre\LitigationOS
# Shell 2: git status
# Shell 3: git diff
```

### 3. Stop Completed Shells IMMEDIATELY

After reading output from ANY async shell, call `stop_powershell` on it RIGHT AWAY.
Every dangling shell consumes a pool slot. 5 dangling shells = 5 wasted slots.

### 4. Use Named Shell IDs — ALWAYS

Always provide explicit `shellId` values (`"build"`, `"test"`, `"lint"`, `"git1"`).
Named IDs make cleanup deterministic — you know exactly which shells to stop.
Auto-generated IDs lead to orphaned sessions that can't be tracked.

### 5. Pre-flight Cleanup Before Multi-Step Operations

At the start of every multi-step operation (builds, tests, commits, agent spawning):
```
Step 1: list_powershell → count active sessions
Step 2: stop_powershell on ALL completed/stale sessions
Step 3: Verify count is below 3
Step 4: Only then proceed with new commands
```

### 6. Recovery Protocol (When "Invalid shell ID" Appears)

This error means the pool is exhausted. Recovery has TWO tiers:

**Tier 1 — Pool Flush (try first):**
1. Call `list_powershell` to see all sessions
2. Call `stop_powershell` on EVERY session listed (no exceptions)
3. Wait 5 seconds for the runtime to reclaim resources
4. Create ONE new shell with a named ID to verify recovery
5. If it works, resume normal operation

**Tier 2 — AUTONOMOS Fallback (when Tier 1 fails):**
If PowerShell is completely dead (every new shell immediately invalid), switch to the
File-Based Command Protocol. This uses ONLY `create` + `view` tools — no PowerShell:

1. Write a Python script to `00_SYSTEM/autonomos/.inbox/NNN_task.cmd.py`
2. If the Command Server is running, it auto-executes and writes to `.outbox/`
3. If no server, write a standalone `.py` file and ask the user to run it
4. Read results via `view` tool on the output file

**Key files for fallback:**
- `00_SYSTEM/autonomos/shared/exec_engine.py` — ExecEngine class (shell-free execution)
- `00_SYSTEM/autonomos/shared/cmd_server.py` — File-based command server
- `00_SYSTEM/_bootstrap_autonomos.py` — One-time setup (user runs manually)

**When to switch to Tier 2:**
- 3+ consecutive "Invalid shell ID" errors on freshly created shells
- `list_powershell` returns no sessions but new shells still fail
- Shell dies before producing ANY output (not just timeout)

## Safe Python Execution

**NEVER** use `python -c "..."` in PowerShell — backslashes, quotes, and f-strings break.
Write Python to a temp `.py` file, execute it, then clean up:

```powershell
# Load the agent profile first
. C:\Users\andre\LitigationOS\00_SYSTEM\tools\agent_profile.ps1

# Then use safe wrappers:
sspy file1.py file2.py    # syntax check (AST parse, no imports)
srun script.py --arg      # safe run (avoids shadow modules)
spy "print(1+1)"          # safe inline Python (temp file, not -c)
senv                      # environment health check
sshadow                   # shadow module audit
spreflight                # kill orphan processes + clean temp files
```

Or use the toolkit directly:
```powershell
$env:PYTHONUTF8 = "1"
python C:\Users\andre\LitigationOS\00_SYSTEM\tools\safe_shell.py check file.py
python C:\Users\andre\LitigationOS\00_SYSTEM\tools\safe_shell.py run script.py
```

## Shadow Modules (22 in Repo Root)

The repo root contains `json.py`, `typing.py`, `tokenize.py`, `numpy.py`, `pandas.py` and 17
others that shadow Python stdlib/third-party modules. **NEVER** set CWD to the repo root when
running Python. Use `safe_run()` or set CWD to the script's own directory.

## Sub-Agent Shell Budget (v2.0 — EXPANDED)

When spawning sub-agents via `task` tool:
- Each sub-agent gets its own ISOLATED shell sessions (its own pipes — NOT shared with main)
- **Limit to 3 parallel sub-agents** (expanded from 2 — isolated pipes are safe)
- Sub-agent shells auto-cleanup on completion
- **Agent pipes do NOT count against main session's shell budget** (different pipe pools)
- **1-second cooldown** between spawning agents (reduced from 2s — isolated pipes)
- Can spawn **2 agents in parallel** in one tool call (they don't interfere)
- Can spawn **1 shell + 1 agent** in same tool call (different pipe pools)
- Before spawning a sub-agent, check: running agents < 3 (via `list_agents`)

## Output Volume Control (EAGAIN Prevention)

Every shell command MUST limit output to prevent pipe buffer overflow:
```powershell
# GOOD — bounded output
git --no-pager log --oneline -20
Get-ChildItem | Select-Object -First 50
pytest -q --tb=line 2>&1 | Select-Object -Last 30

# BAD — unbounded output floods pipes → write EAGAIN
Get-ChildItem -Recurse          # 125K+ files
git log                          # thousands of commits
cat large_file.txt              # entire file through pipe
```

**For large outputs:** redirect to temp file, read with `view` tool:
```powershell
git --no-pager diff > temp\diff.txt   # write to file
# Then: view("temp\diff.txt")          # read without pipes
```

## AUTONOMOS Execution Fallback

When PowerShell is completely unrecoverable, use these tools instead:

| Need | PowerShell Alternative |
|------|----------------------|
| Create directories | `create` tool → write a `.py` script → ask user to run |
| Run Python | `create` tool → write `.py` file → user runs OR cmd_server executes |
| Run shell commands | `create` a `.cmd.py` that uses `subprocess.run()` |
| Read command output | `view` tool on output files |
| Install packages | `create` a `_install.py` → user runs `python _install.py` |
| Git operations | `create` a `_git.py` → user runs it |

**File-Based Command Protocol (detailed):**
```
# Step 1: Copilot creates a command file
create → 00_SYSTEM/autonomos/.inbox/001_build_dirs.cmd.py

# Step 2: If cmd_server is running, it auto-processes
# If not, user runs: python 00_SYSTEM/autonomos/.inbox/001_build_dirs.cmd.py

# Step 3: Output appears at
view → 00_SYSTEM/autonomos/.outbox/001_build_dirs.cmd.out

# Step 4: Copilot reads the result and continues
```
