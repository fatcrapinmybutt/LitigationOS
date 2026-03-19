# ADR-0003: Agent Fleet Architecture — ReAct Loop + Memory + Tool Registry

- **Status:** Accepted
- **Date:** 2026-03-06
- **Deciders:** Andrew Pigors

## Context

LitigationOS operates a fleet of **155+ agents** across 5 fleets:

| Fleet | Count | Role |
|-------|-------|------|
| Delta9 (A01–L08) | 56 | Core pipeline — I/O, intelligence, convergence |
| Delta999 | 12 | Advanced engines — classifier, validator, brief, assembly |
| Copilot agents | 64 | Specialized sub-agents in `.copilot/agents/` |
| Superpower | 13 | Cross-cutting orchestration, governance, self-evolution |
| Convergence | 10 | Phase 5–6 hardening, filing workflow, complaint prep |

All agents inherit from `Agent9999` (`agents/agent_base.py`) with the contract:
```python
run() → AgentResult(agent_id, status, stats)  # Status: SUCCESS | FATAL | CRASH
```

### Current Problems

1. **GOAWAY crashes (27–40 minutes):** Agents lose all in-progress work when the session terminates. No checkpointing means hours of processing vanish.
2. **No persistent memory:** Each agent run starts from zero. An agent that encountered and solved a problem last Tuesday will hit the same problem again and fail the same way before eventually recovering.
3. **EAGAIN / SQLITE_BUSY:** Maximum 3 concurrent background agents. Exceeding this causes database lock contention and cascading failures.
4. **No self-correction:** The 7-Layer Error Protocol provides escalation (retry → skip → checkpoint → deadman → fallback) but agents don't **learn** from errors. They repeat the same mistakes.
5. **Tool overload:** Every agent has access to every tool, even when irrelevant. I/O agents don't need judicial analysis tools; intelligence agents don't need file-move tools.

### First Steps Already Taken

- `agent_memory` table created this session with 43 entries — the first persistent memory store.
- `v_agent_memory_search` view provides basic semantic search over memory entries.
- `db_lock_manager.py` with `managed_db()` context manager enforces WAL mode and busy timeouts.

## Decision Drivers

- Agents must survive GOAWAY crashes without losing work
- Agents must learn from prior runs (errors, solutions, patterns)
- Agents must reason before acting (not just execute a fixed script)
- Agent concurrency must respect the 3-agent EAGAIN limit
- Each agent tier should only access tools relevant to its role
- Must be incrementally adoptable — cannot rewrite 155 agents at once

## Considered Options

### Option 1: ReAct Loop + Persistent Memory + Selective Tool Registry — **CHOSEN**

Enhance the `Agent9999` base class with a ReAct (Reason-Act-Observe) loop, persistent memory via `agent_memory` table, and tier-scoped tool registries.

### Option 2: Plan-and-Execute Pattern

Agents create a complete plan upfront, then execute it step by step. Used by systems like BabyAGI.

### Option 3: Full Autonomous Agents

Unbounded agent loops that run until they decide they're done, with full tool access and self-directed goals.

### Option 4: Keep Current Simple `run()` Contract

Maintain the existing architecture with incremental bug fixes.

## Decision

Adopt a **three-pillar enhancement** to the agent fleet architecture:

### Pillar 1: ReAct Loop

Each agent execution follows a Reason-Act-Observe cycle with a bounded iteration limit:

```
For iteration 1..MAX_ITERATIONS (default: 10):
  1. REASON: Analyze current state, check memory for relevant context
  2. ACT: Execute one tool/operation from the agent's registry
  3. OBSERVE: Evaluate the result — success, failure, or needs more work
  4. CHECKPOINT: Write progress to agent_memory + filesystem
  
  If task complete → return AgentResult(SUCCESS)
  If blocked → return AgentResult(BLOCKED, reason)

If MAX_ITERATIONS reached → return AgentResult(TIMEOUT)
```

### Pillar 2: Persistent Memory

```sql
-- Existing table (enhanced)
CREATE TABLE agent_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    category TEXT NOT NULL,       -- 'error', 'solution', 'pattern', 'checkpoint', 'learning'
    content TEXT NOT NULL,
    context_json TEXT,            -- structured metadata (file paths, error codes, etc.)
    confidence REAL DEFAULT 0.5,  -- 0.0 to 1.0, decays over time
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    last_accessed TEXT,
    access_count INTEGER DEFAULT 0
);

-- Semantic search view
CREATE VIEW v_agent_memory_search AS
SELECT *, 
    confidence * (1.0 - (julianday('now') - julianday(created_at)) / 365.0) AS relevance
FROM agent_memory
ORDER BY relevance DESC;
```

Memory lifecycle:
- **Write:** After every significant action (error encountered, solution found, pattern detected)
- **Read:** At the start of each ReAct iteration — "have I seen this before?"
- **Decay:** Confidence decreases over time. Frequently accessed memories maintain high relevance.
- **Prune:** Memories below 0.1 relevance are archived (not deleted) quarterly.

### Pillar 3: Selective Tool Registry

```python
TOOL_REGISTRY = {
    "tier_io": [          # A01-A12: I/O agents
        "file_read", "file_write", "file_move",
        "zip_extract", "pdf_extract", "ocr_scan",
        "hash_sha256", "manifest_update"
    ],
    "tier_intel": [       # J01-L08: Intelligence agents
        "db_query", "db_write", "fts_search",
        "classify_document", "detect_lane", "score_evidence",
        "extract_entities", "summarize", "reason_llm"
    ],
    "tier_convergence": [ # F01-F06: Filing agents
        "filing_assemble", "filing_validate", "lint_check",
        "bates_stamp", "exhibit_index", "akn_generate",
        "service_proof", "efiling_prep"
    ],
    "tier_super": [       # Superpower agents: orchestration
        "agent_spawn", "agent_status", "agent_stop",
        "memory_search", "memory_write",
        "checkpoint_read", "checkpoint_write"
    ]
}
```

