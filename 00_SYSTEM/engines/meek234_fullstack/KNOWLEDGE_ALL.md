# KNOWLEDGE_ALL — MEEK234 Fullstack Rebuild Pack v20260208_3 (Expanded)

## Counts

- **node_type**: 67
- **edge_type**: 88
- **enum**: 17
- **property_spec**: 157
- **vehicle_type**: 38
- **risk_type**: 21
- **clock_type**: 8
- **forum_gate_profile**: 6
- **denial_ground**: 25
- **record_packet_template**: 6
- **glossary_term**: 690

---

## Node Types

- `Case` — A case/docket (trial/appellate/JTC) with a case_id and posture.
- `Matter` — A matter bundle spanning one or more cases (MEEK2/3/4 lanes).
- `Track` — MEEK track lane (MEEK2/MEEK3/MEEK4).
- `Forum` — Forum layer: trial/coa/msc/jtc.
- `Court` — Court identity (e.g., 14th Circuit, Michigan Court of Appeals).
- `RegisterOfActions` — ROA container; links to ROA entries.
- `ROAEntry` — Single ROA line/item, with dates, doc type, and file/scan pointers.
- `Order` — Signed/entered order; contains effective/served/supersession state.
- `OperatingOrderPin` — Pinned operative controlling order for a candidate vehicle.
- `Event` — Typed event (hearing, filing, service, clerk notice, etc.).
- `ServiceEvent` — Service act: method, recipient, address selection, proof.
- `HearingEvent` — Hearing occurrence; links to transcript/recording.
- `EvidenceItem` — Evidence atom (document, audio, photo, transcript excerpt, etc.).
- `Exhibit` — Exhibit wrapper (with numbering + cover sheet metadata).
- `Transcript` — Transcript artifact; can be partial/full; includes cert status.
- `Recording` — Audio/video recording artifact; includes timestamp pinpoints.
- `Issue` — Legal issue node: preservation status, standard-of-review hooks.
- `Authority` — Authority node (MCR/MCL/MRE/case/benchbook/form).
- `RiskEvent` — Typed risk event (fatal/cureable/dismissal risk/etc.).
- `Clock` — Deadline clock derived from trigger events + tolling.
- `CurePacket` — Minimum packet needed to cure a specific defect/risk.
- `VehicleCandidate` — Candidate legal vehicle with gates + record products required.
- `PresentationGateProfile` — Forum-specific filing gate profile (COA/MSC/JTC strictness).
- `Party` — Party in a matter/case (person or org).
- `Person` — Natural person identity record.
- `Organization` — Organization identity record.
- `Attorney` — Attorney representation record.
- `Address` — Physical or mailing address with bi-temporal validity.
- `ContactPoint` — Phone/email/portal handle used for service/contact.
- `Child` — Child record relevant to custody/support/PT.
- `Filing` — A filed document (motion/brief/pleading/notice) with timestamps and method.
- `Pleading` — Pleading record type (complaint/answer/response).
- `Motion` — Motion record type with hearing linkage and requested relief.
- `Brief` — Brief record type (trial/court of appeals/supreme court).
- `Packet` — A compiled filing packet (record packet) prepared for submission.
- `CommitSuite` — A packaging run (manifested commit) produced by the system.
- `ParentingTimeProvision` — Parenting-time terms/provision in an order.
- `CustodyProvision` — Custody/legal/physical terms in an order.
- `SupportAccount` — Child support account snapshot record.
- `SupportLedgerEntry` — Child support ledger transaction/payment entry.
- `FOCAction` — Friend of the Court action/event (review, recommendation, enforcement).
- `PPO` — Personal Protection Order record.
- `ContemptProceeding` — Contempt proceeding record (civil/criminal, bench-trial, show cause).
- `Warrant` — Warrant/mittimus/bench warrant record.
- `Bond` — Bond/bail condition record.
- `JailCommitment` — Jail commitment/mitimus execution record.
- `EvidenceAtom` — Atomic evidence fact/pointer with provenance, hash, and pinpoints.
- `QuotePin` — Verbatim quote segment pointer (page/line/timecode).
- `ChainOfCustody` — Chain-of-custody log entry for an evidence item.
- `AuthenticationRule` — MRE/MCR authentication or admissibility rule binding to evidence/exhibit.
- `HearsayRule` — Hearsay exception/definition mapping for evidence.
- `BestEvidenceRule` — Best evidence/best available copy requirement mapping.
- `Appeal` — Appeal proceeding record (COA/MSC) with docketing and briefing clocks.
- `ApplicationForLeave` — Application for leave record (COA/MSC).
- `ClaimOfAppeal` — Claim of appeal record (appeal of right).
- `DocketingStatement` — Docketing statement record (COA).
- `BriefingSchedule` — Briefing schedule record (COA/MSC).
- `ClerkLetter` — Clerk warning/deficiency letter (return-without-docketing, cure window).
- `JTCComplaint` — Judicial Tenure Commission complaint record.
- `JTCMilestone` — JTC process milestone event (screening/investigation/charges/etc.).
- `MisconductAllegation` — Allegation of judicial misconduct, mapped to canon/rule and evidence.
- `CanonRule` — Judicial canon or ethics rule reference.
- `StandardOfReview` — Standard of review definition and triggers.
- `DenialGround` — Denial ground template keyed to vehicle and record gaps.
- `Remedy` — Requested remedy/relief definition and constraints.
- `Sanction` — Sanction/remedy imposed by court.
- `Deadline` — Derived deadline with clock, tolling, and service dependencies.

---

## Edge Types

- `MATTER_HAS_CASE`: `Matter` → `Case` — Matter contains a case.
- `CASE_IN_FORUM`: `Case` → `Forum` — Case belongs to a forum layer.
- `CASE_IN_COURT`: `Case` → `Court` — Case is in a court.
- `MATTER_IN_TRACK`: `Matter` → `Track` — Matter lane assignment.
- `CASE_HAS_ROA`: `Case` → `RegisterOfActions` — Case has ROA.
- `ROA_HAS_ENTRY`: `RegisterOfActions` → `ROAEntry` — ROA contains entries.
- `ENTRY_HAS_ORDER`: `ROAEntry` → `Order` — Entry corresponds to an order.
- `CASE_HAS_ORDER`: `Case` → `Order` — Order in case.
- `ORDER_SUPERSEDES`: `Order` → `Order` — Order supersedes a prior order.
- `ORDER_STAYED_BY`: `Order` → `Order` — Order stayed by another order.
- `VEHICLE_REQUIRES_OPERATING_PIN`: `VehicleCandidate` → `OperatingOrderPin` — Candidate requires pinned operative order.
- `PIN_POINTS_TO_ORDER`: `OperatingOrderPin` → `Order` — Pin points to an order.
- `CASE_HAS_EVENT`: `Case` → `Event` — Case event.
- `EVENT_HAS_SERVICE`: `Event` → `ServiceEvent` — Event includes service step.
- `EVENT_HAS_HEARING`: `Event` → `HearingEvent` — Event includes hearing.
- `HEARING_HAS_TRANSCRIPT`: `HearingEvent` → `Transcript` — Hearing transcript link.
- `HEARING_HAS_RECORDING`: `HearingEvent` → `Recording` — Hearing recording link.
- `CASE_HAS_EVIDENCE`: `Case` → `EvidenceItem` — Evidence belongs to case.
- `EVIDENCE_AS_EXHIBIT`: `EvidenceItem` → `Exhibit` — Evidence packaged as an exhibit.
- `ISSUE_IN_CASE`: `Issue` → `Case` — Issue arises in case.
- `ISSUE_SUPPORTED_BY_EVIDENCE`: `Issue` → `EvidenceItem` — Issue supported by evidence.
- `ISSUE_GOVERNED_BY_AUTHORITY`: `Issue` → `Authority` — Issue governed by authority.
- `RISK_IN_CASE`: `RiskEvent` → `Case` — Risk event in case.
- `RISK_HAS_CURE_PACKET`: `RiskEvent` → `CurePacket` — Risk cure packet.
- `CASE_HAS_CLOCK`: `Case` → `Clock` — Case clock.
- `RISK_DEPENDS_ON_CLOCK`: `RiskEvent` → `Clock` — Risk depends on clock.
- `CASE_HAS_VEHICLE_CANDIDATE`: `Case` → `VehicleCandidate` — Case candidate vehicle.
- `VEHICLE_GOVERNED_BY_AUTHORITY`: `VehicleCandidate` → `Authority` — Vehicle governed by authority.
- `FORUM_HAS_GATE_PROFILE`: `Forum` → `PresentationGateProfile` — Forum gate profile.
- `CASE_HAS_PARTY`: `Case` → `Party` — Case includes a party.
- `PARTY_IS_PERSON`: `Party` → `Person` — Party links to person identity.
- `PARTY_IS_ORG`: `Party` → `Organization` — Party links to organization identity.
- `PARTY_HAS_ADDRESS`: `Party` → `Address` — Party has address (bi-temporal).
- `PARTY_HAS_CONTACT`: `Party` → `ContactPoint` — Party contact point.
- `CASE_HAS_CHILD`: `Case` → `Child` — Case child subject.
- `CASE_HAS_FOC_ACTION`: `Case` → `FOCAction` — FOC action within case.
- `PARTY_REPRESENTED_BY`: `Party` → `Attorney` — Party representation.
- `ATTORNEY_HAS_CONTACT`: `Attorney` → `ContactPoint` — Attorney contact point.
- `ATTORNEY_HAS_ADDRESS`: `Attorney` → `Address` — Attorney address.
- `CASE_HAS_FILING`: `Case` → `Filing` — Case filing.
- `FILING_IS_MOTION`: `Filing` → `Motion` — Filing motion subtype.
- `FILING_IS_PLEADING`: `Filing` → `Pleading` — Filing pleading subtype.
- `FILING_IS_BRIEF`: `Filing` → `Brief` — Filing brief subtype.
- `FILING_COMPILED_IN_PACKET`: `Filing` → `Packet` — Filing included in a packet.
- `PACKET_EMITTED_BY_COMMIT`: `Packet` → `CommitSuite` — Packet produced by a commit suite.
- `MOTION_SET_FOR_HEARING`: `Motion` → `HearingEvent` — Motion scheduled for hearing.
- `MOTION_SEEKS_REMEDY`: `Motion` → `Remedy` — Motion seeks remedy.
- `ORDER_CONTAINS_PT_PROVISION`: `Order` → `ParentingTimeProvision` — Order contains parenting time provision.
- `ORDER_CONTAINS_CUSTODY_PROVISION`: `Order` → `CustodyProvision` — Order contains custody provision.
- `CASE_HAS_SUPPORT_ACCOUNT`: `Case` → `SupportAccount` — Case child support account snapshot.
- `SUPPORT_ACCOUNT_HAS_LEDGER`: `SupportAccount` → `SupportLedgerEntry` — Support account ledger entries.
- `LEDGER_ENTRY_IS_EVENT`: `SupportLedgerEntry` → `Event` — Ledger entry as an event.
- `CASE_HAS_PPO`: `Case` → `PPO` — Case has PPO record.
- `PPO_HAS_ORDER`: `PPO` → `Order` — PPO order.
- `CASE_HAS_CONTEMPT`: `Case` → `ContemptProceeding` — Case has contempt proceeding.
- `CONTEMPT_HAS_WARRANT`: `ContemptProceeding` → `Warrant` — Contempt related warrant/mitimus.
- `CONTEMPT_RESULTS_IN_JAIL`: `ContemptProceeding` → `JailCommitment` — Contempt results in jail commitment.
- `CONTEMPT_HAS_SANCTION`: `ContemptProceeding` → `Sanction` — Contempt sanction.
- `CASE_HAS_BOND`: `Case` → `Bond` — Case bond record.
- `BOND_IS_ORDERED_BY`: `Bond` → `Order` — Bond conditions ordered by an order.
- `EVIDENCE_ATOM_SUPPORTS_EVENT`: `EvidenceAtom` → `Event` — Evidence atom supports an event.
- `EVIDENCE_ATOM_SUPPORTS_ISSUE`: `EvidenceAtom` → `Issue` — Evidence atom supports an issue.
- `EVIDENCE_ATOM_SUPPORTS_ALLEGATION`: `EvidenceAtom` → `MisconductAllegation` — Evidence atom supports allegation.
- `EVIDENCE_ATOM_DERIVED_FROM_ITEM`: `EvidenceAtom` → `EvidenceItem` — Evidence atom derived from evidence item.
- `EVIDENCE_ITEM_HAS_COC`: `EvidenceItem` → `ChainOfCustody` — Evidence item chain-of-custody.
- `EVIDENCE_ITEM_HAS_QUOTE_PIN`: `EvidenceItem` → `QuotePin` — Evidence item has quote pinpoints.
- `QUOTE_PIN_IN_TRANSCRIPT`: `QuotePin` → `Transcript` — Quote pin in transcript.
- `QUOTE_PIN_IN_ORDER`: `QuotePin` → `Order` — Quote pin in order.
- `QUOTE_PIN_IN_RECORDING`: `QuotePin` → `EvidenceItem` — Quote pin in recording/audio/video.
- `EVIDENCE_ITEM_AUTH_RULE`: `EvidenceItem` → `AuthenticationRule` — Authentication/admissibility mapping.
- `EVIDENCE_ITEM_HEARSAY_RULE`: `EvidenceItem` → `HearsayRule` — Hearsay mapping.
- `EVIDENCE_ITEM_BEST_EVIDENCE`: `EvidenceItem` → `BestEvidenceRule` — Best-evidence mapping.
- `CASE_HAS_APPEAL`: `Case` → `Appeal` — Case has appeal.
- `APPEAL_HAS_CLAIM_OF_APPEAL`: `Appeal` → `ClaimOfAppeal` — Appeal includes claim of appeal.
- `APPEAL_HAS_APP_LEAVE`: `Appeal` → `ApplicationForLeave` — Appeal includes application for leave.
- `APPEAL_HAS_DOCKETING_STATEMENT`: `Appeal` → `DocketingStatement` — Appeal docketing statement.
- `APPEAL_HAS_BRIEFING_SCHEDULE`: `Appeal` → `BriefingSchedule` — Appeal briefing schedule.
- `APPEAL_RECEIVES_CLERK_LETTER`: `Appeal` → `ClerkLetter` — Appeal clerk letter/notice.
- `CASE_HAS_JTC_COMPLAINT`: `Case` → `JTCComplaint` — Case track includes JTC complaint.
- `JTC_COMPLAINT_HAS_MILESTONE`: `JTCComplaint` → `JTCMilestone` — JTC process milestone.
- `CASE_HAS_MISCONDUCT_ALLEGATION`: `Case` → `MisconductAllegation` — Case alleges misconduct.
- `ALLEGATION_VIOLATES_CANON`: `MisconductAllegation` → `CanonRule` — Allegation mapped to canon/rule.
- `ALLEGATION_SUPPORTED_BY_EVIDENCE`: `MisconductAllegation` → `EvidenceAtom` — Allegation supported by evidence.
- `CASE_HAS_ISSUE`: `Case` → `Issue` — Case issue list.
- `ISSUE_HAS_STANDARD_OF_REVIEW`: `Issue` → `StandardOfReview` — Issue standard of review.
- `VEHICLE_DENIAL_GROUND`: `VehicleCandidate` → `DenialGround` — Vehicle candidate denial grounds.
- `CASE_HAS_DEADLINE`: `Case` → `Deadline` — Case derived deadline.
- `DEADLINE_TRACKED_BY_CLOCK`: `Deadline` → `Clock` — Deadline backed by a clock.

---

## Enums

- `risk_class`: jurisdictional_fatal|admin_return_without_docketing|curable_defect|dismissal_risk|record_incomplete|discretionary_sanction_risk
- `track`: MEEK2|MEEK3|MEEK4
- `forum`: trial|coa|msc|jtc
- `court_level`: district|circuit|coa|msc|jtc|other
- `event_kind`: FilingEvent|HearingEvent|ServiceEvent|ClerkNoticeEvent|TranscriptEvent|OrderEvent|PaymentEvent|ExtensionEvent|OtherEvent|SupportEvent|PPOEvent|ContemptEvent|FOCEvent|AppealEvent|JTCEvent
- `order_status`: entered|signed|served|effective|superseded|stayed|unknown
- `hearing_kind`: motion|evidentiary|showcause|trial|referee|settlement|other
- `party_role`: petitioner|respondent|plaintiff|defendant|appellant|appellee|complainant|judge|friend_of_court|other
- `filing_kind`: motion|pleading|brief|notice|order|affidavit|exhibit_list|appendix|transcript_request|claim_of_appeal|application_leave|other
- `service_method_enum`: personal|certified_mail|registered_mail|first_class_mail|electronic|publication|unknown
- `motion_kind`: modify_parenting_time|modify_custody|enforce_parenting_time|show_cause_contempt|set_aside|reconsideration|stay|fees_sanctions|recusal_disqualification|other
- `evidence_kind`: document|photo|video|audio|text_message|email|social_media|court_record|transcript|recording|other
- `record_item_kind`: order|transcript|exhibit|pleading|motion|brief|notice|proof_of_service|payment_record|other
- `exhibit_color`: plaintiff_yellow|defendant_blue|neutral_white
- `issue_stage`: trial|postjudgment|appeal_coa|appeal_msc|jtc
- `standard_of_review_kind`: de_novo|clear_error|abuse_discretion|plain_error|substantial_evidence|mixed
- `deadline_source`: rule|statute|order|clerk_letter|system

---

## Vehicle Types

- `MEEK2_TRIAL_enforce_parenting_time` [MEEK2/trial] — Motion to Enforce Parenting Time / Make-Up Time / Sanctions
  - requires_operating_order_pin: True
  - record_products:
    - OperatingOrderPin
    - Chronology of denied PT events
    - Service proofs and notices
    - Requested remedy matrix
  - authority_refs:
    - MCL: MCL 552.6xx (parenting time enforcement act) — statutory enforcement lane.

- `MEEK2_TRIAL_modify_custody_parenting_time` [MEEK2/trial] — Motion to Modify Custody/Parenting Time
  - requires_operating_order_pin: True
  - record_products:
    - OperatingOrderPin
    - ROAEntry pointers
    - Proposed order
    - Verified facts/affidavit (if required by posture)
    - Exhibit set with foundations
  - authority_refs:
    - MCR: MCR 3.210 — custody proceedings framework (chapter 3).

- `MEEK2_TRIAL_objection_referee_recommendation` [MEEK2/trial] — Objection to FOC Referee Recommendation / De Novo Review Request
  - requires_operating_order_pin: True
  - record_products:
    - OperatingOrderPin
    - Referee recommendation document
    - Transcript/record (if hearing held)
    - Objection grounds matrix
  - authority_refs:
    - MCR: MCR 3.215 / local FOC procedure — objection and review mechanics vary by type.

- `MEEK2_TRIAL_show_cause_contempt` [MEEK2/trial] — Motion for Order to Show Cause (Custody/Support/PT Contempt)
  - requires_operating_order_pin: True
  - record_products:
    - OperatingOrderPin
    - Affidavit with dates/acts
    - Proposed OSC + service plan
  - authority_refs:
    - MCR: MCR 3.606 / contempt rules — civil/criminal contempt distinctions.

- `MEEK3_COA_claim_of_appeal_ppo` [MEEK3/coa] — Claim of Appeal (PPO appeal of right where applicable)
  - requires_operating_order_pin: True
  - record_products:
    - OperatingOrderPin
    - Timeliness clock proof (entered date)
    - Docketing statement packet
    - Transcript order + proof
  - authority_refs:
    - MCR: MCR 3.709 — PPO appeal routes (rights vs leave).
    - MCR: MCR 7.204 — claim of appeal timing.

- `MEEK3_TRIAL_motion_modify_terminate_ppo` [MEEK3/trial] — Motion to Modify/Terminate PPO
  - requires_operating_order_pin: True
  - record_products:
    - OperatingOrderPin
    - Service proofs for motion + notice of hearing
    - Affidavit(s) + exhibits
  - authority_refs:
    - MCR: MCR 3.707 — time/service rules for modification/termination.

- `MEEK3_TRIAL_motion_show_cause_ppo_contempt` [MEEK3/trial] — Motion to Show Cause (PPO Violation Contempt)
  - requires_operating_order_pin: True
  - record_products:
    - OperatingOrderPin
    - Affidavit + exhibits
    - Hearing record plan (witnesses, transcript)
  - authority_refs:
    - MCR: MCR 3.708 — PPO contempt procedure.

- `MEEK4_COA_superintending_control` [MEEK4/coa] — COA Original Action / Superintending Control (Mandamus/Prohibition)
  - requires_operating_order_pin: True
  - record_products:
    - OperatingOrderPin
    - Verified complaint/petition
    - Appendix/record packet
    - Jurisdiction + adequacy-of-remedy analysis
  - authority_refs:
    - MCR: MCR 7.203(C) (original jurisdiction) — COA superintending control lane.

- `MEEK4_JTC_request_for_investigation` [MEEK4/jtc] — JTC Request for Investigation (Judicial Misconduct)
  - requires_operating_order_pin: True
  - record_products:
    - OperatingOrderPin
    - Verified request (oath/verification)
    - Chronology + issue list
    - Evidence packet + pinpoints
    - Confidentiality handling plan
  - authority_refs:
    - MCR: MCR 9.220 et seq. — JTC process and filings.

- `MEEK4_MSC_original_action_superintending_control` [MEEK4/msc] — MSC Original Action / Superintending Control
  - requires_operating_order_pin: True
  - record_products:
    - OperatingOrderPin
    - Verified complaint/petition
    - Appendix packet
    - Why extraordinary relief is necessary
  - authority_refs:
    - MCR: MCR 7.306 — MSC original proceedings.

