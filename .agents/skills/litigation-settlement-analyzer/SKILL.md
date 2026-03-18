---
name: litigation-settlement-analyzer
description: >-
  Settlement valuation, negotiation strategy, and mediation preparation specialist for
  Michigan family law litigation. Calculates expected case value, generates demand letters,
  prepares mediation briefs, and analyzes per-defendant settlement strategy.
  Use when: settlement, valuation, demand letter, case evaluation, offer of judgment,
  BATNA, WATNA, mediation brief, structured settlement, per-defendant allocation,
  negotiation strategy, settlement conference, MCR 2.403, MCR 2.405.
metadata:
  category: discipline
  author: andrew-pigors
  version: "1.0.0"
  triggers: settlement, valuation, demand, offer of judgment, BATNA, mediation brief
---

# LITIGATION-SETTLEMENT-ANALYZER

## Metadata
- **name**: litigation-settlement-analyzer
- **category**: discipline
- **tier**: 2
- **version**: 1.0.0
- **context**: Pigors v Watson, 14th Judicial Circuit, Muskegon County, MI (Pro Se)
- **depends-on**: litigation-harm-quantifier, litigation-damages-calculator, litigation-analysis-engine

## Description

Expert settlement valuation and negotiation strategy system for multi-defendant Michigan
family law litigation. Performs expected-value analysis (probability of success × damages)
per claim and per defendant. Generates demand letters, case evaluation summaries under
MCR 2.403, and offer of judgment packages under MCR 2.405. Handles per-defendant
settlement allocation across 19 defendants and 6 case lanes. Integrates BATNA/WATNA
analysis, structured settlement comparison, and tax implications assessment.

**Party context:**
- Plaintiff: Andrew James Pigors (Pro Se), 1977 Whitehall Road, Lot 17, North Muskegon MI 49445
- Defendant: Emily A. Watson (NOT "Emily Ann")
- Child: L.D.W. per MCR 8.119(H) — MALE
- Judge: Hon. Jenny L. McNeill — 14th Circuit Court
- 19 defendants across 6 case lanes and 8 jurisdictions

## Capabilities

1. **Expected Value Analysis** — Probability-weighted damages per claim and defendant
2. **BATNA/WATNA Analysis** — Best/Worst alternatives to negotiated agreement
3. **Settlement Demand Letter Generation** — Per-defendant demand packages
4. **Case Evaluation Preparation** — MCR 2.403 case evaluation summary
5. **Offer of Judgment Drafting** — MCR 2.405 offers with costs implications
6. **Mediation Brief Preparation** — MCR 3.216 domestic relations mediation
7. **Per-Defendant Allocation Strategy** — Joint/several liability allocation
8. **Tax Implications Analysis** — Settlement structure tax consequences
9. **Structured Settlement Comparison** — Lump sum vs. structured analysis

## Requirements

- All valuations MUST be evidence-based — cite specific exhibits and damages proof
- BATNA must account for Pro Se status (no attorney fee recovery in most MI claims)
- MCR 2.403 case evaluation: rejection costs apply if verdict exceeds by 10%
- MCR 2.405 offer of judgment: costs/interest accrue from date of rejected offer
- Per-defendant allocation must respect joint and several liability rules
- Custody-related claims (Lane A) are non-monetary — use best-interest factors
- Housing claims (Lane B) have statutory damages under consumer protection laws
- All dollar figures must be supported by documentation in evidence chain

## Patterns

### Pattern 1: Expected Value Case Valuation

```python
from legal_ai.engines import SettlementEngine
from legal_ai.models import ClaimValuation, CaseValuation

def calculate_case_value(case_lane: str) -> CaseValuation:
    """Expected value analysis: probability × damages per claim."""
    engine = SettlementEngine()

    claims = engine.get_claims_by_lane(case_lane)
    valuations = []

    for claim in claims:
        # Probability based on evidence strength and legal merit
        prob_success = engine.assess_probability(
            claim_type=claim.claim_type,
            evidence_strength=claim.evidence_score,
            legal_merit=claim.legal_merit_score,
            jurisdiction_factors=claim.jurisdiction,
        )

        # Damages range from harm quantifier
        damages_low = claim.damages_floor
        damages_high = claim.damages_ceiling
        damages_mid = (damages_low + damages_high) / 2

        valuation = ClaimValuation(
            claim_id=claim.claim_id,
            claim_type=claim.claim_type,
            probability_of_success=prob_success,
            damages_low=damages_low,
            damages_mid=damages_mid,
            damages_high=damages_high,
            expected_value_low=prob_success * damages_low,
            expected_value_mid=prob_success * damages_mid,
            expected_value_high=prob_success * damages_high,
        )
        valuations.append(valuation)

    total_ev = sum(v.expected_value_mid for v in valuations)

    return CaseValuation(
        case_lane=case_lane,
        claim_valuations=valuations,
        total_expected_value=total_ev,
        total_damages_range=(
            sum(v.damages_low for v in valuations),
            sum(v.damages_high for v in valuations),
        ),
    )
```

