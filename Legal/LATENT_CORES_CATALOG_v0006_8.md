# LATENT CORES CATALOG v0005 (Append-only)
Purpose: enumerate newly surfaced/engineered cores to reduce hidden tech debt and prevent capability drift.
Scope: these are implementable modules/daemons/pipelines that can be coded into the LitigationOS Windows x64 stack.

## 1) Governor Layer
1.1 Decision Golden Compass (DGC): monotonic improvement steering; non-regression; value function; cycle selector; convergence rule.
1.2 Permission Model (PM): LLM read-only; validators own state transitions; capability tokens; tamper-evident approvals.
1.3 Policy Router: file-state gates (HARVEST/ANALYZE/DRAFT/FILE_READY/PCG), per-track config, per-court config.

## 2) Replayability + Observability Core
2.1 EventLog JSONL (append-only): run_id scoped; component/phase/ops; crash-safe fsync; strict schema.
2.2 JobQueue SQLite WAL: claim/lease/retry/backoff; resumable after crash; deterministic replays.
2.3 Telemetry Bridge (OpenTelemetry): correlate traces/logs/metrics; export to local collector (no SaaS).
2.4 Lineage Bridge (OpenLineage): optional run->dataset lineage events; binds ingestion to derived graphs.

Refs:
- OpenTelemetry spec/docs: https://opentelemetry.io/
- OpenLineage spec: https://openlineage.io/

## 3) Schema Governance Core
3.1 Schema versioning: SemVer + migration ids; compatibility matrix.
3.2 Migration runner: Cypher migrations + contract tests; idempotent bootstrap.
3.3 Store contracts: JSON Schema for eventlog/jobqueue/manifests/pointers.

Ref:
- Neo4j migrations concept: https://neo4j.com/labs/

## 4) External Asset Core (700MB-safe)
4.1 CASv3 pointers: assets/pointers/*.pointer.json (hash+bytes+locations+license+provenance).
4.2 Resolver: choose best source (local|rclone|http|annex|datalad), verify hash, cache.
4.3 Annex/Datalad: optional large evidence datasets tracked without packing into releases.

Refs:
- git-annex: https://git-annex.branchable.com/
- DataLad: https://www.datalad.org/
- rclone: https://rclone.org/

## 5) Supply-Chain Core
5.1 SBOM: CycloneDX generation for releases.
5.2 VEX: OpenVEX for vulnerability assertions.
5.3 Provenance: SLSA provenance; in-toto attestation format for build steps.
5.4 Signing: cosign/sigstore for artifact signing (or Windows Authenticode in addition).
5.5 Updates: TUF metadata for safe update distribution.

Refs:
- CycloneDX spec: https://cyclonedx.org/
- OpenVEX: https://openvex.dev/
- SLSA: https://slsa.dev/
- in-toto: https://in-toto.io/
- Sigstore/cosign: https://www.sigstore.dev/
- TUF: https://theupdateframework.io/

## 6) PO Ledger Coupling Core
6.1 Proof Obligations are first-class artifacts (po_ledger.json + po_evidence_map.json).
6.2 PCW enforcement: state transitions only through validators; PCG gate references satisfied POs.
6.3 Reopen recipe: every evidence pointer must support retrieval (bundle->entry->page/line/time).

## 7) Michigan Authority Snapshot Core
7.1 Authority snapshot builder: download and freeze official MI court rules/forms; effective dates; snapshot id.
7.2 Proposition gating: no out-of-snapshot propositions in FILE_READY/PCG.

Ref:
- Michigan Court Rules (official): https://www.courts.michigan.gov/


## v0006 Additions (Core-Patches + Daemons)
- BinderCompletenessGate: binder index→filesystem reconciliation; blocks release on missing.
- DocContainerIntegrityGate: docx/pdf/zip validation with safe outputs only.
- LinkCataloger+SourceIndex: canonical MI authority/form source registry + tiers.
- SchemaGov+Migrations: Neo4j constraints/index governance + rollback scripts.
- CapabilityToken Write Barrier: LLM read-only; validators own transitions.
- Replayability Core: event-sourced runs + idempotent output routing.
- QuoteLock Workbench: candidate/verified quote lifecycle.
- External Asset CAS: content-addressed pointers + chunk maps + receipts.
- Decision Golden Compass: EV scoring + regression rollback.
