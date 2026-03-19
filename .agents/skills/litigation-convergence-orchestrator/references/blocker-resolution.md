# Blocker Resolution — Convergence Orchestrator Reference

## Overview

Blockers are gaps that prevent forward progress on a lane or filing.
They are the highest priority items in the convergence cycle and must be
resolved before any filing proceeds. This reference defines the resolution
procedures for each blocker category.

---

## Blocker Classification System

### Category 1: Authority Blockers

```yaml
blocker_type: AUTHORITY
description: Missing, invalid, or overruled authority prevents filing
severity: CRITICAL
resolution_owner: litigation-authority-validator
examples:
  - "Key statute cited in motion has been amended — argument invalid"
  - "Primary case authority overruled — no substitute identified"
  - "Authority chain for best-interest factor (j) incomplete"
resolution_steps:
  1. Identify the specific authority gap (which citation, which filing)
  2. Search for replacement authority:
     a. Check Michigan Supreme Court decisions first
     b. Then Michigan Court of Appeals published opinions
     c. Then secondary sources for analogous authority
  3. Validate replacement authority:
     a. Verify existence (RULE-EXT-001)
     b. Verify currency (RULE-CUR-001 through 005)
     c. Verify binding status in 14th Circuit
  4. Update all filings referencing the old authority
  5. Re-run authority chain completeness check
  6. Verify chain score >= 4/5 before clearing blocker
escalation_trigger: No replacement authority found within 4 hours
escalation_action: Attorney review — may require argument restructuring
lane_specific:
  A: "Best-interest factor authorities are non-negotiable — MCL 722.23"
  B: "Housing code authorities must cite specific MCL provision"
  C: "Cross-lane authorities must be consistent across lanes"
```

### Category 2: Evidence Blockers

```yaml
blocker_type: EVIDENCE
description: Critical evidence missing, contradictory, or inadmissible
severity: CRITICAL
resolution_owner: litigation-brain-spec
examples:
  - "No documentation of housing code violations for Lane B damages"
  - "Contradictory dates between custody petition and housing complaint"
  - "Key exhibit not authenticated per MRE 901"
resolution_steps:
  1. Identify the specific evidence gap
  2. Determine if evidence exists but hasn't been collected:
     a. Check document inventory (OMEGA Phase 1 output)
     b. Check if evidence is in opposing party's possession
     c. Check if evidence needs to be created (affidavit, declaration)
  3. If evidence needs discovery:
     a. Draft targeted discovery request
     b. Set discovery deadline relative to court deadline
     c. Flag as BLOCKER until discovery response received
  4. If evidence exists but is inadmissible:
     a. Identify admissibility issue (hearsay, authentication, relevance)
     b. Research applicable exception (MRE 803/804 for hearsay)
     c. Prepare foundation for admission
  5. If evidence is contradictory:
     a. Determine which version is correct (primary sources)
     b. Update all filings to use correct version
     c. Check for cross-lane contamination
  6. Re-validate evidence linkage after resolution
escalation_trigger: Evidence cannot be obtained before court deadline
escalation_action: >
  Attorney review — may require motion for continuance or
  alternative strategy that doesn't depend on missing evidence
lane_specific:
  A: "Parenting time logs, school records, medical records critical"
  B: "Inspection reports, repair requests, lease documents critical"
  C: "Cross-lane timeline consistency is non-negotiable"
```

### Category 3: Filing Blockers

```yaml
blocker_type: FILING
description: Filing cannot be assembled due to missing components
severity: HIGH
resolution_owner: litigation-filing-packager
examples:
  - "Certificate of service template missing for Lane A motion"
  - "Proposed order format doesn't match 14th Circuit requirements"
  - "Filing exceeds page limit (MCR 2.119(A)(2) for motions)"
resolution_steps:
  1. Identify the specific filing component that is missing or deficient
  2. For missing components:
     a. Check filing packager templates
     b. Check 14th Circuit local rules for specific requirements
     c. Generate missing component from template
  3. For format violations:
     a. Identify specific rule violated (MCR, local rule)
     b. Reformat to comply
     c. Re-validate format compliance
  4. For content violations:
     a. Identify excess content (page limit, argument scope)
     b. Edit for conciseness without losing substance
     c. Re-validate content completeness
  5. Re-run filing readiness check
escalation_trigger: Component requires information not available to system
escalation_action: Attorney must provide missing information
lane_specific:
  A: "MCR 3.210 has specific custody filing requirements"
  B: "CZ case filings follow standard MCR 2.110 format"
  C: "Convergence filings may need to reference both case numbers"
```

