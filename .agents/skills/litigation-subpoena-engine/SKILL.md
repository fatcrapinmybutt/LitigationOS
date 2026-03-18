---
name: litigation-subpoena-engine
description: >-
  Subpoena generation, service tracking, and enforcement specialist for Michigan family
  law litigation. Generates MCR 2.305/2.506 compliant subpoenas, tracks service status,
  prepares motions to compel, and manages third-party record requests.
  Use when: subpoena, duces tecum, witness compel, third-party records, deposition notice,
  UIDDA, out-of-state witness, bank records, school records, CPS records, police records,
  employer records, compel production, subpoena enforcement, contempt for non-compliance.
metadata:
  category: discipline
  author: andrew-pigors
  version: "1.0.0"
  triggers: subpoena, duces tecum, compel, witness, records request, UIDDA, service tracking
---

# LITIGATION-SUBPOENA-ENGINE

## Metadata
- **name**: litigation-subpoena-engine
- **category**: discipline
- **tier**: 2
- **version**: 1.0.0
- **context**: Pigors v Watson, 14th Judicial Circuit, Muskegon County, MI (Pro Se)
- **depends-on**: litigation-service-engine, litigation-discovery-warfare, litigation-filing-architect

## Description

Expert subpoena generation and enforcement system for Michigan family law proceedings.
Handles witness subpoenas (MCR 2.506), subpoenas duces tecum for document production
(MCR 2.305), out-of-state witness compulsion via UIDDA (MCL 600.1852), and third-party
record requests from banks, employers, schools, CPS, and law enforcement. Tracks service
status per subpoena, detects non-compliance, and generates motions to compel with
sanctions requests under MCR 2.313.

**Party context:**
- Plaintiff: Andrew James Pigors (Pro Se), 1977 Whitehall Road, Lot 17, North Muskegon MI 49445
- Defendant: Emily A. Watson (NOT "Emily Ann")
- Child: L.D.W. per MCR 8.119(H) — MALE
- Judge: Hon. Jenny L. McNeill — 14th Circuit Court

## Capabilities

1. **Subpoena Duces Tecum Generation** — MCR 2.305 compliant document production subpoenas
2. **Witness Subpoena Generation** — MCR 2.506 compliant attendance subpoenas
3. **Service Tracking and Compliance Monitoring** — Per-subpoena service status with deadlines
4. **Motion to Compel for Non-Compliance** — MCR 2.313 enforcement with sanctions
5. **Out-of-State Witness Subpoenas** — UIDDA process per MCL 600.1852
6. **Protective Order Analysis** — MCR 2.302(C) scope limitations and challenges
7. **Third-Party Record Subpoenas** — Banks, employers, schools, CPS, police
8. **Quash Motion Defense** — Responding to motions to quash subpoenas

## Requirements

- All subpoenas MUST include the case caption with correct case number per lane
- Subpoenas MUST be issued by the clerk or an attorney (Pro Se parties request issuance)
- Witness fees and mileage MUST be tendered with service per MCL 600.1455
- Document production subpoenas MUST specify documents with reasonable particularity
- 14-day minimum notice for document production per MCR 2.305(A)(1)
- Out-of-state subpoenas require domestication in the foreign jurisdiction
- All subpoenas must track: issued date, served date, return date, compliance status
- Lane routing: custody subpoenas → Lane A, housing → Lane B, PPO → Lane D

## Patterns

### Pattern 1: Subpoena Duces Tecum for Third-Party Records

```python
from legal_ai.engines import SubpoenaEngine
from legal_ai.models import Subpoena, SubpoenaType

def generate_duces_tecum(
    recipient: str,
    recipient_address: str,
    documents_requested: list[str],
    production_date: str,
    case_lane: str = "A",
) -> Subpoena:
    """Generate MCR 2.305 subpoena duces tecum."""
    engine = SubpoenaEngine()

    subpoena = engine.create_subpoena(
        subpoena_type=SubpoenaType.DUCES_TECUM,
        case_number=engine.get_case_number(case_lane),
        court="14th Circuit Court, Muskegon County",
        judge="Hon. Jenny L. McNeill",
        plaintiff="Andrew James Pigors",
        defendant="Emily A. Watson",
        recipient=recipient,
        recipient_address=recipient_address,
        documents=documents_requested,
        production_date=production_date,
        # MCR 2.305(A)(1): 14-day minimum notice
        notice_days=14,
    )

    # Validate completeness
    engine.validate_subpoena(subpoena, rules=["MCR 2.305", "MCR 2.506"])
    return subpoena

# Example: Bank records subpoena
bank_subpoena = generate_duces_tecum(
    recipient="Records Custodian, Chase Bank",
    recipient_address="123 Main St, Muskegon, MI 49440",
    documents_requested=[
        "All account statements for Emily A. Watson from 2023-01-01 to present",
        "All deposit and withdrawal records exceeding $500",
        "Safe deposit box access logs",
    ],
    production_date="2025-04-15",
    case_lane="A",
)
```

