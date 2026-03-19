# Gotchas — ai-agent-architect-omega

## Anti-Rationalization Table

| # | Excuse (The Lie) | Reality (The Truth) | Consequence |
|---|-----------------|---------------------|-------------|
| 1 | "I need 5 parallel agents for maximum throughput on this task." | LitigationOS hard limit: max 3 background agents concurrent (4 in EAGAIN v3.0, but 3 is the safe operational ceiling). Each agent uses isolated pipes, but OS process pressure + DB connection contention still exists. Past sessions crashed with EAGAIN after spawning 4+ agents. | `write EAGAIN` pipe buffer overflow. All shells become invalid. Entire session requires restart. 20+ minutes of work lost. |
| 2 | "The agent completed — I'll read its results after I finish this other task." | Context compaction can clear agent results at ANY time. If you don't call `read_agent` immediately on completion notification, the results may be gone. Past sessions lost an entire 12-packet placeholder fill because agent-60 results were never retrieved. | All work done by the completed agent is permanently lost. Must re-run the entire agent task from scratch. |
| 3 | "I designed a 6-agent pipeline with automatic handoffs — it's elegant." | Over-engineering agent systems is the #1 failure mode. A single well-prompted general-purpose agent outperforms a 6-agent pipeline 90% of the time. More agents = more coordination overhead, more failure points, more EAGAIN risk, more context loss. | System is fragile, slow, and unmaintainable. Each agent handoff loses context. Debugging a 6-agent failure chain is nearly impossible. |
| 4 | "My agent can handle this autonomously — no checkpoints needed." | GOAWAY 503 errors kill agents after 27-40 minutes. Without checkpoints, everything since the last save is lost. The MANBEARPIG rule: checkpoint to SQL todos + filesystem every 10 minutes or every 3 agent completions. | Agent dies at minute 35. Zero recovery point. 35 minutes of autonomous work vanishes. User frustration level: maximum. |
| 5 | "I'll give the agent full creative freedom — it knows what tools to use." | Agents hallucinate capabilities they don't have. A `task(explore)` agent has grep/glob/view/bash but NOT edit/create. A `task(task)` agent can run commands but has Haiku model (less reasoning power). Mismatching agent type to task = guaranteed failure. | Agent tries to edit a file but has no edit tool → hallucinates success → downstream steps build on nonexistent changes → cascade failure. |
| 6 | "I spawned agents for all sub-tasks — now I'll wait for all of them." | Waiting for all agents blocks your progress. Some agents may be stuck or slow. Always process results as they arrive — read completed agents immediately, start next wave while slow agents finish. Batch-and-wait is an anti-pattern. | Session stalls for 10+ minutes waiting for one slow agent while 3 completed agents' results are aging and at risk of compaction loss. |
| 7 | "The agent fleet is 155+ agents, so my new agent is just one more." | Every new agent must: (a) inherit Agent9999 base class, (b) implement `run() → AgentResult(agent_id, status, stats)`, (c) register in `master_index.db`, (d) fit into a tier (I/O: 1-3, Intelligence: J/K/L, Convergence: F), (e) follow the 7-layer error protocol. Skipping any step breaks the orchestrator. | Orphan agent: not discovered by orchestrator, not included in fleet runs, no error recovery, no checkpoint integration. Wastes resources silently. |

---

## Common Failure Modes

### 1. EAGAIN Cascade from Agent Over-Spawn
- **What happens**: More than 3 agents are spawned concurrently. Even though agent pipes are isolated, OS file descriptor pressure + DB connection contention triggers cascading failures. PowerShell sessions become invalid.
- **How to prevent**: Before spawning ANY agent: `list_agents` → count RUNNING (not completed/idle) → must be < 3. Wait 0.5-1 second between spawns. Max 2 agents in parallel in one tool call.
- **Risk level**: HIGH

### 2. Agent Result Loss via Context Compaction
- **What happens**: An agent completes successfully but `read_agent` is not called immediately. Context compaction runs, clearing the agent's result buffer. When finally read, the results are empty or truncated.
- **How to prevent**: On EVERY `system_notification` of agent completion → call `read_agent` IMMEDIATELY in the next response. Cache critical results in session SQL: `INSERT INTO agent_results (agent_id, task, result) VALUES (...)`.
- **Risk level**: HIGH

### 3. Wrong Agent Type Selection
- **What happens**: A code-editing task is assigned to an `explore` agent (which has no edit/create tools), or a complex reasoning task is assigned to a `task` agent (which uses Haiku, a less capable model).
- **How to prevent**: Match agent type to need: `explore` = read-only investigation (Haiku), `task` = command execution with pass/fail (Haiku), `general-purpose` = complex multi-step work (Sonnet), `code-review` = diff analysis (read-only).
- **Risk level**: MEDIUM

### 4. Missing Checkpoint Before Long Autonomous Run
- **What happens**: An agent is launched for a 30+ minute autonomous task without checkpoint instructions. GOAWAY 503 kills it at minute 27. No intermediate results saved.
- **How to prevent**: For any task expected to take >15 minutes, break into waves of 3 sub-tasks max. Include checkpoint instructions in the agent prompt: "After each sub-task, write progress to `00_SYSTEM/PROGRESS_LOG.md`."
- **Risk level**: HIGH

### 5. Circular Agent Dependencies
- **What happens**: Agent A waits for Agent B's output, but Agent B was designed to consume Agent A's output. Deadlock — neither agent can proceed.
- **How to prevent**: Always draw the dependency graph before launching multi-agent workflows. Use `todo_deps` table to track dependencies. No cycles allowed — topological sort must succeed.
- **Risk level**: MEDIUM

---

## Integration Gotchas

- **Agent9999 base class**: All fleet agents inherit from `agents/agent_base.py`. The contract is `run() → AgentResult(agent_id, status, stats)`. Status must be SUCCESS, FATAL, or CRASH. Anything else breaks the orchestrator's status aggregation.
- **master_index.db**: Agent registration database (SQLite WAL mode). Tables: `files`, `ready_queue`, `dedup_clusters`, `zip_contents`, `atoms`, `judicial_findings`, `action_scores`, `agent_log`. New agents must register here.
- **7-Layer Error Protocol**: Every agent must implement all 7 layers: try → specific catch → broad catch → checkpoint → deadman switch (120s) → retry (3× exponential) → tier fallback. Skipping layers means unrecoverable crashes.
- **EAGAIN + agents**: Agents use ISOLATED pipes (safe). But agents that internally spawn PowerShell sub-processes create SHARED pipes. If your agent design calls shell commands, route through `exec_command` MCP, not `powershell` tool.
- **DB connections in agents**: Agents share the 3-connection pool via `managed_db()` semaphore. An agent that holds a DB connection for its entire lifetime starves other agents. Open connections briefly, use them, close immediately.
