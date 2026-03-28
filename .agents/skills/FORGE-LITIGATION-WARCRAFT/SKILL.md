---
name: FORGE-LITIGATION-WARCRAFT
description: >-
  Unified litigation document production engine fusing motion drafting, brief writing,
  complaint generation, filing assembly, emergency motion practice, SCAO form completion,
  Michigan e-filing protocols, court rule compliance, and document QA into a complete
  judicial-grade document factory. Produces MCR 2.113-compliant motions, IRAC/CREAC briefs,
  verified complaints, proposed orders, certificates of service, and exhibit packages.
  Michigan family law specialized. Triggers on motion, brief, complaint, filing, emergency,
  SCAO form, e-filing, court document, proposed order, certificate of service.
category: litigation
version: "1.0.0"
triggers:
  - "draft motion"
  - "write brief"
  - "file complaint"
  - "court filing"
  - "emergency motion"
  - "SCAO form"
  - "proposed order"
  - "certificate of service"
  - "MCR compliance"
  - "Michigan e-filing"
  - "IRAC brief"
  - "filing package"
metadata:
  tier: FORGE
  fused_skills: 10
  author: andrew-pigors + copilot-omega-delta-99
  forge_date: 2026-03-27
  forge_class: litigation-production
  emergent_capability: "Complete judicial-grade document factory producing court-ready filing stacks from evidence to submission"
---



# ⚔️ FORGE-LITIGATION-WARCRAFT
> **Judicial-Grade Document Production Engine (Ω-Δ99)**

| Field | Value |
| --- | --- |
| Court Focus | 14th Circuit Court, Muskegon County, Michigan family law |
| Core Matter | *Pigors v Watson*, Case No. **2024-001507-DC** |
| Judge Context | Hon. Jenny L. McNeill |
| Child Reference Rule | Refer to the child as **L.D.W. only** |
| Service Rule | Jennifer Barnes (P55406) is **WITHDRAWN**; serve Emily A. Watson directly at **2160 Garland Dr, Norton Shores, MI 49441** |
| FOC Service Rule | Pamela Rusco, Friend of the Court, **990 Terrace St, Muskegon, MI 49442** |
| Date Rule | All sample dates and generated date logic use **2026** |
| Formatting Rule | 12pt Times New Roman, double-spaced, 1-inch margins, 8.5×11 inch paper |
| Anti-Hallucination Rule | Never use "Jane Berry", "Patricia Berry", "P35878", or "91% alienation" |
| Production Goal | Generate court-ready motions, briefs, complaints, orders, SCAO forms, and filing stacks with verification and QA |

This superskill is a unified litigation production engine for drafting, validating, packaging, and routing Michigan family-law filings. It assumes a document factory posture: evidence enters at one side, compliant court-ready products exit at the other side. Every output must preserve Michigan caption practice, MCR-driven structure, accurate service data, child anonymization, and filing-lane specific packaging.

## Forged from 10 Skills

| # | Source Skill | Contribution |
| --- | --- | --- |
| 1 | litigation-brief-writer | IRAC/CREAC briefs, legal memoranda |
| 2 | litigation-motion-practice | MCR 2.119 motion drafting |
| 3 | litigation-motion-response-factory | Responses, replies, sur-replies |
| 4 | litigation-filing-architect | Filing strategy and packet design |
| 5 | litigation-complaint-drafter | Verified complaints, civil actions |
| 6 | litigation-emergency-motion-engine | Ex parte motions, TROs |
| 7 | michigan-litigation-writer | MCR 2.113 format compliance |
| 8 | court-filing-assembler | Packet assembly, exhibits, service |
| 9 | litigation-scao-forms-vault | MC 12, MC 375, DC 100, FOC forms |
| 10 | litigation-michigan-efiling-portal | MiFILE/TrueFiling submission |

## Architecture

```text
+--------------------------------------------------------------------------------+
|                         FORGE-LITIGATION-WARCRAFT Ω-Δ99                         |
+--------------------------------------------------------------------------------+
|  LW1 Motion Engine  --->  LW2 Brief Writer  --->  LW6 Proposed Orders          |
|         |                        |                         |                     |
|         v                        v                         v                     |
|  LW4 Emergency Factory ---> LW3 Complaint Gen ---> LW5 SCAO Completion         |
|         |                        |                         |                     |
|         +------------------------+------------+------------+                     |
|                                              v                                  |
|                                   LW7 Filing Package Assembler                  |
|                                              |                                  |
|                                              v                                  |
|                                       LW8 E-Filing Router                       |
+--------------------------------------------------------------------------------+
Inputs: facts, evidence, authorities, deadlines, service data, court selection
Outputs: motions, briefs, complaints, orders, forms, filing bundles, submission payloads
```



## LW1: Motion Engine

**Purpose**

Generate MCR 2.119-compliant motions with caption, body, relief, signature block, and direct-service logic for the Michigan family-law lane in *Pigors v Watson*.

**Design Pattern**

Template Method + rule-guarded string composition. The caption is fixed, relief is parameterized, and validation runs before assembly.

**Code Examples**

### LW1.1 Caption and Motion Skeleton

```python
from dataclasses import dataclass
from datetime import date

@dataclass
class Caption:
    court: str = "STATE OF MICHIGAN\nIN THE CIRCUIT COURT FOR THE COUNTY OF MUSKEGON\nFAMILY DIVISION"
    case_number: str = "2024-001507-DC"
    plaintiff: str = "ANDREW JAMES PIGORS"
    defendant: str = "EMILY A. WATSON"
    judge: str = "HON. JENNY L. MCNEILL"

def motion_header(title: str, filing_date: str = "March 27, 2026") -> str:
    c = Caption()
    return f"""{c.court}

ANDREW JAMES PIGORS,                          Case No. {c.case_number}
        Plaintiff,
v                                             Hon. {c.judge}
EMILY A. WATSON,
        Defendant.
__________________________________/

PLAINTIFF'S {title.upper()}
Filed: {filing_date}
"""
```

### LW1.2 MCR 2.119 Motion Body Builder

