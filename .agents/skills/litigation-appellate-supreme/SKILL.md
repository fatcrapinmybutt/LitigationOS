---
name: litigation-appellate-supreme
description: "Use when handling appellate matters — appeal briefs, standards of review, record preparation, claim of appeal, MSC applications, void judgments, judicial recusal, trial preparation for appeal preservation, venue transfer, and jury instructions. Michigan COA/MSC focused (Pigors v Watson, COA 366810)."
category: discipline
version: "2.0.0"
triggers:
  - appeal
  - appellate
  - COA
  - MSC
  - standard of review
  - claim of appeal
  - brief
  - void judgment
  - recusal
  - disqualification
  - MCR 7.200
  - MCR 7.300
lanes:
  - "A: Watson/Custody (2024-001507-DC)"
  - "B: Shady Oaks/Housing (2025-002760-CZ)"
  - "C: Federal §1983 (USDC WDMI)"
  - "D: PPO (2023-5907-PP)"
  - "E: Judicial Misconduct/JTC"
  - "F: Appellate (COA 366810)"
court: "14th Judicial Circuit, Muskegon County; Michigan COA; Michigan Supreme Court"
case: Pigors v Watson
dependencies: []
metadata:
  model: opus
  forged_from: 10
  forge_date: 2026-03-12
---

# LITIGATION-APPELLATE-SUPREME — Elite Composite Skill

> Forged from 10 individual skills into one supreme composite.
> Sources: litigation-appellate-strategist, litigation-appellate-record-specialist, litigation-appeal-brief-engine, litigation-supreme-court-architect, litigation-void-judgment-engine, litigation-judicial-analyst, litigation-judicial-recusal-engine, litigation-trial-preparation-specialist, litigation-venue-transfer-specialist, litigation-jury-instruction-engine

## When to Apply

Activate this skill for ANY work related to:
- **Appellate Strategy**: appeal timing, standard of review, issue preservation, MCR 7.200
- **Record Preparation**: lower court record, transcript ordering, appendix assembly, MCR 7.210
- **Appeal Brief Writing**: statement of questions, statement of facts, argument structure, MCR 7.212
- **Supreme Court Architecture**: application for leave, jurisdiction, MSC rules, MCR 7.300
- **Void Judgment Engine**: void vs voidable, MCR 2.612, collateral attack, due process violations
- **Judicial Analysis**: judge profiling, ruling patterns, bias detection, reversal rates
- **Recusal Engine**: MCR 2.003 disqualification, grounds, procedure, mandamus
- **Trial Preparation**: trial strategy, exhibit preparation, witness order, jury instructions
- **Venue Transfer**: MCR 2.222, forum non conveniens, transfer motions
- **Michigan Appellate Quick Reference**: consolidated MCR 7.xxx citations

---

## §1. Appellate Strategy

> appeal timing, standard of review, issue preservation, MCR 7.200

### Standards of Review
*Source: litigation-appellate-strategist*

| Standard | Applies To | Burden | Key Language |
|----------|-----------|--------|--------------|
| **De novo** | Questions of law, statutory interpretation, constitutional issues | No deference to trial court | "We review de novo..." |
| **Clear error** | Findings of fact (MCR 2.613(C)) | Definite and firm conviction of mistake | "A finding is clearly erroneous when..." |
| **Abuse of discretion** | Discretionary rulings (custody, evidentiary, discovery) | Outcome outside range of principled outcomes | "An abuse of discretion occurs when..." |
| **Great weight** | Custody best-interest findings (MCL 722.28) | Even greater deference than clear error | "Affirm unless the evidence clearly preponderates..." |
| **Plain error** | Unpreserved issues | Affects substantial rights, manifest injustice | "Plain error affecting substantial rights..." |

### Lane-Specific Standard of Review Map

**Lane A: Watson/Custody**
| Issue | Standard |
|-------|----------|
| Best interest factor findings | Great weight (MCL 722.28) |
| Change of established custodial environment | Clear error |
| Proper cause / change of circumstances | Clear error |
| PPO issuance/modification | Abuse of discretion |
| Evidentiary rulings | Abuse of discretion |
| Statutory interpretation | De novo |

**Lane B: Shady Oaks/Housing**
| Issue | Standard |
|-------|----------|
| Summary disposition ruling | De novo |
| Contract interpretation | De novo |
| Damage calculation | Clear error |
| Discovery rulings | Abuse of discretion |
| Warranty of habitability | De novo |

---

### Issue Preservation Audit
*Source: litigation-appellate-strategist*

```
FOR EACH potential appellate issue:
  1. Was the issue raised in the trial court? [Y/N]
  2. Was a specific objection made on the record? [Y/N]
  3. Was the trial court given opportunity to rule? [Y/N]
  4. Was the ruling adverse? [Y/N]
  5. Was a motion for reconsideration filed? [Y/N]
  6. Is the issue jurisdictional (preserved automatically)? [Y/N]

  IF all YES → FULLY PRESERVED → include in appeal
  IF any NO  → PARTIALLY PRESERVED → evaluate plain error
  IF multiple NO → LIKELY WAIVED → do not include unless plain error
```

---

### Michigan Code of Judicial Conduct — Complete Canon Analysis
*Source: litigation-judicial-analyst*

### Canon 1: Integrity and Independence of the Judiciary
A judge shall uphold the integrity and independence of the judiciary.

| Violation Pattern | Indicator | Evidence Source | Severity |
|------------------|-----------|-----------------|----------|
| Undermining public confidence | Arbitrary rulings without legal basis | Order analysis vs. governing law | 7-8 |
| External influence susceptibility | Ruling patterns correlating with FOC recommendations despite errors | Docket timing analysis | 6-7 |
| Appearance of impropriety | Personal relationships with parties/counsel | Public records, disclosure filings | 8-9 |

### Canon 2: Avoiding Impropriety and Its Appearance
A judge shall avoid impropriety and the appearance of impropriety in all activities.

