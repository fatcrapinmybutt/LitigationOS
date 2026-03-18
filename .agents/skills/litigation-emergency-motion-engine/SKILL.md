---
name: litigation-emergency-motion-engine
description: >-
  Emergency and ex parte motion specialist for Michigan family law litigation.
  Drafts emergency motions, TROs, ex parte custody motions, PPO modifications,
  and expedited hearing requests with same-day filing preparation.
  Use when: emergency motion, ex parte, TRO, temporary restraining order, emergency custody,
  PPO modification, expedited hearing, same-day filing, irreparable harm, imminent danger,
  MCR 2.119(F), MCR 3.207, MCR 3.310, MCL 600.2950, show cause, emergency relief.
metadata:
  category: discipline
  author: andrew-pigors
  version: "1.0.0"
  triggers: emergency motion, ex parte, TRO, emergency custody, PPO, expedited hearing
---

# LITIGATION-EMERGENCY-MOTION-ENGINE

## Metadata
- **name**: litigation-emergency-motion-engine
- **category**: discipline
- **tier**: 1 (high priority — time-sensitive filings)
- **version**: 1.0.0
- **context**: Pigors v Watson, 14th Judicial Circuit, Muskegon County, MI (Pro Se)
- **depends-on**: litigation-filing-architect, litigation-evidence-harvester, litigation-ppo-specialist

## Description

Emergency and ex parte motion specialist for time-critical Michigan family law filings.
Handles emergency motions under MCR 2.119(F) requiring demonstration of irreparable harm,
ex parte custody motions under MCR 3.207(A), temporary restraining orders under MCR 3.310,
PPO emergency modifications under MCL 600.2950, and expedited hearing requests. Generates
same-day filing packages with verified statements of facts, supporting affidavits, proposed
orders, and good faith certifications. Tracks 14-day followup hearing requirements for
ex parte orders under MCR 3.207(B).

**Party context:**
- Plaintiff: Andrew James Pigors (Pro Se), 1977 Whitehall Road, Lot 17, North Muskegon MI 49445
- Defendant: Emily A. Watson (NOT "Emily Ann")
- Child: L.D.W. per MCR 8.119(H) — MALE
- Judge: Hon. Jenny L. McNeill — 14th Circuit Court

## Capabilities

1. **Emergency Motion Drafting** — MCR 2.119(F) with irreparable harm showing
2. **Ex Parte Motion Requirements** — Verified statement, notice certification
3. **TRO Preparation** — MCR 3.310 temporary restraining order
4. **Emergency Custody Motion** — MCR 3.207(A) immediate custody modification
5. **PPO Emergency Modification** — MCL 600.2950 protection order changes
6. **Expedited Hearing Request** — Shortened time for hearing on emergency matters
7. **Same-Day Filing Preparation** — Complete package for immediate court submission
8. **14-Day Followup Scheduling** — MCR 3.207(B) mandatory hearing tracking
9. **Good Faith Certification** — MCR 2.119(F)(1) required certification
10. **Irreparable Harm Showing** — Structured demonstration of imminent, irreparable injury

## Requirements

- Emergency motions MUST demonstrate irreparable injury — speculation is insufficient
- Ex parte motions MUST include verified statement of facts (sworn, signed, notarized)
- MCR 2.119(F): good faith certification that movant attempted notice to opposing party
- If notice was not given, MUST explain why notice was impracticable
- MCR 3.207(B): hearing within 14 days of ex parte order — TRACK THIS DEADLINE
- PPO petitions: separate from regular motions — use SCAO form CC 375 (PPO domestic)
- All emergency filings must include proposed order for immediate judicial signature
- TRO bond may be required per MCR 3.310 — calculate and address in motion
- Lane routing: custody emergency → Lane A, PPO → Lane D, housing emergency → Lane B

## Patterns

### Pattern 1: Emergency Motion with Irreparable Harm Showing

