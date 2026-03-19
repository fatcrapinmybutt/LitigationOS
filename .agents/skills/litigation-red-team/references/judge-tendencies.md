# Judge Tendencies — litigation-red-team

## Judicial Tendency Analysis for Red Team Review

This reference provides judge-specific red team considerations for the 14th
Judicial Circuit. Understanding judicial tendencies allows red team review
to predict how a judge will react to both your filing and opposing attacks.

---

## Judge McNeill — 14th Circuit, Family Division

### General Tendencies
| Category | Observed Tendency |
|----------|------------------|
| Procedural strictness | High — enforces MCR formatting, deadlines, service requirements |
| Pro se tolerance | Moderate — explains requirements but expects compliance |
| Hearing style | Structured — expects organized presentation |
| Order turnaround | Standard — follows 14th Circuit timelines |
| Continuance grants | Selective — requires good cause |

### Motion-Specific Tendencies
| Motion Type | Tendency |
|-------------|----------|
| Custody modification | Strict Vodvarka application — must clear threshold |
| PPO modification | Reviews evidentiary basis carefully |
| Discovery motions | Expects meet-and-confer before filing |
| Contempt | Requires clear evidence of willful violation |
| Emergency/ex parte | High bar — true emergency must be shown |

### Red Team Implications — McNeill
1. **Format your filing perfectly** — McNeill will notice defects before reading substance
2. **Clear Vodvarka first** — if proper cause section is weak, nothing else matters
3. **Organize exhibits meticulously** — McNeill references exhibit indexes during hearings
4. **Anticipate FOC reliance** — McNeill gives weight to FOC recommendations
5. **Avoid emotional language** — McNeill responds to factual, evidence-based arguments
6. **Brief length matters** — McNeill has enforced page limits; be concise
7. **Service must be perfect** — defective service will be caught and filing rejected

### Predicted Judicial Concerns — Lane A
- "Has proper cause been established under Vodvarka?"
- "What does the FOC recommendation say?"
- "Is this the appropriate venue for this request?"
- "Has the child's established custodial environment been addressed?"
- "Are the best interest factors individually analyzed?"

---

## Judge Hoopes — 14th Circuit, Civil Division

### General Tendencies
| Category | Observed Tendency |
|----------|------------------|
| Procedural strictness | Moderate to high — follows MCR but practical |
| Pro se tolerance | Standard — follows law but may explain procedure |
| Hearing style | Efficient — values concise oral argument |
| Order turnaround | Standard |
| Continuance grants | Reasonable — balances fairness with docket management |

### Motion-Specific Tendencies
| Motion Type | Tendency |
|-------------|----------|
| Summary disposition | Follows MCR 2.116 standards closely |
| Discovery disputes | Expects proportionality and meet-and-confer |
| TRO/injunctive relief | Requires all four factors clearly addressed |
| Class/representative | Standard certification analysis |
| Corporate motions | Familiar with entity-level litigation |

### Red Team Implications — Hoopes
1. **Address corporate defenses head-on** — Hoopes sees corporate defendants regularly
2. **Proportionality matters** — discovery requests must be proportional to claims
3. **Summary disposition risk is real** — Hoopes will grant if elements aren't met
4. **Concise argument wins** — Hoopes values efficiency; don't over-brief
5. **Injunctive relief requires all factors** — irreparable harm, likelihood of success, balance of equities, public interest
6. **Anticipate sophisticated defense** — Hoopes expects both sides to be prepared

### Predicted Judicial Concerns — Lane B
- "Has the plaintiff established standing and privity?"
- "Were notice requirements under MCL 554.139 satisfied?"
- "What is the evidentiary basis for claimed damages?"
- "Is there a factual dispute precluding summary disposition?"
- "Has the plaintiff demonstrated irreparable harm for injunctive relief?"

---

## Red Team Judicial Filter

### Pre-Filing Judicial Check
Before submitting any filing to red team review, apply the judicial filter:

```
For each section of the filing:
  1. Would Judge [name] understand this paragraph on first reading?
  2. Would Judge [name] find the legal authority persuasive?
  3. Would Judge [name] find the factual basis sufficient?
  4. Is this section free of emotional language that Judge [name] would discount?
  5. Does this section comply with Judge [name]'s known procedural preferences?
```

### Scoring
- 5/5 = GREEN — section likely to be well-received
- 3–4/5 = YELLOW — section needs revision
- 0–2/5 = RED — section likely to trigger negative judicial reaction

---

## Appellate Judges — Michigan Court of Appeals

### General COA Tendencies (14th Circuit Appeals)
- Panel assignment is random — cannot predict specific judges
- Standard of review matters enormously — abuse of discretion (custody) vs. de novo (legal questions)
- Record preservation is mandatory — if it's not in the trial court record, it doesn't exist on appeal
- Briefs must comply with MCR 7.212 strictly — non-compliant briefs may be stricken

### Red Team for Appeal Preservation
Every filing should be reviewed for appellate preservation:
1. Is the legal argument clearly stated for appellate review?
2. Are constitutional issues raised (or they're waived)?
3. Is the standard of review identified?
4. Are factual findings supported by record evidence?
5. Are objections timely and specific?
