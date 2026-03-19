# APPEND-ONLY Judicial Case Outline and Analysis

## Scope

Append to prior results using the uploaded scan archives to build a chronological judicial outline and filing-route analysis for the Muskegon family/PPO lanes (MEEK2/MEEK3).

## Ingestion Summary

- Archives uploaded: **6**
- Unpacked successfully: **5**
- Failed/corrupt archive(s): **/mnt/data/SCANNED EXPARTE EMILY AND JUDGE DOCS.zip**
- Extracted records (this batch scope): **183**
- Chronology date span (curated): **2024-04-05 → 2026-01-06**

## Chronology

### Provenance tags
- **DOC_EXTRACTED** = date/event directly visible in uploaded scanned text
- **DOC_RECITED_ANALYSIS** = date/event recited inside uploaded NoReply chronology packet
- **USER_ASSERTED** = prior pinned user-position anchor

| chron_id | date | event | proof_tag | source_files |
| --- | --- | --- | --- | --- |
| CHRON-001 | 2024-04-05 | Complaint filed (custody/PT/child support) | DOC_EXTRACTED | 2sided judge orders scanned_0017.pdf |
| CHRON-002 | 2024-04-29 | Facilitative information conference and ex parte custody/PT/support order | DOC_EXTRACTED | 2sided judge orders scanned_0017.pdf |
| CHRON-003 | 2024-05-03 | Uniform Child Support Order effective date | DOC_EXTRACTED | 2sided judge orders scanned_0014.pdf; 2sided judge orders scanned_0013.pdf |
| CHRON-004 | 2024-06-05 | FOC recommendation entered (custody/PT/support sequence) | DOC_EXTRACTED | 2sided judge orders scanned_0016.pdf; 2sided judge orders scanned_0017.pdf |
| CHRON-005 | 2024-07-17 | Trial / support hearing resulting in UCSO pages | DOC_EXTRACTED | 2sided judge orders scanned_0013.pdf; 2sided judge orders scanned_0014.pdf |
| CHRON-006 | 2024-08-23 | Final Judgment entered (repeated court recitation) | DOC_EXTRACTED | 2sided judge orders scanned_0010.pdf; 2sided judge orders scanned_0017.pdf; custody scanned2_0016.pdf |
| CHRON-007 | 2025-02-14 | Plaintiff parenting-time motion filed | DOC_EXTRACTED | 2sided judge orders scanned_0009.pdf; 2sided judge orders scanned_0010.pdf |
| CHRON-008 | 2025-03-04 | FOC recommendation on Plaintiff parenting-time motion | DOC_EXTRACTED | 2sided judge orders scanned_0009.pdf; 2sided judge orders scanned_0010.pdf |
| CHRON-009 | 2025-03-26 | FOC recommendation packet (multi-page scanned recommendation set) | DOC_RECITED_ANALYSIS / DOC_EXTRACTED_PARTIAL | NoReply chronology packets (date recited); custody scanned pages 0038-0042 (recommendation/order text present, date OCR weak) |
| CHRON-010 | 2025-05-16 | Filing bond order appears in chronology (narrative packet) | DOC_RECITED_ANALYSIS | NoReply_20260105_131859_0010.pdf |
| CHRON-011 | 2025-05-20 | Order imposing $250 bond / order denying motion (page dated 5/20/2025) | DOC_EXTRACTED | 2sided judge orders scanned_0007.pdf |
| CHRON-012 | 2025-07-29 | Last parenting time / no contact since this date (user position) | USER_ASSERTED | personal_context_summary |
| CHRON-013 | 2025-08-06 | Ex parte order suspending parenting time (narrative chronology anchor) | DOC_RECITED_ANALYSIS | NoReply_20260105_131859_0009.pdf |
| CHRON-014 | 2025-08-08 | Defendant ex parte motion/order filing appears in scanned court packet | DOC_EXTRACTED | expartescannedandmine_0004.pdf |
| CHRON-015 | 2025-08-08 | Plaintiff verified objection to ex parte suspension motion (filed packet) | DOC_EXTRACTED | expartescannedandmine_0006.pdf |
| CHRON-016 | 2025-08-22 | Hearing date shown in Plaintiff prep/slideshow packet | DOC_EXTRACTED | expartescannedandmine_0007.pdf |
| CHRON-017 | 2025-08-28 | Evidentiary hearing continued to permit counsel / HealthWest records (narrative) | DOC_RECITED_ANALYSIS | NoReply_20260105_131859_0010.pdf |
| CHRON-018 | 2025-09-04 | Evidentiary hearing held | DOC_EXTRACTED | 2sided judge orders scanned_0001.pdf |
| CHRON-019 | 2025-09-09 | Order following 9/4 hearing signed | DOC_RECITED_ANALYSIS | NoReply_20260105_131859_0010.pdf |
| CHRON-020 | 2025-09-12 | Hearing date set then rescheduled to 10/29/2025 | DOC_EXTRACTED | 2sided judge orders scanned_0001.pdf |
| CHRON-021 | 2025-10-08 | HealthWest records/assessment discussion and no-contact concerns (narrative) | DOC_RECITED_ANALYSIS | NoReply_20260105_131859_0011.pdf |
| CHRON-022 | 2025-10-29 | Hearing appearance; oral disqualification motion denied; adjournment for second assessment issue | DOC_EXTRACTED / DOC_RECITED_ANALYSIS | 2sided judge orders scanned_0001.pdf; NoReply_20260105_131859_0011.pdf |
| CHRON-023 | 2025-11-23 | Contempt jail term start (user position) | USER_ASSERTED | personal_context_summary |
| CHRON-024 | 2025-11-26 | PPO violation hearing and order following hearing date appears in packet/order pages | DOC_EXTRACTED / DOC_RECITED_ANALYSIS | 2sided judge orders scanned_0001.pdf; NoReply_20260105_131859_0011.pdf |
| CHRON-025 | 2026-01-06 | Contempt jail term end (user position) | USER_ASSERTED | personal_context_summary |

