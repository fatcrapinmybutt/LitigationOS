# Emergence Signals — Convergence Orchestrator Reference

## What is Emergence?

Emergence in litigation is the appearance of patterns, connections, or
strategic opportunities that only become visible when data from multiple
sources is analyzed together. No single document, lane, or skill reveals
these patterns — they emerge from convergence.

In Pigors v Watson, emergence detection is especially critical because
the three case lanes (Watson/Custody, Shady Oaks/Housing, Convergence)
share entities, timelines, and legal theories that create cross-lane
strategic opportunities.

---

## Signal Type Specifications

### SIGNAL TYPE 1: CROSS_GRAPH

```yaml
signal: CROSS_GRAPH
description: >
  Pattern that spans two or more case lanes, connecting entities,
  events, or legal theories across Lane A ↔ B ↔ C boundaries.
detection_method:
  1. Build entity graph per lane (persons, locations, dates, documents)
  2. Compute entity overlap between lane pairs (A↔B, B↔C, A↔C)
  3. For each shared entity, compare attributes across lanes
  4. Flag entities with >3 connections across lanes
  5. Score cross-graph strength (connections × relevance)
examples:
  - entity: "Watson"
    lane_a: "Respondent in custody case, alleged alienation"
    lane_b: "Former resident of Shady Oaks property"
    emergence: "Watson's housing instability at Shady Oaks directly
               relevant to custody fitness under MCL 722.23(d)"
    novelty: 8
  - entity: "Property condition"
    lane_a: "Children's living environment safety concern"
    lane_b: "Housing code violations documented by inspector"
    emergence: "Housing inspection reports become custody evidence
               under MCL 722.23(c) and (g)"
    novelty: 7
  - entity: "Timeline overlap"
    lane_a: "Custody hearing scheduled March 2025"
    lane_b: "Housing complaint filed February 2025"
    emergence: "Proximity suggests coordinated litigation strategy
               or shared fact pattern needing unified presentation"
    novelty: 6
thresholds:
  minimum_connections: 3
  novelty_threshold: 6
  attorney_review_threshold: 8
```

### SIGNAL TYPE 2: CHAIN_COMPLETE

```yaml
signal: CHAIN_COMPLETE
description: >
  An authority chain reaches full support — all required elements
  (statute + binding case + supporting case + pinpoint + currency)
  are now present for a key legal proposition.
detection_method:
  1. Monitor authority chain scores from litigation-authority-validator
  2. Track chains that were previously incomplete (score < 5)
  3. When a chain reaches 5/5, fire CHAIN_COMPLETE event
  4. Check if completion unlocks dependent propositions
  5. Evaluate strategic impact of newly complete chain
examples:
  - chain: "All 12 best-interest factors fully cited"
    previous_score: 3/5 (factors f, g, j were missing authority)
    new_score: 5/5
    impact: "Custody motion can now proceed with full authority support"
    novelty: 7
  - chain: "Warranty of habitability complete chain"
    previous_score: 4/5 (missing supporting case)
    new_score: 5/5
    impact: "Housing claim fully supported, ready for summary disposition"
    novelty: 5
thresholds:
  trigger_on_score: 5 (complete)
  strategic_review: when chain supports filing-ready motion
```

### SIGNAL TYPE 3: CONTRADICTION

```yaml
signal: CONTRADICTION
description: >
  Two lanes assert facts or legal positions that are incompatible.
  Contradictions must be resolved before any affected filing proceeds.
detection_method:
  1. Extract factual assertions per lane
  2. Build assertion index with entity + claim + lane
  3. Compare claims about shared entities across lanes
  4. Flag pairs where claims conflict
  5. Classify: factual contradiction vs. framing difference
  6. Score severity (contradiction × filing proximity)
examples:
  - entity: "Pigors financial status"
    lane_a_claim: "Financially stable, provides for children"
    lane_b_claim: "Unable to afford alternative housing after Shady Oaks"
    contradiction_type: "Framing difference — resolvable"
    resolution: "Clarify: stable income but Shady Oaks price gouging"
    novelty: 4
  - entity: "Timeline of events"
    lane_a_claim: "Moved out of Watson residence on March 15"
    lane_b_claim: "Shady Oaks lease started January 1"
    contradiction_type: "Potential factual error — dates overlap"
    resolution: "Verify actual move dates with lease and utility records"
    novelty: 6
severity_levels:
  critical: "Direct factual contradiction (dates, amounts, events)"
  high: "Inconsistent characterizations of same entity"
  medium: "Framing differences that could be exploited"
  low: "Minor inconsistencies in non-material details"
thresholds:
  halt_filing: severity == critical
  review_filing: severity >= high
  note_only: severity <= medium
```

