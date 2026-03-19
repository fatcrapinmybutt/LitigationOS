# Missing-Radar: Operational Loop Upgrades (Michigan Custody/PT • Ex Parte • Contempt • COA/MSC • JTC)

This is a **gap list** for the operational loop that turns a ZIP of materials into **file-ready** appellate/original-action/JTC work product. It is written “multi-role” (lawyer, judge, clerk, court reporter, prosecutor, father) so each missing layer is stated as an **acceptance requirement** rather than a feature wish.

## 1) Missing layers (high priority)

### 1.1 Record-spine ingestion: ROA/Case-History + file-stamps
**What’s missing:** an explicit, deterministic “record spine” that anchors everything to **what the court has** and **when** it was filed/entered.

**Why it matters (clerk/judge/appellate panel):** appellate and disciplinary reviewers heavily discount assertions not tied to the filed record. Your loop should treat “record spine” as the **primary index** that all other products reference.

**Minimum acceptance criteria:**
- A **Register of Actions / Case History** data structure (per court, per case) with:
  - docket entry text (as available)
  - filed date
  - entry date
  - document id (if present)
  - links to the extracted file(s)
- Every order/notice in the ZIP is classified as:
  - **file-stamped** (preferred) vs.
  - **unstamped** (needs acquisition)

### 1.2 Bi-temporal dates: signed vs entered vs served vs heard
**What’s missing:** your timeline cannot be single-axis. For higher courts, the relevant date may be **entry** (for appeal timing), **service** (for response windows), or the **hearing date** (for due process analysis).

**Minimum acceptance criteria:**
- Each “event” supports at least these timestamps (when available):
  - `signed_dt` / `entered_dt` / `served_dt` / `hearing_dt` / `filed_dt`
- A deadline engine reads **service method** to compute earliest lawful action dates in contempt/show-cause contexts.

### 1.3 Service-proof pipeline (especially contempt and ex parte)
**What’s missing:** a first-class “ServiceChain” that treats proof of service as mandatory evidence, not optional metadata.

**Why it matters:** contempt and show-cause procedures are service-sensitive. Michigan’s contempt benchbook notes a show-cause hearing timing rule based on personal vs mail service (MCR 3.208(B)(4)).

**Minimum acceptance criteria:**
- For each served item, capture:
  - who served
  - how served (personal, mail, etc.)
  - service date
  - served parties
  - supporting exhibit (proof-of-service page)
- Compute and store “earliest permissible hearing date” for show-cause matters.

### 1.4 Transcript procurement + monitoring (court reporter + COA clerk reality)
**What’s missing:** a deterministic transcript workflow that can **prove** (a) what was ordered, (b) when, and (c) what was filed.

**Why it matters:** COA clerk IOPs emphasize consequences for late transcript orders, and COA self-help materials emphasize strict compliance with appellate formatting and record requirements.

**Minimum acceptance criteria:**
- Transcript request packets per hearing:
  - hearing identifier (date/time/judge)
  - “what to transcribe” scope
  - request sent date
  - reporter contact (if known)
  - confirmation receipt artifact (email/letter)
- “Transcript status” states: `needed → requested → confirmed → filed → verified`.

### 1.5 Record completeness test: exhibits + attachments + audio/video
**What’s missing:** a check that the record you are relying on is complete enough to support your argument.

**Why it matters:** briefing requirements require facts supported by citations to the record. The COA brief cover-page checklist explicitly requires “Statement of Facts (with citation to the record)” and “Arguments (with applicable standard of review)” among other components.

**Minimum acceptance criteria:**
- For each factual proposition you intend to use, a **record citation target** exists:
  - file name + page number (or Bates)
  - docket entry association when available
- A “missing exhibits” radar (common failure mode: referenced exhibit never filed or not included in the appellate record).

### 1.6 Privacy/PII redaction lane (clerk gate)
**What’s missing:** a PII-safety layer that ensures higher-court filings will not be rejected or create downstream sealing/redaction problems.

**Why it matters:** Michigan has explicit rules and SCAO forms for protected personal identifying information (PII). MCR 1.109 is the core rule, and forms like **MC 97 / MC 97a** exist for submitting protected PII in a nonpublic manner.

