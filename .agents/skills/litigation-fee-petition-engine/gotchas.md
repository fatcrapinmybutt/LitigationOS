# Gotchas — litigation-fee-petition-engine

## Anti-Rationalization Table

| # | Excuse (The Lie) | Reality (The Truth) | Consequence |
|---|-----------------|---------------------|-------------|
| 1 | "Pro se litigants can recover attorney fees just like represented parties." | *Kay v Ehrler*, 499 US 432 (1991) held that pro se litigants generally CANNOT recover attorney fees. This applies to most fee-shifting statutes. Andrew James Pigors can recover actual litigation COSTS (filing fees, service costs, copies, transcripts) but NOT the equivalent of attorney time. Exception: 42 USC § 1988 has been narrowly interpreted, and some state statutes may differ. | Requesting attorney fees as a pro se litigant = instant credibility loss. The court will deny the fee request AND the opposing party may use it to characterize filings as unreasonable. Focus fee petitions on recoverable costs and statutory sanctions, not phantom attorney hours. |
| 2 | "The lodestar calculation is simple — hours times rate equals fees." | The lodestar is the STARTING POINT, not the end. After calculating hours × rate, courts apply adjustments: reduce for duplicative work, block billing discounts, excessive research, travel time, unsuccessful claims, and the degree of success. *Smith v Khouri*, 481 Mich 519, 530-531 (2008) lists 8 factors. | Submitting an unadjusted lodestar invites opposing counsel to make the adjustments for you — and they'll reduce aggressively. Present a pre-adjusted lodestar that accounts for known weaknesses. Courts respect petitioners who self-regulate. |
| 3 | "All time spent on the case is compensable — we should bill for everything." | Only time reasonably expended on SUCCESSFUL claims is compensable. Time spent on claims you lost, excessive research, administrative tasks, and intra-office conferences must be excluded. *Hensley v Eckerhart*, 461 US 424, 434 (1983): "hours that are excessive, redundant, or otherwise unnecessary" must be excluded. | Inflated fee petitions get slashed by the court, sometimes dramatically. A petition requesting $50,000 that gets reduced to $15,000 signals to the court that the petitioner was unreasonable. Self-editing before filing produces better results than judicial editing. |
| 4 | "MCR 2.403(O) sanctions automatically include all litigation costs." | MCR 2.403(O) sanctions cover costs incurred FROM THE DATE OF REJECTION. Pre-rejection costs are excluded. The calculation requires: (1) identifying the rejection date, (2) isolating post-rejection costs, (3) proving each cost was reasonably incurred, and (4) showing the costs relate to the litigation. | Requesting pre-rejection costs in an MCR 2.403(O) petition = partial denial and credibility damage. The court will require a detailed breakdown showing when each cost was incurred. Maintain separate time records for pre-rejection and post-rejection periods. |
| 5 | "Cost bills are automatic after winning — just submit the total and the court will approve." | MCR 2.625 cost bills must be specific and documented. Each cost item must be identified, explained, and supported by receipts or records. The opposing party can challenge each item. Courts regularly reduce cost bills that include improper items. | Poorly documented cost bills get objected to and reduced. Filing fees without receipts, mileage without logs, and copy costs without invoices all get denied. Document every expenditure contemporaneously. |

---

## Common Failure Modes

### 1. Pro Se Fee Recovery Overreach
- **What happens**: Pro se litigant requests "attorney fees" for their own time, which courts consistently deny
- **How to prevent**: Focus on recoverable costs (MCR 2.625), statutory sanctions, and specific fee-shifting provisions that may apply to non-attorney costs; never characterize personal time as "attorney fees"
- **Lane risk**: HIGH — damages credibility across ALL filings if fee petition is seen as unreasonable

### 2. Insufficient Time Records
- **What happens**: Fee petition submitted without contemporaneous time records, resulting in court reducing hours to estimate
- **How to prevent**: Keep detailed, contemporaneous time records from day one; record date, task description, time spent, and which claim/issue the time relates to
- **Lane risk**: HIGH — courts can reduce by 50%+ when records are vague or reconstructed

### 3. Failure to Segregate by Claim
- **What happens**: Time spent on unsuccessful claims mixed with successful claims, and court reduces the entire petition
- **How to prevent**: Track time by claim/issue from the beginning; when preparing the petition, include only time for prevailing claims; address mixed-result scenarios explicitly
- **Lane risk**: MEDIUM — *Hensley* requires segregation, and failure to do it invites reduction

### 4. Missed MCR 2.625 Deadline
- **What happens**: Cost bill not filed within 28 days after judgment per MCR 2.625(B), resulting in waiver
- **How to prevent**: Calendar the 28-day cost bill deadline immediately upon favorable judgment; prepare cost bill in advance of judgment so it's ready to file
- **Lane risk**: HIGH — missed deadline = waived costs

---

## Integration Gotchas

- **litigation-damages-calculator** provides the overall damages framework into which fee recovery fits
- **litigation-case-evaluation-specialist** must coordinate MCR 2.403(O) sanctions calculations with fee engine
- **litigation-court-order-tracker** monitors fee-related orders and deadlines
- **litigation-filing-countdown** tracks the 28-day MCR 2.625 cost bill deadline
- Fee petitions require different treatment in each lane — § 1988 fees (Lane E) are different from MCR 3.206(D) fees (Lane A)
