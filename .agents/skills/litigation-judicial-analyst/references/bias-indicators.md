# Bias Indicators — litigation-judicial-analyst

## Bias Detection Framework for Michigan 14th Judicial Circuit

This reference provides a structured methodology for detecting, documenting,
and scoring judicial bias indicators in the Pigors v Watson litigation.

---

## Structural Bias Indicators

### SB-1: Outcome Disparity
**Definition**: Statistically different ruling rates favoring one party over
similarly situated parties in comparable cases.

**How to Measure**:
1. Compile all rulings in your case(s) by outcome (granted/denied)
2. Compare against rulings in comparable cases before same judge
3. Calculate grant rate for plaintiff-type motions vs. defendant-type motions
4. Statistical significance requires ≥ 10 comparable rulings

**Scoring**:
| Disparity | Score | Interpretation |
|-----------|-------|----------------|
| < 10% difference | 0–1 | Normal variation |
| 10–25% difference | 2–4 | Possible pattern — document |
| 25–50% difference | 5–7 | Probable pattern — investigate |
| > 50% difference | 8–10 | Strong evidence of bias |

**Lane A Application**: Compare McNeill's custody rulings for mothers vs.
fathers in comparable circumstances. Compare pro se vs. represented outcomes.

**Lane B Application**: Compare Hoopes' rulings in landlord-tenant cases.
Track plaintiff (tenant) vs. defendant (landlord) grant rates on dispositive motions.

---

### SB-2: Procedural Asymmetry
**Definition**: Different procedural treatment of similarly situated parties.

**Indicators**:
- One party granted extensions/continuances while other denied
- Different briefing page limits applied
- Different discovery latitude
- Different hearing time allocated
- Different standard of proof applied (explicitly or implicitly)

**Documentation Method**:
| Request | Party A Result | Party B Result | Date | Notes |
|---------|---------------|----------------|------|-------|
| Continuance | [Granted/Denied] | [Granted/Denied] | | |
| Extension | [Granted/Denied] | [Granted/Denied] | | |
| Discovery motion | [Granted/Denied] | [Granted/Denied] | | |

---

### SB-3: Temporal Patterns
**Definition**: Delayed rulings for one party, expedited for another.

**How to Measure**:
1. Track days between hearing and written order for each party's motions
2. Compare average delay for plaintiff motions vs. defendant motions
3. Flag orders issued same day (expedited) vs. those delayed > 30 days

**Red Flag**: If the judge routinely rules from the bench in favor of one
party but takes weeks to issue written orders for the other party's motions.

---

### SB-4: Access Disparity
**Definition**: Differential access to the court between parties.

**Indicators**:
- One party's motions scheduled for hearing promptly; other's delayed
- One party gets full oral argument time; other cut short
- One party allowed additional filings; other denied
- Chamber conferences with one party (ex parte risk)

---

### SB-5: Pro Se Penalty
**Definition**: Harsher treatment of self-represented litigants compared to
represented parties on procedural compliance.

**Michigan Standard**: While pro se litigants must follow the same rules as
attorneys, judges have a duty to ensure fair proceedings. A pattern of
dismissing pro se filings for minor defects while excusing similar defects
from represented parties indicates bias.

**Measurement**:
- Compare technical rejection rate for pro se vs. attorney filings
- Compare leniency on deadline compliance
- Compare judicial explanations given to pro se vs. represented parties

---

## Behavioral Bias Indicators

### BB-1: Tone Differential
**Definition**: Observably different vocal tone, language, or demeanor toward
different parties during hearings.

**Documentation**: Record immediately after each hearing:
- Judge's tone toward Party A: 1 (hostile) to 5 (warm)
- Judge's tone toward Party B: 1 (hostile) to 5 (warm)
- Specific language used (condescending, respectful, dismissive, etc.)
- Direct quotes when possible

### BB-2: Interruption Asymmetry
**Definition**: Judge interrupts one party significantly more than the other.

**Documentation**: Count during each hearing:
- Interruptions of Party A's argument: [count]
- Interruptions of Party B's argument: [count]
- Nature of interruptions (clarifying, hostile, dismissive, redirecting)

### BB-3: Credibility Presumption
**Definition**: Judge accepts one party's factual claims without scrutiny
while subjecting the other party's claims to extensive questioning.

**Indicators**:
- "I believe [Party A]" without evidentiary basis
- Requiring corroboration from one party but not the other
- Taking judicial notice of facts favorable to one party

### BB-4: Sua Sponte Assistance
**Definition**: Judge raises legal arguments or suggests procedural steps
that benefit one party without prompting.

**Michigan Rule**: Judges may explain procedure to pro se litigants, but
should not advocate for either party. Sua sponte assistance that benefits
one party and harms the other indicates bias.

### BB-5: Hostile Questioning
**Definition**: Judge asks adversarial, cross-examination-style questions
of one party while asking neutral or supportive questions of the other.

**Documentation**: Record questions asked by judge of each party, noting tone
and whether the question advances one party's case.

---

## Evidentiary Bias Indicators

### EB-1: Selective Admission
**Indicator**: Admitting weak or questionable evidence from one party while
excluding strong evidence from the other on similar grounds.

### EB-2: Weight Manipulation
**Indicator**: Giving disproportionate weight to evidence from one party in
findings of fact while minimizing comparable evidence from the other.

### EB-3: Burden Shifting
**Indicator**: Improperly shifting the burden of proof to the party that
does not bear it. In custody (Lane A), the movant bears the burden. In
housing (Lane B), the plaintiff bears the burden on each element.

### EB-4: Negative Inference
**Indicator**: Drawing negative inferences from silence or absence of
evidence against one party while not applying the same to the other.

### EB-5: Record Manipulation
**Indicator**: Off-record comments that influence proceedings, sealed
proceedings without proper cause, delayed transcript production.

---

## Composite Bias Score Calculation

```
For each hearing / proceeding, score each applicable indicator (0–10).

Structural Score = average(SB-1 through SB-5 scores)
Behavioral Score = average(BB-1 through BB-5 scores)
Evidentiary Score = average(EB-1 through EB-5 scores)

Composite Score = (Structural × 0.30) + (Behavioral × 0.35) + (Evidentiary × 0.35)

Interpretation:
  0.0–2.0: MINIMAL — Normal judicial discretion
  2.1–4.0: MODERATE — Pattern emerging, document and monitor
  4.1–6.0: SEVERE — Clear bias pattern, consider recusal motion
  6.1–8.0: EGREGIOUS — Systemic misconduct, file recusal + JTC
  8.1–10.0: EXTREME — Willful rights violation, recusal + JTC + federal complaint
```

---

## Evidence Preservation Protocol

For each bias indicator observed:
1. **Contemporaneous notes**: Write within 1 hour of observation
2. **Transcript request**: File for expedited transcript if significant
3. **Witness identification**: Note any other persons who observed the behavior
4. **Pattern log**: Add to running pattern database for the judge
5. **Cross-reference**: Link to specific Canon violation(s)