```python
from legal_ai.engines import EmergencyMotionEngine
from legal_ai.models import EmergencyMotion, IrreparableHarmShowing

def draft_emergency_motion(
    case_lane: str,
    emergency_type: str,
    facts: list[str],
    evidence_exhibits: list[str],
    relief_requested: list[str],
) -> EmergencyMotion:
    """Draft MCR 2.119(F) emergency motion with irreparable harm."""
    engine = EmergencyMotionEngine()

    # Build irreparable harm showing — required for emergency relief
    harm_showing = IrreparableHarmShowing(
        nature_of_harm=engine.categorize_harm(facts),
        imminence="immediate — delay will cause harm before regular hearing",
        irreparability="monetary damages cannot compensate for harm to child",
        factual_basis=facts,
        supporting_evidence=evidence_exhibits,
        # Standard: actual, imminent, irreparable injury
        legal_standard=(
            "MCR 2.119(F)(1): Emergency motion is warranted where "
            "irreparable injury will result from waiting for a regularly "
            "scheduled motion hearing."
        ),
    )

    motion = EmergencyMotion(
        case_number=engine.get_case_number(case_lane),
        court="14th Circuit Court, Muskegon County",
        judge="Hon. Jenny L. McNeill",
        movant="Andrew James Pigors",
        respondent="Emily A. Watson",
        motion_type=emergency_type,
        harm_showing=harm_showing,
        relief_requested=relief_requested,
        # MCR 2.119(F)(1): good faith certification
        good_faith_cert=engine.generate_good_faith_cert(
            notice_given=True,
            notice_method="text message and email",
            notice_date=engine.today(),
            notice_details="Notified opposing party of intent to file emergency motion",
        ),
        # MCR 2.119(F): proposed order for immediate signature
        proposed_order=engine.draft_proposed_order(relief_requested),
        # Supporting affidavit with sworn facts
        affidavit=engine.draft_verified_statement(facts, evidence_exhibits),
    )

    engine.validate_emergency_motion(motion)
    return motion
```

### Pattern 2: Ex Parte Custody Motion (MCR 3.207)

```python
from legal_ai.engines import EmergencyMotionEngine
from legal_ai.models import ExParteCustodyMotion

def draft_ex_parte_custody_motion(
    danger_to_child: list[str],
    evidence_of_danger: list[str],
    custody_change_requested: str,
) -> ExParteCustodyMotion:
    """MCR 3.207(A) / MCR 3.206(D) ex parte custody modification."""
    engine = EmergencyMotionEngine()

    motion = ExParteCustodyMotion(
        case_number="2024-001507-DC",
        case_lane="A",
        court="14th Circuit Court, Muskegon County",
        judge="Hon. Jenny L. McNeill",
        movant="Andrew James Pigors",
        respondent="Emily A. Watson",
        child="L.D.W.",
        # MCR 3.207(A): must show child will be exposed to potential harm
        danger_showing={
            "facts": danger_to_child,
            "evidence": evidence_of_danger,
            "standard": (
                "MCR 3.207(A): Ex parte order may be entered without "
                "notice when the child's health, safety, or welfare may "
                "be endangered by delay in granting relief."
            ),
        },
        custody_change=custody_change_requested,
        # Verified statement — MUST be sworn
        verified_statement=engine.draft_verified_statement(
            facts=danger_to_child,
            exhibits=evidence_of_danger,
            sworn=True,
        ),
        proposed_order=engine.draft_proposed_order(
            [custody_change_requested],
            # MCR 3.207(B): order must set hearing within 14 days
            include_hearing_date=True,
            hearing_within_days=14,
        ),
    )

    # Schedule followup hearing tracker
    engine.schedule_followup_hearing(
        case_number="2024-001507-DC",
        deadline_days=14,
        rule="MCR 3.207(B)",
        description="Hearing on ex parte custody order — MANDATORY within 14 days",
    )

    return motion
```

### Pattern 3: PPO Emergency Modification

```python
from legal_ai.engines import EmergencyMotionEngine

def file_ppo_modification(
    ppo_case_number: str,
    modification_type: str,
    grounds: list[str],
    evidence: list[str],
) -> dict:
    """MCL 600.2950 Personal Protection Order modification."""
    engine = EmergencyMotionEngine()

    modification = engine.draft_ppo_motion(
        case_number=ppo_case_number,
        case_lane="D",
        court="14th Circuit Court, Muskegon County",
        petitioner="Andrew James Pigors",
        respondent="Emily A. Watson",
        modification_type=modification_type,  # "extend", "modify", "terminate"
        grounds=grounds,
        evidence=evidence,
        # MCL 600.2950(1): required showing
        required_showing={
            "domestic_relationship": True,
            "specific_conduct": grounds,
            "reasonable_apprehension": modification_type != "terminate",
        },
        # Use SCAO form CC 375 (domestic) or CC 376 (non-domestic)
        scao_form="CC 375",
    )

    return {
        "motion": modification,
        "scao_form": "CC 375",
        "filing_instructions": [
            "Complete SCAO form CC 375",
            "Attach supporting affidavit",
            "File with clerk — no filing fee for PPO petitions",
            "Request immediate hearing if emergency",
        ],
    }
```

