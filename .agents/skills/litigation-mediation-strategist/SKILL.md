---
name: litigation-mediation-strategist
description: >-
  Mediation preparation, negotiation tactics, and ADR strategy specialist for Michigan
  family law litigation. Drafts mediation briefs, develops opening statements, builds
  issue prioritization matrices, and manages mediator selection.
  Use when: mediation, ADR, alternative dispute resolution, mediation brief, mediator
  selection, negotiation strategy, mediation confidentiality, settlement conference,
  custody mediation, MCR 2.410, MCR 2.411, MCR 3.216, mediation privilege.
metadata:
  category: discipline
  author: andrew-pigors
  version: "1.0.0"
  triggers: mediation, ADR, mediation brief, mediator, negotiation, settlement conference
---

# LITIGATION-MEDIATION-STRATEGIST

## Metadata
- **name**: litigation-mediation-strategist
- **category**: discipline
- **tier**: 2
- **version**: 1.0.0
- **context**: Pigors v Watson, 14th Judicial Circuit, Muskegon County, MI (Pro Se)
- **depends-on**: litigation-settlement-analyzer, litigation-custody-specialist, litigation-brief-writer

## Description

Expert mediation preparation and negotiation strategy system for Michigan family law
proceedings. Handles both general civil mediation under MCR 2.410-2.412 and domestic
relations mediation under MCR 3.216. Prepares comprehensive mediation briefs, develops
opening statements, constructs issue prioritization and trade-off matrices, calculates
walk-away points, and manages mediator selection per MCR 2.411(B). Ensures compliance
with mediation communications privilege under MCR 2.412.

**Party context:**
- Plaintiff: Andrew James Pigors (Pro Se), 1977 Whitehall Road, Lot 17, North Muskegon MI 49445
- Defendant: Emily A. Watson (NOT "Emily Ann")
- Child: L.D.W. per MCR 8.119(H) — MALE
- Judge: Hon. Jenny L. McNeill — 14th Circuit Court

## Capabilities

1. **Mediation Brief Drafting** — MCR 2.411/3.216 compliant briefs
2. **Opening Statement Preparation** — Persuasive yet conciliatory opening remarks
3. **Issue Prioritization Matrix** — Ranked issues with trade-off flexibility scores
4. **BATNA Development** — Walk-away point and reservation value calculation
5. **Mediator Selection Criteria** — MCR 2.411(B) qualification analysis
6. **Confidentiality Compliance** — MCR 2.412 privilege rules enforcement
7. **Custody Mediation Strategies** — MCR 3.216 best-interest focused approach
8. **Post-Mediation Agreement Drafting** — Binding settlement documentation
9. **Objection to Mediation Process** — MCR 2.411(C) objection grounds

## Requirements

- Mediation briefs MUST be factual and conciliatory — avoid adversarial tone
- Custody issues: child's best interest is paramount — MCL 722.23 factors
- MCR 2.412: mediation communications are PRIVILEGED — never cite in court filings
- Mediator must meet MCR 2.411(B) qualifications (trained, experienced, impartial)
- Domestic relations mediation under MCR 3.216 is mandatory unless exempted
- Walk-away points must be evidence-based, not emotional
- Issue trade-off matrix must identify negotiables vs. non-negotiables clearly
- All mediation materials must protect confidential strategy from disclosure

## Patterns

### Pattern 1: Mediation Brief Drafting

```python
from legal_ai.engines import MediationEngine
from legal_ai.models import MediationBrief, MediationIssue

def draft_mediation_brief(
    case_lane: str,
    mediation_date: str,
    mediator_name: str,
    issues: list[dict],
) -> MediationBrief:
    """Draft MCR 3.216 / MCR 2.411 compliant mediation brief."""
    engine = MediationEngine()

    # Categorize issues by priority
    prioritized = engine.prioritize_issues(issues)

    brief = MediationBrief(
        case_number=engine.get_case_number(case_lane),
        court="14th Circuit Court, Muskegon County",
        mediation_date=mediation_date,
        mediator=mediator_name,
        plaintiff="Andrew James Pigors",
        defendant="Emily A. Watson",
        sections={
            "case_summary": engine.generate_case_summary(case_lane),
            "disputed_issues": [
                MediationIssue(
                    issue=iss["description"],
                    plaintiff_position=iss["our_position"],
                    defendant_position=iss.get("opposing_position", "Unknown"),
                    priority=iss["priority"],
                    flexibility=iss["flexibility_score"],  # 1-10
                    supporting_evidence=iss.get("exhibits", []),
                )
                for iss in prioritized
            ],
            "settlement_history": engine.get_prior_offers(case_lane),
            "proposed_resolution": engine.draft_proposed_terms(prioritized),
        },
        # MCR 2.412: mark as confidential mediation material
        confidentiality_notice=(
            "This brief is prepared for mediation purposes only. "
            "Per MCR 2.412, mediation communications are privileged "
            "and may not be disclosed in subsequent proceedings."
        ),
    )

    return brief
```

