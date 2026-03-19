# Case Lane Router v13.0.0

## LitigationOS Skill Module — Document-to-Lane Routing Engine

---

## Purpose and Scope

The Case Lane Router analyzes incoming documents and assigns them to the correct case lane (A through G) based on content analysis, keyword patterns, party references, and court references. Each lane represents a distinct legal matter or thread within the litigation portfolio.

Accurate routing ensures:
- Documents are discoverable within the correct case context.
- Evidence chains are built within the right lane.
- Cross-lane references are properly linked rather than misfiled.
- No document is orphaned or routed to a catch-all bucket.

---

## Input Requirements

| Field | Type | Description |
|-------|------|-------------|
| `document_path` | `FilePath` | Path to the document to route |
| `extracted_text` | `str` | Pre-extracted text (optional; will OCR if absent) |
| `metadata` | `dict` | PDF/DOCX metadata if available |
| `classification` | `str` | Output from `pdf_court_file_classifier` |
| `force_lane` | `str` | Manual override lane (optional) |
| `multi_lane` | `bool` | Allow routing to multiple lanes (default: `false`) |

---

## Lane Definitions

### Lane A — Primary Custody & Parenting Time
```
Keywords:     custody, parenting time, parenting plan, best interest, MCL 722.23,
              best interest factors, established custodial environment, proper cause,
              change of circumstances, overnight, visitation, FOC, Friend of the Court,
              parenting schedule, holiday schedule, summer parenting
Party refs:   Primary custodial parent, non-custodial parent, minor child(ren)
Court refs:   Family Division, Circuit Court — Family, FC docket prefix
MCR refs:     MCR 3.210, MCR 3.211, MCR 3.214
```

### Lane B — Domestic Violence & Personal Protection Orders
```
Keywords:     PPO, personal protection order, domestic violence, assault, threat,
              stalking, harassment, MCL 600.2950, restraining order, no-contact,
              safe haven, DV shelter, lethality assessment, VINE notification
Party refs:   Petitioner, Respondent, protected person
Court refs:   Circuit Court, PPO docket
MCR refs:     MCR 3.701, MCR 3.703, MCR 3.705, MCR 3.706, MCR 3.707, MCR 3.708
```

### Lane C — Financial & Support Matters
```
Keywords:     child support, spousal support, alimony, income, UIFSA, arrearage,
              garnishment, income withholding, MiChildSupport, deviation, imputed income,
              financial disclosure, uniform support order, MCL 552.605, FOC recommendation
Party refs:   Obligor, Obligee, payee, payer
Court refs:   FOC, Friend of the Court, IV-D
MCR refs:     MCR 3.211, MCR 3.213, MCR 3.206(C)
```

### Lane D — Discovery & Evidence Disputes
```
Keywords:     interrogatories, request for production, deposition, subpoena, FOIA,
              discovery motion, compel, sanctions, protective order, privilege log,
              document request, admission, Rule 35 examination, expert witness,
              forensic examination
Party refs:   Requesting party, Responding party, deponent, witness
Court refs:   Any court handling discovery motions
MCR refs:     MCR 2.302, MCR 2.306, MCR 2.307, MCR 2.310, MCR 2.312, MCR 2.313
```

### Lane E — Judicial Conduct & Due Process
```
Keywords:     judicial misconduct, ex parte, bias, disqualification, recusal,
              due process, 14th amendment, equal protection, Canons of Judicial Conduct,
              JTC, Judicial Tenure Commission, MCR 2.003, appearance of impropriety,
              judicial immunity, mandamus, superintending control
Party refs:   Judge (named), referee, magistrate, JTC
Court refs:   Court of Appeals, Supreme Court, JTC
MCR refs:     MCR 2.003, MCR 7.203, MCR 7.301, MCR 9.200 series
```

### Lane F — Appeals & Post-Judgment
```
Keywords:     appeal, appellate, Court of Appeals, leave to appeal, claim of appeal,
              brief on appeal, standard of review, abuse of discretion, clearly erroneous,
              de novo, remand, affirm, reverse, motion for reconsideration, relief from
              judgment, MCR 2.612, post-judgment, modification
Party refs:   Appellant, Appellee, cross-appellant
Court refs:   Michigan Court of Appeals, Michigan Supreme Court
MCR refs:     MCR 7.101, MCR 7.201, MCR 7.203, MCR 7.205, MCR 7.212, MCR 7.215
```

### Lane G — Federal & Civil Rights
```
Keywords:     42 USC 1983, Section 1983, civil rights, federal court, USDC,
              constitutional violation, Monell, qualified immunity, deliberate indifference,
              color of state law, federal question, 28 USC 1331, 28 USC 1343,
              Bivens, substantive due process, procedural due process, Rooker-Feldman
Party refs:   Plaintiff (federal), Defendant (government actor), municipality
Court refs:   U.S. District Court, Eastern/Western District of Michigan, Sixth Circuit
MCR refs:     N/A — Federal Rules of Civil Procedure apply (FRCP)
```