```python
def build_motion_body(relief_requested: str, facts: list[str], authority: list[str]) -> str:
    lines = []
    lines.append("NOW COMES Plaintiff, Andrew James Pigors, in propria persona, and moves this Court for relief.")
    lines.append("")
    lines.append("In support of this motion, Plaintiff states:")
    lines.append("")
    for index, fact in enumerate(facts, start=1):
        lines.append(f"{index}. {fact}")
    lines.append("")
    lines.append("This motion is brought pursuant to:")
    for cite in authority:
        lines.append(f"- {cite}")
    lines.append("")
    lines.append("WHEREFORE, Plaintiff respectfully requests that the Court:")
    for item in relief_requested.split(";"):
        lines.append(f"- {item.strip()}")
    return "\n".join(lines)

facts = [
    "The parties are the parents of L.D.W.",
    "This action is pending in Muskegon County under Case No. 2024-001507-DC.",
    "Immediate judicial intervention is necessary to protect the child’s stability and parenting-time structure in 2026."
]

authority = ["MCR 2.119", "MCR 3.210", "MCL 722.27"]
relief = "set the motion for hearing; enter temporary relief; grant any other just and proper relief"
print(build_motion_body(relief, facts, authority))
```

### LW1.3 Signature Block and Service Footer

```python
def signature_block(name: str = "Andrew James Pigors") -> str:
    return f"""Respectfully submitted,

{name}
In Propria Persona
Dated: March 27, 2026
"""

def service_footer() -> str:
    return """CERTIFICATE OF SERVICE

I certify that on March 27, 2026, I served this motion upon:
1. Emily A. Watson, 2160 Garland Dr, Norton Shores, MI 49441
2. Pamela Rusco, Friend of the Court, 990 Terrace St, Muskegon, MI 49442

Jennifer Barnes (P55406) is withdrawn and is not listed for service.
"""
```

### LW1.4 Full Motion Assembly Example

```python
def generate_motion_packet(title: str, facts: list[str], authority: list[str], relief: str) -> str:
    parts = [
        motion_header(title),
        build_motion_body(relief_requested=relief, facts=facts, authority=authority),
        "",
        "MEMORANDUM OF LAW",
        "Plaintiff relies on the authorities cited above and the attached brief.",
        "",
        signature_block(),
        "",
        service_footer(),
    ]
    return "\n".join(parts)

sample_motion = generate_motion_packet(
    title="Motion to Modify Parenting Time",
    facts=[
        "Plaintiff seeks a defined parenting-time schedule in the best interests of L.D.W.",
        "The requested structure is specific, enforceable, and drafted for immediate judicial implementation in 2026.",
        "The proposed order aligns relief with the factual record and requested findings."
    ],
    authority=["MCR 2.119", "MCR 3.210", "MCL 722.27a"],
    relief="enter the proposed schedule; require compliance with the order; award all further just relief",
)
print(sample_motion[:1200])
```

### LW1.5 Motion Validation Guardrails

```python
REQUIRED_MOTION_RULES = {
    "child_reference": "L.D.W.",
    "format": "12pt Times New Roman, double-spaced, 1-inch margins, 8.5x11",
    "service_emily": "2160 Garland Dr, Norton Shores, MI 49441",
    "service_foc": "990 Terrace St, Muskegon, MI 49442",
    "year": "2026",
}

def validate_motion_text(text: str) -> list[str]:
    errors = []
    if "L.D.W." not in text:
        errors.append("Child reference missing or not anonymized.")
    if "2026" not in text:
        errors.append("All dates must be set in 2026.")
    if "Jane Berry" in text or "Patricia Berry" in text or "P35878" in text or "91% alienation" in text:
        errors.append("Anti-hallucination forbidden term detected.")
    if "Jennifer Barnes" in text and "withdrawn" not in text.lower():
        errors.append("Barnes must be marked withdrawn if mentioned.")
    return errors
```

**Integration**

LW1 feeds requested relief and factual predicates into LW2 for memorandum support, LW6 for proposed orders, and LW7 for assembly.


## LW2: Brief/Memorandum Writer

**Purpose**

Produce IRAC and CREAC briefs, standards of review, authorities tables, and argument sections tied to the corresponding motion or complaint.

**Design Pattern**

Structured argument synthesis. Questions presented, fact blocks, argument units, and authorities indexes are built from reusable components.

**Code Examples**

### LW2.1 Table of Contents and Authorities Collector

```python
from collections import defaultdict

class BriefIndex:
    def __init__(self) -> None:
        self.toc = []
        self.authorities = defaultdict(list)

    def add_heading(self, title: str, page: int) -> None:
        self.toc.append((title, page))

    def add_authority(self, category: str, cite: str, page: int) -> None:
        self.authorities[category].append((cite, page))

    def render(self) -> str:
        toc_lines = ["TABLE OF CONTENTS"]
        toc_lines.extend([f"{title} ................................ {page}" for title, page in self.toc])
        auth_lines = ["INDEX OF AUTHORITIES"]
        for category, cites in self.authorities.items():
            auth_lines.append(category.upper())
            for cite, page in cites:
                auth_lines.append(f"{cite} ................................ {page}")
        return "\n".join(toc_lines + [""] + auth_lines)
```

### LW2.2 IRAC Builder

```python
def irac(issue: str, rule: str, application: str, conclusion: str) -> str:
    return f"""ISSUE
{issue}

RULE
{rule}

APPLICATION
{application}

CONCLUSION
{conclusion}
"""

sample_irac = irac(
    issue="Whether the Court should grant temporary parenting-time relief consistent with the best interests of L.D.W.",
    rule="Under MCL 722.27a and MCR 3.210, the Court may structure parenting time to protect the child’s welfare and provide enforceable terms.",
    application="The record supports a schedule with precise exchanges, compliance terms, and immediate 2026 implementation. The proposal is detailed and reduces ambiguity.",
    conclusion="The Court should enter the proposed parenting-time schedule and any necessary enforcement terms."
)
print(sample_irac)
```

### LW2.3 CREAC Argument Section Generator