### Pattern 2: Issue Prioritization and Trade-Off Matrix

```python
from legal_ai.engines import MediationEngine

def build_trade_off_matrix(case_lane: str) -> dict:
    """Prioritize issues and identify negotiable vs. non-negotiable items."""
    engine = MediationEngine()

    issues = engine.get_all_issues(case_lane)
    matrix = {"non_negotiable": [], "flexible": [], "tradeable": []}

    for issue in issues:
        score = engine.score_issue(
            issue,
            factors={
                "impact_on_child": issue.child_impact_score,
                "legal_strength": issue.legal_merit,
                "emotional_weight": issue.emotional_weight,
                "precedent_value": issue.precedent_importance,
                "financial_impact": issue.financial_impact,
            },
        )

        category_item = {
            "issue": issue.description,
            "priority_score": score.total,
            "our_ideal_outcome": issue.ideal_outcome,
            "minimum_acceptable": issue.minimum_acceptable,
            "trade_value": score.trade_value,
        }

        if score.total >= 9:
            matrix["non_negotiable"].append(category_item)
        elif score.total >= 6:
            matrix["flexible"].append(category_item)
        else:
            matrix["tradeable"].append(category_item)

    return matrix
```

### Pattern 3: Mediator Selection and Objection

```python
from legal_ai.engines import MediationEngine

def evaluate_mediator(
    mediator_name: str,
    case_lane: str,
) -> dict:
    """Evaluate mediator qualifications per MCR 2.411(B)."""
    engine = MediationEngine()

    evaluation = {
        "mediator": mediator_name,
        "qualifications_check": {
            # MCR 2.411(B)(1): general qualifications
            "training_hours": engine.check_training(mediator_name),
            "experience_years": engine.check_experience(mediator_name),
            "family_law_expertise": engine.check_specialty(
                mediator_name, "family_law"
            ),
            "impartiality": engine.check_conflicts(
                mediator_name,
                parties=["Andrew James Pigors", "Emily A. Watson"],
            ),
        },
        "recommendation": None,
        "objection_grounds": [],
    }

    # Check for objection grounds per MCR 2.411(C)
    if not evaluation["qualifications_check"]["impartiality"]:
        evaluation["objection_grounds"].append(
            "Conflict of interest — MCR 2.411(C)(1)"
        )
    if not evaluation["qualifications_check"]["family_law_expertise"]:
        evaluation["objection_grounds"].append(
            "Insufficient domestic relations experience — MCR 2.411(C)(3)"
        )

    evaluation["recommendation"] = (
        "ACCEPT" if not evaluation["objection_grounds"]
        else "OBJECT"
    )

    return evaluation
```

### Pattern 4: Post-Mediation Settlement Agreement

```python
from legal_ai.engines import MediationEngine, SettlementDrafter

def draft_settlement_agreement(
    agreed_terms: list[dict],
    case_lane: str,
) -> dict:
    """Convert mediation agreement into binding settlement document."""
    engine = MediationEngine()
    drafter = SettlementDrafter()

    agreement = drafter.draft_agreement(
        case_number=engine.get_case_number(case_lane),
        court="14th Circuit Court, Muskegon County",
        plaintiff="Andrew James Pigors",
        defendant="Emily A. Watson",
        terms=agreed_terms,
        # Custody provisions per MCL 722.23
        custody_provisions=engine.extract_custody_terms(agreed_terms),
        # Include required domestic relations provisions
        required_clauses=[
            "child_support_reservation",
            "parenting_time_specifics",
            "decision_making_authority",
            "dispute_resolution_mechanism",
        ],
        # MCR 3.216: agreement must be in writing and signed
        signature_blocks=["plaintiff", "defendant", "mediator"],
    )

    return {
        "agreement": agreement,
        "requires_court_approval": True,  # Custody terms need judicial approval
        "filing_instructions": "Submit as stipulated order per MCR 2.602",
    }
```

## Anti-Patterns

