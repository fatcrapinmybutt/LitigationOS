---
name: litigation-void-judgment-engine
description: "Void judgment analysis and jurisdictional challenge specialist for Michigan courts. Use when: void judgment, MCR 2.612, jurisdictional deficiency, due process violation, void ab initio, relief from judgment, collateral attack, §1983 jurisdiction bypass."
---

# Litigation Void Judgment Engine

**Role**: Void judgment and jurisdictional challenge specialist for Michigan family law and civil rights litigation (Pigors v. Watson). Analyzes court orders and judgments for jurisdictional deficiencies, due process violations, and void ab initio doctrine applicability. Manages MCR 2.612(C)(1) relief-from-judgment motions and federal §1983 jurisdiction bypass when state courts fail to correct void orders.

## Capabilities

- MCR 2.612(C)(1) relief from judgment analysis across all 6 grounds (a-f)
- Jurisdiction deficiency identification: subject matter, personal, in rem
- Due process violation detection using Mathews v. Eldridge balancing test
- Void ab initio doctrine application — no time limit, cannot be waived, immune to res judicata
- Res judicata and collateral estoppel defense analysis (inapplicable to void judgments)
- Retroactive relief calculation (custody time lost, financial harm from void orders)
- Federal §1983 jurisdiction bypass for state court failures to correct constitutional violations
- Ex parte order challenges (MCR 3.207 emergency custody, PPO issuance without hearing)
- Void vs. voidable distinction: void = jurisdictional defect, voidable = procedural error
- Superintending control writs per MCL 600.1701 when normal appeal inadequate

## Requirements

- Access to `litigation_context.db` for order history, judicial actions, and jurisdictional records
- Complete docket sheets for each case lane showing all orders entered
- Hearing transcripts (if any) for due process analysis
- Service records to verify personal jurisdiction
- MANBEARPIG inference engine for jurisdictional deficiency scoring
- Python 3.12+

## Patterns

### Pattern 1: Void vs. Voidable Classification

**When to use**: Before filing any relief-from-judgment motion — the classification determines the legal standard, time limits, and available relief.

```python
from enum import Enum
from typing import List, Optional

class JudgmentStatus(Enum):
    VOID = "void"           # No jurisdiction → no time limit → collateral attack OK
    VOIDABLE = "voidable"   # Jurisdiction existed but procedural error → time limits apply
    VALID = "valid"         # No deficiency found

def classify_judgment(
    order_date: str,
    court: str,
    case_number: str,
    lane: str,
    jurisdictional_facts: dict,
) -> dict:
    """
    Classify a judgment as void, voidable, or valid.

    VOID if any of these exist:
    - Court lacked subject matter jurisdiction (MCL 600.605/600.611)
    - Court lacked personal jurisdiction and it was not waived
    - Judge was disqualified and continued to act (MCR 2.003)
    - Constitutional due process violated (no notice, no hearing on dispositive matter)

    VOIDABLE if:
    - Jurisdiction existed but procedural rules were violated
    - Correctable error occurred (wrong form, late filing accepted)

    Key distinction: Void judgments are nullities — they have no legal effect,
    cannot be ratified, and are subject to collateral attack at any time.
    Bowie v Arder, 441 Mich 23 (1992).
    """
    deficiencies = []

    # Check subject matter jurisdiction
    if not jurisdictional_facts.get("subject_matter_jurisdiction"):
        deficiencies.append({
            "type": "subject_matter",
            "description": "Court lacked subject matter jurisdiction",
            "authority": "MCL 600.605; MCL 600.611",
            "severity": "VOID",
            "time_limit": "None — void judgments may be attacked at any time",
        })

    # Check personal jurisdiction
    if not jurisdictional_facts.get("personal_jurisdiction_established"):
        if not jurisdictional_facts.get("personal_jurisdiction_waived"):
            deficiencies.append({
                "type": "personal",
                "description": "Court lacked personal jurisdiction (not waived)",
                "authority": "MCR 2.105; US Const. 14th Amend.",
                "severity": "VOID",
                "time_limit": "None",
            })

    # Check judicial disqualification
    if jurisdictional_facts.get("judge_disqualified") or \
       jurisdictional_facts.get("disqualification_motion_pending"):
        deficiencies.append({
            "type": "disqualification",
            "description": "Judge disqualified or disqualification motion pending — "
                           "orders entered by disqualified judge are void",
            "authority": "MCR 2.003; In re Hatcher, 443 Mich 426 (1993)",
            "severity": "VOID",
            "time_limit": "None",
        })

    # Check due process
    if jurisdictional_facts.get("no_notice_given") or \
       jurisdictional_facts.get("no_hearing_on_dispositive"):
        deficiencies.append({
            "type": "due_process",
            "description": "Due process violated — no notice and/or no hearing "
                           "before dispositive order entered",
            "authority": "US Const. 14th Amend.; Mathews v. Eldridge, 424 US 319 (1976)",
            "severity": "VOID",
            "time_limit": "None",
        })

    # Classification
    void_deficiencies = [d for d in deficiencies if d["severity"] == "VOID"]
    if void_deficiencies:
        status = JudgmentStatus.VOID
    elif deficiencies:
        status = JudgmentStatus.VOIDABLE
    else:
        status = JudgmentStatus.VALID

    return {
        "order_date": order_date,
        "court": court,
        "case_number": case_number,
        "lane": lane,
        "classification": status.value,
        "deficiencies": deficiencies,
        "relief_available": get_available_relief(status, deficiencies),
        "time_limit": "None" if status == JudgmentStatus.VOID else "MCR 2.612(C)(2) — 1 year for (a)(b)(c); reasonable time for (d)(e)(f)",
    }


def get_available_relief(status: JudgmentStatus, deficiencies: list) -> list:
    """Determine available relief mechanisms based on classification."""
    relief = []
    if status == JudgmentStatus.VOID:
        relief.extend([
            "MCR 2.612(C)(1)(d) — judgment is void (no time limit)",
            "Collateral attack in any proceeding",
            "MCL 600.1701 — superintending control (if court refuses to vacate)",
            "42 USC §1983 — federal action for deprivation of rights under color of law",
        ])
    elif status == JudgmentStatus.VOIDABLE:
        relief.extend([
            "MCR 2.612(C)(1)(a) — mistake, inadvertence (within 1 year)",
            "MCR 2.612(C)(1)(f) — any other reason justifying relief",
            "Direct appeal within time limits",
        ])
    return relief
```