| Violation Pattern | Indicator | Evidence Source | Severity |
|------------------|-----------|-----------------|----------|
| 2(A): Conduct raising reasonable question | Pattern of one-sided rulings | Statistical ruling analysis | 6-8 |
| 2(B): Lending prestige of office | Using judicial authority to advance private interests | Public records | 7-9 |
| 2(C): Testifying as character witness | Voluntarily testifying or providing references | Court records | 5-6 |

### Canon 3: Performing Duties Impartially and Diligently
A judge shall perform the duties of judicial office impartially and diligently.

| Sub-Rule | Violation Pattern | McNeill Evidence | Severity |
|----------|------------------|------------------|----------|
| 3(A)(1): Faithful to law | Rulings contradicting governing MCR/MCL | Order text vs. statute analysis | 8-9 |
| 3(A)(3): Patient, dignified, courteous | Hostile treatment of pro se party on the record | Transcript excerpts | 6-8 |
| 3(A)(4): No ex parte communications | **267 documented violations** — orders without notice, off-record conversations, sealed proceedings | Docket analysis, order timing | 9-10 |
| 3(B)(5): No bias on protected characteristics | Differential treatment of parties | Comparative ruling analysis | 7-8 |
| 3(B)(7): Recusal when impartiality questioned | Refusal to recuse despite documented bias | Recusal motion history | 8-9 |

### Canon 4: Extra-Judicial Activities
A judge shall conduct extra-judicial activities so as not to cast doubt on impartiality.

| Violation Pattern | Indicator | Evidence Source | Severity |
|------------------|-----------|-----------------|----------|
| 4(A): Activities casting doubt | Community connections creating conflicts | Public records | 5-7 |
| 4(D): Financial conflicts | Financial interests in case outcomes | Disclosure filings | 7-9 |

### Canon 5: Political Activity
A judge shall refrain from inappropriate political activity.

| Violation Pattern | Indicator | Evidence Source | Severity |
|------------------|-----------|-----------------|----------|
| 5(A)(1): Political organization leadership | Active political involvement | Public records, campaign filings | 5-7 |
| 5(C)(1): Campaign conduct | Endorsements or quid pro quo indicators | Campaign records, public statements | 6-8 |

### Canon 6: Compliance with the Code
A judge shall comply with this Code and should report violations by other judges.

| Violation Pattern | Indicator | Evidence Source | Severity |
|------------------|-----------|-----------------|----------|
| Failure to self-report | Knowledge of own violations without correction | Pattern analysis | 7-8 |
| Failure to report others | Knowledge of other judges' violations | Cross-case analysis | 5-6 |

### Canon 7: A Judge or Candidate for Judicial Office
(Applies primarily during campaigns; less relevant to sitting judge conduct analysis.)

---

### MCR 2.003 — Disqualification Standards and Motion Template
*Source: litigation-judicial-analyst*

### Grounds for Disqualification (MCR 2.003(C)(1))
| Ground | MCR Section | Standard | McNeill Application |
|--------|-------------|----------|---------------------|
| Personal bias or prejudice | (C)(1)(a) | Bias toward a party or attorney | 377 documented violations showing pattern |
| Personal knowledge of disputed facts | (C)(1)(b) | Judge has extra-judicial knowledge | Ex parte communications (267 instances) |
| Prior involvement | (C)(1)(c) | Previously involved as lawyer/witness/judge | N/A for current analysis |
| Financial interest | (C)(1)(d) | Direct or indirect financial interest | Check disclosure filings |
| Related to party/attorney | (C)(1)(e) | Within third degree of relationship | Investigate community connections |
| **Catch-all** | **(C)(1)(b)** | **Impartiality might reasonably be questioned** | **44% ex parte order rate + 329+ day separation** |

### MCR 2.003(D) — Procedure
1. **Motion must be filed**: In writing, specifying grounds with particularity
2. **Affidavit required**: Setting forth facts supporting disqualification
3. **Timeliness**: File promptly after discovering grounds (no specific deadline in MCR, but unreasonable delay = waiver argument)
4. **Judge rules on own motion**: The challenged judge decides the motion (MCR 2.003(D)(3)(a))
5. **If denied**: Seek immediate review via MCR 7.203(A) (application for leave)
6. **Peremptory disqualification**: MCR 2.003(B) — one automatic disqualification per side per case (file BEFORE any substantive proceeding)

### Disqualification Motion Template
```
MOTION FOR DISQUALIFICATION OF JUDGE [NAME]

I. GROUNDS
This motion is brought pursuant to MCR 2.003(C)(1)(a) and (b), on the
grounds that [Judge]'s impartiality might reasonably be questioned based on:

1. [Specific bias instance with date and record citation]
2. [Pattern evidence — number of violations, dates, citations]
3. [Ex parte communication evidence with dates]
4. [Cumulative impact — 329+ days separation, outcome]

II. SUPPORTING AUTHORITY
[IRAC analysis citing MCR 2.003, In re Contempt of Henry, Crampton v Dep't
of State, and other Michigan disqualification case law]

III. RELIEF REQUESTED
WHEREFORE, [Party] respectfully requests that [Judge] be disqualified from
further proceedings in this matter and the case be reassigned.

[Attached: Affidavit of Bias with specific facts]
[Attached: Exhibit Index documenting violations]
```

---

## §2. Record Preparation

> lower court record, transcript ordering, appendix assembly, MCR 7.210

### Record Designation Protocol (MCR 7.210)
*Source: litigation-appellate-strategist*

### Required Record Components
```
1. Register of actions
2. All original papers filed in the trial court
3. Transcripts of all proceedings (or settled statement)
4. All exhibits admitted or offered and refused
5. Jury instructions (if applicable)
6. Verdict form (if applicable)
```

### Record Designation Checklist

