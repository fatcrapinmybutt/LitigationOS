---
name: OMEGA-EXPERT-WITNESS
description: >-
  Expert witness management for Michigan family law litigation. Covers Daubert/MRE 702
  qualification analysis, expert report review, cross-examination preparation, rebuttal
  expert strategy, custody evaluator challenges, GAL accountability, and forensic expert
  coordination. Integrates with OMEGA-LITIGATION-SUPREME for filing and OMEGA-EVIDENCE
  for exhibit management.
category: litigation
version: "1.0.0"
triggers:
  - expert witness
  - Daubert
  - MRE 702
  - qualification
  - custody evaluator
  - GAL
  - guardian ad litem
  - forensic
  - rebuttal expert
  - cross-examination expert
  - expert report
  - IME
  - independent medical
lanes:
  - "A: Watson/Custody"
  - "D: PPO"
  - "E: Judicial Misconduct"
  - "F: Appellate"
court: "14th Judicial Circuit, Muskegon County; Michigan COA"
case: Pigors v Watson
metadata:
  tier: "1 (Litigation Core)"
  author: andrew-pigors + copilot-omega
  jurisdiction: Michigan
---

# 🔬 OMEGA-EXPERT-WITNESS v1.0

> **Expert Witness Management for Michigan Family Law**
> Daubert/MRE 702 · Custody Evaluators · GAL Accountability · Cross-Exam Prep
> Case: Pigors v Watson · Lanes A, D, E, F

## Module EW1: Daubert/MRE 702 Qualification Analysis

### Michigan Standard (Daubert adopted via Gilbert v DaimlerChrysler)
Michigan applies Daubert through MRE 702 (amended 2004):
1. **Qualified** — education, experience, training, knowledge
2. **Reliable methodology** — testable, peer-reviewed, known error rate, generally accepted
3. **Relevant** — testimony assists trier of fact, fits the facts of the case
4. **Sufficient factual basis** — opinion based on sufficient facts/data

### Qualification Challenge Workflow
```
Expert disclosed →
  ├─ Review CV/credentials for actual qualifications
  ├─ Check: licensed in Michigan? Board certified?
  ├─ Review: prior testimony history (Daubert challenges)
  ├─ Assess: methodology used (standardized? peer-reviewed?)
  ├─ Check: sufficient factual basis (did they review all records?)
  └─ Decision: challenge qualification OR attack methodology at trial
```

### Motion in Limine Template (Expert Exclusion)
```
MOTION IN LIMINE TO EXCLUDE [EXPERT] TESTIMONY
I. Expert's qualifications are insufficient (MRE 702(a))
II. Methodology is unreliable (MRE 702(b) — Daubert factors)
III. Opinion lacks sufficient factual basis (MRE 702(c))
IV. Testimony would mislead jury / unfairly prejudicial (MRE 403)
Authority: Gilbert v DaimlerChrysler, 470 Mich 749 (2004)
           Edry v Adelman, 486 Mich 634 (2010)
           People v Kowalski, 492 Mich 106 (2012)
```

## Module EW2: Custody Evaluator Challenges

### Common Challenge Grounds (Michigan Family Law)
| Ground | Authority | Application |
|--------|-----------|------------|
| Bias/lack of neutrality | MCR 3.111(B) | Evaluator met only with one party |
| Inadequate investigation | MCL 722.27a | Failed to interview key witnesses |
| Ignored evidence | MCL 722.23 (best interest factors) | Disregarded documented incidents |
| Unqualified methodology | MRE 702 / Daubert | Used non-standardized instruments |
| Conflict of interest | AFCC Guidelines | Prior relationship with a party |
| Failed to review records | Standard of practice | Ignored court orders, police reports |

### Challenge Procedure
1. File **Motion to Strike Custody Evaluation** (or portions)
2. Request **Daubert hearing** on evaluator's methodology
3. Cross-examine evaluator on:
   - What records were reviewed vs. available
   - Which witnesses were contacted
   - Methodology/instruments used and their validity
   - Whether both parties got equal time/access
4. If evaluation biased → request **new independent evaluation**

## Module EW3: GAL Accountability

