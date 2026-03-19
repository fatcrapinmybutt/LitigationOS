# Cycle Protocol — Convergence Orchestrator Reference

## Full Convergence Cycle Specification

### Cycle Initialization

```yaml
cycle_init:
  step: 0
  name: CYCLE_INIT
  actions:
    - Generate cycle_id: "CONV-{ISO-date}-{sequence}"
    - Load previous cycle report (if exists)
    - Load current quality_score baseline
    - Determine cycle mode:
        score >= 90: MAINTENANCE
        score 70-89: STANDARD
        score 50-69: INTENSIVE
        score < 50:  EMERGENCY
    - Check court deadlines within 14 days
    - If deadline mode: override to DEADLINE pacing
    - Load lane configurations (A, B, C)
    - Initialize gap_registry from previous cycle
    - Record cycle_start_time
  outputs:
    - cycle_id
    - cycle_mode
    - baseline_score
    - active_lanes
    - deadline_override: boolean
  duration_estimate: 2-5 minutes
```

---

### Phase 1: SELF-TEST

```yaml
phase_1_self_test:
  step: 1
  name: SELF_TEST
  mcp_tool: litigation_self_test()
  actions:
    - Invoke litigation_self_test() with current lane context
    - For each skill in fleet:
        - Validate output contract compliance
        - Check cross-reference resolution
        - Verify trigger responsiveness
        - Test with representative inputs per lane
    - For each lane (A, B, C):
        - Validate filing completeness
        - Check evidence linkage integrity
        - Verify timeline consistency
        - Test authority chain resolution
    - Collect all test results into test_results[]
  pass_criteria:
    - All skills respond to their triggers
    - All output contracts parse correctly
    - All cross-references resolve to existing skills
    - No evidence links point to missing documents
  fail_handling:
    - Log each failure with skill name, test name, error
    - Classify failures: CRITICAL / HIGH / MEDIUM / LOW
    - CRITICAL failures → immediate BLOCKER creation
    - HIGH failures → DNEW creation
    - MEDIUM/LOW → NEXT_PATCH queue
  outputs:
    - test_results: list[test_result]
    - tests_passed: integer
    - tests_failed: integer
    - critical_failures: integer
  duration_estimate: 10-30 minutes
```

---

### Phase 2: SELF-AUDIT

```yaml
phase_2_self_audit:
  step: 2
  name: SELF_AUDIT
  mcp_tool: litigation_self_audit()
  actions:
    - Invoke litigation_self_audit() with full fleet scope
    - For each skill:
        - Check SKILL.md exists (ALL CAPS)
        - Verify name matches directory (kebab-case)
        - Verify description starts with "Use when..."
        - Verify triggers >= 3
        - Verify SKILL.md < 500 lines
        - Verify category is "discipline"
        - Check gotchas.md exists
        - Verify anti-rationalization table >= 5 rows
        - Check references/ directory populated
    - For fleet-wide:
        - Check dependency graph for cycles
        - Verify all cross-references resolve
        - Check trigger coverage completeness
        - Validate fleet manifest accuracy
  pass_criteria:
    - All CRITICAL compliance checks pass
    - No circular dependencies
    - Trigger coverage > 85%
    - Fleet manifest matches filesystem
  fail_handling:
    - Log each compliance failure with severity
    - Skills with compliance_score < 70: flag for remediation
    - Update fleet manifest with current scores
  outputs:
    - audit_results: list[audit_result]
    - fleet_compliance_avg: float
    - non_compliant_skills: list[string]
  duration_estimate: 5-15 minutes
```

---

### Phase 3: QUALITY SCORING

