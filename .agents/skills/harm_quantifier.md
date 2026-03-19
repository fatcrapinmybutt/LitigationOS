# Harm Quantifier v13.0.0

## LitigationOS Skill Module — Parent-Child Separation Harm Quantification

---

## Purpose and Scope

The Harm Quantifier measures and documents the harm caused by parent-child separation using evidence-based developmental psychology metrics, attachment theory frameworks, and Michigan statutory best-interest factor analysis under MCL 722.23.

This skill produces quantified harm assessments that:
- Support damages claims in § 1983 federal civil rights actions
- Demonstrate "irreparable harm" for emergency motion standards
- Provide structured best-interest factor analysis for custody proceedings
- Document ongoing developmental harm for appellate arguments
- Quantify the cumulative impact of prolonged separation

---

## Input Requirements

| Field | Type | Description |
|-------|------|-------------|
| `child_profiles` | `List[ChildProfile]` | Children affected by separation |
| `separation_events` | `List[SeparationEvent]` | Timeline of separation periods |
| `pre_separation_baseline` | `dict` | Baseline relationship quality before separation |
| `current_contact` | `dict` | Current level of parent-child contact |
| `professional_evaluations` | `List[DocumentRef]` | Psych evals, custody evaluations, GAL reports |
| `school_records` | `List[DocumentRef]` | Academic records showing impact |
| `medical_records` | `List[DocumentRef]` | Relevant medical/mental health records |

### ChildProfile Schema
```json
{
  "child_id": "CHILD-001",
  "age_at_separation": 5.5,
  "current_age": 7.2,
  "developmental_stage": "early_childhood",
  "pre_separation_attachment": "secure",
  "special_needs": [],
  "school_status": "enrolled"
}
```

### SeparationEvent Schema
```json
{
  "event_id": "SEP-001",
  "start_date": "2024-03-15",
  "end_date": null,
  "type": "full_separation",
  "cause": "court_order",
  "ordering_doc": "DOC-2024-1847",
  "prior_contact_level": "50_50_custody",
  "post_contact_level": "no_contact"
}
```

---

## Processing Methodology

### Framework 1: Developmental Impact Assessment

Based on established developmental psychology research, score impact by age group:

**Infant/Toddler (0–3 years):**
```
Metrics:
  - Attachment disruption severity (0–10)
    Secure attachment → No contact = 10 (catastrophic)
    Secure attachment → Supervised only = 7
    Insecure attachment → No contact = 6
  - Developmental milestone risk
    Language delay probability: +35% per 6 months separation
    Social-emotional delay probability: +45% per 6 months separation
    Regression risk (already-achieved milestones): +25%
  - Separation anxiety escalation (0–10)
    Based on duration × pre-separation attachment quality

Weight: ×1.5 (highest vulnerability period)
```

**Early Childhood (3–6 years):**
```
Metrics:
  - Self-blame / magical thinking severity (0–10)
    Children this age frequently believe they caused the separation
  - Behavioral regression indicators (0–10)
    Bed-wetting, thumb-sucking, tantrums beyond age-appropriate
  - Social development impact (0–10)
    Peer relationship formation, school readiness
  - Identity formation disruption (0–10)
    Child's sense of family, belonging, security

Weight: ×1.3
```

**Middle Childhood (6–12 years):**
```
Metrics:
  - Academic performance impact (0–10)
    GPA decline, attention/concentration issues, school avoidance
  - Peer relationship disruption (0–10)
    Social withdrawal, aggression, difficulty with trust
  - Loyalty conflict severity (0–10)
    Pressure to choose sides, alienation dynamics
  - Grief and loss processing (0–10)
    Ambiguous loss (parent alive but absent)

Weight: ×1.1
```

**Adolescent (12–18 years):**
```
Metrics:
  - Identity development disruption (0–10)
    Adolescent identity formation requires stable parental models
  - Risk behavior escalation (0–10)
    Substance use, delinquency, self-harm correlations
  - Academic/future planning impact (0–10)
    College preparation, career development, motivation
  - Autonomy development distortion (0–10)
    Premature independence vs. unhealthy dependence

Weight: ×1.0
```

