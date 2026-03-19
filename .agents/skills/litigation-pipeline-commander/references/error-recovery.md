# Error Recovery — Pipeline Commander Reference

## Error Recovery Architecture

The OMEGA pipeline operates in a hostile environment where errors are expected,
not exceptional. Documents may be corrupted, services may be unavailable,
data may conflict. The error recovery system ensures the pipeline continues
producing valid output despite these conditions.

---

## Error Classification

### Level 1: Transient Errors

```yaml
level: 1
name: TRANSIENT
description: >
  Temporary failures caused by resource contention, network issues,
  file locks, or timing problems. These resolve on retry.
examples:
  - File temporarily locked by another process
  - Service endpoint timeout (< 30 seconds)
  - Memory allocation failure during peak usage
  - Temporary disk space shortage
recovery:
  strategy: RETRY_WITH_BACKOFF
  max_retries: 3
  backoff_schedule:
    retry_1: wait 30 seconds
    retry_2: wait 60 seconds
    retry_3: wait 120 seconds
  on_success: Continue phase normally, log recovery event
  on_failure: Escalate to Level 2
logging:
  level: WARNING
  include: error_type, retry_count, resolution_time
```

### Level 2: Data Errors

```yaml
level: 2
name: DATA_ERROR
description: >
  Errors caused by malformed input, unexpected format, parse failures,
  or data quality issues. The specific document has problems but the
  pipeline can continue with remaining documents.
examples:
  - Malformed PDF that cannot be parsed
  - Document with unrecognized encoding
  - Corrupted image file in exhibits
  - Unexpected date format in financial records
  - Empty or zero-byte file
recovery:
  strategy: QUARANTINE_AND_CONTINUE
  actions:
    1. Move problematic document to quarantine
    2. Log quarantine reason with document ID
    3. Tag document with "quarantine_{phase}_{error_type}"
    4. Continue phase with remaining documents
    5. Include quarantine count in checkpoint
  quarantine_threshold: 20%  # If > 20% quarantined, HALT
  on_success: Phase completes with quarantine report
  on_threshold_breach: Escalate to Level 3
logging:
  level: ERROR
  include: document_id, error_type, quarantine_reason
lane_specific_notes:
  A: "Custody documents are often scanned at low quality — expect OCR issues"
  B: "Inspection reports may be handwritten — parse with extra tolerance"
  C: "Cross-lane documents should never be quarantined without review"
```

### Level 3: Logic Errors

```yaml
level: 3
name: LOGIC_ERROR
description: >
  Unexpected system state, assertion failures, or algorithm errors.
  The pipeline has reached a state that should not be possible.
examples:
  - Phase 7 merge encounters circular entity reference
  - Authority chain validation produces contradictory results
  - Brain-spec graph has orphan nodes after Phase 5
  - Checkpoint hash mismatch (data integrity concern)
  - Phase dependency violation (phase ran out of order)
recovery:
  strategy: ROLLBACK_AND_RESTART
  actions:
    1. Save complete state dump for forensic analysis
    2. Identify the specific assertion/logic that failed
    3. Rollback to previous phase checkpoint
    4. Enable diagnostic logging (verbose mode)
    5. Restart failed phase with diagnostic logging
    6. If restart succeeds: analyze root cause from logs
    7. If restart fails: escalate to Level 4
  diagnostic_logging:
    - All function entry/exit points
    - All data transformations
    - All decision points with values
    - Memory state at key checkpoints
  on_success: Phase completes, diagnostic log reviewed offline
  on_failure: Escalate to Level 4
logging:
  level: CRITICAL
  include: full state dump, stack trace, data snapshot
```

### Level 4: Critical Failures

```yaml
level: 4
name: CRITICAL_FAILURE
description: >
  System-level failures that compromise data integrity or prevent
  any further pipeline progress. Requires human intervention.
examples:
  - Data corruption detected in checkpoint chain
  - System disk failure during write operation
  - MCP tool returns inconsistent state across calls
  - Phase output fails integrity check (hash mismatch)
  - Unrecoverable circular dependency in data
recovery:
  strategy: HALT_AND_ESCALATE
  actions:
    1. HALT pipeline immediately — no further phases
    2. Save ALL state for forensic analysis:
       - All checkpoints
       - Current phase state
       - Error logs
       - System metrics
       - Data snapshots
    3. Lock pipeline from restart (prevent further damage)
    4. Generate incident report
    5. Notify human operator with:
       - What failed
       - What phase was active
       - Last known good state
       - Recommended recovery approach
    6. WAIT for human authorization before any restart
  on_resolution:
    1. Human diagnoses root cause
    2. Human approves recovery plan
    3. Pipeline resumes from approved checkpoint
    4. Post-incident review scheduled
logging:
  level: CRITICAL
  include: everything — full forensic log
```

