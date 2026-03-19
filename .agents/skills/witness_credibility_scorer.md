# Witness Credibility Scorer v13.0.0

## LitigationOS Skill Module — Witness Reliability & Credibility Assessment

---

## Purpose and Scope

The Witness Credibility Scorer evaluates witness reliability by analyzing consistency of statements, level of independent corroboration, potential bias indicators, and prior contradictions. It produces a quantified credibility score that:

- Prioritizes witness preparation efforts
- Identifies impeachment opportunities for opposing witnesses
- Assesses the evidentiary weight of witness-dependent evidence chains
- Supports or challenges the court's credibility findings on appeal

This skill analyzes **documents and records** — it does not interact with witnesses directly.

---

## Input Requirements

| Field | Type | Description |
|-------|------|-------------|
| `witness_name` | `str` | Name of the witness to evaluate |
| `witness_role` | `str` | Role: `"party"`, `"expert"`, `"fact"`, `"character"`, `"court_officer"` |
| `statements` | `List[StatementRef]` | All known statements by this witness |
| `depositions` | `List[DocumentRef]` | Deposition transcripts |
| `affidavits` | `List[DocumentRef]` | Signed affidavits |
| `testimony` | `List[DocumentRef]` | Hearing/trial transcripts |
| `reports` | `List[DocumentRef]` | Expert reports, custody evaluations, FOC reports |
| `corroborating_docs` | `List[DocumentRef]` | Independent documents relevant to witness claims |
| `known_relationships` | `List[RelationshipRef]` | Relationships to parties |

### StatementRef Schema
```json
{
  "statement_id": "ST-001",
  "date": "2024-01-15",
  "context": "deposition",
  "source_doc": "DOC-2024-0501",
  "summary": "Witness stated Father was present at school pickup every day",
  "key_claims": [
    {"claim_id": "CL-001", "text": "Father present at school pickup daily", "verifiable": true}
  ]
}
```

---

## Processing Methodology

### Dimension 1: Internal Consistency Analysis

Compare all statements by the same witness across time and context.

```
Consistency Check Process:
  1. Extract all claims from all statements
  2. Group claims by topic/subject
  3. Compare claims within each topic group for contradictions
  4. Score consistency per topic and aggregate

Scoring:
  All claims consistent across all statements:              10/10
  Minor detail variations (dates off by 1-2 days):          8/10
  Moderate inconsistencies (conflicting descriptions):      5/10
  Direct contradictions on material facts:                   2/10
  Complete reversal of prior position:                       0/10

Contradiction Classification:
  TRIVIAL:    Irrelevant detail differences (color of shirt, exact time)
  MINOR:      Non-material differences (slightly different sequence)
  MATERIAL:   Contradictions on facts relevant to case issues
  CRITICAL:   Contradictions that undermine the witness's entire testimony
```

**Temporal Consistency:**
```
  - Do statements become more detailed over time? (Possible coaching indicator)
  - Do statements become less detailed over time? (Normal memory decay)
  - Do new claims appear in later statements that weren't in earlier ones?
  - Do claims disappear from later statements?
```

### Dimension 2: Corroboration Level

Assess how well independent evidence supports the witness's claims.

```
Corroboration Scoring per Claim:
  Fully corroborated by independent document:     10/10
  Partially corroborated (consistent but incomplete): 7/10
  Neither corroborated nor contradicted:           5/10
  Partially contradicted by independent evidence:  3/10
  Directly contradicted by independent evidence:   0/10

Independent Source Quality:
  Court records (orders, docket entries):  Weight ×1.0
  Official records (school, medical):     Weight ×0.9
  Third-party communications:             Weight ×0.7
  Other party's statements:               Weight ×0.5
  Self-serving documents:                 Weight ×0.2

Aggregate Corroboration Score:
  corroboration = weighted_avg(claim_scores × source_quality)
```

### Dimension 3: Bias Indicator Assessment

Evaluate potential motivations that could affect truthfulness.

