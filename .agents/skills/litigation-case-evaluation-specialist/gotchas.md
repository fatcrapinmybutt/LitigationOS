# Gotchas — litigation-case-evaluation-specialist

## Anti-Rationalization Table

| # | Excuse (The Lie) | Reality (The Truth) | Consequence |
|---|-----------------|---------------------|-------------|
| 1 | "Case evaluation is optional — we can skip it and go straight to trial." | MCR 2.403(A) allows courts to ORDER case evaluation. When ordered, participation is mandatory. Even when not ordered, case evaluation creates powerful leverage through MCR 2.403(O) sanctions — a rejected evaluation that the rejecting party fails to improve upon by 10% triggers attorney fee/cost sanctions. | Skipping a court-ordered case evaluation = contempt risk. Ignoring voluntary evaluation = losing the strategic advantage of MCR 2.403(O) sanction leverage. In Pigors v Watson, case evaluation sanctions could significantly affect the opposing party's litigation calculus. |
| 2 | "The case evaluation summary doesn't need to be detailed — evaluators will ask questions." | Evaluators receive multiple case summaries and have LIMITED time to review each. MCR 2.403(D) gives each side a summary presentation. A weak summary means evaluators base their award on the OPPOSING party's narrative. You get ONE chance to frame the case. | Evaluators adopt opposing party's facts and issue an unfavorable award. Once the award is issued, you must decide accept/reject within 28 days (MCR 2.403(K)). An unfavorable award you must reject triggers potential MCR 2.403(O) sanctions exposure. |
| 3 | "If we reject the evaluation, we just go to trial — there's no real downside to rejection." | MCR 2.403(O) sanctions are severe: the rejecting party pays the OTHER side's actual costs (attorney fees, expert fees, expenses) from the date of rejection IF the final verdict is not more favorable than the evaluation by at least 10%. For pro se litigants, this means paying opposing counsel's fees. | Rejecting an evaluation creates a 10% improvement threshold you MUST beat at trial. If you reject a $50,000 custody-related evaluation award and the trial result isn't at least 10% better, you owe Emily A. Watson's attorney fees from rejection date to trial. This can be tens of thousands of dollars. |
| 4 | "Case evaluation panels are neutral — we don't need to worry about evaluator selection." | MCR 2.403(D) allows objections to evaluators for cause. Evaluators may have conflicts, biases, or lack relevant expertise. In family law, an evaluator without custody experience may undervalue custody-specific evidence. You can and should vet proposed evaluators. | An evaluator unfamiliar with MCL 722.23 best-interest factors or the specific dynamics of custody disputes issues an uninformed award. This becomes the benchmark against which sanctions are measured. A bad evaluator = a bad benchmark = sanctions exposure. |
| 5 | "The MCR 2.403(O) sanctions calculation is straightforward — it's just attorney fees." | MCR 2.403(O) sanctions include: reasonable attorney fees, actual costs incurred from rejection date, AND expert witness fees. The calculation requires detailed billing records, and disputes over reasonableness are common. *Haliw v City of Sterling Heights*, 471 Mich 700 (2005) provides the framework. | Underestimating sanctions exposure leads to bad accept/reject decisions. A party who rejects thinking sanctions will be minimal may face a $20,000+ sanctions bill that exceeds the difference between the evaluation and trial result. |

---

## Common Failure Modes

### 1. Summary Preparation Failure
- **What happens**: Case evaluation summary is rushed, incomplete, or fails to address all claims and defenses with evidence citations
- **How to prevent**: Begin summary preparation 30+ days before evaluation; include key evidence, legal authority, and damages computation; practice the oral presentation
- **Lane risk**: HIGH — poor summary = unfavorable award = sanctions exposure on rejection

### 2. Accept/Reject Miscalculation
- **What happens**: Party rejects evaluation without properly calculating the 10% improvement threshold and sanctions exposure under MCR 2.403(O)
- **How to prevent**: Build detailed financial model: (evaluation award) × 1.10 = threshold; estimate opposing party's fees from rejection to trial; compare to expected trial outcome
- **Lane risk**: CRITICAL — wrong decision can cost tens of thousands in sanctions

### 3. Deadline Miss on Response
- **What happens**: Party fails to accept or reject within 28 days per MCR 2.403(K), resulting in deemed rejection
- **How to prevent**: Calendar the 28-day deadline immediately upon receiving evaluation award; file written response before deadline; serve on all parties
- **Lane risk**: HIGH — deemed rejection triggers MCR 2.403(O) sanctions exposure without deliberate strategic choice

### 4. Evaluator Conflict Undetected
- **What happens**: Evaluator has undisclosed relationship with opposing counsel, opposing party, or relevant witnesses
- **How to prevent**: Research proposed evaluators before hearing; file MCR 2.403(D) objection for cause if conflict exists; document basis for objection
- **Lane risk**: MEDIUM — biased evaluation becomes the sanctions benchmark

---

## Integration Gotchas

- **litigation-damages-calculator** must provide accurate damages estimates for accept/reject analysis
- **litigation-analysis-engine** provides evidence strength scoring needed for evaluation summary
- **litigation-case-strategy-architect** coordinates evaluation strategy with overall case strategy
- Accept/reject deadline must be tracked by **litigation-court-order-tracker** and **litigation-filing-countdown**
- MCR 2.403(O) sanctions interact with **litigation-fee-petition-engine** for calculation methodology
