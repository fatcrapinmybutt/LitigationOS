# Gotchas — document-forge-supreme

## Anti-Rationalization Table

| # | Excuse (The Lie) | Reality (The Truth) | Consequence |
|---|-----------------|---------------------|-------------|
| 1 | "I'll use a placeholder like `[INSERT CASE NUMBER]` — Andrew can fill it in later." | The DB has the data. `litigation_context.db` contains 790+ tables with case numbers, docket events, party info, evidence quotes, and deadlines. The user explicitly said: *"thats the whole point of this. to USE MY FILES ON MY DRIVES."* Query the DB before inserting ANY placeholder. | User gets a document full of `[ANDREW_REQUIRED]` placeholders when the data was available the entire time. Wastes hours of manual fill-in. Defeats the purpose of the system. |
| 2 | "The defendant's name is Emily Ann Watson." | Her name is **Emily A. Watson**. NOT "Emily Ann", NOT "Emily M.", NOT "Tiffany". Past sessions hallucinated "Jane Berry" and "Patricia Berry (SBN P35878)" — people who never existed. The Verified Party Identity table is the ONLY source of truth. | Hallucinated party names in a sworn court filing = potential perjury. "Jane Berry" appeared in 60+ files before being caught. A wrong name on a filed document cannot be unfiled. |
| 3 | "The motion format looks right — standard legal formatting." | Michigan court rules (MCR) have specific requirements: MCR 2.113 caption format, MCR 7.212 brief formatting (double-spaced, 1-inch margins, specific font sizes), page limits per MCR 7.212(B), certificate of service per MCR 2.107. "Looks right" is not compliant. | Court clerk rejects the filing. Motion denied on procedural grounds. Deadline passes while reformatting. Muskegon County Local Rules add additional requirements beyond MCR. |
| 4 | "I generated the certificate of service — it lists the opposing party." | Does it list the correct address? Jennifer Barnes (P55406) WITHDREW as Emily's attorney. Service must go to the correct current address. Is proof of service on the correct SCAO form? Did you include the method of service and date? | Defective service = filing is procedurally void. Court may strike the motion. Opposing party claims no notice. All work wasted. |
| 5 | "The case number is 2024-001507." | Which case? Which lane? LitigationOS has 6 case lanes. Case number 2024-001507-DC is Lane A (custody). 2023-5907-PP is Lane D (PPO). 2025-002760-CZ is Lane B (housing). Cross-contaminating case numbers between lanes is a fatal error. | Wrong case number on a filing = filing goes to wrong case. Could expose sealed information. Could be construed as fraud on the court. |
| 6 | "I cited 305 interference incidents in the motion." | Did you run `SELECT COUNT(*) FROM [table] WHERE [condition]` and verify? Did you deduplicate? Past sessions generated inflated statistics that were embedded in sworn filings. The "91% alienation score" was pseudo-scientific and fabricated. Every statistic MUST be traceable to a specific DB query. | Inflated statistics in a sworn filing = misrepresentation to the court. Opposing counsel challenges the number, you can't produce the source query, credibility destroyed. |
| 7 | "The document is ready to file — I ran a spell check." | Spell check doesn't verify: (a) correct case number per lane, (b) correct judge name (Hon. Jenny L. McNeill, NOT "Amy McNeill"), (c) correct party addresses, (d) MCR-compliant formatting, (e) all exhibits attached and Bates-stamped, (f) certificate of service with correct addresses, (g) e-filing format compliance. Use `pre-filing-qa` agent for GO/NO-GO. | One of the 7 unchecked items is wrong. Filing is rejected, returned, or worse — accepted with errors that become part of the permanent record. |

---

## Common Failure Modes

### 1. Party Name Hallucination
- **What happens**: The model generates a party name from training data instead of the verified identity table. "Jane Berry", "Patricia Berry", "Amy McNeill", "Emily Ann Watson" have all appeared in past generated documents.
- **How to prevent**: Reference the Verified Party Identity table for EVERY name in every document. Use `[UNKNOWN — VERIFY]` if a name isn't in the table — never guess. Run `pre-filing-qa` agent before finalizing.
- **Risk level**: HIGH (potential perjury)

### 2. Placeholder Laziness
- **What happens**: Generator inserts `[ANDREW_REQUIRED]`, `[INSERT]`, `[ATTACH]` placeholders instead of querying the database. The data exists in `litigation_context.db` tables like `docket_events`, `evidence_quotes`, `claims`, `deadlines`, `documents`, `judicial_violations`.
- **How to prevent**: Before ANY placeholder: (1) query litigation_context.db, (2) search filesystem with `rg`/`fd`, (3) check `COMPLETE_FILING_DATA_SUMMARY.txt`. Only use placeholder if ALL three return nothing, with specific instructions on where to find the data.
- **Risk level**: HIGH (user frustration)

### 3. Wrong Court Formatting Standard
- **What happens**: Document is formatted for generic legal standards instead of Michigan-specific MCR rules and Muskegon County local rules. Wrong margins, wrong spacing, wrong caption format, wrong page numbering.
- **How to prevent**: Always reference MCR 2.113 (caption), MCR 7.212 (brief format), MCR 2.119 (motion practice), and Muskegon County 14th Circuit local rules. Use court_forms.db for SCAO form numbers.
- **Risk level**: MEDIUM (filing rejection)

### 4. Lane Cross-Contamination in Documents
- **What happens**: A motion for Lane A (custody) accidentally references evidence or case numbers from Lane D (PPO) or Lane E (misconduct). Lanes are legally separate proceedings.
- **How to prevent**: Verify lane assignment before generating any document. Use MEEK signal detection. Each document should reference only its lane's case number, evidence, and docket entries.
- **Risk level**: HIGH (could expose sealed information)

### 5. Missing Signature Block and Verification
- **What happens**: Generated document lacks the pro se signature block, verification under oath (if required), or date. Michigan courts require specific signature block formatting for pro se litigants.
- **How to prevent**: Every filing must end with: Andrew James Pigors (pro se), address (1977 Whitehall Road, Lot 17, North Muskegon, MI 49445), phone ((231) 903-5690), email, date line. Verified documents need notary block.
- **Risk level**: MEDIUM (filing rejection)

---

## Integration Gotchas

- **pre-filing-qa agent**: Run this agent on EVERY document before filing. It generates a GO/NO-GO report checking party names, case numbers, formatting, service requirements, and completeness.
- **court_forms.db**: Contains 39 Michigan SCAO court form definitions. Query it for form numbers: `SELECT * FROM forms WHERE form_type LIKE '%motion%'`.
- **exhibit-formatter agent**: For documents with exhibits, use this agent to apply consistent Bates stamps, tabs, and index generation. Don't manually number exhibits.
- **Lane databases**: Each lane has its own DB (lane_A_custody.db through lane_F_appellate.db). Cross-reference the lane DB for case-specific evidence, not just the central litigation_context.db.
- **OMEGA-LITIGATION-SUPREME M4**: The Filing Factory module in OMEGA-LITIGATION-SUPREME handles end-to-end document generation with built-in QA. Use it for complex filings; use document-forge-supreme for general document generation (reports, letters, non-court documents).