```
Bias Categories and Weights:

  RELATIONSHIP BIAS (max 3.0 deduction)
    - Party to the case:                              -2.0
    - Family member of a party:                        -1.5
    - Close friend of a party:                         -1.0
    - Professional relationship (attorney, therapist): -0.5
    - No known relationship:                           -0.0
    
  FINANCIAL BIAS (max 2.0 deduction)
    - Paid expert witness:                             -1.0
    - Financial interest in outcome:                   -2.0
    - No financial interest:                           -0.0
    
  PROFESSIONAL BIAS (max 2.0 deduction)
    - History of advocacy for one position:            -1.5
    - Professional reputation at stake:                -1.0
    - Court-appointed (theoretically neutral):         -0.0
    
  RETALIATORY BIAS (max 2.0 deduction)
    - History of conflict with a party:                -1.5
    - Subject to complaint/discipline by a party:      -2.0
    - No known conflicts:                              -0.0

  INSTITUTIONAL BIAS (max 1.0 deduction)
    - FOC/court staff (systemic alignment):            -0.5
    - Government employee with policy constraints:     -0.5
    - Independent third party:                         -0.0

Bias Score = 10.0 - sum(applicable deductions), minimum 0.0
```

### Dimension 4: Prior Contradiction & Impeachment Analysis

Identify specific impeachment opportunities.

```
Impeachment Categories:
  1. PRIOR INCONSISTENT STATEMENT (MRE 613)
     Statement A (date 1) contradicts Statement B (date 2)
     Impeachment strength: based on materiality and clarity of contradiction
     
  2. BIAS/MOTIVE (MRE 616)
     Evidence showing witness has reason to fabricate or shade testimony
     
  3. CHARACTER FOR TRUTHFULNESS (MRE 608)
     Prior instances of dishonesty (not limited to convictions)
     
  4. CONVICTION (MRE 609)
     Felony convictions or dishonesty crimes within 10 years
     
  5. SPECIFIC CONTRADICTION BY EXTRINSIC EVIDENCE (MRE 613(b))
     Document or other witness directly contradicts a specific claim
     
  6. LACK OF PERSONAL KNOWLEDGE (MRE 602)
     Witness testifying about matters they couldn't have observed

Impeachment Score per Item:
  devastating (completely destroys credibility on topic):  10/10
  significant (raises serious doubt):                      7/10
  moderate (creates some doubt):                           5/10
  minor (noted but unlikely to change outcome):            3/10
```

### Dimension 5: Expert Witness Specific (if applicable)

```
Additional Metrics for Expert Witnesses:
  - Qualifications match opinions offered:     ____/10
  - Methodology generally accepted (Daubert):  ____/10
  - Sufficient factual basis for opinions:     ____/10
  - Opinions within scope of expertise:        ____/10
  - Consistency with own published work:       ____/10
  - Hired-gun indicator (always testifies for one side): ____/10
```

---

## Aggregate Credibility Score

```
Final Credibility Score Calculation:

  For fact/party witnesses:
    credibility = (
      consistency_score    × 0.30 +
      corroboration_score  × 0.30 +
      bias_score          × 0.20 +
      impeachment_inverse × 0.20     # (10 - impeachment_vulnerability)
    )

  For expert witnesses:
    credibility = (
      consistency_score    × 0.20 +
      corroboration_score  × 0.20 +
      bias_score          × 0.15 +
      impeachment_inverse × 0.15 +
      expert_score        × 0.30
    )

Classification:
  9.0–10.0:  Highly credible — strong witness
  7.0–8.9:   Credible — minor vulnerabilities
  5.0–6.9:   Moderate credibility — significant concerns
  3.0–4.9:   Low credibility — substantial impeachment available
  0.0–2.9:   Not credible — recommend exclusion or aggressive impeachment
```

---

## Output Format

