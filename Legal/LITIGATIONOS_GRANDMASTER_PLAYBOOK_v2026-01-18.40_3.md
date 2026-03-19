# LITIGATIONOS — GRANDMASTER BUILD & OPERATIONS PLAYBOOK v2026-01-18.20

**Purpose:** Build a production-grade LitigationOS that can (1) ingest and preserve your litigation record, (2) normalize it into a durable evidence + authority knowledge base, (3) produce court-ready draft bundles and decision-support outputs, and (4) run as an auditable, deterministic system that improves over time.

> **Non-legal disclaimer:** This playbook is an engineering/operations blueprint for building a litigation information system. It does not replace a licensed attorney’s judgment, nor does it guarantee outcomes in any court.

---

## How to read this document
- This is written as **25+ “pages”** for planning, but delivered as **machine-readable markdown**.
- Each page contains: **Intent → Inputs → Outputs → Automation → Verification**.
- Everything is structured for **end-to-end automation** with human-in-the-loop approval at irreversible steps (filing/service).

## Core design principles
1. **Record-first:** The system’s source of truth is the *record*, not narrative.
2. **Append-only:** New information is added; originals are never overwritten.
3. **Deterministic builds:** Given the same inputs, the system produces the same outputs (or explicitly versioned deltas).
4. **Auditability:** Every derived artifact is traceable to source files and extraction steps.
5. **Separation of concerns:** Ingestion ≠ indexing ≠ reasoning ≠ drafting ≠ packaging ≠ deployment.
6. **Safety gates:** Destructive operations are opt-in and logged; default is read-only.

---

## Table of contents
- **Phase 0 — Mission, Scope, and Safety**
  - P01 Mission & outcomes
  - P02 Threat model & risk controls
  - P03 Operating modes & governance
- **Phase 1 — Repository, Tooling, and Continuous Delivery**
  - P04 Repo layout & conventions
  - P05 Copilot/agent onboarding & PR discipline
  - P06 CI/CD, runners, and reproducible environments
- **Phase 2 — Canonical Data Model and Storage**
  - P07 Evidence Vault & file identity
  - P08 Metadata, timestamps, and lineage
  - P09 Case spine, dockets, and deadlines
  - P10 Authority library & snapshots
- **Phase 3 — Ingestion & Normalization Pipelines**
  - P11 Intake channels (drives, email, downloads, portals)
  - P12 Extractors (PDF/DOCX/TXT) + OCR
  - P13 Sharding, embeddings, and quality scoring
  - P14 Validation, dedupe, and quarantine
- **Phase 4 — Graph Construction (Neo4j) and Query Layer**
  - P15 Graph schema: entities, events, propositions
  - P16 Constraints/indexes and performance
  - P17 Importers, idempotency, and migrations
- **Phase 5 — Retrieval, Reasoning, and Draft Assist**
  - P18 GraphRAG retrieval strategy
  - P19 Prompting, guardrails, and evidence-grounding
  - P20 Decision support: checklists, matrices, contradiction maps
- **Phase 6 — Court-Ready Outputs: Drafting, Bundling, and Exhibits**
  - P21 Draft compiler (templates, snippets, citations)
  - P22 Exhibit builder and binder assembler
  - P23 Filing packet generator & preflight
- **Phase 7 — UI, Automation, and Daily Operations**
  - P24 Command center UI + search
  - P25 Schedulers, watchers, and incremental harvest cycles
  - P26 Observability, incident response, and backups
- **Appendices — Schemas and Runbooks**
  - P27 Schemas (JSON/YAML) and naming
  - P28 Security model + secrets + redaction
  - P29 Testing strategy + golden fixtures
  - P30 Roadmap: scaling to multiple cases and teams

---

# P01 — Mission & outcomes

## Intent
- Define what LitigationOS must *do* (outcomes) and what it must *never do* (safety boundaries).
- Convert “win my case” into **engineering deliverables**: record completeness, contradiction surfacing, deadline certainty, and court-ready packets.

## Inputs
- Cases, courts, parties (can start with one case; the architecture supports many).
- Evidence corpus (documents, images, audio, video, chat exports).
- Authority corpus (rules/statutes/caselaw PDFs or structured extracts).
- Operational constraints (device(s), storage, offline/online, budget).

## Outputs (non-negotiable)
- **Vault:** immutable storage with manifest and provenance per item.
- **Chronology:** timeline database (event-centric) with bi-temporal support (event date vs discovered date).
- **Quote Ledger:** verifiable excerpts keyed to file+page+location (no free-floating quotes).
- **Order/Notice chain:** who ordered what, when, and how you were notified/served.
- **Deadlines:** computed and tracked with evidence of the trigger.
- **Draft bundles:** motion/affidavit/brief drafts + exhibit lists + binder structure.
- **Audit trail:** every run emits logs, lineage events, and a reproducible manifest.

## Automation contract
- Every pipeline step has: `inputs/`, `work/`, `outputs/`, `logs/`, and an idempotent `run_id`.
- Re-runs must not duplicate nodes/documents; they create **deltas**.
- All irreversible steps are separated into a **human-confirm** stage.

## Verification
- System can answer: “Show me the source for this claim/quote/deadline.”
- System can rebuild an output bundle from scratch using only the Vault + configs.
- System can enumerate **what is missing** to reach a complete record.

## Failure modes & mitigations
- Missing inputs → produce a **gap report** (not guesses).
- Corrupt files → isolate into quarantine; keep originals untouched.
- Conflicting timestamps → record both (observed vs declared).
- Tool drift (library upgrades) → pin versions; record versions in manifests.

---

# P02 — Threat model & risk controls

## Intent
- Treat litigation data as **high-stakes**: loss, alteration, or confusion about provenance can be outcome-determinative.
- Define a threat model and bake controls into architecture.

## Threats (T) → Controls (C)
- **T1: Accidental overwrite/deletion** → C: append-only Vault; read-only mounts; “write requires flag”.
- **T2: Silent corruption** → C: periodic verification; archive integrity checks; quarantine registry.
- **T3: Provenance ambiguity** → C: store original + extraction outputs; maintain lineage per derived artifact.
- **T4: Credential leakage** → C: secret scanning; env-only secrets; never store tokens in repo.
- **T5: Over-automation (unsafe filing/service)** → C: explicit execution gates + checklists; human approval.
- **T6: Model hallucination in drafting** → C: evidence-grounded generation; cite-to-source enforcement; “unknown” allowed.

## Evidence integrity controls
- Preserve originals as-is; derived versions are separate artifacts.
- Store extraction parameters and tool versions per run.
- Consider optional hashing/digital signatures for high-integrity workflows (hashes stored separately).

## Redaction & privacy
- Separate **private working sets** from **court-public bundles**.
- Redaction pipeline is explicit and produces a redaction log (what/where/why).
- Avoid embedding minors’ sensitive data into vector stores unless access-controlled.

## Operational controls
- Role separation: ingestion operator vs drafter vs reviewer.
- Audit logs are immutable and time-stamped.
- Backups are versioned and tested via restore drills.

## Verification
- Run a quarterly “disaster drill”: restore Vault + graph from backup and reproduce a known packet.
- Run a “tamper drill”: modify a derived file and ensure the system detects mismatch vs manifest.

---

# P03 — Operating modes & governance

## Intent
- Define predictable modes so the system behaves consistently under stress (deadlines/hearings).

## Modes
- **DISCOVERY:** aggressive ingestion, extraction, clustering; tolerate partials; label uncertainties.
- **DRAFT:** generate drafts and work products; allow candidate quotes but mark “unverified”.
- **FILE_READY:** strict; only verified quotes/citations; all dependencies present; preflight must PASS.
- **LITIGATION_DAY:** minimal changes; focus on retrieval, checklists, printing/export; freeze upgrades.
- **POST_HEARING:** ingest new orders/transcripts; delta analysis; update chronology and gap reports.

## Governance objects
- `CASE_REGISTRY.yaml`: defines case IDs, captions, parties, court, judge, docket sources.
- `AUTH_SNAPSHOT.yaml`: defines authority sources + effective dates + snapshot ID.
- `RUN_LEDGER.jsonl`: append-only run events with inputs/outputs pointers.
- `POLICY.yaml`: redaction rules, retention rules, safety gates.

## Decision discipline (engineering)
- Any new feature must state: (a) what output it improves, (b) what it risks breaking, (c) how it is tested.
- Change budget: cap diff size and number of touched components per PR.
- “No surprises”: default to additive changes; avoid renames/mass refactors.

## Verification
- Each mode has a CLI switch, and the system prints which rules are active.
- A run is reproducible by reading `RUN_LEDGER` entry and re-running with same configs.

---

# P04 — Repo layout & conventions

## Intent
- Create a repo layout that supports modular growth without chaos.

## Recommended monorepo layout
- `apps/` — user-facing executables (GUI/CLI).
- `services/` — long-running daemons (watchers, schedulers).
- `packages/` — reusable libraries (vault, extractors, graph, drafting).
- `pipelines/` — orchestrated workflows (harvest, graph-build, packager).
- `schemas/` — JSON/YAML schemas and validation rules.
- `templates/` — document templates and snippet libraries.
- `ops/` — deployment scripts, Docker, systemd/Task Scheduler plans.
- `.github/` — CI workflows + Copilot instructions + agents.
- `docs/` — runbooks, onboarding, architecture decisions (ADRs).
- `tests/` — golden fixtures + pipeline integration tests.

## Naming & versioning rules
- Every run produces a `run_id` of the form `YYYYMMDD_HHMMSSZ_<case>_<pipeline>_<hash8>`.
- Artifacts are stored under `outputs/case_24-01507-DC/run_20260118_000001Z/` with a manifest.
- Config files are versioned; changes produce a new config version suffix.

## Engineering standards (baseline)
- Python: type hints, structured logging, clear exit codes, defensive file I/O.
- PowerShell: strict mode, stop-on-error, explicit `-WhatIf` modes where possible.
- Data formats: JSON Lines for event logs; YAML for hand-edited registry; CSV for spreadsheets/exports.

## Verification
- New developer can run: `make bootstrap` (or equivalent) and then `make smoke` within 30 minutes.
- Repo enforces formatting/linting via CI on every PR.

---

# P05 — Copilot/agent onboarding & PR discipline

## Intent
- Configure the repository so AI agents can contribute safely and predictably.

## Instruction files (recommended)
- `.github/copilot-instructions.md` — repo-wide: goals, build/test commands, DoD, boundaries.
- `.github/instructions/*.instructions.md` — scoped instructions using `applyTo` globs (language/tool specific).
- `AGENTS.md` — agent operating manual (workflow, safety, review requirements).

## PR discipline for agents
- Agents only work on a single objective per PR.
- Every PR includes: rationale, how to test, risk notes, and rollback plan.
- Agents must not change production data paths unless explicitly requested.
- Agents must not add secrets; all credentials come from CI secrets or local env only.

## Branching model
- `main` is always shippable.
- Feature branches: `agent/<short-task>-<date>`.
- Release tags are cut only from `main` after passing CI + smoke tests.

## Automated checks (minimum)
- Lint/format (Python: ruff/black; PS: PSScriptAnalyzer; Markdown: markdownlint).
- Unit tests (if present) and at least one end-to-end pipeline test using fixtures.
- Security scanning (secret scanning; dependency scanning if available).

## Verification
- New issue can be turned into a PR by an agent without human babysitting; human only reviews/merges.
- The repo’s instructions reflect real commands; unknowns are explicitly marked as unknown.

---

# P06 — CI/CD, runners, and reproducible environments

## Intent
- Make builds deterministic and portable across Windows + Linux, with minimal friction.

## Environment strategy
- **Primary dev:** Windows (because that’s where court artifacts and many tools live).
- **CI:** Linux runners (faster, cheaper) + optional self-hosted Windows runner for integration tests.
- Containerize services where feasible (extractors, neo4j stack).

## Dependency pinning
- Python: `pyproject.toml` + lock file (uv/poetry/pip-tools).
- Node (if UI): `package-lock.json`/`pnpm-lock.yaml`.
- Neo4j: pin image/tag and record schema migration version.

## Reproducible pipelines
- Each pipeline has a Dockerfile or a deterministic “bootstrap” script.
- CI runs “smoke” pipelines on sample data to verify end-to-end function.

## Release packaging
- CLI tools shipped as Python zipapp or pip package + frozen binary for non-dev machines.
- GUI shipped as signed installer where possible; include version + manifest in about dialog.

## Verification
- `make ci-smoke` runs locally and matches CI behavior.
- A clean checkout can reproduce a known run given the same fixture set.

---

# P07 — Evidence Vault & file identity

## Intent
- Implement an evidence vault that preserves originals and makes every derived artifact traceable.

## Vault structure (recommended)
- `vault/original/` — byte-for-byte originals as received.
- `vault/derivatives/` — text extracts, OCR outputs, thumbnails, audio transcripts.
- `vault/manifests/` — per-run manifest files (JSON + CSV).
- `vault/quarantine/` — corrupt/unsupported items + error logs.
- `vault/exports/` — court-facing exports (redacted, curated).

## Identity model
- `item_id`: stable ID derived from (source_path, size, modified_time, and optionally content hash).
- `version_id`: derived output version keyed to extractor+params+timestamp.
- `provenance`: who/when/how acquired (download, scan, email, FOIA, portal).

## Integrity options
- **Baseline:** store size + timestamps + extraction logs.
- **High-integrity:** store SHA-256 hashes (or stronger) for originals and key derivatives; store hash logs separately.

## Automation
- `vault ingest <path>`: copies original into `vault/original/` and emits a manifest row.
- `vault verify`: walks vault and compares to manifest; emits discrepancies report.
- `vault export --case <id> --bundle <rule>`: produces a curated export set with a manifest.

## Verification
- Every item in any packet can be traced back to `vault/original/EV_00000001/source.pdf`.
- The system can prove what changed between two versions of the same item.

---

# P08 — Metadata, timestamps, and lineage

## Intent
- Normalize time and lineage so cross-document comparisons are reliable.

## Timestamp model (bi-temporal)
- `event_time`: when the real-world event happened (hearing date, incident date).
- `record_time`: when it entered the record (file-stamp date, ROA entry date).
- `ingest_time`: when you acquired it.
- `process_time`: when the system extracted/converted it.

## Timestamp format
- Use an unambiguous ISO-8601/RFC-3339 profile string (UTC preferred) in logs and manifests.
- Store original local timestamps too (as observed), but compute a normalized UTC field.

## Lineage model (OpenLineage-inspired)
- Treat each pipeline step as a **Job** producing **Datasets** (outputs) from input datasets.
- Emit `RunEvent`-like records to `RUN_LEDGER.jsonl` for auditability.
- Store extractor versions and parameters as run facets/metadata.

## Automation
- `lineage emit`: append a structured JSON event for each step (START, COMPLETE, FAIL).
- `lineage graph`: visualize pipeline lineage for a run_id (optional).

## Verification
- Given an output artifact, the system can show: inputs → steps → tools → parameters → output.
- Sorting by time produces consistent chronology even across time zones.

---

# P09 — Case spine, dockets, and deadlines

## Intent
- Model the case as a sequence of docketed events and procedural triggers.

## Core objects
- `Case`: case_id, caption, court, division, judge(s), parties, counsel.
- `DocketEntry`: entry_no, date, title, document links, file-stamp indicators.
- `Hearing`: date/time, type, notice served, exhibits, transcript pointer.
- `Order`: signed date, filed date, served date, effective date, directives.
- `Deadline`: trigger event, due date, rule basis, responsible party, proof.

## Deadlines engine
- Compute deadlines from trigger events (order entered, notice served, etc.).
- Store the computation as data: trigger evidence + rule formula + result.
- Flag uncertain triggers (missing service proof) and generate acquisition tasks.

## Automation
- `case init --case-id X`: creates registry and directory skeleton for case.
- `docket import`: ingest docket spreadsheets/exports/PDF ROA and normalize to JSONL.
- `deadlines recompute`: recompute with versioned rule sets; emit delta report.

## Verification
- Each deadline must show the trigger source and the computation method.
- A “missing service” should prevent false certainty and produce an action plan.

---

# P10 — Authority library & snapshots

## Intent
- Maintain a versioned authority library so drafts and analyses reference the correct effective rules.

## Authority corpus
- Sources: rules, statutes, benchbooks, court forms, local administrative orders, published opinions.
- Store as: original PDFs + extracted text + structured “authority nodes” (citations, sections).

## Snapshot concept
- A snapshot is a frozen set of authority documents with effective dates and source metadata.
- Drafts reference `snapshot_id` so you can reproduce what authority the system used.

## Normalization
- Parse headings/sections into anchors: `auth_id`, `section_id`, `pinpoint`.
- Store in an index: `authority_snapshot_index.jsonl` and optionally graph nodes.

## Automation
- `auth ingest <folder>`: import authority PDFs; extract text; build anchors index.
- `auth snapshot create --effective YYYY-MM-DD`: freeze the set and tag it.
- `auth diff <snapshotA> <snapshotB>`: show changed sections and impacted propositions.

## Verification
- A draft can list every authority used, with snapshot_id and pinpoint anchors.
- If a rule changes, the system can highlight which templates are impacted.

---

# P11 — Intake channels (drives, downloads, portals)

## Intent
- Make intake effortless and consistent so nothing falls through cracks.

## Channels
- **Local drives:** watch folders for new PDFs, images, audio, ZIPs.
- **Cloud mirror:** optional rclone/Drive sync into a controlled intake directory.
- **Email exports:** convert emails to PDF/EML and ingest with metadata (sender/date).
- **Portals:** download orders/dockets/transcripts; store “download receipt” evidence (timestamped).
- **Scans:** phone scanner and flatbed scans go to a single “scans_inbox/” path.

## Intake normalization
- Every intake event writes a `source_receipt.json` describing: origin, time, method, operator.
- ZIPs are unpacked into a run-scoped directory; originals preserved.

## Automation
- `watcher` daemon monitors intake dirs; triggers `harvest` pipeline on changes.
- `zip unpack --preserve`: expands archives while preserving original filenames and folder structure; logs errors.
- `receipt capture`: produces receipts for portal downloads (URL, timestamp, filename).

## Verification
- Intake dashboard shows “new since last run” with counts by type and case mapping candidates.
- Any failure (corrupt PDF, passworded archive) is logged and quarantined without stopping other processing.

---

# P12 — Extractors (PDF/DOCX/TXT) + OCR

## Intent
- Convert heterogeneous documents into reliable text + structure while preserving originals.

## Extractor stack
- **Primary:** Apache Tika server/service for broad file-type coverage.
- **PDF text:** use a PDF text extractor; fallback to OCR when text layer is missing/garbled.
- **OCR:** OCR images and scanned PDFs into searchable PDFs and plain text; keep confidence metrics.

## Extraction outputs
- `text.txt` (plain extracted text).
- `meta.json` (metadata: author, created, modified, page count, mime type).
- `pages/` shards: `page_0001.txt` etc to enable pinpointing without heavy OCR loops.
- `render/` thumbnails for UI preview and evidence stamping.

## Quality scoring
- Text density score (chars/page).
- OCR confidence histogram (if available).
- “Needs review” flags for low-confidence pages.

## Automation
- `extract run --input <item> --strategy auto`: picks best extractor and falls back as needed.
- `ocr run --only-missing-text`: OCR only when text layer absent or below threshold.
- `extract shard --pages`: emit page-level shards and offsets.

## Verification
- Extraction reports list pages with low confidence and candidates for rescan.
- All derived outputs link back to original item_id and record extraction tool versions.

---

# P13 — Sharding, embeddings, and quality scoring

## Intent
- Prepare the corpus for high-precision retrieval without losing provenance.

## Shard types
- **Document shards:** whole-document or section-level shards (headings).
- **Page shards:** per page for PDFs (best for pinpoint quotes).
- **Paragraph shards:** for dense text documents (DOCX/MD).
- **Entity/event shards:** extracted structured records (people, dates, places).

## Embedding strategy
- Create embeddings at shard level, not whole file.
- Store embedding metadata: model name/version, dimensions, token counts, creation time.
- Keep raw text alongside embedding ID for debugging and future re-embedding.

## Quality scoring
- Retrieval confidence = f(text quality, source type, recency, citation density, OCR confidence).
- Use this score to prefer better sources and avoid garbage-in retrieval.

## Automation
- `shard build --mode auto`: produce shard JSONL with offsets and page pointers.
- `embed upsert --store <vector_store>`: push embeddings + metadata.
- `reembed --model X`: versioned re-embedding; do not overwrite old embeddings.

## Verification
- Random sample audit: 50 shards must reconstruct cleanly to the original file and location.
- “Find this phrase” queries return shards with correct pointers (page/line).

---

# P14 — Validation, dedupe, and quarantine

## Intent
- Keep the system trustworthy by aggressively surfacing broken inputs and duplicates.

## Validation checks
- File open/read test; PDF render test; archive test (zip integrity).
- Password detection for PDFs/ZIPs (do not brute-force; just flag).
- MIME/type mismatch detection (extension vs content).
- Duplicate detection (same content under different names) via hashes or similarity.

## Quarantine policy
- Quarantine items that cannot be processed safely.
- Keep original untouched; store error logs and minimal metadata.
- Allow “manual override” to reprocess after fixing external issues.

## Dedup strategy
- First pass: hash-based (exact duplicates).
- Second pass: fuzzy similarity on extracted text (near-duplicates).
- Canonicalize one as “primary” and link others as alternates (do not delete).

## Automation
- `validate run`: writes `validation_report.json` and `quarantine_index.csv`.
- `dedupe run`: writes `dedupe_map.json` (primary→aliases).
- `repair suggest`: emits recommended remediation (rescan, re-export, re-download).

## Verification
- Quarantine count trends down over time as you remediate, not up unpredictably.
- Dedupe map never loses information; it only clusters and links.

---

# P15 — Graph schema: entities, events, propositions

## Intent
- Build a property graph that answers litigation questions quickly and supports RAG with provenance.

## Node types (minimum viable)
- `Case`, `Court`, `Judge`, `Party(Person|Org)`, `Attorney`
- `DocketEntry`, `Filing`, `Order`, `Hearing`, `Transcript`
- `EvidenceItem` (vault original), `Derivative` (extracted text/OCR), `Exhibit`
- `Event` (real-world occurrence), `Claim`/`Proposition` (assertion), `Quote` (verbatim excerpt)
- `Authority` (source), `AuthoritySection` (pinpoint anchor)
- `Deadline`, `Service`, `Notice`, `Task`

## Relationship types (minimum viable)
- `(:Filing)-[:IN_CASE]->(:Case)
- `(:Order)-[:ISSUED_IN]->(:Case)
- `(:Order)-[:DERIVED_FROM]->(:EvidenceItem|:Derivative)
- `(:Quote)-[:FROM_PAGE]->(:Derivative {page})
- `(:Proposition)-[:SUPPORTED_BY]->(:Quote|:EvidenceItem)
- `(:Proposition)-[:CITES]->(:AuthoritySection)
- `(:Proposition)-[:CONTRADICTS]->(:Proposition)
- `(:Deadline)-[:TRIGGERED_BY]->(:Order|:Notice|:DocketEntry)
- `(:Service)-[:SERVES]->(:Filing|:Order) and `(:Service)-[:TO]->(:Party)

## Property standards
- Stable IDs: `case_id`, `item_id`, `docket_id`, `auth_id`, `section_id`.
- Time fields: `event_time`, `record_time`, `ingest_time` as ISO-8601 strings + epoch ms.
- Provenance fields: `source_path`, `source_receipt_id`, `run_id`.

## Automation
- `graph init`: apply constraints/indexes and baseline schema metadata.
- `graph upsert`: idempotent upsert by stable IDs; never create duplicates on reruns.
- `graph link`: second-pass linking (entities, dates, cross-references).

## Verification
- Graph queries can answer: “what order created this deadline?”, “what evidence supports this proposition?”, “what quotes are tied to this exhibit?”
- Every proposition node has at least one link to supporting evidence or is marked `status=UNSUPPORTED`.

---

# P16 — Constraints/indexes and performance

## Intent
- Prevent duplicates and keep queries fast using constraints and indexes.

## Constraints (examples)
- Uniqueness constraints on stable IDs: `Case.case_id`, `EvidenceItem.item_id`, `AuthoritySection.section_id`, etc.
- Existence constraints for required properties where supported: stable IDs and key timestamps.
- Naming constraints explicitly and using `IF NOT EXISTS` for idempotency.

## Indexes (examples)
- Lookup indexes on commonly filtered fields: `ingest_time`, `record_time`, `court`, `judge`, `case_id`.
- Full-text indexes for searching extracted text (if using Neo4j fulltext).
- Vector index if using Neo4j vector search for embeddings.

## Query patterns
- Always anchor queries via indexed IDs first, then traverse.
- Avoid “scan everything” patterns for large corpora; use selective match + relationship traversal.
- Use profile/EXPLAIN in development to detect regressions.

## Automation
- `schema apply`: runs all constraint/index statements idempotently.
- `schema verify`: checks actual DB schema vs expected schema manifest.
- `perf smoke`: runs a standardized set of queries and records timings.

## Verification
- Importing the same dataset twice does not increase node counts beyond expected deltas.
- Common queries (case overview, find quotes, list deadlines) remain within target latency.

---

# P17 — Importers, idempotency, and migrations

## Intent
- Build importers that can run repeatedly without breaking the graph.

## Importer tiers
- **Tier A (Vault → Graph metadata):** create `EvidenceItem` nodes and ingestion metadata.
- **Tier B (Derivatives → Quotes/Pages):** load page shards, quote spans, OCR stats.
- **Tier C (Case spine):** docket entries, filings, orders, hearings, deadlines.
- **Tier D (Reasoning layer):** propositions, contradictions, issue tags, authority links.

## Idempotent upserts
- Use `MERGE` on stable IDs; set immutable properties on create; mutable properties on match.
- Store `last_seen_run_id` and `first_seen_run_id` per node to track deltas.
- Maintain a `DEDUPE_MAP` for when IDs collide or are re-keyed.

## Schema migrations
- Keep schema version in DB: `(:SchemaVersion {version, applied_at, git_sha})`.
- Migrations are ordered scripts checked into `ops/migrations/`.
- CI runs migrations on a fresh DB and verifies expected schema and sample imports.

## Automation
- `import run --case 24-01507-DC`: executes Tier A→D as configured; emits import report with counts.
- `migrate up`: applies pending migrations and logs results.
- `import verify`: checks invariants (no duplicate IDs; required relationships exist).

## Verification
- A full rebuild from Vault yields the same graph counts (within controlled deltas).
- Any mismatch produces a structured “why” report (missing shards, parsing errors, etc.).

---

# P18 — GraphRAG retrieval strategy

## Intent
- Use a hybrid retrieval method that prioritizes provenance and structured filters.

## Retrieval layers
- **L0: Case filter** — constrain by case_id, date range, document type.
- **L1: Graph neighborhood** — traverse from relevant entities (orders, parties, exhibits) to nearby evidence.
- **L2: Vector similarity** — search shard embeddings for semantic matches.
- **L3: Rerank** — rerank candidates using cross-encoder or heuristic scoring (quality + proximity + citations).
- **L4: Assemble context pack** — output a bounded set of shards with pointers and metadata.

## Context pack contract
- Always include: `item_id`, `derivative_id`, `page`, `offsets`, `run_id`, and a `quality_score`.
- Never include orphan text without pointers.
- Include both raw excerpts and normalized text (if cleanup is applied).

## Anti-hallucination tactics
- Use “citation-first” prompting: model must cite shards before claiming facts.
- Enforce “unknown” as an acceptable outcome; missing input triggers acquisition tasks.
- Separate “analysis narrative” from “record extracts”; never merge them silently.

## Automation
- `retrieval query --case 24-01507-DC --question "List all orders referencing a psychological evaluation"`: returns a JSON context pack + a short answer.
- `contextpack export`: writes context pack to disk for review and future reuse.
- `contextpack diff`: compare context packs between runs to see what changed.

## Verification
- Random sample: 10 retrieved excerpts must resolve to the correct page in the original PDF.
- Retrieval results must be stable across reruns or explainable by new data.

---

# P19 — Prompting, guardrails, and evidence-grounding

## Intent
- Make the LLM behave like an assistant drafter that is accountable to the record.

## Prompt architecture
- **System policy:** never invent facts; always cite sources for factual claims; label assumptions.
- **Case policy:** jurisdiction constraints; naming conventions; preferred document structures.
- **Task policy:** what to produce (matrix, motion draft, exhibit list) and format constraints.
- **Context pack:** the only allowable factual basis for outputs in strict modes.

## Guardrail patterns
- “Two-channel output”: (1) result, (2) citation map (shard IDs → claims).
- “Verifier step”: a deterministic checker validates that every factual sentence has a citation.
- “Quote lock”: verbatim quotes must be copied exactly from shard text; if uncertain, mark as candidate.

## Draft separation
- Drafts can include strategy and hypotheses, but must distinguish between (a) record facts, (b) inferences, (c) legal argument.
- Court-ready outputs disallow uncertain quotes and unsupported factual assertions.

## Automation
- `draft run --mode DRAFT`: produces drafts + a validation report.
- `draft run --mode FILE_READY`: fails closed on missing citations/quotes.
- `verify citations`: checks drafts and produces a per-sentence citation coverage report.

## Verification
- A validator can point to the exact shard for any statement in a file-ready packet.
- Unsupported statements are surfaced, not hidden.

---

# P20 — Decision support outputs: matrices, contradiction maps

## Intent
- Convert raw record into actionable views: gaps, contradictions, and next actions.

## Core products
- **Findings Gap Matrix:** order/findings vs evidence vs missing record pieces.
- **Contradiction Map:** statement vs statement vs source; highlight conflicts and required clarifications.
- **Service/Notice Chain:** a timeline of service/notice events and proofs.
- **Harm/Impact Index:** categorize harms (time loss, financial, due process) tied to record items.
- **Question Bank:** cross-exam question sets tied to specific quotes/exhibits.

## Method
- Treat each “claim of the court/opponent” as a proposition node.
- Link supporting evidence; if absent, mark as `UNSUPPORTED` and surface as a gap.
- Generate a prioritized task list based on (a) deadlines, (b) materiality, (c) ease of acquisition.

## Automation
- `reports build --case 24-01507-DC`: generates the suite of matrices in both Markdown and CSV.
- `contradictions detect`: extracts and links conflicting propositions.
- `gaps enumerate`: produces `MISSING_INPUTS.yaml` with acquisition plan.

## Verification
- Each matrix row links to source items and page pointers.
- Priority ordering is explainable (deadline proximity + materiality score).

---

# P21 — Draft compiler (templates, snippets, citations)

## Intent
- Produce consistent, court-ready drafts from structured inputs.

## Template strategy
- Separate **structure templates** (section headings, boilerplate) from **fact blocks** (record extracts).
- Store templates in `templates/` with versioning and a schema for required fields.
- Allow multiple style targets (state motion, appellate brief, affidavit) without rewriting engines.

## Citation strategy
- Use a citation object: `{source_item_id, derivative_id, page, span_start, span_end, label}`.
- Citations are inserted into drafts via deterministic renderers (e.g., footnotes or parentheticals).
- Generate a “citation appendix” automatically listing all sources in order.

## Compilation pipeline
1. Select target template + case + mode (DRAFT vs FILE_READY).
2. Pull context packs for each section (facts, procedural history, exhibits).
3. Render fact blocks with citations.
4. Render argument scaffolding (non-factual text) using policy prompts.
5. Run validators (citation coverage, quote accuracy, formatting rules).

## Automation
- `compile motion --template X --case Y`: produces `motion.docx` + `motion.md` + validation report.
- `compile affidavit --facts <contextpack>`: produces affidavit draft with fact paragraph numbering.
- `compile appendix --citations`: produces a source index appendix.

## Verification
- “Fact paragraphs” can be traced back to evidence items.
- The compiler refuses to finalize if required fields are missing in file-ready mode.

---

# P22 — Exhibit builder and binder assembler

## Intent
- Turn evidence items into court-usable exhibits with consistent labeling and indexes.

## Exhibit pipeline
- Select items for a filing packet (from vault or graph query).
- Produce: cover page, exhibit label overlay (non-destructive), and combined PDF output.
- Create an exhibit index (CSV + PDF appendix) with descriptions and source pointers.

## Non-destructive principle
- Original files never altered.
- Stamped/labeled versions are derivatives stored under `vault/derivatives/` with clear linkage.

## Binder assembly
- Merge: cover sheets + exhibits in order + index + optional certificates/service proofs.
- Output both (a) a printable PDF binder, and (b) a “filing upload set” according to portal requirements.

## Automation
- `exhibits build --case 24-01507-DC --list exhibits.yaml`: generates labeled exhibits and a merged binder.
- `binder build --packet motion_X`: outputs `binder.pdf`, `index.csv`, `manifest.json`.
- `binder verify`: checks page counts, exhibit ordering, and file readability.

## Verification
- Each exhibit in the binder has a cover page and stable Exhibit ID.
- Index entries resolve to original item IDs and page pointers.

---

# P23 — Filing packet generator & preflight

## Intent
- Make “ready to file” an objective state verified by checkers, not gut-feel.

## Packet contents
- Draft document (DOCX/PDF).
- Exhibit binder (PDF) or individual exhibits per court rules.
- Proofs/certificates: service, notice, verification as needed.
- Cover sheets and indexes.
- A `preflight_report.md` stating what was checked and what passed/failed.

## Preflight checks
- All referenced exhibits exist and are readable.
- All citations resolve to existing shard pointers.
- No “UNVERIFIED QUOTE” tags remain in file-ready mode.
- Filenames and sizes comply with portal limits (configurable).
- Service list matches case registry (parties and service methods).

## Execution gates
- Preflight PASS is required before packet export.
- Export requires explicit human confirmation (command flag and interactive prompt).

## Automation
- `packet build --case 24-01507-DC --target motion_Y`: produces a complete packet folder + manifest.
- `packet preflight`: outputs PASS/FAIL with actionable fixes.
- `packet export --destination <path>`: copies packet to an upload directory; does not delete originals.

## Verification
- Packet folder is self-contained: you can zip it and move it without breaking references.
- Preflight report is included for future disputes about what was filed.

---

# P24 — Command center UI + search

## Intent
- Provide a single pane of glass for record navigation under deadline pressure.

## UI screens (minimum viable)
- **Case dashboard:** next deadlines, recent filings/orders, outstanding gaps.
- **Search:** full-text + semantic + filters (by case, date, doc type, party).
- **Timeline:** event-centric with record_time vs event_time toggles.
- **Exhibits:** list, preview, build binder, export packet.
- **Reports:** findings gap matrix, contradiction map, service chain.
- **Run history:** each pipeline run with status, counts, and artifacts.

## UX constraints
- Must be usable on low-power machines; avoid heavy 3D/giant graphs by default.
- Every list item should open the underlying PDF at the right page (deep link to viewer).
- “Explain why” button: show citations and provenance for any displayed fact.

## Automation
- UI triggers pipelines via a local API (CLI wrappers) and streams logs live.
- Provide “safe mode” for hearing day: disable ingestion and schema migrations.

## Verification
- UI can reproduce a known packet and show its manifest.
- Search results always show pointers (item_id + page).

---

# P25 — Schedulers, watchers, and incremental harvest cycles

## Intent
- Keep the system continuously up to date without manual effort.

## Incremental harvest cycle
- Detect new/changed files in intake folders.
- Ingest into vault (original + receipt).
- Extract/OCR as needed; shard; embed; validate.
- Upsert graph (Tier A→D as configured).
- Generate deltas: what changed since last cycle (new orders, new transcripts, new deadlines).

## Scheduling options
- Windows Task Scheduler: run `harvest --incremental` multiple times daily.
- Background service: a watcher daemon triggers harvest immediately on new files.
- Manual “panic button”: one-click run before a hearing to ensure everything is current.

## Backpressure controls
- Queue jobs; cap concurrent OCR/extraction to avoid memory spikes.
- Prioritize by urgency: new orders/notices > transcripts > bulk archives.

## Automation
- `scheduler install`: creates scheduled tasks with logs and safe permissions.
- `watcher run`: monitors directories and enqueues jobs.
- `harvest status`: shows queue, last run result, and current health indicators.

## Verification
- The scheduler never silently fails; it writes a heartbeat file and emits alerts on missed runs.
- Incremental runs are fast; full rebuild remains possible and tested.

---

# P26 — Observability, incident response, and backups

## Intent
- Treat LitigationOS like a production system: measure, alert, and recover.

## Observability pillars
- **Logs:** structured JSON logs with timestamps, levels, run_id, case_id.
- **Metrics:** counts of ingested items, extraction failures, OCR queue, graph node/rel counts.
- **Tracing/lineage:** run-level lineage events linking jobs and datasets.

## Incident classes
- **Data issue:** corrupt file, extraction failure, missing pages → quarantine + remediation plan.
- **System issue:** DB down, disk full, memory spike → restart strategy + safe mode.
- **Integrity issue:** mismatch between vault and manifest → lock exports until resolved.

## Backup strategy
- Vault backups: incremental + periodic full snapshot; verify restore procedure.
- Neo4j backups: consistent backups at off-hours; store schema version and migration logs.
- Config backups: commit to git; tag releases.

## Automation
- `health check`: verifies disk space, DB connectivity, queue health, last successful run.
- `backup run`: executes backup plan and verifies outputs.
- `restore drill`: automated test in a sandbox environment monthly.

## Verification
- You can restore to a known point-in-time and reproduce outputs.
- Health checks are visible in UI and logs; failures generate a human-readable summary.

---

# P27 — Schemas (JSON/YAML) and naming

## Intent
- Make data exchange stable by formalizing schemas.

## Key schemas
- `CASE_REGISTRY.yaml` — case definitions and parties.
- `PIPELINES.yaml` — pipeline definitions, resources, scheduling, thresholds.
- `ITEM_MANIFEST.json` — vault manifest for a run.
- `SHARDS.jsonl` — shard records with pointers and text hashes.
- `GRAPH_UPSERT.jsonl` — node/edge upserts (optional interchange format).
- `CONTEXT_PACK.json` — bounded retrieval pack with pointers and scores.
- `PRE_FLIGHT_REPORT.json` — packet readiness checks.

## Naming conventions
- IDs are lowercase snake_case.
- Files are named: `<artifact>__<case_id>__<run_id>.<ext>`.
- All time fields are ISO-8601 strings with timezone or `Z`.

## Schema validation
- Use JSON Schema for machine validation where feasible.
- Provide `schema validate <file>` CLI that fails with actionable error messages.

## Verification
- Tools refuse unknown fields in strict modes (prevents drift).
- Schema versions are embedded in every output artifact.

---

# P28 — Security model + secrets + redaction

## Intent
- Keep sensitive data safe while enabling collaboration and reliable exports.

## Access model
- Separate roles: `operator`, `reviewer`, `admin`.
- Vault is readable by all roles; only operator/admin can ingest.
- Export bundles are created in a separate directory with explicit permissions.

## Secrets management
- No secrets in git. Use OS credential store or environment variables.
- CI secrets are stored in GitHub Actions secrets; rotate periodically.
- Token scopes are minimal (read-only where possible).

## Redaction pipeline
- Define redaction rules in `POLICY.yaml` (names, minors, addresses).
- Produce redacted derivatives; never redact originals.
- Emit `REDACTION_LOG.csv`: item_id, page, location, redaction reason.

## Audit and compliance
- Log every export and who initiated it.
- Retain logs in append-only format for dispute resolution.

## Verification
- Run “export audit”: scan exports for disallowed patterns (e.g., SSNs) before finalizing.
- Confirm that redaction is reproducible and reversible (because originals remain).

---

# P29 — Testing strategy + golden fixtures

## Intent
- Make upgrades safe by testing the things that matter: provenance, reproducibility, and correctness.

## Test pyramid
- **Unit tests:** parsers, validators, ID generation, timestamp normalization.
- **Integration tests:** extraction pipeline on fixtures; graph upsert idempotency.
- **E2E tests:** build a sample packet from fixtures and compare to golden outputs.

## Golden fixtures
- A small corpus representing each document type (scanned PDF, text PDF, DOCX, image, ZIP).
- Include a docket sample and an order sample with known extracted quotes.
- Store fixture manifests and expected outputs under version control.

## Regression prevention
- Every bug fix adds a test reproducing the bug.
- Performance tests: baseline timing for key queries/pipelines.

## Automation
- `make test`: runs unit + integration tests.
- `make e2e`: runs a full pipeline and compares outputs to golden manifests.
- CI blocks merges on test failures.

## Verification
- A new release cannot change quote extraction for fixtures without explicit approval and updated goldens.
- Idempotency tests show stable node counts across repeated imports.

---

# P30 — Roadmap: scaling to multiple cases and teams

## Intent
- Evolve LitigationOS from a single-operator system to a scalable platform.

## Scaling axes
- **More cases:** per-case registries, shared authority snapshots, cross-case entity resolution.
- **More operators:** role-based access, audit trails, review workflows, shared dashboards.
- **More data types:** audio/video transcription, phone exports, social media archives.
- **More outputs:** appellate packets, FOIA bundles, hearing kits.

## Milestones
- M1: Vault + extraction + shard + basic search (single case).
- M2: Graph build + deadlines + matrices (single case).
- M3: Draft compiler + exhibit builder + packet preflight (single case).
- M4: UI command center + scheduling + health checks.
- M5: Multi-case + cross-case contradiction detection + collaborative review.

## De-risking strategy
- Keep each milestone shippable and usable.
- Measure value: time saved per week, record completeness score, deadline confidence score.
- Avoid “big bang” rewrites; iterate with migrations and fixtures.

## Verification
- Each milestone is tied to concrete user workflows (prepare hearing kit, respond to notice, assemble binder).
- Backwards compatibility: old runs remain readable; new features are additive.

---

# P31 — Developer bootstrap (one command to ready)

## Intent
- Minimize friction: a new machine can be productive quickly.

## Bootstrap targets
- Install prerequisites (Python, Node if needed, Docker, Java for Tika if used).
- Create local `.env` from `.env.example` with non-secret defaults.
- Start dependencies (Neo4j, Tika) via docker compose.
- Run smoke pipeline on fixtures and open UI.

## Recommended scripts
- `ops/bootstrap.ps1` (Windows): installs/pins toolchain; sets PATH; creates venv; installs deps.
- `ops/bootstrap.sh` (Linux/mac): same intent for CI and dev containers.
- `make bootstrap` (or `task bootstrap`): wrapper calling the right script.

## Automation
- Scripts must be idempotent and safe: re-running should not break environment.
- Scripts should emit: versions installed, where configs live, and next commands.

## Verification
- `make smoke` runs: start services, ingest fixtures, build graph, run 5 canonical queries, produce a sample packet.
- The smoke report is stored in `outputs/smoke/<run_id>/`.

---

# P32 — Neo4j stack: deploy, secure, backup

## Intent
- Treat Neo4j as critical infrastructure; keep it stable and backed up.

## Deployment options
- **Local Docker Compose:** fastest and repeatable; recommended for single operator.
- **Bare metal install:** when Docker unavailable; requires more ops discipline.
- **Remote server:** for multi-device access; requires TLS and strict access controls.

## Minimum docker compose services
- `neo4j` (pinned tag), volumes for data/logs/import/backups.
- Optional `tika` server.
- Optional `reverse_proxy` for TLS termination (if remote).

## Security hardening
- Set strong password; restrict binding to localhost by default.
- Separate `import/` directory; never mount entire drive into container if avoidable.
- Disable or restrict plugins you don’t need; document what is enabled.

## Backup runbook
- Nightly: logical backup or filesystem snapshot (depending on edition and setup).
- Weekly: full snapshot + test restore in a sandbox DB instance.
- Store backup manifests and restore verification logs in `vault/manifests/`.

## Automation
- `ops/neo4j_up.ps1`: start stack, wait for ready, run schema apply.
- `ops/neo4j_backup.ps1`: run backup, verify file sizes, record run ledger.
- `ops/neo4j_restore_drill.ps1`: restore into a temp DB and run smoke queries.

## Verification
- You can blow away the DB and rebuild it from Vault; restore is a speed optimization, not a single point of failure.
- Backups are verified; unverified backups are treated as missing.

---

# P33 — Pipeline orchestration: from scripts to a real scheduler

## Intent
- Scale from “run scripts manually” to resilient orchestration with retries and state.

## Orchestrator levels
- **Level 1:** Task Scheduler + CLI scripts (simple, robust).
- **Level 2:** A local queue + worker daemon (retries, prioritization).
- **Level 3:** Workflow orchestrator (Prefect/Temporal/Airflow) for multi-machine reliability.

## State model
- Jobs are immutable: `job_id`, `case_id`, `pipeline`, `inputs`, `mode`, `priority`.
- Runs are events: `run_id`, `job_id`, status transitions, metrics, outputs pointers.

## Retry and idempotency
- Retries are safe only if steps are idempotent.
- If a step is not idempotent, it must write a lock file and support resume.

## Automation
- `services/queue/` implements: enqueue, dequeue, status, dead-letter queue.
- `services/worker/` executes steps and emits lineage events.
- `pipelines/<name>/pipeline.yaml` declares step order and resources.

## Verification
- The orchestrator can resume after a crash without duplicating graph nodes or vault items.
- Backpressure works: large OCR jobs do not starve urgent order ingestion.

---

# P34 — Document generation toolkit (DOCX/PDF) with traceable citations

## Intent
- Generate drafts that are easy to edit (DOCX) and easy to file/print (PDF).

## Dual-output rule
- Produce **DOCX** for editing and **PDF** for final review/printing.
- Keep a `draft_source.json` describing how the document was assembled (sections, citations).

## Citation rendering patterns
- Inline parentheticals: `(Exh A, p. 3)` for quick reading.
- Footnotes/endnotes: better for longer briefs; maintain a consistent format.
- Citation appendix: an automatically generated index of evidence items used.

## Template system
- Use docx templates with named content controls/placeholders for deterministic fill.
- Keep style definitions (fonts, numbering) stable; store templates under version control.

## Automation
- `draft render --template <docx> --data <json>`: produces docx + pdf + render log.
- `draft validate`: checks required sections, numbering, and citation coverage.
- `draft diff`: shows changes between two versions (textual diff + citation delta).

## Verification
- A reviewer can click a citation entry and open the original evidence at the correct page.
- The system can regenerate the same PDF from the same inputs and template version.

---

# P35 — Exhibit stamping and page labeling (non-destructive overlays)

## Intent
- Add exhibit labels and page IDs without damaging originals.

## Overlay rules
- Produce an overlay layer (stamp) that can be removed by reverting to original.
- Keep stamps small and away from substantive text (top-right margin typical).
- Stamp includes: Exhibit ID, case_id (optional), and page number.

## Workflows
- **Single file exhibit:** label PDF pages, add cover page, output merged exhibit PDF.
- **Multi-file exhibit:** merge files, then stamp sequentially and add unified cover page.
- **Image exhibit:** convert to PDF with preserved resolution, then stamp.

## Automation
- `stamp apply --input <pdf> --label 'Exh A' --party plaintiff`: outputs stamped derivative.
- `cover generate --exhibit A --desc "Order (Signed) — 2023-12-04 PPO"`: outputs a cover PDF from structured metadata.
- `merge exhibits.yaml`: merges cover + stamped content.

## Verification
- Stamped output preserves page content (no rasterizing unless unavoidable).
- Index matches exhibit IDs and descriptions; cover page metadata matches manifest.

---

# P36 — Operational playbooks (hearing day, after order, escalation)

## Intent
- Provide repeatable runbooks for time-critical moments.

## Hearing-day runbook (T-24h to T-0)
- Freeze upgrades: switch to `LITIGATION_DAY` mode.
- Run `harvest --incremental` once; ensure last run is SUCCESS.
- Generate: hearing kit binder, question bank, and service/notice chain.
- Print/export: critical orders, docket, exhibit index, timeline summary.
- Confirm deadlines and next steps; create a post-hearing ingestion plan.

## Post-order runbook (T+0 to T+24h)
- Ingest new order/transcript/notice; capture portal receipt.
- Run `delta report`: what changed, new deadlines, contradictions introduced.
- Update gap matrix and task list.
- If an immediate response is required, generate a targeted packet preflight.

## Escalation runbook (when record integrity is contested)
- Export: manifests, receipts, run ledger, and relevant originals.
- Produce a provenance narrative: what you received, when, and how it was processed.
- Freeze and snapshot the authority set used for any draft/argument.

## Verification
- Each runbook ends with a checklist and an exported “kit” folder.
- Kits contain manifests so you can prove what you relied on at the time.

---

# P37 — Issue management and triage loops (engineering + litigation)

## Intent
- Use a single triage system to prevent “lost tasks” across software and litigation work.

## Issue taxonomy
- **DATA:** missing record, corrupt file, unknown provenance.
- **PROC:** deadline uncertainty, service/notice gap, missing docket entry.
- **DRAFT:** draft requires review, citation failures, quote mismatch.
- **OPS:** DB down, disk space low, scheduler failures.
- **FEATURE:** new capability request; must tie to a workflow/product.

## Triage loop
1. Capture (issue created automatically or manually).
2. Classify (taxonomy + severity).
3. Assign (owner: operator/agent/system).
4. Execute (pipeline step or code change).
5. Verify (tests/preflight/manifest).
6. Close with evidence (links to run outputs).

## Automation
- Auto-create issues from pipeline failures (quarantine events, missed schedules).
- Auto-link issues to run_ids and artifacts.
- Use templates for consistent issue capture: what happened, where, logs, expected behavior.

## Verification
- Every closed issue references: run_id, artifact path, and verification result.
- Monthly review: recurring issues become feature work; one-off issues become documented mitigations.

---

# P38 — Integrating GitHub Copilot coding agent safely

## Intent
- Make Copilot/agents productive without letting them break critical invariants.

## Repo-level instructions
- Define the system’s invariants (append-only vault, provenance, no secrets, idempotent imports).
- Define how to run tests and smoke checks before PRs.
- Define what agents may change automatically vs what needs explicit approval (e.g., schema migrations).

## Agent workflow
- Issues describe a single objective and acceptance criteria.
- Agents create a branch, implement, run tests, and open a PR with a structured summary.
- Humans review: (1) invariants, (2) security, (3) correctness, (4) tests, (5) doc updates.

## Safety gates
- Agents must not modify `vault/` contents in the repo (vault is external).
- Agents must not introduce network calls without documenting purpose and safeguards.
- Agents must not change legal templates without updating goldens and validation rules.

## Automation
- Use `.github` instructions files for guidance and `.github/workflows` for enforcement.
- Use PR checks that fail if required sections in PR description are missing.

## Verification
- A typical agent PR is reviewable in under 15 minutes because it is scoped and tested.
- Agents improve speed; they do not increase operational risk.

---

# P39 — CLI contract: commands, flags, and exit codes

## Intent
- Define stable CLIs so UI/agents/orchestrators can call pipelines reliably.

## Command groups (concrete subcommands)
- `lit vault ingest --root "F:\LITIGATION_INTAKE" --case-id 24-01507-DC --out "F:\LitigationOS\Vault"` — intake→vault, manifest, quarantine.
- `lit vault verify --case-id 24-01507-DC --vault "F:\LitigationOS\Vault" --json` — integrity scan + corruption list.
- `lit extract pdf --case-id 24-01507-DC --vault "F:\LitigationOS\Vault" --out "F:\LitigationOS\Derivatives" --ocr auto --json` — PDF→text/shards (OCR only when needed).
- `lit graph schema-apply --db bolt://localhost:7687 --auth neo4j:neo4j --schema graph/schema/neo4j_schema_v1.cypher` — schema + constraints.
- `lit graph import --case-id 24-01507-DC --db bolt://localhost:7687 --inputs "F:\LitigationOS\Derivatives" --idempotent --json` — idempotent import with counts.
- `lit retrieve query --case-id 24-01507-DC --question "What orders control parenting time exchanges?" --json` — ContextPack + answer stub.
- `lit draft compile --case-id 24-01507-DC --vehicle "MI-FOC-PT-ENFORCE" --mode DRAFT --out "F:\LitigationOS\Drafts" --json` — draft compiler (no filing unless PCG PASS).
- `lit exhibits build --case-id 24-01507-DC --packet "PT_ENFORCE" --out "F:\LitigationOS\Exhibits" --stamp plaintiff --json` — exhibit covers/stamps/merges.
- `lit packet build --case-id 24-01507-DC --packet "PT_ENFORCE" --mode FILE_READY --out "F:\LitigationOS\Packets" --preflight --json` — binder + preflight.
- `lit ops scheduler install --schedule "0 6,12,18,23 * * *" --task harvest --json` — scheduled harvest cycles.

## Standard flags (all commands)
- `--case-id` (when relevant)
- `--run-id` (optional; auto-generated if omitted)
- `--mode {DISCOVERY|DRAFT|FILE_READY|LITIGATION_DAY}`
- `--config <path>`
- `--dry-run` (no writes except logs)
- `--json` (machine-readable output)
- `--log-level {DEBUG|INFO|WARN|ERROR}`

## Exit codes (recommended)
- `0` success
- `2` usage/config error
- `10` recoverable processing error (quarantine created)
- `20` preflight fail (actionable fixes available)
- `50` infrastructure failure (DB/service unavailable)

## Verification
- Every command prints (and can output JSON): inputs, outputs, and next suggested actions.
- Exit codes are consistent and tested, enabling automation.

---

# P40 — Configuration blueprints (YAML) for end-to-end automation

## Intent
- Provide machine-readable configs that define behavior without code changes.

## Key config files
- `config/system.yaml`: global paths, resource limits, logging, security.
- `config/cases/<case_id>.yaml`: parties, court, docket sources, service list.
- `config/pipelines.yaml`: pipeline steps and thresholds.
- `config/redaction.yaml`: redaction patterns and export policies.

## Example: system.yaml (conceptual fields)
- `paths.vault_root`
- `paths.intake_roots[]`
- `resources.max_ocr_workers`
- `resources.max_extract_workers`
- `neo4j.uri`, `neo4j.user`, `neo4j.password_env`
- `tika.url`
- `modes.FILE_READY.confirm_required: true`

## Example: pipelines.yaml (conceptual fields)
- `harvest.steps: [ingest, validate, extract, shard, embed, graph_upsert, reports]`
- `validate.quarantine_on_error: true`
- `extract.ocr_thresholds: {min_chars_per_page: 50}`
- `reports.enabled: [gaps, contradictions, deadlines]`

## Verification
- Config changes are versioned and logged in run ledger.
- Invalid configs fail fast with schema validation errors.

---
# P41 — Docket / ROA ingestion: connectors, normalization, and reconciliation

## Intent
- Convert court-facing docket/ROA listings, notices, and filing receipts into normalized objects that drive deadlines, findings gaps, and drafting.

## Inputs
- ROA / docket exports (PDF/HTML/CSV)
- Filing receipts and confirmations (PDF/email printouts)
- Clerk notices (hearing notices, deficiency notices)
- Orders and minute entries (file-stamped PDFs)

## Outputs
- `docket/roa_normalized.jsonl` (one row per docket entry)
- `docket/roa_entities.json` (parties, attorneys, judge, court, case metadata)
- `docket/roa_link_map.json` (maps docket entries → vault evidence IDs)
- `reports/docket_delta.md` (what changed since last ingest)

## Canonical object model
- `Case`:
  - `case_id`, `court_id`, `caption`, `judge`, `division`, `county`, `jurisdiction`
- `DocketEntry`:
  - `entry_id` (stable), `case_id`, `date_filed`, `date_entered`, `title`, `text_raw`, `doc_count`, `source_ref`
- `DocketDocumentRef`:
  - `entry_id`, `doc_slot`, `filename_hint`, `vault_object_id` (once known)
- `Notice`:
  - `type` (hearing/deficiency/service/other), `served_date`, `hearing_date`, `method`, `source_ref`

## Automation (high-level)
1) **Acquire**: pull ROA/docket export from portal or scan.
2) **Parse**: extract text/tables; normalize dates; preserve raw.
3) **Normalize**: generate stable `entry_id` = hash(case_id + date_entered + title + ordinal).
4) **Reconcile**: attempt to link each docket entry to an existing vault file via:
   - filename similarity
   - embedded stamps (date/case)
   - receipt IDs
   - page-level fingerprints (first-page text signature)
5) **Delta**: compare to prior `roa_normalized.jsonl`; emit new/changed entries only.

## Verification
- Every normalized row retains `source_ref` pointing to: vault object → page/line window.
- Date fields include both `date_filed` and `date_entered` when present; missing values are `null` (not inferred).
- Delta report lists:
  - new entries
  - changed text/title
  - new linked documents

---
# P42 — ServiceChain and NoticeChain: proof-first procedural spine

## Intent
- Turn service proofs, notices, and returns into an auditable “procedural spine” so you can prove (or challenge) jurisdiction, notice, and due process without re-reading the full record each time.

## Inputs
- Proofs of service, return of service, mailing certificates
- Clerk hearing notices, adjournment notices, deficiency notices
- Orders containing service directives (e.g., “serve within X days”)
- Email/text communications only if admissible and preserved (exported with metadata)

## Outputs
- `procedure/service_chain.jsonl` (each attempted service event)
- `procedure/notice_chain.jsonl` (each notice event)
- `procedure/service_coverage_matrix.csv` (document × person × method × status)
- `reports/service_risk.md` (missing/late/invalid service flags)

## Canonical service event fields
- `service_event_id` (stable)
- `case_id`, `document_id` (link to Filing/Order motion), `target_person_id`
- `method` (personal/registered mail/first class/email/other)
- `server_identity` (process server/deputy/party)
- `attempt_ts`, `completed_ts`
- `result` (served/failed/refused/unknown)
- `proof_ref` (vault pointer: file/page)

## Canonical notice event fields
- `notice_event_id` (stable)
- `case_id`, `notice_type` (hearing/adjournment/deficiency)
- `served_ts`, `hearing_ts` (if applicable)
- `method`, `recipient_set`
- `source_ref` (vault pointer)

## Automation
1) **Ingest** proofs/notices from intake folder.
2) **Extract** signature blocks, stamps, and key dates.
3) **Normalize** into chain events with stable IDs.
4) **Link** each chain event to:
   - the underlying filing/order it concerns
   - the person served/notified
5) **Score** procedural risk:
   - missing proof
   - service too close to hearing
   - mismatched names/addresses
   - method inconsistent with required method (where known)

## Verification
- Every chain event contains a single authoritative `source_ref` that can be opened to prove the event.
- A “chain gap” report is generated when:
  - a docket entry exists for a hearing but there is no corresponding notice in the vault
  - a motion/order exists requiring service but no proof exists

---
# P42 — ServiceChain and NoticeChain: proof-first procedural spine

## Intent
- Convert service proofs and notices into an auditable procedural spine that supports: (a) affirmative proof of notice/service, and (b) targeted challenges when service/notice is defective.

## Inputs
- Proof of service / return of service documents (personal, certified, first-class, electronic)
- Certificates of mailing
- Hearing notices and adjournment notices
- Orders that reference service/notice events
- Email/SMS screenshots (when relevant and admissible)

## Outputs
- `procedure/service_chain.jsonl` (event stream)
- `procedure/notice_chain.jsonl` (event stream)
- `procedure/service_gaps.md` (missing proofs, suspicious timing)
- `procedure/proc_assertions.json` (machine-readable assertions + confidence)

## Event schema (service_chain.jsonl)
Each row is an immutable event with pointers to the source.
- `event_id` (stable)
- `case_id`
- `event_type`: `SERVE|MAIL|FILE|RECEIVE|NOTICE|RETURN|AFFIDAVIT|OTHER`
- `served_party` / `serving_party`
- `method`: `personal|certified|first_class|electronic|unknown`
- `service_address` (structured when possible)
- `served_date` (date on proof)
- `filed_date` (date entered/received by court)
- `hearing_date` (if event relates to a hearing)
- `source_ref` (vault object + page/line window)

## Automation (high-level)
1) **Ingest** proofs/notices from intake and link them to `Case`.
2) **Parse** for: names, addresses, method, dates, hearing targets.
3) **Normalize**: dates in ISO format; standardize party names to entity IDs.
4) **Cross-link** to docket entries (P41) using date/title proximity.
5) **Compute gaps**:
   - “hearing is X days after service/notice”
   - missing proof where order indicates service occurred
   - inconsistent method/address across proofs
6) **Emit assertions** (non-conclusive, evidence-backed):
   - `assertion_id`, `claim`, `supporting_event_ids[]`, `contrary_event_ids[]`, `status`.

## Verification
- Every event row must include at least one `source_ref`.
- Every computed gap must list the specific events and the calculation inputs.

---
# P42 — ServiceChain and NoticeChain: proof-first procedural spine

## Intent
- Convert service proofs and notices into an auditable procedural spine that supports: (a) affirmative proof of notice/service, and (b) targeted challenges when service/notice is defective.

## Inputs
- Proof of service / return of service (personal, certified mail, first-class, electronic)
- Certificates of mailing
- Hearing notices and adjournment notices
- Orders with embedded service directives

## Outputs
- `procedure/service_chain.jsonl` (one row per service act)
- `procedure/notice_chain.jsonl` (one row per notice event)
- `procedure/service_gaps.md` (missing proofs, suspicious timing, conflicts)
- `procedure/service_graph.cypher` (optional: nodes/edges for Neo4j)

## Canonical objects
- `ServiceEvent`:
  - `service_id`, `case_id`, `document_id` (what was served), `served_on` (party/attorney), `method`, `server_name`, `served_date`, `served_time`, `address`, `proof_ref`
- `NoticeEvent`:
  - `notice_id`, `case_id`, `event_type` (hearing/adjournment/deficiency), `hearing_datetime`, `notice_date`, `served_on`, `method`, `proof_ref`

## Automation
1) **Ingest proofs/notices** into vault and tag as `SERVICE_PROOF` or `NOTICE`.
2) **Extract structured fields** (names, dates, address, method) using deterministic regex + page anchors.
3) **Normalize times** to ISO-8601; preserve original text snippets for audit.
4) **Link** service/notice rows to:
   - the served document (order/motion)
   - the docket entry (if known)
   - the hearing/event object (if known)
5) **Flag gaps**:
   - hearing without notice artifact
   - order requiring service without proof
   - proof date after hearing date

## Verification
- Each row includes `proof_ref` pointing to vault object + page window.
- A “rebuild” produces identical chain output given identical inputs (idempotent).

---
# P42 — ServiceChain and NoticeChain: proof-first procedural spine

## Intent
- Convert service proofs and notices into an auditable procedural spine that supports: (a) affirmative proof of notice/service, and (b) targeted challenges when service/notice is defective.

## Inputs
- Proof of service / return of service (personal service, certified mail, first-class mail, electronic)
- Certificates of mailing
- Hearing notices, adjournment notices, deficiency notices
- Orders containing service directives (serve by X date; serve by method Y)

## Outputs
- `procedure/service_chain.jsonl` (append-only ServiceEvent rows)
- `procedure/notice_chain.jsonl` (append-only NoticeEvent rows)
- `procedure/service_disputes.jsonl` (Dispute rows keyed to service events)
- `reports/procedure_spine.md` (chronological spine with citations)

## Canonical object model
- `ServiceEvent`:
  - `event_id` (stable), `case_id`, `doc_vault_id`, `served_party`, `served_role` (party/attorney/agency), `method`, `service_date`, `proof_date`, `server_name`, `server_type` (process_server/sheriff/party), `address`, `source_ref`
- `NoticeEvent`:
  - `event_id`, `case_id`, `notice_type` (hearing/adjournment/deficiency/other), `hearing_date_time`, `issued_date`, `served_date`, `method`, `recipient`, `source_ref`
- `Dispute`:
  - `dispute_id`, `event_id`, `assertion` (what is disputed), `basis` (facts/evidence), `requested_relief`, `status`

## Automation (high-level)
1) **Ingest**: vault all service/notice documents, preserving originals.
2) **Extract**: pull structured fields using form patterns and text anchors.
3) **Normalize**:
   - date/time normalization (UTC + local display)
   - party normalization (canonical name table)
   - method normalization (enum)
4) **Link**:
   - link ServiceEvent → the served filing/order via docket/ROA and document stamps
   - link NoticeEvent → hearing/session objects in the calendar spine
5) **Validate**:
   - check for missing service on filings that require it
   - check for notice lead-time anomalies (configurable thresholds)
6) **Report**: emit `procedure_spine.md` grouped by hearing and by filing.

## Verification
- Every event must have `source_ref` pointing to a vault object plus pinpoint (page/line or page/region).
- The spine report must support two read modes:
  - **Affirmative**: “service was completed on X by Y method”
  - **Challenge**: “service is missing/late/unclear” with linked disputes.

---
# P43 — Deadline Engine: docket-driven, rule-driven, and configurable

## Intent
- Produce a continuously updated deadline calendar from docket events, notices, and orders.
- Track: statutory deadlines, rule-based deadlines, and court-ordered deadlines.

## Inputs
- DocketEntry objects (P41)
- NoticeChain and ServiceChain (P42)
- Order extractions (time-to-comply directives)
- Manual overrides (rare; logged)

## Outputs
- `deadlines/deadline_events.jsonl` (append-only)
- `deadlines/deadline_calendar.ics` (importable)
- `reports/deadlines.md` (grouped by urgency and by hearing)
- `reports/deadline_risk.md` (miss risk, ambiguity risk)

## Canonical object model
- `DeadlineEvent`:
  - `deadline_id` (stable)
  - `case_id`
  - `deadline_type` (statute/rule/order/custom)
  - `trigger_event_id` (docket/notice/service/order)
  - `trigger_date`
  - `due_date`
  - `computation` (human-readable formula + machine fields)
  - `timezone`
  - `status` (open/satisfied/disputed)
  - `satisfied_by` (filing_id / proof_id)
  - `source_ref` (pinpoint)

## Automation (high-level)
1) **Trigger detection**: detect deadline triggers from:
   - hearing scheduled
   - motion filed
   - order entered
   - notice served
2) **Rule mapping**:
   - map trigger → candidate deadline rules (configurable by court/track)
   - retain provenance for the mapping (why this rule was applied)
3) **Order override**:
   - if an order sets a specific due date, treat it as higher priority and link the rule deadline as “shadow” (for audit)
4) **Conflict resolution**:
   - multiple candidates → choose the most conservative due date unless a higher-priority rule/order dominates
   - log all candidates in `deadline_risk.md`
5) **Publication**:
   - generate `deadline_calendar.ics` for device import
   - render `deadlines.md` with “next actions” tied to procedural vehicles

## Verification
- Every computed deadline carries:
  - the trigger evidence pointer
  - the selected rule/order pointer
  - a computation trace
- Recompute is deterministic (idempotent) given identical inputs and config.

---
# P44 — Findings Gap Engine: required findings vs record reality

## Intent
- Identify where an order/judgment makes determinations without explicit supporting findings, or where required findings are absent.
- Output is record-safe: it states “gap between requirement and what is present in record” rather than asserting improper motives.

## Inputs
- Orders (file-stamped) extracted into Order objects
- Authority rule library (configured by jurisdiction/track)
- QuoteDB / excerpt index from the record
- Docket context (what was before the court)

## Outputs
- `reports/findings_gap_matrix.csv` (row per required finding)
- `reports/findings_gap_appendix.md` (court-ready appendix format)
- `graphs/findings_gap.graph.json` (nodes: finding requirement, order passage, evidence passage)

## Canonical row schema (findings_gap_matrix.csv)
- `case_id`
- `order_vault_id`
- `order_date`
- `issue_topic` (custody/PT/support/PPO/contempt/housing)
- `required_finding` (short label)
- `requirement_source` (authority ref id)
- `order_quote_ref` (pinpoint if present)
- `record_support_refs[]` (pinpoint excerpts that support)
- `gap_class`:
  - `MISSING_FINDING` (required finding not stated)
  - `UNCLEAR_FINDING` (ambiguous)
  - `NO_RECORD_SUPPORT` (finding stated but no support located)
  - `CONTRARY_RECORD` (record contains contrary excerpt)
- `confidence` (0–100)
- `notes`

## Automation (high-level)
1) **Requirement set selection**: choose the “finding requirements profile” based on issue_topic and court level.
2) **Order passage extraction**:
   - locate sections containing determinations
   - capture quoted passages as QuoteDB entries with pinpoints
3) **Support retrieval**:
   - retrieve candidate supporting excerpts (graph-filtered) from QuoteDB
   - score by topical similarity and temporal relevance
4) **Gap classification**:
   - if order lacks required finding language → `MISSING_FINDING`
   - if order contains finding but no supporting excerpt found → `NO_RECORD_SUPPORT`
   - if contrary excerpt exists with higher relevance → `CONTRARY_RECORD`
5) **Appendix rendering**:
   - emit a clean appendix with numbered items and pinpoints, ready for reuse in motions/appeals.

## Verification
- The appendix is reproducible from the CSV; CSV is reproducible from the underlying QuoteDB pointers.
- Each gap row includes at least one authority pointer and one record pointer (even if the record pointer is “order lacks section,” represented by an order-range anchor).

---
# P45 — Contradiction Engine: Order vs Order vs Evidence vs Docket

## Intent
- Detect contradictions and tension points across:
  - order-to-order
  - order-to-evidence
  - docket-to-order (procedural mismatch)
- Output is phrased as contradictions between statements and record elements, not accusations.

## Inputs
- Orders extracted into structured objects (with QuoteDB pinpoints)
- Evidence items + excerpts (QuoteDB)
- Docket timeline (P41) and procedural spine (P42)

## Outputs
- `reports/contradiction_map.csv`
- `reports/contradiction_brief.md` (issue-grouped)
- `graphs/contradictions.graph.json`

## Canonical contradiction row schema
- `contradiction_id`
- `case_id`
- `topic`
- `statement_a_ref` (QuoteRef)
- `statement_b_ref` (QuoteRef)
- `type`: `ORDER_ORDER` | `ORDER_EVIDENCE` | `DOCKET_ORDER` | `PROCEDURE_ORDER`
- `relation`: `INCONSISTENT` | `TENSION` | `OMISSION`
- `severity` (0–100)
- `remedy_hints[]` (procedural vehicles; non-binding)

## Automation (high-level)
1) **Extract propositions**: convert order passages into “Proposition” nodes with normalized subject/verb/object and modality.
2) **Temporal alignment**: index each proposition by (event_date, entered_date, effective_date).
3) **Pairing**:
   - within-topic: compare propositions within same topic window
   - cross-topic: compare where a later order implicitly depends on earlier facts
4) **Contradiction scoring**:
   - direct logical negation scores highest
   - “silent override” scores medium
   - omission (expected statement absent) scores based on requirement profile
5) **Output synthesis**:
   - produce short “contradiction statements” that cite both sides and list the factual hinge.

## Verification
- Every contradiction row links to both sides with pinpoints.
- Severity is explainable (feature breakdown stored in a sidecar JSON).

---
# P46 — Examination Pack Engine: testimony goals → admissible question banks

## Intent
- Generate structured question banks for hearings/trials (and deposition outlines where permitted), tightly linked to:
  - a specific fact to prove/disprove
  - the exhibit/quote that supports the fact
  - the procedural purpose (foundation, impeachment, credibility, timeline)
- Keep format adaptable: “question bank” rather than a rigid script, because courtroom control varies.

## Inputs
- Issues list (topic → elements/facts to prove)
- QuoteDB excerpts (page-keyed)
- Contradiction map (P45)
- Witness roster (party, third-party, expert, custodian)

## Outputs
- `reports/exam_pack_<hearing_id>.md`
- `reports/witness_goal_matrix.csv`

## Canonical witness_goal_matrix schema
- `witness_id`
- `topic`
- `goal` (e.g., authenticate exhibit; establish timeline; impeach claim)
- `fact_to_establish`
- `supporting_refs[]` (QuoteRef / ExhibitRef)
- `question_type` (foundation/open/leading/impeachment)
- `risk_notes`

## Automation (high-level)
1) **Goal selection**: pick 3–7 goals per witness per hearing (configurable).
2) **Fact decomposition**: each goal decomposes into 3 layers:
   - anchors (undisputed basics)
   - contested hinge facts
   - impeachment pivots
3) **Question drafting**:
   - foundation questions to authenticate the record
   - chronology questions to lock dates/times
   - impeachment questions that force a yes/no against a pinned quote
4) **Exhibit integration**:
   - each question block references the exhibit/quote it is aiming to use
   - each block includes “if objection → alternate path” options
5) **Output formatting**:
   - short blocks with checkboxes for live use
   - print-safe layout

## Verification
- Every impeachment question includes a specific pinned contradiction reference.
- The pack can be regenerated deterministically for the same hearing_id + inputs.

---
# P47 — Motion/Brief Compiler: claim-to-proof-to-authority assembly

## Intent
- Assemble filings as a reproducible compilation process, not hand-written documents.
- Enforce structure: factual assertions must reference record artifacts; legal propositions must reference authority snapshots.

## Inputs
- Vehicle selection (motion type / petition type)
- Findings gaps (P44) and contradictions (P45)
- Service/deadline constraints (P42–P43)
- Record excerpts (QuoteDB)

## Outputs
- `drafts/<case_id>/<run_id>/<vehicle>/<doc>.docx` (or PDF)
- `drafts/<case_id>/<run_id>/tables/authority_triples.jsonl`
- `drafts/<case_id>/<run_id>/tables/fact_assertions.jsonl`
- `reports/drafting_preflight.md`

## Core compilation units
- `FactAssertion`:
  - `fact_id`, `text`, `support_refs[]`, `confidence`, `dispute_tag`
- `LegalProposition`:
  - `prop_id`, `text`, `authority_ref`, `pinpoint`, `effective_date`
- `ArgumentBlock`:
  - `block_id`, `claims[]`, `facts[]`, `props[]`, `requested_relief`

## Automation (high-level)
1) **Select vehicle template**: choose a document blueprint by court/track.
2) **Populate facts**:
   - only from FactAssertion objects with support refs
   - unresolved disputes are explicitly labeled as disputed
3) **Populate propositions**:
   - only from the authority snapshot set for the jurisdiction/date
4) **Render**:
   - render to DOCX/PDF with consistent headings and page numbering
5) **Preflight**:
   - fail if any fact lacks support refs
   - warn if any proposition lacks pinpoints

## Verification
- Preflight report enumerates every paragraph with:
  - fact/proposition IDs used
  - evidence/authority refs used
- Output includes a “record pointer index” so every citation is traceable.

---
# P48 — Exhibit Binder Builder: cover pages, stamping, and index

## Intent
- Produce court-ready exhibit packets consistently:
  - cover page per exhibit
  - exhibit label overlay
  - combined PDF with bookmarks
  - exhibit index keyed to citations used in briefs

## Inputs
- Selected exhibit list (ExhibitRef objects)
- Source vault objects (originals)
- Optional: extracted page ranges (if partial exhibits are used)

## Outputs
- `exhibits/<case_id>/<run_id>/Exhibit_Index.csv`
- `exhibits/<case_id>/<run_id>/Exhibit_<ID>_<short_title>.pdf`
- `exhibits/<case_id>/<run_id>/Exhibits_Combined.pdf`
- `reports/exhibits_preflight.md`

## Binder rules
- Preserve originals; stamping occurs on derivatives only.
- Each exhibit gets a cover page containing:
  - case caption
  - exhibit ID
  - description
  - source filename
  - date (if known)
  - offering party

## Automation (high-level)
1) Convert each source to a standardized PDF derivative (if needed).
2) Generate cover page PDF.
3) Apply small exhibit label overlay to each page of the exhibit.
4) Merge cover + exhibit into one file.
5) Create combined PDF and insert bookmarks at each exhibit boundary.
6) Generate index and cross-reference to citations used in the motion/brief.

## Verification
- Index row must contain a vault pointer for the underlying source.
- Combined PDF page count equals sum of individual exhibits.

---
# P49 — Hearing-Mode Daemon: real-time capture, preservation, and next actions

## Intent
- Provide an operational “hearing mode” that:
  - captures what happened (notes + timestamps)
  - tags immediate preservation actions (request transcript, request exhibits, file notice)
  - logs objections and rulings for later use
- Designed for human-in-the-loop use during hearings.

## Inputs
- Scheduled hearing object (from NoticeChain P42)
- Agenda (issues expected)
- Question bank (P46)

## Outputs
- `hearing/<case_id>/<hearing_id>/Live_Notes.md`
- `hearing/<case_id>/<hearing_id>/Rulings.jsonl`
- `hearing/<case_id>/<hearing_id>/Preservation_Actions.md`

## Automation (high-level)
1) Pre-hearing: generate a one-page “today packet” with:
   - hearing logistics
   - top 5 goals
   - exhibits likely to be used
2) Live capture: append-only note lines with timestamps and tags:
   - `OBJ:` objection
   - `RUL:` ruling
   - `REQ:` request to court
   - `ADM:` exhibit admitted
3) Post-hearing: compute a preservation checklist:
   - transcript order
   - follow-up filings
   - deadline updates

## Verification
- Each “critical event” line links to the relevant exhibit/question bank goal.

---
# P50 — Appellate / Extraordinary Relief Pipeline: record assembly and issue framing

## Intent
- Treat appeals/supervisory/extrajudicial escalation as a pipeline:
  - record assembly
  - issue selection
  - standard-of-review mapping
  - appendix construction

## Inputs
- Docket/ROA (P41)
- Orders + transcripts + exhibits
- Findings gaps (P44) and contradictions (P45)
- Preservation log (P49)

## Outputs
- `appeal/<case_id>/<run_id>/Issue_Map.md`
- `appeal/<case_id>/<run_id>/Record_Index.csv`
- `appeal/<case_id>/<run_id>/Appendix.pdf` (or appendix bundle)
- `appeal/<case_id>/<run_id>/Argument_Outline.md`

## Automation (high-level)
1) Identify candidate issues from:
   - missing findings
   - procedural anomalies
   - evidentiary rulings
2) For each issue, compute:
   - governing standard of review (configured)
   - preservation status (objected? raised?)
   - best supporting excerpts
3) Build record index:
   - order pages
   - transcript pages
   - exhibit pages
4) Render appendix:
   - clean, page-numbered, bookmarks

## Verification
- Every issue in Issue_Map has a pointer set: order + transcript/exhibit.

---
# P51 — Judicial Conduct Track: narrative restraint + evidence discipline

## Intent
- Provide a separate “judicial conduct” pipeline that:
  - stays evidence-first
  - avoids argumentative tone
  - maps specific conduct to specific record points

## Inputs
- On-record statements (transcripts)
- Orders and procedural anomalies
- Preservation log (P49)

## Outputs
- `conduct/<judge_id>/<run_id>/Allegations_Table.csv`
- `conduct/<judge_id>/<run_id>/Evidence_Pack_Index.csv`
- `conduct/<judge_id>/<run_id>/Narrative.md`

## Canonical allegation schema
- `allegation_id`
- `event_date`
- `conduct_type` (demeanor/ruling/procedure/communication)
- `record_refs[]`
- `impact` (how it affected notice, evidence, rights)
- `requested_action` (discipline/assignment review/other)

## Verification
- Every allegation row has at least one transcript or order pinpoint.

---
# P52 — Settlement / Stipulation Support: leverage from provable gaps

## Intent
- Convert evidence-backed weaknesses and risks into negotiation leverage without overclaiming.

## Inputs
- Findings gaps (P44), contradictions (P45)
- Procedural risk report (P43)
- Damages/harm notes (case-specific)

## Outputs
- `negotiation/<case_id>/<run_id>/Leverage_Summary.md`
- `negotiation/<case_id>/<run_id>/Offer_Terms.yaml`
- `negotiation/<case_id>/<run_id>/Concessions_Map.md`

## Automation (high-level)
1) Generate a one-page leverage summary that lists:
   - provable contradictions
   - provable missing findings
   - procedural exposure
2) Translate into terms:
   - what you want
   - what you offer
   - what you will file if not resolved (procedural, not threats)
3) Generate a concessions map to track what is negotiable vs non-negotiable.

## Verification
- Every leverage claim has a record pointer.

---
# P53 — Risk Model: failure modes, mitigation, and “do no harm” defaults

## Intent
- Enumerate system failure modes (technical + procedural) and enforce mitigation at design time.

## Inputs
- Pipeline definitions (P34–P40)
- User risk tolerance settings

## Outputs
- `risk/Risk_Register.md`
- `risk/Safety_Invariants.md`
- `risk/Failure_Playbooks/` (one file per high-impact failure)

## Failure mode taxonomy
- **Data loss**: originals overwritten, vault corruption
- **Provenance loss**: excerpts without pointers, broken links
- **Deadline errors**: missed due date due to wrong trigger
- **Over-automation**: system produces filings without human review
- **Privacy breach**: exporting sensitive items unintentionally

## Mitigation controls (defaults)
- Originals immutable; derivatives only.
- Two-phase operations for write actions:
  - phase A: build plan + show diffs
  - phase B: execute only with explicit confirmation in FILE_READY mode
- Deadline computation logs all candidates and the selection rule.
- Export policies are deny-by-default.

## Verification
- A “dry run” must produce the same planned outputs as a real run, minus execution.
- High-impact operations require a signed run ledger entry.

---
# P54 — Test Strategy: reproducible correctness with minimal overhead

## Intent
- Provide a layered testing strategy that keeps the system stable as it grows.

## Inputs
- Modules and CLIs
- Sample fixture set (non-sensitive)

## Outputs
- `tests/` (unit + contract tests)
- `fixtures/` (small, synthetic record samples)
- `reports/test_matrix.md`

## Test layers
- **Unit**: parsers, normalizers, serializers
- **Contract**: pipeline stage I/O schemas
- **Golden-run**: end-to-end pipeline produces identical manifests for identical fixtures
- **Negative**: corrupted PDFs, missing pages, malformed dates

## Verification
- Every pipeline stage must have:
  - schema validation test
  - at least one negative-case test
- CI must run the fastest meaningful subset on every PR.

---
# P55 — Release Engineering: versioning, installers, and upgrade safety

## Intent
- Ship LitigationOS as a reproducible release that upgrades safely without breaking the vault.

## Inputs
- Build configuration and dependency lockfiles
- Supported platform matrix (Windows, Linux, Android/Termux optional)

## Outputs
- `dist/` release artifacts
- `release/Release_Notes.md`
- `release/Migration_Guide.md`

## Release rules
- Versioning: `MAJOR.MINOR.PATCH` with a date-stamped build tag.
- Migrations:
  - additive schema changes are preferred
  - destructive migrations require explicit migration scripts and backups
- Installers must not touch vault originals; only install binaries and configs.

## Verification
- Release build is reproducible in CI.
- A “smoke run” on fixtures is required per release.

---
# P56 — Backup & Disaster Recovery: vault survival discipline

## Intent
- Ensure the vault can survive device failure, corruption, and user error.

## Inputs
- Vault root and config
- Backup targets (external drive, cloud mirror, offline)

## Outputs
- `backup/Backup_Plan.md`
- `backup/Restore_Playbook.md`
- `backup/Integrity_Report.md`

## Backup approach
- 3-2-1 rule (three copies, two media, one offsite) adapted to your constraints.
- Backups are append-only snapshots; never “sync delete” originals.
- Integrity checks:
  - periodic manifest verification
  - periodic random sampling of restorations

## Verification
- Restore drill quarterly (fixtures + a small real subset).
- Restore is documented step-by-step and produces a validated manifest.

---
# P57 — Mobile / Field Intake: capture-first, sync-later

## Intent
- Enable fast capture of documents, photos, audio, and notes from a phone while preserving provenance.

## Inputs
- Camera scans / PDFs
- Audio recordings (hearing hallway notes, interviews where lawful)
- Quick notes

## Outputs
- `intake/mobile/<run_id>/` (raw captures)
- `intake/mobile/<run_id>/Mobile_Intake_Manifest.json`
- Synced vault objects (once imported)

## Capture protocol
- Each capture creates:
  - raw file
  - a JSON sidecar with: timestamp, location (optional), source device, short description, case_id guess
- Capture names are deterministic: `YYYYMMDD_HHMMSS_<type>_<shortdesc>.<ext>`

## Verification
- Manifest references every captured file; no orphan files.
- A later import run links the mobile manifest into the main run ledger.

---
# P58 — AI Guardrails: reliability, non-invention, and provenance binding

## Intent
- Make AI outputs usable by binding them to evidence and clearly labeling uncertainty.

## Inputs
- QuoteDB, Findings gaps, Contradictions, Authority snapshot
- Drafting mode (DISCOVERY/DRAFT/FILE_READY)

## Outputs
- `ai/outputs/<run_id>/ContextPack.json`
- `ai/outputs/<run_id>/Drafts/`
- `ai/outputs/<run_id>/Guardrail_Report.md`

## Guardrail rules
- AI cannot emit a factual claim without at least one support ref.
- AI cannot emit a legal proposition without an authority ref + pinpoint.
- Any unresolved uncertainty must be labeled as:
  - `UNKNOWN` (not found)
  - `DISPUTED` (conflicting excerpts)
  - `ASSUMPTION` (explicitly hypothetical)

## Verification
- Guardrail report lists every unsupported sentence and blocks FILE_READY.

---
# P59 — Productization Track: turning LitigationOS into a durable business-grade tool

## Intent
- Create a revenue-capable product without contaminating the litigation vault or compromising privacy.

## Inputs
- Stable core pipelines (harvest, extract, shard, graph upsert, reports)
- Licensing model decisions

## Outputs
- `product/ROADMAP.md`
- `product/EDITION_MATRIX.md`
- `product/DEMO_FIXTURES/` (synthetic)

## Product boundary rules
- The product uses synthetic demo fixtures only.
- Real case vaults never ship with the product.
- Telemetry is opt-in; offline-first is supported.

## Verification
- A “clean room” build of the product passes without any private fixtures present.

---
# P60 — First 14 Days Plan: execute to a working spine, then expand

## Intent
- Provide an execution plan that produces a working LitigationOS core quickly and safely.

## Day 1–2: Spine
- Create vault + manifests + run ledger.
- Build ingest → extract → shard → search (no graph yet).

## Day 3–5: Procedure
- Implement docket ingest + ServiceChain + Deadline Engine.
- Produce first “procedure spine” report.

## Day 6–8: Findings and contradictions
- Implement Findings Gap Engine and Contradiction Engine.
- Produce first appendix-ready reports.

## Day 9–11: Drafting and exhibits
- Implement Motion/Brief Compiler (preflight enforced).
- Implement Exhibit Binder Builder.

## Day 12–14: Graph + retrieval
- Add Neo4j schema and idempotent import.
- Add GraphRAG retrieval and ContextPacks.

## Verification
- By Day 14, you can generate:
  - a deadline calendar
  - a procedure spine
  - a findings gap appendix
  - a contradiction brief
  - a draft motion with a linked exhibit binder

---



===============================================================================
APPEND-ONLY EXPANSION • PAGES P61–P85 (v2026-01-18.3)
===============================================================================
Contract:
- Append-only: prior content unchanged.
- “Page” is an operational unit (machine-readable schema) not a PDF render.
- All “court outputs” remain FILE_READY only when provenance + citations are complete.

-------------------------------------------------------------------------------
PAGE P61 — AUTHORITY SNAPSHOT: BUILD, VERSION, AND PINPOINT DISCIPLINE
-------------------------------------------------------------------------------
Intent
- Create a single authoritative, versioned corpus of rules/statutes/orders/caselaw used by the system.
- Enforce “no-out-of-snapshot” proposition gating for any FILE_READY output.

Inputs
- Raw authority sources (PDF/HTML/TXT), including:
  - Court rules (MCR), statutes (MCL), evidence rules (MRE), administrative orders, local court rules.
  - Court orders and notices that impose case-specific procedures.
- “Snapshot metadata”:
  - authority_id, source_url_or_path, version_label, effective_date_start, effective_date_end (if known), retrieved_at, hash (optional).

Outputs
- authority_snapshot/authority_snapshot_index.json
  - Array of AuthorityRef rows with stable auth_ref_id and pinpoints.
- authority_snapshot/authority_text_store/
  - Normalized text shards keyed by (auth_ref_id, section, subsection, paragraph).
- authority_snapshot/authority_propositions.jsonl
  - Proposition atoms: {prop_id, prop_text, auth_ref_id, pinpoint, tags, confidence="SOURCE_VERIFIED"}.
- authority_snapshot/AUTH_SNAPSHOT_README.md

Automation
- Pipeline: ingest → normalize → segment → index → proposition extraction (human-reviewed for “verified” status).
- Pinpoint scheme (uniform):
  - For rules/statutes: “Rule X.YY(A)(1)” + section/paragraph if present.
  - For cases: “CaseName, Reporter (Year), pincite” (only if the exact text exists in the corpus).
- Enforce two-tier proposition states:
  - CANDIDATE: extracted but not verified word-for-word.
  - VERIFIED: verified against normalized authority shard.

Verification
- Snapshot audit report:
  - Missing effective dates flagged as UNKNOWN_EFFECTIVE_DATE (allowed; cannot be used to assert temporal applicability).
  - Duplicate authorities deduped by canonicalization rules.
- “No-out-of-snapshot gate” test:
  - FILE_READY compilation fails if any proposition lacks VERIFIED authority backing.

-------------------------------------------------------------------------------
PAGE P62 — FORMS-FIRST VEHICLE MAP: FROM RELIEF → VEHICLE → ELEMENTS → PROOFS
-------------------------------------------------------------------------------
Intent
- Convert “what you want” into precise, court-recognized procedural vehicles (forms/motions/appeals).
- Require every vehicle to define proof obligations (POs) that can be machine-checked.

Inputs
- Relief request (structured): {relief_type, court_level, case_id, urgency, constraints}
- Vehicle catalog (initially seeded; then extended):
  - Each Vehicle has: vehicle_id, jurisdiction, controlling_rules, required_forms, service_rules, deadlines, elements/standards.

Outputs
- vehicle_map/vehicle_catalog.json
- vehicle_map/vehicle_instances/<case_id>/<vehicle_instance_id>.json
- vehicle_map/vehicle_po_templates.jsonl
  - PO templates keyed by vehicle_id.
- vehicle_map/vehicle_decision_log.jsonl
  - “Why we picked this vehicle” with traceable rationale.

Automation
- Vehicle selection engine (deterministic ranking):
  1) Match by court level and relief type.
  2) Filter by time constraints (e.g., emergency/ex parte).
  3) Filter by availability of required facts/evidence.
  4) Score by risk and likelihood of procedural rejection.
- Emits “top candidate list” + recommended vehicle, but never forces filing.

Verification
- Vehicle completeness check:
  - Must specify: form(s), rule(s), service chain, deadlines, and at least one PO template.
- If any required part missing:
  - Emit PINPOINT_MISSING items with acquisition plan; keep state at DRAFT.

-------------------------------------------------------------------------------
PAGE P63 — PCW + ADD + PCG: PRACTICAL GATEKEEPING THAT DOES NOT STALL PROGRESS
-------------------------------------------------------------------------------
Intent
- Maintain forward motion by allowing DISCOVERY/DRAFT artifacts while protecting FILE_READY actions with PCG.
- Quantify “how sure” the system is (Assurance-Driven Deliberation) before irreversible steps.

Inputs
- Vehicle instance file (P62)
- Evidence atoms (P67)
- Authority snapshot propositions (P61)
- Service/notice constraints (P42/P66)

Outputs
- pcw/po_state/<case_id>/<vehicle_instance_id>.json
  - Per-PO: state OPEN|PARTIAL|SATISFIED, evidence_refs, auth_refs, validator results.
- pcw/add_assurance/<run_id>.json
  - Assurance score breakdown: coverage, provenance, contradiction risk, service readiness.
- pcw/pcg_gate_report/<vehicle_instance_id>.md
  - FILE_READY pass/fail with blockers.

Automation
- PO evaluation rules:
  - PO SATISFIED only if:
    - Evidence reference exists with stable pointer(s) and provenance,
    - Authority proposition VERIFIED,
    - Validator passes (format/logic tests).
- ADD scoring (example rubric; configurable):
  - Coverage (0–30), Provenance (0–25), Consistency (0–20), Procedural readiness (0–15), Clarity (0–10).
- PCG final gate:
  - PASS only when all “core” POs SATISFIED and service/deadlines are PASS.

Verification
- Gate enforcement unit tests:
  - “No citations → cannot be FILE_READY.”
  - “Any unresolved contradiction → cannot be FILE_READY unless addressed in disclosure section.”

-------------------------------------------------------------------------------
PAGE P64 — QUOTELOCK: SAFE QUOTING AND CITATION IN COURT-FACING OUTPUTS
-------------------------------------------------------------------------------
Intent
- Prevent quote drift and maintain record integrity for every verbatim excerpt.
- Allow “candidate quotes” during discovery without contaminating final filings.

Inputs
- Extracted text shards (orders/transcripts/authority)
- Candidate quote selections from analysis tools

Outputs
- quotes/quote_ledger.jsonl
  - Each quote: {quote_id, text, source_ref, page, line_range, extraction_method, status=CANDIDATE|VERIFIED}
- quotes/quote_verification_reports/<quote_id>.json
  - Dual extraction check results.
- quotes/quote_manifest_<run_id>.csv

Automation
- Two-pass verification requirement for VERIFIED status:
  - Pass A: primary extractor
  - Pass B: independent extractor/method
- If mismatch:
  - Keep as CANDIDATE and emit QUOTELOCK_MISMATCH record.

Verification
- FILE_READY compiler refuses to include CANDIDATE quotes.
- DRAFT outputs may include CANDIDATE quotes with conspicuous tag [[UNVERIFIED_QUOTE]].

-------------------------------------------------------------------------------
PAGE P65 — RECORD SPINE: ORDERS, TRANSCRIPTS, ROA, AND “WHAT THE COURT ACTUALLY DID”
-------------------------------------------------------------------------------
Intent
- Build the canonical “Record Spine” that all later analysis depends on.
- Separate “allegations” from “recorded actions” and “procedural posture.”

Inputs
- ROA/docket exports (CSV/PDF scrape)
- Orders (file-stamped PDFs)
- Hearing notices + proofs of service
- Transcripts (if available)

Outputs
- record_spine/record_spine.json
  - {case_id, court, judge, parties, docket_entries[], orders[], hearings[], service_events[]}
- record_spine/record_spine_timeline.jsonl
  - Time-ordered spine events with bitemporal timestamps.
- record_spine/record_spine_gaps.json
  - Missing transcripts, missing notices, uncertain dates.

Automation
- Reconciliation rules:
  - Docket entry “order entered” must link to an actual file-stamped PDF or be flagged.
  - Hearing occurrence must link to notice + proof of service or be flagged.
- Bitemporal model:
  - event_time (when it happened) vs recorded_time (when it entered the record).

Verification
- Spine integrity check:
  - Every spine event has at least one “source of record” pointer.
  - Unresolved gaps are enumerated with acquisition plans.

-------------------------------------------------------------------------------
PAGE P66 — SERVICE/NOTICE ENGINE: COMPUTABLE SERVICE CHAINS AND DEFECT DETECTION
-------------------------------------------------------------------------------
Intent
- Detect defective notice/service and model how defects affect enforceability, contempt exposure, and appeal posture.
- Produce a service chain that is machine-checkable and printable.

Inputs
- Service proofs (returns, affidavits, officer returns)
- Notices (hearing notices, summons, scheduling orders)
- Court rules (service/notice provisions) from snapshot

Outputs
- service_chain/service_chain.jsonl
  - {service_event_id, document_id, method, server, recipient, address, served_at, proof_ref}
- service_chain/service_defects.json
  - Defects: missing proof, late notice, wrong address, improper method, unclear party served.
- service_chain/service_exhibits/
  - Binder-ready extracts of service proofs and notices.

Automation
- Defect detection heuristics (non-dispositive, flag-only):
  - Notice window below minimum (if authority known); otherwise mark UNKNOWN_MIN_NOTICE.
  - Non-party server for restricted documents flagged.
  - Address mismatch flagged.
- Produces “defect memo” DRAFT output with citations.

Verification
- If service is core PO for a motion:
  - PCG requires service chain PASS or explicit justified alternative (e.g., court-ordered service method).

-------------------------------------------------------------------------------
PAGE P67 — EVIDENCE ATOMS: THE SMALLEST AUDITABLE UNITS
-------------------------------------------------------------------------------
Intent
- Convert every evidentiary claim into a linkable atom that can be cited, bundled, and validated.

Inputs
- Originals: PDF, DOCX, image, audio, video, text
- Derivatives: OCR text, transcripts, extracted metadata

Outputs
- evidence/evidence_atoms.jsonl
  - Atom schema:
    - atom_id (stable), file_id, kind, page/time range, snippet_ref, provenance_ref
    - relevance_tags, admissibility_notes (DRAFT), linked_entities
- evidence/evidence_index.csv
- evidence/evidence_atom_exhibits/ (optional coverpages/binders)

Automation
- Atom creation rules:
  - PDFs: per page or per paragraph shard
  - Audio/video: per timestamp segment
  - Messages: per message event
- Each atom links back to the original file and extraction method.

Verification
- Every atom must have stable pointers to original + derivative.
- Duplicates deduped by canonicalization + similarity checks (never deleting originals).

-------------------------------------------------------------------------------
PAGE P68 — CONTRADICTION MAP ENGINE: ORDER VS ORDER VS EVIDENCE
-------------------------------------------------------------------------------
Intent
- Identify internal inconsistencies and “findings gaps” without editorializing.
- Produce a contradiction table usable in hearings and appellate appendices.

Inputs
- Record spine (P65)
- Evidence atoms (P67)
- Quote ledger (P64)

Outputs
- analysis/contradictions/contradiction_map.json
  - Nodes: statements (order excerpts, testimony excerpts, party assertions)
  - Edges: contradiction/support/unknown
- analysis/contradictions/contradiction_table.csv
  - columns: A_statement_ref, B_statement_ref, relationship, notes, needed_sources
- analysis/contradictions/contradiction_appendix.md (DRAFT)

Automation
- Relationship inference is always “soft” until validated:
  - Uses rules: temporal conflict, factual conflict, legal standard conflict, procedural conflict.
- Outputs require “why it might conflict” not “it is false.”

Verification
- Any contradiction used in FILE_READY must cite VERIFIED quotes or precise page references.

-------------------------------------------------------------------------------
PAGE P69 — FINDINGS GAP ENGINE: “WHAT IS MISSING” AS A FIRST-CLASS OBJECT
-------------------------------------------------------------------------------
Intent
- Turn missing findings (or missing record support) into structured, checkable objects.

Inputs
- Orders and hearing outcomes
- Legal standard templates (from authority snapshot)
- Vehicle PO templates

Outputs
- analysis/findings_gaps/findings_gap_matrix.json
  - {gap_id, required_finding, expected_support, observed_support, citations, status}
- analysis/findings_gaps/findings_gap_appendix.md
- analysis/findings_gaps/gap_to_vehicle_candidates.json

Automation
- For each relevant legal standard:
  - Determine “required finding slots” and check whether order text contains them.
- If unknown whether required:
  - Mark LEGAL_STANDARD_UNKNOWN and request authority supplementation.

Verification
- Every gap must point to:
  - (a) the expected standard proposition (VERIFIED) or be flagged,
  - (b) the order excerpt (VERIFIED or page pointer).

-------------------------------------------------------------------------------
PAGE P70 — DRAFT COMPILER: FROM ATOMS → SECTIONS → BRIEF/MOTION PACKETS
-------------------------------------------------------------------------------
Intent
- Generate court-ready documents by assembling validated blocks, not by free-form drafting.
- Ensure every paragraph is traceable to evidence/authority or flagged.

Inputs
- Vehicle instance (P62)
- PO state (P63)
- Evidence atoms + quote ledger + authority propositions

Outputs
- drafts/<case_id>/<vehicle_instance_id>/document.md
- drafts/<case_id>/<vehicle_instance_id>/citations.jsonl
- drafts/<case_id>/<vehicle_instance_id>/block_trace.json
- drafts/<case_id>/<vehicle_instance_id>/compile_report.md

Automation
- Block types:
  - FACT_BLOCK (requires evidence atoms)
  - LAW_BLOCK (requires VERIFIED propositions)
  - ARG_BLOCK (requires at least 1 FACT_BLOCK + 1 LAW_BLOCK)
  - RELIEF_BLOCK (requires vehicle mapping)
- Citation policy:
  - Every paragraph must have citations OR be tagged [[NO_CITATION:EXPLAIN]] (DRAFT only).

Verification
- FILE_READY requires:
  - Zero [[NO_CITATION]] tags,
  - PCG PASS,
  - QuoteLock verified if quoting.

-------------------------------------------------------------------------------
PAGE P71 — EXHIBIT FACTORY: COVERPAGES, LABELS, AND BINDER ASSEMBLY
-------------------------------------------------------------------------------
Intent
- Generate exhibit packets consistently: cover page + exhibit label + source pointer.
- Keep original evidence unmodified; stamping occurs on duplicates only.

Inputs
- Evidence atoms + original file refs
- Case caption data + offering party

Outputs
- exhibits/<case_id>/EXHIBIT_MATRIX.csv
- exhibits/<case_id>/packets/Exhibit_<ID>_<slug>.pdf
- exhibits/<case_id>/covers/Exhibit_<ID>_cover.pdf
- exhibits/<case_id>/labels/Exhibit_<ID>_label.png

Automation
- Exhibit ID allocation:
  - Deterministic: based on sorted evidence atom IDs + run_id.
- Coverpage fields:
  - case caption, exhibit ID, description, source file pointer, date, offering party, provenance note.

Verification
- Packet validation:
  - Ensure cover first page present.
  - Ensure no modification of originals in-place.
  - Ensure Exhibit Matrix cross-links to packet paths.

-------------------------------------------------------------------------------
PAGE P72 — PACKET PREFLIGHT: “MI-FILE READY” WITHOUT GUESSWORK
-------------------------------------------------------------------------------
Intent
- Ensure compiled packet is technically and procedurally ready before filing/service.
- Provide explicit “fix list” rather than vague failure.

Inputs
- Draft compiler output
- Exhibit packets
- Service chain readiness
- Court-specific formatting rules (if known) from authority snapshot or local rules

Outputs
- preflight/<case_id>/<vehicle_instance_id>/PREFLIGHT_REPORT.md
- preflight/<case_id>/<vehicle_instance_id>/PREFLIGHT_FIXLIST.json
- preflight/<case_id>/<vehicle_instance_id>/bundle/ (staging folder)

Automation
- Checks:
  - Required attachments present
  - PDF readability, page order, bookmarks (optional)
  - Caption completeness
  - Signature blocks present (if required)
  - Service method + addresses present
  - Deadline compliance check

Verification
- Preflight gate:
  - FILE_READY requires all “critical” checks PASS.
  - Non-critical warnings allowed but must be disclosed in report.

-------------------------------------------------------------------------------
PAGE P73 — HEARING-MODE DAEMON: REAL-TIME PRESERVATION AND ACTION LOGGING
-------------------------------------------------------------------------------
Intent
- Capture events during hearings (notes, rulings, objections, exhibit admissions) in a structured, later-usable format.
- Avoid “memory drift” by recording in near-real-time.

Inputs
- Hearing calendar entry (time/place)
- Open note capture channel (mobile/desktop)
- Prebuilt question bank + contradiction tables

Outputs
- hearing_mode/<case_id>/<hearing_id>/HEARING_LOG.jsonl
- hearing_mode/<case_id>/<hearing_id>/RULING_SUMMARY.md
- hearing_mode/<case_id>/<hearing_id>/PRESERVATION_FLAGS.json

Automation
- Hotkeys/templates for entries:
  - TIME, SPEAKER, EVENT_TYPE (ruling/objection/exhibit), SUMMARY, follow-up tasks.
- Immediately creates:
  - “Transcript order” task stub if transcript is required for appeal.
  - “Record correction” tasks if discrepancies observed.

Verification
- Post-hearing reconciliation:
  - Compare hearing log to transcript (when obtained) and mark deltas.

-------------------------------------------------------------------------------
PAGE P74 — APPELLATE / EXTRAORDINARY RELIEF PACKAGING: REPEATABLE BUILDS
-------------------------------------------------------------------------------
Intent
- Create repeatable appellate packets (appendices) using the same block+trace discipline as trial motions.
- Maintain separation: argument vs record appendix.

Inputs
- Findings gap appendix (P69)
- Contradiction appendix (P68)
- Verified quote ledger (P64)
- Authority propositions (P61)

Outputs
- appellate/<case_id>/<app_id>/APPENDIX_INDEX.md
- appellate/<case_id>/<app_id>/APPENDIX_PACKETS/
- appellate/<case_id>/<app_id>/ARGUMENT_DRAFT.md
- appellate/<case_id>/<app_id>/BUILD_REPORT.md

Automation
- Appendix builder:
  - Select record excerpts by citation keys
  - Generate index with page references (internal page numbers can be computed from packet assembly order).
- Argument builder:
  - Only references appendix items by stable IDs and citations.

Verification
- “Appendix completeness” test:
  - Every cited record item in argument exists in appendix.
  - No CANDIDATE quotes used.

-------------------------------------------------------------------------------
PAGE P75 — JUDICIAL CONDUCT TRACK: FACT-ONLY NARRATIVE + EVIDENCE MAP
-------------------------------------------------------------------------------
Intent
- Produce a fact-only, record-anchored narrative for judicial conduct complaints.
- Avoid legal conclusions where not necessary; focus on verifiable acts/quotes/omissions.

Inputs
- Hearing log + transcripts
- Orders
- Denial conversion map (if used)
- Authority (canons/rules) snapshot entries (if included)

Outputs
- conduct/<case_id>/JTC_FACT_MEMO.md (DRAFT)
- conduct/<case_id>/JTC_EVIDENCE_MAP.csv
- conduct/<case_id>/JTC_TIMELINE.jsonl

Automation
- Event-to-evidence mapping:
  - Each allegation line must map to (order/transcript/page/line) or be omitted.
- Optional: “severity scoring” is always internal, never filed as-is unless rewritten.

Verification
- Zero invented facts rule:
  - Any line without evidence pointer is removed or marked as “unverified; not included.”

-------------------------------------------------------------------------------
PAGE P76 — DATA CONTRACTS: CANONICAL JSON SCHEMAS FOR PIPELINE STABILITY
-------------------------------------------------------------------------------
Intent
- Prevent the system from breaking as modules evolve by locking down core schemas.
- Enable safe refactors and third-party tooling integration.

Inputs
- Current pipeline outputs (manifests, ledgers, indices)

Outputs
- schemas/*.schema.json for:
  - authority_snapshot_index
  - evidence_atoms
  - record_spine
  - service_chain
  - po_state
  - quote_ledger
  - draft_trace
- schemas/SCHEMA_CHANGELOG.md

Automation
- Schema validation step in CI and local runs:
  - Every produced artifact validates against its schema.
- Versioning:
  - Semantic version for each schema, plus compatibility notes.

Verification
- Backward compatibility check for “minor” schema bumps:
  - Old artifacts still parse.
- Hard fail for breaking changes without explicit major bump.

-------------------------------------------------------------------------------
PAGE P77 — REPO LAYOUT: MONOREPO DISCIPLINE FOR A LITIGATION SYSTEM
-------------------------------------------------------------------------------
Intent
- Make the repo navigable and enforce separation between code, configs, and generated outputs.

Inputs
- None (design decision)

Outputs
- Standard folder layout (recommended):
  - apps/ (UI + CLI entry points)
  - pipelines/ (orchestrated flows)
  - modules/ (pure libraries)
  - schemas/ (jsonschema)
  - docs/ (runbooks)
  - examples/ (toy datasets, not real case data)
  - tools/ (dev scripts)
  - .github/ (copilot + actions)
- docs/REPO_LAYOUT.md

Automation
- CI checks:
  - forbid committing generated case artifacts into repo (use vault storage instead)
  - allow only examples/ synthetic fixtures.

Verification
- “No real data in repo” guard:
  - patterns for filenames/paths blocked (configurable).

-------------------------------------------------------------------------------
PAGE P78 — VAULT STORAGE: LOCAL-FIRST, MIRRORABLE, RECOVERABLE
-------------------------------------------------------------------------------
Intent
- Keep case data in an evidence vault outside the repo with deterministic paths, not in Git history.
- Support mirroring/sync without rewriting history.

Inputs
- Vault root (user-controlled)
- Intake sources (downloads, scans, exports)

Outputs
- Deterministic vault structure (example):
  - Vault/CASE/<case_id>/original/
  - Vault/CASE/<case_id>/derived/
  - Vault/CASE/<case_id>/runs/<run_id>/
  - Vault/COMMON/authority_snapshot/<snapshot_id>/
- Vault/VaultIndex.json

Automation
- “Ingest” creates:
  - immutable originals (copy-in)
  - derivative folder with extractor outputs
  - run folder with logs/manifests

Verification
- Vault integrity scan:
  - detect missing pointers, broken links, incomplete runs.

-------------------------------------------------------------------------------
PAGE P79 — ORCHESTRATION: ONE COMMAND PER STAGE, IDEMPOTENT BY DESIGN
-------------------------------------------------------------------------------
Intent
- Allow a user to run ingest, extract, index, graph, analyze, draft, exhibits, preflight
  - each step independently, resumably, and safely.

Inputs
- Case selection + vault roots + snapshot id

Outputs
- CLI surface (spec-level):
  - litigos ingest --case <id> --in <path> --vault <root>
  - litigos extract --case <id> --run <run_id>
  - litigos index --case <id> --run <run_id>
  - litigos graph --case <id> --run <run_id>
  - litigos analyze --case <id> --run <run_id>
  - litigos draft --case <id> --vehicle <vehicle_id>
  - litigos exhibits --case <id> --selection <json>
  - litigos preflight --case <id> --vehicle_instance <id>

Automation
- Stage manager:
  - emits run_id if absent
  - reads prior stage outputs if present
  - never duplicates work unless forced (cache-aware)

Verification
- Every stage outputs:
  - manifest, report, and “what changed” delta log.

-------------------------------------------------------------------------------
PAGE P80 — OBSERVABILITY: METRICS THAT MATTER (NOT PRETTY DASHBOARDS)
-------------------------------------------------------------------------------
Intent
- Provide measurable operational confidence and quickly locate failures.

Inputs
- All run logs + schemas

Outputs
- observability/run_metrics.jsonl
  - per run: docs processed, pages extracted, OCR failures, quote verify failures, schema failures, gate failures.
- observability/system_health.md
  - rolling summary

Automation
- Metrics extraction step at end of each run.
- Optional “alert file” written when gate fails with high severity.

Verification
- Metrics correctness checks:
  - counts match manifest file lists
  - no negative or impossible values.

-------------------------------------------------------------------------------
PAGE P81 — SECURITY MODEL: LEAST PRIVILEGE + NO-SECRETS + NON-DESTRUCTIVE DEFAULTS
-------------------------------------------------------------------------------
Intent
- Reduce risk of accidental deletion, privilege leaks, or data exposure.

Inputs
- Environment inventory (OS, storage, accounts)

Outputs
- security/SECURITY_MODEL.md
- Recommended “roles”:
  - Reader: can analyze but cannot write to originals
  - Builder: can create derivatives
  - Executor: can assemble FILE_READY packets
- “No secrets in repo” gate:
  - commit scanning patterns

Automation
- Pre-commit checks (optional):
  - secret scan
  - forbidden path scan (vault data)

Verification
- Documented incident workflow:
  - how to revoke, rotate, and quarantine.

-------------------------------------------------------------------------------
PAGE P82 — RELEASE ENGINEERING: VERSIONED BUNDLES, NOT CHAOS
-------------------------------------------------------------------------------
Intent
- Produce reproducible releases for your own use (and later productization) without drift.

Inputs
- Repo state + dependency locks

Outputs
- Release artifacts (spec):
  - dist/LitigationOS_<version>_win_x64.zip
  - dist/LitigationOS_<version>_termux.zip
  - dist/manifest.json
  - dist/CHANGELOG.md

Automation
- Build pipeline:
  - pin dependencies
  - run tests
  - build distributables
  - verify distributables contain required files
  - generate checksums (optional; only if enabled)

Verification
- Release smoke test:
  - run litigos --version
  - run minimal ingest/extract on sample fixtures.

-------------------------------------------------------------------------------
PAGE P83 — PRODUCTIZATION LAYER: FROM “MY CASES” TO “REUSABLE SYSTEM”
-------------------------------------------------------------------------------
Intent
- Separate case-specific content (vault) from product code (repo), enabling reuse.

Inputs
- Vault + multiple cases

Outputs
- “Case profile” concept:
  - case_profile/<case_id>.json includes court, judge, parties, local rules references, filing preferences.
- Template pack:
  - Generic vehicles and forms library (no case data).

Automation
- Case bootstrap wizard:
  - create case profile
  - initialize vault folders
  - ingest authority snapshot references

Verification
- Hard rule: product code runs without any single case being present.

-------------------------------------------------------------------------------
PAGE P84 — 30-DAY EXECUTION PLAN: WHAT I WOULD BUILD FIRST, IN ORDER
-------------------------------------------------------------------------------
Intent
- Provide a pragmatic build sequence that yields usable outputs early.

Inputs
- Your chosen “pilot case” and vault root

Outputs
- Day 1–3:
  - Vault ingest + extraction + evidence atoms + record spine skeleton
- Day 4–7:
  - Quote ledger + service chain + deadline engine (even if some data manual)
- Day 8–12:
  - Findings gap + contradictions + first “cross-exam pack” DRAFT output
- Day 13–18:
  - Vehicle map + PO templates + PCW/ADD/PCG gating
- Day 19–24:
  - Draft compiler + exhibit factory + preflight
- Day 25–30:
  - Appellate packaging + conduct track outputs + observability + release bundle

Automation
- Daily checkpoints:
  - “What can be filed today?” list (only if PCG PASS for some vehicle)
  - “Top blockers” list (input-dependent items)

Verification
- At end of day 30:
  - at least one complete DRAFT packet
  - at least one complete FILE_READY packet (only if the necessary inputs exist)

-------------------------------------------------------------------------------
PAGE P85 — INPUT DEPENDENCIES: THE ONLY THINGS THAT CAN BLOCK “TO THE CEILING”
-------------------------------------------------------------------------------
Intent
- Define the minimal set of real-world inputs that automation cannot conjure.

Blocking Input Classes (enumerated)
- File-stamped orders (or certified copies)
- Official transcripts (or audio if transcripts unavailable)
- ROA/docket export sufficient to reconcile dates
- Proofs of service / notices (or the absence thereof, documented)
- Local rules/administrative orders affecting procedure
- Your own factual declarations (if needed) signed under oath

Acquisition Plan Template (machine-readable)
- blockers/<case_id>/BLOCKERS.json items:
  - {blocker_id, category, description, why_needed, how_to_get, expected_time, status}
- Standardized “how to get” patterns:
  - clerk request, transcript order, FOIA request, subpoena (if authorized), discovery request, motion to compel (vehicle-mapped).

Verification
- The system is allowed to advance indefinitely in DISCOVERY/DRAFT.
- FILE_READY is permitted only when these dependencies are satisfied for the selected vehicle.

END OF APPEND-ONLY EXPANSION P61–P85
===============================================================================



===============================================================================
APPEND-ONLY EXPANSION • PAGES P86–P110 (v2026-01-18.4)
===============================================================================
Theme of this expansion:
- “Graph Brain Completion”: Neo4j ingestion that is resumable, idempotent, and audit-friendly.
- “Retrieval that never lies”: Context Packs that preserve pointers + quote discipline.
- “Automation without self-destruction”: scheduled harvest + task queue + safe defaults.
- “Court-case solver layer”: structured generation of question banks, hearing packs, and record-driven drafts.

-------------------------------------------------------------------------------
PAGE P86 — NEO4J CORE GRAPH: LOCKED SCHEMA + CONSTRAINTS/INDEXES
-------------------------------------------------------------------------------
Intent
- Establish the minimal, stable graph schema required to support:
  - Record Spine, Evidence Atoms, Quotes, Authority Propositions, Service Chain, Deadlines
  - Findings Gaps, Contradictions, Draft Blocks, Exhibits, Vehicles, PO State
- Make schema evolution explicit, versioned, and testable.

Inputs
- `schemas/*.schema.json` (P76)
- Domain primitives from earlier pages:
  - Case, Party, DocketEntry, Order, Hearing, Notice, ServiceEvent
  - EvidenceFile, EvidenceAtom, Derivative, Quote
  - AuthorityRef, Proposition
  - Vehicle, VehicleInstance, ProofObligation, POState
  - DraftDoc, DraftBlock, CitationLink
  - Exhibit, ExhibitPacket
  - FindingGap, ContradictionEdge
  - Deadline, Trigger, Task

Outputs
- `graph/schema/neo4j_schema_v1.cypher`
  - CREATE CONSTRAINT / INDEX statements
- `graph/schema/neo4j_labels_and_rels.md`
  - Machine-readable label/relationship catalog
- `graph/schema/neo4j_schema_version.json`
  - {schema_version, created_at, compatible_artifact_versions[]}

Automation
- Schema apply command (idempotent):
  - litigos graph schema-apply --db bolt://localhost:7687 --schema graph/schema/neo4j_schema_v1.cypher
- Pattern: use IF NOT EXISTS where supported; otherwise pre-check existence.

Verification
- Schema smoke tests:
  - Ensure unique constraints exist for stable IDs:
    - Case.case_id, EvidenceFile.file_id, EvidenceAtom.atom_id, Quote.quote_id, Proposition.prop_id, VehicleInstance.vehicle_instance_id
  - Ensure essential indexes exist:
    - Case.case_id
    - EvidenceAtom.case_id + atom_id (composite if desired)
    - DocketEntry.case_id + entry_id
  - “No duplicate node” test: import run must not create duplicates for unique IDs.

-------------------------------------------------------------------------------
PAGE P87 — GRAPH IDENTITY: STABLE IDs, NATURAL KEYS, AND COLLISION AVOIDANCE
-------------------------------------------------------------------------------
Intent
- Guarantee stable identifiers across runs so imports are merge-safe and repeatable.

Inputs
- Vault file_id scheme (P78)
- Evidence atom_id scheme (P67)
- Quote quote_id scheme (P64)
- Authority auth_ref_id + prop_id scheme (P61)
- Vehicle instance IDs (P62)

Outputs
- `graph/id_policy/ID_POLICY.md`
- `graph/id_policy/id_generation_rules.json`
  - rules for deterministic IDs

Automation
- Deterministic ID generation strategy (recommended):
  - Prefer: (case_id + local stable key) + normalization + short hash of the key string
  - Avoid: random UUIDs unless they are stored permanently the first time and never regenerated
- Collision monitor:
  - Detect if different objects yield same ID; emit `ID_COLLISION` blocker.

Verification
- “Round-trip ID” test:
  - Given the same inputs, IDs are identical across runs.
- “Cross-run merge” test:
  - Running the same import twice yields no net-new nodes (except run metadata).

-------------------------------------------------------------------------------
PAGE P88 — GRAPH IMPORT PIPELINE: CSV/JSONL STAGING + MERGE-ONLY WRITES
-------------------------------------------------------------------------------
Intent
- Import pipeline outputs into Neo4j without using destructive operations.
- Support resumable execution at each stage.

Inputs
- Staging exports from pipeline (examples):
  - record_spine/record_spine.json
  - evidence/evidence_atoms.jsonl
  - quotes/quote_ledger.jsonl
  - authority_snapshot/authority_propositions.jsonl
  - service_chain/service_chain.jsonl
  - deadlines/deadline_index.jsonl
  - drafts/*/block_trace.json
  - exhibits/*/EXHIBIT_MATRIX.csv
- Graph connection config

Outputs
- `graph/staging/<run_id>/nodes_*.csv` and `rels_*.csv` (or JSONL)
- `graph/import/IMPORT_PLAN.md`
  - explicit file order + constraints
- `graph/import/import_report_<run_id>.md`

Automation
- Import plan (recommended ordering):
  1) Case + Parties
  2) Docket Entries + Hearings + Orders + Notices
  3) EvidenceFile + Derivative + EvidenceAtom
  4) Quote nodes linked to EvidenceAtom + Order/Transcript sources
  5) AuthorityRef + Proposition nodes
  6) Vehicle + VehicleInstance + POState
  7) FindingsGap + Contradiction edges
  8) DraftDoc + DraftBlocks + CitationLink
  9) Exhibit + ExhibitPacket
  10) Deadline + Task
- “Merge-only” Cypher patterns:
  - MERGE on stable IDs, SET properties, MERGE relationships, never DELETE.

Verification
- Import idempotency:
  - import run repeated → same node counts for core entities
- Referential integrity:
  - every relationship endpoint exists; otherwise relationship load is deferred and logged as `MISSING_ENDPOINT`.

-------------------------------------------------------------------------------
PAGE P89 — GRAPH RUN LEDGER: EVERY IMPORT IS A FIRST-CLASS EVENT
-------------------------------------------------------------------------------
Intent
- Make every graph write traceable to a run_id and artifact set.

Inputs
- run_id, case_id, snapshot_id
- staging manifest and metrics

Outputs
- Graph nodes:
  - (:Run {run_id, started_at, finished_at, tool_version, git_sha, schema_version})
  - (:Artifact {artifact_id, path, kind, produced_at})
  - (:Run)-[:PRODUCED]->(:Artifact)
  - (:Run)-[:AFFECTED_CASE]->(:Case)
- File outputs:
  - graph/import/run_ledger_<run_id>.json

Automation
- On every run:
  - Create/merge Run node
  - Link produced artifacts and metrics
  - Link Run to affected Cases

Verification
- “Forensic trace” test:
  - From any node, you can traverse back to a Run or Artifact that produced/updated it.

-------------------------------------------------------------------------------
PAGE P90 — BLOOM DASHBOARDS: OPINIONATED VIEWS THAT MATCH LITIGATION TASKS
-------------------------------------------------------------------------------
Intent
- Provide operational graph views aligned to litigation tasks (not generic graph porn).

Inputs
- Neo4j DB with schema and data

Outputs
- `graph/bloom/perspectives/`
  - `RecordSpine.perspective.json`
  - `EvidenceAtlas.perspective.json`
  - `QuoteLedger.perspective.json`
  - `ServiceChain.perspective.json`
  - `Deadlines.perspective.json`
  - `FindingsGaps.perspective.json`
  - `Contradictions.perspective.json`
  - `DraftTrace.perspective.json`
- `graph/bloom/queries/`
  - curated Cypher queries with parameters

Automation
- Perspective generator:
  - ensures node captions and relationship directions are consistent
- “One-click queries”:
  - Case overview, next deadlines, missing transcript list, service defects, top contradictions.

Verification
- Query correctness:
  - Each query must return results on sample fixtures and not require manual edits.

-------------------------------------------------------------------------------
PAGE P91 — CONTEXT PACKS: RETRIEVAL THAT PRESERVES PROVENANCE
-------------------------------------------------------------------------------
Intent
- Build GraphRAG-style retrieval without hallucinations by packaging:
  - candidate nodes + their provenance pointers + quote statuses + authority refs.

Inputs
- Graph entities + text stores (authority, order OCR, transcripts)
- Query intent: “What do I need for X?” “Where is the contradiction?” “Draft motion for Y.”

Outputs
- `context_packs/<case_id>/<pack_id>.json`
  - {pack_id, query, created_at, case_id, items[], warnings[]}
  - item schema:
    - {item_id, kind, node_ref, source_refs[], quote_ids[], prop_ids[], confidence, status}
- `context_packs/<case_id>/<pack_id>_SUMMARY.md` (human-readable)
- `context_packs/<case_id>/<pack_id>_TRACE.json` (full trace)

Automation
- Context pack builder stages:
  1) Graph filter by case_id + node types
  2) Expand 1–2 hops from seed nodes
  3) Rank by relevance (vector + graph heuristics if available)
  4) Attach provenance and status fields
- Strict rule:
  - If something cannot be traced to a SourceRef, it is excluded or flagged as `UNSUPPORTED`.

Verification
- Context pack audit:
  - 100% of items have at least one source_ref or are explicitly `UNSUPPORTED` and excluded from FILE_READY usage.

-------------------------------------------------------------------------------
PAGE P92 — RETRIEVAL MODES: DISCOVERY vs DRAFT vs FILE_READY
-------------------------------------------------------------------------------
Intent
- Control how retrieval outputs may be used depending on stakes.

Inputs
- Context pack (P91)
- Quote ledger verification status (P64)
- Authority proposition verification status (P61)

Outputs
- `retrieval/policy.json`
  - defines allowed content per mode
- `retrieval/mode_reports/<pack_id>.md`

Automation
- Mode gates:
  - DISCOVERY:
    - allow candidate quotes, allow incomplete authority, allow unknown standards (with warnings)
  - DRAFT:
    - allow candidate quotes but must be tagged; require at least one authoritative basis per legal section
  - FILE_READY:
    - require VERIFIED quotes + VERIFIED propositions; prohibit unsupported items

Verification
- Compiler enforcement:
  - A document can be “rendered” in any mode, but only FILE_READY can be exported for filing.

-------------------------------------------------------------------------------
PAGE P93 — AUTOMATED “QUESTION BANK” GENERATOR (CROSS-EXAM / HEARING PACKS)
-------------------------------------------------------------------------------
Intent
- Convert contradictions and findings gaps into structured question banks and hearing packs.

Inputs
- contradiction_table.csv (P68)
- findings_gap_matrix.json (P69)
- quote ledger (verified where possible)
- witness roster (optional)

Outputs
- `hearing_packs/<case_id>/<hearing_id>/QUESTION_BANK.json`
  - per topic: goal, leading questions, follow-ups, expected exhibits, citations
- `hearing_packs/<case_id>/<hearing_id>/HEARING_PACK.md`
  - printable outline
- `hearing_packs/<case_id>/<hearing_id>/EXHIBIT_SHORTLIST.json`

Automation
- Question templates:
  - Confirm/deny questions tied to a single citation
  - Follow-ups: “If no, then…” tied to next citation
  - “Impeachment hook” questions only where contradictions are evidence-backed
- Keep tone neutral, fact-driven.

Verification
- Every question must map to at least one evidence reference or be marked as “investigate” (DRAFT only).
- FILE_READY hearing pack requires all citations resolved.

-------------------------------------------------------------------------------
PAGE P94 — ORDER-TO-OBLIGATION: AUTOMATICALLY DERIVE “WHAT YOU MUST DO NEXT”
-------------------------------------------------------------------------------
Intent
- Turn orders and notices into explicit tasks, deadlines, and proof obligations.

Inputs
- Orders + notices (P65)
- Authority snapshot (for deadlines where possible)
- Case profile (P83)

Outputs
- `tasks/<case_id>/TASKS.jsonl`
  - {task_id, derived_from_doc, action, due_date, dependencies, status}
- `deadlines/<case_id>/deadline_index.jsonl`
- `obligations/<case_id>/order_obligations.json`

Automation
- NLP + rule-based extraction (flag-only, never “final” without review):
  - detect “shall/must/ordered” sentences
  - detect due dates and hearing dates
  - attach document pointers and set as DRAFT tasks

Verification
- Task audit:
  - human review required to mark tasks “confirmed” for FILE_READY planning.

-------------------------------------------------------------------------------
PAGE P95 — “DENIAL NORMALIZER”: TRACK DENIALS, SILENCE, AND PROCEDURAL ESCAPES
-------------------------------------------------------------------------------
Intent
- Build a structured record of denials (explicit and implicit) and the procedural options they unlock.

Inputs
- Motions filed + outcomes + orders
- Docket entries
- Hearing logs (P73)

Outputs
- `denials/<case_id>/DENIAL_DB.jsonl`
  - {denial_id, motion_id, denied_at, form_of_denial, stated_reasons, record_refs}
- `denials/<case_id>/DENIAL_CONVERSION_MAP.json`
  - mapping: denial type → procedural response candidates (vehicle IDs)

Automation
- Normalize denial types:
  - denied with prejudice, denied without prejudice, moot, no ruling, bench denial, written denial, “silence beyond X days” (if authority known)
- Generate response candidates (DRAFT):
  - motion for reconsideration, motion to correct record, appeal, extraordinary relief, etc.
  - Always “candidate” until matched to authority + local rules.

Verification
- No procedural assertion is FILE_READY unless authority proposition exists and is VERIFIED.

-------------------------------------------------------------------------------
PAGE P96 — “RECORD CORRECTION” PIPELINE: DISCREPANCY → MOTION CANDIDATE
-------------------------------------------------------------------------------
Intent
- When transcript/order conflicts with what occurred, create a record-correction candidate path.

Inputs
- Hearing log (P73)
- Transcript (if available)
- Order text
- Quote verification results

Outputs
- `record_corrections/<case_id>/DISCREPANCIES.json`
- `record_corrections/<case_id>/CORRECTION_VEHICLE_CANDIDATES.json`
- `record_corrections/<case_id>/CORRECTION_DRAFT.md` (DRAFT only)

Automation
- Discrepancy types:
  - missing transcript, incorrect party name/date, misstated ruling, missing exhibits admitted, etc.
- For each discrepancy:
  - cite transcript lines (if available) + hearing log time markers

Verification
- FILE_READY requires:
  - verified transcript pointers or certified record support.

-------------------------------------------------------------------------------
PAGE P97 — “FACT CLAIMS” ENGINE: FACTS AS ATOMS, NOT AS RHETORIC
-------------------------------------------------------------------------------
Intent
- Keep fact assertions precise, minimal, and traceable.

Inputs
- Evidence atoms, quote ledger, record spine

Outputs
- `claims/<case_id>/FACT_CLAIMS.jsonl`
  - {claim_id, claim_text, evidence_refs[], time_scope, parties, status}
- `claims/<case_id>/FACT_CLAIMS_REPORT.md`

Automation
- Claim generation rules:
  - One claim per sentence.
  - Remove adjectives and conclusions.
  - Attach at least one evidence reference or mark as “needs support.”

Verification
- FILE_READY compiler will only use claims with evidence_refs present and verified where required.

-------------------------------------------------------------------------------
PAGE P98 — “LEGAL PROPS” ENGINE: PROPOSITIONS AS COMPILABLE UNITS
-------------------------------------------------------------------------------
Intent
- Make legal standards executable by linking them to:
  - Authority propositions, Vehicle elements, Findings gap slots, and PO templates.

Inputs
- authority_propositions.jsonl (P61)
- vehicle catalog + po templates (P62)
- findings gap templates (P69)

Outputs
- `law/LEGAL_PROP_LINKS.jsonl`
  - {link_id, prop_id, vehicle_id, element_slot, po_template_id, notes}
- `law/LEGAL_STANDARDS_MATRIX.csv`

Automation
- Link discovery (semi-automatic):
  - initial tag-based matching (e.g., “service”, “notice”, “custody factor”, “contempt”)
  - human review to confirm “controls vs informs”

Verification
- FILE_READY requires:
  - each legal section references VERIFIED propositions, not “inferred” law.

-------------------------------------------------------------------------------
PAGE P99 — “MOTION LIBRARY”: REUSABLE BLOCKS, NOT COPY-PASTE DOCUMENTS
-------------------------------------------------------------------------------
Intent
- Build a library of reusable motion sections that compile into a case-specific document.

Inputs
- Draft compiler block types (P70)
- Vehicle definitions (P62)

Outputs
- `motion_library/blocks/*.json`
  - blocks contain: label, purpose, inputs required, output text template, citation requirements
- `motion_library/library_index.json`

Automation
- Block templates are parameterized:
  - references: party names, dates, docket entries, exhibits
- Blocks may not emit FILE_READY text unless required inputs are present.

Verification
- Block unit tests:
  - missing inputs produce explicit “blocked” status and never silently omit.

-------------------------------------------------------------------------------
PAGE P100 — “EXHIBIT SELECTION” ASSISTANT: FROM CLAIMS → MINIMUM EXHIBIT SET
-------------------------------------------------------------------------------
Intent
- Reduce overwhelm by selecting the smallest set of exhibits that supports required claims/POs.

Inputs
- PO state (P63)
- Fact claims (P97)
- Evidence atoms (P67)

Outputs
- `exhibits/<case_id>/EXHIBIT_SELECTION.json`
  - {selection_id, goals[], chosen_atoms[], excluded_atoms[], rationale}
- `exhibits/<case_id>/EXHIBIT_SELECTION_REPORT.md`

Automation
- Greedy cover algorithm (deterministic):
  - choose atoms that cover the most unsatisfied POs/claims first
  - prefer verified quotes and primary sources
- Exclusion rationale:
  - redundancy, low relevance, potential prejudice/confusion (not legal advice; just risk note).

Verification
- Coverage report:
  - list each PO/claim and which exhibit supports it; unresolved items flagged.

-------------------------------------------------------------------------------
PAGE P101 — “FOIA / RECORD REQUEST” TRACK: REQUESTS AS OBJECTS WITH DEADLINES
-------------------------------------------------------------------------------
Intent
- Track public record requests and responses as evidence and deadline objects.

Inputs
- Request letters, emails, portal confirmations
- Response documents

Outputs
- `record_requests/<case_id>/REQUESTS.jsonl`
  - {request_id, target_agency, sent_at, scope, status, response_due, response_refs[]}
- `record_requests/<case_id>/REQUEST_PACKET/` (DRAFT letter templates + logs)

Automation
- Deadline computation:
  - Only if authority proposition exists; otherwise store as “unknown due date” and request authority capture.
- Attach responses to evidence atoms automatically.

Verification
- Every request has proof of sending reference or is marked “draft”.

-------------------------------------------------------------------------------
PAGE P102 — “DISCOVERY” TRACK: REQUESTS, RESPONSES, DEFICIENCIES (IF APPLICABLE)
-------------------------------------------------------------------------------
Intent
- Model discovery as structured exchanges with provable deficiencies.

Inputs
- Discovery requests, responses, objections
- Service proofs

Outputs
- `discovery/<case_id>/DISCOVERY_EXCHANGES.json`
- `discovery/<case_id>/DEFICIENCY_LOG.jsonl`
- `discovery/<case_id>/MOTION_CANDIDATES.json` (DRAFT)

Automation
- Deficiency detection (flag-only):
  - non-response, incomplete response, privilege assertions, etc.
- Suggest procedural candidates only as DRAFT until authority is linked.

Verification
- No FILE_READY discovery motions without verified authority and proof obligations satisfied.

-------------------------------------------------------------------------------
PAGE P103 — “SETTLEMENT / NEGOTIATION” SUPPORT: OFFERS AS VERSIONED OBJECTS
-------------------------------------------------------------------------------
Intent
- Track offers and negotiation states without contaminating court filings improperly.

Inputs
- Offer drafts, communications, terms

Outputs
- `settlement/<case_id>/OFFERS.jsonl`
  - {offer_id, sent_at, terms, status, notes, attachments}
- `settlement/<case_id>/NEGOTIATION_STATE.json`

Automation
- Redaction discipline:
  - keep settlement artifacts separate from court-facing packets.
- Optionally generate internal “BATNA” notes (non-court).

Verification
- Guardrails:
  - settlement artifacts never auto-included in exhibit selection unless explicitly requested and procedurally appropriate.

-------------------------------------------------------------------------------
PAGE P104 — CONFIGURATION SYSTEM: CASE PROFILES + ENV PROFILES + FEATURE FLAGS
-------------------------------------------------------------------------------
Intent
- Make the system configurable without code edits.

Inputs
- Case profile (P83)
- Environment profile (paths, db endpoints)

Outputs
- `config/cases/<case_id>.json`
- `config/environments/<env>.json`
- `config/features.json`
  - feature flags: OCR engine selection, quote verification methods, graph import strategy, UI toggles

Automation
- Config loader:
  - validates JSON against schemas
  - rejects unknown keys unless in “experimental” section

Verification
- “Config drift” test:
  - run prints effective config with redaction of secrets.

-------------------------------------------------------------------------------
PAGE P105 — SCHEDULED HARVEST: SAFE, REPEATABLE, AND AUDITABLE
-------------------------------------------------------------------------------
Intent
- Run periodic ingest/extract/index tasks without corrupting vault or graph state.

Inputs
- Monitored intake folders (e.g., downloads, Drive mount)
- Schedule (e.g., 4x/day)

Outputs
- `scheduler/SCHEDULED_RUNS.jsonl`
- `scheduler/last_success.json`
- Run folders with standard outputs

Automation
- Scheduler behavior:
  - Detect new files (by filename + size + modified time; optional hash)
  - Stage to vault ingest
  - Run extract/index
  - Optionally run graph import (only if configured)
- Safe defaults:
  - read-only scans of input sources
  - no deletion, no renaming of originals

Verification
- “Dry-run mode” required for first deployment.
- “Quarantine” if extractor fails on a file repeatedly:
  - move copy to quarantine area (never touch original).

-------------------------------------------------------------------------------
PAGE P106 — TASK QUEUE + WORKERS: AVOID “ONE BIG SCRIPT” FAILURE MODES
-------------------------------------------------------------------------------
Intent
- Break work into resumable tasks (ingest, extract, verify quotes, import graph, compile draft).

Inputs
- Task definitions derived from pipeline stages

Outputs
- `queue/TASK_QUEUE.jsonl`
- `queue/WORKER_LOGS/worker_<id>.log`
- `queue/TASK_RESULTS.jsonl`

Automation
- Worker pattern:
  - pulls next task
  - locks task
  - executes with retries
  - emits result + pointers
- Task idempotency:
  - tasks must be safe to retry; outputs are either identical or versioned by run_id.

Verification
- Dead-letter queue for repeated failures:
  - tasks moved to `FAILED_PERMANENT` with explicit remediation notes.

-------------------------------------------------------------------------------
PAGE P107 — UI LAYER: “CONTROL TOWER” THAT OPERATES THE PIPELINE
-------------------------------------------------------------------------------
Intent
- Provide a single UI (desktop + optional mobile view) to:
  - select case, run stages, inspect outputs, view graph, generate packets

Inputs
- Config profiles
- Vault state + graph state
- Run metrics

Outputs
- UI spec files:
  - `ui/CONTROL_TOWER_SPEC.md`
  - `ui/screens/*.md` (screen contracts)
- Optional build targets:
  - desktop app (PySide/Electron/other)
  - web dashboard (local-only)

Automation
- UI actions map to CLI commands:
  - UI never mutates vault directly; it calls pipeline APIs/commands.
- “Output viewer”:
  - open draft docs, view exhibit packets, show service chain and deadline calendar.

Verification
- UI must support:
  - “simulate / dry-run”
  - “show me what will change”
  - “open run report”

-------------------------------------------------------------------------------
PAGE P108 — INTEGRATION TEST HARNESS: FIXTURES WITHOUT REAL CASE DATA
-------------------------------------------------------------------------------
Intent
- Ensure system reliability using synthetic fixtures so development never relies on sensitive data.

Inputs
- Fixture generator inputs (fake docket, fake PDFs, fake transcripts)

Outputs
- `examples/fixtures/`
  - small synthetic PDFs, docket CSV, transcript text
- `tests/integration/test_end_to_end.py` (or equivalent)
- `tests/fixtures_manifest.json`

Automation
- Fixture generator produces:
  - at least one case with:
    - 2 docket entries, 1 order, 1 hearing notice, 1 service proof, 1 transcript excerpt
- CI runs:
  - ingest → extract → index → graph import (optional) → draft in DISCOVERY mode

Verification
- Assertions:
  - evidence atoms exist
  - quote ledger contains items
  - record spine created
  - schema validation passes
  - no destructive operations performed

-------------------------------------------------------------------------------
PAGE P109 — REPO GOVERNANCE: PR TEMPLATES, ISSUE FORMS, CODEOWNERS, RELEASE TAGS
-------------------------------------------------------------------------------
Intent
- Make collaboration (including with agents) predictable and reviewable.

Inputs
- None

Outputs
- `.github/pull_request_template.md`
  - objective, test plan, risk, rollback, artifacts produced, run_id
- `.github/ISSUE_TEMPLATE/`
  - pipeline bug report, feature request, case onboarding request
- `CODEOWNERS` (optional)
- `RELEASE.md` + semantic tag policy

Automation
- CI checks enforce:
  - PR template sections present (lightweight check)
  - schema validation on produced sample artifacts

Verification
- “Review readiness”:
  - PR must include how to run and what changed.

-------------------------------------------------------------------------------
PAGE P110 — “PROBLEM SOLVER” LOOP: DAILY OPERATIONS THAT CONVERT CHAOS → ACTION
-------------------------------------------------------------------------------
Intent
- Provide a daily operational cycle that keeps litigation moving:
  - identify immediate threats (deadlines/hearings)
  - close gaps (missing record items)
  - generate next best procedural move (vehicle candidates)
  - produce court-safe packets when ready

Inputs
- Deadlines index
- Task queue
- Record spine gaps
- PO state and assurance scores

Outputs
- `daily_ops/<case_id>/DAILY_BRIEF_<date>.md`
  - Today’s deadlines, top blockers, recommended actions (DRAFT), tasks to run
- `daily_ops/<case_id>/NEXT_BEST_ACTION.json`
  - {candidate_vehicle_ids[], why, blockers, estimated readiness}
- Updated queue tasks + run_id for any executed jobs

Automation
- Daily run steps:
  1) Refresh intake scan (read-only)
  2) Update record spine and deadlines
  3) Recompute PO states and assurance
  4) Emit “Top 10 blockers” with acquisition plan
  5) If any vehicle reaches PCG PASS, produce FILE_READY packet staging bundle

Verification
- “No surprises” policy:
  - Any action that changes artifacts produces a manifest + report.
  - FILE_READY artifacts always include trace + preflight report.

END OF APPEND-ONLY EXPANSION P86–P110
===============================================================================


===============================================================================
APPEND-ONLY EXPANSION P111–P140 (GitHub + Copilot Coding Agent + Repo Automation)
Build date (local): 2026-01-18 (America/Detroit)
===============================================================================

-------------------------------------------------------------------------------
PAGE P111 — “ONBOARD THIS REPO” (ONE-SHOT COPILOT CODING AGENT REPO HARDENING)
-------------------------------------------------------------------------------
Intent
- Make this repository maximally “agent-ready” for GitHub Copilot coding agent:
  - deterministic environment setup
  - unambiguous build/test commands
  - repo-local instructions and path-scoped instructions
  - custom agents for specialized work streams
  - issue/PR templates engineered for high-quality agent output

Inputs
- Repository default branch (main/master).
- Primary languages (e.g., Python + JS/Electron + PowerShell).
- Target runtime(s): Windows 10/11 local + Ubuntu x64 GitHub Actions runner for Copilot coding agent execution.
- LitigationOS invariants (Truth-Lock, Append-Only, PCW/ADD→PCG) to embed as “non-negotiables.”

Outputs (Repo Files)
- `.github/copilot-instructions.md`
- `.github/instructions/*.instructions.md` (path-scoped)
- `.github/agents/*.agent.md` (custom agents)
- `.github/workflows/copilot-setup-steps.yml` (deterministic agent setup)
- `.github/ISSUE_TEMPLATE/*`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `AGENTS.md` (human-readable agent doctrine + local dev contract)
- `docs/DEV_QUICKSTART.md` (single-source “how to run”)
- `docs/ARCHITECTURE.md` (system map; component contracts)
- `docs/SECURITY.md` (secrets, environments, firewall posture, supply chain)

Steps (Manual, 15–30 minutes)
1) Add the files above (templates in pages P112–P123).
2) Merge to default branch (required for Copilot setup workflow discovery).
3) Enable Copilot coding agent on the repo (org/repo settings).
4) Create a first “seed issue” with narrow acceptance criteria (P116).
5) Run Copilot coding agent to open a PR; review; iterate using PR comments.

Automation (Preferred)
- Use Copilot coding agent itself to implement the onboarding as its first PR:
  - “Create the repo instruction files and workflows exactly per Playbook P112–P123.”
  - “Also add docs/DEV_QUICKSTART.md and AGENTS.md as specified.”

Verification
- Acceptance checks:
  - Copilot coding agent can run tests/lint without trial-and-error dependency hunts.
  - Agent-created PRs conform to repo contract (no renames, append-only for evidence/docs).
  - PRs include: summary, risk notes, test evidence, and rollback plan.

-------------------------------------------------------------------------------
PAGE P112 — `.github/copilot-instructions.md` (REPO-LEVEL AGENT CONTRACT)
-------------------------------------------------------------------------------
Intent
- Provide Copilot coding agent a single, authoritative contract for how to work in this repo:
  - how to run, test, build, and package
  - how to structure outputs
  - what “done” means
  - what NOT to do

File: `.github/copilot-instructions.md`
Template (adapt values, keep structure stable):

```md
# Copilot Repository Instructions — LitigationOS

## Prime Directive
- Produce changes that are *deterministic, testable, and reviewable*.
- Prefer small PRs with clear acceptance criteria.
- Do not rename or restructure core top-level folders unless the issue explicitly requests it.
- Evidence and outputs are append-only by default.

## Build / Test / Lint (single source of truth)
- Python:
  - Install: `python -m pip install -r requirements.txt`
  - Unit tests: `python -m pytest -q`
  - Lint: `python -m ruff check .`
  - Format: `python -m ruff format .`
- Node/Electron (if present):
  - Install: `npm ci`
  - Test: `npm test`
  - Build: `npm run build`
- PowerShell (if present):
  - Lint: `pwsh -NoProfile -Command "Invoke-ScriptAnalyzer -Path . -Recurse"`

## Repo Invariants (non-negotiable)
- Truth-Lock: do not invent facts in generated legal text; require citations/pinpoints when producing filing-ready outputs.
- Append-only: avoid destructive edits of evidence artifacts; use versioned additions.
- PCW/ADD→PCG: when implementing filing/service automation, always expose proof obligations and a final execution gate.
- No placeholders/TODOs in user-facing artifacts (docs, forms, motions).

## PR Expectations
- Each PR must include:
  - What changed + why (3–8 bullets)
  - How to run tests (exact commands)
  - Risk notes + rollback plan
  - Any schema changes with migration notes
- Prefer adding or updating documentation in `docs/` for any non-trivial changes.

## Safety / Secrets
- Never print secrets in logs.
- Never commit credentials.
- Use `.env.example` for required variables; real values come from GitHub Environments.

## When unsure
- Ask for clarification in the issue/PR thread; do not guess.
```

Verification
- The instructions mention exact commands that *exist* in the repo.
- If commands differ, update template to match reality (don’t drift).

-------------------------------------------------------------------------------
PAGE P113 — PATH-SCOPED INSTRUCTIONS (`.github/instructions/*.instructions.md`)
-------------------------------------------------------------------------------
Intent
- Provide precision instructions only for relevant subtrees.
- Reduce “prompt soup” by scoping guidance to file globs.

Pattern
- Place files under: `.github/instructions/`
- Name: `<topic>.instructions.md`
- Use YAML frontmatter to scope.

Example 1: Python core (scoped)
File: `.github/instructions/python-core.instructions.md`

```md
---
applyTo: "**/*.py"
---
# Python Core Instructions

- Prefer standard library; add dependencies only when justified.
- Every new function: type hints + docstring + unit tests.
- Logging: use `logging` with module-level logger; no print() in production paths.
- Errors: raise precise exceptions; include actionable messages.
- Determinism: avoid global randomness; seed when needed.

## IO + Evidence Discipline
- All file writes go to `out/` unless explicitly required elsewhere.
- Never overwrite evidence inputs; write derived artifacts to versioned outputs.
```

Example 2: Neo4j/Cypher (scoped)
File: `.github/instructions/neo4j.instructions.md`

```md
---
applyTo: "**/*.cypher"
---
# Neo4j / Cypher Instructions

- Prefer parameterized Cypher.
- Enforce constraints + indexes in `schema/neo4j_constraints.cypher`.
- Migration scripts must be idempotent.
- Avoid APOC unless required; document APOC dependencies clearly.

## Graph Semantics
- Node IDs must be stable and reproducible.
- Relationships must include provenance pointers (file/page/line or shard IDs).
```

Example 3: GitHub Actions (scoped)
File: `.github/instructions/github-actions.instructions.md`

```md
---
applyTo: ".github/workflows/**/*.yml"
---
# GitHub Actions Instructions

- Keep workflows minimal and cache dependencies.
- Pin action versions to major versions at least.
- Use least-privilege permissions.
- Include a `workflow_dispatch` trigger for manual runs.
```

Verification
- Confirm Copilot respects these instructions by assigning tasks that touch each subtree and reviewing the resulting PR.

-------------------------------------------------------------------------------
PAGE P114 — `AGENTS.md` (HUMAN + AGENT OPERATOR DOCTRINE)
-------------------------------------------------------------------------------
Intent
- Establish a single, human-readable “doctrine” file for how agents should behave,
  so maintainers can review and enforce consistent behavior.

File: `AGENTS.md`
Minimum required sections
- “How we work” (PR style, test requirements)
- “Append-only evidence rule”
- “PCW/ADD/PCG concepts used in this repo”
- “Where to put outputs” (out/, dist/, artifacts/)
- “Support boundaries” (what the system will not automate without explicit confirmation)

Suggested structure
- 1 page, tight bullets; link out to `docs/ARCHITECTURE.md` and `docs/DEV_QUICKSTART.md`.

-------------------------------------------------------------------------------
PAGE P115 — CUSTOM AGENTS (`.github/agents/*.agent.md`) FOR SPECIALIZATION
-------------------------------------------------------------------------------
Intent
- Create role-focused agents to reduce hallucination and increase task quality.
- Agents are Markdown files with YAML frontmatter and a prompt body.

Location + naming
- Directory: `.github/agents/`
- File suffix: `.agent.md`
- Agent “name” must be unique.

Core agents recommended for LitigationOS
- `harvest-engineer` — document ingestion, manifests, cyclepacks
- `graph-engineer` — Neo4j schema, importers, Bloom outputs
- `forms-engineer` — forms-first mapping, packet assembly, SCAO overlays
- `qa-specialist` — tests, fixtures, determinism, CI hardening
- `security-specialist` — secrets, dependency hygiene, threat model
- `release-engineer` — packaging, versioning, installers, checksums

-------------------------------------------------------------------------------
PAGE P116 — AGENT TASK SCOPING (ISSUE WRITING THAT PRODUCES HIGH-QUALITY PRS)
-------------------------------------------------------------------------------
Intent
- Agent output quality is proportional to issue quality.
- Every agent issue must be “well-scoped” with explicit acceptance criteria.

Issue template contract (minimal)
- Problem statement (2–6 lines)
- Constraints (non-negotiables)
- Acceptance criteria (checkbox list)
- Test plan (exact commands)
- Out-of-scope list

Rule of thumb
- If acceptance criteria > 12 bullets, split the issue.

Example (good)
- “Add `.github/copilot-instructions.md` and `.github/workflows/copilot-setup-steps.yml` as per Playbook P112 and P121. Verify workflow runs and exits 0.”

Example (bad)
- “Finish the whole LitigationOS.”

-------------------------------------------------------------------------------
PAGE P117 — PR ITERATION LOOP (COMMENT-DRIVEN, LOW-FRICTION)
-------------------------------------------------------------------------------
Intent
- Use PR comments to steer without restarting.
- Treat the PR thread as the authoritative “control plane.”

Loop
1) Agent opens PR.
2) Reviewer leaves one comment with:
   - prioritized fixes (top 3–7)
   - “do not change” warnings (paths/behavior)
   - required test output
3) Agent updates PR.
4) Reviewer merges when acceptance criteria is satisfied.

Recommended comment format (copy/paste)
- “Update PR to address:”
  1) …
  2) …
  3) …
- “Do NOT change:”
  - …
- “Run tests:”
  - …
- “Definition of done:”
  - …

-------------------------------------------------------------------------------
PAGE P118 — CUSTOM AGENT PROFILE: `harvest-engineer.agent.md`
-------------------------------------------------------------------------------
File: `.github/agents/harvest-engineer.agent.md`

```md
---
name: harvest-engineer
description: Builds deterministic intake/harvest pipelines, manifests, and CyclePacks; never mutates evidence inputs.
tools: ["read","edit","search","execute"]
---

You are the Harvest Engineer for LitigationOS.

## Mission
- Implement robust, deterministic harvesting: unzip → index → shard → manifest → cyclepack.
- Outputs must be append-only and verifiable.

## Non-negotiables
- Never overwrite or delete evidence inputs.
- All outputs go under `out/` (or `artifacts/` if repo standard says so).
- Every run produces:
  - `manifest.json` + `manifest.csv`
  - `run.log`
  - `cyclepack.zip` (or folder if zip is deferred)
- Include a “dry-run” mode for any potentially destructive operation.

## Implementation standards
- Python preferred; use argparse, logging, exit codes.
- Provide tests for critical path functions (sharding, manifesting).
- If external tools are required (tika, mupdf, etc.), document them and add install steps.

## Deliverables in PR
- Code + tests + minimal docs update in `docs/DEV_QUICKSTART.md`.
- A sample output folder in `out/sample/` generated by tests or fixtures.
```

Verification
- Agent stays inside its scope and produces deterministic outputs.

-------------------------------------------------------------------------------
PAGE P119 — CUSTOM AGENT PROFILE: `graph-engineer.agent.md`
-------------------------------------------------------------------------------
File: `.github/agents/graph-engineer.agent.md`

```md
---
name: graph-engineer
description: Neo4j schema + import pipelines + Bloom exports; enforces provenance and stable IDs.
tools: ["read","edit","search","execute"]
---

You are the Graph Engineer for LitigationOS.

## Mission
- Define/maintain Neo4j schema (constraints, indexes, canonical labels).
- Build importers for EvidenceAtoms, Quotes, Orders, ServiceChain, VehicleMap, PO_DB.
- Provide repeatable “one command” import runbook for local + CI.

## Non-negotiables
- Stable node IDs (hash or deterministic key) — no random UUIDs unless wrapped by stable mapping.
- Every relationship includes provenance pointers (file/shard/page/line).
- Provide an idempotent schema migration script.
- Provide a smoke-test Cypher query pack for validation.

## Deliverables
- `schema/` with constraints + indexes
- `import/` with loaders
- `docs/GRAPH_RUNBOOK.md`
- `tests/` smoke imports (using tiny fixtures)
```

-------------------------------------------------------------------------------
PAGE P120 — CUSTOM AGENT PROFILE: `forms-engineer.agent.md`
-------------------------------------------------------------------------------
File: `.github/agents/forms-engineer.agent.md`

```md
---
name: forms-engineer
description: Forms-first vehicle mapping and packet assembly; produces court-ready bundles with traceability.
tools: ["read","edit","search","execute"]
---

You are the Forms Engineer for LitigationOS.

## Mission
- Implement “Forms-First”: relief → vehicle/form → rule/standard → elements → proof obligations → exhibits.
- Generate packet outputs (draft-level) with a complete manifest and cross-references.

## Non-negotiables
- Do not output filing-ready legal text with invented facts.
- Every factual assertion must point to a source reference in the evidence ledger.
- Every packet includes a validation report enumerating missing POs and acquisition plan.

## Deliverables
- `vehicles/` registry (YAML/JSON)
- packet compiler module + tests
- `docs/VEHICLEMAP.md`
```

-------------------------------------------------------------------------------
PAGE P121 — `copilot-setup-steps.yml` (DETERMINISTIC AGENT ENVIRONMENT)
-------------------------------------------------------------------------------
Intent
- Preinstall dependencies for Copilot coding agent to avoid unreliable trial-and-error.
- Required location: `.github/workflows/copilot-setup-steps.yml` on default branch.
- Job name must be exactly: `copilot-setup-steps`.

Recommended template (Python-first + optional Node)
File: `.github/workflows/copilot-setup-steps.yml`

```yml
name: "Copilot Setup Steps"
on:
  workflow_dispatch:
  push:
    paths:
      - .github/workflows/copilot-setup-steps.yml
  pull_request:
    paths:
      - .github/workflows/copilot-setup-steps.yml

jobs:
  copilot-setup-steps:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - name: Checkout
        uses: actions/checkout@v5

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install Python deps
        run: |
          python -m pip install --upgrade pip
          if [ -f requirements.txt ]; then python -m pip install -r requirements.txt; fi
          if [ -f requirements-dev.txt ]; then python -m pip install -r requirements-dev.txt; fi

      - name: Set up Node (optional)
        if: ${{ hashFiles('package-lock.json') != '' }}
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"

      - name: Install Node deps (optional)
        if: ${{ hashFiles('package-lock.json') != '' }}
        run: npm ci
```

Notes
- Copilot coding agent currently runs on Ubuntu x64 runners; keep your setup compatible.
- If you use Git LFS, set `lfs: true` in checkout steps.

Verification
- Manually run this workflow from the Actions tab.
- Ensure it exits 0 consistently.

-------------------------------------------------------------------------------
PAGE P122 — ISSUE + PR TEMPLATES (AGENT-GRADE ACCEPTANCE CRITERIA)
-------------------------------------------------------------------------------
Files
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/ISSUE_TEMPLATE/agent_task.yml`
- `.github/ISSUE_TEMPLATE/bug.yml`
- `.github/ISSUE_TEMPLATE/feature.yml`

PR template (minimal)
```md
## Summary
-

## Why
-

## How to test
- [ ] `python -m pytest -q`

## Risk / Rollback
- Risk:
- Rollback:

## Notes
-
```

Agent task issue template (YAML example)
```yml
name: Agent Task
description: A narrowly scoped task for Copilot coding agent
title: "[AGENT] "
labels: ["agent-task"]
body:
  - type: textarea
    id: problem
    attributes:
      label: Problem statement
      description: What is wrong / missing?
    validations:
      required: true
  - type: textarea
    id: constraints
    attributes:
      label: Constraints (non-negotiable)
      value: |
        - Do not rename core folders.
        - Append-only for evidence artifacts.
        - Add tests for critical logic.
    validations:
      required: true
  - type: textarea
    id: acceptance
    attributes:
      label: Acceptance criteria (checkboxes)
      value: |
        - [ ] `lit vault verify` exits 0 and writes `outputs/*/vault_verify.json`.
        - [ ] `lit graph import` is idempotent: second run changes counts by 0 (except run ledger nodes).
        - [ ] `lit packet build --mode FILE_READY` fails closed if any required PO is not SATISFIED.
    validations:
      required: true
  - type: textarea
    id: testplan
    attributes:
      label: Test plan (exact commands)
      value: |
        - `python -m pytest -q`
        - `python -m ruff check .`
        - `python -m mypy src --ignore-missing-imports`
    validations:
      required: true
```

-------------------------------------------------------------------------------
PAGE P123 — “IN-CHAT AGENT PROMPT” TO ONBOARD THE REPO (COPY/PASTE)
-------------------------------------------------------------------------------
Intent
- A single prompt you can paste into Copilot Agents (GitHub.com) to make it create the onboarding PR.

Prompt (copy/paste)
```text
You are operating as a repo onboarding specialist for GitHub Copilot coding agent.
Create a PR that onboards this repository following the LitigationOS Grandmaster Playbook P111–P122.

Requirements:
1) Add the following files exactly (create if missing):
   - .github/copilot-instructions.md
   - .github/instructions/python-core.instructions.md
   - .github/instructions/neo4j.instructions.md
   - .github/instructions/github-actions.instructions.md
   - .github/agents/harvest-engineer.agent.md
   - .github/agents/graph-engineer.agent.md
   - .github/agents/forms-engineer.agent.md
   - .github/workflows/copilot-setup-steps.yml
   - .github/PULL_REQUEST_TEMPLATE.md
   - .github/ISSUE_TEMPLATE/agent_task.yml
   - AGENTS.md
   - docs/DEV_QUICKSTART.md
2) Use least-privilege permissions in workflows.
3) Ensure the setup workflow runs and exits 0.
4) Do not rename existing folders or remove content.
5) Update docs/DEV_QUICKSTART.md with the exact build/test commands that exist in this repo.

Acceptance criteria:
- All files above exist on the PR branch.
- The setup workflow is valid YAML and uses the required job name `copilot-setup-steps`.
- DEV_QUICKSTART contains verified commands and expected outputs.
```

-------------------------------------------------------------------------------
PAGE P124 — REPO INDEXING + CONTENT EXCLUSION (REDUCE CONTEXT NOISE)
-------------------------------------------------------------------------------
Intent
- Prevent the agent from reading giant binary artifacts or irrelevant folders.
- Reduce hallucination by keeping the agent’s context grounded in source and docs.

Approach
- Keep heavy evidence ZIPs out of repo, or place them under explicit paths excluded from indexing.
- Add a “docs-first” architecture:
  - `docs/ARCHITECTURE.md` is canonical for component map
  - `docs/DEV_QUICKSTART.md` is canonical for run commands
  - `docs/GRAPH_RUNBOOK.md` is canonical for Neo4j ops

Verification
- Agent PRs cite/modify the docs rather than inventing new run commands.

-------------------------------------------------------------------------------
PAGE P125 — MCP EXTENSIONS (MODEL CONTEXT PROTOCOL) FOR HIGHER AUTONOMY
-------------------------------------------------------------------------------
Intent
- Give coding agent additional tools (GitHub MCP, Playwright MCP) in a controlled way.

Recommended baseline
- Enable GitHub MCP (read-only tools) for repo-aware operations.
- Enable Playwright MCP only if you have a local web UI to test, and restrict it to localhost.

Policy
- Start with minimal tool surface.
- Expand tool allowlists only after repeated successful PR cycles.

Verification
- Use the agent to fetch issue context, inspect PR checks, and validate docs without manual copy/paste.

-------------------------------------------------------------------------------
PAGE P126 — “LITIGATIONOS AS A MONOREPO” (STRUCTURE THAT SCALES WITH AGENTS)
-------------------------------------------------------------------------------
Intent
- Make the repo predictable for automation:
  - stable directories
  - explicit ownership
  - minimal cross-cutting coupling

Recommended top-level
- `apps/` (GUI, CLI launchers)
- `core/` (domain logic: PCW, evidence ledger, importers)
- `pipelines/` (harvest, transform, package)
- `schema/` (Neo4j schema, JSON schemas)
- `docs/` (single-source documentation)
- `tests/` (fixtures, unit + integration)
- `tools/` (dev scripts, build helpers)
- `out/` (ignored; generated artifacts)

Verification
- A new contributor can answer: “where do I add X?” in under 2 minutes.

-------------------------------------------------------------------------------
PAGE P127 — “ONE COMMAND” RUNBOOKS (DETERMINISTIC ENTRYPOINTS)
-------------------------------------------------------------------------------
Intent
- Agents do best when there are stable, simple entrypoints.

Required run targets
- `make test` / `./scripts/test.sh` (Linux) + `scripts/test.ps1` (Windows)
- `make lint`
- `make format`
- `make graph-import-smoke`
- `make package`

If Make is not used
- Provide a single `scripts/run_all_checks.{sh,ps1}` and reference it in docs.

Verification
- Agent PRs run the same commands, yielding reproducible results.

-------------------------------------------------------------------------------
PAGE P128 — RELEASE ENGINEERING (VERSIONED ARTIFACTS + CHECKSUMS)
-------------------------------------------------------------------------------
Intent
- Deterministic packaging with verifiable outputs.
- Avoid “download expired” by ensuring local build scripts regenerate artifacts.

Release artifacts
- CLI bundle ZIP
- GUI installer or portable EXE
- Schema pack (constraints + migrations)
- Sample cyclepack (fixtures only, no sensitive evidence)

Release workflow
- Tag releases; use GitHub Releases.
- Attach checksums (SHA-256) and manifest JSON.
- Maintain a “builder” script that reconstructs everything offline.

Verification
- A clean clone can build the same artifacts with documented commands.

-------------------------------------------------------------------------------
PAGE P129 — WINDOWS + ANDROID (TERMUX) DUAL-TARGET SUPPORT
-------------------------------------------------------------------------------
Intent
- Maintain two operator paths without duplicating logic.

Pattern
- Core logic in Python modules.
- Thin wrappers:
  - `scripts/*.ps1` for Windows
  - `termux/*.sh` for Android
- Config maps:
  - Windows: `F:\` canonical evidence root
  - Android: `/storage/emulated/0/Download` output root

Verification
- Same command semantics across both platforms, differing only in paths.

-------------------------------------------------------------------------------
PAGE P130 — “GRAPH IMPORT: RESUMABLE” (THE HARD BLOCKER SOLVER)
-------------------------------------------------------------------------------
Intent
- Make Neo4j import resumable, append-only, and observable.

Minimum features
- Chunked imports (by shard_id ranges)
- Idempotent merges keyed by stable IDs
- Checkpoint file: `out/import_state.json`
- “resume” flag: continue from last successful chunk
- Metrics: nodes/edges loaded per chunk + time

Verification
- Kill import mid-run; resume; final counts match expected.

-------------------------------------------------------------------------------
PAGE P131 — “TEST DATA FIXTURES THAT DON’T LEAK EVIDENCE”
-------------------------------------------------------------------------------
Intent
- Agents need fixtures to test without accessing sensitive evidence.

Fixture rules
- Use synthetic docs or heavily redacted samples.
- Store in `tests/fixtures/`.
- Include “golden” outputs for deterministic comparisons.

Verification
- CI passes using fixtures only.

-------------------------------------------------------------------------------
PAGE P132 — SECURITY POSTURE FOR AGENTS (SECRETS + FIREWALL + SUPPLY CHAIN)
-------------------------------------------------------------------------------
Intent
- Reduce risk of agent-enabled automation.

Controls
- GitHub Environments: store secrets/vars in `copilot` environment.
- Use least-privilege workflow permissions.
- Pin dependencies and enable Dependabot.
- Prefer allowlists over broad network access for CI.
- Keep large evidence stores out of the repo; use local mounts or encrypted storage.

Verification
- No secrets in logs or commits.
- Workflows pass security review.

-------------------------------------------------------------------------------
PAGE P133 — “LEGAL OUTPUT SAFETY” (DRAFT vs FILE_READY)
-------------------------------------------------------------------------------
Intent
- Maintain clean separation between research/draft content and filing-ready content.

Rule
- Agents may generate DRAFT legal text with placeholders *only if* clearly marked as DRAFT
  AND never auto-packaged into FILE_READY packets.
- FILE_READY requires:
  - verified quotes
  - pinned evidence references
  - PO saturation
  - service + deadline checks

Verification
- CI prevents accidental inclusion of DRAFT content in FILE_READY bundles.

-------------------------------------------------------------------------------
PAGE P134 — OBSERVABILITY (RUN LOGS, METRICS, AND FAILURE DIAGNOSTICS)
-------------------------------------------------------------------------------
Intent
- “No silent failures.”

Minimum logging
- Every pipeline step logs:
  - inputs
  - outputs
  - counts
  - duration
  - errors with tracebacks
- Store logs in `out/logs/<run_id>/`

Verification
- A failed run leaves a complete forensic trace.

-------------------------------------------------------------------------------
PAGE P135 — GOVERNOR PILLAR: OUTPUT REGISTRY + MANIFESTS
-------------------------------------------------------------------------------
Intent
- Make every generated artifact discoverable and reproducible.

Registry file
- `out/REGISTRY.jsonl` (append-only)
  - {run_id, ts, command, inputs[], outputs[], status, metrics}

Manifest rule
- Every ZIP includes:
  - `manifest.json`
  - `manifest.csv`
  - `README.md`
  - `run.log`

Verification
- Any artifact can be traced back to a run + inputs.

-------------------------------------------------------------------------------
PAGE P136 — “NARROW-FIRST” DELIVERY: BUILD THE CORE PIPELINE BEFORE GUI
-------------------------------------------------------------------------------
Intent
- Prevent GUI work from masking core pipeline instability.

Order of operations
1) Harvest pipeline stable (fixtures + deterministic outputs)
2) Graph import stable (resumable)
3) Packet compiler stable (DRAFT vs FILE_READY gates)
4) THEN GUI wrapper + orchestrator

Verification
- CLI-only can fully reproduce outputs.

-------------------------------------------------------------------------------
PAGE P137 — GUI STRATEGY (ELECTRON/PYSIDE) WITH A STABLE BACKEND CONTRACT
-------------------------------------------------------------------------------
Intent
- GUI is a front-end; backend contract remains stable and testable.

Contract
- Backend exposes:
  - `run_harvest(config) -> run_id`
  - `run_graph_import(run_id) -> status`
  - `build_packet(case_id, vehicle_id) -> packet_path`
- GUI reads `out/REGISTRY.jsonl` and presents progress.

Verification
- GUI is replaceable without rewriting core logic.

-------------------------------------------------------------------------------
PAGE P138 — AUTOMATION SCHEDULES (SAFE, READ-ONLY DEFAULTS)
-------------------------------------------------------------------------------
Intent
- Frequent harvest cycles without risk.

Default schedule
- “4x per day” read-only harvest:
  - scan + index + manifest + blockers report
- No network calls unless required and configured.

Verification
- Scheduled jobs cannot mutate evidence; outputs are append-only.

-------------------------------------------------------------------------------
PAGE P139 — HUMAN-IN-THE-LOOP CHECKPOINTS (WHERE AUTOMATION MUST STOP)
-------------------------------------------------------------------------------
Intent
- Identify irreversible steps requiring explicit human approval.

Stop points
- Any filing or service activity (PCG gate)
- Any evidence modification or renaming
- Any claim/vehicle selection that changes litigation posture

Verification
- System refuses to proceed without explicit approval.

-------------------------------------------------------------------------------
PAGE P140 — OPERATOR CHECKLIST: “FIRST WEEK TO AGENT-STABLE REPO”
-------------------------------------------------------------------------------
Day 1
- Merge onboarding PR (P111–P123 files).
- Confirm `copilot-setup-steps.yml` runs successfully.

Day 2
- Create 3 seed issues (small):
  - Add `scripts/run_all_checks`
  - Add `docs/ARCHITECTURE.md`
  - Add Neo4j schema constraints file

Day 3–4
- Add one custom agent for tests; use it to improve coverage.

Day 5–7
- Add resumable graph import scaffolding + fixtures.
- Establish first end-to-end “fixture harvest → graph import → packet draft” CI job.

Success definition
- Agent PR cycles converge quickly:
  - low rework
  - consistent tests
  - stable docs
  - reproducible artifacts

END OF APPEND-ONLY EXPANSION P111–P140
===============================================================================


===============================================================================
APPEND-ONLY EXPANSION P141–P220 — “GOLDEN COMPASS + REPLAYABLE MAINFRAME + SCHEMA GOVERNANCE”
Build date (UTC): 2026-01-18
===============================================================================

P141 — Decision Golden Compass (DGC): the “always-upward” steering law
Goal: eliminate drift, stagnation, and local-optima thrash by enforcing a single, explicit decision calculus that every module, agent, and human workflow must obey.
DGC is *not* a vibe; it is a machine-checkable policy applied at: (a) planning, (b) task selection, (c) execution gating, (d) rollback/replay, (e) long-run roadmap evolution.

DGC.0 Hard Constraints (never violated; fail-closed):
- Truth: no invented facts, no invented record, no invented holdings; missing => PINPOINT_MISSING + acquisition plan.
- Authority: Michigan-first authority snapshot; out-of-snapshot proposition => blocked unless explicitly “overlay” lane.
- Proof-Carrying Workflow (PCW): irreversible acts (filing/service) require POs SATISFIED and PCG PASS.
- Determinism: every run has a RunID, manifest, stable paths, and reproducible outputs (within defined tolerances).
- Safety: no destructive operations without explicit flags; no covert actions.

DGC.1 Upward Objective (maximize) with multi-objective scoring:
For any candidate action A (module run, ingest step, build step, filing draft, escalation lane), compute a score vector:
S(A) = <L,F,C,R,T,Q,P>
Where:
- L = Legal leverage gain (procedure advantage, preserved error, denial conversion potential)
- F = Financial outcome gain (claims value, cost avoidance, enforceability)
- C = Child/family outcome gain (contact restoration, risk reduction, stability)
- R = Record survival gain (appeal posture, preservation, auditability)
- T = Time-to-value (speed; earlier wins preferred, but never at constraint violation)
- Q = Quality gain (robustness, testability, fewer failure modes)
- P = Platform gain (reusability, productization, modularity, future automation lift)

Each axis is 0..100 with explicit rubric (below). A is selected by:
1) filter by DGC.0 hard constraints
2) maximize WeightedSum(A) = Σ wi*axis_i, with default weights:
   wL=0.22,wF=0.18,wC=0.22,wR=0.16,wT=0.08,wQ=0.08,wP=0.06
3) tie-breakers:
   (i) lower operational risk (fewer external dependencies)
   (ii) higher replayability (better event logging, idempotency)
   (iii) higher “PO closure rate” (moves more POs to SATISFIED per unit time)

DGC.2 Rubrics (machine-checkable; no vague scoring)
- L increases when action produces: findings-gap matrix, contradiction map, preserved objections, procedural defaults, deadline defense, service defects, sanctions posture.
- F increases when action produces: quantified damages model, collection/enforcement plan, fee-shift hooks, settlement leverage, asset/LLC mapping.
- C increases when action produces: evidence-based parenting-time restoration steps, safety mitigations, compliance proof.
- R increases when action produces: page/line pins, transcript harvest, ROA alignment, “quote ledger,” exhibit integrity, reproducible packets.
- T increases when action can complete within 1–2 cycles and unlocks downstream steps.
- Q increases when action adds tests, eliminates brittle assumptions, improves error handling, reduces false positives, adds validations.
- P increases when action generalizes into reusable engine or repo-quality module.

DGC.3 Anti-regression (guard against “expansion” that breaks)
- Any change that decreases Q or R by >5 points requires: compensating controls + explicit mitigation notes.
- If any run fails PCG for a reason previously fixed, raise Severity=REGRESSION and open a mandatory FixPO.

DGC.4 DGC Artifacts (required per run)
- `dgc_scorecard.json`: scored candidates + selection rationale + constraints applied.
- `dgc_decision_trace.md`: human-readable summary referencing objective axes and the selected action.
- `dgc_weight_profile.json`: weights used (allow per-track presets; default above).

P142 — Replayability & Audit: Crash-safe job queue + event-sourced run ledger
Objective: every run is replayable, reconstructable, and auditable; failures do not corrupt state.

Core primitives:
- RunID: deterministic identifier (timestamp + machine + short hash of config).
- JobID: UUIDv7 or deterministic content-hash for idempotency.
- EventLog: append-only JSONL, each line = {ts,run_id,job_id,event_type,payload_ref,crc32}.
- Checkpoints: per-job atomic commit of outputs + manifest snapshot.
- IdempotencyKey: prevents duplicate work and supports safe retries.

Minimum event types:
RUN_START,RUN_CONFIG,RUN_ENV,RUN_WARNING,RUN_ERROR,RUN_END,
JOB_ENQUEUE,JOB_START,JOB_PROGRESS,JOB_CHECKPOINT,JOB_END,
ASSET_POINTER_CREATED,ASSET_FETCH,ASSET_VERIFY,
PO_OPEN,PO_UPDATE,PO_SATISFIED,PCG_PASS,PCG_FAIL,
GRAPH_WRITE_PROPOSED,GRAPH_WRITE_COMMITTED,GRAPH_WRITE_BLOCKED,
BUNDLE_BUILD_START,BUNDLE_BUILD_END,SIZE_BUDGET_REPORT

Crash model:
- On crash, orchestrator reads EventLog + Checkpoints, resumes jobs with state=INCOMPLETE.
- Jobs must be restartable and either (a) idempotent, or (b) guarded with idempotency keys.

Poison-job handling:
- If a job fails N times with same signature, quarantine to `QUEUE/poison/` with diagnostics; continue other jobs.

P143 — Permission model: LLM cannot mutate; validators own state transitions
Goal: prevent “creative” output from damaging truth, authority, or graph state.

Roles:
- LLM_ROLE (planner): can read, propose, and draft; cannot mutate graph/state.
- VALIDATOR_ROLE: can approve/reject/modify proposals; can apply limited state changes.
- EXECUTOR_ROLE: runs approved tasks; writes outputs; commits graph changes only if validator has approved.
- HUMAN_ROLE: final authority for irreversible acts; can override with explicit rationale logged.

Capability tokens:
- Each action requires a capability: CAP_READ, CAP_PROPOSE, CAP_VALIDATE, CAP_EXECUTE, CAP_COMMIT_GRAPH, CAP_PACKAGE_RELEASE.
- Capabilities are assigned per module/agent; LLM has CAP_READ + CAP_PROPOSE only.

State transition rule:
- Any mutation of “canonical” artifacts (graph, PO ledger, authority snapshot, manifest) must be:
  Proposed -> Validated -> Committed
where “Validated” produces a signed (or integrity-keyed) approval record stored in EventLog.

Proposal objects:
- `ChangeRequest.json`: {id,author,scope,proposed_ops,preconditions,expected_effects,rollback_plan}
- Graph changes are represented as: Cypher patch files + expected counts + constraints.

Validator checks (minimum):
- TruthLock: all factual nodes/claims carry evidence pins.
- AuthorityLock: all propositions cite snapshot authority with pinpoints + eff date.
- Determinism: stable filenames, no nondeterministic ordering without sorting.
- Safety: no destructive operations without flags.

P144 — Schema governance: explicit, versioned Neo4j + stores, with migrations
Problem: graphs rot without schema discipline; migrations keep the system stable and evolvable.

Schema layers:
1) Graph schema (Neo4j): constraints/indexes + label conventions + relationship types.
2) Artifact schemas: JSON schemas for manifests, PO ledger, evidence atoms, authority refs, timelines.
3) Pipeline schemas: job specs, queue items, event payloads.

Neo4j migrations (open-source approach; no paid tooling required):
- Store migrations as `schema/migrations/V####__name.cypher`
- Each migration includes:
  - header metadata block: version, author, created_ts, depends_on, reversible?
  - pre-check queries with expected results
  - operations: constraints/indexes/procedures
  - post-check queries

Migration runner contract:
- Tracks applied migrations in `SchemaVersion` node with properties {version, applied_ts, run_id, checksum}.
- Enforces monotonic order; refuses to apply out-of-order unless “repair mode” is explicitly invoked.
- Supports dry-run: prints Cypher, does not commit.

Additional stores migrations:
- `stores/migrations/V####__*.sql` for SQLite state stores
- `stores/migrations/V####__*.jsonschema` for JSON schema evolution

Schema invariants (non-negotiable):
- Every node with legal significance must include: `case_id`, `track`, `created_ts`, and either `evid_pin` or `auth_pin` (or both).
- Every relationship must include: `src`, `confidence`, and `provenance_ref`.

P145 — External asset strategy beyond “pointer file”: Content-addressed Asset Vault + fetch plans
Goal: stay under 700MB while preserving integrity and replayability without brittle links.

Design:
- Asset Vault is a CAS (content-addressed store) with optional remotes.
- Each asset is identified by IntegrityKey (BundleUID+EntryPath+CRC32+bytes+mtime) and optionally SHA-256.
- Large assets are stored out-of-band by default (not inside FULL zip) but can be fetched deterministically.

Local CAS layout:
ASSET_VAULT/
  objects/
    43/43e59707d058199d5f24bd2d48a73064a4ef7e32da6ee7d16409d5f00a26c180/blob.bin
  meta/
    43/43e59707d058199d5f24bd2d48a73064a4ef7e32da6ee7d16409d5f00a26c180/meta.json
  index.sqlite (optional; speeds lookup)
  fetch_plans/
    plan_run_20260118_000001Z.json

Pointer file format (`.assetptr.json`):
{version:1,integrity_key,sha256_optional,bytes,mtime,content_type,
 local_hint:"F:\\LitigationOS\\ASSET_VAULT\\sources\\example_large.pdf", remote_hints:[{remote:"gdrive",path:"gdrive:/EDS-USB/ASSET_VAULT/example_large.pdf"}],
 retrieval_policy:{preferred:["local","remote"],verify:["crc32","bytes","mtime","sha256?"]}}

Fetch plan:
- “As-needed” resolution: when a pipeline step requires asset, orchestrator:
  1) checks local hint
  2) checks CAS objects
  3) uses remote hints (rclone copy) if allowed
  4) verifies integrity policy
  5) caches into CAS, updates event log.

Bundle policy:
- FULL zip includes pointer files + metadata + fetch plans, never the large binaries unless explicitly “bundle-with-assets” mode.
- `ASSETS_EXTERNAL/` contains pointers and a human-readable inventory.

P146 — PO ledger coupling: required artifact so PCW is actually enforced
PCW is real only if POs are machine-tracked and gate execution.

Required artifacts per cycle:
- `PO_LEDGER.jsonl`: append-only events for each PO (open/update/satisfied).
- `PO_STATE.json`: current state snapshot (derived; reproducible).
- `PCG_REPORT.md`: final gate result for any irreversible act.

PO record schema (minimum):
{ts,po_id,vehicle_id,track,case_id,
 status:"OBLIGATION_OPEN|OBLIGATION_PARTIAL|OBLIGATION_SATISFIED",
 authority_refs:[{src,pinpoint,eff_date}],
 evidence_refs:[{path,pinpoint,type,integrity_key}],
 test:{name,method,expected,observed},
 validator:{tool_ver,assurance,notes},
 links:{docket_entry?,order?,hearing?}}

Coupling rules:
- Any module that produces a filing draft MUST update POs:
  - required elements -> po_id mapping
  - missing evidence -> PINPOINT_MISSING entry
- Packaging requires inclusion of PO ledger; build fails if missing.

P147 — Governor layer: policy enforcement without “over-strict” brittleness
Goal: enforce correctness while keeping throughput high.

Governors are modular, severity-graded policy modules:
- GOV_TRUTHLOCK
- GOV_AUTHLOCK
- GOV_PCW
- GOV_DEADLINES
- GOV_SERVICE_NOTICE
- GOV_SIZECAP
- GOV_REPRO_BUILD
- GOV_REPLAYABILITY

Each governor emits:
- `gov_findings.jsonl` (append-only)
- `gov_summary.md` (human-readable)
- severity levels: INFO,WARN,BLOCKER
Only BLOCKER stops execution; WARN continues with mandatory fixlist entries.

P148 — Scheduler + Watchers: autonomous but controlled
Watchers monitor roots and schedule jobs; they never file or serve automatically.

Watchers:
- FS_WATCHER: detects new/changed files in F:\ and intake roots; emits “INGEST_REQUEST” jobs.
- DOCKET_WATCHER: (optional) monitors known docket PDFs/exports; offline by default.
- AUTHORITY_WATCHER: checks authority snapshot freshness; runs snapshot refresh when needed.
- BUILD_WATCHER: triggers CI-style local build when code changes.

Scheduler:
- Supports Windows Task Scheduler export (`.xml`) and cross-platform cron scripts.
- Default schedule: 4x/day harvest + nightly full validation + weekly schema check.

P149 — Repro build discipline: CI + reproducible build + signing hooks (Win64 hardening)
Objective: every release is reproducible; executables are hardened and (when possible) signed.

Build reproducibility:
- Pin dependencies with lockfile + hashes.
- Use isolated build env:
  - Python: `uv`/pip with lock, or Poetry with export + hashes.
  - Node/Electron: package-lock.json with `npm ci`.
- Deterministic build flags where supported; sorted file lists for zips.
- CI job runs:
  1) clean checkout
  2) build
  3) run tests
  4) bundle
  5) verify manifest + size budget
  6) produce release artifacts

Signing hooks (free-tier compliant notes):
- Local/training/internal distribution: self-signed cert is acceptable (not publicly trusted).
- Public trust typically requires paid cert; treat as optional lane.
- Hook point: `tools/sign_windows.ps1`:
  - if cert present, signs exe/msi
  - else, emits unsigned artifact with “SIGNING_MISSING” finding (WARN).

Hardening checklist:
- Remove debug symbols where feasible
- Enable ASLR/DEP by default (toolchain-level)
- Bundle license files for third-party deps
- Produce SBOM (CycloneDX) for the release

P150 — Latent cores (new) you almost always need for LitigationOS maturity
Core patches / engines that prevent future pain:
1) ROA/DOCKET_NORMALIZER: converts ROA exports into normalized DocketEntry nodes and deadlines.
2) ORDERCHAIN_ENGINE: parses orders -> triggers -> deadlines -> required notices.
3) SERVICECHAIN_ENGINE: proofs of service + notice -> procedural validity POs.
4) QUOTELOCK_EXTRACTOR: 2-pass verification for quotes (candidate -> verified) with page/line pins.
5) FINDINGSGAP_ENGINE: order findings vs required findings vs record; emits gap matrix.
6) CONTRADICTION_ENGINE: order vs order vs testimony vs exhibit contradictions; assigns severity.
7) FORM_OVERLAY_ENGINE_MI: SCAO forms mapping and fill engine; produces court-ready PDFs/DOCX.
8) AUTH_SNAPSHOT_BUILDER: Michigan authority snapshot index with eff dates and pinpoints.
9) LLM_SANDBOX_ROUTER: routes tasks to local LLMs; strips capabilities; writes proposals only.
10) PACKAGING_BUILDER: reconstructs full bundle from patches/pointers; size-aware.

P151 — Agent suite blueprint (permission-safe)
Agents (each a module with explicit caps):
- IntakeHarvesterAgent (CAP_READ,CAP_EXECUTE): index+extract+manifest
- AuthoritySnapshotAgent (CAP_READ,CAP_EXECUTE,CAP_PROPOSE): build snapshot + propose updates
- GraphBuilderAgent (CAP_READ,CAP_EXECUTE,CAP_PROPOSE): build/import graph; proposes commits
- ValidatorAgent (CAP_READ,CAP_VALIDATE): checks proposals; blocks on hard constraints
- PackagingAgent (CAP_READ,CAP_EXECUTE,CAP_PACKAGE_RELEASE): builds zip/release, size budget
- QAAgent (CAP_READ,CAP_EXECUTE): runs tests, lint, reproducibility checks
- NarrativeCompilerAgent (CAP_READ,CAP_PROPOSE): drafts declarations/briefs with evidence pins
- FormsAgent (CAP_READ,CAP_EXECUTE,CAP_PROPOSE): fills forms; produces overlays; proposes commits

P152 — Advanced “what else” list (high leverage but often forgotten)
- Policy-based red-team: adversary simulation against drafts (procedural attacks, MRE objections, standing/jurisdiction)
- Evidence provenance chain: transformation logs for every extracted artifact (PDF->txt->quote pins)
- Document renderer tests: PDF diff/snapshot tests to ensure court-ready formatting stays stable
- Local training material index: store benchbook/mji summaries as non-quoted embeddings + authority pins
- Threat model + dependency allowlist: prevent sneaky packages; enforce offline mode options
- Multi-repo orchestrator: monorepo or meta-repo with submodules; consistent build scripts
- “Operator UX”: one-click launcher, status dashboard, clear failure explanations, fixlist export

P153 — Completion criteria for this expansion
This expansion is “done” when:
- DGC artifacts exist and influence task selection
- Event-sourced run ledger exists and can replay after a simulated crash
- Migration runner exists and can apply schema changes deterministically
- PO ledger is mandatory in bundles and enforced by PCW/PCG gates
- Asset Vault pointers + fetch plans keep FULL zip well under cap

END OF APPEND-ONLY EXPANSION P141–P220
===============================================================================



===============================================================================
APPEND-ONLY EXPANSION P154–P190 (v2026-01-18.7)
===============================================================================

# P154 — Core Directive Implant: Decision Golden Compass (DGC) as an Executable Policy Layer

## Intent
Make “always upward” a *mechanical property* of the system, not a hope. DGC must:
- steer what gets built next (task selection),
- prevent regressions (anti-regression contracts + golden fixtures),
- prevent unsafe overreach (authority lock, evidence lock, forms-first, PCW/PCG),
- maximize long-run leverage (record completeness, contradiction surfacing, deadline certainty, reusable automation assets).

## DGC integration points (must exist as code + config)
1) **Planner:** ranks candidate work items; only emits a *single best next action* (SBNA) plus a queue.
2) **Executor:** every step runs under a capability token; LLM outputs proposals only; validators apply.
3) **Packager:** refuses release if mandatory artifacts are missing or integrity checks fail.
4) **Observer:** detects drift, repeated failures, and toxic feedback loops; forces “stability sprint” when needed.

## DGC as a policy file
Create `policies/dgc_policy.yml` (human-readable) + compiled `policies/dgc_policy.json` (machine).
Policy fields:
- `hard_constraints`: (fail-closed) truth/quote/authority/forms-first/pcw/pcg/size-cap/no-skeleton
- `objective`: weighted multi-objective utility (auditability, determinism, leverage, UX, speed, correctness)
- `risk_model`: severity×likelihood thresholds; actions with risk>threshold require human confirm
- `anti_regression`: required tests/golden fixtures for each subsystem
- `stability_rules`: if consecutive failures > N, switch to harden/repair mode

## Required DGC artifacts per run
- `runs/<run_id>/dgc_scorecard.json` (candidate list + scores + chosen SBNA)
- `runs/<run_id>/dgc_explanations.md` (operator-readable, short)
- `runs/<run_id>/policy_snapshot/` (exact policies used)

## Verification
- Given a run folder, a third party can see *why* the next action was chosen, *what constraints applied*, and *what would have won if constraints were relaxed*.


# P155 — Replayability: Crash-Safe Job Queue + Event Log (RunLedger v2)

## Intent
A LitigationOS run must be replayable and auditable under failure (power loss, crash, partial outputs). Build an event-sourced execution spine:
- deterministic inputs/config → deterministic step plan
- step execution emits immutable events
- replay reconstructs state and resumes pending steps

## Data model (SQLite + WAL; single-file portability)
Use `state/runledger.db` with tables:
- `runs(run_id, started_at, finished_at, mode, config_hash, status, host_fingerprint)`
- `jobs(job_id, run_id, name, step, deps_json, capability, status, attempt, last_error, started_at, finished_at)`
- `events(event_id, run_id, ts, type, actor, payload_json, sha256)`
- `artifacts(artifact_id, run_id, kind, path, bytes, sha256, created_at, provenance_json)`
- `locks(lock_id, scope, owner, acquired_at, released_at)`

## Event types (minimum)
- `RUN_STARTED`, `RUN_PLANNED`, `JOB_QUEUED`, `JOB_STARTED`, `JOB_PROGRESS`, `JOB_FINISHED`, `JOB_FAILED`, `RUN_FINISHED`
- `VAULT_ITEM_ADDED`, `EXTRACTOR_OUTPUT_ADDED`, `GRAPH_MUTATION_APPLIED`, `MIGRATION_APPLIED`
- `GATE_PASSED`, `GATE_FAILED`, `HUMAN_CONFIRM_REQUIRED`, `HUMAN_CONFIRM_GRANTED`

## Resume rules
- If `JOB_STARTED` exists without `JOB_FINISHED`, job is re-queued with attempt+1.
- If attempt exceeds policy threshold, job transitions to `BLOCKED` and emits a fixlist.
- All writes go through a temp path + atomic rename to prevent partial output corruption.

## Verification
- Provide `tools/replay_run.py --run-id <id> --resume` to re-run from last consistent point.


# P156 — Permission Model v3: Capability Lattice + Policy-Governed State Transitions

## Intent
Prevent accidental mutation and hallucinated state changes by separating:
- **Proposers** (LLMs/agents) → generate structured proposals only
- **Validators** → evaluate proposals against hard constraints + record
- **Appliers** → commit mutations (graph/db/files) only when validators sign off

## Capability lattice
Define a strict set of capabilities; tokens are *scoped* and time-bounded:
- `CAP_READ_VAULT`, `CAP_READ_CONFIG`, `CAP_EXTRACT_TEXT`, `CAP_OCR`, `CAP_INDEX`, `CAP_VECTORIZE`
- `CAP_PROPOSE_GRAPH_MUTATION`, `CAP_APPLY_GRAPH_MUTATION`
- `CAP_PROPOSE_DRAFT`, `CAP_RENDER_PDF`, `CAP_FILL_FORMS`
- `CAP_PACKAGE_RELEASE`, `CAP_EXPORT`
- `CAP_NETWORK_FETCH` (default off; requires explicit policy allowance)

## State transitions (owned by validators)
Represent pipeline state as explicit transitions:
- `INGESTED → EXTRACTED → INDEXED → GROUNDED → DRAFTED → VALIDATED → PACKAGE_READY → RELEASED`
Only validators may move artifacts forward, based on evidence/authority pins.

## Proposal format (strict JSON)
Every proposal must be a JSON document with:
- `proposal_id`, `run_id`, `scope`, `intended_effect`
- `inputs` (artifact ids), `outputs` (planned artifact ids)
- `patches` (graph mutations or file ops)
- `claims` (if any) with required evidence pins
- `risks` + requested capabilities

## Verification
- An LLM cannot “silently do” something. It can only propose; validators enforce.


# P157 — External Asset Strategy v3: Content-Addressed PackStore (CAPS) + Pointer Manifests

## Intent
Keep the FULL bundle ≤700MB while supporting arbitrarily large evidence/authority corpora.
Provide a better-than-“just pointers” system: **a content-addressed pack store** (git-like) with deterministic reconstruction.

## Design
1) **CAS objects:** each external file becomes an object with digest (default: SHA-256) and size.
2) **Chunking:** optionally chunk large objects (e.g., 8–32MB) into chunk objects to enable partial fetch.
3) **Packfiles:** group many objects/chunks into compressed packfiles (`packs/pack_<id>.zst`).
4) **Indexes:** store pack index mapping object→pack→offset/len in small JSON/SQLite.
5) **Pointers:** inside the ≤700MB bundle, store only:
   - object metadata (`assets/index.jsonl`)
   - pack indexes (`assets/packs/index.sqlite`)
   - fetch plan templates (`assets/fetchers/*.py|ps1`)
   - optional “seed packs” that are small but high-value (authority snapshots, schemas)

## Fetch lanes (free, operator-controlled)
- Local drives (F:/D:/) fetcher
- rclone to Google Drive/Dropbox/OneDrive (only if configured by operator)
- Manual import lane: `tools/assets_import.py --path <folder>`

## Deterministic rebuild
Builder must reconstruct the identical logical asset tree from:
- pointer manifests + local packstore (or fetched packs)
No silent downloads; every fetch is logged and hash-verified.

## Verification
- `tools/assets_verify.py` enumerates missing objects and produces an acquisition plan.


# P158 — Schema Governance v4: Versioned Migrations for Neo4j + Local Stores

## Intent
Prevent schema drift. Graph schema must be:
- explicit, versioned, enforceable, and migratable
- aligned to the data model for Evidence/Authority/POs/Orders/Service/Deadlines

## Components
1) `schema/neo4j/` migrations:
- `V0001__init.cypher`
- `V0002__constraints_indexes.cypher`
- `V0003__add_po_ledger.cypher`
…
2) `schema/sql/` migrations for runledger + auxiliary stores
3) `schema/contracts/` invariants tested in CI (schema must match expectations)

## Migration runner
Create `tools/migrate.py`:
- reads current schema version from `(:SchemaVersion {name:'litigos', version:'V####'})`
- applies forward-only migrations idempotently
- records `MigrationApplied` events in RunLedger
- validates constraints/indexes exist

## Verification
- `tools/schema_check.py` fails build if constraints/indexes missing.


# P159 — PCW Enforcement: PO Ledger as a Mandatory First-Class Artifact

## Intent
PCW is meaningless without an enforceable ledger. Every vehicle/draft must have:
- explicit Proof Obligations (POs)
- evidence pins for each PO
- authority pins for each PO
- a validator decision trace (PASS/PARTIAL/OPEN)

## PO ledger structure
File: `outputs/<run_id>/po_ledger.jsonl` (append-only lines; easy diff/merge)
Each row:
- `po_id`, `case_id`, `vehicle_id`, `prop_id`
- `po_type` (jurisdiction/service/deadline/element/finding/authority)
- `authority_ref` (snapshot_id + section; if missing → AUTHORITY_PINPOINT_MISSING)
- `evidence_ref` (vault_id + page/line/bates; if missing → EVIDENCE_PINPOINT_MISSING)
- `test` (how validator decides)
- `state` (OPEN|PARTIAL|SATISFIED)
- `validator_ver`, `ts`

## Coupling rules
- Draft compiler may not emit FILE_READY unless all *core* POs for the chosen vehicle are SATISFIED.
- Packaging gate fails if `po_ledger` missing.


# P160 — Watchers/Daemons/Schedulers v3: Autonomous Harvest Without Chaos

## Intent
Run continuously without trashing state. Watchers must be:
- debounced, idempotent, and crash-safe
- policy-governed (what sources are allowed)
- low-risk by default (read-only ingestion)

## Required daemons
1) `watch_drive`: monitors local folders (F:/ + configured roots) for new/changed files
2) `watch_rclone`: sync delta scan (no auto-delete), writes delta manifest
3) `watch_downloads`: monitors browser/portal downloads folder
4) `watch_maildrops`: monitors exported .eml/.msg drops (no direct email login unless operator sets up)
5) `watch_scanner`: ingests scanned PDFs from a scan folder
6) `watch_repo`: monitors repo changes and triggers CI locally

## Scheduling
- Use OS scheduler (Task Scheduler) to run orchestrator 4×/day (configurable)
- Use a lightweight internal scheduler for finer granularity (minutes) but never overlapping runs (global lock)

## Verification
- Each daemon writes to RunLedger; no hidden work.


# P161 — Runners: Local-First CI, Repro Builds, and Release Hardening

## Intent
Make “works on my machine” irrelevant. Provide:
- reproducible build environments
- local runner scripts + optional GitHub Actions
- release gates (schema check, smoke tests, size budget, SBOM)

## Repro strategy (practical)
- Pin Python deps (`requirements.lock` or `uv.lock`)
- Pin Node deps if GUI uses Electron (`package-lock.json`)
- Record tool versions in `MANIFEST/toolchain.json`
- Provide a single `tools/build_all.py` that:
  1) runs tests
  2) builds GUI
  3) builds exe
  4) runs smoke tests
  5) packages release

## Signing hooks
- Optional self-sign for local trust; public trust lane is separate.
- Signing is never silent; emits explicit finding if missing.


# P162 — Agentic Architecture v4: Governors, Planners, Executors, Validators

## Intent
Scale to many modules without losing control.

## Roles (strict)
- **Governor:** owns the DGC policy + selects SBNA
- **Planner:** decomposes SBNA into jobs with dependencies
- **Executor:** runs jobs under capability tokens
- **Validator:** approves state transitions + blocks unsafe outputs
- **Packager:** creates releases + manifests + builders
- **Observer:** watches telemetry; forces hardening when needed

## Agent interface contract
Each agent is a module with:
- `capabilities_required`
- `inputs_spec` and `outputs_spec`
- `determinism` declaration (expected stable outputs)
- `tests` and `golden fixtures`


# P163 — Graph Brains v3: 3–5 Blooms (Jurisdiction/Authority/Record/Procedure)

## Intent
Implement multiple “brains” as filtered projections of one master graph.

## Recommended blooms
1) **Jurisdiction Brain:** courts, venues, judges, clerks, agencies; filing lanes; transfer/escalation.
2) **Authority Brain (MI-first):** MCR/MCL/MRE/benchbooks/SCAO forms; effective dates; proposition nodes.
3) **Record Brain:** evidence vault, quotes, exhibits, transcripts, hearing events, ROA/docket.
4) **Procedure Brain:** vehicles, prerequisites, deadlines, service/notice chains, preservation steps.
5) **Adversary Brain (optional):** parties/entities, corporate shells, relationships, pattern evidence.

## Crosswiring
- A vehicle node links to:
  - required authority proposition nodes
  - required POs
  - required exhibits/record items
  - draft templates and form overlays


# P164 — Latent “You Forgot This” Catalog (Expanded)

## Intent
A curated list of missing-but-critical subsystems that prevent stagnation.

### Data/record cores
- TRANSCRIPT_PIPELINE: ingest + segment + speaker map + page/line pinning (no OCR unless necessary)
- AUDIO_VIDEO_PIPELINE: metadata + transcript alignment + excerpt pinning (store pointers for large media)
- FILE_CORRUPTION_SCANNER: list corrupt archives/files safely; quarantine registry
- DUPLICATE_DETECTOR: byte-level + semantic dedupe; preserve originals

### Legal logic cores (MI-first, authority snapshot required)
- VEHICLE_CANDIDATE_GENERATOR: relief→candidate forms/vehicles with prerequisite checklist
- ELEMENT_MATRIX_GENERATOR: elements→required facts→evidence pins
- PRESERVATION_ENGINE: objection/preservation prompts keyed to hearing stage
- FINDINGS_REQUIREMENT_MAP: required findings vs actual findings vs record

### Graph + retrieval cores
- CONTEXT_PACK_BUILDER: minimal context bundle for any claim
- GRAPH_DIFF_ENGINE: compare two runs’ graphs and explain deltas
- BLOOM_THEME_PACKAGER: palettes, node shapes, tooltip schema, drilldowns (no proprietary lock-in)

### Ops + governance cores
- CONFIG_AUDITOR: checks for policy violations before runs
- SECRET_HYGIENE: prevent accidental token/PII commits
- INCIDENT_RUNBOOKS: when something breaks, produce deterministic fixlists


# P165 — Convergence Definition: “What does DONE mean?”

## DONE criteria (engineering)
DONE is reached when the system can, end-to-end:
1) ingest new documents automatically (read-only)
2) update manifests + indexes + graph deterministically
3) emit a case-ready dashboard: timeline, exhibits, deadlines, contradictions
4) propose filings (forms-first) with a complete PO ledger
5) block unsafe outputs (PCG) until POs satisfied
6) package a reproducible release and rebuild it from scratch

## DONE criteria (operator)
- One-click: “Harvest → Update Graph → Produce SBNA outputs”
- Clear fixlists for missing inputs
- No silent automation; everything logged


# P166 — Blockers & Acquisition Plan Template (Mandatory in Absence of Inputs)

If any of these are UNKNOWN, you must emit a structured acquisition plan (no guessing):
- Controlling orders + ROA exports + timestamps
- Proofs of service/notice and hearing notices
- Authority snapshot sources (official PDFs) + effective dates
- SCAO form instructions and fillable form copies

Template:
- BLOCKER_ID
- What’s missing (exact)
- Why it matters (which gate/PO)
- Where to obtain (official source or operator location)
- How to ingest (watcher lane)
- Validation method (hash/manifest/page pins)


# P167 — NEXT: Implementation Punchlist (SBNA-oriented)

If continuing without new inputs, default SBNA order:
1) Implement RunLedger v2 + crash-safe queue
2) Implement capability lattice + proposal/apply split
3) Implement CAPS external asset vault + builder integration
4) Implement Neo4j migrations runner + schema checks
5) Make PO ledger mandatory in every draft bundle
6) Add watchers with lock + debounce
7) Wire GUI dashboard to RunLedger + graphs + outputs


END OF APPEND-ONLY EXPANSION P154–P190
===============================================================================


===============================================================================
APPEND-ONLY EXPANSION P191–P235 (v2026-01-18.8)
Focus: latent cores + governors + daemons + runners + replayability + MI-logic wiring.
===============================================================================

P191 — COREPATCH REGISTRY: how the system discovers “missing cores” and upgrades safely
Intent: make expansion automatic but non-destructive. A COREPATCH is a structured unit of capability: {problem,scope,inputs,outputs,gates,tests,rollback,metrics}.
Mechanism:
- `corepatch/registry.json` is the canonical index (append-only; new entries never delete old).
- `corepatch/select.py` selects the next patch set using DGC scoring + gap pressure + operational risk.
- A COREPATCH is never “applied” directly by an LLM. The LLM can propose; the Validator/Applier executes after tests.
Registry fields (minimum):
- corepatch_id (e.g., CP-ORDERCHAIN-0001)
- category (intake|extract|graph|authority|draft|forms|ops|ui|security|packaging)
- trigger_signals (observed symptoms)
- required_artifacts (what must exist after apply)
- gate_impact (which gates become stronger)
- tests (commands + expected outputs)
- rollback_plan (how to revert)
- observability (counters + logs)

P192 — GOVERNOR PILLAR v2: a deterministic “brainstem” that turns chaos into runs
Role: orchestrate without hallucination. Everything becomes a RunLedger entry and a JobQueue item.
Components:
- `governor/config.yaml`: single source of truth for roots, remotes, case registry, schedules.
- `governor/runledger.sqlite` (WAL enabled): event-sourced log of jobs, artifacts, deltas, failures.
- `governor/jobqueue.sqlite`: crash-safe queue with retry policy, backoff, idempotency keys.
- `governor/plan.json`: the chosen SBNA plan for this run (inputs→steps→expected artifacts).
Rules:
- Every job must be restartable; on crash, resume from last committed step.
- Every job must be idempotent; rerun should not multiply nodes/artifacts.
- No job may mutate sources; only derived outputs.

P193 — RUN REPLAY: making every run replayable, auditable, and court-safe
Event-sourcing contract:
- Each pipeline step emits `RunEvent` records with: {ts,run_id,step_id,inputs_hash,outputs_hash,exit_code,summary,paths}.
- Each derived artifact is registered: {artifact_id,type,case_id,run_id,producer,depends_on[],integrity_key}.
- Replay reads RunEvents + manifests to reproduce outputs or pinpoint where divergence occurred.
Replay modes:
- `replay --mode EXACT`: same tools/versions; fails if toolchain mismatch.
- `replay --mode BEST_EFFORT`: allows newer toolchain, but emits drift report and does not label FILE_READY.

P194 — PERMISSION MODEL v3: LLM as proposer, validators as enforcers, appliers as writers
Goal: avoid silent corruption and keep the system “law-locked” and record-locked.
Capability lattice (examples):
- CAP_READ_VAULT, CAP_READ_GRAPH, CAP_READ_AUTH
- CAP_PROPOSE_PATCH, CAP_PROPOSE_DRAFT
- CAP_APPLY_GRAPH_MIGRATION, CAP_APPLY_FILE_WRITE
- CAP_PACKAGE_RELEASE
Policy engine:
- `policy/rules.json` expresses which capabilities can be used in which modes.
- LLM outputs are restricted to “proposal objects”: JSON change requests, never direct writes.
State transitions:
- Only `ValidatorAgent` can mark POs SATISFIED.
- Only `PCG` can authorize irreversible actions (filing/service/export-to-court packet).
- `ApplierAgent` executes only after Validator PASS.

P195 — EXTERNAL ASSET VAULT v3: beyond pointers, toward content-addressed packfiles
Problem: pointer files alone become brittle; packfiles make assets durable and offline-friendly.
Design:
- Store large assets in CAS, but also support “packfiles” (like git pack): many assets compressed into deterministic bundles.
- FULL chat zip stays small by shipping:
  1) pointer metadata
  2) fetch plans
  3) pack index files (no blobs)
Pack index:
- `packs/pack_0001.idx.json`: lists {asset_sha256,pack_id,offset,length,crc32,bytes,content_type}.
- `packs/pack_0001.pack.zst`: the compressed blob pack (kept external by default).
Builder behavior:
- If pack exists locally, builder reconstructs exact assets without network.
- If pack missing, builder uses rclone to fetch pack from configured remotes, then verifies index and checksums.
Why this is better:
- Minimizes file-count overhead on Windows.
- Keeps integrity deterministic while allowing offline.
- Scales to thousands of assets without 700MB chat-zip explosion.

P196 — PO LEDGER v2: enforce PCW at compilation time, not just as policy text
Upgrade: make PO ledger a required input to all drafting and packet building.
Compiler rules:
- A draft is labeled FILE_READY only if:
  - all mandatory POs for the selected Vehicle are SATISFIED
  - all authority refs are in-snapshot (effective-date checked)
  - all quotes are VERIFIED (QuoteLock)
- If any mandatory PO is not SATISFIED:
  - compiler emits FIXLIST.json + acquisition plan tasks
  - output label remains DRAFT

P197 — VEHICLEMAP v2: formalize vehicle selection so “relief” always routes to a form + rule
Vehicle nodes:
- VehicleID, forum, form_id (SCAO/MC/FOC), prerequisites, deadlines, service chain, standard, elements.
- Each element maps to a PO.
Selection:
- Relief request enters as `ReliefIntent`.
- VehicleMap chooses candidate vehicles and ranks them using: jurisdiction fit, risk, time-to-relief, evid completeness.

P198 — AUTHORITY SNAPSHOT v2: authority as an indexed, versioned library with effective dates
Requirements:
- Snapshot has `snapshot_id`, `source_manifest`, and `effective_date_range`.
- Every AuthorityRef must include: {src_id,section,pinpoint,eff_date,snapshot_id}.
- Out-of-snapshot refs are blocked in FILE_READY.
Implementation:
- Store sources in `authority/sources/` (official PDFs or extracted text) and index in `authority/index.json`.
- Build “proposition nodes” in graph: each rule subpart becomes a node with edges to Vehicles and POs.

P199 — WATCHERS & DAEMONS SUITE: the system that keeps the corpus alive
Baseline watchers (safe, file-based):
- DriveWatcher: monitors intake roots for new files (debounce + file-stable checks).
- ZipWatcher: extracts zip safely into quarantine then normalizes.
- AuthorityWatcher: detects new authority PDFs and triggers snapshot rebuild.
- GraphWatcher: runs health checks and compaction.
- DraftWatcher: re-runs validation when new evidence satisfies a PO.
Scheduler discipline:
- All watcher runs become queue jobs; no inline “daemon magic.”
- Backoff and lock files prevent duplicate work.

P200 — RUNNERS: free-tier, local-first, reproducible execution
Runner lanes:
- LocalRunner (Windows): primary.
- WSL2Runner (optional): for tools better on Linux.
- ContainerRunner (optional): deterministic builds via Docker (all free).
- RemoteRunner (optional): self-hosted runner on your own machine (free).
Repro discipline:
- Lock dependencies (`uv.lock` or `poetry.lock`) and record tool versions per run.
- “Golden fixtures” stored as small synthetic samples, not real evidence.

P201 — GRAPH BRAINS: 3–5 Bloom views, each with a stable contract
Brain 1: Authority+Vehicles+Forms map (courts, forms, MCR/MCL nodes, Vehicles, POs).
Brain 2: Case spine (ROA, orders, hearings, service/notice, deadlines).
Brain 3: Evidence universe (exhibits, quote ledger, timeline, contradictions).
Brain 4: Adversary/entity map (people/entities, addresses, roles, credibility markers).
Brain 5 (optional): Judicial conduct + Canon/JTC workflow (quotes→canon→evidence→filing vehicles).
Each brain has:
- entry nodes
- required relationships
- queries saved as Bloom perspectives
- exportable HTML view (for offline)

P202 — “LATENT CORES” CATALOG v2 (expanded): the modules you regret not adding early
Intake:
- PORTAL_DROPBOX_CONVERTER (manual download folder→vault)
- EMAIL_EXPORT_NORMALIZER (mbox/eml→events)
- DUPLICATE_FILENAME_RESOLVER (same name, different bytes)
Extraction:
- PAGE_MAP_BUILDER (page→text→bbox maps)
- OCR_SELECTIVE_ROUTER (only OCR when text layer absent)
- TABLE_EXTRACTOR (orders/dockets as tables)
Graph:
- ID_STABILITY_ENFORCER (stable IDs across imports)
- MERGE_SAFETY_GUARD (prevents accidental cross-case merges)
- MIGRATION_DIFF_REPORTER (schema diff per run)
Reasoning:
- EVIDENCE_WEIGHTER (recency, authoritativeness, directness)
- HEARING_DEFENSE_SIM (cross-exam packs, objections)
Drafting:
- CITATION_COVERAGE_AUDITOR (per sentence)
- FORM_FIELD_VALIDATOR (SCAO field constraints)
Ops:
- BACKUP_ROTATION_MANAGER (3-2-1 policy)
- CORRUPTION_SCANNER (read-only)
UI:
- ONE_CLICK_RUN (Harvest→Graph→SBNA)
- FIXLIST_WORKBENCH (turn gaps into tasks)

P203 — Convergence criteria for the “next plateau”
System is at the next plateau when:
- A fresh machine can run: vault ingest → extract → graph import → retrieval → draft compile → packet build.
- Any FILE_READY packet has: PO ledger PASS + PCG PASS + QuoteLock VERIFIED.
- A crash during extraction/import can be resumed without duplications.
- External assets can be fetched via deterministic pack index without manual hunting.

END OF APPEND-ONLY EXPANSION P191–P235
===============================================================================


-------------------------------------------------------------------------------
PAGE P196 — Authority acquisition lanes (Michigan-first, QuoteLock-compatible)
-------------------------------------------------------------------------------
Intent
- Ensure every legal proposition in the graph can be traced to an authority snapshot artifact with effective date and pinpoint-ready structure.
- Keep QuoteLock enforceable: no verbatim authority text is used in FILE_READY unless extracted and verified from your snapshot.

Authority lanes (ordered; first successful wins)
1) OPERATOR_SUPPLIED_SNAPSHOT (preferred): operator places official PDFs (MCR/MCL/MRE/benchbooks/SCAO instructions) into `authority/original/`.
2) SCAO_BULK_DOWNLOAD (manual + scripted ingest): operator downloads official zip/pdf collections, then ingests.
3) COURT_WEBSITE_PDF (manual): operator downloads the PDF from the official site and saves into `authority/original/`.
4) PRINTED_SCAN_LANE: scan of printed authority pages; OCR + page markers; treated as lower confidence until matched to official PDF.

Snapshot build contract
- Input: `authority/original/*.pdf` + `authority/snapshot_config.json`
- Output:
  - `authority/snapshots/<snapshot_id>/authority_index.jsonl` (one record per section/subsection)
  - `authority/snapshots/<snapshot_id>/pinpoint_map.json` (page→section alignment hints)
  - `authority/snapshots/<snapshot_id>/extracts/` (text extractions keyed by page)
  - `authority/snapshots/<snapshot_id>/quote_candidates.jsonl` (candidate quotes with verification status)

Verification tiers
- Tier Q0 (candidate): text extracted once; not yet double-checked.
- Tier Q1 (verified): independently re-extracted with a second method and diff=0.
- Tier Q2 (anchored): verified and mapped to section + effective date + snapshot_id; allowed in FILE_READY.

Gates
- Any proposition node used to justify a procedural step must carry `auth_ref{snapshot_id,src_id,subsec,eff_date,pin}`.
- If missing, emit AUTHORITY_PINPOINT_MISSING + acquisition plan; do not fabricate.

-------------------------------------------------------------------------------
END OF APPEND-ONLY EXPANSION P191–P196
-------------------------------------------------------------------------------


-------------------------------------------------------------------------------
APPEND-ONLY EXPANSION P197–P215 — “STACK ASSEMBLER + DOCVISION + EMBEDDINGS + ARG + WATCHERS”
Build date (UTC): 2026-01-18
-------------------------------------------------------------------------------

P197 — MASTER_STACK_ASSEMBLER_CORE (pack fusion without chaos)
Purpose: unify scattered LitigationOS artifacts (zips, CSV universes, scripts, dashboards) into one deterministic, reproducible “Master Stack” directory tree, preserving originals, detecting corrupt archives, and producing a single master zip for transport.

Design goals
- Zero-destructive: never modify original inputs; only copy/extract into a new stack root.
- “Valid zip or quarantine”: all archives are validated; invalid archives are preserved as-is in RAW_ZIPS/.
- One canonical layout for cross-pack wiring: CORE_GRAPH_AND_INDEX/ becomes the “brain stem” that viewers, loaders, and dashboards attach to.
- Deterministic naming and path sanitation: stable output regardless of OS locale or special characters.

Canonical layout (StackRoot)
- LITIGATION_OS_MASTER_STACK/
  - CORE_GRAPH_AND_INDEX/
    - omni_nodes_universe.csv
    - omni_edges_master.csv
    - authority_index.csv
    - MASTER_LEGAL_TEXT_INDEX_*.csv
    - decisions*.csv
    - neo4j_nodes.csv
    - nodes_normalized.csv
    - edges_normalized.csv
    - unified_nodes.csv
    - master_edges.csv
    - Authority_Subgraph_edges.csv
  - SCRIPTS_AND_DOCS/
    - OMNI_UNIFIED_DRIVE_ORGANIZER.py (or equivalent)
    - omni_graph_from_legal_index.py
    - README_OMNI_LEGAL_TO_GRAPH.txt
    - README_OMNI_NODES_UNIVERSE.txt
  - RAW_ZIPS/
    - <any invalid or non-standard zip preserved verbatim>
  - EXTRACTED_PACKS/
    - <each valid zip extracted into its own folder>
  - README_LITIGATION_OS_MASTER_STACK.txt
  - STACK_MANIFEST.json
  - STACK_BUILD_LOG.txt

Core operations
1) Scan input directory for .zip → validate with zipfile.is_zipfile
2) Extract valid zips into EXTRACTED_PACKS/<zip_stem>/
3) Copy key “brain stem” CSVs into CORE_GRAPH_AND_INDEX/
4) Copy bridge scripts/docs into SCRIPTS_AND_DOCS/
5) Generate README_LITIGATION_OS_MASTER_STACK.txt describing the wiring model
6) Create STACK_MANIFEST.json
   - includes: extracted_map, invalid_zips, copied_core_files, copied_scripts, build_ts
7) Export a master transport zip: LITIGATION_OS_MASTER_STACK_v1.zip

Why this matters to LitigationOS
- It turns “lots of packs” into “one mountable substrate” for the Governor Pillar dashboard, Neo4j import, and HTML viewers.
- It creates a stable integration seam for future “CyclePacks” and patch-based storage under the 700MB cap.

Integration hook
- Add MASTER_STACK_ASSEMBLER as a Packaging/Distribution module invoked by DGC when:
  - more than N packs exist, OR
  - new CSV universes appear, OR
  - you need to ship a portable “brain snapshot” to another machine.

Required artifacts emitted by this core
- STACK_MANIFEST.json (inventory + maps)
- STACK_BUILD_LOG.txt (append-only logs)
- README_LITIGATION_OS_MASTER_STACK.txt (wiring instructions)
- LITIGATION_OS_MASTER_STACK_v1.zip (transport artifact)

P198 — PACK_FUSION_POLICY (unify many sources without breaking determinism)
Problem: multiple bundles, CyclePacks, “unified” zips, and dashboards are valuable, but they drift into incompatible folder assumptions.
Solution: a single pack fusion policy that is enforced by the packaging governor.

Rules
- Every external pack is treated as a read-only source. Fusion creates a new composed tree.
- Fusion is declared by a PackPlan:
  - pack_plan.json: {plan_id, inputs:[{path,type,priority}], outputs:[...], selectors:[...], conflict_policy}
- Conflict policy is explicit:
  - prefer higher priority pack
  - if equal priority and hashes differ → fork into CONFLICTS/<file>__from_<pack>
- “Brain stem precedence”: CORE_GRAPH_AND_INDEX always wins for viewer wiring.

P199 — DOCVISION_QA_ENGINE (layout-aware extraction + local multimodal reasoning)
Objective: treat PDFs and scanned images as first-class, queryable evidence/authority sources, without relying on external paid APIs.

Pipeline (two-stage: perception → reasoning)
Stage 1: Perception
- Input: PDF pages (rendered to images where needed), photos, scans.
- Output: structured tokens with layout and/or extracted text, with provenance pins.
- Techniques:
  - Text-layer extraction first (fast path) if PDF contains real text.
  - If no text layer or low confidence: OCR fallback.
  - Layout-aware models for key-value extraction, table hints, and Q/A grounding.

Stage 2: Reasoning
- Local LLM (Ollama/llama.cpp/transformers runtime) consumes:
  - extracted text
  - layout hints
  - page images (if using a VL model)
- Outputs proposals only (LLM_ROLE): quote candidates, entity mentions, candidate nodes/edges, candidate authority props.

Model menu (open-source, local deployable)
Document Q/A (layout-aware)
- impira/layoutlm-document-qa — https://hf.co/impira/layoutlm-document-qa
- naver-clova-ix/donut-base-finetuned-docvqa — https://hf.co/naver-clova-ix/donut-base-finetuned-docvqa

Vision-language (useful for “noisy scans,” handwriting, weird formatting)
- Qwen/Qwen2.5-VL-3B-Instruct — https://hf.co/Qwen/Qwen2.5-VL-3B-Instruct
- Qwen/Qwen2.5-VL-7B-Instruct — https://hf.co/Qwen/Qwen2.5-VL-7B-Instruct
- Qwen/Qwen2.5-VL-32B-Instruct — https://hf.co/Qwen/Qwen2.5-VL-32B-Instruct

Selection rubric (practical)
- If compute is limited: start with 3B VL for “page understanding” + separate text LLM for long synthesis.
- If you need high-quality grounded answers from structured documents: LayoutLM/Donut for extraction; LLM for narrative.
- If you need deep “visual” reading: 7B+ VL models.

DOCVISION artifacts (mandatory)
- docvision/pages/<doc_id>/<page_num>.png (if rendered)
- docvision/text/<doc_id>/<page_num>.txt (fast-path extraction)
- docvision/ocr/<doc_id>/<page_num>.json (OCR tokens + confidences)
- docvision/layout/<doc_id>/<page_num>.json (boxes + tokens)
- docvision/qa_candidates.jsonl (question, answer, evidence pointers)
- docvision/provenance.jsonl (transforms + tools + versions)

P200 — EMBEDDINGS_RAG_ENGINE (hybrid retrieval built for legal corpora)
Goal: make everything searchable and recall-heavy without sacrificing precision; integrate with GraphRAG.

Embedding model menu (open-source)
- sentence-transformers/all-MiniLM-L6-v2 — https://hf.co/sentence-transformers/all-MiniLM-L6-v2
- sentence-transformers/all-mpnet-base-v2 — https://hf.co/sentence-transformers/all-mpnet-base-v2
- BAAI/bge-m3 — https://hf.co/BAAI/bge-m3
- jinaai/jina-embeddings-v3 — https://hf.co/jinaai/jina-embeddings-v3

Retrieval strategy (default)
- Sparse search: keyword/BM25-style for exact legal phrases.
- Dense search: embeddings for semantic recall.
- Rerank (optional): cross-encoder or LLM scoring in local mode.
- Graph filter first: constrain by case_id/track/type (authority vs evidence vs docket) before vector search.

Chunking strategy (record-safe)
- Orders/transcripts: chunk by heading/section; preserve page and line anchors.
- Authority: chunk by rule/statute section; preserve subsection and effective date.
- Evidence: chunk by exhibit boundaries; preserve Bates/page/time.

Embedding artifacts
- vstore/chunks.jsonl (chunk_id, text_ref, pins)
- vstore/embeddings/<model_id>.bin or .npy (store outside FULL zip if large)
- vstore/index_meta.json (model, dims, normalize, created_ts)
- retrieval/traces/<query_id>.json (candidates + scores + pins)

P201 — ARG_ENGINE (Argumentation Reasoning Graph; “how filings get built”)
ARG = a graph-native representation of legal arguments that links:
- Claim nodes (requested relief / proposition)
- Element nodes (legal elements and burdens)
- Authority nodes (snapshot refs)
- Evidence nodes (pinned excerpts)
- Counterargument nodes (anticipated defenses)
- Procedure nodes (vehicles/forms, prerequisites)

ARG invariants
- Every Claim must be satisfiable as:
  Claim -> Elements -> (EvidencePins + AuthorityPins)
- Every Element must declare:
  - burden (who must prove)
  - standard (preponderance/clear/abuse/etc, where applicable)
  - failure modes (what breaks it)
- Every Counterargument must be linked to:
  - rebuttal evidence
  - rebuttal authority
  - procedural mitigation (preservation, objections)

ARG edges (typed)
- REQUIRES_ELEMENT
- SATISFIED_BY_EVIDENCE
- SUPPORTED_BY_AUTHORITY
- CONTRADICTED_BY
- REBUTS
- DEPENDS_ON_PROCEDURE
- PRESERVATION_REQUIRED

ARG artifacts
- arg/claims.jsonl
- arg/elements.jsonl
- arg/counters.jsonl
- arg/argument_maps/<claim_id>.json (compiled view)

P202 — QUOTELOCK_VERIFIER v2 (triple-checked, tool-diverse)
Rule: verbatim quotation is allowed for FILE_READY only if independently verified.

Verification methods (tool-diverse)
- Method A: primary PDF text extraction (fast path)
- Method B: alternate extraction engine
- Method C: image-render + OCR extraction (only when needed)

Verification policy
- If A==B: Verified Q1.
- If A!=B and PDF is scanned: require C; if C matches one method exactly and the mismatch is explainable (ligatures/hyphenation rules documented), mark Verified Q1 with normalization notes.
- If mismatch cannot be resolved: keep as Q0 candidate; do not use in FILE_READY.

Artifacts
- quotelock/candidates.jsonl
- quotelock/verified.jsonl
- quotelock/diffs/<quote_id>.diff
- quotelock/normalization_rules.md

P203 — TRACK PRESETS (DGC weight profiles per MEEK)
MEEK1 (housing/LT): emphasize F and L; preserve claims/fees; heavy evidence ledger.
- weights: wL=0.24,wF=0.22,wC=0.06,wR=0.20,wT=0.08,wQ=0.12,wP=0.08
MEEK2 (custody/PT): emphasize C and R; preservation and due process.
- weights: wL=0.22,wF=0.08,wC=0.28,wR=0.22,wT=0.08,wQ=0.08,wP=0.04
MEEK3 (PPO/contempt): emphasize L and R; service/notice and record survival.
- weights: wL=0.26,wF=0.06,wC=0.18,wR=0.24,wT=0.08,wQ=0.10,wP=0.08
MEEK4 (Canon/JTC): emphasize R and L; quote integrity, pattern evidence, procedural correctness.
- weights: wL=0.20,wF=0.02,wC=0.14,wR=0.34,wT=0.06,wQ=0.14,wP=0.10

P204 — WATCHERS + SCHEDULER (autonomous without filing/serving)
Watchers detect, propose, and enqueue; they never execute irreversible acts.

Daemon set
- DriveDeltaHarvester: monitors roots → emits INGEST_REQUEST jobs.
- AuthoritySnapshotWatcher: monitors authority packs freshness → emits AUTH_REFRESH jobs.
- DocketExportWatcher: watches for new ROA/docket exports → emits DOCKET_INGEST jobs.
- GraphHealthWatcher: checks constraints/indexes + missing node invariants → emits GRAPH_REPAIR_PROPOSAL.
- SizeBudgetWatcher: tracks bundle size trajectory; triggers PATCHES mode at 650MB projection.

Scheduler outputs
- Windows Task Scheduler XML exports per daemon
- cron-equivalent scripts for non-Windows

P205 — CONNECTOR GOVERNANCE (Drive/rclone/local)
Connector actions are capability-gated.
- LLM_ROLE: cannot call connectors directly; can only propose connector actions.
- EXECUTOR_ROLE: may run rclone copy/sync only when a validated job requests it.
- Every connector transfer produces:
  - transfer_receipt.json (src,dst,bytes,integrity checks)
  - eventlog entries

P206 — SIZECAP ENGINE v2 (patch-aware, regression-aware)
Policy
- If FULL zip > 650MB projected: switch to PATCHES mode automatically.
- If any single file > 100MB: default to asset pointer unless explicitly “bundle-with-assets”.
- Logs bounded: only tail N KB in FULL zip; full logs stored out-of-band with pointers.

Outputs
- size_budget_report.json
- size_budget_report.md
- offenders.csv

P207 — TEST HARNESS (PDF/OCR/graph)
Minimum tests
- PDF extraction round-trip: render->OCR->quote verify on a sample set.
- Graph schema tests: constraints exist; required properties exist; node counts reasonable.
- Deterministic packaging: two builds with same inputs yield identical manifests.

P208 — SECURITY BASELINE (offline-first)
- Dependency allowlist + hash pinning.
- License inventory (SBOM) and VEX notes when relevant.
- No network by default; connectors only under explicit validated jobs.

P209 — GUI/UX INTEGRATION SEAM
- Orchestrator emits a status_feed.jsonl designed to be consumed by:
  - Electron, PySide6, WinUI wrappers
- UI shows: current job, current file, current phase, warnings, blockers, next actions.

P210 — “CONTINUE” semantics (growth without thrash)
- Each continue cycle must add one of:
  - a new core/daemon/agent
  - a new enforceable invariant
  - a new replayable pipeline segment
  - a new schema migration
  - a new validator/gate
- Cycles stop only when further value is input-dependent; blockers must be enumerated with acquisition plans.

P211 — Acquisition plan template (input-dependent blockers)
- Missing input is declared as:
  - missing_id, why_needed, minimal acceptable substitute, fastest acquisition route, verification method.

P212 — Minimum “brains/blooms” wiring (Neo4j + viewers)
- Brain 1: Michigan Court/Authority Universe (courts, forms, rule/ statute sections)
- Brain 2: Case Spine (orders, hearings, service, ROA, deadlines)
- Brain 3: Evidence Universe (exhibits, transcripts, messages, photos)
- Brain 4: Argument Graph (ARG) (claims/elements/authority/evidence/counters)
- Brain 5 (optional): Pattern/Misconduct (Canon/JTC patterns, denial conversion, retaliation indicators)

P213 — Export surfaces
- Bloom-ready CSV exports
- HTML wheel explorer export
- Court-ready packagers (binder export + exhibit stamping integration points)

P214 — Required per-cycle artifacts (now expanded)
- CASE_STATE (<=25 lines)
- LEDGERΔ (SoR, exhibits, timeline, authority triples, contradictions, deadlines)
- PO_LEDGER + PCG report
- DGC scorecard + decision trace
- Eventlog + jobqueue receipts
- Manifest + size budget report

P215 — Stop condition (convergence)
- Stop only when:
  - all governors are PASS/WARN-only, AND
  - the next meaningful improvement requires new inputs (authority PDFs, orders, transcripts, ROA exports), AND
  - an acquisition plan is produced for each missing input.

-------------------------------------------------------------------------------
END OF APPEND-ONLY EXPANSION P197–P215
-------------------------------------------------------------------------------


===============================================================================
APPENDIX: EXPONENTIAL GROWTH CYCLE • v2026-01-18.22 • build_utc=2026-01-18 18:12:16Z
Append-only policy: this section adds new latent cores + patch protocols + indices.
===============================================================================

P216) DECISION GOLDEN COMPASS v2 (DGC2) — “UPWARD-ONLY” NAVIGATION LAW (EXECUTABLE SPEC)
Goal: force every cycle to produce *net upward capability* without drifting into chaos, brittleness, or non-actionable sprawl.
DGC2 operates as a meta-controller over: module proposals, acceptance, priorities, kill-switches, and packaging.
DGC2 invariants:
- TruthLock, QuoteLock, AuthorityLock, FormsFirst, PCW/ADD, PCG, Packaging are non-negotiable constraints.
- “Upward” means: (a) more capabilities *or* (b) lower failure rate *or* (c) higher replayability/auditability *or* (d) stronger MI-law/record safety.
- Every accepted change must have a measurable delta and a rollback-safe containment boundary.

DGC2 cycle algorithm (deterministic):
1) INVENTORY: read bundle registry + last cycle ledger; compute coverage map:
   coverage = {{ingest, ocr, quote_verify, authority_snapshot, form_overlay, graph_ingest, rag, pcw, pcg, packaging, gui, ci, security, scheduling}}
2) GAP-RADAR: for each coverage area compute “harm of missing” (HoM) score:
   HoM = severity_to_case_outcomes + frequency + time_pressure + dependency_degree
3) NOVELTY-RANK: candidate improvements get a novelty score (Nv):
   Nv = (new capability?1:0) + (new guarantee?1:0) + (removes manual step?1:0) + (reduces failures?1:0)
4) RISK-SHIELD: candidate risk score (Rs):
   Rs = (attack_surface + complexity + brittleness + license risk + size risk + MI-lock risk)
5) DECISION SCORE:
   D = 3*HoM + 2*Nv - 2*Rs - 1*cost_estimate
6) ACCEPTANCE RULE:
   Accept top-K candidates until marginal gain < epsilon OR a constraint boundary is hit.
7) SHIP RULE:
   If any “core gate” becomes weaker, compensate in same cycle (net gain or revert).
8) OUTPUT RULE:
   Produce updated playbook + updated pack manifest + runnable builders (or acquisition plan if blocked).

DGC2 tie-breakers (when D scores are close):
- Prefer capabilities that reduce irreversibility risk: replayability + audit.
- Prefer improvements that reduce dependency on external services.
- Prefer improvements that harden QuoteLock/AuthorityLock/PCW enforcement.

DGC2 “regression governor”:
- Detect repeated failure signatures in logs (same exception class / same missing file class / same env drift).
- Mandatory action: add auto-heal + preflight check + clearer diagnostics for that signature, before adding new features.

P217) GOVERNOR PILLAR vNext — RUN REPLAYABILITY + EVENT-SOURCED EXECUTION (CRASH-SAFE)
Problem: “runs are not replayable” leads to un-auditable deltas, and makes PCW/PO proof fragile.
Solution: enforce an event-sourced run model with a crash-safe queue, exactly-once semantics, and attestations.
Artifacts (append-only):
- RUN_EVENTLOG.jsonl (required): {{ts, run_id, stage, action, inputs, outputs, status, err, integrity_key, metrics}}
- JOB_QUEUE.sqlite (required): durable queue with job idempotency keys
- RUN_STATE.json (required): canonical pointer to last completed stage, resume cursor
- STAGE_ATTEST.json (per stage): record of completed stage outputs (signing optional)
Stages (recommended):
0) PRECHECK (env, disk, deps, authority snapshot presence, legal guardrails loaded)
1) HARVEST (file enumeration, extraction, manifest updates)
2) TRANSFORM (OCR, text normalization, chunking, embedding)
3) GRAPH_INGEST (Neo4j upsert via migrations)
4) PCW_BUILD (PO ledger build, element grids, vehicle maps)
5) VALIDATE (QuoteLock verify, authority in-snapshot check, service/deadline sanity)
6) PACKAGE (CyclePack, release zip(s), builder updates)
Crash/restart rules:
- Each stage produces a cursor and is resumable.
- A stage must be idempotent: re-run yields same outputs for same inputs (best-effort deterministic).
- Only the Governor transitions stage states; LLM cannot mutate stage states directly (see Permission Model).

P218) PERMISSION MODEL v2 — “LLM READ-ONLY; GATES OWN MUTATION” (CEILING UPGRADE)
Roles:
- LLM (planner/analyst): may read context, propose actions, draft outputs, but cannot mark gates PASS, cannot change graph, cannot finalize bundles.
- Validators (deterministic code): own PASS/FAIL decisions for QuoteLock, AuthorityLock, PCW completeness, PCG gate.
- Governor (orchestrator): the only component allowed to apply mutations (write graph, write bundles, change run state) and only *after* validators PASS.
Mechanism:
- Write operations require a “Mutation Ticket” (MT) issued by validators:
  MT = {{run_id, stage, allowed_ops[], inputs_hash, validator_versions, timestamp, expiry}}
- Governor checks MT before any state-changing operation.
This prevents “creative drift” and supports auditability.

P219) SCHEMA GOVERNANCE v2 — NEO4J MIGRATIONS + MULTI-STORE CONTRACTS (STATE OF THE ART)
Core principle: schema changes are versioned, migratable, and validated before ingest.
Required components:
- schema/neo4j/ (Cypher migrations):
  - 0001_init_constraints.cypher
  - 0002_indexes.cypher
  - 0003_add_nodes_edges.cypher
  - ...
- schema/contracts/ (JSON Schemas for node/edge payloads):
  - Node.AuthorityRef.schema.json
  - Node.EvidenceAtom.schema.json
  - Node.Vehicle.schema.json
  - Edge.SUPPORTS.schema.json
  - Edge.QUOTES.schema.json
  - ...
- schema/migration_state.json (tracks applied migrations; append-only events + current pointer)
Migration gate:
- Preflight: verify Neo4j connectivity; check current schema version; run “dry validate” of all planned node/edge writes against JSON schema.
- Apply migrations in a single transaction batch when supported; otherwise chunk with restart markers.
- Postcheck: ensure constraints/indexes exist; ensure required labels/properties match contracts.

P220) EXTERNAL ASSET STRATEGY v2 — CONTENT-ADDRESSABLE “ASSET VAULT” (BETTER THAN POINTER+HASH)
Constraint: releases must stay ≤700MB; heavy assets must not be embedded repeatedly.
Upgrade: implement a local Content-Addressable Asset Vault (CAAV) with packfiles + manifests + optional remote sync.
Concept:
- Large assets live in CAAV under content ID:
  CID = blake3(bytes)  (or integrity_key as configured)
- Assets stored as packfiles:
  ASSET_VAULT/pack/pack_0001.car (or .pack) + ASSET_VAULT/index/pack_0001.idx
- Bundle stores only:
  - asset pointers (CID + size + mime + original path + provenance)
  - optional tiny thumbnails/previews
- Builder script can “hydrate” assets from:
  (a) local vault, (b) user-drive paths, (c) optional rclone remote.
Why better:
- Dedup across all versions automatically.
- Single copy on disk; bundles remain slim.
- Hydration is deterministic and auditable (CID verification).
Required files:
- ASSET_VAULT/manifest.json (append-only asset registry)
- ASSET_VAULT/policy.json (what qualifies as “external asset” by size/type)
- ASSET_VAULT/hydrate_plan.json (per release: required CIDs)

P221) PO LEDGER COUPLING v2 — MAKING PCW REAL (NOT ASPIRATIONAL)
Mandatory artifact (per run + per vehicle candidate):
- PO_LEDGER.jsonl:
  Each record: {{po_id, vehicle_id, proposition_id, authority_pin, evidence_pin, state, validator, assurance, ts, notes}}
Rules:
- A vehicle cannot be marked READY unless all mandatory POs are SATISFIED.
- EvidencePin must be resolvable: {{path + page/line/Bates or timecodes}}.
- AuthorityPin must be “in snapshot” unless explicitly flagged “OUT_OF_SNAPSHOT” (not court-ready).
- The ledger must be included in packaging and referenced by any generated filing index.

P222) DOCUMENT UNDERSTANDING CORE (DOCVISION) — OCR/LAYOUT/QA LANE HARDENING (SELF-HOSTED)
Goal: harvest record-safe quotes, headings, page anchors, stamps, and form fields from hostile PDFs.
Lanes (recommended fallback ladder):
Lane 0: Text-layer extraction (fast, cheap) → validate density/quality
Lane 1: Classical OCR (line detection + recognition)
Lane 2: VLM OCR (layout + tables + formulas) for degraded scans
Lane 3: Human-assisted spot checks (only where QuoteLock cannot be satisfied)

Suggested open models (Hugging Face anchors):
- DocQA baseline: https://hf.co/impira/layoutlm-document-qa
- DocVQA baseline: https://hf.co/naver-clova-ix/donut-base-finetuned-docvqa
- OCR + document parse: https://hf.co/rednote-hilab/dots.ocr
- OCR VLM lane (3B): https://hf.co/ChatDOC/OCRFlux-3B
- OCR VLM lane (3B): https://hf.co/nanonets/Nanonets-OCR2-3B
- Classical OCR (det/rec): https://hf.co/PaddlePaddle/PP-OCRv5_server_det and https://hf.co/PaddlePaddle/PP-OCRv5_server_rec
- OCR alt: https://hf.co/stepfun-ai/GOT-OCR-2.0-hf
Spaces for inspiration / UI prototypes:
- Document to Markdown (Docling showcase): https://hf.co/spaces/mozilla-ai/document-to-markdown
- Multimodal OCR aggregators: https://hf.co/spaces/prithivMLmods/Multimodal-OCR and https://hf.co/spaces/prithivMLmods/Multimodal-OCR3

Outputs (contracts):
- doc_pages.jsonl: per-page geometry + blocks + reading order
- ocr_text.txt + ocr_blocks.jsonl (word-level boxes)
- anchor_map.json: {{doc_id, page, block_id}} → canonical anchor ids
- quote_candidates.jsonl (unverified)
- quote_verified.jsonl (two-pass verified; diff=0) (QuoteLock)

P223) TRANSCRIPT/AUDIO CORE — ASR + DIARIZATION + ALIGNMENT → EVIDENCE ATOMS
Goal: convert hearing audio into time-anchored EvidenceAtoms + QuoteDB entries.
Suggested models:
- ASR: https://hf.co/openai/whisper-large-v3 (or turbo: /whisper-large-v3-turbo)
- Speaker diarization: https://hf.co/pyannote/speaker-diarization-3.1
- Forced alignment: https://hf.co/MahmoudAshraf/mms-300m-1130-forced-aligner
Outputs:
- transcript.vtt (time-coded)
- transcript.jsonl (segment-level with speaker labels)
- word_alignment.jsonl (optional)
- hearing_quote_candidates.jsonl → hearing_quote_verified.jsonl (QuoteLock path)

P224) LEGAL NER + ENTITY NORMALIZATION CORE — NAME/JUDGE/COURT/DOCKET EXTRACTOR
Purpose: structured extraction for graph nodes and contradiction detection (names, dates, docket nos, addresses, agencies).
Suggested model:
- English legal NER (spaCy transformer): https://hf.co/opennyaiorg/en_legal_ner_trf
Outputs:
- entities.jsonl (span + type + confidence + source anchor)
- entity_resolution.json (canonical forms + aliases)
Graph binding:
- Entities become nodes with provenance edges to Quote/EvidenceAtoms.

P225) RAG/EMBEDDING CORE v2 — HYBRID RETRIEVAL WITH GRAPH FILTERS (PRACTICAL DEFAULTS)
Embedding candidates:
- https://hf.co/sentence-transformers/all-MiniLM-L6-v2 (fast)
- https://hf.co/sentence-transformers/all-mpnet-base-v2 (stronger)
- https://hf.co/BAAI/bge-m3 (multilingual + hybrid)
- https://hf.co/jinaai/jina-embeddings-v3 (modern)
Index partitioning:
- V_AUTH (authority snapshot shards)
- V_ORDERS (orders + notices)
- V_EXHIBITS (exhibits, images, letters)
- V_TRANSCRIPTS (audio transcripts)
Reranking:
- optional cross-encoder lane (self-hosted) if needed; enforce “no invented facts” with quote gating.

P226) DATASETS FOR EVAL/FINETUNE (OPTIONAL, NOT REQUIRED FOR RUNTIME)
DocVQA datasets:
- https://hf.co/datasets/lmms-lab/DocVQA
- https://hf.co/datasets/vidore/docvqa_test_subsampled
Legal corpora (research / eval):
- https://hf.co/datasets/pile-of-law/pile-of-law
- LRAGE evaluation helpers (RAG eval for legal): https://hf.co/datasets/hoorangyee/pile-of-law-bm25 and https://hf.co/datasets/hoorangyee/pile-of-law-chunked
Policy:
- Datasets do not ship inside the 700MB release. Store as CAAV assets or remote pointers.

P227) “DENY-RESISTANT” VALIDATION CORE — PROCEDURAL ATTACK SIMULATOR (RED-TEAM)
Purpose: detect how filings can be denied procedurally (service, timeliness, prerequisites, format).
Inputs:
- vehicle candidate + service chain + deadlines + fees/bonds + controlling orders.
Outputs:
- VALIDATION_REPORT.json (PASS/FAIL per gate)
- DENIAL_CONVERSION_MAP.json (if denied, map reason→repair)
- WRIT_TRIGGER_REPORT.json (if adequate-remedy failure is arguable; flagged only, not executed)
Rule:
- no court-ready package unless validator PASS for core gates.

P228) GUI/UX CORE v2 — “OBSERVABLE LITIGATION OS”
Minimum non-negotiables (even in early builds):
- live run log (stage + current file)
- gate dashboard (Truth/Quote/Authority/PCW/PCG/Packaging)
- queue status + resume button
- artifact explorer (manifest driven)
Optional:
- Bloom-ready HTML export from Neo4j (viewer bundle) plus a lightweight embedded viewer.

P229) CI + REPRODUCIBLE BUILD + SIGNING HOOKS (WIN64 HARDENING PIPELINE)
Goals:
- reproducible builds (same inputs → same outputs)
- artifact provenance (build logs + SBOM)
- optional signing step hook (user-provided cert; not embedded)
Gates:
- lint + unit tests + smoke run on sample pack
- bundle integrity test (zip test + manifest match)
- “no external network” tests for runtime modules
Outputs:
- RELEASE_NOTES.md
- BUILD_ATTEST.json

P230) SCHEDULERS/WATCHERS v2 — SAFE AUTONOMY WITHOUT SURPRISE FILINGS
Watchers:
- Drive watcher (F:/ + gdrive mount) → new file events
- Authority snapshot watcher → effective-date drift detection
- Queue runner → resume incomplete stages
- Packaging runner → builds CyclePacks
Schedule:
- periodic runs allowed (e.g., 4/day) but only up to “PACKAGE” stage.
Hard stop:
- filing/service stages are never automatic; require explicit user command + PCG PASS.

P231) NEW CORE CATALOG (LATENT CORES ADDED THIS CYCLE)
- MASTER_STACK_ASSEMBLER_CORE (pack fusion)
- RUN_REPLAYABILITY_CORE (event log + queue)
- PERMISSION_MODEL_V2 (mutation tickets)
- SCHEMA_GOVERNANCE_V2 (migrations + contracts)
- CAAV_ASSET_VAULT (packfiles + hydrate)
- PO_LEDGER_COUPLING_V2 (PCW enforcement)
- DOCVISION_LANES (OCR/doc QA)
- TRANSCRIPT_PIPELINE (ASR/diarization/align)
- LEGAL_NER_NORMALIZER (entity layer)
- RAG_HYBRID_V2 (partitioned indexes)
- DENY_RESISTANT_REDTEAM (procedural denial simulator)
- REPRO_BUILD_HARDENING (CI + attest)
- SAFE_AUTONOMY_SCHEDULERS (watchers)

P232) NEXT EXPONENTIAL JUMPS (QUEUED CANDIDATES, SUBJECT TO DGC2)
(These are proposals; acceptance depends on DGC2 scoring in the next cycle.)
- Formal “Record Spine Builder” that derives ROA/entry dates → deadlines automatically (requires docket input).
- Automated “Form Field Map” compiler (SCAO PDFs → fill map) with overlay audit.
- Witness profile engine (credibility/contradictions anchored to quotes).
- Multi-case partitioned graphs (per case + global authority graph) with crosslinks.

END APPENDIX v2026-01-18.22

===============================================================================
APPENDIX v2026-01-18.23 — EXPONENTIAL GROWTH BLOCK (P233–P270)
Invariant: append-only; no destructive edits; every new capability binds to DGC2 + PCW + replayability.
===============================================================================

P233) MODEL REGISTRY + LICENSE GOVERNOR (MRLG) — “ONLY APPROVED MODELS/SETS ENTER PRODUCTION”
Intent: keep the system “free/open/self-hosted” while preventing silent license traps and ensuring reproducible, auditable model usage.
Inputs:
- Candidate repos (HF models/datasets/spaces), local model files, Ollama manifests, gguf files, etc.
Outputs (required):
- MODEL_REGISTRY.json (append-only; one entry per model version)
- DATASET_REGISTRY.json (append-only; one entry per dataset version)
- LICENSE_RISK_REPORT.md (generated per cycle; BLOCKER/WARN/INFO)
- MODEL_LOCKFILE.json (the exact set of models allowed in CURRENT)
Automation:
- For each model/dataset candidate:
  - capture repo_id, commit hash or “revision tag,” task, framework, size, expected VRAM/RAM envelope
  - capture license tag (from HF metadata), and enforce policy
  - assign “AllowedUse” class:
    A) PROD_OK (permissive; supports commercial distribution)
    B) PROD_OK_WITH_NOTICE (permissive but requires notices/attribution)
    C) INTERNAL_ONLY (restricted; allowed for private analysis only; not shipped)
    D) BLOCKED (disallowed)
License policy (default; tunable):
- PROD_OK examples: MIT, Apache-2.0, BSD, ISC
- PROD_OK_WITH_NOTICE: MPL-2.0, LGPL (requires dynamic link style compliance in some cases)
- INTERNAL_ONLY: CC-BY-NC-*, CC-BY-NC-SA-* (noncommercial), “research only,” custom nonredistribution terms
- BLOCKED: unknown license, no license, or terms incompatible with redistribution
Verification:
- CI gate: cannot build “RELEASE” if any model/dataset is BLOCKED; cannot ship PROD bundle if any dependency is INTERNAL_ONLY.

Concrete HF anchors discovered (links for registry population; versions must be locked in registry):
DocQA:
- https://hf.co/impira/layoutlm-document-qa (license: MIT)
- https://hf.co/naver-clova-ix/donut-base-finetuned-docvqa (license: MIT)
OCR / Document parse:
- https://hf.co/rednote-hilab/dots.ocr (license: MIT)
- https://hf.co/ChatDOC/OCRFlux-3B (finetune on Qwen2.5-VL; verify base model license in registry)
- https://hf.co/stepfun-ai/GOT-OCR-2.0-hf (license: Apache-2.0)
- https://hf.co/PaddlePaddle/PP-OCRv5_server_det (license: Apache-2.0)
- https://hf.co/PaddlePaddle/PP-OCRv5_server_rec (license: Apache-2.0)
ASR / diarization / alignment:
- https://hf.co/openai/whisper-large-v3 (see HF license field; lock and comply)
- https://hf.co/openai/whisper-large-v3-turbo (see HF license field; lock and comply)
- https://hf.co/pyannote/speaker-diarization-3.1 (license: MIT; NOTE: pyannote models sometimes require accepting model terms on HF—treat as INTERNAL_ONLY unless acceptance+redistribution allowed)
- https://hf.co/MahmoudAshraf/mms-300m-1130-forced-aligner (license: Apache-2.0)
Legal dataset warning example:
- https://hf.co/datasets/pile-of-law/pile-of-law (license: CC-BY-NC-SA-4.0 => INTERNAL_ONLY by default; do not ship; do not mix into commercial training without legal review)

P234) LOCAL LLM ROUTER v3 — “SELF-HOST ONLY, TOOL-GATED”
Intent: route reasoning/drafting tasks to local models without granting mutation powers and without leaking sensitive data.
Core requirements:
- Router must support: llama.cpp server, Ollama, vLLM, local transformers pipelines (offline).
- Router emits: MODEL_INVOCATION events (inputs redacted if required), outputs, and confidence metadata.
Permission model:
- Router runs under CAP_PROPOSE only; outputs are proposals that must pass VALIDATOR_ROLE and PCW/PO gates.
- Any attempt to “commit graph changes” from LLM outputs is BLOCKED unless a Mutation Ticket exists.
Routing lanes:
- Lane A (Light): summarization, indexing assistance, tag proposals
- Lane B (Evidence-bound): draft text that references EvidencePins and AuthorityPins only
- Lane C (Strict QuoteLock): only uses verified quote ledger; cannot introduce new quotes
- Lane D (Red-Team): produces denial/attack hypotheses; must remain labeled as adversarial simulation
Artifacts:
- LLM_ROUTER_CONFIG.json (allowed models per lane)
- PROMPT_TEMPLATES/ (versioned)
- OUTPUT_SANITIZER_RULES.yaml (redaction rules)

P235) EVALUATION HARNESS v1 — “MEASURE UPWARD MOVEMENT, NOT VIBES”
Intent: quantify whether each cycle improved the system; feed DGC2 with real metrics.
Metrics families:
- Extraction accuracy: quote verification pass rate; OCR confidence distribution; layout parsing error rate
- Retrieval quality: top-k hit rate on known queries; rerank delta; false-positive citations blocked
- Draft quality: PO closure rate; validator pass rate; denial-simulation survival
- Operational: mean time to ingest; mean time to rebuild; crash recovery success rate
Artifacts:
- METRICS_TIMESERIES.jsonl (append-only)
- EVAL_REPORT.md (per cycle)
- BENCHMARK_CASES/ (small, synthetic or user-supplied; never includes restricted content in public repos)
Dataset lane:
- DocVQA evaluation sources:
  - https://hf.co/datasets/lmms-lab/DocVQA (Apache-2.0)
  - https://hf.co/datasets/vidore/docvqa_test_subsampled_beir (check tags; treat as INTERNAL_ONLY until confirmed)
Rule: evaluation datasets are allowed even if INTERNAL_ONLY provided they are not redistributed with releases.

P236) DOCVISION CORE v2 — “OCR + LAYOUT + TABLES + PDF→MD”
Intent: extract court orders, notices, exhibits, and forms into trustworthy structured text with stable pinpoints.
Lane ladder (DGC2 picks by cost/benefit):
- Tier 0: native text extract (fast; fallback: OCR if low text density)
- Tier 1: classical OCR (PaddleOCR v5 det+rec)
- Tier 2: VLM OCR (OCRFlux-3B, dots.ocr, GOT-OCR-2.0) for hard scans, forms, tables
- Tier 3: DocQA (LayoutLM/Donut) to answer structured questions over page images
Outputs (mandatory):
- EXTRACTED_TEXT/ (per page shard)
- PAGE_GEOMETRY.json (page boxes, line boxes)
- TABLES.json (when detected)
- QUOTE_CANDIDATES.jsonl (with page coords)
- QUOTE_VERIFIED.jsonl (after QuoteLock verifier)
Verifier rules:
- Two-pass extraction for any quote promoted to VERIFIED:
  pass1: OCR/layout model extraction
  pass2: independent extractor (alternate OCR or pdf text extractor)
  diff must be 0; else quote remains CANDIDATE with “VERIFY_FAIL_SIGNATURE”.

P237) TRANSCRIPT + AUDIO PIPELINE v2 — “TIMELINE-ALIGNED, SPEAKER-ATTRIBUTED QUOTES”
Intent: convert recordings into admissible-ready references (without fabricating anything).
Stages:
1) Ingest audio/video; compute fingerprints; store pointer/assetptr if large
2) ASR transcription (Whisper)
3) Diarization (pyannote; if terms restrict redistribution, run local and mark internal)
4) Forced alignment (MMS aligner) to pin word timestamps
5) Segmenter: emits time-coded QuoteCandidates linked to timeline events
Artifacts:
- TRANSCRIPT.raw.json (model output)
- TRANSCRIPT.cleaned.txt (no editorializing; corrections logged)
- DIARIZATION.rttm
- ALIGNMENT.json (word-level)
- AUDIO_QUOTE_LEDGER.jsonl (QuoteLock pipeline applied to audio: time pins + source file)
Gate:
- No “speaker attribution” is upgraded to VERIFIED unless diarization confidence >= threshold and/or independent corroboration exists.

P238) REDACTION + PRIVACY CORE — “SAFE SHARING WITHOUT LOSING EVIDENCE VALUE”
Intent: produce court-safe and public-safe variants of the same bundle.
Outputs:
- REDACTION_MAP.json (what was redacted, why, where)
- PUBLIC_PACK/ (redacted exhibits and narrative)
- COURT_PACK/ (full record, minimally redacted per court rules)
Policies:
- Detect: SSN, DOB, minors’ names, addresses (configurable), medical data
- Redaction must be non-destructive: keep originals; store derived redacted copies
- Log every redaction decision; never silently alter originals

P239) EXHIBIT FACTORY v3 — “COVER PAGES, LABELS, BATES, PDF/A, AND INDEX”
Intent: produce a coherent exhibit binder with consistent stamping and indexing.
Capabilities:
- Exhibit cover page generator (caption, exhibit id, description, source pointer)
- Color-coded labels (plaintiff yellow / defendant blue)
- Bates numbering (optional; if used, include mapping ledger)
- PDF/A conversion lane (where feasible)
- Exhibit index with page counts, titles, and source integrity keys
Outputs:
- EXHIBITS/EXH_###.pdf
- EXHIBITS/index.csv
- EXHIBITS/bates_map.csv (if bates)
- EXHIBITS/build_log.txt

P240) MI FORMS OVERLAY FACTORY — “FORMS-FIRST, FIELD-VALIDATED”
Intent: fill SCAO/MC/FOC forms with graph-sourced fields and validate completeness.
Key primitives:
- FORM_CATALOG: each form has {form_id, revision_date, required_fields, field_types, dependencies}
- FIELD_MAP: mapping from graph nodes to form fields
- FORM_AUDIT: a per-run record of what populated each field and from where
Gates:
- Any form output is BLOCKED unless required fields are populated or marked “intentionally blank” with justification.
Outputs:
- FORMS/filled/<form_id>_<run_id>.pdf
- FORMS/audit/<form_id>_<run_id>.json

P241) RECORD SPINE BUILDER v1 — “ROA/DOCKET → DEADLINES → SERVICE/NOTICE → ORDERCHAIN”
Intent: build the procedural backbone so everything else can hang off it.
Inputs:
- ROA exports, docket PDFs, e-filing receipts, stamped orders, hearing notices, proofs of service
Outputs:
- DOCKET_NORMALIZED.csv (event rows)
- ORDERCHAIN.json (orders linked by modification/supersession)
- SERVICECHAIN.json (service events linked to filings/orders)
- DEADLINES.json (computed deadlines with authority references)
Validation:
- Every docket row must point to a file+pin or be explicitly “missing” with acquisition plan.
- Deadlines must include AuthorityPins (from snapshot) once authority is ingested.

P242) DEADLINE ENGINE v3 — “RULE-BOUND, SNAPSHOT-BOUND”
Intent: compute deadlines without guessing; anything uncertain becomes a PO.
Rules:
- No deadline is “court-ready” unless:
  - triggering event is pinned to record (docket entry/order)
  - authority basis is pinned to snapshot (rule/statute/order)
  - computed date is explained (calendar rules: business days vs calendar days)
Outputs:
- DEADLINES/ledger.jsonl (append-only)
- DEADLINES/alerts.ics (operator reminders; optional)
- DEADLINES/validator_report.md

P243) SERVICE/NOTICE VALIDATOR v2 — “PROCEDURAL ATTACK SURVIVOR”
Intent: preflight service/notice issues that are common denial vectors.
Outputs:
- SERVICE_NOTICE_REPORT.json (flags: defective service, short notice, missing proof)
- FIXLIST.md (what to cure, how)
- PO updates (service-related POs opened/updated)

P244) DENIAL CONVERSION CORE v2 — “TURN ‘NO’ INTO A PROCEDURAL WIN”
Intent: structure every denial into: record evidence → preserved error → next vehicle.
Outputs:
- DENIAL_CONVERSION_MAP.json (per denial: what happened, why it’s wrong/unsupported, what to do next)
- ADEQUATE_REMEDY_ANALYSIS.json (trial vs COA original action considerations; authority pins required)
- WRIT_TRIGGER_REPORT.json (only if conditions met; otherwise remains empty)

P245) APPELLATE TRACK BUILDER v1 — “APPEAL/SUPERINTENDING CONTROL PACKETS (BLUEPRINT)”
Intent: generate the internal pack skeleton (not court filing) with record pins and vehicle map.
Outputs:
- APPELLATE_PACK/ (draft index, record citations map, issue list, preservation map)
Gates:
- No claims about legal standards or holdings without authority pins.
- QuoteLock applies to any quotations in appellate narratives.

P246) JTC TRACK BUILDER v1 — “MISCONDUCT NARRATIVE WITH PINS”
Intent: produce a JTC-ready evidence map: quote→canon/rule proposition→pinpoint.
Outputs:
- JTC_PACK/ (timeline, quote ledger, exhibit map, allegation/proposition map)
Gates:
- Only verified quotes; any disputed remains clearly labeled and separate.

P247) ENTITY RESOLUTION CORE v2 — “WHO IS WHO (PEOPLE/ORGS/LLCS)”
Intent: disambiguate names and entities across cases and records.
Outputs:
- ENTITY_REGISTRY.json (stable IDs, aliases, confidence)
- RESOLUTION_EVENTS.jsonl (append-only)
Method:
- deterministic string normalization + evidence-backed aliasing
- graph edges: SAME_AS (only when justified), POSSIBLY_SAME_AS (default)

P248) CORPORATE STRUCTURE / VEILPIERCER LANE (MEEK1 POWER CORE)
Intent: map park entity → parent entities → management → billing systems → registered agents, using evidence + public records (authority pins required for legal claims).
Outputs:
- ORG_GRAPH/ (nodes: entities, roles, contracts, invoices, communications)
- CLAIMS_CANDIDATE_GRID.csv (elements vs facts vs evidence pins; no claims without pins)

P249) UI COMMAND CENTER v2 — “ONE SCREEN FOR THE WHOLE OS”
Intent: provide operator-level visibility and control without sacrificing auditability.
Must-have panes:
- Status: current run, queue, errors, fixlist
- Search: evidence + quotes + authority
- Timeline: bitemporal + orderchain overlay
- Graph: Neo4j Bloom + HTML explorer export
- Drafts: generated packets, PO status, PCG gate status
- Assets: hydration status, missing pointers, vault health
Constraints:
- UI triggers only create jobs; jobs execute through orchestrator; orchestrator writes logs/events.

P250) ORCHESTRATION OPTIONS (FREE/OPEN)
Intent: run pipelines reliably without paid SaaS.
Options (choose one; all acceptable):
- “Lightweight”: internal Python orchestrator + SQLite queue + Windows Task Scheduler
- “Workflow engine”: Prefect OSS or Dagster OSS (self-hosted); all runs local; no cloud dependency
Invariant:
- Orchestrator must emit event log and must be resumable after crash.

P251) SELF-HOSTED RUNNERS + BUILD FARM (FREE)
Intent: automate builds/tests without external cost caps.
Blueprint:
- Self-hosted GitHub Actions runner on Windows box
- Nightly reproducible build + smoke tests + bundle export
- Offline-safe mode: no internet required for runtime; dependency cache allowed for builds
Outputs:
- BUILD_ARTIFACTS/ (signed/unsigned exe, SBOM, attestations, logs)

P252) SECURITY CORE — “DEPENDENCY ALLOWLIST + OFFLINE DEFAULT”
Intent: reduce supply-chain risk.
Controls:
- dependency allowlist (hash-locked)
- block arbitrary code execution from downloaded scripts
- secrets: env-only, never committed
- sandbox external parsers (PDF parsers can crash; isolate)

P253) EXTENSION SDK v1 — “PLUGINS, NOT CHAOS”
Intent: new modules can be added without breaking invariants.
Plugin contract:
- module.json (name, version, inputs, outputs, caps needed)
- validate.py (preflight checks)
- run.py (idempotent execution)
- tests/ (smoke)
Registry:
- MODULE_REGISTRY.json (append-only)
Governor:
- refuses to run modules missing declared outputs or missing caps.

P254) CONVERGENCE LOOP v2 — “STOP WHEN GAINS FLATTEN, NOT WHEN YOU’RE TIRED”
Intent: formal “continue” semantics.
Per cycle:
- harvest deltas
- propose top N expansions
- accept only those that raise DGC2 score or close POs
- emit “diminishing returns” report when improvement < eps for K cycles
Output:
- CONVERGENCE_REPORT.md

P255) MINIMUM REQUIRED ARTIFACT SET (PER RUN)
Mandatory:
- CASE_STATE.md
- RUN_EVENTLOG.jsonl
- JOB_QUEUE.sqlite (or export)
- MANIFEST/index.json
- PO_LEDGER.jsonl + PO_STATE.json
- QUOTE_LEDGER (candidate + verified)
- DEADLINES ledger
- VALIDATION_REPORT.json + FIXLIST.md
- DGC artifacts (scorecard + decision trace)

P256) BACKUP/RESTORE + DISASTER RECOVERY (DR)
Rules:
- backups must be testable; restoration must be scripted
- vault + graph + manifests must restore consistently
Artifacts:
- DR_RUNBOOK.md
- BACKUP_CHECKPOINTS.csv
- RESTORE_TEST_REPORT.md

P257) TEST STRATEGY v2 — “GOLDEN FILES + PROPERTY TESTS”
- golden-file tests for manifests and deterministic zips
- PDF render tests (hash+page count+font detection)
- quote verifier tests (must reject mismatches)
- migration tests (apply+rollback where supported)

P258) PACKAGING v3 — “700MB GUARANTEE WITH PATCH MODE”
- always build FULL + CORE + LITE packs
- auto-split large zips into parts (simple numbered parts)
- always ship world-first builder script to reconstruct locally

P259) ROADMAP: THE NEXT 3 “EXPONENTIAL JUMPS”
Jump 1: “Authority Snapshot Builder” + rule miner + proposition library → closes authority pins at scale.
Jump 2: “Record Spine Builder” from ROA/dockets → deadlines/service/orderchain → makes appellate posture deterministic.
Jump 3: “Forms Overlay Factory” + field map compiler → court-ready packet generation becomes routine.

P260–P270) RESERVED PAGES FOR NEXT CYCLE ACCEPTANCE
(This region intentionally reserved to accept DGC2-scored expansions without renumber churn.)
===============================================================================
END APPENDIX v2026-01-18.23
===============================================================================

===============================================================================
APPENDIX v2026-01-18.24 — HIGH-SIGNAL Δ PACK (P271–P330)
Theme: “Reduce unknown-unknowns.” Add missing governance + integration contracts so future modules land cleanly.
===============================================================================

P271) HF DISCOVERY INTAKE (MODELS/DATASETS/SPACES) — “INSPIRATION ≠ DEPENDENCY”
Purpose: convert discovery (HF repos/spaces/datasets) into auditable, license-safe, reproducible candidates without introducing cloud-runtime coupling.
Rule: HF Spaces are NEVER a runtime dependency. They are “idea probes.” Runtime remains self-hosted only.

HF Spaces discovered (candidates to inspect, NOT dependencies):
- PDF→MD/JSON extraction idea: https://hf.co/spaces/opendatalab/MinerU  (Space: “convert PDF to Markdown and JSON”)
- PDF parser demo: https://hf.co/spaces/chunking-ai/chunking-pdf-parser
- Multi-Modal OCR demos / model collections:
  - https://hf.co/spaces/merterbak/DeepSeek-OCR-Demo
  - https://hf.co/spaces/prithivMLmods/Multimodal-OCR
  - https://hf.co/spaces/prithivMLmods/Multimodal-OCR3
- OCR/vision demo: https://hf.co/spaces/PaddlePaddle/PaddleOCR-VL_Online_Demo
- PDF Q/A UI demo: https://hf.co/spaces/cvachet/pdf-chatbot

Policy:
- Any “Space” yields: (a) repo link(s), (b) technique notes, (c) local reimplementation plan, (d) LICENSE check. No code is imported into CURRENT until MRLG approves.

P272) MODEL REGISTRY + LICENSE GOVERNOR (MRLG) — “PROMOTE ONLY WHEN LOCKED”
Upgrade:
- Registry must record: repo_id, revision, license tag, size, intended lane, allowed distribution class, and “terms acceptance required?” flag.
- Blocker: any model requiring interactive “Accept terms” is INTERNAL_ONLY by default; never shipped in redistributable bundles.
- Enforce a “two-key” rule to promote to PROD_OK:
  (1) permissive license (policy-defined) AND (2) no extra-use constraints (acceptance gates, noncommercial clauses, private-only clauses).

High-signal model anchors from HF search (lock by revision in registry):
DocQA:
- LayoutLM DocQA: https://hf.co/impira/layoutlm-document-qa  (license tag in HF: MIT)
- Donut DocVQA: https://hf.co/naver-clova-ix/donut-base-finetuned-docvqa  (license tag: MIT)
OCR/VLM OCR:
- GOT-OCR 2.0: https://hf.co/stepfun-ai/GOT-OCR-2.0-hf (license tag: Apache-2.0)
- PP-OCR v5 det: https://hf.co/PaddlePaddle/PP-OCRv5_server_det (license tag: Apache-2.0)
- PP-OCR v5 rec: https://hf.co/PaddlePaddle/PP-OCRv5_server_rec (license tag: Apache-2.0)
Datasets (evaluation lane):
- DocVQA eval suite dataset: https://hf.co/datasets/lmms-lab/DocVQA (license tag: Apache-2.0)
- DocVQA subsampled beir: https://hf.co/datasets/vidore/docvqa_test_subsampled_beir (verify license tags before use)

License risk example (do not ship; internal evaluation only unless cleared):
- Pile of Law: https://hf.co/datasets/pile-of-law/pile-of-law (commonly tagged CC-BY-NC-SA; treat as INTERNAL_ONLY unless policy updated)

P273) “OFFLINE-BUILD, OFFLINE-RUN” DOUBLE GATE
Motivation: protect reliability, privacy, and court defensibility.
Rules:
- BUILD can optionally download dependencies; RUN must function with “no internet” mode enabled.
- Any module requiring network must declare it (ModuleContract.network=true) and provide offline fallback or hard BLOCK unless operator overrides.
Artifacts:
- OFFLINE_RUN_PROOF.md (what was tested offline)
- DEP_CACHE_RECEIPT.json (what was fetched at build-time)

P274) MODULE CONTRACT v2 — “PLUGINS CAN’T CHEAT”
Every module MUST ship:
- module.json: {name,ver,inputs,outputs,caps,network,determinism,side_effects,storage_roots}
- validate.py: checks prerequisites + produces FIXLIST on failure
- run.py: idempotent execution; emits events; never mutates canonical state without Mutation Ticket
- outputs must be enumerated and verifiable (existence + size + schema validation)
Governor enforcement:
- If module declares output but fails to emit it => BLOCKER + regression signature.

P275) MUTATION TICKETS v1 — “VALIDATORS OWN STATE”
Ticket format:
- MUT_TICKET.json: {ticket_id,scope,allowed_ops,expires,validator_id,run_id,checksum}
Only Governor can commit canonical writes (graph, schema state, PO state, authority snapshot).
LLM outputs can propose patches but never receive tickets.

P276) “GRAPH WRITE PROTOCOL” (GWP) — “PROPOSE → DIFF → APPLY”
Cypher commit discipline:
- proposals as Cypher patch files + expected row counts + safety predicates
- dry-run query to estimate impact
- apply only with ticket
Artifacts:
- GRAPH_PATCHES/<run_id>/*.cypher
- GRAPH_APPLY_REPORT.json (expected vs observed counts)
- GRAPH_ROLLFORWARD_PLAN.md (no silent rollback; rollforward-only repairs)

P277) NEO4J BOOTSTRAP CORE — “CONSTRAINTS FIRST”
Migration invariants:
- Always apply constraints/indexes before bulk import.
- Keep schema version nodes in graph: :SchemaVersion {version,checksum,applied_ts,run_id}
- Block graph writes if schema missing required constraints (preflight gate).

P278) “BLOOM THEME PACK” LANE — “UI IS A PRODUCT SURFACE”
Deliverables:
- Bloom style JSON (node labels, colors, caption rules)
- Node popup schema (what fields render and in what order)
- Query presets (“brains/nucleuses”):
  - Courts/Authorities Brain
  - Case Record Spine Brain
  - Evidence/Exhibits Brain
  - Violations/Denial Conversion Brain
  - Actionability/Next Steps Brain
Rules:
- UI presets are generated from registry/labels; do not hand-edit without recording.
Artifacts:
- UI/BLOOM/theme.json
- UI/BLOOM/popup_schema.json
- UI/BLOOM/queries.cypher

P279) PDF→MD/JSON “LOCAL REBUILD” PLAN (MinerU-inspired)
Goal: replicate “PDF to Markdown + JSON” extraction locally, with QuoteLock compatibility.
Local pipeline:
- pdf ingestion → page images (if scanned) → OCR lane selection → structure detection → markdown builder
- output includes page anchors + geometry so every quote can be pinned.
Hard gate:
- any extracted quote promoted to VERIFIED must pass QuoteLock verifier (two independent extractors; diff=0).

P280) “TABLES + FORMS” STRUCTURE CORE
Court evidence often lives in tables (billing ledgers, financial disclosures, school records).
Outputs:
- TABLES.json with cell coords and normalized values
- FORM_FIELDS.json for detected field/value pairs with bounding boxes
Validation:
- numeric normalization logs (no silent rounding)
- provenance per cell: {source,page,coords,extractor}

P281) DATA QUALITY GOVERNOR (DQG)
Rules:
- Every extracted artifact has a “confidence + failure signature.”
- Governor prevents low-confidence extraction from being treated as fact without escalation to PO.
Artifacts:
- DQ_REPORT.json
- LOW_CONFIDENCE_QUEUE.jsonl (follow-up jobs)

P282) QUOTELOCK v3 — “VERIFY THEN USE”
Upgrade:
- Verified quote record must include: method1+method2 outputs, diff proof, and a stable “quote_id”.
- Any narrative generator MUST refuse to quote unless quote_id exists in QUOTE_VERIFIED ledger.

P283) AUTHORITY SNAPSHOT “DIFF & DRIFT” CORE
Even with MI-only lock, authorities change.
Controls:
- snapshot version has effective date and source URLs
- weekly diff jobs compare snapshot to refreshed sources; diffs become proposals (never auto-committed)
Artifacts:
- AUTH_SNAPSHOT_DIFF.json
- AUTH_SNAPSHOT_CHANGELOG.md

P284) SERVICE/NOTICE + DEADLINES “EXPLAINER MODE”
To be deny-resistant, computed deadlines must be explainable.
Each deadline entry includes:
- trigger event pin
- governing authority pin
- counting method (calendar vs business days)
- computed date
- “uncertainty flag” if any input missing
Artifacts:
- DEADLINES/explained_deadlines.md

P285) “FIXLIST AS PRODUCT” CORE
Fixlists are actionable work orders.
Rules:
- every BLOCKER must emit a fixlist item with:
  (a) exact missing input
  (b) where to find it
  (c) what artifact to produce
  (d) what PO it closes
Artifacts:
- FIXLIST.md
- FIXLIST.json (machine-readable)
- FIXLIST_TO_QUEUE.json (auto-enqueue follow-ups)

P286) “PACK TRIAD” RELEASE DISCIPLINE (FULL/CORE/LITE)
To preserve size cap and deliverability:
- FULL: source + tools + superpins + manifests + pointers (no large assets)
- CORE: minimal runnable + builder + policies + schemas
- LITE_OUTPUTS: run outputs only (no source)
All packs include builder scripts and receipts.

P287) “SPLIT PACK” FALLBACK (DETERMINISTIC PARTS)
If any zip exceeds platform limits:
- split into .part.000/.001/... with manifest mapping
- include rejoin instructions and a rejoin script.

P288) “WORLD-FIRST BUILDER” REQUIREMENT (DURABLE RECOVERY)
Every cycle must keep a local builder that can:
- reconstruct FULL pack from CURRENT + VERSIONS + PATCHES + pointers
- run integrity checks
- export durable zip to user-controlled storage (e.g., rclone remotes)

P289) SECURITY: PARSER ISOLATION
PDF parsers and OCR libs can be crashy.
Mitigation:
- isolate extraction in a subprocess
- enforce timeouts
- capture crash signatures to LOW_CONFIDENCE_QUEUE rather than corrupting run
Artifacts:
- PARSER_CRASH_REPORT.jsonl

P290) EXPONENTIAL NEXT ACCEPTANCE SET (DGC2 CANDIDATES)
Candidates staged for next cycle (must pass DGC2 scoring + license governor):
- Local “PDF→MD” module modeled after MinerU’s output contract (not dependent on Space)
- GOT-OCR lane integration module (if license+terms OK)
- Donut/LayoutLM docQA lane modules for “structured question answering” over orders
- Evaluation harness that tracks QuoteLock pass rate and retrieval hit rates over time

P291–P330) RESERVED FOR NEXT HIGH-SIGNAL Δ ACCEPTANCE
This region stays reserved to accept only the highest DGC2-score candidates without renumber churn.
===============================================================================
END APPENDIX v2026-01-18.24
===============================================================================

===============================================================================
APPENDIX v2026-01-18.25 — HIGH-SIGNAL Δ PACK (P331–P395)
Theme: “Turn discovered capability into enforceable, local-only modules.” All deltas bind to MRLG + ModuleContract v2 + MutationTickets + QuoteLock.
===============================================================================

P331) HF DISCOVERY → LOCAL MODULE PIPELINE (“IDEA PROBE TO SHIPPABLE CORE”)
Rule: HF Spaces are never runtime deps. They are technique probes. Every Space yields:
(1) Technique Notes (what it does), (2) Candidate local modules, (3) License/governor check, (4) Deterministic local test harness, (5) Integration points (events, POs, manifests).
Discovered Spaces (probe-only; capture in MRLG):
- MinerU (PDF→Markdown+JSON concept): https://hf.co/spaces/opendatalab/MinerU (Space; updated 2025-12-19)
- chunking-pdf-parser (PDF parse demo): https://hf.co/spaces/chunking-ai/chunking-pdf-parser (Space; updated 2025-05-27)

P332) MRLG UPGRADES: “LICENSE TAGS ARE NOT ENOUGH”
Enhancement:
- Registry must store BOTH: HF license tag AND redistribution constraints/terms acceptance flags.
- Default rule: if the model requires click-through acceptance or nonstandard terms => INTERNAL_ONLY unless explicitly cleared.
Concrete model anchors with license tags (lock by revision in registry):
- GOT-OCR 2.0 (apache-2.0): https://hf.co/stepfun-ai/GOT-OCR-2.0-hf
- Donut DocVQA (mit): https://hf.co/naver-clova-ix/donut-base-finetuned-docvqa
- LayoutLM DocQA (mit): https://hf.co/impira/layoutlm-document-qa
- dots.ocr (mit; custom_code flagged in tags => governance must sandbox execution): https://hf.co/rednote-hilab/dots.ocr
- PP-OCR v5 det/rec (apache-2.0): https://hf.co/PaddlePaddle/PP-OCRv5_server_det | https://hf.co/PaddlePaddle/PP-OCRv5_server_rec
- whisper-large-v3 (apache-2.0): https://hf.co/openai/whisper-large-v3
Notes:
- OCRFlux-3B is a finetune on Qwen2.5-VL-3B-Instruct; MRLG must record BOTH the finetune and base model constraints: https://hf.co/ChatDOC/OCRFlux-3B

P333) “DOC PARSE LOCAL” MODULE SET (PDF→MD+JSON) — CONTRACT-FIRST
Goal: local, deterministic conversion of PDFs into:
- Markdown (human view)
- JSON structure (machine view; pages/blocks/lines/tables/fields)
- Geometry (for pinpoints)
- Quote ledgers (candidate + verified)
Module set (each is a ModuleContract v2 plugin):
A) pdf_ingest: classify PDF (text-native vs scanned), compute text density, shard pages
B) pdf_text_extract: native text extraction with page anchors
C) pdf_page_render: rasterize pages deterministically (dpi, colorspace fixed)
D) ocr_lane: choose Tier 1/2 OCR based on scan hardness + DQG
E) layout_lane: detect blocks/lines/tables/forms; emit geometry
F) md_builder: assemble markdown with page/line anchors
G) json_builder: produce structured JSON with stable ids
H) quotelock_verify: verify quotes (two independent extractors; diff=0)
Artifacts:
- EXTRACT/pdf/<doc_id>/{md,json,geometry,quotes_candidate,quotes_verified}
- DQ_REPORT.json (confidence, failure signatures)
- RUN_EVENTLOG.jsonl entries for every page shard

P334) DOCVISION LANE MAP v3 (“FAST FIRST, VLM WHEN WORTH IT”)
Tier policy:
- Tier 0: native text extraction (fast) → if low text density => Tier 1+
- Tier 1: PP-OCR v5 det/rec (classic OCR; stable + fast)
- Tier 2: GOT-OCR-2.0 for hard scans/tables (higher compute; best-effort)
- Tier 3: dots.ocr for rich layout/table/formula (governed: sandbox custom code; pin versions)
- Tier 4: DocQA (Donut/LayoutLM) for “question-driven” extraction (e.g., “what is the hearing date?”)
All Tier ≥2 results MUST be routed through QuoteLock before being used as “verified quotes.”

P335) DOCQA “STRUCTURED QUESTION SETS” (FOR ORDERS/NOTICES)
Purpose: convert orders/notices into normalized fields with high confidence.
Question templates (examples; must be auditable):
- “Hearing date/time/location”
- “Judge name”
- “Relief granted/denied”
- “Compliance requirements”
- “Deadlines”
Outputs:
- ORDER_FIELDS.json (with source page coords + extractor lane + confidence)
Gate:
- If confidence < threshold or extraction mismatch across lanes => field remains DISPUTED and opens PO.

P336) “SCAO FORMS CATALOG + FIELD MAP COMPILER” (FORMS-FIRST OPERATIONALIZED)
Core:
- Maintain FORM_CATALOG entries with revision dates, required fields, and validation rules.
- Compile PDF field maps (AcroForm) and DOCX field placeholders into a uniform FormField schema.
Outputs:
- FORMS/catalog.json
- FORMS/field_maps/<form_id>.json
- FORMS/validators/<form_id>.jsonschema
- FORMS/audit/<run_id>/<form_id>.json (what filled what, from which graph nodes/evidence pins)

P337) VEHICLEMAP ENGINE v2 (“RELIEF→FORM→RULE→PO GRID”)
Produces:
- VEHICLE_MAP.json (per target relief)
- ELEMENT_GRID.csv (elements x evidence pins)
- PO templates (per element)
Tie-in:
- filing drafts are blocked unless mandatory POs are SATISFIED.

P338) AUTHORITY SNAPSHOT BUILDER v3 (“DIFF/DRIFT + PROPOSITION SHARDS”)
Outputs:
- AUTH_SNAPSHOT/index.json (refs w/ eff date)
- PROP_LIBRARY/*.jsonl (AuthorityTriples: proposition→authority→pinpoint)
- AUTH_DIFF/weekly/*.json (diff proposals)
Governance:
- no auto-commit to snapshot; diffs become proposed changes requiring validator ticket.

P339) CITATION/PINPOINT ENGINE (“PAGE/LINE/BATES/TIME NORMALIZER”)
Problem: pinpoints vary by medium.
Solution:
- Unified Pin schema:
  - FactPin: {path, page, line, bbox?, bates?, time?, offset?, integrity_key}
  - LawPin: {source_id, section, subsection, eff_date, url?, edition?}
Outputs:
- PINS/index.json
- PIN_AUDIT.jsonl (append-only)

P340) “RECORD SPINE v2” — ORDERCHAIN + DEADLINES + SERVICECHAIN AS A SINGLE BACKBONE
Enhancement:
- Order events link to deadlines and service requirements.
- Every computed deadline carries an “explainer block.”
Artifacts:
- RECORD_SPINE/orderchain.json
- RECORD_SPINE/servicechain.json
- RECORD_SPINE/deadlines.json
- RECORD_SPINE/explainers.md
Gate:
- any uncertain trigger or authority basis => opens PO and does not become court-ready.

P341) “DENIAL SIMULATOR v2” — PROCEDURAL ATTACK SURFACE MAP
Outputs:
- DENIAL_SURFACE_MAP.json (attack vectors: service, jurisdiction, timeliness, form completeness, evidence admissibility)
- FIXLIST.md (cures)
- DENIAL_CONVERSION_MAP.json (rollforward plans; no rollback)

P342) “LLM PROMPT GOVERNOR v2” — PROPOSALS ONLY, QUOTE-GATED
Controls:
- Forbid unverified quotes in court-ready outputs
- Forbid legal propositions without authority pins
- Forbid factual assertions without evidence pins
Artifacts:
- PROMPT_GUARDRAILS.yaml
- GENERATION_AUDIT.jsonl

P343) “CUSTOM_CODE SANDBOX” FOR TRANSFORMERS MODELS (DOTS.OCR CLASS)
Why: some HF models use custom code tags; that can execute arbitrary python.
Policy:
- sandbox inference subprocess
- restricted env
- dependency allowlist
- timeouts + crash capture
Artifacts:
- SANDBOX/policy.json
- SANDBOX/crash_reports.jsonl

P344) “ASSET VAULT v3” — PACKFILES + HYDRATION PLANS
Upgrade:
- add packfile compaction jobs
- hydration plans generated per run, not ad hoc
- verify on hydrate: bytes+mtime+crc32 (+sha256 optional)
Artifacts:
- ASSET_VAULT/packfiles/*.pack
- ASSET_VAULT/hydration_plans/<run_id>.json
- ASSET_VAULT/verify_reports/<run_id>.json

P345) “PACK TRIAD v2” — FULL/CORE/LITE_OUTPUTS WITH RECEIPTS
Every pack must include:
- manifest + receipt
- builder script
- policy summaries
- versioned superpin snapshot

P346) NEXT HIGH-SIGNAL ACCEPTANCE SET (DGC2 CANDIDATES)
Candidate modules staged for scoring next cycle:
- local_pdf_to_mdjson (MinerU-inspired contract, fully local)
- ppocr_lane (Tier 1)
- got_ocr_lane (Tier 2)
- dots_ocr_lane (Tier 3; sandboxed)
- docqa_lane (Tier 4; Donut/LayoutLM)
- docqa_question_sets for orders/notices
All candidates must pass MRLG + offline-run gate + ModuleContract v2 + QuoteLock integration.

P347–P395) RESERVED FOR NEXT Δ ACCEPTANCE (NO RENumber churn)
===============================================================================
END APPENDIX v2026-01-18.25
===============================================================================

===============================================================================
APPENDIX v2026-01-18.26 — HIGH-SIGNAL Δ PACK (P396–P460)
Theme: “Close integration gaps.” Add enforceable schema + import discipline + model-lane expansion (Nougat) under MRLG.
===============================================================================

P396) NOUGAT LANE (PDF/SCAN → MARKDOWN) — “POWERFUL, BUT LICENSE-GATED”
Why: Nougat-style image-to-text models can produce high-quality Markdown from structured pages; can be useful for court PDFs when OCR+layout fails.
Candidates discovered (must be registered in MRLG and license-governed):
- https://hf.co/facebook/nougat-base (license tag: cc-by-nc-4.0 => INTERNAL_ONLY by default)
- https://hf.co/facebook/nougat-small (license tag: cc-by-4.0 => potentially PROD_OK_WITH_NOTICE; verify MRLG)
- https://hf.co/Norm/nougat-latex-base (license tag: apache-2.0 => potentially PROD_OK; verify MRLG)
Governance:
- Nougat lane is NEVER “authoritative text.” Its output must pass DQG and is treated as STRUCTURED_EXTRACT unless QuoteLock verification passes against an independent extractor.
- Any quote sourced from Nougat must be verified via QuoteLock (two-extractor diff=0) before it can be used as VERIFIED.
Artifacts:
- EXTRACT/pdf/<doc_id>/nougat/{md,raw.json,confidence.json}
- DQ_REPORT.json entries per page
- QUOTE_CANDIDATES.jsonl with extractor="nougat"

P397) EXTRACTION CONSENSUS ENGINE (ECE) — “TWO-OF-THREE BEFORE PROMOTION”
Problem: OCR/VLM outputs can disagree; we need a deterministic promotion rule that avoids hallucinated text.
Rule (default; tunable per doc type):
- For each candidate line/field/quote, run N extractors (N≥2) and compute exact-text match, normalized match, and geometry overlap.
Promotion:
- VERIFIED_QUOTE requires exact match across 2 independent extractors AND matching page anchor.
- VERIFIED_FIELD requires either (A) exact match across 2 extractors, OR (B) 3 extractors with majority agreement + high confidence + no mismatch flags.
Outputs:
- CONSENSUS/fields.jsonl
- CONSENSUS/quotes.jsonl
- CONSENSUS/mismatch_report.json
Integration:
- QuoteLock uses ECE as the “verification conductor,” but still enforces diff=0 for VERIFIED.

P398) GRAPH SCHEMA v1.2 — “LEGAL BRAIN NEEDS EXPLICIT NODE/EDGE TYPES”
All nodes/edges must be schema-governed and migration-managed (Schema Governance v2).
Core node labels (minimum viable, enforceable):
- :Case {case_id, court_id, track, created_ts}
- :Court {court_id, name, level, county?}
- :AuthorityRef {auth_id, source, section, eff_date, url?, edition?}
- :Proposition {prop_id, text, auth_id, pinpoint, eff_date}
- :Vehicle {vehicle_id, name, form_id?, governing_rules[], prerequisites[]}
- :ProofObligation {po_id, vehicle_id, element_id, status, created_ts}
- :EvidenceAtom {evid_id, source_path, integrity_key, created_ts, type}
- :Quote {quote_id, text, status, method1, method2, created_ts}
- :Order {order_id, entered_date, judge?, title?, source_evid_id}
- :DocketEntry {docket_id, date, description, source_evid_id}
- :ServiceEvent {svc_id, date, method, proof_evid_id}
- :Deadline {dl_id, due_date, basis_auth_id, trigger_ref, explain_ref}
- :FilingDraft {draft_id, type, created_ts, status}
- :Denial {denial_id, date, reason, source_ref}
- :Run {run_id, started_ts, ended_ts, status}
- :Job {job_id, module, status, attempt_count}
Required relationship types (minimum):
- (:Case)-[:IN_COURT]->(:Court)
- (:AuthorityRef)-[:SUPPORTS]->(:Proposition)
- (:Vehicle)-[:GOVERNED_BY]->(:AuthorityRef)
- (:Vehicle)-[:HAS_PO]->(:ProofObligation)
- (:ProofObligation)-[:SATISFIED_BY]->(:EvidenceAtom)  (only when VERIFIED pins exist)
- (:EvidenceAtom)-[:CONTAINS]->(:Quote)
- (:Order)-[:SUPPORTED_BY]->(:EvidenceAtom)
- (:DocketEntry)-[:SUPPORTED_BY]->(:EvidenceAtom)
- (:Deadline)-[:BASED_ON]->(:AuthorityRef)
- (:Deadline)-[:TRIGGERED_BY]->(:Order|:DocketEntry)
- (:ServiceEvent)-[:PROVES_SERVICE_OF]->(:FilingDraft|:Order)
- (:Denial)-[:CONVERTED_TO]->(:Vehicle)
- (:Run)-[:RAN_JOB]->(:Job)
Hard invariants (governor-enforced):
- Any :Proposition used for court-ready drafting must have :AuthorityRef with eff_date and pinpoint.
- Any :Quote used in court-ready drafting must be VERIFIED and linked to an :EvidenceAtom that has a FactPin.
- Any :ProofObligation used to pass PCG must have SATISFIED status and at least one :EvidenceAtom SATISFIED_BY edge.

P399) NEO4J MIGRATION TEMPLATE — “CONSTRAINTS + INDEXES”
Migration file contract:
schema/migrations/V0120__graph_schema_v1_2.cypher creates:
- unique constraints: Case.case_id, AuthorityRef.auth_id, EvidenceAtom.evid_id, Quote.quote_id, Vehicle.vehicle_id, ProofObligation.po_id, Deadline.dl_id
- indexes: EvidenceAtom.integrity_key, DocketEntry.date, Order.entered_date
Governor:
- graph writes blocked if required constraints missing (preflight).

P400) CSV IMPORT CONTRACT (BULK + INCREMENTAL) — “NO AD-HOC LOADS”
Bulk import (first build) uses neo4j-admin import with deterministic CSVs:
- IMPORT/nodes_case.csv; IMPORT/nodes_court.csv; IMPORT/nodes_authorityref.csv; IMPORT/nodes_proposition.csv; IMPORT/nodes_evidenceatom.csv; IMPORT/nodes_quote.csv; IMPORT/nodes_vehicle.csv; IMPORT/nodes_po.csv; IMPORT/nodes_order.csv; IMPORT/nodes_docket.csv; IMPORT/nodes_service.csv; IMPORT/nodes_deadline.csv; IMPORT/nodes_draft.csv; IMPORT/nodes_denial.csv; IMPORT/rels_*.csv
Each CSV must include: stable id, created_ts, provenance (run_id or evidence ref).
Incremental import uses Cypher MERGE patches generated by GraphBuilderAgent and applied only via Mutation Ticket.
Artifacts:
- IMPORT/README.md (headers + examples)
- GRAPH_PATCHES/<run_id>/*.cypher
- GRAPH_APPLY_REPORT.json

P401) VECTOR STORE CONTRACT (OPTIONAL, BUT GOVERNED)
Purpose: accelerate retrieval without weakening TruthLock/QuoteLock.
Rule: embeddings never become evidence; they are recall aids only.
Index partitions: VEC_AUTHORITY, VEC_ORDERS, VEC_EXHIBITS, VEC_TRANSCRIPTS.
Required metadata per chunk:
{chunk_id, case_id, track, source_evid_id, page?, time?, quote_ids[], integrity_key}
Retrieval gate:
- drafted outputs must cite EvidencePins/AuthorityPins; embedding hits alone cannot justify a claim.

P402) EVIDENCE ATOMIZER v2 — “ONE FILE → MANY ATOMS”
Process: file ingest → classify → extract → shard into atoms; each atom receives integrity_key and pointer to original.
Outputs:
- EVIDENCE_ATOMS/index.json
- EVIDENCE_ATOMS/atoms/*.json
- EXTRACT/raw_text/*.txt
- EXTRACT/page_images/*.png (pointer-only by default if large)
Each atom includes provenance: extractor lane, versions, confidence, failure signatures.

P403) DISPUTE MODEL v1 — FACT/LAW STATES
States: VERIFIED, DISPUTED, UNKNOWN.
Rules:
- Court-ready outputs cite VERIFIED only.
- Draft/analysis may include DISPUTED only if explicitly labeled and never used as sole support.
Artifacts:
- DISPUTE_LEDGER.jsonl
- DISPUTE_SUMMARY.md

P404) DGC2 ACCEPTANCE HOOKS — “EXTRACTION LANE PROMOTION”
Promotion requires: MRLG PASS, Offline-run PASS, Sandbox policy if custom code, eval harness results, DQG + QuoteLock pass-rate thresholds.
Artifacts:
- LANE_EVAL_REPORT.md
- LANE_PROMOTION_TICKET.json (validator-issued)

P405) COURT PACKET BUILDER v1 — STRUCTURED OUTPUTS
Outputs:
- COURT_PACK/<case_id>/<run_id>/ with filings, exhibits, proofs, appendices, and manifest+PO snapshot+validation report.
Gate:
- PCG PASS required to produce FILE_READY status.

P406) QUOTE USAGE HARD RULE — NO LEAKAGE BETWEEN TRACKS
Quotes are scoped: quote_id includes case_id and source_evid_id; cross-case reuse requires explicit provenance edge.

P407) RUN REPLAY HARDENING — EXACT RECONSTRUCTION
Replay requires recorded inputs (pointers allowed), manifested outputs, hydration plans for external assets.
Artifacts:
- REPLAY/inputs_receipt.json
- REPLAY/rebuild_script.py (world-first builder invocation)

P408–P460) RESERVED FOR NEXT Δ ACCEPTANCE
Focus candidates: implement local_pdf_to_mdjson (PP-OCR first), implement ECE consensus engine and wire into QuoteLock, implement schema+migrations+import tooling.
===============================================================================
END APPENDIX v2026-01-18.26
===============================================================================

===============================================================================
APPENDIX v2026-01-18.27 — HIGH-SIGNAL Δ PACK (P461–P520)
Theme: “Docling-grade structured parsing + deterministic chunking.” Convert HF discoveries into local-only lanes with enforceable contracts.
===============================================================================

P461) DOCLING LANE FAMILY (STRUCTURED PARSE) — “LOCAL MINERU-CLASS OUTPUTS”
Anchor repos (register + pin revisions in MRLG; no cloud runtime):
- Docling model bundle: https://hf.co/docling-project/docling-models (licenses: cdla-permissive-2.0, apache-2.0)
- Layout detector: https://hf.co/docling-project/docling-layout-heron (license: apache-2.0; rt_detr_v2)
- Small multimodal parsers:
  - https://hf.co/ibm-granite/granite-docling-258M (license: apache-2.0; idefics3; 257.5M params)
  - https://hf.co/docling-project/SmolDocling-256M-preview (license: cdla-permissive-2.0; idefics3; 256.5M params; ONNX tagged)
Policy:
- Docling lanes are STRUCTURED_EXTRACT by default; VERIFIED requires ECE+QuoteLock promotion rules.
- MRLG must record dual-license cases explicitly (docling-models).

P462) LAYOUT-HERON MODULE (“layout_lane_docling_heron”)
Role: object-detection layout segmentation to emit stable geometry for blocks/headings/paragraphs/tables/figures.
Contract:
- Inputs: page images + render spec (dpi/colorspace fixed)
- Outputs: GEOMETRY.jsonl per page with bbox,label,confidence,model_id,revision,run_id
Gate:
- If geometry missing/low confidence => fallback to rule-based layout heuristics AND open DQG item.

P463) DOC PARSER MODULES (IDEFICS3 CLASS) — “docparse_granite / docparse_smoldocling”
Role: image-text-to-text structured parse for hard scans and complex layouts (mixed text/tables/forms).
Contracts:
- Inputs: page image shards + optional geometry hints + prompt templates (audited assets)
- Outputs: PARSE.jsonl (per page) with extracted text blocks + table candidates + captions + inline code/formula (if produced)
Governance:
- Prompt templates are versioned and recorded in GENERATION_AUDIT.jsonl.
- Any field/quote used in court-ready drafting MUST be promoted via ECE+QuoteLock.

P464) DOCLING LANE ROUTER (“docling_lane_router”)
Role: unify docling-family predictors behind a single lane router:
- choose layout-heron + (Tier0 native | PP-OCR | GOT-OCR | dots | docparse_granite | docparse_smoldocling) based on hardness score + DQG deficits.
Outputs:
- LANE_DECISIONS.jsonl (per page) explaining: hardness inputs, chosen lane, fallback reason, compute cost estimate.
Hard rule:
- Router cannot escalate to heavier lane without logging rationale (confidence deficit, table/form need, OCR mismatch).

P465) DETERMINISTIC CHUNKING CORE v2 (“chunker_geom_hash”)
Goal: stable retrieval chunks across repeated runs (replayable indexing).
Chunk identity:
- chunk_id = H(doc_id|page|layout_label|bbox_rounded|norm_text_hash)
- bbox_rounded uses fixed decimal; norm_text_hash uses unicode normalize + whitespace fold.
Outputs:
- CHUNKS/index.jsonl (chunk metadata)
- CHUNKS/map_to_pins.jsonl (chunk→FactPins/QuoteIds)
Safety:
- chunks are recall aids only; they never become evidence.

P466) “FASTPDF PARSER” PROBE → LOCAL REIMPLEMENTATION
Probe Space (idea-only): https://hf.co/spaces/chunking-ai/chunking-pdf-parser
Local target modules:
- pdf_parse_fast: fast structural scan (page count, xref, encryption, text-layer stats)
- pdf_chunk_prepass: identify candidate pages needing OCR/VLM lanes
Deliverable:
- FAST_SCAN_REPORT.json with hardness features for lane router.

P467) OCR ERROR-DETECTION SIDE-LANE (INTERNAL ONLY BY DEFAULT)
Candidate (noncommercial tagged): https://hf.co/xiaoyao9184/surya_ocr_error_detection (license tag: cc-by-nc-sa-4.0)
Policy:
- INTERNAL_ONLY unless MRLG clears redistribution.
- Usage: post-OCR anomaly detector feeding DQG (flags likely OCR corruption; opens PO/DQ items).

P468) MODEL PACK BUILDER (“model_pack_builder”) — PIN + CACHE + PROVE
Purpose: reproducible model acquisition with offline-run compliance.
Outputs:
- MODELS/registry.lock.json (repo_id, revision, license, size, receipts)
- MODELS/cache/ (local mirror paths; pointer strategy if cap pressure)
- MODELS/verify_reports/<run_id>.json
Rule:
- Default: no module downloads models at run-time. Downloads occur in build/provision steps only.

P469) RUNTIME MATRIX GOVERNOR (“infer_runtime_matrix”)
Goal: deterministic selection of inference runtime per machine.
Matrix factors:
- GPU presence/VRAM, model size, quant availability, CPU SIMD, ONNX availability, throughput target, DQG thresholds.
Artifacts:
- RUNTIME_MATRIX.json (chosen engines + reasons)
- PERF_BUDGET.md (expected cost per lane)
Gate:
- If runtime differs from prior run, record drift reason in RUN_EVENTLOG.

P470) COMPUTE GOVERNOR v2 — “CHEAPEST LANE THAT PASSES QUALITY”
Rule:
- Start Tier0/1; escalate only when DQG says insufficient.
- Penalize hallucination-risk lanes unless verification passes (ECE+QuoteLock).
Artifacts:
- COSTED_LANE_LOG.jsonl (time/memory per page shard + failure signatures)

P471) GEOMETRY↔TEXT ALIGNMENT ENGINE (“align_text_to_layout”)
Purpose: reconcile OCR text lines with layout boxes to produce stable pinpoints for QuoteLock.
Outputs:
- ALIGNMENT.jsonl (per page): line_bbox,layout_block_id,confidence,method
- FACTPINS.jsonl upgrades: bbox + line offsets + block refs
Gate:
- mismatch opens DQ item; prevents VERIFIED promotion unless anchors reconcile.

P472) TABLE NORMALIZATION ENGINE v2 (“table_to_ledger”)
Purpose: convert extracted tables into row-based ledgers for disputes (MEEK1 ledgers, support calcs, etc.).
Outputs:
- LEDGERS/<doc_id>.csv
- LEDGER_AUDIT.json (normalization steps; no silent rounding)
- DISCREPANCY_CANDIDATES.jsonl (flagged anomalies)
Hard rule:
- ledger-derived claims remain DISPUTED until supported by VERIFIED pins.

P473) FORMS FIELD ENGINE v2 (“forms_field_extract + forms_field_fill”)
Purpose: unify:
- extraction (field/value from filled forms/PDFs)
- filling (SCAO overlay) with audit + PO compliance.
Outputs:
- FORM_FIELDS_EXTRACTED.json (bbox/value/confidence)
- FORM_FILL_AUDIT.json (source graph node ids + evidence pins)
Gate:
- fills blocked unless graph fields satisfy required POs (EvidencePins/AuthorityPins where mandated).

P474) WINDOWS SCHEDULER + WATCHERS v2 (SAFE AUTORUN)
Deliverable:
- schedule_harvest.ps1 creates 4/day tasks with offline-run mode, bounded concurrency, crash-safe job queue, strict storage roots (never C:\).
Artifacts:
- SCHEDULE/tasks_export.xml
- WATCHERS/status.json
Gate:
- tasks created only if preflight PASS and storage roots valid.

P475) SELF-HOSTED RUNNERS HARDENING v2
Targets:
- local runner pool; optional GitHub self-hosted runners (no secrets in repo); “runner capability manifest.”
Artifacts:
- RUNNERS/capabilities.json
- RUNNERS/policies.json
Hard rule:
- runners cannot mutate canonical state; they produce proposals/artifacts; Governor commits via tickets.

P476) DGC2 SCORECARD v1 — “DECISION GOLDEN COMPASS FOR NEW LANES”
Purpose: keep “upward growth” disciplined and safety-locked (avoid sprawl that increases denial risk).
Score dimensions (0–5):
- Value-to-case (MEEK alignment)
- License safety (MRLG)
- Offline-run feasibility
- Determinism + replayability
- QuoteLock compatibility
- Implementation complexity/maintenance
Promotion:
- below-threshold modules remain staged; only high scores are integrated into CURRENT.
Artifacts:
- DGC2/scorecard.json (per candidate)
- DGC2/decision_log.md (why promoted or deferred)

P477) “DOC-PARSER EVAL HARNESS” v1 — BENCHMARKS FOR COURT PDFS
Goal: objective acceptance tests on representative Michigan court PDFs (orders, notices, filings).
Metrics:
- QuoteLock pass-rate
- Field extraction precision/recall (hearing date/judge/relief)
- Table cell accuracy for ledgers
- Runtime cost per page
Artifacts:
- EVAL/benchmark_manifest.json (pointer-only to PDFs)
- EVAL/results/<run_id>.json
- EVAL/summary.md

P478–P520) RESERVED FOR NEXT Δ ACCEPTANCE
Next likely acceptance set:
- implement docling_layout_heron lane (P462) + alignment engine (P471)
- implement deterministic chunker (P465) and connect to vector store contract
- implement model pack builder (P468) + runtime matrix governor (P469)
===============================================================================
END APPENDIX v2026-01-18.27
===============================================================================

===============================================================================
APPENDIX v2026-01-18.28 — HIGH-SIGNAL Δ PACK (P521–P600)
Theme: “Next-tier retrieval + governance coupling.” Add visual-doc retrieval, hybrid RAG discipline, and hard PO-ledger coupling to the build/pack/replay system.
===============================================================================

P521) VISUAL DOCUMENT RETRIEVAL LANE (VDR) — “FIND THE PAGE EVEN WHEN OCR FAILS”
Purpose: court PDFs often have scans where OCR is weak; VDR retrieves pages by visual/textual cues without trusting OCR as truth.
Candidate anchors (MRLG pin + license govern; local only):
- ColPali (visual document retrieval; MIT): https://hf.co/vidore/colpali-v1.2  | https://hf.co/vidore/colpali-v1.3
Policy:
- VDR is recall-only; it proposes page candidates. Any claim/quote still requires EvidencePins + QuoteLock verification.
Outputs:
- VDR/hits.jsonl {query,doc_id,page,score,thumb_ref,run_id}
- VDR/query_pack.json {templates,case_id,track}
Integration:
- Retrieval Router can use VDR for “page candidate generation” when text search returns weak results.

P522) HYBRID RETRIEVAL ROUTER v3 (“LEXICAL+VECTOR+VISUAL”)
Lanes:
- LEX: ripgrep/FTS over extracted text + filenames + metadata
- VEC: embeddings over verified chunks (never raw OCR-only content unless flagged)
- RERANK: cross-encoder reranker for top-k (recall safe; not evidence)
- VIS: VDR page-level retrieval (ColPali)
Candidate anchors (MRLG pin):
- Embeddings (MIT): https://hf.co/BAAI/bge-m3
- Reranker (Apache-2.0): https://hf.co/BAAI/bge-reranker-v2-m3
Router contract:
- Input: QueryIntent (facts? law? deadline? service? order content?) + case scope + allowed sources
- Output: RetrievalSet with provenance: {method,chunk_ids,quote_ids,page_candidates,confidence}
Hard rule:
- Router must attach at least one EvidencePin or AuthorityPin before any output can be marked “court-ready.” Retrieval alone never suffices.

P523) “SAFE CHUNK PROMOTION” RULES (CHUNKS → QUOTES → FACTS)
New invariants:
- chunk_id may reference QuoteCandidates; only QuoteVerified ids can back FactPins.
- Facts are never extracted “from a chunk.” Facts are extracted from EvidenceAtoms with pins.
Artifacts:
- CHUNKS/promotions.jsonl {chunk_id,quote_candidate_ids,quote_verified_ids,ts,run_id}

P524) PO LEDGER COUPLING v2 — “PCW ENFORCED BY ARTIFACT + GRAPH, ALWAYS”
Requirement (non-optional):
- Every run produces a PO_LEDGER snapshot as BOTH:
  A) graph nodes (:ProofObligation with status + SATISFIED_BY edges), and
  B) file artifact PO_LEDGER/<run_id>.jsonl (append-only)
Coupling rule:
- PCG PASS requires PO_LEDGER snapshot hash (integrity_key) recorded in:
  - RUN receipt
  - COURT_PACK manifest
  - GRAPH :Run node
No silent overrides:
- Any manual override requires an explicit Validator Ticket and creates a PO_OVERRIDE record with reason + scope.

P525) “PO→PACK” HARD GATE — “NO FILE_READY WITHOUT PO RECEIPT”
Court packet builder MUST embed:
- PO_LEDGER snapshot
- Validation report listing which POs gate which filing outputs
- EvidencePin/AuthorityPin indices
Artifacts:
- COURT_PACK/.../PO_LEDGER_snapshot.jsonl
- COURT_PACK/.../VALIDATION_REPORT.md
- COURT_PACK/.../PINS/index.json

P526) “DECISION GOLDEN COMPASS” v2 (DGC2→DGC3) — UPWARD GROWTH WITH DISCIPLINE
Goal: keep expansion high-velocity without entropy.
DGC3 inputs:
- Backlog candidates (modules/lanes/patches)
- Risk profile (denial surface, license risk, determinism risk)
- Value profile (MEEK alignment, time saved, error reduction)
- Maintenance cost
DGC3 outputs (per cycle):
- ACCEPT set (integrate now)
- STAGE set (park in reserved pages)
- REJECT/DEFER set (explicit reasons)
Artifacts:
- DGC3/plan_<run_id>.json {accept,stage,defer,reasoning}
- DGC3/scorecard_<run_id>.csv
Rule:
- Any new capability must land either as (A) a governed module with contracts OR (B) a staged candidate with eval plan. No “floating ideas.”

P527) “EVAL AS FIRST-CLASS CITIZEN” v2 — BENCHMARKS FOR RETRIEVAL
Retrieval eval targets:
- Evidence recall: can we find the correct page/quote?
- Pin accuracy: do pins match verified text?
- False-positive rate: retrieval suggests irrelevant pages?
Artifacts:
- EVAL/retrieval/queries.json (templated by track)
- EVAL/retrieval/results_<run_id>.json
- EVAL/retrieval/summary_<run_id>.md
Promotion gate:
- Hybrid Router methods are promoted only if eval improves AND false positives stay under threshold.

P528) “LEXICAL CORE” HARDENING: RIPGREP + SQLITE FTS
Rationale: lexical search is deterministic and cheap; it catches filenames and exact phrases needed for QuoteLock.
Outputs:
- SEARCH/fts.sqlite (doc_id, page, text, pins, quote_ids)
- SEARCH/rg_index.json (paths + file types)
Gate:
- If extraction changes, the index is rebuilt and receipt logged (replay-safe).

P529) “AUTHORITY+VEHICLE” INDEX FORMS-FIRST (FAST LOOKUPS)
Build two indexes:
- AuthorityIndex: {authority_ref → propositions → vehicles → POs}
- VehicleIndex: {vehicle/form → prerequisites → service → deadlines → required exhibits}
Artifacts:
- INDEX/authority_index.json
- INDEX/vehicle_index.json
- INDEX/po_templates.jsonl

P530) “CASE SCOPE FIREWALL” — PREVENT CROSS-CONTAMINATION
Enhancement:
- Retrieval Router, LLM Router, and Packet Builder must all accept an explicit ScopeToken:
  {case_id,track,allowed_courts,allowed_evidence_roots}
Hard rule:
- no query may run without ScopeToken; prevents accidental mixing of unrelated cases/tracks.

P531) “SECRETS & CREDENTIALS” GOVERNOR (NO LEAKS, NO BROKEN RUNS)
Policy:
- secrets never stored in repo or packs
- store secrets in OS keychain or encrypted local vault; reference by secret_id only
Artifacts:
- SECRETS/policy.md
- SECRETS/secret_refs.json (ids only; no values)
Gate:
- Any module attempting to print env vars is blocked (log redaction enforced).

P532) “SBOM + SUPPLY CHAIN RECEIPTS” (REPRO BUILD HARDENING)
Add:
- CycloneDX SBOM generation for python/node deps
- signed build receipts (where signing is configured)
Artifacts:
- BUILD/sbom.cdx.json
- BUILD/build_receipt.json {git_rev?,tool_versions,signing_status,hashes}
Gate:
- Release pack requires SBOM + receipt; otherwise “DEV_ONLY” tag.

P533) “CRASH TRIAGE PACK” (REPLAYABLE FAILURES)
On any crash:
- capture module inputs pointers
- capture stdout/stderr tail
- capture parser crash signature (from P289)
Artifacts:
- CRASH/<run_id>/<job_id>/triage.json
- CRASH/<run_id>/<job_id>/logs_tail.txt
Rule:
- crashes never silently discard partial outputs; outputs are marked PARTIAL and queued.

P534) AUTONOMOUS WATCHERS v3 — “DELTA HARVEST WITHOUT CHAOS”
Watch targets:
- local drives (F:/, D:/, etc per Gate 0 storage eligibility)
- rclone remotes (gdrive roots) as pointer-only scanning unless hydrated
Outputs:
- WATCHERS/delta_events.jsonl {path,event_type,ts,root,run_id}
- QUEUE/jobs.jsonl (crash-safe)
Policy:
- watchers are read-only; they enqueue work; Governor executes.

P535) “EXTERNAL ASSET STRATEGY” v4 — CAS + PACKFILES + RANGED HYDRATION
Upgrade:
- Content-addressed storage (CAS) for large assets: store once, reference everywhere.
- Packfiles are CAS-compacted; hydration supports ranged pulls from user-controlled remotes.
Artifacts:
- ASSET_VAULT/cas/index.jsonl {integrity_key,bytes,where}
- ASSET_VAULT/packfiles/*.pack (zstd recommended)
- ASSET_VAULT/hydration_plans/<run_id>.json
Gate:
- Packs stay under cap by default; assets remain pointers unless explicitly hydrated.

P536) “LEGAL OUTPUT SAFETY” v2 — DRAFT vs FILE_READY BOUNDARY
Rules:
- DRAFT may include DISPUTED, but must label clearly.
- FILE_READY must be VERIFIED-only for factual quotes and must include PO receipts.
Artifacts:
- OUTPUTS/state_tags.json {draft,file_ready,blocked}

P537) NEXT ACCEPTANCE SET (DGC3) — WHAT SHOULD LAND NEXT
High-value, low-risk integrations:
- implement VDR lane with ColPali (page candidate retrieval) + ScopeToken firewall
- implement Hybrid Retrieval Router v3 with bge-m3 + reranker
- implement PO ledger coupling v2 + PO→PACK hard gate
- implement Lexical Core (rg + sqlite FTS) to stabilize QuoteLock workflows

P538–P600) RESERVED FOR NEXT Δ ACCEPTANCE
===============================================================================
END APPENDIX v2026-01-18.28
===============================================================================

===============================================================================
APPENDIX v2026-01-18.29 — HIGH-SIGNAL Δ PACK (P601–P680)
Theme: “Michigan procedural engines become shippable.” Add Trial/COA/MSC/JTC lane modules, forms-first enforcement, and record-survival automation—all governed by AuthoritySnapshot + PO ledger + QuoteLock.
===============================================================================

P601) “MI PROCEDURE LIBRARY” (MPL) — VEHICLE-FIRST, SNAPSHOT-GATED
Purpose: encode Michigan procedural vehicles as executable specs, not prose.
Core rule:
- MPL entries may NOT cite or paraphrase authority unless AuthoritySnapshot provides the exact pin.
MPL entry schema (VehicleSpec v1):
{vehicle_id,level(trial|coa|msc|jtc|federal_overlay),relief_tags[],forms[],authority_refs[],standard_of_review?,elements[],prereqs[],deadlines[],service_chain[],record_needs[],exhibits_required[],common_denials[],fallbacks[]}
Outputs:
- MPL/vehicle_specs/*.json
- MPL/vehicle_index.json (relief→vehicles)
- MPL/forms_index.json (form→vehicles)
Gate:
- any missing authority pin ⇒ VehicleSpec is “DRAFT_ONLY” and opens PO.

P602) “AUTHORITY SNAPSHOT EXTENDER” — COURT-LEVELS + ADMIN ORDERS + JTC RULES
Enhancement:
- AuthoritySnapshot must support multiple collections with independent effective dating:
  A) Trial rules (MCR + local orders)
  B) Appellate rules (COA/MSC rules and forms instructions)
  C) Judicial discipline rules (MCR 9.200+ series, JTC procedure refs)
  D) Benchbooks/MJI/SCAO form instructions
Outputs:
- AUTH_SNAPSHOT/collections.json
- AUTH_SNAPSHOT/index.json
- AUTH_SNAPSHOT/pin_resolver.json (how to reopen pin)
Hard rule:
- No “court-ready” output may reference authority outside snapshot; out-of-snapshot ⇒ blocked with acquisition plan.

P603) “FORMS-FIRST COMPILER” v3 — SCAO FORM PACKETS AS BUILT ARTIFACTS
Purpose: stop treating forms as afterthoughts.
Pipeline:
- FORM_CATALOG → FIELD_MAPS → VALIDATORS → FILL_PLANS → RENDER → AUDIT
Artifacts (per form):
- FORMS/<form_id>/field_map.json
- FORMS/<form_id>/validator.jsonschema
- FORMS/<form_id>/fill_plan.json (graph fields + pins)
- FORMS/<form_id>/rendered/<run_id>/* (pdf/docx outputs)
- FORMS/<form_id>/audit/<run_id>.json
Gate:
- any field filled without an allowed source ⇒ PO opens and render is tagged “DRAFT_ONLY.”

P604) “SERVICECHAIN GENERATOR” v2 — SERVICE IS A FIRST-CLASS ENGINE
Purpose: service defects are denial magnets; automate them.
Inputs:
- VehicleSpec.service_chain + court/local practice config + parties/addresses registry
Outputs:
- SERVICE/plan_<run_id>.json (who/what/when/how)
- SERVICE/proof_of_service_draft.docx|pdf (forms-first if available)
- SERVICE/receipt.json (what evidence proves service)
Rules:
- service events create :ServiceEvent nodes linked to EvidenceAtoms + pins.
Gate:
- if service plan uncertain ⇒ opens PO and blocks FILE_READY.

P605) “DEADLINE ENGINE” v3 — DEADLINES AS COMPUTED OBJECTS WITH EXPLAINERS
Enhancement:
- Every Deadline must include:
  (a) trigger event pointer (Order/DocketEntry pin),
  (b) authority pin for the computation rule,
  (c) computation trace (human-readable explainer).
Outputs:
- DEADLINES/index.json
- DEADLINES/explainers.md
- DEADLINES/calendar.ics (optional; local only)
Gate:
- any deadline without a pinned basis ⇒ UNKNOWN, opens PO.

P606) “ORDERCHAIN / DOCKET HARVEST” v2 — INGEST AS STRUCTURED EVENTS
Purpose: stop manual docket copying; make docket entries machine-usable.
Artifacts:
- DOCKET/<case_id>/entries.jsonl {date,desc,source_pin,evid_id}
- ORDERS/<case_id>/orders.jsonl {entered_date,title,relief_summary_pin,evid_id}
- RECORD_SPINE/* updated (P340)
Rule:
- docket-derived assertions are DISPUTED until supported by order text pins (QuoteLock path) where needed.

P607) “COA ORIGINAL ACTION BUILDER” v1 — SUPERINTENDING CONTROL LANE (PROPOSAL→PACK)
Purpose: generate a governed playbook and packet for a COA original action without inventing procedure.
Outputs:
- COA_OA/<case_id>/<run_id>/
  - petition.docx (draft) + exhibits index
  - verification/affidavit (if required by VehicleSpec)
  - jurisdiction/adequate-remedy analysis memo (DRAFT)
  - PCG gate report + PO ledger snapshot
Gates:
- jurisdiction and adequate-remedy POs must be satisfied before FILE_READY tag.
Note:
- All procedural rules/forms referenced must be pinned in AuthoritySnapshot (P602).

P608) “APPEAL PACK BUILDER” v1 — CLAIM OF APPEAL / APPLICATION / STAY / BOND (AS VEHICLES)
Principle:
- “Appeal” is not a monolith; each move is a VehicleSpec with its own POs.
Artifacts:
- APPEALS/<case_id>/<run_id>/ (structured packet)
- APPEALS/vehicle_decisions.json (why appeal vs application vs OA, etc)
Gate:
- no auto-selection; DGC3 must select path with explicit rationale and denial-surface mitigations.

P609) “JTC COMPLAINT BUILDER” v2 — MISCONDUCT EVIDENCE SANITIZER + SEVERITY SCORER
Purpose: produce a disciplined JTC narrative that is evidence-pinned and scope-clean.
Modules:
- misconduct_claim_atomizer: converts allegations into discrete misconduct “claims” each requiring:
  - event pins, quote pins, authority pins (JTC/Canon references), harm framing
- severity_scorer: ranks claims for inclusion; avoids overbreadth
- privacy_sanitizer: redacts sensitive child info where required; creates sealed appendix if needed
Outputs:
- JTC/<run_id>/complaint_draft.md|docx
- JTC/<run_id>/claim_grid.csv (claim→evidence→authority)
- JTC/<run_id>/redaction_map.json
Gate:
- any claim without pins is excluded from FILE_READY package.

P610) “CANON / BENCHBOOK VIOLATION MAPPER” v2 — FROM EVENTS TO VIOLATION CANDIDATES
Purpose: turn courtroom behavior into structured violation candidates without asserting guilt.
Outputs:
- VIOLATIONS/candidates.jsonl {event_id,behavior_summary_pin,possible_authority_refs[],confidence}
Rule:
- candidates remain “proposed” until authority pins are verified in snapshot.

P611) “LIVE PRESERVATION DAEMON” v2 — HEARING MODE, REAL-TIME CAPTURE
Purpose: ensure record-survival discipline during hearings.
Features:
- hotkeys to log objections/offers of proof/time stamps (local)
- capture audio/video file pointers (no cloud)
- produce immediate hearing packet: timeline, objection ledger, exhibit offer ledger
Outputs:
- LIVE_PRESERVATION_LOG.jsonl (append-only)
- HEARING/<date>/objections.jsonl
- HEARING/<date>/offers_of_proof.jsonl
Gate:
- daemon never mutates graph; it writes artifacts; Governor ingests via tickets.

P612) “TRANSCRIPT ATTACK ENGINE” v2 — TIME-PINNED SEGMENTS + DISCREPANCY FLAGS
Purpose: systematically extract contradictions between transcript, orders, and record.
Outputs:
- TRANSCRIPTS/<doc_id>/segments.jsonl {t_start,t_end,text,status,pins}
- DISCREPANCY_MAP.jsonl {transcript_pin,order_pin,type,notes}
Rule:
- discrepancies are triage items; do not become claims until pinned and validated.

P613) “DENIAL NORMALIZER” v2 — CLEAN DENIAL FORCER
Purpose: convert vague denials into actionable cure plans and fallback vehicles.
Outputs:
- DENIALS/<run_id>/normalized.json
- DENIALS/<run_id>/cure_plan.md
- DENIALS/<run_id>/fallback_vehicle_map.json
Gate:
- denial normalization requires service/deadline/authority pins; else opens PO.

P614) “LOCAL CONFIG GOVERNANCE” v2 — COUNTY/COURT PRACTICE AS VERSIONED CONFIG
Purpose: capture local practice without guessing.
Artifacts:
- CONFIG/courts/<court_id>.json (local filing rules, judge preferences ONLY if sourced/pinned)
- CONFIG/courts/<court_id>.sources.json (pins/pointers)
Rule:
- unsourced local practice claims forbidden; must be pinned or omitted.

P615) “MEEK TRACK PACK BUILDERS” v1 — SAME ENGINES, TRACK-SPECIFIC OUTPUTS
Deliverable pack profiles:
- MEEK1: ledgers, utility billing disputes, LT notices, escrow logic (if any), entity veil map (pointer-only)
- MEEK2: parenting time restoration, FOC enforcement, contempt defense, mental-health order attack
- MEEK3: PPO modification/termination, show-cause defense, service/notice attacks
- MEEK4: JTC/canon packages, COA OA posture, bias/predetermination pattern
Artifacts:
- PACK_PROFILES/mEEK*.json (what outputs are required by track)

P616) “GRAPH-TO-PACKET TRACE” v1 — EVERY OUTPUT HAS A TRACE MAP
Purpose: court-grade traceability.
Outputs:
- TRACE/<run_id>/trace_map.json {output_file→nodes/edges→pins→authority_refs}
Gate:
- FILE_READY requires trace map + PO ledger snapshot.

P617) “MUTATION TICKET ENFORCER” v2 — WHO CAN CHANGE WHAT
Rule:
- LLM cannot mutate canonical graph/state.
- GraphBuilderAgent emits patches.
- ValidatorAgent issues MutationTickets.
- Governor applies patches and records apply report.
Artifacts:
- TICKETS/<run_id>/*.json
- GRAPH_APPLY_REPORT.json
Hard rule:
- any write without ticket ⇒ reject and log incident.

P618) “QUALITY BUDGET” v2 — TIME/COMPUTE BOUNDS WITHOUT QUALITY LOSS
Purpose: keep the system usable on Win64 desktop constraints.
Mechanism:
- per-lane timeouts, retry budgets, and fallback ladders.
- hard cap on “expensive lanes per doc” unless DQG demands.
Artifacts:
- BUDGETS/compute.json
- BUDGETS/outcomes_<run_id>.json

P619) NEXT ACCEPTANCE SET (DGC3) — SHIP THE MOST DENIAL-RESISTANT MODULES
Recommended accept-first:
- Forms-first compiler v3 (P603)
- ServiceChain v2 + Proof artifacts (P604)
- Deadline engine v3 explainers (P605)
- COA OA builder v1 skeletonization is forbidden: must ship as governed templates + pack builder (P607)
- JTC builder v2 claim grid + sanitizer (P609)
All with PO ledger coupling + trace maps (P524,P616).

P620–P680) RESERVED FOR NEXT Δ ACCEPTANCE
===============================================================================
END APPENDIX v2026-01-18.29
===============================================================================

===============================================================================
APPENDIX v2026-01-18.30 — HIGH-SIGNAL Δ PACK (P681–P760)
Theme: “Branch-out cores that still obey AuthoritySnapshot + Forms-First + PO ledger + QuoteLock + replayability.”
Goal: add above-and-beyond system layers (GUI/UX, build+sign, module sandboxing, local LLM ops, privacy/security, data governance) WITHOUT weakening the core gates.
===============================================================================

P681) GOVERNOR “CONTROL PLANE” v3 — SINGLE SOURCE OF EXECUTION TRUTH
Problem: when modules proliferate, you need one deterministic orchestrator with replay.
Control Plane duties (non-delegable):
- owns Run lifecycle (create/queue/execute/commit/replay)
- owns PCW/PCG state transitions (via PO ledger)
- owns schema migration + graph write enforcement (MutationTickets only)
- owns packaging + receipts + cap policy (≤700MB)
Artifacts:
- RUNS/<run_id>/run.json (inputs, scope token, module plan, versions)
- RUNS/<run_id>/eventlog.jsonl (append-only)
- RUNS/<run_id>/commit_report.json (what became canonical)
Hard rule:
- No module writes to canonical stores except via Governor commit step.

P682) MODULE SANDBOXING v2 — “UNTRUSTED CODE RUNS IN A BOX”
Threat model: plugins/third-party parsers can corrupt state or leak secrets.
Design:
- module runner executes each module in isolated process boundary:
  - read-only mounts for canonical evidence roots
  - write-only mount for run workspace
  - explicit allowlist for outbound network (default: none)
- policy file per module: resources allowed (cpu/gpu, file patterns, timeouts).
Artifacts:
- SANDBOX/policies/<module>.json
- SANDBOX/denials.jsonl (blocked operations)
Gate:
- any module requesting broader permissions must pass DGC3 + explicit allow.

P683) LLM PERMISSION MODEL v3 — “LLM IS ADVISOR, NOT WRITER OF STATE”
Upgrade:
- LLM outputs are treated as PROPOSALS:
  - ProposedNodes, ProposedEdges, ProposedDrafts, ProposedPOResolutions
- ValidatorAgent converts proposals into MutationTickets or rejects with reasons.
Artifacts:
- PROPOSALS/<run_id>/*.jsonl
- VALIDATION/<run_id>/proposal_decisions.jsonl
Hard rule:
- LLM cannot directly emit “VERIFIED.” Only QuoteLock/ECE/Validator can promote.

P684) GUI/UX CORE v2 — “OPERATOR-FIRST, AUDIT-FIRST”
Goal: state-of-the-art Win64 GUI that surfaces gates, not magic.
Required panels (minimum):
- Dashboard: run status, queue, health, cap usage
- Case Scope: case_id, track, allowed roots, court level
- AuthoritySnapshot: versions, collections, gaps, pending POs
- Forms-First: form catalog, field-map status, fill audits
- PO Ledger: open/partial/satisfied POs with evidence/authority pins
- QuoteLock: candidate/verified, mismatch diffs, ECE promotion trail
- Replay: rerun old run_id deterministically, compare Δ outputs
Artifacts exported for GUI:
- UI/state.json (read model)
- UI/events.jsonl (live stream)
Rule:
- GUI reads from Governor artifacts only; does not bypass gates.

P685) UI “DENY-RESISTANCE HUD” — REAL-TIME RISK SURFACING
Purpose: show denial surface before filing.
Signals:
- service uncertainty, deadline uncertainty, missing authority pins, missing evidence pins, out-of-snapshot refs, disputed facts present, local practice unsourced, transcript/order mismatch present
Output:
- HUD/risk_map.json (scored)
- HUD/mitigation_plan.md (ordered cure steps)
Gate:
- FILE_READY forbidden if high-risk signals remain unaddressed.

P686) REPRO BUILD DISCIPLINE v2 — CI + DETERMINISTIC BUILDS + SIGNING HOOKS
Targets:
- reproducible Win64 .exe builds (PyInstaller/Nuitka) with pinned deps
- deterministic artifact naming
- build receipts + SBOM + hash receipts
Signing:
- signing is optional but supported via hooks; keys never stored in repo.
Artifacts:
- BUILD/pipeline.yml (local + CI profiles)
- BUILD/receipts/<build_id>.json
- BUILD/sbom.cdx.json (required)
- BUILD/signing_hooks/{sign.ps1,verify.ps1} (no secrets)
Gate:
- Release packs require receipts + SBOM; “unsigned” status must be explicit.

P687) “WORLD-FIRST BUILDER” v2 — OFFLINE REBUILD OF THE ENTIRE PROJECT
Purpose: sandbox links expire; rebuild locally from the bundle.
Requirements:
- self-extract core pack + incremental packs
- reconstruct exact folder trees + verify CRC32/integrity_key receipts
Artifacts:
- TOOLS/worldfirst_builder.py
- TOOLS/self_extract_pack.py (optional)
- REBUILD/rebuild_report.json
Hard rule:
- builder never fetches from the internet unless user explicitly enables hydration.

P688) EXTERNAL ASSET STRATEGY v5 — POINTERS + CAS + PACKFILES + CONTENT FILTERS
Upgrade beyond “pointer+hash”:
- CAS store keyed by integrity_key supports:
  - dedupe
  - packfile compaction
  - ranged hydration from user-controlled remote
- content filters:
  - auto-exclude binaries/models from FULL packs unless “ModelPack” flagged
- “hydration manifests” describe how to fetch/restore assets.
Artifacts:
- ASSET_VAULT/cas/index.jsonl
- ASSET_VAULT/packfiles/*.pack
- ASSET_VAULT/hydration/<run_id>.json
- ASSET_VAULT/policies.json
Gate:
- FULL packs remain ≤700MB by default; large assets are pointer-only with deterministic rebuild paths.

P689) LOCAL LLM ORCHESTRATION v2 — MULTI-RUNTIME, LOCAL-ONLY DEFAULT
Goal: integrate open-source LLMs without external APIs.
Runtimes:
- Ollama (local server) for convenience
- llama.cpp for embedded/offline
- vLLM (optional) for GPU servers
- ONNX/OpenVINO (optional) for CPU acceleration
Policy:
- LLM used only for: summarization, proposal drafting, retrieval query generation, contradiction suggestions
- never for authoritative quotes; never for authority text unless pinned via snapshot
Artifacts:
- LLM/runtime_matrix.json
- LLM/models.lock.json (pinned; license recorded)
- LLM/prompts/{templates}.txt (versioned)
- LLM/audit.jsonl (prompt ids, inputs pointers, outputs ids)
Gate:
- LLM outputs cannot satisfy POs unless backed by EvidencePins/AuthorityPins.

P690) “PROMPT FIREWALL” + “OUTPUT CONTRACT” v2 — STOP LEAKAGE + STOP HALLUCINATION
Purpose: keep LLM in a narrow corridor.
Mechanisms:
- strict schema outputs (JSON only) for proposals
- banned tokens list for “fabricated citations”
- scope token injection required for all prompts
Artifacts:
- LLM/firewall_rules.json
- LLM/contract_schemas/*.jsonschema
- LLM/firewall_denials.jsonl

P691) PRIVACY + CHILD DATA GUARD v2 — REDACTION IS A PIPELINE, NOT A MANUAL STEP
Rules:
- child identifiers minimized in public packets
- produce sealed appendix set if needed (operator-controlled)
Artifacts:
- PRIVACY/redaction_rules.json
- PRIVACY/redaction_map_<run_id>.json
- PACKETS/<run_id>/PUBLIC vs /SEALED folders (if enabled)
Gate:
- JTC/appeal packs require redaction map when child data present.

P692) SECURITY POSTURE v2 — LOG REDACTION + SECRET HYGIENE + TAMPER EVIDENCE
Add:
- log redaction filters (paths, tokens, PII)
- secret refs only (no values)
- tamper-evident receipts (integrity_key + manifest chain)
Artifacts:
- SECURITY/redaction_filters.json
- SECURITY/secret_refs.json
- SECURITY/receipts_chain.jsonl

P693) DATA GOVERNANCE v2 — “APPEND-ONLY BY DEFAULT, EXPLICIT DELETIONS ONLY”
Principles:
- all run outputs append-only
- canonical store updates only by commit reports
- deletions require explicit “DATA_DELETE_TICKET” and are rare
Artifacts:
- GOVERNANCE/data_policy.md
- TICKETS/data_delete/*.json
Gate:
- deletion tickets logged and reflected in manifests.

P694) “CASE INTELLIGENCE” LANE — PATTERN DETECTION WITHOUT CLAIMING FACTS
Goal: derive hypotheses and triage, not assertions.
Features:
- contradiction clustering
- retaliation pattern candidates
- timing correlation (orders ↔ service ↔ denials)
Outputs:
- INTEL/<run_id>/hypotheses.jsonl (tagged “non-assertive”)
- INTEL/<run_id>/triage_queue.json
Gate:
- hypotheses cannot be used in court-ready drafting unless converted into pinned Facts.

P695) “RECORD SURVIVAL” PACKETS v2 — HEARING/POST-HEARING AUTOMATION
Deliverables:
- hearing-day binder (exhibit list, offers of proof ledger, objection ledger)
- post-hearing preservation memo (what happened; what was preserved; what is missing)
Outputs:
- HEARING/<date>/binder.md
- HEARING/<date>/preservation_memo.md
- HEARING/<date>/evidence_requests.md (missing items list)
Gate:
- any “missing transcript/order” becomes PO with acquisition plan.

P696) “AUTHORITY SNAPSHOT ACQUISITION” LANE — OFFICIAL SOURCES ONLY (PIN-FIRST)
Design: authority snapshot builder must:
- download from official sources (SCAO, MSC/COA official, benchbooks publishers) as configured
- store raw PDFs/HTML as EvidenceAtoms with pins
- extract structured index but never treat it as authority unless pinned
Artifacts:
- AUTH_SNAPSHOT/sources_registry.json (official source list + update cadence)
- AUTH_SNAPSHOT/raw/<collection>/<doc_id> (pointer-only if large)
- AUTH_SNAPSHOT/extracted/index.jsonl
Gate:
- no authority entries without a raw source pointer + pin resolver.

P697) “LOCAL PRACTICE” ACQUISITION LANE — SOURCED OR SILENT
Rule: local practice config is allowed only if:
- sourced to local admin order, written court policy, or on-record statement pinned in transcript/order
Artifacts:
- CONFIG/courts/<court_id>.sources.json
Gate:
- unsourced preferences prohibited; omit rather than guess.

P698) “CROSS-STORE CONSISTENCY CHECKER” v1 — GRAPH/VEC/FILES MUST AGREE
Purpose: prevent drift.
Checks:
- every EvidenceAtom referenced in graph exists in manifest
- every QuoteVerified points to an EvidenceAtom with pins
- vector chunks map to valid QuoteIds
Artifacts:
- CONSISTENCY/<run_id>/report.json
- CONSISTENCY/<run_id>/fix_suggestions.md
Gate:
- commit blocked if critical inconsistencies.

P699) “RECOVERY & SELF-HEAL” v2 — AUTONOMOUS REPAIR WITHOUT MUTATING EVIDENCE
Goals:
- detect partial runs, broken indices, missing caches
- rebuild derived artifacts deterministically
Artifacts:
- RECOVERY/<run_id>/heal_plan.json
- RECOVERY/<run_id>/heal_report.json
Rule:
- repairs never overwrite originals; only regenerate derived outputs.

P700) NEXT ACCEPTANCE SET (DGC3) — ABOVE-AND-BEYOND, BUT DENY-RESISTANT
High-value additions to integrate next:
- Governor Control Plane v3 + sandbox policies (P681,P682)
- GUI/UX core read-model + HUD risk map (P684,P685)
- World-first builder v2 + asset strategy v5 (P687,P688)
- Local LLM orchestration v2 + prompt firewall v2 (P689,P690)
- Cross-store consistency checker (P698)
All must remain snapshot-gated and replayable.

P701–P760) RESERVED FOR NEXT Δ ACCEPTANCE
===============================================================================
END APPENDIX v2026-01-18.30
===============================================================================

===============================================================================
APPENDIX v2026-01-18.31 — HIGH-SIGNAL Δ PACK (P761–P860)
Theme: “Graph Brain becomes operational.” Add Neo4j schema/migrations, a query + view library, agent contracts, and exportable Bloom-ready “brains,” all still snapshot-gated with PO/QuoteLock and fully replayable.
===============================================================================

P761) NEO4J SCHEMA GOVERNANCE v3 — “MIGRATIONS OR IT DIDN’T HAPPEN”
Goal: treat graph schema like code: versioned, replayable, idempotent.
Components:
- SchemaSpec (constraints/indexes/labels/rel types/property types)
- MigrationRunner (applies vNNNN migrations in order, records receipts)
- DriftDetector (compares live DB to SchemaSpec; produces fix plan)
Artifacts:
- GRAPH/schema/schema_spec.json
- GRAPH/schema/migrations/v0001__init.cypher
- GRAPH/schema/migrations/v0002__add_constraints.cypher
- GRAPH/schema/migrations/index.json (order + deps)
- GRAPH/schema/receipts/<db_id>.jsonl (applied, ts, checksum)
Gates:
- Any write to graph requires schema PASS (no missing constraints).
- Migrations are the only way to change schema; manual changes create INCIDENT.

P762) PROPERTY-TYPING + NORMALIZATION — “NO ‘STRINGLY-TYPED’ COURT DATA”
Rules:
- Date-like fields stored as ISO date strings in canonical props AND normalized helper props.
- IDs are normalized (case_id, doc_id, run_id) via a single canonical normalizer.
Artifacts:
- GRAPH/schema/property_types.json
- GRAPH/schema/normalizers.json
- CONSISTENCY/type_checks_<run_id>.json

P763) “DB IDENTITIES” + MULTI-DB SUPPORT v1
Use cases:
- separate DBs per track/case (or per environment) while sharing schema + tools.
Artifacts:
- GRAPH/db_registry.json {db_id, uri, profile, allowed_cases}
- GRAPH/connection_profiles/*.json (no secrets; secret refs only)
Gate:
- ScopeToken must name a db_id; no default DB to prevent cross-contamination.

P764) “WRITE PATH” LOCKDOWN — ENFORCED AT CYPHER LAYER
Mechanism:
- GraphBuilderAgent produces parameterized Cypher + patch sets (ProposedGraphPatch)
- ValidatorAgent issues MutationTicket signed (logical) with allowed op set
- Governor applies patch, logs receipts
Artifacts:
- GRAPH/patches/<run_id>/*.jsonl
- GRAPH/tickets/<run_id>/*.json
- GRAPH/apply_reports/<run_id>.json
Hard rule:
- No ad-hoc Cypher writes in runtime modules.

P765) CORE NODE/EDGE LIBRARY v2 — MINIMAL, POWERFUL, STABLE
Canonical node families (summary; detailed schema lives in schema_spec):
- :Case, :Track, :Court, :Party, :Person, :Organization
- :EvidenceAtom, :QuoteCandidate, :QuoteVerified, :FactPin, :AuthorityRef
- :VehicleSpec, :FormSpec, :ProofObligation, :Run, :Ticket
- :Event, :Deadline, :ServiceEvent, :Order, :DocketEntry
Canonical relationship families:
- (Case)-[:HAS_TRACK]->(Track)
- (EvidenceAtom)-[:HAS_PIN]->(FactPin)
- (QuoteVerified)-[:FROM_EVIDENCE]->(EvidenceAtom)
- (FactPin)-[:SUPPORTS]->(Proposition|Claim|PO)
- (PO)-[:SATISFIED_BY]->(EvidenceAtom|AuthorityRef)
- (Run)-[:PRODUCED]->(Artifact) and (Run)-[:UPDATED]->(NodeSet)
Rule:
- additions allowed only via migrations; avoid proliferation.

P766) “BRAINS” / “BLOOMS” AS EXPORTED VIEW PACKS v2
Goal: export 3–5 primary Bloom “brains” as deterministic view definitions + style packs.
Brains (default set; scope-adjustable):
- Brain_A: Courts+Jurisdictions+Forms+Authorities (AuthoritySnapshot-backed)
- Brain_B: Case Spine (Orders/Docket/Deadlines/Service)
- Brain_C: Evidence+QuoteLock+FactPins+Contradictions
- Brain_D: Vehicles+PO Ledger+PCG gates+Packets
- Brain_E: JTC/Canon/Appellate escalation lanes (if enabled)
Artifacts:
- BLOOM/viewpacks/Brain_A.json (queries + perspective)
- BLOOM/viewpacks/Brain_A.style.json (theme, colors, captions)
- BLOOM/viewpacks/index.json
Rule:
- Viewpacks are generated from graph + config; never edited manually as “source of truth.”

P767) BLOOM THEME ENGINE v1 — “VISUAL SEMANTICS ARE CONTROLLED”
Purpose: consistent color/label semantics across brains.
Inputs:
- NodeType→color palette map
- EdgeType→stroke style map
- Caption rules (e.g., EvidenceAtom shows doc_id + date)
Artifacts:
- BLOOM/theme/theme.json
- BLOOM/theme/caption_rules.json
- BLOOM/theme/legend.md
Gate:
- any theme drift requires version bump + receipt.

P768) QUERY LIBRARY v2 — “INVESTIGATION QUERIES AS REUSABLE ASSETS”
Purpose: stop writing one-off Cypher; store as assets with parameters and expected outputs.
Query asset schema:
{name, purpose, params, cypher, expected_shape, safety_notes, examples}
Query packs (initial high-value set):
- Q_TIMELINE: Event timeline with bitemp fields
- Q_DEADLINES: open/unknown deadlines with explainer links
- Q_SERVICE: service gaps and proof chain
- Q_PO: open/partial POs, what would satisfy them
- Q_QUOTES: QuoteCandidate vs QuoteVerified diffs
- Q_CONTRADICTIONS: conflicting claims supported by pins
- Q_ORDERS_VS_TRANSCRIPT: mismatch candidates
Artifacts:
- GRAPH/queries/*.json
- GRAPH/queries/index.json
Gate:
- queries used by GUI must declare “read-only” and include ScopeToken param.

P769) GRAPH EXPORTS v2 — HTML EXPLORER + STATIC READ MODE
Goal: view the brains without requiring a live Neo4j instance.
Exports:
- HTML explorer (sigma.js/vis-network style) built from snapshots
- read-only JSON graph slices per brain (node/edge lists with captions)
Artifacts:
- EXPORTS/graph_snapshot/<run_id>/Brain_A.json
- EXPORTS/html_explorer/<run_id>/index.html (static)
Rule:
- exports are derived artifacts; do not mutate canonical stores.

P770) “EVIDENCE ATOM REGISTRY” v2 — DEDUPE + REOPEN RECIPES
Purpose: EvidenceAtoms must be stable IDs across runs.
Mechanism:
- integrity_key + canonical path pointer
- resolver recipe: bundle→entry→page/line/time/bates
Artifacts:
- EVIDENCE/registry.jsonl
- EVIDENCE/reopen_recipes.jsonl
Gate:
- any output that references evidence must include a reopen recipe pointer.

P771) QUOTELOCK WORKBENCH v2 — DIFF-FIRST, PROMOTION-ONLY
Features:
- show candidate extraction side-by-side with image render or text-layer source
- require human or deterministic verifier step (ECE) to promote
Artifacts:
- QUOTELOCK/workbench/<run_id>/*.json
- QUOTELOCK/diffs/<run_id>/*.md
Gate:
- “Verified quote” requires dual-source verification record.

P772) FORMS FIELD MAP STUDIO v1 — VERSIONED FIELD MAPS WITH TESTS
Goal: field maps evolve safely.
Artifacts:
- FORMS/field_maps/<form_id>/v0001.json
- FORMS/field_maps/<form_id>/tests/v0001_cases.json
- FORMS/field_maps/<form_id>/test_report_<run_id>.json
Gate:
- field map changes must pass tests before being used in FILE_READY render.

P773) PACKET BUILDER v2 — COURT PACKS AS COMPILATIONS, NOT “FILES”
Every packet compiles:
- cover/index
- Vehicle decision record
- PO ledger snapshot
- QuoteVerified index
- EvidenceAtom reopen recipes index
- Service plan + proof chain
- Deadline explainers
- Trace map
Artifacts:
- PACKETS/<case_id>/<run_id>/MANIFEST.json
- PACKETS/<case_id>/<run_id>/TRACE/trace_map.json
- PACKETS/<case_id>/<run_id>/PO/po_ledger_snapshot.jsonl
Gate:
- packet compile fails closed if any required artifact missing.

P774) “REPLAY & DIFF” ENGINE v2 — Δ IS A FIRST-CLASS OUTPUT
Goal: every run produces a diff against prior run (same scope).
Diff layers:
- files (added/changed)
- graph (node/edge counts + semantic changes)
- POs (status transitions)
- quotes (candidate→verified promotions)
Artifacts:
- DIFF/<run_id>/diff_summary.md
- DIFF/<run_id>/diff_files.json
- DIFF/<run_id>/diff_graph.json
- DIFF/<run_id>/diff_po.json
Rule:
- “continue” implies diff output; no silent changes.

P775) AGENT CONTRACTS v2 — “EACH AGENT OWNS A LANE + ARTIFACTS”
Agents (minimum set; each must be runnable headless):
- HarvesterAgent: inventory + delta events + pointers
- ExtractorAgent: Docling/OCR lanes + chunking outputs
- AuthoritySnapshotAgent: acquire/update snapshot (official sources) + pins
- QuoteLockAgent: candidate extraction + verification workflow (ECE)
- FormsAgent: field maps + fill plans + render + audit
- VehicleAgent: VehicleSpecs + prerequisites/deadlines/service
- POAgent: instantiate/update PO ledger + satisfaction checks
- ValidatorAgent: gate decisions + tickets + reports
- GraphBuilderAgent: propose graph patches + queries + viewpacks
- GovernorAgent: orchestrate and commit
Artifacts:
- AGENTS/registry.json (agent ids, CLI entrypoints, inputs/outputs)
- AGENTS/contracts/*.jsonschema
Hard rule:
- agents cannot hide outputs; every action emits artifacts + eventlog entries.

P776) JOB QUEUE v2 — CRASH-SAFE, PRIORITIZED, REPLAYABLE
Queue semantics:
- append-only job log with statuses
- idempotent jobs (safe retry)
- priority by track urgency (deadlines > ingest > refactor)
Artifacts:
- QUEUE/jobs.jsonl
- QUEUE/status.json
- QUEUE/retry_policy.json
Gate:
- queue runner cannot bypass ScopeToken.

P777) CONFIG “LAW PACKS” v1 — SNAPSHOT SOURCES + UPDATE POLICY
Purpose: define where authority docs come from (official only) and when to refresh.
Artifacts:
- AUTH_SNAPSHOT/law_packs.json {collection, sources, cadence, rules}
- AUTH_SNAPSHOT/update_log.jsonl
Gate:
- “refresh snapshot” cannot run without a pinned source registry.

P778) NEXT ACCEPTANCE SET (DGC3) — MAKE THE BRAINS VISIBLE
Accept-first build targets:
- schema governance v3 + migrations runner
- query library + GUI read model
- viewpack + theme generator
- replay+diff engine v2
All stay under the core gates; no authority text without snapshot pins.

P779–P860) RESERVED FOR NEXT Δ ACCEPTANCE
===============================================================================
END APPENDIX v2026-01-18.31
===============================================================================

===============================================================================
APPENDIX v2026-01-18.32 — HIGH-SIGNAL Δ PACK (P861–P960)
Theme: “Verification, testing, and adversarial hardening.” Add executable specs, fuzzing/chaos, denial-surface simulation, performance budgets, and release governance—still bound to AuthoritySnapshot + Forms-First + PO ledger + QuoteLock + replayability.
===============================================================================

P861) EXECUTABLE SPEC LAYER (ESL) v1 — “SPEC AS ARTIFACT, NOT PROSE”
Goal: every critical invariant becomes machine-checkable.
Spec types:
- SchemaSpecs (graph, manifests, tickets)
- GateSpecs (PCW/PCG thresholds and required artifacts)
- OutputSpecs (packet structure, field-map completeness)
- SafetySpecs (no out-of-scope authority; no unpinned claims)
Artifacts:
- SPECS/*.jsonschema
- SPECS/invariants.md (human view; derived)
- SPECS/expected_shapes/*.json (golden shapes)
Gate:
- any module output must validate against its declared Spec; failures are BLOCKING for FILE_READY.

P862) GOLDEN-FILES + SNAPSHOT TESTS v2 — “YOU CAN’T REGRESS QUIETLY”
Approach:
- store minimal “golden” inputs (pointer-only if large) and expected outputs (hashes + shapes)
- re-run in CI/local to prove determinism
Artifacts:
- TESTS/golden_inputs/index.json (pointers + hydration plan)
- TESTS/golden_outputs/index.json (hashes + schemas)
- TESTS/reports/<run_id>.json
Gate:
- release requires green golden tests for core lanes (AuthoritySnapshot, QuoteLock, Forms, PO Ledger, Packet compile).

P863) PROPERTY-BASED TESTING (PBT) v1 — “FIND EDGE CASES BEFORE THE JUDGE DOES”
Targets:
- deadline computation (date arithmetic, triggers)
- service plan generation (valid/invalid permutations)
- field-map filling (missing/ambiguous sources)
- pin resolver (page/line/bates/time formatting)
Artifacts:
- TESTS/pbt/<module>_strategies.py (or json strategy defs)
- TESTS/pbt/reports/<run_id>.json
Policy:
- PBT must generate counterexamples with replay seeds.
Gate:
- PBT failures block promotion of a module version.

P864) DENIAL-SURFACE FUZZER (DSF) v1 — “SIMULATE HOW A COURT COULD DENY”
Purpose: generate adversarial checks without inventing facts.
Inputs:
- VehicleSpec + local practice sources + known denial patterns (curated)
Outputs:
- REDTEAM/denial_surface_<run_id>.json {issue,impact,fix,linked_POs}
- REDTEAM/priority_cures_<run_id>.md
Hard rule:
- DSF can only propose “risk conditions”; it cannot assert procedural law without AuthoritySnapshot pins.

P865) FORMS ADVERSARIAL VALIDATOR v2 — “FIELDS THAT LOOK FILLED BUT ARE WRONG”
Checks:
- required fields blank or whitespace
- field filled from DISPUTED source
- field filled from out-of-scope case
- field filled without pin trace
Outputs:
- FORMS/validation/<run_id>/form_findings.json
- FORMS/validation/<run_id>/remediation.md
Gate:
- any high-severity form finding blocks FILE_READY.

P866) QUOTELOCK “ANTI-HALLUCINATION” TEST BATTERY v2
Purpose: ensure QuoteLock never promotes wrong text.
Tests:
- OCR drift: compare text-layer vs OCR vs image crop
- line-break/punctuation mismatches
- quote boundary misalignment
Outputs:
- QUOTELOCK/tests/<run_id>/results.json
- QUOTELOCK/tests/<run_id>/diffs.md
Gate:
- if verifier can’t reconcile sources, quote remains Candidate; PO opens.

P867) “PIN RESOLVER” HARDENING v2 — OPENABLE PINS OR NO CLAIM
Standardize pin formats:
- PDF pins: {doc_id,page,span(text offsets),line_range?}
- Image pins: {doc_id,page,bbox(px),dpi}
- Audio pins: {file_id,timestamp_start,timestamp_end}
- Bates pins: {bates_start,bates_end,doc_id,page?}
Artifacts:
- PINS/spec.json
- PINS/examples.json
Gate:
- every FactPin in FILE_READY outputs must conform to spec and be resolvable.

P868) PERFORMANCE BUDGET ENGINE v2 — “FAST PATHS WITH EXPLAINABLE ESCALATION”
Goal: keep Win64 desktop performance usable while preserving quality.
Mechanism:
- per-lane budgets (time, RAM, disk)
- escalation ladder: lexical→vector→rerank→visual→OCR
- “stop conditions” when marginal gain is low
Artifacts:
- BUDGETS/policy.json
- BUDGETS/telemetry_<run_id>.json
- BUDGETS/escalation_trace_<run_id>.jsonl
Gate:
- if budget exceeded, module must degrade gracefully and emit PO for missing outcomes (not fabricate).

P869) OBSERVABILITY STACK v2 — “EVERY RUN IS DEBUGGABLE”
Metrics:
- lane latencies, failure rates, cache hit ratio
- PO counts by category
- Quote promotions by source type
Artifacts:
- OBS/metrics_<run_id>.json
- OBS/health_<run_id>.json
- OBS/alerts_<run_id>.jsonl (local only)
Rule:
- observability artifacts are capped in size and summarized for packs.

P870) CHAOS / FAILURE INJECTION v1 — “SURVIVE REALITY”
Faults injected (controlled):
- missing file, corrupt PDF, timeouts, OCR failure, DB down, disk full simulation
Outputs:
- CHAOS/scenarios.json
- CHAOS/results_<run_id>.json
- RECOVERY/heal_report.json (must show self-heal behavior)
Gate:
- release requires pass of a minimal chaos suite (non-destructive).

P871) RELEASE GOVERNANCE v2 — “PROMOTION PATHS ARE EXPLICIT”
Promotion states:
- DEV → STAGED → RELEASE_CANDIDATE → RELEASE
Requirements by stage:
- DEV: basic tests + manifests
- STAGED: golden tests + PBT subset + DSF report
- RC: chaos suite + SBOM + build receipts + cap check
- RELEASE: signed (if configured) + docs + migration receipts
Artifacts:
- RELEASES/state_<version>.json
- RELEASES/checklist_<version>.md
Gate:
- Governor refuses to label RELEASE if checklist not satisfied.

P872) “VERSIONED DOCS” + TRAINING MATERIAL INGEST v1 (PO-GATED)
Goal: keep playbooks and operator training in sync with code.
Policy:
- training materials can be ingested as EvidenceAtoms (pointer-only if large)
- summaries are DRAFT until quote/pin verified
Artifacts:
- DOCS/training/index.json (pointers + scope)
- DOCS/training/summaries_<run_id>.md (labeled)
Gate:
- no “authority training” may be treated as authority unless it is itself an authority source in snapshot.

P873) “SEMANTIC DIFF” ENGINE v1 — Δ THAT IS MEANINGFUL
Beyond file diffs:
- detect changed VehicleSpec prerequisites
- detect changed PO templates
- detect changed field maps
- detect changed query packs/viewpacks
Artifacts:
- DIFF/semantic_<run_id>.json
- DIFF/semantic_<run_id>.md

P874) “LICENSE GOVERNOR” v1 — OPEN-SOURCE ONLY, RECORDED
Goal: prevent accidental inclusion of restricted assets.
Mechanism:
- every external component recorded with license + source pointer
- module runner refuses unknown license status
Artifacts:
- LICENSES/third_party.lock.json
- LICENSES/findings_<run_id>.json
Gate:
- unknown/blocked license ⇒ component staged only; not shipped.

P875) “SEALING & REDACTION QA” v1 — PUBLIC/SEALED PACK CONSISTENCY
Checks:
- sealed items not referenced in public packet
- public packet includes necessary redaction map
Outputs:
- PRIVACY/qa_<run_id>.json
- PRIVACY/qa_<run_id>.md

P876) “DOC CORRUPTION TRIAGE” LANE v1 — READ-ONLY DETECTION
Purpose: detect corrupt files without modifying them.
Outputs:
- INTEGRITY/corrupt_scan_<run_id>.csv {path,type,reason}
- INTEGRITY/retest_plan_<run_id>.md
Policy:
- rename/repair actions are optional and require explicit operator command/ticket.

P877) NEXT ACCEPTANCE SET (DGC3) — HARDEN WITHOUT SLOWING
Integrate next:
- ESL specs + golden tests for core lanes (P861,P862)
- Denial-surface fuzzing + forms adversarial validator (P864,P865)
- Pin resolver hardening + QuoteLock test battery (P866,P867)
- Release governance v2 + license governor (P871,P874)

P878–P960) RESERVED FOR NEXT Δ ACCEPTANCE
===============================================================================
END APPENDIX v2026-01-18.32
===============================================================================

===============================================================================
APPENDIX v2026-01-18.33 — HIGH-SIGNAL Δ PACK (P961–P1060)
Theme: “Court-ready assembly + autonomous ops.” Add filing-grade document assembly, exhibit governance, scheduler/runners, and MI-specific operational lanes while preserving AuthoritySnapshot + Forms-First + PO ledger + QuoteLock + replayability.
===============================================================================

P961) COURT PACK “ASSEMBLY LINE” v3 — DOCX/PDF AS PRODUCTS WITH QA
Goal: a court packet is a compiled artifact with deterministic assembly steps.
Stages:
- Stage A: Draft sources (docx/md/json proposals) → Stage B: Render → Stage C: Merge → Stage D: Validate → Stage E: Stamp/Index → Stage F: Release
Artifacts:
- ASSEMBLY/<run_id>/plan.json (ordered steps + inputs + outputs)
- ASSEMBLY/<run_id>/render_report.json
- ASSEMBLY/<run_id>/validate_report.json
- PACKETS/<run_id>/FINAL/ (ready-to-file)
Gates:
- Stage D validation must PASS; else output tagged DRAFT_ONLY and opens POs for defects.

P962) RENDER CORE v2 — LOCAL, REPRODUCIBLE, NO-CLOUD DEFAULT
Purpose: deterministic conversion for filings (docx→pdf; md→pdf; images→pdf).
Engines (pluggable; local):
- LibreOffice headless (docx→pdf)
- ReportLab (pdf generation)
- qpdf/ghostscript (merge/linearize if allowed) as optional; policy-gated
Artifacts:
- RENDER/engines.json (what is installed; versions)
- RENDER/jobs/<run_id>.jsonl
Gate:
- engine versions recorded in build receipts; render output must be reproducible for the same inputs.

P963) PACK VALIDATION v2 — “EFILING-SAFE” AS CONFIG, NOT GUESSWORK
Goal: validate packet against a configurable “court filing profile.”
Profiles:
- generic “Michigan efiling safe” profile (operator-tunable)
- court-specific profiles (only if sourced/pinned via local admin order or written policy)
Checks (profile-driven):
- file count, file types, max size, page count, OCR/text-layer presence, bookmarks, margins, orientation, font embedding (if needed), scan quality thresholds
Artifacts:
- VALIDATION/profiles/*.json
- VALIDATION/results/<run_id>.json
Gate:
- profile failures block FILE_READY.

P964) EXHIBIT GOVERNOR v3 — STAMPING + COVER PAGES + COLOR RULES
Purpose: exhibits are governed objects with consistent labeling.
Rules:
- Plaintiff exhibits use yellow labels; Defendant exhibits use blue labels.
- Each exhibit may have a cover page with caption + exhibit id + description + source pointer + reopen recipe pointer.
Artifacts:
- EXHIBITS/<case_id>/registry.jsonl
- EXHIBITS/<run_id>/stamp_plan.json
- EXHIBITS/<run_id>/stamped/*.pdf
- EXHIBITS/<run_id>/cover_pages/*.pdf
Gate:
- exhibit ids must be unique in packet; cover pages must not assert unpinned facts.

P965) EXHIBIT INDEX + OFFER-OF-PROOF PACK v2
Purpose: hearing readiness and record survival.
Outputs:
- EXHIBITS/<run_id>/exhibit_index.csv
- OFFERS_OF_PROOF/<run_id>/offer_ledger.jsonl
- OFFERS_OF_PROOF/<run_id>/proposed_oop_doc.md|docx (DRAFT unless pins)
Gate:
- any offer-of-proof narrative must be pinned or clearly marked as proposed.

P966) “BATES / PAGE-ID” OPTIONAL LANE — INTEGRITYKEY-FIRST, BATES AS PRESENTATION
Policy:
- internal identity uses integrity_key + reopen recipe.
- bates/page-id can be generated for presentation when needed (config-gated).
Artifacts:
- PAGING/bates_map_<run_id>.json
- PAGING/stamped/<run_id>/*.pdf (if enabled)
Gate:
- bates stamps must not cover evidence content; margin-safe.

P967) SIGNATURES + NOTARIZATION ASSIST v1 — FORMS-FIRST SUPPORT, NOT LEGAL ADVICE
Goal: help assemble signature blocks, verification statements, and notarization checklists.
Outputs:
- SIGNING/<run_id>/signature_map.json (who signs what; where)
- SIGNING/<run_id>/notary_checklist.md (operator checklist)
Gate:
- never fabricate witness/notary facts; this lane is checklist-only unless evidence/pins exist.

P968) “MI-FILE UPLOAD PACK” v1 — SPLIT + NAMING + METADATA (PROFILE-DRIVEN)
Purpose: prepare upload-friendly file sets without guessing platform rules.
Outputs:
- UPLOAD/<run_id>/bundle_plan.json (split strategy)
- UPLOAD/<run_id>/files/* (named per profile)
- UPLOAD/<run_id>/metadata.json (titles/desc; pinned where applicable)
Gate:
- splitting must preserve exhibit ids and trace maps; includes reconciliation report.

P969) SCHEDULER + RUNNERS v3 — AUTONOMOUS DAILY OPS WITH REPLAY
Goal: run harvest/validate/pack cycles without operator babysitting.
Runner modes:
- manual CLI run
- Windows Scheduled Task profile (local only)
- daemon “watch + queue” mode
Artifacts:
- SCHEDULE/profiles/*.xml (task templates; no secrets)
- RUNNERS/runner_config.json
- RUNNERS/runbook.md
- QUEUE/jobs.jsonl updated by watchers
Gates:
- scheduled runs are scope-limited; never “global scan” unless explicit profile allows.

P970) WATCHERS v4 — FILESYSTEM + DOCKET + INBOX (SOURCE-BASED)
Watcher types:
- FileWatcher: new/changed artifacts within allowed roots
- InboxWatcher: intake folder triage (zips, PDFs, images)
- DocketWatcher: parses docket updates only when sourced (operator-provided docket exports; no scraping assumptions)
Artifacts:
- WATCHERS/state.json
- WATCHERS/events.jsonl
- INTAKE/triage_<run_id>.json
Gate:
- watchers can only enqueue jobs; cannot mutate canonical stores directly.

P971) “INTAKE TRIAGE” v3 — FAST CLASSIFICATION, SAFE EXTRACTION
Goals:
- detect file type, corruption hints, encryption, embedded objects
- route to extract lanes (text-layer, OCR, visual retrieval)
Artifacts:
- INTAKE/classify.jsonl
- INTAKE/extract_plan.json
- INTAKE/quarantine/ (pointer-only; never delete originals)
Gate:
- encrypted/unknown binaries stay quarantined and open POs; do not attempt unsafe parsing.

P972) “ZIP DECOMPOSE + REPACK” v2 — RESUMABLE, DEDUPED, CAP-SAFE
Purpose: handle large multi-part zip inputs and preserve replayability.
Features:
- decomposer writes content-addressed store entries
- repacker produces CyclePacks for portability
Artifacts:
- ZIPS/decomposed/<zip_id>/index.json
- ZIPS/cyclepacks/<run_id>/*.zip
Gate:
- repack uses asset strategy v5 (CAS/packfiles) to remain ≤700MB for FULL packs.

P973) “RUN LEDGER” v4 — ONE LEDGER TO RULE THE WORK
Goal: unify eventlog, PO ledger snapshots, tickets, diffs, and pack receipts.
Artifacts:
- LEDGER/run_ledger_<run_id>.jsonl (append-only)
- LEDGER/summary_<run_id>.md
Hard rule:
- every module action emits a ledger record; no silent actions.

P974) FOIA LANE v2 — DEADLINES + RESPONSE TRACKING (FACT-PINNED)
Scope:
- FOIA request lifecycle as structured events + computed deadlines.
Outputs:
- FOIA/<agency>/<request_id>/timeline.jsonl
- FOIA/<agency>/<request_id>/deadlines.json
- FOIA/<agency>/<request_id>/packet_draft.md|docx (DRAFT unless pins)
Gate:
- all FOIA assertions must pin to request/response docs; no unsourced timeline facts.

P975) COMMUNICATIONS LEDGER v1 — MESSAGES AS EVIDENCE ATOMS
Purpose: systematize texts/emails/portal messages into EvidenceAtoms with pins.
Outputs:
- COMMS/registry.jsonl
- COMMS/threads/<thread_id>.jsonl
- COMMS/extract_<run_id>.json
Gate:
- personal/sensitive data redaction pipeline applies before public packets.

P976) “CLAIM→VEHICLE” RESOLVER v2 — RELIEF ROUTING WITH DENIAL MINIMIZATION
Goal: given a desired relief, choose vehicles via MPL + constraints.
Mechanism:
- rank vehicles by: prerequisites satisfied, deadlines ok, service feasible, authority snapshot complete, denial surface low
Outputs:
- VM/vehicle_ranking_<run_id>.json
- SBNA/single_best_action_<run_id>.md
Gate:
- ranking cannot assume facts; it consumes PO ledger + pinned data only.

P977) “OPERATOR DECISION GOLDEN COMPASS” DGC4 — EXPANSION WITH GOVERNANCE
Upgrade:
- DGC4 selects the next delta set by value density, denial-resistance uplift, and replay safety.
Scoring dimensions:
- Legal leverage (if in scope)
- Denial risk reduction
- Evidence pin coverage increase
- Automation ROI (time saved)
- Complexity cost and reliability
Artifacts:
- DGC/scorecard_<run_id>.json
- DGC/decision_<run_id>.md (traceable rationale)
Rule:
- DGC4 can recommend branching modules, but promotion requires ESL+tests.

P978) “CASE TEMPLATES” v1 — BOOTSTRAP NEW CASES WITHOUT GUESSWORK
Purpose: new case onboarding creates structure without asserting facts.
Outputs:
- CASES/<case_id>/case_template.json
- CASES/<case_id>/initial_PO_set.jsonl
- CASES/<case_id>/intake_checklist.md
Gate:
- templates are neutral; facts enter only through EvidenceAtoms and pins.

P979) NEXT ACCEPTANCE SET (DGC4) — SHIP COURT-ASSEMBLY + OPS FIRST
Recommended ship order:
1) Assembly Line v3 + Render Core v2 + Validation profiles (P961–P963)
2) Exhibit Governor v3 + Exhibit Index/OOP pack v2 (P964–P965)
3) Scheduler/Runners v3 + Watchers v4 + Intake triage v3 (P969–P971)
4) Run Ledger v4 + Upload pack v1 (P973,P968)
All remain snapshot-gated and replayable.

P980–P1060) RESERVED FOR NEXT Δ ACCEPTANCE
===============================================================================
END APPENDIX v2026-01-18.33
===============================================================================

===============================================================================
APPENDIX v2026-01-18.34 — HIGH-SIGNAL Δ PACK (P1061–P1180)
Theme: “Fill the minimally-completed areas.” Add concrete schemas, configs, and runnable contracts for the previously-defined cores (AuthoritySnapshot, Forms-First, PO Ledger, QuoteLock, Replayability, Packaging). Replace hand-wavy nouns with enforceable shapes.
===============================================================================

P1061) CANONICAL REPO + RUNTIME LAYOUT v2 (STABLE, MODULAR, SHIP-READY)
Goal: a single folder topology that supports:
- CLI headless runs
- GUI read-model
- deterministic build + releases
- append-only run artifacts
Layout (logical; adapt to Windows paths as needed):
/ (repo root)
  /apps/
    /desktop_gui/                # Win64 GUI (reads UI/state.json + UI/events.jsonl)
    /cli/                        # entrypoints, subcommands, help text
  /core/
    /governor/                   # control plane, scheduler, commit engine, PCW/PCG gates
    /stores/                     # file store + CAS + manifests + registry abstractions
    /graph/                      # neo4j schema, migrations, queries, viewpacks
    /evidence/                   # EvidenceAtom registry, pin resolver, extract lanes
    /authority/                  # AuthoritySnapshot agent + law packs config
    /forms/                      # catalog, field maps, render + validation
    /po/                         # PO templates, ledger engine, satisfaction checks
    /quotelock/                  # candidate extraction + verifier workflow
    /packets/                    # packet compiler + assembly line
    /security/                   # privacy, redaction, secret refs, license governor
    /tests/                      # golden tests, PBT, chaos suite, spec validation
  /assets_external/              # pointer-only references (no bulky binaries in FULL packs)
  /schemas/                      # JSONSchemas for all artifacts (ESL)
  /docs/                         # operator runbooks + training (PO-gated)
  /tools/                        # world-first builder, self-extract, packers, validators
  /runs/                         # generated; append-only (not committed unless desired)
Stability rule:
- folder names above are stable identity anchors; extensions are additive only.

P1062) “ARTIFACT CONTRACT” META-SCHEMA v1 — EVERY FILE HAS A TYPE + OWNER + STAGE
Artifact header fields (embedded in JSON or sidecar .meta.json):
- artifact_type (enum), artifact_id (stable), produced_by (agent_id), run_id
- stage (DRAFT|CANDIDATE|VERIFIED|FILE_READY), scope_token, created_ts
- inputs[] pointers, outputs[] pointers, spec_version, schema_ref
- integrity_key (if file-based) or content_fingerprint (if jsonl)
Artifacts:
- schemas/artifact_meta.schema.json
- MANIFEST/artifact_index.jsonl (one row per artifact)
Gate:
- any artifact referenced in packets must have meta + pass schema.

P1063) SCOPE TOKEN v2 — NOT JUST A STRING, A SIGNED(LOCAL) POLICY ENVELOPE
ScopeToken contents:
- db_id, case_ids[], track_ids[]
- allowed_roots[] (glob patterns), excluded_roots[]
- authority_snapshot_version (required for law usage)
- privacy_mode (PUBLIC|SEALED|INTERNAL)
- network_policy (OFF|ALLOWLIST)
- max_scan_depth, max_bytes (budgets), job_priorities
Artifacts:
- schemas/scope_token.schema.json
- GOVERNOR/scope_tokens/<token_id>.json (secret-free)
Gate:
- Governor refuses to run without an explicit ScopeToken.

P1064) PROPOSALS + TICKETS v2 — STANDARD PATCH FORMAT FOR EVERYTHING
Proposal schema types:
- ProposedGraphPatch (nodes/edges upserts, deletions disallowed by default)
- ProposedDocPatch (doc sections + insert/replace with anchors)
- ProposedPOUpdate (status transitions + satisfaction evidence)
- ProposedFormFillPlan (field→source pin mapping)
Ticket types:
- MutationTicket (graph writes)
- PacketCompileTicket (release assembly)
- RedactionTicket (privacy transformations)
Artifacts:
- schemas/proposals/*.schema.json
- schemas/tickets/*.schema.json
Gate:
- ticket issuance requires ValidatorAgent signature (logical) and traceable evidence/authority pins.

P1065) EVIDENCEATOM JSON SHAPE v2 — DEDUPED IDENTITY + REOPEN RECIPES
EvidenceAtom core fields:
- evidence_id, case_id, source_path_pointer (may be external pointer)
- file_kind (pdf|img|audio|txt|email|zip|other), size_bytes, mtime
- integrity_key (BundleUID+EntryPath+CRC32+bytes+mtime) or equivalent
- extraction_products[]: {product_type, pointer, spec_version}
- pins_index_pointer (FactPins list), quotes_index_pointer
Reopen recipe fields:
- bundle_ref, entry_path, page, line_range, bates_range, timestamp_range, bbox, text_offsets
Artifacts:
- schemas/evidence_atom.schema.json
- EVIDENCE/registry.jsonl (append-only)
- EVIDENCE/reopen_recipes.jsonl (append-only)
Gate:
- any FactPin must reference evidence_id + reopen recipe pointer.

P1066) FACTPIN + QUOTE TYPES v2 — EXPLICIT PROMOTION PATHS
FactPin:
- pin_id, evidence_id, pin_kind (pdf_line|pdf_span|img_bbox|audio_time|bates|other)
- locator fields (page, line_range, offsets, bbox, time)
- normalized_text (optional), extraction_method, confidence (non-authoritative)
QuoteCandidate:
- quote_id, evidence_id, pin_ref, text_candidate, method, warnings[]
QuoteVerified:
- quote_id, evidence_id, pin_ref, text_verified, verification_record_ref
VerificationRecord (ECE):
- verifier_type (textlayer_vs_image|dual_extract|manual_confirmed), inputs[] pointers, diff_summary
Artifacts:
- schemas/fact_pin.schema.json
- schemas/quote_candidate.schema.json
- schemas/quote_verified.schema.json
- schemas/verification_record.schema.json
Gate:
- FILE_READY packets may include QuoteVerified only; QuoteCandidate stays internal unless labeled.

P1067) PO LEDGER SCHEMA v3 — PCW IS REAL ONLY IF THE LEDGER IS MACHINE-CHECKABLE
ProofObligationTemplate fields:
- po_template_id, vehicle_id, proposition_id (optional), required (bool)
- authority_refs[] (must be pinned to AuthoritySnapshot)
- satisfaction_tests[] (machine-checkable predicates)
ProofObligation instance fields:
- po_id, po_template_id, status (OPEN|PARTIAL|SATISFIED)
- satisfactions[]: {evidence_id|authority_ref_id, pin_ref, test_id, validator_record}
- blockers[]: {blocker_kind, missing_pointer, acquire_plan_ref}
Ledger snapshot:
- run_id, case_id, vehicle_id, po_rows[] (or jsonl)
Artifacts:
- schemas/po_template.schema.json
- schemas/po_instance.schema.json
- PO/ledger.jsonl
- PO/snapshots/<run_id>.jsonl
Gate:
- any “ready to file” decision must cite the PO snapshot hash/fingerprint.

P1068) VEHICLESPEC SCHEMA v3 — FORMS-FIRST EXECUTABLE PROCEDURE MAP
VehicleSpec fields:
- vehicle_id, court_level, relief_types[]
- required_forms[] (FormSpec ids), optional_forms[]
- authority_refs[] (snapshot-pinned; no text quotes required)
- prerequisites[] (PO template refs, factual predicates pinned)
- deadlines[] (computable triggers)
- service_plan_template_ref (ServiceChain)
- packet_profile_ref (Validation Profile)
Artifacts:
- schemas/vehicle_spec.schema.json
- VM/library/*.json (one per vehicle)
Gate:
- VehicleSpecs cannot reference unknown court policies; local practice must be sourced.

P1069) FORMS-FIRST: FORMSPEC + FIELDMAP + FILLPLAN SCHEMAS v3
FormSpec:
- form_id, title, version, source_pointer (official), fields[] (canonical ids)
FieldMap:
- field_id → source rule(s) (EvidencePin, GraphField, constant allowed only if truly constant)
- validation rules (regex, enums, required conditions)
FillPlan:
- field_id → chosen source + pin refs + fallback + warning flags
Artifacts:
- schemas/form_spec.schema.json
- schemas/field_map.schema.json
- schemas/fill_plan.schema.json
- FORMS/catalog/index.json
- FORMS/field_maps/<form_id>/vNNNN.json
Gate:
- a filled field without a trace/pin opens PO; cannot be silent.

P1070) SERVICECHAIN SCHEMA v2 — SERVICE IS A PRODUCT WITH PROOF
ServicePlan:
- service_id, method (personal|mail|alt|unknown), target party, address_pointer (privacy-gated)
- required proofs (affidavit, receipt, return, acknowledgement)
- due dates computed from deadlines engine
Artifacts:
- schemas/service_plan.schema.json
- SERVICE/plans/<run_id>.json
- SERVICE/proofs/<run_id>/* (placeholders forbidden; if missing, PO opens)
Gate:
- service gaps are first-class denial risks; HUD must show them.

P1071) DEADLINE ENGINE v4 — COMPUTED DEADLINES MUST BE EXPLAINABLE
Deadline object:
- deadline_id, trigger_event_ref, computed_date, timezone
- authority_refs[] (snapshot pinned), computation_trace (human-readable)
- status (KNOWN|ESTIMATED|UNKNOWN) with why
Artifacts:
- schemas/deadline.schema.json
- DEADLINES/<run_id>/deadlines.json
- DEADLINES/<run_id>/explainers.md
Gate:
- UNKNOWN deadlines open POs; do not present as certain.

P1072) PACKET PROFILE SCHEMA v2 — VALIDATION WITHOUT GUESSING
PacketProfile:
- profile_id, name, description, source_refs[] (policy/admin order pins if court-specific)
- constraints: max_mb, max_pages, allowed_types, naming_rules, split_rules, bookmarks, OCR requirements
Artifacts:
- schemas/packet_profile.schema.json
- VALIDATION/profiles/*.json
Gate:
- court-specific profiles require sourced policy pins; else use generic profile.

P1073) ASSEMBLY PLAN SCHEMA v2 — REPRODUCIBLE DOCUMENT FACTORY
AssemblyPlan steps:
- step_id, tool_id, inputs[], outputs[], args, expected_hashes (optional)
Tools:
- tool_id, version, location, allowed_ops, deterministic_notes
Artifacts:
- schemas/assembly_plan.schema.json
- ASSEMBLY/<run_id>/plan.json
Gate:
- any non-deterministic tool must be flagged; receipts required.

P1074) “MINIMALLY COMPLETED” AREA: BUILD + SIGNING — MAKE IT RUNBOOK-GRADE
Add explicit runbook artifacts:
- BUILD/runbook_windows.md (PyInstaller/Nuitka paths; env pinning; offline builds)
- BUILD/ci_matrix.md (fast checks vs full checks)
- BUILD/signing_hooks/README.md (how to sign without exposing secrets)
- BUILD/versioning.md (how build ids relate to run ids and playbook versions)
Gates:
- build must output receipts + SBOM; signing is a separate optional lane.

P1075) “MINIMALLY COMPLETED” AREA: GUI → DEFINE READ MODEL CONTRACTS v2
GUI reads:
- UI/state.json (current case context, queue status, health, cap usage)
- UI/events.jsonl (stream)
- UI/panels/*.json (structured panel payloads)
Panel payload schemas:
- UI/panels/po_ledger.json
- UI/panels/quotelock.json
- UI/panels/forms.json
- UI/panels/hud_risk.json
Artifacts:
- schemas/ui_state.schema.json
- schemas/ui_event.schema.json
- schemas/ui_panels/*.schema.json
Rule:
- GUI never consumes raw internal store directly; only read model.

P1076) “MINIMALLY COMPLETED” AREA: WATCHERS/QUEUE — DEFINE JOB SCHEMA + IDENTITY
Job schema:
- job_id, job_type, scope_token_id, priority, created_ts
- inputs pointers, retry_policy, status transitions
Artifacts:
- schemas/job.schema.json
- QUEUE/jobs.jsonl (append-only)
- QUEUE/status.json (derived)
Gate:
- job runner must be idempotent; retries require deterministic seeds.

P1077) “MINIMALLY COMPLETED” AREA: LICENSE GOVERNOR — DEFINE THIRD-PARTY LOCK FORMAT
Third-party lock row:
- component_id, version, license_id, source_pointer, sha256(optional), allow_status
Artifacts:
- schemas/third_party_lock.schema.json
- LICENSES/third_party.lock.json
Gate:
- unknown license => staged only; cannot ship in release.

P1078) “MINIMALLY COMPLETED” AREA: ASSET STRATEGY v5 — DEFINE POINTER RECORDS
PointerRecord:
- pointer_id, kind (gdrive|local|url|cas), location, expected_integrity_key
- hydration_steps (local-only default), size_estimate
Artifacts:
- schemas/pointer_record.schema.json
- ASSET_VAULT/pointers.jsonl
Rule:
- FULL packs include pointer records; hydration is optional and operator-controlled.

P1079) SPEC VALIDATOR RUNNER v1 — ONE COMMAND THAT CHECKS EVERYTHING
CLI entry:
- litigationos validate --run <run_id> --scope <scope_token>
Checks:
- JSONSchema validate all artifacts
- cross-store consistency
- PO ledger referenced by packet compile
- QuoteVerified only where allowed
Outputs:
- VALIDATION/global_<run_id>.json
- VALIDATION/global_<run_id>.md (human)
Gate:
- “validate PASS” is required for RELEASE states.

P1080) “STARTER IMPLEMENTATION SET” — WHAT TO CODE FIRST (HIGH RETURN)
Priority coding targets (non-optional foundation):
1) schemas/ for: EvidenceAtom, FactPin, Quote types, PO ledger, VehicleSpec, Form specs, PacketProfile, ScopeToken
2) Governor validation runner (P1079) + basic ESL
3) PO ledger engine that can open/close POs with satisfactions
4) Forms fill plan generator that emits field traces and opens POs for missing traces
5) QuoteLock verifier record scaffolding (no promotion without records)
Rationale:
- these five create enforceable gates; everything else plugs into them.

P1081–P1180) RESERVED FOR NEXT Δ ACCEPTANCE
===============================================================================
END APPENDIX v2026-01-18.34
===============================================================================

===============================================================================
APPENDIX v2026-01-18.35 — HIGH-SIGNAL Δ PACK (P1181–P1320)
Theme: “Close remaining thin spots.” Convert the last “named but under-specified” areas into concrete, enforceable contracts: ModuleRegistry, Plugin ABI, Packfiles/CAS, Graph Migrations receipts, QueryPacks/ViewPacks, Local-LLM integration, and CI/Release discipline. Includes vetted open-source model pointers discovered via Hugging Face search (links).
===============================================================================

P1181) MODULE REGISTRY v2 — EVERYTHING RUNNABLE IS DECLARED (NO HIDDEN MODULES)
Goal: stop “module sprawl” and ensure every lane has a declared I/O contract.
ModuleRecord fields:
- module_id (stable), version, owner_lane (authority|evidence|forms|po|quotelock|graph|packets|ops|ui)
- entrypoint (python module:function OR exe path), cli_command (if any)
- input_artifacts[] (artifact_type enums), output_artifacts[]
- required_specs[] (schema refs), required_tools[] (tool_id refs)
- budgets (time/ram/disk), idempotency (true/false), retry_policy
- promotion_state (DEV|STAGED|RC|RELEASE) + required_tests
Artifacts:
- schemas/module_record.schema.json
- REGISTRY/modules.jsonl (append-only)
- REGISTRY/lanes.json (lane definitions)
Gate:
- Runner refuses to execute undeclared modules; Governor refuses to promote modules without their required test receipts.

P1182) PLUGIN ABI v1 — SAFE EXTENSIBILITY WITHOUT GIVING PLUGINS WRITE POWER
Goal: allow “new cores” without risking uncontrolled graph/state mutation.
Plugin categories:
- ExtractorPlugin (produces extraction products; cannot write graph)
- ValidatorPlugin (consumes artifacts and emits findings/tickets; can block)
- RendererPlugin (doc/pdf transform; receipts required)
- SearchPlugin (vector/lexical retrieval; read-only)
Plugin packaging:
- python wheel or folder plugin with manifest.json
Plugin manifest fields:
- plugin_id, version, license, entrypoints, capabilities (declared)
- allowed_artifact_io (types), forbidden_ops (default deny)
Artifacts:
- schemas/plugin_manifest.schema.json
- PLUGINS/installed/index.json
Gate:
- Plugin must pass LicenseGovernor + Spec validation; capabilities are enforced by Governor “sandbox wrapper.”

P1183) PACKFILES + CAS v1 — MORE ADVANCED THAN “EXTERNAL ASSETS”
Problem: keep FULL packs ≤700MB while preserving replayability, dedupe, and exact reconstruction.
Solution: content-addressable “PackfileStore” with pointer records:
- small artifacts shipped inline
- large artifacts stored as packfiles (chunked, deduped) or external pointers (gdrive/local)
Design:
- CAS objects stored by {oid = blake3(content)} or IntegrityKey-derived id (policy choice)
- Packfiles are bundles of CAS objects with index + chunk map
PointerRecord now supports kind=cas:
- pointer_record.location = "cas://<oid>" or "pack://<pack_id>#<oid>"
Hydration:
- “hydrate” command assembles required objects locally from packfiles or external sources, verifying IntegrityKey/oid
Artifacts:
- schemas/pack_index.schema.json
- ASSET_VAULT/cas/index.jsonl
- ASSET_VAULT/packfiles/<pack_id>.pack + <pack_id>.index.json
- TOOLS/hydrate_assets.py (local-only; no silent network)
Gates:
- FULL pack must never include bulky binaries unless they compress small; else pointer-only.
- Packet compile must declare which pointers were hydrated for the run; receipts recorded in Run Ledger.

P1184) WORLD-FIRST BUILDER v2 — REBUILD EVERYTHING LOCALLY, DETERMINISTIC
Goal: eliminate reliance on sandbox links and preserve “append-only” version lineage.
Builder responsibilities:
- verify repo structure + schemas present
- reconstruct CyclePacks from:
  - VERSIONS snapshots OR PATCHES + checkpoints
  - packfiles + pointer records (optional hydrate)
- produce:
  - FULL.zip (cap-safe)
  - CORE.zip (schemas/tools/specs)
  - LITE outputs pack (latest run artifacts only)
Artifacts:
- TOOLS/mbp_worldfirst_builder.py (already mandated by standing preference)
- TOOLS/builder_receipts/<run_id>.json
Gate:
- builder must perform testzip + schema validation + size budget report.

P1185) GRAPH MIGRATIONS RECEIPTS v2 — GOVERNED, IDEMPOTENT, DRIFT-DETECTING
Thin spot addressed: migrations were named, but lacked “receipt + drift model.”
Migration record:
- migration_id, from_version, to_version
- cypher_files[] pointers
- expected_constraints/indexes snapshot (hash)
- apply_trace (what was applied), drift_check_result
Artifacts:
- schemas/graph_migration.schema.json
- GRAPH/migrations/<migration_id>/{up.cypher,down.cypher,meta.json}
- GRAPH/migrations/receipts/<run_id>.jsonl
Gates:
- before graph writes: drift check must PASS (or open PO and block writes)
- down migrations are optional but if absent, must say “irreversible by design” in meta.

P1186) QUERYPACK + VIEWPACK CONTRACTS v2 — “BLOOMS / BRAINS” ARE BUILD ARTIFACTS
QueryPack:
- pack_id, version, intended_brain (CourtBrain|FormsBrain|EvidenceBrain|POBrain|JTCBrain)
- queries[] with parameters, expected_output_shape schema
ViewPack:
- layout definitions for Bloom/GUI panels; color semantics, node styles
Artifacts:
- schemas/query_pack.schema.json
- schemas/view_pack.schema.json
- GRAPH/querypacks/*.json
- GRAPH/viewpacks/*.json
Gate:
- query outputs must validate against expected shapes; prevents UI regressions.

P1187) LOCAL LLM INTEGRATION LANE v2 — OPEN-SOURCE ONLY, HOSTED LOCALLY
Goal: “LLM cannot mutate graph/state; validators/gates own state transitions.”
Runtime choices (local, operator-hosted):
- Ollama or llama.cpp server for generation
- local embedding service for vector store updates
Roles:
- LLM: propose (text-only) → Proposal artifacts
- Validators: check → Tickets
- Governor: commit → mutations
Artifacts:
- LLM/runtime_config.json (endpoints local only)
- LLM/prompt_policies.json (system prompts, tool limits)
- LLM/proposals/<run_id>.jsonl (append-only)
Gate:
- any LLM output used in FILE_READY must be mediated via Proposals→Validators→Governor.

P1188) RECOMMENDED OPEN-SOURCE MODELS (HUGGING FACE POINTERS; LINKS)
Document layout / DocQA / structured extraction:
- LayoutLMv3 base: https://hf.co/microsoft/layoutlmv3-base
- LayoutLMv2 base uncased: https://hf.co/microsoft/layoutlmv2-base-uncased
- LayoutLM Document QA: https://hf.co/impira/layoutlm-document-qa
Vision-document extraction (image-to-text):
- Donut base: https://hf.co/naver-clova-ix/donut-base
- Nougat base: https://hf.co/facebook/nougat-base
Visual-document retrieval (page-image embeddings; strong for scanned PDFs):
- ColPali v1.2: https://hf.co/vidore/colpali-v1.2
Embeddings (text):
- BGE small en v1.5: https://hf.co/BAAI/bge-small-en-v1.5
- E5 large v2: https://hf.co/intfloat/e5-large-v2
Key dataset pointers (for evaluation/benchmarks; not bundled—pointer-only):
- DocVQA: https://hf.co/datasets/lmms-lab/DocVQA

Policy:
- these are pointers and must be tracked in third_party.lock.json (license, source) and hydrated only by explicit operator action.

P1189) “MODEL GOVERNOR” v1 — MODELS ARE ASSETS WITH LICENSE + SIZE + POLICY
ModelRecord:
- model_id, source_url, license_id, intended_use (embedding|ocr|vision_retrieval|gen)
- local_storage_policy (pointer-only|packfile|inline ok)
- runtime_binding (ollama tag / gguf path / transformers id)
Artifacts:
- schemas/model_record.schema.json
- MODELS/registry.jsonl
Gates:
- unknown license or unknown runtime binding ⇒ staged only; cannot be used in RELEASE pipelines.

P1190) “LLM PROMPT HYGIENE” v1 — PREVENT CROSS-CASE BLEED AND FACT INVENTION
PromptPolicy:
- scope constraints: case_id/track_id required
- forbidden: invent facts, invent citations, promote QuoteCandidate
- required: cite pins for any factual claim; else label as “unverified candidate”
Artifacts:
- schemas/prompt_policy.schema.json
- LLM/policies/*.json
Gate:
- if LLM output lacks required structure, it cannot produce a Proposal artifact.

P1191) “INPUT NORMALIZATION” v2 — PATHS, IDS, AND TIMEZONES
Thin spot: inconsistent identity across stores.
Normalization:
- canonical IDs: case_id, evidence_id, authority_ref_id, po_id, form_id
- time: America/Detroit default; all timestamps ISO8601
- paths: store pointers, never raw absolute paths in portable artifacts
Artifacts:
- NORMALIZE/policy.json
- NORMALIZE/map_<run_id>.json
Gate:
- any artifact failing normalization is rejected by validator.

P1192) CI MATRIX v2 — FAST VS FULL, BOTH REPRODUCIBLE
Fast CI (minutes):
- schema validation
- unit tests for PO/QuoteLock/Forms fill plan generation
- lint + license lock check
Full CI (long):
- golden tests
- PBT subset
- chaos suite minimal
- pack cap check with size budget report
Artifacts:
- CI/matrix.yml (document)
- CI/receipts/<run_id>.json
Gate:
- RC promotion requires full CI receipts.

P1193) RELEASE ARTIFACT SPLITTING v2 — CAP-SAFE WITHOUT LOSING LINEAGE
Artifacts (deterministic names):
- <ROOT>__<version>__CORE.zip (schemas/tools/specs)
- <ROOT>__<version>__FULL.zip (cap-safe; pointer+packfile aware)
- <ROOT>__<version>__CYCLEPACK_<run_id>.zip (latest outputs)
Policy:
- FULL is capped; CORE is always small; CYCLEPACK can be shared separately.
Gate:
- every release must include CORE; FULL optional if under cap, else packfile+pointer plan required.

P1194) “MINIMALLY COMPLETED” AREA: ERROR TAXONOMY + INCIDENT RUNBOOK v1
Error taxonomy:
- E_SCOPE, E_SCHEMA, E_AUTH_SNAPSHOT, E_PIN_RESOLVE, E_QUOTELOCK, E_PO, E_FORMS, E_GRAPH, E_PACK, E_BUDGET
Incident response:
- capture run ledger + minimal reproduction pack (CORE + failing artifacts)
Artifacts:
- OPS/errors.md
- OPS/incidents/<run_id>.md
- OPS/repro_packs/<run_id>/*

P1195) “MINIMALLY COMPLETED” AREA: RETENTION + PRUNING POLICY v1 (APPEND-ONLY SAFE)
Goal: avoid runaway disk while preserving append-only semantics.
Mechanism:
- run-level pruning: keep receipts + summaries; rotate large intermediates to packfiles
- never delete originals; only move derived artifacts behind pointers/packfiles
Artifacts:
- RETENTION/policy.json
- RETENTION/actions_<run_id>.json
Gate:
- pruning is a ticketed action; default is dry-run.

P1196) NEXT ACCEPTANCE SET (DGC5) — ENFORCE, THEN EXPAND
Ship order:
1) ModuleRegistry + Plugin ABI (P1181,P1182)
2) Packfiles/CAS + hydrate tooling + builder receipts (P1183,P1184)
3) Graph migrations receipts + drift check gate (P1185)
4) QueryPack/ViewPack contracts (P1186)
5) ModelGovernor + PromptPolicy (P1189,P1190)
Then expand: more brains, more vehicle libraries, more court-specific profiles (only when sourced).

P1197–P1320) RESERVED FOR NEXT Δ ACCEPTANCE
===============================================================================
END APPENDIX v2026-01-18.35
===============================================================================

===============================================================================
APPENDIX v2026-01-18.36 — HIGH-SIGNAL Δ PACK (P1321–P1500)
Theme: “Retrieval + Transcript + Redaction + Evaluation.” Finish the under-specified “RAG brain” and “hearing/transcript” lanes with contracts, gates, and model pointers. Adds a full RetrievalSpec/ChunkSpec/ContextPackSpec, audio/transcript pipelines with diarization, sealed/public redaction lane, and an evaluation harness (offline, replayable). Still bound to AuthoritySnapshot + Forms-First + PO ledger + QuoteLock + replayability + cap-safe packaging.
===============================================================================

P1321) RETRIEVAL CORE v3 — HYBRID RAG WITH GRAPH FILTERS (READ-ONLY)
Goal: Retrieval is a governed subsystem with explicit query objects, budgets, and auditable traces.
Architecture:
- GraphFilter stage (Neo4j read) → CandidateDocIDs
- Lexical stage (BM25) → candidate spans
- Vector stage (Qdrant/FAISS) → candidate spans
- Rerank stage (cross-encoder) → final context set
- ContextPack builder → minimal, pinned, budgeted context for downstream (LLM or human)
Hard rule:
- Retrieval never asserts facts; it returns pointers/pins and candidates.

P1322) RETRIEVALSPEC SCHEMA v1 — HOW A QUERY RUN IS DEFINED
RetrievalSpec fields:
- retrieval_spec_id, version
- stores: {graph:true/false, bm25:true/false, vector:true/false, rerank:true/false}
- budgets: {max_candidates, max_context_chars, max_docs, max_time_ms}
- filters: {case_ids, evidence_types, date_ranges, authority_snapshot_version required}
- reranker_model_id (ModelGovernor)
- output: {context_pack_profile_id}
Artifacts:
- schemas/retrieval_spec.schema.json
- RETRIEVAL/specs/*.json
Gate:
- Query runs must reference a RetrievalSpec; “ad hoc retrieval” is forbidden in production runs.

P1323) CHUNKSPEC + EMBEDDINGRECORD v2 — ONE CHUNK IDENTITY ACROSS STORES
ChunkSpec:
- chunk_id, evidence_id, source_locator (page/span/time), text_pointer, token_count
- chunk_kind (order|motion|transcript|email|img_ocr|authority|other)
- normalization (lowercase rules, whitespace), language
EmbeddingRecord:
- chunk_id, model_id, vector_pointer, dims, created_ts
BM25Record:
- chunk_id, term_stats_pointer (optional), index_name
Artifacts:
- schemas/chunk.schema.json
- schemas/embedding_record.schema.json
- schemas/bm25_record.schema.json
- RETRIEVAL/chunks.jsonl
- RETRIEVAL/embeddings.jsonl
Gate:
- chunk text pointers must be resolvable; else chunk is invalid.

P1324) CONTEXTPACKSPEC v2 — “MIN CONTEXT” IS CONFIGURABLE, PINNED, AND BUDGETED
ContextPackSpec:
- profile_id
- required sections: {case_state, key_orders, controlling_authority_refs, service_status, deadlines, PO_snapshot_ref}
- optional sections: {top_evidence_pins, contradictions, denial_surface, exhibits_index}
- budget: chars per section, total chars
Outputs:
- CONTEXTPACK/<run_id>.md (human readable)
- CONTEXTPACK/<run_id>.json (machine)
Hard rule:
- any factual statement in ContextPack must carry a FactPin or be labeled “unverified candidate.”

P1325) RERANKER GOVERNOR v1 — RERANK IS A MODEL WITH LICENSE + POLICY
Add ModelGovernor entries (pointers; hydrate explicit):
- BAAI/bge-reranker-v2-m3 (Apache-2.0): https://hf.co/BAAI/bge-reranker-v2-m3
- cross-encoder/ms-marco-MiniLM-L6-v2 (Apache-2.0): https://hf.co/cross-encoder/ms-marco-MiniLM-L6-v2
Notes:
- bge-reranker provides strong multilingual; ms-marco MiniLM is lightweight and stable.
Gate:
- rerank stage must record model_id + version + inference settings in run ledger.

P1326) TRANSCRIPT LANE v3 — AUDIO/VIDEO→TRANSCRIPT→PINS→QUOTELOCK
Goal: treat transcripts like evidence with reopen recipes.
Pipeline:
- ingest media → extract audio (ffmpeg) → ASR → diarization → align timestamps → segment → pins
Artifacts:
- MEDIA/registry.jsonl
- TRANSCRIPTS/<run_id>/segments.jsonl (time-aligned)
- TRANSCRIPTS/<run_id>/transcript.txt|json
- TRANSCRIPTS/<run_id>/pins.jsonl (audio_time pins)
- TRANSCRIPTS/<run_id>/quotecandidates.jsonl
Gates:
- transcript text used in FILE_READY must pass QuoteLock verification (dual extraction or manual confirm).
- diarization is “helpful but not dispositive”; speaker labels remain candidates unless confirmed.

P1327) ASR MODEL POINTERS (LOCAL; LICENSE-GOVERNED)
Recommended pointers:
- openai/whisper-large-v3: https://hf.co/openai/whisper-large-v3
- openai/whisper-large-v3-turbo: https://hf.co/openai/whisper-large-v3-turbo
- distil-whisper/distil-large-v3 (MIT): https://hf.co/distil-whisper/distil-large-v3
- Systran/faster-whisper-large-v3 (ctranslate2): https://hf.co/Systran/faster-whisper-large-v3
Policy:
- choose a “fast” and “accurate” profile; record chosen profile in transcript receipts.

P1328) DIARIZATION POINTERS (LOCAL; LICENSE-GOVERNED)
Recommended pointer:
- pyannote/speaker-diarization-3.1 (MIT): https://hf.co/pyannote/speaker-diarization-3.1
Artifacts:
- MODELS/registry.jsonl entry + runtime binding
Gate:
- diarization requires explicit consent profile if any privacy constraints apply; outputs go through redaction lane before public packets.

P1329) TRANSCRIPT RECEIPTS v2 — MAKE TRANSCRIPTION REPLAYABLE
TranscriptReceipt fields:
- media_id, asr_model_id, diarization_model_id (optional)
- preprocessing: sample rate, channels, normalization
- decoding settings, timestamps policy, chunk sizes
- checksum of audio extraction output (optional)
Artifacts:
- schemas/transcript_receipt.schema.json
- TRANSCRIPTS/<run_id>/receipt.json
Gate:
- any transcript in a packet must have a receipt.

P1330) REDACTION LANE v3 — SEALED/PUBLIC DUAL OUTPUTS WITH TRACE MAP
Goal: create “public-safe” and “sealed/full” variants deterministically.
Inputs:
- packet artifacts + privacy_mode + redaction rules
Outputs:
- PACKETS/<run_id>/SEALED/*.pdf
- PACKETS/<run_id>/PUBLIC/*.pdf
- REDACTION/<run_id>/map.json (what was redacted, where, why)
Redaction rule sources:
- operator-defined policies; and court orders if pinned
Gates:
- redaction must never delete content; it masks and records mapping.
- redaction must not alter evidence meaning (best effort); if risk, open PO and flag.

P1331) REDACTIONSPEC SCHEMA v1 — CONFIGURABLE, AUDITABLE
RedactionSpec:
- spec_id, privacy_mode, patterns (regex), entity lists, page regions
- allowlist overrides, logging policy, output naming rules
Artifacts:
- schemas/redaction_spec.schema.json
- REDACTION/specs/*.json
Gate:
- any public packet must cite its RedactionSpec + map.

P1332) EVALUATION HARNESS v2 — OFFLINE BENCHMARKING WITH REPLAY
Goal: measure retrieval and extraction quality without internet and without fabricating results.
Eval types:
- Retrieval eval: precision@k, recall@k against labeled pins
- QuoteLock eval: match rate vs verified quotes
- Form fill eval: trace coverage rate, missing-field PO rate
- Deadline engine eval: correctness on pinned orders
Artifacts:
- EVAL/suites/*.json (suite definitions)
- EVAL/results/<run_id>.json
- EVAL/reports/<run_id>.md
Gates:
- modules promoted to RC require passing their relevant eval suite.

P1333) “LABELED PINS” DATASET v1 — LOCAL GROUND TRUTH, CAP-SAFE
Approach:
- store only references: (evidence_id, pin_ref, label) + short notes
- do not store bulky documents in eval datasets
Artifacts:
- EVAL/ground_truth/pins.jsonl
- schemas/ground_truth_pin.schema.json

P1334) “DENIAL SURFACE” EVAL v1 — PROVE RED TEAM IMPROVEMENTS
Metrics:
- count of OPEN POs in core gates
- count of unknown deadlines
- service proof completeness rate
- quote verified coverage
- packet validation pass rate
Artifacts:
- EVAL/denial_surface/<run_id>.json

P1335) “MINIMALLY COMPLETED” AREA: VECTOR STORE GOVERNANCE v1
Define VectorStoreConfig:
- store type (qdrant|faiss), path pointers, dims, metric
- namespace policy: per case_id separation
- retention policy: chunk pruning via pointer/packfile
Artifacts:
- schemas/vector_store_config.schema.json
- RETRIEVAL/vector_store_config.json
Gate:
- embeddings cannot mix cases unless explicitly allowed by ScopeToken.

P1336) “MINIMALLY COMPLETED” AREA: AUTHORITYSNAPSHOT ACQUISITION PLAN v2 (INPUT-DEPENDENT)
Because web scraping is not assumed, the system requires operator-provided source bundles or pinned downloads.
AuthoritySnapshot inputs:
- official PDFs/HTML saved locally with pointer records
- effective-date metadata captured in snapshot index
Outputs:
- AUTHORITY/snapshots/<ver>/authority_index.jsonl
- AUTHORITY/snapshots/<ver>/pin_map.jsonl
Gates:
- propositions must cite authority_ref_id with effective date; out-of-snapshot propositions are blocked.

P1337) NEXT ACCEPTANCE SET (DGC6) — “MAKE RAG PROVABLE”
Ship order:
1) RetrievalSpec + ChunkSpec + ContextPackSpec + validator (P1322–P1324)
2) Transcript lane receipts + pins + QuoteLock integration (P1326–P1329)
3) Redaction lane dual outputs + map (P1330–P1331)
4) Eval harness + labeled pins dataset + denial surface metrics (P1332–P1334)
5) Vector store governance (P1335)

P1338–P1500) RESERVED FOR NEXT Δ ACCEPTANCE
===============================================================================
END APPENDIX v2026-01-18.36
===============================================================================

===============================================================================
APPENDIX v2026-01-18.37 — HIGH-SIGNAL Δ PACK (P1501–P1740)
Theme: “Michigan Authority + Forms Graph Brain becomes executable.” Close the remaining thin spots around (1) AuthoritySnapshot governance, (2) SCAO/FOC/MC form library + field overlays, (3) Court/Jurisdiction graph modeling and Bloom viewpacks, (4) Case law ingestion without hallucinated holdings, (5) procedural profiles (trial→COA→MSC→JTC), and (6) record-survival hearing mode. All additions preserve: MI-only authority lock, pin-required claims, Forms-First, PO ledger enforcement, QuoteLock promotion rules, replayability, and cap-safe packaging.
===============================================================================

P1501) “MICHIGAN LAW PACK” v1 — AUTHORITYSNAPSHOT INPUTS ARE ARTIFACTS, NOT ASSUMPTIONS
Goal: AuthoritySnapshot is built from operator-provided official sources saved locally (or as pointer records). The snapshot is a compiled product with indexes and pin maps; no web scraping is assumed.
LawPack types (inputs):
- MCR Pack (rules PDFs/HTML dumps saved locally)
- MCL Pack (statute text dumps saved locally)
- MRE Pack
- Benchbook Pack (official benchbooks)
- SCAO Forms Pack (official forms + instructions)
- MSC Administrative Orders Pack (official)
- Local Administrative Orders Pack (court-specific; pinned)
- Published Caselaw Pack (MSC + published COA opinions)
Artifacts:
- AUTHORITY/packs/<pack_id>/{manifest.json, sources/*, pointers.jsonl}
- schemas/law_pack_manifest.schema.json
Hard rule:
- A LawPack is never “active” unless it has a manifest + pointer records + an ingestion receipt.

P1502) AUTHORITYSNAPSHOT BUILD PIPELINE v2 — COMPILE, INDEX, PINMAP, EFFECTIVE DATES
AuthoritySnapshot outputs (per snapshot version):
- authority_index.jsonl: AuthorityRef rows (type, source, section, effective date fields, pointer to text)
- authority_pin_map.jsonl: Pin locators for each AuthorityRef (page/line/offset)
- authority_toc.json: navigable table of contents
- authority_receipt.json: build receipts (inputs, versions, tools)
AuthorityRef minimal schema (expanded):
- authority_ref_id, kind (MCR|MCL|MRE|Benchbook|SCAOForm|MSC_AO|Local_AO|Caselaw_Pub)
- citation_key (normalized), section_path (e.g., “3.310(B)(2)” style; no quotes)
- effective_start, effective_end (nullable)
- source_pointer (pack pointer), text_pointer (extracted normalized text)
- pin_map_pointer (to authority_pin_map entries)
Gates:
- out-of-snapshot authority usage is blocked at proposition level.
- effective-date mismatch opens PO (requires updated snapshot or proof of applicability).

P1503) “AUTHORITYTRIPLE” CONTRACT v3 — PROPOSITION→AUTHORITY→PINPOINT, NO QUOTES BY DEFAULT
AuthorityTriple fields:
- proposition_id (stable), proposition_text (non-quoted; summary only)
- authority_refs[]: {authority_ref_id, pinpoint_ref (pin_id), effective_date_used}
- scope_token_id, created_ts
- status (CANDIDATE|VERIFIED) where VERIFIED requires QuoteLock if verbatim text is included
Artifacts:
- schemas/authority_triple.schema.json
- AUTHORITY/triples/<case_id>.jsonl (append-only)
Rule:
- If verbatim rule text is needed, it must be stored as QuoteVerified with pin_ref; otherwise store only the normalized proposition.

P1504) CASELAW INGEST v2 — HOLDINGS ARE NEVER INVENTED; THEY ARE PINNED EXTRACTS
CaselawDoc record:
- case_id (court+date+name normalized), reporter cite if known (as text; no guessing)
- doc_pointer, extracted_text_pointer, pin_map_pointer
- headnote_candidates (internal only), holdings (only as pinned excerpts)
Holdings rule:
- “Holding” nodes can exist only as:
  - HoldingExtract nodes with QuoteVerified text spans + pin refs
  - or as Proposition nodes backed by those extracts
Artifacts:
- CASELAW/registry.jsonl
- CASELAW/holdings_extracts.jsonl
Gates:
- any claim “X held Y” requires a HoldingExtract pin; otherwise it is blocked or labeled “candidate.”

P1505) “COURT BRAIN” GRAPH MODEL v3 — JURISDICTIONS ARE FIRST-CLASS NODES
Goal: model Michigan court structure as an executable map for forms/vehicles/procedure.
Core nodes:
- Court (level, county, division)
- Docket/Case (case_id, type, parties, status)
- Judge (name, court, role, assignment history)
- ProcedureLane (trial|COA|MSC|JTC|FOIA)
- Vehicle (relief→procedure mapping; Forms-First)
- Form (SCAO/MC/FOC/COA forms)
- AuthorityRef (from snapshot)
- Order/Motion/Filing (as artifacts with pins)
Edges (non-exhaustive):
- Court HAS_DIVISION Division
- Case FILED_IN Court
- Case ASSIGNED_TO Judge
- Vehicle GOVERNED_BY AuthorityRef
- Vehicle REQUIRES_FORM Form
- Form INSTRUCTED_BY AuthorityRef (instructions)
- Filing SUPPORTS Vehicle (by purpose)
- Order TRIGGERS Deadline
- EvidenceAtom SUPPORTS Filing (via pins)
Gates:
- edges do not imply truth; truth claims require EvidencePins/AuthorityPins.

P1506) “PROCEDURE PROFILE” v2 — TRIAL→COA→MSC→JTC AS CONFIGURABLE PLANS
ProcedureProfile fields:
- profile_id, lane (trial|coa|msc|jtc), court_level
- allowed vehicles list (VehicleSpec ids)
- default packet profile (Validation profile)
- service defaults (ServiceChain templates)
- standard outputs list (packets, affidavits, notices, etc.)
Artifacts:
- schemas/procedure_profile.schema.json
- PROCEDURE/profiles/*.json
Rule:
- A lane cannot execute a vehicle not present in the active ProcedureProfile.

P1507) “APPELLATE PACK” LANE v1 — RECORD-FIRST, PIN-FIRST, FORMS-FIRST
Goal: standardize production of appellate-ready artifacts without inventing record contents.
Artifacts:
- APPEAL/<run_id>/record_index.csv (orders, transcripts, exhibits, filings; pinned)
- APPEAL/<run_id>/issue_matrix.json (issues→propositions→pins)
- APPEAL/<run_id>/standard_of_review.json (as propositions with authority pins)
- APPEAL/<run_id>/packet_draft/ (DRAFT unless PO satisfied)
Gates:
- if transcript missing, PO opens (Acquire transcript plan). No “as if transcript said X.”

P1508) “JTC PACK” LANE v2 — MISCONDUCT CLAIMS REQUIRE RECORD PINS + CATEGORY TAGS
Goal: keep JTC narratives grounded and categorized without speculative accusations.
Artifacts:
- JTC/<run_id>/allegation_rows.jsonl: {category, event, pin_refs, authority_refs (code/benchbook), severity_score (heuristic), disclosure_mode (sealed/public)}
- JTC/<run_id>/timeline.jsonl (bitemp, pinned)
- JTC/<run_id>/packet_draft.md|docx (DRAFT unless POs satisfied)
Gates:
- any direct quotation of judge/counsel must be QuoteVerified.
- any allegation without record pin is labeled “candidate” and cannot be FILE_READY.

P1509) FORMS LIBRARY v3 — FORMS ARE VERSIONED ASSETS WITH FIELD DEFINITIONS
FormsCatalog fields:
- form_id, title, edition/version if known, source_pointer (official), instructions_pointer
- form_kind (MC|FOC|SCAO|COA|MSC|JTC), jurisdiction tags
- fields[] (canonical field ids + types)
Artifacts:
- FORMS/catalog/index.json
- FORMS/forms/<form_id>/{source/*, extracted/*, meta.json}
- schemas/forms_catalog.schema.json

P1510) FIELD OVERLAY ENGINE v2 — PDF COORDS + DOCX MERGEFIELDS, BOTH GOVERNED
OverlayMap types:
- PDFOverlayMap: {page, bbox, field_id, font policy, alignment}
- DOCXFieldMap: {mergefield/bookmark id, field_id}
Artifacts:
- FORMS/overlays/<form_id>/vNNNN/pdf_overlay.json
- FORMS/overlays/<form_id>/vNNNN/docx_fields.json
- schemas/pdf_overlay.schema.json
- schemas/docx_field_map.schema.json
Gates:
- overlay maps must be validated against the source form version (hash/pointer). If source changes, PO opens and overlay is staged.

P1511) FORMS “TRACE COVERAGE” METRIC v1 — MEASURE WHAT IS ACTUALLY AUTOMATED
Metrics:
- required field count, traced field count, missing trace count
- traced-by evidence vs traced-by computed vs traced-by operator constant (constants must be justified)
Outputs:
- FORMS/coverage/<run_id>.json
- FORMS/coverage/<run_id>.md
Gate:
- missing traces open POs; FILE_READY cannot conceal missing data.

P1512) “PROCEDURAL SANITY CHECKER” v2 — MOTION LIMITS, PREREQS, AND SERVICE AS FIRST-CLASS FAILURES
Thin spot addressed: earlier “preflight” was described; now it becomes a dedicated checker with explicit findings objects.
Findings schema:
- finding_id, kind (deadline|service|fee|notice|jurisdiction|standing|prereq|format|caption)
- severity (blocker|warning|info), evidence/authority pins, fix_plan_ref
Artifacts:
- schemas/finding.schema.json
- VALIDATION/findings/<run_id>.jsonl
Gates:
- any blocker finding blocks FILE_READY and opens POs.

P1513) “HEARING MODE DAEMON” v2 — REAL-TIME RECORD SURVIVAL CHECKLISTS
Goal: when a hearing is imminent, generate time-bound checklists and OOP triggers without inventing facts.
Inputs:
- hearing event (date/time), active issues, missing record items
Outputs:
- HEARING/<run_id>/checklist.md (what to bring, what to request, what to preserve)
- HEARING/<run_id>/offer_of_proof_triggers.json (conditions that should trigger OOP)
- HEARING/<run_id>/objection_bank.json (proposition-based; no quotes unless verified)
Gates:
- hearing-mode outputs are “operator aids”; they do not assert what occurred unless pinned to transcript.

P1514) “ORDERCHAIN” + “SERVICECHAIN” COUPLING v2 — ORDERS DRIVE DEADLINES, DEADLINES DRIVE SERVICE
Add explicit linkage rules:
- Every Order node with a pin can emit Deadline objects (computed).
- Each Deadline object can emit ServicePlan requirements.
Artifacts:
- ORDERCHAIN/<case_id>/order_events.jsonl
- DEADLINES/<case_id>/deadline_events.jsonl
- SERVICE/<case_id>/service_events.jsonl
Gate:
- missing order text/pins prevents computing deadlines (OPEN PO).

P1515) “CONTRADICTION MAP” v2 — FORMALIZE WHAT COUNTS AS A CONTRADICTION
Contradiction record:
- contradiction_id, type (fact-vs-fact|order-vs-order|testimony-vs-record|date-vs-date)
- side_a pin refs, side_b pin refs
- materiality score, affected vehicles/POs
Artifacts:
- schemas/contradiction.schema.json
- CONTRADICTIONS/<case_id>.jsonl
Rule:
- contradictions are not “resolved” by narrative; resolution requires a pinned explanation or court order.

P1516) BLOOM/GUI VIEWPACKS v3 — 3–5 BRAINS ARE CONFIG, NOT AD-HOC
Define default “brains” (viewpacks + querypacks):
1) CourtAuthorityBrain (courts, lanes, vehicles, forms, authority)
2) CaseProcedureBrain (case, orders, deadlines, service, filings)
3) EvidenceContradictionBrain (evidence atoms, pins, contradictions, quote states)
4) JudicialConductBrain (events, transcript pins, allegation rows, severity)
5) OperationsBrain (queue, runs, budgets, cap usage, incidents)
Artifacts:
- GRAPH/viewpacks/<brain>.json
- GRAPH/querypacks/<brain>.json
Gate:
- viewpacks validate against UI panel schemas and query output shapes.

P1517) “COLOR/THEME PACK” CONTRACT v1 — THEMES ARE DATA, NOT HARD-CODED
ThemePack fields:
- theme_id, palette (named colors), node style mappings, edge style mappings
- accessibility hints (contrast targets), dark/light variants
Artifacts:
- UI/themes/*.json
- schemas/theme_pack.schema.json
Rule:
- theme can change without altering graph logic; UI reads ThemePack only.

P1518) “IMPORT/EXPORT” v2 — GRAPH EXPORTS ARE REPLAYABLE AND CAP-SAFE
Exports:
- graph snapshots (cypher dump optional), csv nodes/edges, bloom json (if supported)
- all exports include a manifest + receipts + schema version stamps
Artifacts:
- EXPORTS/<run_id>/{graph.csv,nodes.csv,edges.csv,manifest.json,receipt.json}
Gate:
- exporting cannot drop identity keys; import must be able to rehydrate stable IDs.

P1519) DGC7 (DECISION GOLDEN COMPASS) — “UPWARD, BUT MEASURED”
Upgrade DGC scoring to include:
- “contract completion” (schemas + validators + receipts) as a multiplicative booster
- “denial surface reduction per LOC” as ROI metric
- “replay integrity delta” (how much more replayable)
- “cap safety delta” (bytes added vs dedupe)
Outputs:
- DGC/scorecard_<run_id>.json (full metrics)
- DGC/decision_<run_id>.md (why this delta was chosen)
Rule:
- DGC can recommend broad expansions, but the system ships only enforceable contracts first.

P1520) NEXT ACCEPTANCE SET (DGC7) — “MAKE MI AUTH + FORMS SHIP-ABLE”
Ship order:
1) LawPack manifests + AuthoritySnapshot builder receipts (P1501–P1502)
2) Forms catalog + overlay maps schemas + trace coverage metrics (P1509–P1511)
3) Procedure profiles + sanity checker findings objects (P1506–P1512)
4) Brain viewpacks/querypacks + UI theme packs (P1516–P1517)
5) Hearing mode daemon + order/service coupling + contradiction map (P1513–P1515)
Then expand: more vehicles, more court-specific packet profiles (only when sourced).

P1521–P1740) RESERVED FOR NEXT Δ ACCEPTANCE
===============================================================================
END APPENDIX v2026-01-18.37
===============================================================================


---
## Δ v0006 Ingest + Core-Patch Explosion (v2026-01-18.38)
### 0) Ingested upstream sources (preserved verbatim)
- SOURCES/original/LitigationOS Graph + LLM Blueprint for MEEK Tracks.md
- SOURCES/original/FRED PRIME LEGAL INTELLIGENCE OPERATIONS MANUAL.txt
- SOURCES/original/TRUE MASTER operations.txt
- SOURCES/original/LAW LIBRARIES LINKS.txt
- SOURCES/original/all michigan court form links ALL JURISDICTIONS.md
- SOURCES/original/Superpin Codex Instructions.pdf
- SOURCES/original/Branch · Superpin Codex Instructions-2.pdf

### 1) New missing-but-required cores (high-signal)
1. **BinderCompletenessGate**: compares binder/index CSV→actual files; emits MISSING_LIST + acquire plan; blocks PACKAGING.
2. **DocContainerIntegrityGate**: validates `.docx` (ZIP structure), `.pdf` (openable), `.zip` (testzip); emits CORRUPT_LIST; never modifies originals.
3. **AuthoritySourceIndex + RefreshPlan**: converts raw authority/form URL lists into a governed SourceIndex (official-first), with effectivity windows + local mirror recipes.
4. **FormsFirst Crosswire Builder**: turns SCAO form catalog → graph nodes → governing rule pointers → VehicleMap templates.
5. **SchemaGov + Migration Engine**: versioned constraints/indexes + compatibility checks across Neo4j + side stores; emits MIGRATION_PLAN + APPLY/ROLLBACK scripts.
6. **Capability / Permission Model (LLM read-only)**: LLM may propose mutations but cannot apply; only Gate/Validator actors can write; every write requires CapabilityToken + audit trail.
7. **Replayability Core (event-sourced)**: crash-safe queue + append-only event log → deterministic replays; run_id + step_id + inputs hash → idempotent outputs.
8. **QuoteLock Workbench**: candidate quotes are tagged/held until verified by independent extractors; verified-only can pass PCG.
9. **External Asset CAS**: advanced pointer strategy (content-addressed, chunked) + optional rclone fetch; keeps FULL zip under 700MB.
10. **Decision Golden Compass (DGC)**: always-upward optimizer that selects next actions using impact/risk/dependency/coverage metrics; never regresses without explicit rollback.

### 2) Decision Golden Compass (installed into core directive)
**Goal:** Every cycle produces net upward movement in (a) legal actionability, (b) engineering determinism, (c) evidence admissibility/traceability, (d) user-run reliability.
**DGC Inputs (measured each run):**
- Coverage: % of required artifacts produced; % POs satisfied; % sources indexed.
- Reliability: crash rate; idempotency violations; test pass rate; validator FAIL counts.
- Actionability: SBNA confidence; vehicle eligibility PASS counts; service/deadline pass.
- Debt: open FIXLIST size; missing evidence count; unresolved authority pinpoints.
**DGC Rule:** pick the highest expected-value improvement that (1) reduces FAIL surface, (2) increases proof/traceability, and (3) does not violate authority/truth locks.
**DGC Mechanics:**
- Maintain `KSTORE/DGC_SCORECARD.json` and `KSTORE/DGC_QUEUE.jsonl`.
- Each candidate change is scored: `EV = (Impact*Urgency*Reusability) / (Risk*Cost*ScopeLeak)`.
- Any regression triggers auto-rollback + FIXLIST; no upgrade ships without Verify cycle.
**DGC Output:** ranked next-steps + gated execution plan; never infinite wandering; convergence means diminishing EV.

### 3) External assets (better than simple pointers)
Replace naive `/ASSETS_EXTERNAL/` with **CAS+Manifests**:
- `ASSETS/CAS/` stores only small metadata locally.
- Each large asset has: `asset_id` (sha256), `size`, `mime`, `origin_pointer`, `license`, `retrieval_recipe`.
- Optional **chunk map** (`zstd-chunked`) for resumable pulls.
- `TOOLS/litos_assets.py` governs add/fetch/verify; builders can reconstruct packs by pulling assets on-demand.
- FULL zip includes only `ASSETS/index.json` + receipts; never embeds large binaries.

### 4) Replayability + crash safety
- **SQLite-backed job queue** with leases + retries + dead-letter.
- **Event log** JSONL: every step emits START/END/FAIL with inputs digest + outputs list.
- **Idempotency**: every output path derived from `{run_id, step_id, content_digest}`; overwrites forbidden unless explicitly `--overwrite`.
- **Replay**: `TOOLS/litos_eventlog.py replay --run <id>` rebuilds outputs from recorded inputs.

### 5) Schema governance (Neo4j + stores)
- `SCHEMA/neo4j/` contains: constraints, indexes, label conventions, rel-types, property specs.
- `SCHEMA/migrations/` uses semver: `001_init`, `002_add_constraints`, ...; each migration has APPLY + VERIFY + ROLLBACK.
- `SCHEMA/contracts/` hosts JSON Schema for CSV imports (nodes/edges) + validator.
- Store-specific: Qdrant collections schema; SQLite table schema; filesystem contract.

### 6) Forms-first crosswire blueprint (from ingested blueprint)
From the uploaded blueprint, formalize **domain node kits** per MEEK track:
- MEEK1 nodes: Person/Org/Property/LeaseAgreement/CourtCase/LegalDocument/Event/Issue.
- MEEK2 nodes: Person/Child/CourtCase/LegalDocument/Event/Issue.
- MEEK3 nodes: PPO/ShowCause/Contempt nodes + speech/evidence nodes.
- MEEK4 nodes: Judge/Court/Order/Transcript/JTCComplaint/CanonIssue.
Each kit must map to: (a) required evidence atoms, (b) governing MI authority pointers, (c) SCAO/MC/FOC form candidates, (d) PO ledger obligations.

### 7) AuthoritySnapshot + SourceIndex (from link libraries)
Use `DATA/mi_source_index_v0006.json` generated from the link corpora:
- Tier 0 (official MI): courts.michigan.gov, SCAO forms, MI rules PDFs, MI benchbooks.
- Tier 1 (official federal overlay): mieb.uscourts.gov etc.
- Tier 2 (secondary): Cornell LII, Justia; **research-only**, not authority.
Gates: filing-ready outputs may cite only Tier 0/1 sources and must include pinpoints + effectivity.

### 8) PO ledger coupling (required artifacts)
Every run that proposes an action must emit:
- `ARTIFACTS/PO_LEDGER.json` (PO id, authority pointer, evidence pointer(s), status, validator signature).
- `ARTIFACTS/PO_GRAPH.cypher` (ProofObligation nodes + SATISFIES edges).
PCG PASS requires all mandatory POs satisfied.

### 9) QuoteLock integration
- Candidate quotes stored as `QUOTE_CANDIDATE` with extractor metadata.
- Verification requires ≥2 independent extractors (e.g., PDF text + screenshot or alternate parser) with byte-range/pageno match.
- Only `QUOTE_VERIFIED` may flow into filing drafts.

### 10) New tools added in v0006
- `TOOLS/litos_link_catalog.py` → builds MI source index JSON/CSV from URL corpora.
- `TOOLS/litos_binder_gate.py` → checks binder/index CSV against folder tree; outputs missing list.
- `TOOLS/litos_doc_integrity.py` → safe validation of docx/pdf/zip containers; outputs corrupt list.

### 11) Minimal-completion sweep
Areas that were historically under-specified are now explicitly governed:
- **Repro builds**: lockfiles, CI pipelines, signing hooks, deterministic build inputs.
- **Runner safety**: read-only default; explicit `--apply` for mutations.
- **Data lineage**: every derived artifact points back to source path + extractor + time.
- **Governance**: regression suite + golden queries + rollback discipline.


---
## Δ v0007 Contracts+BLOOM+CI (v2026-01-18.39)
### 1) Graph Contracts (hard requirement)
- `SCHEMA/contracts/nodes_row.schema.json` and `edges_row.schema.json` define minimum row-level contracts for nodes/edges CSVs.
- Validator: `python TOOLS/litos_graph_contracts_validate.py --nodes <nodes.csv> --edges <edges.csv> --outdir OUT --schema-dir SCHEMA/contracts --check-referential`.
- Gate: any Neo4j import/export pipeline MUST run this before ingest; failures produce FIXLIST and block packaging.
### 2) Bloom Perspective Pack (deterministic captions)
- `BLOOM/perspective/perspective_pack.json` sets caption fields and label mapping for consistent visual browsing.
- `BLOOM/perspective/IMPORT_CHECKLIST.md` provides a repeatable import checklist.
### 3) CI + Repro builds + Signing hooks
- `CI/README.md` sets discipline: pinned deps, contract validation, zip integrity, manifest generation, build gating.
- `.github/workflows/ci.yml` is a starter pipeline (replace example paths with real once repo has example CSVs).
- `BUILD/sign_exe.ps1` signs an .exe when signtool+cert are available; otherwise emits a clear FAIL without modifying anything.
### 4) Permission model (capability tokens, expanded)
- All mutations to graph/state require an issued `CapabilityToken` tied to run_id and actor_id.
- LLM actor produces `PROPOSED_MUTATION` events only; it cannot commit. Committers are deterministic Gate/Validator processes.
- Every commit emits: before/after diff + justification + evidence/authority pointers where applicable.
### 5) Minimally completed sweep closure
- Graph contracts were previously implied; now explicit artifacts exist (schemas + validator).
- Bloom style guidance was verbal; now a deterministic pack exists.
- Repro build discipline was conceptual; now CI + signing hooks exist.

---
## Δ v0008 Authority+Forms Executability (v2026-01-18.40)
This delta closes a major gap: “AuthoritySnapshot + Forms-First” are now *buildable artifacts* (offline, pointer-first) rather than only conceptual modules.

### 1) New core directories (run_id outputs; append-only)
Created root directories with governance READMEs:
`AUTHORITY/ FORMS/ GRAPH/ PROCEDURE/ APPEAL/ JTC/ DGC/ ORDERCHAIN/ DEADLINES/ SERVICE/ CONTRADICTIONS/ HEARING/ EXPORTS/ RETRIEVAL/ REDACTION/ EVAL/`.

Rule: directories are empty-safe but must contain a README describing append-only outputs + gates. FILE_READY outputs still require PO ledger + pins.

### 2) AuthoritySnapshot Builder v1 (offline, regex+pins)
Shipped:
- `TOOLS/litos_authority_snapshot_builder.py`
- `SCHEMA/authority/law_pack_manifest.schema.json`
- `SCHEMA/authority/authority_ref.schema.json`
- `SCHEMA/authority/authority_snapshot_receipt.schema.json`
Demo output (pointer-grade, not QuoteVerified):
- `AUTHORITY/snapshots/SNAP_MI_AUTH_v0008_demo/authority_index.jsonl`
- `AUTHORITY/snapshots/SNAP_MI_AUTH_v0008_demo/authority_pin_map.jsonl`
- `AUTHORITY/snapshots/SNAP_MI_AUTH_v0008_demo/receipt.json`
Gate impact:
- Enables *proposition-level authority gating* by producing AuthorityRefs + pins without inventing holdings.
- QuoteLock still required for verbatim rule text or “court held” assertions.

### 3) Forms Catalog Builder v1 (offline, pointer-first)
Shipped:
- `TOOLS/litos_forms_catalog_builder.py`
- `SCHEMA/forms/forms_catalog.schema.json`
Generated catalog from your provided link corpus:
- `FORMS/catalog/MI_FORMS_v0008/index.json` (forms=2955)
Governance:
- URL-only entries remain pointer-only; no title invention.
- Local directory scan mode supports real file-backed entries.

### 4) PDF extractor formalized (repeatable QuoteLock candidate extraction)
Shipped:
- `TOOLS/litos_pdf_extract.py`
Outputs:
- `SOURCES/extracted/*.txt` page-marked, deterministic.

### 5) SourceIndex MI refreshed
Generated:
- `DATA/mi_source_index_v0008.json` and `.csv` (URLs=8942)
Use:
- Seeds acquisition planning (official sources prioritized), without assuming network access or correctness of secondary mirrors.

### 6) Latent cores catalog refreshed (PROPOSED vs SHIPPED)
- `DOCS/LATENT_CORES_CATALOG_v0008.md` consolidates “what to build next” as enforceable core proposals, backed by high-signal lines from the operator manuals/blueprints (non-filing, non-QuoteVerified).