**Minimum acceptance criteria:**
- Automated scan for protected PII patterns (DOB, SSN fragments, full financial account numbers, etc.)
- Output:
  - a redaction plan per document
  - list of required PII forms (MC 97 / MC 97a) where appropriate
  - optional MC 97r request pathway for redaction of protected PII already filed

## 2) Missing “case-type lanes” (custody/PT, ex parte, contempt)

### 2.1 Ex parte custody/parenting-time: “immediate response lane”
**What’s missing:** a dedicated lane that (a) detects an ex parte custody/PT/support order, (b) auto-creates the right response vehicle, and (c) tracks the procedural timeline.

**Michigan anchor points to build around:**
- **FOC 61** is the SCAO form for an objection to an ex parte order and motion to rescind/modify.
- Michigan Court Rules Chapter 3 includes a “procedure following service of ex parte order” rule section that, as adopted/amended, describes the court’s timing obligations for an evidentiary hearing when a motion to rescind/modify is filed.

**Minimum acceptance criteria:**
- Detect ex parte orders by:
  - caption keywords + rule references + FOC filing codes
  - order text patterns (“ex parte”, “temporary”, “without notice”)
- Auto-build:
  - a prefilled FOC 61 packet (data pulled from the record spine)
  - an exhibit list with the exact pages referenced
  - a deadline tracker keyed to service and filing

### 2.2 Parenting time: enforcement and make-up time lane
**What’s missing:** an enforcement lane that stays grounded in Michigan’s custody act framing and FOC operational reality.

**Michigan anchor points to build around:**
- Michigan law recognizes the importance of parenting time and a child’s right to parenting time absent endangerment findings; the Michigan Parenting Time Guideline cites MCL 722.27a and emphasizes the “strong relationship” policy framing.
- County FOC offices publish local forms/pamphlets; Muskegon County provides parenting-time forms/resources.

**Minimum acceptance criteria:**
- A structured “missed parenting time ledger” with:
  - date/time denied
  - method of denial/withholding
  - proof artifact (text, email, police report, third-party statement, etc.)
- A “requested remedy library” (make-up time schedule proposals, exchange logistics, communication protocols).

### 2.3 Contempt/show-cause lane: due-process compliance map
**What’s missing:** a contempt lane that enforces procedural minimums instead of only producing narratives.

**Michigan anchor points to build around:**
- Michigan Judicial Institute contempt materials include a checklist for indirect civil contempt proceedings and cite MCR 3.606 and MCL 600.1701 et seq.
- The contempt benchbook excerpt notes the service-to-hearing minimum timing rule in MCR 3.208(B)(4).

**Minimum acceptance criteria:**
- Per show-cause packet:
  - notice/order text
  - service proof
  - computed “earliest lawful hearing date”
  - hearing result summary (if transcript exists)
- A due-process “defect detector” that flags:
  - insufficient time after service
  - unclear allegations (no specific acts, dates, orders violated)
  - missing advisements (as applicable)

## 3) Missing “higher-court production lanes” (COA/MSC/original actions/JTC)

### 3.1 COA civil appeals: formatting + component completeness enforcement
**What’s missing:** a strict brief-composition validator.

**Michigan anchor points to build around:**
- The COA “Guide to Handling a Civil Appeal” highlights formatting requirements and points to MCR 7.212.
- The COA “Brief Cover Page” form enumerates required components (ToC, Index of Authorities, Jurisdictional Statement, Questions, Facts with record cites, Arguments with standard of review, Relief Requested, etc.).

**Minimum acceptance criteria:**
- A machine-checkable “brief structure contract” that verifies the presence/order of components.
- A record-citation validator that rejects “facts” paragraphs lacking record citations.

### 3.2 COA original actions (superintending control / mandamus / habeas)
**What’s missing:** a router that correctly distinguishes original actions from appeals and generates the correct initial pleading package.

**Michigan anchor points to build around:**
- The COA “Guide to Original Actions” states that the main court rule for original actions is MCR 7.203(C) and describes common original-action types.

**Minimum acceptance criteria:**
- A jurisdiction gate that answers:
  - Is this reviewable by appeal/leave, or is an original action appropriate?
  - Is there an adequate legal remedy?
  - What record is required to support the request?

### 3.3 Michigan Supreme Court (MSC) practice lane
**What’s missing:** a “MSC packaging” lane that aligns COA-derived briefing requirements with MSC-specific expectations.

