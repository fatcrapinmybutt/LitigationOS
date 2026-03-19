# Analysis Workflow Command

## When to Use

- Deep analysis of any legal topic, person, entity, or event
- Judicial behavior profiling and misconduct pattern detection
- Contradiction discovery across evidence sources
- Strategic assessment of adversary positions

## Quick Start

```
# By target
/analyze person "Judge McNeill"    → Judicial profile + ruling patterns + Canon violations
/analyze person "Amy Watson"       → Adversary profile + inconsistencies + impeachment opportunities
/analyze entity "Shady Oaks Homes" → Corporate structure + violations + liability exposure

# By topic
/analyze topic "parenting time orders 2024" → Authority + timeline + contradictions
/analyze event "2024-03-15 hearing"         → Transcript analysis + order comparison

# By claim
/analyze claim "IIED vs Watson"    → Elements analysis + evidence strength + gaps
```

## Analysis Pipeline

```
TARGET → GATHER → CROSS-REF → CONTRADICT → STRATEGIZE → REPORT
```

### Phase 1: TARGET
- Identify subject (person, entity, event, topic, claim)
- Classify by lane (A/B/C) — NEVER mix

### Phase 2: GATHER
- Pull all atoms, timeline entries, graph nodes related to target
- Dispatches to: **litigation-evidence-harvester** (if new evidence needed)
- MCP: `litigation_search_evolved`, `litigation_query_graph`

### Phase 3: CROSS-REF
- Cross-reference across knowledge graphs, documents, transcripts
- Dispatches to: **litigation-authority-validator** (for legal basis)
- Output: Cross-reference density map

### Phase 4: CONTRADICT
- Identify contradictions, inconsistencies, changed positions
- Dispatches to: **litigation-impeachment-engine**
- Output: [CM] ContradictionMap

### Phase 5: STRATEGIZE
- Map findings to viable legal actions + remedies
- Dispatches to: **litigation-judicial-analyst** (for judges), **litigation-red-team** (for stress-test)
- Output: Strategic recommendations + [SBNA] Single Best Next Action

### Phase 6: REPORT
Output blocks:
- `[CS] CASE_STATE` — Current case posture
- `[CM] ContradictionMap` — All discovered contradictions
- `[AT] AuthorityTriples` — Supporting authority
- `[TL] Timeline` — Relevant chronology
- `[SBNA]` — Recommended next actions (2-3 max)

## Cross-References

- [Agent Swarm](../references/agent-swarm/README.md) — 50+ agent dispatch
- [Convergence](../references/convergence/README.md) — Quality scoring
- [Fleet Dispatch](../references/fleet/dispatch-matrix.md) — Agent routing
