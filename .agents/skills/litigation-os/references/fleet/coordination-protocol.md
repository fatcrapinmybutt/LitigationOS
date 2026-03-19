# Fleet Coordination Protocol

## Data Flow Between Agents

Agents communicate via output contracts. Each agent produces structured blocks that downstream agents consume.

### Output Contract Flow

```
[CS] CASE_STATE ───→ Any agent (context)
[VM] VehicleMap ───→ filing-architect → brief-writer → red-team
[AT] AuthorityTriples ───→ authority-validator → brief-writer
[EX] ExhibitMatrix ───→ evidence-harvester → filing-architect
[CM] ContradictionMap ───→ impeachment-engine → red-team
[TL] Timeline ───→ Any agent (chronology)
[VR] Red Team Report ───→ red-team → filing-architect (revisions)
[SBNA] Next Action ───→ Any agent (prioritization)
```

## Handoff Rules

### 1. Lane Isolation
Every handoff MUST preserve lane assignment. An agent receiving work from Lane A MUST NOT produce Lane B outputs.

### 2. Evidence Posture Preservation
Atoms passed between agents retain their posture tags. An agent MUST NOT upgrade ALLEGATION to RECORD_FACT.

### 3. Provenance Chain
Every output block includes the producing agent name and cycle timestamp.

### 4. Error Escalation
If an agent encounters a blocker it cannot resolve:
1. Log the blocker with error code
2. Return partial results with `STATUS: BLOCKED`
3. Core orchestrator re-routes to alternative agent or escalates

### 5. Convergence Integration
All agent outputs feed into the convergence cycle:
- DNEW: New information discovered by any agent
- BLOCKERS: Issues any agent cannot resolve
- NEXT_PATCH: Highest-leverage fix across all agents

## Anti-Patterns

| Anti-Pattern | Correct Behavior |
|-------------|-----------------|
| Agent A calls Agent B directly | Route through core dispatcher |
| Agent modifies another agent's output | Create new output block, reference original |
| Agent ignores lane assignment | STOP. Delete output. Re-run with correct lane. |
| Agent upgrades evidence posture | Only evidence-harvester assigns posture from source verification |
| Agent skips red-team in FILE_READY mode | Red-team is MANDATORY before any court submission |