```python
def creac(conclusion: str, rule: str, explanation: str, application: str, wrap_up: str) -> str:
    return f"""CONCLUSION
{conclusion}

RULE
{rule}

EXPLANATION
{explanation}

APPLICATION
{application}

CONCLUSION
{wrap_up}
"""

argument = creac(
    conclusion="Temporary relief is warranted.",
    rule="MCR 2.119 authorizes motion practice; MCL 722.27 permits custody-related relief pending adjudication.",
    explanation="Michigan briefing should connect governing rule text to the requested remedy, then explain why the requested order is administrable.",
    application="The proposed order gives the Court a complete enforcement-ready instrument, identifies the parties, preserves anonymity for L.D.W., and includes service-specific details for Muskegon County practice.",
    wrap_up="Accordingly, the Court should grant the motion."
)
print(argument)
```

### LW2.4 Standard of Review Library

```python
STANDARD_OF_REVIEW = {
    "custody": "Orders affecting custody are reviewed under the standards applicable to the relief sought, with factual findings reviewed under the great-weight standard and discretionary rulings for abuse of discretion.",
    "parenting_time": "Parenting-time determinations are reviewed for abuse of discretion, with legal questions reviewed de novo.",
    "injunction": "A trial court’s decision on interim injunctive or emergency relief is generally reviewed for abuse of discretion.",
    "1983": "Federal civil-rights pleading sufficiency is reviewed under the applicable Rule 12 standards, with legal issues reviewed de novo.",
}

def standard_of_review(topic: str) -> str:
    return STANDARD_OF_REVIEW[topic]

print(standard_of_review("parenting_time"))
```

### LW2.5 Full Brief Constructor

```python
def build_brief(title: str, argument_sections: list[str]) -> str:
    index = BriefIndex()
    index.add_heading("Table of Contents", 1)
    index.add_heading("Index of Authorities", 2)
    index.add_heading("Statement of Questions Presented", 3)
    index.add_heading("Statement of Facts", 4)
    for idx, _ in enumerate(argument_sections, start=1):
        index.add_heading(f"Argument {idx}", 4 + idx)
    index.add_authority("Statutes", "MCL 722.27", 5)
    index.add_authority("Statutes", "MCL 722.27a", 6)
    index.add_authority("Court Rules", "MCR 2.119", 3)
    index.add_authority("Court Rules", "MCR 3.210", 5)

    body = [
        title.upper(),
        "",
        index.render(),
        "",
        "STATEMENT OF QUESTIONS PRESENTED",
        "1. Should the Court grant the relief described in the motion? Plaintiff answers: Yes.",
        "",
        "STATEMENT OF FACTS",
        "The parties are before the Court in 2026 regarding relief affecting L.D.W. The filing packet is designed for direct adjudicative use.",
        "",
    ]
    body.extend(argument_sections)
    return "\n".join(body)
```

**Integration**

LW2 consumes motion metadata from LW1 and complaint metadata from LW3, then exports argument sections into LW6 findings and LW7 packet components.


## LW3: Complaint Generator

**Purpose**

Draft verified complaints with numbered paragraphs, causes of action, prayer for relief, and lane-specific tailoring for custody, civil, and §1983 filings.

**Design Pattern**

Declarative pleading objects. Paragraphs, causes of action, and prayer blocks are separate assets combined into a single verified pleading.

**Code Examples**

### LW3.1 Verified Complaint Data Structures

```python
from dataclasses import dataclass, field

@dataclass
class Paragraph:
    number: int
    text: str

    def render(self) -> str:
        return f"{self.number}. {self.text}"

@dataclass
class CauseOfAction:
    heading: str
    allegations: list[str] = field(default_factory=list)
    relief: list[str] = field(default_factory=list)

    def render(self, start_number: int) -> tuple[str, int]:
        lines = [self.heading]
        counter = start_number
        for allegation in self.allegations:
            lines.append(f"{counter}. {allegation}")
            counter += 1
        lines.append("WHEREFORE, Plaintiff requests:")
        for item in self.relief:
            lines.append(f"- {item}")
        return "\n".join(lines), counter
```

### LW3.2 Custody Complaint Generator (DC 100 lane)

```python
def generate_custody_complaint() -> str:
    intro = [
        "VERIFIED COMPLAINT",
        "",
        "1. Plaintiff Andrew James Pigors is an adult resident with standing to seek custody-related relief.",
        "2. Defendant Emily A. Watson is an adult resident subject to the jurisdiction of this Court.",
        "3. The minor child at issue is identified only as L.D.W.",
        "4. Venue is proper in Muskegon County under the pending family matter, Case No. 2024-001507-DC.",
        "5. Plaintiff requests custody and parenting-time determinations in the best interests of L.D.W.",
    ]
    cause = CauseOfAction(
        heading="COUNT I — CUSTODY AND PARENTING-TIME RELIEF",
        allegations=[
            "Plaintiff incorporates the preceding paragraphs.",
            "A defined court order is necessary to provide enforceable terms in 2026.",
            "The requested relief is crafted to be specific, practical, and immediately administrable."
        ],
        relief=[
            "Enter custody and parenting-time provisions in the best interests of L.D.W.",
            "Adopt the attached proposed order.",
            "Grant any other relief the Court deems just and proper."
        ]
    )
    cause_text, _ = cause.render(6)
    verification = """VERIFICATION

    I declare under penalty of perjury that the foregoing factual allegations are true to the best of my knowledge, information, and belief.

    Dated: March 27, 2026
    Andrew James Pigors
    """
    return "\n".join(intro + ["", cause_text, "", verification])
```

### LW3.3 Civil Complaint Generator (CC 257 lane)

