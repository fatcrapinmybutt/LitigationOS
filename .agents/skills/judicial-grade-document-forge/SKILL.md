# Judicial-Grade Document Forge v1.0
## 15-Step Mandatory Pipeline for Court-Ready Filings

### MISSION
Every document produced by this skill MUST pass all 15 gates before delivery. NO shortcuts. NO partial deliveries. This produces filings that exceed attorney quality.

### APPLIES TO
All court filings (motions, briefs, petitions, complaints, affidavits, applications) for:
- 14th Circuit Court (Family Division) — Muskegon County
- Michigan Court of Appeals (COA)
- Michigan Supreme Court (MSC)
- US District Court Western District of Michigan (WDMI)
- Judicial Tenure Commission (JTC)

### THE 15 GATES

#### GATE 1: JURISDICTION & VENUE LOCK
- Verify correct court, division, case number
- Confirm subject matter jurisdiction
- Verify personal jurisdiction over all parties
- Check venue requirements (MCR 2.221-2.226)
- OUTPUT: Jurisdiction block with case caption

#### GATE 2: AUTHORITY FOUNDATION
- Query michigan_court_rules table for applicable MCR
- Query michigan_statutes table for applicable MCL
- Query michigan_evidence_rules for applicable MRE
- Query michigan_case_law for controlling authorities
- Cross-reference filing_rule_map for mandatory authorities
- OUTPUT: Authority spine (minimum 5 primary authorities per filing)

#### GATE 3: EVIDENCE MINING
- Query evidence_quotes table for relevant quotes
- Query actionable_evidence for supporting items
- Query watson_family_conspiracy for conspiracy evidence
- Query healthwest_evidence for medical/evaluation evidence
- Query chatgpt_litigation_intel for narrative support
- DEDUPLICATE all evidence (content-based, not hash-based)
- OUTPUT: Evidence inventory with Bates references

#### GATE 4: LEGAL STANDARD FRAMEWORK
- Identify burden of proof (preponderance/clear & convincing/beyond reasonable doubt)
- State elements of each cause of action
- Map evidence to each element
- Identify any affirmative defenses to preempt
- OUTPUT: Element-by-element proof chart

#### GATE 5: NARRATIVE CONSTRUCTION
- Chronological fact pattern with pinpoint citations
- Every fact supported by exhibit reference
- Andrews narrative is 100% truthful — present as sworn testimony
- No inflammatory language — let facts speak
- OUTPUT: Statement of Facts section

#### GATE 6: LEGAL ARGUMENT (IRAC)
- Issue: Clear statement of each legal question
- Rule: Controlling authority with pinpoint citations
- Application: Apply facts to law with evidence citations
- Conclusion: State requested relief precisely
- Minimum 3 IRAC blocks per filing
- OUTPUT: Legal argument section

#### GATE 7: PARTY IDENTITY VERIFICATION
- Cross-reference ALL names against verified party table
- Andrew James Pigors (Plaintiff) — 1977 Whitehall Road, Lot 17, North Muskegon, MI 49445
- Emily A. Watson (Defendant) — 2160 Garland Drive, Norton Shores, MI 49441
- L.D.W. (Child — initials ONLY per MCR 8.119(H))
- Hon. Jenny L. McNeill — 14th Circuit Court, Family Division
- Jennifer Barnes P55406 — WITHDREW
- Pamela Rusco — Judge McNeill's Secretary, 990 Terrace St, Muskegon MI 49442
- Ronald Berry — NON-ATTORNEY, Emily's boyfriend/domestic partner
- NEVER invent names, bar numbers, or evidence statistics
- OUTPUT: Verified caption and party blocks

#### GATE 8: MICHIGAN FORMATTING COMPLIANCE
- MCR 2.113 format (caption, spacing, margins, font)
- Page numbering, line spacing (double-spaced body)
- Proper caption block with case number, judge name
- Prayer for relief section
- Signature block (Pro Se with contact info)
- Date and verification/certification
- OUTPUT: Formatted document shell

#### GATE 9: CITATION VALIDATION
- Every case citation verified: Name, Volume, Reporter, Page, Year
- Every MCR citation verified: Rule number, subdivision
- Every MCL citation verified: Section number, subsection
- Every MRE citation verified: Rule number
- Flag any unverifiable citations as [NEEDS VERIFICATION]
- OUTPUT: Citation appendix

#### GATE 10: EXHIBIT INTEGRATION
- Assign Bates numbers (PIGORS-XXXXX series)
- Create exhibit index with descriptions
- Cross-reference exhibits in body text
- Ensure every key claim has exhibit support
- OUTPUT: Exhibit list and cross-reference table

#### GATE 11: COURT FORMS ATTACHMENT
- Identify required SCAO forms per MCR
- Pre-fill with verified party data
- MC 264 (Affidavit of Service), CC 379 (PPO), MC 230 (Contempt)
- Fee waiver forms if applicable (MC 20)
- OUTPUT: Completed court forms list

#### GATE 12: CERTIFICATE OF SERVICE
- MCR 2.107 compliant service certificate
- All parties listed with addresses
- Service method (first-class mail, personal, e-filing)
- Date of service
- OUTPUT: Signed certificate template

#### GATE 13: ANTI-HALLUCINATION AUDIT
- Verify every statistic is traceable to a DB query
- Verify no fabricated names, bar numbers, or case numbers
- Verify no inflated evidence counts (deduplicated)
- Check for "Jane Berry", "Patricia Berry" — PURGE if found
- Verify no "91% alienation score" or similar pseudo-science
- Every claim must have evidence or [EVIDENCE NEEDED] tag
- OUTPUT: Audit checklist (PASS/FAIL per item)

#### GATE 14: ADVERSARIAL RED TEAM
- What would opposing counsel attack?
- Identify weakest arguments — strengthen or remove
- Check for inadmissible evidence references
- Verify standing for each claim
- Check statute of limitations for each cause of action
- Preempt procedural objections (service, timeliness, format)
- OUTPUT: Red team report with mitigations

#### GATE 15: FINAL QA & DELIVERY
- Spell check, grammar check, legal terminology accuracy
- Cross-check all page references and exhibit numbers
- Verify signature blocks complete
- Generate filing instructions (court, fees, deadlines, method)
- Package: Main document + Affidavit + Exhibits + Forms + Certificate + Cover Page + Instructions
- OUTPUT: COMPLETE FILING PACKAGE (7 files minimum)

### QUALITY SCORING
Each gate scores 0-10. Total possible: 150.
- 140+ = SUPREME (file immediately)
- 120-139 = EXCELLENT (minor polish needed)
- 100-119 = GOOD (specific fixes required)
- Below 100 = REJECT (do not file — rework required)

### INVOCATION
When any filing task is received:
1. Identify filing ID (F1-F10) and target court
2. Run ALL 15 gates sequentially
3. Score each gate
4. If total < 100, loop back to weakest gate and improve
5. Deliver only when score >= 120

### DB TABLES USED
- michigan_court_rules, michigan_statutes, michigan_evidence_rules, michigan_judicial_canons
- michigan_case_law, filing_rule_map
- evidence_quotes, actionable_evidence, watson_family_conspiracy
- healthwest_evidence, claude_session_evidence
- chatgpt_litigation_intel, encyclopedia_sections
- bates_assignments, certificates_of_service, generated_court_forms