- `MEEK4_TRIAL_motion_disqualify_judge` [MEEK4/trial] — Motion to Disqualify Judge
  - requires_operating_order_pin: True
  - record_products:
    - OperatingOrderPin
    - Record excerpts supporting disqualification grounds
    - Affidavit (if required)
    - Prior rulings timeline
  - authority_refs:
    - MCR: MCR 2.003 — disqualification procedure and timing.

- `VEH_meek2_appeal_coa_app_for_leave` [MEEK2/coa] — Application for leave to appeal (custody/support interlocutory or discretionary)
  - requires_operating_order_pin: True
  - record_products:
    - OperatingOrderPin
    - Order + ROA entry
    - Application packet + appendix
    - Fee/IFP
    - Service proof
  - authority_refs:
    - MCR: varies — See relevant rule/vehicle.

- `VEH_meek2_appeal_coa_claim_of_appeal` [MEEK2/coa] — Claim of appeal from final custody/support order (as applicable)
  - requires_operating_order_pin: True
  - record_products:
    - OperatingOrderPin
    - Appealed order + ROA entry
    - Claim of appeal + fee/IFP
    - Service proof
    - Docketing statement
  - authority_refs:
    - MCR: varies — See relevant rule/vehicle.

- `VEH_meek2_emergency_motion_parenting_time` [MEEK2/trial] — Emergency ex parte/short-notice motion re parenting time (when permitted)
  - requires_operating_order_pin: True
  - record_products:
    - OperatingOrderPin
    - Immediate harm/facts affidavit
    - Proposed interim order
    - Service plan / notice statement
    - Exhibits
  - authority_refs:
    - MCR: varies — See relevant rule/vehicle.

- `VEH_meek2_foc_review_request` [MEEK2/trial] — Request for Friend of the Court review/recommendation
  - requires_operating_order_pin: True
  - record_products:
    - OperatingOrderPin
    - FOCAction request form/letter
    - Issue statement
    - Supporting exhibits
    - Service plan (if required)
  - authority_refs:
    - MCL: 552.505 et seq (FOC Act) — Friend of the Court authority and procedures.

- `VEH_meek2_motion_contempt_parenting_time_order` [MEEK2/trial] — Motion for order to show cause (parenting-time order enforcement contempt)
  - requires_operating_order_pin: True
  - record_products:
    - OperatingOrderPin
    - Specific violation events
    - Notice/service proof
    - Requested sanctions/remedies
    - Exhibits
  - authority_refs:
    - MCR: varies — See relevant rule/vehicle.

- `VEH_meek2_motion_enforce_parenting_time_act` [MEEK2/trial] — Parenting Time Enforcement Act motion (makeup time, enforcement, fees)
  - requires_operating_order_pin: True
  - record_products:
    - OperatingOrderPin
    - Parenting-time order provision(s) at issue
    - Parenting-time denial events (Event nodes)
    - Notice/service proofs
    - Requested remedies (makeup time, fees, penalties)
    - Exhibits (messages, ROA, police/FOC records if any)
  - authority_refs:
    - MCL: 552.641 et seq (Parenting Time Enforcement Act) — Enforcement mechanisms, makeup time, and remedies.

- `VEH_meek2_motion_modify_child_support` [MEEK2/trial] — Motion to modify child support
  - requires_operating_order_pin: True
  - record_products:
    - OperatingOrderPin
    - Current support order
    - Income proofs (both parties if available)
    - Overnights/parenting-time schedule proof
    - Health insurance + childcare expense proof
    - MCSF calculation worksheet outputs
    - Service plan
  - authority_refs:
    - SCAO/FOC: Michigan Child Support Formula (MCSF) — Guideline-based support calculation framework.

- `VEH_meek2_motion_modify_custody` [MEEK2/trial] — Motion to modify custody (legal/physical)
  - requires_operating_order_pin: True
  - record_products:
    - OperatingOrderPin
    - Custody order/provisions
    - ECE (established custodial environment) evidence mapping
    - Best-interests factor mapping
    - Service plan
    - Proposed order
  - authority_refs:
    - MCL: 722.27 (custody; ECE/change) — Custody modification statute.
    - MCL: 722.23 (best interests factors) — Best interest factors.

- `VEH_meek2_motion_modify_parenting_time` [MEEK2/trial] — Motion to modify parenting time
  - requires_operating_order_pin: True
  - record_products:
    - OperatingOrderPin
    - Current parenting-time order (signed/entered)
    - Proposed order/provisions
    - Service plan + address selection
    - Factual basis (change of circumstances / best interests mapping)
    - Exhibit list + proofs
  - authority_refs:
    - MCL: 722.27a (parenting time) — Parenting time statute; court may grant/modify; factors and terms.
    - MCR: 3.210 et seq (domestic relations) — Domestic relations procedural framework (see chapter 3).

- `VEH_meek2_motion_reconsideration` [MEEK2/trial] — Motion for reconsideration (trial court)
  - requires_operating_order_pin: True
  - record_products:
    - OperatingOrderPin
    - Target order + entry date
    - Grounds (palpable error / new evidence)
    - Service proof
    - Proposed order
  - authority_refs:
    - MCR: varies — See relevant rule/vehicle.

- `VEH_meek2_motion_set_aside` [MEEK2/trial] — Motion for relief from judgment/order (trial court)
  - requires_operating_order_pin: True
  - record_products:
    - OperatingOrderPin
    - Target order/judgment
    - Grounds
    - Supporting evidence
    - Service proof
    - Proposed order
  - authority_refs:
    - MCR: varies — See relevant rule/vehicle.

- `VEH_meek3_coa_application_for_leave` [MEEK3/coa] — Application for leave to appeal (COA)
  - requires_operating_order_pin: True
  - record_products:
    - OperatingOrderPin
    - Order + ROA entry
    - Application packet (questions presented, statement of facts, argument)
    - Appendix per rule
    - Fee/IFP
    - Service proof
  - authority_refs:
    - MCR: 7.205 (time for application for leave) — Jurisdictional time requirements for leave applications.

- `VEH_meek3_coa_claim_of_appeal` [MEEK3/coa] — Claim of appeal (appeal of right) from final order / contempt order (as applicable)
  - requires_operating_order_pin: True
  - record_products:
    - OperatingOrderPin
    - Appealed order + ROA entry
    - Proof of entry date (ROA)
    - Claim of appeal form + fee/IFP
    - Jurisdictional statement
    - Service proof
    - Docketing statement clock tracking
  - authority_refs:
    - MCR: 7.204 (time for claim of appeal) — Jurisdictional 21-day period in civil cases unless otherwise provided.

- `VEH_meek3_coa_motion_stay` [MEEK3/coa] — Court of Appeals motion for stay (pending appeal)
  - requires_operating_order_pin: True
  - record_products:
    - OperatingOrderPin
    - Appealed order
    - Jurisdictional basis (claim/app)
    - Affidavit of harm
    - Appendix/exhibits
    - Service proof
  - authority_refs:
    - MCR: varies — See relevant rule/vehicle.

- `VEH_meek3_motion_disqualify_judge` [MEEK3/trial] — Motion to disqualify judge
  - requires_operating_order_pin: True
  - record_products:
    - OperatingOrderPin
    - Grounds narrative + pinpoints
    - Affidavit (if required)
    - Service plan
    - Proposed order
  - authority_refs:
    - MCR: 2.003 (disqualification) — Procedure and timing for disqualification requests.

- `VEH_meek3_motion_modify_terminate_ppo` [MEEK3/trial] — Motion to modify or terminate PPO
  - requires_operating_order_pin: True
  - record_products:
    - OperatingOrderPin
    - PPO order + ROA pin
    - Service proof/notice compliance
    - Factual basis + exhibits
    - Requested modifications/termination terms
  - authority_refs:
    - MCR: 3.707 (motion to modify/terminate PPO) — PPO modification/termination procedure.

- `VEH_meek3_motion_reconsideration` [MEEK3/trial] — Motion for reconsideration (PPO/contempt context)
  - requires_operating_order_pin: True
  - record_products:
    - OperatingOrderPin
    - Target order + entry date
    - Grounds
    - Service proof
    - Proposed order
  - authority_refs:
    - MCR: varies — See relevant rule/vehicle.

- `VEH_meek3_motion_stay` [MEEK3/trial] — Motion for stay of proceedings / stay of sentence (as applicable)
  - requires_operating_order_pin: True
  - record_products:
    - OperatingOrderPin
    - Basis for stay
    - Proposed order
    - Service proof
  - authority_refs:
    - MCR: varies — See relevant rule/vehicle.

- `VEH_meek3_motion_to_quash` [MEEK3/trial] — Motion to quash / modify subpoena (if needed)
  - requires_operating_order_pin: True
  - record_products:
    - OperatingOrderPin
    - Subpoena copy
    - Grounds
    - Service proof
    - Proposed order
  - authority_refs:
    - MCR: varies — See relevant rule/vehicle.

- `VEH_meek3_msc_application_for_leave` [MEEK3/msc] — Michigan Supreme Court application for leave (or further review) (as applicable)
  - requires_operating_order_pin: True
  - record_products:
    - OperatingOrderPin
    - COA disposition order/opinion
    - MSC application packet (questions presented, reasons for review, argument)
    - Appendix
    - Fee/IFP
    - Service proof
    - Nonconforming filing cure plan
  - authority_refs:
    - MCR: 7.305 (MSC filing; nonconforming effect) — Nonconforming filings do not satisfy time limits; cure rules apply.

- `VEH_meek3_show_cause_response_packet` [MEEK3/trial] — Show-cause / contempt response packet (PPO violation allegations)
  - requires_operating_order_pin: True
  - record_products:
    - OperatingOrderPin
    - Show-cause order/notice + service proof
    - Allegation matrix (counts ↔ evidence)
    - Defense exhibits + authentication notes
    - Witness list + subpoenas if needed
    - Proposed findings/order
  - authority_refs:
    - MCR: 3.708/3.709 (PPO contempt procedure/appeal) — Contempt hearing and appeal rules for PPO matters.

- `VEH_meek3_transcript_request` [MEEK3/trial] — Transcript/recording request and certification packet
  - requires_operating_order_pin: True
  - record_products:
    - OperatingOrderPin
    - Hearing date + court reporter info
    - Payment/IFP (if applicable)
    - Request letter/form
    - Proof of request/receipt
  - authority_refs:
    - MCR: varies — See relevant rule/vehicle.

- `VEH_meek4_coa_superintending_control` [MEEK4/coa] — COA original action: superintending control/mandamus/prohibition (as applicable)
  - requires_operating_order_pin: True
  - record_products:
    - OperatingOrderPin
    - Jurisdictional statement
    - Record packet
    - Request for relief
    - Service proof
    - Prior lower-court request/disposition
  - authority_refs:
    - MCR: varies — See relevant rule/vehicle.

- `VEH_meek4_jtc_complaint` [MEEK4/jtc] — Judicial Tenure Commission complaint (judicial misconduct)
  - requires_operating_order_pin: True
  - record_products:
    - OperatingOrderPin
    - MisconductAllegation list (typed)
    - EvidenceAtom pointers + quote pins
    - CanonRule mapping
    - Chronological timeline
    - Packaging + confidentiality labeling
    - Proof of prior administrative remedies (if any)
  - authority_refs:
    - MCR: 9.200 et seq (JTC procedure) — Michigan Court Rules governing JTC proceedings.

- `VEH_meek4_jtc_response_28_day_letter` [MEEK4/jtc] — Response packet to JTC 28-day letter/request (if issued)
  - requires_operating_order_pin: True
  - record_products:
    - OperatingOrderPin
    - JTC notice/letter
    - Requested information
    - EvidenceAtom pointers
    - Narrative response
    - Attachment list
  - authority_refs:
    - MCR: varies — See relevant rule/vehicle.

- `VEH_meek4_msc_complaint_administrative` [MEEK4/msc] — MSC complaint about administrative/court operations (if applicable)
  - requires_operating_order_pin: True
  - record_products:
    - OperatingOrderPin
    - Facts + supporting documentation
    - Prior requests to local administration
    - Relief requested
    - Service/notice plan
  - authority_refs:
    - MCR: varies — See relevant rule/vehicle.

- `VEH_meek4_msc_superintending_control` [MEEK4/msc] — Superintending control / original action (as applicable)
  - requires_operating_order_pin: True
  - record_products:
    - OperatingOrderPin
    - Jurisdictional basis statement
    - Record packet (orders, transcripts, ROA)
    - Relief requested
    - Service plan
    - Prior requests to lower court + disposition
  - authority_refs:
    - MCR: 3.302 (superintending control) — Superintending control procedure (trial/original actions).
    - MCR: 7.305 (MSC filings) — MSC filing and nonconforming rules.


---

## Risk Types

- `RISK_missing_operating_order_pin_any` [*/*] (record_incomplete; sev=70) — Operating Order Pin missing for candidate vehicle
  - trigger_when: MISSING_NODE:OperatingOrderPin
  - cure_cost: 2
  - cure_deadline_clock: next_filing_deadline
  - cure_minimum_packet:
    - Identify operative controlling order (signed/entered/served/effective)
    - Pin ROA entry id + upload order PDF + service proof if available
    - Supersession/stay links (if any)
  - authority_refs:
    - LitigationOS: OperatingOrderPin requirement — System gate: pin operative order before selecting vehicle.

- `RISK_clerk_notice_unprocessed` [*/*] (curable_defect; sev=65) — Clerk notice/deficiency letter not processed
  - trigger_when: EVENT_KIND_PRESENT:ClerkNoticeEvent
  - cure_cost: 2
  - cure_deadline_clock: clerk_cure_window
  - cure_minimum_packet:
    - Parse notice; extract cure window + required items
    - Assemble cure packet + proof of filing
    - If dismissed/returned: motion to reinstate or refile as permitted
  - authority_refs:
    - COA/MSC/JTC practice: clerk notices/deficiency letters — Modeled as TriggerEvent→Clock→RiskEvent.

- `COA_claim_of_appeal_late` [*/coa] (jurisdictional_fatal; sev=95) — Claim of appeal appears untimely
  - trigger_when: CLOCK_EXPIRED:coa_claim_of_appeal
  - cure_cost: 5
  - cure_deadline_clock: coa_claim_of_appeal
  - cure_minimum_packet:
    - Verify entered date of appealed order (ROA/order)
    - If late: evaluate other vehicle (leave, delayed leave, superintending control)
  - authority_refs:
    - MCR: MCR 7.204(A) — time limits for claim of appeal.

- `COA_docketing_statement_missing` [*/coa] (dismissal_risk; sev=85) — Docketing statement missing/late
  - trigger_when: MISSING_PACKET:coa_docketing_statement
  - cure_cost: 2
  - cure_deadline_clock: coa_docketing_statement_due
  - cure_minimum_packet:
    - Completed docketing statement
    - Fee waiver (if needed)
    - Proof of filing + service
  - authority_refs:
    - MCR: MCR 7.212(H) — docketing statement timing + IOP deficiency-letter practice.

- `COA_dismissal_letter_cure_window_running` [*/coa] (dismissal_risk; sev=88) — COA deficiency letter cure window running
  - trigger_when: EVENT_TAG_PRESENT:coa_deficiency_letter
  - cure_cost: 3
  - cure_deadline_clock: coa_deficiency_cure
  - cure_minimum_packet:
    - All items listed in deficiency letter
    - Cover letter referencing deficiency
    - Proof of filing + service
  - authority_refs:
    - COA IOP: IOP 7.204(H)(1)-(3) — deficiency letter and potential dismissal.

- `COA_transcript_order_missing` [*/coa] (record_incomplete; sev=80) — Transcript not ordered/arranged; record risk
  - trigger_when: MISSING_PACKET:coa_transcript_request
  - cure_cost: 3
  - cure_deadline_clock: coa_transcript_due
  - cure_minimum_packet:
    - Transcript order/request + proof
    - Statement of transcript filing/certification as required
  - authority_refs:
    - MCR: MCR 7.210(B) — ordering transcripts and record.

- `MSC_application_leave_late` [*/msc] (jurisdictional_fatal; sev=95) — MSC application for leave appears untimely
  - trigger_when: CLOCK_EXPIRED:msc_application_leave
  - cure_cost: 5
  - cure_deadline_clock: msc_application_leave
  - cure_minimum_packet:
    - Verify service/decision date that triggers the MSC clock
    - If late: evaluate other vehicles (reconsideration, extraordinary relief)
  - authority_refs:
    - MCR: MCR 7.305(C) — MSC application timing and consequences for nonconforming filings.

- `MSC_return_without_docketing_nonconforming` [*/msc] (admin_return_without_docketing; sev=92) — MSC filing nonconforming / returned (time limit not satisfied unless corrected)
  - trigger_when: EVENT_TAG_PRESENT:msc_return_without_docketing
  - cure_cost: 4
  - cure_deadline_clock: msc_return_cure
  - cure_minimum_packet:
    - Corrected filing fully conforming to requirements
    - Motion explaining correction (if clerk requires)
    - Proof of timely cure attempt
  - authority_refs:
    - MCR: MCR 7.305(C)(4) — nonconforming pleading does not satisfy time limit if not corrected.

- `JTC_request_unverified` [MEEK4/jtc] (curable_defect; sev=78) — JTC request for investigation not verified on oath
  - trigger_when: PACKET_FIELD_FALSE:jtc_request_verified
  - cure_cost: 2
  - cure_deadline_clock: jtc_intake_window
  - cure_minimum_packet:
    - Verified request for investigation (oath/verification)
    - Structured allegations + chronology + evidence pinpoints
  - authority_refs:
    - MCR: MCR 9.220 (request for investigation) — intake step; request must be in writing/verified.

- `JTC_28_day_letter_response_due` [MEEK4/jtc] (record_incomplete; sev=80) — JTC 28-day letter response due (further investigation stage)
  - trigger_when: EVENT_TAG_PRESENT:jtc_28_day_letter
  - cure_cost: 3
  - cure_deadline_clock: jtc_28_day_letter
  - cure_minimum_packet:
    - Written response addressing allegations
    - Supporting exhibits + record references
    - Confidentiality-compliant packaging
  - authority_refs:
    - MCR: MCR 9.222 ("28-day letter") — further investigation + respondent opportunity to respond.

- `JTC_complaint_issued_next_steps` [MEEK4/jtc] (discretionary_sanction_risk; sev=85) — JTC formal complaint issued; hearing/milestone obligations begin
  - trigger_when: EVENT_TAG_PRESENT:jtc_formal_complaint
  - cure_cost: 4
  - cure_deadline_clock: jtc_answer_due
  - cure_minimum_packet:
    - Answer/response per JTC rules
    - Hearing preparation packet
    - Record organization + index
  - authority_refs:
    - MCR: MCR 9.224 et seq. — complaint/hearing/neutral stages.

- `PPO_motion_modify_terminate_deadline` [MEEK3/trial] (curable_defect; sev=75) — PPO modification/termination motion deadline triggered
  - trigger_when: CLOCK_EXPIRED:ppo_modify_terminate_window
  - cure_cost: 3
  - cure_deadline_clock: ppo_modify_terminate_window
  - cure_minimum_packet:
    - If 14-day window missed: good-cause showing (as required)
    - Motion + notice of hearing + service proofs
  - authority_refs:
    - MCR: MCR 3.707(A)(1)(b) — 14 days from service/actual notice for respondent ex parte PPO motion.

- `PPO_violation_hearing_sentence_appeal_right` [MEEK3/trial] (dismissal_risk; sev=70) — PPO contempt sentence entered; appeal route must be correct
  - trigger_when: EVENT_TAG_PRESENT:ppo_contempt_sentence
  - cure_cost: 3
  - cure_deadline_clock: coa_claim_of_appeal
  - cure_minimum_packet:
    - Identify whether appeal of right applies
    - Pin order + sentence + hearing record
    - File correct appellate vehicle
  - authority_refs:
    - MCR: MCR 3.709(C) — appeal of right from criminal contempt sentence after contested hearing.

- `CUSTODY_missing_hearing_record` [MEEK2/trial] (record_incomplete; sev=72) — No transcript/record for key hearing
  - trigger_when: MISSING_PACKET:trial_transcript
  - cure_cost: 3
  - cure_deadline_clock: appeal_or_objection_deadline
  - cure_minimum_packet:
    - Order transcript/recording
    - Settle statement if transcript unavailable
    - Pin hearing date/time + issues preserved
  - authority_refs:
    - MCR: MCR 7.210 (record on appeal) — record completeness for appellate review.

- `RISK_msc_nonconforming_no_toll` [*/msc] (jurisdictional_fatal; sev=95) — Nonconforming MSC filing does not satisfy time limit
  - trigger_when: CLERK_LETTER:nonconforming_return, MISSING_DOC:compliant_replacement
  - cure_cost: 3
  - cure_deadline_clock: MCR_7_305_nonconforming_cure_window
  - cure_minimum_packet:
    - Clerk letter
    - Corrected compliant application/brief/appendix
    - Service proof
    - Fee/IFP proof
  - authority_refs:
    - MCR: 7.305(G) — Nonconforming filing does not satisfy time limitation.

- `RISK_coa_claim_of_appeal_deadline` [*/coa] (jurisdictional_fatal; sev=98) — Claim of appeal deadline (MCR 7.204) missed/imminent
  - trigger_when: MISSING_OR_EXPIRED_CLOCK:MCR_7_204_21_day_clock
  - cure_cost: 5
  - cure_deadline_clock: MCR_7_204_21_day_clock
  - cure_minimum_packet:
    - Claim of appeal
    - Proof of entry date (ROA)
    - Fee/IFP
    - Service proof
  - authority_refs:
    - MCR: 7.204 — Time for filing claim of appeal; jurisdictional consequences implied by rule framework.