---

## Error Recovery Decision Tree

```
ERROR DETECTED IN PHASE {N}
│
├─ Is it a timeout/resource contention?
│   └─ YES → Level 1: Retry with backoff (max 3 attempts)
│       ├─ Retry succeeds → Continue phase
│       └─ All retries fail → ↓
│
├─ Is it a specific document/data issue?
│   └─ YES → Level 2: Quarantine document
│       ├─ Quarantine < 20% → Continue phase
│       └─ Quarantine ≥ 20% → ↓
│
├─ Is it a logic/assertion failure?
│   └─ YES → Level 3: Rollback to Phase {N-1}
│       ├─ Restart with diagnostics succeeds → Continue
│       └─ Restart fails → ↓
│
└─ CRITICAL FAILURE
    └─ Level 4: HALT pipeline → Human intervention required
```

---

## Phase-Specific Error Handling

### Phase 0 (Safety) Errors
```yaml
common_errors:
  - PII detection false positive (rate: ~5%)
    action: Flag for review, don't auto-quarantine
  - Privilege marker ambiguity
    action: Err on side of caution — quarantine
  - Corrupted file detected
    action: Quarantine immediately, do not process
special_rules:
  - Phase 0 errors are NEVER auto-recovered
  - Every Phase 0 error requires human review
  - Phase 0 has no "acceptable failure" threshold
```

### Phase 4 (Extract) Errors
```yaml
common_errors:
  - OCR quality too low for extraction
    action: Quarantine, recommend re-scan
  - Unexpected document format
    action: Try secondary extraction method, then quarantine
  - Entity extraction ambiguity
    action: Flag entity as "ambiguous", continue
special_rules:
  - Lane A custody documents may have poor scan quality
  - Lane B inspection reports may be handwritten
  - Extract errors in Lane C cross-lane documents escalate to Level 3
```

### Phase 7 (Merge) Errors
```yaml
common_errors:
  - Entity merge conflict (same person, different attributes)
    action: Create "conflict" node, escalate for resolution
  - Timeline contradiction between lanes
    action: Flag both versions, do not auto-resolve
  - Data loss during merge operation
    action: Level 3 — rollback and restart with diagnostics
special_rules:
  - Phase 7 is the highest-risk phase for errors
  - No auto-resolution of cross-lane conflicts
  - All merge decisions must be logged with rationale
  - Budget 50% extra time for Phase 7 error handling
```

### Phase 15 (Validate) Errors
```yaml
common_errors:
  - Quality score below threshold (< 85)
    action: NOT an error — this is a finding. Loop back to address gaps.
  - Convergence tool unresponsive
    action: Level 1 retry, then Level 3 if persistent
  - Validation contradicts previous phase results
    action: Level 3 — investigate data integrity
special_rules:
  - Phase 15 failures do NOT corrupt data
  - Phase 15 failures BLOCK Phase 16 (Desktop)
  - Low quality scores require convergence cycle, not error recovery
```

---

## Incident Report Template

```yaml
incident_report:
  incident_id: string         # "INC-{date}-{seq}"
  pipeline_id: string
  phase: integer
  error_level: integer        # 1-4
  timestamp: ISO-8601
  description: string
  root_cause: string          # If determined
  data_impact:
    documents_affected: integer
    lanes_affected: list[string]
    checkpoints_affected: list[string]
  recovery_actions_taken:
    - action: string
      result: string
      timestamp: ISO-8601
  resolution:
    status: enum              # resolved | escalated | pending
    resolution_method: string
    resumed_from_phase: integer
    data_loss: boolean
    data_loss_details: string
  lessons_learned: string
  prevention_recommendation: string
```

---

## Error Metrics Dashboard

```yaml
error_metrics:
  pipeline_id: string
  total_errors: integer
  errors_by_level:
    level_1: integer
    level_2: integer
    level_3: integer
    level_4: integer
  errors_by_phase:
    phase_0: integer
    phase_1: integer
    # ... through phase_16
  recovery_success_rate: float
  avg_recovery_time_seconds: float
  quarantine_rate: float
  pipeline_uptime_percentage: float
  most_error_prone_phase: integer
  most_common_error_type: string
```
