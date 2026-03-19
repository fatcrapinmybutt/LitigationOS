# Gotchas — multi-agent-brainstorming

## Anti-Rationalization Table

| # | Excuse (The Lie) | Reality (The Truth) | Consequence |
|---|-----------------|---------------------|-------------|
| 1 | "More review agents = more thorough review" | Every agent consumes an isolated pipe and context window. Spawning 5 review agents simultaneously exceeds the 4-agent EAGAIN limit. The 5th agent either crashes or blocks, and its review is lost. | EAGAIN cascade, agent results lost to pipe overflow, multi-agent review incomplete with no record of what was covered. |
| 2 | "I'll read the agent results after all reviewers finish" | Context compaction can clear agent results at ANY time. If you don't call `read_agent` immediately on completion notification, the work is gone. Past sessions lost entire 12-packet reviews this way. | Skeptic agent spent 3 minutes identifying critical flaws in the filing strategy. Results never read. Flaws ship to court. |
| 3 | "The agents will naturally synthesize their feedback" | Agents are stateless. The Skeptic doesn't know what the Constraint Guardian said. The User Advocate can't build on the Skeptic's findings. Without explicit synthesis by the Integrator, feedback is fragmented and contradictory. | Three reviewers flag the same issue differently, two contradict each other, none addresses the actual highest-risk gap. Designer picks the easiest feedback to address, ignores the rest. |
| 4 | "Running reviewers in parallel saves time" | The process is SEQUENTIAL by design — Skeptic → Constraint Guardian → User Advocate → Integrator. Running them in parallel means later reviewers can't build on earlier findings. And parallel agent spawns still risk EAGAIN if combined with shells. | Parallel reviewers produce redundant feedback (all three flag the same surface issue), while the deeper systemic flaw that requires sequential reasoning goes undetected. |
| 5 | "The review is taking too long — let's skip the Integrator" | The Integrator/Arbiter is the only agent authorized to resolve conflicts between reviewers and declare the design complete. Without arbitration, conflicting feedback creates decision paralysis. | Skeptic says "remove feature X", User Advocate says "feature X is critical for usability." No resolution. Designer picks the one they agree with, not the one that's correct. |
| 6 | "We ran the review — the design is validated" | Running the process doesn't equal quality. If agents were poorly prompted, if the design document was incomplete, or if reviewer scope wasn't enforced, the review is theater — it looks thorough but caught nothing. | False confidence. "We did multi-agent review" becomes a rationalization for shipping a flawed design. The review stamp becomes a rubber stamp. |
| 7 | "I'll checkpoint results at the end of the full review" | GOAWAY 503 errors kill agent sessions after 27-40 minutes. A full 5-agent sequential review can take 15-25 minutes. If you don't checkpoint after each agent completes, a crash at agent 4 loses agents 1-3 results too. | 20 minutes of review work lost to a single timeout. Agent results weren't cached to session SQL. Must restart the entire review from scratch — if the deadline hasn't passed. |

---

## Common Failure Modes

### 1. Agent Count Explosion
- **What happens**: The orchestrator spawns more than 4 concurrent agents (the EAGAIN-safe limit). This commonly happens when the primary designer, skeptic, and constraint guardian are all running simultaneously while background agents from other tasks are still active.
- **How to prevent**: Before spawning any review agent, run `list_agents` to count running agents. Wait for previous agents to complete before spawning the next reviewer. The review process is sequential by design — respect that.
- **Risk level**: HIGH

### 2. Lost Results to Context Compaction
- **What happens**: An agent completes its review, the system sends a notification, but the orchestrator is busy with another task. By the time it reads the agent result, context compaction has cleared it.
- **How to prevent**: On EVERY agent completion notification, call `read_agent` IMMEDIATELY in your next response. Cache critical results to session SQL: `INSERT INTO agent_results (agent_id, role, findings) VALUES (...)`.
- **Risk level**: HIGH

### 3. Redundant Agent Work
- **What happens**: Without proper scoping, multiple reviewer agents flag the same obvious issues (e.g., "missing error handling") while missing deeper, role-specific concerns. The Skeptic and Constraint Guardian produce nearly identical feedback.
- **How to prevent**: Prompt each agent with its EXACT role constraints from the skill definition. Include in the prompt what previous reviewers already flagged, so later reviewers can focus on their unique domain.
- **Risk level**: MEDIUM

### 4. Failure to Synthesize
- **What happens**: Four reviewers produce four separate feedback documents. The Designer addresses them piecemeal, fixing contradictions in opposite directions. No single coherent revision emerges.
- **How to prevent**: The Integrator/Arbiter MUST receive ALL reviewer feedback before arbitrating. Compile all feedback into a single document before the Integrator runs. The Integrator's output is the authoritative revision guide.
- **Risk level**: MEDIUM

### 5. Process Timeout Under Deadlines
- **What happens**: The full sequential review (5 agents × 3-5 minutes each) takes 15-25 minutes. Combined with GOAWAY 503 timeout risk at 27-40 minutes, the review may not complete in a single session.
- **How to prevent**: Checkpoint after each agent phase. If the session is approaching 25 minutes, save all collected results to session SQL and create a continuation todo. The review can resume in a new session.
- **Risk level**: MEDIUM

---

## Integration Gotchas

- **Brainstorming skill is a prerequisite**: Multi-agent-brainstorming expects a completed design from the `brainstorming` skill as input. The Understanding Lock must already be confirmed. Don't invoke multi-agent review on a raw, unstructured idea.
- **EAGAIN budget is shared**: The 4-agent limit is system-wide, not per-skill. If other tasks have 2 agents running, you only have budget for 2 review agents. Check `list_agents` before every spawn.
- **Session SQL for checkpointing**: Create an `agent_results` table at the start of any multi-agent review. After each reviewer completes, INSERT their findings. This survives context compaction and session crashes.
- **Exit disposition is mandatory**: When invoked by an orchestration layer, the skill MUST report APPROVED, REVISE, or REJECT. Don't let the review end without an explicit disposition from the Integrator.
- **Lane scoping carries through**: If the brainstorm was scoped to Lane A (Custody), ALL review agents must stay in Lane A. A reviewer suggesting PPO strategies (Lane D) is violating lane isolation.