```yaml
record_designation:
  lower_court_file:
    - register_of_actions: boolean
    - complaint_and_amendments: boolean
    - answer_and_amendments: boolean
    - all_motions_and_responses: boolean
    - all_court_orders: boolean
    - final_judgment_or_order: boolean
  transcripts:
    - all_hearings: boolean
    - specific_hearings: list[date_and_description]
    - transcript_ordered_date: ISO-8601
    - transcript_due_date: ISO-8601
    - court_reporter_name: string
  exhibits:
    - plaintiff_exhibits: list[exhibit_id]
    - defendant_exhibits: list[exhibit_id]
    - admitted_exhibits: list[exhibit_id]
    - refused_exhibits: list[exhibit_id]
  supplemental:
    - deposition_transcripts: list[deponent_name]
    - discovery_responses: list[description]
```

---

## §3. Appeal Brief Writing

> statement of questions, statement of facts, argument structure, MCR 7.212

### Standards of Review
*Source: litigation-appellate-strategist*

| Standard | Applies To | Burden | Key Language |
|----------|-----------|--------|--------------|
| **De novo** | Questions of law, statutory interpretation, constitutional issues | No deference to trial court | "We review de novo..." |
| **Clear error** | Findings of fact (MCR 2.613(C)) | Definite and firm conviction of mistake | "A finding is clearly erroneous when..." |
| **Abuse of discretion** | Discretionary rulings (custody, evidentiary, discovery) | Outcome outside range of principled outcomes | "An abuse of discretion occurs when..." |
| **Great weight** | Custody best-interest findings (MCL 722.28) | Even greater deference than clear error | "Affirm unless the evidence clearly preponderates..." |
| **Plain error** | Unpreserved issues | Affects substantial rights, manifest injustice | "Plain error affecting substantial rights..." |

### Lane-Specific Standard of Review Map

**Lane A: Watson/Custody**
| Issue | Standard |
|-------|----------|
| Best interest factor findings | Great weight (MCL 722.28) |
| Change of established custodial environment | Clear error |
| Proper cause / change of circumstances | Clear error |
| PPO issuance/modification | Abuse of discretion |
| Evidentiary rulings | Abuse of discretion |
| Statutory interpretation | De novo |

**Lane B: Shady Oaks/Housing**
| Issue | Standard |
|-------|----------|
| Summary disposition ruling | De novo |
| Contract interpretation | De novo |
| Damage calculation | Clear error |
| Discovery rulings | Abuse of discretion |
| Warranty of habitability | De novo |

---

### Michigan Code of Judicial Conduct — Complete Canon Analysis
*Source: litigation-judicial-analyst*

### Canon 1: Integrity and Independence of the Judiciary
A judge shall uphold the integrity and independence of the judiciary.

| Violation Pattern | Indicator | Evidence Source | Severity |
|------------------|-----------|-----------------|----------|
| Undermining public confidence | Arbitrary rulings without legal basis | Order analysis vs. governing law | 7-8 |
| External influence susceptibility | Ruling patterns correlating with FOC recommendations despite errors | Docket timing analysis | 6-7 |
| Appearance of impropriety | Personal relationships with parties/counsel | Public records, disclosure filings | 8-9 |

### Canon 2: Avoiding Impropriety and Its Appearance
A judge shall avoid impropriety and the appearance of impropriety in all activities.

| Violation Pattern | Indicator | Evidence Source | Severity |
|------------------|-----------|-----------------|----------|
| 2(A): Conduct raising reasonable question | Pattern of one-sided rulings | Statistical ruling analysis | 6-8 |
| 2(B): Lending prestige of office | Using judicial authority to advance private interests | Public records | 7-9 |
| 2(C): Testifying as character witness | Voluntarily testifying or providing references | Court records | 5-6 |

### Canon 3: Performing Duties Impartially and Diligently
A judge shall perform the duties of judicial office impartially and diligently.

| Sub-Rule | Violation Pattern | McNeill Evidence | Severity |
|----------|------------------|------------------|----------|
| 3(A)(1): Faithful to law | Rulings contradicting governing MCR/MCL | Order text vs. statute analysis | 8-9 |
| 3(A)(3): Patient, dignified, courteous | Hostile treatment of pro se party on the record | Transcript excerpts | 6-8 |
| 3(A)(4): No ex parte communications | **267 documented violations** — orders without notice, off-record conversations, sealed proceedings | Docket analysis, order timing | 9-10 |
| 3(B)(5): No bias on protected characteristics | Differential treatment of parties | Comparative ruling analysis | 7-8 |
| 3(B)(7): Recusal when impartiality questioned | Refusal to recuse despite documented bias | Recusal motion history | 8-9 |

### Canon 4: Extra-Judicial Activities
A judge shall conduct extra-judicial activities so as not to cast doubt on impartiality.

| Violation Pattern | Indicator | Evidence Source | Severity |
|------------------|-----------|-----------------|----------|
| 4(A): Activities casting doubt | Community connections creating conflicts | Public records | 5-7 |
| 4(D): Financial conflicts | Financial interests in case outcomes | Disclosure filings | 7-9 |

### Canon 5: Political Activity
A judge shall refrain from inappropriate political activity.

| Violation Pattern | Indicator | Evidence Source | Severity |
|------------------|-----------|-----------------|----------|
| 5(A)(1): Political organization leadership | Active political involvement | Public records, campaign filings | 5-7 |
| 5(C)(1): Campaign conduct | Endorsements or quid pro quo indicators | Campaign records, public statements | 6-8 |

### Canon 6: Compliance with the Code
A judge shall comply with this Code and should report violations by other judges.

| Violation Pattern | Indicator | Evidence Source | Severity |
|------------------|-----------|-----------------|----------|
| Failure to self-report | Knowledge of own violations without correction | Pattern analysis | 7-8 |
| Failure to report others | Knowledge of other judges' violations | Cross-case analysis | 5-6 |

### Canon 7: A Judge or Candidate for Judicial Office
(Applies primarily during campaigns; less relevant to sitting judge conduct analysis.)

---

### MCR 2.003 — Disqualification Standards and Motion Template
*Source: litigation-judicial-analyst*