- `RISK_coa_leave_application_deadline` [*/coa] (jurisdictional_fatal; sev=96) — Application for leave deadline (MCR 7.205) missed/imminent
  - trigger_when: MISSING_OR_EXPIRED_CLOCK:MCR_7_205_21_day_clock
  - cure_cost: 5
  - cure_deadline_clock: MCR_7_205_21_day_clock
  - cure_minimum_packet:
    - Application for leave packet
    - Appendix
    - Fee/IFP
    - Service proof
    - Proof of entry date (ROA)
  - authority_refs:
    - MCR: 7.205(A) — Time requirements; defines entry date; jurisdictional statement in rule.

- `RISK_service_defect` [*/*] (curable_defect; sev=70) — Service/proof defect
  - trigger_when: MISSING_NODE:ServiceEvent, MISSING_DOC:proof_of_service
  - cure_cost: 3
  - cure_deadline_clock: service_due_now
  - cure_minimum_packet:
    - Correct service method selection
    - Correct address selection justification
    - Proof of service
    - Re-service if required
  - authority_refs:
    - MCR: 2.105-2.107 — Service rules; depends on party and document.

- `RISK_transcript_not_ordered` [*/coa] (record_incomplete; sev=78) — Transcript/record not ordered or certified
  - trigger_when: MISSING_DOC:transcript_order, MISSING_DOC:certificate_no_transcript
  - cure_cost: 4
  - cure_deadline_clock: transcript_order_clock
  - cure_minimum_packet:
    - Transcript order and proof of request
    - Reporter confirmation
    - Certificate/stipulation if none
    - Record index
  - authority_refs:
    - MCR: 7.210-7.212 — Record/transcript and briefing rules (chapter 7).

- `RISK_jtc_28_day_letter_deadline` [MEEK4/jtc] (admin_return_without_docketing; sev=80) — JTC 28-day letter response deadline
  - trigger_when: TRIGGER:ClerkLetter(kind=jtc_28_day_letter)
  - cure_cost: 3
  - cure_deadline_clock: MCR_9_222_28_day_clock
  - cure_minimum_packet:
    - Written response
    - Requested documents
    - Attachment index
  - authority_refs:
    - MCR: 9.222 — 28-day notice letter process.

- `RISK_trial_disqualification_timeliness` [*/trial] (curable_defect; sev=75) — Judge disqualification request timeliness risk
  - trigger_when: MOTION:disqualification, CLOCK_NEAR:DQ_14_day_discovery
  - cure_cost: 2
  - cure_deadline_clock: DQ_14_day_discovery
  - cure_minimum_packet:
    - Motion for disqualification
    - Affidavit (if applicable)
    - Proof of when grounds discovered
    - Service proof
  - authority_refs:
    - MCR: 2.003(D)(1)(a) — Motion within 14 days after discovering grounds (rule text).


---

## Clock Types

- `MCR_7_204_21_day_clock` [coa] — Claim of appeal due
  - start_event: Order entered (entry date per ROA)
  - duration_days: 21
  - notes: Civil claim of appeal generally due within 21 days after entry of order/judgment, unless otherwise provided.
  - authority_refs:
    - MCR: 7.204(A)(1) — Time for filing claim of appeal; 21 days after entry.

- `MCR_7_205_21_day_clock` [coa] — Application for leave due
  - start_event: Order entered (entry date per ROA)
  - duration_days: 21
  - notes: Application for leave generally due within 21 days after entry; tolling may apply for certain postjudgment motions per rule.
  - authority_refs:
    - MCR: 7.205(A)(1) — Time for filing application for leave; tolling details in rule.

- `MCR_7_205_granted_leave_docketing_statement_clock` [coa] — Docketing statement due after leave granted
  - start_event: Order granting leave is certified
  - duration_days: 28
  - authority_refs:
    - MCR: 7.205(C)(3) — Docketing statement due 28 days after certification of order granting leave.

- `MCR_7_205_granted_leave_transcript_clock` [coa] — Transcript order due after leave granted
  - start_event: Order granting leave is certified
  - duration_days: 14
  - authority_refs:
    - MCR: 7.205(C)(3) — Transcript order within 14 days after certification of order granting leave.

- `DQ_14_day_discovery` [trial] — Disqualification motion due
  - start_event: Grounds discovered
  - duration_days: 14
  - authority_refs:
    - MCR: 2.003(D)(1)(a) — Motion within 14 days after discovery of grounds.

- `MCR_9_222_28_day_clock` [jtc] — Respond to JTC 28-day letter
  - start_event: JTC notice letter sent
  - duration_days: 28
  - authority_refs:
    - MCR: 9.222(A) — Respondent judge has 28 days to respond after notice letter.

- `service_due_now` [all] — Service due / proof needed
  - start_event: Filing served/required
  - duration_rule: depends_on_filing_and_rule
  - notes: Service rules vary by court and document; compute via rule profile.

- `transcript_order_clock` [coa] — Order transcript / certify no transcript
  - start_event: Notice of appeal or leave granted
  - duration_rule: varies
  - notes: Record/transcript clocks depend on MCR 7.210/7.212 and orders/certifications.


---

## Forum Gate Profiles

- `trial_default` [trial] gate=moderate
  - clerk_notice_behavior: typically sets hearing/return instructions; local practice varies
  - common_fail_modes: missing required findings in orders, service/proof gaps, no transcript/record for appellate review
  - cure_style: motion + proposed order + proof packet
  - formatting_constraints:
    - Local practice; ensure notice/proposed order/service proof.
  - return_without_docketing_behaviors:
    - Clerk may reject for missing fee/signature/incorrect form; judge may deny without hearing on insufficient record.
  - fastest_cures:
    - File proof of service
    - Attach operative order
    - Submit proposed order

- `coa_default` [coa] gate=strict-but-curable
  - clerk_notice_behavior: deficiency letter with cure deadline; possible dismissal if not cured
  - common_fail_modes: untimely claim/application, missing docketing statement, transcript/record not ordered/settled, briefing defects or missed deadlines
  - cure_style: cure packet + motion to reinstate/extend as allowed
  - formatting_constraints:
    - Follow MCR 7.200 subchapter formatting; include appendix and certificates.
  - return_without_docketing_behaviors:
    - Clerk deficiency notice with cure window; dismissal/reinstatement path may exist depending on rule/order.
  - fastest_cures:
    - Supplement appendix
    - File missing fee/IFP
    - Correct caption/service proof

- `msc_default` [msc] gate=very-strict
  - clerk_notice_behavior: return-without-docketing / nonconforming filings can miss jurisdictional time limits
  - common_fail_modes: late ALA/appeal filing, nonconforming filing returned (time limit not satisfied if not corrected), missing required attachments/copies
  - cure_style: immediate cure + motion if allowed; prioritize zero-defect filing
  - formatting_constraints:
    - Strict presentation; nonconforming does not satisfy time limits.
  - return_without_docketing_behaviors:
    - Return without docketing for noncompliance; must cure quickly; time limits still run.
  - fastest_cures:
    - Cure nonconformance immediately
    - Attach required appendix items
    - Fix service/fee

- `jtc_default` [jtc] gate=process-milestone-accurate
  - clerk_notice_behavior: screening/investigation notices; 28-day letter; confidentiality constraints
  - common_fail_modes: unverified/unstructured request, missing chronology/evidence pinpoints, failure to respond to 28-day letter or notices, attempt to force public disclosure prematurely
  - cure_style: structured request + evidence packet + milestone responses
  - formatting_constraints:
    - Confidentiality-sensitive; follow JTC rule structure; include attachments index.
  - return_without_docketing_behaviors:
    - Screening may close without action; 28-day letter response window.
  - fastest_cures:
    - Respond to 28-day letter with requested items
    - Clarify allegations with evidence pins

- `coa_emergency_stay` [coa] gate=high
  - clerk_notice_behavior: expedited review; strict compliance expected
  - common_fail_modes: missing jurisdictional basis, missing affidavit of harm, incomplete appendix, service defects
  - cure_style: supplemental filing same day when possible
  - formatting_constraints:
    - Include emergency designation if applicable; follow motion requirements and appendix.
  - return_without_docketing_behaviors:
    - Clerk deficiency notice; possible denial on record insufficiency.
  - fastest_cures:
    - File missing affidavit and appendix excerpts
    - Correct service immediately

- `trial_ex_parte_short_notice` [trial] gate=high
  - clerk_notice_behavior: judge-specific; may require certification of efforts to give notice
  - common_fail_modes: no certification of notice, no immediate-harm facts, no proposed order
  - cure_style: convert to noticed motion; supplement affidavits
  - formatting_constraints:
    - Include notice statement/certification when required.
  - return_without_docketing_behaviors:
    - May be refused or set for hearing.
  - fastest_cures:
    - Add affidavit; add notice certification; attach proposed order


---

## Denial Grounds

- `DG_missing_jurisdictional_deadline` [coa] — Untimely filing (jurisdictional)
  - when: Claim/application filed after time limit.
  - cure: File proper vehicle timely if possible; seek relief only if rule permits; preserve record.

- `DG_nonconforming_packet` [msc] — Nonconforming packet returned
  - when: Packet noncompliant with filing requirements.
  - cure: Cure defects and refile within time; ensure compliance.

- `DG_record_missing_order` [all] — Operative order not provided/pinned
  - when: Request relies on an order but order not included or unclear.
  - cure: Pin/attach operative order + ROA entry + dates.

- `DG_record_missing_service` [all] — Service/proof missing
  - when: Required service not shown.
  - cure: Re-serve and file proof.

- `DG_no_factual_support` [all] — Insufficient factual support
  - when: No affidavit/evidence supporting requested relief.
  - cure: Add affidavit + exhibits; authenticate.

- `DG_no_legal_standard` [all] — No legal standard / authority cited
  - when: Motion/brief does not state applicable rule/standard.
  - cure: Add authority + standard + apply facts.

- `DG_relief_not_available` [all] — Relief not available via chosen vehicle
  - when: Vehicle cannot grant requested relief in this posture.
  - cure: Select correct vehicle/form; refile.

- `DG_mootness` [coa] — Mootness
  - when: Issue becomes moot by subsequent events.
  - cure: Address exceptions; seek expedited relief.

- `DG_preservation_failure` [coa] — Issue not preserved
  - when: Issue not preserved below; no plain-error basis shown.
  - cure: Develop preservation record or argue plain error.

- `DG_appendix_defective` [coa] — Appendix incomplete
  - when: Required documents missing from appendix.
  - cure: Supplement/cure per clerk notice.

- `DG_generic_01` [all] — Formatting noncompliance
  - when: Detected by presentation gate profile.
  - cure: Cure via gate checklist; refile/supplement.

- `DG_generic_02` [all] — Missing fee/IFP
  - when: Detected by presentation gate profile.
  - cure: Cure via gate checklist; refile/supplement.

- `DG_generic_03` [all] — Missing certificate of compliance
  - when: Detected by presentation gate profile.
  - cure: Cure via gate checklist; refile/supplement.

- `DG_generic_04` [all] — Improper caption/case number
  - when: Detected by presentation gate profile.
  - cure: Cure via gate checklist; refile/supplement.

- `DG_generic_05` [all] — Improper service address
  - when: Detected by presentation gate profile.
  - cure: Cure via gate checklist; refile/supplement.

- `DG_generic_06` [all] — Confidentiality violation
  - when: Detected by presentation gate profile.
  - cure: Cure via gate checklist; refile/supplement.

- `DG_generic_07` [all] — Exhibit labeling defective
  - when: Detected by presentation gate profile.
  - cure: Cure via gate checklist; refile/supplement.

- `DG_generic_08` [all] — Witness list untimely
  - when: Detected by presentation gate profile.
  - cure: Cure via gate checklist; refile/supplement.

- `DG_generic_09` [all] — Subpoena defect
  - when: Detected by presentation gate profile.
  - cure: Cure via gate checklist; refile/supplement.

- `DG_generic_10` [all] — Hearsay/authentication gaps
  - when: Detected by presentation gate profile.
  - cure: Cure via gate checklist; refile/supplement.

- `DG_generic_11` [all] — Order lacks required findings
  - when: Detected by presentation gate profile.
  - cure: Cure via gate checklist; refile/supplement.

- `DG_generic_12` [all] — Standard of review not stated
  - when: Detected by presentation gate profile.
  - cure: Cure via gate checklist; refile/supplement.

- `DG_generic_13` [all] — Incomplete ROA / missing entry date
  - when: Detected by presentation gate profile.
  - cure: Cure via gate checklist; refile/supplement.

- `DG_generic_14` [all] — Missing transcript certification
  - when: Detected by presentation gate profile.
  - cure: Cure via gate checklist; refile/supplement.

- `DG_generic_15` [all] — Late reconsideration motion
  - when: Detected by presentation gate profile.
  - cure: Cure via gate checklist; refile/supplement.


---

## Record Packet Templates

- `PACK_trial_motion_core` [trial] — Trial court motion packet (core)
  - Caption/notice of hearing (if set)
  - Motion
  - Affidavit(s)
  - Exhibit list
  - Proposed order
  - Proof of service

- `PACK_trial_show_cause_response` [trial] — Show-cause response packet
  - Show-cause notice/order
  - Response/brief
  - Exhibit list
  - Exhibits
  - Witness list/subpoenas
  - Proposed findings/order
  - Proof of service

- `PACK_coa_claim_of_appeal` [coa] — COA claim of appeal packet
  - Claim of appeal
  - Register of Actions excerpt showing entry date
  - Appealed order/judgment
  - Fee/IFP
  - Proof of service
  - Docketing statement (when due)

- `PACK_coa_leave_application` [coa] — COA application for leave packet
  - Application for leave
  - Questions presented
  - Statement of facts
  - Argument
  - Appendix (key orders, transcripts excerpts, ROA)
  - Fee/IFP
  - Proof of service

- `PACK_msc_leave_application` [msc] — MSC application for leave packet
  - COA opinion/order
  - MSC application
  - Questions presented
  - Reasons for review
  - Argument
  - Appendix
  - Fee/IFP
  - Proof of service

- `PACK_jtc_complaint` [jtc] — JTC complaint packet
  - Complaint narrative
  - MisconductAllegation list
  - CanonRule mapping
  - Timeline
  - Evidence attachment index
  - Key evidence excerpts/quotes
  - Contact info


---

## Glossary Terms

- `Authority.appendix` — Authority.appendix
  - definition: Field/atom 'appendix' within Authority.

- `Authority.authentication` — Authority.authentication
  - definition: Field/atom 'authentication' within Authority.

- `Authority.best_evidence` — Authority.best_evidence
  - definition: Field/atom 'best_evidence' within Authority.

- `Authority.case_id` — Authority.case_id
  - definition: Field/atom 'case_id' within Authority.

- `Authority.certification` — Authority.certification
  - definition: Field/atom 'certification' within Authority.

- `Authority.effective_date` — Authority.effective_date
  - definition: Field/atom 'effective_date' within Authority.

- `Authority.entered_date` — Authority.entered_date
  - definition: Field/atom 'entered_date' within Authority.

- `Authority.hearsay` — Authority.hearsay
  - definition: Field/atom 'hearsay' within Authority.

- `Authority.id` — Authority.id
  - definition: Field/atom 'id' within Authority.

- `Authority.index` — Authority.index
  - definition: Field/atom 'index' within Authority.

- `Authority.notice` — Authority.notice
  - definition: Field/atom 'notice' within Authority.

- `Authority.pinpoint` — Authority.pinpoint
  - definition: Field/atom 'pinpoint' within Authority.

- `Authority.preservation` — Authority.preservation
  - definition: Field/atom 'preservation' within Authority.

- `Authority.proof_of_service` — Authority.proof_of_service
  - definition: Field/atom 'proof_of_service' within Authority.

- `Authority.served_date` — Authority.served_date
  - definition: Field/atom 'served_date' within Authority.

- `Authority.standard_of_review` — Authority.standard_of_review
  - definition: Field/atom 'standard_of_review' within Authority.

- `Authority.verification` — Authority.verification
  - definition: Field/atom 'verification' within Authority.

- `AuthoritySnapshot` — AuthoritySnapshot
  - definition: Frozen reference set of rules/statutes/forms/cases for a time period.

- `CLOCK_DQ_14_day_discovery` — Clock::DQ_14_day_discovery
  - definition: Disqualification motion due
  - tags: clock, trial

- `CLOCK_MCR_7_204_21_day_clock` — Clock::MCR_7_204_21_day_clock
  - definition: Claim of appeal due
  - tags: clock, coa

- `CLOCK_MCR_7_205_21_day_clock` — Clock::MCR_7_205_21_day_clock
  - definition: Application for leave due
  - tags: clock, coa

- `CLOCK_MCR_7_205_granted_leave_docketing_statement_clock` — Clock::MCR_7_205_granted_leave_docketing_statement_clock
  - definition: Docketing statement due after leave granted
  - tags: clock, coa

- `CLOCK_MCR_7_205_granted_leave_transcript_clock` — Clock::MCR_7_205_granted_leave_transcript_clock
  - definition: Transcript order due after leave granted
  - tags: clock, coa

- `CLOCK_MCR_9_222_28_day_clock` — Clock::MCR_9_222_28_day_clock
  - definition: Respond to JTC 28-day letter
  - tags: clock, jtc

- `CLOCK_service_due_now` — Clock::service_due_now
  - definition: Service due / proof needed
  - tags: clock, all

- `CLOCK_transcript_order_clock` — Clock::transcript_order_clock
  - definition: Order transcript / certify no transcript
  - tags: clock, coa

- `COADismissalRiskEngine` — COADismissalRiskEngine
  - definition: COA risk engine keyed to docketing statement/transcripts/briefing/IOPs.

- `COA_ConfidentialityRule` — COA_ConfidentialityRule
  - definition: ConfidentialityRule concept for coa.
  - tags: R, i, s, k, E, n, g, i, n, e

- `COA_CureWindow` — COA_CureWindow
  - definition: CureWindow concept for coa.
  - tags: R, i, s, k, E, n, g, i, n, e

- `COA_DeficiencyLetter` — COA_DeficiencyLetter
  - definition: DeficiencyLetter concept for coa.
  - tags: R, i, s, k, E, n, g, i, n, e

- `COA_FilingPacket` — COA_FilingPacket
  - definition: FilingPacket concept for coa.
  - tags: R, i, s, k, E, n, g, i, n, e

- `COA_Forum` — COA_Forum
  - definition: Forum layer semantics and filing gates.
  - tags: R, i, s, k, E, n, g, i, n, e

- `COA_MilestoneTimeline` — COA_MilestoneTimeline
  - definition: MilestoneTimeline concept for coa.
  - tags: R, i, s, k, E, n, g, i, n, e

- `COA_ReinstatementMotion` — COA_ReinstatementMotion
  - definition: ReinstatementMotion concept for coa.
  - tags: R, i, s, k, E, n, g, i, n, e

- `COA_ReturnWithoutDocketing` — COA_ReturnWithoutDocketing
  - definition: ReturnWithoutDocketing concept for coa.
  - tags: R, i, s, k, E, n, g, i, n, e

- `ClerkNoticeEvent` — ClerkNoticeEvent
  - definition: Clerk deficiency/return letter, docketing notice, or administrative warning.

- `Clock` — Clock
  - definition: Computed deadline clock derived from triggers and tolling.

- `Clock.appendix` — Clock.appendix
  - definition: Field/atom 'appendix' within Clock.

- `Clock.authentication` — Clock.authentication
  - definition: Field/atom 'authentication' within Clock.

- `Clock.best_evidence` — Clock.best_evidence
  - definition: Field/atom 'best_evidence' within Clock.

- `Clock.case_id` — Clock.case_id
  - definition: Field/atom 'case_id' within Clock.

- `Clock.certification` — Clock.certification
  - definition: Field/atom 'certification' within Clock.

- `Clock.effective_date` — Clock.effective_date
  - definition: Field/atom 'effective_date' within Clock.

- `Clock.entered_date` — Clock.entered_date
  - definition: Field/atom 'entered_date' within Clock.

- `Clock.hearsay` — Clock.hearsay
  - definition: Field/atom 'hearsay' within Clock.

- `Clock.id` — Clock.id
  - definition: Field/atom 'id' within Clock.

- `Clock.index` — Clock.index
  - definition: Field/atom 'index' within Clock.

- `Clock.notice` — Clock.notice
  - definition: Field/atom 'notice' within Clock.

- `Clock.pinpoint` — Clock.pinpoint
  - definition: Field/atom 'pinpoint' within Clock.

- `Clock.preservation` — Clock.preservation
  - definition: Field/atom 'preservation' within Clock.

- `Clock.proof_of_service` — Clock.proof_of_service
  - definition: Field/atom 'proof_of_service' within Clock.

- `Clock.served_date` — Clock.served_date
  - definition: Field/atom 'served_date' within Clock.

- `Clock.standard_of_review` — Clock.standard_of_review
  - definition: Field/atom 'standard_of_review' within Clock.

- `Clock.verification` — Clock.verification
  - definition: Field/atom 'verification' within Clock.

- `CurePacket` — CurePacket
  - definition: Minimum packet to cure a defect; used for clerk letters and dismissal risks.

- `DENIAL_DG_appendix_defective` — DenialGround::DG_appendix_defective
  - definition: Appendix incomplete
  - tags: denial, coa