Agents receive only their tier's tools at initialization. Cross-tier tool access requires explicit escalation through the orchestrator.

## Rationale

### Why ReAct (Option 1)

- **Bounded reasoning:** Max 10 iterations prevents unbounded loops (unlike Option 3) while allowing self-correction (unlike Option 4).
- **Observable:** Each Reason-Act-Observe step is logged, creating an audit trail of agent decision-making.
- **Self-correcting:** When an action fails, the agent reasons about the failure, checks memory for prior solutions, and adapts — this is the key capability missing from the current architecture.
- **Checkpoint-friendly:** Each iteration is a natural checkpoint boundary. If GOAWAY hits, the agent resumes from the last completed iteration.

### Why Not Plan-and-Execute (Option 2)

- Litigation evidence is highly variable — a plan created at the start may be invalid after the first file is processed.
- Requires the agent to predict all steps upfront, which is infeasible when processing unknown file types and formats.
- No built-in self-correction; if the plan fails, the agent is stuck.

### Why Not Full Autonomous (Option 3)

- Unbounded loops risk exhausting the 3-agent EAGAIN limit indefinitely.
- No guaranteed termination — an agent could loop forever on a hard problem.
- Difficult to debug and audit when agents make unconstrained decisions.

### Why Not Status Quo (Option 4)

- Agents will continue crashing and losing work on GOAWAY.
- Agents will continue repeating the same errors without learning.
- The 7-Layer Error Protocol handles escalation but not prevention.
- The system has hit the ceiling of what simple `run()` contracts can achieve.

## Consequences

### Positive

- **Crash resilience:** Checkpointing every iteration means GOAWAY loses at most one iteration's work (~30 seconds) instead of the entire run (~30 minutes).
- **Cross-session learning:** Agent A03 that solved a Unicode encoding issue on Tuesday will recall the solution on Wednesday via `agent_memory`.
- **Reduced errors:** Self-correction within the ReAct loop catches and fixes errors before they propagate to downstream agents.
- **Tool safety:** I/O agents can't accidentally corrupt the database; intelligence agents can't accidentally move evidence files.
- **Debuggability:** Full ReAct trace (reason → act → observe) for every agent execution enables post-mortem analysis.

### Negative

- **Base class complexity:** `Agent9999` grows from a simple `run()` contract to a stateful ReAct engine. More code, more potential bugs.
- **Memory management overhead:** Reading and writing memory on every iteration adds ~50ms per cycle. For 155 agents × 10 iterations = 1,550 memory operations per full fleet run.
- **Retrofit effort:** 155+ agents must be updated to use the new base class. This must be phased to avoid breaking the fleet.
- **Memory table growth:** Without pruning, `agent_memory` could grow to millions of rows. Quarterly archival is necessary.

### Neutral

- The 7-Layer Error Protocol remains in place as the fallback beneath the ReAct loop. ReAct handles intelligent recovery; the error protocol handles catastrophic failures.

## Implementation Notes

### Phase 1: Enhanced Base Class (Week 1)

Update `Agent9999` in `agents/agent_base.py`:

```python
class Agent9999:
    MAX_ITERATIONS = 10
    CHECKPOINT_INTERVAL = 300  # seconds (5 minutes)

    def run(self) -> AgentResult:
        self._load_relevant_memories()
        for i in range(self.MAX_ITERATIONS):
            reasoning = self._reason(self.state)
            action, params = self._select_action(reasoning)
            result = self._execute(action, params)
            self._observe(result)
            self._checkpoint_if_due()
            if self._is_complete():
                return AgentResult(self.agent_id, "SUCCESS", self.stats)
        return AgentResult(self.agent_id, "TIMEOUT", self.stats)
```

### Phase 2: Memory Integration (Week 2)

- Enhance `agent_memory` table with `context_json` and `confidence` columns
- Build memory read/write methods into `Agent9999`
- Create `memory_search(agent_id, query, limit)` helper
- Add memory decay cron job

### Phase 3: Tool Registry (Week 3)

- Define tool registries per tier in `config.py`
- Modify `Agent9999.__init__()` to accept a tier and load only relevant tools
- Add tool-access audit logging

### Phase 4: Retrofit Fleet (Weeks 4–8)

Phased rollout by tier, highest-value first:

1. **Convergence agents (F01–F06):** Filing assembly is the most error-prone and benefits most from self-correction.
2. **Intelligence agents (J01–L08):** Legal analysis benefits most from memory (case law patterns, judicial behavior).
3. **I/O agents (A01–A12):** File processing benefits from remembering format quirks and extraction failures.
4. **Delta999 and Superpower:** Last, as these are already more sophisticated.

### Concurrency Guard

```python
# In agent_orchestrator.py
AGENT_SEMAPHORE = asyncio.Semaphore(3)  # EAGAIN prevention

async def run_agent(agent):
    async with AGENT_SEMAPHORE:
        return await agent.run()
```

### Monitoring

- `agent_memory` row count and category distribution reported in `STARTUP_REPORT.md`
- ReAct iteration counts tracked in `agent_log` table
- Checkpoint age alerts: if any agent's last checkpoint is >10 minutes old during a run, warn the orchestrator
