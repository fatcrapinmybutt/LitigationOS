---
name: litigation-appeal-brief-engine
description: >-
  Appellate brief drafting and standard of review specialist for Michigan Court of Appeals
  and Supreme Court. Handles claim of appeal, leave applications, appellant/appellee briefs,
  issue preservation, record citations, and appendix preparation.
  Use when: appeal, appellate brief, claim of appeal, leave to appeal, standard of review,
  issue preservation, record citation, appendix, MCR 7.204, MCR 7.205, MCR 7.212,
  COA 366810, Michigan Supreme Court, oral argument, reply brief.
metadata:
  category: discipline
  author: andrew-pigors
  version: "1.0.0"
  triggers: appeal, appellate brief, COA, MSC, standard of review, claim of appeal, MCR 7.212
---

# LITIGATION-APPEAL-BRIEF-ENGINE

## Metadata
- **name**: litigation-appeal-brief-engine
- **category**: discipline
- **tier**: 2
- **version**: 1.0.0
- **context**: Pigors v Watson, COA 366810, 14th Judicial Circuit, Muskegon County, MI (Pro Se)
- **depends-on**: litigation-appellate-strategist, litigation-record-builder, litigation-brief-writer

## Description

Comprehensive appellate brief drafting system for Michigan Court of Appeals (COA) and
Michigan Supreme Court (MSC) proceedings. Generates fully formatted briefs complying with
MCR 7.212 requirements including statement of jurisdiction, statement of questions
presented, statement of facts with record citations, argument with standard of review
analysis, and relief requested. Handles claim of appeal (MCR 7.204), application for
leave to appeal (MCR 7.205), reply briefs, and appendix preparation (MCR 7.212(G)).
Performs issue preservation analysis to identify whether each issue was properly raised
in the lower court.

**Party context:**
- Plaintiff-Appellant: Andrew James Pigors (Pro Se)
- Defendant-Appellee: Emily A. Watson
- Child: L.D.W. per MCR 8.119(H) — MALE
- Trial Judge: Hon. Jenny L. McNeill — 14th Circuit Court
- COA Case: 366810

## Capabilities

1. **Claim of Appeal Preparation** — MCR 7.204 claim with jurisdictional statement
2. **Leave to Appeal Application** — MCR 7.205 with supporting brief
3. **Appellant's Brief Drafting** — Full MCR 7.212 compliant brief
4. **Standard of Review Selection** — De novo, clear error, abuse of discretion analysis
5. **Issue Preservation Analysis** — Was each issue raised and ruled on below?
6. **Record Citation Format** — MCR 7.212(C)(7) compliant lower court record citations
7. **Statement of Questions Presented** — MCR 7.212(C)(5) formatted questions
8. **Appendix Preparation** — MCR 7.212(G) appendix with required documents
9. **Reply Brief Generation** — Response to appellee's arguments
10. **Oral Argument Preparation** — Key points, anticipated questions, rebuttal

## Requirements

- ALL record references must use format per MCR 7.212(C)(7): "(Tr vol X, p Y)" or "(Lower Ct File, p Y)"
- Statement of questions presented must be outcome-determinative per MCR 7.212(C)(5)
- Brief length: max 50 pages (appellant), max 50 pages (appellee) per MCR 7.212(B)
- Appendix MUST include: judgment/order appealed, relevant portions of lower court record
- Each issue must identify the applicable standard of review
- Issue preservation: unpreserved issues reviewed only for plain error
- Filing deadlines: 56 days from claim (appellant), 35 days after (appellee)
- Font: 12-point proportional or 10-point monospaced per MCR 7.212(B)

## Patterns

### Pattern 1: MCR 7.212 Appellant's Brief Structure