```yaml
phase_3_quality_scoring:
  step: 3
  name: QUALITY_SCORING
  actions:
    - Compute component scores from Phase 1 + Phase 2:
        authority_completeness:
          source: litigation-authority-validator results
          weight: 0.25
          calculation: validated_citations / total_citations
        evidence_coverage:
          source: evidence linkage tests
          weight: 0.20
          calculation: supported_claims / total_claims
        filing_readiness:
          source: filing format and content tests
          weight: 0.20
          calculation: passing_filing_checks / total_filing_checks
        strategy_coherence:
          source: cross-lane strategy consistency
          weight: 0.15
          calculation: consistent_positions / total_positions
        cross_lane_integrity:
          source: contradiction detection results
          weight: 0.10
          calculation: 1.0 - (contradictions_found / entities_checked)
        emergence_capture:
          source: previous cycle emergence log
          weight: 0.10
          calculation: emergence_events_actioned / emergence_events_total
    - Compute per-lane scores (same formula, lane-filtered data)
    - Compare overall score to previous cycle
    - Determine trajectory: improving / stable / regressing
    - IF regressing: set regression_flag = true
  outputs:
    - quality_score: float (0-100)
    - lane_scores: {A: float, B: float, C: float}
    - component_scores: {component: float}
    - trajectory: enum
    - regression_flag: boolean
  duration_estimate: 2-5 minutes
```

---

### Phase 4: GAP CLASSIFICATION

```yaml
phase_4_gap_classification:
  step: 4
  name: GAP_CLASSIFICATION
  actions:
    - Collect all failures from Phase 1 and Phase 2
    - For each failure, classify:
        - BLOCKER if: prevents filing, blocks other skills, deadline impact
        - DNEW if: new gap discovered this cycle, not previously tracked
        - NEXT_PATCH if: known gap, not deadline-critical, deferrable
    - Prioritize by: court_deadline_days × severity_weight
        severity_weights:
          critical: 10
          high: 7
          medium: 4
          low: 1
        priority = severity_weight / max(court_deadline_days, 1)
    - Update gap_registry with new classifications
    - Retire resolved gaps from previous cycle
  outputs:
    - dnew_items: list[dnew_item]
    - blocker_items: list[blocker_item]
    - next_patch_items: list[next_patch_item]
    - gap_registry: updated registry
  duration_estimate: 5-10 minutes
```

---

### Phase 5: EMERGENCE DETECTION

See references/emergence-signals.md for full protocol.

### Phase 6: PATCH EXECUTION

See references/blocker-resolution.md for resolution procedures.

### Phase 7: RE-TEST

```yaml
phase_7_retest:
  step: 7
  name: RE_TEST
  actions:
    - Re-invoke litigation_self_test()
    - Focus on items patched in Phase 6
    - Verify each patched BLOCKER is resolved
    - Verify each patched DNEW is resolved
    - Check for regression (new failures introduced by patches)
    - Re-compute quality_score
    - Compare to Phase 3 score
    - IF score improved: cycle successful
    - IF score unchanged: investigate stall
    - IF score decreased: regression — flag for root cause
  outputs:
    - retest_results: list[test_result]
    - final_quality_score: float
    - improvement: float (delta from Phase 3)
    - regression_detected: boolean
  duration_estimate: 10-30 minutes
```

---

### Cycle Finalization

```yaml
cycle_finalize:
  step: 8
  name: CYCLE_FINALIZE
  actions:
    - Generate cycle_report
    - Calculate next_cycle_recommended based on score
    - Update fleet manifest if compliance changed
    - Archive cycle data for historical analysis
    - Log cycle summary to convergence timeline
    - Notify if escalation conditions met
  outputs:
    - convergence_cycle_report (see SKILL.md output contract)
  duration_estimate: 2-5 minutes
```

---

## Cycle Mode Specifications

### MAINTENANCE Mode (score >= 90)
- Skip Phase 6 (Patch) unless BLOCKERs found
- Phase 5 (Emergence) runs with expanded scope
- Phase 7 (Re-test) runs abbreviated checks
- Total estimated time: 30-60 minutes

### STANDARD Mode (score 70-89)
- All phases execute normally
- Total estimated time: 60-120 minutes

### INTENSIVE Mode (score 50-69)
- Phase 1 and Phase 2 run twice (double-pass)
- Phase 5 runs with deep emergence scan
- Phase 6 addresses all DNEW items (not just BLOCKERs)
- Total estimated time: 120-240 minutes

### EMERGENCY Mode (score < 50)
- All phases execute with maximum detail logging
- Phase 6 addresses ALL gaps regardless of priority
- No NEXT_PATCH deferral allowed
- Continuous re-test until score > 50 or human override
- Total estimated time: 240+ minutes
