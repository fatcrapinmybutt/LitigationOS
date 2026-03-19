# Gotchas — litigation-appellate-supreme

## Anti-Rationalization Table

| # | Excuse (The Lie) | Reality (The Truth) | Consequence |
|---|-----------------|---------------------|-------------|
| 1 | "The standard of review doesn't matter that much — the facts speak for themselves." | Standard of review is the FIRST thing the appellate court applies. Using "de novo" when the correct standard is "great weight of the evidence" (MCL 722.28 for custody) means your entire argument is framed wrong. The COA will apply the correct standard regardless of what you argue. | Brief is unpersuasive because it asks the court to do something it legally cannot — reweigh evidence under the wrong standard. Panel may note the error in dicta, damaging credibility. |
| 2 | "I preserved this issue by raising it at trial — no need to document where." | Issue preservation requires a contemporaneous objection on the correct grounds, stated on the record, with a ruling by the trial court. MCR 2.517(A)(7). Merely "discussing" an issue is not preservation. You must cite the specific transcript page and line. | Issue is reviewed for plain error only (MCR 2.613(C)), which requires showing: (1) error occurred, (2) error was plain, (3) error affected substantial rights, (4) error seriously affected fairness/integrity of proceedings. This is nearly impossible to meet. |
| 3 | "The 21-day claim of appeal deadline is flexible for good cause." | The 21-day deadline for filing a claim of appeal (MCR 7.204(A)(1)) is JURISDICTIONAL. The COA has no authority to extend it. Missing this deadline means the appeal is dismissed for lack of jurisdiction — full stop. No motion, no exception, no "good cause." | Case over. The only remaining option is an application for leave to appeal, which is discretionary and has a much lower acceptance rate. |
| 4 | "I'll include the full trial transcript in the appendix — more is better." | MCR 7.212(C) requires an appendix containing only "those parts of the record that are reasonably necessary for the determination of the issues on appeal." Including the entire transcript wastes the panel's time and violates the rule. | Panel may strike the appendix or, worse, form a negative impression of counsel's ability to identify relevant issues. Excess pages also risk exceeding filing limits. |
| 5 | "I'll raise every possible issue on appeal to maximize chances." | Raising too many issues dilutes the strongest arguments. Michigan appellate courts have explicitly noted that "an appellant's best strategy is usually to select the strongest issue or issues." *People v Miller*, unpublished. Focus on 3-5 strongest issues with clear preservation and strong authority. | The panel gives each issue superficial treatment instead of deep analysis. The strongest issues get lost among the weak ones. |
| 6 | "The record speaks for itself — I don't need to order all the transcripts." | MCR 7.210(B)(1) requires the appellant to order transcripts within 14 days of filing the claim of appeal. If transcripts are not ordered timely, the COA may dismiss the appeal. The appellant bears the burden of providing an adequate record. | Without complete transcripts, the COA presumes the missing portions support the trial court's ruling. Issues that depend on those missing portions are forfeited. |
| 7 | "I can raise new arguments on appeal that I didn't make below." | Michigan appellate courts generally refuse to address issues not raised in the trial court. *Booth Newspapers, Inc v Univ of Michigan Bd of Regents*, 444 Mich 211, 234 (1993). Exceptions are narrow: jurisdictional defects, plain error, or issues of great public importance. | New argument rejected. The appellate court will not be the first tribunal to address an issue that could have been raised and corrected at the trial level. |

---

## Common Failure Modes

### 1. Wrong Standard of Review Applied
- **What happens**: Brief argues for de novo review of factual findings that receive clear-error or great-weight review, or argues abuse of discretion for legal questions reviewed de novo.
- **How to prevent**: Consult the Lane-Specific Standard of Review Map in this skill. For each issue on appeal, identify the standard FIRST before writing the argument. Cross-reference with `appellate-standards-of-review.md`.
- **Lane risk**: HIGH for Lane A (custody) — great weight standard (MCL 722.28) is the most deferential and most commonly misapplied.

### 2. Jurisdictional Deadline Miss
- **What happens**: Claim of appeal not filed within 21 days of the order being appealed (MCR 7.204(A)(1)), or application for leave to appeal to MSC not filed within 42 days (MCR 7.305(C)(2)).
- **How to prevent**: Use `deadline_dashboard` MCP tool immediately upon identifying an appealable order. Set calendar alerts for 14-day and 7-day warnings. File early — never on the last day.
- **Lane risk**: CRITICAL for Lane F (appellate) — jurisdictional deadlines cannot be extended by any court.

### 3. Inadequate Record on Appeal
- **What happens**: Transcripts not ordered within 14 days (MCR 7.210(B)(1)), or register of actions / exhibits not included in the record.
- **How to prevent**: Order ALL transcripts of relevant proceedings immediately upon filing claim of appeal. Request register of actions from clerk. Verify exhibit list is complete.
- **Lane risk**: HIGH for Lane F — missing record portions create irrebuttable presumption against appellant.

### 4. Statement of Questions Presented Deficiency
- **What happens**: Questions presented are too broad ("Did the trial court err?"), too narrow (omitting key sub-issues), or don't match the arguments in the brief.
- **How to prevent**: Draft questions presented AFTER writing arguments. Each question should correspond to one section of the argument. Format per MCR 7.212(D): "Whether [specific ruling] constitutes [specific error] requiring [specific relief]."
- **Lane risk**: MEDIUM for all lanes — poorly framed questions confuse the panel and may result in issues not being addressed.

### 5. Failure to Address Controlling Authority
- **What happens**: Brief ignores binding precedent from the Michigan Supreme Court or published COA opinions that cut against the appellant's position.
- **How to prevent**: Always search for adverse authority. Distinguish unfavorable cases rather than ignoring them. The panel will find them regardless — better to address them proactively.
- **Lane risk**: MEDIUM for all lanes — failure to address adverse authority is an ethics violation under MRPC 3.3(a)(2) and destroys credibility.

---

## Integration Gotchas

- **litigation-appellate-supreme feeds into OMEGA-LITIGATION-SUPREME M6 (Domain Specialists, sub-module D3: Appellate)** — use this skill for detailed appellate work, then route through OMEGA-SUPREME for QA gates.
- **Lane F (Appellate) has DIFFERENT rules than Lanes A-E (trial level)** — MCR 7.2xx governs COA; MCR 7.3xx governs MSC. Do NOT apply MCR 2.xxx trial rules to appellate filings.
- **Appellate deadlines are JURISDICTIONAL, not procedural** — unlike trial-level deadlines that can sometimes be extended, missing an appellate deadline means the court literally lacks power to hear the case.
- **TrueFiling is required for COA/MSC** — circuit court uses MiFile. The e-filing platforms have different format requirements, file size limits, and document naming conventions.
- **Cross-reference with litigation-supreme-commander for any trial-level motions that preserve issues for appeal** — issue preservation is a trial-level task that directly affects appellate success.