```python
from legal_ai.engines import AppealBriefEngine
from legal_ai.models import AppellateBrief, QuestionPresented

def draft_appellant_brief(
    coa_case_number: str,
    lower_court_case: str,
    issues_on_appeal: list[dict],
    record_excerpts: list[dict],
) -> AppellateBrief:
    """Draft MCR 7.212 compliant appellant's brief."""
    engine = AppealBriefEngine()

    brief = AppellateBrief(
        case_number=coa_case_number,
        court="Michigan Court of Appeals",
        appellant="Andrew James Pigors",
        appellee="Emily A. Watson",
        lower_court="14th Circuit Court, Muskegon County",
        lower_court_case=lower_court_case,
        lower_court_judge="Hon. Jenny L. McNeill",
        sections={
            # MCR 7.212(C)(1): table of contents
            "table_of_contents": engine.generate_toc(),
            # MCR 7.212(C)(2): index of authorities
            "index_of_authorities": engine.build_authority_index(issues_on_appeal),
            # MCR 7.212(C)(3): statement of jurisdiction
            "jurisdiction_statement": engine.draft_jurisdiction_statement(
                basis="MCR 7.203(A) — appeal of right from final order",
                lower_court_order_date=engine.get_order_date(lower_court_case),
                claim_of_appeal_date=engine.get_claim_date(coa_case_number),
            ),
            # MCR 7.212(C)(5): statement of questions presented
            "questions_presented": [
                QuestionPresented(
                    question=iss["question"],
                    answer_below=iss["answer_below"],
                    preservation_cite=iss["preservation_cite"],
                )
                for iss in issues_on_appeal
            ],
            # MCR 7.212(C)(6): statement of facts
            "statement_of_facts": engine.draft_facts(
                record_excerpts=record_excerpts,
                # MCR 7.212(C)(7): citations to lower court record
                citation_format="lower_court_record",
            ),
            # MCR 7.212(C)(7): argument
            "argument": engine.draft_arguments(issues_on_appeal),
            # MCR 7.212(C)(8): relief requested
            "relief_requested": engine.draft_relief(issues_on_appeal),
        },
    )

    # Validate format compliance
    engine.validate_brief(brief, rules=["MCR 7.212"])
    return brief
```

### Pattern 2: Standard of Review Selection

```python
from legal_ai.engines import AppealBriefEngine

def select_standard_of_review(issue_type: str, details: dict) -> dict:
    """Select and apply the correct appellate standard of review."""
    engine = AppealBriefEngine()

    standards = {
        "legal_question": {
            "standard": "De Novo",
            "description": "Questions of law are reviewed de novo on appeal.",
            "citation": "Maldonado v Ford Motor Co, 476 Mich 372, 388 (2006)",
            "deference": "None — appellate court decides independently",
        },
        "factual_finding": {
            "standard": "Clear Error",
            "description": (
                "Findings of fact are reviewed for clear error. "
                "A finding is clearly erroneous when the reviewing court "
                "is left with a definite and firm conviction that a mistake "
                "was made."
            ),
            "citation": "In re BZ, 264 Mich App 286, 296 (2004)",
            "deference": "High — reversal only if definitely wrong",
        },
        "discretionary_ruling": {
            "standard": "Abuse of Discretion",
            "description": (
                "Discretionary decisions are reviewed for abuse of discretion. "
                "An abuse of discretion occurs when the trial court's decision "
                "falls outside the range of principled outcomes."
            ),
            "citation": "Maldonado v Ford Motor Co, 476 Mich 372, 388 (2006)",
            "deference": "Substantial — must be outside range of reasonable outcomes",
        },
        "custody_best_interest": {
            "standard": "Great Weight / Clear Error",
            "description": (
                "Custody best-interest findings reviewed under great weight "
                "standard per MCL 722.28. Findings of fact: clear error. "
                "Discretionary decisions: abuse of discretion."
            ),
            "citation": "Vodvarka v Grasmeyer, 259 Mich App 499, 507 (2003)",
            "deference": "Very high — affirm unless against great weight of evidence",
        },
        "unpreserved_error": {
            "standard": "Plain Error",
            "description": (
                "Unpreserved issues reviewed for plain error affecting "
                "substantial rights. Must show: (1) error occurred, "
                "(2) error was plain, (3) error affected substantial rights."
            ),
            "citation": "Kern v Blethen-Coluni, 240 Mich App 333, 336 (2000)",
            "deference": "Maximum — reversal only for serious injustice",
        },
    }

    selected = standards.get(issue_type, standards["discretionary_ruling"])
    return {
        **selected,
        "issue_type": issue_type,
        "application": engine.apply_standard(selected["standard"], details),
    }
```