### Pattern 2: Witness Subpoena with Fee Tender

```python
from legal_ai.engines import SubpoenaEngine, ServiceTracker
from legal_ai.models import WitnessSubpoena

def generate_witness_subpoena(
    witness_name: str,
    witness_address: str,
    hearing_date: str,
    hearing_time: str,
    hearing_location: str,
    testimony_topics: list[str],
    case_lane: str = "A",
) -> WitnessSubpoena:
    """Generate MCR 2.506 witness subpoena with mandatory fee tender."""
    engine = SubpoenaEngine()

    # MCL 600.1455: witness fee = $12/day + $0.10/mile (round trip)
    mileage = engine.calculate_mileage(
        from_address=witness_address,
        to_address=hearing_location,
    )
    witness_fee = 12.00  # per day
    mileage_fee = mileage * 0.10  # per mile round trip
    total_tender = witness_fee + mileage_fee

    subpoena = engine.create_witness_subpoena(
        case_number=engine.get_case_number(case_lane),
        court="14th Circuit Court, Muskegon County",
        witness_name=witness_name,
        witness_address=witness_address,
        hearing_date=hearing_date,
        hearing_time=hearing_time,
        hearing_location=hearing_location,
        testimony_topics=testimony_topics,
        fee_tendered=total_tender,
    )

    # Register with service tracker
    tracker = ServiceTracker()
    tracker.register_subpoena(subpoena, status="issued")

    return subpoena
```

### Pattern 3: Motion to Compel After Non-Compliance

```python
from legal_ai.engines import SubpoenaEngine, MotionDrafter
from legal_ai.models import MotionToCompel

def prepare_motion_to_compel(
    subpoena_id: str,
    non_compliant_party: str,
    description_of_failure: str,
    sanctions_requested: bool = True,
) -> MotionToCompel:
    """MCR 2.313 motion to compel compliance with subpoena."""
    engine = SubpoenaEngine()
    drafter = MotionDrafter()

    # Retrieve original subpoena and service proof
    subpoena = engine.get_subpoena(subpoena_id)
    service_proof = engine.get_service_proof(subpoena_id)

    motion = drafter.draft_motion_to_compel(
        case_number=subpoena.case_number,
        court=subpoena.court,
        non_compliant_party=non_compliant_party,
        subpoena_details=subpoena,
        service_proof=service_proof,
        failure_description=description_of_failure,
        # MCR 2.313(A): motion to compel discovery
        rule_basis="MCR 2.313(A)",
        # MCR 2.313(B)(2)(b): sanctions including attorney fees
        request_sanctions=sanctions_requested,
        sanctions_basis="MCR 2.313(B)(2)(b)" if sanctions_requested else None,
        # Pro Se: request costs rather than attorney fees
        costs_description="Costs of filing this motion and related expenses",
    )

    return motion
```

### Pattern 4: UIDDA Out-of-State Subpoena

```python
from legal_ai.engines import SubpoenaEngine

def generate_uidda_subpoena(
    foreign_state: str,
    witness_name: str,
    witness_address: str,
    documents_or_testimony: str,
) -> dict:
    """MCL 600.1852 Uniform Interstate Depositions and Discovery Act."""
    engine = SubpoenaEngine()

    # Step 1: Obtain Michigan subpoena from issuing court
    mi_subpoena = engine.create_subpoena(
        subpoena_type="duces_tecum",
        case_number="2024-001507-DC",
        court="14th Circuit Court, Muskegon County",
        recipient=witness_name,
        recipient_address=witness_address,
    )

    # Step 2: Generate UIDDA package for foreign jurisdiction
    uidda_package = engine.prepare_uidda_package(
        michigan_subpoena=mi_subpoena,
        foreign_state=foreign_state,
        # MCL 600.1852: present MI subpoena to clerk in foreign state
        domestication_instructions=True,
    )

    return {
        "michigan_subpoena": mi_subpoena,
        "uidda_package": uidda_package,
        "foreign_state": foreign_state,
        "next_steps": [
            f"File Michigan subpoena with clerk of court in {foreign_state}",
            f"Clerk issues {foreign_state} subpoena incorporating MI terms",
            "Serve per foreign state's rules of civil procedure",
        ],
    }
```

