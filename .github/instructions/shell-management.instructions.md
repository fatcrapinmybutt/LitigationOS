---
description: Shell session management rules for Copilot agents in LitigationOS. Apply when running PowerShell commands, spawning sub-agents, or performing multi-step operations.
applyTo: "**/*"
---

# Shell Session Management — Permanent Rules

Hard-won rules from 200+ stale session crashes. Violating these WILL cause "Invalid shell ID" errors.

## The Root Cause

PowerShell sessions are finite OS resources. When an agent creates 20+ sessions without
cleaning up, the runtime exhausts its session pool. New session IDs become invalid immediately
after creation — the telltale sign is `"Invalid shell ID: X"` on a shell you JUST created.

## Prevention Rules (MANDATORY)

### 1. One Shell at a Time (Sync)

For sync commands, reuse the same shell when possible. Chain commands with `&&`:

```powershell
# GOOD — one shell, three commands
cd C:\Users\andre\LitigationOS && git --no-pager status && git --no-pager diff --stat

# BAD — three separate shells for related commands
# Shell 1: cd C:\Users\andre\LitigationOS
# Shell 2: git status
# Shell 3: git diff
```

### 2. Max 3 Concurrent Async Shells

Never have more than 3 async shells running simultaneously. Before creating a new async
shell, call `list_powershell` and count active sessions. If 3+ exist, WAIT or STOP one.

### 3. Always Stop Completed Async Shells

After reading output from an async shell, immediately `stop_powershell` it. Don't leave
completed shells dangling.

### 4. Use Named Shell IDs

Always provide explicit `shellId` values (e.g., `"build"`, `"test"`, `"lint"`). This makes
cleanup deterministic — you know exactly which shells to stop.

### 5. Pre-flight Cleanup at Session Start

At the start of every multi-step operation, run:
```
list_powershell  →  stop all completed/stale sessions  →  then proceed
```

### 6. Recovery Protocol

If you see "Invalid shell ID" on a fresh shell:
1. Call `list_powershell` to see all sessions
2. Stop ALL sessions with `stop_powershell`
3. Wait 5 seconds
4. Try again with a new shell

## Safe Python Execution

Never use `python -c "..."` in PowerShell — backslashes and quotes break. Instead:

```powershell
# Load the agent profile first
. C:\Users\andre\LitigationOS\00_SYSTEM\tools\agent_profile.ps1

# Then use safe wrappers:
sspy file1.py file2.py    # syntax check (AST parse, no imports)
srun script.py --arg      # safe run (avoids shadow modules)
spy "print(1+1)"          # safe inline Python (temp file, not -c)
senv                      # environment health check
sshadow                   # shadow module audit
```

Or use the toolkit directly:
```powershell
$env:PYTHONUTF8 = "1"
python C:\Users\andre\LitigationOS\00_SYSTEM\tools\safe_shell.py check file.py
python C:\Users\andre\LitigationOS\00_SYSTEM\tools\safe_shell.py run script.py
```

## Shadow Modules (22 in Repo Root)

The repo root contains `json.py`, `typing.py`, `tokenize.py`, `numpy.py`, `pandas.py` and 17
others that shadow Python stdlib/third-party modules. NEVER set CWD to the repo root when
running Python. Use `safe_run()` or set CWD to the script's own directory.

## Sub-Agent Shell Budget

When spawning sub-agents via `task` tool:
- Each sub-agent gets its own shell sessions
- Limit to 2 parallel sub-agents to stay under the total session budget
- Sub-agent shells auto-cleanup on completion, but count toward the global limit while running