- `DENIAL_DG_generic_01` — DenialGround::DG_generic_01
  - definition: Formatting noncompliance
  - tags: denial, all

- `DENIAL_DG_generic_02` — DenialGround::DG_generic_02
  - definition: Missing fee/IFP
  - tags: denial, all

- `DENIAL_DG_generic_03` — DenialGround::DG_generic_03
  - definition: Missing certificate of compliance
  - tags: denial, all

- `DENIAL_DG_generic_04` — DenialGround::DG_generic_04
  - definition: Improper caption/case number
  - tags: denial, all

- `DENIAL_DG_generic_05` — DenialGround::DG_generic_05
  - definition: Improper service address
  - tags: denial, all

- `DENIAL_DG_generic_06` — DenialGround::DG_generic_06
  - definition: Confidentiality violation
  - tags: denial, all

- `DENIAL_DG_generic_07` — DenialGround::DG_generic_07
  - definition: Exhibit labeling defective
  - tags: denial, all

- `DENIAL_DG_generic_08` — DenialGround::DG_generic_08
  - definition: Witness list untimely
  - tags: denial, all

- `DENIAL_DG_generic_09` — DenialGround::DG_generic_09
  - definition: Subpoena defect
  - tags: denial, all

- `DENIAL_DG_generic_10` — DenialGround::DG_generic_10
  - definition: Hearsay/authentication gaps
  - tags: denial, all

- `DENIAL_DG_generic_11` — DenialGround::DG_generic_11
  - definition: Order lacks required findings
  - tags: denial, all

- `DENIAL_DG_generic_12` — DenialGround::DG_generic_12
  - definition: Standard of review not stated
  - tags: denial, all

- `DENIAL_DG_generic_13` — DenialGround::DG_generic_13
  - definition: Incomplete ROA / missing entry date
  - tags: denial, all

- `DENIAL_DG_generic_14` — DenialGround::DG_generic_14
  - definition: Missing transcript certification
  - tags: denial, all

- `DENIAL_DG_generic_15` — DenialGround::DG_generic_15
  - definition: Late reconsideration motion
  - tags: denial, all

- `DENIAL_DG_missing_jurisdictional_deadline` — DenialGround::DG_missing_jurisdictional_deadline
  - definition: Untimely filing (jurisdictional)
  - tags: denial, coa

- `DENIAL_DG_mootness` — DenialGround::DG_mootness
  - definition: Mootness
  - tags: denial, coa

- `DENIAL_DG_no_factual_support` — DenialGround::DG_no_factual_support
  - definition: Insufficient factual support
  - tags: denial, all

- `DENIAL_DG_no_legal_standard` — DenialGround::DG_no_legal_standard
  - definition: No legal standard / authority cited
  - tags: denial, all

- `DENIAL_DG_nonconforming_packet` — DenialGround::DG_nonconforming_packet
  - definition: Nonconforming packet returned
  - tags: denial, msc

- `DENIAL_DG_preservation_failure` — DenialGround::DG_preservation_failure
  - definition: Issue not preserved
  - tags: denial, coa

- `DENIAL_DG_record_missing_order` — DenialGround::DG_record_missing_order
  - definition: Operative order not provided/pinned
  - tags: denial, all

- `DENIAL_DG_record_missing_service` — DenialGround::DG_record_missing_service
  - definition: Service/proof missing
  - tags: denial, all

- `DENIAL_DG_relief_not_available` — DenialGround::DG_relief_not_available
  - definition: Relief not available via chosen vehicle
  - tags: denial, all

- `DenialSimulation` — DenialSimulation
  - definition: Library of anticipated denial grounds keyed to vehicle + record gaps.

- `EDGE_ALLEGATION_SUPPORTED_BY_EVIDENCE` — Edge::ALLEGATION_SUPPORTED_BY_EVIDENCE
  - definition: Allegation supported by evidence. (MisconductAllegation→EvidenceAtom).
  - tags: schema, edge

- `EDGE_ALLEGATION_VIOLATES_CANON` — Edge::ALLEGATION_VIOLATES_CANON
  - definition: Allegation mapped to canon/rule. (MisconductAllegation→CanonRule).
  - tags: schema, edge

- `EDGE_APPEAL_HAS_APP_LEAVE` — Edge::APPEAL_HAS_APP_LEAVE
  - definition: Appeal includes application for leave. (Appeal→ApplicationForLeave).
  - tags: schema, edge

- `EDGE_APPEAL_HAS_BRIEFING_SCHEDULE` — Edge::APPEAL_HAS_BRIEFING_SCHEDULE
  - definition: Appeal briefing schedule. (Appeal→BriefingSchedule).
  - tags: schema, edge

- `EDGE_APPEAL_HAS_CLAIM_OF_APPEAL` — Edge::APPEAL_HAS_CLAIM_OF_APPEAL
  - definition: Appeal includes claim of appeal. (Appeal→ClaimOfAppeal).
  - tags: schema, edge

- `EDGE_APPEAL_HAS_DOCKETING_STATEMENT` — Edge::APPEAL_HAS_DOCKETING_STATEMENT
  - definition: Appeal docketing statement. (Appeal→DocketingStatement).
  - tags: schema, edge

- `EDGE_APPEAL_RECEIVES_CLERK_LETTER` — Edge::APPEAL_RECEIVES_CLERK_LETTER
  - definition: Appeal clerk letter/notice. (Appeal→ClerkLetter).
  - tags: schema, edge

- `EDGE_ATTORNEY_HAS_ADDRESS` — Edge::ATTORNEY_HAS_ADDRESS
  - definition: Attorney address. (Attorney→Address).
  - tags: schema, edge

- `EDGE_ATTORNEY_HAS_CONTACT` — Edge::ATTORNEY_HAS_CONTACT
  - definition: Attorney contact point. (Attorney→ContactPoint).
  - tags: schema, edge

- `EDGE_BOND_IS_ORDERED_BY` — Edge::BOND_IS_ORDERED_BY
  - definition: Bond conditions ordered by an order. (Bond→Order).
  - tags: schema, edge

- `EDGE_CASE_HAS_APPEAL` — Edge::CASE_HAS_APPEAL
  - definition: Case has appeal. (Case→Appeal).
  - tags: schema, edge

- `EDGE_CASE_HAS_BOND` — Edge::CASE_HAS_BOND
  - definition: Case bond record. (Case→Bond).
  - tags: schema, edge

- `EDGE_CASE_HAS_CHILD` — Edge::CASE_HAS_CHILD
  - definition: Case child subject. (Case→Child).
  - tags: schema, edge

- `EDGE_CASE_HAS_CLOCK` — Edge::CASE_HAS_CLOCK
  - definition: Case clock. (Case→Clock).
  - tags: schema, edge

- `EDGE_CASE_HAS_CONTEMPT` — Edge::CASE_HAS_CONTEMPT
  - definition: Case has contempt proceeding. (Case→ContemptProceeding).
  - tags: schema, edge

- `EDGE_CASE_HAS_DEADLINE` — Edge::CASE_HAS_DEADLINE
  - definition: Case derived deadline. (Case→Deadline).
  - tags: schema, edge

- `EDGE_CASE_HAS_EVENT` — Edge::CASE_HAS_EVENT
  - definition: Case event. (Case→Event).
  - tags: schema, edge

- `EDGE_CASE_HAS_EVIDENCE` — Edge::CASE_HAS_EVIDENCE
  - definition: Evidence belongs to case. (Case→EvidenceItem).
  - tags: schema, edge

- `EDGE_CASE_HAS_FILING` — Edge::CASE_HAS_FILING
  - definition: Case filing. (Case→Filing).
  - tags: schema, edge

- `EDGE_CASE_HAS_FOC_ACTION` — Edge::CASE_HAS_FOC_ACTION
  - definition: FOC action within case. (Case→FOCAction).
  - tags: schema, edge

- `EDGE_CASE_HAS_ISSUE` — Edge::CASE_HAS_ISSUE
  - definition: Case issue list. (Case→Issue).
  - tags: schema, edge

- `EDGE_CASE_HAS_JTC_COMPLAINT` — Edge::CASE_HAS_JTC_COMPLAINT
  - definition: Case track includes JTC complaint. (Case→JTCComplaint).
  - tags: schema, edge

- `EDGE_CASE_HAS_MISCONDUCT_ALLEGATION` — Edge::CASE_HAS_MISCONDUCT_ALLEGATION
  - definition: Case alleges misconduct. (Case→MisconductAllegation).
  - tags: schema, edge

- `EDGE_CASE_HAS_ORDER` — Edge::CASE_HAS_ORDER
  - definition: Order in case. (Case→Order).
  - tags: schema, edge

- `EDGE_CASE_HAS_PARTY` — Edge::CASE_HAS_PARTY
  - definition: Case includes a party. (Case→Party).
  - tags: schema, edge

- `EDGE_CASE_HAS_PPO` — Edge::CASE_HAS_PPO
  - definition: Case has PPO record. (Case→PPO).
  - tags: schema, edge

- `EDGE_CASE_HAS_ROA` — Edge::CASE_HAS_ROA
  - definition: Case has ROA. (Case→RegisterOfActions).
  - tags: schema, edge

- `EDGE_CASE_HAS_SUPPORT_ACCOUNT` — Edge::CASE_HAS_SUPPORT_ACCOUNT
  - definition: Case child support account snapshot. (Case→SupportAccount).
  - tags: schema, edge

- `EDGE_CASE_HAS_VEHICLE_CANDIDATE` — Edge::CASE_HAS_VEHICLE_CANDIDATE
  - definition: Case candidate vehicle. (Case→VehicleCandidate).
  - tags: schema, edge

- `EDGE_CASE_IN_COURT` — Edge::CASE_IN_COURT
  - definition: Case is in a court. (Case→Court).
  - tags: schema, edge

- `EDGE_CASE_IN_FORUM` — Edge::CASE_IN_FORUM
  - definition: Case belongs to a forum layer. (Case→Forum).
  - tags: schema, edge

- `EDGE_CONTEMPT_HAS_SANCTION` — Edge::CONTEMPT_HAS_SANCTION
  - definition: Contempt sanction. (ContemptProceeding→Sanction).
  - tags: schema, edge

- `EDGE_CONTEMPT_HAS_WARRANT` — Edge::CONTEMPT_HAS_WARRANT
  - definition: Contempt related warrant/mitimus. (ContemptProceeding→Warrant).
  - tags: schema, edge

- `EDGE_CONTEMPT_RESULTS_IN_JAIL` — Edge::CONTEMPT_RESULTS_IN_JAIL
  - definition: Contempt results in jail commitment. (ContemptProceeding→JailCommitment).
  - tags: schema, edge

- `EDGE_DEADLINE_TRACKED_BY_CLOCK` — Edge::DEADLINE_TRACKED_BY_CLOCK
  - definition: Deadline backed by a clock. (Deadline→Clock).
  - tags: schema, edge

- `EDGE_ENTRY_HAS_ORDER` — Edge::ENTRY_HAS_ORDER
  - definition: Entry corresponds to an order. (ROAEntry→Order).
  - tags: schema, edge

- `EDGE_EVENT_HAS_HEARING` — Edge::EVENT_HAS_HEARING
  - definition: Event includes hearing. (Event→HearingEvent).
  - tags: schema, edge

- `EDGE_EVENT_HAS_SERVICE` — Edge::EVENT_HAS_SERVICE
  - definition: Event includes service step. (Event→ServiceEvent).
  - tags: schema, edge

- `EDGE_EVIDENCE_AS_EXHIBIT` — Edge::EVIDENCE_AS_EXHIBIT
  - definition: Evidence packaged as an exhibit. (EvidenceItem→Exhibit).
  - tags: schema, edge

- `EDGE_EVIDENCE_ATOM_DERIVED_FROM_ITEM` — Edge::EVIDENCE_ATOM_DERIVED_FROM_ITEM
  - definition: Evidence atom derived from evidence item. (EvidenceAtom→EvidenceItem).
  - tags: schema, edge

- `EDGE_EVIDENCE_ATOM_SUPPORTS_ALLEGATION` — Edge::EVIDENCE_ATOM_SUPPORTS_ALLEGATION
  - definition: Evidence atom supports allegation. (EvidenceAtom→MisconductAllegation).
  - tags: schema, edge

- `EDGE_EVIDENCE_ATOM_SUPPORTS_EVENT` — Edge::EVIDENCE_ATOM_SUPPORTS_EVENT
  - definition: Evidence atom supports an event. (EvidenceAtom→Event).
  - tags: schema, edge

- `EDGE_EVIDENCE_ATOM_SUPPORTS_ISSUE` — Edge::EVIDENCE_ATOM_SUPPORTS_ISSUE
  - definition: Evidence atom supports an issue. (EvidenceAtom→Issue).
  - tags: schema, edge

- `EDGE_EVIDENCE_ITEM_AUTH_RULE` — Edge::EVIDENCE_ITEM_AUTH_RULE
  - definition: Authentication/admissibility mapping. (EvidenceItem→AuthenticationRule).
  - tags: schema, edge

- `EDGE_EVIDENCE_ITEM_BEST_EVIDENCE` — Edge::EVIDENCE_ITEM_BEST_EVIDENCE
  - definition: Best-evidence mapping. (EvidenceItem→BestEvidenceRule).
  - tags: schema, edge

- `EDGE_EVIDENCE_ITEM_HAS_COC` — Edge::EVIDENCE_ITEM_HAS_COC
  - definition: Evidence item chain-of-custody. (EvidenceItem→ChainOfCustody).
  - tags: schema, edge

- `EDGE_EVIDENCE_ITEM_HAS_QUOTE_PIN` — Edge::EVIDENCE_ITEM_HAS_QUOTE_PIN
  - definition: Evidence item has quote pinpoints. (EvidenceItem→QuotePin).
  - tags: schema, edge

- `EDGE_EVIDENCE_ITEM_HEARSAY_RULE` — Edge::EVIDENCE_ITEM_HEARSAY_RULE
  - definition: Hearsay mapping. (EvidenceItem→HearsayRule).
  - tags: schema, edge

- `EDGE_FILING_COMPILED_IN_PACKET` — Edge::FILING_COMPILED_IN_PACKET
  - definition: Filing included in a packet. (Filing→Packet).
  - tags: schema, edge

- `EDGE_FILING_IS_BRIEF` — Edge::FILING_IS_BRIEF
  - definition: Filing brief subtype. (Filing→Brief).
  - tags: schema, edge

- `EDGE_FILING_IS_MOTION` — Edge::FILING_IS_MOTION
  - definition: Filing motion subtype. (Filing→Motion).
  - tags: schema, edge

- `EDGE_FILING_IS_PLEADING` — Edge::FILING_IS_PLEADING
  - definition: Filing pleading subtype. (Filing→Pleading).
  - tags: schema, edge

- `EDGE_FORUM_HAS_GATE_PROFILE` — Edge::FORUM_HAS_GATE_PROFILE
  - definition: Forum gate profile. (Forum→PresentationGateProfile).
  - tags: schema, edge

- `EDGE_HEARING_HAS_RECORDING` — Edge::HEARING_HAS_RECORDING
  - definition: Hearing recording link. (HearingEvent→Recording).
  - tags: schema, edge

- `EDGE_HEARING_HAS_TRANSCRIPT` — Edge::HEARING_HAS_TRANSCRIPT
  - definition: Hearing transcript link. (HearingEvent→Transcript).
  - tags: schema, edge

- `EDGE_ISSUE_GOVERNED_BY_AUTHORITY` — Edge::ISSUE_GOVERNED_BY_AUTHORITY
  - definition: Issue governed by authority. (Issue→Authority).
  - tags: schema, edge

- `EDGE_ISSUE_HAS_STANDARD_OF_REVIEW` — Edge::ISSUE_HAS_STANDARD_OF_REVIEW
  - definition: Issue standard of review. (Issue→StandardOfReview).
  - tags: schema, edge

- `EDGE_ISSUE_IN_CASE` — Edge::ISSUE_IN_CASE
  - definition: Issue arises in case. (Issue→Case).
  - tags: schema, edge

- `EDGE_ISSUE_SUPPORTED_BY_EVIDENCE` — Edge::ISSUE_SUPPORTED_BY_EVIDENCE
  - definition: Issue supported by evidence. (Issue→EvidenceItem).
  - tags: schema, edge

- `EDGE_JTC_COMPLAINT_HAS_MILESTONE` — Edge::JTC_COMPLAINT_HAS_MILESTONE
  - definition: JTC process milestone. (JTCComplaint→JTCMilestone).
  - tags: schema, edge

- `EDGE_LEDGER_ENTRY_IS_EVENT` — Edge::LEDGER_ENTRY_IS_EVENT
  - definition: Ledger entry as an event. (SupportLedgerEntry→Event).
  - tags: schema, edge

- `EDGE_MATTER_HAS_CASE` — Edge::MATTER_HAS_CASE
  - definition: Matter contains a case. (Matter→Case).
  - tags: schema, edge

- `EDGE_MATTER_IN_TRACK` — Edge::MATTER_IN_TRACK
  - definition: Matter lane assignment. (Matter→Track).
  - tags: schema, edge

- `EDGE_MOTION_SEEKS_REMEDY` — Edge::MOTION_SEEKS_REMEDY
  - definition: Motion seeks remedy. (Motion→Remedy).
  - tags: schema, edge

- `EDGE_MOTION_SET_FOR_HEARING` — Edge::MOTION_SET_FOR_HEARING
  - definition: Motion scheduled for hearing. (Motion→HearingEvent).
  - tags: schema, edge

- `EDGE_ORDER_CONTAINS_CUSTODY_PROVISION` — Edge::ORDER_CONTAINS_CUSTODY_PROVISION
  - definition: Order contains custody provision. (Order→CustodyProvision).
  - tags: schema, edge

- `EDGE_ORDER_CONTAINS_PT_PROVISION` — Edge::ORDER_CONTAINS_PT_PROVISION
  - definition: Order contains parenting time provision. (Order→ParentingTimeProvision).
  - tags: schema, edge

- `EDGE_ORDER_STAYED_BY` — Edge::ORDER_STAYED_BY
  - definition: Order stayed by another order. (Order→Order).
  - tags: schema, edge

- `EDGE_ORDER_SUPERSEDES` — Edge::ORDER_SUPERSEDES
  - definition: Order supersedes a prior order. (Order→Order).
  - tags: schema, edge

- `EDGE_PACKET_EMITTED_BY_COMMIT` — Edge::PACKET_EMITTED_BY_COMMIT
  - definition: Packet produced by a commit suite. (Packet→CommitSuite).
  - tags: schema, edge

- `EDGE_PARTY_HAS_ADDRESS` — Edge::PARTY_HAS_ADDRESS
  - definition: Party has address (bi-temporal). (Party→Address).
  - tags: schema, edge

- `EDGE_PARTY_HAS_CONTACT` — Edge::PARTY_HAS_CONTACT
  - definition: Party contact point. (Party→ContactPoint).
  - tags: schema, edge

- `EDGE_PARTY_IS_ORG` — Edge::PARTY_IS_ORG
  - definition: Party links to organization identity. (Party→Organization).
  - tags: schema, edge

- `EDGE_PARTY_IS_PERSON` — Edge::PARTY_IS_PERSON
  - definition: Party links to person identity. (Party→Person).
  - tags: schema, edge

- `EDGE_PARTY_REPRESENTED_BY` — Edge::PARTY_REPRESENTED_BY
  - definition: Party representation. (Party→Attorney).
  - tags: schema, edge

- `EDGE_PIN_POINTS_TO_ORDER` — Edge::PIN_POINTS_TO_ORDER
  - definition: Pin points to an order. (OperatingOrderPin→Order).
  - tags: schema, edge

- `EDGE_PPO_HAS_ORDER` — Edge::PPO_HAS_ORDER
  - definition: PPO order. (PPO→Order).
  - tags: schema, edge

- `EDGE_QUOTE_PIN_IN_ORDER` — Edge::QUOTE_PIN_IN_ORDER
  - definition: Quote pin in order. (QuotePin→Order).
  - tags: schema, edge

- `EDGE_QUOTE_PIN_IN_RECORDING` — Edge::QUOTE_PIN_IN_RECORDING
  - definition: Quote pin in recording/audio/video. (QuotePin→EvidenceItem).
  - tags: schema, edge

- `EDGE_QUOTE_PIN_IN_TRANSCRIPT` — Edge::QUOTE_PIN_IN_TRANSCRIPT
  - definition: Quote pin in transcript. (QuotePin→Transcript).
  - tags: schema, edge

- `EDGE_RISK_DEPENDS_ON_CLOCK` — Edge::RISK_DEPENDS_ON_CLOCK
  - definition: Risk depends on clock. (RiskEvent→Clock).
  - tags: schema, edge

- `EDGE_RISK_HAS_CURE_PACKET` — Edge::RISK_HAS_CURE_PACKET
  - definition: Risk cure packet. (RiskEvent→CurePacket).
  - tags: schema, edge

- `EDGE_RISK_IN_CASE` — Edge::RISK_IN_CASE
  - definition: Risk event in case. (RiskEvent→Case).
  - tags: schema, edge

- `EDGE_ROA_HAS_ENTRY` — Edge::ROA_HAS_ENTRY
  - definition: ROA contains entries. (RegisterOfActions→ROAEntry).
  - tags: schema, edge

- `EDGE_SUPPORT_ACCOUNT_HAS_LEDGER` — Edge::SUPPORT_ACCOUNT_HAS_LEDGER
  - definition: Support account ledger entries. (SupportAccount→SupportLedgerEntry).
  - tags: schema, edge