### Grounds for Disqualification (MCR 2.003(C)(1))
| Ground | MCR Section | Standard | McNeill Application |
|--------|-------------|----------|---------------------|
| Personal bias or prejudice | (C)(1)(a) | Bias toward a party or attorney | 377 documented violations showing pattern |
| Personal knowledge of disputed facts | (C)(1)(b) | Judge has extra-judicial knowledge | Ex parte communications (267 instances) |
| Prior involvement | (C)(1)(c) | Previously involved as lawyer/witness/judge | N/A for current analysis |
| Financial interest | (C)(1)(d) | Direct or indirect financial interest | Check disclosure filings |
| Related to party/attorney | (C)(1)(e) | Within third degree of relationship | Investigate community connections |
| **Catch-all** | **(C)(1)(b)** | **Impartiality might reasonably be questioned** | **44% ex parte order rate + 329+ day separation** |

### MCR 2.003(D) — Procedure
1. **Motion must be filed**: In writing, specifying grounds with particularity
2. **Affidavit required**: Setting forth facts supporting disqualification
3. **Timeliness**: File promptly after discovering grounds (no specific deadline in MCR, but unreasonable delay = waiver argument)
4. **Judge rules on own motion**: The challenged judge decides the motion (MCR 2.003(D)(3)(a))
5. **If denied**: Seek immediate review via MCR 7.203(A) (application for leave)
6. **Peremptory disqualification**: MCR 2.003(B) — one automatic disqualification per side per case (file BEFORE any substantive proceeding)

### Disqualification Motion Template
```
MOTION FOR DISQUALIFICATION OF JUDGE [NAME]

I. GROUNDS
This motion is brought pursuant to MCR 2.003(C)(1)(a) and (b), on the
grounds that [Judge]'s impartiality might reasonably be questioned based on:

1. [Specific bias instance with date and record citation]
2. [Pattern evidence — number of violations, dates, citations]
3. [Ex parte communication evidence with dates]
4. [Cumulative impact — 329+ days separation, outcome]

II. SUPPORTING AUTHORITY
[IRAC analysis citing MCR 2.003, In re Contempt of Henry, Crampton v Dep't
of State, and other Michigan disqualification case law]

III. RELIEF REQUESTED
WHEREFORE, [Party] respectfully requests that [Judge] be disqualified from
further proceedings in this matter and the case be reassigned.

[Attached: Affidavit of Bias with specific facts]
[Attached: Exhibit Index documenting violations]
```

---

## §4. Supreme Court Architecture

> application for leave, jurisdiction, MSC rules, MCR 7.300

### IRON LAWS — MSC PRACTICE
*Source: litigation-supreme-court-architect*

```
1. JURISDICTION FIRST — Confirm MSC has jurisdiction before drafting anything.
2. GROUNDS OR DEATH — Every application MUST articulate MCR 7.305(B) grounds.
3. 56-DAY WALL — Application for leave must be filed within 56 days of COA
   decision or order. MCR 7.305(C)(2). NO automatic extensions.
4. RECORD IS KING — MSC decides on the record below. If it is not in the
   record, it does not exist.
5. COPY COUNTS MATTER — File original + 1 signed copy + sufficient copies
   for all parties. MCR 7.302(B).
6. SERVICE IS JURISDICTIONAL — Failure to serve = failure to file.
   MCR 7.302(E), MCR 2.107.
7. FEE OR WAIVER — $375 filing fee OR MC 20 fee waiver MUST accompany filing.
8. FORMAT COMPLIANCE — MCR 7.212(C) formatting applies. Violations = rejection.
9. QUESTION PRESENTED CONTROLS — MSC grants leave on QUESTIONS, not cases.
   Frame questions precisely.
10. LESS IS MORE — Fewer, stronger issues > many weak ones at MSC level.
```

---

### Michigan-Specific Rules
*Source: litigation-appeal-brief-engine*

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

### MSC Application Criteria (MCR 7.305(B))
*Source: litigation-appellate-strategist*

An application for leave to appeal to the Michigan Supreme Court should be
pursued ONLY when:

1. **COA panel conflict**: Different COA panels reached conflicting results
2. **Significant public interest**: Issue affects many beyond this case
3. **Constitutional question**: Substantial constitutional issue involved
4. **Clear legal error**: COA misapplied settled law
5. **Developing area**: Law is unsettled and MSC guidance needed

Do NOT pursue MSC application merely because the COA ruling was unfavorable.

## §5. Void Judgment Engine

> void vs voidable, MCR 2.612, collateral attack, due process violations

### MCR 2.003 — Disqualification Standards and Motion Template
*Source: litigation-judicial-analyst*

### Grounds for Disqualification (MCR 2.003(C)(1))
| Ground | MCR Section | Standard | McNeill Application |
|--------|-------------|----------|---------------------|
| Personal bias or prejudice | (C)(1)(a) | Bias toward a party or attorney | 377 documented violations showing pattern |
| Personal knowledge of disputed facts | (C)(1)(b) | Judge has extra-judicial knowledge | Ex parte communications (267 instances) |
| Prior involvement | (C)(1)(c) | Previously involved as lawyer/witness/judge | N/A for current analysis |
| Financial interest | (C)(1)(d) | Direct or indirect financial interest | Check disclosure filings |
| Related to party/attorney | (C)(1)(e) | Within third degree of relationship | Investigate community connections |
| **Catch-all** | **(C)(1)(b)** | **Impartiality might reasonably be questioned** | **44% ex parte order rate + 329+ day separation** |

### MCR 2.003(D) — Procedure
1. **Motion must be filed**: In writing, specifying grounds with particularity
2. **Affidavit required**: Setting forth facts supporting disqualification
3. **Timeliness**: File promptly after discovering grounds (no specific deadline in MCR, but unreasonable delay = waiver argument)
4. **Judge rules on own motion**: The challenged judge decides the motion (MCR 2.003(D)(3)(a))
5. **If denied**: Seek immediate review via MCR 7.203(A) (application for leave)
6. **Peremptory disqualification**: MCR 2.003(B) — one automatic disqualification per side per case (file BEFORE any substantive proceeding)