```python
def generate_civil_complaint(title: str, claims: list[CauseOfAction]) -> str:
    lines = [
        "CIVIL COMPLAINT",
        "",
        "1. Plaintiff files this civil action in 2026.",
        "2. Jurisdiction and venue are pleaded in separately numbered paragraphs.",
        "3. The complaint may be paired with CC 257 and supporting case-type metadata.",
        "",
    ]
    counter = 4
    for claim in claims:
        text, counter = claim.render(counter)
        lines.extend([text, ""])
    return "\n".join(lines)

negligence_style_claim = CauseOfAction(
    heading="COUNT I — DECLARATORY AND INJUNCTIVE RELIEF",
    allegations=[
        "Plaintiff seeks declaratory relief tied to the pleaded controversy.",
        "Plaintiff seeks injunctive terms that can be reduced to a proposed order."
    ],
    relief=["Issue declaratory relief.", "Issue injunctive relief.", "Award other proper relief."]
)
print(generate_civil_complaint("Civil Complaint", [negligence_style_claim]))
```

### LW3.4 Federal Complaint Generator (42 USC §1983 lane)

```python
def generate_1983_complaint(defendants: list[str], constitutional_counts: list[str]) -> str:
    lines = [
        "UNITED STATES DISTRICT COURT",
        "WESTERN DISTRICT OF MICHIGAN",
        "",
        "COMPLAINT FOR DECLARATORY, INJUNCTIVE, AND OTHER RELIEF",
        "",
        "1. This complaint is filed under 42 USC §1983.",
        "2. Plaintiff alleges deprivations of federally protected rights under color-of-law allegations as pleaded.",
        "3. Each defendant is identified in a separate party paragraph.",
        "",
        "PARTIES",
    ]
    for idx, defendant in enumerate(defendants, start=4):
        lines.append(f"{idx}. Defendant {defendant} is named in his, her, or official capacity as pleaded.")
    lines.extend(["", "COUNTS"])
    for count_number, claim in enumerate(constitutional_counts, start=1):
        lines.append(f"COUNT {count_number} — {claim}")
        lines.append(f"Plaintiff pleads the elements of {claim} in numbered paragraphs and requests corresponding relief.")
    lines.extend([
        "",
        "PRAYER FOR RELIEF",
        "- Declare the challenged conduct unlawful.",
        "- Enter appropriate injunctive relief.",
        "- Award costs, fees where authorized, and all further proper relief.",
    ])
    return "\n".join(lines)
```

### LW3.5 Complaint QA and Verification Controls

```python
def complaint_checklist(text: str) -> dict[str, bool]:
    return {
        "numbered_paragraphs": any(line[:1].isdigit() for line in text.splitlines()),
        "verification_block": "VERIFICATION" in text,
        "child_anonymized": "L.D.W." in text and "child" in text.lower(),
        "year_2026": "2026" in text,
        "service_direct_to_emily": "2160 Garland Dr" in text or "service" not in text.lower(),
    }

generated = generate_custody_complaint()
print(complaint_checklist(generated))
```

**Integration**

LW3 can dispatch DC 100 and FOC forms through LW5, bundle attachments through LW7, and select portal routing through LW8.


## LW4: Emergency Motion Factory

**Purpose**

Draft emergency and ex parte motions, TRO-style requests, irreparable-harm narratives, and supporting affidavits for 2026 emergency practice.

**Design Pattern**

Fast-path emergency branching. The module forces separate fields for emergency facts, notice inadequacy, requested temporary order, and follow-up hearing logic.

**Code Examples**

### LW4.1 Ex Parte Motion Builder

```python
def ex_parte_motion(title: str, emergency_facts: list[str], harm_showing: str) -> str:
    lines = [
        motion_header(title, filing_date="April 2, 2026"),
        "EMERGENCY AND EX PARTE REQUEST",
        "",
        "Plaintiff seeks immediate review without ordinary notice because the facts set out below require prompt intervention.",
        "",
        "EMERGENCY FACTS",
    ]
    for idx, fact in enumerate(emergency_facts, start=1):
        lines.append(f"{idx}. {fact}")
    lines.extend([
        "",
        "IRREPARABLE HARM",
        harm_showing,
        "",
        "Plaintiff requests immediate temporary relief pending further hearing.",
    ])
    return "\n".join(lines)
```

### LW4.2 MCR 3.207 Emergency Custody Logic

```python
def emergency_custody_showing() -> str:
    return (
        "Under MCR 3.207, the filing must articulate why immediate action is necessary, "
        "why ordinary notice is inadequate, and what temporary order should issue before hearing. "
        "The narrative should identify present risk, the requested protective structure, and the shortest path to a prompt follow-up hearing."
    )

print(emergency_custody_showing())
```

### LW4.3 Emergency Affidavit Generator

```python
def emergency_affidavit(facts: list[str]) -> str:
    lines = [
        "AFFIDAVIT IN SUPPORT OF EMERGENCY RELIEF",
        "",
        "I, Andrew James Pigors, being first duly sworn, state as follows:",
    ]
    for idx, fact in enumerate(facts, start=1):
        lines.append(f"{idx}. {fact}")
    lines.extend([
        "",
        "FURTHER AFFIANT SAYETH NOT.",
        "",
        "Dated: April 2, 2026",
        "Andrew James Pigors",
    ])
    return "\n".join(lines)
```

### LW4.4 TRO and Immediate Relief Order Draft

```python
def temporary_restraining_order(findings: list[str], directives: list[str]) -> str:
    lines = [
        "PROPOSED EX PARTE ORDER",
        "",
        "THE COURT FINDS:",
    ]
    for finding in findings:
        lines.append(f"- {finding}")
    lines.extend(["", "IT IS ORDERED:"])
    for directive in directives:
        lines.append(f"- {directive}")
    lines.extend([
        "",
        "This temporary order remains effective until further order of the Court or scheduled hearing in 2026.",
        "",
        "Hon. Jenny L. McNeill",
        "Circuit Court Judge",
    ])
    return "\n".join(lines)
```

### LW4.5 Emergency Motion Readiness Scoring

```python
def emergency_score(has_affidavit: bool, has_specific_harm: bool, has_order: bool, has_follow_up_request: bool) -> int:
    score = 0
    score += 25 if has_affidavit else 0
    score += 25 if has_specific_harm else 0
    score += 25 if has_order else 0
    score += 25 if has_follow_up_request else 0
    return score

print(emergency_score(True, True, True, True))
```

**Integration**

