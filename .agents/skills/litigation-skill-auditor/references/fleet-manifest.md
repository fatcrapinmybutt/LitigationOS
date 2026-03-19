# Fleet Manifest — Skill Auditor Reference

## Litigation Skill Fleet — Master Manifest

```yaml
fleet_manifest:
  version: "2.0.0"
  last_audit: "2026-03-15T00:00:00Z"
  court: "14th Judicial Circuit, Muskegon County"
  case: "Pigors v Watson"
  total_skills: 25
  lanes:
    A: "Watson/Custody (2024-001507-DC, 2023-5907-PP, Judge McNeill)"
    B: "Shady Oaks/Housing (2025-002760-CZ, Judge Hoopes)"
    C: "Convergence/County (Muskegon County, 14th Circuit)"
```

---

## Tier 1 Skills (Foundation Layer)

```yaml
tier_1:
  description: >
    Core infrastructure skills that other skills depend on.
    Must be fully operational before Tier 2 can function.
  skills:
    - name: litigation-brain-spec
      version: "2.0.0"
      status: active
      compliance_score: null  # Pending audit
      description: "Use when building or querying the case knowledge graph"
      trigger_count: 5
      lanes: [A, B, C]
      dependents: [litigation-authority-validator, litigation-convergence-orchestrator, litigation-pipeline-commander, litigation-appellate-strategist]

    - name: litigation-filing-packager
      version: "2.0.0"
      status: active
      compliance_score: null
      description: "Use when assembling court filings for submission"
      trigger_count: 4
      lanes: [A, B, C]
      dependents: [litigation-authority-validator, litigation-pipeline-commander, litigation-appellate-strategist]

    - name: litigation-evidence-linker
      version: "2.0.0"
      status: active
      compliance_score: null
      description: "Use when linking evidence to claims and legal arguments"
      trigger_count: 4
      lanes: [A, B, C]
      dependents: [litigation-brain-spec, litigation-convergence-orchestrator]

    - name: litigation-timeline-builder
      version: "2.0.0"
      status: active
      compliance_score: null
      description: "Use when constructing or verifying case timelines"
      trigger_count: 3
      lanes: [A, B, C]
      dependents: [litigation-brain-spec, litigation-pipeline-commander]

    - name: litigation-entity-resolver
      version: "2.0.0"
      status: active
      compliance_score: null
      description: "Use when resolving entity references across documents"
      trigger_count: 3
      lanes: [A, B, C]
      dependents: [litigation-brain-spec, litigation-pipeline-commander]
```

## Tier 2 Skills (Operational Layer)

```yaml
tier_2:
  description: >
    Operational skills that execute specific litigation functions.
    Depend on Tier 1 for data and infrastructure.
  skills:
    - name: litigation-authority-validator
      version: "2.0.0"
      status: active
      compliance_score: null
      description: "Use when verifying MCR/MCL/MRE citations and authority chains"
      trigger_count: 8
      lanes: [A, B, C]
      dependencies: [litigation-brain-spec, litigation-filing-packager]
      files: [SKILL.md, gotchas.md, references/citation-formats.md, references/validation-rules.md, references/chain-templates.md]

    - name: litigation-convergence-orchestrator
      version: "2.0.0"
      status: active
      compliance_score: null
      description: "Use when executing convergence cycles and tracking quality"
      trigger_count: 9
      lanes: [A, B, C]
      dependencies: [litigation-brain-spec, litigation-pipeline-commander, litigation-authority-validator]
      files: [SKILL.md, gotchas.md, references/cycle-protocol.md, references/emergence-signals.md, references/blocker-resolution.md]

    - name: litigation-pipeline-commander
      version: "2.0.0"
      status: active
      compliance_score: null
      description: "Use when executing the OMEGA 16-phase pipeline"
      trigger_count: 9
      lanes: [A, B, C]
      dependencies: [litigation-brain-spec, litigation-convergence-orchestrator, litigation-authority-validator, litigation-filing-packager]
      files: [SKILL.md, gotchas.md, references/phase-specs.md, references/checkpoint-format.md, references/error-recovery.md]

    - name: litigation-appellate-strategist
      version: "2.0.0"
      status: active
      compliance_score: null
      description: "Use when preparing Michigan appellate filings and strategy"
      trigger_count: 10
      lanes: [A, B, C]
      dependencies: [litigation-authority-validator, litigation-filing-packager, litigation-brain-spec]
      files: [SKILL.md, gotchas.md, references/appellate-rules.md, references/brief-templates.md, references/record-requirements.md]

    - name: litigation-skill-auditor
      version: "2.0.0"
      status: active
      compliance_score: null
      description: "Use when auditing the litigation skill fleet for compliance"
      trigger_count: 9
      lanes: [A, B, C]
      dependencies: []
      files: [SKILL.md, gotchas.md, references/audit-checklist.md, references/fleet-manifest.md, references/compliance-rules.md]

    - name: litigation-discovery-manager
      version: "2.0.0"
      status: active
      compliance_score: null
      description: "Use when managing discovery requests, responses, and compliance"
      trigger_count: 5
      lanes: [A, B, C]

    - name: litigation-witness-prepper
      version: "2.0.0"
      status: active
      compliance_score: null
      description: "Use when preparing witnesses for deposition or trial testimony"
      trigger_count: 4
      lanes: [A, B]

    - name: litigation-damage-calculator
      version: "2.0.0"
      status: active
      compliance_score: null
      description: "Use when calculating and documenting damages for claims"
      trigger_count: 4
      lanes: [B, C]

    - name: litigation-motion-drafter
      version: "2.0.0"
      status: active
      compliance_score: null
      description: "Use when drafting motions for Michigan circuit court"
      trigger_count: 5
      lanes: [A, B, C]

    - name: litigation-impeachment-builder
      version: "2.0.0"
      status: active
      compliance_score: null
      description: "Use when building impeachment packages for adverse witnesses"
      trigger_count: 4
      lanes: [A, B]
```

