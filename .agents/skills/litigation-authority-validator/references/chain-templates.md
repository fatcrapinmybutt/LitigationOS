# Authority Chain Templates — Litigation Authority Validator

## Overview

An authority chain is the complete support structure for a legal proposition.
Every factual claim in a brief, motion, or complaint must rest on a complete
authority chain. These templates provide the structure for common proposition
types in Pigors v Watson litigation.

---

## Template 1: Statute-Based Proposition

```
PROPOSITION: [Statement of law derived from statute]
│
├─ PRIMARY AUTHORITY
│   ├─ Statute: MCL § [number]
│   ├─ Specific subsection: MCL § [number]([subsection])
│   └─ Effective date: [date] (verify currency)
│
├─ INTERPRETIVE CASE LAW
│   ├─ Binding case: [Case], [vol] Mich [page], [pinpoint]; [NW2d cite]
│   │   └─ Parenthetical: (holding that [summary of holding])
│   └─ Supporting case: [Case], [vol] Mich App [page], [pinpoint]; [NW2d cite]
│       └─ Parenthetical: (applying [statute] to [similar facts])
│
├─ CURRENCY VERIFICATION
│   ├─ Statute last amended: [date/PA number]
│   ├─ Binding case: not overruled as of [date]
│   └─ Supporting case: not overruled as of [date]
│
└─ CHAIN SCORE: [1-5]
```

### Lane A Example: Best Interest Factor (j)

```
PROPOSITION: A court must consider each parent's willingness to facilitate
             a close relationship between the child and the other parent.
│
├─ PRIMARY AUTHORITY
│   ├─ Statute: MCL § 722.23(j)
│   ├─ Text: "The willingness and ability of each of the parties to
│   │        facilitate and encourage a close and continuing parent-child
│   │        relationship between the child and the other parent..."
│   └─ Effective date: Current (last amended 2023 PA 43)
│
├─ INTERPRETIVE CASE LAW
│   ├─ Binding: Demski v Petlick, 309 Mich App 404, 445-446;
│   │          873 NW2d 596 (2015)
│   │   └─ (holding factor (j) weighs against parent who
│   │       systematically interferes with other parent's relationship)
│   └─ Supporting: Berger v Berger, 277 Mich App 700, 716;
│                   747 NW2d 336 (2008)
│       └─ (noting factor (j) includes both willingness and ability
│           to facilitate the parent-child relationship)
│
├─ CURRENCY VERIFICATION
│   ├─ MCL § 722.23(j): Current — amended by 2023 PA 43
│   ├─ Demski: Good law as of [verification date]
│   └─ Berger: Good law as of [verification date]
│
└─ CHAIN SCORE: 5/5 (complete)
```

---

## Template 2: Case-Law-Based Proposition

```
PROPOSITION: [Legal principle derived from case law]
│
├─ PRIMARY CASE
│   ├─ Case: [Name], [vol] [reporter] [page], [pinpoint]; [parallel cite]
│   ├─ Holding: [specific holding relevant to proposition]
│   ├─ Court: [MSC/COA published/COA unpublished]
│   └─ Binding status: [binding/persuasive] in 14th Circuit
│
├─ SUPPORTING CASES
│   ├─ Case 2: [Name], [cite]
│   │   └─ Parenthetical: (following [Primary Case] and holding...)
│   └─ Case 3: [Name], [cite]
│       └─ Parenthetical: (applying [principle] to [facts])
│
├─ STATUTORY BASIS (if applicable)
│   └─ Underlying statute: MCL § [number]
│
├─ CURRENCY VERIFICATION
│   ├─ Primary case: [status — good law / distinguished / overruled]
│   ├─ Case 2: [status]
│   └─ Case 3: [status]
│
└─ CHAIN SCORE: [1-5]
```

### Lane B Example: Warranty of Habitability

