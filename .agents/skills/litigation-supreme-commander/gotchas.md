# Gotchas — litigation-supreme-commander

## Anti-Rationalization Table

| # | Excuse (The Lie) | Reality (The Truth) | Consequence |
|---|-----------------|---------------------|-------------|
| 1 | "The motion is mostly complete — I'll skip the verification/certificate of service." | MCR 1.109(D)(3) requires a verification on specific motion types, and MCR 2.107 requires proof of service on ALL filings served on opposing parties. A motion without service proof may be stricken. | The court clerk rejects the filing or opposing counsel moves to strike. Days lost, deadlines potentially missed, and the appearance of incompetence before the judge. |
| 2 | "Page limits are just guidelines — the court will understand I need more space." | MCR 7.212(B) imposes a 50-page limit for appellate briefs. MCR 2.119(A)(2) limits trial-level briefs to 20 pages unless leave is granted. These are HARD limits. TrueFiling and MiFile enforce them. | E-filing system rejects the document. If filed by mail, opposing counsel moves to strike the excess pages. The court may refuse to read beyond the limit. |
| 3 | "I served the motion by email — that counts as electronic service." | MCR 2.107(C)(4) requires consent to electronic service. Unless Jennifer Barnes (P55406 — now withdrawn) or successor counsel consented to email service, you must serve by mail or personal delivery. Emily Watson (pro se) must be served per MCR 2.105. | Service is defective. The motion is not properly before the court. Opposing party can claim lack of notice and vacate any resulting order. |
| 4 | "The caption format doesn't really matter — substance over form." | Michigan courts strictly enforce caption requirements under MCR 1.109(D)(1). The caption must include: court name, case number, case title with all parties, judge name, and document title. Pro se filings are held to the same standard. | Filing rejected by clerk. Even if accepted, a sloppy caption signals to the judge that the filer doesn't know the rules — damaging credibility on substantive arguments. |
| 5 | "I'll cite the statute without checking if it was amended recently." | Michigan statutes are amended frequently. MCL 722.23 (best-interest factors) was amended by PA 2023 No. 36. MCR rules change by administrative order (e.g., 2025-08, 2025-42). Always verify current version. | Citing a repealed or amended provision destroys credibility. Opposing counsel will highlight the error. The court may question whether other citations are reliable. |
| 6 | "This is an emergency — I don't need to follow the normal motion briefing schedule." | MCR 2.119(F) has specific requirements for ex parte and emergency motions, including a showing of irreparable harm and why notice could not be given. You can't just label something "emergency" to skip the briefing schedule. | Motion denied for failure to meet emergency standard. Worse, the court may view future legitimate emergency motions with skepticism. |
| 7 | "I already filed this document in the custody case — I can reference it in the PPO case without refiling." | Each case (2024-001507-DC and 2023-5907-PP) has its own record. Documents filed in one case are NOT part of the record in another unless separately filed or incorporated by reference with proper motion. | Arguments based on documents not in the record are unsupported. Appellate courts will not consider evidence outside the lower court record (MCR 7.210(A)). |

---

## Common Failure Modes

### 1. Incomplete Motion Package
- **What happens**: Agent drafts the motion body but omits required components: proposed order, brief in support, notice of hearing, proof of service, verification, or exhibits.
- **How to prevent**: Use the motion-practice-checklist reference. Every motion type has a component checklist. Verify ALL components before marking the filing as complete.
- **Lane risk**: HIGH for Lanes A and D — custody and PPO motions have the most components.

### 2. Wrong Court Rule Set Applied
- **What happens**: Agent applies MCR 7.200 (appellate) rules to a trial-level motion, or applies MCR 2.119 (motion practice) rules to an appellate filing.
- **How to prevent**: First determine the court: 14th Circuit → MCR 2.xxx/3.xxx; COA → MCR 7.2xx; MSC → MCR 7.3xx; USDC → FRCP/local rules. Match rule set to court.
- **Lane risk**: HIGH for Lane F (appellate) — rules are completely different from trial level.

### 3. Service Failure on Pro Se Party
- **What happens**: Agent prepares service on Jennifer Barnes (P55406) who has WITHDRAWN. Emily Watson is now pro se and must be served directly at her address (2160 Garland Drive, Norton Shores, MI 49441).
- **How to prevent**: Always check current representation status in DB before preparing service. Barnes withdrew — all service goes directly to Emily Watson.
- **Lane risk**: HIGH for all lanes — defective service voids the filing's legal effect.

### 4. Deadline Miscalculation
- **What happens**: Agent calculates motion response time as 14 days but fails to exclude weekends/holidays per MCR 1.108, or uses wrong timeline for appeals (21 days for claim of appeal per MCR 7.204(A)(1)).
- **How to prevent**: Always apply MCR 1.108 time computation rules. When period is less than 7 days, exclude weekends and holidays. Use `deadline_dashboard` MCP tool for automated computation.
- **Lane risk**: HIGH for Lane F (appellate) — jurisdictional deadlines are absolute and cannot be extended.

### 5. Missing Proposed Order
- **What happens**: Motion filed without attached proposed order. Many judges in the 14th Circuit require a proposed order with every motion.
- **How to prevent**: Check local court rules for 14th Judicial Circuit. Include proposed order with every dispositive motion as a default practice.
- **Lane risk**: MEDIUM for all lanes — some judges return the motion unfiled without the proposed order.

---

## Integration Gotchas

- **litigation-supreme-commander feeds INTO OMEGA-LITIGATION-SUPREME M4 (Filing Factory)** — this skill provides the detailed drafting logic that M4 orchestrates. Don't duplicate M4's QA gates; let OMEGA-SUPREME handle final QA.
- **Always check `filing_readiness` MCP tool before assembling** — it reports which required components are missing for a given vehicle/filing type.
- **Service tracking is separate from filing** — use `service-tracker` agent or `litigation_service_check` MCP tool to verify all parties have been served after filing.
- **When Barnes withdrew, the certificate of service template changed** — update the service address from Barnes Law Firm to Emily Watson's personal address for ALL pending and future filings.
- **Pro se filings get extra scrutiny** — courts construe pro se filings liberally (Estelle v Gamble) but still require compliance with court rules. Don't rely on liberal construction as an excuse for sloppy work.