LW4 relies on LW6 for temporary orders, LW7 for emergency packet sequencing, and LW8 for portal-specific emergency submission prep.


## LW5: SCAO Form Completion

**Purpose**

Auto-fill MC 12, MC 375, MC 376, DC 100, FOC 89, and CC 257 with case-specific data, service rules, and date rules.

**Design Pattern**

Form schema mapping. Each form is a constrained dictionary rendered from shared case metadata and lane-specific fields.

**Code Examples**

### LW5.1 MC 12 Proof of Service Autofill

```python
MC12_TEMPLATE = {
    "form": "MC 12",
    "title": "Proof of Service",
    "case_number": "2024-001507-DC",
    "court": "14th Circuit Court, Muskegon County",
    "served_parties": [
        {"name": "Emily A. Watson", "address": "2160 Garland Dr, Norton Shores, MI 49441"},
        {"name": "Pamela Rusco", "address": "990 Terrace St, Muskegon, MI 49442"},
    ],
    "service_date": "March 27, 2026",
    "service_method": "mail and electronic service where permitted",
}

def render_mc12(data: dict) -> str:
    lines = [f"{data['form']} - {data['title']}", f"Case No. {data['case_number']}", data["court"], ""]
    for party in data["served_parties"]:
        lines.append(f"Served: {party['name']} — {party['address']}")
    lines.append(f"Date: {data['service_date']}")
    lines.append(f"Method: {data['service_method']}")
    return "\n".join(lines)
```

### LW5.2 MC 375 Motion and MC 376 Response Autofill

```python
def fill_mc375(motion_title: str, hearing_requested: bool = True) -> dict:
    return {
        "form": "MC 375",
        "motion_title": motion_title,
        "case_number": "2024-001507-DC",
        "hearing_requested": hearing_requested,
        "filing_date": "March 27, 2026",
    }

def fill_mc376(response_title: str) -> dict:
    return {
        "form": "MC 376",
        "response_title": response_title,
        "case_number": "2024-001507-DC",
        "filing_date": "March 27, 2026",
    }

print(fill_mc375("Motion to Modify Parenting Time"))
print(fill_mc376("Response to Motion to Modify Parenting Time"))
```

### LW5.3 DC 100, FOC 89, and CC 257 Autofill

```python
def fill_dc100() -> dict:
    return {
        "form": "DC 100",
        "caption": "Andrew James Pigors v Emily A. Watson",
        "child_reference": "L.D.W.",
        "case_number": "2024-001507-DC",
        "venue": "Muskegon County",
    }

def fill_foc89() -> dict:
    return {
        "form": "FOC 89",
        "issue": "Parenting Time",
        "case_number": "2024-001507-DC",
        "requested_relief": "Specific parenting-time schedule and enforcement terms",
    }

def fill_cc257(case_type: str = "civil") -> dict:
    return {
        "form": "CC 257",
        "case_type": case_type,
        "filing_year": 2026,
    }
```

### LW5.4 Form Export Pipeline

```python
def export_form_bundle() -> dict[str, dict]:
    return {
        "mc12": MC12_TEMPLATE,
        "mc375": fill_mc375("Motion for Defined Parenting-Time Order"),
        "mc376": fill_mc376("Response to Parenting-Time Motion"),
        "dc100": fill_dc100(),
        "foc89": fill_foc89(),
        "cc257": fill_cc257(),
    }

forms = export_form_bundle()
for key, value in forms.items():
    print(key, value["form"])
```

### LW5.5 Form-Specific Compliance Rules

```python
FORM_RULES = {
    "MC 12": ["List served parties", "Use 2026 service date", "Identify method of service"],
    "MC 375": ["Match motion title to main filing", "Use correct case number", "Attach notice if hearing requested"],
    "MC 376": ["Mirror motion caption", "State response position clearly"],
    "DC 100": ["Use L.D.W. only", "Confirm family-division context"],
    "FOC 89": ["State parenting-time request with specificity"],
    "CC 257": ["Select correct civil case category"],
}

def rules_for(form_name: str) -> list[str]:
    return FORM_RULES[form_name]
```

**Integration**

LW5 is a support layer for LW1, LW3, and LW7. It provides the standardized form objects that accompany filings and service packets.


## LW6: Proposed Order Generator

**Purpose**

Generate proposed orders matching each motion type with findings, IT IS ORDERED language, and signature lines tailored to the assigned relief.

**Design Pattern**

Findings-to-directives mapping. The motion determines findings, and the order generator translates those findings into clean judicial commands.

**Code Examples**

### LW6.1 Proposed Order Base Class

```python
class ProposedOrder:
    def __init__(self, title: str, findings: list[str], orders: list[str]) -> None:
        self.title = title
        self.findings = findings
        self.orders = orders

    def render(self) -> str:
        lines = [self.title, "", "THE COURT FINDS:"]
        lines.extend([f"- {finding}" for finding in self.findings])
        lines.extend(["", "IT IS ORDERED:"])
        lines.extend([f"- {item}" for item in self.orders])
        lines.extend([
            "",
            "Date: __________________, 2026",
            "",
            "__________________________________",
            "Hon. Jenny L. McNeill",
            "Circuit Court Judge",
        ])
        return "\n".join(lines)
```

### LW6.2 Custody and Parenting-Time Order

```python
def parenting_time_order() -> str:
    order = ProposedOrder(
        title="PROPOSED ORDER REGARDING PARENTING TIME",
        findings=[
            "The Court has reviewed the motion, any supporting brief, and the requested relief.",
            "The order is drafted for immediate implementation in 2026.",
            "The child is identified in this filing only as L.D.W."
        ],
        orders=[
            "The parenting-time schedule attached to the motion is adopted.",
            "Each party shall comply strictly with the exchange provisions.",
            "Further disputes shall be raised by written motion unless emergency circumstances arise."
        ],
    )
    return order.render()
```

### LW6.3 Discovery, Show-Cause, and Enforcement Order Patterns