### Pattern 2: Retroactive Relief Calculator

**When to use**: After establishing an order is void — calculate the harm caused during the period the void order was in effect.

```python
from datetime import date
from decimal import Decimal

def calculate_retroactive_relief(
    void_order_date: date,
    current_date: date,
    custody_time_lost_days: int,
    financial_harm: Decimal,
    lane: str,
) -> dict:
    """
    Calculate retroactive relief for time period a void order was in effect.
    Void orders are nullities — the status quo ante is restored.
    All actions taken under a void order are themselves void.
    """
    days_void_in_effect = (current_date - void_order_date).days

    return {
        "void_order_date": void_order_date.isoformat(),
        "days_in_effect": days_void_in_effect,
        "custody_time_lost_days": custody_time_lost_days,
        "custody_time_lost_description": f"L.D.W. deprived of {custody_time_lost_days} days "
                                          f"with father under void order",
        "financial_harm": float(financial_harm),
        "relief_requested": [
            f"Vacate all orders entered on or after {void_order_date.isoformat()}",
            "Restore custody status to pre-void-order arrangement",
            f"Compensatory damages for {custody_time_lost_days} days of lost parenting time",
            "Attorney fees and costs incurred challenging void order",
        ],
        "section_1983_available": True,
        "section_1983_basis": "Deprivation of parental rights (fundamental liberty interest) "
                              "under color of state law by judicial officer acting without jurisdiction",
        "lane": lane,
    }
```

### Pattern 3: MCR 2.612(C)(1) Grounds Analysis

**When to use**: When preparing a motion for relief from judgment — analyze all 6 grounds systematically.