### Guardian ad Litem Standards (Michigan)
- MCL 712A.17d — GAL duties and powers
- SCAO Administrative Order 2012-7 — GAL standards
- MCR 3.917 — GAL in child protective proceedings

### GAL Challenge Checklist
```
□ Did GAL investigate both households?
□ Did GAL interview the child privately?
□ Did GAL review all relevant records?
□ Did GAL meet with both parents?
□ Did GAL disclose any conflicts of interest?
□ Did GAL file timely reports?
□ Is GAL recommendation supported by facts in record?
□ Did GAL consider ALL best interest factors (MCL 722.23)?
```

### Motion to Remove GAL
Grounds: bias, failure to investigate, conflict of interest, exceeding authority
Authority: Harvey v Harvey, 470 Mich 186 (2004); MCR 3.916

## Module EW4: Cross-Examination Preparation

### Expert Cross-Exam Framework
```
Phase 1 — Establish limitations
  "You didn't review [X document], correct?"
  "You only spent [N hours] on this evaluation?"
  "You didn't interview [key witness]?"

Phase 2 — Challenge methodology
  "The instrument you used — what's its error rate?"
  "Is that methodology peer-reviewed?"
  "Have you used this same methodology in prior cases?"

Phase 3 — Expose bias
  "How many times have you testified for [opposing party's attorney]?"
  "Were you referred by [attorney name]?"
  "Your report was completed before you interviewed my client?"

Phase 4 — Undermine conclusions
  "If [fact X] were true, would that change your opinion?"
  "Your conclusion doesn't account for [documented incident]?"
```

## Module EW5: Rebuttal Expert Strategy

### When to Retain Rebuttal Expert
- Opposing expert makes critical claims you can't counter with lay testimony
- Custody evaluation contains methodological errors requiring expert critique
- Forensic evidence (financial, digital, medical) needs counter-expert
- GAL report relies on disputed psychological claims

### Michigan Rebuttal Expert Rules
- MCR 2.302(B)(4) — Discovery of expert opinions
- MCR 2.401(I)(2) — Expert witness disclosure deadlines
- MRE 703 — Bases of expert opinion
- Rebuttal experts may be disclosed after opponent's expert disclosures

### Cost-Effective Alternatives for Pro Se Litigant
1. **Deposition of opposing expert** — force them to defend methodology under oath
2. **Published authorities** — submit peer-reviewed articles contradicting expert
3. **Cross-examination** — effective cross can neutralize expert without rebuttal
4. **Judicial notice** — request court take judicial notice of contradicting facts (MRE 201)
5. **Amicus support** — organizations that provide expert support to pro se parties

## Module EW6: Specific Expert Types

### Custody/Psychological Evaluator
- Must be licensed psychologist (MCL 333.18201+)
- Standard instruments: MMPI-2, PAI, MCMI-IV, Rorschach (controversial)
- Challenge: validity of instruments for custody determination

### Forensic Accountant
- Hidden income, asset tracing, property valuation
- Child support calculation disputes
- Business valuation in equitable distribution

### Digital Forensics Expert
- Social media evidence authentication
- Text message/email chain verification
- Metadata analysis, timestamp verification
- Device forensics for deleted communications

### Domestic Violence Expert
- Pattern analysis, lethality assessment
- Impact on children (Lundy Bancroft framework)
- Counter: false DV allegations, coercive control misapplication

## Global Rules

### Anti-Hallucination
- NEVER fabricate expert names, credentials, or testimony
- NEVER invent case citations — verify against authority_master_index
- If expert information unknown, use [VERIFY — identify expert] placeholder
- Party names: Andrew James Pigors (plaintiff), Emily A. Watson (defendant), L.D.W. (child)

### DB-First
- Query litigation_context.db for existing expert-related evidence
- Check evidence_quotes for expert testimony transcripts
- Check docket_events for expert disclosure deadlines

### Integration Points
- Filing motions → OMEGA-LITIGATION-SUPREME M4
- Evidence exhibits → OMEGA-EVIDENCE
- Legal research → OMEGA-RESEARCH
- Cross-exam prep → OMEGA-LITIGATION-SUPREME M10 (Adversary Intel)
