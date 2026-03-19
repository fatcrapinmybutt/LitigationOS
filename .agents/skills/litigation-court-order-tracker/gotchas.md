# Gotchas — litigation-court-order-tracker

## Anti-Rationalization Table

| # | Excuse (The Lie) | Reality (The Truth) | Consequence |
|---|-----------------|---------------------|-------------|
| 1 | "We know what the orders say — we don't need to catalog every provision." | In multi-lane litigation with dozens of orders, individual provisions get lost. A custody order may contain 15+ provisions covering exchanges, communication, holidays, decision-making, travel, and more. Each provision is independently enforceable and independently violable. Without a provision-level catalog, violations slip through. | Violations go undetected and undocumented. When you finally file a contempt motion, you discover the order language doesn't say what you thought it said, or you cite the wrong provision. The violation log is useless without precise provision tracking. |
| 2 | "Ex parte orders are temporary — no need to track them long-term." | Ex parte orders under MCR 3.207 remain in effect until the court modifies or vacates them. Some ex parte orders are never formally resolved at the hearing — they persist by default. Losing track of an ex parte order means losing track of enforceable obligations. | A party may violate an ex parte order that everyone "forgot" about because it was never formally vacated. Alternatively, you may be bound by an ex parte order you thought expired. Either way, failure to track = failure to enforce or comply. |
| 3 | "Tracking all six lanes is excessive — just track the active one." | Orders in one lane affect other lanes. A PPO (Lane D) restricts communication that affects custody exchanges (Lane A). A support order (Lane A) creates garnishment rights (Lane B). An appellate stay (Lane F) freezes trial court orders. Cross-lane order interactions require tracking ALL lanes simultaneously. | Missing a cross-lane order interaction causes compliance failures. If a Lane D PPO restricts contact but the Lane A custody order requires communication about exchanges, the conflict must be identified and resolved — which requires tracking both. |
| 4 | "The court clerk's register of actions is sufficient for order tracking." | The register lists orders chronologically but doesn't parse individual provisions, track compliance, or flag upcoming deadlines. It's a filing log, not a compliance management system. Effective order tracking requires: provision extraction, compliance status per provision, violation log, and deadline monitoring. | Relying on the register means discovering violations reactively instead of proactively. Compliance monitoring requires active tracking — checking each provision against evidence of compliance or violation on a regular cadence. |
| 5 | "We'll review orders when we need them — no need for a standing catalog." | Under deadline pressure, searching through dozens of orders for a specific provision wastes critical time. A motion to enforce requires citing the EXACT provision violated with the EXACT language. A pre-built catalog with provision-level indexing enables instant retrieval. | Missed deadlines because you couldn't find the relevant order provision in time. Weak contempt motions because you paraphrased the order instead of quoting it. Compliance failures because you forgot an obligation buried in paragraph 12 of a 15-page order. |

---

## Common Failure Modes

### 1. Provision-Level Tracking Gaps
- **What happens**: Order is cataloged at the document level but individual provisions aren't extracted, causing specific obligations to be missed
- **How to prevent**: Parse every order into individual provisions immediately upon entry; each provision gets its own compliance status and deadline
- **Lane risk**: HIGH — missed provisions = missed compliance obligations

### 2. Superseded Order Confusion
- **What happens**: A modified order supersedes an earlier order, but the tracker still references the old provisions
- **How to prevent**: When a new order issues, mark all affected prior provisions as superseded; link new provisions to old ones; maintain version history
- **Lane risk**: CRITICAL — enforcing a superseded provision or failing to comply with a new one are both problematic

### 3. Cross-Lane Conflict Detection Failure
- **What happens**: Orders in different lanes contain conflicting provisions (e.g., PPO restricts contact but custody order requires it)
- **How to prevent**: Run cross-lane conflict detection whenever a new order is entered; flag apparent conflicts for resolution
- **Lane risk**: HIGH — conflicting orders create compliance impossibility

### 4. Ex Parte Order Expiration Ambiguity
- **What happens**: An ex parte order has no clear expiration and both parties dispute whether it's still in effect
- **How to prevent**: Track ex parte orders with explicit status (active/expired/vacated); file motion to clarify if status is ambiguous; never assume expiration without court order
- **Lane risk**: MEDIUM — ambiguous order status creates enforcement uncertainty

---

## Integration Gotchas

- **litigation-contempt-specialist** depends on the order catalog for contempt motion drafting — every contempt motion must cite specific provisions
- **litigation-filing-countdown** tracks order-derived deadlines — new orders create new deadlines that must be propagated
- **litigation-appellate-record-specialist** needs the complete order catalog for the register of actions verification
- **litigation-case-strategy-architect** uses the order catalog to identify leverage points and compliance failures
- MCR 2.602 governs the form and entry of orders — every tracked order must comply with these requirements