### Pattern 2: Per-Defendant Settlement Demand

```python
from legal_ai.engines import SettlementEngine, DemandLetterDrafter

def generate_demand_letter(
    defendant_name: str,
    claims_against: list[str],
    supporting_exhibits: list[str],
    demand_amount: float,
    response_deadline_days: int = 30,
) -> dict:
    """Generate per-defendant settlement demand letter."""
    engine = SettlementEngine()
    drafter = DemandLetterDrafter()

    # Pull defendant-specific liability analysis
    liability = engine.assess_defendant_liability(
        defendant=defendant_name,
        claims=claims_against,
    )

    letter = drafter.draft_demand(
        plaintiff="Andrew James Pigors",
        defendant=defendant_name,
        case_number=engine.get_primary_case_number(defendant_name),
        court="14th Circuit Court, Muskegon County",
        claims=claims_against,
        liability_summary=liability,
        exhibits=supporting_exhibits,
        demand_amount=demand_amount,
        response_deadline_days=response_deadline_days,
        # Include MCR 2.405 offer of judgment warning
        offer_of_judgment_notice=True,
        # Pro Se: emphasize costs, not attorney fees
        costs_warning="Rejection may result in costs and interest per MCR 2.405",
    )

    return {
        "letter": letter,
        "defendant": defendant_name,
        "demand_amount": demand_amount,
        "response_deadline": response_deadline_days,
    }
```

### Pattern 3: MCR 2.403 Case Evaluation Summary

```python
from legal_ai.engines import SettlementEngine

def prepare_case_evaluation_summary(case_lane: str) -> dict:
    """MCR 2.403 case evaluation panel preparation."""
    engine = SettlementEngine()

    valuation = engine.calculate_case_value(case_lane)
    evidence_summary = engine.summarize_evidence(case_lane)
    legal_theories = engine.list_legal_theories(case_lane)

    summary = {
        "case_number": engine.get_case_number(case_lane),
        "plaintiff": "Andrew James Pigors",
        "defendant_list": engine.get_defendants(case_lane),
        "claims": legal_theories,
        "evidence_summary": evidence_summary,
        "damages_range": valuation.total_damages_range,
        "recommended_evaluation": valuation.total_expected_value,
        # MCR 2.403(O): rejection consequences
        "rejection_consequences": {
            "rule": "MCR 2.403(O)",
            "effect": "Rejecting party pays costs if verdict is more favorable "
                      "to accepting party by at least 10%",
            "costs_include": [
                "Reasonable attorney fees (not applicable to Pro Se)",
                "Actual costs and filing fees",
                "Expert witness fees",
            ],
        },
    }

    return summary
```

### Pattern 4: BATNA/WATNA Analysis

```python
from legal_ai.engines import SettlementEngine
from legal_ai.models import NegotiationAnalysis

def analyze_negotiation_position(
    settlement_offer: float,
    case_lane: str,
) -> NegotiationAnalysis:
    """Best/Worst Alternative to Negotiated Agreement."""
    engine = SettlementEngine()
    valuation = engine.calculate_case_value(case_lane)

    batna = engine.calculate_batna(
        expected_value=valuation.total_expected_value,
        litigation_costs=engine.estimate_costs(case_lane),
        time_to_trial_months=engine.estimate_time_to_trial(case_lane),
        emotional_cost_factor=0.15,  # 15% discount for stress/time
    )

    watna = engine.calculate_watna(
        worst_case_damages=0,  # Complete loss
        litigation_costs=engine.estimate_costs(case_lane),
        adverse_costs_risk=engine.estimate_adverse_costs(case_lane),
    )

    return NegotiationAnalysis(
        settlement_offer=settlement_offer,
        batna_value=batna,
        watna_value=watna,
        expected_trial_value=valuation.total_expected_value,
        recommendation=(
            "ACCEPT" if settlement_offer >= batna
            else "COUNTER" if settlement_offer >= watna
            else "REJECT"
        ),
        zone_of_possible_agreement=(watna, batna),
    )
```

