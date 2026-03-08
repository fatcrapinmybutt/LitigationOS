---
description: Shell session management rules for Copilot agents in LitigationOS. Apply when running PowerShell commands, spawning sub-agents, or performing multi-step operations. CRITICAL — violations cause unrecoverable "Invalid shell ID" crashes.
applyTo: "**/*"
---

# Shell Session Management — ENFORCED Rules (v3.0)

Hard-won rules from 200+ stale session crashes. Violating these WILL cause "Invalid shell ID" errors
that cannot be recovered without restarting the entire Copilot session.

## The Root Cause

PowerShell sessions are finite OS resources managed by the Copilot CLI runtime.
When an agent creates 20+ sessions without cleanup, the runtime exhausts its pool.
New session IDs become invalid immediately after creation — the telltale sign is
`"Invalid shell ID: X"` on a shell you JUST created. Once this happens, NO new shells
can be created until ALL existing sessions are stopped and the pool resets.

## Prevention Rules (MANDATORY — Zero Tolerance)

### 1. HARD LIMIT: Max 3 Concurrent Async Shells

**Before creating ANY new shell**, count existing shells. If 3+ async shells exist, you MUST
stop one before creating another. This is NOT a guideline — it is a hard resource limit.
Exceeding it corrupts the session pool for the rest of the agent run.

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

This error means the pool is exhausted. Recovery requires a full flush:
1. Call `list_powershell` to see all sessions
2. Call `stop_powershell` on EVERY session listed (no exceptions)
3. Wait 5 seconds for the runtime to reclaim resources
4. Create ONE new shell with a named ID to verify recovery
5. If it still fails, the Copilot session must be restarted

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

## Sub-Agent Shell Budget

When spawning sub-agents via `task` tool:
- Each sub-agent gets its own shell sessions
- **Limit to 2 parallel sub-agents** to stay under the total session budget
- Sub-agent shells auto-cleanup on completion, but count toward the global limit while running
- Before spawning a sub-agent, ensure main session has ≤1 active async shell
