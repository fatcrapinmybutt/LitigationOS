# Gotchas — litigation-filing-architect

## Anti-Rationalization Table

This table exists to prevent the most common excuses for cutting corners on
filing architecture. Every row is a real failure mode observed in Michigan
circuit court filings.

| # | Excuse (Rationalization) | Reality (What Actually Happens) | Consequence |
|---|--------------------------|--------------------------------|-------------|
| 1 | "The judge will overlook the formatting — substance matters more." | MCR 2.119(A)(1) specifies formatting requirements. Judges in the 14th Circuit have rejected non-compliant filings at the clerk window. McNeill has returned motions for single-spacing. | Filing rejected. Deadline missed. Motion denied as untimely. |
| 2 | "I'll add the certificate of service later — I need to file today." | MCR 2.107(C) requires proof of service at or before filing. The clerk's office in Muskegon County checks for this. Filing without it is incomplete. | Filing not accepted. If accepted, opposing counsel moves to strike for defective service. |
| 3 | "The case number format doesn't matter as long as it's close." | Muskegon County uses a specific format: YYYY-NNNNNN-XX. Wrong format causes mis-filing, wrong case assignment, or lost documents. The 14th Circuit e-filing system rejects malformed case numbers. | Document filed in wrong case or lost entirely. Must re-file with correct number, potentially missing deadline. |
| 4 | "I don't need a proposed order — the judge will draft one." | MCR 2.602(B)(3) requires the prevailing party to submit a proposed order. Judges expect one with every motion. Failure to include one signals lack of preparation and may delay resolution. | Judge grants motion but has no proposed order to sign. Delay of days to weeks. Opposing party may submit their version first. |
| 5 | "The exhibit index is optional — the exhibits are self-explanatory." | MCR 2.119(A)(2) requires exhibits to be labeled and indexed. Judges in multi-case dockets (like McNeill's family division) rely on indexes to manage volume. | Judge cannot locate your evidence. Arguments referencing exhibits fail because court cannot find them. |
| 6 | "I can use the same filing template for Lane A and Lane B." | Lane A (custody) requires MCR 3.200-series compliance including verified statements and UCCJEA declarations. Lane B (civil/housing) uses MCR 2.100-series. Cross-contaminating templates produces invalid filings. | Filing rejected for wrong form. Legal arguments framed under wrong standard. Opposing counsel moves to dismiss. |
| 7 | "E-filing is just uploading a PDF — the system handles the rest." | Michigan e-filing (TrueFiling/MiFILE) requires specific document types, case categories, and filing codes. Wrong codes route to wrong clerk queues. The 14th Circuit has local e-filing requirements beyond state defaults. | Document sits in wrong queue. No clerk action taken. Appears filed but is not processed. |
| 8 | "Page limits don't apply to pro se filers." | MCR 2.119(A)(3) page limits apply to all filers. Some judges are more lenient with pro se parties, but McNeill has enforced page limits strictly. Hoopes follows local rules on brief length. | Overlength brief stricken or the portion beyond page limits ignored. Key arguments in excess pages are never considered. |

## Common Failure Modes

### 1. VehicleMap Incomplete
**Symptom**: Filing packet missing required supporting documents.
**Cause**: Template selected for primary vehicle only; supporting vehicles not generated.
**Fix**: Always generate complete VehicleMap before populating any individual vehicle.

### 2. Wrong Court Rule Applied
**Symptom**: Motion cites MCR 2.116 (summary disposition) when filing is a MCR 3.210 (custody modification).
**Cause**: Lane mismatch — civil procedure rules applied to family division case.
**Fix**: Validate lane assignment before selecting rule set. Lane A = MCR 3.200 series.

### 3. Deadline Miscalculation
**Symptom**: Filing served 7 days before hearing via mail (should be 14 for mail service).
**Cause**: MCR 2.119(C) mail service adds 5 days to the 9-day personal service requirement.
**Fix**: Always use the deadline calculator with explicit service method specification.

### 4. Missing SCAO Forms
**Symptom**: Filing uses custom cover sheet instead of mandatory SCAO form.
**Cause**: SCAO forms not in template library or not mapped to action ID.
**Fix**: Maintain current SCAO form library. MC 290 for domestic, MC 01 for civil.

### 5. Cross-Lane Reference Failure
**Symptom**: Lane C filing references Lane A evidence without proper cross-reference.
**Cause**: Lane C convergence filings depend on evidence from A and B but reference system not linked.
**Fix**: Always run cross-reference validator for Lane C filings.

## Michigan-Specific Traps

- **FOC involvement**: Lane A filings must account for Friend of the Court. Motions affecting custody/parenting time trigger FOC review. Failure to serve FOC = defective filing.
- **PPO specifics**: MCL 600.2950 PPO modifications have unique procedural requirements distinct from regular motions.
- **Fee waivers**: MCR 2.002 fee waivers must be filed separately and approved before filing fees are waived. Filing with unpaid fees and no waiver = rejected.
- **14th Circuit local rules**: Always check for local administrative orders that modify MCR defaults. The 14th Circuit has specific requirements for motion hearing scheduling.