## Anti-Patterns

### Anti-Pattern 1: Valuing Without Evidence Support
```python
# WRONG — Speculative damages with no documentation
claim.damages_high = 500_000  # arbitrary number

# CORRECT — Evidence-based with exhibit citations
claim.damages_high = engine.compute_damages(
    economic=[("lost wages", 45_000, "Exhibit A-12")],
    statutory=[("consumer protection treble", 3, "MCL 600.3204")],
)
```

### Anti-Pattern 2: Ignoring Case Evaluation Rejection Costs
```python
# WRONG — Rejecting MCR 2.403 evaluation without cost analysis
reject_evaluation(evaluation_amount=50_000)  # blind rejection

# CORRECT — Calculate rejection risk per MCR 2.403(O)
risk = engine.calculate_rejection_risk(
    evaluation_amount=50_000,
    expected_verdict=valuation.expected_value,
    # Rejection penalty triggers if verdict exceeds by 10%
    threshold_percentage=0.10,
)
if risk.penalty_likely:
    print(f"WARNING: Rejection may cost ${risk.estimated_penalty}")
```

### Anti-Pattern 3: Single Demand for All Defendants
```python
# WRONG — One blanket demand to 19 defendants
demand = {"all_defendants": 1_000_000}

# CORRECT — Per-defendant allocation based on liability share
for defendant in defendants:
    allocation = engine.allocate_liability(
        defendant=defendant,
        joint_several=True,
        contribution_share=defendant.liability_percentage,
    )
    generate_demand_letter(defendant.name, allocation.amount)
```

## Michigan-Specific Rules

| Rule | Subject | Key Requirement |
|------|---------|-----------------|
| **MCR 2.403** | Case evaluation | 3-member panel; rejection costs if verdict exceeds by 10% |
| **MCR 2.405** | Offer of judgment | Costs/interest from date of rejected offer to verdict |
| **MCR 3.216** | Domestic relations mediation | Mandatory in custody disputes; confidential |
| **MCL 600.4969** | Structured settlements | Governs periodic payment of judgments |
| **MCR 2.403(O)** | Rejection consequences | Actual costs, expert fees; NOT attorney fees for Pro Se |
| **MCR 2.405(D)** | Costs after rejection | Interest on judgment from offer date; taxable costs |

### Case Evaluation (MCR 2.403) Key Points
- Panel of 3 attorneys evaluates the case
- Each side presents a 30-minute summary
- Panel issues a unanimous or majority evaluation
- Parties have 28 days to accept or reject
- Rejection risk: if trial verdict differs by more than 10%, rejecting party pays costs

### Offer of Judgment (MCR 2.405) Key Points
- Either party may serve a written offer at least 28 days before trial
- If rejected and verdict is more favorable to offeror, offeree pays:
  - Taxable costs from date of offer
  - Interest on judgment from date of offer at rate per MCL 600.6013

## Integration Points

- **litigation-harm-quantifier**: Provides damages calculations for valuation input
- **litigation-damages-calculator**: Computes economic/non-economic damages per claim
- **litigation-analysis-engine**: Supplies evidence strength scores and legal merit
- **litigation-mediation-strategist**: Uses valuations for mediation preparation
- **litigation-brief-writer**: Drafts case evaluation summaries and demand letters
- **litigation-convergence-orchestrator**: Coordinates multi-lane settlement strategy
- **litigation-filing-architect**: Formats MCR 2.403/2.405 filings for court


---

## 🔬 Pass 1: Data Intelligence Layer
*Enhanced: 2026-03-12 | Source: mega_file_harvest (53,625 files)*

### Live Database Arsenal
| Table | Records | Intelligence Value |
|-------|--------:|-------------------|
| `mega_file_harvest` | 53,625 | Complete file index with citations and metadata |
| `evidence_quotes` | 308,704 | Extracted evidence passages with legal significance |
| `contradiction_map` | 10,672 | Detected contradictions across all documents |
| `impeachment_items` | 15,171 | Impeachment-ready witness inconsistencies |
| `judicial_violations` | 1,127 | Documented judicial conduct violations |
| `pages` | 472,482 | Raw page text from ingested documents |
| `master_citations` | 3,684,757 | Extracted citations across all sources |
| `claims` | 653 | Active claims matrix with status tracking |
| `vehicles` | 6 | Filing vehicles with readiness scores |
| `authority_chains` | 28 | Authority chains with completeness scoring |
| `filing_readiness` | 24 | Per-vehicle filing readiness assessment |