### SIGNAL TYPE 4: NOVEL_STRATEGY

```yaml
signal: NOVEL_STRATEGY
description: >
  A new legal theory or strategic approach emerges from combined
  data that was not part of the original case strategy.
detection_method:
  1. After cross-graph and chain-complete analysis
  2. Identify new connections not in original strategy document
  3. Evaluate legal viability of new approach
  4. Score novelty and potential impact
  5. Draft strategy brief for attorney review
examples:
  - strategy: "Housing violations as custody evidence"
    source: "Lane B inspection reports + Lane A best-interest factors"
    theory: "Shady Oaks conditions endanger children under MCL 722.23(c),
            (d), and (g), supporting change of custody environment"
    viability: "HIGH — well-established that living conditions affect custody"
    novelty: 9
  - strategy: "Consumer protection damages in housing case"
    source: "Lane B lease analysis + MCPA provisions"
    theory: "Shady Oaks practices may violate MCPA (MCL 445.903),
            allowing treble damages and attorney fees"
    viability: "MEDIUM — requires showing unfair trade practice"
    novelty: 7
thresholds:
  attorney_review: novelty >= 7
  immediate_review: novelty >= 9
```

### SIGNAL TYPE 5: WITNESS_OVERLAP

```yaml
signal: WITNESS_OVERLAP
description: >
  Same witness is relevant to multiple lanes, creating deposition
  efficiency opportunities and cross-examination strategy synergies.
detection_method:
  1. Extract witness lists per lane
  2. Match witnesses across lanes (name, role, relationship)
  3. Identify witnesses with testimony relevant to 2+ lanes
  4. Evaluate deposition strategy optimization
  5. Flag potential impeachment opportunities across lanes
examples:
  - witness: "Neighbor at Shady Oaks"
    lane_a: "Can testify about children's living conditions"
    lane_b: "Can testify about property maintenance failures"
    strategy: "Single deposition covers both lanes; coordinate questions"
    novelty: 6
  - witness: "Housing inspector"
    lane_a: "Report relevant to children's health/safety (factor g)"
    lane_b: "Report is primary evidence of code violations"
    strategy: "Inspector testimony bridges both cases"
    novelty: 5
thresholds:
  deposition_coordination: overlap in 2+ lanes
  strategy_brief: overlap in all 3 lanes
```

---

## Emergence Scoring Matrix

| Novelty Score | Meaning | Action |
|--------------|---------|--------|
| 9-10 | Breakthrough — case-changing pattern | IMMEDIATE attorney review |
| 7-8 | Significant — new strategic option | Attorney review within 24h |
| 5-6 | Moderate — useful optimization | Log and incorporate at next cycle |
| 3-4 | Minor — incremental improvement | Log for reference |
| 1-2 | Noise — not actionable | Log and dismiss |

---

## Emergence Event Schema

```yaml
emergence_event:
  id: string             # "EMRG-{date}-{seq}"
  signal_type: enum      # CROSS_GRAPH, CHAIN_COMPLETE, CONTRADICTION,
                         # NOVEL_STRATEGY, WITNESS_OVERLAP
  cycle_id: string       # convergence cycle that detected it
  lanes_involved: list   # [A, B] or [A, B, C]
  description: string
  evidence_links: list   # document IDs supporting the emergence
  novelty_score: integer # 1-10
  action_required: enum  # IMMEDIATE, REVIEW_24H, NEXT_CYCLE, LOG_ONLY
  resolution_status: enum # OPEN, IN_REVIEW, RESOLVED, DISMISSED
  attorney_notified: boolean
  timestamp: ISO-8601
```