## Tier 3 Skills (Specialized Layer)

```yaml
tier_3:
  description: >
    Specialized skills for specific case aspects or advanced functions.
    May depend on Tier 1 and Tier 2 skills.
  skills:
    - name: litigation-custody-analyst
      version: "2.0.0"
      status: active
      compliance_score: null
      description: "Use when analyzing custody factors under MCL 722.23"
      trigger_count: 4
      lanes: [A]

    - name: litigation-housing-analyst
      version: "2.0.0"
      status: active
      compliance_score: null
      description: "Use when analyzing housing code violations and habitability"
      trigger_count: 4
      lanes: [B]

    - name: litigation-ppo-strategist
      version: "2.0.0"
      status: active
      compliance_score: null
      description: "Use when managing personal protection order strategy"
      trigger_count: 4
      lanes: [A]

    - name: litigation-judicial-profiler
      version: "2.0.0"
      status: active
      compliance_score: null
      description: "Use when analyzing judicial patterns and preferences"
      trigger_count: 3
      lanes: [A, B, C]

    - name: litigation-compliance-tracker
      version: "2.0.0"
      status: active
      compliance_score: null
      description: "Use when tracking compliance with court orders and deadlines"
      trigger_count: 4
      lanes: [A, B, C]

    - name: litigation-settlement-analyzer
      version: "2.0.0"
      status: active
      compliance_score: null
      description: "Use when evaluating settlement options and negotiation strategy"
      trigger_count: 3
      lanes: [A, B]

    - name: litigation-record-keeper
      version: "2.0.0"
      status: active
      compliance_score: null
      description: "Use when maintaining case file organization and document control"
      trigger_count: 3
      lanes: [A, B, C]

    - name: litigation-cost-tracker
      version: "2.0.0"
      status: active
      compliance_score: null
      description: "Use when tracking litigation costs and budget management"
      trigger_count: 3
      lanes: [A, B, C]

    - name: litigation-client-communicator
      version: "2.0.0"
      status: active
      compliance_score: null
      description: "Use when preparing client communications and status updates"
      trigger_count: 3
      lanes: [A, B, C]

    - name: litigation-foc-liaison
      version: "2.0.0"
      status: active
      compliance_score: null
      description: "Use when interfacing with Friend of Court in custody matters"
      trigger_count: 3
      lanes: [A]
```

---

## Fleet Health Summary

```yaml
fleet_health:
  total_skills: 25
  tier_distribution:
    tier_1: 5
    tier_2: 10
    tier_3: 10
  status_distribution:
    active: 25
    degraded: 0
    non_compliant: 0
    retired: 0
  lane_coverage:
    A_only: 3    # custody-specific skills
    B_only: 1    # housing-specific skills
    AB: 3        # dual-lane skills
    ABC: 18      # all-lane skills
  compliance:
    avg_score: null       # Pending first full audit
    audited_count: 0
    unaudited_count: 25
  last_full_audit: null   # No audit completed yet
  next_scheduled_audit: "2026-03-22T00:00:00Z"
```

---

## Manifest Maintenance Rules

```
RULE 1: Manifest MUST be updated after every audit cycle
RULE 2: Manifest MUST be updated when skills are added or removed
RULE 3: Manifest MUST reflect actual filesystem state
RULE 4: Compliance scores reset to null if skill is modified
RULE 5: Retired skills remain in manifest with status "retired"
RULE 6: Version numbers must match SKILL.md metadata
RULE 7: Manifest is the source of truth for fleet composition
```