```python
def analyze_612_grounds(order_facts: dict) -> list:
    """
    Analyze all 6 grounds under MCR 2.612(C)(1) for relief from judgment.
    Returns applicable grounds sorted by strength.
    """
    grounds = [
        {
            "subsection": "(a)",
            "ground": "Mistake, inadvertence, surprise, or excusable neglect",
            "time_limit": "Within 1 year of judgment",
            "applies": order_facts.get("mistake_or_neglect", False),
            "strength": order_facts.get("mistake_strength", 0),
        },
        {
            "subsection": "(b)",
            "ground": "Newly discovered evidence",
            "time_limit": "Within 1 year; due diligence required",
            "applies": order_facts.get("new_evidence", False),
            "strength": order_facts.get("new_evidence_strength", 0),
        },
        {
            "subsection": "(c)",
            "ground": "Fraud, misrepresentation, or other misconduct of adverse party",
            "time_limit": "Within 1 year",
            "applies": order_facts.get("fraud_or_misconduct", False),
            "strength": order_facts.get("fraud_strength", 0),
        },
        {
            "subsection": "(d)",
            "ground": "Judgment is void",
            "time_limit": "NO TIME LIMIT — void judgments are nullities",
            "applies": order_facts.get("judgment_void", False),
            "strength": 10 if order_facts.get("judgment_void") else 0,
        },
        {
            "subsection": "(e)",
            "ground": "Judgment has been satisfied, released, or discharged",
            "time_limit": "Reasonable time",
            "applies": order_facts.get("judgment_satisfied", False),
            "strength": order_facts.get("satisfaction_strength", 0),
        },
        {
            "subsection": "(f)",
            "ground": "Any other reason justifying relief",
            "time_limit": "Reasonable time",
            "applies": order_facts.get("other_reason", False),
            "strength": order_facts.get("other_reason_strength", 0),
        },
    ]
    applicable = [g for g in grounds if g["applies"]]
    return sorted(applicable, key=lambda g: g["strength"], reverse=True)
```

## Anti-Patterns

### ❌ Conflating Void and Voidable Judgments

**Why bad**: Arguing a voidable judgment is "void" destroys credibility. Void judgments arise from jurisdictional defects (no subject matter jurisdiction, no personal jurisdiction, disqualified judge). Voidable judgments arise from procedural errors within jurisdiction. The legal standards, time limits, and remedies are completely different. Courts harshly penalize conflation because it wastes judicial resources.

**Instead**: Use Pattern 1 (Void vs. Voidable Classification) rigorously. If the defect is procedural, file under MCR 2.612(C)(1)(a) (within 1 year) or appeal. If the defect is jurisdictional, file under MCR 2.612(C)(1)(d) (no time limit). Never call a voidable order "void."

### ❌ Missing the §1983 Federal Bypass When State Courts Refuse Relief

**Why bad**: If the state court refuses to vacate a void order, continuing to file motions in the same court that issued the void order is futile. State courts sometimes refuse to acknowledge their own jurisdictional failures. Exhausting state remedies without pivoting to federal court wastes time and allows ongoing harm.

**Instead**: After one good-faith attempt to vacate in state court, if denied, preserve the issue for appeal AND file a 42 USC §1983 action in federal court (W.D. Michigan). The §1983 claim targets the deprivation of constitutional rights (parental liberty interest) under color of state law. Federal courts have independent jurisdiction to declare state court orders void for constitutional violations.

### ❌ Filing MCR 2.612 Motion Without Addressing Laches

**Why bad**: Even though void judgments have no statutory time limit, Michigan courts apply the equitable doctrine of laches if you unreasonably delayed raising the challenge. Opposing counsel will argue "you knew about this defect for X months/years and did nothing."

**Instead**: Address laches preemptively in every MCR 2.612(C)(1)(d) motion. Explain when the jurisdictional defect was discovered, what diligent steps were taken since discovery, and why any delay was reasonable (e.g., pro se party, complex jurisdictional analysis, ongoing related proceedings).

## Michigan-Specific Rules

- **MCR 2.612(C)(1)(a-f)**: Six grounds for relief from judgment — (a) mistake, (b) new evidence, (c) fraud, (d) void, (e) satisfied, (f) other
- **MCR 2.612(C)(2)**: Time limits — 1 year for (a)(b)(c); reasonable time for (d)(e)(f); void has no absolute limit
- **MCR 2.003**: Disqualification of judge — orders by disqualified judge are void
- **MCL 600.605**: Circuit court general jurisdiction
- **MCL 600.611**: Subject matter jurisdiction requirements
- **MCL 600.1701**: Superintending control — extraordinary remedy when no adequate legal remedy exists
- **US Constitution 14th Amendment**: Due process — notice and opportunity to be heard before deprivation of liberty or property
- **Mathews v. Eldridge, 424 US 319 (1976)**: Three-part due process balancing test
- **Bowie v Arder, 441 Mich 23 (1992)**: Void vs. voidable distinction in Michigan
- **In re Hatcher, 443 Mich 426 (1993)**: Jurisdiction requirements and void orders
- **Al-Maliki v LaGrant**: Due process requirements in Michigan custody proceedings
- **42 USC §1983**: Federal civil rights action for deprivation of rights under color of state law
- **MCR 3.207**: Ex parte emergency custody orders — limited grounds, temporary duration
- **MCR 8.119(H)**: Minor child referenced as L.D.W. only in all filings

