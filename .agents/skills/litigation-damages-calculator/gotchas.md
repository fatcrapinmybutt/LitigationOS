# Gotchas — litigation-damages-calculator

## Anti-Rationalization Table

| # | Excuse (The Lie) | Reality (The Truth) | Consequence |
|---|-----------------|---------------------|-------------|
| 1 | "We'll figure out damages at the end — discovery and liability come first." | Damages must be calculated from the START because they drive: case evaluation positions (MCR 2.403), settlement demands, prayer for relief specificity, and strategic decisions about which claims to pursue. A claim worth $500 in damages may not justify the litigation cost. | Filing a complaint without specific damages calculations results in a weak prayer for relief that undermines credibility. When case evaluation comes (MCR 2.403), you need precise numbers for the accept/reject calculus. Vague damages = vague settlement posture = missed leverage. |
| 2 | "Non-economic damages are speculative — just focus on out-of-pocket costs." | Michigan law recognizes non-economic damages including emotional distress, loss of companionship, and dignitary harm. In civil rights cases (42 USC § 1983), non-economic damages are often the PRIMARY recovery. In custody cases, the harm to the parent-child relationship has real value that courts quantify. | Ignoring non-economic damages leaves significant recovery on the table. In Lane B (housing), habitability violations cause both economic (alternative housing, property damage) and non-economic (stress, health effects) harm. In Lane E (misconduct), the primary harm is dignitary and due process violation. |
| 3 | "Joint and several liability means we can collect everything from one defendant." | MCL 600.6304 modified joint and several liability in Michigan. For non-economic damages, each defendant is liable only for their proportional share unless they are ≥50% at fault. Economic damages retain full joint and several liability. The allocation affects who you sue and what you can collect. | Suing only one defendant when liability is shared means potentially recovering only their proportional share of non-economic damages. The damages model must account for per-defendant allocation under MCL 600.6304. |
| 4 | "Prejudgment interest is automatic — we don't need to request it." | Prejudgment interest under MCL 600.6013 must be REQUESTED and is calculated from the date the complaint is filed (or the date of the loss, depending on the claim). The rate is set by the state treasurer. Failure to request it = waiver. The calculation itself requires knowing the accrual date and applicable rate. | Leaving prejudgment interest off the prayer for relief waives potentially thousands of dollars. On a $50,000 damages claim pending for 2 years, prejudgment interest at the statutory rate adds significant recovery. |
| 5 | "The same damages model works for all six lanes." | Each lane has different damages frameworks: Lane A (custody) uses MCL 722.28 and fee-shifting; Lane B (housing) uses MCL 554.139 damages plus potential MCPA treble damages under MCL 445.911; Lane D (PPO) uses statutory damages; Lane E (misconduct) uses 42 USC § 1983 compensatory + punitive. Each framework has unique caps, multipliers, and proof requirements. | Using a one-size-fits-all damages model means miscalculating every lane. Housing damages include statutory habitability remedies; civil rights damages include § 1988 attorney fees; custody damages are primarily equitable. The calculator must model each lane independently. |

---

## Common Failure Modes

### 1. Double-Counting Across Lanes
- **What happens**: The same harm is counted in both Lane A (custody) and Lane B (housing) damage calculations, inflating the total
- **How to prevent**: Map each element of damage to ONE lane; convergence (Lane C) tracks totals but prevents overlap; use a damages allocation matrix
- **Lane risk**: HIGH for Lane C — convergence creates temptation to count everything everywhere

### 2. Statutory Cap Ignorance
- **What happens**: Damages calculation exceeds statutory caps that apply in specific contexts (e.g., governmental immunity caps, MCL 691.1407)
- **How to prevent**: Identify applicable caps for each claim before calculating; note caps in the damages model; calculate capped and uncapped scenarios
- **Lane risk**: MEDIUM — overcalculating damages when capped undermines credibility

### 3. Mitigation Failure
- **What happens**: Damages model doesn't account for plaintiff's duty to mitigate, which defendant will raise as defense
- **How to prevent**: For each damages category, document mitigation efforts; reduce claimed damages by amounts that reasonable mitigation would have prevented
- **Lane risk**: MEDIUM — failing to address mitigation in your own model lets defendant control the narrative

### 4. Fee Calculation for Pro Se Litigant
- **What happens**: Fee petition includes "attorney fees" for a pro se litigant who has no attorney, which is generally not recoverable per *Kay v Ehrler*, 499 US 432 (1991)
- **How to prevent**: Distinguish between recoverable costs (filing fees, service, copies) and non-recoverable attorney fees for pro se; focus on cost recovery and statutory damages
- **Lane risk**: HIGH — requesting non-recoverable fees damages credibility with the court

---

## Integration Gotchas

- **litigation-fee-petition-engine** handles the fee/cost component of damages — calculator provides the framework, fee engine provides the detail
- **litigation-case-evaluation-specialist** needs damages totals for accept/reject analysis — the 10% threshold under MCR 2.403(O) is measured against these numbers
- **litigation-asset-discovery-engine** provides the financial data needed to calculate actual losses and verify opponent's ability to pay
- **litigation-case-strategy-architect** uses damages calculations to prioritize claims — higher-value claims get more resources
- Each lane's damages must be separately verified before convergence aggregation in Lane C
