# LATENT_CORES_CATALOG_v0008
generated_utc: 2026-01-19T02:46:47Z

## Shipped cores (implemented in-bundle)
- CORE_AUTHORITY_SNAPSHOT_BUILDER (TOOLS/litos_authority_snapshot_builder.py + SCHEMA/authority/* + AUTHORITY/snapshots/* demo)
- CORE_FORMS_CATALOG_BUILDER (TOOLS/litos_forms_catalog_builder.py + SCHEMA/forms/forms_catalog.schema.json + FORMS/catalog/MI_FORMS_v0008/index.json)
- CORE_PDF_EXTRACT (TOOLS/litos_pdf_extract.py + SOURCES/extracted/*.txt)
- CORE_SOURCEINDEX_MI (TOOLS/litos_link_catalog.py + DATA/mi_source_index_v0008.*)
- CORE_GRAPH_CONTRACTS (SCHEMA/contracts/* + TOOLS/litos_graph_contracts_validate.py)

## Proposed cores (candidates extracted from operator manuals / blueprints)
Format: PROPOSED_CORE_ID — purpose — contracts — outputs
- CORE_AUTHORITY_LAWPACK_MANAGER — manage official MI packs (MCR/MCL/MRE/Benchbooks/Forms) with manifests+receipts — LawPackManifest schema — AUTHORITY/packs/<pack_id>/...
- CORE_AUTHORITY_PINMAP_VERIFIER — QuoteLock promotion by independent extractors — QuoteLock contract — QUOTES/verified.jsonl + pin cross-check report
- CORE_FORMS_OVERLAY_ENGINE — PDF bbox + DOCX mergefield overlays governed by form version — overlay schemas — FORMS/overlays/<form_id>/vNNNN/*
- CORE_NEO4J_INGEST_ORCHESTRATOR — import/export graph snapshots w/ contract validation + replay receipts — GraphContracts — EXPORTS/<run_id>/receipt.json
- CORE_REPLAYABLE_JOB_QUEUE — crash-safe queue w/ idempotent steps and event log — Replay contract — LOGS/event_log.jsonl + RUNS/<run_id>/state.json
- CORE_PERMISSION_CAPTOKENS — capability-token signer/validator to prevent LLM mutation — CapabilityToken schema — EVAL/capabilities/*.jsonl
- CORE_GOVERNOR_PILLAR — single orchestrator that runs HARVEST→ANALYZE→VALIDATE→BUNDLE — RunManifest schema — MANIFEST/run_<id>.json
- CORE_RCLONE_WATCHER — scheduled delta ingestion from gdrive mounts (operator-controlled) — Watcher contract — LOGS/watch_events.jsonl
- CORE_TIKA_EXTRACTOR — content extraction pipeline w/ receipts — ExtractReceipt schema — SOURCES/extracted/* + receipts
- CORE_Ollama_LocalLLM — local inference adapter (no external API) — LLMAdapter contract — RETRIEVAL/llm_runs/*.jsonl

## High-signal lines (evidence for proposed cores; not quotations for filing)
001. [Superpin Codex Instructions.txt] precedent suppression gates, Neo4j schema locks/constraints/fulltext incl. AuthorityTriple required
002. [Branch · Superpin Codex Instructions-2.txt] Appended and generated v0026 (new appendices LM–LW: SCAO Forms Autoﬁll+Validation with ﬁeld → pin → authority proof reports; COA/MSC/JTC micro-
003. [Branch · Superpin Codex Instructions-2.txt] resistant posture; record-survival discipline.Always:MI-only authority+pinpoints+forms-ﬁrst; fail-closed gates.Default
004. [Branch · Superpin Codex Instructions-2.txt] without overriding Truth/Authority/Forms/PCW/PCG gates. SUPERPIN CODEX(chat)
005. [LitigationOS Graph + LLM Blueprint for MEEK Tracks.md] A1.Core invariants:MI-only authority lock;Truth-Lock;Forms-first VehicleMap;Pinpoints;One-bundle rule;Continue=accretive;Record-first;Denial-proofing.
006. [LitigationOS Graph + LLM Blueprint for MEEK Tracks.md] AI3.VehicleSelectorAI:(Relief objective+posture+AuthorityTriples+Forms)→Vehicle candidates + PO list (human gate)
007. [LitigationOS Graph + LLM Blueprint for MEEK Tracks.md] LM0 Objective:autopopulate SCAO/FOC/MC forms and validate field-level correctness using pinned facts and governing instructions;emit a “form proof report” (field→pins→authority).
008. [Superpin Codex Instructions.txt] authority+pinpoints+forms-ﬁrst; fail-closed gates.Default
009. [Branch · Superpin Codex Instructions-2.txt] Add Neo4j “brains/blooms” schema migrations and seed loaders (while keeping MI-only authority constraints in the legal layer).
010. [Branch · Superpin Codex Instructions-2.txt] AuthoritySnapshot + Forms-First + PO ledger + QuoteLock + replayability:
011. [Branch · Superpin Codex Instructions-2.txt] staying locked to AuthoritySnapshot + Forms-First + PO ledger + QuoteLock + replayability. This cycle adds the missing “procedural engines” layer:
012. [LitigationOS Graph + LLM Blueprint for MEEK Tracks.md] - **Explore** when foundation is weak: ingest missing authority/records, harden schema, improve validators, add replayability.
013. [LitigationOS Graph + LLM Blueprint for MEEK Tracks.md] <!-- APPEND-ONLY PATCH v2026.01.16.5 | Adds: AuthoritySnapshot ingestion from COURT RULES.zip + FormsMirror module + LegacyEdges importer + Manifest schema binding -->
014. [LitigationOS Graph + LLM Blueprint for MEEK Tracks.md] K1 FormStore schema (Neo4j + SQLite)
015. [Branch · Superpin Codex Instructions-2.txt] A hard-invariant + multi-objective scoring governor that forces every cycle to trend upward without violating Truth/Authority/Forms-ﬁrst/PCW → PCG, and
016. [Branch · Superpin Codex Instructions-2.txt] Adds concrete daemon roles (ﬁle delta watcher, authority snapshot watcher, queue runner, packaging runner).
017. [Branch · Superpin Codex Instructions-2.txt] Appended APPENDIX v2026-01-18.30 (P681–P760) with “above-and-beyond” cores that do not weaken the required stack (AuthoritySnapshot + Forms-First
018. [Branch · Superpin Codex Instructions-2.txt] Appended APPENDIX v2026-01-18.31 (P761–P860) with “Graph Brain becomes operational” deltas while staying fully bound to AuthoritySnapshot + Forms-
019. [Branch · Superpin Codex Instructions-2.txt] Appended APPENDIX v2026-01-18.33 (P961–P1060) with “Court-ready assembly + autonomous ops” deltas—still fully bound to AuthoritySnapshot + Forms-
020. [Branch · Superpin Codex Instructions-2.txt] AuthoritySnapshot Extender to support court-level collections (trial/appellate/JTC/benchbooks/forms) with pin-resolver reopen recipes.
021. [Branch · Superpin Codex Instructions-2.txt] MCR/MCL/MRE,MJI benchbooks,SCAO MC/FOC forms+instr,controlling orders).PINPOINTS(Fact:{path+pg/ln/Bates|time};Law:{src+subsec+eﬀ-
022. [Branch · Superpin Codex Instructions-2.txt] MI Procedure Library (MPL) as executable VehicleSpecs (relief → vehicle → forms → authority pins → elements/POs → deadlines → service → record
023. [Branch · Superpin Codex Instructions-2.txt] SCAO+FOC+MC+etc court forms, crosswired to their governing MCR and/or MCL. The graph will also map out all judical/court actions & procedures &
024. [Branch · Superpin Codex Instructions-2.txt] Write Protocol, Neo4j bootstrap constraints-ﬁrst discipline, Bloom theme pack lane, MinerU-inspired local PDF → MD/JSON rebuild contract, Tables/Forms
025. [Branch · Superpin Codex Instructions-2.txt] authority/forms/benchbooks+eﬀ-dates only.CODE:mono,deterministic,logged,dry-run/tests; no patch/merge;
026. [Branch · Superpin Codex Instructions-2.txt] continue, branch out into diﬀerent areas, above and beyond, high signal deltas and3 AuthoritySnapshot + Forms-First + PO ledger + QuoteLock +
027. [Branch · Superpin Codex Instructions-2.txt] core/ lanes (governor, stores, graph, evidence, authority, forms, PO, QuoteLock, packets, security, tests)
028. [Branch · Superpin Codex Instructions-2.txt] shards only); venue/local practice gates (source-bound); SCAO forms automation ceiling (schema-backed, no placeholders); Appellate + MSC + JTC pack
029. [Branch · Superpin Codex Instructions-2.txt] v0033 appended (Multi-Store governance G/V/K + migrations, caselaw HoldingAtomization + negative-precedent suppression gates, Neo4j schema
030. [FRED PRIME LEGAL INTELLIGENCE OPERATIONS MANUAL.txt] # V4.11 Upgrades (Authority Graph Intake + Add-on → Neo4j Bridge)
031. [FRED PRIME LEGAL INTELLIGENCE OPERATIONS MANUAL.txt] # scripts/authority_edges_to_neo4j.py
032. [FRED PRIME LEGAL INTELLIGENCE OPERATIONS MANUAL.txt] (scripts/"authority_edges_to_neo4j.py").write_text(authority_edges_to_neo4j, encoding="utf-8")
033. [FRED PRIME LEGAL INTELLIGENCE OPERATIONS MANUAL.txt] - `AUTHORITY` (MCL/MCR/MRE/Benchbook/SCAO forms)
034. [FRED PRIME LEGAL INTELLIGENCE OPERATIONS MANUAL.txt] - outputs/authority_edges/20260114_AUTH_EDGES/authorities_edges_neo4j.csv
035. [FRED PRIME LEGAL INTELLIGENCE OPERATIONS MANUAL.txt] - scripts/authority_edges_to_neo4j.py
036. [FRED PRIME LEGAL INTELLIGENCE OPERATIONS MANUAL.txt] 0.3 FORMS-FIRST:No drafting unless VehicleMap exists for relief target:relief→vehicle/form→authority/standard→prereqs→deadlines→service→exhibits→risks→fallback.
037. [FRED PRIME LEGAL INTELLIGENCE OPERATIONS MANUAL.txt] 2.3 AuthorityRef (MI-ONLY):types{MCR,MCL,MRE,MSC_ADMIN_ORDER,SCAO_FORM,SCAO_FORM_INSTR,MI_BENCHBOOK,MJI,MI_CASELAW,(optional)SCAO_GUIDE if snapshotted}.
038. [FRED PRIME LEGAL INTELLIGENCE OPERATIONS MANUAL.txt] Authority precedence:MSC caselaw/Admin Orders > statutes/court rules > COA caselaw > benchbooks/MJI/forms instructions.
039. [FRED PRIME LEGAL INTELLIGENCE OPERATIONS MANUAL.txt] Cycle6 VEHICLEMAP+POs:map relief targets to vehicles/forms;instantiate POs with authority pinpoints;bind atoms/findings to satisfy;assurance scoring.
040. [FRED PRIME LEGAL INTELLIGENCE OPERATIONS MANUAL.txt] Legal propositions may use only: MCR, MCL, MRE, Michigan Benchbooks, SCAO/MC/FOC forms + instructions, controlling MI caselaw.
041. [FRED PRIME LEGAL INTELLIGENCE OPERATIONS MANUAL.txt] MI Authority Lock (legal propositions only): ONLY MCR/MCL/MRE, Michigan Benchbooks, SCAO/MC/FOC forms+instructions, and controlling orders.
042. [FRED PRIME LEGAL INTELLIGENCE OPERATIONS MANUAL.txt] MI5 AUTHORITY SNAPSHOT:Locked PDFs/versions of MI authority sources (MCR/MCL/MRE/Benchbooks/SCAO forms) with auth_snapshot_id.Required for PO validity.
043. [FRED PRIME LEGAL INTELLIGENCE OPERATIONS MANUAL.txt] Types allowed:{MCR,MCL,MRE,MSC_ADMIN_ORDER,SCAO_FORM,SCAO_FORM_INSTR,MI_BENCHBOOK,MJI,MI_CASELAW,(optional)SCAO_GUIDE if snapshotted}.
044. [FRED PRIME LEGAL INTELLIGENCE OPERATIONS MANUAL.txt] authority_edges_to_neo4j = r'''#!/usr/bin/env python3
045. [FRED PRIME LEGAL INTELLIGENCE OPERATIONS MANUAL.txt] subprocess.run([sys.executable, str(scripts/"authority_edges_to_neo4j.py"),
046. [LitigationOS Graph + LLM Blueprint for MEEK Tracks.md] "Build Win64 LitigationOS+GUI+Neo4j Bloom graph(courts/juris,forms↔rules,vehicles/deadlines/service,evidence,appeal/JTC)."
047. [LitigationOS Graph + LLM Blueprint for MEEK Tracks.md] "Forms/Vehicle-first:Relief→Form/Vehicle→Authority→Prereqs/fees/bonds→Deadlines→Service→Exhibits→Risks→Fallback."
048. [LitigationOS Graph + LLM Blueprint for MEEK Tracks.md] - **G‑Store**: Neo4j canonical graph (facts, evidence pins, authority pins, vehicles, POs, docket, entities).
049. [LitigationOS Graph + LLM Blueprint for MEEK Tracks.md] - Authority PDFs/forms snapshots (MCR, benchbooks, SCAO forms, canons/JTC rules) with effective dates
050. [LitigationOS Graph + LLM Blueprint for MEEK Tracks.md] - AuthorityQuery (rules/forms/standards)
051. [LitigationOS Graph + LLM Blueprint for MEEK Tracks.md] - Fix:re-export nodes CSV from source Neo4j OR regenerate from AuthoritySnapshot chunks OR rebuild from subset.json nodes.
052. [LitigationOS Graph + LLM Blueprint for MEEK Tracks.md] - Shared:Authority,CaseLaw,Forms,VenueProfiles,ModelRegistry
053. [LitigationOS Graph + LLM Blueprint for MEEK Tracks.md] - Step1:Neo4j FULLTEXT query across DocPage.text,TxSeg.text,Quote.text,AuthorityChunk.text
054. [LitigationOS Graph + LLM Blueprint for MEEK Tracks.md] - citation patterns (MCR/MCL/MRE,SCAO forms,benchbook refs,reporter cites)
055. [LitigationOS Graph + LLM Blueprint for MEEK Tracks.md] 0.5 FORMS-FIRST/VEHICLE-FIRST:Relief→Vehicle/Form→Authority→Prereqs/Deadlines/Service→Exhibits→Risks→Fallback. Do not draft before vehicle map.
056. [LitigationOS Graph + LLM Blueprint for MEEK Tracks.md] 6) “Schema Migration Assistant”: generates and validates Neo4j migrations with rollback proofs.
057. [LitigationOS Graph + LLM Blueprint for MEEK Tracks.md] A5 FORMS-FIRST/VEHICLE-FIRST:Relief→Vehicle/Form→Authority→Prereqs/fees/bonds→Deadlines→Service/Notice→Exhibits→Risks→Fallback. Do not draft before VehicleMap+POs.
058. [LitigationOS Graph + LLM Blueprint for MEEK Tracks.md] A5 FORMS-FIRST/VEHICLE-FIRST:Relief→Vehicle/Form→Authority→Prereqs/fees/bonds→Deadlines→Service/Notice→Exhibits→Risks→Fallback. Do not draft before VehicleMap.
059. [LitigationOS Graph + LLM Blueprint for MEEK Tracks.md] AW4 CI gates(GitHub Actions/local runner parity):lint(type+format),unit,smoke,integration (Neo4j ephemeral),schema-migrate,dry-run harvest,artifact verify;fail-closed.
060. [LitigationOS Graph + LLM Blueprint for MEEK Tracks.md] BD3 Multi-bloom composition:Blooms={Courts&Jurisdictions,Authority&Forms,Procedures/Vehicles,Case/Track/Evidence};toggle layers;cross-bloom edges.
061. [LitigationOS Graph + LLM Blueprint for MEEK Tracks.md] BI1 Corpus:per-county folder /AUTH/LOCAL/<county>/;LAO nodes in graph with effective dates;mapping to MCR vehicles/forms.
062. [LitigationOS Graph + LLM Blueprint for MEEK Tracks.md] BKR3.For vehicle automation:need current SCAO form set + local Muskegon procedural preferences captured in a “LocalRulePack” file (as evidence/authority snapshot).
063. [LitigationOS Graph + LLM Blueprint for MEEK Tracks.md] D1.1 Lexical: Neo4j fulltext index over EvidenceAtom.text + AuthorityChunk.text (plus optional OpenSearch if added later).
064. [LitigationOS Graph + LLM Blueprint for MEEK Tracks.md] DX1 Service split:Gateway API,Gatekeeper,JobQueue,Neo4j,VectorIndex,CAAV store,LLM server,UI.
065. [LitigationOS Graph + LLM Blueprint for MEEK Tracks.md] F7 COURT EXPORT SAFE MODE:Export bundles include only necessary derived PDFs/forms plus manifest proof; never leak unrelated assets; strict track scoping.
066. [LitigationOS Graph + LLM Blueprint for MEEK Tracks.md] HD3 “Forms-first hard rule”:if a form exists it is primary;non-form motions require template justification and authority.
067. [LitigationOS Graph + LLM Blueprint for MEEK Tracks.md] IZ0 Objective:maintain a governed MI authority corpus (MCR/MCL/MRE/benchbooks/forms/local AOs) with edition locking,version pinning,retroactivity awareness,quote policy.
068. [LitigationOS Graph + LLM Blueprint for MEEK Tracks.md] Inputs: MI authority PDFs/forms/benchbooks; effective dates
069. [LitigationOS Graph + LLM Blueprint for MEEK Tracks.md] J1.2 AuthoritySource{id, snapshot_id, type∈{MCR,MCL,MRE,BENCHBOOK,SCAO_FORM,GUIDELINE,OTHER}, title, file_name, file_sha256, pages, build_time_utc}
070. [LitigationOS Graph + LLM Blueprint for MEEK Tracks.md] JZ3 Resolution hierarchy (MI-first):Constitution/controlling statutes→MCR→binding appellate caselaw→SCAO forms/instructions→benchbook guidance.
071. [LitigationOS Graph + LLM Blueprint for MEEK Tracks.md] K2.2 Ingest: forms → Document/EvidenceItem(kind="form") + Form node + AuthoritySource(type="SCAO_FORM" or "LOCAL_COURT_FORM")
072. [LitigationOS Graph + LLM Blueprint for MEEK Tracks.md] MU0 Objective:build “research packs” per issue/lane with pinned authority shards,case law holdings,forms,venue practice notes;portable and cite-ready.
073. [Superpin Codex Instructions.txt] CoT).WEB:oﬃcial MI authority/forms/benchbooks+eﬀ-dates
074. [Superpin Codex Instructions.txt] MCR/MCL/MRE,MJI benchbooks,SCAO MC/FOC forms+instr,controlling orders).PINPOINTS(Fact:
075. [Superpin Codex Instructions.txt] nodes; governing MCR/MCL as edges; vehicle templates auto-select correct forms).
076. [Superpin Codex Instructions.txt] shards only); venue/local practice gates (source-bound); SCAO forms automation ceiling (schema-
077. [Superpin Codex Instructions.txt] those courts and jurisdictions SCAO+FOC+MC+etc court forms, crosswired to their governing MCR
078. [TRUE MASTER operations.txt] * **Forms Store**: form definitions + field maps + authority links
079. [TRUE MASTER operations.txt] * mbp_authority (MI authority/forms/caselaw shards)
080. [TRUE MASTER operations.txt] 14. **Forms Overlay Engine** (SCAO form mapping; form↔authority edges; required fields)
081. [TRUE MASTER operations.txt] 3. authority_refresh → shard authority + forms + caselaw
082. [TRUE MASTER operations.txt] Authority anchor detection (MCR/MCL/MRE/forms/case names)
083. [TRUE MASTER operations.txt] Automatically conforms to MCR 9.200+ expectations.
084. [TRUE MASTER operations.txt] authority_universe: MI-only primary sources (MCR/MCL/MRE/benchbooks/forms); unpublished COA persuasive-only per MCR 7.215(C)(1).
085. [TRUE MASTER operations.txt] write_layer_report(run_dir, "L300_AUTHORITY_FORMS_CASELAW", {"stats": {"authority_refresh_enabled": auth_enabled}})
086. [Branch · Superpin Codex Instructions-2.txt] Appended and generated v0021 (new appendices IY–JJ: SCAO Forms Autoﬁll engine with ﬁeld → pin bindings + hard validation gates; Benchbook+SCAO
087. [Branch · Superpin Codex Instructions-2.txt] Authority Snapshot Builder v3: diﬀ/drift + proposition shards to scale AuthorityTriples while keeping snapshot updates validator-ticket gated.
088. [Branch · Superpin Codex Instructions-2.txt] Authority “law packs” conﬁg: oﬃcial-source registry + update cadence + logs, still snapshot-gated.
089. [Branch · Superpin Codex Instructions-2.txt] Denial-Surface Fuzzer (risk-condition simulation) and Forms adversarial validator (looks-ﬁlled-but-wrong).
090. [Branch · Superpin Codex Instructions-2.txt] Forms-First Compiler v3 (catalog → ﬁeld maps → validators → ﬁll plans → render → audit) with PO gating on every ﬁeld source.
091. [Branch · Superpin Codex Instructions-2.txt] Gate:- ticket issuance requires ValidatorAgent signature (logical) and traceable evidence/authority pins.
092. [Branch · Superpin Codex Instructions-2.txt] If you want the next cycle to prioritize (A) packaging completion (v0005 FULL zip + link) or (B) deeper core expansion (agents/daemons/Neo4j migration pack),
093. [Branch · Superpin Codex Instructions-2.txt] P143 — Permission model: LLM cannot mutate; validators own state transitionsGoal: prevent “creative” output from damaging truth, authority, or graph state.
094. [Branch · Superpin Codex Instructions-2.txt] SCAO Forms Catalog + Field Map Compiler: form catalog + per-form ﬁeld maps + validators + per-run form audits to operationalize forms-ﬁrst with
095. [Branch · Superpin Codex Instructions-2.txt] Versioned docs/training ingest (PO-gated; never treated as authority unless in snapshot).
096. [Branch · Superpin Codex Instructions-2.txt] graph federation (shared authority vs case-private evidence + isolation tests); QA supergates + release readiness contract; Oﬄine search appliance pack
097. [Branch · Superpin Codex Instructions-2.txt] replayable event-sourced runs, Neo4j+artifact schema migrations, strict LLM permission isolation, content-addressed external asset vault (CAAV),
098. [FRED PRIME LEGAL INTELLIGENCE OPERATIONS MANUAL.txt] (scripts/"gate_neo4j_export.py").write_text(gate_export, encoding="utf-8")
099. [FRED PRIME LEGAL INTELLIGENCE OPERATIONS MANUAL.txt] - `scripts/gate_neo4j_export.py` validates presence, headers, and minimum row counts.
100. [FRED PRIME LEGAL INTELLIGENCE OPERATIONS MANUAL.txt] - merge -> export Neo4j import CSVs -> fail-closed export gate
101. [FRED PRIME LEGAL INTELLIGENCE OPERATIONS MANUAL.txt] 2) Fail-closed gate for Neo4j import artifacts
102. [FRED PRIME LEGAL INTELLIGENCE OPERATIONS MANUAL.txt] 2) Growth pipeline wrapper (merge → Neo4j export → gate)
103. [FRED PRIME LEGAL INTELLIGENCE OPERATIONS MANUAL.txt] 3) Run fail-closed gate for Neo4j export artifacts
104. [FRED PRIME LEGAL INTELLIGENCE OPERATIONS MANUAL.txt] E4 DEADLINES:time computations;trigger rules;service windows;appeal/reconsider windows (MI authority-gated once snapshot loaded).
105. [FRED PRIME LEGAL INTELLIGENCE OPERATIONS MANUAL.txt] Fail-closed gate ensuring Neo4j import CSVs exist and meet minimal sanity checks.
106. [FRED PRIME LEGAL INTELLIGENCE OPERATIONS MANUAL.txt] GATE D Vehicle+PO validity:VehicleMap exists;POs cite authority pinpoints;mandatory POs satisfiable or explicitly blocked with acquisition plan.
107. [FRED PRIME LEGAL INTELLIGENCE OPERATIONS MANUAL.txt] Gate D Vehicle/PO: VehicleMap exists; POs authority-pinned and satisfiable or blocked with tasks
108. [FRED PRIME LEGAL INTELLIGENCE OPERATIONS MANUAL.txt] Gate G AuthoritySnapshot: authority refs must match snapshot_id + effective_date
109. [FRED PRIME LEGAL INTELLIGENCE OPERATIONS MANUAL.txt] GateA Storage/Auth;GateC RecordSpine;GateB Pinpoints;GateD Vehicle/PO;GateE PCG Irreversible;GateF Repro;GateG AuthoritySnapshot.
110. [FRED PRIME LEGAL INTELLIGENCE OPERATIONS MANUAL.txt] I3 Every ProofObligation has an authority_pinpoint bound to AUTH_SNAPSHOT_ID.
111. [FRED PRIME LEGAL INTELLIGENCE OPERATIONS MANUAL.txt] Neo4j “SUCCESS only if verified” gate: declare SUCCESS only when 30_sanity.cypher returns PASS thresholds (no missing IDs, no dupes, relationships present).
112. [FRED PRIME LEGAL INTELLIGENCE OPERATIONS MANUAL.txt] SHACL is optional. You can keep using the Python quality gates when Neo4j is not present.
113. [FRED PRIME LEGAL INTELLIGENCE OPERATIONS MANUAL.txt] V4.6 delivered: deterministic Neo4j wiring + fail-closed export gate + optional smoketest
114. [FRED PRIME LEGAL INTELLIGENCE OPERATIONS MANUAL.txt] gate_neo4j_export.py
115. [FRED PRIME LEGAL INTELLIGENCE OPERATIONS MANUAL.txt] if "## V4.6 Neo4j Wiring Gate" not in rb:
116. [FRED PRIME LEGAL INTELLIGENCE OPERATIONS MANUAL.txt] merge layers → 2) export to neo4j/v5_26_lts/import/ → 3) fail-closed export gate
117. [FRED PRIME LEGAL INTELLIGENCE OPERATIONS MANUAL.txt] python scripts/gate_neo4j_export.py --import-dir neo4j/v5_26_lts/import
118. [FRED PRIME LEGAL INTELLIGENCE OPERATIONS MANUAL.txt] run([sys.executable, str(root/"scripts"/"gate_neo4j_export.py"),
119. [FRED PRIME LEGAL INTELLIGENCE OPERATIONS MANUAL.txt] run([sys.executable, str(root/"scripts"/"gate_neo4j_export.py"), "--import-dir", str(neo_import), "--min-nodes", "1", "--min-edges", "1"], cwd=str(root))
120. [FRED PRIME LEGAL INTELLIGENCE OPERATIONS MANUAL.txt] scripts/gate_neo4j_export.py