### Disqualification Motion Template
```
MOTION FOR DISQUALIFICATION OF JUDGE [NAME]

I. GROUNDS
This motion is brought pursuant to MCR 2.003(C)(1)(a) and (b), on the
grounds that [Judge]'s impartiality might reasonably be questioned based on:

1. [Specific bias instance with date and record citation]
2. [Pattern evidence — number of violations, dates, citations]
3. [Ex parte communication evidence with dates]
4. [Cumulative impact — 329+ days separation, outcome]

II. SUPPORTING AUTHORITY
[IRAC analysis citing MCR 2.003, In re Contempt of Henry, Crampton v Dep't
of State, and other Michigan disqualification case law]

III. RELIEF REQUESTED
WHEREFORE, [Party] respectfully requests that [Judge] be disqualified from
further proceedings in this matter and the case be reassigned.

[Attached: Affidavit of Bias with specific facts]
[Attached: Exhibit Index documenting violations]
```

---

## §6. Judicial Analysis

> judge profiling, ruling patterns, bias detection, reversal rates

### Patterns
*Source: litigation-appeal-brief-engine*

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

*[...151 more lines in source]*

### Anti-Patterns
*Source: litigation-appeal-brief-engine*

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

### Patterns
*Source: litigation-void-judgment-engine*

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

*[...143 more lines in source]*

### Anti-Patterns
*Source: litigation-void-judgment-engine*

### ❌ Conflating Void and Voidable Judgments

**Why bad**: Arguing a voidable judgment is "void" destroys credibility. Void judgments arise from jurisdictional defects (no subject matter jurisdiction, no personal jurisdiction, disqualified judge). Voidable judgments arise from procedural errors within jurisdiction. The legal standards, time limits, and remedies are completely different. Courts harshly penalize conflation because it wastes judicial resources.

**Instead**: Use Pattern 1 (Void vs. Voidable Classification) rigorously. If the defect is procedural, file under MCR 2.612(C)(1)(a) (within 1 year) or appeal. If the defect is jurisdictional, file under MCR 2.612(C)(1)(d) (no time limit). Never call a voidable order "void."

### ❌ Missing the §1983 Federal Bypass When State Courts Refuse Relief

**Why bad**: If the state court refuses to vacate a void order, continuing to file motions in the same court that issued the void order is futile. State courts sometimes refuse to acknowledge their own jurisdictional failures. Exhausting state remedies without pivoting to federal court wastes time and allows ongoing harm.

**Instead**: After one good-faith attempt to vacate in state court, if denied, preserve the issue for appeal AND file a 42 USC §1983 action in federal court (W.D. Michigan). The §1983 claim targets the deprivation of constitutional rights (parental liberty interest) under color of state law. Federal courts have independent jurisdiction to declare state court orders void for constitutional violations.

### ❌ Filing MCR 2.612 Motion Without Addressing Laches

**Why bad**: Even though void judgments have no statutory time limit, Michigan courts apply the equitable doctrine of laches if you unreasonably delayed raising the challenge. Opposing counsel will argue "you knew about this defect for X months/years and did nothing."

**Instead**: Address laches preemptively in every MCR 2.612(C)(1)(d) motion. Explain when the jurisdictional defect was discovered, what diligent steps were taken since discovery, and why any delay was reasonable (e.g., pro se party, complex jurisdictional analysis, ongoing related proceedings).

### Judge Assignment Map
*Source: litigation-judicial-analyst*

| Judge | Lane(s) | Case Type | Case Number(s) |
|-------|---------|-----------|-----------------|
| McNeill | A | Custody / PPO | 2024-001507-DC, 2023-5907-PP |
| Hoopes | B | Housing / Civil | 2025-002760-CZ |
| Multiple | C | Convergence | Cross-lane |

### Bias Indicator Framework
*Source: litigation-judicial-analyst*

### Structural Bias Indicators
1. **Outcome disparity**: Statistically different ruling rates by party type
2. **Procedural asymmetry**: Different procedural treatment of similarly situated parties
3. **Temporal patterns**: Delayed rulings for one party, expedited for another
4. **Access disparity**: Hearing time, motion hearing scheduling differences
5. **Pro se penalty**: Harsher treatment of self-represented litigants

### Behavioral Bias Indicators
1. **Tone differential**: Different vocal tone / language toward parties
2. **Interruption asymmetry**: Interrupting one party more than another
3. **Credibility presumption**: Accepting one party's claims without scrutiny
4. **Sua sponte assistance**: Helping one party's case unprompted
5. **Hostile questioning**: Adversarial questioning of one party only

### Evidentiary Bias Indicators
1. **Selective admission**: Admitting weak evidence for one side, excluding strong for other
2. **Weight manipulation**: Giving disproportionate weight to certain evidence
3. **Burden shifting**: Improperly shifting burden of proof
4. **Inference drawing**: Drawing negative inferences against one party
5. **Record manipulation**: Off-record comments, sealed proceedings without cause

## §7. Recusal Engine

> MCR 2.003 disqualification, grounds, procedure, mandamus

### MCR 2.003 — Disqualification Framework
*Source: litigation-judicial-recusal-engine*

### MCR 2.003(C)(1) — Grounds for Disqualification

| Ground | MCR Section | Description | Evidence Type |
|--------|-------------|-------------|--------------|
| (a) Personal bias or prejudice | 2.003(C)(1)(a) | Judge has personal bias concerning a party | Statements, rulings pattern, ex parte contacts |
| (b) Personal knowledge of disputed facts | 2.003(C)(1)(b) | Judge has personal knowledge of disputed evidentiary facts | Prior involvement, personal observations |
| (c) Prior involvement as attorney | 2.003(C)(1)(c) | Judge served as attorney in the matter | Bar records, case docket review |
| (d) Financial interest | 2.003(C)(1)(d) | Judge has financial interest in controversy | Financial disclosures, property records |
| (e) Related to party or attorney | 2.003(C)(1)(e) | Within third degree of relationship | Family records |
| (f) Former associate of attorney | 2.003(C)(1)(f) | Judge and attorney were associated in practice | Bar association records |
| (g) Other grounds | 2.003(C)(1)(g) | Judge's conduct would create appearance of impropriety | Pattern of conduct |