```python
ORDER_LIBRARY = {
    "discovery": ProposedOrder(
        "PROPOSED ORDER COMPELLING DISCOVERY",
        ["A discovery request is pending and compliance has not yet been completed."],
        ["The responding party shall serve complete responses within 14 days in 2026."]
    ),
    "show_cause": ProposedOrder(
        "PROPOSED ORDER TO SHOW CAUSE",
        ["The motion presents allegations warranting a response hearing."],
        ["The respondent shall appear and show cause at the scheduled hearing."]
    ),
    "enforcement": ProposedOrder(
        "PROPOSED ORDER FOR ENFORCEMENT",
        ["The Court finds clarity is necessary to ensure compliance."],
        ["The parties shall follow the schedule as written pending further order."]
    ),
}
```

### LW6.4 Findings-to-Order Mapper

```python
def order_from_motion(motion_type: str, factual_findings: list[str]) -> str:
    directives = {
        "emergency": ["Temporary relief is granted pending further hearing.", "A follow-up hearing shall be scheduled promptly."],
        "custody": ["The attached parenting-time and custody provisions are adopted."],
        "discovery": ["Responses and documents shall be served by the deadline."],
    }
    order = ProposedOrder(
        title=f"PROPOSED ORDER ON {motion_type.upper()}",
        findings=factual_findings,
        orders=directives[motion_type],
    )
    return order.render()
```

### LW6.5 Order QA Validator

```python
def validate_order(order_text: str) -> list[str]:
    issues = []
    if "IT IS ORDERED" not in order_text:
        issues.append("Missing operative ordering language.")
    if "Jenny L. McNeill" not in order_text:
        issues.append("Judge signature line missing.")
    if "2026" not in order_text:
        issues.append("Order date line must reference 2026.")
    if "L.D.W." not in order_text and "child" in order_text.lower():
        issues.append("Child reference not anonymized.")
    return issues
```

**Integration**

LW6 receives arguments and relief requests from LW1, LW2, and LW4, then returns a hearing-ready order for packaging in LW7.


## LW7: Filing Package Assembler

**Purpose**

Combine motion, brief, affidavit, exhibits, proposed order, certificate of service, and cover sheet into a single indexed filing stack with Bates numbering.

**Design Pattern**

Manifest-driven assembly. The filing stack is constructed from required and optional components, then labeled, indexed, and service-tagged.

**Code Examples**

### LW7.1 Filing Package Manifest

```python
from dataclasses import dataclass

@dataclass
class FilingDocument:
    label: str
    path: str
    required: bool = True

def build_manifest() -> list[FilingDocument]:
    return [
        FilingDocument("Motion", "motion.pdf"),
        FilingDocument("Brief", "brief.pdf"),
        FilingDocument("Affidavit", "affidavit.pdf"),
        FilingDocument("Exhibit A", "exhibit_a.pdf"),
        FilingDocument("Proposed Order", "proposed_order.pdf"),
        FilingDocument("Certificate of Service", "certificate_of_service.pdf"),
        FilingDocument("Cover Sheet", "cover_sheet.pdf", required=False),
    ]
```

### LW7.2 Bates Numbering Logic

```python
def bates_labels(prefix: str, count: int, start: int = 1) -> list[str]:
    labels = []
    for number in range(start, start + count):
        labels.append(f"{prefix}-{number:06d}")
    return labels

print(bates_labels("PIGORS", 5, start=100))
```

### LW7.3 Merge Order and Stack Builder

```python
def merge_order(documents: list[FilingDocument]) -> list[str]:
    ordered = [doc.label for doc in documents if doc.required]
    optional = [doc.label for doc in documents if not doc.required]
    return ordered + optional

filing_stack = merge_order(build_manifest())
for item in filing_stack:
    print(item)
```

### LW7.4 Certificate of Service Packager

```python
def certificate_of_service_text() -> str:
    return """CERTIFICATE OF SERVICE

I certify that on March 27, 2026, I served the filing package on:
- Emily A. Watson, 2160 Garland Dr, Norton Shores, MI 49441
- Pamela Rusco, Friend of the Court, 990 Terrace St, Muskegon, MI 49442

Jennifer Barnes (P55406) is withdrawn and is not a current service recipient.

Andrew James Pigors
"""
```

### LW7.5 End-to-End Filing Stack Assembler

```python
def assemble_filing_stack() -> dict:
    manifest = build_manifest()
    stack = {
        "caption": "Pigors v Watson, 2024-001507-DC",
        "documents": [doc.label for doc in manifest],
        "bates": bates_labels("PIGORS", 25, start=1),
        "service": [
            "Emily A. Watson — 2160 Garland Dr, Norton Shores, MI 49441",
            "Pamela Rusco — 990 Terrace St, Muskegon, MI 49442",
        ],
        "format": "12pt Times New Roman, double-spaced, 1-inch margins, 8.5x11",
    }
    return stack

print(assemble_filing_stack())
```

**Integration**

LW7 is the central bundler for every upstream module. It feeds output labels, service recipients, and fee context into LW8.


## LW8: E-Filing Router

**Purpose**

Route complete filing stacks to MiFILE, TrueFiling, or CM/ECF with portal-specific payloads and fee tracking.

**Design Pattern**

Strategy pattern for venue routing. Each portal gets its own payload builder and validation profile.

**Code Examples**

### LW8.1 Portal Routing Matrix

```python
ROUTING_TABLE = {
    "14th_circuit_family": {"portal": "MiFILE", "venue": "14th Circuit Court, Muskegon County", "case_number": "2024-001507-DC"},
    "coa_366810": {"portal": "TrueFiling", "venue": "Michigan Court of Appeals", "case_number": "366810"},
    "wdmi_federal": {"portal": "CM/ECF", "venue": "Western District of Michigan", "case_number": "new or assigned"},
}

def route_destination(track: str) -> dict:
    return ROUTING_TABLE[track]
```

### LW8.2 Filing Fee Tracking

```python
FILING_FEES = {
    "motion": 20,
    "new_case": 175,
    "appeal": 375,
}

def fee_total(items: list[str]) -> int:
    return sum(FILING_FEES[item] for item in items)

print(fee_total(["motion", "appeal"]))
```

### LW8.3 MiFILE Submission Payload