```
PROPOSITION: Michigan's statutory covenant of habitability requires
             landlords to maintain premises in reasonable repair.
│
├─ PRIMARY CASE
│   ├─ Case: Allison v AEW Capital Management, LLP, 481 Mich 419, 425;
│   │        751 NW2d 8 (2008)
│   ├─ Holding: MCL 554.139 creates a non-waivable covenant that
│   │          landlords keep premises in reasonable repair
│   ├─ Court: Michigan Supreme Court
│   └─ Binding status: Binding on all Michigan courts
│
├─ SUPPORTING CASES
│   ├─ Teufel v Watkins, 267 Mich App 425, 432; 705 NW2d 164 (2005)
│   │   └─ (landlord's duty under MCL 554.139 is non-delegable)
│   └─ Benton v Dart Properties, 270 Mich App 437, 445;
│       715 NW2d 335 (2006)
│       └─ (tenant may recover damages for landlord's breach of
│           statutory duty under MCL 554.139)
│
├─ STATUTORY BASIS
│   └─ MCL § 554.139(1)(a)-(b)
│
├─ CURRENCY VERIFICATION
│   ├─ Allison: Good law as of [date]
│   ├─ Teufel: Good law as of [date]
│   └─ Benton: Good law as of [date]
│
└─ CHAIN SCORE: 5/5 (complete)
```

---

## Template 3: Procedural/Court Rule Proposition

```
PROPOSITION: [Procedural requirement or standard]
│
├─ COURT RULE
│   ├─ Rule: MCR [number]
│   ├─ Subrule: MCR [number]([subrule])
│   └─ Text: [relevant rule text]
│
├─ INTERPRETIVE AUTHORITY
│   ├─ Staff comment (if available): [summary]
│   └─ Case interpreting rule: [Name], [cite]
│       └─ Parenthetical: (interpreting MCR [number] to require...)
│
├─ LOCAL RULE (if applicable)
│   └─ 14th Circuit Local Rule: [number/description]
│
├─ CURRENCY VERIFICATION
│   ├─ Rule current: [yes/no — check administrative orders]
│   └─ Local rule current: [yes/no]
│
└─ CHAIN SCORE: [1-5]
```

---

## Template 4: Cross-Lane Convergence Proposition (Lane C)

```
PROPOSITION: [Statement connecting Lane A and Lane B facts/law]
│
├─ LANE A AUTHORITY
│   ├─ Statute/Case: [cite]
│   └─ Relevance to proposition: [explanation]
│
├─ LANE B AUTHORITY
│   ├─ Statute/Case: [cite]
│   └─ Relevance to proposition: [explanation]
│
├─ CONVERGENCE AUTHORITY
│   ├─ Bridge case/statute: [cite showing connection]
│   └─ Parenthetical: (recognizing that [Lane A topic]
│       is relevant to [Lane B topic])
│
├─ CONSISTENCY CHECK
│   ├─ Lane A position consistent: [yes/no]
│   ├─ Lane B position consistent: [yes/no]
│   └─ No contradictions: [confirmed/flagged]
│
├─ CURRENCY VERIFICATION
│   ├─ Lane A authority: [status]
│   ├─ Lane B authority: [status]
│   └─ Convergence authority: [status]
│
└─ CHAIN SCORE: [1-5]
```

---

## Template 5: Appellate Standard of Review

```
PROPOSITION: [Standard of review for specific appellate issue]
│
├─ STANDARD
│   ├─ Type: [de novo / clear error / abuse of discretion / great weight]
│   ├─ Applicable to: [type of issue being reviewed]
│   └─ Burden: [who bears the burden and what is it]
│
├─ DEFINING AUTHORITY
│   ├─ Primary: [seminal case defining this standard]
│   └─ MCR basis: MCR [number] (if rule-based)
│
├─ APPLICATION CASES
│   ├─ Case applying standard to similar issue: [cite]
│   │   └─ Parenthetical: (reviewing [type] under [standard])
│   └─ Case distinguishing standard: [cite]
│       └─ Parenthetical: (holding [different standard] applies when...)
│
├─ CURRENCY VERIFICATION
│   └─ All authorities current as of [date]
│
└─ CHAIN SCORE: [1-5]
```

---

## Chain Assembly Checklist

Before certifying any authority chain as complete:

1. [ ] Primary authority is binding in the 14th Circuit
2. [ ] At least one supporting authority reinforces the primary
3. [ ] All pinpoint citations verified against source
4. [ ] All parentheticals accurately summarize holdings
5. [ ] Currency verified for every authority in the chain
6. [ ] No cross-lane contradictions (for Lane C chains)
7. [ ] Format follows Michigan citation conventions
8. [ ] Chain score calculated and documented