```json
{
  "scorer": "witness_credibility_scorer_v13",
  "witness": "Dr. Jane Smith",
  "role": "expert",
  "credibility_score": 6.2,
  "classification": "Moderate credibility — significant concerns",
  "dimensions": {
    "consistency": {
      "score": 7.0,
      "contradictions": [
        {
          "topic": "Child's attachment status",
          "statement_1": {"date": "2024-02-01", "claim": "Child securely attached to both parents"},
          "statement_2": {"date": "2024-06-15", "claim": "Child primarily attached to Mother only"},
          "severity": "MATERIAL",
          "no_intervening_event": true
        }
      ]
    },
    "corroboration": {
      "score": 5.5,
      "uncorroborated_claims": [
        {"claim": "Father showed anger during evaluation", "source": "Only witness's report"}
      ],
      "contradicted_claims": [
        {"claim": "Child refused to engage with Father", "contradicted_by": "School records show Father at every parent event"}
      ]
    },
    "bias": {
      "score": 6.0,
      "indicators": [
        {"type": "PROFESSIONAL_BIAS", "detail": "Evaluator has testified for Mother's attorney in 4 prior cases", "deduction": -1.5},
        {"type": "FINANCIAL_BIAS", "detail": "Paid $15,000 by Mother for evaluation", "deduction": -1.0}
      ]
    },
    "impeachment": {
      "vulnerability_score": 6.5,
      "opportunities": [
        {
          "type": "PRIOR_INCONSISTENT_STATEMENT",
          "strength": 7,
          "detail": "February report says 'secure attachment to both'; June report says 'primary attachment to Mother only' with no intervening assessment",
          "mre_rule": "MRE 613"
        },
        {
          "type": "SPECIFIC_CONTRADICTION",
          "strength": 8,
          "detail": "Report claims Father disengaged from school — school records (Exhibit F) show Father attended all conferences",
          "mre_rule": "MRE 613(b)"
        }
      ]
    },
    "expert_specific": {
      "score": 6.5,
      "qualifications_match": 8,
      "methodology_accepted": 7,
      "factual_basis": 5,
      "scope_appropriate": 7,
      "consistency_with_publications": 4,
      "hired_gun_indicator": 6
    }
  },
  "recommended_actions": [
    "Prepare impeachment with school records contradicting disengagement claim",
    "Subpoena evaluator's billing records for prior cases with Mother's attorney",
    "Challenge methodology under Daubert/MRE 702 — insufficient factual basis",
    "Obtain evaluator's published articles on attachment for consistency comparison"
  ]
}
```

---

## Integration Points

| Skill | Integration |
|-------|-------------|
| `evidence_chain_builder` | Witness credibility scores weight evidence chain reliability |
| `harm_quantifier` | Evaluator credibility affects harm metric weight |
| `judicial_pattern_analyzer` | Judge's credibility findings compared against scorer output |
| `filing_optimizer` | Impeachment sections formatted for motion/brief use |
| `emergency_motion_generator` | Low-credibility evaluation may support emergency relief |
| `witness_prep` (engine) | Preparation focuses on areas of low credibility |
| `impeachment_generator` (engine) | Generates impeachment question sequences |

---

## Michigan-Specific Legal References

- **MRE 601** — General rule of competency
- **MRE 602** — Lack of personal knowledge
- **MRE 607** — Who may impeach a witness
- **MRE 608** — Evidence of character and conduct of witness
- **MRE 609** — Impeachment by evidence of conviction of crime
- **MRE 611** — Mode and order of interrogation and presentation
- **MRE 613** — Prior statements of witnesses
- **MRE 616** — Bias of witness
- **MRE 702** — Testimony by experts (Daubert standard in Michigan)
- **MRE 703** — Bases of opinion testimony by experts
- **MCL 600.2160** — Expert witness qualifications
- **Gilbert v DaimlerChrysler Corp, 470 Mich 749 (2004)** — Expert testimony standards
- **Elher v Misra, 499 Mich 11 (2016)** — Expert reliability requirements

---

## Limitations

1. This scorer analyzes **documented statements only** — it cannot assess demeanor, tone, or live testimony credibility.
2. Credibility scores are analytical tools, not admissible evidence. They guide strategy.
3. Bias indicators are flags, not conclusions — a biased witness can still be truthful.
4. Expert-specific scoring requires access to the expert's CV, publications, and prior testimony.
