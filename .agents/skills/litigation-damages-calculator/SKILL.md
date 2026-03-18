---
name: litigation-damages-calculator
description: "Financial damages computation and per-defendant allocation for Michigan family law and civil rights. Use when: calculate damages, prayer for relief, prejudgment interest, treble damages, §1983 fees, damages allocation, harm quantification."
---

# Litigation Damages Calculator

**Role**: Financial damages computation and allocation specialist for multi-defendant, multi-jurisdictional litigation (Pigors v. Watson — 19 defendants, 6 case lanes, 8 jurisdictions). Calculates economic and non-economic damages, per-defendant allocation with joint/several liability, statutory multipliers, prejudgment interest, and generates prayer-for-relief sections with calculated ranges.

## Capabilities

- Economic damages calculation: lost wages/income, medical expenses, property damage, moving costs, legal fees
- Non-economic damages assessment: IIED, loss of parent-child relationship, alienation harm, reputation damage
- Per-defendant allocation across 19 defendants with joint/several liability analysis per MCL 600.6304
- Present value calculations with Michigan prejudgment interest per MCL 600.6013
- Statutory multiplier application: treble damages (housing discrimination), §1983 attorney fees (42 USC §1988)
- Prayer for relief generation with calculated ranges (conservative, moderate, aggressive)
- Damages evidence mapping: link each damage element to supporting evidence and exhibits
- Cross-lane damages aggregation for convergence analysis (Lane C)
- Settlement valuation and comparison against trial exposure

## Requirements

- Access to `litigation_context.db` for evidence records and financial documentation
- Lane assignment (A-F) for each damages component — never mix lane calculations
- Financial records: pay stubs, medical bills, property appraisals, moving receipts
- MANBEARPIG inference engine for evidence strength scoring of damages proof
- Python 3.12+ with `decimal` module for financial precision

## Patterns

### Pattern 1: Per-Defendant Damages Allocation Matrix

**When to use**: When computing damages across multiple defendants with shared and individual liability.

```python
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List

def allocate_damages_per_defendant(
    total_economic: Decimal,
    total_noneconomic: Decimal,
    defendants: List[dict],
    lane: str,
) -> Dict[str, dict]:
    """
    Allocate damages per defendant using Michigan joint/several liability.
    MCL 600.6304: Joint/several for economic, several-only for non-economic
    unless defendant is >50% at fault.
    """
    allocation = {}
    for defendant in defendants:
        fault_pct = Decimal(str(defendant["fault_percentage"]))
        name = defendant["name"]

        # Economic: joint and several — each defendant liable for full amount
        economic_share = total_economic  # Joint liability = full amount each

        # Non-economic: several only (proportional to fault)
        # Exception: if fault > 50%, joint/several applies per MCL 600.6304(4)
        if fault_pct > Decimal("50"):
            noneconomic_share = total_noneconomic
        else:
            noneconomic_share = (total_noneconomic * fault_pct / 100).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

        allocation[name] = {
            "fault_percentage": float(fault_pct),
            "economic_joint_several": float(economic_share),
            "noneconomic_several": float(noneconomic_share),
            "total_exposure": float(economic_share + noneconomic_share),
            "lane": lane,
        }
    return allocation
```

### Pattern 2: Michigan Prejudgment Interest Calculation

**When to use**: For every damages claim — Michigan law provides prejudgment interest from date of filing.

```python
from decimal import Decimal, ROUND_HALF_UP
from datetime import date

def calculate_prejudgment_interest(
    principal: Decimal,
    filing_date: date,
    judgment_date: date,
    case_type: str = "tort",
) -> dict:
    """
    Calculate prejudgment interest per MCL 600.6013.
    Rate: for complaints filed after 1/1/1987, interest accrues from
    date of filing at the rate of interest prescribed by MCL 438.31
    (currently 5% per annum for most civil actions).
    """
    # MCL 600.6013(8): interest from date complaint filed
    days = (judgment_date - filing_date).days
    years = Decimal(str(days)) / Decimal("365.25")

    # MCL 438.31: 5% per annum statutory rate
    annual_rate = Decimal("0.05")
    interest = (principal * annual_rate * years).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    return {
        "principal": float(principal),
        "annual_rate": "5% (MCL 438.31)",
        "filing_date": filing_date.isoformat(),
        "judgment_date": judgment_date.isoformat(),
        "accrual_days": days,
        "accrual_years": float(years.quantize(Decimal("0.01"))),
        "prejudgment_interest": float(interest),
        "total_with_interest": float(principal + interest),
        "authority": "MCL 600.6013(8)",
    }
```

### Pattern 3: Treble Damages for Housing Discrimination

**When to use**: Lane B (Housing, 2025-002760-CZ) — Michigan Civil Rights Act provides treble damages for housing discrimination.