- `EDGE_VEHICLE_DENIAL_GROUND` — Edge::VEHICLE_DENIAL_GROUND
  - definition: Vehicle candidate denial grounds. (VehicleCandidate→DenialGround).
  - tags: schema, edge

- `EDGE_VEHICLE_GOVERNED_BY_AUTHORITY` — Edge::VEHICLE_GOVERNED_BY_AUTHORITY
  - definition: Vehicle governed by authority. (VehicleCandidate→Authority).
  - tags: schema, edge

- `EDGE_VEHICLE_REQUIRES_OPERATING_PIN` — Edge::VEHICLE_REQUIRES_OPERATING_PIN
  - definition: Candidate requires pinned operative order. (VehicleCandidate→OperatingOrderPin).
  - tags: schema, edge

- `ENUMVAL_court_level_circuit` — EnumValue::court_level.circuit
  - definition: Value 'circuit' for enum court_level.
  - tags: schema, enum_value

- `ENUMVAL_court_level_coa` — EnumValue::court_level.coa
  - definition: Value 'coa' for enum court_level.
  - tags: schema, enum_value

- `ENUMVAL_court_level_district` — EnumValue::court_level.district
  - definition: Value 'district' for enum court_level.
  - tags: schema, enum_value

- `ENUMVAL_court_level_jtc` — EnumValue::court_level.jtc
  - definition: Value 'jtc' for enum court_level.
  - tags: schema, enum_value

- `ENUMVAL_court_level_msc` — EnumValue::court_level.msc
  - definition: Value 'msc' for enum court_level.
  - tags: schema, enum_value

- `ENUMVAL_court_level_other` — EnumValue::court_level.other
  - definition: Value 'other' for enum court_level.
  - tags: schema, enum_value

- `ENUMVAL_deadline_source_clerk_letter` — EnumValue::deadline_source.clerk_letter
  - definition: Value 'clerk_letter' for enum deadline_source.
  - tags: schema, enum_value

- `ENUMVAL_deadline_source_order` — EnumValue::deadline_source.order
  - definition: Value 'order' for enum deadline_source.
  - tags: schema, enum_value

- `ENUMVAL_deadline_source_rule` — EnumValue::deadline_source.rule
  - definition: Value 'rule' for enum deadline_source.
  - tags: schema, enum_value

- `ENUMVAL_deadline_source_statute` — EnumValue::deadline_source.statute
  - definition: Value 'statute' for enum deadline_source.
  - tags: schema, enum_value

- `ENUMVAL_deadline_source_system` — EnumValue::deadline_source.system
  - definition: Value 'system' for enum deadline_source.
  - tags: schema, enum_value

- `ENUMVAL_event_kind_AppealEvent` — EnumValue::event_kind.AppealEvent
  - definition: Value 'AppealEvent' for enum event_kind.
  - tags: schema, enum_value

- `ENUMVAL_event_kind_ClerkNoticeEvent` — EnumValue::event_kind.ClerkNoticeEvent
  - definition: Value 'ClerkNoticeEvent' for enum event_kind.
  - tags: schema, enum_value

- `ENUMVAL_event_kind_ContemptEvent` — EnumValue::event_kind.ContemptEvent
  - definition: Value 'ContemptEvent' for enum event_kind.
  - tags: schema, enum_value

- `ENUMVAL_event_kind_ExtensionEvent` — EnumValue::event_kind.ExtensionEvent
  - definition: Value 'ExtensionEvent' for enum event_kind.
  - tags: schema, enum_value

- `ENUMVAL_event_kind_FOCEvent` — EnumValue::event_kind.FOCEvent
  - definition: Value 'FOCEvent' for enum event_kind.
  - tags: schema, enum_value

- `ENUMVAL_event_kind_FilingEvent` — EnumValue::event_kind.FilingEvent
  - definition: Value 'FilingEvent' for enum event_kind.
  - tags: schema, enum_value

- `ENUMVAL_event_kind_HearingEvent` — EnumValue::event_kind.HearingEvent
  - definition: Value 'HearingEvent' for enum event_kind.
  - tags: schema, enum_value

- `ENUMVAL_event_kind_JTCEvent` — EnumValue::event_kind.JTCEvent
  - definition: Value 'JTCEvent' for enum event_kind.
  - tags: schema, enum_value

- `ENUMVAL_event_kind_OrderEvent` — EnumValue::event_kind.OrderEvent
  - definition: Value 'OrderEvent' for enum event_kind.
  - tags: schema, enum_value

- `ENUMVAL_event_kind_OtherEvent` — EnumValue::event_kind.OtherEvent
  - definition: Value 'OtherEvent' for enum event_kind.
  - tags: schema, enum_value

- `ENUMVAL_event_kind_PPOEvent` — EnumValue::event_kind.PPOEvent
  - definition: Value 'PPOEvent' for enum event_kind.
  - tags: schema, enum_value

- `ENUMVAL_event_kind_PaymentEvent` — EnumValue::event_kind.PaymentEvent
  - definition: Value 'PaymentEvent' for enum event_kind.
  - tags: schema, enum_value

- `ENUMVAL_event_kind_ServiceEvent` — EnumValue::event_kind.ServiceEvent
  - definition: Value 'ServiceEvent' for enum event_kind.
  - tags: schema, enum_value

- `ENUMVAL_event_kind_SupportEvent` — EnumValue::event_kind.SupportEvent
  - definition: Value 'SupportEvent' for enum event_kind.
  - tags: schema, enum_value

- `ENUMVAL_event_kind_TranscriptEvent` — EnumValue::event_kind.TranscriptEvent
  - definition: Value 'TranscriptEvent' for enum event_kind.
  - tags: schema, enum_value

- `ENUMVAL_evidence_kind_audio` — EnumValue::evidence_kind.audio
  - definition: Value 'audio' for enum evidence_kind.
  - tags: schema, enum_value

- `ENUMVAL_evidence_kind_court_record` — EnumValue::evidence_kind.court_record
  - definition: Value 'court_record' for enum evidence_kind.
  - tags: schema, enum_value

- `ENUMVAL_evidence_kind_document` — EnumValue::evidence_kind.document
  - definition: Value 'document' for enum evidence_kind.
  - tags: schema, enum_value

- `ENUMVAL_evidence_kind_email` — EnumValue::evidence_kind.email
  - definition: Value 'email' for enum evidence_kind.
  - tags: schema, enum_value

- `ENUMVAL_evidence_kind_other` — EnumValue::evidence_kind.other
  - definition: Value 'other' for enum evidence_kind.
  - tags: schema, enum_value

- `ENUMVAL_evidence_kind_photo` — EnumValue::evidence_kind.photo
  - definition: Value 'photo' for enum evidence_kind.
  - tags: schema, enum_value

- `ENUMVAL_evidence_kind_recording` — EnumValue::evidence_kind.recording
  - definition: Value 'recording' for enum evidence_kind.
  - tags: schema, enum_value

- `ENUMVAL_evidence_kind_social_media` — EnumValue::evidence_kind.social_media
  - definition: Value 'social_media' for enum evidence_kind.
  - tags: schema, enum_value

- `ENUMVAL_evidence_kind_text_message` — EnumValue::evidence_kind.text_message
  - definition: Value 'text_message' for enum evidence_kind.
  - tags: schema, enum_value

- `ENUMVAL_evidence_kind_transcript` — EnumValue::evidence_kind.transcript
  - definition: Value 'transcript' for enum evidence_kind.
  - tags: schema, enum_value

- `ENUMVAL_evidence_kind_video` — EnumValue::evidence_kind.video
  - definition: Value 'video' for enum evidence_kind.
  - tags: schema, enum_value

- `ENUMVAL_exhibit_color_defendant_blue` — EnumValue::exhibit_color.defendant_blue
  - definition: Value 'defendant_blue' for enum exhibit_color.
  - tags: schema, enum_value

- `ENUMVAL_exhibit_color_neutral_white` — EnumValue::exhibit_color.neutral_white
  - definition: Value 'neutral_white' for enum exhibit_color.
  - tags: schema, enum_value

- `ENUMVAL_exhibit_color_plaintiff_yellow` — EnumValue::exhibit_color.plaintiff_yellow
  - definition: Value 'plaintiff_yellow' for enum exhibit_color.
  - tags: schema, enum_value

- `ENUMVAL_filing_kind_affidavit` — EnumValue::filing_kind.affidavit
  - definition: Value 'affidavit' for enum filing_kind.
  - tags: schema, enum_value

- `ENUMVAL_filing_kind_appendix` — EnumValue::filing_kind.appendix
  - definition: Value 'appendix' for enum filing_kind.
  - tags: schema, enum_value

- `ENUMVAL_filing_kind_application_leave` — EnumValue::filing_kind.application_leave
  - definition: Value 'application_leave' for enum filing_kind.
  - tags: schema, enum_value

- `ENUMVAL_filing_kind_brief` — EnumValue::filing_kind.brief
  - definition: Value 'brief' for enum filing_kind.
  - tags: schema, enum_value

- `ENUMVAL_filing_kind_claim_of_appeal` — EnumValue::filing_kind.claim_of_appeal
  - definition: Value 'claim_of_appeal' for enum filing_kind.
  - tags: schema, enum_value

- `ENUMVAL_filing_kind_exhibit_list` — EnumValue::filing_kind.exhibit_list
  - definition: Value 'exhibit_list' for enum filing_kind.
  - tags: schema, enum_value

- `ENUMVAL_filing_kind_motion` — EnumValue::filing_kind.motion
  - definition: Value 'motion' for enum filing_kind.
  - tags: schema, enum_value

- `ENUMVAL_filing_kind_notice` — EnumValue::filing_kind.notice
  - definition: Value 'notice' for enum filing_kind.
  - tags: schema, enum_value

- `ENUMVAL_filing_kind_order` — EnumValue::filing_kind.order
  - definition: Value 'order' for enum filing_kind.
  - tags: schema, enum_value

- `ENUMVAL_filing_kind_other` — EnumValue::filing_kind.other
  - definition: Value 'other' for enum filing_kind.
  - tags: schema, enum_value

- `ENUMVAL_filing_kind_pleading` — EnumValue::filing_kind.pleading
  - definition: Value 'pleading' for enum filing_kind.
  - tags: schema, enum_value

- `ENUMVAL_filing_kind_transcript_request` — EnumValue::filing_kind.transcript_request
  - definition: Value 'transcript_request' for enum filing_kind.
  - tags: schema, enum_value

- `ENUMVAL_forum_coa` — EnumValue::forum.coa
  - definition: Value 'coa' for enum forum.
  - tags: schema, enum_value

- `ENUMVAL_forum_jtc` — EnumValue::forum.jtc
  - definition: Value 'jtc' for enum forum.
  - tags: schema, enum_value

- `ENUMVAL_forum_msc` — EnumValue::forum.msc
  - definition: Value 'msc' for enum forum.
  - tags: schema, enum_value

- `ENUMVAL_forum_trial` — EnumValue::forum.trial
  - definition: Value 'trial' for enum forum.
  - tags: schema, enum_value

- `ENUMVAL_hearing_kind_evidentiary` — EnumValue::hearing_kind.evidentiary
  - definition: Value 'evidentiary' for enum hearing_kind.
  - tags: schema, enum_value

- `ENUMVAL_hearing_kind_motion` — EnumValue::hearing_kind.motion
  - definition: Value 'motion' for enum hearing_kind.
  - tags: schema, enum_value

- `ENUMVAL_hearing_kind_other` — EnumValue::hearing_kind.other
  - definition: Value 'other' for enum hearing_kind.
  - tags: schema, enum_value

- `ENUMVAL_hearing_kind_referee` — EnumValue::hearing_kind.referee
  - definition: Value 'referee' for enum hearing_kind.
  - tags: schema, enum_value

- `ENUMVAL_hearing_kind_settlement` — EnumValue::hearing_kind.settlement
  - definition: Value 'settlement' for enum hearing_kind.
  - tags: schema, enum_value

- `ENUMVAL_hearing_kind_showcause` — EnumValue::hearing_kind.showcause
  - definition: Value 'showcause' for enum hearing_kind.
  - tags: schema, enum_value

- `ENUMVAL_hearing_kind_trial` — EnumValue::hearing_kind.trial
  - definition: Value 'trial' for enum hearing_kind.
  - tags: schema, enum_value

- `ENUMVAL_issue_stage_appeal_coa` — EnumValue::issue_stage.appeal_coa
  - definition: Value 'appeal_coa' for enum issue_stage.
  - tags: schema, enum_value

- `ENUMVAL_issue_stage_appeal_msc` — EnumValue::issue_stage.appeal_msc
  - definition: Value 'appeal_msc' for enum issue_stage.
  - tags: schema, enum_value

- `ENUMVAL_issue_stage_jtc` — EnumValue::issue_stage.jtc
  - definition: Value 'jtc' for enum issue_stage.
  - tags: schema, enum_value

- `ENUMVAL_issue_stage_postjudgment` — EnumValue::issue_stage.postjudgment
  - definition: Value 'postjudgment' for enum issue_stage.
  - tags: schema, enum_value

- `ENUMVAL_issue_stage_trial` — EnumValue::issue_stage.trial
  - definition: Value 'trial' for enum issue_stage.
  - tags: schema, enum_value

- `ENUMVAL_motion_kind_enforce_parenting_time` — EnumValue::motion_kind.enforce_parenting_time
  - definition: Value 'enforce_parenting_time' for enum motion_kind.
  - tags: schema, enum_value

- `ENUMVAL_motion_kind_fees_sanctions` — EnumValue::motion_kind.fees_sanctions
  - definition: Value 'fees_sanctions' for enum motion_kind.
  - tags: schema, enum_value

- `ENUMVAL_motion_kind_modify_custody` — EnumValue::motion_kind.modify_custody
  - definition: Value 'modify_custody' for enum motion_kind.
  - tags: schema, enum_value

- `ENUMVAL_motion_kind_modify_parenting_time` — EnumValue::motion_kind.modify_parenting_time
  - definition: Value 'modify_parenting_time' for enum motion_kind.
  - tags: schema, enum_value

- `ENUMVAL_motion_kind_other` — EnumValue::motion_kind.other
  - definition: Value 'other' for enum motion_kind.
  - tags: schema, enum_value

- `ENUMVAL_motion_kind_reconsideration` — EnumValue::motion_kind.reconsideration
  - definition: Value 'reconsideration' for enum motion_kind.
  - tags: schema, enum_value

- `ENUMVAL_motion_kind_recusal_disqualification` — EnumValue::motion_kind.recusal_disqualification
  - definition: Value 'recusal_disqualification' for enum motion_kind.
  - tags: schema, enum_value

- `ENUMVAL_motion_kind_set_aside` — EnumValue::motion_kind.set_aside
  - definition: Value 'set_aside' for enum motion_kind.
  - tags: schema, enum_value

- `ENUMVAL_motion_kind_show_cause_contempt` — EnumValue::motion_kind.show_cause_contempt
  - definition: Value 'show_cause_contempt' for enum motion_kind.
  - tags: schema, enum_value

- `ENUMVAL_motion_kind_stay` — EnumValue::motion_kind.stay
  - definition: Value 'stay' for enum motion_kind.
  - tags: schema, enum_value

- `ENUMVAL_order_status_effective` — EnumValue::order_status.effective
  - definition: Value 'effective' for enum order_status.
  - tags: schema, enum_value

- `ENUMVAL_order_status_entered` — EnumValue::order_status.entered
  - definition: Value 'entered' for enum order_status.
  - tags: schema, enum_value

- `ENUMVAL_order_status_served` — EnumValue::order_status.served
  - definition: Value 'served' for enum order_status.
  - tags: schema, enum_value

- `ENUMVAL_order_status_signed` — EnumValue::order_status.signed
  - definition: Value 'signed' for enum order_status.
  - tags: schema, enum_value

- `ENUMVAL_order_status_stayed` — EnumValue::order_status.stayed
  - definition: Value 'stayed' for enum order_status.
  - tags: schema, enum_value

- `ENUMVAL_order_status_superseded` — EnumValue::order_status.superseded
  - definition: Value 'superseded' for enum order_status.
  - tags: schema, enum_value

- `ENUMVAL_order_status_unknown` — EnumValue::order_status.unknown
  - definition: Value 'unknown' for enum order_status.
  - tags: schema, enum_value

- `ENUMVAL_party_role_appellant` — EnumValue::party_role.appellant
  - definition: Value 'appellant' for enum party_role.
  - tags: schema, enum_value

- `ENUMVAL_party_role_appellee` — EnumValue::party_role.appellee
  - definition: Value 'appellee' for enum party_role.
  - tags: schema, enum_value

- `ENUMVAL_party_role_complainant` — EnumValue::party_role.complainant
  - definition: Value 'complainant' for enum party_role.
  - tags: schema, enum_value

- `ENUMVAL_party_role_defendant` — EnumValue::party_role.defendant
  - definition: Value 'defendant' for enum party_role.
  - tags: schema, enum_value

- `ENUMVAL_party_role_friend_of_court` — EnumValue::party_role.friend_of_court
  - definition: Value 'friend_of_court' for enum party_role.
  - tags: schema, enum_value

- `ENUMVAL_party_role_judge` — EnumValue::party_role.judge
  - definition: Value 'judge' for enum party_role.
  - tags: schema, enum_value

- `ENUMVAL_party_role_other` — EnumValue::party_role.other
  - definition: Value 'other' for enum party_role.
  - tags: schema, enum_value

- `ENUMVAL_party_role_petitioner` — EnumValue::party_role.petitioner
  - definition: Value 'petitioner' for enum party_role.
  - tags: schema, enum_value

- `ENUMVAL_party_role_plaintiff` — EnumValue::party_role.plaintiff
  - definition: Value 'plaintiff' for enum party_role.
  - tags: schema, enum_value

- `ENUMVAL_party_role_respondent` — EnumValue::party_role.respondent
  - definition: Value 'respondent' for enum party_role.
  - tags: schema, enum_value

- `ENUMVAL_record_item_kind_brief` — EnumValue::record_item_kind.brief
  - definition: Value 'brief' for enum record_item_kind.
  - tags: schema, enum_value

- `ENUMVAL_record_item_kind_exhibit` — EnumValue::record_item_kind.exhibit
  - definition: Value 'exhibit' for enum record_item_kind.
  - tags: schema, enum_value

- `ENUMVAL_record_item_kind_motion` — EnumValue::record_item_kind.motion
  - definition: Value 'motion' for enum record_item_kind.
  - tags: schema, enum_value

- `ENUMVAL_record_item_kind_notice` — EnumValue::record_item_kind.notice
  - definition: Value 'notice' for enum record_item_kind.
  - tags: schema, enum_value

- `ENUMVAL_record_item_kind_order` — EnumValue::record_item_kind.order
  - definition: Value 'order' for enum record_item_kind.
  - tags: schema, enum_value

- `ENUMVAL_record_item_kind_other` — EnumValue::record_item_kind.other
  - definition: Value 'other' for enum record_item_kind.
  - tags: schema, enum_value

- `ENUMVAL_record_item_kind_payment_record` — EnumValue::record_item_kind.payment_record
  - definition: Value 'payment_record' for enum record_item_kind.
  - tags: schema, enum_value

- `ENUMVAL_record_item_kind_pleading` — EnumValue::record_item_kind.pleading
  - definition: Value 'pleading' for enum record_item_kind.
  - tags: schema, enum_value

- `ENUMVAL_record_item_kind_proof_of_service` — EnumValue::record_item_kind.proof_of_service
  - definition: Value 'proof_of_service' for enum record_item_kind.
  - tags: schema, enum_value

- `ENUMVAL_record_item_kind_transcript` — EnumValue::record_item_kind.transcript
  - definition: Value 'transcript' for enum record_item_kind.
  - tags: schema, enum_value

- `ENUMVAL_risk_class_admin_return_without_docketing` — EnumValue::risk_class.admin_return_without_docketing
  - definition: Value 'admin_return_without_docketing' for enum risk_class.
  - tags: schema, enum_value

- `ENUMVAL_risk_class_curable_defect` — EnumValue::risk_class.curable_defect
  - definition: Value 'curable_defect' for enum risk_class.
  - tags: schema, enum_value

- `ENUMVAL_risk_class_discretionary_sanction_risk` — EnumValue::risk_class.discretionary_sanction_risk
  - definition: Value 'discretionary_sanction_risk' for enum risk_class.
  - tags: schema, enum_value

- `ENUMVAL_risk_class_dismissal_risk` — EnumValue::risk_class.dismissal_risk
  - definition: Value 'dismissal_risk' for enum risk_class.
  - tags: schema, enum_value

- `ENUMVAL_risk_class_jurisdictional_fatal` — EnumValue::risk_class.jurisdictional_fatal
  - definition: Value 'jurisdictional_fatal' for enum risk_class.
  - tags: schema, enum_value

- `ENUMVAL_risk_class_record_incomplete` — EnumValue::risk_class.record_incomplete
  - definition: Value 'record_incomplete' for enum risk_class.
  - tags: schema, enum_value

- `ENUMVAL_service_method_enum_certified_mail` — EnumValue::service_method_enum.certified_mail
  - definition: Value 'certified_mail' for enum service_method_enum.
  - tags: schema, enum_value

- `ENUMVAL_service_method_enum_electronic` — EnumValue::service_method_enum.electronic
  - definition: Value 'electronic' for enum service_method_enum.
  - tags: schema, enum_value

- `ENUMVAL_service_method_enum_first_class_mail` — EnumValue::service_method_enum.first_class_mail
  - definition: Value 'first_class_mail' for enum service_method_enum.
  - tags: schema, enum_value

