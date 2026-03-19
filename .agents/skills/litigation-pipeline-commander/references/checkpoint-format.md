# Checkpoint Format — Pipeline Commander Reference

## Checkpoint Architecture

Every OMEGA pipeline phase produces a checkpoint file upon completion.
Checkpoints serve three purposes:
1. **Recovery**: Resume pipeline from last successful phase after failure
2. **Audit**: Verify what was processed and when
3. **Integrity**: Detect data corruption through hash chaining

---

## Checkpoint File Naming Convention

```
Format: phase_{NN}_{name}_{lane}_{timestamp}.json

Examples:
  phase_00_safety_ALL_20260315T143022Z.json
  phase_01_inventory_A_20260315T144512Z.json
  phase_07_merge_ALL_20260315T160033Z.json
  phase_16_desktop_ALL_20260315T180000Z.json
```

---

## Full Checkpoint Schema

```yaml
checkpoint:
  # Identification
  checkpoint_id: string        # UUID v4
  pipeline_id: string          # Parent pipeline run ID
  phase: integer               # 0-16
  phase_name: string           # Human-readable phase name

  # Timing
  timestamp: ISO-8601          # When checkpoint was created
  phase_start_time: ISO-8601   # When phase execution began
  phase_end_time: ISO-8601     # When phase execution completed
  duration_seconds: integer    # Wall clock duration

  # Status
  status: enum                 # complete | failed | partial
  lane: enum                   # A | B | C | ALL
  resumable: boolean           # Can pipeline resume from here?

  # Processing Metrics
  documents:
    input_count: integer       # Documents entering this phase
    output_count: integer      # Documents exiting this phase
    quarantined_count: integer # Documents quarantined during phase
    skipped_count: integer     # Documents skipped (not applicable)

  # Phase-Specific Data
  phase_data:
    # Varies by phase — see Phase-Specific Sections below
    # This is where phase-specific results are stored

  # Error Log
  errors:
    total_count: integer
    errors:
      - error_id: string
        severity: enum         # critical | high | medium | low
        message: string
        document_id: string    # Which document (if applicable)
        recovery_action: string
        resolved: boolean

  # Hash Chain
  hash:
    algorithm: "SHA-256"
    checkpoint_hash: string    # SHA-256 of this checkpoint's data
    previous_hash: string      # SHA-256 of previous phase's checkpoint
    data_hash: string          # SHA-256 of phase output data

  # System Metrics
  system:
    memory_peak_mb: integer
    cpu_seconds: float
    disk_io_mb: float
    warnings: list[string]
```

---

## Phase-Specific Data Structures

### Phase 0: Safety
```yaml
phase_data:
  pii_scan_results:
    documents_scanned: integer
    pii_detected: integer
    pii_types: list[string]    # SSN, DOB, account numbers, etc.
    pii_redacted: integer
  privilege_scan_results:
    privileged_documents: integer
    privilege_types: list[string]
    quarantined: integer
  integrity_results:
    files_checked: integer
    checksums_valid: integer
    checksums_invalid: integer
    corrupted_files: list[string]
```

### Phase 1: Inventory
```yaml
phase_data:
  master_index:
    total_documents: integer
    by_type:
      motions: integer
      exhibits: integer
      correspondence: integer
      court_orders: integer
      depositions: integer
      inspections: integer
      leases: integer
      financial: integer
      other: integer
    by_lane:
      A: integer
      B: integer
      C: integer
      multi: integer
    id_range: string           # e.g., "DOC-A-0001 to DOC-A-0342"
```

### Phase 2: Dedup
```yaml
phase_data:
  dedup_results:
    exact_duplicates_found: integer
    exact_duplicates_removed: integer
    near_duplicates_found: integer
    near_duplicates_merged: integer
    near_duplicates_flagged: integer
    similarity_threshold: float  # 0.90
    dedup_log: list[dedup_entry]
  dedup_entry:
    original_id: string
    duplicate_id: string
    match_type: enum           # exact | near
    similarity_score: float
    action: enum               # removed | merged | flagged
    rationale: string
```

### Phase 3: Classify
```yaml
phase_data:
  classification_results:
    total_classified: integer
    by_category:
      motion: integer
      exhibit: integer
      correspondence: integer
      court_order: integer
      deposition: integer
      inspection_report: integer
      lease_document: integer
      financial_record: integer
      other: integer
    by_lane:
      A: integer
      B: integer
      C: integer
    by_relevance:
      high: integer            # relevance >= 80
      medium: integer          # relevance 50-79
      low: integer             # relevance 20-49
      minimal: integer         # relevance < 20
    classification_confidence_avg: float
```

### Phase 7: Merge (Critical Phase)
```yaml
phase_data:
  merge_results:
    entities_merged: integer
    conflicts_detected: integer
    conflicts_resolved: integer
    conflicts_escalated: integer
    unified_timeline_events: integer
    cross_lane_links_created: integer
    merge_decisions:
      - entity: string
        lanes: list[string]
        action: enum           # merged | flagged | escalated
        rationale: string
        confidence: float
```

---

## Checkpoint Validation Rules

```yaml
validation_rules:
  RULE-CKP-001:
    name: Hash Chain Integrity
    description: >
      Each checkpoint's previous_hash must match the checkpoint_hash
      of the immediately preceding phase's checkpoint.
    severity: CRITICAL
    on_failure: HALT — data integrity compromised

  RULE-CKP-002:
    name: Document Count Consistency
    description: >
      output_count of phase N must equal input_count of phase N+1
      (minus any quarantined in phase N+1).
    severity: HIGH
    on_failure: Investigate document loss/gain

  RULE-CKP-003:
    name: Timestamp Ordering
    description: >
      Phase N+1 timestamp must be after Phase N timestamp.
      Phase end_time must be after phase start_time.
    severity: MEDIUM
    on_failure: Clock sync issue — log warning

  RULE-CKP-004:
    name: Status Completeness
    description: >
      Only checkpoints with status "complete" allow the next phase
      to begin. "failed" and "partial" checkpoints block progression.
    severity: CRITICAL
    on_failure: Resume from last "complete" checkpoint

  RULE-CKP-005:
    name: Lane Consistency
    description: >
      If pipeline is running for specific lanes, all checkpoints
      must reference the correct lane(s).
    severity: HIGH
    on_failure: Lane mismatch — verify pipeline configuration
```

---

## Checkpoint Storage Location

```
Pipeline checkpoints stored at:
  {project_root}/pipeline_checkpoints/{pipeline_id}/
    phase_00_safety_ALL_{timestamp}.json
    phase_01_inventory_A_{timestamp}.json
    ...
    phase_16_desktop_ALL_{timestamp}.json
    pipeline_manifest.json
```

### Pipeline Manifest
```yaml
pipeline_manifest:
  pipeline_id: string
  started: ISO-8601
  last_updated: ISO-8601
  lanes: list[string]
  current_phase: integer
  status: enum                 # running | complete | failed | paused
  checkpoints:
    - phase: integer
      file: string
      hash: string
      status: string
      timestamp: ISO-8601
```

---

## Recovery from Checkpoint

```
RECOVERY PROCEDURE:
1. Locate latest checkpoint with status = "complete"
2. Validate hash chain from Phase 0 to recovery point
3. If hash chain valid → resume from next phase
4. If hash chain broken → find last valid link → resume there
5. Load phase_data from recovery checkpoint
6. Initialize next phase with recovered state
7. Log recovery event with gap analysis
8. Resume pipeline execution
```
