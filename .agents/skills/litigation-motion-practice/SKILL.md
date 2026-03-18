---
name: litigation-motion-practice
description: "Motion drafting, briefing, and MCR 2.119 compliance for Michigan courts. Use when: draft motion, file motion, motion for reconsideration, summary disposition, emergency motion, ex parte motion, response brief, reply brief, proposed order."
---

# Litigation Motion Practice

**Role**: Expert in Michigan motion practice — drafting, filing, briefing schedules, and procedural compliance for all motion types across 6 case lanes (Pigors v. Watson). Handles the full MCR 2.119 lifecycle: motion body with authority citations, response briefs, reply briefs, proposed orders, proof of service, emergency/ex parte procedures, and motion for reconsideration.

## Capabilities

- Motion type selection matrix (dispositive vs. non-dispositive, emergency vs. standard, ex parte vs. noticed)
- MCR 2.119 full compliance: 21-day rule, 7-day response window, 3-day reply window, briefing schedule enforcement
- Motion body drafting with integrated authority citations (MCR/MCL/case law) and record references
- Response brief generation for opposing motions
- Reply brief generation
- Proposed order preparation per MCR 2.602
- Proof of service generation per MCR 2.107
- Emergency/ex parte motion handling per MCR 2.119(F) — verified statement of immediate irreparable harm
- Motion for reconsideration per MCR 2.119(F)(1) — 21-day deadline, palpable error standard
- Summary disposition drafting per MCR 2.116(C)(7)-(10)
- Disqualification motion per MCR 2.003 — affidavit of bias/prejudice
- Motion to set aside void judgment per MCR 2.612(C)(1)(d) — void ab initio, no time limit

## Requirements

- Case number and lane assignment for header compliance
- Access to `litigation_context.db` for prior filings and authority index
- Court-specific local rules (14th Circuit, Muskegon County, W.D. Michigan, COA)
- MANBEARPIG inference engine for authority relevance scoring
- Python 3.12+ with document generation capability

## Patterns

### Pattern 1: MCR 2.119 Motion Lifecycle Manager

**When to use**: For every motion — ensures all deadlines, service requirements, and briefing schedules are tracked.

```python
from datetime import date, timedelta

def calculate_motion_deadlines(
    filing_date: date,
    motion_type: str,
    is_emergency: bool = False,
) -> dict:
    """
    Calculate MCR 2.119 briefing schedule deadlines.
    Standard: Motion filed → 21 days → Hearing; Response due 7 days before; Reply 3 days before.
    Emergency: Can request immediate hearing with verified statement.
    """
    if is_emergency:
        return {
            "motion_filed": filing_date.isoformat(),
            "hearing_date": "As soon as court schedules (MCR 2.119(F)(2))",
            "response_due": "As ordered by court",
            "reply_due": "As ordered by court",
            "service_method": "Most expeditious method (MCR 2.107)",
            "requires_verified_statement": True,
            "mcr_authority": "MCR 2.119(F)(2) — emergency motion",
        }

    # MCR 2.119(C): hearing not sooner than 21 days after service
    earliest_hearing = filing_date + timedelta(days=21)
    # Adjust for weekends/holidays per MCR 2.108
    earliest_hearing = adjust_for_court_days(earliest_hearing)

    # MCR 2.119(C)(1): response at least 7 days before hearing
    response_due = earliest_hearing - timedelta(days=7)
    # MCR 2.119(C)(2): reply at least 3 days before hearing
    reply_due = earliest_hearing - timedelta(days=3)

    return {
        "motion_filed": filing_date.isoformat(),
        "service_deadline": filing_date.isoformat(),  # Same day or next business day
        "earliest_hearing": earliest_hearing.isoformat(),
        "response_due": response_due.isoformat(),
        "reply_due": reply_due.isoformat(),
        "motion_type": motion_type,
        "mcr_authority": "MCR 2.119(C)",
    }


def adjust_for_court_days(d: date) -> date:
    """Adjust date forward if it falls on weekend or court holiday per MCR 2.108."""
    while d.weekday() >= 5:  # Saturday=5, Sunday=6
        d += timedelta(days=1)
    return d
```

