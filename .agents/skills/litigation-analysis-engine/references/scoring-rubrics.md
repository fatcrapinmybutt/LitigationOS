# Scoring Rubrics — Litigation Analysis Engine Reference

## Evidence Strength Scoring Matrix

### Overview
All evidence in LitigationOS is scored on a 0-100 scale using the EGCP method. This rubric defines how each component is calculated per claim type and lane assignment.

### EGCP Component Definitions

#### E — Evidence Completeness (0-25 points)
Measures whether all required evidentiary elements are present for the claim.

| Score | Description | Criteria |
|-------|-------------|----------|
| 0-5 | Critical gaps | Missing 3+ essential elements |
| 6-10 | Major gaps | Missing 2 essential elements |
| 11-15 | Moderate gaps | Missing 1 essential element |
| 16-20 | Minor gaps | All essential elements present, supporting evidence thin |
| 21-25 | Complete | All essential and supporting evidence present |

**Lane A Example (Custody Modification under MCL 722.27):**
- Essential: Change in circumstances evidence (required)
- Essential: Best-interest factor evidence for at least factors (a), (b), (c), (j)
- Supporting: Evidence for remaining factors (d)-(l)
- Supporting: Third-party corroboration (school, medical, counselor)

#### G — Gap Severity (0-25 points, inverse scoring)
Measures how critical the missing evidence is. Higher score = fewer/less critical gaps.

| Score | Description | Impact |
|-------|-------------|--------|
| 0-5 | Fatal gaps | Missing evidence that opposing counsel WILL exploit |
| 6-10 | Serious gaps | Missing evidence that weakens core argument |
| 11-15 | Moderate gaps | Missing evidence that affects persuasiveness |
| 16-20 | Minor gaps | Missing evidence that is nice-to-have |
| 21-25 | No gaps | Evidence package is comprehensive |

**Gap Classification by Claim Type:**
```
FATAL GAPS (filing should be delayed):
  - Custody modification without change-in-circumstances evidence
  - Contempt motion without copy of the violated order
  - Emergency motion without imminent harm evidence
  - PPO without qualifying conduct evidence (MCL 600.2950)

SERIOUS GAPS (filing possible but weakened):
  - Best-interest analysis missing Factor (j) evidence
  - Authority chain with only persuasive (no binding) authority
  - Financial claims without documentary support

MODERATE GAPS (filing viable, address in reply):
  - Missing third-party corroboration
  - Incomplete timeline for pattern evidence
  - Missing parenthetical explanations in authority chain
```

#### C — Citation Strength (0-25 points)
Measures the completeness and currency of the legal authority chain.

| Score | Description | Authority Chain Status |
|-------|-------------|----------------------|
| 0-5 | No authority | No legal citations supporting propositions |
| 6-10 | Weak authority | Only persuasive or unpublished authority cited |
| 11-15 | Moderate | Binding authority cited but chain incomplete |
| 16-20 | Strong | Complete chain: statute + binding case + pinpoint |
| 21-25 | Comprehensive | Multiple binding authorities with parentheticals |

**Michigan Authority Hierarchy (binding strength order):**
1. Michigan Constitution
2. Michigan Legislature (MCL statutes)
3. Michigan Supreme Court published opinions
4. Michigan Court of Appeals published opinions (MCR 7.215(C)(1))
5. Michigan Court of Appeals unpublished opinions (persuasive only)
6. Federal courts on Michigan law questions (persuasive)
7. Other state courts (persuasive)

#### P — Persuasion Potential (0-25 points)
Measures overall narrative coherence and judicial impact.

| Score | Description | Assessment |
|-------|-------------|-----------|
| 0-5 | Not persuasive | Disjointed facts, no narrative arc |
| 6-10 | Weakly persuasive | Facts present but poorly organized |
| 11-15 | Moderately persuasive | Clear argument but rebuttable |
| 16-20 | Strongly persuasive | Compelling narrative with strong evidence |
| 21-25 | Highly persuasive | Overwhelming evidence, minimal rebuttal surface |

### Filing Threshold Matrix

| Filing Type | Minimum EGCP | Lane | Authority |
|-------------|-------------|------|-----------|
| Custody Modification Motion | 65 | A | MCL 722.27, MCR 3.210 |
| Emergency Custody Motion | 55 | A | MCR 3.207(A) |
| PPO Modification | 60 | D | MCL 600.2950, MCR 3.310 |
| Summary Disposition (no issue of fact) | 75 | B | MCR 2.116(C)(10) |
| Summary Disposition (legal question) | 70 | B | MCR 2.116(C)(8) |
| Contempt Motion | 70 | A/D | MCL 600.1701, MCR 3.606 |
| Judicial Disqualification | 75 | E | MCR 2.003(C) |
| Appeal Brief | 70 | F | MCR 7.212 |
| Leave Application (MSC) | 80 | F | MCR 7.302 |
| Default Judgment | 60 | B | MCR 2.603 |
| Fee Petition | 65 | All | MCR 2.625 |
| Discovery Motion to Compel | 55 | All | MCR 2.313 |
| TRO Application | 60 | B | MCR 3.310 |

### Per-Factor Scoring Guide (Lane A — Custody)

#### MCL 722.23 Best-Interest Factors

| Factor | Evidence Types Scored | Max Points | Key Cases |
|--------|----------------------|-----------|-----------|
| (a) Love/affection/ties | Parenting logs, photos, testimony | 8 | *Ireland v Smith*, 451 Mich 457 (1996) |
| (b) Capacity for guidance | Employment, stability, parenting plans | 8 | *Foskett v Foskett*, 247 Mich App 1 (2001) |
| (c) Material provision | Financial records, housing, insurance | 8 | *Berger v Berger*, 277 Mich App 700 (2008) |
| (d) Stable environment | Residence history, school continuity | 8 | *Mogle v Scriver*, 241 Mich App 192 (2000) |
| (e) Family permanence | Household composition, relationships | 6 | *Grew v Knox*, 265 Mich App 333 (2005) |
| (f) Moral fitness | Criminal records, substance use, conduct | 8 | *Fletcher v Fletcher*, 447 Mich 871 (1994) |
| (g) Health | Medical records, mental health eval | 6 | *Grew v Knox*, supra |
| (h) School/community | Report cards, activities, community ties | 6 | *Foskett*, supra |
| (i) Child's preference | Age-appropriate interview/statement | 4-8 | *Pierron v Pierron*, 282 Mich App 222 (2009) |
| (j) Facilitate relationship | Communication logs, co-parenting | 10 | *Demski v Petlick*, 309 Mich App 404 (2015) |
| (k) Domestic violence | PPO records, police reports, CPS | 10 | *MCL 722.23(k)*, *Pennington v Pennington* |
| (l) Other factors | Any relevant evidence | 4 | Court discretion |

### Scoring Calibration Notes

1. **Never auto-score above 20/25 on any component** without human verification
2. **Gap severity must account for opposing party's likely evidence** — not just what we have
3. **Citation strength requires currency check** — a 25/25 score drops to 0 if authority is overruled
4. **Persuasion scoring is subjective** — calibrate against known judicial preferences (Judge McNeill weighs Factor (j) heavily in Lane A)
5. **EGCP scores below filing threshold = acquisition task**, not a filing task
6. **Recalibrate scores after every significant event** — new evidence, new order, new deadline