### Category 4: Strategy Blockers

```yaml
blocker_type: STRATEGY
description: Strategic inconsistency prevents coherent litigation approach
severity: HIGH
resolution_owner: litigation-convergence-orchestrator
examples:
  - "Lane A and Lane B make contradictory claims about Pigors finances"
  - "Aggressive strategy in Lane B conflicts with cooperative tone in Lane A"
  - "Timeline in motion contradicts timeline in complaint"
resolution_steps:
  1. Identify the specific strategic inconsistency
  2. Determine which position is correct or stronger:
     a. Check factual basis for each position
     b. Evaluate which position is more legally advantageous
     c. Assess which position is better supported by evidence
  3. Align all filings to the chosen position:
     a. Update Lane A filings if Lane B position prevails
     b. Update Lane B filings if Lane A position prevails
     c. Update Lane C strategy document to reflect alignment
  4. Check for downstream impacts:
     a. Does alignment change any legal arguments?
     b. Does alignment affect witness preparation?
     c. Does alignment require authority chain updates?
  5. Re-run cross-lane integrity check
escalation_trigger: Both positions have strong factual/legal support
escalation_action: >
  Attorney strategic decision required — present both options
  with pros/cons analysis
lane_specific:
  A: "Custody strategy must prioritize children's best interests"
  B: "Housing strategy must prioritize damage recovery"
  C: "Convergence must not sacrifice either lane's core position"
```

### Category 5: System Blockers

```yaml
blocker_type: SYSTEM
description: Technical or system failure prevents pipeline progress
severity: VARIES
resolution_owner: litigation-pipeline-commander
examples:
  - "Checkpoint corruption in OMEGA Phase 5"
  - "MCP tool (litigation_self_test) returning errors"
  - "Knowledge graph update failed mid-transaction"
resolution_steps:
  1. Identify the specific system failure
  2. Apply error recovery protocol (see pipeline-commander):
     a. Level 1: Retry with backoff
     b. Level 2: Quarantine and continue
     c. Level 3: Rollback and restart
     d. Level 4: Halt and escalate
  3. Verify system is operational after recovery
  4. Re-run affected pipeline phase
  5. Verify data integrity
escalation_trigger: Level 3+ error recovery fails
escalation_action: Manual system intervention required
```

---

## Blocker Resolution Workflow

```
BLOCKER IDENTIFIED
│
├─ Step 1: Classify (Authority / Evidence / Filing / Strategy / System)
├─ Step 2: Assign to resolution owner (skill responsible)
├─ Step 3: Estimate resolution time
├─ Step 4: Check against court deadlines
│   ├─ If resolution_time > time_to_deadline:
│   │   └─ ESCALATE IMMEDIATELY
│   └─ If resolution_time < time_to_deadline:
│       └─ Proceed with resolution steps
├─ Step 5: Execute resolution steps (per category above)
├─ Step 6: Verify resolution
│   ├─ Re-run relevant tests
│   ├─ Confirm blocker criteria no longer met
│   └─ Check for new issues introduced by fix
├─ Step 7: Clear blocker from gap_registry
├─ Step 8: Log resolution details
└─ Step 9: Trigger re-test (convergence Phase 7)
```

---

## Blocker Priority Matrix

| Deadline Proximity | Severity | Priority Score | Response Time |
|-------------------|----------|---------------|---------------|
| < 48 hours | CRITICAL | 100 | Immediate |
| < 48 hours | HIGH | 90 | Within 2 hours |
| < 7 days | CRITICAL | 80 | Within 4 hours |
| < 7 days | HIGH | 70 | Within 8 hours |
| < 14 days | CRITICAL | 60 | Within 12 hours |
| < 14 days | HIGH | 50 | Within 24 hours |
| > 14 days | CRITICAL | 40 | Within 24 hours |
| > 14 days | HIGH | 30 | Within 48 hours |
| Any | MEDIUM | 20 | Next cycle |
| Any | LOW | 10 | When convenient |

---

## Blocker Metrics

Track these metrics across convergence cycles:

```yaml
blocker_metrics:
  total_blockers_identified: integer
  total_blockers_resolved: integer
  avg_resolution_time_hours: float
  blockers_requiring_escalation: integer
  blockers_by_category:
    authority: integer
    evidence: integer
    filing: integer
    strategy: integer
    system: integer
  blockers_by_lane:
    A: integer
    B: integer
    C: integer
  resolution_rate: float  # resolved / identified
  recurrence_rate: float  # same blocker reappearing
```
