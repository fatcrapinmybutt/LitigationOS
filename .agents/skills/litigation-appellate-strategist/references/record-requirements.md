# Record Requirements — Appellate Strategist Reference

## What Constitutes the Record on Appeal

Under MCR 7.210, the record on appeal consists of:

```
1. ORIGINAL PAPERS filed in the trial court
2. REGISTER OF ACTIONS maintained by the clerk
3. TRANSCRIPTS of proceedings (or settled statements)
4. EXHIBITS admitted or offered and refused
5. Any ADDITIONAL items ordered by the COA
```

The appellate court reviews ONLY what is in the record. Facts not in
the record do not exist for appellate purposes.

---

## Record Component Specifications

### Component 1: Original Papers

```yaml
definition: >
  All documents filed with the trial court clerk during
  the proceedings below.
includes:
  - Complaint / petition (original and amendments)
  - Answer / response (original and amendments)
  - All motions filed by any party
  - All responses and replies to motions
  - All briefs filed in support of or opposition to motions
  - Discovery requests and responses (if filed with court)
  - All court orders
  - Final judgment or order appealed from
  - Post-judgment motions
  - Notice of appeal / claim of appeal
  - Certificate of service for each filing
obtaining:
  - Request from 14th Circuit Clerk's Office
  - Clerk assembles lower court file
  - Verify file is complete against register of actions
lane_a_specifics:
  - Include all custody petitions and modifications
  - Include FOC reports and recommendations
  - Include any GAL reports
  - Include PPO petitions and orders
  - Include parenting time orders and modifications
  - Include any Friend of Court motions
lane_b_specifics:
  - Include complaint and all amendments
  - Include summary disposition motion and response
  - Include discovery motions and orders
  - Include any case evaluation results
  - Include all housing inspection documents filed
```

### Component 2: Register of Actions

```yaml
definition: >
  Chronological log maintained by the court clerk recording
  every filing and event in the case.
includes:
  - Date of each filing
  - Description of document filed
  - Date of each hearing
  - Date and description of each order
  - Date of judgment entry
importance:
  - Establishes timeline for appeal deadlines
  - Verifies what was filed and when
  - Used to identify missing documents
  - Confirms entry date of order appealed from
obtaining:
  - Request certified copy from 14th Circuit Clerk
  - Available through MiCourt e-filing system (if case is e-filed)
  - Verify completeness — compare against your own filing log
```

### Component 3: Transcripts

```yaml
definition: >
  Verbatim record of all oral proceedings before the trial court,
  prepared by the certified court reporter.
includes:
  - All hearing transcripts
  - Trial transcripts (if trial held)
  - In camera proceedings
  - Bench conferences (if recorded)
  - Oral rulings and findings
ordering_procedure:
  step_1: Identify court reporter for each hearing
  step_2: File written request with court reporter
  step_3: Pay estimated transcript cost (per-page rate)
  step_4: File certificate of transcript request with COA
  step_5: Court reporter files transcript within 56 days
  step_6: Verify transcript accuracy upon receipt
deadlines:
  order_within: 14 days of filing claim of appeal
  reporter_files_within: 56 days of order (or COA-directed)
  failure_to_order: >
    If appellant fails to order transcript, COA may dismiss
    appeal or presume trial court findings are correct
cost:
  rate: Varies by court reporter (typically $3.50-5.00/page)
  estimated_pages:
    1_hour_hearing: 40-60 pages
    half_day_trial: 120-180 pages
    full_day_trial: 240-360 pages
lane_a_specifics:
  must_include:
    - All custody hearings before Judge McNeill
    - FOC hearing transcripts
    - PPO hearing transcripts
    - Any evidentiary hearings
    - Oral findings on best-interest factors
  critical_note: >
    Judge McNeill's oral findings on best-interest factors are
    THE key record material for custody appeals. Without the
    transcript, you cannot challenge factual findings.
lane_b_specifics:
  must_include:
    - Summary disposition hearing transcript
    - Any discovery dispute hearings
    - Case evaluation hearing (if relevant)
    - Any evidentiary hearings
  critical_note: >
    Judge Hoopes' reasoning on summary disposition is essential.
    Oral reasoning from the bench may differ from written order.
```

### Component 4: Exhibits