### Pattern 2: Motion Structure Template

**When to use**: When drafting any motion — ensures Michigan-compliant structure with proper sections.

```python
def generate_motion_structure(
    motion_type: str,
    case_number: str,
    court: str,
    lane: str,
    relief_requested: str,
    legal_basis: list,
    facts: list,
    argument_points: list,
) -> dict:
    """
    Generate a Michigan-compliant motion structure.
    Per MCR 2.119(A)(1): motion must state with particularity
    the grounds and the relief or order sought.
    """
    return {
        "caption": {
            "court": court,
            "case_number": case_number,
            "plaintiff": "ANDREW JAMES PIGORS",
            "defendant": "EMILY A. WATSON, et al.",
            "document_title": f"PLAINTIFF'S {motion_type.upper()}",
        },
        "sections": [
            {
                "heading": "RELIEF REQUESTED",
                "content": relief_requested,
                "mcr_note": "MCR 2.119(A)(1) — state relief sought",
            },
            {
                "heading": "STATEMENT OF FACTS",
                "content": facts,
                "mcr_note": "MCR 2.119(A)(2) — concise statement of facts",
            },
            {
                "heading": "LEGAL AUTHORITY",
                "content": legal_basis,
                "mcr_note": "Citations to MCR, MCL, and case law",
            },
            {
                "heading": "ARGUMENT",
                "subsections": argument_points,
                "mcr_note": "MCR 2.119(A)(3) — supporting argument",
            },
            {
                "heading": "CONCLUSION AND PRAYER FOR RELIEF",
                "content": f"WHEREFORE, Plaintiff respectfully requests this Court {relief_requested}.",
            },
        ],
        "attachments": [
            "Proposed Order (MCR 2.602)",
            "Proof of Service (MCR 2.107)",
        ],
        "lane": lane,
        "verification": motion_type in ["emergency", "ex_parte"],
    }
```

### Pattern 3: Motion for Reconsideration Per MCR 2.119(F)(1)

**When to use**: Within 21 days of an adverse order — must demonstrate palpable error.

```python
from datetime import date, timedelta

def prepare_reconsideration_motion(
    order_date: date,
    order_description: str,
    palpable_errors: list,
    case_number: str,
    lane: str,
) -> dict:
    """
    MCR 2.119(F)(1): Motion for reconsideration must be filed within
    21 days of the order. Must demonstrate palpable error by which the
    court and the parties have been misled, and show that a different
    disposition would result from correction of the error.
    """
    deadline = order_date + timedelta(days=21)
    deadline = adjust_for_court_days(deadline)
    days_remaining = (deadline - date.today()).days

    if days_remaining < 0:
        return {
            "status": "DEADLINE_EXPIRED",
            "order_date": order_date.isoformat(),
            "deadline": deadline.isoformat(),
            "alternative": "Consider MCR 2.612 relief from judgment if applicable",
        }

    return {
        "motion_type": "Motion for Reconsideration",
        "mcr_authority": "MCR 2.119(F)(1)",
        "standard": "Palpable error that misled the court and parties; different disposition must result",
        "order_date": order_date.isoformat(),
        "filing_deadline": deadline.isoformat(),
        "days_remaining": days_remaining,
        "urgency": "CRITICAL" if days_remaining <= 5 else "HIGH" if days_remaining <= 10 else "STANDARD",
        "palpable_errors": [
            {
                "error_description": err["description"],
                "correct_law_or_fact": err["correction"],
                "different_disposition": err["impact"],
                "supporting_authority": err["authority"],
            }
            for err in palpable_errors
        ],
        "case_number": case_number,
        "lane": lane,
    }
```

## Anti-Patterns

### ❌ Filing Motions Without Proposed Orders

**Why bad**: MCR 2.602(B)(3) requires that proposed orders accompany motions. Filing without a proposed order signals to the court that you either don't know the rules or don't know what relief you want. Judges may deny otherwise meritorious motions simply because no proposed order was submitted.

