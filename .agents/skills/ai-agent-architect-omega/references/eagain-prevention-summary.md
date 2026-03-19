# EAGAIN Prevention Summary — ai-agent-architect-omega

## What is EAGAIN?

`write EAGAIN` is a Node.js IPC pipe buffer overflow error. It occurs when too many PowerShell sessions consume OS pipe resources simultaneously. The kill chain:

```
1. Copilot CLI (Node.js) communicates with shells via OS pipes
2. Each PowerShell session = 3 SHARED pipes (stdin + stdout + stderr)
3. Windows pipe buffers = 64 KB each (192 KB per shell session)
4. Too many SHARED pipes exist → OS returns EAGAIN
5. Node.js fails to write → shell becomes "Invalid"
6. CASCADE: ALL new shells inherit broken pipe state
```

## Pipe Isolation Architecture (The Key Insight)

Not all processes share the same pipe pool:

| Category | Tools | Pipe Type | EAGAIN Risk | Budget |
|----------|-------|-----------|-------------|--------|
| **Zero-pipe** | view, edit, create, grep, glob, sql | None (in-process) | **ZERO** | Unlimited |
| **Isolated-pipe** | task(explore), task(task), task(general-purpose) | Own child process | **CONTAINED** | 3-4 concurrent |
| **Shared-pipe** | powershell (async/sync shells) | Main Node.js IPC | **CRITICAL** | 2 concurrent |
| **No-pipe** | MCP exec_command, exec_python, exec_git | subprocess.run() | **ZERO** | Unlimited |

**Critical distinction**: Shells are SHARED pipes (direct EAGAIN risk). Agents are ISOLATED (overflow kills only that agent). MCP commands use zero pipes. This means:
- Expanding agent count is safe (isolated pipes)
- Shell count is the ONLY variable that matters for EAGAIN
- MCP commands are always safe regardless of system state

## The Three Laws

### Law 1: Concurrency Ceiling

| Resource | Limit | Pipe Type |
|----------|-------|-----------|
| PowerShell shells | **2 max** | SHARED (dangerous) |
| Background agents | **3-4 max** | ISOLATED (safe) |
| MCP commands | **Unlimited** | None |
| Zero-pipe tools | **Unlimited** | None |

### Law 2: Output Pressure Relief

Every shell command MUST limit output:
```powershell
# ✅ GOOD — bounded output
git --no-pager log --oneline -20
Get-ChildItem | Select-Object -First 50

# ❌ BAD — unbounded (floods pipe buffer)
Get-ChildItem -Recurse          # 125K+ lines possible
git log                          # thousands of commits

# For large outputs: redirect to file
git --no-pager diff > temp\diff.txt  # then read with view tool
```

### Law 3: Immediate Cleanup

```
RULE: Shell completes → stop_powershell IMMEDIATELY
RULE: Agent completes → read_agent results → move on
RULE: Never leave a shell "open for later"
RULE: Before multi-step ops → list_powershell → stop all stale
```

## Pre-Spawn Decision Tree

```
Need to run a command?
├─ Non-interactive? → MCP exec_command (ZERO pipes, preferred)
├─ Need parallel work? → task agent (ISOLATED pipes)
│   └─ list_agents → running < 3? → spawn (0.5s cooldown)
└─ Need interactive/REPL? → powershell (SHARED pipes, LAST RESORT)
    └─ list_powershell → active < 2? → spawn (2s cooldown)
```

## Dynamic Throttle Levels

| Level | Name | Shells | Agents | MCP | Trigger |
|-------|------|--------|--------|-----|---------|
| L0 | HEALTHY | 2 | 4 | ∞ | No symptoms |
| L1 | ELEVATED | 1 | 4 | ∞ | 1 shell timeout |
| L2 | WARNING | 1 | 3 | ∞ | Agent error or 2+ shell issues |
| L3 | CRITICAL | 0 | 2 | ∞ | write EAGAIN detected |
| L4 | EMERGENCY | 0 | 1 | ∞ | Multiple EAGAIN + invalid shells |
| L5 | DEAD | 0 | 0 | ∞ | Agents also failing |

**Key**: MCP is ALWAYS available (∞) at every level — you're never truly stuck.

## Recovery Protocol

```
STEP 1: FULL STOP — No new shells or agents
STEP 2: list_powershell → stop ALL sessions
STEP 3: Wait 3-5 seconds (OS reclaims file descriptors)
STEP 4: Test MCP exec_command("Write-Output 'alive'") — should always work
STEP 5: Test ONE shell → if works, resume at L2 for 3 min
STEP 6: If shells dead → stay on MCP + agents (fully functional at L3/L4)
STEP 7: If agents also dead → MCP-only mode (L5)
STEP 8: If MCP dead → AUTONOMOS file-based (create scripts → user runs)
```

## Integration with Agent Architecture

- **Agent budget is separate from shell budget** — agents don't cause EAGAIN
- **Agents that internally call PowerShell** create shared pipes — route through MCP instead
- **DB connections in agents** — shared 3-connection pool via managed_db(), agent count doesn't increase DB pressure
- **Checkpoint before long runs** — GOAWAY 503 kills agents at 27-40 minutes
- **Cache agent results in SQL** — prevents loss from context compaction

## Why v3.0 Makes EAGAIN Structurally Impossible

```
If the main session NEVER calls powershell:
  → 0 shared pipes
  → EAGAIN is impossible

v3.0 routing: MCP for commands, agents for parallel, zero-pipe for everything else
Result: Most sessions use 0 shells → EAGAIN literally cannot occur
```