**Michigan anchor points to build around:**
- The MSC “Guide for Counsel” notes that briefs in calendar cases must follow MCR 7.312(A), referencing MCR 7.212 requirements, and gives practical clerk-oriented guidance.

**Minimum acceptance criteria:**
- A “MSC application/briefing” checklist that:
  - imports the same structural contract used for COA (where incorporated)
  - adds MSC-specific procedural steps (service, appendices as required)

### 3.4 Judicial Tenure Commission (JTC) lane
**What’s missing:** a JTC-ready complaint package builder with rule-awareness.

**Michigan anchor points to build around:**
- JTC’s website explains the investigation/complaint process and warns that site pages may not reflect rule revisions; it points users to MCR 9.200 et seq. as governing.

**Minimum acceptance criteria:**
- A disciplined “allegation unit” format:
  - event → conduct → rule/canon anchor → proof artifact pointer → harm
- A “confidentiality awareness” gate (JTC rules/procedures have confidentiality features; the system should avoid leaking protected information).

## 4) Role-based acceptance tests (what each role needs to see)

### 4.1 Judge (trial or appellate)
A judge’s fast-path to trust is:
- **Clean procedural posture** (what order, what date entered, what jurisdictional vehicle)
- **Issues framed as questions** (each answerable “yes/no” where possible)
- **Record-cited facts only**
- **Standards of review** stated per issue
- **Specific relief requested**

### 4.2 Clerk (accept/reject gate)
A clerk-facing preflight should verify:
- Correct court + correct case number/caption
- Correct cover-page/checklist items for the filing type
- Formatting requirements satisfied (spacing, margins, font size) as described in COA self-help materials
- PII compliance (MCR 1.109 + SCAO PII forms)

### 4.3 Court reporter / stenographer (record survival)
A reporter-facing lane should:
- identify hearings needing transcription
- produce a clear scope (what parts)
- track confirmation and delivery
- store receipts as evidence

### 4.4 Prosecutor (credibility + enforceability lens)
Even in civil contexts, the “prosecutor lens” is useful for:
- whether allegations are **specific** and provable
- whether due process is satisfied (notice/time)
- whether the remedy requested is authorized and enforceable

### 4.5 Father (return-to-parenting-time outcomes)
The father’s lane should optimize for:
- fast restoration of contact where legally available
- prevention of future withholding (exchange protocol + make-up time)
- evidentiary cleanliness (no emotion-forward content without record anchors)

## 5) The “missing” modules to append to the operational loop (implementation-friendly)

### 5.1 Docket/ROA ingest module
- Inputs: PDFs, efile receipts, case history exports
- Output: `roa.json` + `roa.csv` + hash/provenance

### 5.2 PII/Redaction module
- Inputs: extracted text + source PDFs
- Output: `pii_findings.json` + redaction plan + MC 97/97a recommendations

### 5.3 Transcript module
- Inputs: hearing notices, dates, reporter info
- Output: `transcripts_needed.json` + request packets + status ledger

### 5.4 Brief/pleading “structure contract” validators
- Inputs: draft brief/complaint + record citations map
- Output: pass/fail with defect list and auto-repair suggestions

### 5.5 ServiceChain module
- Inputs: proofs of service, envelopes, efiling service confirmations
- Output: `service_chain.json` + computed timing constraints (e.g., show-cause minimum days)

## 6) Practical “missing radar” questions the system should answer automatically
- **Do we have file-stamped copies of every controlling order we rely on?**
- **Do we have proofs of service for every notice/order that matters to a due-process claim?**
- **Do we have transcripts for the hearings that matter to the appellate issues?**
- **Do all factual assertions in the brief have record citations?**
- **Is protected PII removed from public documents and provided via SCAO PII forms when necessary?**
- **Is the procedural vehicle correct (appeal vs leave vs original action vs JTC complaint)?**

## 7) Evidence acquisition plan triggers (fail-soft discovery-first)
When any item is missing, the correct behavior is:
- mark the missing artifact
- generate a concrete acquisition request
- continue building products that do not require the missing item

Typical acquisition targets:
- file-stamped orders
- ROA/case history printouts
- hearing notices
- proofs of service
- transcripts and audio recordings