### MCR 2.003(B) — Peremptory Disqualification

> Each party is entitled to ONE peremptory disqualification of the
> assigned judge as of right, without showing cause.

| Requirement | Detail |
|-------------|--------|
| **Timing** | Must be filed within 14 days of case assignment OR discovery of grounds |
| **Limit** | One per party per case |
| **No grounds required** | Simply file notice; no affidavit needed |
| **Effect** | Case reassigned to new judge |
| **Restriction** | Cannot be used after judge has ruled on contested matter |

> ⚠️ **CRITICAL**: The peremptory right is **lost** once the judge has made
> any ruling on a contested issue. Exercise early or lose it forever.

### MCR 2.003(D) — For-Cause Procedure

1. **File motion and affidavit** — Must include:
   - Specific facts demonstrating bias or disqualification ground
   - Sworn affidavit attesting to truth of facts
   - Legal argument connecting facts to MCR 2.003(C)(1) grounds

2. **Service** — Serve motion on all parties AND the judge.

3. **Referral to chief judge** — If challenged judge does not recuse:
   - Motion is referred to chief judge of the circuit (or designee)
   - Chief judge decides without evidentiary hearing (usually)
   - May order evidentiary hearing in rare cases

4. **Decision** — Chief judge grants or denies.

5. **Appellate review** — Denial is reviewable by COA under MCR 7.203(A).

### Appellate Review of Disqualification Denial
*Source: litigation-judicial-recusal-engine*

### MCR 7.203(A) — Appeal of Right

| Element | Detail |
|---------|--------|
| Basis | Denial of motion for disqualification |
| Filing deadline | 21 days from order denying disqualification |
| Court | Michigan Court of Appeals |
| Standard of review | Abuse of discretion |
| Interim relief | May seek stay of trial court proceedings |

### Mandamus as Alternative (MCR 7.206)

If ordinary appeal is inadequate, extraordinary writ of mandamus:

| Requirement | Standard |
|-------------|----------|
| No other adequate remedy | Appeal inadequate to protect rights |
| Clear legal right | Right to fair and impartial judge |
| Clear legal duty | Judge's duty to recuse when grounds exist |
| Irreparable harm | Prejudice from continued service cannot be undone |

### Judicial Disqualification Analysis — [Case Number]
*Source: litigation-judicial-recusal-engine*

### Judge: Hon. Jenny L. McNeill — 14th Circuit Court
### Bias Score: [X] — [Level]

| # | Date | Category | Description | MCR Ground | Severity |
|---|------|----------|-------------|------------|----------|
| 1 | [Date] | [Type] | [Description] | 2.003(C)(1)([x]) | [1-3] |

### Recommended Action
- [ ] Peremptory disqualification (if available)
- [ ] For-cause disqualification motion
- [ ] JTC complaint
- [ ] Appellate review

### Motion Draft Elements
1. [Factual basis with evidence refs]
2. [Legal argument with MCR citation]
```

### MCR 2.003 — Disqualification Standards and Motion Template
*Source: litigation-judicial-analyst*

### Grounds for Disqualification (MCR 2.003(C)(1))
| Ground | MCR Section | Standard | McNeill Application |
|--------|-------------|----------|---------------------|
| Personal bias or prejudice | (C)(1)(a) | Bias toward a party or attorney | 377 documented violations showing pattern |
| Personal knowledge of disputed facts | (C)(1)(b) | Judge has extra-judicial knowledge | Ex parte communications (267 instances) |
| Prior involvement | (C)(1)(c) | Previously involved as lawyer/witness/judge | N/A for current analysis |
| Financial interest | (C)(1)(d) | Direct or indirect financial interest | Check disclosure filings |
| Related to party/attorney | (C)(1)(e) | Within third degree of relationship | Investigate community connections |
| **Catch-all** | **(C)(1)(b)** | **Impartiality might reasonably be questioned** | **44% ex parte order rate + 329+ day separation** |

### MCR 2.003(D) — Procedure
1. **Motion must be filed**: In writing, specifying grounds with particularity
2. **Affidavit required**: Setting forth facts supporting disqualification
3. **Timeliness**: File promptly after discovering grounds (no specific deadline in MCR, but unreasonable delay = waiver argument)
4. **Judge rules on own motion**: The challenged judge decides the motion (MCR 2.003(D)(3)(a))
5. **If denied**: Seek immediate review via MCR 7.203(A) (application for leave)
6. **Peremptory disqualification**: MCR 2.003(B) — one automatic disqualification per side per case (file BEFORE any substantive proceeding)

### Disqualification Motion Template
```
MOTION FOR DISQUALIFICATION OF JUDGE [NAME]

I. GROUNDS
This motion is brought pursuant to MCR 2.003(C)(1)(a) and (b), on the
grounds that [Judge]'s impartiality might reasonably be questioned based on:

1. [Specific bias instance with date and record citation]
2. [Pattern evidence — number of violations, dates, citations]
3. [Ex parte communication evidence with dates]
4. [Cumulative impact — 329+ days separation, outcome]

II. SUPPORTING AUTHORITY
[IRAC analysis citing MCR 2.003, In re Contempt of Henry, Crampton v Dep't
of State, and other Michigan disqualification case law]

III. RELIEF REQUESTED
WHEREFORE, [Party] respectfully requests that [Judge] be disqualified from
further proceedings in this matter and the case be reassigned.

