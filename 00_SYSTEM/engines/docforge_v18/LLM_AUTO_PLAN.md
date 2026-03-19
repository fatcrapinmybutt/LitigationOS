# LLM_AUTO_PLAN V18
Use Pack-first ingestion:
1. Parse `CASE_STATE.md`
2. Draft from `DRAFT_BLOCKS_DROPIN.md`
3. Pull facts only from `Transcript_StatementOfFacts_Pins.md` and `ContradictionMap.md`
4. Cite Michigan authority only from `AuthorityTriples.md`
5. Respect `Deadlines.md` split anchors (entered/signed/served)
6. Emit acquisition tasks for all PARTIAL/UNRESOLVED authority rows