```python
def mifile_payload(document_titles: list[str]) -> dict:
    return {
        "portal": "MiFILE",
        "court": "14th Circuit Court, Muskegon County",
        "case_number": "2024-001507-DC",
        "documents": document_titles,
        "fee_due": fee_total(["motion"]),
        "service_contacts": [
            {"name": "Emily A. Watson", "address": "2160 Garland Dr, Norton Shores, MI 49441"},
            {"name": "Pamela Rusco", "address": "990 Terrace St, Muskegon, MI 49442"},
        ],
    }
```

### LW8.4 TrueFiling and CM/ECF Payload Variants

```python
def truefiling_payload(document_titles: list[str]) -> dict:
    return {
        "portal": "TrueFiling",
        "case_number": "366810",
        "documents": document_titles,
        "fee_due": fee_total(["appeal"]),
    }

def cmecf_payload(document_titles: list[str]) -> dict:
    return {
        "portal": "CM/ECF",
        "district": "Western District of Michigan",
        "documents": document_titles,
        "fee_due": fee_total(["new_case"]),
    }
```

### LW8.5 Routing and Submission Validator

```python
def validate_submission(track: str, payload: dict) -> list[str]:
    issues = []
    route = route_destination(track)
    if payload.get("portal") != route["portal"]:
        issues.append("Portal mismatch.")
    if "documents" not in payload or not payload["documents"]:
        issues.append("No documents attached.")
    if track == "14th_circuit_family" and payload.get("fee_due") != 20:
        issues.append("Incorrect motion fee for MiFILE track.")
    return issues
```

**Integration**

LW8 consumes the stack emitted by LW7 and applies the correct portal strategy based on court and case lane.


## Decision Tree

```text
START
  |
  +-- Need immediate relief?
  |      |
  |      +-- Yes --> LW4 Emergency Motion Factory --> LW6 Proposed Order --> LW7 Package --> LW8 Route
  |      |
  |      +-- No
  |
  +-- Need a motion?
  |      |
  |      +-- Yes --> LW1 Motion Engine --> LW2 Brief Writer (if memorandum needed) --> LW6
  |
  +-- Need a complaint?
  |      |
  |      +-- Family / custody --> LW3 + LW5 (DC 100 / FOC forms) --> LW7 --> LW8 MiFILE
  |      +-- Civil --> LW3 + LW5 (CC 257) --> LW7 --> LW8
  |      +-- Federal 1983 --> LW3 --> LW7 --> LW8 CM/ECF
  |
  +-- Need response / reply / sur-reply?
         |
         +-- Use LW1 structure + LW2 argument engine + LW6 responsive order if needed
```



## Cross-Module Integration

1. **LW1 → LW2**: A motion record should pass its requested relief, factual summary, and authority list to the brief writer so that the memorandum mirrors the motion exactly.
2. **LW1/LW2 → LW6**: Every motion and brief should generate proposed findings and operative language for the order module.
3. **LW3 → LW5**: Complaint generation selects the proper SCAO or civil cover forms and auto-populates matching case metadata.
4. **LW4 → LW6/LW7**: Emergency filings require simultaneous generation of an emergency motion, affidavit, and ex parte or follow-up order.
5. **LW5 → LW7**: Forms become package components and should be included in the same stack index and Bates plan where appropriate.
6. **LW7 → LW8**: The filing package should export a clean routing payload with portal, fee, case number, and service details.

### Orchestrator Example

```python
def forge_document_factory(track: str, artifact_type: str) -> dict:
    packet = {"track": track, "artifact_type": artifact_type}
    if artifact_type == "motion":
        packet["motion"] = generate_motion_packet(
            title="Motion for Defined Parenting-Time Order",
            facts=[
                "The filing concerns L.D.W. and requests a specific parenting-time schedule.",
                "The record is organized for immediate 2026 adjudication.",
                "The requested terms are paired with a matching proposed order."
            ],
            authority=["MCR 2.119", "MCR 3.210", "MCL 722.27a"],
            relief="enter the schedule; enforce compliance; grant just relief",
        )
        packet["brief"] = build_brief("Brief in Support", [sample_irac, argument])
        packet["order"] = parenting_time_order()
    elif artifact_type == "emergency":
        packet["motion"] = ex_parte_motion(
            "Emergency Motion for Immediate Relief",
            [
                "Immediate intervention is sought in 2026.",
                "The requested relief is narrowly tailored and temporary.",
                "The accompanying affidavit details the urgency."
            ],
            "Absent immediate relief, the risk described in the affidavit will continue before a noticed hearing can occur."
        )
        packet["affidavit"] = emergency_affidavit([
            "I am the Plaintiff in this matter.",
            "The facts described in the emergency motion are true to the best of my knowledge.",
            "Immediate relief is necessary to protect the status quo involving L.D.W."
        ])
        packet["order"] = temporary_restraining_order(
            findings=["The Court has reviewed the emergency submission.", "Immediate temporary terms are warranted pending hearing."],
            directives=["Temporary restrictions are imposed pending hearing.", "A prompt follow-up hearing shall be scheduled."]
        )
    packet["forms"] = export_form_bundle()
    packet["stack"] = assemble_filing_stack()
    packet["route"] = route_destination(track)
    return packet
```



## Domain Applications

| Scenario | Module Path | Output Set |
| --- | --- | --- |
| Standard parenting-time motion | LW1 → LW2 → LW6 → LW7 → LW8 | Motion, brief, proposed order, certificate of service, MiFILE payload |
| Emergency custody / parenting-time request | LW4 → LW6 → LW7 → LW8 | Ex parte motion, affidavit, TRO-style order, package, emergency routing |
| Family complaint launch | LW3 → LW5 → LW7 → LW8 | Verified complaint, DC 100/FOC forms, service package |
| Civil action launch | LW3 → LW5 → LW7 → LW8 | Complaint, CC 257, filing stack |
| Federal §1983 action | LW3 → LW7 → LW8 | Federal complaint, exhibits, CM/ECF routing |
| Motion response / reply | LW1 → LW2 → LW6 → LW7 | Response brief, reply, proposed responsive order |

