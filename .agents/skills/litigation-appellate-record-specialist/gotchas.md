# Gotchas — litigation-appellate-record-specialist

## Anti-Rationalization Table

| # | Excuse (The Lie) | Reality (The Truth) | Consequence |
|---|-----------------|---------------------|-------------|
| 1 | "The transcript isn't critical — the written motions tell the full story." | The transcript IS the record for oral proceedings. Without it, the COA presumes the trial court's findings were supported. MCR 7.210(B)(1) requires the appellant to order transcripts within 14 days. Written motions only capture what was filed, not what was argued, ruled on, or admitted from the bench. | Appellate court presumes trial court was correct on every issue where the transcript is missing. In COA 366810, missing transcripts from custody hearings before Judge McNeill mean those rulings are effectively unreviewable. |
| 2 | "The register of actions is just a formality — the important documents are in the appendix." | The register of actions is the roadmap of the entire case. It shows every filing, every order, every scheduling entry. MCR 7.210(A) includes it as part of the record. The COA uses it to verify procedural history, check preservation, and confirm timeliness. | Without a complete register of actions, the COA cannot verify that issues were preserved, motions were timely, or objections were made. It also cannot verify your procedural narrative in the statement of facts. |
| 3 | "We can supplement the record later if the COA asks for something." | MCR 7.210(H) places the burden on the appellant to ensure a complete record. The COA will NOT ask for missing items — it will simply rule based on what's before it. Supplementation requires a motion and is not guaranteed to be granted. | Issues not supported by the record are forfeited. The court doesn't hunt for evidence of error — you must present it. Late supplementation motions are disfavored and suggest poor preparation. |
| 4 | "Bates numbering is excessive for a family law appeal — it's not a complex commercial case." | Consistent Bates numbering enables the COA panel (and their clerks) to locate any cited exhibit instantly. Without it, the court must search through unnumbered pages, which wastes judicial resources and creates irritation. MCR 7.212(C)(8) requires organized appendix materials. | Disorganized exhibits force the court to work harder to understand your case. In close cases, judicial frustration with disorganized records can tip decisions. Pro se appellants who demonstrate organizational rigor earn credibility. |
| 5 | "We have all the exhibits — we just need to scan and upload them." | Physical exhibits require authentication, pagination, and cross-referencing to the trial court record. Simply scanning them doesn't establish that they were admitted into evidence, marked as exhibits, or part of the record below. Only items properly part of the lower court record can be included. | Including unadmitted exhibits in the appellate record is improper and may result in the COA striking those materials. Worse, relying on struck exhibits means your arguments based on them fail. Verify every exhibit's admission status in the register of actions. |

---

## Common Failure Modes

### 1. Transcript Ordering Delay
- **What happens**: Appellant fails to order transcripts within 14 days of filing claim of appeal (MCR 7.210(B)(1)), or court reporter delays beyond expected timeframe
- **How to prevent**: Order transcripts the same day as filing the claim; follow up with court reporter weekly; file motion for extension if delay is reporter's fault
- **Lane risk**: CRITICAL for Lane F — no transcript = no review of oral proceedings

### 2. Incomplete Register of Actions
- **What happens**: Register obtained from clerk is missing entries, or covers wrong date range
- **How to prevent**: Request register for full case history from filing to present; cross-reference against your own filing log; request correction if entries are missing
- **Lane risk**: HIGH — incomplete register undermines procedural narrative

### 3. Exhibit Pagination Errors
- **What happens**: Exhibit page numbers in the brief don't match actual page numbers in the appendix because exhibits were reorganized after brief citations were written
- **How to prevent**: Finalize exhibit pagination BEFORE drafting the brief; use Bates stamps that won't change; lock pagination before writing begins
- **Lane risk**: HIGH — wrong page references destroy credibility and make arguments unverifiable

### 4. Missing Sealed or Confidential Materials
- **What happens**: Sealed custody evaluation, in camera interview transcript, or CPS report omitted from record because of confidentiality concerns
- **How to prevent**: File motion to include sealed materials in the appellate record under seal; MCR 8.119(I) governs access to sealed records; sealed materials can be part of the record with proper handling
- **Lane risk**: CRITICAL for Lane A — custody evaluations are often the most important evidence and are frequently sealed

### 5. Record Certification Failure
- **What happens**: Record is compiled but not properly certified by the trial court clerk, making it unofficial
- **How to prevent**: Obtain clerk certification stamp on the record; verify certification before filing with COA; certified copies of orders must bear court seal
- **Lane risk**: MEDIUM — uncertified record materials may be challenged by opposing party

---

## Integration Gotchas

- **litigation-appeal-brief-engine** cannot draft citations to the record until the record is compiled and paginated — record compilation MUST precede brief drafting
- **litigation-exhibit-formatter** handles Bates stamping and tab creation — coordinate pagination schemes
- **litigation-filing-packager** assembles the final filing package — record specialist provides the content, packager handles format compliance
- **litigation-court-order-tracker** provides the comprehensive order list needed for the register of actions verification
- L.D.W. references must use initials only per MCR 8.119(H) throughout the entire record
