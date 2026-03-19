# Timeline Anomaly Detector v13.0.0

## LitigationOS Skill Module — Temporal Inconsistency & Docket Gap Detection

---

## Purpose and Scope

The Timeline Anomaly Detector identifies temporal inconsistencies, impossible sequences, backdated documents, and gaps in court records. These anomalies are powerful evidence of:
- Judicial misconduct (orders issued before hearings occur)
- Document fabrication (creation dates inconsistent with filing dates)
- Docket manipulation (missing entries that should exist)
- Due process violations (inadequate notice periods)

In family court litigation, timeline anomalies frequently indicate systemic issues that can support appellate arguments and federal civil rights claims.

---

## Input Requirements

| Field | Type | Description |
|-------|------|-------------|
| `documents` | `List[DocumentRef]` | All documents with dates to analyze |
| `docket_entries` | `List[DocketEntry]` | Court docket entries with timestamps |
| `communications` | `List[CommRecord]` | Emails, texts, letters with timestamps |
| `lane` | `str` | Case lane to analyze (or `"ALL"`) |
| `sensitivity` | `str` | Detection sensitivity: `"low"`, `"medium"`, `"high"` (default: `"medium"`) |

### DocketEntry Schema
```json
{
  "entry_id": "DE-001",
  "date": "2024-03-15",
  "description": "Order Modifying Custody entered",
  "filed_by": "Court",
  "case_number": "24-1847-FC",
  "related_doc_id": "DOC-2024-1847"
}
```

### CommRecord Schema
```json
{
  "comm_id": "COMM-001",
  "date": "2024-03-10",
  "type": "email",
  "from": "opposing_counsel@firm.com",
  "to": "judge_clerk@court.gov",
  "subject": "Re: Smith custody matter",
  "related_case": "24-1847-FC"
}
```

---

## Processing Methodology

### Anomaly Type 1: Backdated Orders

Detect court orders whose effective dates precede necessary procedural steps.

```
Detection Rules:
  - Order date < Motion filing date             → CRITICAL
  - Order date < Hearing date                   → CRITICAL
  - Order date < Service date on opposing party  → HIGH
  - Order signed date < Brief/response deadline  → HIGH
  - Order nunc pro tunc without explicit notation → CRITICAL

Validation:
  Compare order date against:
    1. Docket entry for related motion
    2. Proof of service dates
    3. Hearing transcript dates
    4. PDF metadata creation date
    5. Court e-filing timestamp
```

### Anomaly Type 2: Impossible Sequences

Detect event sequences that violate logical or procedural ordering.

```
Detection Rules:
  - Response filed before motion served                     → CRITICAL
  - Reply brief filed before response brief                 → HIGH
  - Judgment entered before trial commenced                  → CRITICAL
  - Appeal filed before judgment entered                     → MEDIUM (may be interlocutory)
  - Discovery responses before discovery requests served     → HIGH
  - Ex parte order entered on date with no court session     → CRITICAL
  - Custody evaluation completed before evaluator appointed  → HIGH

Michigan-Specific Sequences:
  - MCR 3.210: Motion → 9-day waiting period → Hearing → Order
  - MCR 2.119: Motion → 7-day service → Hearing → Order
  - MCR 3.207: Emergency motion → Same-day/next-day hearing → Temporary order
  - MCR 7.205: Application for leave → 21 days for answer → Decision
```

### Anomaly Type 3: Missing Docket Entries

Detect gaps where docket entries should exist but don't.

```
Detection Rules:
  - Motion filed but no hearing scheduled within 28 days         → MEDIUM
  - Hearing held but no order entered within 21 days             → HIGH
  - Order entered with no preceding motion on docket             → CRITICAL
  - Proof of service missing for filed motion                    → HIGH
  - Objection period passed with no docket activity              → MEDIUM
  - Custody evaluation ordered but no report filed               → HIGH
  - FOC recommendation issued but no hearing on objection        → HIGH

Gap Window Calculations:
  expected_entries = procedural_model(case_type, last_entry)
  actual_entries = docket_entries[date_range]
  missing = expected_entries - actual_entries
```

### Anomaly Type 4: Communication Record Gaps

Detect suspicious gaps or patterns in communication records.

```
Detection Rules:
  - Communications between court and one party with no corresponding 
    communication to other party                                    → CRITICAL (ex parte indicator)
  - Gap > 30 days in attorney-client communication during active phase → MEDIUM
  - Burst of communications immediately before adverse ruling         → HIGH
  - Email timestamps outside business hours to court staff            → LOW
  - Communication records missing for date range where activity 
    is documented on docket                                          → HIGH
```

### Anomaly Type 5: Document Metadata vs Content Date Mismatch

