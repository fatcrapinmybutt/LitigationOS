# Gotchas — litigation-foc-challenge-engine

## Anti-Rationalization Table

| # | Excuse (The Lie) | Reality (The Truth) | Consequence |
|---|-----------------|---------------------|-------------|
| 1 | "The FOC recommendation is just a suggestion — the judge decides independently." | While technically true that the judge makes the final decision, FOC recommendations carry ENORMOUS weight in practice. Judges rely heavily on FOC investigations because they provide the factual foundation for custody and support decisions. An unchallenged FOC recommendation becomes the de facto order in the vast majority of cases. | Failing to challenge an unfavorable FOC recommendation means the judge will likely adopt it without significant modification. In Pigors v Watson, if the FOC recommends against Andrew James Pigors' position, the 21-day challenge window (MCR 3.218(A)) is the ONLY opportunity to prevent that recommendation from becoming an order. |
| 2 | "We missed the 21-day objection deadline — we'll address it at the next hearing." | The 21-day deadline under MCR 3.218(A) is JURISDICTIONAL for objections to FOC recommendations. Missing it means the recommendation can be adopted without a hearing on your objections. While you can raise issues at subsequent proceedings, you've lost the right to a de novo hearing on the specific recommendation. | The FOC recommendation becomes the order. Your objections are waived. The only recourse is a motion to modify based on changed circumstances (MCL 722.27), which requires meeting a higher threshold than an objection would have. The 21-day deadline is one of the most critical in family law practice. |
| 3 | "The FOC investigator was neutral — their recommendation must be fair." | FOC investigators are human and bring biases, time constraints, and limited information to their investigations. They may not have reviewed all relevant documents, may have relied on incomplete interviews, and may have applied incorrect legal standards. MCR 3.218 exists specifically because FOC recommendations need challenge mechanisms. | Accepting a biased or uninformed recommendation without challenge. FOC investigators sometimes conduct superficial investigations due to caseload pressure. They may not have seen critical evidence, may have given undue weight to one party's narrative, or may have applied incorrect child support calculations. |
| 4 | "FOIA requests to the FOC are aggressive and will antagonize the investigator." | FOIA requests (MCL 15.231) are your LEGAL RIGHT and a critical discovery tool. The FOC is a government agency subject to FOIA. Requesting their file reveals: what documents they reviewed, who they interviewed, their notes, and their analytical process. This information is essential for an effective challenge. | Not requesting the FOC file means challenging the recommendation blind. You don't know what the investigator considered, what they missed, or what errors they made. A FOIA request costs $0-$50 and provides the ammunition for an effective MCR 3.218 objection. |
| 5 | "We can't opt out of FOC services — they're mandatory." | MCL 552.505b allows parties to opt out of FOC services by mutual agreement in certain circumstances. Opt-out removes the FOC as intermediary for support collection and eliminates FOC enforcement involvement. However, opt-out doesn't eliminate the court's authority — it shifts administration to the parties. | Not knowing about opt-out means remaining subject to FOC involvement when it may not serve your interests. In cases where the FOC investigator has demonstrated bias, opting out (if both parties agree) removes that biased intermediary from the process. |

---

## Common Failure Modes

### 1. Missed 21-Day Objection Deadline
- **What happens**: Party discovers unfavorable FOC recommendation but files objection after the MCR 3.218(A) 21-day window closes
- **How to prevent**: Calendar a 21-day deadline the INSTANT any FOC recommendation is received; begin drafting objection immediately; file within 14 days to allow time for corrections
- **Lane risk**: CRITICAL — missed deadline = waived objection = recommendation becomes order

### 2. Generalized Objection Without Specifics
- **What happens**: Objection says "the recommendation is wrong" without identifying specific errors in fact-finding, legal analysis, or methodology
- **How to prevent**: Parse the recommendation provision-by-provision; identify every factual error, every legal misapplication, and every piece of evidence the investigator ignored; cite MCL and MCR authority for each objection
- **Lane risk**: HIGH — vague objections are overruled; specific objections force the court to address each point

### 3. Failure to Request De Novo Hearing
- **What happens**: Objection filed but party doesn't request (or doesn't prepare for) the de novo hearing under MCR 3.218(B)
- **How to prevent**: Explicitly request de novo hearing in the objection; prepare evidence and testimony for the hearing as if it were a mini-trial; the hearing is your chance to present the full picture
- **Lane risk**: HIGH — without a hearing, the court decides on papers alone, which disadvantages the objecting party

### 4. Ignoring FOC Investigator Bias Documentation
- **What happens**: Party experiences bias during FOC investigation but doesn't document it, losing the evidence for challenge
- **How to prevent**: Document every FOC interaction contemporaneously: what was said, what was asked, what documents were requested, tone and demeanor; request the FOC file via FOIA immediately after recommendation
- **Lane risk**: HIGH for Lane A — FOC investigator bias directly affects custody recommendations

### 5. Not Connecting Objection to MCL 722.23 Factors
- **What happens**: Objection challenges the recommendation but doesn't tie the challenge to specific best-interest factors, making it sound like mere disagreement
- **How to prevent**: Structure the objection around the 12 best-interest factors; show how the FOC got each relevant factor wrong; cite evidence that supports your position on each factor
- **Lane risk**: HIGH — judges evaluate custody through the MCL 722.23 lens; objections must use the same framework

---

## Integration Gotchas

- **litigation-child-support-analyzer** provides alternative support calculations to challenge FOC support recommendations
- **litigation-court-order-tracker** monitors the 21-day objection deadline and tracks FOC-related orders
- **litigation-evidence-authentication** ensures evidence presented at the de novo hearing meets MRE standards
- **litigation-filing-countdown** tracks the 21-day deadline as CRITICAL — no extensions available
- **litigation-analysis-engine** provides evidence scoring to support specific factor-by-factor challenges