### Framework 2: Attachment Theory Violation Analysis

Based on Bowlby's attachment theory and Ainsworth's classification:

```
Attachment Impact Score:

Pre-Separation Classification → Post-Separation Trajectory:
  Secure → Anxious-Ambivalent:    Score = 6
  Secure → Avoidant:              Score = 7
  Secure → Disorganized:          Score = 10 (most harmful)
  Anxious → Disorganized:         Score = 8
  Avoidant → Disorganized:        Score = 7

Duration Multiplier:
  < 1 month separation:   ×0.5 (potentially recoverable)
  1–3 months:             ×1.0
  3–6 months:             ×1.5
  6–12 months:            ×2.0
  12–24 months:           ×3.0 (significant long-term impact)
  24+ months:             ×4.0 (potentially permanent damage)

Contact Level Modifier:
  Regular meaningful contact maintained:     ×0.3
  Supervised contact only:                   ×0.7
  Phone/video only:                          ×0.8
  No contact:                                ×1.0

Attachment Harm Score = base_score × duration_multiplier × contact_modifier
```

### Framework 3: MCL 722.23 Best Interest Factor Analysis

Score each statutory factor for impact of separation:

```
MCL 722.23 Factors:
  (a) Love, affection, and emotional ties — Impact: ____/10
      How has separation affected the bond between parent and child?
      
  (b) Capacity to provide love, affection, guidance — Impact: ____/10
      Has the separated parent been prevented from providing guidance?
      
  (c) Capacity to provide food, clothing, medical care — Impact: ____/10
      Has the child's material welfare been affected?
      
  (d) Length of time in stable, satisfactory environment — Impact: ____/10
      Has separation disrupted an established custodial environment?
      
  (e) Permanence of existing or proposed custodial home — Impact: ____/10
      Does the separation create instability?
      
  (f) Moral fitness of parties — Impact: ____/10
      N/A to harm quantification (character of parents)
      
  (g) Mental and physical health of parties — Impact: ____/10
      Has separation caused mental health decline in parent or child?
      
  (h) Home, school, and community record — Impact: ____/10
      Has the child's school performance or community ties degraded?
      
  (i) Reasonable preference of child (if old enough) — Impact: ____/10
      Has the child expressed a preference being ignored?
      
  (j) Willingness to facilitate relationship — Impact: ____/10
      Is the custodial parent facilitating or hindering the bond?
      
  (k) Domestic violence — Impact: ____/10
      Is separation being used as a tool of control?
      
  (l) Any other relevant factor — Impact: ____/10
      Additional factors specific to the case
```

### Framework 4: Cumulative Harm Index

Aggregate all frameworks into a single harm index:

```
Cumulative Harm Index (CHI) Calculation:

  developmental_score = weighted_avg(age_group_metrics) × age_weight
  attachment_score = attachment_harm_score (from Framework 2)
  statutory_score = avg(factor_impacts) × factor_count_affected / 12
  
  CHI = (
    developmental_score × 0.35 +
    attachment_score × 0.35 +
    statutory_score × 0.30
  )

CHI Ranges:
  0.0–2.0:   Minimal measurable harm
  2.1–4.0:   Moderate harm — documented impact likely recoverable
  4.1–6.0:   Significant harm — professional intervention needed
  6.1–8.0:   Severe harm — irreparable harm standard likely met
  8.1–10.0:  Catastrophic harm — permanent developmental damage likely
```

---

## Output Format

