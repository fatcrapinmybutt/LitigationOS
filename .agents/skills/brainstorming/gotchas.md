# Gotchas — brainstorming

## Anti-Rationalization Table

| # | Excuse (The Lie) | Reality (The Truth) | Consequence |
|---|-----------------|---------------------|-------------|
| 1 | "The first idea is good enough — let's just build it" | Anchoring bias causes the first idea to dominate all subsequent thinking. In litigation, the first motion strategy you think of may miss a stronger MCR provision or a more favorable procedural angle. | Premature convergence on a suboptimal legal strategy. Filing a motion for reconsideration when a motion to disqualify under MCR 2.003 would have been dispositive. |
| 2 | "We explored alternatives — everyone agreed" | Agreement without structured challenge is groupthink, not consensus. If no one role-played the opposing counsel or the judge, the design was never stress-tested. | Emily Watson's attorney (Barnes, P55406) finds the weakness you didn't test for. Motion denied because you didn't anticipate the obvious counterargument. |
| 3 | "The idea is creative and exciting — constraints can be worked out later" | Ignoring constraints during brainstorming produces ideas that are legally impossible, procedurally barred, or factually unsupported. Michigan court rules (MCR) have strict requirements. | Beautiful filing strategy that violates MCR 7.205 page limits, misses the 21-day deadline under MCR 2.119, or cites authority from the wrong jurisdiction. |
| 4 | "We need to brainstorm more options before deciding" | Endless ideation without convergence criteria is procrastination disguised as thoroughness. In litigation, deadlines are hard — COA filing windows close, PPO hearings are scheduled. | Missed filing deadline while still "exploring options." The 42-day appeal window under MCR 7.204 doesn't wait for your brainstorm to finish. |
| 5 | "This brainstorm generated 15 ideas — we're making progress" | Quantity without evaluation is noise. 15 ideas with no feasibility check, no constraint validation, and no prioritization is worse than 3 well-vetted approaches. | Decision paralysis. User stares at 15 options, picks none, deadline approaches, panic filing with the first idea anyway — back to gotcha #1. |
| 6 | "The brainstorm output is the deliverable" | Brainstorming produces raw material, not finished products. Ideas must be validated against evidence in litigation_context.db, checked against court rules in mcr_rules.db, and tested against opposing counsel's likely arguments. | Raw brainstorm ideas presented as filing strategy. "We should argue judicial bias" without checking whether the DB actually contains evidence of specific MCR 2.003 violations. |
| 7 | "We can scope this during implementation" | Scope creep from brainstorming is the #1 cause of mega-task explosions in LitigationOS. A brainstorm about "PPO enforcement" expands to cover custody modification, FOC contempt, and federal §1983 — 4 separate case lanes. | Agent tries to process all 4 lanes simultaneously, exceeds context window, triggers EAGAIN from spawning too many sub-agents, crashes at 27 minutes with zero deliverables saved. |

---

## Common Failure Modes

### 1. Anchoring Bias (First-Idea Fixation)
- **What happens**: The first proposed approach becomes the de facto choice. All subsequent "alternatives" are compared unfavorably to it rather than evaluated independently.
- **How to prevent**: Always generate at least 2 alternatives BEFORE evaluating any of them. Use the "Six Thinking Hats" technique to force different perspectives. Explicitly ask: "What would opposing counsel argue?"
- **Risk level**: HIGH

### 2. Premature Convergence
- **What happens**: The brainstorm skips from idea generation straight to implementation planning without passing through the Understanding Lock gate. Assumptions go undocumented.
- **How to prevent**: Enforce the Understanding Lock (Step 4 in the process). No design proceeds without explicit user confirmation. Document all assumptions before evaluating approaches.
- **Risk level**: HIGH

### 3. Constraint Blindness
- **What happens**: Ideas are evaluated on creativity and impact but not on feasibility within Michigan court rules, filing deadlines, evidence availability, or procedural requirements.
- **How to prevent**: After generating ideas, run each through a constraint checklist: MCR compliance? Evidence exists in DB? Deadline feasible? Procedurally permitted at this stage? Within the correct case lane?
- **Risk level**: HIGH

### 4. Scope Explosion
- **What happens**: A focused brainstorm ("how to respond to this motion") expands into adjacent topics ("and also we should file for custody modification and also challenge the FOC and also..."). Each expansion is reasonable in isolation but collectively exceeds capacity.
- **How to prevent**: Define explicit non-goals at the start of every brainstorm. If scope expands beyond the original lane, create a separate todo for the new lane and return to the original topic.
- **Risk level**: MEDIUM

### 5. Unvalidated Feasibility
- **What happens**: The brainstorm produces a strategy that sounds legally compelling but isn't supported by the evidence in litigation_context.db. "Argue judicial bias" when the DB has no documented bias incidents.
- **How to prevent**: Before finalizing any litigation strategy from a brainstorm, query the DB for supporting evidence. If evidence doesn't exist, either create an acquisition task or choose a different strategy.
- **Risk level**: MEDIUM

---

## Integration Gotchas

- **Handoff to multi-agent-brainstorming**: High-impact, high-risk designs MUST be handed off to the `multi-agent-brainstorming` skill for structured review before implementation. Don't skip this gate.
- **Lane isolation**: Each brainstorm must be scoped to a single case lane (A-F). Cross-lane brainstorms go to Lane C (Convergence) and require explicit acknowledgment of multi-lane complexity.
- **Decision Log persistence**: The Decision Log from brainstorming must be persisted to session SQL or a durable file. If it only lives in conversation context, compaction will destroy it.
- **YAGNI in litigation context**: "You Aren't Gonna Need It" applies especially hard in litigation. Don't brainstorm filing strategies for hypothetical future scenarios — focus on the next actionable deadline.