## Integration Points

- **litigation-judicial-analyst**: Provides judicial bias data and disqualification analysis for void judgment claims
- **litigation-appellate-strategist**: Coordinates appeal strategy when void judgment motion is denied at trial level
- **litigation-federal-civil-rights**: Receives void judgment analysis for §1983 federal bypass actions
- **litigation-motion-practice**: Generates MCR 2.612 motion papers and briefing
- **litigation-timeline-forensics**: Provides chronological order history showing jurisdictional failures
- **litigation-damages-calculator**: Feeds retroactive relief calculations into damages totals
- **litigation-filing-architect**: Assembles void judgment challenge filing packages
- **MANBEARPIG inference engine**: Scores jurisdictional deficiency strength and due process violations


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

### Governing Authority (Verified)
**MCR:** MCR 2.612(C)(1), MCR 2.612(C)(4), MCR 2.603(D)
**MCL:** MCL 600.2932, MCL 600.6304
**Binding Cases:**
- *Washington v Sinai Hosp, 478 Mich 412*
- *Ragnone v Ragnone, 359 Mich 328*

### Case Lane Intelligence
| Lane | Files Indexed | Case | Court |
|------|-------------:|------|-------|
| A | 3,502 | 2024-001507-DC | 14th Circuit, Muskegon County |
| D | 6,462 | 2023-5907-PP | 14th Circuit |
| E | 9,945 | JTC Complaint - McNeill | Judicial Tenure Commission |
| F | 975 | COA 366810 | Michigan Court of Appeals / Supreme Court |

### Harvest-Discovered Citations (New)
| MCR Citation | Files Found | Status |
|-------------|----------:|--------|
| MCR 2.119 | 1635 | 🆕 Verify & integrate |
| MCR 2.107 | 1369 | 🆕 Verify & integrate |
| MCR 3.207(B) | 933 | 🆕 Verify & integrate |
| MCR 2.003(C)(1) | 882 | 🆕 Verify & integrate |
| MCR 2.313 | 868 | 🆕 Verify & integrate |
| MCR 3.203 | 850 | 🆕 Verify & integrate |
| MCR 1.109 | 795 | 🆕 Verify & integrate |
| MCR 3.606 | 766 | 🆕 Verify & integrate |
| MCR 3.210 | 761 | 🆕 Verify & integrate |
| MCR 2.113 | 756 | 🆕 Verify & integrate |

### FTS5 Query Templates
```sql
-- Search evidence for this skill's domain
SELECT * FROM pages_fts WHERE pages_fts MATCH 'custody AND best AND interest';
SELECT * FROM evidence_quotes WHERE legal_significance LIKE '%722.23%';
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
  Ω-3 Evidence Harvest → Ω-5 Claim Mapping → Ω-6 Contradiction Detection
  Ω-9 Gap Analysis → Ω-11 Risk Assessment → Ω-12 Filing Readiness
```

## ⚡ Pass 3: Elite Combat Refinement
*Enhanced: 2026-03-12 | EGCP-scored | Adversarial-hardened*

### EGCP Filing Thresholds
| Filing Type | Min EGCP | Lane | Authority |
|------------|--------:|------|-----------|
| Custody Modification | 65/100 | A,D,E,F | Verified |
| Emergency Custody | 55/100 | A,D,E,F | Verified |
| PPO Modification/Termination | 60/100 | A,D,E,F | Verified |
| Contempt | 70/100 | A,D,E,F | Verified |
| Judicial Disqualification | 75/100 | A,D,E,F | Verified |
| Appeal Brief | 70/100 | A,D,E,F | Verified |
| Leave Application (MSC) | 80/100 | A,D,E,F | Verified |
| JTC Formal Complaint | 75/100 | A,D,E,F | Verified |

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