```yaml
definition: >
  All exhibits offered by any party during proceedings,
  whether admitted or refused.
includes:
  admitted_exhibits:
    - Marked with exhibit number
    - Admitted into evidence by court order
    - Part of the record automatically
  refused_exhibits:
    - Offered by party but excluded by court
    - CRITICAL for appeal if exclusion is an issue
    - Must be preserved in record for review
  demonstrative_exhibits:
    - Charts, summaries, timelines used at hearing
    - May not be formally admitted but part of proceedings
obtaining:
  - Physical exhibits held by 14th Circuit Clerk
  - Request release for COA appendix preparation
  - Alternatively, request clerk to transmit to COA
  - Digital exhibits: verify format compatibility
lane_a_specifics:
  typical_exhibits:
    - Parenting time logs
    - School records
    - Medical records
    - Communications between parties
    - Photos of living conditions
    - FOC investigation reports
    - GAL reports
    - Financial records
lane_b_specifics:
  typical_exhibits:
    - Lease agreement
    - Housing inspection reports
    - Repair request documentation
    - Photos of property conditions
    - Communication with landlord/management
    - Financial records (rent payments, damages)
    - Expert reports (if any)
    - Building code violation notices
```

---

## Settled Statement (MCR 7.210(B)(3))

When a transcript is unavailable (court reporter unable to produce,
proceedings not recorded, etc.):

```yaml
settled_statement:
  purpose: Substitute for transcript when transcript unavailable
  procedure:
    step_1: >
      Appellant prepares proposed statement of proceedings from
      notes, recollection, and available documents
    step_2: >
      Serve proposed statement on all parties
    step_3: >
      Other parties have 14 days to object or propose amendments
    step_4: >
      If objections, submit to trial court for settlement
    step_5: >
      Trial court approves settled statement
    step_6: >
      Settled statement becomes part of record
  limitations:
    - Not as reliable as actual transcript
    - Opposing party can challenge accuracy
    - Trial court may not recall details
    - Use ONLY when transcript truly unavailable
  lane_note: >
    In custody cases (Lane A), the absence of a transcript is
    nearly fatal on appeal. The "great weight" standard (MCL 722.28)
    means the COA defers to trial court findings unless clearly
    erroneous — and without a transcript, you cannot show clear error.
```

---

## Appendix Requirements

```yaml
appendix:
  purpose: >
    Compilation of key record materials bound with or filed
    alongside the appellate brief for the panel's convenience.
  required_contents:
    - Order or judgment appealed from
    - Register of actions
    - Relevant portions of transcript (cited in brief)
    - Key exhibits cited in brief
  formatting:
    - Sequentially paginated
    - Tab-separated sections
    - Table of contents for appendix
    - Must not exceed necessary materials
  filing:
    - Filed with appellant's brief
    - Serve on all parties
    - One copy to each panel member (check current COA requirements)
```

---

## Record Completeness Verification Checklist

```
BEFORE FILING APPELLANT'S BRIEF:

ORIGINAL PAPERS:
[ ] Complaint/petition obtained
[ ] All motions and responses obtained
[ ] All court orders obtained
[ ] Final judgment/order obtained
[ ] Register of actions obtained and verified

TRANSCRIPTS:
[ ] All hearing dates identified
[ ] Transcripts ordered within 14 days of claim
[ ] Transcript cost paid/deposited
[ ] Court reporter confirmed receipt of order
[ ] Transcripts received and reviewed for accuracy
[ ] All oral findings included

EXHIBITS:
[ ] Exhibit list compiled from trial court records
[ ] All admitted exhibits accounted for
[ ] All refused exhibits preserved (if exclusion is an issue)
[ ] Exhibits in reproducible format for appendix

SUPPLEMENTAL:
[ ] Depositions needed for appeal identified and obtained
[ ] Discovery responses relevant to appeal obtained
[ ] Any supplemental record items identified and ordered

VERIFICATION:
[ ] Record complete — no gaps that affect appellate issues
[ ] All record citations in brief verified against actual record
[ ] Appendix compiled with all necessary materials
```

---

## Common Record Deficiencies

| Deficiency | Consequence | Prevention |
|-----------|-------------|------------|
| Missing transcript | Cannot challenge factual findings | Order transcripts IMMEDIATELY |
| Missing exhibit | Cannot reference evidence on appeal | Verify exhibit list with clerk |
| Incomplete register | Deadline miscalculation risk | Get certified copy from clerk |
| Missing court order | Cannot show what was appealed | Check all orders entered |
| No offer of proof | Cannot challenge evidence exclusion | Make offer of proof at trial |
| Missing post-judgment motion | Preservation issue | File all necessary post-judgment motions |