### Pattern 4: TRO with Bond Calculation

```python
from legal_ai.engines import EmergencyMotionEngine

def prepare_tro_application(
    facts_supporting_tro: list[str],
    specific_conduct_to_restrain: list[str],
    evidence: list[str],
    estimated_harm_value: float,
) -> dict:
    """MCR 3.310 Temporary Restraining Order application."""
    engine = EmergencyMotionEngine()

    tro = engine.draft_tro_application(
        case_number="2024-001507-DC",
        court="14th Circuit Court, Muskegon County",
        movant="Andrew James Pigors",
        respondent="Emily A. Watson",
        conduct_to_restrain=specific_conduct_to_restrain,
        factual_basis=facts_supporting_tro,
        evidence=evidence,
        # MCR 3.310(A): required elements
        required_elements={
            "irreparable_injury": True,
            "injury_immediate": True,
            "no_adequate_legal_remedy": True,
        },
        # MCR 3.310(B): TRO expires in 14 days unless extended
        expiration_days=14,
    )

    # MCR 3.310(C): bond may be required
    bond_analysis = engine.calculate_tro_bond(
        estimated_harm=estimated_harm_value,
        # Pro Se: may request waiver of bond for indigency
        request_waiver=True,
        waiver_basis="Plaintiff proceeds in forma pauperis",
    )

    return {
        "tro_application": tro,
        "bond_analysis": bond_analysis,
        "proposed_tro_order": engine.draft_proposed_order(
            specific_conduct_to_restrain,
            order_type="TRO",
            expiration_days=14,
        ),
        "hearing_on_preliminary_injunction": "Must be scheduled within 14 days",
    }
```

## Anti-Patterns

### Anti-Pattern 1: Emergency Motion Without Actual Emergency
```python
# WRONG — Using emergency procedure for non-urgent matters
draft_emergency_motion(
    emergency_type="discovery dispute",
    facts=["Defendant has not responded to interrogatories in 30 days"],
)
# Court will deny and may sanction for abuse of emergency procedure

# CORRECT — Reserve emergency motions for actual imminent harm
draft_emergency_motion(
    emergency_type="child_safety",
    facts=["Child reported physical abuse today", "Visible injuries documented"],
)
```

### Anti-Pattern 2: Ex Parte Without Notice Certification
```python
# WRONG — Filing ex parte without explaining lack of notice
motion = ExParteCustodyMotion(good_faith_cert=None)
# Court will likely reject without notice certification

# CORRECT — MCR 2.119(F)(1): certify notice attempt or explain why impracticable
motion = ExParteCustodyMotion(
    good_faith_cert=GoodFaithCert(
        notice_attempted=True,
        method="phone, text, email",
        result="No response received within 2 hours",
    )
)
```

### Anti-Pattern 3: Missing 14-Day Followup Hearing
```python
# WRONG — Obtaining ex parte order and not scheduling followup
ex_parte_order = file_ex_parte_motion(...)
# Danger: order expires or is vacated for failure to schedule hearing

# CORRECT — MCR 3.207(B): hearing MUST occur within 14 days
ex_parte_order = file_ex_parte_motion(...)
schedule_followup_hearing(
    deadline_days=14,
    rule="MCR 3.207(B)",
    calendar_alert=True,
)
```

### Anti-Pattern 4: Unsworn Emergency Statement
```python
# WRONG — Unverified statement of facts
statement = "I believe the child is in danger..."  # not sworn

# CORRECT — Verified (sworn) statement required for ex parte relief
statement = engine.draft_verified_statement(
    facts=danger_facts,
    sworn=True,  # includes oath/affirmation language
    notarized=True,
    jurat="Subscribed and sworn before me this ___ day of ___",
)
```

## Michigan-Specific Rules

| Rule | Subject | Key Requirement |
|------|---------|-----------------|
| **MCR 2.119(F)** | Emergency motions | Good faith notice cert; irreparable harm showing |
| **MCR 3.207** | Ex parte domestic orders | Verified statement; hearing within 14 days |
| **MCR 3.207(A)** | Ex parte custody | Child endangered by delay; sworn facts required |
| **MCR 3.207(B)** | Followup hearing | MANDATORY hearing within 14 days of ex parte order |
| **MCR 3.310** | TRO | Irreparable injury; expires 14 days; bond may be required |
| **MCL 600.2950** | PPO (domestic) | Specific conduct; reasonable apprehension; no filing fee |
| **MCR 3.206(D)** | Ex parte relief scope | Limited to custody, parenting time, support emergencies |
| **MCR 2.119(F)(1)** | Good faith certification | Must certify attempt to give notice or explain why not |

