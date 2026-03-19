# Ingested Sources Index v0006
Generated: 2026-01-19T02:18:30Z

This file catalogs preserved upstream inputs and extracts actionable deltas.

## FRED PRIME OPERATIONS MANUAL — observed dataset stats + integrity blockers (historical snapshot)
nodes.csv (59,897 nodes), edges.csv (296,363 edges), authorities_edges.csv (461,779), edges_authorities_xref.csv (212,534). Computed MASTER_LEGAL_TEXT_INDEX corpus stats (47,076 rows; top extensions; duplicate indicators; text-availability distribution). Generated a reusable local runner: scripts/HARVEST_ENGINE_FULL.py

## TRUE MASTER — governed self-improvement loop (extract)
Evaluation Harness + Regression + Anti-drift governance** ### 3.2 Layer Invariants * Every layer is: * deterministic (same inputs → same outputs) * logged (structured JSON logs) * replayable (cache keys) * auditable (manifest + counts + integrity) --- ## 4) 3× EXPANSION CYCLES (SELF-IMPROVING BUT GOVERNED) For **each** upgrade candidate, execute exactly three cycles: ### Cycle A — Diagnose * Identify bottleneck: recall, precision, resolver stability, layout fidelity, speed, storage. * Generate measurable acceptance criteria. ### Cycle B — Implement * Implement the minimal reliable change. * Update schemas, migrations, and runbooks. ### Cycle C — Verify * Run regression suite: * pointer resolution stability * shard reproducibility * retrieval regression (golden queries) * packet compliance gates * If any regression fails: **rollback and emit FIXLIST**. **No upgrade ships without passing Cycle C.

## Graph+LLM Blueprint — node kits (extract)
LitigationOS Graph + LLM Blueprint for MEEK Tracks
LITIGATION OS – System Blueprint:
Graph Database (Neo4j) – Knowledge Graph of Case Facts
MEEK1: Housing Track (Landlord–Tenant Domain)
Node Types: Person, Organization, Property, LeaseAgreement, CourtCase, LegalDocument, Event, Issue/Violation
Person: e.g. Andrew (tenant), landlord entities; properties include name, role (Tenant, Landlord, Attorney, etc).
Organization: e.g. Shady Oaks MHP LLC (landlord company), property management firms; properties: name, type.
Property: rental unit or address; properties: location, lot number, etc.
LeaseAgreement: represents tenancy contract; properties: start/end dates, terms, signatures.
CourtCase: e.g. eviction case (60th District Court, case #2025-250616-LT); properties: case_id, court, status.
LegalDocument: e.g. eviction notice, court order, settlement agreement; properties: title, date, type (Notice, Order, Agreement), summary.
Event: key incidents and milestones (rent nonpayment, repair issues, eviction filed, hearing held, settlement reached); properties: date, description, event_type.
Issue/Violation: conceptual node for notable issues (e.g. “Retaliation”, “Habitability Issue”, “Contradiction in claim”); used to flag legal violations or falsehoods.
Relationship Types:
Person --[RENTS]--> Property (e.g. Andrew “rents” Lot #5, Shady Oaks).
Person --[PARTY_TO]--> CourtCase (e.g. Andrew PARTY_TO Eviction_Case as Defendant; Shady Oaks LLC as Plaintiff).
Organization --[PARTY_TO]--> CourtCase (company as a party, similar to above).
Person --[SIGNEE]--> LeaseAgreement (links tenants/landlords to the lease contract).
LeaseAgreement --[COVERS]--> Property (the lease pertains to a specific property).
CourtCase --[INVOLVES_PROPERTY]--> Property (eviction case involves that rental property).
LegalDocument --[FILED_IN]--> CourtCase (e.g. Eviction_Notice FILED_IN Eviction_Case).
LegalDocument --[RELATES_TO]--> Issue (e.g. RepairComplaintDocument RELATES_TO Habitability Issue).
Event --[PERTAINS_TO]--> CourtCase (e.g. SettlementReachedEvent PERTAINS_TO Eviction_Case).
Event --[INVOLVES]--> Person/Organization (e.g. NonpaymentEvent INVOLVES Andrew and INVOLVES ShadyOaks LLC).
Event --[TRIGGERS]--> LegalDocument (e.g. NonpaymentEvent TRIGGERS Eviction_Notice filing).
Issue --[EVIDENCED_BY]--> Event or LegalDocument (link a noted issue like “Retaliation” to the specific event or document proving it).
MEEK2: Custody Track (Child Custody & Parenting Time)
Node Types: Person, Child, CourtCase, LegalDocument, Event, Issue/Violation
Person: Andrew (father), Emily (mother), possibly attorneys or family members.
Child: the minor child (e.g. LDW); properties: name, DOB, etc.
CourtCase: custody/child-support case (14th Circuit Family Court, case #24-01507-DC); properties: case_id, court, status (e.g. closed, pending).
LegalDocument: e.g. custody orders, parenting time orders, motions for contempt, ex parte emergency orders; properties: title, date, type (Order, Motion, etc), outcome.
Event: significant incidents (e.g. “2024-03-26 Parenting Time Denial”, police call at exchange, court hearing dates); properties: date, description, event_type.
Issue: e.g. “Parenting Time Denial”, “Contempt of Court”, “Custody Interference”, to categorize patterns of problems.
Relationship Types:

