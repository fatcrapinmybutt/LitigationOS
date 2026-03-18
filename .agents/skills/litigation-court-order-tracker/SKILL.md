---
name: litigation-court-order-tracker
description: >-
  Court order compliance monitoring, violation detection, and contempt enforcement
  specialist for Michigan family law litigation. Catalogs all orders across all courts,
  tracks compliance per provision, detects violations with evidence linking, and prepares
  contempt motions.
  Use when: court order, compliance, violation, contempt, show cause, order modification,
  ex parte order, conflicting orders, order enforcement, MCR 3.606, order catalog,
  provision tracking, order timeline, order conflict detection.
metadata:
  category: discipline
  author: andrew-pigors
  version: "1.0.0"
  triggers: court order, compliance, violation, contempt, show cause, order tracking
---

# LITIGATION-COURT-ORDER-TRACKER

## Metadata
- **name**: litigation-court-order-tracker
- **category**: discipline
- **tier**: 2
- **version**: 1.0.0
- **context**: Pigors v Watson, 14th Judicial Circuit, Muskegon County, MI (Pro Se)
- **depends-on**: litigation-timeline-forensics, litigation-evidence-harvester, litigation-judicial-analyst

## Description

Comprehensive court order compliance monitoring and violation detection system for
multi-court Michigan family law litigation. Catalogs every court order across all 6 case
lanes and 8 jurisdictions. Breaks each order into individual provisions with compliance
deadlines. Tracks compliance status per provision with evidence linking. Detects violations
and generates contempt motion packages under MCR 3.606. Identifies conflicting orders from
different courts or judges. Monitors ex parte orders and prepares challenge motions under
MCR 3.207.

**Party context:**
- Plaintiff: Andrew James Pigors (Pro Se), 1977 Whitehall Road, Lot 17, North Muskegon MI 49445
- Defendant: Emily A. Watson (NOT "Emily Ann")
- Child: L.D.W. per MCR 8.119(H) — MALE
- Judge: Hon. Jenny L. McNeill — 14th Circuit Court

## Capabilities

1. **Order Cataloging** — Date, court, judge, type, provisions, compliance status per order
2. **Provision-Level Tracking** — Individual compliance deadlines per order provision
3. **Violation Detection** — Automated evidence-linked violation identification
4. **Contempt Motion Preparation** — MCR 3.606 contempt proceedings package
5. **Order Modification Tracking** — Chronological modification history per order
6. **Ex Parte Order Identification** — Flag and challenge ex parte orders per MCR 3.207
7. **Order Conflict Detection** — Conflicting orders across courts/judges
8. **Show Cause Hearing Preparation** — Evidence binders for show cause hearings

## Requirements

- Every order MUST be cataloged with: date entered, court, judge, case number, order type
- Each provision within an order must be tracked individually with its own compliance status
- Compliance status values: COMPLIED, PARTIAL, VIOLATED, PENDING, EXPIRED, MODIFIED
- Violations MUST link to specific evidence (exhibits, timestamps, witness statements)
- Ex parte orders MUST be flagged for 14-day hearing review per MCR 3.207(B)
- Order conflicts MUST be identified by comparing provisions across courts
- All orders across lanes A-F must be in a single unified catalog for conflict detection
- Contempt motions require: clear order, knowledge of order, willful violation

## Patterns

### Pattern 1: Order Cataloging and Provision Extraction

```python
from legal_ai.engines import OrderTracker
from legal_ai.models import CourtOrder, OrderProvision

def catalog_order(
    order_date: str,
    court: str,
    judge: str,
    case_number: str,
    case_lane: str,
    order_type: str,
    order_text: str,
    source_exhibit: str,
) -> CourtOrder:
    """Catalog a court order and extract individual provisions."""
    tracker = OrderTracker()

    # Parse order text into individual provisions
    provisions = tracker.extract_provisions(order_text)

    order = CourtOrder(
        order_date=order_date,
        court=court,
        judge=judge,
        case_number=case_number,
        case_lane=case_lane,
        order_type=order_type,
        full_text=order_text,
        source_exhibit=source_exhibit,
        provisions=[
            OrderProvision(
                provision_number=i + 1,
                text=prov["text"],
                compliance_deadline=prov.get("deadline"),
                obligated_party=prov.get("obligated_party"),
                status="PENDING",
            )
            for i, prov in enumerate(provisions)
        ],
    )

    tracker.save_order(order)
    return order

# Example: custody order
order = catalog_order(
    order_date="2024-11-15",
    court="14th Circuit Court, Muskegon County",
    judge="Hon. Jenny L. McNeill",
    case_number="2024-001507-DC",
    case_lane="A",
    order_type="Custody Order",
    order_text="IT IS ORDERED: 1. Defendant shall have parenting time...",
    source_exhibit="Exhibit A-45",
)
```

### Pattern 2: Violation Detection with Evidence Linking

```python
from legal_ai.engines import OrderTracker
from legal_ai.models import Violation

def detect_violation(
    order_id: str,
    provision_number: int,
    violation_date: str,
    description: str,
    evidence_exhibits: list[str],
    witness_statements: list[str] | None = None,
) -> Violation:
    """Record an order violation with evidence chain."""
    tracker = OrderTracker()

    order = tracker.get_order(order_id)
    provision = order.provisions[provision_number - 1]

    violation = Violation(
        order_id=order_id,
        provision_number=provision_number,
        provision_text=provision.text,
        violation_date=violation_date,
        violating_party=provision.obligated_party,
        description=description,
        evidence=[
            {"type": "exhibit", "id": ex} for ex in evidence_exhibits
        ] + [
            {"type": "witness", "statement": ws}
            for ws in (witness_statements or [])
        ],
        severity=tracker.assess_severity(provision, description),
    )

    # Update provision status
    tracker.update_provision_status(
        order_id=order_id,
        provision_number=provision_number,
        new_status="VIOLATED",
        violation_id=violation.violation_id,
    )

    return violation
```

### Pattern 3: Contempt Motion Preparation (MCR 3.606)

```python
from legal_ai.engines import OrderTracker, MotionDrafter

def prepare_contempt_motion(
    order_id: str,
    violations: list[str],
    relief_requested: list[str],
) -> dict:
    """MCR 3.606 contempt motion for willful order violations."""
    tracker = OrderTracker()
    drafter = MotionDrafter()

    order = tracker.get_order(order_id)
    violation_records = [tracker.get_violation(v) for v in violations]

    # Contempt requires: (1) clear order, (2) knowledge, (3) willful violation
    contempt_elements = {
        "clear_order": {
            "satisfied": True,
            "proof": f"Order entered {order.order_date} by {order.judge}",
            "exhibit": order.source_exhibit,
        },
        "knowledge_of_order": {
            "satisfied": True,
            "proof": "Order served on respondent / entered in open court",
        },
        "willful_violation": {
            "satisfied": all(v.severity in ("HIGH", "CRITICAL") for v in violation_records),
            "proof": [v.description for v in violation_records],
            "evidence": [e for v in violation_records for e in v.evidence],
        },
    }

    motion = drafter.draft_contempt_motion(
        case_number=order.case_number,
        court=order.court,
        respondent=violation_records[0].violating_party,
        order_details=order,
        violations=violation_records,
        contempt_elements=contempt_elements,
        relief_requested=relief_requested,
        rule_basis="MCR 3.606",
        # MCR 3.606(A): civil contempt to enforce compliance
        contempt_type="civil",
    )

    return {
        "motion": motion,
        "supporting_brief": drafter.draft_supporting_brief(motion),
        "exhibit_list": [e["id"] for v in violation_records for e in v.evidence],
        "proposed_order": drafter.draft_proposed_order(motion),
    }
```

### Pattern 4: Cross-Court Order Conflict Detection

```python
from legal_ai.engines import OrderTracker

def detect_order_conflicts() -> list[dict]:
    """Identify conflicting provisions across courts and judges."""
    tracker = OrderTracker()

    all_orders = tracker.get_all_active_orders()
    conflicts = []

    # Compare provisions across all active orders
    for i, order_a in enumerate(all_orders):
        for order_b in all_orders[i + 1:]:
            for prov_a in order_a.provisions:
                for prov_b in order_b.provisions:
                    conflict = tracker.check_conflict(prov_a, prov_b)
                    if conflict:
                        conflicts.append({
                            "order_a": {
                                "id": order_a.order_id,
                                "court": order_a.court,
                                "judge": order_a.judge,
                                "date": order_a.order_date,
                                "provision": prov_a.text,
                            },
                            "order_b": {
                                "id": order_b.order_id,
                                "court": order_b.court,
                                "judge": order_b.judge,
                                "date": order_b.order_date,
                                "provision": prov_b.text,
                            },
                            "conflict_type": conflict.conflict_type,
                            "resolution_priority": (
                                "later_in_time"
                                if order_a.order_date < order_b.order_date
                                else "earlier_in_time"
                            ),
                        })

    return conflicts
```

## Anti-Patterns

### Anti-Pattern 1: Tracking Orders Without Provisions
```python
# WRONG — Order tracked as monolithic blob
order = CourtOrder(text="Full order text here...", status="active")

# CORRECT — Break into individual provisions with individual tracking
order = CourtOrder(
    provisions=[
        OrderProvision(text="Provision 1...", status="COMPLIED"),
        OrderProvision(text="Provision 2...", status="VIOLATED"),
        OrderProvision(text="Provision 3...", status="PENDING"),
    ]
)
```