### Case Lane Intelligence
| Lane | Files Indexed | Case | Court |
|------|-------------:|------|-------|
| A | 3,502 | 2024-001507-DC | 14th Circuit, Muskegon County |
| B | 3,531 | 2025-002760-CZ | 14th Circuit, Muskegon County |
| C | 279 | USDC filing pending | U.S. District Court, W.D. Michigan |
| D | 6,462 | 2023-5907-PP | 14th Circuit |
| E | 9,945 | JTC Complaint - McNeill | Judicial Tenure Commission |

### Harvest-Discovered Citations (New)
| MCR Citation | Files Found | Status |
|-------------|----------:|--------|
| MCR 2.003 | 1980 | 🆕 Verify & integrate |
| MCR 2.119 | 1635 | 🆕 Verify & integrate |
| MCR 2.107 | 1369 | 🆕 Verify & integrate |
| MCR 3.207 | 1302 | 🆕 Verify & integrate |
| MCR 3.207(B) | 933 | 🆕 Verify & integrate |
| MCR 2.003(C)(1) | 882 | 🆕 Verify & integrate |
| MCR 2.105 | 871 | 🆕 Verify & integrate |
| MCR 2.313 | 868 | 🆕 Verify & integrate |
| MCR 3.203 | 850 | 🆕 Verify & integrate |
| MCR 1.109 | 795 | 🆕 Verify & integrate |

### FTS5 Query Templates
```sql
-- Search evidence for this skill's domain
SELECT * FROM pages_fts WHERE pages_fts MATCH 'custody AND best AND interest';
SELECT * FROM evidence_quotes WHERE legal_significance LIKE '%722.23%';
SELECT * FROM pages_fts WHERE pages_fts MATCH 'habitability OR housing OR landlord';
SELECT * FROM pages_fts WHERE pages_fts MATCH 'protection AND order';
SELECT * FROM pages_fts WHERE pages_fts MATCH 'judicial AND misconduct OR bias';
```

## 🔗 Pass 2: Cross-Skill Integration Matrix
*Enhanced: 2026-03-12 | 71 skills in fleet*

### Direct Integration Points
| Skill | Relationship | Data Flow |
|-------|-------------|-----------|
| `litigation-analysis-engine` | Integration | Bidirectional data exchange |
| `litigation-authority-validator` | Integration | Receives citations → validates authority chains |
| `litigation-filing-architect` | Integration | Provides readiness scores → filing decisions |
| `litigation-red-team` | Integration | Receives outputs → adversarial stress testing |

### Cross-Lane Evidence Routing
| Source Lane | Target Lane | Connection Pattern |
|-----------|------------|-------------------|
| A (Custody (Pigors v Watson)) | F | Trial errors → appellate issues |
| A (Custody (Pigors v Watson)) | E | Biased rulings → JTC complaint evidence |
| B (Housing (Shady Oaks)) | A | Unsafe housing → best-interest factor (d) |
| D (PPO (Protection Orders)) | A | PPO proceedings → false allegation pattern (factor j) |
| D (PPO (Protection Orders)) | E | Improper PPO issuance → judicial bias pattern |
| A (Custody (Pigors v Watson)) | C | Due process violations → §1983 claims |
| E (Judicial Misconduct (JTC)) | F | Misconduct findings → appellate arguments |

### OMEGA Pipeline Phase Mapping
```
This skill operates across these pipeline phases:
  Ω-5 Claim Mapping → Ω-8 Authority Matching → Ω-12 Filing Readiness
```

## ⚡ Pass 3: Elite Combat Refinement
*Enhanced: 2026-03-12 | EGCP-scored | Adversarial-hardened*