### Emergency Filing Checklist
| Item | Required | Rule |
|------|----------|------|
| Verified statement of facts | YES | MCR 3.207(A) |
| Good faith notice certification | YES | MCR 2.119(F)(1) |
| Supporting affidavit | YES | MCR 2.119 |
| Evidence exhibits | RECOMMENDED | — |
| Proposed order | YES | MCR 2.119(A)(2) |
| Proof of service (if notice given) | IF APPLICABLE | MCR 2.107 |
| Bond (TRO only) | MAY BE REQUIRED | MCR 3.310(C) |

### Time-Critical Deadlines
| Event | Deadline | Authority |
|-------|----------|-----------|
| Followup hearing after ex parte | 14 days | MCR 3.207(B) |
| TRO expiration | 14 days (unless extended) | MCR 3.310(B) |
| PPO hearing after objection | 14 days | MCL 600.2950(12) |
| Preliminary injunction hearing | Prompt — typically 14 days | MCR 3.310 |

## Integration Points

- **litigation-filing-architect**: Same-day filing format and e-filing preparation
- **litigation-evidence-harvester**: Emergency evidence collection and exhibit preparation
- **litigation-ppo-specialist**: PPO-specific expertise and SCAO form generation
- **litigation-custody-specialist**: Best-interest factors for custody emergencies
- **litigation-court-order-tracker**: Tracks ex parte orders and 14-day hearing deadlines
- **litigation-service-engine**: Emergency service and notice documentation
- **litigation-pro-se-guardian**: Pro Se compliance for emergency procedures
- **litigation-timeline-forensics**: Documents emergency events in case timeline


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
**MCR:** MCR 3.207(A), MCR 3.207(B), MCR 2.119(F), MCR 3.310
**MCL:** MCL 722.27(1)(c), MCL 600.2950
**Binding Cases:**
- *Brausch v Brausch, 283 Mich App 339*
- *Thompson v Thompson, 261 Mich App 353*

### Case Lane Intelligence
| Lane | Files Indexed | Case | Court |
|------|-------------:|------|-------|
| A | 3,502 | 2024-001507-DC | 14th Circuit, Muskegon County |
| B | 3,531 | 2025-002760-CZ | 14th Circuit, Muskegon County |
| D | 6,462 | 2023-5907-PP | 14th Circuit |
| E | 9,945 | JTC Complaint - McNeill | Judicial Tenure Commission |

### Harvest-Discovered Citations (New)
| MCR Citation | Files Found | Status |
|-------------|----------:|--------|
| MCR 2.003 | 1980 | 🆕 Verify & integrate |
| MCR 2.003(C)(1) | 882 | 🆕 Verify & integrate |
| MCR 2.105 | 871 | 🆕 Verify & integrate |
| MCR 2.313 | 868 | 🆕 Verify & integrate |
| MCR 3.203 | 850 | 🆕 Verify & integrate |
| MCR 1.109 | 795 | 🆕 Verify & integrate |
| MCR 3.606 | 766 | 🆕 Verify & integrate |
| MCR 3.210 | 761 | 🆕 Verify & integrate |
| MCR 2.113 | 756 | 🆕 Verify & integrate |
| MCR 2.302 | 698 | 🆕 Verify & integrate |

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
  Ω-3 Evidence Harvest → Ω-5 Claim Mapping → Ω-6 Contradiction Detection
  Ω-9 Gap Analysis → Ω-11 Risk Assessment → Ω-12 Filing Readiness
```

## ⚡ Pass 3: Elite Combat Refinement
*Enhanced: 2026-03-12 | EGCP-scored | Adversarial-hardened*

### EGCP Filing Thresholds
| Filing Type | Min EGCP | Lane | Authority |
|------------|--------:|------|-----------|
| Custody Modification | 65/100 | A,B,D,E | Verified |
| Emergency Custody | 55/100 | A,B,D,E | Verified |
| PPO Modification/Termination | 60/100 | A,B,D,E | Verified |
| Summary Disposition (C10) | 75/100 | A,B,D,E | Verified |
| Summary Disposition (C8) | 70/100 | A,B,D,E | Verified |
| Contempt | 70/100 | A,B,D,E | Verified |
| Judicial Disqualification | 75/100 | A,B,D,E | Verified |
| Default Judgment | 60/100 | A,B,D,E | Verified |
| TRO Application | 60/100 | A,B,D,E | Verified |
| JTC Formal Complaint | 75/100 | A,B,D,E | Verified |

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
