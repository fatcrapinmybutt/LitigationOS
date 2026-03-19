# Multi-Agent Coordination Patterns

## Overview

Multi-agent brainstorming in LitigationOS uses background agents via the `task` tool.
Each agent runs in an isolated process with its own pipe budget. Coordination patterns
determine how agents interact, share results, and converge on decisions without
exceeding system resource limits.

---

## Pattern 1: Sequential Review Chain

The default pattern for multi-agent brainstorming. Each reviewer runs after the
previous one completes, building on accumulated feedback.

### Flow
```
Designer → Skeptic → Guardian → Advocate → Integrator
   ↓          ↓          ↓          ↓           ↓
 Design    Risks     Constraints  UX Issues   Resolution
```

### Implementation
```
Step 1: Spawn Designer agent (background mode)
Step 2: read_agent → get design output
Step 3: Spawn Skeptic agent with design + "find failures"
Step 4: read_agent → get skeptic feedback
Step 5: Spawn Guardian agent with design + skeptic feedback
Step 6: read_agent → get guardian assessment
Step 7: Spawn Advocate agent with full context
Step 8: read_agent → get advocate concerns
Step 9: Spawn Integrator with ALL feedback
Step 10: read_agent → get final disposition
```

### Resource Profile
- Max 1 agent running at a time
- Total: 5 sequential agents
- Estimated time: 15-25 minutes
- EAGAIN risk: ZERO (sequential = never concurrent)

---

## Pattern 2: Parallel Review with Synthesis

Two or three reviewers run simultaneously, then an integrator synthesizes.
Faster but requires careful EAGAIN management.

### Flow
```
         Designer
        /    |    \
   Skeptic  Guardian  Advocate  (parallel — max 3)
        \    |    /
       Integrator
```

### Implementation
```
Step 1: Designer produces design (sync or background)
Step 2: Spawn Skeptic + Guardian + Advocate in ONE tool call (3 parallel agents)
Step 3: read_agent for each as they complete
Step 4: Cache all results to session SQL immediately
Step 5: Spawn Integrator with compiled feedback
Step 6: read_agent → final disposition
```

### Resource Profile
- Max 3 agents concurrent (at the EAGAIN limit)
- Total: 5 agents (3 parallel + 2 sequential)
- Estimated time: 8-12 minutes
- EAGAIN risk: MODERATE (must ensure no other agents are running)

### Pre-Flight Check
Before spawning the parallel batch:
```
list_agents → running count must be 0
list_powershell → active shells must be ≤ 1
Only then: spawn 3 reviewer agents in one tool call
```

---

## Pattern 3: Diverge-Converge Cycle

Multiple agents independently propose solutions to the same problem,
then a synthesis agent merges the best elements.

### Flow
```
         Problem Statement
        /       |        \
   Agent A   Agent B   Agent C   (independent proposals)
        \       |        /
        Synthesis Agent          (merge best elements)
             |
        Evaluation Agent         (score merged proposal)
```

### When to Use
- Problem has no obvious "right answer"
- Need creative diversity (each agent uses different framing)
- High-stakes decision where a single perspective is insufficient

### Prompting Strategy
Each divergent agent gets the SAME problem but a DIFFERENT instruction:
- Agent A: "Propose the most aggressive legal strategy"
- Agent B: "Propose the most conservative, risk-averse strategy"
- Agent C: "Propose an unconventional approach that opposing counsel won't expect"

---

## Pattern 4: Agent Role Assignment

Each agent in the review has strict, non-overlapping scope. This prevents
redundant work and ensures comprehensive coverage.

### Role Definitions
| Role | Scope | Prohibited Actions |
|------|-------|-------------------|
| **Designer** | Creates and revises the design | Cannot self-approve |
| **Skeptic** | Identifies weaknesses and risks | Cannot propose alternatives |
| **Guardian** | Enforces constraints (MCR, deadlines, rules) | Cannot debate goals |
| **Advocate** | Represents end-user perspective | Cannot redesign architecture |
| **Integrator** | Resolves conflicts, makes final decisions | Cannot add requirements |

### Scope Enforcement in Prompts
Include scope constraints directly in agent prompts:
```
You are the SKEPTIC reviewer. Your ONLY job is to identify:
- Assumptions that may be wrong
- Risks that haven't been addressed
- Edge cases that could cause failure
- Overconfidence in any claim

You MUST NOT:
- Propose new features or alternatives
- Redesign any part of the system
- Offer solutions to the problems you identify
- Comment on style, formatting, or presentation
```

---

## Pattern 5: Checkpoint-and-Resume

For long reviews that may exceed the 27-40 minute GOAWAY timeout window.

### Checkpoint Strategy
After each agent completes:
```sql
INSERT INTO review_checkpoints (
    review_id, agent_role, agent_id, findings, status, checkpointed_at
) VALUES (
    'review-001', 'skeptic', 'agent-42',
    '{"risks": [...], "assumptions": [...]}',
    'completed', CURRENT_TIMESTAMP
);
```

### Resume Strategy
If the session crashes mid-review:
```sql
-- Find where we left off
SELECT agent_role, status FROM review_checkpoints
WHERE review_id = 'review-001'
ORDER BY checkpointed_at;

-- Resume from the next uncompleted role
```

---

## Pattern 6: Result Consolidation

After all reviewers complete, their feedback must be consolidated before
the Integrator can arbitrate.

### Consolidation Template
```markdown
# Review Consolidation — [Design Name]

## Skeptic Findings
- Risk 1: [description] (severity: HIGH/MEDIUM/LOW)
- Risk 2: [description]

## Guardian Assessment
- Constraint violation 1: [description]
- Compliance gap 1: [description]

## Advocate Concerns
- UX issue 1: [description]
- User impact: [description]

## Conflicts Between Reviewers
- Skeptic says X, Advocate says Y → Integrator must resolve
- Guardian requires Z, which conflicts with Designer's approach

## Agreed Issues (All reviewers flagged)
- Issue A: [description] → HIGH PRIORITY (consensus)
```

---

## Agent Communication Anti-Patterns

### ❌ Sharing Full Context Between All Agents
Passing the entire conversation history to every agent wastes tokens and
causes agents to re-litigate settled decisions.
**Fix**: Each agent gets only: (1) the design, (2) their role prompt, (3) prior
reviewer findings relevant to their scope.

### ❌ Agents Responding to Each Other
Agents are stateless — they can't have a conversation. Don't prompt an agent
with "respond to the Skeptic's concerns." Instead, include the relevant
concerns as context and let the agent address them independently.
**Fix**: The orchestrator (main session) handles all inter-agent communication.

### ❌ Running All Agents Simultaneously
Even though isolated pipes support 4 concurrent agents, running 5 review
agents at once exceeds the limit and risks EAGAIN.
**Fix**: Sequential (Pattern 1) or parallel-3 with sequential integrator (Pattern 2).

### ❌ Spawning Agents Without Pre-Flight Check
If 2 agents from a previous task are still running, spawning 3 review agents
means 5 concurrent — EAGAIN guaranteed.
**Fix**: Always `list_agents` before spawning. Wait for running count < 2.