- `ENUMVAL_service_method_enum_personal` — EnumValue::service_method_enum.personal
  - definition: Value 'personal' for enum service_method_enum.
  - tags: schema, enum_value

- `ENUMVAL_service_method_enum_publication` — EnumValue::service_method_enum.publication
  - definition: Value 'publication' for enum service_method_enum.
  - tags: schema, enum_value

- `ENUMVAL_service_method_enum_registered_mail` — EnumValue::service_method_enum.registered_mail
  - definition: Value 'registered_mail' for enum service_method_enum.
  - tags: schema, enum_value

- `ENUMVAL_service_method_enum_unknown` — EnumValue::service_method_enum.unknown
  - definition: Value 'unknown' for enum service_method_enum.
  - tags: schema, enum_value

- `ENUMVAL_standard_of_review_kind_abuse_discretion` — EnumValue::standard_of_review_kind.abuse_discretion
  - definition: Value 'abuse_discretion' for enum standard_of_review_kind.
  - tags: schema, enum_value

- `ENUMVAL_standard_of_review_kind_clear_error` — EnumValue::standard_of_review_kind.clear_error
  - definition: Value 'clear_error' for enum standard_of_review_kind.
  - tags: schema, enum_value

- `ENUMVAL_standard_of_review_kind_de_novo` — EnumValue::standard_of_review_kind.de_novo
  - definition: Value 'de_novo' for enum standard_of_review_kind.
  - tags: schema, enum_value

- `ENUMVAL_standard_of_review_kind_mixed` — EnumValue::standard_of_review_kind.mixed
  - definition: Value 'mixed' for enum standard_of_review_kind.
  - tags: schema, enum_value

- `ENUMVAL_standard_of_review_kind_plain_error` — EnumValue::standard_of_review_kind.plain_error
  - definition: Value 'plain_error' for enum standard_of_review_kind.
  - tags: schema, enum_value

- `ENUMVAL_standard_of_review_kind_substantial_evidence` — EnumValue::standard_of_review_kind.substantial_evidence
  - definition: Value 'substantial_evidence' for enum standard_of_review_kind.
  - tags: schema, enum_value

- `ENUMVAL_track_MEEK2` — EnumValue::track.MEEK2
  - definition: Value 'MEEK2' for enum track.
  - tags: schema, enum_value

- `ENUMVAL_track_MEEK3` — EnumValue::track.MEEK3
  - definition: Value 'MEEK3' for enum track.
  - tags: schema, enum_value

- `ENUMVAL_track_MEEK4` — EnumValue::track.MEEK4
  - definition: Value 'MEEK4' for enum track.
  - tags: schema, enum_value

- `ENUM_court_level` — Enum::court_level
  - definition: Allowed values: district|circuit|coa|msc|jtc|other.
  - tags: schema, enum

- `ENUM_deadline_source` — Enum::deadline_source
  - definition: Allowed values: rule|statute|order|clerk_letter|system.
  - tags: schema, enum

- `ENUM_event_kind` — Enum::event_kind
  - definition: Allowed values: FilingEvent|HearingEvent|ServiceEvent|ClerkNoticeEvent|TranscriptEvent|OrderEvent|PaymentEvent|ExtensionEvent|OtherEvent|SupportEvent|PPOEvent|ContemptEvent|FOCEvent|AppealEvent|JTCEvent.
  - tags: schema, enum

- `ENUM_evidence_kind` — Enum::evidence_kind
  - definition: Allowed values: document|photo|video|audio|text_message|email|social_media|court_record|transcript|recording|other.
  - tags: schema, enum

- `ENUM_exhibit_color` — Enum::exhibit_color
  - definition: Allowed values: plaintiff_yellow|defendant_blue|neutral_white.
  - tags: schema, enum

- `ENUM_filing_kind` — Enum::filing_kind
  - definition: Allowed values: motion|pleading|brief|notice|order|affidavit|exhibit_list|appendix|transcript_request|claim_of_appeal|application_leave|other.
  - tags: schema, enum

- `ENUM_forum` — Enum::forum
  - definition: Allowed values: trial|coa|msc|jtc.
  - tags: schema, enum

- `ENUM_hearing_kind` — Enum::hearing_kind
  - definition: Allowed values: motion|evidentiary|showcause|trial|referee|settlement|other.
  - tags: schema, enum

- `ENUM_issue_stage` — Enum::issue_stage
  - definition: Allowed values: trial|postjudgment|appeal_coa|appeal_msc|jtc.
  - tags: schema, enum

- `ENUM_motion_kind` — Enum::motion_kind
  - definition: Allowed values: modify_parenting_time|modify_custody|enforce_parenting_time|show_cause_contempt|set_aside|reconsideration|stay|fees_sanctions|recusal_disqualification|other.
  - tags: schema, enum

- `ENUM_order_status` — Enum::order_status
  - definition: Allowed values: entered|signed|served|effective|superseded|stayed|unknown.
  - tags: schema, enum

- `ENUM_party_role` — Enum::party_role
  - definition: Allowed values: petitioner|respondent|plaintiff|defendant|appellant|appellee|complainant|judge|friend_of_court|other.
  - tags: schema, enum

- `ENUM_record_item_kind` — Enum::record_item_kind
  - definition: Allowed values: order|transcript|exhibit|pleading|motion|brief|notice|proof_of_service|payment_record|other.
  - tags: schema, enum

- `ENUM_risk_class` — Enum::risk_class
  - definition: Allowed values: jurisdictional_fatal|admin_return_without_docketing|curable_defect|dismissal_risk|record_incomplete|discretionary_sanction_risk.
  - tags: schema, enum

- `ENUM_service_method_enum` — Enum::service_method_enum
  - definition: Allowed values: personal|certified_mail|registered_mail|first_class_mail|electronic|publication|unknown.
  - tags: schema, enum

- `ENUM_standard_of_review_kind` — Enum::standard_of_review_kind
  - definition: Allowed values: de_novo|clear_error|abuse_discretion|plain_error|substantial_evidence|mixed.
  - tags: schema, enum

- `ENUM_track` — Enum::track
  - definition: Allowed values: MEEK2|MEEK3|MEEK4.
  - tags: schema, enum

- `Exhibit` — Exhibit
  - definition: Court exhibit wrapper w/ numbering + cover sheet metadata.

- `Exhibit.appendix` — Exhibit.appendix
  - definition: Field/atom 'appendix' within Exhibit.

- `Exhibit.authentication` — Exhibit.authentication
  - definition: Field/atom 'authentication' within Exhibit.

- `Exhibit.best_evidence` — Exhibit.best_evidence
  - definition: Field/atom 'best_evidence' within Exhibit.

- `Exhibit.case_id` — Exhibit.case_id
  - definition: Field/atom 'case_id' within Exhibit.

- `Exhibit.certification` — Exhibit.certification
  - definition: Field/atom 'certification' within Exhibit.

- `Exhibit.effective_date` — Exhibit.effective_date
  - definition: Field/atom 'effective_date' within Exhibit.

- `Exhibit.entered_date` — Exhibit.entered_date
  - definition: Field/atom 'entered_date' within Exhibit.

- `Exhibit.hearsay` — Exhibit.hearsay
  - definition: Field/atom 'hearsay' within Exhibit.

- `Exhibit.id` — Exhibit.id
  - definition: Field/atom 'id' within Exhibit.

- `Exhibit.index` — Exhibit.index
  - definition: Field/atom 'index' within Exhibit.

- `Exhibit.notice` — Exhibit.notice
  - definition: Field/atom 'notice' within Exhibit.

- `Exhibit.pinpoint` — Exhibit.pinpoint
  - definition: Field/atom 'pinpoint' within Exhibit.

- `Exhibit.preservation` — Exhibit.preservation
  - definition: Field/atom 'preservation' within Exhibit.

- `Exhibit.proof_of_service` — Exhibit.proof_of_service
  - definition: Field/atom 'proof_of_service' within Exhibit.

- `Exhibit.served_date` — Exhibit.served_date
  - definition: Field/atom 'served_date' within Exhibit.

- `Exhibit.standard_of_review` — Exhibit.standard_of_review
  - definition: Field/atom 'standard_of_review' within Exhibit.

- `Exhibit.verification` — Exhibit.verification
  - definition: Field/atom 'verification' within Exhibit.

- `FastestCureGenerator` — FastestCureGenerator
  - definition: Ranks cure packets by cost + deadline urgency.

- `HearingEvent` — HearingEvent
  - definition: Hearing event with type, transcript, and recording links.

- `HearingEvent.appendix` — HearingEvent.appendix
  - definition: Field/atom 'appendix' within HearingEvent.

- `HearingEvent.authentication` — HearingEvent.authentication
  - definition: Field/atom 'authentication' within HearingEvent.

- `HearingEvent.best_evidence` — HearingEvent.best_evidence
  - definition: Field/atom 'best_evidence' within HearingEvent.

- `HearingEvent.case_id` — HearingEvent.case_id
  - definition: Field/atom 'case_id' within HearingEvent.

- `HearingEvent.certification` — HearingEvent.certification
  - definition: Field/atom 'certification' within HearingEvent.

- `HearingEvent.effective_date` — HearingEvent.effective_date
  - definition: Field/atom 'effective_date' within HearingEvent.

- `HearingEvent.entered_date` — HearingEvent.entered_date
  - definition: Field/atom 'entered_date' within HearingEvent.

- `HearingEvent.hearsay` — HearingEvent.hearsay
  - definition: Field/atom 'hearsay' within HearingEvent.

- `HearingEvent.id` — HearingEvent.id
  - definition: Field/atom 'id' within HearingEvent.

- `HearingEvent.index` — HearingEvent.index
  - definition: Field/atom 'index' within HearingEvent.

- `HearingEvent.notice` — HearingEvent.notice
  - definition: Field/atom 'notice' within HearingEvent.

- `HearingEvent.pinpoint` — HearingEvent.pinpoint
  - definition: Field/atom 'pinpoint' within HearingEvent.

- `HearingEvent.preservation` — HearingEvent.preservation
  - definition: Field/atom 'preservation' within HearingEvent.

- `HearingEvent.proof_of_service` — HearingEvent.proof_of_service
  - definition: Field/atom 'proof_of_service' within HearingEvent.

- `HearingEvent.served_date` — HearingEvent.served_date
  - definition: Field/atom 'served_date' within HearingEvent.

- `HearingEvent.standard_of_review` — HearingEvent.standard_of_review
  - definition: Field/atom 'standard_of_review' within HearingEvent.

- `HearingEvent.verification` — HearingEvent.verification
  - definition: Field/atom 'verification' within HearingEvent.

- `Issue` — Issue
  - definition: A preserved/legal issue with standard-of-review hooks.

- `Issue.appendix` — Issue.appendix
  - definition: Field/atom 'appendix' within Issue.

- `Issue.authentication` — Issue.authentication
  - definition: Field/atom 'authentication' within Issue.

- `Issue.best_evidence` — Issue.best_evidence
  - definition: Field/atom 'best_evidence' within Issue.

- `Issue.case_id` — Issue.case_id
  - definition: Field/atom 'case_id' within Issue.

- `Issue.certification` — Issue.certification
  - definition: Field/atom 'certification' within Issue.

- `Issue.effective_date` — Issue.effective_date
  - definition: Field/atom 'effective_date' within Issue.

- `Issue.entered_date` — Issue.entered_date
  - definition: Field/atom 'entered_date' within Issue.

- `Issue.hearsay` — Issue.hearsay
  - definition: Field/atom 'hearsay' within Issue.

- `Issue.id` — Issue.id
  - definition: Field/atom 'id' within Issue.

- `Issue.index` — Issue.index
  - definition: Field/atom 'index' within Issue.

- `Issue.notice` — Issue.notice
  - definition: Field/atom 'notice' within Issue.

- `Issue.pinpoint` — Issue.pinpoint
  - definition: Field/atom 'pinpoint' within Issue.

- `Issue.preservation` — Issue.preservation
  - definition: Field/atom 'preservation' within Issue.

- `Issue.proof_of_service` — Issue.proof_of_service
  - definition: Field/atom 'proof_of_service' within Issue.

- `Issue.served_date` — Issue.served_date
  - definition: Field/atom 'served_date' within Issue.

- `Issue.standard_of_review` — Issue.standard_of_review
  - definition: Field/atom 'standard_of_review' within Issue.

- `Issue.verification` — Issue.verification
  - definition: Field/atom 'verification' within Issue.

- `JTCMilestone` — JTCMilestone
  - definition: Judicial Tenure Commission stage node (screening → investigation → disposition).

- `JTC_ConfidentialityRule` — JTC_ConfidentialityRule
  - definition: ConfidentialityRule concept for jtc.

- `JTC_CureWindow` — JTC_CureWindow
  - definition: CureWindow concept for jtc.

- `JTC_DeficiencyLetter` — JTC_DeficiencyLetter
  - definition: DeficiencyLetter concept for jtc.

- `JTC_FilingPacket` — JTC_FilingPacket
  - definition: FilingPacket concept for jtc.

- `JTC_Forum` — JTC_Forum
  - definition: Forum layer semantics and filing gates.

- `JTC_MilestoneTimeline` — JTC_MilestoneTimeline
  - definition: MilestoneTimeline concept for jtc.

- `JTC_ReinstatementMotion` — JTC_ReinstatementMotion
  - definition: ReinstatementMotion concept for jtc.

- `JTC_ReturnWithoutDocketing` — JTC_ReturnWithoutDocketing
  - definition: ReturnWithoutDocketing concept for jtc.

- `MEEK2_AuthorityTriples` — MEEK2_AuthorityTriples
  - definition: AuthorityTriples artifact specialized for MEEK2.

- `MEEK2_CommitSuite` — MEEK2_CommitSuite
  - definition: CommitSuite artifact specialized for MEEK2.

- `MEEK2_ContradictionMap` — MEEK2_ContradictionMap
  - definition: ContradictionMap artifact specialized for MEEK2.

- `MEEK2_DeadlinesTracker` — MEEK2_DeadlinesTracker
  - definition: DeadlinesTracker artifact specialized for MEEK2.

- `MEEK2_ExhibitMatrix` — MEEK2_ExhibitMatrix
  - definition: ExhibitMatrix artifact specialized for MEEK2.

- `MEEK2_Lane` — MEEK2_Lane
  - definition: Track lane scope and required artifacts.

- `MEEK2_Pack` — MEEK2_Pack
  - definition: Pack artifact specialized for MEEK2.

- `MEEK2_RecordPacket` — MEEK2_RecordPacket
  - definition: RecordPacket artifact specialized for MEEK2.

- `MEEK2_RunLedger` — MEEK2_RunLedger
  - definition: RunLedger artifact specialized for MEEK2.

- `MEEK2_SoRLedger` — MEEK2_SoRLedger
  - definition: SoRLedger artifact specialized for MEEK2.

- `MEEK2_Timeline` — MEEK2_Timeline
  - definition: Timeline artifact specialized for MEEK2.

- `MEEK2_ValidatorReport` — MEEK2_ValidatorReport
  - definition: ValidatorReport artifact specialized for MEEK2.

- `MEEK3_AuthorityTriples` — MEEK3_AuthorityTriples
  - definition: AuthorityTriples artifact specialized for MEEK3.

- `MEEK3_CommitSuite` — MEEK3_CommitSuite
  - definition: CommitSuite artifact specialized for MEEK3.

- `MEEK3_ContradictionMap` — MEEK3_ContradictionMap
  - definition: ContradictionMap artifact specialized for MEEK3.

- `MEEK3_DeadlinesTracker` — MEEK3_DeadlinesTracker
  - definition: DeadlinesTracker artifact specialized for MEEK3.

- `MEEK3_ExhibitMatrix` — MEEK3_ExhibitMatrix
  - definition: ExhibitMatrix artifact specialized for MEEK3.

- `MEEK3_Lane` — MEEK3_Lane
  - definition: Track lane scope and required artifacts.

- `MEEK3_Pack` — MEEK3_Pack
  - definition: Pack artifact specialized for MEEK3.

- `MEEK3_RecordPacket` — MEEK3_RecordPacket
  - definition: RecordPacket artifact specialized for MEEK3.

- `MEEK3_RunLedger` — MEEK3_RunLedger
  - definition: RunLedger artifact specialized for MEEK3.

- `MEEK3_SoRLedger` — MEEK3_SoRLedger
  - definition: SoRLedger artifact specialized for MEEK3.

- `MEEK3_Timeline` — MEEK3_Timeline
  - definition: Timeline artifact specialized for MEEK3.

- `MEEK3_ValidatorReport` — MEEK3_ValidatorReport
  - definition: ValidatorReport artifact specialized for MEEK3.

- `MEEK4_AuthorityTriples` — MEEK4_AuthorityTriples
  - definition: AuthorityTriples artifact specialized for MEEK4.

- `MEEK4_CommitSuite` — MEEK4_CommitSuite
  - definition: CommitSuite artifact specialized for MEEK4.

- `MEEK4_ContradictionMap` — MEEK4_ContradictionMap
  - definition: ContradictionMap artifact specialized for MEEK4.

- `MEEK4_DeadlinesTracker` — MEEK4_DeadlinesTracker
  - definition: DeadlinesTracker artifact specialized for MEEK4.

- `MEEK4_ExhibitMatrix` — MEEK4_ExhibitMatrix
  - definition: ExhibitMatrix artifact specialized for MEEK4.

- `MEEK4_Lane` — MEEK4_Lane
  - definition: Track lane scope and required artifacts.

- `MEEK4_Pack` — MEEK4_Pack
  - definition: Pack artifact specialized for MEEK4.

- `MEEK4_RecordPacket` — MEEK4_RecordPacket
  - definition: RecordPacket artifact specialized for MEEK4.

- `MEEK4_RunLedger` — MEEK4_RunLedger
  - definition: RunLedger artifact specialized for MEEK4.

- `MEEK4_SoRLedger` — MEEK4_SoRLedger
  - definition: SoRLedger artifact specialized for MEEK4.

- `MEEK4_Timeline` — MEEK4_Timeline
  - definition: Timeline artifact specialized for MEEK4.

- `MEEK4_ValidatorReport` — MEEK4_ValidatorReport
  - definition: ValidatorReport artifact specialized for MEEK4.

- `MSCReturnWithoutDocketingEngine` — MSCReturnWithoutDocketingEngine
  - definition: MSC risk engine keyed to strict time + clerk return practice.

- `MSC_ConfidentialityRule` — MSC_ConfidentialityRule
  - definition: ConfidentialityRule concept for msc.
  - tags: R, i, s, k, E, n, g, i, n, e

- `MSC_CureWindow` — MSC_CureWindow
  - definition: CureWindow concept for msc.
  - tags: R, i, s, k, E, n, g, i, n, e

- `MSC_DeficiencyLetter` — MSC_DeficiencyLetter
  - definition: DeficiencyLetter concept for msc.
  - tags: R, i, s, k, E, n, g, i, n, e

- `MSC_FilingPacket` — MSC_FilingPacket
  - definition: FilingPacket concept for msc.
  - tags: R, i, s, k, E, n, g, i, n, e

- `MSC_Forum` — MSC_Forum
  - definition: Forum layer semantics and filing gates.
  - tags: R, i, s, k, E, n, g, i, n, e

- `MSC_MilestoneTimeline` — MSC_MilestoneTimeline
  - definition: MilestoneTimeline concept for msc.
  - tags: R, i, s, k, E, n, g, i, n, e

- `MSC_ReinstatementMotion` — MSC_ReinstatementMotion
  - definition: ReinstatementMotion concept for msc.
  - tags: R, i, s, k, E, n, g, i, n, e

- `MSC_ReturnWithoutDocketing` — MSC_ReturnWithoutDocketing
  - definition: ReturnWithoutDocketing concept for msc.
  - tags: R, i, s, k, E, n, g, i, n, e

- `NODE_Address` — Node::Address
  - definition: Physical or mailing address with bi-temporal validity.
  - tags: schema, node

- `NODE_Appeal` — Node::Appeal
  - definition: Appeal proceeding record (COA/MSC) with docketing and briefing clocks.
  - tags: schema, node

- `NODE_ApplicationForLeave` — Node::ApplicationForLeave
  - definition: Application for leave record (COA/MSC).
  - tags: schema, node

- `NODE_Attorney` — Node::Attorney
  - definition: Attorney representation record.
  - tags: schema, node

- `NODE_AuthenticationRule` — Node::AuthenticationRule
  - definition: MRE/MCR authentication or admissibility rule binding to evidence/exhibit.
  - tags: schema, node

- `NODE_Authority` — Node::Authority
  - definition: Authority node (MCR/MCL/MRE/case/benchbook/form).
  - tags: schema, node

- `NODE_BestEvidenceRule` — Node::BestEvidenceRule
  - definition: Best evidence/best available copy requirement mapping.
  - tags: schema, node

- `NODE_Bond` — Node::Bond
  - definition: Bond/bail condition record.
  - tags: schema, node

- `NODE_Brief` — Node::Brief
  - definition: Brief record type (trial/court of appeals/supreme court).
  - tags: schema, node

- `NODE_BriefingSchedule` — Node::BriefingSchedule
  - definition: Briefing schedule record (COA/MSC).
  - tags: schema, node

- `NODE_CanonRule` — Node::CanonRule
  - definition: Judicial canon or ethics rule reference.
  - tags: schema, node

- `NODE_Case` — Node::Case
  - definition: A case/docket (trial/appellate/JTC) with a case_id and posture.
  - tags: schema, node

