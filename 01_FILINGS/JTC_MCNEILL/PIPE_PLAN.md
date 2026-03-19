# PIPE_03_24-01507-DC_JTC_JTC

## CASE_STATE (from CS)
- case: `24-01507-DC`
- lane: `JTC` (code `J`)
- court target: `JTC`
- goal: **JTC complaint packet: hostile record + procedural irregularities**
- emit profile: `heavy`
- tag_mode: `TRUTH_TAGS_ON` | quote_mode: `pinpoint_or_candidate` | pii_policy: `strict`
- channel: `MiFILE` | service_methods: `UNKNOWN`

## Stage plan (inputs → outputs)
- 01. **OOP** (OperatingOrderPins) | requires: ∅ | produces: OOP, OOP_LIBRARY
- 02. **OG** (OrderGraph) | requires: OOP | produces: ORDERGRAPH, TERMTABLE, ATTACKSURFACE
- 03. **AT** (AuthorityTriplesPlus) | requires: OG | produces: TRIPLES, BURDENS, SOR
- 04. **BM** (BenchbookMirror) | requires: AT | produces: FINDINGS, DENIAL_TRAPS, CLOSING_SCRIPT
- 05. **PR** (PacketRecipe) | requires: BM | produces: PACKET_RECIPE, RELIEF_STACK, OUTCOME_MATRIX
- 06. **EM** (ExhibitMatrix) | requires: PR | produces: EXMX, HEARSAY_PLAN, IMPEACHMENT_BUNDLES
- 07. **FS** (FoundationScripts) | requires: EM | produces: FOUNDATION_SCRIPTS, OBJECTION_RESPONSES
- 08. **BT** (BiTemporalTimeline) | requires: FS | produces: BITL, ROAMAP, STATEMENT_INDEX
- 09. **RT** (RedTeam) | requires: BT | produces: REDTEAM, PATCHPLAN, FINAL_LINT
- 10. **MN** (ManifestNotes) | requires: RT | produces: OPS_MANIFEST, EXPORT_PLAN, NAMING_RULES
- 11. **NX** (NextMoves) | requires: MN | produces: SBNA, NEXT_MOVES, ESCALATION_RAILS

## AcquisitionTasks (UNKNOWN→copy/paste ready)
- **AT-24-01507-DC-CTRL_ORDERS**
  - UNKNOWN: Most recent controlling order(s) (entered/signed/effective) + ROA line + service proof.
  - WHY: Required to build OOP/OrderGraph/TermTable and tether relief to enforceable terms.
  - HOW: Court clerk file review/certified copy request (case file access via court-approved method). | MiFILE: download filed-stamped copies and service logs (user-authorized). | MiCOURT public case search: verify event chronology and ROA-style entries (public metadata).
  - DONE WHEN: PDF order(s) + ROA entry reference + service proof artifact(s).

- **AT-24-01507-DC-ROA_PRINT**
  - UNKNOWN: ROA printout / docket entry list showing filings and order entries for the relevant window.
  - WHY: Needed for BiTemporal spine and ROA cross-validation; flags missing docket entries.
  - HOW: MiCOURT public case search print (public metadata). | Clerk ROA print/certified register request (if available).
  - DONE WHEN: ROA/docket list with dates and event labels for the period.

- **AT-24-01507-DC-TRANSCRIPT_AUDIO**
  - UNKNOWN: Transcript or audio request receipts + any transcripts for key hearings tied to adverse rulings/statements.
  - WHY: Quote/pinpoint and preservation; supports StatementIndex and record-correction lanes.
  - HOW: Request transcript through judge’s secretary/court reporter per local procedure. | Request audio (if available) with chain-of-custody notes; keep receipts.
  - DONE WHEN: Transcript PDFs (or audio + request receipts) indexed by hearing date.

- **AT-24-01507-DC-INCIDENT_LIST**
  - UNKNOWN: Incident list (date/time/place/what was said/done) with record pins where available.
  - WHY: JTC packet must be incident-based and record-pinned where possible.
  - HOW: Use chat archive statements as USER_ASSERTED seeds; then attach record pins from orders/transcripts. | Create BiTemporal entries with 'record_time' UNKNOWN until pinned.
  - DONE WHEN: Incident table with exhibit references or planned record retrieval tasks.

## SBNA (computed fail-soft)
- AT-24-01507-DC-INCIDENT_LIST: Build incident list with record pins where possible; attach adverse orders/transcript tasks.
