# Agent Swarm — 50+ Specialized Agents

## Architecture

The swarm operates in lanes, each handling a domain of litigation work.
The Orchestrator decides which agent runs next based on blockers + deltas.

### AGENT:ORCHESTRATOR
- **Role**: Decides which agent runs next based on blockers + deltas
- **Inputs**: User objective + repo state + indices + blockers
- **Outputs**: Cycle plan: DNEW, BLOCKERS, NEXT_PATCH, updated manifest pointers
- **Rule**: Stop only under convergence (DNEW=empty, quality>=95, RedTeam=nits only)

## Lane Summary

| Lane | Agents | Reference |
|------|--------|-----------|
| Authority (Michigan-first) | 7 | [authority-lane.md](authority-lane.md) |
| Evidence | 7 | [evidence-lane.md](evidence-lane.md) |
| Chronology & Contradictions | 5 | [evidence-lane.md](evidence-lane.md) |
| Drafting (Court-Grade) | 7 | [drafting-lane.md](drafting-lane.md) |
| Packaging | 4 | [utility-lane.md](utility-lane.md) |
| Product (App/Website) | 7 | [utility-lane.md](utility-lane.md) |
| Utility | 13 | [utility-lane.md](utility-lane.md) |

## Dispatching

Use `litigation_swarm_dispatch` to assign tasks:
```
litigation_swarm_dispatch(task="rebuild authority chains for MCR 3.206", agents=["AUTH_HARVESTER", "PINPOINT_ENGINE"])
```

Or query agent specs:
```
litigation_get_subagent_spec(agent_name="TIMELINE_BUILDER")
```