```
Detection Rules:
  - PDF creation date differs from document date by > 7 days         → HIGH
  - PDF modification date is after filing date                       → MEDIUM
  - Document references events that hadn't occurred at stated date   → CRITICAL
  - Scan timestamp predates the document date on face of document    → CRITICAL
```

---

## Scoring & Classification

Each anomaly receives a severity score:

```
Severity Levels:
  CRITICAL (0.90–1.00): Strong indicator of misconduct or fabrication
  HIGH     (0.70–0.89): Significant procedural violation
  MEDIUM   (0.40–0.69): Requires investigation but may have explanation
  LOW      (0.10–0.39): Minor irregularity, document for completeness

Anomaly Score Calculation:
  base_score = severity_weight × evidence_strength
  multiplier = 1.0
  if multiple anomalies cluster around same date:    multiplier += 0.2
  if anomaly involves judge directly:                multiplier += 0.3
  if anomaly pattern repeats across cases:           multiplier += 0.4
  final_score = min(base_score × multiplier, 1.0)
```

---

## Output Format

```json
{
  "detector": "timeline_anomaly_detector_v13",
  "analysis_scope": {
    "lane": "A",
    "date_range": ["2023-01-01", "2024-12-31"],
    "documents_analyzed": 312,
    "docket_entries_analyzed": 89,
    "communications_analyzed": 1247
  },
  "anomalies": [
    {
      "anomaly_id": "TA-001",
      "type": "BACKDATED_ORDER",
      "severity": "CRITICAL",
      "score": 0.95,
      "date": "2024-03-15",
      "description": "Custody modification order dated 2024-03-15 but no motion for modification appears on docket before this date. First related motion filed 2024-03-22.",
      "evidence": {
        "order_doc": "DOC-2024-1847",
        "order_date": "2024-03-15",
        "earliest_related_motion": "DOC-2024-1902",
        "motion_date": "2024-03-22",
        "gap_days": -7
      },
      "legal_implications": [
        "Violation of MCR 3.210(C) — no pending motion at time of order",
        "Due process violation — no notice or opportunity to be heard",
        "Potential grounds for appeal under MCR 7.203(A)"
      ],
      "recommended_actions": [
        "File motion for relief from judgment under MCR 2.612",
        "Request certified docket sheet to verify entries",
        "Preserve PDF metadata as evidence of creation date"
      ]
    }
  ],
  "timeline_visualization": {
    "events": [
      {"date": "2024-03-10", "type": "communication", "desc": "Email from OC to court clerk"},
      {"date": "2024-03-15", "type": "order", "desc": "Custody order entered", "anomaly": "TA-001"},
      {"date": "2024-03-22", "type": "motion", "desc": "Motion for custody modification filed"}
    ]
  },
  "summary": {
    "total_anomalies": 7,
    "critical": 2,
    "high": 3,
    "medium": 1,
    "low": 1,
    "pattern_detected": "Cluster of anomalies around March 2024 custody modification"
  }
}
```

---

## Integration Points

| Skill | Integration |
|-------|-------------|
| `evidence_chain_builder` | Anomalies generate chain-building inputs for misconduct claims |
| `case_lane_router` | Anomalies tagged with originating lane for routing context |
| `judicial_pattern_analyzer` | Critical anomalies involving judges feed directly into pattern analysis |
| `pdf_court_file_classifier` | Metadata dates from classification used for mismatch detection |
| `emergency_motion_generator` | Critical anomalies may trigger emergency motion generation |
| `timeline_engine` (engine) | Engine module performs the temporal computation |
| `docket_analyzer` (engine) | Provides parsed docket data for gap detection |
| `temporal_analyzer` (engine) | Low-level temporal comparison functions |

---

## Michigan-Specific Legal References

- **MCR 3.210(C)** — Required procedure before custody modification
- **MCR 2.119(C)** — Time for service and filing of motion responses
- **MCR 3.207** — Emergency procedures and timelines
- **MCR 2.612** — Relief from judgment (remedy for backdated/improper orders)
- **MCR 8.119** — Court records management requirements
- **MCL 722.27(1)(c)** — Proper cause / change of circumstances required before modification
- **U.S. Const. Amend. XIV** — Due process (notice and opportunity to be heard)
- **Mathews v. Eldridge, 424 U.S. 319 (1976)** — Due process balancing test
- **MCR 2.003(C)(1)** — Disqualification for bias (when anomalies implicate judge)

---

## Sensitivity Levels

| Level | Description |
|-------|-------------|
| `low` | Only flag CRITICAL anomalies with score ≥ 0.90 |
| `medium` | Flag CRITICAL and HIGH anomalies with score ≥ 0.70 |
| `high` | Flag all anomalies with score ≥ 0.40, including speculative patterns |