```json
{
  "quantifier": "harm_quantifier_v13",
  "case": "24-1847-FC",
  "assessment_date": "2025-01-15",
  "children": [
    {
      "child_id": "CHILD-001",
      "age": 7.2,
      "separation_duration_months": 21.5,
      "cumulative_harm_index": 7.4,
      "classification": "Severe harm — irreparable harm standard likely met",
      "developmental_impact": {
        "stage": "middle_childhood",
        "metrics": {
          "academic_impact": 7,
          "peer_relationship": 6,
          "loyalty_conflict": 8,
          "grief_processing": 9
        },
        "weighted_score": 7.5
      },
      "attachment_analysis": {
        "pre_separation": "secure",
        "current_trajectory": "anxious-ambivalent",
        "base_score": 6,
        "duration_multiplier": 3.0,
        "contact_modifier": 1.0,
        "attachment_harm_score": 18.0,
        "normalized_score": 8.0
      },
      "best_interest_factors": {
        "a_emotional_ties": {"impact": 9, "narrative": "Complete severance of daily parental bond"},
        "b_guidance_capacity": {"impact": 8, "narrative": "Father unable to provide any guidance during separation"},
        "d_stable_environment": {"impact": 9, "narrative": "Established custodial environment disrupted"},
        "g_mental_health": {"impact": 7, "narrative": "Child showing anxiety symptoms per school counselor report"},
        "h_school_record": {"impact": 6, "narrative": "GPA dropped from 3.5 to 2.8 since separation"},
        "j_facilitate_relationship": {"impact": 8, "narrative": "Custodial parent resisting all contact"}
      },
      "supporting_evidence": [
        {"doc_id": "DOC-2024-2501", "type": "school_report", "relevance": "GPA decline documentation"},
        {"doc_id": "DOC-2024-2600", "type": "counselor_notes", "relevance": "Anxiety symptoms"}
      ]
    }
  ],
  "aggregate_harm": {
    "total_children_affected": 1,
    "mean_chi": 7.4,
    "max_chi": 7.4,
    "irreparable_harm_met": true,
    "emergency_relief_warranted": true
  },
  "legal_applications": {
    "emergency_motion": "CHI ≥ 6.0 supports irreparable harm showing per MCR 3.207",
    "appellate_argument": "Severe harm supports abuse-of-discretion standard on appeal",
    "section_1983": "CHI ≥ 8.0 supports substantive due process violation claim",
    "best_interest_reanalysis": "Separation harm changes factor analysis under MCL 722.23"
  }
}
```

---

## Integration Points

| Skill | Integration |
|-------|-------------|
| `evidence_chain_builder` | Harm metrics become conclusion evidence in chains |
| `emergency_motion_generator` | CHI ≥ 6.0 triggers emergency motion generation |
| `judicial_pattern_analyzer` | Harm caused by judicial misconduct quantified here |
| `filing_optimizer` | Harm quantification formatted as exhibit for filings |
| `timeline_anomaly_detector` | Separation events correlated with timeline anomalies |
| `witness_credibility_scorer` | Professional evaluator credibility affects metric weight |
| `harms_calculator` (engine) | Engine performs numerical computation |

---

## Michigan-Specific Legal References

- **MCL 722.23** — Best interest of the child factors (a)–(l)
- **MCL 722.25** — Established custodial environment
- **MCL 722.27** — Custody modification standards
- **MCL 722.27a** — Parenting time; best interest of child
- **MCR 3.210(C)** — Custody proceedings requirements
- **MCR 3.207(B)** — Standard for emergency/ex parte relief
- **Troxel v Granville, 530 US 57 (2000)** — Fundamental parental rights
- **Santosky v Kramer, 455 US 745 (1982)** — Due process in parental rights
- **Vodvarka v Grasmeyer, 259 Mich App 499 (2003)** — Proper cause / change of circumstances
- **Lieberman et al., "The Impact of Separation on Children"** — Developmental research basis

---

## Ethical Safeguards

1. Harm scores are **evidence-based estimates**, not clinical diagnoses. They do not replace professional evaluation.
2. Always recommend professional assessment when CHI ≥ 4.0.
3. Never overstate harm for tactical advantage — courts penalize exaggeration.
4. Children's privacy must be protected — use initials or pseudonyms in filings per MCR 3.903(A).
5. Harm quantification must account for harm from **both** sides — including harm from maintaining an unsafe environment.