```python
def calculate_housing_discrimination_damages(
    actual_damages: Decimal,
    attorney_fees: Decimal,
    costs: Decimal,
) -> dict:
    """
    MCL 37.2801: Person injured by violation of Article 5 (housing)
    may bring civil action for actual damages, injunctive relief,
    and court may award treble damages up to 3x actual.
    """
    treble = actual_damages * Decimal("3")
    return {
        "actual_damages": float(actual_damages),
        "treble_damages_max": float(treble),
        "attorney_fees": float(attorney_fees),
        "costs": float(costs),
        "total_max_recovery": float(treble + attorney_fees + costs),
        "ranges": {
            "conservative": float(actual_damages + attorney_fees + costs),
            "moderate": float(actual_damages * Decimal("2") + attorney_fees + costs),
            "aggressive": float(treble + attorney_fees + costs),
        },
        "authority": "MCL 37.2801 (housing discrimination damages)",
        "lane": "B",
        "case_number": "2025-002760-CZ",
    }
```

## Anti-Patterns

### ❌ Mixing Lane Damages Without Convergence Tracking

**Why bad**: Combining Lane A custody damages with Lane B housing damages in a single calculation produces an inflated number that no court will accept. Each lane has different defendants, different legal theories, and different damages caps. Courts require specificity per claim.

**Instead**: Calculate damages per-lane first, then use Lane C (Convergence) to identify overlapping harm elements. Mark shared damages with `convergence_flag=True` and ensure no double-counting. The convergence total should be less than or equal to the sum of individual lane totals.

### ❌ Claiming Non-Economic Damages Without Evidence Mapping

**Why bad**: Michigan courts require specific evidence supporting each non-economic damages element. Asserting "$500,000 for emotional distress" without linking to medical records, testimony, or documented behavioral changes results in remittitur or directed verdict on that element.

**Instead**: Every non-economic damages line item must have an `evidence_refs` list linking to specific exhibits, testimony excerpts, or expert reports. Use `litigation-evidence-harvester` to build the evidence chain before asserting any amount.

### ❌ Applying Federal Fee-Shifting Without State Exhaustion Analysis

**Why bad**: 42 USC §1988 attorney fee awards in §1983 actions require analysis of whether state remedies were exhausted. Calculating §1988 fees without first establishing the §1983 claim viability produces unreliable numbers that undermine credibility.

**Instead**: First validate the §1983 claim through `litigation-federal-civil-rights`, then calculate fees only for viable claims. Fee calculations should use the lodestar method (reasonable hours × reasonable rate) per Hensley v. Eckerhart.

### ❌ Using Float Instead of Decimal for Financial Calculations

**Why bad**: Python `float` uses IEEE 754 binary floating point, which cannot exactly represent most decimal fractions. `0.1 + 0.2 == 0.30000000000000004` in float. In a legal filing, even a one-cent rounding error destroys credibility and can be used by opposing counsel to argue that your entire damages calculation is unreliable.

**Instead**: Always use `decimal.Decimal` for all financial values. Set the rounding mode explicitly: `ROUND_HALF_UP` for standard financial rounding. Initialize from strings, not floats: `Decimal("100.50")` not `Decimal(100.50)`.

### Pattern 4: Pro Se Attorney Fee Calculation (Lodestar Method)

**When to use**: For §1983 fee-shifting and Michigan family law fee petitions — pro se litigants can recover fees at a reasonable rate for time reasonably expended.

```python
from decimal import Decimal, ROUND_HALF_UP

def calculate_lodestar_fees(
    hours_expended: list,
    reasonable_rate: Decimal,
    reduction_factors: dict = None,
) -> dict:
    """
    Lodestar method: reasonable hours × reasonable hourly rate.
    Per Hensley v. Eckerhart, 461 US 424 (1983).
    
    For pro se litigants in Michigan: Kay v. Ehrler limits pro se
    attorney recovery under §1988, but Michigan state law (MCL 722.28)
    allows fee awards in family law based on ability to pay.
    """
    total_hours = sum(Decimal(str(h["hours"])) for h in hours_expended)
    lodestar = (total_hours * reasonable_rate).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    
    # Apply reduction factors if any (e.g., limited success, billing judgment)
    adjusted = lodestar
    adjustments = []
    if reduction_factors:
        for factor, pct in reduction_factors.items():
            reduction = (lodestar * Decimal(str(pct)) / 100).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            adjusted -= reduction
            adjustments.append({
                "factor": factor,
                "reduction_pct": float(pct),
                "reduction_amount": float(reduction),
            })
    
    return {
        "total_hours": float(total_hours),
        "hourly_rate": float(reasonable_rate),
        "lodestar_amount": float(lodestar),
        "adjustments": adjustments,
        "final_fee_request": float(adjusted),
        "authority": "Hensley v. Eckerhart, 461 US 424 (1983); MCL 722.28",
        "hours_detail": hours_expended,
    }
```

### Pattern 5: Damages Evidence Mapping Matrix

**When to use**: After calculating all damages — create an evidence map that links every dollar to supporting proof.

