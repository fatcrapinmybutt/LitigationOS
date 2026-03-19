# Agent Design Patterns — ai-agent-architect-omega

## Agent9999 Base Class Contract

Every agent in the LitigationOS fleet (155+) inherits from `Agent9999` in `agents/agent_base.py`. The contract is non-negotiable:

```python
class Agent9999:
    """Base class for all LitigationOS agents."""

    def run(self) -> AgentResult:
        """Execute the agent's primary task.

        Returns:
            AgentResult with:
                agent_id: str       — unique identifier (e.g., "A01", "J03", "F06")
                status: str         — SUCCESS | FATAL | CRASH
                stats: dict         — execution metrics (items_processed, errors, duration)
        """
        raise NotImplementedError

# AgentResult is the universal return type
@dataclass
class AgentResult:
    agent_id: str
    status: str      # SUCCESS | FATAL | CRASH — nothing else
    stats: dict      # Must include: items_processed, errors, duration_seconds
```

## Fleet Architecture (Three Lanes)

```
Lane 1 (I/O) — Tiers 1-3: A01-A12
  ├── Tier 1: Inventory agents (A01-A04) — scan, catalog, hash
  ├── Tier 2: Dedup agents (A05-A08) — content-based dedup, cluster
  └── Tier 3: Extraction agents (A09-A12) — PDF, DOCX, structured, atomize

Lane 2 (Intelligence) — Tiers J/K/L: J01-L08
  ├── Tier J: Judicial profiling (J01-J04) — bias detection, ruling patterns
  ├── Tier K: Case intelligence (K01-K04) — evidence scoring, gap analysis
  └── Tier L: Legal analysis (L01-L08) — authority chains, citation graphs

Convergence — F01-F06
  ├── F01-F02: Filing assembly — template, variables, QA
  ├── F03-F04: Brain feed — LEXOS micro-brains, knowledge merge
  └── F05-F06: Graph build — dependency graph, CyclePack export
```

## 7-Layer Error Protocol (Every Agent)

```
Layer 1: TRY — Execute primary operation
Layer 2: SPECIFIC CATCH — Known exceptions → targeted recovery
Layer 3: BROAD CATCH — Unknown exceptions → log + skip item + continue
Layer 4: CHECKPOINT — Every N items → save progress → crash-resume possible
Layer 5: DEADMAN SWITCH — 120s no progress → self-diagnose → report
Layer 6: AGENT RETRY — 3× exponential backoff (10ms → 80ms → 640ms)
Layer 7: TIER FALLBACK — Escalate to orchestrator → flag + continue fleet
```

## Message Bus Pattern

Agents communicate through the message bus, not direct calls:

```python
# Agent publishes work product
bus.publish("tier1.inventory.complete", {
    "agent_id": "A01",
    "items_cataloged": 1247,
    "ready_queue_additions": 892
})

# Downstream agent subscribes
@bus.subscribe("tier1.inventory.complete")
def on_inventory_ready(event):
    # Tier 2 dedup agents consume this
    process_ready_queue(event["ready_queue_additions"])
```

## Plan-and-Execute Pattern (Multi-Agent)

```
1. ORCHESTRATOR receives complex task
2. PLANNER agent decomposes into ordered subtasks with dependencies
3. DISPATCHER assigns subtasks to available agents (respecting tier/capability)
4. EXECUTOR agents run subtasks in parallel (where dependency graph allows)
5. MONITOR agent tracks progress, detects stalls (deadman switch)
6. REPLAN: If subtask fails → orchestrator adjusts remaining plan
7. CONVERGE: Merge all results → validate against original goal
```

## Quality Scoring Model

```python
# Every agent output is scored on 4 dimensions:
quality_score = {
    "completeness": 0.0-1.0,  # Did the agent process all assigned items?
    "accuracy": 0.0-1.0,       # Are results factually correct? (spot-check)
    "timeliness": 0.0-1.0,     # Did it complete within expected duration?
    "resource_efficiency": 0.0-1.0  # CPU/memory/DB connections within budget?
}
# Minimum passing score: 0.7 on each dimension
# Fleet average target: 0.85+ across all dimensions
```

## Agent Registration Checklist

Before deploying a new agent to the fleet:

1. **Inherit Agent9999** — `class MyAgent(Agent9999):`
2. **Implement `run()`** — must return `AgentResult(agent_id, status, stats)`
3. **Register in master_index.db** — `INSERT INTO agent_log (agent_id, tier, description, ...)`
4. **Assign to tier** — I/O (1-3), Intelligence (J/K/L), or Convergence (F)
5. **Implement 7-layer error protocol** — all 7 layers, no shortcuts
6. **Add deadman switch** — 120s timeout with self-diagnosis
7. **Test with orchestrator dry-run** — `python -m agents.agent_orchestrator --agent MY_ID --dry-run`
8. **Document in fleet manifest** — update agent count and tier description

## Copilot Sub-Agent Types (for Task Tool)

| Type | Model | Tools | Use For |
|------|-------|-------|---------|
| `explore` | Haiku | grep/glob/view/bash | Read-only investigation, codebase Q&A |
| `task` | Haiku | All CLI tools | Command execution, builds, tests (pass/fail) |
| `general-purpose` | Sonnet | All tools | Complex multi-step work, reasoning-heavy tasks |
| `code-review` | Sonnet | All CLI (read-only) | Diff analysis, quality review |

**Key insight**: `explore` and `task` use Haiku (fast, cheap, less reasoning). `general-purpose` uses Sonnet (slower, smarter). Match agent type to task complexity.