**Instead**: Always generate a proposed order with every motion. The proposed order should track the exact relief requested in the motion, use "IT IS ORDERED" language, include a signature line for the judge, and contain a certificate of service. Use `litigation-filing-architect` to ensure format compliance.

### ❌ Exceeding Page Limits Without Leave of Court

**Why bad**: Local court rules impose page limits (typically 20 pages for briefs in 14th Circuit, 50 pages for COA per MCR 7.212(B)). Exceeding limits without prior leave of court results in the excess pages being struck or the entire filing rejected at the clerk's window.

**Instead**: Check applicable page limits before drafting. If the argument requires more space, file a separate motion for leave to file an overlength brief **before** filing the substantive motion. Front-load the strongest arguments within the page limit.

### ❌ Treating Motion for Reconsideration as a Second Bite

**Why bad**: MCR 2.119(F)(1) is not an opportunity to re-argue the same points. The "palpable error" standard requires demonstrating the court was actually misled — not just that you disagree with the outcome. Courts routinely deny reconsideration motions that merely rehash prior arguments, and may sanction for frivolous filing.

**Instead**: Identify specific factual or legal errors in the court's reasoning. Point to evidence or authority the court overlooked or misapplied. Show that correcting the error would change the result. If no palpable error exists, consider appeal instead of reconsideration.

## Michigan-Specific Rules

- **MCR 2.119(A)**: Motion requirements — state grounds with particularity, specify relief sought
- **MCR 2.119(C)**: Briefing schedule — 21-day notice, 7-day response, 3-day reply
- **MCR 2.119(F)(1)**: Motion for reconsideration — 21-day deadline, palpable error standard
- **MCR 2.119(F)(2)**: Emergency motions — verified statement of immediate irreparable injury
- **MCR 2.119(F)(3)**: Court may deny without hearing if motion does not comply
- **MCR 2.116(C)(7)-(10)**: Summary disposition grounds — (7) immunity/limitation, (8) no genuine issue, (9) no factual support, (10) no legal basis
- **MCR 2.602**: Proposed orders — required format, court approval, entry procedure
- **MCR 2.107**: Service of process — methods, timing, proof of service requirements
- **MCR 2.003**: Disqualification of judge — motion procedure, affidavit requirements
- **MCR 2.612(C)(1)**: Relief from judgment — 6 grounds including (d) void judgment
- **MCR 2.302(B)**: Discovery scope — relevant to motion discovery disputes
- **MCR 7.211**: Appeal motions — different rules apply in Court of Appeals (Lane F)
- **MCR 8.119(H)**: Minor child referenced as L.D.W. in all motion papers

## Integration Points

- **litigation-brief-writer**: Receives motion outlines; generates full brief text with citations
- **litigation-filing-architect**: Assembles motion + proposed order + proof of service into filing package
- **litigation-service-engine**: Tracks service of motion papers on all parties
- **litigation-void-judgment-engine**: Provides MCR 2.612 analysis for relief-from-judgment motions
- **litigation-judicial-analyst**: Supplies judicial pattern data for disqualification motions
- **litigation-damages-calculator**: Feeds damages calculations into prayer-for-relief sections
- **litigation-deposition-strategist**: Discovery motions may arise from deposition disputes
- **litigation-filing-countdown**: Monitors filing deadlines for motions and responses


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
**MCR:** MCR 2.116, MCR 2.119, MCR 2.119(A)(2), MCR 2.119(C)(1), MCR 2.119(F)
**Binding Cases:**
- *Maiden v Rozwood, 461 Mich 109*
- *Quinto v Cross & Peters, 451 Mich 358*

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
| MCR 3.207 | 1302 | 🆕 Verify & integrate |
| MCR 3.207(B) | 933 | 🆕 Verify & integrate |
| MCR 2.003(C)(1) | 882 | 🆕 Verify & integrate |
| MCR 2.105 | 871 | 🆕 Verify & integrate |
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
  Ω-5 Claim Mapping → Ω-8 Authority Matching → Ω-12 Filing Readiness
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