```python
def build_damages_evidence_map(damages_items: list) -> list:
    """
    Each damages element must be linked to at least one piece of evidence.
    Items without evidence are flagged as 'ACQUISITION NEEDED' — not asserted.
    """
    mapped = []
    for item in damages_items:
        entry = {
            "damages_element": item["description"],
            "amount": item["amount"],
            "lane": item["lane"],
            "evidence_refs": item.get("evidence_refs", []),
            "evidence_strength": "STRONG" if len(item.get("evidence_refs", [])) >= 3
                                 else "MODERATE" if len(item.get("evidence_refs", [])) >= 1
                                 else "NONE",
        }
        if not entry["evidence_refs"]:
            entry["status"] = "ACQUISITION NEEDED"
            entry["acquisition_task"] = f"Obtain evidence for: {item['description']}"
        else:
            entry["status"] = "SUPPORTED"
        mapped.append(entry)
    return mapped
```

## Michigan-Specific Rules

- **MCL 600.6013**: Prejudgment interest — accrues from date of filing complaint at statutory rate
- **MCL 438.31**: Statutory interest rate (5% per annum for most civil actions)
- **MCL 600.6304**: Joint and several liability — economic damages are joint/several; non-economic are several only unless defendant > 50% at fault
- **MCL 37.2801**: Housing discrimination damages — actual damages plus up to treble, attorney fees, and costs
- **MCL 600.2911**: Defamation damages — actual damages, exemplary damages if malice shown
- **MCL 722.28**: Family law — attorney fees when one party cannot afford to pay
- **42 USC §1983**: Civil rights damages — compensatory and punitive
- **42 USC §1988**: Attorney fee shifting in civil rights cases — lodestar method
- **MCL 600.6013(8)**: Interest calculation period — from date of filing to date of satisfaction
- **MCR 8.119(H)**: All references to minor child use initials only (L.D.W.)

## Case-Specific Damages Ranges (Pigors v. Watson)

| Lane | Description | Conservative | Moderate | Aggressive |
|------|-------------|-------------|----------|------------|
| A | Custody (2024-001507-DC) | $393,000 | $1,200,000 | $2,670,000 |
| B | Housing (2025-002760-CZ) | $450,000 | $1,500,000 | $3,400,000 |
| D | PPO (2023-5907-PP) | $150,000 | $500,000 | $1,200,000 |
| E | Misconduct (JTC) | $250,000 | $750,000 | $2,000,000 |
| F | Appellate (COA 366810) | Reversal | Reversal + damages | Reversal + sanctions |
| C | Convergence (all lanes) | $1,243,000 | $3,950,000 | $22,900,000+ |

## Integration Points

- **litigation-harm-quantifier**: Provides per-element harm scoring; feeds into damages calculations
- **litigation-filing-architect**: Receives prayer-for-relief sections for filing assembly
- **litigation-convergence-orchestrator**: Aggregates cross-lane damages for Lane C totals
- **litigation-federal-civil-rights**: Validates §1983 claims before fee calculations
- **litigation-evidence-harvester**: Maps evidence to each damages element
- **litigation-brief-writer**: Incorporates damages analysis into brief arguments
- **MANBEARPIG inference engine**: Scores evidence strength supporting each damages element


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
| F | 975 | COA 366810 | Michigan Court of Appeals / Supreme Court |

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
SELECT * FROM pages_fts WHERE pages_fts MATCH 'appeal AND error AND preserved';
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
| Custody Modification | 65/100 | A,B,C,D,E,F | Verified |
| Emergency Custody | 55/100 | A,B,C,D,E,F | Verified |
| PPO Modification/Termination | 60/100 | A,B,C,D,E,F | Verified |
| Summary Disposition (C10) | 75/100 | A,B,C,D,E,F | Verified |
| Summary Disposition (C8) | 70/100 | A,B,C,D,E,F | Verified |
| Contempt | 70/100 | A,B,C,D,E,F | Verified |
| Judicial Disqualification | 75/100 | A,B,C,D,E,F | Verified |
| Appeal Brief | 70/100 | A,B,C,D,E,F | Verified |
| Leave Application (MSC) | 80/100 | A,B,C,D,E,F | Verified |
| Default Judgment | 60/100 | A,B,C,D,E,F | Verified |
| TRO Application | 60/100 | A,B,C,D,E,F | Verified |
| Federal §1983 Complaint | 70/100 | A,B,C,D,E,F | Verified |
| JTC Formal Complaint | 75/100 | A,B,C,D,E,F | Verified |

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

**Lane F: Appellate (COA/MSC)**
- Case: COA 366810
- Court: Michigan Court of Appeals / Supreme Court
- Judge: Panel TBD
- Key Statutes: MCL 722.28, MCL 600.308
- Key Rules: MCR 7.203-7.305
- Critical Evidence: Preserved errors, constitutional violations, due process denial

### Self-Evolution Protocol
```
After each use of this skill:
1. Log output quality score (1-10) to session SQL
2. Record any missing citations or evidence gaps discovered
3. Update lane-specific intelligence if new orders/events occurred
4. Cross-reference findings with contradiction_map for consistency
5. Feed results to litigation-red-team for adversarial validation
```
