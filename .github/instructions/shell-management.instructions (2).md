---
description: Shell session management rules — GLOBAL. Apply to ALL repos, ALL workspaces, ALL agents. Prevents "Invalid shell ID" crashes from session pool exhaustion.
applyTo: "**/*"
---

# Shell Session Management — GLOBAL Rules

These rules apply to EVERY repository, EVERY workspace, EVERY Copilot agent session.
They prevent the "Invalid shell ID" crash that occurs when 20+ PowerShell sessions
accumulate without cleanup.

## Root Cause

PowerShell sessions are finite OS resources managed by the Copilot CLI runtime.
When an agent creates 20+ sessions without cleanup, the runtime exhausts its pool.
New session IDs become invalid immediately after creation.

## MANDATORY Rules

### Rule 1: Max 3 Concurrent Async Shells
Before creating ANY async shell, mentally count running shells. If 3+ exist, STOP one first.
This is a HARD LIMIT — no exceptions, no "just one more."

### Rule 2: Chain Related Commands
Use `&&` to chain related commands in ONE shell instead of separate shells:
```powershell
# CORRECT: one shell, three commands
cd C:\project && git --no-pager status && git --no-pager diff --stat

# WRONG: three separate shells
```

### Rule 3: Stop Completed Shells Immediately
After reading output from an async shell, call `stop_powershell` RIGHT AWAY.
Never leave completed shells dangling.

### Rule 4: Use Named Shell IDs
Always provide explicit `shellId` values (`"build"`, `"test"`, `"lint"`).
Named IDs make cleanup deterministic.

### Rule 5: Pre-flight Cleanup
At the start of every multi-step operation:
1. Call `list_powershell` to see all sessions
2. Stop ALL completed/stale sessions
3. Only then proceed with new commands

### Rule 6: Recovery Protocol
If you see "Invalid shell ID" on a fresh shell:
1. `list_powershell` — see all sessions
2. `stop_powershell` on ALL sessions
3. Wait 5 seconds
4. Retry with a new named shell

## Safe Python Execution

Never use `python -c "..."` — backslashes and quotes break in PowerShell.
Write Python to a temp `.py` file, execute it, then clean up.

## Sub-Agent Shell Budget

When spawning sub-agents via `task` tool:
- Each sub-agent gets its own shell sessions
- Limit to 2 parallel sub-agents to stay under the global session budget
- Sub-agent shells auto-cleanup on completion but count toward the limit while running