- `NODE_ChainOfCustody` — Node::ChainOfCustody
  - definition: Chain-of-custody log entry for an evidence item.
  - tags: schema, node

- `NODE_Child` — Node::Child
  - definition: Child record relevant to custody/support/PT.
  - tags: schema, node

- `NODE_ClaimOfAppeal` — Node::ClaimOfAppeal
  - definition: Claim of appeal record (appeal of right).
  - tags: schema, node

- `NODE_ClerkLetter` — Node::ClerkLetter
  - definition: Clerk warning/deficiency letter (return-without-docketing, cure window).
  - tags: schema, node

- `NODE_Clock` — Node::Clock
  - definition: Deadline clock derived from trigger events + tolling.
  - tags: schema, node

- `NODE_CommitSuite` — Node::CommitSuite
  - definition: A packaging run (manifested commit) produced by the system.
  - tags: schema, node

- `NODE_ContactPoint` — Node::ContactPoint
  - definition: Phone/email/portal handle used for service/contact.
  - tags: schema, node

- `NODE_ContemptProceeding` — Node::ContemptProceeding
  - definition: Contempt proceeding record (civil/criminal, bench-trial, show cause).
  - tags: schema, node

- `NODE_Court` — Node::Court
  - definition: Court identity (e.g., 14th Circuit, Michigan Court of Appeals).
  - tags: schema, node

- `NODE_CurePacket` — Node::CurePacket
  - definition: Minimum packet needed to cure a specific defect/risk.
  - tags: schema, node

- `NODE_CustodyProvision` — Node::CustodyProvision
  - definition: Custody/legal/physical terms in an order.
  - tags: schema, node

- `NODE_Deadline` — Node::Deadline
  - definition: Derived deadline with clock, tolling, and service dependencies.
  - tags: schema, node

- `NODE_DenialGround` — Node::DenialGround
  - definition: Denial ground template keyed to vehicle and record gaps.
  - tags: schema, node

- `NODE_DocketingStatement` — Node::DocketingStatement
  - definition: Docketing statement record (COA).
  - tags: schema, node

- `NODE_Event` — Node::Event
  - definition: Typed event (hearing, filing, service, clerk notice, etc.).
  - tags: schema, node

- `NODE_EvidenceAtom` — Node::EvidenceAtom
  - definition: Atomic evidence fact/pointer with provenance, hash, and pinpoints.
  - tags: schema, node

- `NODE_EvidenceItem` — Node::EvidenceItem
  - definition: Evidence atom (document, audio, photo, transcript excerpt, etc.).
  - tags: schema, node

- `NODE_Exhibit` — Node::Exhibit
  - definition: Exhibit wrapper (with numbering + cover sheet metadata).
  - tags: schema, node

- `NODE_FOCAction` — Node::FOCAction
  - definition: Friend of the Court action/event (review, recommendation, enforcement).
  - tags: schema, node

- `NODE_Filing` — Node::Filing
  - definition: A filed document (motion/brief/pleading/notice) with timestamps and method.
  - tags: schema, node

- `NODE_Forum` — Node::Forum
  - definition: Forum layer: trial/coa/msc/jtc.
  - tags: schema, node

- `NODE_HearingEvent` — Node::HearingEvent
  - definition: Hearing occurrence; links to transcript/recording.
  - tags: schema, node

- `NODE_HearsayRule` — Node::HearsayRule
  - definition: Hearsay exception/definition mapping for evidence.
  - tags: schema, node

- `NODE_Issue` — Node::Issue
  - definition: Legal issue node: preservation status, standard-of-review hooks.
  - tags: schema, node

- `NODE_JTCComplaint` — Node::JTCComplaint
  - definition: Judicial Tenure Commission complaint record.
  - tags: schema, node

- `NODE_JTCMilestone` — Node::JTCMilestone
  - definition: JTC process milestone event (screening/investigation/charges/etc.).
  - tags: schema, node

- `NODE_JailCommitment` — Node::JailCommitment
  - definition: Jail commitment/mitimus execution record.
  - tags: schema, node

- `NODE_Matter` — Node::Matter
  - definition: A matter bundle spanning one or more cases (MEEK2/3/4 lanes).
  - tags: schema, node

- `NODE_MisconductAllegation` — Node::MisconductAllegation
  - definition: Allegation of judicial misconduct, mapped to canon/rule and evidence.
  - tags: schema, node

- `NODE_Motion` — Node::Motion
  - definition: Motion record type with hearing linkage and requested relief.
  - tags: schema, node

- `NODE_OperatingOrderPin` — Node::OperatingOrderPin
  - definition: Pinned operative controlling order for a candidate vehicle.
  - tags: schema, node

- `NODE_Order` — Node::Order
  - definition: Signed/entered order; contains effective/served/supersession state.
  - tags: schema, node

- `NODE_Organization` — Node::Organization
  - definition: Organization identity record.
  - tags: schema, node

- `NODE_PPO` — Node::PPO
  - definition: Personal Protection Order record.
  - tags: schema, node

- `NODE_Packet` — Node::Packet
  - definition: A compiled filing packet (record packet) prepared for submission.
  - tags: schema, node

- `NODE_ParentingTimeProvision` — Node::ParentingTimeProvision
  - definition: Parenting-time terms/provision in an order.
  - tags: schema, node

- `NODE_Party` — Node::Party
  - definition: Party in a matter/case (person or org).
  - tags: schema, node

- `NODE_Person` — Node::Person
  - definition: Natural person identity record.
  - tags: schema, node

- `NODE_Pleading` — Node::Pleading
  - definition: Pleading record type (complaint/answer/response).
  - tags: schema, node

- `NODE_PresentationGateProfile` — Node::PresentationGateProfile
  - definition: Forum-specific filing gate profile (COA/MSC/JTC strictness).
  - tags: schema, node

- `NODE_QuotePin` — Node::QuotePin
  - definition: Verbatim quote segment pointer (page/line/timecode).
  - tags: schema, node

- `NODE_ROAEntry` — Node::ROAEntry
  - definition: Single ROA line/item, with dates, doc type, and file/scan pointers.
  - tags: schema, node

- `NODE_Recording` — Node::Recording
  - definition: Audio/video recording artifact; includes timestamp pinpoints.
  - tags: schema, node

- `NODE_RegisterOfActions` — Node::RegisterOfActions
  - definition: ROA container; links to ROA entries.
  - tags: schema, node

- `NODE_Remedy` — Node::Remedy
  - definition: Requested remedy/relief definition and constraints.
  - tags: schema, node

- `NODE_RiskEvent` — Node::RiskEvent
  - definition: Typed risk event (fatal/cureable/dismissal risk/etc.).
  - tags: schema, node

- `NODE_Sanction` — Node::Sanction
  - definition: Sanction/remedy imposed by court.
  - tags: schema, node

- `NODE_ServiceEvent` — Node::ServiceEvent
  - definition: Service act: method, recipient, address selection, proof.
  - tags: schema, node

- `NODE_StandardOfReview` — Node::StandardOfReview
  - definition: Standard of review definition and triggers.
  - tags: schema, node

- `NODE_SupportAccount` — Node::SupportAccount
  - definition: Child support account snapshot record.
  - tags: schema, node

- `NODE_SupportLedgerEntry` — Node::SupportLedgerEntry
  - definition: Child support ledger transaction/payment entry.
  - tags: schema, node

- `NODE_Track` — Node::Track
  - definition: MEEK track lane (MEEK2/MEEK3/MEEK4).
  - tags: schema, node

- `NODE_Transcript` — Node::Transcript
  - definition: Transcript artifact; can be partial/full; includes cert status.
  - tags: schema, node

- `NODE_VehicleCandidate` — Node::VehicleCandidate
  - definition: Candidate legal vehicle with gates + record products required.
  - tags: schema, node

- `NODE_Warrant` — Node::Warrant
  - definition: Warrant/mittimus/bench warrant record.
  - tags: schema, node

- `OperatingOrderPin` — OperatingOrderPin
  - definition: Pinned operative order required for selecting any legal vehicle.
  - tags: V, e, h, i, c, l, e, M, a, p

- `OperatingOrderPin.appendix` — OperatingOrderPin.appendix
  - definition: Field/atom 'appendix' within OperatingOrderPin.
  - tags: V, e, h, i, c, l, e, M, a, p

- `OperatingOrderPin.authentication` — OperatingOrderPin.authentication
  - definition: Field/atom 'authentication' within OperatingOrderPin.
  - tags: V, e, h, i, c, l, e, M, a, p

- `OperatingOrderPin.best_evidence` — OperatingOrderPin.best_evidence
  - definition: Field/atom 'best_evidence' within OperatingOrderPin.
  - tags: V, e, h, i, c, l, e, M, a, p

- `OperatingOrderPin.case_id` — OperatingOrderPin.case_id
  - definition: Field/atom 'case_id' within OperatingOrderPin.
  - tags: V, e, h, i, c, l, e, M, a, p

- `OperatingOrderPin.certification` — OperatingOrderPin.certification
  - definition: Field/atom 'certification' within OperatingOrderPin.
  - tags: V, e, h, i, c, l, e, M, a, p

- `OperatingOrderPin.effective_date` — OperatingOrderPin.effective_date
  - definition: Field/atom 'effective_date' within OperatingOrderPin.
  - tags: V, e, h, i, c, l, e, M, a, p

- `OperatingOrderPin.entered_date` — OperatingOrderPin.entered_date
  - definition: Field/atom 'entered_date' within OperatingOrderPin.
  - tags: V, e, h, i, c, l, e, M, a, p

- `OperatingOrderPin.hearsay` — OperatingOrderPin.hearsay
  - definition: Field/atom 'hearsay' within OperatingOrderPin.
  - tags: V, e, h, i, c, l, e, M, a, p

- `OperatingOrderPin.id` — OperatingOrderPin.id
  - definition: Field/atom 'id' within OperatingOrderPin.
  - tags: V, e, h, i, c, l, e, M, a, p

- `OperatingOrderPin.index` — OperatingOrderPin.index
  - definition: Field/atom 'index' within OperatingOrderPin.
  - tags: V, e, h, i, c, l, e, M, a, p

- `OperatingOrderPin.notice` — OperatingOrderPin.notice
  - definition: Field/atom 'notice' within OperatingOrderPin.
  - tags: V, e, h, i, c, l, e, M, a, p

- `OperatingOrderPin.pinpoint` — OperatingOrderPin.pinpoint
  - definition: Field/atom 'pinpoint' within OperatingOrderPin.
  - tags: V, e, h, i, c, l, e, M, a, p

- `OperatingOrderPin.preservation` — OperatingOrderPin.preservation
  - definition: Field/atom 'preservation' within OperatingOrderPin.
  - tags: V, e, h, i, c, l, e, M, a, p

- `OperatingOrderPin.proof_of_service` — OperatingOrderPin.proof_of_service
  - definition: Field/atom 'proof_of_service' within OperatingOrderPin.
  - tags: V, e, h, i, c, l, e, M, a, p

- `OperatingOrderPin.served_date` — OperatingOrderPin.served_date
  - definition: Field/atom 'served_date' within OperatingOrderPin.
  - tags: V, e, h, i, c, l, e, M, a, p

- `OperatingOrderPin.standard_of_review` — OperatingOrderPin.standard_of_review
  - definition: Field/atom 'standard_of_review' within OperatingOrderPin.
  - tags: V, e, h, i, c, l, e, M, a, p

- `OperatingOrderPin.verification` — OperatingOrderPin.verification
  - definition: Field/atom 'verification' within OperatingOrderPin.
  - tags: V, e, h, i, c, l, e, M, a, p

- `PACKET_PACK_coa_claim_of_appeal` — PacketTemplate::PACK_coa_claim_of_appeal
  - definition: COA claim of appeal packet
  - tags: packet, coa

- `PACKET_PACK_coa_leave_application` — PacketTemplate::PACK_coa_leave_application
  - definition: COA application for leave packet
  - tags: packet, coa

- `PACKET_PACK_jtc_complaint` — PacketTemplate::PACK_jtc_complaint
  - definition: JTC complaint packet
  - tags: packet, jtc

- `PACKET_PACK_msc_leave_application` — PacketTemplate::PACK_msc_leave_application
  - definition: MSC application for leave packet
  - tags: packet, msc

- `PACKET_PACK_trial_motion_core` — PacketTemplate::PACK_trial_motion_core
  - definition: Trial court motion packet (core)
  - tags: packet, trial

- `PACKET_PACK_trial_show_cause_response` — PacketTemplate::PACK_trial_show_cause_response
  - definition: Show-cause response packet
  - tags: packet, trial

- `PresentationGateProfile` — PresentationGateProfile
  - definition: Forum-specific file acceptance profile (COA curable; MSC strict; JTC milestone-accurate).

- `RISK_COA_claim_of_appeal_late` — RiskType::COA_claim_of_appeal_late
  - definition: Claim of appeal appears untimely
  - tags: risk, coa, *

- `RISK_COA_dismissal_letter_cure_window_running` — RiskType::COA_dismissal_letter_cure_window_running
  - definition: COA deficiency letter cure window running
  - tags: risk, coa, *

- `RISK_COA_docketing_statement_missing` — RiskType::COA_docketing_statement_missing
  - definition: Docketing statement missing/late
  - tags: risk, coa, *

- `RISK_COA_transcript_order_missing` — RiskType::COA_transcript_order_missing
  - definition: Transcript not ordered/arranged; record risk
  - tags: risk, coa, *

- `RISK_CUSTODY_missing_hearing_record` — RiskType::CUSTODY_missing_hearing_record
  - definition: No transcript/record for key hearing
  - tags: risk, trial, MEEK2

- `RISK_JTC_28_day_letter_response_due` — RiskType::JTC_28_day_letter_response_due
  - definition: JTC 28-day letter response due (further investigation stage)
  - tags: risk, jtc, MEEK4

- `RISK_JTC_complaint_issued_next_steps` — RiskType::JTC_complaint_issued_next_steps
  - definition: JTC formal complaint issued; hearing/milestone obligations begin
  - tags: risk, jtc, MEEK4

- `RISK_JTC_request_unverified` — RiskType::JTC_request_unverified
  - definition: JTC request for investigation not verified on oath
  - tags: risk, jtc, MEEK4

- `RISK_MSC_application_leave_late` — RiskType::MSC_application_leave_late
  - definition: MSC application for leave appears untimely
  - tags: risk, msc, *

- `RISK_MSC_return_without_docketing_nonconforming` — RiskType::MSC_return_without_docketing_nonconforming
  - definition: MSC filing nonconforming / returned (time limit not satisfied unless corrected)
  - tags: risk, msc, *

- `RISK_PPO_motion_modify_terminate_deadline` — RiskType::PPO_motion_modify_terminate_deadline
  - definition: PPO modification/termination motion deadline triggered
  - tags: risk, trial, MEEK3

- `RISK_PPO_violation_hearing_sentence_appeal_right` — RiskType::PPO_violation_hearing_sentence_appeal_right
  - definition: PPO contempt sentence entered; appeal route must be correct
  - tags: risk, trial, MEEK3

- `RISK_RISK_clerk_notice_unprocessed` — RiskType::RISK_clerk_notice_unprocessed
  - definition: Clerk notice/deficiency letter not processed
  - tags: risk, *, *

- `RISK_RISK_coa_claim_of_appeal_deadline` — RiskType::RISK_coa_claim_of_appeal_deadline
  - definition: Claim of appeal deadline (MCR 7.204) missed/imminent
  - tags: risk, coa, *

- `RISK_RISK_coa_leave_application_deadline` — RiskType::RISK_coa_leave_application_deadline
  - definition: Application for leave deadline (MCR 7.205) missed/imminent
  - tags: risk, coa, *

- `RISK_RISK_jtc_28_day_letter_deadline` — RiskType::RISK_jtc_28_day_letter_deadline
  - definition: JTC 28-day letter response deadline
  - tags: risk, jtc, MEEK4

- `RISK_RISK_missing_operating_order_pin_any` — RiskType::RISK_missing_operating_order_pin_any
  - definition: Operating Order Pin missing for candidate vehicle
  - tags: risk, *, *

- `RISK_RISK_msc_nonconforming_no_toll` — RiskType::RISK_msc_nonconforming_no_toll
  - definition: Nonconforming MSC filing does not satisfy time limit
  - tags: risk, msc, *

- `RISK_RISK_service_defect` — RiskType::RISK_service_defect
  - definition: Service/proof defect
  - tags: risk, *, *

- `RISK_RISK_transcript_not_ordered` — RiskType::RISK_transcript_not_ordered
  - definition: Transcript/record not ordered or certified
  - tags: risk, coa, *

- `RISK_RISK_trial_disqualification_timeliness` — RiskType::RISK_trial_disqualification_timeliness
  - definition: Judge disqualification request timeliness risk
  - tags: risk, trial, *

- `ROAEntry` — ROAEntry
  - definition: Single ROA entry line.

- `ROAEntry.appendix` — ROAEntry.appendix
  - definition: Field/atom 'appendix' within ROAEntry.

- `ROAEntry.authentication` — ROAEntry.authentication
  - definition: Field/atom 'authentication' within ROAEntry.

- `ROAEntry.best_evidence` — ROAEntry.best_evidence
  - definition: Field/atom 'best_evidence' within ROAEntry.

- `ROAEntry.case_id` — ROAEntry.case_id
  - definition: Field/atom 'case_id' within ROAEntry.

- `ROAEntry.certification` — ROAEntry.certification
  - definition: Field/atom 'certification' within ROAEntry.

- `ROAEntry.effective_date` — ROAEntry.effective_date
  - definition: Field/atom 'effective_date' within ROAEntry.

- `ROAEntry.entered_date` — ROAEntry.entered_date
  - definition: Field/atom 'entered_date' within ROAEntry.

- `ROAEntry.hearsay` — ROAEntry.hearsay
  - definition: Field/atom 'hearsay' within ROAEntry.

- `ROAEntry.id` — ROAEntry.id
  - definition: Field/atom 'id' within ROAEntry.

- `ROAEntry.index` — ROAEntry.index
  - definition: Field/atom 'index' within ROAEntry.

- `ROAEntry.notice` — ROAEntry.notice
  - definition: Field/atom 'notice' within ROAEntry.

- `ROAEntry.pinpoint` — ROAEntry.pinpoint
  - definition: Field/atom 'pinpoint' within ROAEntry.

- `ROAEntry.preservation` — ROAEntry.preservation
  - definition: Field/atom 'preservation' within ROAEntry.

- `ROAEntry.proof_of_service` — ROAEntry.proof_of_service
  - definition: Field/atom 'proof_of_service' within ROAEntry.

- `ROAEntry.served_date` — ROAEntry.served_date
  - definition: Field/atom 'served_date' within ROAEntry.

- `ROAEntry.standard_of_review` — ROAEntry.standard_of_review
  - definition: Field/atom 'standard_of_review' within ROAEntry.

- `ROAEntry.verification` — ROAEntry.verification
  - definition: Field/atom 'verification' within ROAEntry.

- `Recording` — Recording
  - definition: Audio/video recording with time pinpoints.

- `RegisterOfActions` — RegisterOfActions
  - definition: ROA ledger: entry list of docket items.

- `RegisterOfActions.appendix` — RegisterOfActions.appendix
  - definition: Field/atom 'appendix' within RegisterOfActions.

- `RegisterOfActions.authentication` — RegisterOfActions.authentication
  - definition: Field/atom 'authentication' within RegisterOfActions.

- `RegisterOfActions.best_evidence` — RegisterOfActions.best_evidence
  - definition: Field/atom 'best_evidence' within RegisterOfActions.

- `RegisterOfActions.case_id` — RegisterOfActions.case_id
  - definition: Field/atom 'case_id' within RegisterOfActions.

- `RegisterOfActions.certification` — RegisterOfActions.certification
  - definition: Field/atom 'certification' within RegisterOfActions.

- `RegisterOfActions.effective_date` — RegisterOfActions.effective_date
  - definition: Field/atom 'effective_date' within RegisterOfActions.

- `RegisterOfActions.entered_date` — RegisterOfActions.entered_date
  - definition: Field/atom 'entered_date' within RegisterOfActions.

- `RegisterOfActions.hearsay` — RegisterOfActions.hearsay
  - definition: Field/atom 'hearsay' within RegisterOfActions.

- `RegisterOfActions.id` — RegisterOfActions.id
  - definition: Field/atom 'id' within RegisterOfActions.

- `RegisterOfActions.index` — RegisterOfActions.index
  - definition: Field/atom 'index' within RegisterOfActions.

- `RegisterOfActions.notice` — RegisterOfActions.notice
  - definition: Field/atom 'notice' within RegisterOfActions.

- `RegisterOfActions.pinpoint` — RegisterOfActions.pinpoint
  - definition: Field/atom 'pinpoint' within RegisterOfActions.

- `RegisterOfActions.preservation` — RegisterOfActions.preservation
  - definition: Field/atom 'preservation' within RegisterOfActions.

- `RegisterOfActions.proof_of_service` — RegisterOfActions.proof_of_service
  - definition: Field/atom 'proof_of_service' within RegisterOfActions.

- `RegisterOfActions.served_date` — RegisterOfActions.served_date
  - definition: Field/atom 'served_date' within RegisterOfActions.

- `RegisterOfActions.standard_of_review` — RegisterOfActions.standard_of_review
  - definition: Field/atom 'standard_of_review' within RegisterOfActions.

- `RegisterOfActions.verification` — RegisterOfActions.verification
  - definition: Field/atom 'verification' within RegisterOfActions.

- `RiskEvent` — RiskEvent
  - definition: Typed risk; includes fastest-cure packet and deadline clock.
  - tags: R, i, s, k, E, n, g, i, n, e

