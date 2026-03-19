# Filing Workflow Command

## When to Use

- Building a new court filing from any legal action (A1-A35, B1-B14, C1-C7)
- Producing a VehicleMap-driven filing architecture
- Generating court-ready documents with exhibits + service packages

## Quick Start

```
# By legal action ID
/file A12   → Motion to Modify Parenting Time (Lane A: Custody)
/file B3    → Verified Complaint: Housing Code Violations (Lane B: Housing)
/file C2    → JTC Complaint (Lane C: Convergence)

# By filing type
/file motion-contempt --lane A --adversary "Amy Watson"
/file complaint --lane B --adversary "Shady Oaks Homes"
/file application-leave-appeal --court COA --case 2024-001507-DC
```

## Filing Workflow State Machine

```
IDENTIFY → RESEARCH → MAP → DRAFT → REVIEW → PACKAGE → SERVE
```

### Phase 1: IDENTIFY
- Select legal action ID from case lanes
- Dispatches to: **litigation-claim-researcher** (if facts need mapping)
- Output: Action ID + adversary + court level

### Phase 2: RESEARCH
- Pull all authority for the selected action
- Dispatches to: **litigation-authority-validator**, **litigation-cause-of-action-library**
- Output: [AT] AuthorityTriples + elements checklist

### Phase 3: MAP (VehicleMap)
- Generate VehicleMap: relief → vehicle → authority → elements → evidence → deadlines → service
- Dispatches to: **litigation-filing-architect**
- Output: [VM] VehicleMap with all mandatory fields

### Phase 4: DRAFT
- Generate court document structure
- Dispatches to: **litigation-complaint-drafter** (complaints) or **litigation-brief-writer** (motions/briefs)
- Output: Draft filing with [EX] ExhibitMatrix + [TL] Timeline

### Phase 5: REVIEW
- Adversarial stress-test the draft
- Dispatches to: **litigation-red-team**
- Output: [VR] Validation/RedTeam report + fixes applied

### Phase 6: PACKAGE
- Produce court-ready packet: filing + exhibits + proposed order + proof of service
- Dispatches to: **litigation-filing-architect**
- Output: Complete filing package

### Phase 7: SERVE
- Generate service package with proper method per party
- Dispatches to: **litigation-service-engine**
- Output: MC 12 proofs of service + method verification

## Mode Interaction

| Mode | Behavior |
|------|----------|
| `MODE:DRAFT` | Phases 1-4 only. Labels uncertainties. Fast. |
| `MODE:FILE_READY` | All 7 phases. No uncertainty. Every attachment present. |
| `MODE:PCG` | Blocks on PASS gate. Core proof + service + deadlines must be satisfied. |

## Cross-References

- [Case Lanes](../references/case-lanes/README.md) — Action IDs + adversaries
- [VehicleMap Library](../references/michigan-authority/vehicle-library.md) — Relief mapping
- [MCR Reference](../references/michigan-authority/mcr-reference.md) — Court rules
- [Fleet Dispatch](../references/fleet/dispatch-matrix.md) — Agent routing
