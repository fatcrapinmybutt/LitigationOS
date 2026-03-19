# VehicleMap Library — Templates & Examples

## VehicleMap Schema

Every filing follows this mandatory structure:

```
RELIEF: [What you want the court to do]
VEHICLE: [Motion/Application/Complaint type]
JURISDICTION: [Court + case number]
GOVERNING_AUTHORITY: [MCR/MCL/MRE citations]
ELEMENTS/BURDEN: [What must be proven + standard]
REQUIRED_SECTIONS:
  - Caption + case number
  - Statement of facts (record-grounded)
  - Legal argument (authority-pinned)
  - Relief requested (specific operational verbs)
  - Verification/signature
REQUIRED_ATTACHMENTS:
  - Proposed order
  - Proof of service (MC 12)
  - Exhibits with cover pages
  - [Vehicle-specific attachments]
DEADLINES:
  - Filing deadline
  - Service deadline
  - Response period
SERVICE:
  - Method (personal, mail, e-filing)
  - Parties to serve
  - Proof of service form
RISKS:
  - [Identified risk events with severity]
SUCCESS_CRITERIA:
  - [What "win" looks like]
```

## Example: Contempt for Violating Court Order

```
RELIEF: Hold respondent in contempt for violating parenting time order
VEHICLE: Motion and Order to Show Cause
JURISDICTION: 14th Circuit Court, Muskegon County (2024-001507-DC)
GOVERNING_AUTHORITY: MCR 3.606, MCR 3.708, MCL 600.1701
ELEMENTS/BURDEN:
  - Valid court order existed (attach certified copy)
  - Respondent had knowledge of the order
  - Respondent willfully violated specific provisions
  - Standard: clear and convincing evidence
REQUIRED_SECTIONS:
  - Caption with case number
  - Statement of the order violated (date, provisions)
  - Factual basis for each alleged violation (dates, specifics)
  - Legal argument citing MCR 3.606 elements
  - Relief: show cause hearing, make-up PT, fees
REQUIRED_ATTACHMENTS:
  - Proposed Order to Show Cause
  - Certified copy of order violated
  - Proof of service (MC 12)
  - Supporting affidavit/verification
  - Exhibits proving violations
DEADLINES:
  - No fixed deadline (reasonable diligence)
  - Hearing within 21 days of show cause order
  - Response: 14 days before hearing
SERVICE:
  - Personal service of Order to Show Cause preferred
  - Mail with 3-day extension if permitted
  - Serve all parties + FOC
RISKS:
  - severity:high — Failure to prove "willfulness"
  - severity:medium — Incomplete violation record
  - severity:low — Service defects
SUCCESS_CRITERIA:
  - Court finds contempt
  - Make-up parenting time ordered
  - Attorney fees/costs awarded
  - Compliance mechanism established
```

## Example: Emergency Restore Parenting Time

```
RELIEF: Restore parenting time pending hearing
VEHICLE: Emergency Motion for Temporary Order
JURISDICTION: 14th Circuit Court, Muskegon County (2024-001507-DC)
GOVERNING_AUTHORITY: MCR 3.207(B), MCL 722.27a, MCL 722.27
ELEMENTS/BURDEN:
  - Existing custody/PT order in effect
  - Irreparable harm to child or parent if PT not restored
  - Strong likelihood of success on merits
  - Balance of hardships favors movant
REQUIRED_SECTIONS:
  - Caption with EMERGENCY designation
  - Statement of current PT order provisions
  - Facts showing deprivation of PT (329+ days)
  - Harm to children from severed relationship
  - Legal argument: fundamental right + best interest
  - Specific PT schedule requested
REQUIRED_ATTACHMENTS:
  - Proposed temporary order with specific PT schedule
  - Proof of service
  - Affidavit of emergency
  - Evidence of denied PT (texts, communications, records)
DEADLINES:
  - URGENT — file immediately
  - Court should rule within days (emergency)
SERVICE:
  - Same-day service on opposing party/counsel
  - e-file + email courtesy copy to judge
RISKS:
  - severity:critical — Judge McNeill may deny (disqualification motion may be needed first)
  - severity:high — Incomplete evidence of denial
SUCCESS_CRITERIA:
  - Temporary PT order entered
  - Specific enforceable schedule
  - Next hearing date set
```

## Filing Lane Quick Reference

| Lane | Court | Key Vehicles |
|------|-------|-------------|
| Trial/Family | 14th Circuit | Motions, show cause, proposed orders |
| COA | Michigan COA | Leave to appeal (MCR 7.205), original action (MCR 7.206) |
| MSC | Michigan Supreme Court | Leave to appeal (MCR 7.305) |
| JTC | Judicial Tenure Commission | Verified complaint |
| Federal | WDMI | §1983 complaint |