### Pattern 3: Issue Preservation Analysis

```python
from legal_ai.engines import AppealBriefEngine

def analyze_issue_preservation(
    issue: str,
    lower_court_record: list[dict],
) -> dict:
    """Determine whether an issue was properly preserved for appeal."""
    engine = AppealBriefEngine()

    # Search lower court record for issue-related filings/objections
    preservation_evidence = engine.search_record(
        record=lower_court_record,
        search_terms=engine.extract_key_terms(issue),
    )

    analysis = {
        "issue": issue,
        "preserved": False,
        "preservation_type": None,
        "record_citations": [],
        "standard_if_unpreserved": "Plain Error",
    }

    for evidence in preservation_evidence:
        if evidence["type"] == "objection":
            analysis["preserved"] = True
            analysis["preservation_type"] = "timely_objection"
            analysis["record_citations"].append(
                f"(Tr vol {evidence['volume']}, p {evidence['page']})"
            )
        elif evidence["type"] == "motion":
            analysis["preserved"] = True
            analysis["preservation_type"] = "written_motion"
            analysis["record_citations"].append(
                f"(Lower Ct File, p {evidence['page']})"
            )
        elif evidence["type"] == "brief_argument":
            analysis["preserved"] = True
            analysis["preservation_type"] = "briefed_below"
            analysis["record_citations"].append(
                f"(Lower Ct File, p {evidence['page']})"
            )

    if not analysis["preserved"]:
        analysis["recommendation"] = (
            "Argue plain error under Kern v Blethen-Coluni, "
            "240 Mich App 333, 336 (2000), or request that the Court "
            "address in the interest of justice."
        )

    return analysis
```

### Pattern 4: Appendix Preparation (MCR 7.212(G))

```python
from legal_ai.engines import AppealBriefEngine

def prepare_appendix(
    coa_case_number: str,
    lower_court_case: str,
    appealed_order: dict,
    key_exhibits: list[dict],
) -> dict:
    """Prepare MCR 7.212(G) required appendix."""
    engine = AppealBriefEngine()

    # MCR 7.212(G): Required appendix contents
    appendix = {
        "required_documents": [
            {
                "tab": "A",
                "description": "Judgment or Order Appealed From",
                "document": appealed_order,
                "required_by": "MCR 7.212(G)(1)",
            },
            {
                "tab": "B",
                "description": "Relevant Docket Entries",
                "document": engine.get_docket_entries(lower_court_case),
                "required_by": "MCR 7.212(G)(2)",
            },
        ],
        "discretionary_documents": [],
    }

    # Add key transcript excerpts and exhibits
    for i, exhibit in enumerate(key_exhibits):
        appendix["discretionary_documents"].append({
            "tab": chr(67 + i),  # C, D, E, ...
            "description": exhibit["description"],
            "document": exhibit,
            "referenced_in_brief": exhibit.get("brief_page"),
        })

    # Validate appendix completeness
    engine.validate_appendix(appendix, rules=["MCR 7.212(G)"])

    return appendix
```

## Anti-Patterns

### Anti-Pattern 1: Record Citations Without Proper Format
```python
# WRONG — Vague or missing record citations
brief.argument += "The trial court erred when it excluded the evidence."

# CORRECT — MCR 7.212(C)(7) requires specific record citations
brief.argument += (
    "The trial court erred when it excluded the CPS report. "
    "(Tr vol II, pp 47-49; Lower Ct File, p 234.)"
)
```