[Attached: Affidavit of Bias with specific facts]
[Attached: Exhibit Index documenting violations]
```

---

## §8. Trial Preparation

> trial strategy, exhibit preparation, witness order, jury instructions

### Michigan Rules — Jury Instructions
*Source: litigation-jury-instruction-engine*

### MCR 2.512 — Instructions to Jury

**(A) Request for Instructions:**
- Any party may file written requests for jury instructions
- Requests must be filed at the close of evidence or earlier if ordered
- Each instruction shall be on a separate sheet
- Instructions shall be numbered and identify the party requesting them

**(B) Objections:**
- Objections to instructions must be made before instructions are given
- Must state the matter objected to and the grounds for objection
- Failure to object waives the right to appellate review (absent manifest injustice)

**(C) Court's Duty:**
- Court must instruct the jury on applicable law
- Court must give M Civ JI when they are applicable, accurate, and pertinent
- Court may give additional instructions not covered by M Civ JI

### MCR 2.516 — Jury Verdicts

**(A) Return of Verdict:**
- Verdicts must be unanimous unless parties stipulate otherwise
- Verdict must be returned in open court

**(B) Special Verdicts:**
- Court may require a special verdict (specific factual findings)
- Court may use general verdict with interrogatories

**(C) Polling the Jury:**
- Either party may request the jury be polled
- Each juror asked individually whether the verdict is their verdict

## §9. Venue Transfer

> MCR 2.222, forum non conveniens, transfer motions

## §10. Michigan Appellate Quick Reference

> consolidated MCR 7.xxx citations

### MCR 2.003 — Disqualification Standards and Motion Template
*Source: litigation-judicial-analyst*

### Grounds for Disqualification (MCR 2.003(C)(1))
| Ground | MCR Section | Standard | McNeill Application |
|--------|-------------|----------|---------------------|
| Personal bias or prejudice | (C)(1)(a) | Bias toward a party or attorney | 377 documented violations showing pattern |
| Personal knowledge of disputed facts | (C)(1)(b) | Judge has extra-judicial knowledge | Ex parte communications (267 instances) |
| Prior involvement | (C)(1)(c) | Previously involved as lawyer/witness/judge | N/A for current analysis |
| Financial interest | (C)(1)(d) | Direct or indirect financial interest | Check disclosure filings |
| Related to party/attorney | (C)(1)(e) | Within third degree of relationship | Investigate community connections |
| **Catch-all** | **(C)(1)(b)** | **Impartiality might reasonably be questioned** | **44% ex parte order rate + 329+ day separation** |

### MCR 2.003(D) — Procedure
1. **Motion must be filed**: In writing, specifying grounds with particularity
2. **Affidavit required**: Setting forth facts supporting disqualification
3. **Timeliness**: File promptly after discovering grounds (no specific deadline in MCR, but unreasonable delay = waiver argument)
4. **Judge rules on own motion**: The challenged judge decides the motion (MCR 2.003(D)(3)(a))
5. **If denied**: Seek immediate review via MCR 7.203(A) (application for leave)
6. **Peremptory disqualification**: MCR 2.003(B) — one automatic disqualification per side per case (file BEFORE any substantive proceeding)

### Disqualification Motion Template
```
MOTION FOR DISQUALIFICATION OF JUDGE [NAME]

I. GROUNDS
This motion is brought pursuant to MCR 2.003(C)(1)(a) and (b), on the
grounds that [Judge]'s impartiality might reasonably be questioned based on:

1. [Specific bias instance with date and record citation]
2. [Pattern evidence — number of violations, dates, citations]
3. [Ex parte communication evidence with dates]
4. [Cumulative impact — 329+ days separation, outcome]

II. SUPPORTING AUTHORITY
[IRAC analysis citing MCR 2.003, In re Contempt of Henry, Crampton v Dep't
of State, and other Michigan disqualification case law]

III. RELIEF REQUESTED
WHEREFORE, [Party] respectfully requests that [Judge] be disqualified from
further proceedings in this matter and the case be reassigned.