### EGCP Filing Thresholds
| Filing Type | Min EGCP | Lane | Authority |
|------------|--------:|------|-----------|
| Custody Modification | 65/100 | A,B,C,D,E | Verified |
| Emergency Custody | 55/100 | A,B,C,D,E | Verified |
| PPO Modification/Termination | 60/100 | A,B,C,D,E | Verified |
| Summary Disposition (C10) | 75/100 | A,B,C,D,E | Verified |
| Summary Disposition (C8) | 70/100 | A,B,C,D,E | Verified |
| Contempt | 70/100 | A,B,C,D,E | Verified |
| Judicial Disqualification | 75/100 | A,B,C,D,E | Verified |
| Default Judgment | 60/100 | A,B,C,D,E | Verified |
| TRO Application | 60/100 | A,B,C,D,E | Verified |
| Federal §1983 Complaint | 70/100 | A,B,C,D,E | Verified |
| JTC Formal Complaint | 75/100 | A,B,C,D,E | Verified |

### Adversarial Defense Matrix
| Attack Vector | Defense | Skill Response |
|-------------|---------|---------------|
| Opposing motion to strike evidence | Pre-authenticate under MRE 901-903 | Run litigation-evidence-authentication |
| Challenge to standing | Verify party status and injury-in-fact | Document concrete harm with citations |
| Laches/statute of limitations | Verify timeliness under MCL/MCR | Check deadline_sentinel calculations |
| Hearsay objection | Map to MRE 801-807 exceptions | Pre-classify all evidence by exception |
| Judicial discretion argument | Identify abuse-of-discretion factors | Score against published standards |
| Mootness challenge | Show continuing controversy or capable-of-repetition | Document ongoing harm pattern |

### Quality Gates (Pre-Output Checklist)
```
□ All citations verified against authority_chains table
□ No hallucinated case names or statute numbers
□ Cross-lane contamination check passed (MEEK signal verified)
□ EGCP score meets filing threshold for target vehicle
□ Pinpoint citations include page + paragraph references
□ Opposing argument anticipated and addressed
□ Party names verified: Andrew J. Pigors, Emily A. Watson, L.D.W.
□ Judge name verified: Hon. Jenny L. McNeill (NOT McNeil)
□ Case numbers verified with leading zeros: 2024-001507-DC
□ No fabricated evidence (CPS = 1 call, NOT 9 investigations)
```

### Case-Specific Intelligence

**Lane A: Custody (Pigors v Watson)**
- Case: 2024-001507-DC
- Court: 14th Circuit, Muskegon County
- Judge: Hon. Jenny L. McNeill
- Key Statutes: MCL 722.23, MCL 722.27, MCL 722.28
- Key Rules: MCR 3.206-3.215
- Critical Evidence: 329+ days separation, 44% ex parte rate, Factor (j) alienation

**Lane B: Housing (Shady Oaks)**
- Case: 2025-002760-CZ
- Court: 14th Circuit, Muskegon County
- Judge: TBD
- Key Statutes: MCL 554.139, MCL 125.534-540, MCL 600.2918
- Key Rules: MCR 2.116, MCR 2.603
- Critical Evidence: 6GB evidence, HOA complaints, LARA registrations, FOIA personnel

**Lane C: Federal Civil Rights (§1983)**
- Case: USDC filing pending
- Court: U.S. District Court, W.D. Michigan
- Judge: TBD
- Key Statutes: 42 USC § 1983, 42 USC § 1985, 42 USC § 1988
- Key Rules: FRCP 8, FRCP 12, FRCP 56
- Critical Evidence: Color of law violations, Monell policy, pattern evidence across lanes

**Lane D: PPO (Protection Orders)**
- Case: 2023-5907-PP
- Court: 14th Circuit
- Judge: Hon. Jenny L. McNeill
- Key Statutes: MCL 600.2950, MCL 750.411h
- Key Rules: MCR 3.705-3.708
- Critical Evidence: False PPO allegations pattern, zero CPS findings after 1 investigation

**Lane E: Judicial Misconduct (JTC)**
- Case: JTC Complaint - McNeill
- Court: Judicial Tenure Commission
- Judge: Target: Hon. Jenny L. McNeill
- Key Statutes: Const 1963 art 6 § 30, MCR 9.104-9.205
- Key Rules: MCR 2.003, Code of Judicial Conduct
- Critical Evidence: 1,127 violations, 44% ex parte rate, muting father 7x in hearing

### Self-Evolution Protocol
```
After each use of this skill:
1. Log output quality score (1-10) to session SQL
2. Record any missing citations or evidence gaps discovered
3. Update lane-specific intelligence if new orders/events occurred
4. Cross-reference findings with contradiction_map for consistency
5. Feed results to litigation-red-team for adversarial validation
```