### Anti-Pattern 2: Contempt Without All Three Elements
```python
# WRONG — Filing contempt without proving all elements
file_contempt(violation="she didn't follow the order")

# CORRECT — MCR 3.606 requires all three elements proven
file_contempt(
    clear_order=True,         # (1) unambiguous order
    knowledge_proven=True,    # (2) respondent knew of order
    willful_violation=True,   # (3) deliberate non-compliance
    evidence_chain=evidence,  # evidence for each element
)
```

### Anti-Pattern 3: Ignoring Ex Parte Order Challenge Deadlines
```python
# WRONG — Letting ex parte order stand without challenge
# MCR 3.207(B): hearing must be held within 14 days

# CORRECT — Immediately request hearing to challenge
if order.is_ex_parte:
    challenge_deadline = order.order_date + timedelta(days=14)
    tracker.schedule_challenge(order, deadline=challenge_deadline)
    tracker.alert(f"Ex parte order: hearing required by {challenge_deadline}")
```

## Michigan-Specific Rules

| Rule | Subject | Key Requirement |
|------|---------|-----------------|
| **MCR 3.606** | Contempt in domestic cases | Civil contempt to enforce compliance; criminal for punishment |
| **MCR 3.207** | Ex parte orders (domestic) | Requires verified statement; hearing within 14 days |
| **MCR 2.602** | Order requirements | Signed by judge; specific and unambiguous provisions |
| **MCR 2.612** | Relief from judgment/order | Grounds: mistake, newly discovered evidence, fraud, void |
| **MCR 3.207(A)** | Emergency ex parte | Irreparable injury required; verified complaint |
| **MCR 3.207(B)** | Ex parte hearing deadline | Hearing within 14 days; respondent has right to be heard |
| **MCR 2.602(B)(3)** | Service of orders | Orders must be served on all parties per court rule |

### Contempt Standards (MCR 3.606)
- **Civil contempt**: coercive — designed to compel compliance; purge condition required
- **Criminal contempt**: punitive — punishment for past violation
- **Burden of proof**: movant must show violation by preponderance (civil) or beyond reasonable doubt (criminal)
- **Defense**: inability to comply (not unwillingness) is a defense
- **Purge condition**: civil contempt order MUST include a way to purge the contempt

### Order Hierarchy
1. **Federal court orders** take precedence over state (Supremacy Clause)
2. **Later-in-time** orders generally supersede earlier conflicting orders
3. **Higher court** orders bind lower courts
4. **Emergency/ex parte** orders are temporary and must be confirmed at hearing

## Integration Points

- **litigation-timeline-forensics**: Provides chronological order history for conflict detection
- **litigation-evidence-harvester**: Links evidence exhibits to specific violations
- **litigation-judicial-analyst**: Analyzes judicial patterns in order issuance
- **litigation-filing-architect**: Formats contempt motions per court requirements
- **litigation-sanctions-engine**: Escalates repeated violations to sanctions workflow
- **litigation-pro-se-guardian**: Ensures Pro Se compliance with own order obligations
- **litigation-emergency-motion-engine**: Handles emergency modification requests
- **litigation-convergence-orchestrator**: Cross-lane order conflict resolution


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
| C | 279 | USDC filing pending | U.S. District Court, W.D. Michigan |
| D | 6,462 | 2023-5907-PP | 14th Circuit |
| E | 9,945 | JTC Complaint - McNeill | Judicial Tenure Commission |

### Harvest-Discovered Citations (New)
| MCR Citation | Files Found | Status |
|-------------|----------:|--------|
| MCR 2.003 | 1980 | 🆕 Verify & integrate |
| MCR 2.119 | 1635 | 🆕 Verify & integrate |
| MCR 2.107 | 1369 | 🆕 Verify & integrate |
| MCR 2.003(C)(1) | 882 | 🆕 Verify & integrate |
| MCR 2.105 | 871 | 🆕 Verify & integrate |
| MCR 2.313 | 868 | 🆕 Verify & integrate |
| MCR 3.203 | 850 | 🆕 Verify & integrate |
| MCR 1.109 | 795 | 🆕 Verify & integrate |
| MCR 3.210 | 761 | 🆕 Verify & integrate |
| MCR 2.113 | 756 | 🆕 Verify & integrate |

### FTS5 Query Templates
```sql
-- Search evidence for this skill's domain
SELECT * FROM pages_fts WHERE pages_fts MATCH 'custody AND best AND interest';
SELECT * FROM evidence_quotes WHERE legal_significance LIKE '%722.23%';
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
| Custody Modification | 65/100 | A,C,D,E | Verified |
| Emergency Custody | 55/100 | A,C,D,E | Verified |
| PPO Modification/Termination | 60/100 | A,C,D,E | Verified |
| Contempt | 70/100 | A,C,D,E | Verified |
| Judicial Disqualification | 75/100 | A,C,D,E | Verified |
| Federal §1983 Complaint | 70/100 | A,C,D,E | Verified |
| JTC Formal Complaint | 75/100 | A,C,D,E | Verified |

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