## Analysis Highlights

- The **2-sided judge-order scan packet** acts as the chronology spine: it recites the complaint/facilitative/FOC/judgment chain and later ex parte-hearing milestones (including 9/4/2025, 10/29/2025, and 11/26/2025 references).
- The **ex parte scan packet** includes direct OCR hits for the ex parte suspension order/motion pages and a filed **verified objection** packet (8/8/2025 filing stamp visible).
- A scanned order page dated **5/20/2025** includes the **$250 bond** language for future motions; this is a major procedural leverage anchor.
- The order recitations mention a **HealthWest second-assessment** issue and adjournment logic, which supports your service/non-service and due-process analysis lane.

## Court Routing and Candidate Filings

| route_id | court | vehicle | status | anchor_events |
| --- | --- | --- | --- | --- |
| V-TRIAL-001 | Muskegon 14th Circuit (Family) | Motion to modify/restore parenting time + evidentiary hearing request | HIGH_PRIORITY (timeliness/order-pin check needed) | CHRON-013..CHRON-022 (+ CHRON-012 no-contact anchor) |
| V-TRIAL-002 | Muskegon 14th Circuit (Family) | Motion for relief from order / set-aside (service + due-process lane) | HIGH_PRIORITY (exact rule branch must be pinned) | CHRON-013..CHRON-022 |
| V-TRIAL-003 | Muskegon 14th Circuit (Family) | Motion to enforce parenting time / compensatory parenting time (or FOC enforcement) | CONDITIONAL on operative order terms | CHRON-012 + CHRON-023..CHRON-025 (subject to operative orders/PPO amendment) |
| V-TRIAL-004 | Muskegon 14th Circuit (Family) | Motion to settle/correct record + transcript/record completeness | HIGH_LEVERAGE record-survival step | CHRON-017..CHRON-024 |
| V-TRIAL-005 | Muskegon 14th Circuit (Family) | Written/renewed judicial disqualification motion (if new grounds) | CONDITIONAL (new grounds/timing required) | CHRON-022 (+ transcript/order text) |
| V-COA-001 | Michigan Court of Appeals | Application for leave / delayed application (family postjudgment orders) | TIMELINESS_BRANCH (ROA + entry dates required) | CHRON-013..CHRON-024 (plus appealable order IDs) |
| V-COA-002 | Michigan Court of Appeals | Emergency/stay motion tied to active parenting-time harm | CONDITIONAL but high-impact if branch open | CHRON-012..CHRON-025 + current operative order |
| V-MSC-001 | Michigan Supreme Court | Application for leave after COA disposition | FUTURE_BRANCH | COA-dependent |
| V-JTC-001 | Michigan Judicial Tenure Commission | JTC complaint packet (conduct chronology + record cites) | PARALLEL_NON-APPELLATE | CHRON-017..CHRON-024 + transcripts |

### Best-path filing order

1. **14th Circuit Family first** — restoration/relief/record-correction package (operative case lane).
2. **Parallel JTC build** — conduct chronology packet while transcripts/order chain are being pinned.
3. **COA branch** — finalize after ROA/order entry dates are pinned (timeliness branch).
4. **MSC branch** — stage after COA output unless a separate extraordinary route becomes supportable.

## Immediate acquisition targets for next append cycle

- Complete signed **order chain** (ex parte + post-hearing orders) with proofs of service
- **ROA / Register of Actions** for exact entry dates and timeliness calculations
- **Transcripts**: 8/28/2025, 9/4/2025, 10/29/2025, 11/26/2025
- HealthWest order/materials + service proof + delivery timing evidence

## Web verification status

`web.run` failed with an internal error during this pass, so I could not do live Michigan forms/rules verification. I proceeded with uploaded-record extraction and prior pinned context. Before filing, run one more pass to pin current forms and deadline rules from official Michigan sources.