## Quick Reference Card

- **Caption anchor**: STATE OF MICHIGAN / IN THE CIRCUIT COURT FOR THE COUNTY OF MUSKEGON / FAMILY DIVISION
- **Case number**: 2024-001507-DC
- **Judge line**: Hon. Jenny L. McNeill
- **Parties**: Andrew James Pigors v Emily A. Watson
- **Child rule**: L.D.W. only
- **Service**: Emily directly at 2160 Garland Dr, Norton Shores, MI 49441
- **FOC**: Pamela Rusco, 990 Terrace St, Muskegon, MI 49442
- **Dates**: 2026 only
- **Fonts and layout**: 12pt Times New Roman, double-spaced, 1-inch margins, 8.5×11
- **Fees**: $20 motion, $175 new case, $375 appeal
- **Portals**: MiFILE (14th Circuit), TrueFiling (COA 366810), CM/ECF (WDMI)
- **Forbidden hallucinations**: "Jane Berry", "Patricia Berry", "P35878", "91% alienation"



## Extended Pattern Library

### LW1 Motion Variants

#### LW1 Pattern 1

```python
def lw1_pattern_1(payload: dict) -> dict:
    return {
        "module": "LW1",
        "pattern": "1",
        "case_number": "2024-001507-DC",
        "year": 2026,
        "child_reference": "L.D.W.",
        "service": [
            "Emily A. Watson — 2160 Garland Dr, Norton Shores, MI 49441",
            "Pamela Rusco — 990 Terrace St, Muskegon, MI 49442",
        ],
        "payload": payload,
    }

example_1 = lw1_pattern_1({"title": "Motion Variants example 1"})
print(example_1)
```

### LW2 Brief Variants

#### LW2 Pattern 1

```python
def lw2_pattern_1(payload: dict) -> dict:
    return {
        "module": "LW2",
        "pattern": "1",
        "case_number": "2024-001507-DC",
        "year": 2026,
        "child_reference": "L.D.W.",
        "service": [
            "Emily A. Watson — 2160 Garland Dr, Norton Shores, MI 49441",
            "Pamela Rusco — 990 Terrace St, Muskegon, MI 49442",
        ],
        "payload": payload,
    }

example_1 = lw2_pattern_1({"title": "Brief Variants example 1"})
print(example_1)
```

### LW3 Complaint Variants

#### LW3 Pattern 1

```python
def lw3_pattern_1(payload: dict) -> dict:
    return {
        "module": "LW3",
        "pattern": "1",
        "case_number": "2024-001507-DC",
        "year": 2026,
        "child_reference": "L.D.W.",
        "service": [
            "Emily A. Watson — 2160 Garland Dr, Norton Shores, MI 49441",
            "Pamela Rusco — 990 Terrace St, Muskegon, MI 49442",
        ],
        "payload": payload,
    }

example_1 = lw3_pattern_1({"title": "Complaint Variants example 1"})
print(example_1)
```

### LW4 Emergency Variants

#### LW4 Pattern 1

```python
def lw4_pattern_1(payload: dict) -> dict:
    return {
        "module": "LW4",
        "pattern": "1",
        "case_number": "2024-001507-DC",
        "year": 2026,
        "child_reference": "L.D.W.",
        "service": [
            "Emily A. Watson — 2160 Garland Dr, Norton Shores, MI 49441",
            "Pamela Rusco — 990 Terrace St, Muskegon, MI 49442",
        ],
        "payload": payload,
    }

example_1 = lw4_pattern_1({"title": "Emergency Variants example 1"})
print(example_1)
```

### LW5 Form Variants

#### LW5 Pattern 1

```python
def lw5_pattern_1(payload: dict) -> dict:
    return {
        "module": "LW5",
        "pattern": "1",
        "case_number": "2024-001507-DC",
        "year": 2026,
        "child_reference": "L.D.W.",
        "service": [
            "Emily A. Watson — 2160 Garland Dr, Norton Shores, MI 49441",
            "Pamela Rusco — 990 Terrace St, Muskegon, MI 49442",
        ],
        "payload": payload,
    }

example_1 = lw5_pattern_1({"title": "Form Variants example 1"})
print(example_1)
```

### LW6 Order Variants

#### LW6 Pattern 1

```python
def lw6_pattern_1(payload: dict) -> dict:
    return {
        "module": "LW6",
        "pattern": "1",
        "case_number": "2024-001507-DC",
        "year": 2026,
        "child_reference": "L.D.W.",
        "service": [
            "Emily A. Watson — 2160 Garland Dr, Norton Shores, MI 49441",
            "Pamela Rusco — 990 Terrace St, Muskegon, MI 49442",
        ],
        "payload": payload,
    }

example_1 = lw6_pattern_1({"title": "Order Variants example 1"})
print(example_1)
```

### LW7 Assembly Variants

#### LW7 Pattern 1

```python
def lw7_pattern_1(payload: dict) -> dict:
    return {
        "module": "LW7",
        "pattern": "1",
        "case_number": "2024-001507-DC",
        "year": 2026,
        "child_reference": "L.D.W.",
        "service": [
            "Emily A. Watson — 2160 Garland Dr, Norton Shores, MI 49441",
            "Pamela Rusco — 990 Terrace St, Muskegon, MI 49442",
        ],
        "payload": payload,
    }

example_1 = lw7_pattern_1({"title": "Assembly Variants example 1"})
print(example_1)
```

### LW8 Routing Variants

#### LW8 Pattern 1

```python
def lw8_pattern_1(payload: dict) -> dict:
    return {
        "module": "LW8",
        "pattern": "1",
        "case_number": "2024-001507-DC",
        "year": 2026,
        "child_reference": "L.D.W.",
        "service": [
            "Emily A. Watson — 2160 Garland Dr, Norton Shores, MI 49441",
            "Pamela Rusco — 990 Terrace St, Muskegon, MI 49442",
        ],
        "payload": payload,
    }

example_1 = lw8_pattern_1({"title": "Routing Variants example 1"})
print(example_1)
```