### Anti-Pattern 2: Raising Unpreserved Issues Without Plain Error Analysis
```python
# WRONG — Arguing unpreserved issue as if fully preserved
argue_issue("trial court applied wrong standard", standard="de novo")

# CORRECT — Acknowledge preservation status and argue plain error
argue_issue(
    "trial court applied wrong standard",
    preserved=False,
    standard="plain_error",
    plain_error_showing={
        "error_occurred": True,
        "error_plain": True,
        "substantial_rights_affected": True,
    },
)
```

### Anti-Pattern 3: Exceeding Page Limits
```python
# WRONG — 75-page brief (MCR 7.212(B) limits to 50 pages)
brief.compile()  # 75 pages — will be rejected

# CORRECT — Monitor page count and trim or request leave to exceed
if brief.page_count > 50:
    brief.trim_to_limit(max_pages=50)
    # Or file motion for leave to exceed page limit per MCR 7.212(B)
```

### Anti-Pattern 4: Wrong Standard of Review
```python
# WRONG — Applying de novo to custody best-interest findings
issue.standard_of_review = "de novo"

# CORRECT — MCL 722.28: custody findings get great weight
issue.standard_of_review = "great_weight"
issue.citation = "Vodvarka v Grasmeyer, 259 Mich App 499 (2003)"
```

## Michigan-Specific Rules

| Rule | Subject | Key Requirement |
|------|---------|-----------------|
| **MCR 7.204** | Claim of appeal | Filed within 21 days of order; 42 days for post-judgment motion |
| **MCR 7.205** | Application for leave | 21-day deadline; supporting brief required |
| **MCR 7.212** | Briefs format | TOC, authority index, jurisdiction, questions, facts, argument |
| **MCR 7.212(B)** | Page limits | 50 pages max; 12-point proportional font |
| **MCR 7.212(C)(5)** | Questions presented | Must be concise and outcome-determinative |
| **MCR 7.212(C)(7)** | Record citations | "(Tr vol X, p Y)" or "(Lower Ct File, p Y)" format |
| **MCR 7.212(G)** | Appendix | Must include appealed order and relevant docket entries |
| **MCR 7.215** | Opinions and orders | Published vs. unpublished opinion standards |
| **MCR 7.302** | Application to MSC | 56-day deadline from COA decision |
| **MCR 7.216** | Motions in COA | Motion practice during pendency of appeal |
| **MCL 722.28** | Custody appeal standard | Great weight to trial court's best-interest findings |

### Filing Timeline (Appeal of Right — MCR 7.204)
| Step | Deadline | Rule |
|------|----------|------|
| Claim of appeal | 21 days from order (42 if post-judgment motion) | MCR 7.204(A) |
| Order transcripts | 14 days from claim | MCR 7.210(B) |
| Appellant's brief | 56 days from claim (or transcript filing) | MCR 7.212(A)(1) |
| Appellee's brief | 35 days from service of appellant's brief | MCR 7.212(A)(2) |
| Reply brief (optional) | 21 days from service of appellee's brief | MCR 7.212(A)(3) |

### Standards of Review Quick Reference
| Issue Type | Standard | Deference Level |
|-----------|----------|-----------------|
| Questions of law | De novo | None |
| Findings of fact | Clear error | High |
| Discretionary rulings | Abuse of discretion | Substantial |
| Custody best-interest | Great weight | Very high |
| Unpreserved issues | Plain error | Maximum |

## Integration Points

- **litigation-appellate-strategist**: Provides strategic issue selection and framing
- **litigation-record-builder**: Assembles the lower court record for citations
- **litigation-brief-writer**: Core brief writing patterns and persuasion techniques
- **litigation-authority-validator**: Validates all case citations are current
- **litigation-filing-architect**: Formats for COA e-filing requirements
- **litigation-judicial-analyst**: Analyzes appellate panel tendencies
- **litigation-timeline-forensics**: Identifies timeline entries for statement of facts
- **litigation-evidence-harvester**: Sources exhibits for appendix preparation


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
