# LitigationOS — ERD Superset Field Dictionary (v2026-01-19.2)

This file is **append-only** and contains two populations:

- **PROPOSED**: canonical normalized ERD superset (intended target model).
- **EXTRACTED**: table-like structures discovered in your uploaded artifacts (CSV headers / JSON schemas).

## Entity Index

- [ActionPlan](#actionplan) — PROPOSED
- [Address](#address) — PROPOSED
- [Agent](#agent) — PROPOSED
- [Artifact](#artifact) — PROPOSED
- [AtomStatementLink](#atomstatementlink) — PROPOSED
- [AuthorityPinpoint](#authoritypinpoint) — PROPOSED
- [AuthoritySnapshot](#authoritysnapshot) — PROPOSED
- [AuthoritySource](#authoritysource) — PROPOSED
- [BagItBag](#bagitbag) — PROPOSED
- [BagItManifest](#bagitmanifest) — PROPOSED
- [BagItTagManifest](#bagittagmanifest) — PROPOSED
- [BloomPerspective](#bloomperspective) — PROPOSED
- [Bundle](#bundle) — PROPOSED
- [BundleEntry](#bundleentry) — PROPOSED
- [Case](#case) — PROPOSED
- [CaseOrgLink](#caseorglink) — PROPOSED
- [CasePersonLink](#casepersonlink) — PROPOSED
- [CloudEvent](#cloudevent) — PROPOSED
- [ContextPack](#contextpack) — PROPOSED
- [Contradiction](#contradiction) — PROPOSED
- [Court](#court) — PROPOSED
- [DSSEEnvelope](#dsseenvelope) — PROPOSED
- [DerivationActivity](#derivationactivity) — PROPOSED
- [DocketEntry](#docketentry) — PROPOSED
- [Document](#document) — PROPOSED
- [Draft](#draft) — PROPOSED
- [EXTRACTED_AuthorityRef](#extracted_authorityref) — EXTRACTED
- [EXTRACTED_AuthoritySnapshotReceipt](#extracted_authoritysnapshotreceipt) — EXTRACTED
- [EXTRACTED_DeadlineTrigger](#extracted_deadlinetrigger) — EXTRACTED
- [EXTRACTED_EC_AUTHORITY_MAP_CONSOLIDATED__codex_json_csv_extracted_csv](#extracted_ec_authority_map_consolidated__codex_json_csv_extracted_csv) — EXTRACTED
- [EXTRACTED_EC_AUTHORITY_MAP__codex_json_csv_extracted_csv](#extracted_ec_authority_map__codex_json_csv_extracted_csv) — EXTRACTED
- [EXTRACTED_EC_HARM_INDEX_CONSOLIDATED__codex_json_csv_extracted_csv](#extracted_ec_harm_index_consolidated__codex_json_csv_extracted_csv) — EXTRACTED
- [EXTRACTED_EC_HARM_INDEX__codex_json_csv_extracted_csv](#extracted_ec_harm_index__codex_json_csv_extracted_csv) — EXTRACTED
- [EXTRACTED_EC_INDEX (1)__codex_json_csv_extracted_csv](#extracted_ec_index (1)__codex_json_csv_extracted_csv) — EXTRACTED
- [EXTRACTED_EC_RELIEF_SUGGEST__codex_json_csv_extracted_csv](#extracted_ec_relief_suggest__codex_json_csv_extracted_csv) — EXTRACTED
- [EXTRACTED_EvidenceAtom](#extracted_evidenceatom) — EXTRACTED
- [EXTRACTED_Final_Micro_Batch__Solo_Image____Codex_Nodes__data_csv](#extracted_final_micro_batch__solo_image____codex_nodes__data_csv) — EXTRACTED
- [EXTRACTED_FormsCatalog](#extracted_formscatalog) — EXTRACTED
- [EXTRACTED_Inferred_Edges___Eternal_Graph__data_csv](#extracted_inferred_edges___eternal_graph__data_csv) — EXTRACTED
- [EXTRACTED_LawPackManifest](#extracted_lawpackmanifest) — EXTRACTED
- [EXTRACTED_LitigationOS Addendum Bundle Manifest](#extracted_litigationos addendum bundle manifest) — EXTRACTED
- [EXTRACTED_LitigationOS Neo4j Export CSV Contract (column_level)](#extracted_litigationos neo4j export csv contract (column_level)) — EXTRACTED
- [EXTRACTED_LitigationOS Neo4j edges_csv row](#extracted_litigationos neo4j edges_csv row) — EXTRACTED
- [EXTRACTED_LitigationOS Neo4j nodes_csv row](#extracted_litigationos neo4j nodes_csv row) — EXTRACTED
- [EXTRACTED_MI_HC_ZIP_ExecutionPlan](#extracted_mi_hc_zip_executionplan) — EXTRACTED
- [EXTRACTED_Micro_Batch_1___Codex_Nodes__data_csv](#extracted_micro_batch_1___codex_nodes__data_csv) — EXTRACTED
- [EXTRACTED_Micro_Batches_11_13___Codex_Nodes__data_csv](#extracted_micro_batches_11_13___codex_nodes__data_csv) — EXTRACTED
- [EXTRACTED_Micro_Batches_14_16___Codex_Nodes__data_csv](#extracted_micro_batches_14_16___codex_nodes__data_csv) — EXTRACTED
- [EXTRACTED_Micro_Batches_17_19___Codex_Nodes__data_csv](#extracted_micro_batches_17_19___codex_nodes__data_csv) — EXTRACTED
- [EXTRACTED_Micro_Batches_2_4___Codex_Nodes__data_csv](#extracted_micro_batches_2_4___codex_nodes__data_csv) — EXTRACTED
- [EXTRACTED_Micro_Batches_5_7___Codex_Nodes__data_csv](#extracted_micro_batches_5_7___codex_nodes__data_csv) — EXTRACTED
- [EXTRACTED_Micro_Batches_8_10___Codex_Nodes__data_csv](#extracted_micro_batches_8_10___codex_nodes__data_csv) — EXTRACTED
- [EXTRACTED_MindEye2_violation_to_remedy (1)__codex_json_csv_extracted_csv](#extracted_mindeye2_violation_to_remedy (1)__codex_json_csv_extracted_csv) — EXTRACTED
- [EXTRACTED_MindEye2_violation_to_remedy__codex_json_csv_extracted_csv](#extracted_mindeye2_violation_to_remedy__codex_json_csv_extracted_csv) — EXTRACTED
- [EXTRACTED_Parsed_JSON_Nodes_from_Git_Dataset__data_csv](#extracted_parsed_json_nodes_from_git_dataset__data_csv) — EXTRACTED
- [EXTRACTED_Procedural_Edges___Synthesized__data_csv](#extracted_procedural_edges___synthesized__data_csv) — EXTRACTED
- [EXTRACTED_ProofObligation](#extracted_proofobligation) — EXTRACTED
- [EXTRACTED_QuoteLedgerEntry](#extracted_quoteledgerentry) — EXTRACTED
- [EXTRACTED_RecordSpineEvent](#extracted_recordspineevent) — EXTRACTED
- [EXTRACTED_action_row](#extracted_action_row) — EXTRACTED
- [EXTRACTED_atom_row](#extracted_atom_row) — EXTRACTED
- [EXTRACTED_authority_graph_nodeid_to_authorityid_csv](#extracted_authority_graph_nodeid_to_authorityid_csv) — EXTRACTED
- [EXTRACTED_authority_graph_nodes_normalized_csv](#extracted_authority_graph_nodes_normalized_csv) — EXTRACTED
- [EXTRACTED_authority_triples_csv](#extracted_authority_triples_csv) — EXTRACTED
- [EXTRACTED_court_rules_zip_manifest_csv](#extracted_court_rules_zip_manifest_csv) — EXTRACTED
- [EXTRACTED_court_rules_zip_validity_findings_csv](#extracted_court_rules_zip_validity_findings_csv) — EXTRACTED
- [EXTRACTED_delta_row](#extracted_delta_row) — EXTRACTED
- [EXTRACTED_edges:authorities_xref](#extracted_edges:authorities_xref) — EXTRACTED
- [EXTRACTED_edges:authority_cross_refs](#extracted_edges:authority_cross_refs) — EXTRACTED
- [EXTRACTED_edges:authority_has_shard](#extracted_edges:authority_has_shard) — EXTRACTED
- [EXTRACTED_edges:authority_has_shard_prior](#extracted_edges:authority_has_shard_prior) — EXTRACTED
- [EXTRACTED_edges:statement_asserts_fact](#extracted_edges:statement_asserts_fact) — EXTRACTED
- [EXTRACTED_edges_csv](#extracted_edges_csv) — EXTRACTED
- [EXTRACTED_eternal_graph_edges__ETERNAL_GRAPH_BUNDLE_20250902_140440_csv](#extracted_eternal_graph_edges__eternal_graph_bundle_20250902_140440_csv) — EXTRACTED
- [EXTRACTED_eternal_graph_edges__ETERNAL_GRAPH_CSV_JSON_COMPOSITE_20250902_141155_csv](#extracted_eternal_graph_edges__eternal_graph_csv_json_composite_20250902_141155_csv) — EXTRACTED
- [EXTRACTED_eternal_graph_nodes__ETERNAL_GRAPH_BUNDLE_20250902_140440_csv](#extracted_eternal_graph_nodes__eternal_graph_bundle_20250902_140440_csv) — EXTRACTED
- [EXTRACTED_eternal_graph_nodes__ETERNAL_GRAPH_CSV_JSON_COMPOSITE_20250902_141155_csv](#extracted_eternal_graph_nodes__eternal_graph_csv_json_composite_20250902_141155_csv) — EXTRACTED
- [EXTRACTED_gate_row](#extracted_gate_row) — EXTRACTED
- [EXTRACTED_harvest_summary](#extracted_harvest_summary) — EXTRACTED
- [EXTRACTED_index_csv](#extracted_index_csv) — EXTRACTED
- [EXTRACTED_invalid_rows_csv](#extracted_invalid_rows_csv) — EXTRACTED
- [EXTRACTED_job](#extracted_job) — EXTRACTED
- [EXTRACTED_litigation_edges_cyc051_060__codex_json_csv_extracted_csv](#extracted_litigation_edges_cyc051_060__codex_json_csv_extracted_csv) — EXTRACTED
- [EXTRACTED_litigation_nodes (1)__codex_json_csv_extracted_csv](#extracted_litigation_nodes (1)__codex_json_csv_extracted_csv) — EXTRACTED
- [EXTRACTED_litigation_nodes (2)__codex_json_csv_extracted_csv](#extracted_litigation_nodes (2)__codex_json_csv_extracted_csv) — EXTRACTED
- [EXTRACTED_litigation_nodes__codex_json_csv_extracted_csv](#extracted_litigation_nodes__codex_json_csv_extracted_csv) — EXTRACTED
- [EXTRACTED_litigation_nodes_cyc051_060__codex_json_csv_extracted_csv](#extracted_litigation_nodes_cyc051_060__codex_json_csv_extracted_csv) — EXTRACTED
- [EXTRACTED_manifest](#extracted_manifest) — EXTRACTED
- [EXTRACTED_manifest_csv](#extracted_manifest_csv) — EXTRACTED
- [EXTRACTED_mi_source_index_v0006_csv](#extracted_mi_source_index_v0006_csv) — EXTRACTED
- [EXTRACTED_mi_source_index_v0008_csv](#extracted_mi_source_index_v0008_csv) — EXTRACTED
- [EXTRACTED_neo4j_edges_FINAL__codex_json_csv_extracted_csv](#extracted_neo4j_edges_final__codex_json_csv_extracted_csv) — EXTRACTED
- [EXTRACTED_neo4j_nodes (3)__codex_json_csv_extracted_csv](#extracted_neo4j_nodes (3)__codex_json_csv_extracted_csv) — EXTRACTED
- [EXTRACTED_neo4j_nodes_FINAL__codex_json_csv_extracted_csv](#extracted_neo4j_nodes_final__codex_json_csv_extracted_csv) — EXTRACTED
- [EXTRACTED_nodes:authorities](#extracted_nodes:authorities) — EXTRACTED
- [EXTRACTED_nodes:authority](#extracted_nodes:authority) — EXTRACTED
- [EXTRACTED_nodes:authority_prior](#extracted_nodes:authority_prior) — EXTRACTED
- [EXTRACTED_nodes:authority_shard](#extracted_nodes:authority_shard) — EXTRACTED
- [EXTRACTED_nodes:authority_shard_prior](#extracted_nodes:authority_shard_prior) — EXTRACTED
- [EXTRACTED_nodes:factclaim](#extracted_nodes:factclaim) — EXTRACTED
- [EXTRACTED_nodes:statement](#extracted_nodes:statement) — EXTRACTED
- [EXTRACTED_nodes_csv](#extracted_nodes_csv) — EXTRACTED
- [EXTRACTED_rules_extracted_csv](#extracted_rules_extracted_csv) — EXTRACTED
- [EXTRACTED_scao_forms_master__codex_json_csv_extracted_csv](#extracted_scao_forms_master__codex_json_csv_extracted_csv) — EXTRACTED
- [EXTRACTED_score_row](#extracted_score_row) — EXTRACTED
- [EXTRACTED_signal_row](#extracted_signal_row) — EXTRACTED
- [EXTRACTED_sor_manifest_csv](#extracted_sor_manifest_csv) — EXTRACTED
- [EXTRACTED_vehicle_row](#extracted_vehicle_row) — EXTRACTED
- [EdgeTable](#edgetable) — PROPOSED
- [EvidenceAtom](#evidenceatom) — PROPOSED
- [EvidenceFoundationCheck](#evidencefoundationcheck) — PROPOSED
- [EvidenceItem](#evidenceitem) — PROPOSED
- [EvidenceItemExhibitLink](#evidenceitemexhibitlink) — PROPOSED
- [Exhibit](#exhibit) — PROPOSED
- [Fact](#fact) — PROPOSED
- [FactAtomLink](#factatomlink) — PROPOSED
- [Filing](#filing) — PROPOSED
- [GatePOLink](#gatepolink) — PROPOSED
- [GateResult](#gateresult) — PROPOSED
- [GraphContract](#graphcontract) — PROPOSED
- [Hearing](#hearing) — PROPOSED
- [InTotoLink](#intotolink) — PROPOSED
- [IntegrityCheck](#integritycheck) — PROPOSED
- [Neo4jImportJob](#neo4jimportjob) — PROPOSED
- [NodeTable](#nodetable) — PROPOSED
- [OCFLInventory](#ocflinventory) — PROPOSED
- [OCFLObject](#ocflobject) — PROPOSED
- [Objection](#objection) — PROPOSED
- [OfferOfProof](#offerofproof) — PROPOSED
- [OpenLineageRun](#openlineagerun) — PROPOSED
- [Order](#order) — PROPOSED
- [Organization](#organization) — PROPOSED
- [OtelLogRecord](#otellogrecord) — PROPOSED
- [OtelMetricPoint](#otelmetricpoint) — PROPOSED
- [OtelSpan](#otelspan) — PROPOSED
- [PIIItem](#piiitem) — PROPOSED
- [POAtomLink](#poatomlink) — PROPOSED
- [POPinLink](#popinlink) — PROPOSED
- [Person](#person) — PROPOSED
- [ProofObligation](#proofobligation) — PROPOSED
- [Proposition](#proposition) — PROPOSED
- [PropositionFactLink](#propositionfactlink) — PROPOSED
- [PropositionPinLink](#propositionpinlink) — PROPOSED
- [ProvenanceActivity](#provenanceactivity) — PROPOSED
- [ProvenanceAgent](#provenanceagent) — PROPOSED
- [ProvenanceEntity](#provenanceentity) — PROPOSED
- [ProvenanceRelation](#provenancerelation) — PROPOSED
- [ROCrateContext](#rocratecontext) — PROPOSED
- [ROCrateEntity](#rocrateentity) — PROPOSED
- [RedactionAction](#redactionaction) — PROPOSED
- [RetrievalEvent](#retrievalevent) — PROPOSED
- [Run](#run) — PROPOSED
- [RunArtifactLink](#runartifactlink) — PROPOSED
- [RunEvent](#runevent) — PROPOSED
- [RunMetric](#runmetric) — PROPOSED
- [RunStep](#runstep) — PROPOSED
- [SBOMCycloneDXComponent](#sbomcyclonedxcomponent) — PROPOSED
- [SBOMSPDXPackage](#sbomspdxpackage) — PROPOSED
- [SLSAProvenance](#slsaprovenance) — PROPOSED
- [Schedule](#schedule) — PROPOSED
- [ServiceAttempt](#serviceattempt) — PROPOSED
- [ServicePlan](#serviceplan) — PROPOSED
- [ServiceProof](#serviceproof) — PROPOSED
- [Signature](#signature) — PROPOSED
- [Statement](#statement) — PROPOSED
- [StatementFactLink](#statementfactlink) — PROPOSED
- [Task](#task) — PROPOSED
- [Transcript](#transcript) — PROPOSED
- [TranscriptRequest](#transcriptrequest) — PROPOSED
- [TranscriptSegment](#transcriptsegment) — PROPOSED
- [VEXStatement](#vexstatement) — PROPOSED
- [Vehicle](#vehicle) — PROPOSED
- [VehicleMap](#vehiclemap) — PROPOSED
- [VehiclePropositionLink](#vehiclepropositionlink) — PROPOSED
- [WARCRecord](#warcrecord) — PROPOSED
- [Workspace](#workspace) — PROPOSED

---

## ActionPlan

**Origin:** PROPOSED  
**Description:** Selected actions post-gate (file/service/notice/appeal).  
**Primary Key:** actionplan_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| actionplan_id | ulid | Y | Primary key. |
| ap_id | ulid | Y | Primary identifier (ULID recommended). |
| ap_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| ap_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| ap_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| ap_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| ap_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| ap_tags_json | json | N | Freeform tags / labels. |
| ap_notes | text | N | Human notes. |
| ap_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| ap_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| case_id | ulid | N |  |
| run_id | ulid | N |  |
| gate_result_id | ulid | N |  |
| actions_json | json | N |  |
| bundle_id | ulid | N |  |
| execution_notes | text | N |  |

## Address

**Origin:** PROPOSED  
**Description:** Postal address normalized.  
**Primary Key:** address_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| address_id | ulid | Y | Primary key. |
| addr_id | ulid | Y | Primary identifier (ULID recommended). |
| addr_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| addr_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| addr_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| addr_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| addr_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| addr_tags_json | json | N | Freeform tags / labels. |
| addr_notes | text | N | Human notes. |
| addr_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| addr_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| line1 | text | Y |  |
| line2 | text | N |  |
| city | text | Y |  |
| state | text | Y |  |
| postal_code | text | Y |  |
| country | text | N |  |
| lat | float | N |  |
| lng | float | N |  |

## Agent

**Origin:** PROPOSED  
**Description:** Executable actor (human or automation worker).  
**Primary Key:** agent_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| agent_id | ulid | Y | Primary identifier (ULID recommended). |
| agent_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| agent_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| agent_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| agent_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| agent_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| agent_tags_json | json | N | Freeform tags / labels. |
| agent_notes | text | N | Human notes. |
| agent_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| agent_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| agent_name | text | Y |  |
| agent_type | enum | N | human\\|script\\|service\\|llm\\|scheduler |
| host_fingerprint | text | N |  |
| runtime | text | N | python/node/powershell/etc |
| runtime_version | text | N |  |
| capabilities_json | json | N |  |
| default_workdir | text | N |  |
| default_output_root | text | N |  |
| security_profile | enum | N |  |

## Artifact

**Origin:** PROPOSED  
**Description:** A file artifact (original or derived) tracked with lineage.  
**Primary Key:** artifact_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| artifact_id | ulid | Y | Primary key. |
| art_id | ulid | Y | Primary identifier (ULID recommended). |
| art_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| art_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| art_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| art_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| art_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| art_tags_json | json | N | Freeform tags / labels. |
| art_notes | text | N | Human notes. |
| art_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| art_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| artifact_kind | enum | Y |  |
| relative_path | text | Y |  |
| filename | text | Y |  |
| extension | text | N |  |
| mime_type | text | N |  |
| bytes | int | N |  |
| crc32 | text | N |  |
| mtime_utc | datetime_rfc3339 | N |  |
| derived_from_artifact_id | ulid | N |  |
| derivation_activity_id | ulid | N |  |
| vault_cid | text | N |  |
| content_preview | text | N |  |

## AtomStatementLink

**Origin:** PROPOSED  
**Description:** Link table: EvidenceAtom ↔ Statement.  
**Primary Key:** atomstatementlink_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| atomstatementlink_id | ulid | Y | Primary identifier (ULID recommended). |
| atomstatementlink_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| atomstatementlink_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| atomstatementlink_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| atomstatementlink_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| atomstatementlink_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| atomstatementlink_tags_json | json | N | Freeform tags / labels. |
| atomstatementlink_notes | text | N | Human notes. |
| atomstatementlink_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| atomstatementlink_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| atom_id | ulid | Y |  |
| stmt_id | ulid | Y |  |
| basis | text | N | Extraction rationale. |

## AuthorityPinpoint

**Origin:** PROPOSED  
**Description:** Pinpoint locator within an authority source (section, page/line, paragraph, etc.).  
**Primary Key:** authoritypinpoint_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| authoritypinpoint_id | ulid | Y | Primary key. |
| pin_id | ulid | Y | Primary identifier (ULID recommended). |
| pin_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| pin_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| pin_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| pin_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| pin_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| pin_tags_json | json | N | Freeform tags / labels. |
| pin_notes | text | N | Human notes. |
| pin_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| pin_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| authority_source_id | ulid | Y |  |
| pin_type | enum | Y | section\\|page_line\\|para\\|holding\\|rule_part |
| pin_label | text | Y | e.g., MCR 2.003(C)(1) or p.12 l.3-10 |
| pin_path | text | N | machine path |
| page | int | N |  |
| line_start | int | N |  |
| line_end | int | N |  |
| excerpt_verified | bool | N |  |
| excerpt_text | text | N | Only if QuoteLock verified. |
| verification_artifact_id | ulid | N |  |

## AuthoritySnapshot

**Origin:** PROPOSED  
**Description:** Frozen set of authorities valid for a run/release boundary.  
**Primary Key:** authoritysnapshot_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| authoritysnapshot_id | ulid | Y | Primary key. |
| snap_id | ulid | Y | Primary identifier (ULID recommended). |
| snap_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| snap_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| snap_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| snap_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| snap_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| snap_tags_json | json | N | Freeform tags / labels. |
| snap_notes | text | N | Human notes. |
| snap_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| snap_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| snapshot_label | text | Y |  |
| created_for_run_id | ulid | N |  |
| coverage_json | json | N | Which MCR/MCL/MRE etc included. |
| index_artifact_id | ulid | N | auth_snapshot_index.json |
| is_locked | bool | N |  |

## AuthoritySource

**Origin:** PROPOSED  
**Description:** A primary authority source (MCR/MCL/MRE/Benchbook/MSC AO/COA cases/JTC rules, etc.).  
**Primary Key:** authoritysource_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| authoritysource_id | ulid | Y | Primary key. |
| authsrc_id | ulid | Y | Primary identifier (ULID recommended). |
| authsrc_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| authsrc_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| authsrc_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| authsrc_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| authsrc_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| authsrc_tags_json | json | N | Freeform tags / labels. |
| authsrc_notes | text | N | Human notes. |
| authsrc_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| authsrc_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| authority_kind | enum | Y |  |
| title | text | Y |  |
| publisher | text | N |  |
| effective_date | date | N |  |
| version_label | text | N |  |
| source_artifact_id | ulid | N |  |
| extracted_text_artifact_id | ulid | N |  |
| citation_style | text | N |  |

## BagItBag

**Origin:** PROPOSED  
**Description:** BagIt package root metadata (bagit.txt, bag-info, tag files).  
**Primary Key:** bagitbag_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| bagitbag_id | ulid | Y | Primary key. |
| bb_id | ulid | Y | Primary identifier (ULID recommended). |
| bb_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| bb_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| bb_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| bb_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| bb_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| bb_tags_json | json | N | Freeform tags / labels. |
| bb_notes | text | N | Human notes. |
| bb_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| bb_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| bundle_id | ulid | N |  |
| bag_version | text | N |  |
| encoding | text | N |  |
| bag_dir | text | N |  |
| bagit_txt_artifact_id | ulid | N |  |
| bag_info_artifact_id | ulid | N |  |

## BagItManifest

**Origin:** PROPOSED  
**Description:** BagIt payload manifest lines (checksum -> relative path).  
**Primary Key:** bagitmanifest_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| bagitmanifest_id | ulid | Y | Primary key. |
| bm_id | ulid | Y | Primary identifier (ULID recommended). |
| bm_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| bm_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| bm_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| bm_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| bm_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| bm_tags_json | json | N | Freeform tags / labels. |
| bm_notes | text | N | Human notes. |
| bm_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| bm_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| bag_id | ulid | Y |  |
| algorithm | text | Y |  |
| payload_path | text | Y |  |
| checksum | text | Y |  |
| bytes | bigint | N |  |

## BagItTagManifest

**Origin:** PROPOSED  
**Description:** BagIt tagmanifest lines (checksum -> tag file path).  
**Primary Key:** bagittagmanifest_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| bagittagmanifest_id | ulid | Y | Primary key. |
| btm_id | ulid | Y | Primary identifier (ULID recommended). |
| btm_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| btm_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| btm_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| btm_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| btm_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| btm_tags_json | json | N | Freeform tags / labels. |
| btm_notes | text | N | Human notes. |
| btm_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| btm_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| bag_id | ulid | Y |  |
| algorithm | text | Y |  |
| tag_path | text | Y |  |
| checksum | text | Y |  |
| bytes | bigint | N |  |

## BloomPerspective

**Origin:** PROPOSED  
**Description:** Neo4j Bloom perspective pack metadata.  
**Primary Key:** bloomperspective_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| bloomperspective_id | ulid | Y | Primary key. |
| bp_id | ulid | Y | Primary identifier (ULID recommended). |
| bp_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| bp_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| bp_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| bp_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| bp_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| bp_tags_json | json | N | Freeform tags / labels. |
| bp_notes | text | N | Human notes. |
| bp_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| bp_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| perspective_name | text | Y |  |
| json_artifact_id | ulid | N |  |
| import_checklist_artifact_id | ulid | N |  |
| style_notes | text | N |  |

## Bundle

**Origin:** PROPOSED  
**Description:** A packaged deliverable (ZIP folder, MiFile packet, authority pack, etc.).  
**Primary Key:** bundle_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| bundle_id | ulid | Y | Primary identifier (ULID recommended). |
| bundle_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| bundle_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| bundle_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| bundle_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| bundle_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| bundle_tags_json | json | N | Freeform tags / labels. |
| bundle_notes | text | N | Human notes. |
| bundle_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| bundle_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| case_id | ulid | N |  |
| bundle_type | enum | Y | zip\\|packet\\|authority_pack\\|context_pack |
| bundle_version | text | N |  |
| root_path | text | N |  |
| primary_artifact_id | ulid | N |  |
| manifest_artifact_id | ulid | N |  |
| integrity_check_id | ulid | N |  |
| signature_id | ulid | N |  |
| readme_artifact_id | ulid | N |  |
| release_notes_artifact_id | ulid | N |  |

## BundleEntry

**Origin:** PROPOSED  
**Description:** A file/member row within a Bundle.  
**Primary Key:** bundleentry_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| bundleentry_id | ulid | Y | Primary key. |
| be_id | ulid | Y | Primary identifier (ULID recommended). |
| be_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| be_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| be_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| be_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| be_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| be_tags_json | json | N | Freeform tags / labels. |
| be_notes | text | N | Human notes. |
| be_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| be_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| bundle_id | ulid | Y |  |
| artifact_id | ulid | N |  |
| relative_path | text | Y |  |
| bytes | int | N |  |
| crc32 | text | N |  |
| mtime_utc | datetime_rfc3339 | N |  |
| role | enum | N | source\\|output\\|log\\|manifest\\|index\\|diagram |
| content_type | text | N |  |

## Case

**Origin:** PROPOSED  
**Description:** A legal case or matter (trial/appellate/admin).  
**Primary Key:** case_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| case_id | ulid | Y | Primary identifier (ULID recommended). |
| case_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| case_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| case_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| case_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| case_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| case_tags_json | json | N | Freeform tags / labels. |
| case_notes | text | N | Human notes. |
| case_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| case_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| case_number | text | N |  |
| caption | text | N |  |
| track | enum | N | MEEK1..MEEK4 etc. |
| court_id | ulid | N |  |
| case_type | enum | N | Custody, PPO, LT, Appeal, JTC, etc. |
| filed_date | date | N |  |
| closed_date | date | N |  |
| is_active | bool | N |  |
| controlling_order_id | ulid | N | Order currently controlling core posture. |
| register_of_actions_artifact_id | ulid | N |  |
| case_summary_md_artifact_id | ulid | N |  |
| case_state_json_artifact_id | ulid | N | Schema-enforced CASE_STATE output. |
| risk_flags_json | json | N | Bias/retaliation/waiver hazards. |

## CaseOrgLink

**Origin:** PROPOSED  
**Description:** Link table: Case ↔ Organization.  
**Primary Key:** caseorglink_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| caseorglink_id | ulid | Y | Primary identifier (ULID recommended). |
| caseorglink_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| caseorglink_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| caseorglink_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| caseorglink_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| caseorglink_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| caseorglink_tags_json | json | N | Freeform tags / labels. |
| caseorglink_notes | text | N | Human notes. |
| caseorglink_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| caseorglink_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| case_id | ulid | Y |  |
| org_id | ulid | Y |  |
| role | text | N | Role in case. |

## CasePersonLink

**Origin:** PROPOSED  
**Description:** Link table: Case ↔ Person.  
**Primary Key:** casepersonlink_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| casepersonlink_id | ulid | Y | Primary identifier (ULID recommended). |
| casepersonlink_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| casepersonlink_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| casepersonlink_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| casepersonlink_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| casepersonlink_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| casepersonlink_tags_json | json | N | Freeform tags / labels. |
| casepersonlink_notes | text | N | Human notes. |
| casepersonlink_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| casepersonlink_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| case_id | ulid | Y |  |
| person_id | ulid | Y |  |
| role | text | N | Role in case (plaintiff/defendant/judge/witness/etc). |

## CloudEvent

**Origin:** PROPOSED  
**Description:** CloudEvents 1.0 event (for stage + artifact lifecycle).  
**Primary Key:** cloudevent_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| cloudevent_id | ulid | Y | Primary key. |
| ce_id | ulid | Y | Primary identifier (ULID recommended). |
| ce_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| ce_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| ce_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| ce_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| ce_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| ce_tags_json | json | N | Freeform tags / labels. |
| ce_notes | text | N | Human notes. |
| ce_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| ce_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| run_id | ulid | N |  |
| id | text | Y |  |
| source | text | Y |  |
| specversion | text | Y |  |
| type | text | Y |  |
| subject | text | N |  |
| time | datetime_rfc3339 | N |  |
| datacontenttype | text | N |  |
| dataschema | text | N |  |
| data | json | N |  |
| extensions_json | json | N |  |

## ContextPack

**Origin:** PROPOSED  
**Description:** Packaged retrieval context for a drafting task.  
**Primary Key:** contextpack_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| contextpack_id | ulid | Y | Primary key. |
| cp_id | ulid | Y | Primary identifier (ULID recommended). |
| cp_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| cp_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| cp_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| cp_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| cp_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| cp_tags_json | json | N | Freeform tags / labels. |
| cp_notes | text | N | Human notes. |
| cp_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| cp_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| case_id | ulid | N |  |
| task_id | ulid | N |  |
| query | text | N |  |
| filters_json | json | N |  |
| retrieval_artifact_id | ulid | N |  |
| rerank_artifact_id | ulid | N |  |
| selected_evidence_atom_ids_json | json | N |  |
| selected_authority_pin_ids_json | json | N |  |

## Contradiction

**Origin:** PROPOSED  
**Description:** Explicit contradiction mapping between two statements/facts.  
**Primary Key:** contradiction_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| contradiction_id | ulid | Y | Primary key. |
| cx_id | ulid | Y | Primary identifier (ULID recommended). |
| cx_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| cx_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| cx_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| cx_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| cx_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| cx_tags_json | json | N | Freeform tags / labels. |
| cx_notes | text | N | Human notes. |
| cx_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| cx_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| case_id | ulid | N |  |
| lhs_statement_id | ulid | N |  |
| rhs_statement_id | ulid | N |  |
| lhs_fact_id | ulid | N |  |
| rhs_fact_id | ulid | N |  |
| contradiction_type | enum | N |  |
| analysis | text | N |  |

## Court

**Origin:** PROPOSED  
**Description:** Court or tribunal (trial, appellate, agency, JTC).  
**Primary Key:** court_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| court_id | ulid | Y | Primary identifier (ULID recommended). |
| court_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| court_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| court_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| court_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| court_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| court_tags_json | json | N | Freeform tags / labels. |
| court_notes | text | N | Human notes. |
| court_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| court_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| court_name | text | Y |  |
| court_level | enum | N | Trial / COA / MSC / Agency / JTC / Federal overlay. |
| jurisdiction | text | N | Michigan, WDMI, etc. |
| county | text | N |  |
| location_address_id | ulid | N |  |
| efile_portal | text | N | MiFile, etc. |
| local_admin_orders_artifact_id | ulid | N |  |

## DSSEEnvelope

**Origin:** PROPOSED  
**Description:** DSSE envelope for signed attestations.  
**Primary Key:** dsseenvelope_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| dsseenvelope_id | ulid | Y | Primary key. |
| dsse_id | ulid | Y | Primary identifier (ULID recommended). |
| dsse_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| dsse_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| dsse_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| dsse_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| dsse_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| dsse_tags_json | json | N | Freeform tags / labels. |
| dsse_notes | text | N | Human notes. |
| dsse_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| dsse_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| bundle_id | ulid | N |  |
| payload_type | text | N |  |
| payload_b64 | text | N |  |
| signatures_json | json | N |  |

## DerivationActivity

**Origin:** PROPOSED  
**Description:** PROV-style activity node for transformations (extract, OCR, parse, compile, etc.).  
**Primary Key:** derivationactivity_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| derivationactivity_id | ulid | Y | Primary key. |
| act_id | ulid | Y | Primary identifier (ULID recommended). |
| act_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| act_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| act_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| act_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| act_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| act_tags_json | json | N | Freeform tags / labels. |
| act_notes | text | N | Human notes. |
| act_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| act_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| run_id | ulid | N |  |
| activity_type | enum | Y |  |
| tool_name | text | N |  |
| tool_version | text | N |  |
| started_utc | datetime_rfc3339 | N |  |
| ended_utc | datetime_rfc3339 | N |  |
| params_json | json | N |  |
| metrics_json | json | N |  |
| logs_artifact_id | ulid | N |  |

## DocketEntry

**Origin:** PROPOSED  
**Description:** Register of actions / docket entry.  
**Primary Key:** docketentry_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| docketentry_id | ulid | Y | Primary key. |
| docket_id | ulid | Y | Primary identifier (ULID recommended). |
| docket_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| docket_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| docket_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| docket_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| docket_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| docket_tags_json | json | N | Freeform tags / labels. |
| docket_notes | text | N | Human notes. |
| docket_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| docket_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| case_id | ulid | Y |  |
| docket_seq | int | N |  |
| filed_utc | datetime_rfc3339 | N |  |
| entry_text | text | N |  |
| entry_type | enum | N |  |
| document_id | ulid | N |  |
| order_id | ulid | N |  |
| hearing_id | ulid | N |  |
| fee_amount | money | N |  |
| receipt_artifact_id | ulid | N |  |
| mifile_txn_id | text | N |  |

## Document

**Origin:** PROPOSED  
**Description:** A logical document (motion, brief, order, exhibit cover, transcript, etc.) independent of files.  
**Primary Key:** document_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| document_id | ulid | Y | Primary key. |
| doc_id | ulid | Y | Primary identifier (ULID recommended). |
| doc_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| doc_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| doc_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| doc_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| doc_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| doc_tags_json | json | N | Freeform tags / labels. |
| doc_notes | text | N | Human notes. |
| doc_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| doc_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| case_id | ulid | N |  |
| doc_type | enum | Y |  |
| title | text | N |  |
| version_label | text | N |  |
| author_person_id | ulid | N |  |
| created_local_date | date | N |  |
| filed_date | date | N |  |
| filed_by_party_link_id | ulid | N |  |
| primary_artifact_id | ulid | N | Current primary file artifact (PDF/DOCX). |
| text_extract_artifact_id | ulid | N |  |
| ocr_extract_artifact_id | ulid | N |  |
| pii_scan_report_artifact_id | ulid | N |  |
| redaction_plan_artifact_id | ulid | N |  |
| quote_anchor_index_artifact_id | ulid | N |  |
| authority_snapshot_id | ulid | N |  |
| pcw_gate_result_id | ulid | N |  |

## Draft

**Origin:** PROPOSED  
**Description:** A draft artifact with versioning (md/docx/pdf).  
**Primary Key:** draft_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| draft_id | ulid | Y | Primary key. |
| dr_id | ulid | Y | Primary identifier (ULID recommended). |
| dr_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| dr_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| dr_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| dr_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| dr_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| dr_tags_json | json | N | Freeform tags / labels. |
| dr_notes | text | N | Human notes. |
| dr_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| dr_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| case_id | ulid | N |  |
| task_id | ulid | N |  |
| document_id | ulid | N |  |
| draft_type | enum | N | md\\|docx\\|pdf |
| version | text | N |  |
| artifact_id | ulid | N |  |
| notes | text | N |  |

## EXTRACTED_AuthorityRef

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: AuthorityRef  
**Primary Key:** extracted_authorityref_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_authorityref_id | ulid | Y | Primary key. |
| authority_ref_id | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/authority_ref.schema.json |
| authority_ref_id | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/authority_ref.schema.json |
| authority_ref_id | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/authority/authority_ref.schema.json |
| citation_key | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/authority_ref.schema.json |
| citation_key | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/authority_ref.schema.json |
| citation_key | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/authority/authority_ref.schema.json |
| effective_end | string|null | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/authority_ref.schema.json |
| effective_end | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/authority_ref.schema.json |
| effective_end | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/authority/authority_ref.schema.json |
| effective_start | string|null | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/authority_ref.schema.json |
| effective_start | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/authority_ref.schema.json |
| effective_start | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/authority/authority_ref.schema.json |
| kind | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/authority_ref.schema.json |
| kind | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/authority_ref.schema.json |
| kind | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/authority/authority_ref.schema.json |
| meta | object | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/authority_ref.schema.json |
| meta | object | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/authority_ref.schema.json |
| meta | object | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/authority/authority_ref.schema.json |
| pin_ids | array | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/authority_ref.schema.json |
| pin_ids | array | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/authority_ref.schema.json |
| pin_ids | array | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/authority/authority_ref.schema.json |
| section_path | string|null | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/authority_ref.schema.json |
| section_path | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/authority_ref.schema.json |
| section_path | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/authority/authority_ref.schema.json |
| source_id | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/authority_ref.schema.json |
| source_id | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/authority_ref.schema.json |
| source_id | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/authority/authority_ref.schema.json |
| source_path | string|null | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/authority_ref.schema.json |
| source_path | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/authority_ref.schema.json |
| source_path | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/authority/authority_ref.schema.json |
| text_pointer | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/authority_ref.schema.json |
| text_pointer | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/authority_ref.schema.json |
| text_pointer | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/authority/authority_ref.schema.json |

## EXTRACTED_AuthoritySnapshotReceipt

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: AuthoritySnapshotReceipt  
**Primary Key:** extracted_authoritysnapshotreceipt_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_authoritysnapshotreceipt_id | ulid | Y | Primary key. |
| generated_utc | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/authority_snapshot_receipt.schema.json |
| generated_utc | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/authority_snapshot_receipt.schema.json |
| generated_utc | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/authority/authority_snapshot_receipt.schema.json |
| inputs_sha256 | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/authority_snapshot_receipt.schema.json |
| inputs_sha256 | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/authority_snapshot_receipt.schema.json |
| inputs_sha256 | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/authority/authority_snapshot_receipt.schema.json |
| outputs | object | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/authority_snapshot_receipt.schema.json |
| outputs | object | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/authority_snapshot_receipt.schema.json |
| outputs | object | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/authority/authority_snapshot_receipt.schema.json |
| pack_manifest_path | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/authority_snapshot_receipt.schema.json |
| pack_manifest_path | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/authority_snapshot_receipt.schema.json |
| pack_manifest_path | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/authority/authority_snapshot_receipt.schema.json |
| snapshot_id | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/authority_snapshot_receipt.schema.json |
| snapshot_id | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/authority_snapshot_receipt.schema.json |
| snapshot_id | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/authority/authority_snapshot_receipt.schema.json |
| tool | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/authority_snapshot_receipt.schema.json |
| tool | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/authority_snapshot_receipt.schema.json |
| tool | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/authority/authority_snapshot_receipt.schema.json |
| tool_version | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/authority_snapshot_receipt.schema.json |
| tool_version | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/authority_snapshot_receipt.schema.json |
| tool_version | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/authority/authority_snapshot_receipt.schema.json |

## EXTRACTED_DeadlineTrigger

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: DeadlineTrigger  
**Primary Key:** extracted_deadlinetrigger_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_deadlinetrigger_id | ulid | Y | Primary key. |
| anchor_event_id | string | N | From: launcher/schemas/deadline_trigger.schema.json |
| case_id | string | N | From: launcher/schemas/deadline_trigger.schema.json |
| deadline_id | string | N | From: launcher/schemas/deadline_trigger.schema.json |
| due_date_local | string | N | From: launcher/schemas/deadline_trigger.schema.json |
| notes | string | N | From: launcher/schemas/deadline_trigger.schema.json |
| rule_ref | string | N | From: launcher/schemas/deadline_trigger.schema.json |
| ts_utc | string | N | From: launcher/schemas/deadline_trigger.schema.json |

## EXTRACTED_EC_AUTHORITY_MAP_CONSOLIDATED__codex_json_csv_extracted_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: EC_AUTHORITY_MAP_CONSOLIDATED__codex_json_csv_extracted.csv  
**Primary Key:** extracted_ec_authority_map_consolidated__codex_json_csv_extracted_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_ec_authority_map_consolidated__codex_json_csv_extracted_csv_id | ulid | Y | Primary key. |
| cite | text | N | From: eternal/nodes/EC_AUTHORITY_MAP_CONSOLIDATED__codex_json_csv_extracted.csv |
| cite | text | N | From: eternal/edges/EC_AUTHORITY_MAP_CONSOLIDATED__codex_json_csv_extracted.csv |
| cite | text | N | From: eternal/neo4j_import/EC_AUTHORITY_MAP_CONSOLIDATED__codex_json_csv_extracted.csv |
| file | text | N | From: eternal/nodes/EC_AUTHORITY_MAP_CONSOLIDATED__codex_json_csv_extracted.csv |
| file | text | N | From: eternal/edges/EC_AUTHORITY_MAP_CONSOLIDATED__codex_json_csv_extracted.csv |
| file | text | N | From: eternal/neo4j_import/EC_AUTHORITY_MAP_CONSOLIDATED__codex_json_csv_extracted.csv |
| kind | text | N | From: eternal/nodes/EC_AUTHORITY_MAP_CONSOLIDATED__codex_json_csv_extracted.csv |
| kind | text | N | From: eternal/edges/EC_AUTHORITY_MAP_CONSOLIDATED__codex_json_csv_extracted.csv |
| kind | text | N | From: eternal/neo4j_import/EC_AUTHORITY_MAP_CONSOLIDATED__codex_json_csv_extracted.csv |
| source_dir | text | N | From: eternal/nodes/EC_AUTHORITY_MAP_CONSOLIDATED__codex_json_csv_extracted.csv |
| source_dir | text | N | From: eternal/edges/EC_AUTHORITY_MAP_CONSOLIDATED__codex_json_csv_extracted.csv |
| source_dir | text | N | From: eternal/neo4j_import/EC_AUTHORITY_MAP_CONSOLIDATED__codex_json_csv_extracted.csv |
| stream | text | N | From: eternal/nodes/EC_AUTHORITY_MAP_CONSOLIDATED__codex_json_csv_extracted.csv |
| stream | text | N | From: eternal/edges/EC_AUTHORITY_MAP_CONSOLIDATED__codex_json_csv_extracted.csv |
| stream | text | N | From: eternal/neo4j_import/EC_AUTHORITY_MAP_CONSOLIDATED__codex_json_csv_extracted.csv |

## EXTRACTED_EC_AUTHORITY_MAP__codex_json_csv_extracted_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: EC_AUTHORITY_MAP__codex_json_csv_extracted.csv  
**Primary Key:** extracted_ec_authority_map__codex_json_csv_extracted_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_ec_authority_map__codex_json_csv_extracted_csv_id | ulid | Y | Primary key. |
| cite | text | N | From: eternal/nodes/EC_AUTHORITY_MAP__codex_json_csv_extracted.csv |
| cite | text | N | From: eternal/edges/EC_AUTHORITY_MAP__codex_json_csv_extracted.csv |
| cite | text | N | From: eternal/neo4j_import/EC_AUTHORITY_MAP__codex_json_csv_extracted.csv |
| context | text | N | From: eternal/nodes/EC_AUTHORITY_MAP__codex_json_csv_extracted.csv |
| context | text | N | From: eternal/edges/EC_AUTHORITY_MAP__codex_json_csv_extracted.csv |
| context | text | N | From: eternal/neo4j_import/EC_AUTHORITY_MAP__codex_json_csv_extracted.csv |
| file | text | N | From: eternal/nodes/EC_AUTHORITY_MAP__codex_json_csv_extracted.csv |
| file | text | N | From: eternal/edges/EC_AUTHORITY_MAP__codex_json_csv_extracted.csv |
| file | text | N | From: eternal/neo4j_import/EC_AUTHORITY_MAP__codex_json_csv_extracted.csv |
| kind | text | N | From: eternal/nodes/EC_AUTHORITY_MAP__codex_json_csv_extracted.csv |
| kind | text | N | From: eternal/edges/EC_AUTHORITY_MAP__codex_json_csv_extracted.csv |
| kind | text | N | From: eternal/neo4j_import/EC_AUTHORITY_MAP__codex_json_csv_extracted.csv |
| stream | text | N | From: eternal/nodes/EC_AUTHORITY_MAP__codex_json_csv_extracted.csv |
| stream | text | N | From: eternal/edges/EC_AUTHORITY_MAP__codex_json_csv_extracted.csv |
| stream | text | N | From: eternal/neo4j_import/EC_AUTHORITY_MAP__codex_json_csv_extracted.csv |

## EXTRACTED_EC_HARM_INDEX_CONSOLIDATED__codex_json_csv_extracted_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: EC_HARM_INDEX_CONSOLIDATED__codex_json_csv_extracted.csv  
**Primary Key:** extracted_ec_harm_index_consolidated__codex_json_csv_extracted_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_ec_harm_index_consolidated__codex_json_csv_extracted_csv_id | ulid | Y | Primary key. |
| file | text | N | From: eternal/nodes/EC_HARM_INDEX_CONSOLIDATED__codex_json_csv_extracted.csv |
| file | text | N | From: eternal/edges/EC_HARM_INDEX_CONSOLIDATED__codex_json_csv_extracted.csv |
| file | text | N | From: eternal/neo4j_import/EC_HARM_INDEX_CONSOLIDATED__codex_json_csv_extracted.csv |
| source_dir | text | N | From: eternal/nodes/EC_HARM_INDEX_CONSOLIDATED__codex_json_csv_extracted.csv |
| source_dir | text | N | From: eternal/edges/EC_HARM_INDEX_CONSOLIDATED__codex_json_csv_extracted.csv |
| source_dir | text | N | From: eternal/neo4j_import/EC_HARM_INDEX_CONSOLIDATED__codex_json_csv_extracted.csv |
| stream | text | N | From: eternal/nodes/EC_HARM_INDEX_CONSOLIDATED__codex_json_csv_extracted.csv |
| stream | text | N | From: eternal/edges/EC_HARM_INDEX_CONSOLIDATED__codex_json_csv_extracted.csv |
| stream | text | N | From: eternal/neo4j_import/EC_HARM_INDEX_CONSOLIDATED__codex_json_csv_extracted.csv |
| topic | text | N | From: eternal/nodes/EC_HARM_INDEX_CONSOLIDATED__codex_json_csv_extracted.csv |
| topic | text | N | From: eternal/edges/EC_HARM_INDEX_CONSOLIDATED__codex_json_csv_extracted.csv |
| topic | text | N | From: eternal/neo4j_import/EC_HARM_INDEX_CONSOLIDATED__codex_json_csv_extracted.csv |

## EXTRACTED_EC_HARM_INDEX__codex_json_csv_extracted_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: EC_HARM_INDEX__codex_json_csv_extracted.csv  
**Primary Key:** extracted_ec_harm_index__codex_json_csv_extracted_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_ec_harm_index__codex_json_csv_extracted_csv_id | ulid | Y | Primary key. |
| case_refs | text | N | From: eternal/nodes/EC_HARM_INDEX__codex_json_csv_extracted.csv |
| case_refs | text | N | From: eternal/edges/EC_HARM_INDEX__codex_json_csv_extracted.csv |
| case_refs | text | N | From: eternal/neo4j_import/EC_HARM_INDEX__codex_json_csv_extracted.csv |
| dates_found | text | N | From: eternal/nodes/EC_HARM_INDEX__codex_json_csv_extracted.csv |
| dates_found | text | N | From: eternal/edges/EC_HARM_INDEX__codex_json_csv_extracted.csv |
| dates_found | text | N | From: eternal/neo4j_import/EC_HARM_INDEX__codex_json_csv_extracted.csv |
| detected_authorities | text | N | From: eternal/nodes/EC_HARM_INDEX__codex_json_csv_extracted.csv |
| detected_authorities | text | N | From: eternal/edges/EC_HARM_INDEX__codex_json_csv_extracted.csv |
| detected_authorities | text | N | From: eternal/neo4j_import/EC_HARM_INDEX__codex_json_csv_extracted.csv |
| evidence_snippets | text | N | From: eternal/nodes/EC_HARM_INDEX__codex_json_csv_extracted.csv |
| evidence_snippets | text | N | From: eternal/edges/EC_HARM_INDEX__codex_json_csv_extracted.csv |
| evidence_snippets | text | N | From: eternal/neo4j_import/EC_HARM_INDEX__codex_json_csv_extracted.csv |
| file | text | N | From: eternal/nodes/EC_HARM_INDEX__codex_json_csv_extracted.csv |
| file | text | N | From: eternal/edges/EC_HARM_INDEX__codex_json_csv_extracted.csv |
| file | text | N | From: eternal/neo4j_import/EC_HARM_INDEX__codex_json_csv_extracted.csv |
| judges | text | N | From: eternal/nodes/EC_HARM_INDEX__codex_json_csv_extracted.csv |
| judges | text | N | From: eternal/edges/EC_HARM_INDEX__codex_json_csv_extracted.csv |
| judges | text | N | From: eternal/neo4j_import/EC_HARM_INDEX__codex_json_csv_extracted.csv |
| ppo_flag | text | N | From: eternal/nodes/EC_HARM_INDEX__codex_json_csv_extracted.csv |
| ppo_flag | text | N | From: eternal/edges/EC_HARM_INDEX__codex_json_csv_extracted.csv |
| ppo_flag | text | N | From: eternal/neo4j_import/EC_HARM_INDEX__codex_json_csv_extracted.csv |
| stream | text | N | From: eternal/nodes/EC_HARM_INDEX__codex_json_csv_extracted.csv |
| stream | text | N | From: eternal/edges/EC_HARM_INDEX__codex_json_csv_extracted.csv |
| stream | text | N | From: eternal/neo4j_import/EC_HARM_INDEX__codex_json_csv_extracted.csv |
| suggested_relief | text | N | From: eternal/nodes/EC_HARM_INDEX__codex_json_csv_extracted.csv |
| suggested_relief | text | N | From: eternal/edges/EC_HARM_INDEX__codex_json_csv_extracted.csv |
| suggested_relief | text | N | From: eternal/neo4j_import/EC_HARM_INDEX__codex_json_csv_extracted.csv |

## EXTRACTED_EC_INDEX (1)__codex_json_csv_extracted_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: EC_INDEX (1)__codex_json_csv_extracted.csv  
**Primary Key:** extracted_ec_index (1)__codex_json_csv_extracted_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_ec_index (1)__codex_json_csv_extracted_csv_id | ulid | Y | Primary key. |
| abs_path | text | N | From: eternal/nodes/EC_INDEX (1)__codex_json_csv_extracted.csv |
| abs_path | text | N | From: eternal/edges/EC_INDEX (1)__codex_json_csv_extracted.csv |
| abs_path | text | N | From: eternal/neo4j_import/EC_INDEX (1)__codex_json_csv_extracted.csv |
| pages | text | N | From: eternal/nodes/EC_INDEX (1)__codex_json_csv_extracted.csv |
| pages | text | N | From: eternal/edges/EC_INDEX (1)__codex_json_csv_extracted.csv |
| pages | text | N | From: eternal/neo4j_import/EC_INDEX (1)__codex_json_csv_extracted.csv |
| parse_error | text | N | From: eternal/nodes/EC_INDEX (1)__codex_json_csv_extracted.csv |
| parse_error | text | N | From: eternal/edges/EC_INDEX (1)__codex_json_csv_extracted.csv |
| parse_error | text | N | From: eternal/neo4j_import/EC_INDEX (1)__codex_json_csv_extracted.csv |
| rel_path | text | N | From: eternal/nodes/EC_INDEX (1)__codex_json_csv_extracted.csv |
| rel_path | text | N | From: eternal/edges/EC_INDEX (1)__codex_json_csv_extracted.csv |
| rel_path | text | N | From: eternal/neo4j_import/EC_INDEX (1)__codex_json_csv_extracted.csv |
| sha256 | text | N | From: eternal/nodes/EC_INDEX (1)__codex_json_csv_extracted.csv |
| sha256 | text | N | From: eternal/edges/EC_INDEX (1)__codex_json_csv_extracted.csv |
| sha256 | text | N | From: eternal/neo4j_import/EC_INDEX (1)__codex_json_csv_extracted.csv |
| size_bytes | text | N | From: eternal/nodes/EC_INDEX (1)__codex_json_csv_extracted.csv |
| size_bytes | text | N | From: eternal/edges/EC_INDEX (1)__codex_json_csv_extracted.csv |
| size_bytes | text | N | From: eternal/neo4j_import/EC_INDEX (1)__codex_json_csv_extracted.csv |
| text_chars | text | N | From: eternal/nodes/EC_INDEX (1)__codex_json_csv_extracted.csv |
| text_chars | text | N | From: eternal/edges/EC_INDEX (1)__codex_json_csv_extracted.csv |
| text_chars | text | N | From: eternal/neo4j_import/EC_INDEX (1)__codex_json_csv_extracted.csv |
| type | text | N | From: eternal/nodes/EC_INDEX (1)__codex_json_csv_extracted.csv |
| type | text | N | From: eternal/edges/EC_INDEX (1)__codex_json_csv_extracted.csv |
| type | text | N | From: eternal/neo4j_import/EC_INDEX (1)__codex_json_csv_extracted.csv |

## EXTRACTED_EC_RELIEF_SUGGEST__codex_json_csv_extracted_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: EC_RELIEF_SUGGEST__codex_json_csv_extracted.csv  
**Primary Key:** extracted_ec_relief_suggest__codex_json_csv_extracted_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_ec_relief_suggest__codex_json_csv_extracted_csv_id | ulid | Y | Primary key. |
| count | text | N | From: eternal/nodes/EC_RELIEF_SUGGEST__codex_json_csv_extracted.csv |
| count | text | N | From: eternal/edges/EC_RELIEF_SUGGEST__codex_json_csv_extracted.csv |
| count | text | N | From: eternal/neo4j_import/EC_RELIEF_SUGGEST__codex_json_csv_extracted.csv |
| relief | text | N | From: eternal/nodes/EC_RELIEF_SUGGEST__codex_json_csv_extracted.csv |
| relief | text | N | From: eternal/edges/EC_RELIEF_SUGGEST__codex_json_csv_extracted.csv |
| relief | text | N | From: eternal/neo4j_import/EC_RELIEF_SUGGEST__codex_json_csv_extracted.csv |
| stream | text | N | From: eternal/nodes/EC_RELIEF_SUGGEST__codex_json_csv_extracted.csv |
| stream | text | N | From: eternal/edges/EC_RELIEF_SUGGEST__codex_json_csv_extracted.csv |
| stream | text | N | From: eternal/neo4j_import/EC_RELIEF_SUGGEST__codex_json_csv_extracted.csv |

## EXTRACTED_EvidenceAtom

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: EvidenceAtom  
**Primary Key:** extracted_evidenceatom_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_evidenceatom_id | ulid | Y | Primary key. |
| evid_id | string | N | From: launcher/schemas/evidence_atom.schema.json |
| kind | string | N | From: launcher/schemas/evidence_atom.schema.json |
| labels | array | N | From: launcher/schemas/evidence_atom.schema.json |
| notes | string | N | From: launcher/schemas/evidence_atom.schema.json |
| pointers | array | N | From: launcher/schemas/evidence_atom.schema.json |
| receipt | object | N | From: launcher/schemas/evidence_atom.schema.json |
| source_path | string | N | From: launcher/schemas/evidence_atom.schema.json |
| ts_utc | string | N | From: launcher/schemas/evidence_atom.schema.json |

## EXTRACTED_Final_Micro_Batch__Solo_Image____Codex_Nodes__data_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: Final_Micro-Batch__Solo_Image____Codex_Nodes__data.csv  
**Primary Key:** extracted_final_micro_batch__solo_image____codex_nodes__data_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_final_micro_batch__solo_image____codex_nodes__data_csv_id | ulid | Y | Primary key. |
| id | text | N | From: eternal/nodes/Final_Micro-Batch__Solo_Image____Codex_Nodes__data.csv |
| id | text | N | From: eternal/edges/Final_Micro-Batch__Solo_Image____Codex_Nodes__data.csv |
| id | text | N | From: eternal/neo4j_import/Final_Micro-Batch__Solo_Image____Codex_Nodes__data.csv |
| label | text | N | From: eternal/nodes/Final_Micro-Batch__Solo_Image____Codex_Nodes__data.csv |
| label | text | N | From: eternal/edges/Final_Micro-Batch__Solo_Image____Codex_Nodes__data.csv |
| label | text | N | From: eternal/neo4j_import/Final_Micro-Batch__Solo_Image____Codex_Nodes__data.csv |
| source_file | text | N | From: eternal/nodes/Final_Micro-Batch__Solo_Image____Codex_Nodes__data.csv |
| source_file | text | N | From: eternal/edges/Final_Micro-Batch__Solo_Image____Codex_Nodes__data.csv |
| source_file | text | N | From: eternal/neo4j_import/Final_Micro-Batch__Solo_Image____Codex_Nodes__data.csv |

## EXTRACTED_FormsCatalog

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: FormsCatalog  
**Primary Key:** extracted_formscatalog_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_formscatalog_id | ulid | Y | Primary key. |
| catalog_id | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/forms/forms_catalog.schema.json |
| catalog_id | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/forms/forms_catalog.schema.json |
| catalog_id | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/forms/forms_catalog.schema.json |
| forms | array | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/forms/forms_catalog.schema.json |
| forms | array | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/forms/forms_catalog.schema.json |
| forms | array | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/forms/forms_catalog.schema.json |
| generated_utc | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/forms/forms_catalog.schema.json |
| generated_utc | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/forms/forms_catalog.schema.json |
| generated_utc | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/forms/forms_catalog.schema.json |
| source_inputs | array | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/forms/forms_catalog.schema.json |
| source_inputs | array | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/forms/forms_catalog.schema.json |
| source_inputs | array | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/forms/forms_catalog.schema.json |

## EXTRACTED_Inferred_Edges___Eternal_Graph__data_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: Inferred_Edges___Eternal_Graph__data.csv  
**Primary Key:** extracted_inferred_edges___eternal_graph__data_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_inferred_edges___eternal_graph__data_csv_id | ulid | Y | Primary key. |
| "" | text | N | From: eternal/nodes/Inferred_Edges___Eternal_Graph__data.csv |
| "" | text | N | From: eternal/edges/Inferred_Edges___Eternal_Graph__data.csv |
| "" | text | N | From: eternal/neo4j_import/Inferred_Edges___Eternal_Graph__data.csv |

## EXTRACTED_LawPackManifest

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: LawPackManifest  
**Primary Key:** extracted_lawpackmanifest_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_lawpackmanifest_id | ulid | Y | Primary key. |
| created_utc | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/law_pack_manifest.schema.json |
| created_utc | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/law_pack_manifest.schema.json |
| created_utc | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/authority/law_pack_manifest.schema.json |
| notes | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/law_pack_manifest.schema.json |
| notes | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/law_pack_manifest.schema.json |
| notes | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/authority/law_pack_manifest.schema.json |
| pack_id | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/law_pack_manifest.schema.json |
| pack_id | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/law_pack_manifest.schema.json |
| pack_id | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/authority/law_pack_manifest.schema.json |
| pack_kind | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/law_pack_manifest.schema.json |
| pack_kind | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/law_pack_manifest.schema.json |
| pack_kind | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/authority/law_pack_manifest.schema.json |
| sources | array | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/law_pack_manifest.schema.json |
| sources | array | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/authority/law_pack_manifest.schema.json |
| sources | array | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/authority/law_pack_manifest.schema.json |

## EXTRACTED_LitigationOS Addendum Bundle Manifest

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: LitigationOS Addendum Bundle Manifest  
**Primary Key:** extracted_litigationos addendum bundle manifest_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_litigationos addendum bundle manifest_id | ulid | Y | Primary key. |
| bundle_name | string | N | From: addendum/_meta/litigationos_pack.schema.json |
| files | array | N | From: addendum/_meta/litigationos_pack.schema.json |
| generated_at | string | N | From: addendum/_meta/litigationos_pack.schema.json |

## EXTRACTED_LitigationOS Neo4j Export CSV Contract (column_level)

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: LitigationOS Neo4j Export CSV Contract (column-level)  
**Primary Key:** extracted_litigationos neo4j export csv contract (column_level)_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_litigationos neo4j export csv contract (column_level)_id | ulid | Y | Primary key. |
| constraints | object | N | From: launcher/schemas/neo4j_export/nodes_runs.schema.json |
| constraints | object | N | From: launcher/schemas/neo4j_export/nodes_files.schema.json |
| constraints | object | N | From: launcher/schemas/neo4j_export/nodes_pdf_pages.schema.json |
| constraints | object | N | From: launcher/schemas/neo4j_export/nodes_transcript_atoms.schema.json |
| constraints | object | N | From: launcher/schemas/neo4j_export/nodes_authority_candidates.schema.json |
| constraints | object | N | From: launcher/schemas/neo4j_export/nodes_service_candidates.schema.json |
| constraints | object | N | From: launcher/schemas/neo4j_export/rels_run_has_file.schema.json |
| constraints | object | N | From: launcher/schemas/neo4j_export/rels_file_has_pdf_page.schema.json |
| constraints | object | N | From: launcher/schemas/neo4j_export/rels_file_has_transcript_atom.schema.json |
| constraints | object | N | From: launcher/schemas/neo4j_export/rels_run_has_authority_candidate.schema.json |
| constraints | object | N | From: launcher/schemas/neo4j_export/rels_run_has_service_candidate.schema.json |
| kind | string | N | From: launcher/schemas/neo4j_export/nodes_runs.schema.json |
| kind | string | N | From: launcher/schemas/neo4j_export/nodes_files.schema.json |
| kind | string | N | From: launcher/schemas/neo4j_export/nodes_pdf_pages.schema.json |
| kind | string | N | From: launcher/schemas/neo4j_export/nodes_transcript_atoms.schema.json |
| kind | string | N | From: launcher/schemas/neo4j_export/nodes_authority_candidates.schema.json |
| kind | string | N | From: launcher/schemas/neo4j_export/nodes_service_candidates.schema.json |
| kind | string | N | From: launcher/schemas/neo4j_export/rels_run_has_file.schema.json |
| kind | string | N | From: launcher/schemas/neo4j_export/rels_file_has_pdf_page.schema.json |
| kind | string | N | From: launcher/schemas/neo4j_export/rels_file_has_transcript_atom.schema.json |
| kind | string | N | From: launcher/schemas/neo4j_export/rels_run_has_authority_candidate.schema.json |
| kind | string | N | From: launcher/schemas/neo4j_export/rels_run_has_service_candidate.schema.json |
| optional_columns | array | N | From: launcher/schemas/neo4j_export/nodes_runs.schema.json |
| optional_columns | array | N | From: launcher/schemas/neo4j_export/nodes_files.schema.json |
| optional_columns | array | N | From: launcher/schemas/neo4j_export/nodes_pdf_pages.schema.json |
| optional_columns | array | N | From: launcher/schemas/neo4j_export/nodes_transcript_atoms.schema.json |
| optional_columns | array | N | From: launcher/schemas/neo4j_export/nodes_authority_candidates.schema.json |
| optional_columns | array | N | From: launcher/schemas/neo4j_export/nodes_service_candidates.schema.json |
| optional_columns | array | N | From: launcher/schemas/neo4j_export/rels_run_has_file.schema.json |
| optional_columns | array | N | From: launcher/schemas/neo4j_export/rels_file_has_pdf_page.schema.json |
| optional_columns | array | N | From: launcher/schemas/neo4j_export/rels_file_has_transcript_atom.schema.json |
| optional_columns | array | N | From: launcher/schemas/neo4j_export/rels_run_has_authority_candidate.schema.json |
| optional_columns | array | N | From: launcher/schemas/neo4j_export/rels_run_has_service_candidate.schema.json |
| path | string | N | From: launcher/schemas/neo4j_export/nodes_runs.schema.json |
| path | string | N | From: launcher/schemas/neo4j_export/nodes_files.schema.json |
| path | string | N | From: launcher/schemas/neo4j_export/nodes_pdf_pages.schema.json |
| path | string | N | From: launcher/schemas/neo4j_export/nodes_transcript_atoms.schema.json |
| path | string | N | From: launcher/schemas/neo4j_export/nodes_authority_candidates.schema.json |
| path | string | N | From: launcher/schemas/neo4j_export/nodes_service_candidates.schema.json |
| path | string | N | From: launcher/schemas/neo4j_export/rels_run_has_file.schema.json |
| path | string | N | From: launcher/schemas/neo4j_export/rels_file_has_pdf_page.schema.json |
| path | string | N | From: launcher/schemas/neo4j_export/rels_file_has_transcript_atom.schema.json |
| path | string | N | From: launcher/schemas/neo4j_export/rels_run_has_authority_candidate.schema.json |
| path | string | N | From: launcher/schemas/neo4j_export/rels_run_has_service_candidate.schema.json |
| required_columns | array | N | From: launcher/schemas/neo4j_export/nodes_runs.schema.json |
| required_columns | array | N | From: launcher/schemas/neo4j_export/nodes_files.schema.json |
| required_columns | array | N | From: launcher/schemas/neo4j_export/nodes_pdf_pages.schema.json |
| required_columns | array | N | From: launcher/schemas/neo4j_export/nodes_transcript_atoms.schema.json |
| required_columns | array | N | From: launcher/schemas/neo4j_export/nodes_authority_candidates.schema.json |
| required_columns | array | N | From: launcher/schemas/neo4j_export/nodes_service_candidates.schema.json |
| required_columns | array | N | From: launcher/schemas/neo4j_export/rels_run_has_file.schema.json |
| required_columns | array | N | From: launcher/schemas/neo4j_export/rels_file_has_pdf_page.schema.json |
| required_columns | array | N | From: launcher/schemas/neo4j_export/rels_file_has_transcript_atom.schema.json |
| required_columns | array | N | From: launcher/schemas/neo4j_export/rels_run_has_authority_candidate.schema.json |
| required_columns | array | N | From: launcher/schemas/neo4j_export/rels_run_has_service_candidate.schema.json |
| typed_columns | object | N | From: launcher/schemas/neo4j_export/nodes_runs.schema.json |
| typed_columns | object | N | From: launcher/schemas/neo4j_export/nodes_files.schema.json |
| typed_columns | object | N | From: launcher/schemas/neo4j_export/nodes_pdf_pages.schema.json |
| typed_columns | object | N | From: launcher/schemas/neo4j_export/nodes_transcript_atoms.schema.json |
| typed_columns | object | N | From: launcher/schemas/neo4j_export/nodes_authority_candidates.schema.json |
| typed_columns | object | N | From: launcher/schemas/neo4j_export/nodes_service_candidates.schema.json |
| typed_columns | object | N | From: launcher/schemas/neo4j_export/rels_run_has_file.schema.json |
| typed_columns | object | N | From: launcher/schemas/neo4j_export/rels_file_has_pdf_page.schema.json |
| typed_columns | object | N | From: launcher/schemas/neo4j_export/rels_file_has_transcript_atom.schema.json |
| typed_columns | object | N | From: launcher/schemas/neo4j_export/rels_run_has_authority_candidate.schema.json |
| typed_columns | object | N | From: launcher/schemas/neo4j_export/rels_run_has_service_candidate.schema.json |

## EXTRACTED_LitigationOS Neo4j edges_csv row

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: LitigationOS Neo4j edges.csv row  
**Primary Key:** extracted_litigationos neo4j edges_csv row_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_litigationos neo4j edges_csv row_id | ulid | Y | Primary key. |
| authority_path | string|null | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/contracts/edges_row.schema.json |
| authority_path | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/contracts/edges_row.schema.json |
| authority_path | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0007/SCHEMA/contracts/edges_row.schema.json |
| authority_path | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/contracts/edges_row.schema.json |
| authority_pinpoint | string|null | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/contracts/edges_row.schema.json |
| authority_pinpoint | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/contracts/edges_row.schema.json |
| authority_pinpoint | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0007/SCHEMA/contracts/edges_row.schema.json |
| authority_pinpoint | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/contracts/edges_row.schema.json |
| case_id | string|null | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/contracts/edges_row.schema.json |
| case_id | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/contracts/edges_row.schema.json |
| case_id | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0007/SCHEMA/contracts/edges_row.schema.json |
| case_id | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/contracts/edges_row.schema.json |
| end_id | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/contracts/edges_row.schema.json |
| end_id | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/contracts/edges_row.schema.json |
| end_id | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0007/SCHEMA/contracts/edges_row.schema.json |
| end_id | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/contracts/edges_row.schema.json |
| evidence_locator | string|null | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/contracts/edges_row.schema.json |
| evidence_locator | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/contracts/edges_row.schema.json |
| evidence_locator | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0007/SCHEMA/contracts/edges_row.schema.json |
| evidence_locator | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/contracts/edges_row.schema.json |
| evidence_path | string|null | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/contracts/edges_row.schema.json |
| evidence_path | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/contracts/edges_row.schema.json |
| evidence_path | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0007/SCHEMA/contracts/edges_row.schema.json |
| evidence_path | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/contracts/edges_row.schema.json |
| start_id | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/contracts/edges_row.schema.json |
| start_id | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/contracts/edges_row.schema.json |
| start_id | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0007/SCHEMA/contracts/edges_row.schema.json |
| start_id | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/contracts/edges_row.schema.json |
| track | string|null | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/contracts/edges_row.schema.json |
| track | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/contracts/edges_row.schema.json |
| track | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0007/SCHEMA/contracts/edges_row.schema.json |
| track | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/contracts/edges_row.schema.json |
| type | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/contracts/edges_row.schema.json |
| type | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/contracts/edges_row.schema.json |
| type | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0007/SCHEMA/contracts/edges_row.schema.json |
| type | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/contracts/edges_row.schema.json |

## EXTRACTED_LitigationOS Neo4j nodes_csv row

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: LitigationOS Neo4j nodes.csv row  
**Primary Key:** extracted_litigationos neo4j nodes_csv row_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_litigationos neo4j nodes_csv row_id | ulid | Y | Primary key. |
| case_id | string|null | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/contracts/nodes_row.schema.json |
| case_id | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/contracts/nodes_row.schema.json |
| case_id | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0007/SCHEMA/contracts/nodes_row.schema.json |
| case_id | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/contracts/nodes_row.schema.json |
| created_utc | string|null | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/contracts/nodes_row.schema.json |
| created_utc | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/contracts/nodes_row.schema.json |
| created_utc | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0007/SCHEMA/contracts/nodes_row.schema.json |
| created_utc | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/contracts/nodes_row.schema.json |
| id | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/contracts/nodes_row.schema.json |
| id | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/contracts/nodes_row.schema.json |
| id | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0007/SCHEMA/contracts/nodes_row.schema.json |
| id | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/contracts/nodes_row.schema.json |
| labels | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/contracts/nodes_row.schema.json |
| labels | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/contracts/nodes_row.schema.json |
| labels | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0007/SCHEMA/contracts/nodes_row.schema.json |
| labels | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/contracts/nodes_row.schema.json |
| source_locator | string|null | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/contracts/nodes_row.schema.json |
| source_locator | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/contracts/nodes_row.schema.json |
| source_locator | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0007/SCHEMA/contracts/nodes_row.schema.json |
| source_locator | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/contracts/nodes_row.schema.json |
| source_path | string|null | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/contracts/nodes_row.schema.json |
| source_path | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/contracts/nodes_row.schema.json |
| source_path | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0007/SCHEMA/contracts/nodes_row.schema.json |
| source_path | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/contracts/nodes_row.schema.json |
| track | string|null | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/contracts/nodes_row.schema.json |
| track | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/contracts/nodes_row.schema.json |
| track | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0007/SCHEMA/contracts/nodes_row.schema.json |
| track | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/contracts/nodes_row.schema.json |
| updated_utc | string|null | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/contracts/nodes_row.schema.json |
| updated_utc | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/contracts/nodes_row.schema.json |
| updated_utc | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0007/SCHEMA/contracts/nodes_row.schema.json |
| updated_utc | string|null | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/SCHEMA/contracts/nodes_row.schema.json |

## EXTRACTED_MI_HC_ZIP_ExecutionPlan

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: MI_HC_ZIP_ExecutionPlan  
**Primary Key:** extracted_mi_hc_zip_executionplan_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_mi_hc_zip_executionplan_id | ulid | Y | Primary key. |
| inputs | object | N | From: addendum/schemas/execution_plan.schema.json |
| plan_version | string | N | From: addendum/schemas/execution_plan.schema.json |
| run_mode | string | N | From: addendum/schemas/execution_plan.schema.json |
| stages | array | N | From: addendum/schemas/execution_plan.schema.json |

## EXTRACTED_Micro_Batch_1___Codex_Nodes__data_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: Micro-Batch_1___Codex_Nodes__data.csv  
**Primary Key:** extracted_micro_batch_1___codex_nodes__data_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_micro_batch_1___codex_nodes__data_csv_id | ulid | Y | Primary key. |
| id | text | N | From: eternal/nodes/Micro-Batch_1___Codex_Nodes__data.csv |
| id | text | N | From: eternal/edges/Micro-Batch_1___Codex_Nodes__data.csv |
| id | text | N | From: eternal/neo4j_import/Micro-Batch_1___Codex_Nodes__data.csv |
| label | text | N | From: eternal/nodes/Micro-Batch_1___Codex_Nodes__data.csv |
| label | text | N | From: eternal/edges/Micro-Batch_1___Codex_Nodes__data.csv |
| label | text | N | From: eternal/neo4j_import/Micro-Batch_1___Codex_Nodes__data.csv |
| source_file | text | N | From: eternal/nodes/Micro-Batch_1___Codex_Nodes__data.csv |
| source_file | text | N | From: eternal/edges/Micro-Batch_1___Codex_Nodes__data.csv |
| source_file | text | N | From: eternal/neo4j_import/Micro-Batch_1___Codex_Nodes__data.csv |

## EXTRACTED_Micro_Batches_11_13___Codex_Nodes__data_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: Micro-Batches_11_13___Codex_Nodes__data.csv  
**Primary Key:** extracted_micro_batches_11_13___codex_nodes__data_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_micro_batches_11_13___codex_nodes__data_csv_id | ulid | Y | Primary key. |
| id | text | N | From: eternal/nodes/Micro-Batches_11_13___Codex_Nodes__data.csv |
| id | text | N | From: eternal/edges/Micro-Batches_11_13___Codex_Nodes__data.csv |
| id | text | N | From: eternal/neo4j_import/Micro-Batches_11_13___Codex_Nodes__data.csv |
| label | text | N | From: eternal/nodes/Micro-Batches_11_13___Codex_Nodes__data.csv |
| label | text | N | From: eternal/edges/Micro-Batches_11_13___Codex_Nodes__data.csv |
| label | text | N | From: eternal/neo4j_import/Micro-Batches_11_13___Codex_Nodes__data.csv |
| source_file | text | N | From: eternal/nodes/Micro-Batches_11_13___Codex_Nodes__data.csv |
| source_file | text | N | From: eternal/edges/Micro-Batches_11_13___Codex_Nodes__data.csv |
| source_file | text | N | From: eternal/neo4j_import/Micro-Batches_11_13___Codex_Nodes__data.csv |

## EXTRACTED_Micro_Batches_14_16___Codex_Nodes__data_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: Micro-Batches_14_16___Codex_Nodes__data.csv  
**Primary Key:** extracted_micro_batches_14_16___codex_nodes__data_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_micro_batches_14_16___codex_nodes__data_csv_id | ulid | Y | Primary key. |
| id | text | N | From: eternal/nodes/Micro-Batches_14_16___Codex_Nodes__data.csv |
| id | text | N | From: eternal/edges/Micro-Batches_14_16___Codex_Nodes__data.csv |
| id | text | N | From: eternal/neo4j_import/Micro-Batches_14_16___Codex_Nodes__data.csv |
| label | text | N | From: eternal/nodes/Micro-Batches_14_16___Codex_Nodes__data.csv |
| label | text | N | From: eternal/edges/Micro-Batches_14_16___Codex_Nodes__data.csv |
| label | text | N | From: eternal/neo4j_import/Micro-Batches_14_16___Codex_Nodes__data.csv |
| source_file | text | N | From: eternal/nodes/Micro-Batches_14_16___Codex_Nodes__data.csv |
| source_file | text | N | From: eternal/edges/Micro-Batches_14_16___Codex_Nodes__data.csv |
| source_file | text | N | From: eternal/neo4j_import/Micro-Batches_14_16___Codex_Nodes__data.csv |

## EXTRACTED_Micro_Batches_17_19___Codex_Nodes__data_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: Micro-Batches_17_19___Codex_Nodes__data.csv  
**Primary Key:** extracted_micro_batches_17_19___codex_nodes__data_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_micro_batches_17_19___codex_nodes__data_csv_id | ulid | Y | Primary key. |
| id | text | N | From: eternal/nodes/Micro-Batches_17_19___Codex_Nodes__data.csv |
| id | text | N | From: eternal/edges/Micro-Batches_17_19___Codex_Nodes__data.csv |
| id | text | N | From: eternal/neo4j_import/Micro-Batches_17_19___Codex_Nodes__data.csv |
| label | text | N | From: eternal/nodes/Micro-Batches_17_19___Codex_Nodes__data.csv |
| label | text | N | From: eternal/edges/Micro-Batches_17_19___Codex_Nodes__data.csv |
| label | text | N | From: eternal/neo4j_import/Micro-Batches_17_19___Codex_Nodes__data.csv |
| source_file | text | N | From: eternal/nodes/Micro-Batches_17_19___Codex_Nodes__data.csv |
| source_file | text | N | From: eternal/edges/Micro-Batches_17_19___Codex_Nodes__data.csv |
| source_file | text | N | From: eternal/neo4j_import/Micro-Batches_17_19___Codex_Nodes__data.csv |

## EXTRACTED_Micro_Batches_2_4___Codex_Nodes__data_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: Micro-Batches_2_4___Codex_Nodes__data.csv  
**Primary Key:** extracted_micro_batches_2_4___codex_nodes__data_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_micro_batches_2_4___codex_nodes__data_csv_id | ulid | Y | Primary key. |
| id | text | N | From: eternal/nodes/Micro-Batches_2_4___Codex_Nodes__data.csv |
| id | text | N | From: eternal/edges/Micro-Batches_2_4___Codex_Nodes__data.csv |
| id | text | N | From: eternal/neo4j_import/Micro-Batches_2_4___Codex_Nodes__data.csv |
| label | text | N | From: eternal/nodes/Micro-Batches_2_4___Codex_Nodes__data.csv |
| label | text | N | From: eternal/edges/Micro-Batches_2_4___Codex_Nodes__data.csv |
| label | text | N | From: eternal/neo4j_import/Micro-Batches_2_4___Codex_Nodes__data.csv |
| source_file | text | N | From: eternal/nodes/Micro-Batches_2_4___Codex_Nodes__data.csv |
| source_file | text | N | From: eternal/edges/Micro-Batches_2_4___Codex_Nodes__data.csv |
| source_file | text | N | From: eternal/neo4j_import/Micro-Batches_2_4___Codex_Nodes__data.csv |

## EXTRACTED_Micro_Batches_5_7___Codex_Nodes__data_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: Micro-Batches_5_7___Codex_Nodes__data.csv  
**Primary Key:** extracted_micro_batches_5_7___codex_nodes__data_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_micro_batches_5_7___codex_nodes__data_csv_id | ulid | Y | Primary key. |
| id | text | N | From: eternal/nodes/Micro-Batches_5_7___Codex_Nodes__data.csv |
| id | text | N | From: eternal/edges/Micro-Batches_5_7___Codex_Nodes__data.csv |
| id | text | N | From: eternal/neo4j_import/Micro-Batches_5_7___Codex_Nodes__data.csv |
| label | text | N | From: eternal/nodes/Micro-Batches_5_7___Codex_Nodes__data.csv |
| label | text | N | From: eternal/edges/Micro-Batches_5_7___Codex_Nodes__data.csv |
| label | text | N | From: eternal/neo4j_import/Micro-Batches_5_7___Codex_Nodes__data.csv |
| source_file | text | N | From: eternal/nodes/Micro-Batches_5_7___Codex_Nodes__data.csv |
| source_file | text | N | From: eternal/edges/Micro-Batches_5_7___Codex_Nodes__data.csv |
| source_file | text | N | From: eternal/neo4j_import/Micro-Batches_5_7___Codex_Nodes__data.csv |

## EXTRACTED_Micro_Batches_8_10___Codex_Nodes__data_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: Micro-Batches_8_10___Codex_Nodes__data.csv  
**Primary Key:** extracted_micro_batches_8_10___codex_nodes__data_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_micro_batches_8_10___codex_nodes__data_csv_id | ulid | Y | Primary key. |
| id | text | N | From: eternal/nodes/Micro-Batches_8_10___Codex_Nodes__data.csv |
| id | text | N | From: eternal/edges/Micro-Batches_8_10___Codex_Nodes__data.csv |
| id | text | N | From: eternal/neo4j_import/Micro-Batches_8_10___Codex_Nodes__data.csv |
| label | text | N | From: eternal/nodes/Micro-Batches_8_10___Codex_Nodes__data.csv |
| label | text | N | From: eternal/edges/Micro-Batches_8_10___Codex_Nodes__data.csv |
| label | text | N | From: eternal/neo4j_import/Micro-Batches_8_10___Codex_Nodes__data.csv |
| source_file | text | N | From: eternal/nodes/Micro-Batches_8_10___Codex_Nodes__data.csv |
| source_file | text | N | From: eternal/edges/Micro-Batches_8_10___Codex_Nodes__data.csv |
| source_file | text | N | From: eternal/neo4j_import/Micro-Batches_8_10___Codex_Nodes__data.csv |

## EXTRACTED_MindEye2_violation_to_remedy (1)__codex_json_csv_extracted_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: MindEye2_violation_to_remedy (1)__codex_json_csv_extracted.csv  
**Primary Key:** extracted_mindeye2_violation_to_remedy (1)__codex_json_csv_extracted_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_mindeye2_violation_to_remedy (1)__codex_json_csv_extracted_csv_id | ulid | Y | Primary key. |
| remedy_category | text | N | From: eternal/nodes/MindEye2_violation_to_remedy (1)__codex_json_csv_extracted.csv |
| remedy_category | text | N | From: eternal/edges/MindEye2_violation_to_remedy (1)__codex_json_csv_extracted.csv |
| remedy_category | text | N | From: eternal/neo4j_import/MindEye2_violation_to_remedy (1)__codex_json_csv_extracted.csv |
| remedy_label | text | N | From: eternal/nodes/MindEye2_violation_to_remedy (1)__codex_json_csv_extracted.csv |
| remedy_label | text | N | From: eternal/edges/MindEye2_violation_to_remedy (1)__codex_json_csv_extracted.csv |
| remedy_label | text | N | From: eternal/neo4j_import/MindEye2_violation_to_remedy (1)__codex_json_csv_extracted.csv |
| violation_id | text | N | From: eternal/nodes/MindEye2_violation_to_remedy (1)__codex_json_csv_extracted.csv |
| violation_id | text | N | From: eternal/edges/MindEye2_violation_to_remedy (1)__codex_json_csv_extracted.csv |
| violation_id | text | N | From: eternal/neo4j_import/MindEye2_violation_to_remedy (1)__codex_json_csv_extracted.csv |
| violation_label | text | N | From: eternal/nodes/MindEye2_violation_to_remedy (1)__codex_json_csv_extracted.csv |
| violation_label | text | N | From: eternal/edges/MindEye2_violation_to_remedy (1)__codex_json_csv_extracted.csv |
| violation_label | text | N | From: eternal/neo4j_import/MindEye2_violation_to_remedy (1)__codex_json_csv_extracted.csv |

## EXTRACTED_MindEye2_violation_to_remedy__codex_json_csv_extracted_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: MindEye2_violation_to_remedy__codex_json_csv_extracted.csv  
**Primary Key:** extracted_mindeye2_violation_to_remedy__codex_json_csv_extracted_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_mindeye2_violation_to_remedy__codex_json_csv_extracted_csv_id | ulid | Y | Primary key. |
| remedy_category | text | N | From: eternal/nodes/MindEye2_violation_to_remedy__codex_json_csv_extracted.csv |
| remedy_category | text | N | From: eternal/edges/MindEye2_violation_to_remedy__codex_json_csv_extracted.csv |
| remedy_category | text | N | From: eternal/neo4j_import/MindEye2_violation_to_remedy__codex_json_csv_extracted.csv |
| remedy_label | text | N | From: eternal/nodes/MindEye2_violation_to_remedy__codex_json_csv_extracted.csv |
| remedy_label | text | N | From: eternal/edges/MindEye2_violation_to_remedy__codex_json_csv_extracted.csv |
| remedy_label | text | N | From: eternal/neo4j_import/MindEye2_violation_to_remedy__codex_json_csv_extracted.csv |
| violation_id | text | N | From: eternal/nodes/MindEye2_violation_to_remedy__codex_json_csv_extracted.csv |
| violation_id | text | N | From: eternal/edges/MindEye2_violation_to_remedy__codex_json_csv_extracted.csv |
| violation_id | text | N | From: eternal/neo4j_import/MindEye2_violation_to_remedy__codex_json_csv_extracted.csv |
| violation_label | text | N | From: eternal/nodes/MindEye2_violation_to_remedy__codex_json_csv_extracted.csv |
| violation_label | text | N | From: eternal/edges/MindEye2_violation_to_remedy__codex_json_csv_extracted.csv |
| violation_label | text | N | From: eternal/neo4j_import/MindEye2_violation_to_remedy__codex_json_csv_extracted.csv |

## EXTRACTED_Parsed_JSON_Nodes_from_Git_Dataset__data_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: Parsed_JSON_Nodes_from_Git_Dataset__data.csv  
**Primary Key:** extracted_parsed_json_nodes_from_git_dataset__data_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_parsed_json_nodes_from_git_dataset__data_csv_id | ulid | Y | Primary key. |
| id | text | N | From: eternal/nodes/Parsed_JSON_Nodes_from_Git_Dataset__data.csv |
| id | text | N | From: eternal/edges/Parsed_JSON_Nodes_from_Git_Dataset__data.csv |
| id | text | N | From: eternal/neo4j_import/Parsed_JSON_Nodes_from_Git_Dataset__data.csv |
| label | text | N | From: eternal/nodes/Parsed_JSON_Nodes_from_Git_Dataset__data.csv |
| label | text | N | From: eternal/edges/Parsed_JSON_Nodes_from_Git_Dataset__data.csv |
| label | text | N | From: eternal/neo4j_import/Parsed_JSON_Nodes_from_Git_Dataset__data.csv |
| source_file | text | N | From: eternal/nodes/Parsed_JSON_Nodes_from_Git_Dataset__data.csv |
| source_file | text | N | From: eternal/edges/Parsed_JSON_Nodes_from_Git_Dataset__data.csv |
| source_file | text | N | From: eternal/neo4j_import/Parsed_JSON_Nodes_from_Git_Dataset__data.csv |

## EXTRACTED_Procedural_Edges___Synthesized__data_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: Procedural_Edges___Synthesized__data.csv  
**Primary Key:** extracted_procedural_edges___synthesized__data_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_procedural_edges___synthesized__data_csv_id | ulid | Y | Primary key. |
| label | text | N | From: eternal/nodes/Procedural_Edges___Synthesized__data.csv |
| label | text | N | From: eternal/edges/Procedural_Edges___Synthesized__data.csv |
| label | text | N | From: eternal/neo4j_import/Procedural_Edges___Synthesized__data.csv |
| reason | text | N | From: eternal/nodes/Procedural_Edges___Synthesized__data.csv |
| reason | text | N | From: eternal/edges/Procedural_Edges___Synthesized__data.csv |
| reason | text | N | From: eternal/neo4j_import/Procedural_Edges___Synthesized__data.csv |
| source | text | N | From: eternal/nodes/Procedural_Edges___Synthesized__data.csv |
| source | text | N | From: eternal/edges/Procedural_Edges___Synthesized__data.csv |
| source | text | N | From: eternal/neo4j_import/Procedural_Edges___Synthesized__data.csv |
| target | text | N | From: eternal/nodes/Procedural_Edges___Synthesized__data.csv |
| target | text | N | From: eternal/edges/Procedural_Edges___Synthesized__data.csv |
| target | text | N | From: eternal/neo4j_import/Procedural_Edges___Synthesized__data.csv |

## EXTRACTED_ProofObligation

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: ProofObligation  
**Primary Key:** extracted_proofobligation_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_proofobligation_id | ulid | Y | Primary key. |
| artifact_kind | string | N | From: launcher/schemas/proof_obligation.schema.json |
| assurance | number | N | From: launcher/schemas/proof_obligation.schema.json |
| authority_refs | array | N | From: launcher/schemas/proof_obligation.schema.json |
| evidence_refs | array | N | From: launcher/schemas/proof_obligation.schema.json |
| po_id | string | N | From: launcher/schemas/proof_obligation.schema.json |
| proposition | string | N | From: launcher/schemas/proof_obligation.schema.json |
| status | string | N | From: launcher/schemas/proof_obligation.schema.json |
| validator | string | N | From: launcher/schemas/proof_obligation.schema.json |

## EXTRACTED_QuoteLedgerEntry

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: QuoteLedgerEntry  
**Primary Key:** extracted_quoteledgerentry_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_quoteledgerentry_id | ulid | Y | Primary key. |
| loc | string | N | From: launcher/schemas/quote_ledger.schema.json |
| quote_id | string | N | From: launcher/schemas/quote_ledger.schema.json |
| source_pointer | string | N | From: launcher/schemas/quote_ledger.schema.json |
| tags | array | N | From: launcher/schemas/quote_ledger.schema.json |
| text | string | N | From: launcher/schemas/quote_ledger.schema.json |
| ts_utc | string | N | From: launcher/schemas/quote_ledger.schema.json |
| verified | boolean | N | From: launcher/schemas/quote_ledger.schema.json |

## EXTRACTED_RecordSpineEvent

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: RecordSpineEvent  
**Primary Key:** extracted_recordspineevent_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_recordspineevent_id | ulid | Y | Primary key. |
| case_id | string | N | From: launcher/schemas/record_spine_event.schema.json |
| event_id | string | N | From: launcher/schemas/record_spine_event.schema.json |
| event_type | string | N | From: launcher/schemas/record_spine_event.schema.json |
| loc | string | N | From: launcher/schemas/record_spine_event.schema.json |
| meta | object | N | From: launcher/schemas/record_spine_event.schema.json |
| source_ref | string | N | From: launcher/schemas/record_spine_event.schema.json |
| summary | string | N | From: launcher/schemas/record_spine_event.schema.json |
| ts_utc | string | N | From: launcher/schemas/record_spine_event.schema.json |

## EXTRACTED_action_row

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: action_row  
**Primary Key:** extracted_action_row_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_action_row_id | ulid | Y | Primary key. |
| action_id | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/action_row.schema.json |
| action_id | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/action_row.schema.json |
| created_utc | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/action_row.schema.json |
| created_utc | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/action_row.schema.json |
| depends_on_gates | array | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/action_row.schema.json |
| depends_on_gates | array | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/action_row.schema.json |
| description | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/action_row.schema.json |
| description | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/action_row.schema.json |
| priority | integer | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/action_row.schema.json |
| priority | integer | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/action_row.schema.json |
| supports_deltas | array | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/action_row.schema.json |
| supports_deltas | array | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/action_row.schema.json |
| title | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/action_row.schema.json |
| title | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/action_row.schema.json |

## EXTRACTED_atom_row

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: atom_row  
**Primary Key:** extracted_atom_row_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_atom_row_id | ulid | Y | Primary key. |
| atom_id | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/atom_row.schema.json |
| atom_id | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/atom_row.schema.json |
| atom_type | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/atom_row.schema.json |
| atom_type | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/atom_row.schema.json |
| confidence | integer | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/atom_row.schema.json |
| confidence | integer | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/atom_row.schema.json |
| created_utc | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/atom_row.schema.json |
| created_utc | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/atom_row.schema.json |
| source_locator | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/atom_row.schema.json |
| source_locator | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/atom_row.schema.json |
| source_path | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/atom_row.schema.json |
| source_path | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/atom_row.schema.json |
| tags | array | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/atom_row.schema.json |
| tags | array | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/atom_row.schema.json |
| text | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/atom_row.schema.json |
| text | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/atom_row.schema.json |
| track | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/atom_row.schema.json |
| track | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/atom_row.schema.json |

## EXTRACTED_authority_graph_nodeid_to_authorityid_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: authority_graph_nodeid_to_authorityid.csv  
**Primary Key:** extracted_authority_graph_nodeid_to_authorityid_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_authority_graph_nodeid_to_authorityid_csv_id | ulid | Y | Primary key. |
| authority_id | text | N | From: cyclepacks/authority/data/authority_graph_nodeid_to_authorityid.csv |
| authority_id | text | N | From: cyclepacks/authority_merge/data/authority_graph_nodeid_to_authorityid.csv |
| source_node_id | text | N | From: cyclepacks/authority/data/authority_graph_nodeid_to_authorityid.csv |
| source_node_id | text | N | From: cyclepacks/authority_merge/data/authority_graph_nodeid_to_authorityid.csv |

## EXTRACTED_authority_graph_nodes_normalized_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: authority_graph_nodes_normalized.csv  
**Primary Key:** extracted_authority_graph_nodes_normalized_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_authority_graph_nodes_normalized_csv_id | ulid | Y | Primary key. |
| authority_id | text | N | From: cyclepacks/authority/data/authority_graph_nodes_normalized.csv |
| authority_id | text | N | From: cyclepacks/authority_merge/data/authority_graph_nodes_normalized.csv |
| authority_type | text | N | From: cyclepacks/authority/data/authority_graph_nodes_normalized.csv |
| authority_type | text | N | From: cyclepacks/authority_merge/data/authority_graph_nodes_normalized.csv |
| citation | text | N | From: cyclepacks/authority/data/authority_graph_nodes_normalized.csv |
| citation | text | N | From: cyclepacks/authority_merge/data/authority_graph_nodes_normalized.csv |
| source_node_id | text | N | From: cyclepacks/authority/data/authority_graph_nodes_normalized.csv |
| source_node_id | text | N | From: cyclepacks/authority_merge/data/authority_graph_nodes_normalized.csv |
| version | text | N | From: cyclepacks/authority/data/authority_graph_nodes_normalized.csv |
| version | text | N | From: cyclepacks/authority_merge/data/authority_graph_nodes_normalized.csv |

## EXTRACTED_authority_triples_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: authority_triples.csv  
**Primary Key:** extracted_authority_triples_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_authority_triples_csv_id | ulid | Y | Primary key. |
| authority_id | text | N | From: cyclepacks/authority/data/authority_triples.csv |
| authority_id | text | N | From: cyclepacks/authority_merge/data/authority_triples.csv |
| authority_type | text | N | From: cyclepacks/authority/data/authority_triples.csv |
| authority_type | text | N | From: cyclepacks/authority_merge/data/authority_triples.csv |
| citation | text | N | From: cyclepacks/authority/data/authority_triples.csv |
| citation | text | N | From: cyclepacks/authority_merge/data/authority_triples.csv |
| pinpoint | text | N | From: cyclepacks/authority/data/authority_triples.csv |
| pinpoint | text | N | From: cyclepacks/authority_merge/data/authority_triples.csv |
| proposition | text | N | From: cyclepacks/authority/data/authority_triples.csv |
| proposition | text | N | From: cyclepacks/authority_merge/data/authority_triples.csv |
| prov_activity | text | N | From: cyclepacks/authority/data/authority_triples.csv |
| prov_activity | text | N | From: cyclepacks/authority_merge/data/authority_triples.csv |
| source_row_id | text | N | From: cyclepacks/authority/data/authority_triples.csv |
| source_row_id | text | N | From: cyclepacks/authority_merge/data/authority_triples.csv |
| supporting_shard_id | text | N | From: cyclepacks/authority/data/authority_triples.csv |
| supporting_shard_id | text | N | From: cyclepacks/authority_merge/data/authority_triples.csv |
| triple_id | text | N | From: cyclepacks/authority/data/authority_triples.csv |
| triple_id | text | N | From: cyclepacks/authority_merge/data/authority_triples.csv |

## EXTRACTED_court_rules_zip_manifest_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: court_rules_zip_manifest.csv  
**Primary Key:** extracted_court_rules_zip_manifest_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_court_rules_zip_manifest_csv_id | ulid | Y | Primary key. |
| bytes | text | N | From: addendum/court_rules_zip_manifest.csv |
| crc32_hex | text | N | From: addendum/court_rules_zip_manifest.csv |
| entry | text | N | From: addendum/court_rules_zip_manifest.csv |
| ext | text | N | From: addendum/court_rules_zip_manifest.csv |
| integrity_key | text | N | From: addendum/court_rules_zip_manifest.csv |
| mtime | text | N | From: addendum/court_rules_zip_manifest.csv |
| zip_file | text | N | From: addendum/court_rules_zip_manifest.csv |

## EXTRACTED_court_rules_zip_validity_findings_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: court_rules_zip_validity_findings.csv  
**Primary Key:** extracted_court_rules_zip_validity_findings_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_court_rules_zip_validity_findings_csv_id | ulid | Y | Primary key. |
| entry | text | N | From: addendum/court_rules_zip_validity_findings.csv |
| ext | text | N | From: addendum/court_rules_zip_validity_findings.csv |
| issue | text | N | From: addendum/court_rules_zip_validity_findings.csv |
| zip_file | text | N | From: addendum/court_rules_zip_validity_findings.csv |

## EXTRACTED_delta_row

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: delta_row  
**Primary Key:** extracted_delta_row_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_delta_row_id | ulid | Y | Primary key. |
| created_utc | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/delta_row.schema.json |
| created_utc | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/delta_row.schema.json |
| delta_id | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/delta_row.schema.json |
| delta_id | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/delta_row.schema.json |
| description | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/delta_row.schema.json |
| description | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/delta_row.schema.json |
| priority | integer | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/delta_row.schema.json |
| priority | integer | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/delta_row.schema.json |
| supporting_atoms | array | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/delta_row.schema.json |
| supporting_atoms | array | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/delta_row.schema.json |
| supporting_signals | array | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/delta_row.schema.json |
| supporting_signals | array | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/delta_row.schema.json |
| theme | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/delta_row.schema.json |
| theme | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/delta_row.schema.json |

## EXTRACTED_edges:authorities_xref

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: edges:authorities_xref  
**Primary Key:** extracted_edges:authorities_xref_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_edges:authorities_xref_id | ulid | Y | Primary key. |
| :END_ID | text | N | From: cyclepacks/authority/sources/original/edges_authorities_xref.csv |
| :END_ID | text | N | From: cyclepacks/authority_merge/sources/original/edges_authorities_xref.csv |
| :START_ID | text | N | From: cyclepacks/authority/sources/original/edges_authorities_xref.csv |
| :START_ID | text | N | From: cyclepacks/authority_merge/sources/original/edges_authorities_xref.csv |
| :TYPE | text | N | From: cyclepacks/authority/sources/original/edges_authorities_xref.csv |
| :TYPE | text | N | From: cyclepacks/authority_merge/sources/original/edges_authorities_xref.csv |
| relation | text | N | From: cyclepacks/authority/sources/original/edges_authorities_xref.csv |
| relation | text | N | From: cyclepacks/authority_merge/sources/original/edges_authorities_xref.csv |

## EXTRACTED_edges:authority_cross_refs

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: edges:authority_cross_refs  
**Primary Key:** extracted_edges:authority_cross_refs_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_edges:authority_cross_refs_id | ulid | Y | Primary key. |
| :END_ID(Authority) | text | N | From: cyclepacks/authority/neo4j/edges_authority_cross_refs.csv |
| :END_ID(Authority) | text | N | From: cyclepacks/authority_merge/neo4j/edges_authority_cross_refs.csv |
| :START_ID(Authority) | text | N | From: cyclepacks/authority/neo4j/edges_authority_cross_refs.csv |
| :START_ID(Authority) | text | N | From: cyclepacks/authority_merge/neo4j/edges_authority_cross_refs.csv |
| :TYPE | text | N | From: cyclepacks/authority/neo4j/edges_authority_cross_refs.csv |
| :TYPE | text | N | From: cyclepacks/authority_merge/neo4j/edges_authority_cross_refs.csv |
| relation | text | N | From: cyclepacks/authority/neo4j/edges_authority_cross_refs.csv |
| relation | text | N | From: cyclepacks/authority_merge/neo4j/edges_authority_cross_refs.csv |

## EXTRACTED_edges:authority_has_shard

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: edges:authority_has_shard  
**Primary Key:** extracted_edges:authority_has_shard_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_edges:authority_has_shard_id | ulid | Y | Primary key. |
| :END_ID(AuthorityShard) | text | N | From: cyclepacks/authority/neo4j/edges_authority_has_shard.csv |
| :END_ID(AuthorityShard) | text | N | From: cyclepacks/authority_merge/neo4j/edges_authority_has_shard.csv |
| :END_ID(AuthorityShard) | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/neo4j/edges_authority_has_shard.csv |
| :START_ID(Authority) | text | N | From: cyclepacks/authority/neo4j/edges_authority_has_shard.csv |
| :START_ID(Authority) | text | N | From: cyclepacks/authority_merge/neo4j/edges_authority_has_shard.csv |
| :START_ID(Authority) | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/neo4j/edges_authority_has_shard.csv |
| :TYPE | text | N | From: cyclepacks/authority/neo4j/edges_authority_has_shard.csv |
| :TYPE | text | N | From: cyclepacks/authority_merge/neo4j/edges_authority_has_shard.csv |
| :TYPE | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/neo4j/edges_authority_has_shard.csv |

## EXTRACTED_edges:authority_has_shard_prior

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: edges:authority_has_shard_prior  
**Primary Key:** extracted_edges:authority_has_shard_prior_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_edges:authority_has_shard_prior_id | ulid | Y | Primary key. |
| :END_ID(AuthorityShard) | text | N | From: cyclepacks/authority/neo4j/edges_authority_has_shard_prior.csv |
| :END_ID(AuthorityShard) | text | N | From: cyclepacks/authority_merge/neo4j/edges_authority_has_shard_prior.csv |
| :START_ID(Authority) | text | N | From: cyclepacks/authority/neo4j/edges_authority_has_shard_prior.csv |
| :START_ID(Authority) | text | N | From: cyclepacks/authority_merge/neo4j/edges_authority_has_shard_prior.csv |
| :TYPE | text | N | From: cyclepacks/authority/neo4j/edges_authority_has_shard_prior.csv |
| :TYPE | text | N | From: cyclepacks/authority_merge/neo4j/edges_authority_has_shard_prior.csv |

## EXTRACTED_edges:statement_asserts_fact

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: edges:statement_asserts_fact  
**Primary Key:** extracted_edges:statement_asserts_fact_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_edges:statement_asserts_fact_id | ulid | Y | Primary key. |
| :END_ID(FactClaim) | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/neo4j/edges_statement_asserts_fact.csv |
| :START_ID(Statement) | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/neo4j/edges_statement_asserts_fact.csv |
| :TYPE | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/neo4j/edges_statement_asserts_fact.csv |

## EXTRACTED_edges_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: edges.csv  
**Primary Key:** extracted_edges_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_edges_csv_id | ulid | Y | Primary key. |
| authority_path | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040421_UTC_86c87087/graph/edges.csv |
| authority_path | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040457_UTC_fff97690/graph/edges.csv |
| authority_path | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040524_UTC_7678222f/graph/edges.csv |
| authority_path | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040948_UTC_041fb7cb/graph/edges.csv |
| authority_path | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_041049_UTC_094c5afd/graph/edges.csv |
| authority_pinpoint | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040421_UTC_86c87087/graph/edges.csv |
| authority_pinpoint | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040457_UTC_fff97690/graph/edges.csv |
| authority_pinpoint | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040524_UTC_7678222f/graph/edges.csv |
| authority_pinpoint | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040948_UTC_041fb7cb/graph/edges.csv |
| authority_pinpoint | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_041049_UTC_094c5afd/graph/edges.csv |
| case_id | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040421_UTC_86c87087/graph/edges.csv |
| case_id | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040457_UTC_fff97690/graph/edges.csv |
| case_id | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040524_UTC_7678222f/graph/edges.csv |
| case_id | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040948_UTC_041fb7cb/graph/edges.csv |
| case_id | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_041049_UTC_094c5afd/graph/edges.csv |
| end_id | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040421_UTC_86c87087/graph/edges.csv |
| end_id | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040457_UTC_fff97690/graph/edges.csv |
| end_id | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040524_UTC_7678222f/graph/edges.csv |
| end_id | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040948_UTC_041fb7cb/graph/edges.csv |
| end_id | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_041049_UTC_094c5afd/graph/edges.csv |
| evidence_locator | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040421_UTC_86c87087/graph/edges.csv |
| evidence_locator | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040457_UTC_fff97690/graph/edges.csv |
| evidence_locator | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040524_UTC_7678222f/graph/edges.csv |
| evidence_locator | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040948_UTC_041fb7cb/graph/edges.csv |
| evidence_locator | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_041049_UTC_094c5afd/graph/edges.csv |
| evidence_path | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040421_UTC_86c87087/graph/edges.csv |
| evidence_path | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040457_UTC_fff97690/graph/edges.csv |
| evidence_path | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040524_UTC_7678222f/graph/edges.csv |
| evidence_path | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040948_UTC_041fb7cb/graph/edges.csv |
| evidence_path | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_041049_UTC_094c5afd/graph/edges.csv |
| start_id | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040421_UTC_86c87087/graph/edges.csv |
| start_id | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040457_UTC_fff97690/graph/edges.csv |
| start_id | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040524_UTC_7678222f/graph/edges.csv |
| start_id | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040948_UTC_041fb7cb/graph/edges.csv |
| start_id | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_041049_UTC_094c5afd/graph/edges.csv |
| track | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040421_UTC_86c87087/graph/edges.csv |
| track | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040457_UTC_fff97690/graph/edges.csv |
| track | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040524_UTC_7678222f/graph/edges.csv |
| track | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040948_UTC_041fb7cb/graph/edges.csv |
| track | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_041049_UTC_094c5afd/graph/edges.csv |
| type | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040421_UTC_86c87087/graph/edges.csv |
| type | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040457_UTC_fff97690/graph/edges.csv |
| type | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040524_UTC_7678222f/graph/edges.csv |
| type | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040948_UTC_041fb7cb/graph/edges.csv |
| type | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_041049_UTC_094c5afd/graph/edges.csv |

## EXTRACTED_eternal_graph_edges__ETERNAL_GRAPH_BUNDLE_20250902_140440_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: eternal_graph_edges__ETERNAL_GRAPH_BUNDLE_20250902_140440.csv  
**Primary Key:** extracted_eternal_graph_edges__eternal_graph_bundle_20250902_140440_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_eternal_graph_edges__eternal_graph_bundle_20250902_140440_csv_id | ulid | Y | Primary key. |
| label | text | N | From: eternal/nodes/eternal_graph_edges__ETERNAL_GRAPH_BUNDLE_20250902_140440.csv |
| label | text | N | From: eternal/edges/eternal_graph_edges__ETERNAL_GRAPH_BUNDLE_20250902_140440.csv |
| label | text | N | From: eternal/neo4j_import/eternal_graph_edges__ETERNAL_GRAPH_BUNDLE_20250902_140440.csv |
| reason | text | N | From: eternal/nodes/eternal_graph_edges__ETERNAL_GRAPH_BUNDLE_20250902_140440.csv |
| reason | text | N | From: eternal/edges/eternal_graph_edges__ETERNAL_GRAPH_BUNDLE_20250902_140440.csv |
| reason | text | N | From: eternal/neo4j_import/eternal_graph_edges__ETERNAL_GRAPH_BUNDLE_20250902_140440.csv |
| source | text | N | From: eternal/nodes/eternal_graph_edges__ETERNAL_GRAPH_BUNDLE_20250902_140440.csv |
| source | text | N | From: eternal/edges/eternal_graph_edges__ETERNAL_GRAPH_BUNDLE_20250902_140440.csv |
| source | text | N | From: eternal/neo4j_import/eternal_graph_edges__ETERNAL_GRAPH_BUNDLE_20250902_140440.csv |
| target | text | N | From: eternal/nodes/eternal_graph_edges__ETERNAL_GRAPH_BUNDLE_20250902_140440.csv |
| target | text | N | From: eternal/edges/eternal_graph_edges__ETERNAL_GRAPH_BUNDLE_20250902_140440.csv |
| target | text | N | From: eternal/neo4j_import/eternal_graph_edges__ETERNAL_GRAPH_BUNDLE_20250902_140440.csv |

## EXTRACTED_eternal_graph_edges__ETERNAL_GRAPH_CSV_JSON_COMPOSITE_20250902_141155_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: eternal_graph_edges__ETERNAL_GRAPH_CSV_JSON_COMPOSITE_20250902_141155.csv  
**Primary Key:** extracted_eternal_graph_edges__eternal_graph_csv_json_composite_20250902_141155_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_eternal_graph_edges__eternal_graph_csv_json_composite_20250902_141155_csv_id | ulid | Y | Primary key. |
| label | text | N | From: eternal/nodes/eternal_graph_edges__ETERNAL_GRAPH_CSV_JSON_COMPOSITE_20250902_141155.csv |
| label | text | N | From: eternal/edges/eternal_graph_edges__ETERNAL_GRAPH_CSV_JSON_COMPOSITE_20250902_141155.csv |
| label | text | N | From: eternal/neo4j_import/eternal_graph_edges__ETERNAL_GRAPH_CSV_JSON_COMPOSITE_20250902_141155.csv |
| reason | text | N | From: eternal/nodes/eternal_graph_edges__ETERNAL_GRAPH_CSV_JSON_COMPOSITE_20250902_141155.csv |
| reason | text | N | From: eternal/edges/eternal_graph_edges__ETERNAL_GRAPH_CSV_JSON_COMPOSITE_20250902_141155.csv |
| reason | text | N | From: eternal/neo4j_import/eternal_graph_edges__ETERNAL_GRAPH_CSV_JSON_COMPOSITE_20250902_141155.csv |
| source | text | N | From: eternal/nodes/eternal_graph_edges__ETERNAL_GRAPH_CSV_JSON_COMPOSITE_20250902_141155.csv |
| source | text | N | From: eternal/edges/eternal_graph_edges__ETERNAL_GRAPH_CSV_JSON_COMPOSITE_20250902_141155.csv |
| source | text | N | From: eternal/neo4j_import/eternal_graph_edges__ETERNAL_GRAPH_CSV_JSON_COMPOSITE_20250902_141155.csv |
| target | text | N | From: eternal/nodes/eternal_graph_edges__ETERNAL_GRAPH_CSV_JSON_COMPOSITE_20250902_141155.csv |
| target | text | N | From: eternal/edges/eternal_graph_edges__ETERNAL_GRAPH_CSV_JSON_COMPOSITE_20250902_141155.csv |
| target | text | N | From: eternal/neo4j_import/eternal_graph_edges__ETERNAL_GRAPH_CSV_JSON_COMPOSITE_20250902_141155.csv |

## EXTRACTED_eternal_graph_nodes__ETERNAL_GRAPH_BUNDLE_20250902_140440_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: eternal_graph_nodes__ETERNAL_GRAPH_BUNDLE_20250902_140440.csv  
**Primary Key:** extracted_eternal_graph_nodes__eternal_graph_bundle_20250902_140440_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_eternal_graph_nodes__eternal_graph_bundle_20250902_140440_csv_id | ulid | Y | Primary key. |
| id | text | N | From: eternal/nodes/eternal_graph_nodes__ETERNAL_GRAPH_BUNDLE_20250902_140440.csv |
| id | text | N | From: eternal/edges/eternal_graph_nodes__ETERNAL_GRAPH_BUNDLE_20250902_140440.csv |
| id | text | N | From: eternal/neo4j_import/eternal_graph_nodes__ETERNAL_GRAPH_BUNDLE_20250902_140440.csv |
| label | text | N | From: eternal/nodes/eternal_graph_nodes__ETERNAL_GRAPH_BUNDLE_20250902_140440.csv |
| label | text | N | From: eternal/edges/eternal_graph_nodes__ETERNAL_GRAPH_BUNDLE_20250902_140440.csv |
| label | text | N | From: eternal/neo4j_import/eternal_graph_nodes__ETERNAL_GRAPH_BUNDLE_20250902_140440.csv |
| source_file | text | N | From: eternal/nodes/eternal_graph_nodes__ETERNAL_GRAPH_BUNDLE_20250902_140440.csv |
| source_file | text | N | From: eternal/edges/eternal_graph_nodes__ETERNAL_GRAPH_BUNDLE_20250902_140440.csv |
| source_file | text | N | From: eternal/neo4j_import/eternal_graph_nodes__ETERNAL_GRAPH_BUNDLE_20250902_140440.csv |

## EXTRACTED_eternal_graph_nodes__ETERNAL_GRAPH_CSV_JSON_COMPOSITE_20250902_141155_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: eternal_graph_nodes__ETERNAL_GRAPH_CSV_JSON_COMPOSITE_20250902_141155.csv  
**Primary Key:** extracted_eternal_graph_nodes__eternal_graph_csv_json_composite_20250902_141155_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_eternal_graph_nodes__eternal_graph_csv_json_composite_20250902_141155_csv_id | ulid | Y | Primary key. |
| id | text | N | From: eternal/nodes/eternal_graph_nodes__ETERNAL_GRAPH_CSV_JSON_COMPOSITE_20250902_141155.csv |
| id | text | N | From: eternal/edges/eternal_graph_nodes__ETERNAL_GRAPH_CSV_JSON_COMPOSITE_20250902_141155.csv |
| id | text | N | From: eternal/neo4j_import/eternal_graph_nodes__ETERNAL_GRAPH_CSV_JSON_COMPOSITE_20250902_141155.csv |
| label | text | N | From: eternal/nodes/eternal_graph_nodes__ETERNAL_GRAPH_CSV_JSON_COMPOSITE_20250902_141155.csv |
| label | text | N | From: eternal/edges/eternal_graph_nodes__ETERNAL_GRAPH_CSV_JSON_COMPOSITE_20250902_141155.csv |
| label | text | N | From: eternal/neo4j_import/eternal_graph_nodes__ETERNAL_GRAPH_CSV_JSON_COMPOSITE_20250902_141155.csv |
| prefix | text | N | From: eternal/nodes/eternal_graph_nodes__ETERNAL_GRAPH_CSV_JSON_COMPOSITE_20250902_141155.csv |
| prefix | text | N | From: eternal/edges/eternal_graph_nodes__ETERNAL_GRAPH_CSV_JSON_COMPOSITE_20250902_141155.csv |
| prefix | text | N | From: eternal/neo4j_import/eternal_graph_nodes__ETERNAL_GRAPH_CSV_JSON_COMPOSITE_20250902_141155.csv |
| source_file | text | N | From: eternal/nodes/eternal_graph_nodes__ETERNAL_GRAPH_CSV_JSON_COMPOSITE_20250902_141155.csv |
| source_file | text | N | From: eternal/edges/eternal_graph_nodes__ETERNAL_GRAPH_CSV_JSON_COMPOSITE_20250902_141155.csv |
| source_file | text | N | From: eternal/neo4j_import/eternal_graph_nodes__ETERNAL_GRAPH_CSV_JSON_COMPOSITE_20250902_141155.csv |

## EXTRACTED_gate_row

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: gate_row  
**Primary Key:** extracted_gate_row_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_gate_row_id | ulid | Y | Primary key. |
| created_utc | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/gate_row.schema.json |
| created_utc | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/gate_row.schema.json |
| evidence | array | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/gate_row.schema.json |
| evidence | array | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/gate_row.schema.json |
| gate_id | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/gate_row.schema.json |
| gate_id | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/gate_row.schema.json |
| name | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/gate_row.schema.json |
| name | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/gate_row.schema.json |
| requirements | array | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/gate_row.schema.json |
| requirements | array | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/gate_row.schema.json |
| status | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/gate_row.schema.json |
| status | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/gate_row.schema.json |

## EXTRACTED_harvest_summary

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: harvest_summary  
**Primary Key:** extracted_harvest_summary_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_harvest_summary_id | ulid | Y | Primary key. |
| extensions | array | N | From: launcher/schemas/harvest_summary.schema.json |
| run_dir | string | N | From: launcher/schemas/harvest_summary.schema.json |
| run_id | string | N | From: launcher/schemas/harvest_summary.schema.json |
| scan | object | N | From: launcher/schemas/harvest_summary.schema.json |
| ts_utc | string | N | From: launcher/schemas/harvest_summary.schema.json |

## EXTRACTED_index_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: index.csv  
**Primary Key:** extracted_index_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_index_csv_id | ulid | Y | Primary key. |
| bytes | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/MANIFEST/index.csv |
| bytes | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0005/MANIFEST/index.csv |
| mtime_utc | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0005/MANIFEST/index.csv |
| path | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/MANIFEST/index.csv |
| path | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0005/MANIFEST/index.csv |
| sha256 | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/MANIFEST/index.csv |
| sha256 | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0005/MANIFEST/index.csv |

## EXTRACTED_invalid_rows_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: invalid_rows.csv  
**Primary Key:** extracted_invalid_rows_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_invalid_rows_csv_id | ulid | Y | Primary key. |
| errors | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040948_UTC_041fb7cb/graph/validation/invalid_rows.csv |
| errors | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_041049_UTC_094c5afd/graph/validation/invalid_rows.csv |
| file | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040948_UTC_041fb7cb/graph/validation/invalid_rows.csv |
| file | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_041049_UTC_094c5afd/graph/validation/invalid_rows.csv |
| line | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040948_UTC_041fb7cb/graph/validation/invalid_rows.csv |
| line | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_041049_UTC_094c5afd/graph/validation/invalid_rows.csv |

## EXTRACTED_job

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: job  
**Primary Key:** extracted_job_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_job_id | ulid | Y | Primary key. |
| created_utc | string | N | From: launcher/schemas/job.schema.json |
| job_id | string | N | From: launcher/schemas/job.schema.json |
| kind | string | N | From: launcher/schemas/job.schema.json |
| payload | object | N | From: launcher/schemas/job.schema.json |
| result | object|null | N | From: launcher/schemas/job.schema.json |
| status | string | N | From: launcher/schemas/job.schema.json |

## EXTRACTED_litigation_edges_cyc051_060__codex_json_csv_extracted_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: litigation_edges_cyc051-060__codex_json_csv_extracted.csv  
**Primary Key:** extracted_litigation_edges_cyc051_060__codex_json_csv_extracted_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_litigation_edges_cyc051_060__codex_json_csv_extracted_csv_id | ulid | Y | Primary key. |
| note | text | N | From: eternal/nodes/litigation_edges_cyc051-060__codex_json_csv_extracted.csv |
| note | text | N | From: eternal/edges/litigation_edges_cyc051-060__codex_json_csv_extracted.csv |
| note | text | N | From: eternal/neo4j_import/litigation_edges_cyc051-060__codex_json_csv_extracted.csv |
| source | text | N | From: eternal/nodes/litigation_edges_cyc051-060__codex_json_csv_extracted.csv |
| source | text | N | From: eternal/edges/litigation_edges_cyc051-060__codex_json_csv_extracted.csv |
| source | text | N | From: eternal/neo4j_import/litigation_edges_cyc051-060__codex_json_csv_extracted.csv |
| target | text | N | From: eternal/nodes/litigation_edges_cyc051-060__codex_json_csv_extracted.csv |
| target | text | N | From: eternal/edges/litigation_edges_cyc051-060__codex_json_csv_extracted.csv |
| target | text | N | From: eternal/neo4j_import/litigation_edges_cyc051-060__codex_json_csv_extracted.csv |
| type | text | N | From: eternal/nodes/litigation_edges_cyc051-060__codex_json_csv_extracted.csv |
| type | text | N | From: eternal/edges/litigation_edges_cyc051-060__codex_json_csv_extracted.csv |
| type | text | N | From: eternal/neo4j_import/litigation_edges_cyc051-060__codex_json_csv_extracted.csv |

## EXTRACTED_litigation_nodes (1)__codex_json_csv_extracted_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: litigation_nodes (1)__codex_json_csv_extracted.csv  
**Primary Key:** extracted_litigation_nodes (1)__codex_json_csv_extracted_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_litigation_nodes (1)__codex_json_csv_extracted_csv_id | ulid | Y | Primary key. |
| id | text | N | From: eternal/nodes/litigation_nodes (1)__codex_json_csv_extracted.csv |
| id | text | N | From: eternal/edges/litigation_nodes (1)__codex_json_csv_extracted.csv |
| id | text | N | From: eternal/neo4j_import/litigation_nodes (1)__codex_json_csv_extracted.csv |
| label | text | N | From: eternal/nodes/litigation_nodes (1)__codex_json_csv_extracted.csv |
| label | text | N | From: eternal/edges/litigation_nodes (1)__codex_json_csv_extracted.csv |
| label | text | N | From: eternal/neo4j_import/litigation_nodes (1)__codex_json_csv_extracted.csv |
| type | text | N | From: eternal/nodes/litigation_nodes (1)__codex_json_csv_extracted.csv |
| type | text | N | From: eternal/edges/litigation_nodes (1)__codex_json_csv_extracted.csv |
| type | text | N | From: eternal/neo4j_import/litigation_nodes (1)__codex_json_csv_extracted.csv |

## EXTRACTED_litigation_nodes (2)__codex_json_csv_extracted_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: litigation_nodes (2)__codex_json_csv_extracted.csv  
**Primary Key:** extracted_litigation_nodes (2)__codex_json_csv_extracted_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_litigation_nodes (2)__codex_json_csv_extracted_csv_id | ulid | Y | Primary key. |
| id | text | N | From: eternal/nodes/litigation_nodes (2)__codex_json_csv_extracted.csv |
| id | text | N | From: eternal/edges/litigation_nodes (2)__codex_json_csv_extracted.csv |
| id | text | N | From: eternal/neo4j_import/litigation_nodes (2)__codex_json_csv_extracted.csv |
| label | text | N | From: eternal/nodes/litigation_nodes (2)__codex_json_csv_extracted.csv |
| label | text | N | From: eternal/edges/litigation_nodes (2)__codex_json_csv_extracted.csv |
| label | text | N | From: eternal/neo4j_import/litigation_nodes (2)__codex_json_csv_extracted.csv |
| type | text | N | From: eternal/nodes/litigation_nodes (2)__codex_json_csv_extracted.csv |
| type | text | N | From: eternal/edges/litigation_nodes (2)__codex_json_csv_extracted.csv |
| type | text | N | From: eternal/neo4j_import/litigation_nodes (2)__codex_json_csv_extracted.csv |

## EXTRACTED_litigation_nodes__codex_json_csv_extracted_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: litigation_nodes__codex_json_csv_extracted.csv  
**Primary Key:** extracted_litigation_nodes__codex_json_csv_extracted_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_litigation_nodes__codex_json_csv_extracted_csv_id | ulid | Y | Primary key. |
| id | text | N | From: eternal/nodes/litigation_nodes__codex_json_csv_extracted.csv |
| id | text | N | From: eternal/edges/litigation_nodes__codex_json_csv_extracted.csv |
| id | text | N | From: eternal/neo4j_import/litigation_nodes__codex_json_csv_extracted.csv |
| label | text | N | From: eternal/nodes/litigation_nodes__codex_json_csv_extracted.csv |
| label | text | N | From: eternal/edges/litigation_nodes__codex_json_csv_extracted.csv |
| label | text | N | From: eternal/neo4j_import/litigation_nodes__codex_json_csv_extracted.csv |
| type | text | N | From: eternal/nodes/litigation_nodes__codex_json_csv_extracted.csv |
| type | text | N | From: eternal/edges/litigation_nodes__codex_json_csv_extracted.csv |
| type | text | N | From: eternal/neo4j_import/litigation_nodes__codex_json_csv_extracted.csv |

## EXTRACTED_litigation_nodes_cyc051_060__codex_json_csv_extracted_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: litigation_nodes_cyc051-060__codex_json_csv_extracted.csv  
**Primary Key:** extracted_litigation_nodes_cyc051_060__codex_json_csv_extracted_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_litigation_nodes_cyc051_060__codex_json_csv_extracted_csv_id | ulid | Y | Primary key. |
| group | text | N | From: eternal/nodes/litigation_nodes_cyc051-060__codex_json_csv_extracted.csv |
| group | text | N | From: eternal/edges/litigation_nodes_cyc051-060__codex_json_csv_extracted.csv |
| group | text | N | From: eternal/neo4j_import/litigation_nodes_cyc051-060__codex_json_csv_extracted.csv |
| id | text | N | From: eternal/nodes/litigation_nodes_cyc051-060__codex_json_csv_extracted.csv |
| id | text | N | From: eternal/edges/litigation_nodes_cyc051-060__codex_json_csv_extracted.csv |
| id | text | N | From: eternal/neo4j_import/litigation_nodes_cyc051-060__codex_json_csv_extracted.csv |
| label | text | N | From: eternal/nodes/litigation_nodes_cyc051-060__codex_json_csv_extracted.csv |
| label | text | N | From: eternal/edges/litigation_nodes_cyc051-060__codex_json_csv_extracted.csv |
| label | text | N | From: eternal/neo4j_import/litigation_nodes_cyc051-060__codex_json_csv_extracted.csv |
| meta | text | N | From: eternal/nodes/litigation_nodes_cyc051-060__codex_json_csv_extracted.csv |
| meta | text | N | From: eternal/edges/litigation_nodes_cyc051-060__codex_json_csv_extracted.csv |
| meta | text | N | From: eternal/neo4j_import/litigation_nodes_cyc051-060__codex_json_csv_extracted.csv |
| size | text | N | From: eternal/nodes/litigation_nodes_cyc051-060__codex_json_csv_extracted.csv |
| size | text | N | From: eternal/edges/litigation_nodes_cyc051-060__codex_json_csv_extracted.csv |
| size | text | N | From: eternal/neo4j_import/litigation_nodes_cyc051-060__codex_json_csv_extracted.csv |
| type | text | N | From: eternal/nodes/litigation_nodes_cyc051-060__codex_json_csv_extracted.csv |
| type | text | N | From: eternal/edges/litigation_nodes_cyc051-060__codex_json_csv_extracted.csv |
| type | text | N | From: eternal/neo4j_import/litigation_nodes_cyc051-060__codex_json_csv_extracted.csv |
| url | text | N | From: eternal/nodes/litigation_nodes_cyc051-060__codex_json_csv_extracted.csv |
| url | text | N | From: eternal/edges/litigation_nodes_cyc051-060__codex_json_csv_extracted.csv |
| url | text | N | From: eternal/neo4j_import/litigation_nodes_cyc051-060__codex_json_csv_extracted.csv |

## EXTRACTED_manifest

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: manifest  
**Primary Key:** extracted_manifest_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_manifest_id | ulid | Y | Primary key. |
| items | array | N | From: launcher/schemas/manifest.schema.json |
| meta | object | N | From: launcher/schemas/manifest.schema.json |

## EXTRACTED_manifest_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: manifest.csv  
**Primary Key:** extracted_manifest_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_manifest_csv_id | ulid | Y | Primary key. |
| bytes | text | N | From: cyclepacks/authority/manifest.csv |
| bytes | text | N | From: cyclepacks/authority_merge/manifest.csv |
| bytes | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/manifest.csv |
| path | text | N | From: cyclepacks/authority/manifest.csv |
| path | text | N | From: cyclepacks/authority_merge/manifest.csv |
| path | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/manifest.csv |
| sha256 | text | N | From: cyclepacks/authority/manifest.csv |
| sha256 | text | N | From: cyclepacks/authority_merge/manifest.csv |
| sha256 | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/manifest.csv |

## EXTRACTED_mi_source_index_v0006_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: mi_source_index_v0006.csv  
**Primary Key:** extracted_mi_source_index_v0006_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_mi_source_index_v0006_csv_id | ulid | Y | Primary key. |
| category | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/DATA/mi_source_index_v0006.csv |
| category | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0006/DATA/mi_source_index_v0006.csv |
| category | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0007/DATA/mi_source_index_v0006.csv |
| category | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/DATA/mi_source_index_v0006.csv |
| url | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/DATA/mi_source_index_v0006.csv |
| url | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0006/DATA/mi_source_index_v0006.csv |
| url | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0007/DATA/mi_source_index_v0006.csv |
| url | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/DATA/mi_source_index_v0006.csv |

## EXTRACTED_mi_source_index_v0008_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: mi_source_index_v0008.csv  
**Primary Key:** extracted_mi_source_index_v0008_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_mi_source_index_v0008_csv_id | ulid | Y | Primary key. |
| category | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/DATA/mi_source_index_v0008.csv |
| category | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/DATA/mi_source_index_v0008.csv |
| url | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/DATA/mi_source_index_v0008.csv |
| url | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/VERSIONS/v0008/DATA/mi_source_index_v0008.csv |

## EXTRACTED_neo4j_edges_FINAL__codex_json_csv_extracted_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: neo4j_edges_FINAL__codex_json_csv_extracted.csv  
**Primary Key:** extracted_neo4j_edges_final__codex_json_csv_extracted_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_neo4j_edges_final__codex_json_csv_extracted_csv_id | ulid | Y | Primary key. |
| :END_ID | text | N | From: eternal/nodes/neo4j_edges_FINAL__codex_json_csv_extracted.csv |
| :END_ID | text | N | From: eternal/edges/neo4j_edges_FINAL__codex_json_csv_extracted.csv |
| :END_ID | text | N | From: eternal/neo4j_import/neo4j_edges_FINAL__codex_json_csv_extracted.csv |
| :START_ID | text | N | From: eternal/nodes/neo4j_edges_FINAL__codex_json_csv_extracted.csv |
| :START_ID | text | N | From: eternal/edges/neo4j_edges_FINAL__codex_json_csv_extracted.csv |
| :START_ID | text | N | From: eternal/neo4j_import/neo4j_edges_FINAL__codex_json_csv_extracted.csv |
| :TYPE | text | N | From: eternal/nodes/neo4j_edges_FINAL__codex_json_csv_extracted.csv |
| :TYPE | text | N | From: eternal/edges/neo4j_edges_FINAL__codex_json_csv_extracted.csv |
| :TYPE | text | N | From: eternal/neo4j_import/neo4j_edges_FINAL__codex_json_csv_extracted.csv |
| jurisdiction | text | N | From: eternal/nodes/neo4j_edges_FINAL__codex_json_csv_extracted.csv |
| jurisdiction | text | N | From: eternal/edges/neo4j_edges_FINAL__codex_json_csv_extracted.csv |
| jurisdiction | text | N | From: eternal/neo4j_import/neo4j_edges_FINAL__codex_json_csv_extracted.csv |
| note | text | N | From: eternal/nodes/neo4j_edges_FINAL__codex_json_csv_extracted.csv |
| note | text | N | From: eternal/edges/neo4j_edges_FINAL__codex_json_csv_extracted.csv |
| note | text | N | From: eternal/neo4j_import/neo4j_edges_FINAL__codex_json_csv_extracted.csv |
| theme | text | N | From: eternal/nodes/neo4j_edges_FINAL__codex_json_csv_extracted.csv |
| theme | text | N | From: eternal/edges/neo4j_edges_FINAL__codex_json_csv_extracted.csv |
| theme | text | N | From: eternal/neo4j_import/neo4j_edges_FINAL__codex_json_csv_extracted.csv |

## EXTRACTED_neo4j_nodes (3)__codex_json_csv_extracted_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: neo4j_nodes (3)__codex_json_csv_extracted.csv  
**Primary Key:** extracted_neo4j_nodes (3)__codex_json_csv_extracted_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_neo4j_nodes (3)__codex_json_csv_extracted_csv_id | ulid | Y | Primary key. |
| :LABEL | text | N | From: eternal/nodes/neo4j_nodes (3)__codex_json_csv_extracted.csv |
| :LABEL | text | N | From: eternal/edges/neo4j_nodes (3)__codex_json_csv_extracted.csv |
| :LABEL | text | N | From: eternal/neo4j_import/neo4j_nodes (3)__codex_json_csv_extracted.csv |
| id:ID | text | N | From: eternal/nodes/neo4j_nodes (3)__codex_json_csv_extracted.csv |
| id:ID | text | N | From: eternal/edges/neo4j_nodes (3)__codex_json_csv_extracted.csv |
| id:ID | text | N | From: eternal/neo4j_import/neo4j_nodes (3)__codex_json_csv_extracted.csv |
| name | text | N | From: eternal/nodes/neo4j_nodes (3)__codex_json_csv_extracted.csv |
| name | text | N | From: eternal/edges/neo4j_nodes (3)__codex_json_csv_extracted.csv |
| name | text | N | From: eternal/neo4j_import/neo4j_nodes (3)__codex_json_csv_extracted.csv |
| type | text | N | From: eternal/nodes/neo4j_nodes (3)__codex_json_csv_extracted.csv |
| type | text | N | From: eternal/edges/neo4j_nodes (3)__codex_json_csv_extracted.csv |
| type | text | N | From: eternal/neo4j_import/neo4j_nodes (3)__codex_json_csv_extracted.csv |

## EXTRACTED_neo4j_nodes_FINAL__codex_json_csv_extracted_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: neo4j_nodes_FINAL__codex_json_csv_extracted.csv  
**Primary Key:** extracted_neo4j_nodes_final__codex_json_csv_extracted_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_neo4j_nodes_final__codex_json_csv_extracted_csv_id | ulid | Y | Primary key. |
| group | text | N | From: eternal/nodes/neo4j_nodes_FINAL__codex_json_csv_extracted.csv |
| group | text | N | From: eternal/edges/neo4j_nodes_FINAL__codex_json_csv_extracted.csv |
| group | text | N | From: eternal/neo4j_import/neo4j_nodes_FINAL__codex_json_csv_extracted.csv |
| id:ID | text | N | From: eternal/nodes/neo4j_nodes_FINAL__codex_json_csv_extracted.csv |
| id:ID | text | N | From: eternal/edges/neo4j_nodes_FINAL__codex_json_csv_extracted.csv |
| id:ID | text | N | From: eternal/neo4j_import/neo4j_nodes_FINAL__codex_json_csv_extracted.csv |
| label | text | N | From: eternal/nodes/neo4j_nodes_FINAL__codex_json_csv_extracted.csv |
| label | text | N | From: eternal/edges/neo4j_nodes_FINAL__codex_json_csv_extracted.csv |
| label | text | N | From: eternal/neo4j_import/neo4j_nodes_FINAL__codex_json_csv_extracted.csv |
| meta:json | text | N | From: eternal/nodes/neo4j_nodes_FINAL__codex_json_csv_extracted.csv |
| meta:json | text | N | From: eternal/edges/neo4j_nodes_FINAL__codex_json_csv_extracted.csv |
| meta:json | text | N | From: eternal/neo4j_import/neo4j_nodes_FINAL__codex_json_csv_extracted.csv |
| size:int | text | N | From: eternal/nodes/neo4j_nodes_FINAL__codex_json_csv_extracted.csv |
| size:int | text | N | From: eternal/edges/neo4j_nodes_FINAL__codex_json_csv_extracted.csv |
| size:int | text | N | From: eternal/neo4j_import/neo4j_nodes_FINAL__codex_json_csv_extracted.csv |
| type | text | N | From: eternal/nodes/neo4j_nodes_FINAL__codex_json_csv_extracted.csv |
| type | text | N | From: eternal/edges/neo4j_nodes_FINAL__codex_json_csv_extracted.csv |
| type | text | N | From: eternal/neo4j_import/neo4j_nodes_FINAL__codex_json_csv_extracted.csv |
| url | text | N | From: eternal/nodes/neo4j_nodes_FINAL__codex_json_csv_extracted.csv |
| url | text | N | From: eternal/edges/neo4j_nodes_FINAL__codex_json_csv_extracted.csv |
| url | text | N | From: eternal/neo4j_import/neo4j_nodes_FINAL__codex_json_csv_extracted.csv |

## EXTRACTED_nodes:authorities

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: nodes:authorities  
**Primary Key:** extracted_nodes:authorities_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_nodes:authorities_id | ulid | Y | Primary key. |
| :LABEL | text | N | From: cyclepacks/authority/sources/original/nodes_authorities.csv |
| :LABEL | text | N | From: cyclepacks/authority_merge/sources/original/nodes_authorities.csv |
| group | text | N | From: cyclepacks/authority/sources/original/nodes_authorities.csv |
| group | text | N | From: cyclepacks/authority_merge/sources/original/nodes_authorities.csv |
| id:ID | text | N | From: cyclepacks/authority/sources/original/nodes_authorities.csv |
| id:ID | text | N | From: cyclepacks/authority_merge/sources/original/nodes_authorities.csv |
| label | text | N | From: cyclepacks/authority/sources/original/nodes_authorities.csv |
| label | text | N | From: cyclepacks/authority_merge/sources/original/nodes_authorities.csv |
| tokens | text | N | From: cyclepacks/authority/sources/original/nodes_authorities.csv |
| tokens | text | N | From: cyclepacks/authority_merge/sources/original/nodes_authorities.csv |

## EXTRACTED_nodes:authority

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: nodes:authority  
**Primary Key:** extracted_nodes:authority_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_nodes:authority_id | ulid | Y | Primary key. |
| authority_id:ID(Authority) | text | N | From: cyclepacks/authority/neo4j/nodes_authority.csv |
| authority_id:ID(Authority) | text | N | From: cyclepacks/authority_merge/neo4j/nodes_authority.csv |
| authority_id:ID(Authority) | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/neo4j/nodes_authority.csv |
| authority_type | text | N | From: cyclepacks/authority/neo4j/nodes_authority.csv |
| authority_type | text | N | From: cyclepacks/authority_merge/neo4j/nodes_authority.csv |
| authority_type | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/neo4j/nodes_authority.csv |
| citation | text | N | From: cyclepacks/authority/neo4j/nodes_authority.csv |
| citation | text | N | From: cyclepacks/authority_merge/neo4j/nodes_authority.csv |
| citation | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/neo4j/nodes_authority.csv |

## EXTRACTED_nodes:authority_prior

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: nodes:authority_prior  
**Primary Key:** extracted_nodes:authority_prior_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_nodes:authority_prior_id | ulid | Y | Primary key. |
| authority_id:ID(Authority) | text | N | From: cyclepacks/authority/neo4j/nodes_authority_prior.csv |
| authority_id:ID(Authority) | text | N | From: cyclepacks/authority_merge/neo4j/nodes_authority_prior.csv |
| authority_type | text | N | From: cyclepacks/authority/neo4j/nodes_authority_prior.csv |
| authority_type | text | N | From: cyclepacks/authority_merge/neo4j/nodes_authority_prior.csv |
| citation | text | N | From: cyclepacks/authority/neo4j/nodes_authority_prior.csv |
| citation | text | N | From: cyclepacks/authority_merge/neo4j/nodes_authority_prior.csv |

## EXTRACTED_nodes:authority_shard

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: nodes:authority_shard  
**Primary Key:** extracted_nodes:authority_shard_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_nodes:authority_shard_id | ulid | Y | Primary key. |
| authority_id | text | N | From: cyclepacks/authority/neo4j/nodes_authority_shard.csv |
| authority_id | text | N | From: cyclepacks/authority_merge/neo4j/nodes_authority_shard.csv |
| authority_id | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/neo4j/nodes_authority_shard.csv |
| citation | text | N | From: cyclepacks/authority/neo4j/nodes_authority_shard.csv |
| citation | text | N | From: cyclepacks/authority_merge/neo4j/nodes_authority_shard.csv |
| pinpoint | text | N | From: cyclepacks/authority/neo4j/nodes_authority_shard.csv |
| pinpoint | text | N | From: cyclepacks/authority_merge/neo4j/nodes_authority_shard.csv |
| pinpoint | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/neo4j/nodes_authority_shard.csv |
| row_id | text | N | From: cyclepacks/authority/neo4j/nodes_authority_shard.csv |
| row_id | text | N | From: cyclepacks/authority_merge/neo4j/nodes_authority_shard.csv |
| shard_id:ID(AuthorityShard) | text | N | From: cyclepacks/authority/neo4j/nodes_authority_shard.csv |
| shard_id:ID(AuthorityShard) | text | N | From: cyclepacks/authority_merge/neo4j/nodes_authority_shard.csv |
| shard_id:ID(AuthorityShard) | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/neo4j/nodes_authority_shard.csv |
| source | text | N | From: cyclepacks/authority/neo4j/nodes_authority_shard.csv |
| source | text | N | From: cyclepacks/authority_merge/neo4j/nodes_authority_shard.csv |
| source | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/neo4j/nodes_authority_shard.csv |
| status | text | N | From: cyclepacks/authority/neo4j/nodes_authority_shard.csv |
| status | text | N | From: cyclepacks/authority_merge/neo4j/nodes_authority_shard.csv |
| text | text | N | From: cyclepacks/authority/neo4j/nodes_authority_shard.csv |
| text | text | N | From: cyclepacks/authority_merge/neo4j/nodes_authority_shard.csv |
| text | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/neo4j/nodes_authority_shard.csv |

## EXTRACTED_nodes:authority_shard_prior

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: nodes:authority_shard_prior  
**Primary Key:** extracted_nodes:authority_shard_prior_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_nodes:authority_shard_prior_id | ulid | Y | Primary key. |
| authority_id | text | N | From: cyclepacks/authority/neo4j/nodes_authority_shard_prior.csv |
| authority_id | text | N | From: cyclepacks/authority_merge/neo4j/nodes_authority_shard_prior.csv |
| citation | text | N | From: cyclepacks/authority/neo4j/nodes_authority_shard_prior.csv |
| citation | text | N | From: cyclepacks/authority_merge/neo4j/nodes_authority_shard_prior.csv |
| row_id | text | N | From: cyclepacks/authority/neo4j/nodes_authority_shard_prior.csv |
| row_id | text | N | From: cyclepacks/authority_merge/neo4j/nodes_authority_shard_prior.csv |
| shard_id:ID(AuthorityShard) | text | N | From: cyclepacks/authority/neo4j/nodes_authority_shard_prior.csv |
| shard_id:ID(AuthorityShard) | text | N | From: cyclepacks/authority_merge/neo4j/nodes_authority_shard_prior.csv |
| status | text | N | From: cyclepacks/authority/neo4j/nodes_authority_shard_prior.csv |
| status | text | N | From: cyclepacks/authority_merge/neo4j/nodes_authority_shard_prior.csv |

## EXTRACTED_nodes:factclaim

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: nodes:factclaim  
**Primary Key:** extracted_nodes:factclaim_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_nodes:factclaim_id | ulid | Y | Primary key. |
| fact_id:ID(FactClaim) | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/neo4j/nodes_factclaim.csv |
| generated_at | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/neo4j/nodes_factclaim.csv |
| normalized_proposition | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/neo4j/nodes_factclaim.csv |
| prov_activity_id | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/neo4j/nodes_factclaim.csv |
| prov_agent_id | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/neo4j/nodes_factclaim.csv |
| prov_entity_id | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/neo4j/nodes_factclaim.csv |
| truth_status | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/neo4j/nodes_factclaim.csv |

## EXTRACTED_nodes:statement

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: nodes:statement  
**Primary Key:** extracted_nodes:statement_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_nodes:statement_id | ulid | Y | Primary key. |
| generated_at | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/neo4j/nodes_statement.csv |
| line | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/neo4j/nodes_statement.csv |
| prov_activity_id | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/neo4j/nodes_statement.csv |
| prov_agent_id | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/neo4j/nodes_statement.csv |
| prov_entity_id | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/neo4j/nodes_statement.csv |
| source_path | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/neo4j/nodes_statement.csv |
| statement_id:ID(Statement) | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/neo4j/nodes_statement.csv |
| text | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/neo4j/nodes_statement.csv |
| truth_status | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/neo4j/nodes_statement.csv |

## EXTRACTED_nodes_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: nodes.csv  
**Primary Key:** extracted_nodes_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_nodes_csv_id | ulid | Y | Primary key. |
| case_id | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040421_UTC_86c87087/graph/nodes.csv |
| case_id | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040457_UTC_fff97690/graph/nodes.csv |
| case_id | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040524_UTC_7678222f/graph/nodes.csv |
| case_id | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040948_UTC_041fb7cb/graph/nodes.csv |
| case_id | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_041049_UTC_094c5afd/graph/nodes.csv |
| created_utc | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040421_UTC_86c87087/graph/nodes.csv |
| created_utc | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040457_UTC_fff97690/graph/nodes.csv |
| created_utc | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040524_UTC_7678222f/graph/nodes.csv |
| created_utc | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040948_UTC_041fb7cb/graph/nodes.csv |
| created_utc | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_041049_UTC_094c5afd/graph/nodes.csv |
| id | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040421_UTC_86c87087/graph/nodes.csv |
| id | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040457_UTC_fff97690/graph/nodes.csv |
| id | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040524_UTC_7678222f/graph/nodes.csv |
| id | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040948_UTC_041fb7cb/graph/nodes.csv |
| id | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_041049_UTC_094c5afd/graph/nodes.csv |
| labels | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040421_UTC_86c87087/graph/nodes.csv |
| labels | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040457_UTC_fff97690/graph/nodes.csv |
| labels | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040524_UTC_7678222f/graph/nodes.csv |
| labels | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040948_UTC_041fb7cb/graph/nodes.csv |
| labels | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_041049_UTC_094c5afd/graph/nodes.csv |
| source_locator | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040421_UTC_86c87087/graph/nodes.csv |
| source_locator | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040457_UTC_fff97690/graph/nodes.csv |
| source_locator | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040524_UTC_7678222f/graph/nodes.csv |
| source_locator | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040948_UTC_041fb7cb/graph/nodes.csv |
| source_locator | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_041049_UTC_094c5afd/graph/nodes.csv |
| source_path | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040421_UTC_86c87087/graph/nodes.csv |
| source_path | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040457_UTC_fff97690/graph/nodes.csv |
| source_path | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040524_UTC_7678222f/graph/nodes.csv |
| source_path | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040948_UTC_041fb7cb/graph/nodes.csv |
| source_path | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_041049_UTC_094c5afd/graph/nodes.csv |
| track | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040421_UTC_86c87087/graph/nodes.csv |
| track | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040457_UTC_fff97690/graph/nodes.csv |
| track | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040524_UTC_7678222f/graph/nodes.csv |
| track | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040948_UTC_041fb7cb/graph/nodes.csv |
| track | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_041049_UTC_094c5afd/graph/nodes.csv |
| updated_utc | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040421_UTC_86c87087/graph/nodes.csv |
| updated_utc | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040457_UTC_fff97690/graph/nodes.csv |
| updated_utc | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040524_UTC_7678222f/graph/nodes.csv |
| updated_utc | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_040948_UTC_041fb7cb/graph/nodes.csv |
| updated_utc | text | N | From: master_full/LITIGATIONOS__MASTERv1.0/BRAIN/RUNS/RUN_20260119_041049_UTC_094c5afd/graph/nodes.csv |

## EXTRACTED_rules_extracted_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: rules_extracted.csv  
**Primary Key:** extracted_rules_extracted_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_rules_extracted_csv_id | ulid | Y | Primary key. |
| chapter | text | N | From: cyclepacks/authority/sources/original/rules_extracted.csv |
| chapter | text | N | From: cyclepacks/authority_merge/sources/original/rules_extracted.csv |
| chapter | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/sources/original/rules_extracted.csv |
| context | text | N | From: cyclepacks/authority/sources/original/rules_extracted.csv |
| context | text | N | From: cyclepacks/authority_merge/sources/original/rules_extracted.csv |
| context | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/sources/original/rules_extracted.csv |
| rule | text | N | From: cyclepacks/authority/sources/original/rules_extracted.csv |
| rule | text | N | From: cyclepacks/authority_merge/sources/original/rules_extracted.csv |
| rule | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/sources/original/rules_extracted.csv |
| source_doc | text | N | From: cyclepacks/authority/sources/original/rules_extracted.csv |
| source_doc | text | N | From: cyclepacks/authority_merge/sources/original/rules_extracted.csv |
| source_doc | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/sources/original/rules_extracted.csv |

## EXTRACTED_scao_forms_master__codex_json_csv_extracted_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: scao_forms_master__codex_json_csv_extracted.csv  
**Primary Key:** extracted_scao_forms_master__codex_json_csv_extracted_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_scao_forms_master__codex_json_csv_extracted_csv_id | ulid | Y | Primary key. |
| citations | text | N | From: eternal/nodes/scao_forms_master__codex_json_csv_extracted.csv |
| citations | text | N | From: eternal/edges/scao_forms_master__codex_json_csv_extracted.csv |
| citations | text | N | From: eternal/neo4j_import/scao_forms_master__codex_json_csv_extracted.csv |
| code | text | N | From: eternal/nodes/scao_forms_master__codex_json_csv_extracted.csv |
| code | text | N | From: eternal/edges/scao_forms_master__codex_json_csv_extracted.csv |
| code | text | N | From: eternal/neo4j_import/scao_forms_master__codex_json_csv_extracted.csv |
| court | text | N | From: eternal/nodes/scao_forms_master__codex_json_csv_extracted.csv |
| court | text | N | From: eternal/edges/scao_forms_master__codex_json_csv_extracted.csv |
| court | text | N | From: eternal/neo4j_import/scao_forms_master__codex_json_csv_extracted.csv |
| form_id | text | N | From: eternal/nodes/scao_forms_master__codex_json_csv_extracted.csv |
| form_id | text | N | From: eternal/edges/scao_forms_master__codex_json_csv_extracted.csv |
| form_id | text | N | From: eternal/neo4j_import/scao_forms_master__codex_json_csv_extracted.csv |
| source_url | text | N | From: eternal/nodes/scao_forms_master__codex_json_csv_extracted.csv |
| source_url | text | N | From: eternal/edges/scao_forms_master__codex_json_csv_extracted.csv |
| source_url | text | N | From: eternal/neo4j_import/scao_forms_master__codex_json_csv_extracted.csv |
| title | text | N | From: eternal/nodes/scao_forms_master__codex_json_csv_extracted.csv |
| title | text | N | From: eternal/edges/scao_forms_master__codex_json_csv_extracted.csv |
| title | text | N | From: eternal/neo4j_import/scao_forms_master__codex_json_csv_extracted.csv |

## EXTRACTED_score_row

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: score_row  
**Primary Key:** extracted_score_row_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_score_row_id | ulid | Y | Primary key. |
| confidence | integer | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/score_row.schema.json |
| confidence | integer | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/score_row.schema.json |
| created_utc | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/score_row.schema.json |
| created_utc | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/score_row.schema.json |
| feasibility | integer | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/score_row.schema.json |
| feasibility | integer | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/score_row.schema.json |
| impact | integer | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/score_row.schema.json |
| impact | integer | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/score_row.schema.json |
| item_id | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/score_row.schema.json |
| item_id | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/score_row.schema.json |
| priority | integer | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/score_row.schema.json |
| priority | integer | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/score_row.schema.json |
| risk | integer | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/score_row.schema.json |
| risk | integer | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/score_row.schema.json |

## EXTRACTED_signal_row

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: signal_row  
**Primary Key:** extracted_signal_row_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_signal_row_id | ulid | Y | Primary key. |
| atoms | array | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/signal_row.schema.json |
| atoms | array | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/signal_row.schema.json |
| created_utc | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/signal_row.schema.json |
| created_utc | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/signal_row.schema.json |
| kind | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/signal_row.schema.json |
| kind | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/signal_row.schema.json |
| score | integer | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/signal_row.schema.json |
| score | integer | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/signal_row.schema.json |
| signal_id | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/signal_row.schema.json |
| signal_id | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/signal_row.schema.json |
| text | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/signal_row.schema.json |
| text | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/signal_row.schema.json |

## EXTRACTED_sor_manifest_csv

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: sor_manifest.csv  
**Primary Key:** extracted_sor_manifest_csv_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_sor_manifest_csv_id | ulid | Y | Primary key. |
| bytes | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/data/sor_manifest.csv |
| ext | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/data/sor_manifest.csv |
| mtime | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/data/sor_manifest.csv |
| name | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/data/sor_manifest.csv |
| path | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/data/sor_manifest.csv |
| sha256 | text | N | From: cyclepacks/statement_fact/LITIGATIONOS_STATEMENT_FACT_PROV_AUTH_CYCLE_20260107_181048/data/sor_manifest.csv |

## EXTRACTED_vehicle_row

**Origin:** EXTRACTED  
**Description:** Extracted table-like structure from artifacts: vehicle_row  
**Primary Key:** extracted_vehicle_row_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| extracted_vehicle_row_id | ulid | Y | Primary key. |
| created_utc | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/vehicle_row.schema.json |
| created_utc | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/vehicle_row.schema.json |
| lane | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/vehicle_row.schema.json |
| lane | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/vehicle_row.schema.json |
| missing_authority | array | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/vehicle_row.schema.json |
| missing_authority | array | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/vehicle_row.schema.json |
| status | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/vehicle_row.schema.json |
| status | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/vehicle_row.schema.json |
| vehicle | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/vehicle_row.schema.json |
| vehicle | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/vehicle_row.schema.json |
| vehicle_id | string | N | From: master/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/vehicle_row.schema.json |
| vehicle_id | string | N | From: master_full/LITIGATIONOS__MASTERv1.0/SCHEMA/brain/vehicle_row.schema.json |

## EdgeTable

**Origin:** PROPOSED  
**Description:** Edge CSV logical table (for Neo4j import).  
**Primary Key:** edgetable_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| edgetable_id | ulid | Y | Primary key. |
| et_id | ulid | Y | Primary identifier (ULID recommended). |
| et_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| et_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| et_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| et_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| et_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| et_tags_json | json | N | Freeform tags / labels. |
| et_notes | text | N | Human notes. |
| et_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| et_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| contract_id | ulid | N |  |
| table_name | text | Y |  |
| type | text | N |  |
| csv_artifact_id | ulid | N |  |
| from_label | text | N |  |
| to_label | text | N |  |
| from_field | text | N |  |
| to_field | text | N |  |
| indexes_json | json | N |  |

## EvidenceAtom

**Origin:** PROPOSED  
**Description:** Smallest analyzable unit (fact/quote/metadata fragment) extracted from EvidenceItem.  
**Primary Key:** evidenceatom_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| evidenceatom_id | ulid | Y | Primary key. |
| atom_id | ulid | Y | Primary identifier (ULID recommended). |
| atom_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| atom_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| atom_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| atom_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| atom_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| atom_tags_json | json | N | Freeform tags / labels. |
| atom_notes | text | N | Human notes. |
| atom_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| atom_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| case_id | ulid | N |  |
| evidence_item_id | ulid | Y |  |
| atom_type | enum | Y | quote\\|timestamp\\|field\\|message\\|image_region\\|etc |
| content_text | text | N |  |
| content_json | json | N |  |
| content_hash | text | N |  |
| source_locator | text | N | Re-open recipe: bundle→entry→page/line/time. |
| start_offset | int | N |  |
| end_offset | int | N |  |
| start_time_ms | int | N |  |
| end_time_ms | int | N |  |
| confidence | float | N |  |
| quote_lock_status | enum | N | CANDIDATE\\|VERIFIED |
| verification_artifact_id | ulid | N |  |

## EvidenceFoundationCheck

**Origin:** PROPOSED  
**Description:** MRE-based admissibility checklist row per exhibit/artifact.  
**Primary Key:** evidencefoundationcheck_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| evidencefoundationcheck_id | ulid | Y | Primary key. |
| mre_id | ulid | Y | Primary identifier (ULID recommended). |
| mre_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| mre_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| mre_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| mre_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| mre_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| mre_tags_json | json | N | Freeform tags / labels. |
| mre_notes | text | N | Human notes. |
| mre_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| mre_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| case_id | ulid | N |  |
| evidence_item_id | ulid | N |  |
| artifact_id | ulid | N |  |
| exhibit_id | ulid | N |  |
| rule | text | N | MRE citation string |
| issue | text | N | authentication\\|hearsay\\|best_evidence\\|relevance\\|403\\|etc |
| status | enum | N | OPEN\\|PARTIAL\\|SATISFIED\\|BLOCKED |
| supporting_atom_ids_json | json | N |  |
| notes | text | N |  |

## EvidenceItem

**Origin:** PROPOSED  
**Description:** A piece of evidence (file, photo, report, message export, etc.).  
**Primary Key:** evidenceitem_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| evidenceitem_id | ulid | Y | Primary key. |
| ev_id | ulid | Y | Primary identifier (ULID recommended). |
| ev_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| ev_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| ev_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| ev_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| ev_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| ev_tags_json | json | N | Freeform tags / labels. |
| ev_notes | text | N | Human notes. |
| ev_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| ev_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| case_id | ulid | N |  |
| evidence_type | enum | Y |  |
| title | text | N |  |
| captured_utc | datetime_rfc3339 | N |  |
| source_device | text | N |  |
| source_app | text | N |  |
| original_artifact_id | ulid | Y |  |
| derived_text_artifact_id | ulid | N |  |
| derived_ocr_artifact_id | ulid | N |  |
| metadata_json | json | N |  |
| authentication_notes | text | N |  |
| mre_foundation_checklist_json | json | N |  |
| sensitivity_level | enum | N |  |

## EvidenceItemExhibitLink

**Origin:** PROPOSED  
**Description:** Link table: EvidenceItem ↔ Exhibit.  
**Primary Key:** evidenceitemexhibitlink_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| evidenceitemexhibitlink_id | ulid | Y | Primary identifier (ULID recommended). |
| evidenceitemexhibitlink_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| evidenceitemexhibitlink_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| evidenceitemexhibitlink_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| evidenceitemexhibitlink_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| evidenceitemexhibitlink_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| evidenceitemexhibitlink_tags_json | json | N | Freeform tags / labels. |
| evidenceitemexhibitlink_notes | text | N | Human notes. |
| evidenceitemexhibitlink_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| evidenceitemexhibitlink_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| evidence_item_id | ulid | Y |  |
| exhibit_id | ulid | Y |  |
| purpose | text | N | Why included in exhibit. |

## Exhibit

**Origin:** PROPOSED  
**Description:** An exhibit prepared for filing/hearing, linking EvidenceItems to a packet with cover pages.  
**Primary Key:** exhibit_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| exhibit_id | ulid | Y | Primary key. |
| exh_id | ulid | Y | Primary identifier (ULID recommended). |
| exh_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| exh_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| exh_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| exh_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| exh_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| exh_tags_json | json | N | Freeform tags / labels. |
| exh_notes | text | N | Human notes. |
| exh_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| exh_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| case_id | ulid | Y |  |
| exhibit_label | text | Y | Exhibit A, B, ... |
| offering_party | enum | N | Plaintiff/Defendant |
| cover_document_id | ulid | N |  |
| compiled_pdf_artifact_id | ulid | N |  |
| exhibit_matrix_row_id | ulid | N |  |
| is_filed | bool | N |  |
| filed_filing_id | ulid | N |  |

## Fact

**Origin:** PROPOSED  
**Description:** A normalized fact candidate with provenance to EvidenceAtoms and evaluation state.  
**Primary Key:** fact_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| fact_id | ulid | Y | Primary identifier (ULID recommended). |
| fact_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| fact_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| fact_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| fact_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| fact_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| fact_tags_json | json | N | Freeform tags / labels. |
| fact_notes | text | N | Human notes. |
| fact_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| fact_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| case_id | ulid | N |  |
| fact_text | text | Y |  |
| fact_type | enum | N |  |
| truth_status | enum | N | OPEN\\|PARTIAL\\|SATISFIED per PCW-like grading. |
| harm_category | enum | N |  |
| materiality | enum | N |  |
| validation_notes | text | N |  |

## FactAtomLink

**Origin:** PROPOSED  
**Description:** Link table: Fact ↔ EvidenceAtom.  
**Primary Key:** factatomlink_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| factatomlink_id | ulid | Y | Primary identifier (ULID recommended). |
| factatomlink_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| factatomlink_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| factatomlink_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| factatomlink_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| factatomlink_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| factatomlink_tags_json | json | N | Freeform tags / labels. |
| factatomlink_notes | text | N | Human notes. |
| factatomlink_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| factatomlink_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| fact_id | ulid | Y |  |
| atom_id | ulid | Y |  |
| weight | float | N | Support weight. |

## Filing

**Origin:** PROPOSED  
**Description:** A filing event (submitted to court).  
**Primary Key:** filing_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| filing_id | ulid | Y | Primary identifier (ULID recommended). |
| filing_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| filing_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| filing_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| filing_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| filing_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| filing_tags_json | json | N | Freeform tags / labels. |
| filing_notes | text | N | Human notes. |
| filing_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| filing_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| case_id | ulid | Y |  |
| document_id | ulid | Y |  |
| filed_utc | datetime_rfc3339 | N |  |
| filed_method | enum | N | MiFile, in-person, mail. |
| fee_paid | money | N |  |
| fee_waiver_requested | bool | N |  |
| fee_receipt_artifact_id | ulid | N |  |
| served | bool | N |  |
| service_batch_id | ulid | N |  |
| docket_entry_id | ulid | N |  |
| resulting_order_id | ulid | N |  |

## GatePOLink

**Origin:** PROPOSED  
**Description:** Link table: GateResult ↔ ProofObligation.  
**Primary Key:** gatepolink_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| gatepolink_id | ulid | Y | Primary identifier (ULID recommended). |
| gatepolink_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| gatepolink_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| gatepolink_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| gatepolink_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| gatepolink_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| gatepolink_tags_json | json | N | Freeform tags / labels. |
| gatepolink_notes | text | N | Human notes. |
| gatepolink_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| gatepolink_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| gate_id | ulid | Y |  |
| po_id | ulid | Y |  |
| status | enum | N | sat\\|unsat\\|waived |

## GateResult

**Origin:** PROPOSED  
**Description:** A gate evaluation decision for a stage/run artifact.  
**Primary Key:** gateresult_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| gateresult_id | ulid | Y | Primary key. |
| gate_id | ulid | Y | Primary identifier (ULID recommended). |
| gate_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| gate_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| gate_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| gate_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| gate_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| gate_tags_json | json | N | Freeform tags / labels. |
| gate_notes | text | N | Human notes. |
| gate_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| gate_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| case_id | ulid | N |  |
| run_id | ulid | N |  |
| stage | text | Y |  |
| status | enum | Y | PASS\\|FAIL\\|PARTIAL\\|DEGRADED |
| unsat_core_artifact_id | ulid | N |  |
| decision_md_artifact_id | ulid | N |  |
| policy_bundle_artifact_id | ulid | N |  |
| metrics_json | json | N |  |

## GraphContract

**Origin:** PROPOSED  
**Description:** JSON Schema contract for node/edge CSVs.  
**Primary Key:** graphcontract_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| graphcontract_id | ulid | Y | Primary key. |
| gc_id | ulid | Y | Primary identifier (ULID recommended). |
| gc_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| gc_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| gc_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| gc_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| gc_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| gc_tags_json | json | N | Freeform tags / labels. |
| gc_notes | text | N | Human notes. |
| gc_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| gc_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| contract_name | text | Y |  |
| version | text | N |  |
| schema_artifact_id | ulid | N |  |
| validator_command | text | N |  |
| notes | text | N |  |

## Hearing

**Origin:** PROPOSED  
**Description:** A scheduled court hearing/session.  
**Primary Key:** hearing_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| hearing_id | ulid | Y | Primary identifier (ULID recommended). |
| hearing_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| hearing_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| hearing_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| hearing_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| hearing_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| hearing_tags_json | json | N | Freeform tags / labels. |
| hearing_notes | text | N | Human notes. |
| hearing_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| hearing_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| case_id | ulid | Y |  |
| court_id | ulid | N |  |
| hearing_type | enum | N |  |
| scheduled_start_utc | datetime_rfc3339 | N |  |
| scheduled_end_utc | datetime_rfc3339 | N |  |
| actual_start_utc | datetime_rfc3339 | N |  |
| actual_end_utc | datetime_rfc3339 | N |  |
| judge_person_id | ulid | N |  |
| location | text | N |  |
| is_evidentiary | bool | N |  |
| was_on_record | bool | N |  |
| minutes_artifact_id | ulid | N |  |
| transcript_id | ulid | N |  |
| resulting_order_id | ulid | N |  |

## InTotoLink

**Origin:** PROPOSED  
**Description:** in-toto link metadata (step material/products).  
**Primary Key:** intotolink_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| intotolink_id | ulid | Y | Primary key. |
| it_id | ulid | Y | Primary identifier (ULID recommended). |
| it_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| it_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| it_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| it_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| it_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| it_tags_json | json | N | Freeform tags / labels. |
| it_notes | text | N | Human notes. |
| it_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| it_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| run_id | ulid | N |  |
| step_name | text | N |  |
| materials_json | json | N |  |
| products_json | json | N |  |
| byproducts_json | json | N |  |
| command_json | json | N |  |
| environment_json | json | N |  |
| signatures_json | json | N |  |

## IntegrityCheck

**Origin:** PROPOSED  
**Description:** Integrity verification run (zip test, CRC scan, duplicates, etc.).  
**Primary Key:** integritycheck_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| integritycheck_id | ulid | Y | Primary key. |
| ic_id | ulid | Y | Primary identifier (ULID recommended). |
| ic_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| ic_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| ic_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| ic_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| ic_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| ic_tags_json | json | N | Freeform tags / labels. |
| ic_notes | text | N | Human notes. |
| ic_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| ic_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| bundle_id | ulid | N |  |
| artifact_id | ulid | N |  |
| check_type | enum | Y | zip_test\\|crc_scan\\|schema_validate\\|pii_scan\\|quote_lock |
| status | enum | N | PASS\\|WARN\\|FAIL |
| started_utc | datetime_rfc3339 | N |  |
| ended_utc | datetime_rfc3339 | N |  |
| findings_artifact_id | ulid | N |  |
| metrics_json | json | N |  |

## Neo4jImportJob

**Origin:** PROPOSED  
**Description:** Neo4j admin import job record.  
**Primary Key:** neo4jimportjob_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| neo4jimportjob_id | ulid | Y | Primary key. |
| nj_id | ulid | Y | Primary identifier (ULID recommended). |
| nj_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| nj_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| nj_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| nj_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| nj_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| nj_tags_json | json | N | Freeform tags / labels. |
| nj_notes | text | N | Human notes. |
| nj_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| nj_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| run_id | ulid | N |  |
| db_name | text | N |  |
| nodes_dir | text | N |  |
| rels_dir | text | N |  |
| command_line | text | N |  |
| status | enum | N | PLANNED\\|RUNNING\\|DONE\\|FAIL |
| logs_artifact_id | ulid | N |  |

## NodeTable

**Origin:** PROPOSED  
**Description:** Node CSV logical table (for Neo4j import).  
**Primary Key:** nodetable_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| nodetable_id | ulid | Y | Primary key. |
| nt_id | ulid | Y | Primary identifier (ULID recommended). |
| nt_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| nt_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| nt_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| nt_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| nt_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| nt_tags_json | json | N | Freeform tags / labels. |
| nt_notes | text | N | Human notes. |
| nt_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| nt_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| contract_id | ulid | N |  |
| table_name | text | Y |  |
| label | text | N |  |
| csv_artifact_id | ulid | N |  |
| primary_key_field | text | N |  |
| indexes_json | json | N |  |
| constraints_json | json | N |  |

## OCFLInventory

**Origin:** PROPOSED  
**Description:** OCFL inventory.json normalized view.  
**Primary Key:** ocflinventory_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| ocflinventory_id | ulid | Y | Primary key. |
| oci_id | ulid | Y | Primary identifier (ULID recommended). |
| oci_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| oci_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| oci_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| oci_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| oci_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| oci_tags_json | json | N | Freeform tags / labels. |
| oci_notes | text | N | Human notes. |
| oci_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| oci_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| ocfl_object_id | ulid | Y |  |
| head | text | N |  |
| type | text | N |  |
| digest_algorithm | text | N |  |
| manifest_json | json | N |  |
| versions_json | json | N |  |
| fixity_json | json | N |  |

## OCFLObject

**Origin:** PROPOSED  
**Description:** OCFL logical object.  
**Primary Key:** ocflobject_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| ocflobject_id | ulid | Y | Primary key. |
| oc_id | ulid | Y | Primary identifier (ULID recommended). |
| oc_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| oc_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| oc_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| oc_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| oc_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| oc_tags_json | json | N | Freeform tags / labels. |
| oc_notes | text | N | Human notes. |
| oc_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| oc_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| bundle_id | ulid | N |  |
| object_id | text | Y |  |
| object_root | text | N |  |
| inventory_artifact_id | ulid | N |  |
| digest_algorithm | text | N |  |

## Objection

**Origin:** PROPOSED  
**Description:** On-record objection (for appeal preservation).  
**Primary Key:** objection_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| objection_id | ulid | Y | Primary key. |
| obj_id | ulid | Y | Primary identifier (ULID recommended). |
| obj_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| obj_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| obj_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| obj_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| obj_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| obj_tags_json | json | N | Freeform tags / labels. |
| obj_notes | text | N | Human notes. |
| obj_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| obj_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| case_id | ulid | Y |  |
| hearing_id | ulid | N |  |
| transcript_segment_id | ulid | N |  |
| objecting_party_link_id | ulid | N |  |
| basis | text | N | rule\\|relevance\\|hearsay\\|foundation\\|etc |
| ruling | enum | N | SUSTAINED\\|OVERRULED\\|RESERVED |
| notes | text | N |  |

## OfferOfProof

**Origin:** PROPOSED  
**Description:** Offer of proof payload (what was excluded).  
**Primary Key:** offerofproof_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| offerofproof_id | ulid | Y | Primary key. |
| oop_id | ulid | Y | Primary identifier (ULID recommended). |
| oop_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| oop_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| oop_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| oop_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| oop_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| oop_tags_json | json | N | Freeform tags / labels. |
| oop_notes | text | N | Human notes. |
| oop_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| oop_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| case_id | ulid | Y |  |
| hearing_id | ulid | N |  |
| document_id | ulid | N |  |
| artifact_id | ulid | N |  |
| related_exhibit_id | ulid | N |  |
| excluded_evidence_item_id | ulid | N |  |
| notes | text | N |  |

## OpenLineageRun

**Origin:** PROPOSED  
**Description:** OpenLineage run entity.  
**Primary Key:** openlineagerun_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| openlineagerun_id | ulid | Y | Primary key. |
| olr2_id | ulid | Y | Primary identifier (ULID recommended). |
| olr2_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| olr2_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| olr2_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| olr2_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| olr2_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| olr2_tags_json | json | N | Freeform tags / labels. |
| olr2_notes | text | N | Human notes. |
| olr2_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| olr2_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| run_id | ulid | N |  |
| namespace | text | N |  |
| name | text | N |  |
| run_uuid | text | N |  |
| event_time | datetime_rfc3339 | N |  |
| inputs_json | json | N |  |
| outputs_json | json | N |  |
| facets_json | json | N |  |

## Order

**Origin:** PROPOSED  
**Description:** An order issued by the court.  
**Primary Key:** order_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| order_id | ulid | Y | Primary identifier (ULID recommended). |
| order_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| order_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| order_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| order_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| order_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| order_tags_json | json | N | Freeform tags / labels. |
| order_notes | text | N | Human notes. |
| order_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| order_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| case_id | ulid | Y |  |
| document_id | ulid | N |  |
| signed_date | date | N |  |
| entered_date | date | N |  |
| judge_person_id | ulid | N |  |
| order_type | enum | N |  |
| is_interim | bool | N |  |
| supersedes_order_id | ulid | N |  |
| stayed_by_order_id | ulid | N |  |
| effective_date | date | N |  |
| expiration_date | date | N |  |
| findings_required | bool | N |  |
| findings_text_extract | text | N |  |
| relief_summary_json | json | N |  |
| deadline_bundle_id | ulid | N | Derived deadlines from order. |

## Organization

**Origin:** PROPOSED  
**Description:** An organization (landlord entity, agency, law firm, etc.).  
**Primary Key:** organization_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| organization_id | ulid | Y | Primary key. |
| org_id | ulid | Y | Primary identifier (ULID recommended). |
| org_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| org_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| org_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| org_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| org_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| org_tags_json | json | N | Freeform tags / labels. |
| org_notes | text | N | Human notes. |
| org_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| org_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| org_name | text | Y |  |
| org_type | enum | N | LLC, court, agency, etc. |
| registered_agent_person_id | ulid | N |  |
| registered_address_id | ulid | N |  |
| website | text | N |  |
| ein | text | N |  |

## OtelLogRecord

**Origin:** PROPOSED  
**Description:** OpenTelemetry log record (normalized).  
**Primary Key:** otellogrecord_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| otellogrecord_id | ulid | Y | Primary key. |
| olr_id | ulid | Y | Primary identifier (ULID recommended). |
| olr_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| olr_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| olr_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| olr_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| olr_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| olr_tags_json | json | N | Freeform tags / labels. |
| olr_notes | text | N | Human notes. |
| olr_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| olr_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| run_id | ulid | N |  |
| timestamp | datetime_rfc3339 | N |  |
| severity_text | text | N |  |
| body | text | N |  |
| attributes_json | json | N |  |
| trace_id | text | N |  |
| span_id | text | N |  |

## OtelMetricPoint

**Origin:** PROPOSED  
**Description:** OpenTelemetry metric point (normalized).  
**Primary Key:** otelmetricpoint_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| otelmetricpoint_id | ulid | Y | Primary key. |
| omp_id | ulid | Y | Primary identifier (ULID recommended). |
| omp_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| omp_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| omp_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| omp_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| omp_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| omp_tags_json | json | N | Freeform tags / labels. |
| omp_notes | text | N | Human notes. |
| omp_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| omp_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| run_id | ulid | N |  |
| metric_name | text | Y |  |
| unit | text | N |  |
| type | text | N |  |
| value | float | N |  |
| attributes_json | json | N |  |
| timestamp | datetime_rfc3339 | N |  |

## OtelSpan

**Origin:** PROPOSED  
**Description:** OpenTelemetry trace span (normalized).  
**Primary Key:** otelspan_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| otelspan_id | ulid | Y | Primary key. |
| os_id | ulid | Y | Primary identifier (ULID recommended). |
| os_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| os_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| os_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| os_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| os_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| os_tags_json | json | N | Freeform tags / labels. |
| os_notes | text | N | Human notes. |
| os_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| os_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| run_id | ulid | N |  |
| trace_id | text | Y |  |
| span_id | text | Y |  |
| parent_span_id | text | N |  |
| name | text | N |  |
| kind | text | N |  |
| start_time | datetime_rfc3339 | N |  |
| end_time | datetime_rfc3339 | N |  |
| status_code | text | N |  |
| status_message | text | N |  |
| attributes_json | json | N |  |
| events_json | json | N |  |

## PIIItem

**Origin:** PROPOSED  
**Description:** PII/PHI finding (for redaction workflows).  
**Primary Key:** piiitem_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| piiitem_id | ulid | Y | Primary key. |
| pii_id | ulid | Y | Primary identifier (ULID recommended). |
| pii_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| pii_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| pii_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| pii_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| pii_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| pii_tags_json | json | N | Freeform tags / labels. |
| pii_notes | text | N | Human notes. |
| pii_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| pii_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| artifact_id | ulid | Y |  |
| document_id | ulid | N |  |
| pii_type | enum | Y |  |
| confidence | float | N |  |
| locator_json | json | N | page/line/bbox/timecode |
| text_snippet | text | N |  |
| recommended_action | enum | N | redact\\|mask\\|review |

## POAtomLink

**Origin:** PROPOSED  
**Description:** Link table: ProofObligation ↔ EvidenceAtom.  
**Primary Key:** poatomlink_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| poatomlink_id | ulid | Y | Primary identifier (ULID recommended). |
| poatomlink_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| poatomlink_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| poatomlink_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| poatomlink_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| poatomlink_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| poatomlink_tags_json | json | N | Freeform tags / labels. |
| poatomlink_notes | text | N | Human notes. |
| poatomlink_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| poatomlink_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| po_id | ulid | Y |  |
| atom_id | ulid | Y |  |
| satisfies | enum | N | direct\\|partial |

## POPinLink

**Origin:** PROPOSED  
**Description:** Link table: ProofObligation ↔ AuthorityPinpoint.  
**Primary Key:** popinlink_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| popinlink_id | ulid | Y | Primary identifier (ULID recommended). |
| popinlink_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| popinlink_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| popinlink_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| popinlink_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| popinlink_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| popinlink_tags_json | json | N | Freeform tags / labels. |
| popinlink_notes | text | N | Human notes. |
| popinlink_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| popinlink_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| po_id | ulid | Y |  |
| pin_id | ulid | Y |  |
| satisfies | enum | N | required_basis |

## Person

**Origin:** PROPOSED  
**Description:** A natural person (party, witness, judge, clerk, etc.).  
**Primary Key:** person_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| person_id | ulid | Y | Primary identifier (ULID recommended). |
| person_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| person_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| person_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| person_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| person_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| person_tags_json | json | N | Freeform tags / labels. |
| person_notes | text | N | Human notes. |
| person_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| person_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| full_name | text | Y |  |
| dob | date | N |  |
| role_flags_json | json | N | party/witness/judge/etc |
| primary_address_id | ulid | N |  |
| primary_phone | text | N |  |
| primary_email | text | N |  |
| bar_number | text | N | If attorney. |
| notes_sensitive | text | N | Use redaction policy if exported. |

## ProofObligation

**Origin:** PROPOSED  
**Description:** Proof obligation (PO) required by a vehicle, keyed to authority + evidence requirements.  
**Primary Key:** proofobligation_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| proofobligation_id | ulid | Y | Primary key. |
| po_id | ulid | Y | Primary identifier (ULID recommended). |
| po_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| po_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| po_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| po_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| po_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| po_tags_json | json | N | Freeform tags / labels. |
| po_notes | text | N | Human notes. |
| po_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| po_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| case_id | ulid | N |  |
| vehicle_id | ulid | Y |  |
| po_code | text | Y |  |
| po_name | text | Y |  |
| po_type | enum | N | CoreSAT\\|NonCore |
| authority_snapshot_id | ulid | N |  |
| required_authority_pins_json | json | N |  |
| required_evidence_types_json | json | N |  |
| status | enum | N | OBLIGATION_OPEN\\|OBLIGATION_PARTIAL\\|OBLIGATION_SATISFIED |
| assurance_score | float | N |  |
| validator_version | text | N |  |
| last_evaluated_utc | datetime_rfc3339 | N |  |

## Proposition

**Origin:** PROPOSED  
**Description:** Atomic legal proposition used in drafting; must cite AuthorityPinpoints inside snapshot for PCG outputs.  
**Primary Key:** proposition_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| proposition_id | ulid | Y | Primary key. |
| prop_id | ulid | Y | Primary identifier (ULID recommended). |
| prop_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| prop_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| prop_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| prop_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| prop_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| prop_tags_json | json | N | Freeform tags / labels. |
| prop_notes | text | N | Human notes. |
| prop_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| prop_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| case_id | ulid | N |  |
| proposition_text | text | Y |  |
| domain | enum | N | procedure\\|substantive\\|evidence\\|appellate |
| authority_snapshot_id | ulid | N |  |
| confidence | float | N |  |
| status_gate | enum | N | DRAFT\\|VERIFIED\\|RELEASE |

## PropositionFactLink

**Origin:** PROPOSED  
**Description:** Link table: Proposition ↔ Fact.  
**Primary Key:** propositionfactlink_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| propositionfactlink_id | ulid | Y | Primary identifier (ULID recommended). |
| propositionfactlink_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| propositionfactlink_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| propositionfactlink_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| propositionfactlink_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| propositionfactlink_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| propositionfactlink_tags_json | json | N | Freeform tags / labels. |
| propositionfactlink_notes | text | N | Human notes. |
| propositionfactlink_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| propositionfactlink_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| prop_id | ulid | Y |  |
| fact_id | ulid | Y |  |
| fit | enum | N | element\\|context\\|harm |

## PropositionPinLink

**Origin:** PROPOSED  
**Description:** Link table: Proposition ↔ AuthorityPinpoint.  
**Primary Key:** propositionpinlink_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| propositionpinlink_id | ulid | Y | Primary identifier (ULID recommended). |
| propositionpinlink_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| propositionpinlink_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| propositionpinlink_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| propositionpinlink_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| propositionpinlink_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| propositionpinlink_tags_json | json | N | Freeform tags / labels. |
| propositionpinlink_notes | text | N | Human notes. |
| propositionpinlink_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| propositionpinlink_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| prop_id | ulid | Y |  |
| pin_id | ulid | Y |  |
| pin_role | enum | N | holding\\|rule\\|commentary |

## ProvenanceActivity

**Origin:** PROPOSED  
**Description:** W3C PROV Activity mirror row (interop).  
**Primary Key:** provenanceactivity_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| provenanceactivity_id | ulid | Y | Primary key. |
| prov_a_id | ulid | Y | Primary identifier (ULID recommended). |
| prov_a_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| prov_a_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| prov_a_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| prov_a_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| prov_a_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| prov_a_tags_json | json | N | Freeform tags / labels. |
| prov_a_notes | text | N | Human notes. |
| prov_a_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| prov_a_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| external_id | text | N |  |
| label | text | N |  |
| type | text | N |  |
| started_at_utc | datetime_rfc3339 | N |  |
| ended_at_utc | datetime_rfc3339 | N |  |
| location | text | N |  |

## ProvenanceAgent

**Origin:** PROPOSED  
**Description:** W3C PROV Agent mirror row (interop).  
**Primary Key:** provenanceagent_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| provenanceagent_id | ulid | Y | Primary key. |
| prov_g_id | ulid | Y | Primary identifier (ULID recommended). |
| prov_g_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| prov_g_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| prov_g_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| prov_g_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| prov_g_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| prov_g_tags_json | json | N | Freeform tags / labels. |
| prov_g_notes | text | N | Human notes. |
| prov_g_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| prov_g_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| external_id | text | N |  |
| label | text | N |  |
| type | text | N |  |
| location | text | N |  |

## ProvenanceEntity

**Origin:** PROPOSED  
**Description:** W3C PROV Entity mirror row (interop).  
**Primary Key:** provenanceentity_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| provenanceentity_id | ulid | Y | Primary key. |
| prov_e_id | ulid | Y | Primary identifier (ULID recommended). |
| prov_e_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| prov_e_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| prov_e_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| prov_e_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| prov_e_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| prov_e_tags_json | json | N | Freeform tags / labels. |
| prov_e_notes | text | N | Human notes. |
| prov_e_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| prov_e_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| external_id | text | N |  |
| label | text | N |  |
| type | text | N |  |
| value_json | json | N |  |
| generated_at_utc | datetime_rfc3339 | N |  |
| location | text | N |  |

## ProvenanceRelation

**Origin:** PROPOSED  
**Description:** W3C PROV relations (wasGeneratedBy/used/wasDerivedFrom/etc.).  
**Primary Key:** provenancerelation_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| provenancerelation_id | ulid | Y | Primary key. |
| prov_r_id | ulid | Y | Primary identifier (ULID recommended). |
| prov_r_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| prov_r_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| prov_r_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| prov_r_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| prov_r_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| prov_r_tags_json | json | N | Freeform tags / labels. |
| prov_r_notes | text | N | Human notes. |
| prov_r_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| prov_r_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| rel_type | enum | Y |  |
| from_external_id | text | N |  |
| to_external_id | text | N |  |
| attrs_json | json | N |  |

## ROCrateContext

**Origin:** PROPOSED  
**Description:** RO-Crate root context (ro-crate-metadata.json).  
**Primary Key:** rocratecontext_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| rocratecontext_id | ulid | Y | Primary key. |
| rcc_id | ulid | Y | Primary identifier (ULID recommended). |
| rcc_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| rcc_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| rcc_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| rcc_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| rcc_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| rcc_tags_json | json | N | Freeform tags / labels. |
| rcc_notes | text | N | Human notes. |
| rcc_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| rcc_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| bundle_id | ulid | N |  |
| metadata_artifact_id | ulid | N |  |
| root_dataset_entity_id | ulid | N |  |
| profile | text | N |  |

## ROCrateEntity

**Origin:** PROPOSED  
**Description:** RO-Crate entity (JSON-LD node).  
**Primary Key:** rocrateentity_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| rocrateentity_id | ulid | Y | Primary key. |
| rce_id | ulid | Y | Primary identifier (ULID recommended). |
| rce_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| rce_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| rce_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| rce_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| rce_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| rce_tags_json | json | N | Freeform tags / labels. |
| rce_notes | text | N | Human notes. |
| rce_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| rce_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| bundle_id | ulid | N |  |
| crate_id | text | Y |  |
| type | text | N |  |
| name | text | N |  |
| description | text | N |  |
| jsonld_fragment | json | N |  |
| artifact_id | ulid | N |  |

## RedactionAction

**Origin:** PROPOSED  
**Description:** Planned or executed redaction step.  
**Primary Key:** redactionaction_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| redactionaction_id | ulid | Y | Primary key. |
| red_id | ulid | Y | Primary identifier (ULID recommended). |
| red_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| red_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| red_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| red_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| red_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| red_tags_json | json | N | Freeform tags / labels. |
| red_notes | text | N | Human notes. |
| red_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| red_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| artifact_id | ulid | Y |  |
| pii_item_id | ulid | N |  |
| action_type | enum | Y | box\\|text_replace\\|remove_page\\|metadata_strip |
| action_params_json | json | N |  |
| status | enum | N | PLANNED\\|DONE\\|SKIPPED |
| output_artifact_id | ulid | N |  |

## RetrievalEvent

**Origin:** PROPOSED  
**Description:** Audit of a retrieval run (vector + graph + rerank).  
**Primary Key:** retrievalevent_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| retrievalevent_id | ulid | Y | Primary key. |
| re_id | ulid | Y | Primary identifier (ULID recommended). |
| re_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| re_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| re_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| re_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| re_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| re_tags_json | json | N | Freeform tags / labels. |
| re_notes | text | N | Human notes. |
| re_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| re_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| run_id | ulid | N |  |
| context_pack_id | ulid | N |  |
| query | text | N |  |
| results_artifact_id | ulid | N |  |
| metrics_json | json | N |  |

## Run

**Origin:** PROPOSED  
**Description:** A deterministic run (R##) producing manifests, reports, cyclepacks.  
**Primary Key:** run_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| run_id | ulid | Y | Primary identifier (ULID recommended). |
| run_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| run_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| run_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| run_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| run_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| run_tags_json | json | N | Freeform tags / labels. |
| run_notes | text | N | Human notes. |
| run_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| run_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| series_id | text | N |  |
| run_name | text | Y |  |
| started_utc | datetime_rfc3339 | Y |  |
| ended_utc | datetime_rfc3339 | N |  |
| status | enum | Y | INIT\\|RUNNING\\|DEGRADED\\|FAILED\\|COMPLETED |
| inputs_manifest_artifact_id | ulid | N |  |
| outputs_manifest_artifact_id | ulid | N |  |
| run_ledger_artifact_id | ulid | N |  |
| event_log_artifact_id | ulid | N |  |
| checkpoint_artifact_id | ulid | N |  |
| tool_versions_json | json | N |  |
| idempotency_keys_json | json | N |  |

## RunArtifactLink

**Origin:** PROPOSED  
**Description:** Link table: Run ↔ Artifact.  
**Primary Key:** runartifactlink_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| runartifactlink_id | ulid | Y | Primary identifier (ULID recommended). |
| runartifactlink_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| runartifactlink_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| runartifactlink_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| runartifactlink_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| runartifactlink_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| runartifactlink_tags_json | json | N | Freeform tags / labels. |
| runartifactlink_notes | text | N | Human notes. |
| runartifactlink_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| runartifactlink_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| run_id | ulid | Y |  |
| artifact_id | ulid | Y |  |
| role | enum | N | input\\|output\\|report\\|checkpoint |

## RunEvent

**Origin:** PROPOSED  
**Description:** Event log row for runs/steps (audit).  
**Primary Key:** runevent_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| runevent_id | ulid | Y | Primary key. |
| evt_id | ulid | Y | Primary identifier (ULID recommended). |
| evt_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| evt_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| evt_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| evt_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| evt_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| evt_tags_json | json | N | Freeform tags / labels. |
| evt_notes | text | N | Human notes. |
| evt_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| evt_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| run_id | ulid | N |  |
| step_id | ulid | N |  |
| agent_id | ulid | N |  |
| event_time_utc | datetime_rfc3339 | Y |  |
| event_type | enum | Y |  |
| severity | enum | N | DEBUG\\|INFO\\|WARN\\|ERROR\\|FATAL |
| message | text | N |  |
| context_json | json | N |  |
| related_artifact_id | ulid | N |  |

## RunMetric

**Origin:** PROPOSED  
**Description:** Key/value metrics (for dashboards and ADD scoring).  
**Primary Key:** runmetric_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| runmetric_id | ulid | Y | Primary key. |
| metric_id | ulid | Y | Primary identifier (ULID recommended). |
| metric_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| metric_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| metric_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| metric_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| metric_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| metric_tags_json | json | N | Freeform tags / labels. |
| metric_notes | text | N | Human notes. |
| metric_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| metric_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| run_id | ulid | N |  |
| step_id | ulid | N |  |
| metric_name | text | Y |  |
| metric_value | float | N |  |
| metric_value_text | text | N |  |
| unit | text | N |  |
| dimensions_json | json | N |  |
| observed_utc | datetime_rfc3339 | N |  |

## RunStep

**Origin:** PROPOSED  
**Description:** A step within a Run (pipeline stage execution).  
**Primary Key:** runstep_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| runstep_id | ulid | Y | Primary key. |
| step_id | ulid | Y | Primary identifier (ULID recommended). |
| step_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| step_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| step_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| step_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| step_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| step_tags_json | json | N | Freeform tags / labels. |
| step_notes | text | N | Human notes. |
| step_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| step_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| run_id | ulid | Y |  |
| step_name | text | Y |  |
| step_seq | int | N |  |
| stage | enum | N | Atoms\\|Deltas\\|Signals\\|Scores\\|Gates\\|Actions\\|Vehicles\\|Graph\\|Packaging |
| started_utc | datetime_rfc3339 | N |  |
| ended_utc | datetime_rfc3339 | N |  |
| status | enum | N | OK\\|WARN\\|FAIL\\|SKIP |
| input_artifacts_json | json | N |  |
| output_artifacts_json | json | N |  |
| metrics_json | json | N |  |
| error_artifact_id | ulid | N |  |

## SBOMCycloneDXComponent

**Origin:** PROPOSED  
**Description:** CycloneDX component node (SBOM).  
**Primary Key:** sbomcyclonedxcomponent_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| sbomcyclonedxcomponent_id | ulid | Y | Primary key. |
| cdx_id | ulid | Y | Primary identifier (ULID recommended). |
| cdx_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| cdx_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| cdx_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| cdx_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| cdx_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| cdx_tags_json | json | N | Freeform tags / labels. |
| cdx_notes | text | N | Human notes. |
| cdx_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| cdx_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| bundle_id | ulid | N |  |
| bom_ref | text | Y |  |
| type | text | N |  |
| name | text | N |  |
| version | text | N |  |
| purl | text | N |  |
| cpe | text | N |  |
| hashes_json | json | N |  |
| licenses_json | json | N |  |

## SBOMSPDXPackage

**Origin:** PROPOSED  
**Description:** SPDX package node (SBOM).  
**Primary Key:** sbomspdxpackage_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| sbomspdxpackage_id | ulid | Y | Primary key. |
| spdxp_id | ulid | Y | Primary identifier (ULID recommended). |
| spdxp_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| spdxp_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| spdxp_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| spdxp_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| spdxp_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| spdxp_tags_json | json | N | Freeform tags / labels. |
| spdxp_notes | text | N | Human notes. |
| spdxp_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| spdxp_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| bundle_id | ulid | N |  |
| spdx_id | text | Y |  |
| name | text | N |  |
| version_info | text | N |  |
| download_location | text | N |  |
| license_concluded | text | N |  |
| license_declared | text | N |  |
| checksums_json | json | N |  |
| external_refs_json | json | N |  |

## SLSAProvenance

**Origin:** PROPOSED  
**Description:** SLSA provenance statement (normalized).  
**Primary Key:** slsaprovenance_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| slsaprovenance_id | ulid | Y | Primary key. |
| slsa_id | ulid | Y | Primary identifier (ULID recommended). |
| slsa_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| slsa_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| slsa_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| slsa_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| slsa_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| slsa_tags_json | json | N | Freeform tags / labels. |
| slsa_notes | text | N | Human notes. |
| slsa_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| slsa_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| bundle_id | ulid | N |  |
| predicate_type | text | N |  |
| subject_json | json | N |  |
| builder_json | json | N |  |
| build_type | text | N |  |
| invocation_json | json | N |  |
| metadata_json | json | N |  |
| materials_json | json | N |  |

## Schedule

**Origin:** PROPOSED  
**Description:** Recurring schedule definition (e.g., 4x/day harvest).  
**Primary Key:** schedule_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| schedule_id | ulid | Y | Primary key. |
| sched_id | ulid | Y | Primary identifier (ULID recommended). |
| sched_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| sched_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| sched_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| sched_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| sched_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| sched_tags_json | json | N | Freeform tags / labels. |
| sched_notes | text | N | Human notes. |
| sched_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| sched_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| schedule_name | text | Y |  |
| cron | text | N |  |
| timezone | text | N |  |
| is_enabled | bool | N |  |
| target_pipeline | text | N |  |
| params_json | json | N |  |
| last_run_id | ulid | N |  |
| next_due_utc | datetime_rfc3339 | N |  |

## ServiceAttempt

**Origin:** PROPOSED  
**Description:** A concrete attempt instance (date, carrier, tracking).  
**Primary Key:** serviceattempt_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| serviceattempt_id | ulid | Y | Primary key. |
| svca_id | ulid | Y | Primary identifier (ULID recommended). |
| svca_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| svca_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| svca_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| svca_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| svca_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| svca_tags_json | json | N | Freeform tags / labels. |
| svca_notes | text | N | Human notes. |
| svca_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| svca_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| service_plan_id | ulid | Y |  |
| attempted_utc | datetime_rfc3339 | N |  |
| carrier | text | N |  |
| tracking_number | text | N |  |
| result | enum | N | SENT\\|DELIVERED\\|RETURNED\\|REFUSED\\|UNKNOWN |
| proof_artifact_id | ulid | N |  |

## ServicePlan

**Origin:** PROPOSED  
**Description:** Planned service chain for a filing (methods, addresses, deadlines).  
**Primary Key:** serviceplan_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| serviceplan_id | ulid | Y | Primary key. |
| svc_id | ulid | Y | Primary identifier (ULID recommended). |
| svc_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| svc_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| svc_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| svc_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| svc_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| svc_tags_json | json | N | Freeform tags / labels. |
| svc_notes | text | N | Human notes. |
| svc_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| svc_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| case_id | ulid | N |  |
| filing_id | ulid | N |  |
| served_party_link_id | ulid | N |  |
| method | enum | N | mail\\|personal\\|email\\|mifile\\|publication |
| address_id | ulid | N |  |
| deadline_utc | datetime_rfc3339 | N |  |
| status | enum | N | PLANNED\\|IN_PROGRESS\\|COMPLETE\\|FAILED |
| notes | text | N |  |

## ServiceProof

**Origin:** PROPOSED  
**Description:** Service proof object (receipt, affidavit of service).  
**Primary Key:** serviceproof_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| serviceproof_id | ulid | Y | Primary key. |
| svcp_id | ulid | Y | Primary identifier (ULID recommended). |
| svcp_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| svcp_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| svcp_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| svcp_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| svcp_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| svcp_tags_json | json | N | Freeform tags / labels. |
| svcp_notes | text | N | Human notes. |
| svcp_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| svcp_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| service_attempt_id | ulid | Y |  |
| proof_type | enum | N | receipt\\|affidavit\\|mifile_confirmation |
| artifact_id | ulid | N |  |
| verified | bool | N |  |
| verified_by_agent_id | ulid | N |  |
| verified_utc | datetime_rfc3339 | N |  |

## Signature

**Origin:** PROPOSED  
**Description:** Signature / attestation for a bundle (optional, free tooling only).  
**Primary Key:** signature_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| signature_id | ulid | Y | Primary key. |
| sig_id | ulid | Y | Primary identifier (ULID recommended). |
| sig_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| sig_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| sig_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| sig_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| sig_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| sig_tags_json | json | N | Freeform tags / labels. |
| sig_notes | text | N | Human notes. |
| sig_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| sig_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| bundle_id | ulid | N |  |
| artifact_id | ulid | N |  |
| sig_type | enum | N | minisign\\|cosign\\|pgp |
| public_key_ref | text | N |  |
| signature_artifact_id | ulid | N |  |
| attestation_artifact_id | ulid | N |  |
| signed_utc | datetime_rfc3339 | N |  |

## Statement

**Origin:** PROPOSED  
**Description:** A statement (utterance/claim) attributable to a speaker or source; may be true/false/unknown.  
**Primary Key:** statement_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| statement_id | ulid | Y | Primary key. |
| stmt_id | ulid | Y | Primary identifier (ULID recommended). |
| stmt_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| stmt_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| stmt_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| stmt_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| stmt_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| stmt_tags_json | json | N | Freeform tags / labels. |
| stmt_notes | text | N | Human notes. |
| stmt_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| stmt_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| case_id | ulid | N |  |
| speaker_person_id | ulid | N |  |
| speaker_role | text | N |  |
| statement_text | text | Y |  |
| statement_date | date | N |  |
| context | text | N |  |
| source_atom_id | ulid | N |  |
| classification | enum | N | assertion/denial/accusation |

## StatementFactLink

**Origin:** PROPOSED  
**Description:** Link table: Statement ↔ Fact.  
**Primary Key:** statementfactlink_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| statementfactlink_id | ulid | Y | Primary identifier (ULID recommended). |
| statementfactlink_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| statementfactlink_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| statementfactlink_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| statementfactlink_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| statementfactlink_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| statementfactlink_tags_json | json | N | Freeform tags / labels. |
| statementfactlink_notes | text | N | Human notes. |
| statementfactlink_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| statementfactlink_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| stmt_id | ulid | Y |  |
| fact_id | ulid | Y |  |
| relation | enum | N | supports\\|contradicts\\|duplicates |

## Task

**Origin:** PROPOSED  
**Description:** A human-facing work item (draft motion, build pack, ingest authority).  
**Primary Key:** task_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| task_id | ulid | Y | Primary identifier (ULID recommended). |
| task_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| task_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| task_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| task_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| task_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| task_tags_json | json | N | Freeform tags / labels. |
| task_notes | text | N | Human notes. |
| task_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| task_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| case_id | ulid | N |  |
| task_type | enum | Y |  |
| title | text | N |  |
| description | text | N |  |
| status | enum | N | OPEN\\|IN_PROGRESS\\|DONE\\|BLOCKED |
| priority | int | N |  |
| due_utc | datetime_rfc3339 | N |  |
| assigned_person_id | ulid | N |  |
| context_pack_id | ulid | N |  |

## Transcript

**Origin:** PROPOSED  
**Description:** Hearing transcript (logical).  
**Primary Key:** transcript_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| transcript_id | ulid | Y | Primary key. |
| tx_id | ulid | Y | Primary identifier (ULID recommended). |
| tx_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| tx_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| tx_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| tx_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| tx_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| tx_tags_json | json | N | Freeform tags / labels. |
| tx_notes | text | N | Human notes. |
| tx_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| tx_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| case_id | ulid | Y |  |
| hearing_id | ulid | Y |  |
| requested_date | date | N |  |
| received_date | date | N |  |
| vendor | text | N |  |
| pages | int | N |  |
| cost | money | N |  |
| audio_artifact_id | ulid | N |  |
| pdf_artifact_id | ulid | N |  |
| text_extract_artifact_id | ulid | N |  |
| quote_anchor_index_artifact_id | ulid | N |  |
| objection_offer_proof_matrix_artifact_id | ulid | N |  |

## TranscriptRequest

**Origin:** PROPOSED  
**Description:** Request for transcript (tracking).  
**Primary Key:** transcriptrequest_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| transcriptrequest_id | ulid | Y | Primary key. |
| trq_id | ulid | Y | Primary identifier (ULID recommended). |
| trq_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| trq_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| trq_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| trq_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| trq_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| trq_tags_json | json | N | Freeform tags / labels. |
| trq_notes | text | N | Human notes. |
| trq_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| trq_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| case_id | ulid | Y |  |
| hearing_id | ulid | N |  |
| requested_from_person_id | ulid | N | court reporter/clerk |
| requested_utc | datetime_rfc3339 | N |  |
| due_utc | datetime_rfc3339 | N |  |
| status | enum | N | REQUESTED\\|PAID\\|RECEIVED\\|OVERDUE |
| receipt_artifact_id | ulid | N |  |
| transcript_id | ulid | N |  |

## TranscriptSegment

**Origin:** PROPOSED  
**Description:** Timestamped / page-line segment inside a transcript.  
**Primary Key:** transcriptsegment_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| transcriptsegment_id | ulid | Y | Primary key. |
| trs_id | ulid | Y | Primary identifier (ULID recommended). |
| trs_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| trs_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| trs_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| trs_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| trs_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| trs_tags_json | json | N | Freeform tags / labels. |
| trs_notes | text | N | Human notes. |
| trs_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| trs_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| transcript_id | ulid | Y |  |
| page_start | int | N |  |
| line_start | int | N |  |
| page_end | int | N |  |
| line_end | int | N |  |
| time_start | text | N |  |
| time_end | text | N |  |
| speaker_person_id | ulid | N |  |
| text | text | N |  |
| quote_anchor_id | ulid | N |  |

## VEXStatement

**Origin:** PROPOSED  
**Description:** Vulnerability Exploitability eXchange statement (generic).  
**Primary Key:** vexstatement_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| vexstatement_id | ulid | Y | Primary key. |
| vex_id | ulid | Y | Primary identifier (ULID recommended). |
| vex_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| vex_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| vex_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| vex_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| vex_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| vex_tags_json | json | N | Freeform tags / labels. |
| vex_notes | text | N | Human notes. |
| vex_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| vex_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| bundle_id | ulid | N |  |
| vuln_id | text | Y |  |
| product_id | text | N |  |
| status | text | N |  |
| justification | text | N |  |
| action_statement | text | N |  |
| impact_statement | text | N |  |
| timestamp | datetime_rfc3339 | N |  |

## Vehicle

**Origin:** PROPOSED  
**Description:** Procedural vehicle (motion/complaint/appeal form) forms-first.  
**Primary Key:** vehicle_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| vehicle_id | ulid | Y | Primary key. |
| veh_id | ulid | Y | Primary identifier (ULID recommended). |
| veh_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| veh_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| veh_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| veh_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| veh_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| veh_tags_json | json | N | Freeform tags / labels. |
| veh_notes | text | N | Human notes. |
| veh_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| veh_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| vehicle_name | text | Y |  |
| vehicle_type | enum | N | Motion, Appeal, JTC complaint, etc. |
| scao_form_id | ulid | N |  |
| trigger_conditions_json | json | N |  |
| elements_grid_artifact_id | ulid | N |  |
| default_deadlines_json | json | N |  |

## VehicleMap

**Origin:** PROPOSED  
**Description:** Mapping of relief → form/vehicle → authority → proof obligations.  
**Primary Key:** vehiclemap_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| vehiclemap_id | ulid | Y | Primary key. |
| vm_id | ulid | Y | Primary identifier (ULID recommended). |
| vm_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| vm_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| vm_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| vm_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| vm_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| vm_tags_json | json | N | Freeform tags / labels. |
| vm_notes | text | N | Human notes. |
| vm_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| vm_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| case_id | ulid | N |  |
| vehicle_id | ulid | N |  |
| relief_sought | text | N |  |
| form_code | text | N |  |
| mcr_gate_json | json | N |  |
| elements_json | json | N |  |
| po_ids_json | json | N |  |
| service_plan_id | ulid | N |  |
| deadline_trigger_id | ulid | N |  |

## VehiclePropositionLink

**Origin:** PROPOSED  
**Description:** Link table: Vehicle ↔ Proposition.  
**Primary Key:** vehiclepropositionlink_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| vehiclepropositionlink_id | ulid | Y | Primary identifier (ULID recommended). |
| vehiclepropositionlink_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| vehiclepropositionlink_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| vehiclepropositionlink_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| vehiclepropositionlink_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| vehiclepropositionlink_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| vehiclepropositionlink_tags_json | json | N | Freeform tags / labels. |
| vehiclepropositionlink_notes | text | N | Human notes. |
| vehiclepropositionlink_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| vehiclepropositionlink_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| vehicle_id | ulid | Y |  |
| prop_id | ulid | Y |  |
| use_type | enum | N | elements\\|standard\\|procedure |

## WARCRecord

**Origin:** PROPOSED  
**Description:** WARC record (capture unit) normalized header set.  
**Primary Key:** warcrecord_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| warcrecord_id | ulid | Y | Primary key. |
| wr_id | ulid | Y | Primary identifier (ULID recommended). |
| wr_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| wr_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| wr_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| wr_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| wr_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| wr_tags_json | json | N | Freeform tags / labels. |
| wr_notes | text | N | Human notes. |
| wr_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| wr_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_id | ulid | Y |  |
| bundle_id | ulid | N |  |
| warc_file_artifact_id | ulid | N |  |
| warc_record_id | text | N |  |
| warc_type | text | N |  |
| warc_date | datetime_rfc3339 | N |  |
| content_type | text | N |  |
| target_uri | text | N |  |
| payload_digest | text | N |  |
| block_digest | text | N |  |
| content_length | bigint | N |  |
| headers_json | json | N |  |

## Workspace

**Origin:** PROPOSED  
**Description:** Top-level container for a LitigationOS universe (drives, cases, authority snapshots, runs).  
**Primary Key:** workspace_id  

| Field | Type | Req | Notes |
|---|---|---:|---|
| workspace_id | ulid | Y | Primary identifier (ULID recommended). |
| workspace_created_utc | datetime_rfc3339 | Y | Created timestamp (UTC). |
| workspace_updated_utc | datetime_rfc3339 | N | Last updated timestamp (UTC). |
| workspace_created_by_agent_id | ulid | N | Agent/worker that created the record. |
| workspace_updated_by_agent_id | ulid | N | Agent/worker that last updated the record. |
| workspace_status | enum | N | Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.). |
| workspace_tags_json | json | N | Freeform tags / labels. |
| workspace_notes | text | N | Human notes. |
| workspace_integrity_key | text | N | IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec. |
| workspace_source_ref | text | N | Canonical source pointer (Vault CID / path / locator). |
| workspace_name | text | Y |  |
| canonical_drive_root | text | N | Typically F:/ for litigation data; D:/ for revenue. |
| google_drive_roots_json | json | N | e.g., EDS-USB, Litigation_OS$. |
| vault_base_url | text | N | e.g., http://localhost:8899 |
| neo4j_uri | text | N |  |
| neo4j_db | text | N |  |
| default_timezone | text | N | IANA tz |
| policy_bundle_ref | text | N | Active policy-as-code bundle |