## Anti-Patterns

### Anti-Pattern 1: Issuing Subpoena Without Proper Authority
```python
# WRONG — Pro Se litigant cannot self-issue subpoenas in Michigan
subpoena.issued_by = "Andrew James Pigors"  # NO — not an attorney

# CORRECT — Request issuance from the clerk of court
subpoena.issued_by = "Clerk, 14th Circuit Court"
subpoena.requested_by = "Andrew James Pigors, Plaintiff Pro Se"
```

### Anti-Pattern 2: Insufficient Notice Period
```python
# WRONG — Less than 14 days for document production
subpoena = create_duces_tecum(
    production_date="2025-03-05",  # Only 3 days from today
)

# CORRECT — MCR 2.305(A)(1) requires 14-day minimum
subpoena = create_duces_tecum(
    production_date="2025-03-20",  # 14+ days from service
)
```

### Anti-Pattern 3: Failing to Tender Witness Fees
```python
# WRONG — No fee tender with witness subpoena
serve_subpoena(subpoena, witness_fee=0)
# Result: subpoena is voidable; witness can refuse to appear

# CORRECT — MCL 600.1455 requires fee + mileage tender at service
serve_subpoena(
    subpoena,
    witness_fee=12.00,        # $12/day
    mileage_fee=round_trip * 0.10,  # $0.10/mile
)
```

### Anti-Pattern 4: Overly Broad Document Requests
```python
# WRONG — Fishing expedition, subject to quash
documents = ["All records relating to Emily Watson"]

# CORRECT — Specific, relevant, time-bounded
documents = [
    "Bank statements for account ending in XXXX, Jan 2023 – Dec 2024",
    "Wire transfers exceeding $500 during same period",
    "Account holder address changes during same period",
]
```

## Michigan-Specific Rules

| Rule | Subject | Key Requirement |
|------|---------|-----------------|
| **MCR 2.305** | Subpoena duces tecum | 14-day notice; reasonable particularity; may inspect/copy |
| **MCR 2.506** | Subpoena for attendance | Issued by clerk or attorney; compelling attendance at hearing/trial |
| **MCR 2.313** | Motion to compel | Certification of good-faith conference required; sanctions available |
| **MCR 2.302(C)** | Protective orders | Court may limit scope of discovery to protect privacy |
| **MCL 600.1455** | Subpoena power/fees | $12/day witness fee + $0.10/mile mileage; tender at service |
| **MCL 600.1852** | UIDDA | Present MI subpoena to foreign state clerk for domestication |
| **MCR 2.506(G)** | Contempt for disobedience | Failure to obey subpoena = contempt of court |
| **MCR 3.206(C)** | Discovery in domestic cases | Discovery per MCR 2.301–2.314 applies to domestic relations |

### Witness Fee Schedule (MCL 600.1455)
- Per diem: $12.00 per day of attendance
- Mileage: $0.10 per mile (round trip from witness residence to courthouse)
- Tender required AT TIME OF SERVICE — not later
- Non-tender renders subpoena unenforceable

### Third-Party Record Categories
| Record Type | Typical Custodian | Special Requirements |
|-------------|-------------------|---------------------|
| Bank records | Financial institution records dept | RFPA notice may apply for federal banks |
| Employment records | HR department | May require employee consent or court order |
| School records | School district records custodian | FERPA: requires court order per 20 USC §1232g |
| CPS records | MDHHS | MCL 722.627: court order required for release |
| Police reports | Law enforcement records bureau | FOIA request or subpoena; some exempt per MCL 15.243 |
| Medical records | Health information management | HIPAA: qualified protective order per 45 CFR 164.512(e) |

## Integration Points

- **litigation-service-engine**: Hands off service tracking after subpoena generation
- **litigation-discovery-warfare**: Coordinates subpoenas with broader discovery strategy
- **litigation-filing-architect**: Formats subpoena filings per court requirements
- **litigation-evidence-harvester**: Ingests documents received via subpoena response
- **litigation-sanctions-engine**: Escalates non-compliance to sanctions workflow
- **litigation-court-order-tracker**: Logs court orders related to subpoena enforcement
- **litigation-timeline-forensics**: Adds subpoena milestones to case timeline


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
| MCR 3.203 | 850 | 🆕 Verify & integrate |
| MCR 1.109 | 795 | 🆕 Verify & integrate |
| MCR 3.606 | 766 | 🆕 Verify & integrate |

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
