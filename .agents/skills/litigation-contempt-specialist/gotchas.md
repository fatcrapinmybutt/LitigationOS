# Gotchas — litigation-contempt-specialist

## Anti-Rationalization Table

| # | Excuse (The Lie) | Reality (The Truth) | Consequence |
|---|-----------------|---------------------|-------------|
| 1 | "Contempt is simple — they violated the order, so file a motion and the court will hold them in contempt." | Contempt has strict procedural requirements. Civil contempt (MCL 600.1701) requires proof that: (1) a valid order existed, (2) the party had knowledge of the order, (3) the party had the ABILITY to comply, and (4) the party willfully failed to comply. *In re Contempt of Dougherty*, 429 Mich 81 (1987). Missing any element = motion denied. | Filing a contempt motion without establishing all four elements wastes the court's time and damages credibility. Judge McNeill will scrutinize the ability-to-comply element closely. If Emily A. Watson can show inability (job loss, illness), the motion fails regardless of the violation. |
| 2 | "Civil and criminal contempt are the same — the distinction doesn't matter." | Civil contempt coerces future compliance; criminal contempt punishes past violations. The distinction determines: burden of proof (preponderance vs. beyond reasonable doubt), right to jury (no for civil, yes for criminal if >6 months), purge conditions (required for civil, not for criminal), and procedural requirements. *Sword v Sword*, 399 Mich 367 (1976). | Using criminal contempt procedures in a civil contempt motion (or vice versa) = procedural defect that gets the motion denied. In family law, civil contempt with purge conditions is almost always the right tool because the goal is compliance, not punishment. |
| 3 | "We don't need specific evidence — the court knows the other party isn't complying." | The court knows NOTHING that isn't in the record. Every violation must be documented with specific dates, specific provisions violated, and specific evidence. A generalized claim of non-compliance without particulars is insufficient. MCR 3.606 requires specificity in the show-cause motion. | Vague contempt motions get denied at the threshold. "Respondent is not following the custody order" is insufficient. "Respondent failed to deliver L.D.W. for parenting time on January 15, 2025, in violation of Paragraph 3 of the October 10, 2024 Custody Order" is proper. |
| 4 | "Makeup parenting time is an adequate remedy — we don't need contempt." | Makeup time under MCL 722.27a compensates for SPECIFIC missed visits but does not address the pattern or deter future violations. Contempt adds: potential fines, jail time (stayed pending purge), attorney fee awards, and a judicial finding of willful non-compliance that affects future custody proceedings. | Relying only on makeup time enables continued violations because there's no consequence. A contempt finding creates a documented record of willful non-compliance that supports future custody modification under MCL 722.27 and weighs against the violator under MCL 722.23(j). |
| 5 | "Filing contempt will make things worse — it'll antagonize the other party and the judge." | Courts EXPECT contempt motions when orders are being violated. Failure to enforce your rights signals acquiescence. Under MCL 722.23(j), the court considers each parent's willingness to facilitate the relationship. Documenting violations through contempt preserves the record. | Not filing contempt allows violations to become the new normal. Courts may later say "you didn't object at the time" and treat the violation as acquiesced. Filing contempt is not hostile — it's exercising the legal remedy the court created for exactly this situation. |

---

## Common Failure Modes

### 1. Inability to Prove Willfulness
- **What happens**: Motion filed but respondent demonstrates inability to comply (job loss, medical issue, schedule conflict beyond their control)
- **How to prevent**: Investigate the respondent's circumstances before filing; document evidence of ABILITY to comply alongside evidence of non-compliance; anticipate inability defenses
- **Lane risk**: HIGH for Lane A — custody violations often have he-said/she-said character

### 2. Unclear Purge Conditions
- **What happens**: Court finds contempt but purge conditions are vague or impossible to satisfy, leading to enforcement problems
- **How to prevent**: Propose specific, measurable, achievable purge conditions in your motion (e.g., "comply with Section 3 of the custody order for 90 consecutive days"); avoid vague conditions like "obey the order"
- **Lane risk**: MEDIUM — bad purge conditions undermine the contempt finding

### 3. Stale Violations
- **What happens**: Contempt motion filed months after violations occurred, weakening the urgency and suggesting the violations weren't important
- **How to prevent**: File contempt motions promptly after documenting a pattern (2-3 violations); maintain a running violation log with dates and evidence; don't wait until you have dozens of violations
- **Lane risk**: MEDIUM — delay suggests acquiescence

### 4. Missing the Order
- **What happens**: Contempt motion doesn't attach or specifically cite the order being violated, or the order's language is ambiguous
- **How to prevent**: Always attach a certified copy of the order to the motion; quote the specific provision violated; if order language is ambiguous, address the ambiguity
- **Lane risk**: HIGH — without a clear order, there's nothing to hold in contempt of

### 5. Compensatory Damages Miscalculation
- **What happens**: Request for compensatory damages (attorney fees, lost wages, travel costs) is unsupported or inflated
- **How to prevent**: Document all costs with receipts; calculate lost wages with pay stubs; track mileage with a log; request only costs directly caused by the violation
- **Lane risk**: MEDIUM — inflated damage claims undermine credibility

---

## Integration Gotchas

- **litigation-court-order-tracker** provides the order catalog and violation log — contempt specialist uses this data to draft motions
- **litigation-evidence-authentication** ensures violation evidence meets MRE standards for the contempt hearing
- **litigation-child-support-analyzer** provides arrearage calculations for support-based contempt
- **litigation-emergency-motion-engine** handles emergency contempt situations (immediate threat to child safety)
- MCR 3.606 show cause motions interact with **litigation-filing-packager** for assembly
- Document every violation immediately — evidence gathered months later is weaker than contemporaneous documentation