[Attached: Affidavit of Bias with specific facts]
[Attached: Exhibit Index documenting violations]
```

---

## Michigan Legal Citations Index

### Michigan Court Rules (MCR)
- MCR 2.003
- MCR 2.003(B)
- MCR 2.003(C)(1)
- MCR 2.003(C)(1)(a)
- MCR 2.003(D)
- MCR 2.003(D)(3)(a)
- MCR 2.105
- MCR 2.107
- MCR 2.222
- MCR 2.222(A)
- MCR 2.223
- MCR 2.507
- MCR 2.507(A)
- MCR 2.507(D)
- MCR 2.507(G)
- MCR 2.509
- MCR 2.509(A)
- MCR 2.509(B)
- MCR 2.511
- MCR 2.512
- MCR 2.512(A)
- MCR 2.512(B)
- MCR 2.512(C)
- MCR 2.513
- MCR 2.514
- MCR 2.516
- MCR 2.516(B)
- MCR 2.517
- MCR 2.612
- MCR 2.612(C)(1)
- MCR 2.612(C)(1)(a)
- MCR 2.612(C)(1)(d)
- MCR 2.612(C)(1)(f)
- MCR 2.612(C)(2)
- MCR 2.613
- MCR 2.613(C)
- MCR 3.207
- MCR 7.201
- MCR 7.202(6)
- MCR 7.203
- MCR 7.203(A)
- MCR 7.204
- MCR 7.204(A)
- MCR 7.204(D)
- MCR 7.205
- MCR 7.205(F)
- MCR 7.206
- MCR 7.210
- MCR 7.210(A)
- MCR 7.210(B)
- MCR 7.210(B)(1)
- MCR 7.210(B)(3)
- MCR 7.210(H)
- MCR 7.212
- MCR 7.212(A)
- MCR 7.212(A)(1)
- MCR 7.212(A)(2)
- MCR 7.212(A)(3)
- MCR 7.212(B)
- MCR 7.212(C)
- MCR 7.212(C)(1)
- MCR 7.212(C)(2)
- MCR 7.212(C)(3)
- MCR 7.212(C)(5)
- MCR 7.212(C)(6)
- MCR 7.212(C)(7)
- MCR 7.212(C)(8)
- MCR 7.212(G)
- MCR 7.212(G)(1)
- MCR 7.212(G)(2)
- MCR 7.215
- MCR 7.216
- MCR 7.300
- MCR 7.301
- MCR 7.302
- MCR 7.302(B)
- MCR 7.302(E)
- MCR 7.303
- MCR 7.305
- MCR 7.305(B)
- MCR 7.305(B)(1)
- MCR 7.305(B)(3)
- MCR 7.305(C)(2)
- MCR 7.305(D)
- MCR 7.306
- MCR 7.308
- MCR 7.309
- MCR 7.311
- MCR 8.119(H)
- MCR 9.104
- MCR 9.200
- MCR 9.220
- MCR 9.221
- MCR 9.223
- MCR 9.224
- MCR 9.225

### Michigan Compiled Laws (MCL)
- MCL 600.1428
- MCL 600.1601
- MCL 600.1605
- MCL 600.1611
- MCL 600.1615
- MCL 600.1621
- MCL 600.1629
- MCL 600.1641
- MCL 600.1651
- MCL 600.1655
- MCL 600.1701
- MCL 600.605
- MCL 600.611
- MCL 722.28


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
| MCR 2.119 | 1635 | 🆕 Verify & integrate |
| MCR 3.207(B) | 933 | 🆕 Verify & integrate |
| MCR 2.313 | 868 | 🆕 Verify & integrate |
| MCR 3.203 | 850 | 🆕 Verify & integrate |
| MCR 1.109 | 795 | 🆕 Verify & integrate |
| MCR 3.606 | 766 | 🆕 Verify & integrate |
| MCR 3.210 | 761 | 🆕 Verify & integrate |
| MCR 2.113 | 756 | 🆕 Verify & integrate |
| MCR 2.302 | 698 | 🆕 Verify & integrate |
| MCR 3.206 | 667 | 🆕 Verify & integrate |

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
  Ω-8 Authority Matching → Ω-9 Gap Analysis → Ω-13 Document Generation
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

---

## Decision Tree

```
ENTRY: Appellate task received
│
├─ Q1: What stage of appellate process?
│   ├─ Pre-appeal (trial level) → BRANCH A: Issue Preservation & Trial Prep
│   ├─ Filing the appeal → BRANCH B: Claim of Appeal / Leave Application
│   ├─ Briefing → BRANCH C: Appellate Brief Writing
│   ├─ Judicial challenge → BRANCH D: Recusal / Disqualification
│   └─ Post-decision → BRANCH E: MSC Application / Rehearing
│
├─ BRANCH A: Issue Preservation & Trial Prep
│   ├─ Step 1: Identify all issues to preserve for appeal
│   ├─ Step 2: Ensure contemporaneous objection on the record for each issue
│   ├─ Step 3: Request specific findings from trial court on contested issues
│   ├─ Step 4: Document transcript page/line for each preservation point
│   └─ OUTPUT: Preservation checklist with record citations
│
├─ BRANCH B: Claim of Appeal / Leave Application
│   ├─ Step 1: Determine appeal type — right (MCR 7.203) vs leave (MCR 7.205)
│   ├─ Step 2: Calculate jurisdictional deadline (21 days — NO EXTENSIONS)
│   ├─ Step 3: Order transcripts within 14 days (MCR 7.210(B)(1))
│   ├─ Step 4: Prepare claim of appeal / application with required components
│   ├─ Step 5: File via TrueFiling with proper fee or fee waiver
│   └─ OUTPUT: Filed claim of appeal with transcript order and docket statement
│
├─ BRANCH C: Appellate Brief Writing
│   ├─ Step 1: Identify standard of review for each issue (use standards matrix)
│   ├─ Step 2: Select 3-5 strongest issues — do NOT raise every possible issue
│   ├─ Step 3: Draft required sections per MCR 7.212(D) in order
│   ├─ Step 4: Verify all citations and address adverse authority
│   ├─ Step 5: Prepare appendix per MCR 7.212(C) — relevant portions only
│   ├─ Step 6: Check page limits (50 pages brief, appendix separate)
│   └─ OUTPUT: Complete appellate brief with appendix, ready for TrueFiling
│
├─ BRANCH D: Recusal / Disqualification
│   ├─ Step 1: Identify grounds under MCR 2.003(C)
│   ├─ Step 2: Gather evidence of bias from DB (judicial_violations table)
│   ├─ Step 3: File motion for disqualification within 14 days of discovery
│   ├─ Step 4: If denied — mandamus to COA (MCR 3.302)
│   └─ OUTPUT: Disqualification motion or mandamus petition
│
└─ BRANCH E: MSC Application / Rehearing
    ├─ Step 1: Calculate 42-day deadline from COA decision (MCR 7.305(C)(2))
    ├─ Step 2: Identify grounds for MSC review (conflict, public interest, clarity)
    ├─ Step 3: Draft application within 50-page limit
    ├─ Step 4: Include COA opinion and trial court order in appendix
    └─ OUTPUT: Application for leave to appeal to MSC
```

---

## Output Contract

```yaml
output:
  type: enum [brief, claim_of_appeal, leave_application, motion, preservation_checklist, analysis]
  format: markdown
  required_fields:
    - summary: string
    - citations: list[string]  # verified only
    - confidence: float  # 0.0-1.0
    - lane: enum [A, B, C, D, E, F]
    - case_number: string
    - standard_of_review: string  # must be stated for each issue
    - preservation_status: enum [preserved, unpreserved_plain_error, structural_error]
    - deadline: string  # jurisdictional deadline with date
  quality_gates:
    - all_citations_verified: boolean
    - no_hallucinated_names: boolean
    - db_first_confirmed: boolean
    - traceable_statistics: boolean
    - correct_standard_of_review: boolean
    - issues_preserved_below: boolean
    - page_limits_respected: boolean
    - appendix_complete: boolean
```