### Anti-Pattern 1: Adversarial Tone in Mediation Brief
```python
# WRONG — Aggressive, litigation-style language
brief.opening = "Defendant's pattern of deception and manipulation..."

# CORRECT — Factual, solution-oriented language
brief.opening = (
    "The parties have been unable to resolve parenting time "
    "arrangements. Plaintiff proposes the following framework..."
)
```

### Anti-Pattern 2: Disclosing Mediation Communications in Court
```python
# WRONG — Citing what was said in mediation (MCR 2.412 violation)
motion.argument = "At mediation, Defendant admitted she withheld records..."

# CORRECT — Never reference mediation communications in filings
motion.argument = "Evidence shows records were not produced as ordered..."
# Use independent evidence, NOT mediation disclosures
```

### Anti-Pattern 3: Mediating Without Walk-Away Point
```python
# WRONG — Entering mediation without defined limits
mediation.prepare(strategy="see what happens")

# CORRECT — Define BATNA and walk-away point BEFORE mediation
mediation.prepare(
    batna=settlement_analyzer.calculate_batna(case_lane),
    walk_away_point=25_000,  # minimum acceptable
    non_negotiables=["parenting time", "decision-making"],
    tradeable_items=["property division timeline"],
)
```

### Anti-Pattern 4: Skipping Mandatory Domestic Relations Mediation
```python
# WRONG — Ignoring MCR 3.216 mandatory mediation
skip_mediation(reason="waste of time")
# Result: court may sanction or delay proceedings

# CORRECT — Comply or file exemption request per MCR 3.216
if exemption_grounds:
    file_exemption(
        ground="domestic violence history",
        rule="MCR 3.216(H)",  # exemption for DV
        evidence=dv_evidence,
    )
else:
    participate_in_good_faith()
```

## Michigan-Specific Rules

| Rule | Subject | Key Requirement |
|------|---------|-----------------|
| **MCR 2.410** | ADR generally | Court may order ADR; parties may stipulate |
| **MCR 2.411** | Case evaluation | 3-panel evaluation; rejection cost consequences |
| **MCR 2.412** | Mediation privilege | Communications are confidential and privileged |
| **MCR 3.216** | Domestic mediation | Mandatory in custody disputes unless exempt |
| **MCR 3.216(H)** | Mediation exemption | Domestic violence exemption from mandatory mediation |
| **MCL 691.1551-1564** | Michigan Mediation Act | Governs mediation procedures and enforceability |
| **MCR 2.411(B)** | Mediator qualifications | Training, experience, impartiality requirements |
| **MCR 2.411(C)** | Objection to mediator | Grounds for disqualification of assigned mediator |

### Mediation Privilege (MCR 2.412) — Critical Rules
- Mediation communications are **privileged** and inadmissible
- Privilege applies to: statements, conduct, documents created for mediation
- Exceptions: written signed agreements; threats of violence; professional malpractice claims
- Mediator may not be compelled to testify about mediation communications
- **Violation consequence**: evidence excluded, potential sanctions

### Domestic Relations Mediation (MCR 3.216)
- **Mandatory** in custody and parenting time disputes
- Parties must attend **in good faith**
- Exemptions: domestic violence (MCR 3.216(H)), other good cause
- Mediator communicates impasse (not content) to the court
- Agreement in mediation must be reduced to writing and signed by both parties

## Integration Points

- **litigation-settlement-analyzer**: Provides BATNA values and case evaluation data
- **litigation-custody-specialist**: MCL 722.23 best-interest factors for custody mediation
- **litigation-brief-writer**: Drafts mediation briefs with appropriate tone
- **litigation-harm-quantifier**: Damages data for settlement range calculation
- **litigation-pro-se-guardian**: Ensures Pro Se procedural compliance in ADR
- **litigation-court-order-tracker**: Converts mediation agreements into trackable orders
- **litigation-filing-architect**: Formats post-mediation filings for court submission


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
| Custody Modification | 65/100 | A,D,E | Verified |
| Emergency Custody | 55/100 | A,D,E | Verified |
| PPO Modification/Termination | 60/100 | A,D,E | Verified |
| Contempt | 70/100 | A,D,E | Verified |
| Judicial Disqualification | 75/100 | A,D,E | Verified |
| JTC Formal Complaint | 75/100 | A,D,E | Verified |

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

### Self-Evolution Protocol
```
After each use of this skill:
1. Log output quality score (1-10) to session SQL
2. Record any missing citations or evidence gaps discovered
3. Update lane-specific intelligence if new orders/events occurred
4. Cross-reference findings with contradiction_map for consistency
5. Feed results to litigation-red-team for adversarial validation
```