- `RiskEvent.appendix` — RiskEvent.appendix
  - definition: Field/atom 'appendix' within RiskEvent.
  - tags: R, i, s, k, E, n, g, i, n, e

- `RiskEvent.authentication` — RiskEvent.authentication
  - definition: Field/atom 'authentication' within RiskEvent.
  - tags: R, i, s, k, E, n, g, i, n, e

- `RiskEvent.best_evidence` — RiskEvent.best_evidence
  - definition: Field/atom 'best_evidence' within RiskEvent.
  - tags: R, i, s, k, E, n, g, i, n, e

- `RiskEvent.case_id` — RiskEvent.case_id
  - definition: Field/atom 'case_id' within RiskEvent.
  - tags: R, i, s, k, E, n, g, i, n, e

- `RiskEvent.certification` — RiskEvent.certification
  - definition: Field/atom 'certification' within RiskEvent.
  - tags: R, i, s, k, E, n, g, i, n, e

- `RiskEvent.effective_date` — RiskEvent.effective_date
  - definition: Field/atom 'effective_date' within RiskEvent.
  - tags: R, i, s, k, E, n, g, i, n, e

- `RiskEvent.entered_date` — RiskEvent.entered_date
  - definition: Field/atom 'entered_date' within RiskEvent.
  - tags: R, i, s, k, E, n, g, i, n, e

- `RiskEvent.hearsay` — RiskEvent.hearsay
  - definition: Field/atom 'hearsay' within RiskEvent.
  - tags: R, i, s, k, E, n, g, i, n, e

- `RiskEvent.id` — RiskEvent.id
  - definition: Field/atom 'id' within RiskEvent.
  - tags: R, i, s, k, E, n, g, i, n, e

- `RiskEvent.index` — RiskEvent.index
  - definition: Field/atom 'index' within RiskEvent.
  - tags: R, i, s, k, E, n, g, i, n, e

- `RiskEvent.notice` — RiskEvent.notice
  - definition: Field/atom 'notice' within RiskEvent.
  - tags: R, i, s, k, E, n, g, i, n, e

- `RiskEvent.pinpoint` — RiskEvent.pinpoint
  - definition: Field/atom 'pinpoint' within RiskEvent.
  - tags: R, i, s, k, E, n, g, i, n, e

- `RiskEvent.preservation` — RiskEvent.preservation
  - definition: Field/atom 'preservation' within RiskEvent.
  - tags: R, i, s, k, E, n, g, i, n, e

- `RiskEvent.proof_of_service` — RiskEvent.proof_of_service
  - definition: Field/atom 'proof_of_service' within RiskEvent.
  - tags: R, i, s, k, E, n, g, i, n, e

- `RiskEvent.served_date` — RiskEvent.served_date
  - definition: Field/atom 'served_date' within RiskEvent.
  - tags: R, i, s, k, E, n, g, i, n, e

- `RiskEvent.standard_of_review` — RiskEvent.standard_of_review
  - definition: Field/atom 'standard_of_review' within RiskEvent.
  - tags: R, i, s, k, E, n, g, i, n, e

- `RiskEvent.verification` — RiskEvent.verification
  - definition: Field/atom 'verification' within RiskEvent.
  - tags: R, i, s, k, E, n, g, i, n, e

- `ServiceEvent` — ServiceEvent
  - definition: Service act: method, address selection, proof, completion rules.

- `ServiceEvent.appendix` — ServiceEvent.appendix
  - definition: Field/atom 'appendix' within ServiceEvent.

- `ServiceEvent.authentication` — ServiceEvent.authentication
  - definition: Field/atom 'authentication' within ServiceEvent.

- `ServiceEvent.best_evidence` — ServiceEvent.best_evidence
  - definition: Field/atom 'best_evidence' within ServiceEvent.

- `ServiceEvent.case_id` — ServiceEvent.case_id
  - definition: Field/atom 'case_id' within ServiceEvent.

- `ServiceEvent.certification` — ServiceEvent.certification
  - definition: Field/atom 'certification' within ServiceEvent.

- `ServiceEvent.effective_date` — ServiceEvent.effective_date
  - definition: Field/atom 'effective_date' within ServiceEvent.

- `ServiceEvent.entered_date` — ServiceEvent.entered_date
  - definition: Field/atom 'entered_date' within ServiceEvent.

- `ServiceEvent.hearsay` — ServiceEvent.hearsay
  - definition: Field/atom 'hearsay' within ServiceEvent.

- `ServiceEvent.id` — ServiceEvent.id
  - definition: Field/atom 'id' within ServiceEvent.

- `ServiceEvent.index` — ServiceEvent.index
  - definition: Field/atom 'index' within ServiceEvent.

- `ServiceEvent.notice` — ServiceEvent.notice
  - definition: Field/atom 'notice' within ServiceEvent.

- `ServiceEvent.pinpoint` — ServiceEvent.pinpoint
  - definition: Field/atom 'pinpoint' within ServiceEvent.

- `ServiceEvent.preservation` — ServiceEvent.preservation
  - definition: Field/atom 'preservation' within ServiceEvent.

- `ServiceEvent.proof_of_service` — ServiceEvent.proof_of_service
  - definition: Field/atom 'proof_of_service' within ServiceEvent.

- `ServiceEvent.served_date` — ServiceEvent.served_date
  - definition: Field/atom 'served_date' within ServiceEvent.

- `ServiceEvent.standard_of_review` — ServiceEvent.standard_of_review
  - definition: Field/atom 'standard_of_review' within ServiceEvent.

- `ServiceEvent.verification` — ServiceEvent.verification
  - definition: Field/atom 'verification' within ServiceEvent.

- `TRIAL_ConfidentialityRule` — TRIAL_ConfidentialityRule
  - definition: ConfidentialityRule concept for trial.

- `TRIAL_CureWindow` — TRIAL_CureWindow
  - definition: CureWindow concept for trial.

- `TRIAL_DeficiencyLetter` — TRIAL_DeficiencyLetter
  - definition: DeficiencyLetter concept for trial.

- `TRIAL_FilingPacket` — TRIAL_FilingPacket
  - definition: FilingPacket concept for trial.

- `TRIAL_Forum` — TRIAL_Forum
  - definition: Forum layer semantics and filing gates.

- `TRIAL_MilestoneTimeline` — TRIAL_MilestoneTimeline
  - definition: MilestoneTimeline concept for trial.

- `TRIAL_ReinstatementMotion` — TRIAL_ReinstatementMotion
  - definition: ReinstatementMotion concept for trial.

- `TRIAL_ReturnWithoutDocketing` — TRIAL_ReturnWithoutDocketing
  - definition: ReturnWithoutDocketing concept for trial.

- `Transcript` — Transcript
  - definition: Certified hearing transcript or partial excerpt.
  - tags: R, e, c, o, r, d, C, o, m, p, l, e, t, e, n, e, s, s

- `Transcript.appendix` — Transcript.appendix
  - definition: Field/atom 'appendix' within Transcript.
  - tags: R, e, c, o, r, d, C, o, m, p, l, e, t, e, n, e, s, s

- `Transcript.authentication` — Transcript.authentication
  - definition: Field/atom 'authentication' within Transcript.
  - tags: R, e, c, o, r, d, C, o, m, p, l, e, t, e, n, e, s, s

- `Transcript.best_evidence` — Transcript.best_evidence
  - definition: Field/atom 'best_evidence' within Transcript.
  - tags: R, e, c, o, r, d, C, o, m, p, l, e, t, e, n, e, s, s

- `Transcript.case_id` — Transcript.case_id
  - definition: Field/atom 'case_id' within Transcript.
  - tags: R, e, c, o, r, d, C, o, m, p, l, e, t, e, n, e, s, s

- `Transcript.certification` — Transcript.certification
  - definition: Field/atom 'certification' within Transcript.
  - tags: R, e, c, o, r, d, C, o, m, p, l, e, t, e, n, e, s, s

- `Transcript.effective_date` — Transcript.effective_date
  - definition: Field/atom 'effective_date' within Transcript.
  - tags: R, e, c, o, r, d, C, o, m, p, l, e, t, e, n, e, s, s

- `Transcript.entered_date` — Transcript.entered_date
  - definition: Field/atom 'entered_date' within Transcript.
  - tags: R, e, c, o, r, d, C, o, m, p, l, e, t, e, n, e, s, s

- `Transcript.hearsay` — Transcript.hearsay
  - definition: Field/atom 'hearsay' within Transcript.
  - tags: R, e, c, o, r, d, C, o, m, p, l, e, t, e, n, e, s, s

- `Transcript.id` — Transcript.id
  - definition: Field/atom 'id' within Transcript.
  - tags: R, e, c, o, r, d, C, o, m, p, l, e, t, e, n, e, s, s

- `Transcript.index` — Transcript.index
  - definition: Field/atom 'index' within Transcript.
  - tags: R, e, c, o, r, d, C, o, m, p, l, e, t, e, n, e, s, s

- `Transcript.notice` — Transcript.notice
  - definition: Field/atom 'notice' within Transcript.
  - tags: R, e, c, o, r, d, C, o, m, p, l, e, t, e, n, e, s, s

- `Transcript.pinpoint` — Transcript.pinpoint
  - definition: Field/atom 'pinpoint' within Transcript.
  - tags: R, e, c, o, r, d, C, o, m, p, l, e, t, e, n, e, s, s

- `Transcript.preservation` — Transcript.preservation
  - definition: Field/atom 'preservation' within Transcript.
  - tags: R, e, c, o, r, d, C, o, m, p, l, e, t, e, n, e, s, s

- `Transcript.proof_of_service` — Transcript.proof_of_service
  - definition: Field/atom 'proof_of_service' within Transcript.
  - tags: R, e, c, o, r, d, C, o, m, p, l, e, t, e, n, e, s, s

- `Transcript.served_date` — Transcript.served_date
  - definition: Field/atom 'served_date' within Transcript.
  - tags: R, e, c, o, r, d, C, o, m, p, l, e, t, e, n, e, s, s

- `Transcript.standard_of_review` — Transcript.standard_of_review
  - definition: Field/atom 'standard_of_review' within Transcript.
  - tags: R, e, c, o, r, d, C, o, m, p, l, e, t, e, n, e, s, s

- `Transcript.verification` — Transcript.verification
  - definition: Field/atom 'verification' within Transcript.
  - tags: R, e, c, o, r, d, C, o, m, p, l, e, t, e, n, e, s, s

- `VEHICLE_MEEK2_TRIAL_enforce_parenting_time` — Vehicle::MEEK2_TRIAL_enforce_parenting_time
  - definition: 
  - tags: vehicle, trial, MEEK2

- `VEHICLE_MEEK2_TRIAL_modify_custody_parenting_time` — Vehicle::MEEK2_TRIAL_modify_custody_parenting_time
  - definition: 
  - tags: vehicle, trial, MEEK2

- `VEHICLE_MEEK2_TRIAL_objection_referee_recommendation` — Vehicle::MEEK2_TRIAL_objection_referee_recommendation
  - definition: 
  - tags: vehicle, trial, MEEK2

- `VEHICLE_MEEK2_TRIAL_show_cause_contempt` — Vehicle::MEEK2_TRIAL_show_cause_contempt
  - definition: 
  - tags: vehicle, trial, MEEK2

- `VEHICLE_MEEK3_COA_claim_of_appeal_ppo` — Vehicle::MEEK3_COA_claim_of_appeal_ppo
  - definition: 
  - tags: vehicle, coa, MEEK3

- `VEHICLE_MEEK3_TRIAL_motion_modify_terminate_ppo` — Vehicle::MEEK3_TRIAL_motion_modify_terminate_ppo
  - definition: 
  - tags: vehicle, trial, MEEK3

- `VEHICLE_MEEK3_TRIAL_motion_show_cause_ppo_contempt` — Vehicle::MEEK3_TRIAL_motion_show_cause_ppo_contempt
  - definition: 
  - tags: vehicle, trial, MEEK3

- `VEHICLE_MEEK4_COA_superintending_control` — Vehicle::MEEK4_COA_superintending_control
  - definition: 
  - tags: vehicle, coa, MEEK4

- `VEHICLE_MEEK4_JTC_request_for_investigation` — Vehicle::MEEK4_JTC_request_for_investigation
  - definition: 
  - tags: vehicle, jtc, MEEK4

- `VEHICLE_MEEK4_MSC_original_action_superintending_control` — Vehicle::MEEK4_MSC_original_action_superintending_control
  - definition: 
  - tags: vehicle, msc, MEEK4

- `VEHICLE_MEEK4_TRIAL_motion_disqualify_judge` — Vehicle::MEEK4_TRIAL_motion_disqualify_judge
  - definition: 
  - tags: vehicle, trial, MEEK4

- `VEHICLE_VEH_meek2_appeal_coa_app_for_leave` — Vehicle::VEH_meek2_appeal_coa_app_for_leave
  - definition: Application for leave to appeal (custody/support interlocutory or discretionary)
  - tags: vehicle, coa, MEEK2

- `VEHICLE_VEH_meek2_appeal_coa_claim_of_appeal` — Vehicle::VEH_meek2_appeal_coa_claim_of_appeal
  - definition: Claim of appeal from final custody/support order (as applicable)
  - tags: vehicle, coa, MEEK2

- `VEHICLE_VEH_meek2_emergency_motion_parenting_time` — Vehicle::VEH_meek2_emergency_motion_parenting_time
  - definition: Emergency ex parte/short-notice motion re parenting time (when permitted)
  - tags: vehicle, trial, MEEK2

- `VEHICLE_VEH_meek2_foc_review_request` — Vehicle::VEH_meek2_foc_review_request
  - definition: Request for Friend of the Court review/recommendation
  - tags: vehicle, trial, MEEK2

- `VEHICLE_VEH_meek2_motion_contempt_parenting_time_order` — Vehicle::VEH_meek2_motion_contempt_parenting_time_order
  - definition: Motion for order to show cause (parenting-time order enforcement contempt)
  - tags: vehicle, trial, MEEK2

- `VEHICLE_VEH_meek2_motion_enforce_parenting_time_act` — Vehicle::VEH_meek2_motion_enforce_parenting_time_act
  - definition: Parenting Time Enforcement Act motion (makeup time, enforcement, fees)
  - tags: vehicle, trial, MEEK2

- `VEHICLE_VEH_meek2_motion_modify_child_support` — Vehicle::VEH_meek2_motion_modify_child_support
  - definition: Motion to modify child support
  - tags: vehicle, trial, MEEK2

- `VEHICLE_VEH_meek2_motion_modify_custody` — Vehicle::VEH_meek2_motion_modify_custody
  - definition: Motion to modify custody (legal/physical)
  - tags: vehicle, trial, MEEK2

- `VEHICLE_VEH_meek2_motion_modify_parenting_time` — Vehicle::VEH_meek2_motion_modify_parenting_time
  - definition: Motion to modify parenting time
  - tags: vehicle, trial, MEEK2

- `VEHICLE_VEH_meek2_motion_reconsideration` — Vehicle::VEH_meek2_motion_reconsideration
  - definition: Motion for reconsideration (trial court)
  - tags: vehicle, trial, MEEK2

- `VEHICLE_VEH_meek2_motion_set_aside` — Vehicle::VEH_meek2_motion_set_aside
  - definition: Motion for relief from judgment/order (trial court)
  - tags: vehicle, trial, MEEK2

- `VEHICLE_VEH_meek3_coa_application_for_leave` — Vehicle::VEH_meek3_coa_application_for_leave
  - definition: Application for leave to appeal (COA)
  - tags: vehicle, coa, MEEK3

- `VEHICLE_VEH_meek3_coa_claim_of_appeal` — Vehicle::VEH_meek3_coa_claim_of_appeal
  - definition: Claim of appeal (appeal of right) from final order / contempt order (as applicable)
  - tags: vehicle, coa, MEEK3

- `VEHICLE_VEH_meek3_coa_motion_stay` — Vehicle::VEH_meek3_coa_motion_stay
  - definition: Court of Appeals motion for stay (pending appeal)
  - tags: vehicle, coa, MEEK3

- `VEHICLE_VEH_meek3_motion_disqualify_judge` — Vehicle::VEH_meek3_motion_disqualify_judge
  - definition: Motion to disqualify judge
  - tags: vehicle, trial, MEEK3

- `VEHICLE_VEH_meek3_motion_modify_terminate_ppo` — Vehicle::VEH_meek3_motion_modify_terminate_ppo
  - definition: Motion to modify or terminate PPO
  - tags: vehicle, trial, MEEK3

- `VEHICLE_VEH_meek3_motion_reconsideration` — Vehicle::VEH_meek3_motion_reconsideration
  - definition: Motion for reconsideration (PPO/contempt context)
  - tags: vehicle, trial, MEEK3

- `VEHICLE_VEH_meek3_motion_stay` — Vehicle::VEH_meek3_motion_stay
  - definition: Motion for stay of proceedings / stay of sentence (as applicable)
  - tags: vehicle, trial, MEEK3

- `VEHICLE_VEH_meek3_motion_to_quash` — Vehicle::VEH_meek3_motion_to_quash
  - definition: Motion to quash / modify subpoena (if needed)
  - tags: vehicle, trial, MEEK3

- `VEHICLE_VEH_meek3_msc_application_for_leave` — Vehicle::VEH_meek3_msc_application_for_leave
  - definition: Michigan Supreme Court application for leave (or further review) (as applicable)
  - tags: vehicle, msc, MEEK3

- `VEHICLE_VEH_meek3_show_cause_response_packet` — Vehicle::VEH_meek3_show_cause_response_packet
  - definition: Show-cause / contempt response packet (PPO violation allegations)
  - tags: vehicle, trial, MEEK3

- `VEHICLE_VEH_meek3_transcript_request` — Vehicle::VEH_meek3_transcript_request
  - definition: Transcript/recording request and certification packet
  - tags: vehicle, trial, MEEK3

- `VEHICLE_VEH_meek4_coa_superintending_control` — Vehicle::VEH_meek4_coa_superintending_control
  - definition: COA original action: superintending control/mandamus/prohibition (as applicable)
  - tags: vehicle, coa, MEEK4

- `VEHICLE_VEH_meek4_jtc_complaint` — Vehicle::VEH_meek4_jtc_complaint
  - definition: Judicial Tenure Commission complaint (judicial misconduct)
  - tags: vehicle, jtc, MEEK4

- `VEHICLE_VEH_meek4_jtc_response_28_day_letter` — Vehicle::VEH_meek4_jtc_response_28_day_letter
  - definition: Response packet to JTC 28-day letter/request (if issued)
  - tags: vehicle, jtc, MEEK4

- `VEHICLE_VEH_meek4_msc_complaint_administrative` — Vehicle::VEH_meek4_msc_complaint_administrative
  - definition: MSC complaint about administrative/court operations (if applicable)
  - tags: vehicle, msc, MEEK4

- `VEHICLE_VEH_meek4_msc_superintending_control` — Vehicle::VEH_meek4_msc_superintending_control
  - definition: Superintending control / original action (as applicable)
  - tags: vehicle, msc, MEEK4

- `VehicleCandidate` — VehicleCandidate
  - definition: A potential filing vehicle with record gates and denial grounds.

- `VehicleCandidate.appendix` — VehicleCandidate.appendix
  - definition: Field/atom 'appendix' within VehicleCandidate.

- `VehicleCandidate.authentication` — VehicleCandidate.authentication
  - definition: Field/atom 'authentication' within VehicleCandidate.

- `VehicleCandidate.best_evidence` — VehicleCandidate.best_evidence
  - definition: Field/atom 'best_evidence' within VehicleCandidate.

- `VehicleCandidate.case_id` — VehicleCandidate.case_id
  - definition: Field/atom 'case_id' within VehicleCandidate.

- `VehicleCandidate.certification` — VehicleCandidate.certification
  - definition: Field/atom 'certification' within VehicleCandidate.

- `VehicleCandidate.effective_date` — VehicleCandidate.effective_date
  - definition: Field/atom 'effective_date' within VehicleCandidate.

- `VehicleCandidate.entered_date` — VehicleCandidate.entered_date
  - definition: Field/atom 'entered_date' within VehicleCandidate.

- `VehicleCandidate.hearsay` — VehicleCandidate.hearsay
  - definition: Field/atom 'hearsay' within VehicleCandidate.

- `VehicleCandidate.id` — VehicleCandidate.id
  - definition: Field/atom 'id' within VehicleCandidate.

- `VehicleCandidate.index` — VehicleCandidate.index
  - definition: Field/atom 'index' within VehicleCandidate.

- `VehicleCandidate.notice` — VehicleCandidate.notice
  - definition: Field/atom 'notice' within VehicleCandidate.

- `VehicleCandidate.pinpoint` — VehicleCandidate.pinpoint
  - definition: Field/atom 'pinpoint' within VehicleCandidate.

- `VehicleCandidate.preservation` — VehicleCandidate.preservation
  - definition: Field/atom 'preservation' within VehicleCandidate.

- `VehicleCandidate.proof_of_service` — VehicleCandidate.proof_of_service
  - definition: Field/atom 'proof_of_service' within VehicleCandidate.

- `VehicleCandidate.served_date` — VehicleCandidate.served_date
  - definition: Field/atom 'served_date' within VehicleCandidate.

- `VehicleCandidate.standard_of_review` — VehicleCandidate.standard_of_review
  - definition: Field/atom 'standard_of_review' within VehicleCandidate.

- `VehicleCandidate.verification` — VehicleCandidate.verification
  - definition: Field/atom 'verification' within VehicleCandidate.