---

## Processing Methodology

### Step 1: Text Extraction
If `extracted_text` is not provided, extract text using:
1. PDF text layer extraction (if available)
2. OCR via local Tesseract (if scanned)
3. DOCX paragraph extraction
4. Plain text read

### Step 2: Keyword Scoring
For each lane, compute a keyword match score:

```
For each lane L in [A, B, C, D, E, F, G]:
    score[L] = 0
    for each keyword K in lane L keywords:
        count = occurrences of K in extracted_text (case-insensitive)
        if count > 0:
            score[L] += weight(K) * min(count, 5)  # Cap at 5 to prevent flooding

Keyword Weights:
    Primary keywords (e.g., "custody", "PPO", "child support"):  3.0
    Secondary keywords (e.g., "parenting time", "garnishment"):   2.0
    Tertiary keywords (e.g., "schedule", "income"):               1.0
    MCR/MCL references specific to a lane:                        4.0
```

### Step 3: Party Reference Matching
Scan for party references that indicate a specific lane:

```
For each lane L:
    for each party_pattern P in lane L party refs:
        if P found in text:
            score[L] += 2.5
```

### Step 4: Court Reference Matching
Match court and docket references:

```
For each lane L:
    for each court_ref C in lane L court refs:
        if C found in text:
            score[L] += 3.0
    
    # Docket prefix matching (e.g., "24-1847-FC" → Lane A)
    if docket prefix matches lane L pattern:
        score[L] += 5.0
```

### Step 5: Normalization & Decision

```
normalized_scores = {L: score[L] / max_possible_score[L] for L in lanes}
primary_lane = argmax(normalized_scores)

if multi_lane:
    assigned_lanes = [L for L in lanes if normalized_scores[L] >= 0.30]
else:
    assigned_lanes = [primary_lane]

if max(normalized_scores.values()) < 0.15:
    assigned_lanes = ["UNROUTED"]
    flag = "REQUIRES_MANUAL_REVIEW"
```

---

## Output Format

```json
{
  "router": "case_lane_router_v13",
  "document": "incoming\\2024-03-15_motion.pdf",
  "primary_lane": "A",
  "assigned_lanes": ["A"],
  "confidence": 0.87,
  "scores": {
    "A": 0.87,
    "B": 0.12,
    "C": 0.34,
    "D": 0.08,
    "E": 0.05,
    "F": 0.02,
    "G": 0.00
  },
  "routing_evidence": {
    "keywords_matched": {
      "A": ["custody", "parenting time", "best interest", "MCL 722.23"],
      "C": ["child support", "income"]
    },
    "party_refs_matched": ["custodial parent", "minor child"],
    "court_refs_matched": ["Circuit Court — Family"],
    "docket_prefix": "FC"
  },
  "cross_lane_links": [
    {"lane": "C", "reason": "Financial references in custody document", "score": 0.34}
  ]
}
```

---

## Integration Points

| Skill | Integration |
|-------|-------------|
| `pdf_court_file_classifier` | Classification result informs routing weight (real court files get priority routing) |
| `convergence_dedup_engine` | Cross-lane duplicate sets flagged for unified routing |
| `evidence_chain_builder` | Routed documents feed into lane-specific evidence chains |
| `timeline_anomaly_detector` | Anomalies detected within lane context |
| `judicial_pattern_analyzer` | Lane E documents automatically feed judicial analysis |
| `scan_ingester` (engine) | Ingester triggers router after classification |
| `litigation-convergence-orchestrator` | Orchestrator manages routing queue and conflicts |

---

## Michigan-Specific Legal References

- **MCR 3.201** — Applicability of family division sub-chapters (defines Lane A/B/C scope)
- **MCL 722.21–722.31** — Child Custody Act (Lane A primary statute)
- **MCL 600.2950** — Personal Protection Orders (Lane B primary statute)
- **MCL 552.601–552.650** — Support and Parenting Time Enforcement Act (Lane C)
- **MCR 2.302–2.313** — Discovery rules (Lane D)
- **MCR 2.003** — Disqualification of judges (Lane E)
- **MCR 7.201–7.215** — Appeals (Lane F)
- **42 USC § 1983** — Federal civil rights (Lane G)

---

## Conflict Resolution

When a document scores above threshold in multiple lanes:
1. **Primary lane** = highest scoring lane.
2. **Cross-lane links** are created for secondary lanes scoring ≥ 0.30.
3. The document is stored in the primary lane with symlinks/references in secondary lanes.
4. If `multi_lane` is enabled, full copies are placed in each qualifying lane.
5. If two lanes score within 0.05 of each other, flag for manual review.
