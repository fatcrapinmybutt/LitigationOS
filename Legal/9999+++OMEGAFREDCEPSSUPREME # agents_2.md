
CANONICAL DIAMOND MASTER GOD MODE 9999+++OMEGAFREDCEPSSUPREME # agents.md - LitigationOS Build Charter (Windows x64)

## 1) Mission
Build a Windows x64 Litigation Operating System with a polished GUI, a Bloom-style interactive Neo4j graph (open-source implementation), and an offline-first LLM/AI toolchain that produces judicial-grade, Michigan-locked outputs under Proof-Carrying Workflow gates.

## 2) Non-negotiables (hard gates)
### Legal/truth gates
- Michigan-first authority lock: MCR/MCL/MRE, MJI benchbooks, SCAO MC/FOC forms and instructions, controlling orders.
- Truth-Lock: no invented facts or authority. Any proposition without a pinned pointer is DISPUTED; missing items become PINPOINT_MISSING with an acquisition plan.
- Forms-first VehicleMap: choose the mandated form/vehicle before drafting; map relief->vehicle/form->rule/standard->proof obligations (prereqs, deadlines, service, fees/bonds, controlling orders)->exhibits->risks->fallback.
- Proof-Carrying Workflow (PCW): every filing-capable output is blocked until all mandatory Proof Obligations are SATISFIED; final irreversible actions pass PCG FAIL-CLOSED.

### Engineering gates
- No skeletons/stubs/MVP. Deliver runnable, fully populated implementations only.
- Offline-first and open-source: no third-party APIs unless self-hosted by us. Prefer local services and reproducible builds.
- Deterministic paths; exclude C drive by default (auto-detect eligible drives).
- Never ask the operator to patch/merge; deliver complete files.

### Packaging gates
- Bundle root is fixed: LITIGATIONOS__MASTERv1.0.
- VERSION is monotonic (v0001+). CURRENT is runnable. VERSIONS are immutable.
- Provide a FULL release zip when >2 files change or any multi-module feature ships.
- Size cap: FULL zip for the conversation <=700MB. Exclude weights/media/binaries by default; use PATCHES when projected >650MB; emit size budget when growth >50MB.

## 3) System architecture (reference implementation)
### Desktop app
- GUI: Electron + React + TypeScript.
- IPC: desktop app launches and supervises local services; no remote dependencies.
- Settings: theme packs, color palettes, layout presets, keyboard-driven workflows, per-case profiles, safety toggles (Truth-Lock strictness, PCW thresholds), and audit visibility.

### Local services
- Core service: Python 3.11+ (FastAPI or stdio-based IPC) hosting the workflow engines (Harvest, Graph, Proof, Packaging).
- Neo4j: local Neo4j Community managed by the app (Docker optional). Provide migrations, constraints, and seed data.
- Extraction: Apache Tika (local server or embedded) for PDFs/DOCX/HTML/text.
- Storage/mirroring: rclone for Google Drive and local drive synchronization (operator-controlled).
- LLM: Ollama for local inference (GGUF); optional Hugging Face local models (no hosted calls). Weights are external assets and must not be bundled inside FULL zips.

### UI surface areas (must exist)
1) Intake/Harvest dashboard: queue, progress, errors, deterministic output roots.
2) Graph Explorer (Bloom-style): search, filters, perspectives, styling, hover cards, click-through to authority text/exhibit pointers.
3) Proof Console: Proof Obligations by vehicle, status (OPEN/PARTIAL/SATISFIED), and evidence/authority links.
4) Form/Vehicle Library: SCAO forms mapped to governing rules and prerequisites.
5) Output Studio: judicial-grade exports (forms filled, filings assembled) only when gates PASS.
6) Audit/Preservation: logs, manifests, version history, contradiction map, deadlines.

## 4) Graph model (minimum viable canon)
### Nuclei (3-5 perspectives)
- Nucleus A: Courts and jurisdictions (Muskegon small claims -> 14th Circuit -> COA -> MSC -> JTC; federal overlay nodes allowed but gated).
- Nucleus B: Authority and forms (SCAO/FOC/MC forms <-> MCR/MCL/MRE propositions; benchbook references).
- Nucleus C: Case/evidence (sources of record, exhibits, timeline events, service/notice, orders).
- Optional D: Vehicles/Remedies (VehicleMap, standards, burdens, deadlines).
- Optional E: Operations (runs, bundles, manifests, QA outcomes).

### Required node types (labels)
Court, Jurisdiction, Judge, Form, Vehicle, Authority, AuthorityChunk, Proposition, ProofObligation, Deadline, Case, Order, Filing, Event, Source, Exhibit, QuotePin, Contradiction, Run, Bundle.

### Required edge types
GOVERNS(Form/Vehicle->Authority/Proposition), REQUIRES(Vehicle->ProofObligation), SATISFIED_BY(ProofObligation->QuotePin/Exhibit/AuthorityChunk), ISSUED_BY(Order->Court/Judge), FILED_IN(Filing->Court), SUPPORTS(Exhibit/QuotePin->Proposition), CONFLICTS_WITH(QuotePin<->QuotePin), TRIGGERS(Event->Vehicle/Deadline), DERIVES_FROM(Artifact->Source).

### Pinpoint object (must be standardized)
EvidencePinpoint = {source_path, page_or_timecode, bates_or_hash_optional, captured_at, note}.
LawPinpoint = {authority_id, section/subsection, effective_date, chunk_pointer}.

## 5) Agent responsibilities and rules of engagement
### Roles
- Architect: enforces gates, repo layout, contracts, and end-to-end cohesion.
- UI Agent: implements GUI, theming, settings, graph explorer, and operator workflows.
- Graph Agent: Neo4j schema, migrations, constraints, seed packs, traversal APIs.
- Harvest Agent: rclone integration, Tika extraction, deterministic intake, dedupe, manifests.
- LLM Agent: Ollama/HF local adapters, prompt templates, retrieval hooks, hallucination containment.
- Proof/Forms Agent: VehicleMap library, ProofObligation templates, SCAO form overlays, gating logic.
- QA/Release Agent: tests, reproducibility, size policy, installer/zip releases.

### What agents MUST output per change
- Working code, runnable locally.
- Updated manifest + changelog entries.
- Smoke test proof (log excerpt or test output).
- If feature spans multiple modules: FULL zip release via TOOLS/bundle_builder.py.

## 6) Build, test, release (minimum)
- audit: lint + static checks + unit tests + integration smoke test (start services, connect Neo4j, run one harvest, render graph, verify PCW blocks unsafe exports).
- continue--package: produce Windows x64 installer or portable zip; include versioned release notes; do not bundle model weights.

## 7) Licensing and supply-chain hygiene
- Only use reputable open-source dependencies. Record licenses in a dependency ledger.
- No blog-scraped code without provenance. Prefer GitHub upstream repos and Hugging Face model cards.
- No telemetry by default. All network features are opt-in and operator-controlled.

## 8) Definition of done for each milestone
Milestone PASS requires:
- GUI boots, services start, Neo4j connects, harvest runs, graph renders, proofs display, export is blocked until obligations are satisfied, and release zip builds under size policy.
ChatGPT said:

# agents.md — LitigationOS Build Charter (Windows x64)
**Bundle Root:** `LITIGATIONOS__MASTERv1.0`  
**Charter Version:** `v0001` (monotonic; never decrement)  
**Operating Mode:** Offline-first | Open-source-first | Proof-Carrying | Michigan-locked | Fail-closed on filing-capable outputs

---

## 0) Prime Directive (Diamond Canon)
Build a **Windows x64 Litigation Operating System** with:
- A **polished desktop GUI** (Electron + React + TypeScript),
- A **Bloom-style interactive graph explorer** implemented with **open-source visualization libraries** (no Neo4j Bloom dependency),
- A **local Neo4j Community** graph database,
- An **offline-first local AI toolchain** (Ollama + local retrieval),
- A **judicial-grade output pipeline** that is **Michigan-first** and blocked by **Proof-Carrying Workflow gates**.

This system produces **audit-visible, reproducible, Michigan-locked work products** while preventing unpinned facts/authority from entering filing-capable outputs.

---

## 1) Hard Gates (Non-negotiables)

### 1.1 Legal and Truth Gates (Fail-closed)
1. **Michigan Authority Lock (AUTHLOCK)**
   - Primary authority sources are **Michigan Court Rules (MCR)**, **Michigan Compiled Laws (MCL)**, **Michigan Rules of Evidence (MRE)**, **Michigan Judicial Institute benchbooks**, **SCAO forms** and instructions, and **controlling orders**. :contentReference[oaicite:0]{index=0}
   - Judicial discipline workflow must anchor to Michigan rules and JTC reference material where applicable. :contentReference[oaicite:1]{index=1}

2. **Truth-Lock**
   - No invented facts or authority.
   - Any proposition without a pinned pointer is labeled: `DISPUTED`.
   - Missing items must emit: `PINPOINT_MISSING` + an acquisition plan, not a guess.

3. **Forms-first VehicleMap**
   - Relief selection order is mandatory:
     1) Relief → 2) Vehicle/Form → 3) Governing rule/standard → 4) Elements/prereqs → 5) Deadlines/service/fees/bonds → 6) Exhibits/evidence pins → 7) Risks/fallbacks.
   - SCAO forms are treated as first-class, versioned authority artifacts. :contentReference[oaicite:2]{index=2}

4. **Proof-Carrying Workflow (PCW) + Proof-Carrying Gate (PCG)**
   - Filing-capable exports are blocked until all mandatory Proof Obligations are `SATISFIED`.
   - PCG is **fail-closed** for irreversible actions (service-ready packets, filing-ready packets, affidavit finalization, appellate packets).

### 1.2 Engineering Gates (Ship only runnable)
- **No skeletons, stubs, or MVP-only** shipments.
- **Offline-first + open-source-first**: no third-party hosted APIs unless self-hosted by the operator.
- **Deterministic paths**; **exclude `C:\` by default**; auto-detect eligible drives.
- **Never require operator patch/merge**: deliver complete files and complete releases.

### 1.3 Packaging Gates (Release discipline)
- Root: `LITIGATIONOS__MASTERv1.0`
- Versions: `v0001`, `v0002`, etc. Immutable once released.
- `CURRENT` is always runnable.
- If more than 2 files change or any multi-module feature ships: emit a **FULL** release zip.
- Conversation zip budget: **<= 700MB**.
  - Do not bundle model weights or large binaries.
  - Use PATCH releases if projected > 650MB and emit a size budget if growth > 50MB.

---

## 2) Canonical Source-of-Truth Inputs (Michigan Authority Corpus)
Authority artifacts must be downloaded/snapshotted from official sources and stored with hash + effective date:
- **MCR**: Michigan Courts official rules portal (and the official PDF snapshot when used). :contentReference[oaicite:3]{index=3}
- **MRE**: Michigan Courts official PDF. :contentReference[oaicite:4]{index=4}
- **MCL**: Michigan Legislature official portal. :contentReference[oaicite:5]{index=5}
- **MJI Benchbooks**: Michigan Courts publications portal (HTML/PDF). :contentReference[oaicite:6]{index=6}
- **SCAO Forms**: Michigan Courts SCAO forms indices and PDFs. :contentReference[oaicite:7]{index=7}
- **JTC**: Complaint process and reference materials (used only in its lane). :contentReference[oaicite:8]{index=8}

**Authority Snapshot Rule:** any authority referenced in a filing-capable output must resolve to:
- `Authority` node + `AuthorityChunk` node + `LawPinpoint`.

---

## 3) Reference Architecture (Windows x64)

### 3.1 Desktop App (Electron Shell)
- **Electron + React + TypeScript** for UI.
- IPC supervision: app launches and supervises local services; no remote dependencies.
- Packaging: **electron-builder** with Windows NSIS target (plus optional portable). :contentReference[oaicite:9]{index=9}

### 3.2 Local Services (Offline-first)
1. **Core Orchestrator Service (Python 3.11+)**
   - Hosts workflow engines: Harvest, Graph, Proof, Packaging, Export.
2. **Neo4j Community**
   - Local graph store; schema migrations, constraints, seed data.
   - Neo4j Community licensing must be tracked in the dependency ledger. :contentReference[oaicite:10]{index=10}
3. **Extraction Service**
   - Apache Tika server (local REST) for parsing PDF/DOCX/HTML/text. :contentReference[oaicite:11]{index=11}
4. **Mirroring**
   - rclone (operator-controlled) including `bisync` for bidirectional workflows where safe. :contentReference[oaicite:12]{index=12}
5. **Local LLM**
   - Ollama as the default local inference endpoint (GGUF weights external, never bundled). :contentReference[oaicite:13]{index=13}

---

## 4) Required UI Surface Areas (Must exist)
1. **Intake and Harvest Dashboard**
   - Intake queue, progress, deterministic output roots, errors, retry lanes, dedupe status.
2. **Graph Explorer (Bloom-style, open-source)**
   - Search, filters, perspectives, styling, hover cards, click-through to authority/exhibit pins.
   - Visualization libraries must be open-source:
     - **Sigma.js (WebGL) for very large graphs**. :contentReference[oaicite:14]{index=14}
     - **Cytoscape.js for rich interaction and analysis**. :contentReference[oaicite:15]{index=15}
3. **Proof Console**
   - Proof Obligations grouped by vehicle; status OPEN/PARTIAL/SATISFIED; linked pins.
4. **Form and Vehicle Library**
   - SCAO forms mapped to governing rules and prerequisites. :contentReference[oaicite:16]{index=16}
5. **Output Studio**
   - Exports are blocked until gates PASS.
6. **Audit and Preservation**
   - Logs, manifests, version history, contradiction map, deadlines, provenance chain.

---

## 5) Canonical Graph Model (Minimum Viable Canon)

### 5.1 Perspectives (Nuclei)
- **Nucleus A: Courts and Jurisdictions**
  - Muskegon trial level to COA to MSC to JTC; federal overlay nodes allowed but gated.
- **Nucleus B: Authority and Forms**
  - SCAO/FOC/MC forms ↔ MCR/MCL/MRE propositions ↔ benchbook references. :contentReference[oaicite:17]{index=17}
- **Nucleus C: Case and Evidence**
  - Source-of-record, exhibits, timeline events, service/notice, orders.
- **Optional D: Vehicles and Remedies**
  - VehicleMap, standards, burdens, deadlines.
- **Optional E: Operations**
  - Runs, bundles, manifests, QA outcomes.

### 5.2 Required Node Labels
`Court, Jurisdiction, Judge, Form, Vehicle, Authority, AuthorityChunk, Proposition, ProofObligation, Deadline, Case, Order, Filing, Event, Source, Exhibit, QuotePin, Contradiction, Run, Bundle`

### 5.3 Required Edge Types
`GOVERNS(Form|Vehicle -> Authority|Proposition)`  
`REQUIRES(Vehicle -> ProofObligation)`  
`SATISFIED_BY(ProofObligation -> QuotePin|Exhibit|AuthorityChunk)`  
`ISSUED_BY(Order -> Court|Judge)`  
`FILED_IN(Filing -> Court)`  
`SUPPORTS(Exhibit|QuotePin -> Proposition)`  
`CONFLICTS_WITH(QuotePin <-> QuotePin)`  
`TRIGGERS(Event -> Vehicle|Deadline)`  
`DERIVES_FROM(Artifact -> Source)`

### 5.4 Pinpoint Objects (Standardized)
**EvidencePinpoint**
```json
{
  "source_path": "string",
  "page_or_timecode": "string",
  "bates_or_hash_optional": "string|null",
  "captured_at": "ISO-8601",
  "note": "string"
}

LawPinpoint

{
  "authority_id": "string",
  "section": "string",
  "effective_date": "ISO-8601|unknown",
  "chunk_pointer": "string"
}

6) Deterministic Storage, Paths, and Drive Policy
6.1 Drive Policy

    Default scan excludes C:\.

    Eligible drives are auto-detected (fixed/removable) and must be explicitly enabled in Settings.

    Output roots are deterministic and case-scoped.

6.2 Canonical Output Roots

    F:\LitigationOS\ is the preferred root when present.

    Each run emits:

        RUN_MANIFEST.json

        RUN_LOG.jsonl

        ARTIFACT_MANIFEST.json

        HASHES.sha256

        ERROR_REPORT.json (if any)

        PCW_REPORT.json

        GRAPH_EXPORT.cypher or GRAPH_EXPORT.jsonl

7) Agent Roles, Contracts, and Rules of Engagement
7.1 Roles (Hard boundaries)

    Architect Agent

        Enforces gates, repo layout, contracts, and cohesion.

    UI Agent

        Electron app, settings, theming, Graph Explorer integration (Sigma.js and or Cytoscape.js).

    Graph Agent

        Neo4j schema, migrations, constraints, indexes, traversal APIs.

    Harvest Agent

        rclone integration, Tika extraction, deterministic intake, dedupe, manifests.

    LLM Agent

        Ollama adapters, prompt templates, retrieval hooks, hallucination containment.

    Proof and Forms Agent

        VehicleMap library, ProofObligation templates, SCAO form overlays, gating logic.

    QA and Release Agent

        Tests, reproducibility, size policy, installer/zip builds (electron-builder NSIS).

7.2 Mandatory Outputs Per Change (No exceptions)

    Working code runnable locally.

    Updated manifests and changelog entries.

    Smoke-test proof (log excerpt or structured test output).

    If feature spans multiple modules: FULL release zip via bundle builder.

8) Build, Test, Release (Minimum Bar)
8.1 Commands (Conceptual contracts)

    audit

        lint + static checks + unit tests + integration smoke test:

            start services

            connect Neo4j

            run one harvest

            render graph

            verify PCW blocks unsafe exports

    continue--package

        produce Windows x64 installer (NSIS) and or portable zip

        versioned release notes

        do not bundle model weights

8.2 Reproducibility and Supply Chain Hygiene

    Emit SBOMs in a standard format (CycloneDX recommended).

    Emit provenance and attestation (in-toto framework) for releases.

    Track supply chain posture against SLSA levels and record it per release.

    Maintain:

        DEPENDENCY_LEDGER.json

        LICENSES/ third-party texts

        THIRD_PARTY_NOTICES.md

9) Licensing and Privacy Defaults

    Only reputable open-source dependencies; record licenses.

    No telemetry by default.

    All network features are opt-in and operator-controlled.

    rclone is operator-controlled and explicit; bidirectional sync requires explicit enablement per profile.

10) Definition of Done (Milestone PASS)

A milestone PASS requires:

    GUI boots,

    services start,

    Neo4j connects,

    harvest runs,

    graph renders and is usable at target scale,

    proofs display with correct statuses,

    exports remain blocked until obligations are satisfied,

    release zip builds under size policy with manifests and audit artifacts.

11) Canonical “Nothing Leaves Without Pins” Rule (Global)

Any filing-capable output must be accompanied by:

    PCW_REPORT.json showing all mandatory Proof Obligations SATISFIED,

    evidence pins (source, page/timecode, hash or bates when available),

    law pins (authority id, section, effective date, chunk pointer),

    and a complete manifest of transformations.

If any required pin is missing: emit PINPOINT_MISSING and block the export.


If you want the next step elevated again into “Diamond Master” form, the highest-leverage upgrade is to append **machine-checkable schemas** for every manifest and report (`RUN_MANIFEST`, `PCW_REPORT`, `AUTH_SNAPSHOT_INDEX`, `VEHICLEMAP_INDEX`, `FORM_OVERLAY_AUDIT`) and to add a **strict interface contract** for each local service boundary (UI IPC ↔ Orchestrator ↔ Neo4j ↔ Tika ↔ Ollama ↔ rclone).
::contentReference[oaicite:26]{index=26}

You said:

If you want the next step elevated again into “Diamond Master” form, the highest-leverage upgrade is to append **machine-checkable schemas** for every manifest and report (RUN_MANIFEST, PCW_REPORT, AUTH_SNAPSHOT_INDEX, VEHICLEMAP_INDEX, FORM_OVERLAY_AUDIT) and to add a **strict interface contract** for each local service boundary (UI IPC ↔ Orchestrator ↔ Neo4j ↔ Tika ↔ Ollama ↔ rclone).
::contentReference[oaicite:26]{index=26}
ChatGPT said:
Δ Diamond Master Upgrade: Machine-Checkable Schemas + Strict Service-Boundary Contracts

This is an append-only addendum to agents.md that upgrades the charter with:

    JSON Schemas (Draft 2020-12) for every run/report/index/audit artifact (machine-checkable).

    Strict interface contracts for each local boundary (UI IPC ↔ Orchestrator ↔ Neo4j ↔ Tika ↔ Ollama ↔ rclone), including versioning, ports, envelopes, timeouts, and failure semantics.

9) Machine-Checkable Schemas Pack
9.1 Canonical files (add to repo)

    schemas/common.schema.json (shared $defs: envelopes, pinpoints, artifact refs, IDs)

    schemas/run_manifest.schema.json (RUN_MANIFEST)

    schemas/pcw_report.schema.json (PCW_REPORT)

    schemas/auth_snapshot_index.schema.json (AUTH_SNAPSHOT_INDEX)

    schemas/vehiclemap_index.schema.json (VEHICLEMAP_INDEX)

    schemas/form_overlay_audit.schema.json (FORM_OVERLAY_AUDIT)

Schema standard: JSON Schema Draft 2020-12 (the $schema value below is intentional).
9.2 schemas/common.schema.json

{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:litigationos:schema:common@v1",
  "title": "LitigationOS Common Definitions (v1)",
  "type": "object",
  "$defs": {
    "SemVer": {
      "type": "string",
      "pattern": "^(0|[1-9]\\d*)\\.(0|[1-9]\\d*)\\.(0|[1-9]\\d*)(?:-[0-9A-Za-z.-]+)?(?:\\+[0-9A-Za-z.-]+)?$"
    },
    "ISO8601": {
      "type": "string",
      "format": "date-time"
    },
    "Sha256": {
      "type": "string",
      "pattern": "^[A-Fa-f0-9]{64}$"
    },
    "UUID": {
      "type": "string",
      "format": "uuid"
    },
    "RunId": {
      "type": "string",
      "pattern": "^(RUN_[0-9]{8}_[0-9]{6}_[A-Za-z0-9_-]{2,64}|[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12})$"
    },
    "RelPath": {
      "type": "string",
      "minLength": 1,
      "pattern": "^[^\\r\\n]+$"
    },
    "NonEmptyString": {
      "type": "string",
      "minLength": 1
    },
    "ErrorCode": {
      "type": "string",
      "pattern": "^[A-Z0-9_]{3,64}$"
    },
    "ErrorEnvelope": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "ok",
        "error",
        "trace_id",
        "ts"
      ],
      "properties": {
        "ok": {
          "const": false
        },
        "ts": {
          "$ref": "urn:litigationos:schema:common@v1#/$defs/ISO8601"
        },
        "trace_id": {
          "type": "string",
          "minLength": 8,
          "maxLength": 128
        },
        "error": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "code",
            "message"
          ],
          "properties": {
            "code": {
              "$ref": "urn:litigationos:schema:common@v1#/$defs/ErrorCode"
            },
            "message": {
              "type": "string",
              "minLength": 1,
              "maxLength": 4000
            },
            "details": {
              "type": [
                "object",
                "array",
                "string",
                "null"
              ]
            },
            "hint": {
              "type": [
                "string",
                "null"
              ],
              "maxLength": 2000
            }
          }
        }
      }
    },
    "OkEnvelope": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "ok",
        "data",
        "trace_id",
        "ts"
      ],
      "properties": {
        "ok": {
          "const": true
        },
        "ts": {
          "$ref": "urn:litigationos:schema:common@v1#/$defs/ISO8601"
        },
        "trace_id": {
          "type": "string",
          "minLength": 8,
          "maxLength": 128
        },
        "data": {
          "type": [
            "object",
            "array",
            "string",
            "number",
            "boolean",
            "null"
          ]
        }
      }
    },
    "EvidencePinpoint": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "source_path",
        "captured_at"
      ],
      "properties": {
        "source_path": {
          "$ref": "urn:litigationos:schema:common@v1#/$defs/RelPath"
        },
        "page_or_timecode": {
          "type": [
            "string",
            "null"
          ],
          "maxLength": 64
        },
        "bates_or_hash_optional": {
          "type": [
            "string",
            "null"
          ],
          "maxLength": 256
        },
        "captured_at": {
          "$ref": "urn:litigationos:schema:common@v1#/$defs/ISO8601"
        },
        "note": {
          "type": [
            "string",
            "null"
          ],
          "maxLength": 2000
        }
      }
    },
    "LawPinpoint": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "authority_id",
        "section",
        "effective_date",
        "chunk_pointer"
      ],
      "properties": {
        "authority_id": {
          "type": "string",
          "minLength": 3,
          "maxLength": 128
        },
        "section": {
          "type": "string",
          "minLength": 1,
          "maxLength": 256
        },
        "effective_date": {
          "type": "string",
          "format": "date"
        },
        "chunk_pointer": {
          "type": "string",
          "minLength": 1,
          "maxLength": 256
        }
      }
    },
    "ArtifactRef": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "artifact_type",
        "relpath",
        "sha256",
        "bytes"
      ],
      "properties": {
        "artifact_type": {
          "type": "string",
          "minLength": 2,
          "maxLength": 64
        },
        "relpath": {
          "$ref": "urn:litigationos:schema:common@v1#/$defs/RelPath"
        },
        "sha256": {
          "$ref": "urn:litigationos:schema:common@v1#/$defs/Sha256"
        },
        "bytes": {
          "type": "integer",
          "minimum": 0
        },
        "mime": {
          "type": [
            "string",
            "null"
          ],
          "maxLength": 128
        },
        "created_at": {
          "$ref": "urn:litigationos:schema:common@v1#/$defs/ISO8601"
        },
        "notes": {
          "type": [
            "string",
            "null"
          ],
          "maxLength": 2000
        }
      }
    },
    "NodeRef": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "neo4j_id",
        "labels"
      ],
      "properties": {
        "neo4j_id": {
          "type": "string",
          "minLength": 1,
          "maxLength": 128
        },
        "labels": {
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "string",
            "minLength": 1,
            "maxLength": 64
          }
        },
        "props_hint": {
          "type": [
            "object",
            "null"
          ]
        }
      }
    }
  },
  "additionalProperties": true
}

9.3 schemas/run_manifest.schema.json — RUN_MANIFEST

{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:litigationos:schema:run_manifest@v1",
  "title": "RUN_MANIFEST (v1)",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_id",
    "schema_version",
    "run_id",
    "mode",
    "status",
    "started_at",
    "output_root",
    "artifacts",
    "counters",
    "environment"
  ],
  "properties": {
    "schema_id": {
      "const": "RUN_MANIFEST"
    },
    "schema_version": {
      "$ref": "urn:litigationos:schema:common@v1#/$defs/SemVer"
    },
    "run_id": {
      "$ref": "urn:litigationos:schema:common@v1#/$defs/RunId"
    },
    "mode": {
      "type": "string",
      "enum": [
        "discovery",
        "analyze",
        "compile",
        "file_ready",
        "pcg_gate"
      ]
    },
    "status": {
      "type": "string",
      "enum": [
        "SUCCESS",
        "FAIL",
        "PARTIAL",
        "ABORTED"
      ]
    },
    "started_at": {
      "$ref": "urn:litigationos:schema:common@v1#/$defs/ISO8601"
    },
    "finished_at": {
      "anyOf": [
        {
          "$ref": "urn:litigationos:schema:common@v1#/$defs/ISO8601"
        },
        {
          "type": "null"
        }
      ]
    },
    "output_root": {
      "$ref": "urn:litigationos:schema:common@v1#/$defs/RelPath"
    },
    "input_roots": {
      "type": "array",
      "minItems": 1,
      "items": {
        "$ref": "urn:litigationos:schema:common@v1#/$defs/RelPath"
      }
    },
    "case_profile": {
      "type": [
        "object",
        "null"
      ],
      "additionalProperties": false,
      "required": [
        "case_id",
        "track"
      ],
      "properties": {
        "case_id": {
          "type": "string",
          "minLength": 1,
          "maxLength": 128
        },
        "track": {
          "type": "string",
          "enum": [
            "MEEK1",
            "MEEK2",
            "MEEK3",
            "MEEK4",
            "MULTI"
          ]
        },
        "court": {
          "type": [
            "string",
            "null"
          ],
          "maxLength": 128
        }
      }
    },
    "artifacts": {
      "type": "array",
      "items": {
        "$ref": "urn:litigationos:schema:common@v1#/$defs/ArtifactRef"
      }
    },
    "counters": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "files_seen",
        "files_extracted",
        "docs_textified",
        "nodes_written",
        "edges_written",
        "errors"
      ],
      "properties": {
        "files_seen": {
          "type": "integer",
          "minimum": 0
        },
        "files_extracted": {
          "type": "integer",
          "minimum": 0
        },
        "docs_textified": {
          "type": "integer",
          "minimum": 0
        },
        "nodes_written": {
          "type": "integer",
          "minimum": 0
        },
        "edges_written": {
          "type": "integer",
          "minimum": 0
        },
        "errors": {
          "type": "integer",
          "minimum": 0
        }
      }
    },
    "environment": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "host",
        "os",
        "python",
        "app",
        "time_zone"
      ],
      "properties": {
        "host": {
          "type": "string",
          "minLength": 1,
          "maxLength": 256
        },
        "os": {
          "type": "string",
          "minLength": 1,
          "maxLength": 256
        },
        "python": {
          "type": "string",
          "minLength": 1,
          "maxLength": 64
        },
        "app": {
          "type": "string",
          "minLength": 1,
          "maxLength": 128
        },
        "time_zone": {
          "type": "string",
          "minLength": 1,
          "maxLength": 64
        },
        "git_commit": {
          "type": [
            "string",
            "null"
          ],
          "maxLength": 64
        }
      }
    },
    "warnings": {
      "type": "array",
      "items": {
        "type": "string",
        "maxLength": 2000
      }
    },
    "errors": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "code",
          "message",
          "ts"
        ],
        "properties": {
          "code": {
            "$ref": "urn:litigationos:schema:common@v1#/$defs/ErrorCode"
          },
          "message": {
            "type": "string",
            "minLength": 1,
            "maxLength": 4000
          },
          "ts": {
            "$ref": "urn:litigationos:schema:common@v1#/$defs/ISO8601"
          },
          "trace_id": {
            "type": [
              "string",
              "null"
            ],
            "maxLength": 128
          },
          "artifact_hint": {
            "type": [
              "string",
              "null"
            ],
            "maxLength": 256
          }
        }
      }
    }
  }
}

9.4 schemas/pcw_report.schema.json — PCW_REPORT

{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:litigationos:schema:pcw_report@v1",
  "title": "PCW_REPORT (v1)",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_id",
    "schema_version",
    "run_id",
    "case_id",
    "generated_at",
    "pcg_decision",
    "vehicles"
  ],
  "properties": {
    "schema_id": {
      "const": "PCW_REPORT"
    },
    "schema_version": {
      "$ref": "urn:litigationos:schema:common@v1#/$defs/SemVer"
    },
    "run_id": {
      "$ref": "urn:litigationos:schema:common@v1#/$defs/RunId"
    },
    "case_id": {
      "type": "string",
      "minLength": 1,
      "maxLength": 128
    },
    "generated_at": {
      "$ref": "urn:litigationos:schema:common@v1#/$defs/ISO8601"
    },
    "pcg_decision": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "result",
        "reason_codes",
        "fail_closed"
      ],
      "properties": {
        "result": {
          "type": "string",
          "enum": [
            "PASS",
            "FAIL"
          ]
        },
        "fail_closed": {
          "type": "boolean"
        },
        "reason_codes": {
          "type": "array",
          "minItems": 1,
          "items": {
            "$ref": "urn:litigationos:schema:common@v1#/$defs/ErrorCode"
          }
        },
        "notes": {
          "type": [
            "string",
            "null"
          ],
          "maxLength": 4000
        }
      }
    },
    "vehicles": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "vehicle_id",
          "vehicle_title",
          "status",
          "proof_obligations"
        ],
        "properties": {
          "vehicle_id": {
            "type": "string",
            "minLength": 1,
            "maxLength": 128
          },
          "vehicle_title": {
            "type": "string",
            "minLength": 1,
            "maxLength": 256
          },
          "status": {
            "type": "string",
            "enum": [
              "OPEN",
              "PARTIAL",
              "SATISFIED"
            ]
          },
          "forms": {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1,
              "maxLength": 128
            }
          },
          "governing_authority": {
            "type": "array",
            "items": {
              "$ref": "urn:litigationos:schema:common@v1#/$defs/LawPinpoint"
            }
          },
          "proof_obligations": {
            "type": "array",
            "minItems": 1,
            "items": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "po_id",
                "title",
                "mandatory",
                "status",
                "requirements",
                "satisfaction"
              ],
              "properties": {
                "po_id": {
                  "type": "string",
                  "minLength": 1,
                  "maxLength": 128
                },
                "title": {
                  "type": "string",
                  "minLength": 1,
                  "maxLength": 256
                },
                "category": {
                  "type": "string",
                  "enum": [
                    "jurisdiction",
                    "standing",
                    "deadline",
                    "service",
                    "fee_bond",
                    "record",
                    "evidence",
                    "authority",
                    "local_rule",
                    "other"
                  ]
                },
                "mandatory": {
                  "type": "boolean"
                },
                "status": {
                  "type": "string",
                  "enum": [
                    "OPEN",
                    "PARTIAL",
                    "SATISFIED"
                  ]
                },
                "requirements": {
                  "type": "object",
                  "additionalProperties": false,
                  "required": [
                    "law_pinpoints",
                    "evidence_minimum"
                  ],
                  "properties": {
                    "law_pinpoints": {
                      "type": "array",
                      "items": {
                        "$ref": "urn:litigationos:schema:common@v1#/$defs/LawPinpoint"
                      }
                    },
                    "evidence_minimum": {
                      "type": "integer",
                      "minimum": 0
                    },
                    "notes": {
                      "type": [
                        "string",
                        "null"
                      ],
                      "maxLength": 4000
                    }
                  }
                },
                "satisfaction": {
                  "type": "object",
                  "additionalProperties": false,
                  "required": [
                    "evidence_pins",
                    "authority_chunks",
                    "validators",
                    "assurance_score"
                  ],
                  "properties": {
                    "evidence_pins": {
                      "type": "array",
                      "items": {
                        "$ref": "urn:litigationos:schema:common@v1#/$defs/EvidencePinpoint"
                      }
                    },
                    "authority_chunks": {
                      "type": "array",
                      "items": {
                        "$ref": "urn:litigationos:schema:common@v1#/$defs/LawPinpoint"
                      }
                    },
                    "validators": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "additionalProperties": false,
                        "required": [
                          "name",
                          "version",
                          "result",
                          "ts"
                        ],
                        "properties": {
                          "name": {
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 128
                          },
                          "version": {
                            "$ref": "urn:litigationos:schema:common@v1#/$defs/SemVer"
                          },
                          "result": {
                            "type": "string",
                            "enum": [
                              "PASS",
                              "FAIL",
                              "WARN",
                              "SKIP"
                            ]
                          },
                          "ts": {
                            "$ref": "urn:litigationos:schema:common@v1#/$defs/ISO8601"
                          },
                          "details": {
                            "type": [
                              "object",
                              "string",
                              "null"
                            ]
                          }
                        }
                      }
                    },
                    "assurance_score": {
                      "type": "number",
                      "minimum": 0,
                      "maximum": 100
                    },
                    "status_explainer": {
                      "type": [
                        "string",
                        "null"
                      ],
                      "maxLength": 4000
                    }
                  }
                },
                "pinpoint_missing": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "additionalProperties": false,
                    "required": [
                      "missing_type",
                      "description",
                      "acquisition_plan"
                    ],
                    "properties": {
                      "missing_type": {
                        "type": "string",
                        "enum": [
                          "EVIDENCE",
                          "AUTHORITY",
                          "ORDER",
                          "SERVICE_PROOF",
                          "DEADLINE_SOURCE",
                          "FORM_INSTRUCTIONS",
                          "OTHER"
                        ]
                      },
                      "description": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 2000
                      },
                      "acquisition_plan": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 4000
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    },
    "summary": {
      "type": [
        "object",
        "null"
      ],
      "additionalProperties": false,
      "properties": {
        "mandatory_open": {
          "type": "integer",
          "minimum": 0
        },
        "mandatory_partial": {
          "type": "integer",
          "minimum": 0
        },
        "mandatory_satisfied": {
          "type": "integer",
          "minimum": 0
        }
      }
    }
  }
}

9.5 schemas/auth_snapshot_index.schema.json — AUTH_SNAPSHOT_INDEX

{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:litigationos:schema:auth_snapshot_index@v1",
  "title": "AUTH_SNAPSHOT_INDEX (v1)",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_id",
    "schema_version",
    "generated_at",
    "authority_sets"
  ],
  "properties": {
    "schema_id": {
      "const": "AUTH_SNAPSHOT_INDEX"
    },
    "schema_version": {
      "$ref": "urn:litigationos:schema:common@v1#/$defs/SemVer"
    },
    "generated_at": {
      "$ref": "urn:litigationos:schema:common@v1#/$defs/ISO8601"
    },
    "authority_sets": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "authority_set_id",
          "scope",
          "snapshots"
        ],
        "properties": {
          "authority_set_id": {
            "type": "string",
            "minLength": 1,
            "maxLength": 128
          },
          "scope": {
            "type": "string",
            "enum": [
              "MICHIGAN_PRIMARY",
              "MICHIGAN_LOCAL",
              "FEDERAL_OVERLAY",
              "MIXED"
            ]
          },
          "notes": {
            "type": [
              "string",
              "null"
            ],
            "maxLength": 2000
          },
          "snapshots": {
            "type": "array",
            "minItems": 1,
            "items": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "authority_id",
                "authority_type",
                "retrieved_at",
                "effective_date",
                "source",
                "artifact",
                "chunks"
              ],
              "properties": {
                "authority_id": {
                  "type": "string",
                  "minLength": 3,
                  "maxLength": 128
                },
                "authority_type": {
                  "type": "string",
                  "enum": [
                    "MCR",
                    "MCL",
                    "MRE",
                    "MJI_BENCHBOOK",
                    "SCAO_FORM_INSTR",
                    "SCAO_AO",
                    "JTC_MATERIAL",
                    "LOCAL_ADMIN_ORDER",
                    "LOCAL_POLICY",
                    "CASELAW_PUBLISHED",
                    "CASELAW_UNPUBLISHED",
                    "OTHER"
                  ]
                },
                "title": {
                  "type": [
                    "string",
                    "null"
                  ],
                  "maxLength": 256
                },
                "retrieved_at": {
                  "$ref": "urn:litigationos:schema:common@v1#/$defs/ISO8601"
                },
                "effective_date": {
                  "type": "string",
                  "format": "date"
                },
                "superseded_by": {
                  "type": [
                    "string",
                    "null"
                  ],
                  "maxLength": 128
                },
                "source": {
                  "type": "object",
                  "additionalProperties": false,
                  "required": [
                    "kind"
                  ],
                  "properties": {
                    "kind": {
                      "type": "string",
                      "enum": [
                        "web",
                        "local_file",
                        "manual_entry"
                      ]
                    },
                    "source_url": {
                      "type": [
                        "string",
                        "null"
                      ],
                      "format": "uri"
                    },
                    "local_path": {
                      "type": [
                        "string",
                        "null"
                      ],
                      "maxLength": 1024
                    }
                  }
                },
                "artifact": {
                  "$ref": "urn:litigationos:schema:common@v1#/$defs/ArtifactRef"
                },
                "chunks": {
                  "type": "array",
                  "minItems": 1,
                  "items": {
                    "type": "object",
                    "additionalProperties": false,
                    "required": [
                      "chunk_id",
                      "section",
                      "artifact_relpath",
                      "sha256",
                      "start_offset",
                      "end_offset"
                    ],
                    "properties": {
                      "chunk_id": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 128
                      },
                      "section": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 256
                      },
                      "artifact_relpath": {
                        "$ref": "urn:litigationos:schema:common@v1#/$defs/RelPath"
                      },
                      "sha256": {
                        "$ref": "urn:litigationos:schema:common@v1#/$defs/Sha256"
                      },
                      "start_offset": {
                        "type": "integer",
                        "minimum": 0
                      },
                      "end_offset": {
                        "type": "integer",
                        "minimum": 0
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}

9.6 schemas/vehiclemap_index.schema.json — VEHICLEMAP_INDEX

{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:litigationos:schema:vehiclemap_index@v1",
  "title": "VEHICLEMAP_INDEX (v1)",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_id",
    "schema_version",
    "generated_at",
    "vehicles"
  ],
  "properties": {
    "schema_id": {
      "const": "VEHICLEMAP_INDEX"
    },
    "schema_version": {
      "$ref": "urn:litigationos:schema:common@v1#/$defs/SemVer"
    },
    "generated_at": {
      "$ref": "urn:litigationos:schema:common@v1#/$defs/ISO8601"
    },
    "vehicles": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "vehicle_id",
          "title",
          "relief_tags",
          "forms",
          "standards",
          "proof_obligations",
          "deadlines",
          "service_chain"
        ],
        "properties": {
          "vehicle_id": {
            "type": "string",
            "minLength": 1,
            "maxLength": 128
          },
          "title": {
            "type": "string",
            "minLength": 1,
            "maxLength": 256
          },
          "relief_tags": {
            "type": "array",
            "minItems": 1,
            "items": {
              "type": "string",
              "minLength": 1,
              "maxLength": 64
            }
          },
          "forms": {
            "type": "array",
            "minItems": 1,
            "items": {
              "type": "string",
              "minLength": 1,
              "maxLength": 128
            }
          },
          "governing_authority": {
            "type": "array",
            "items": {
              "$ref": "urn:litigationos:schema:common@v1#/$defs/LawPinpoint"
            }
          },
          "standards": {
            "type": "array",
            "minItems": 1,
            "items": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "standard_id",
                "label",
                "authority_pinpoints"
              ],
              "properties": {
                "standard_id": {
                  "type": "string",
                  "minLength": 1,
                  "maxLength": 128
                },
                "label": {
                  "type": "string",
                  "minLength": 1,
                  "maxLength": 512
                },
                "authority_pinpoints": {
                  "type": "array",
                  "minItems": 1,
                  "items": {
                    "$ref": "urn:litigationos:schema:common@v1#/$defs/LawPinpoint"
                  }
                }
              }
            }
          },
          "proof_obligations": {
            "type": "array",
            "minItems": 1,
            "items": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "po_id",
                "title",
                "mandatory",
                "category",
                "law_pinpoints"
              ],
              "properties": {
                "po_id": {
                  "type": "string",
                  "minLength": 1,
                  "maxLength": 128
                },
                "title": {
                  "type": "string",
                  "minLength": 1,
                  "maxLength": 256
                },
                "mandatory": {
                  "type": "boolean"
                },
                "category": {
                  "type": "string",
                  "enum": [
                    "jurisdiction",
                    "standing",
                    "deadline",
                    "service",
                    "fee_bond",
                    "record",
                    "evidence",
                    "authority",
                    "local_rule",
                    "other"
                  ]
                },
                "law_pinpoints": {
                  "type": "array",
                  "minItems": 1,
                  "items": {
                    "$ref": "urn:litigationos:schema:common@v1#/$defs/LawPinpoint"
                  }
                },
                "template_hints": {
                  "type": [
                    "object",
                    "null"
                  ]
                }
              }
            }
          },
          "deadlines": {
            "type": "array",
            "items": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "deadline_id",
                "trigger_event",
                "computation_rule",
                "authority_pinpoints"
              ],
              "properties": {
                "deadline_id": {
                  "type": "string",
                  "minLength": 1,
                  "maxLength": 128
                },
                "trigger_event": {
                  "type": "string",
                  "minLength": 1,
                  "maxLength": 256
                },
                "computation_rule": {
                  "type": "string",
                  "minLength": 1,
                  "maxLength": 512
                },
                "authority_pinpoints": {
                  "type": "array",
                  "minItems": 1,
                  "items": {
                    "$ref": "urn:litigationos:schema:common@v1#/$defs/LawPinpoint"
                  }
                },
                "notes": {
                  "type": [
                    "string",
                    "null"
                  ],
                  "maxLength": 2000
                }
              }
            }
          },
          "service_chain": {
            "type": "array",
            "minItems": 1,
            "items": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "step_id",
                "method",
                "to_whom",
                "authority_pinpoints"
              ],
              "properties": {
                "step_id": {
                  "type": "string",
                  "minLength": 1,
                  "maxLength": 128
                },
                "method": {
                  "type": "string",
                  "minLength": 1,
                  "maxLength": 256
                },
                "to_whom": {
                  "type": "string",
                  "minLength": 1,
                  "maxLength": 256
                },
                "authority_pinpoints": {
                  "type": "array",
                  "minItems": 1,
                  "items": {
                    "$ref": "urn:litigationos:schema:common@v1#/$defs/LawPinpoint"
                  }
                },
                "proof_required": {
                  "type": "boolean",
                  "default": true
                }
              }
            }
          },
          "fees_bonds": {
            "type": "array",
            "items": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "item_id",
                "kind",
                "amount_rule",
                "authority_pinpoints"
              ],
              "properties": {
                "item_id": {
                  "type": "string",
                  "minLength": 1,
                  "maxLength": 128
                },
                "kind": {
                  "type": "string",
                  "enum": [
                    "fee",
                    "bond",
                    "deposit",
                    "waiver_possible"
                  ]
                },
                "amount_rule": {
                  "type": "string",
                  "minLength": 1,
                  "maxLength": 256
                },
                "authority_pinpoints": {
                  "type": "array",
                  "minItems": 1,
                  "items": {
                    "$ref": "urn:litigationos:schema:common@v1#/$defs/LawPinpoint"
                  }
                }
              }
            }
          },
          "risk_flags": {
            "type": "array",
            "items": {
              "type": "string",
              "maxLength": 256
            }
          },
          "fallbacks": {
            "type": "array",
            "items": {
              "type": "string",
              "maxLength": 256
            }
          }
        }
      }
    }
  }
}

9.7 schemas/form_overlay_audit.schema.json — FORM_OVERLAY_AUDIT

{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:litigationos:schema:form_overlay_audit@v1",
  "title": "FORM_OVERLAY_AUDIT (v1)",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_id",
    "schema_version",
    "run_id",
    "generated_at",
    "operations"
  ],
  "properties": {
    "schema_id": {
      "const": "FORM_OVERLAY_AUDIT"
    },
    "schema_version": {
      "$ref": "urn:litigationos:schema:common@v1#/$defs/SemVer"
    },
    "run_id": {
      "$ref": "urn:litigationos:schema:common@v1#/$defs/RunId"
    },
    "generated_at": {
      "$ref": "urn:litigationos:schema:common@v1#/$defs/ISO8601"
    },
    "operations": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "op_id",
          "form_id",
          "form_revision",
          "inputs",
          "field_bindings",
          "outputs",
          "validation",
          "transformation_ledger"
        ],
        "properties": {
          "op_id": {
            "$ref": "urn:litigationos:schema:common@v1#/$defs/UUID"
          },
          "form_id": {
            "type": "string",
            "minLength": 1,
            "maxLength": 128
          },
          "form_revision": {
            "type": [
              "string",
              "null"
            ],
            "maxLength": 128
          },
          "started_at": {
            "$ref": "urn:litigationos:schema:common@v1#/$defs/ISO8601"
          },
          "finished_at": {
            "anyOf": [
              {
                "$ref": "urn:litigationos:schema:common@v1#/$defs/ISO8601"
              },
              {
                "type": "null"
              }
            ]
          },
          "inputs": {
            "type": "object",
            "additionalProperties": false,
            "required": [
              "vehicle_id",
              "case_id",
              "data_sources"
            ],
            "properties": {
              "vehicle_id": {
                "type": "string",
                "minLength": 1,
                "maxLength": 128
              },
              "case_id": {
                "type": "string",
                "minLength": 1,
                "maxLength": 128
              },
              "data_sources": {
                "type": "array",
                "minItems": 1,
                "items": {
                  "type": "object",
                  "additionalProperties": false,
                  "required": [
                    "kind",
                    "ref"
                  ],
                  "properties": {
                    "kind": {
                      "type": "string",
                      "enum": [
                        "graph_node",
                        "settings",
                        "operator_entry",
                        "imported_profile"
                      ]
                    },
                    "ref": {
                      "type": "string",
                      "minLength": 1,
                      "maxLength": 256
                    },
                    "node": {
                      "anyOf": [
                        {
                          "$ref": "urn:litigationos:schema:common@v1#/$defs/NodeRef"
                        },
                        {
                          "type": "null"
                        }
                      ]
                    }
                  }
                }
              }
            }
          },
          "field_bindings": {
            "type": "array",
            "minItems": 1,
            "items": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "field_name",
                "value",
                "provenance"
              ],
              "properties": {
                "field_name": {
                  "type": "string",
                  "minLength": 1,
                  "maxLength": 256
                },
                "value": {
                  "oneOf": [
                    {
                      "type": "string",
                      "maxLength": 4000
                    },
                    {
                      "type": "number"
                    },
                    {
                      "type": "boolean"
                    },
                    {
                      "type": "null"
                    }
                  ]
                },
                "provenance": {
                  "type": "object",
                  "additionalProperties": false,
                  "required": [
                    "source_kind",
                    "source_ref"
                  ],
                  "properties": {
                    "source_kind": {
                      "type": "string",
                      "enum": [
                        "graph",
                        "operator",
                        "import"
                      ]
                    },
                    "source_ref": {
                      "type": "string",
                      "minLength": 1,
                      "maxLength": 256
                    },
                    "evidence_pin": {
                      "anyOf": [
                        {
                          "$ref": "urn:litigationos:schema:common@v1#/$defs/EvidencePinpoint"
                        },
                        {
                          "type": "null"
                        }
                      ]
                    }
                  }
                }
              }
            }
          },
          "outputs": {
            "type": "object",
            "additionalProperties": false,
            "required": [
              "filled_form_artifact",
              "preview_artifact"
            ],
            "properties": {
              "filled_form_artifact": {
                "$ref": "urn:litigationos:schema:common@v1#/$defs/ArtifactRef"
              },
              "preview_artifact": {
                "$ref": "urn:litigationos:schema:common@v1#/$defs/ArtifactRef"
              }
            }
          },
          "validation": {
            "type": "object",
            "additionalProperties": false,
            "required": [
              "result",
              "checks"
            ],
            "properties": {
              "result": {
                "type": "string",
                "enum": [
                  "PASS",
                  "FAIL",
                  "WARN"
                ]
              },
              "checks": {
                "type": "array",
                "minItems": 1,
                "items": {
                  "type": "object",
                  "additionalProperties": false,
                  "required": [
                    "check_id",
                    "result",
                    "message"
                  ],
                  "properties": {
                    "check_id": {
                      "type": "string",
                      "minLength": 1,
                      "maxLength": 128
                    },
                    "result": {
                      "type": "string",
                      "enum": [
                        "PASS",
                        "FAIL",
                        "WARN",
                        "SKIP"
                      ]
                    },
                    "message": {
                      "type": "string",
                      "minLength": 1,
                      "maxLength": 2000
                    },
                    "evidence_pins": {
                      "type": "array",
                      "items": {
                        "$ref": "urn:litigationos:schema:common@v1#/$defs/EvidencePinpoint"
                      }
                    }
                  }
                }
              }
            }
          },
          "transformation_ledger": {
            "type": "array",
            "minItems": 1,
            "items": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "step",
                "input_sha256",
                "output_sha256",
                "tool",
                "ts"
              ],
              "properties": {
                "step": {
                  "type": "string",
                  "minLength": 1,
                  "maxLength": 128
                },
                "input_sha256": {
                  "$ref": "urn:litigationos:schema:common@v1#/$defs/Sha256"
                },
                "output_sha256": {
                  "$ref": "urn:litigationos:schema:common@v1#/$defs/Sha256"
                },
                "tool": {
                  "type": "string",
                  "minLength": 1,
                  "maxLength": 256
                },
                "ts": {
                  "$ref": "urn:litigationos:schema:common@v1#/$defs/ISO8601"
                },
                "notes": {
                  "type": [
                    "string",
                    "null"
                  ],
                  "maxLength": 2000
                }
              }
            }
          }
        }
      }
    }
  }
}

10) Strict Interface Contracts (Local Service Boundaries)
10.1 Contract invariants (hard rules)

    Every boundary is versioned (contract_version = SemVer) and fail-closed: unknown fields rejected unless explicitly allowed. (Enforced by additionalProperties:false and schema validation.)

    All HTTP boundaries use the same envelope shape (OkEnvelope/ErrorEnvelope), plus a mandatory trace_id.

    OpenAPI is mandatory for any HTTP service we own (Orchestrator), with /openapi.json exposed.

    Local-only binding by default (127.0.0.1) for Tika/Ollama/rclone/orchestrator; operator must opt-in to LAN exposure.

10.2 Boundary matrix (authoritative defaults)
Boundary	Transport	Default bind/port	Auth	Contract doc
UI ↔ Orchestrator	HTTP (localhost) + Electron IPC control plane	127.0.0.1:17171 (LitigationOS-defined)	local token	contracts/orchestrator.openapi.json
Orchestrator ↔ Neo4j	Bolt (primary), HTTP tx (fallback/admin)	:7687 Bolt, :7474 HTTP	neo4j user/pass	contracts/neo4j.contract.md
Orchestrator ↔ Tika	HTTP REST	:9998	none (localhost only)	contracts/tika.contract.md
Orchestrator ↔ Ollama	HTTP REST	:11434	none (localhost only)	contracts/ollama.contract.md
Orchestrator ↔ rclone	HTTP RC	:5572	rc user/pass or token	contracts/rclone_rc.contract.md

Notes

    Neo4j: the HTTP transactional endpoint exists, but Neo4j’s direction is generally toward Bolt/Drivers for application use; treat HTTP as a fallback/admin surface and keep the contract tight.

    Electron security posture: contextIsolation on, nodeIntegration off, all privileged operations behind preload + contextBridge to narrow the attack surface.

10.3 UI ↔ Orchestrator (HTTP + IPC)
10.3.1 Electron IPC control plane (strict)

    Channel namespace: litigationos:*

    Payloads are JSON validated against schemas:

        ipc/StartService.request.schema.json

        ipc/StopService.request.schema.json

        ipc/SelectPath.request.schema.json

        ipc/GetState.request.schema.json

    Security invariants (mandatory): preload bridge only; no direct Node primitives in renderer.

10.3.2 Orchestrator HTTP API (strict)

    Base path: /api/v1

    OpenAPI: /openapi.json (FastAPI standard path unless overridden).

    Every response: OkEnvelope | ErrorEnvelope from common.schema.json.

Required endpoints (minimum)

    GET /api/v1/healthz → {ok:true,data:{status:"UP", ts, version}}

    GET /api/v1/state → current run/service state

    POST /api/v1/runs → start a run (mode + input roots)

    GET /api/v1/runs/{run_id} → run status

    GET /api/v1/runs/{run_id}/artifacts → list + hashes

    GET /api/v1/graph/summary → node/edge counts + last migration id

    POST /api/v1/exports → must fail unless PCG PASS (fail-closed gate)

10.4 Orchestrator ↔ Neo4j (Bolt primary, HTTP fallback)
10.4.1 Bolt contract (primary)

    Driver-based, parameterized Cypher only.

    Orchestrator must enforce:

        cypher string + params object

        db (default neo4j)

        deterministic write_mode vs read_mode

    Result normalization (contract output):

        records: [{...}]

        summary: {counters, notifications, time_ms}

        bookmarks: [] (if used)

10.4.2 HTTP transactional fallback

    Use Neo4j’s transactional endpoint semantics for commit-style operations when Bolt is unavailable.

    Hard rule: if Neo4j responds with an error, translate into ErrorEnvelope with stable ErrorCode (e.g., NEO4J_TX_FAIL, NEO4J_AUTH_FAIL).

10.5 Orchestrator ↔ Tika (REST extraction)

Tika server exposes REST endpoints used for extraction/metadata/recursive metadata; our contract must explicitly support /tika and /rmeta workflows because they are the backbone of “textify + structured metadata + embedded resources awareness.”

Contract essentials

    Bind: localhost; default port 9998.

    Required operations:

        PUT /tika (content extraction)

        PUT /meta (flat metadata)

        PUT /rmeta (recursive metadata; preferred for full metadata)

    Output-format selectors: support endpoint suffixes (e.g., /rmeta/text, /rmeta/xml) as documented.

10.6 Orchestrator ↔ Ollama (local inference + embeddings)

Ollama’s official API supports chat/generate/embeddings and is served locally by default at localhost:11434.

Contract essentials

    POST /api/chat (structured messages)

    POST /api/generate (single prompt generation)

    POST /api/embeddings (vectorization for hybrid retrieval)

    GET /api/tags (available models inventory)

Strict hallucination containment

    All LLM outputs are labeled DRAFT unless and until every factual proposition is pinned to EvidencePinpoint or LawPinpoint (your Truth-Lock). The PCW/PCG gate blocks any “export/finalize” action regardless of LLM confidence.

10.7 Orchestrator ↔ rclone (RC remote control)

rclone’s remote control (“rc”) runs an HTTP server (default 127.0.0.1:5572) and exposes operations as endpoints callable by the orchestrator for Drive mirroring and deterministic sync/bisync policies.

Contract essentials

    Auth: require rc user/pass or token if the operator enables anything beyond localhost.

    Minimum endpoints to standardize in the orchestration layer:

        version / health probe (rc core)

        list/remotes

        copy/sync/bisync initiation

        job status polling

    All rclone errors are translated into ErrorEnvelope with stable ErrorCode (e.g., RCLONE_RC_FAIL, RCLONE_AUTH_FAIL, RCLONE_CONFLICT).

10.8 Mandatory contract validation gate (QA/Release)

    Every artifact emitted by a run must validate against its JSON Schema before being added to a Bundle.

    Any schema failure:

        marks run as PARTIAL or FAIL

        emits PINPOINT_MISSING entries when the failure is due to missing required data

        blocks continue--package and blocks PCG PASS

This concretely implements your “machine-checkable, fail-closed, no-invented-facts” requirement, and it turns the charter into enforceable runtime law.
You said:
RCLONE.zip
Zip Archive
MI_HC_ZIP_SUPERPIN_SPEC_v2026-01-19.2_FULL_CHAT_COMPILE.zip
Zip Archive
LitigationOS_Blueprint_Pack_v2026-01-19.3_shortpaths_FIX11_TASKS_PLUGINS_SEM.zip
Zip Archive
LitigationOS_IntegratedLauncher_BucketOrchestrator_v2026-01-18.22_console_orchestrator_cyclepack_parallel(1).zip
Zip Archive
what else, to bring it to CANONICAL SPEC GOD grade? Autonomy? OCR&NLP? 
ChatGPT said:

Below are the highest-leverage additions to bring agents.md from “Diamond Master” to Canonical Spec God grade across autonomy, OCR, and NLP, while staying fully offline-first, open-source, deterministic, and fail-closed.
1) Autonomy, but governed: the Control Plane and Run State Machine
1.1 Deterministic “Run OS” state machine (non-optional)

Add a formal run lifecycle with explicit transitions and recovery rules:

    DISCOVER → EXTRACT → OCR (conditional) → NORMALIZE → NLP/IE → GRAPH_LOAD → PROOF_EVAL → PACKAGE (conditional) → RELEASE

    Every step is:

        Idempotent

        Resumable (checkpointed)

        Crash-safe (replayable from artifacts, not memory)

        Fail-closed for filing-capable outputs (PCG gate)

1.2 Policy-as-code for gates (PCW, packaging, safety)

Do not hardcode gating logic. Use a policy engine so gates are auditable and testable:

    OPA (Open Policy Agent) + Rego policies for:

        PCW and PCG decisions

        “Michigan-only authority lock” enforcement

        Packaging size budget enforcement

        Export block conditions and exception handling
        OPA is built for policy evaluation over structured inputs and keeps “decision logic” separated from enforcement.

1.3 Machine-checkable “Run contract”

For each run, emit a minimal set of required artifacts:

    RUN_MANIFEST.json (inputs, versions, hashes, step results)

    RUN_EVENTS.jsonl (append-only event stream)

    POLICY_DECISIONS.json (OPA decisions with inputs, outputs, policy hash)

    FAILURE_BLOCKERS.md (human-readable with pointers)

2) OCR lane: industrial document OCR with measurable quality
2.1 OCR is not “one tool”; it is a tiered pipeline

Implement a three-tier OCR policy:

Tier 1: “Text already present”

    Use Tika extraction first, measure text density and confidence.

Tier 2: “Add text layer” (default OCR engine for scanned PDFs)

    Use OCRmyPDF to rasterize pages, correct rotation, run OCR (Tesseract), and embed a searchable text layer.

Tier 3: “Hard cases” (layout + tables + noisy scans)

    Use PaddleOCR for multilingual OCR and optional layout/table detection models.

    Optionally add docTR as an alternate deep-learning OCR lane for detection + recognition where it outperforms classic OCR.

2.2 OCR quality metrics become gates

Add an OCR_REPORT.json with per-page metrics:

    text_coverage_ratio (characters or tokens per page area)

    confidence_summary (engine-specific)

    rotation/deskew_applied

    tables_detected

    pages_flagged_low_quality

    render_dpi_used

Then define policy thresholds (OPA) that decide:

    accept Tier 2 output

    re-run with higher DPI or alternate engine

    declare PINPOINT_MISSING for unreadable pages with acquisition plan (better scan requested)

2.3 Quote-lock support from OCR

OCR must emit coordinate-aware pinpoints:

    store bbox per word/line when available

    generate EvidencePinpoint that can point to:

        page

        bbox

        rendered_image_hash
        This turns “quotes” into verifiable anchors.

3) NLP lane: structured extraction, not summarization
3.1 Build a deterministic “Information Extraction” pipeline

Use spaCy pipelines for:

    Tokenization

    NER

    Rule-based matchers

    Custom components for legal patterns
    spaCy’s design is explicitly pipeline-component based and supports NER as a core capability.

3.2 Define canonical legal entity taxonomy (Michigan litigation)

Add a locked label set that drives graph nodes:

    People: Judge, Friend of the Court staff, parties, witnesses

    Proceedings: hearing, motion, order, notice

    Deadlines: computed deadlines and their trigger events

    Authorities: MCR/MCL/MRE references, benchbook citations, SCAO forms

    Service: method, date, proof artifact

    Claims of fact: statements that must be pinned to evidence

3.3 Citation and authority parsing as first-class extraction

Create a deterministic “authority mention” extractor:

    MCR patterns, MCL patterns, MRE patterns

    Benchbook reference patterns

    SCAO form IDs and instructions references

Output: AUTH_MENTIONS.json with spans and confidence, then map to:

    Authority nodes and AuthorityChunk nodes

4) Service boundary contracts: strict, versioned, and validated
4.1 OpenAPI + JSON Schema for every service boundary

    Define every local API using OpenAPI 3.1, which supports JSON Schema 2020-12 compatibility.

    Use JSON Schema 2020-12 for manifests and reports so you can validate everything mechanically.

4.2 Tika boundary: specify endpoints and parse modes

Treat Tika as a contract service:

    Use Tika Server REST usage and standardize on /rmeta for recursive metadata extraction.

5) Graph at scale: Bloom-style interaction without Bloom
5.1 WebGL graph renderer built for thousands of nodes

For the Bloom-like explorer, use a WebGL graph renderer such as sigma.js, which is explicitly aimed at rendering and interacting with thousands of nodes and edges.
5.2 Mandatory performance mechanics

Hard-require these behaviors in spec:

    neighborhood expansion, not full render

    degree-based clustering and “supernodes”

    server-side filtering and pagination

    cached perspectives

6) Supply-chain hygiene: judicial-grade provenance for the software itself
6.1 Adopt SLSA-aligned build attestations

Add a security and integrity layer for releases:

    provenance

    repeatable build inputs

    audit trail
    SLSA provides a structured framework for supply-chain integrity.

6.2 Emit SBOM for every release

Use CycloneDX SBOM for dependency inventory and provenance reporting.
7) Multimodal expansion: audio to quote pins (optional but high leverage)

If you want full multimodal court-record ingestion:

    Local speech-to-text with Whisper (open source) for audio packs, emitting time-coded quote units.

8) “Definition of Done” upgrade: add measurable acceptance tests

Extend milestone PASS criteria to include:

    OCR lane: at least one scanned PDF successfully OCR’d with OCR_REPORT.json emitted and validated

    NLP lane: at least one document produces entity graph nodes plus AUTH_MENTIONS.json

    Policy lane: OPA policy decisions emitted, policy tests passing

    Contracts lane: OpenAPI and JSON Schema validation passes before packaging

    Graph lane: sigma.js renders a 10k-node slice with progressive expansion

Recommended “Spec Addendum” checklist to append next

Add these new canonical artifacts and schemas (all JSON Schema 2020-12):

    OCR_REPORT.schema.json

    NLP_REPORT.schema.json

    AUTH_MENTIONS.schema.json

    POLICY_DECISIONS.schema.json

    SERVICE_CONTRACTS/ OpenAPI 3.1 specs per service

    GRAPH_PERSPECTIVES.schema.json

    SBOM.cdx.json per release

If you want, the next escalation step is to write the exact schema set (Draft 2020-12) and the OpenAPI 3.1 service contracts for each boundary (UI IPC, Orchestrator API, Graph API, Tika adapter, OCR adapter, Ollama adapter, rclone adapter) as an append-only “Spec Addendum Pack.”
You said:
If you want, the next escalation step is to write the exact schema set (Draft 2020-12) and the OpenAPI 3.1 service contracts
 for each boundary (UI IPC, Orchestrator API, Graph API, Tika adapter, 
OCR adapter, Ollama adapter, rclone adapter) as an append-only “Spec 
Addendum Pack.”
ChatGPT said:

Always show details
import os, json, textwrap, zipfile, hashlib, datetime, pathlib, re
from pathlib import Path

base = Path("/mnt/data/LITIGATIONOS__MASTERv1.0__SPEC_ADDENDUM_v0001")
if base.exists():
    # append-only principle: do not delete; instead create a new version folder if exists
    # but for sandbox correctness, create a unique suffix
    suffix = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
    base = Path(f"/mnt/data/LITIGATIONOS__MASTERv1.0__SPEC_ADDENDUM_v0001__{suffix}")
base.mkdir(parents=True)

# Helpers
def write_text(rel_path: str, content: str):
    p = base / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p

def write_json(rel_path: str, obj):
    p = base / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return p

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

SCHEMA_URI = "https://json-schema.org/draft/2020-12/schema"

# ---------------------------
# Common schemas
# ---------------------------
ids_schema = {
  "$schema": SCHEMA_URI,
  "$id": "litigationos://schemas/common/ids.schema.json",
  "title": "LitigationOS Common Identifiers",
  "type": "object",
  "$defs": {
    "uuid": {"type": "string", "pattern": "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"},
    "request_id": {"$ref": "#/$defs/uuid"},
    "correlation_id": {"$ref": "#/$defs/uuid"},
    "run_id": {"type":"string","pattern":"^RUN_[0-9]{8}_[0-9]{6}_[A-Z0-9]{6}$"},
    "artifact_id": {"type":"string","pattern":"^ART_[0-9]{8}_[0-9]{6}_[A-Z0-9]{6}$"},
    "node_id": {"type":"string","minLength":1,"maxLength":256},
    "edge_id": {"type":"string","minLength":1,"maxLength":256}
  },
  "additionalProperties": False
}
write_json("schemas/common/ids.schema.json", ids_schema)

hash_schema = {
  "$schema": SCHEMA_URI,
  "$id": "litigationos://schemas/common/hash.schema.json",
  "title": "LitigationOS Hash Objects",
  "type": "object",
  "$defs": {
    "sha256": {"type":"string","pattern":"^[0-9a-f]{64}$"},
    "sha1": {"type":"string","pattern":"^[0-9a-f]{40}$"},
    "md5": {"type":"string","pattern":"^[0-9a-f]{32}$"},
    "hashes": {
      "type":"object",
      "properties":{
        "sha256":{"$ref":"#/$defs/sha256"},
        "sha1":{"$ref":"#/$defs/sha1"},
        "md5":{"$ref":"#/$defs/md5"}
      },
      "required":["sha256"],
      "additionalProperties": False
    }
  },
  "additionalProperties": False
}
write_json("schemas/common/hash.schema.json", hash_schema)

errors_schema = {
  "$schema": SCHEMA_URI,
  "$id": "litigationos://schemas/common/errors.schema.json",
  "title": "LitigationOS Error and Warning Objects",
  "type": "object",
  "$defs": {
    "severity": {"type":"string","enum":["INFO","WARN","ERROR","FATAL"]},
    "error_code": {"type":"string","pattern":"^[A-Z0-9_]{3,64}$"},
    "pointer": {
      "type":"object",
      "properties":{
        "path":{"type":"string","minLength":1},
        "page_or_timecode":{"type":"string","minLength":1},
        "note":{"type":"string","minLength":1,"maxLength":4000}
      },
      "required":["path","page_or_timecode"],
      "additionalProperties": False
    },
    "error": {
      "type":"object",
      "properties":{
        "severity":{"$ref":"#/$defs/severity"},
        "code":{"$ref":"#/$defs/error_code"},
        "message":{"type":"string","minLength":1,"maxLength":8000},
        "details":{"type":["object","array","string","number","boolean","null"]},
        "pointers":{"type":"array","items":{"$ref":"#/$defs/pointer"}}
      },
      "required":["severity","code","message"],
      "additionalProperties": False
    },
    "warning": {
      "allOf":[{"$ref":"#/$defs/error"}]
    }
  },
  "additionalProperties": False
}
write_json("schemas/common/errors.schema.json", errors_schema)

pinpoints_schema = {
  "$schema": SCHEMA_URI,
  "$id": "litigationos://schemas/common/pinpoints.schema.json",
  "title": "LitigationOS Pinpoints (Evidence and Law)",
  "type":"object",
  "$defs": {
    "bbox": {
      "type":"object",
      "properties":{
        "x":{"type":"number"},
        "y":{"type":"number"},
        "w":{"type":"number"},
        "h":{"type":"number"}
      },
      "required":["x","y","w","h"],
      "additionalProperties": False
    },
    "EvidencePinpoint": {
      "type":"object",
      "properties":{
        "source_path":{"type":"string","minLength":1},
        "page_or_timecode":{"type":"string","minLength":1},
        "bates_or_hash_optional":{"type":"string","minLength":1},
        "captured_at":{"type":"string","format":"date-time"},
        "bbox":{"$ref":"#/$defs/bbox"},
        "note":{"type":"string","maxLength":8000}
      },
      "required":["source_path","page_or_timecode","captured_at"],
      "additionalProperties": False
    },
    "LawPinpoint": {
      "type":"object",
      "properties":{
        "authority_id":{"type":"string","minLength":1},
        "section":{"type":"string","minLength":1},
        "effective_date":{"type":"string","format":"date"},
        "chunk_pointer":{"type":"string","minLength":1}
      },
      "required":["authority_id","section","effective_date","chunk_pointer"],
      "additionalProperties": False
    }
  },
  "additionalProperties": False
}
write_json("schemas/common/pinpoints.schema.json", pinpoints_schema)

envelope_schema = {
  "$schema": SCHEMA_URI,
  "$id": "litigationos://schemas/common/envelope.schema.json",
  "title": "LitigationOS API Envelope",
  "type":"object",
  "properties":{
    "ok":{"type":"boolean"},
    "ts":{"type":"string","format":"date-time"},
    "request_id":{"$ref":"ids.schema.json#/$defs/request_id"},
    "correlation_id":{"$ref":"ids.schema.json#/$defs/correlation_id"},
    "result":{"type":["object","array","string","number","boolean","null"]},
    "errors":{"type":"array","items":{"$ref":"errors.schema.json#/$defs/error"}},
    "warnings":{"type":"array","items":{"$ref":"errors.schema.json#/$defs/warning"}}
  },
  "required":["ok","ts","request_id","result","errors","warnings"],
  "additionalProperties": False
}
write_json("schemas/common/envelope.schema.json", envelope_schema)

artifact_schema = {
  "$schema": SCHEMA_URI,
  "$id": "litigationos://schemas/common/artifact.schema.json",
  "title": "LitigationOS Artifact Pointer",
  "type":"object",
  "$defs":{
    "ArtifactPointer":{
      "type":"object",
      "properties":{
        "artifact_id":{"$ref":"ids.schema.json#/$defs/artifact_id"},
        "rel_path":{"type":"string","minLength":1},
        "media_type":{"type":"string","minLength":1},
        "hashes":{"$ref":"hash.schema.json#/$defs/hashes"},
        "created_at":{"type":"string","format":"date-time"},
        "note":{"type":"string","maxLength":8000}
      },
      "required":["artifact_id","rel_path","media_type","hashes","created_at"],
      "additionalProperties": False
    }
  },
  "additionalProperties": False
}
write_json("schemas/common/artifact.schema.json", artifact_schema)

policy_decision_schema = {
  "$schema": SCHEMA_URI,
  "$id": "litigationos://schemas/common/policy_decision.schema.json",
  "title":"LitigationOS Policy Decision Record",
  "type":"object",
  "properties":{
    "policy_id":{"type":"string","minLength":1},
    "policy_hash":{"$ref":"hash.schema.json#/$defs/sha256"},
    "decision_id":{"$ref":"ids.schema.json#/$defs/uuid"},
    "decided_at":{"type":"string","format":"date-time"},
    "input_digest":{"$ref":"hash.schema.json#/$defs/sha256"},
    "result":{"type":["object","array","string","number","boolean","null"]},
    "explain":{"type":["object","array","string","null"]}
  },
  "required":["policy_id","policy_hash","decision_id","decided_at","input_digest","result"],
  "additionalProperties": False
}
write_json("schemas/common/policy_decision.schema.json", policy_decision_schema)

# ---------------------------
# IPC schemas (Electron <-> Main <-> Python)
# ---------------------------
ipc_message_schema = {
  "$schema": SCHEMA_URI,
  "$id": "litigationos://schemas/ipc/ipc_message.schema.json",
  "title":"LitigationOS IPC Message",
  "type":"object",
  "properties":{
    "request_id":{"$ref":"../common/ids.schema.json#/$defs/request_id"},
    "correlation_id":{"$ref":"../common/ids.schema.json#/$defs/correlation_id"},
    "ts":{"type":"string","format":"date-time"},
    "channel":{"type":"string","enum":["INTAKE","GRAPH","PROOF","FORMS","OUTPUTS","AUDIT","SETTINGS","SYSTEM"]},
    "action":{"type":"string","minLength":1,"maxLength":128},
    "payload":{"type":["object","array","string","number","boolean","null"]},
    "idempotency_key":{"type":"string","minLength":8,"maxLength":128},
    "timeout_ms":{"type":"integer","minimum":100,"maximum":600000}
  },
  "required":["request_id","ts","channel","action","payload"],
  "additionalProperties": False
}
write_json("schemas/ipc/ipc_message.schema.json", ipc_message_schema)

ipc_response_schema = {
  "$schema": SCHEMA_URI,
  "$id": "litigationos://schemas/ipc/ipc_response.schema.json",
  "title":"LitigationOS IPC Response",
  "type":"object",
  "properties":{
    "request_id":{"$ref":"../common/ids.schema.json#/$defs/request_id"},
    "correlation_id":{"$ref":"../common/ids.schema.json#/$defs/correlation_id"},
    "ts":{"type":"string","format":"date-time"},
    "ok":{"type":"boolean"},
    "result":{"type":["object","array","string","number","boolean","null"]},
    "errors":{"type":"array","items":{"$ref":"../common/errors.schema.json#/$defs/error"}},
    "warnings":{"type":"array","items":{"$ref":"../common/errors.schema.json#/$defs/warning"}}
  },
  "required":["request_id","ts","ok","result","errors","warnings"],
  "additionalProperties": False
}
write_json("schemas/ipc/ipc_response.schema.json", ipc_response_schema)

# ---------------------------
# Orchestrator API schemas
# ---------------------------
run_create_schema = {
  "$schema": SCHEMA_URI,
  "$id": "litigationos://schemas/api/orchestrator/run_create.schema.json",
  "title":"Create Run Request",
  "type":"object",
  "properties":{
    "mode":{"type":"string","enum":["discovery","file_ready"]},
    "input_roots":{"type":"array","minItems":1,"items":{"type":"string","minLength":1}},
    "case_profile":{"type":"string","minLength":1,"maxLength":128},
    "exclude_roots":{"type":"array","items":{"type":"string","minLength":1}},
    "settings":{
      "type":"object",
      "properties":{
        "truth_lock_strictness":{"type":"string","enum":["fail_soft","fail_closed"]},
        "pcw_threshold":{"type":"number","minimum":0,"maximum":1},
        "max_workers":{"type":"integer","minimum":1,"maximum":64}
      },
      "required":["truth_lock_strictness","pcw_threshold","max_workers"],
      "additionalProperties": False
    }
  },
  "required":["mode","input_roots","settings"],
  "additionalProperties": False
}
write_json("schemas/api/orchestrator/run_create.schema.json", run_create_schema)

run_summary_schema = {
  "$schema": SCHEMA_URI,
  "$id": "litigationos://schemas/api/orchestrator/run_summary.schema.json",
  "title":"Run Summary",
  "type":"object",
  "properties":{
    "run_id":{"$ref":"../../common/ids.schema.json#/$defs/run_id"},
    "created_at":{"type":"string","format":"date-time"},
    "mode":{"type":"string","enum":["discovery","file_ready"]},
    "status":{"type":"string","enum":["CREATED","RUNNING","FAILED","BLOCKED","COMPLETED"]},
    "current_step":{"type":"string","minLength":1},
    "percent":{"type":"number","minimum":0,"maximum":100},
    "output_root":{"type":"string","minLength":1}
  },
  "required":["run_id","created_at","mode","status","current_step","percent","output_root"],
  "additionalProperties": False
}
write_json("schemas/api/orchestrator/run_summary.schema.json", run_summary_schema)

run_action_schema = {
  "$schema": SCHEMA_URI,
  "$id":"litigationos://schemas/api/orchestrator/run_action.schema.json",
  "title":"Run Action Request",
  "type":"object",
  "properties":{
    "step":{"type":"string","enum":["DISCOVER","EXTRACT","OCR","NORMALIZE","NLP","GRAPH_LOAD","PROOF_EVAL","PACKAGE"]},
    "options":{"type":"object"}
  },
  "required":["step","options"],
  "additionalProperties": False
}
write_json("schemas/api/orchestrator/run_action.schema.json", run_action_schema)

run_manifest_schema = {
  "$schema": SCHEMA_URI,
  "$id":"litigationos://schemas/reports/run_manifest.schema.json",
  "title":"RUN_MANIFEST",
  "type":"object",
  "properties":{
    "run_id":{"$ref":"../common/ids.schema.json#/$defs/run_id"},
    "bundle_root":{"type":"string","const":"LITIGATIONOS__MASTERv1.0"},
    "spec_addendum_version":{"type":"string","pattern":"^v[0-9]{4}$"},
    "created_at":{"type":"string","format":"date-time"},
    "inputs":{
      "type":"object",
      "properties":{
        "input_roots":{"type":"array","minItems":1,"items":{"type":"string","minLength":1}},
        "exclude_roots":{"type":"array","items":{"type":"string","minLength":1}}
      },
      "required":["input_roots"],
      "additionalProperties": False
    },
    "engine_versions":{"type":"object","additionalProperties":{"type":"string"}},
    "artifacts":{"type":"array","items":{"$ref":"../common/artifact.schema.json#/$defs/ArtifactPointer"}},
    "policy_decisions":{"type":"array","items":{"$ref":"../common/policy_decision.schema.json"}},
    "blockers":{"type":"array","items":{"$ref":"../common/errors.schema.json#/$defs/error"}}
  },
  "required":["run_id","bundle_root","spec_addendum_version","created_at","inputs","engine_versions","artifacts","policy_decisions","blockers"],
  "additionalProperties": False
}
write_json("schemas/reports/run_manifest.schema.json", run_manifest_schema)

# PCW report schema (minimal but strict)
pcw_report_schema = {
  "$schema": SCHEMA_URI,
  "$id":"litigationos://schemas/reports/pcw_report.schema.json",
  "title":"PCW_REPORT",
  "type":"object",
  "properties":{
    "run_id":{"$ref":"../common/ids.schema.json#/$defs/run_id"},
    "vehicle_id":{"type":"string","minLength":1},
    "generated_at":{"type":"string","format":"date-time"},
    "pcw_status":{"type":"string","enum":["PASS","FAIL","BLOCKED"]},
    "obligations":{
      "type":"array",
      "items":{
        "type":"object",
        "properties":{
          "po_id":{"type":"string","minLength":1},
          "status":{"type":"string","enum":["OPEN","PARTIAL","SATISFIED"]},
          "is_core":{"type":"boolean"},
          "required_authority":{"type":"array","items":{"$ref":"../common/pinpoints.schema.json#/$defs/LawPinpoint"}},
          "required_evidence":{"type":"array","items":{"$ref":"../common/pinpoints.schema.json#/$defs/EvidencePinpoint"}},
          "validator":{"type":"string","minLength":1},
          "assurance":{"type":"number","minimum":0,"maximum":1},
          "notes":{"type":"string","maxLength":8000}
        },
        "required":["po_id","status","is_core","required_authority","required_evidence","validator","assurance"],
        "additionalProperties": False
      }
    },
    "blockers":{"type":"array","items":{"$ref":"../common/errors.schema.json#/$defs/error"}}
  },
  "required":["run_id","vehicle_id","generated_at","pcw_status","obligations","blockers"],
  "additionalProperties": False
}
write_json("schemas/reports/pcw_report.schema.json", pcw_report_schema)

# OCR report schema
ocr_report_schema = {
  "$schema": SCHEMA_URI,
  "$id":"litigationos://schemas/reports/ocr_report.schema.json",
  "title":"OCR_REPORT",
  "type":"object",
  "properties":{
    "run_id":{"$ref":"../common/ids.schema.json#/$defs/run_id"},
    "source_pdf":{"type":"string","minLength":1},
    "generated_at":{"type":"string","format":"date-time"},
    "engine":{"type":"string","enum":["ocrmypdf","tesseract","paddleocr","doctr"]},
    "language":{"type":"string","minLength":1},
    "dpi":{"type":"integer","minimum":72,"maximum":600},
    "pages":{
      "type":"array",
      "items":{
        "type":"object",
        "properties":{
          "page":{"type":"integer","minimum":1},
          "text_coverage_ratio":{"type":"number","minimum":0,"maximum":1},
          "confidence":{"type":"number","minimum":0,"maximum":1},
          "rotation_applied":{"type":"integer","minimum":-180,"maximum":180},
          "deskew_applied":{"type":"boolean"},
          "tables_detected":{"type":"boolean"},
          "low_quality_flag":{"type":"boolean"},
          "notes":{"type":"string","maxLength":4000}
        },
        "required":["page","text_coverage_ratio","rotation_applied","deskew_applied","tables_detected","low_quality_flag"],
        "additionalProperties": False
      }
    },
    "thresholds":{
      "type":"object",
      "properties":{
        "min_text_coverage_ratio":{"type":"number","minimum":0,"maximum":1},
        "min_confidence":{"type":"number","minimum":0,"maximum":1}
      },
      "required":["min_text_coverage_ratio","min_confidence"],
      "additionalProperties": False
    },
    "blockers":{"type":"array","items":{"$ref":"../common/errors.schema.json#/$defs/error"}}
  },
  "required":["run_id","source_pdf","generated_at","engine","language","dpi","pages","thresholds","blockers"],
  "additionalProperties": False
}
write_json("schemas/reports/ocr_report.schema.json", ocr_report_schema)

# NLP report schema
nlp_report_schema = {
  "$schema": SCHEMA_URI,
  "$id":"litigationos://schemas/reports/nlp_report.schema.json",
  "title":"NLP_REPORT",
  "type":"object",
  "properties":{
    "run_id":{"$ref":"../common/ids.schema.json#/$defs/run_id"},
    "source_doc":{"type":"string","minLength":1},
    "generated_at":{"type":"string","format":"date-time"},
    "pipeline":{"type":"string","minLength":1},
    "entities":{
      "type":"array",
      "items":{
        "type":"object",
        "properties":{
          "label":{"type":"string","minLength":1},
          "text":{"type":"string","minLength":1},
          "start_char":{"type":"integer","minimum":0},
          "end_char":{"type":"integer","minimum":0},
          "confidence":{"type":"number","minimum":0,"maximum":1},
          "evidence_pin":{"$ref":"../common/pinpoints.schema.json#/$defs/EvidencePinpoint"}
        },
        "required":["label","text","start_char","end_char"],
        "additionalProperties": False
      }
    },
    "authority_mentions":{
      "type":"array",
      "items":{
        "type":"object",
        "properties":{
          "authority_type":{"type":"string","enum":["MCR","MCL","MRE","BENCHBOOK","SCAO_FORM","ADMIN_ORDER","CASELAW"]},
          "raw_text":{"type":"string","minLength":1},
          "normalized_id":{"type":"string","minLength":1},
          "span_start":{"type":"integer","minimum":0},
          "span_end":{"type":"integer","minimum":0},
          "confidence":{"type":"number","minimum":0,"maximum":1}
        },
        "required":["authority_type","raw_text","normalized_id","span_start","span_end","confidence"],
        "additionalProperties": False
      }
    },
    "blockers":{"type":"array","items":{"$ref":"../common/errors.schema.json#/$defs/error"}}
  },
  "required":["run_id","source_doc","generated_at","pipeline","entities","authority_mentions","blockers"],
  "additionalProperties": False
}
write_json("schemas/reports/nlp_report.schema.json", nlp_report_schema)

# ---------------------------
# OpenAPI 3.1 contracts
# ---------------------------
OPENAPI_DIALECT = "https://json-schema.org/draft/2020-12/schema"

def openapi_header(title, version, server_url):
    return textwrap.dedent(f"""\
    openapi: 3.1.0
    jsonSchemaDialect: "{OPENAPI_DIALECT}"
    info:
      title: "{title}"
      version: "{version}"
    servers:
      - url: "{server_url}"
    """).rstrip() + "\n"

# Orchestrator OpenAPI
orchestrator_yaml = openapi_header("LitigationOS Orchestrator API", "v0001", "http://127.0.0.1:37811")
orchestrator_yaml += textwrap.dedent("""\
paths:
  /health:
    get:
      operationId: health
      responses:
        "200":
          description: Healthy
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Envelope"
  /runs:
    post:
      operationId: createRun
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/RunCreateRequest"
      responses:
        "200":
          description: Run created
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/EnvelopeRunSummary"
  /runs/{run_id}:
    get:
      operationId: getRun
      parameters:
        - name: run_id
          in: path
          required: true
          schema:
            $ref: "#/components/schemas/RunId"
      responses:
        "200":
          description: Run status
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/EnvelopeRunSummary"
  /runs/{run_id}/actions:
    post:
      operationId: runAction
      parameters:
        - name: run_id
          in: path
          required: true
          schema:
            $ref: "#/components/schemas/RunId"
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/RunActionRequest"
      responses:
        "200":
          description: Action accepted
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/EnvelopeRunSummary"
  /runs/{run_id}/artifacts:
    get:
      operationId: listArtifacts
      parameters:
        - name: run_id
          in: path
          required: true
          schema:
            $ref: "#/components/schemas/RunId"
      responses:
        "200":
          description: Artifact list
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/EnvelopeArtifactList"
components:
  schemas:
    Uuid:
      type: string
      pattern: "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
    RunId:
      type: string
      pattern: "^RUN_[0-9]{8}_[0-9]{6}_[A-Z0-9]{6}$"
    Sha256:
      type: string
      pattern: "^[0-9a-f]{64}$"
    Error:
      type: object
      additionalProperties: false
      required: [severity, code, message]
      properties:
        severity:
          type: string
          enum: [INFO, WARN, ERROR, FATAL]
        code:
          type: string
          pattern: "^[A-Z0-9_]{3,64}$"
        message:
          type: string
          minLength: 1
          maxLength: 8000
        details: {}
        pointers:
          type: array
          items:
            $ref: "#/components/schemas/Pointer"
    Pointer:
      type: object
      additionalProperties: false
      required: [path, page_or_timecode]
      properties:
        path:
          type: string
        page_or_timecode:
          type: string
        note:
          type: string
          maxLength: 4000
    Envelope:
      type: object
      additionalProperties: false
      required: [ok, ts, request_id, result, errors, warnings]
      properties:
        ok:
          type: boolean
        ts:
          type: string
          format: date-time
        request_id:
          $ref: "#/components/schemas/Uuid"
        correlation_id:
          $ref: "#/components/schemas/Uuid"
        result: {}
        errors:
          type: array
          items:
            $ref: "#/components/schemas/Error"
        warnings:
          type: array
          items:
            $ref: "#/components/schemas/Error"
    RunCreateRequest:
      type: object
      additionalProperties: false
      required: [mode, input_roots, settings]
      properties:
        mode:
          type: string
          enum: [discovery, file_ready]
        input_roots:
          type: array
          minItems: 1
          items:
            type: string
            minLength: 1
        case_profile:
          type: string
          minLength: 1
          maxLength: 128
        exclude_roots:
          type: array
          items:
            type: string
        settings:
          type: object
          additionalProperties: false
          required: [truth_lock_strictness, pcw_threshold, max_workers]
          properties:
            truth_lock_strictness:
              type: string
              enum: [fail_soft, fail_closed]
            pcw_threshold:
              type: number
              minimum: 0
              maximum: 1
            max_workers:
              type: integer
              minimum: 1
              maximum: 64
    RunActionRequest:
      type: object
      additionalProperties: false
      required: [step, options]
      properties:
        step:
          type: string
          enum: [DISCOVER, EXTRACT, OCR, NORMALIZE, NLP, GRAPH_LOAD, PROOF_EVAL, PACKAGE]
        options:
          type: object
    ArtifactPointer:
      type: object
      additionalProperties: false
      required: [artifact_id, rel_path, media_type, hashes, created_at]
      properties:
        artifact_id:
          type: string
          pattern: "^ART_[0-9]{8}_[0-9]{6}_[A-Z0-9]{6}$"
        rel_path:
          type: string
        media_type:
          type: string
        hashes:
          type: object
          additionalProperties: false
          required: [sha256]
          properties:
            sha256:
              $ref: "#/components/schemas/Sha256"
            sha1:
              type: string
              pattern: "^[0-9a-f]{40}$"
            md5:
              type: string
              pattern: "^[0-9a-f]{32}$"
        created_at:
          type: string
          format: date-time
        note:
          type: string
          maxLength: 8000
    RunSummary:
      type: object
      additionalProperties: false
      required: [run_id, created_at, mode, status, current_step, percent, output_root]
      properties:
        run_id:
          $ref: "#/components/schemas/RunId"
        created_at:
          type: string
          format: date-time
        mode:
          type: string
          enum: [discovery, file_ready]
        status:
          type: string
          enum: [CREATED, RUNNING, FAILED, BLOCKED, COMPLETED]
        current_step:
          type: string
          minLength: 1
        percent:
          type: number
          minimum: 0
          maximum: 100
        output_root:
          type: string
    EnvelopeRunSummary:
      allOf:
        - $ref: "#/components/schemas/Envelope"
        - type: object
          properties:
            result:
              $ref: "#/components/schemas/RunSummary"
    EnvelopeArtifactList:
      allOf:
        - $ref: "#/components/schemas/Envelope"
        - type: object
          properties:
            result:
              type: object
              additionalProperties: false
              required: [items]
              properties:
                items:
                  type: array
                  items:
                    $ref: "#/components/schemas/ArtifactPointer"
""")
write_text("contracts/openapi/orchestrator.openapi.yaml", orchestrator_yaml)

# Graph API OpenAPI
graph_yaml = openapi_header("LitigationOS Graph API", "v0001", "http://127.0.0.1:37821")
graph_yaml += textwrap.dedent("""\
paths:
  /health:
    get:
      operationId: health
      responses:
        "200":
          description: Healthy
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Envelope"
  /graph/search:
    post:
      operationId: graphSearch
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/GraphSearchRequest"
      responses:
        "200":
          description: Search results
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/EnvelopeGraphSearchResponse"
  /graph/neighborhood:
    post:
      operationId: neighborhoodExpand
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/NeighborhoodExpandRequest"
      responses:
        "200":
          description: Neighborhood slice
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/EnvelopeGraphSlice"
components:
  schemas:
    Uuid:
      type: string
      pattern: "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
    Error:
      type: object
      additionalProperties: false
      required: [severity, code, message]
      properties:
        severity:
          type: string
          enum: [INFO, WARN, ERROR, FATAL]
        code:
          type: string
          pattern: "^[A-Z0-9_]{3,64}$"
        message:
          type: string
          minLength: 1
          maxLength: 8000
        details: {}
    Envelope:
      type: object
      additionalProperties: false
      required: [ok, ts, request_id, result, errors, warnings]
      properties:
        ok:
          type: boolean
        ts:
          type: string
          format: date-time
        request_id:
          $ref: "#/components/schemas/Uuid"
        correlation_id:
          $ref: "#/components/schemas/Uuid"
        result: {}
        errors:
          type: array
          items:
            $ref: "#/components/schemas/Error"
        warnings:
          type: array
          items:
            $ref: "#/components/schemas/Error"
    GraphSearchRequest:
      type: object
      additionalProperties: false
      required: [query, limit]
      properties:
        query:
          type: string
          minLength: 1
          maxLength: 2048
        filters:
          type: object
          additionalProperties: false
          properties:
            labels:
              type: array
              items:
                type: string
            edge_types:
              type: array
              items:
                type: string
            case_id:
              type: string
        limit:
          type: integer
          minimum: 1
          maximum: 5000
    Node:
      type: object
      additionalProperties: false
      required: [id, labels, properties]
      properties:
        id:
          type: string
          minLength: 1
          maxLength: 256
        labels:
          type: array
          minItems: 1
          items:
            type: string
            minLength: 1
        properties:
          type: object
    Edge:
      type: object
      additionalProperties: false
      required: [id, source, target, type, properties]
      properties:
        id:
          type: string
          minLength: 1
          maxLength: 256
        source:
          type: string
          minLength: 1
          maxLength: 256
        target:
          type: string
          minLength: 1
          maxLength: 256
        type:
          type: string
          minLength: 1
        properties:
          type: object
    GraphSlice:
      type: object
      additionalProperties: false
      required: [nodes, edges]
      properties:
        nodes:
          type: array
          items:
            $ref: "#/components/schemas/Node"
        edges:
          type: array
          items:
            $ref: "#/components/schemas/Edge"
    GraphSearchResponse:
      allOf:
        - $ref: "#/components/schemas/GraphSlice"
        - type: object
          additionalProperties: false
          required: [truncated]
          properties:
            truncated:
              type: boolean
    NeighborhoodExpandRequest:
      type: object
      additionalProperties: false
      required: [node_id, depth, limit]
      properties:
        node_id:
          type: string
          minLength: 1
          maxLength: 256
        depth:
          type: integer
          minimum: 1
          maximum: 3
        limit:
          type: integer
          minimum: 1
          maximum: 20000
    EnvelopeGraphSearchResponse:
      allOf:
        - $ref: "#/components/schemas/Envelope"
        - type: object
          properties:
            result:
              $ref: "#/components/schemas/GraphSearchResponse"
    EnvelopeGraphSlice:
      allOf:
        - $ref: "#/components/schemas/Envelope"
        - type: object
          properties:
            result:
              $ref: "#/components/schemas/GraphSlice"
""")
write_text("contracts/openapi/graph.openapi.yaml", graph_yaml)

# Tika adapter OpenAPI
tika_yaml = openapi_header("LitigationOS Tika Adapter API", "v0001", "http://127.0.0.1:37831")
tika_yaml += textwrap.dedent("""\
paths:
  /health:
    get:
      operationId: health
      responses:
        "200":
          description: Healthy
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Envelope"
  /tika/extract:
    post:
      operationId: extractText
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/TikaExtractRequest"
      responses:
        "200":
          description: Extracted
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/EnvelopeTikaExtractResponse"
components:
  schemas:
    Uuid:
      type: string
      pattern: "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
    Sha256:
      type: string
      pattern: "^[0-9a-f]{64}$"
    Error:
      type: object
      additionalProperties: false
      required: [severity, code, message]
      properties:
        severity:
          type: string
          enum: [INFO, WARN, ERROR, FATAL]
        code:
          type: string
          pattern: "^[A-Z0-9_]{3,64}$"
        message:
          type: string
          minLength: 1
          maxLength: 8000
        details: {}
    Envelope:
      type: object
      additionalProperties: false
      required: [ok, ts, request_id, result, errors, warnings]
      properties:
        ok:
          type: boolean
        ts:
          type: string
          format: date-time
        request_id:
          $ref: "#/components/schemas/Uuid"
        correlation_id:
          $ref: "#/components/schemas/Uuid"
        result: {}
        errors:
          type: array
          items:
            $ref: "#/components/schemas/Error"
        warnings:
          type: array
          items:
            $ref: "#/components/schemas/Error"
    TikaExtractRequest:
      type: object
      additionalProperties: false
      required: [input_path, mode, tika_base_url]
      properties:
        input_path:
          type: string
          minLength: 1
        mode:
          type: string
          enum: [text, rmeta]
        tika_base_url:
          type: string
          minLength: 1
          default: "http://127.0.0.1:9998"
        output_dir:
          type: string
        timeout_ms:
          type: integer
          minimum: 100
          maximum: 600000
    ArtifactPointer:
      type: object
      additionalProperties: false
      required: [rel_path, sha256, media_type]
      properties:
        rel_path:
          type: string
        sha256:
          $ref: "#/components/schemas/Sha256"
        media_type:
          type: string
    TikaExtractResponse:
      type: object
      additionalProperties: false
      required: [artifacts, content_sha256]
      properties:
        content_sha256:
          $ref: "#/components/schemas/Sha256"
        artifacts:
          type: array
          items:
            $ref: "#/components/schemas/ArtifactPointer"
    EnvelopeTikaExtractResponse:
      allOf:
        - $ref: "#/components/schemas/Envelope"
        - type: object
          properties:
            result:
              $ref: "#/components/schemas/TikaExtractResponse"
""")
write_text("contracts/openapi/tika_adapter.openapi.yaml", tika_yaml)

# OCR adapter OpenAPI
ocr_yaml = openapi_header("LitigationOS OCR Adapter API", "v0001", "http://127.0.0.1:37841")
ocr_yaml += textwrap.dedent("""\
paths:
  /health:
    get:
      operationId: health
      responses:
        "200":
          description: Healthy
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Envelope"
  /ocr/pdf:
    post:
      operationId: ocrPdf
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/OcrPdfRequest"
      responses:
        "200":
          description: OCR completed
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/EnvelopeOcrPdfResponse"
components:
  schemas:
    Uuid:
      type: string
      pattern: "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
    Sha256:
      type: string
      pattern: "^[0-9a-f]{64}$"
    Error:
      type: object
      additionalProperties: false
      required: [severity, code, message]
      properties:
        severity:
          type: string
          enum: [INFO, WARN, ERROR, FATAL]
        code:
          type: string
          pattern: "^[A-Z0-9_]{3,64}$"
        message:
          type: string
          minLength: 1
          maxLength: 8000
        details: {}
    Envelope:
      type: object
      additionalProperties: false
      required: [ok, ts, request_id, result, errors, warnings]
      properties:
        ok:
          type: boolean
        ts:
          type: string
          format: date-time
        request_id:
          $ref: "#/components/schemas/Uuid"
        correlation_id:
          $ref: "#/components/schemas/Uuid"
        result: {}
        errors:
          type: array
          items:
            $ref: "#/components/schemas/Error"
        warnings:
          type: array
          items:
            $ref: "#/components/schemas/Error"
    OcrPdfRequest:
      type: object
      additionalProperties: false
      required: [input_pdf, output_pdf, engine, language, dpi]
      properties:
        input_pdf:
          type: string
          minLength: 1
        output_pdf:
          type: string
          minLength: 1
        output_txt:
          type: string
        engine:
          type: string
          enum: [ocrmypdf, tesseract, paddleocr, doctr]
        language:
          type: string
          minLength: 1
          default: "eng"
        dpi:
          type: integer
          minimum: 72
          maximum: 600
          default: 300
        deskew:
          type: boolean
          default: true
        rotate:
          type: boolean
          default: true
        timeout_ms:
          type: integer
          minimum: 100
          maximum: 1800000
    OcrPdfResponse:
      type: object
      additionalProperties: false
      required: [output_pdf_sha256, report_path, report_sha256]
      properties:
        output_pdf_sha256:
          $ref: "#/components/schemas/Sha256"
        report_path:
          type: string
        report_sha256:
          $ref: "#/components/schemas/Sha256"
    EnvelopeOcrPdfResponse:
      allOf:
        - $ref: "#/components/schemas/Envelope"
        - type: object
          properties:
            result:
              $ref: "#/components/schemas/OcrPdfResponse"
""")
write_text("contracts/openapi/ocr_adapter.openapi.yaml", ocr_yaml)

# Ollama adapter OpenAPI
ollama_yaml = openapi_header("LitigationOS Ollama Adapter API", "v0001", "http://127.0.0.1:37851")
ollama_yaml += textwrap.dedent("""\
paths:
  /health:
    get:
      operationId: health
      responses:
        "200":
          description: Healthy
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Envelope"
  /llm/chat:
    post:
      operationId: chat
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/ChatRequest"
      responses:
        "200":
          description: Chat response
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/EnvelopeChatResponse"
  /llm/embed:
    post:
      operationId: embed
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/EmbedRequest"
      responses:
        "200":
          description: Embeddings
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/EnvelopeEmbedResponse"
  /llm/models:
    get:
      operationId: listModels
      responses:
        "200":
          description: Model list
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/EnvelopeModelList"
components:
  schemas:
    Uuid:
      type: string
      pattern: "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
    Error:
      type: object
      additionalProperties: false
      required: [severity, code, message]
      properties:
        severity:
          type: string
          enum: [INFO, WARN, ERROR, FATAL]
        code:
          type: string
          pattern: "^[A-Z0-9_]{3,64}$"
        message:
          type: string
          minLength: 1
          maxLength: 8000
        details: {}
    Envelope:
      type: object
      additionalProperties: false
      required: [ok, ts, request_id, result, errors, warnings]
      properties:
        ok:
          type: boolean
        ts:
          type: string
          format: date-time
        request_id:
          $ref: "#/components/schemas/Uuid"
        correlation_id:
          $ref: "#/components/schemas/Uuid"
        result: {}
        errors:
          type: array
          items:
            $ref: "#/components/schemas/Error"
        warnings:
          type: array
          items:
            $ref: "#/components/schemas/Error"
    ChatMessage:
      type: object
      additionalProperties: false
      required: [role, content]
      properties:
        role:
          type: string
          enum: [system, user, assistant, tool]
        content:
          type: string
    ChatRequest:
      type: object
      additionalProperties: false
      required: [ollama_base_url, model, messages, stream]
      properties:
        ollama_base_url:
          type: string
          default: "http://127.0.0.1:11434/api"
        model:
          type: string
          minLength: 1
        messages:
          type: array
          minItems: 1
          items:
            $ref: "#/components/schemas/ChatMessage"
        options:
          type: object
        stream:
          type: boolean
          default: false
    ChatResponse:
      type: object
      additionalProperties: false
      required: [role, content]
      properties:
        role:
          type: string
          const: assistant
        content:
          type: string
        usage:
          type: object
    EmbedRequest:
      type: object
      additionalProperties: false
      required: [ollama_base_url, model, input]
      properties:
        ollama_base_url:
          type: string
          default: "http://127.0.0.1:11434/api"
        model:
          type: string
          minLength: 1
        input:
          type: array
          minItems: 1
          items:
            type: string
    EmbedResponse:
      type: object
      additionalProperties: false
      required: [embeddings]
      properties:
        embeddings:
          type: array
          items:
            type: array
            items:
              type: number
    ModelList:
      type: object
      additionalProperties: false
      required: [models]
      properties:
        models:
          type: array
          items:
            type: object
    EnvelopeChatResponse:
      allOf:
        - $ref: "#/components/schemas/Envelope"
        - type: object
          properties:
            result:
              $ref: "#/components/schemas/ChatResponse"
    EnvelopeEmbedResponse:
      allOf:
        - $ref: "#/components/schemas/Envelope"
        - type: object
          properties:
            result:
              $ref: "#/components/schemas/EmbedResponse"
    EnvelopeModelList:
      allOf:
        - $ref: "#/components/schemas/Envelope"
        - type: object
          properties:
            result:
              $ref: "#/components/schemas/ModelList"
""")
write_text("contracts/openapi/ollama_adapter.openapi.yaml", ollama_yaml)

# rclone adapter OpenAPI
rclone_yaml = openapi_header("LitigationOS rclone Adapter API", "v0001", "http://127.0.0.1:37861")
rclone_yaml += textwrap.dedent("""\
paths:
  /health:
    get:
      operationId: health
      responses:
        "200":
          description: Healthy
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Envelope"
  /rclone/rc:
    post:
      operationId: rcCall
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/RcloneRcRequest"
      responses:
        "200":
          description: RC response
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/EnvelopeRcloneRcResponse"
  /rclone/sync:
    post:
      operationId: sync
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/RcloneSyncRequest"
      responses:
        "200":
          description: Sync started or completed
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/EnvelopeRcloneSyncResponse"
components:
  schemas:
    Uuid:
      type: string
      pattern: "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
    Error:
      type: object
      additionalProperties: false
      required: [severity, code, message]
      properties:
        severity:
          type: string
          enum: [INFO, WARN, ERROR, FATAL]
        code:
          type: string
          pattern: "^[A-Z0-9_]{3,64}$"
        message:
          type: string
          minLength: 1
          maxLength: 8000
        details: {}
    Envelope:
      type: object
      additionalProperties: false
      required: [ok, ts, request_id, result, errors, warnings]
      properties:
        ok:
          type: boolean
        ts:
          type: string
          format: date-time
        request_id:
          $ref: "#/components/schemas/Uuid"
        correlation_id:
          $ref: "#/components/schemas/Uuid"
        result: {}
        errors:
          type: array
          items:
            $ref: "#/components/schemas/Error"
        warnings:
          type: array
          items:
            $ref: "#/components/schemas/Error"
    RcloneRcRequest:
      type: object
      additionalProperties: false
      required: [rc_base_url, command, params]
      properties:
        rc_base_url:
          type: string
          default: "http://127.0.0.1:5572"
        command:
          type: string
          minLength: 1
        params:
          type: object
        timeout_ms:
          type: integer
          minimum: 100
          maximum: 1800000
    RcloneRcResponse:
      type: object
      additionalProperties: false
      required: [response]
      properties:
        response: {}
    RcloneSyncRequest:
      type: object
      additionalProperties: false
      required: [rc_base_url, src, dst, direction, flags]
      properties:
        rc_base_url:
          type: string
          default: "http://127.0.0.1:5572"
        src:
          type: string
          minLength: 1
        dst:
          type: string
          minLength: 1
        direction:
          type: string
          enum: [push, pull, bidirectional]
        flags:
          type: array
          items:
            type: string
        timeout_ms:
          type: integer
          minimum: 100
          maximum: 1800000
    RcloneSyncResponse:
      type: object
      additionalProperties: false
      required: [mode, summary]
      properties:
        mode:
          type: string
          enum: [rc_sync, rc_job]
        summary: {}
    EnvelopeRcloneRcResponse:
      allOf:
        - $ref: "#/components/schemas/Envelope"
        - type: object
          properties:
            result:
              $ref: "#/components/schemas/RcloneRcResponse"
    EnvelopeRcloneSyncResponse:
      allOf:
        - $ref: "#/components/schemas/Envelope"
        - type: object
          properties:
            result:
              $ref: "#/components/schemas/RcloneSyncResponse"
""")
write_text("contracts/openapi/rclone_adapter.openapi.yaml", rclone_yaml)

# ---------------------------
# Docs: port map and service matrix
# ---------------------------
write_text("docs/PORTS.md", textwrap.dedent("""\
# Ports and Local Endpoints (Canonical)

All endpoints are loopback-only unless explicitly overridden.

| Service | Default URL | Notes |
|---|---|---|
| Orchestrator API | http://127.0.0.1:37811 | Workflow control plane |
| Graph API | http://127.0.0.1:37821 | Bloom-style graph queries for UI |
| Tika Adapter | http://127.0.0.1:37831 | Wraps Apache Tika Server |
| OCR Adapter | http://127.0.0.1:37841 | Wraps OCRmyPDF and optional deep OCR lanes |
| Ollama Adapter | http://127.0.0.1:37851 | Wraps local Ollama daemon |
| rclone Adapter | http://127.0.0.1:37861 | Wraps rclone RC calls |
| Apache Tika Server | http://127.0.0.1:9998 | External process started by app |
| Ollama | http://127.0.0.1:11434/api | External process started by operator or app |
| rclone RC | http://127.0.0.1:5572 | External process started by operator or app |
| Neo4j Bolt | bolt://127.0.0.1:7687 | Database driver transport |
| Neo4j HTTP | http://127.0.0.1:7474 | Optional administrative transport |
"""))

write_text("docs/SERVICE_MATRIX.md", textwrap.dedent("""\
# Service Boundary Contracts (Canonical)

This addendum defines the boundary contracts and machine-checkable schemas for each local interface.

## Contract invariants
- Every request carries request_id and may carry correlation_id.
- Every response is wrapped in the Envelope schema.
- Every service MUST be idempotent for any request that includes idempotency_key.
- Any filing-capable export remains blocked until PCW and PCG gates PASS.

## Boundary list
- UI IPC: schemas/ipc/ipc_message.schema.json and schemas/ipc/ipc_response.schema.json
- Orchestrator API: contracts/openapi/orchestrator.openapi.yaml
- Graph API: contracts/openapi/graph.openapi.yaml
- Tika Adapter: contracts/openapi/tika_adapter.openapi.yaml
- OCR Adapter: contracts/openapi/ocr_adapter.openapi.yaml
- Ollama Adapter: contracts/openapi/ollama_adapter.openapi.yaml
- rclone Adapter: contracts/openapi/rclone_adapter.openapi.yaml
"""))

write_text("docs/VALIDATION.md", textwrap.dedent("""\
# Validation (Canonical)

## JSON Schema
All schemas declare Draft 2020-12 via:
- $schema = https://json-schema.org/draft/2020-12/schema

## OpenAPI
All OpenAPI documents use:
- openapi: 3.1.0
- jsonSchemaDialect: https://json-schema.org/draft/2020-12/schema

Validation pipeline expectation:
1) Validate all *.schema.json files under schemas/ using a Draft 2020-12 validator.
2) Parse all OpenAPI YAML files and verify openapi field is 3.1.0 and jsonSchemaDialect matches.
3) Contract tests: simulate a request to each /health endpoint and validate Envelope response shape.
"""))

write_text("docs/SECURITY.md", textwrap.dedent("""\
# Security and Local-Only Assumptions (Canonical)

- Loopback-only binding for all internal APIs.
- Electron security posture:
  - contextIsolation enabled
  - nodeIntegration disabled
  - preload exposes a minimal contextBridge surface
- No telemetry by default.
- Any network features require explicit operator opt-in.
"""))

# Examples
write_json("examples/orchestrator/create_run.request.json", {
  "mode":"discovery",
  "input_roots":["F:\\","G:\\gdrive_mirror\\"],
  "case_profile":"MEEK2_24-01507-DC",
  "exclude_roots":["C:\\"],
  "settings":{"truth_lock_strictness":"fail_closed","pcw_threshold":0.9,"max_workers":8}
})
write_json("examples/ocr/ocr_pdf.request.json", {
  "input_pdf":"F:\\LITIGATION_INTAKE\\scan1.pdf",
  "output_pdf":"F:\\LITIGATIONOS__MASTERv1.0\\RUNS\\RUN_20260121_010101_ABC123\\ocr\\scan1.ocr.pdf",
  "engine":"ocrmypdf",
  "language":"eng",
  "dpi":300,
  "deskew":True,
  "rotate":True,
  "timeout_ms":900000
})
write_json("examples/ollama/chat.request.json", {
  "ollama_base_url":"http://127.0.0.1:11434/api",
  "model":"gemma3",
  "messages":[{"role":"user","content":"Extract Michigan Court Rule citations from the following text: MCR 3.207(B)(1)."}],
  "options":{"temperature":0},
  "stream":False
})
write_json("examples/rclone/sync.request.json", {
  "rc_base_url":"http://127.0.0.1:5572",
  "src":"F:\\LITIGATION_INTAKE\\",
  "dst":"gdrive:/LITIGATION_INTAKE/",
  "direction":"push",
  "flags":["--checksum","--copy-links"],
  "timeout_ms":1800000
})

# Root index
write_text("SPEC_ADDENDUM_PACK__INDEX.md", textwrap.dedent("""\
# Spec Addendum Pack v0001 (Append-Only)

This pack adds Draft 2020-12 JSON Schemas and OpenAPI 3.1 service contracts for LitigationOS local boundaries.

## Contents
- schemas/common: Envelope, IDs, hashes, errors, pinpoints, policy decisions, artifacts
- schemas/ipc: Electron IPC message and response schemas
- schemas/api and schemas/reports: Orchestrator request schemas and report schemas
- contracts/openapi: OpenAPI 3.1 contracts for Orchestrator, Graph, Tika adapter, OCR adapter, Ollama adapter, rclone adapter
- docs: ports, service matrix, validation, security
- examples: request examples for major adapters

## Integration
Unzip into the bundle root: LITIGATIONOS__MASTERv1.0

No files in this pack overwrite existing files by default when placed under a new versioned subfolder.
"""))

# Build a manifest for this pack
file_records = []
for p in base.rglob("*"):
    if p.is_file():
        rel = str(p.relative_to(base)).replace("\\","/")
        file_records.append({
            "rel_path": rel,
            "bytes": p.stat().st_size,
            "sha256": sha256_file(p),
            "modified_utc": datetime.datetime.utcfromtimestamp(p.stat().st_mtime).replace(microsecond=0).isoformat() + "Z"
        })
pack_manifest = {
    "pack_name": base.name,
    "created_at_utc": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
    "schema_dialect": "draft-2020-12",
    "openapi_version": "3.1.0",
    "file_count": len(file_records),
    "files": sorted(file_records, key=lambda x: x["rel_path"])
}
write_json("PACK_MANIFEST.json", pack_manifest)

# Zip it
zip_path = Path("/mnt/data") / f"{base.name}.zip"
with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
    for rec in pack_manifest["files"]:
        z.write(base / rec["rel_path"], arcname=f"{base.name}/{rec['rel_path']}")
zip_path, zip_path.stat().st_size

Always show details
import os, json, textwrap, zipfile, hashlib, datetime
from pathlib import Path

base = Path("/mnt/data/LITIGATIONOS__MASTERv1.0__SPEC_ADDENDUM_v0001")
if base.exists():
    suffix = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
    base = Path(f"/mnt/data/LITIGATIONOS__MASTERv1.0__SPEC_ADDENDUM_v0001__{suffix}")
base.mkdir(parents=True, exist_ok=True)

def write_text(rel_path: str, content: str):
    p = base / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p

def write_json(rel_path: str, obj):
    p = base / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return p

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

SCHEMA_URI = "https://json-schema.org/draft/2020-12/schema"
OPENAPI_DIALECT = "https://json-schema.org/draft/2020-12/schema"

# ---- Common schemas
write_json("schemas/common/ids.schema.json", {
  "$schema": SCHEMA_URI,
  "$id": "litigationos://schemas/common/ids.schema.json",
  "title": "LitigationOS Common Identifiers",
  "type": "object",
  "$defs": {
    "uuid": {"type": "string", "pattern": "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"},
    "request_id": {"$ref": "#/$defs/uuid"},
    "correlation_id": {"$ref": "#/$defs/uuid"},
    "run_id": {"type":"string","pattern":"^RUN_[0-9]{8}_[0-9]{6}_[A-Z0-9]{6}$"},
    "artifact_id": {"type":"string","pattern":"^ART_[0-9]{8}_[0-9]{6}_[A-Z0-9]{6}$"},
    "node_id": {"type":"string","minLength":1,"maxLength":256},
    "edge_id": {"type":"string","minLength":1,"maxLength":256}
  },
  "additionalProperties": False
})

write_json("schemas/common/hash.schema.json", {
  "$schema": SCHEMA_URI,
  "$id": "litigationos://schemas/common/hash.schema.json",
  "title": "LitigationOS Hash Objects",
  "type": "object",
  "$defs": {
    "sha256": {"type":"string","pattern":"^[0-9a-f]{64}$"},
    "sha1": {"type":"string","pattern":"^[0-9a-f]{40}$"},
    "md5": {"type":"string","pattern":"^[0-9a-f]{32}$"},
    "hashes": {
      "type":"object",
      "properties":{
        "sha256":{"$ref":"#/$defs/sha256"},
        "sha1":{"$ref":"#/$defs/sha1"},
        "md5":{"$ref":"#/$defs/md5"}
      },
      "required":["sha256"],
      "additionalProperties": False
    }
  },
  "additionalProperties": False
})

write_json("schemas/common/errors.schema.json", {
  "$schema": SCHEMA_URI,
  "$id": "litigationos://schemas/common/errors.schema.json",
  "title": "LitigationOS Error and Warning Objects",
  "type": "object",
  "$defs": {
    "severity": {"type":"string","enum":["INFO","WARN","ERROR","FATAL"]},
    "error_code": {"type":"string","pattern":"^[A-Z0-9_]{3,64}$"},
    "pointer": {
      "type":"object",
      "properties":{
        "path":{"type":"string","minLength":1},
        "page_or_timecode":{"type":"string","minLength":1},
        "note":{"type":"string","minLength":1,"maxLength":4000}
      },
      "required":["path","page_or_timecode"],
      "additionalProperties": False
    },
    "error": {
      "type":"object",
      "properties":{
        "severity":{"$ref":"#/$defs/severity"},
        "code":{"$ref":"#/$defs/error_code"},
        "message":{"type":"string","minLength":1,"maxLength":8000},
        "details":{"type":["object","array","string","number","boolean","null"]},
        "pointers":{"type":"array","items":{"$ref":"#/$defs/pointer"}}
      },
      "required":["severity","code","message"],
      "additionalProperties": False
    },
    "warning": {
      "allOf":[{"$ref":"#/$defs/error"}]
    }
  },
  "additionalProperties": False
})

write_json("schemas/common/pinpoints.schema.json", {
  "$schema": SCHEMA_URI,
  "$id": "litigationos://schemas/common/pinpoints.schema.json",
  "title": "LitigationOS Pinpoints (Evidence and Law)",
  "type":"object",
  "$defs": {
    "bbox": {
      "type":"object",
      "properties":{
        "x":{"type":"number"},
        "y":{"type":"number"},
        "w":{"type":"number"},
        "h":{"type":"number"}
      },
      "required":["x","y","w","h"],
      "additionalProperties": False
    },
    "EvidencePinpoint": {
      "type":"object",
      "properties":{
        "source_path":{"type":"string","minLength":1},
        "page_or_timecode":{"type":"string","minLength":1},
        "bates_or_hash_optional":{"type":"string","minLength":1},
        "captured_at":{"type":"string","format":"date-time"},
        "bbox":{"$ref":"#/$defs/bbox"},
        "note":{"type":"string","maxLength":8000}
      },
      "required":["source_path","page_or_timecode","captured_at"],
      "additionalProperties": False
    },
    "LawPinpoint": {
      "type":"object",
      "properties":{
        "authority_id":{"type":"string","minLength":1},
        "section":{"type":"string","minLength":1},
        "effective_date":{"type":"string","format":"date"},
        "chunk_pointer":{"type":"string","minLength":1}
      },
      "required":["authority_id","section","effective_date","chunk_pointer"],
      "additionalProperties": False
    }
  },
  "additionalProperties": False
})

write_json("schemas/common/envelope.schema.json", {
  "$schema": SCHEMA_URI,
  "$id": "litigationos://schemas/common/envelope.schema.json",
  "title": "LitigationOS API Envelope",
  "type":"object",
  "properties":{
    "ok":{"type":"boolean"},
    "ts":{"type":"string","format":"date-time"},
    "request_id":{"$ref":"ids.schema.json#/$defs/request_id"},
    "correlation_id":{"$ref":"ids.schema.json#/$defs/correlation_id"},
    "result":{"type":["object","array","string","number","boolean","null"]},
    "errors":{"type":"array","items":{"$ref":"errors.schema.json#/$defs/error"}},
    "warnings":{"type":"array","items":{"$ref":"errors.schema.json#/$defs/warning"}}
  },
  "required":["ok","ts","request_id","result","errors","warnings"],
  "additionalProperties": False
})

write_json("schemas/common/artifact.schema.json", {
  "$schema": SCHEMA_URI,
  "$id": "litigationos://schemas/common/artifact.schema.json",
  "title": "LitigationOS Artifact Pointer",
  "type":"object",
  "$defs":{
    "ArtifactPointer":{
      "type":"object",
      "properties":{
        "artifact_id":{"$ref":"ids.schema.json#/$defs/artifact_id"},
        "rel_path":{"type":"string","minLength":1},
        "media_type":{"type":"string","minLength":1},
        "hashes":{"$ref":"hash.schema.json#/$defs/hashes"},
        "created_at":{"type":"string","format":"date-time"},
        "note":{"type":"string","maxLength":8000}
      },
      "required":["artifact_id","rel_path","media_type","hashes","created_at"],
      "additionalProperties": False
    }
  },
  "additionalProperties": False
})

write_json("schemas/common/policy_decision.schema.json", {
  "$schema": SCHEMA_URI,
  "$id": "litigationos://schemas/common/policy_decision.schema.json",
  "title":"LitigationOS Policy Decision Record",
  "type":"object",
  "properties":{
    "policy_id":{"type":"string","minLength":1},
    "policy_hash":{"$ref":"hash.schema.json#/$defs/sha256"},
    "decision_id":{"$ref":"ids.schema.json#/$defs/uuid"},
    "decided_at":{"type":"string","format":"date-time"},
    "input_digest":{"$ref":"hash.schema.json#/$defs/sha256"},
    "result":{"type":["object","array","string","number","boolean","null"]},
    "explain":{"type":["object","array","string","null"]}
  },
  "required":["policy_id","policy_hash","decision_id","decided_at","input_digest","result"],
  "additionalProperties": False
})

# ---- IPC schemas
write_json("schemas/ipc/ipc_message.schema.json", {
  "$schema": SCHEMA_URI,
  "$id": "litigationos://schemas/ipc/ipc_message.schema.json",
  "title":"LitigationOS IPC Message",
  "type":"object",
  "properties":{
    "request_id":{"$ref":"../common/ids.schema.json#/$defs/request_id"},
    "correlation_id":{"$ref":"../common/ids.schema.json#/$defs/correlation_id"},
    "ts":{"type":"string","format":"date-time"},
    "channel":{"type":"string","enum":["INTAKE","GRAPH","PROOF","FORMS","OUTPUTS","AUDIT","SETTINGS","SYSTEM"]},
    "action":{"type":"string","minLength":1,"maxLength":128},
    "payload":{"type":["object","array","string","number","boolean","null"]},
    "idempotency_key":{"type":"string","minLength":8,"maxLength":128},
    "timeout_ms":{"type":"integer","minimum":100,"maximum":600000}
  },
  "required":["request_id","ts","channel","action","payload"],
  "additionalProperties": False
})

write_json("schemas/ipc/ipc_response.schema.json", {
  "$schema": SCHEMA_URI,
  "$id": "litigationos://schemas/ipc/ipc_response.schema.json",
  "title":"LitigationOS IPC Response",
  "type":"object",
  "properties":{
    "request_id":{"$ref":"../common/ids.schema.json#/$defs/request_id"},
    "correlation_id":{"$ref":"../common/ids.schema.json#/$defs/correlation_id"},
    "ts":{"type":"string","format":"date-time"},
    "ok":{"type":"boolean"},
    "result":{"type":["object","array","string","number","boolean","null"]},
    "errors":{"type":"array","items":{"$ref":"../common/errors.schema.json#/$defs/error"}},
    "warnings":{"type":"array","items":{"$ref":"../common/errors.schema.json#/$defs/warning"}}
  },
  "required":["request_id","ts","ok","result","errors","warnings"],
  "additionalProperties": False
})

# ---- Orchestrator and report schemas
write_json("schemas/api/orchestrator/run_create.schema.json", {
  "$schema": SCHEMA_URI,
  "$id": "litigationos://schemas/api/orchestrator/run_create.schema.json",
  "title":"Create Run Request",
  "type":"object",
  "properties":{
    "mode":{"type":"string","enum":["discovery","file_ready"]},
    "input_roots":{"type":"array","minItems":1,"items":{"type":"string","minLength":1}},
    "case_profile":{"type":"string","minLength":1,"maxLength":128},
    "exclude_roots":{"type":"array","items":{"type":"string","minLength":1}},
    "settings":{
      "type":"object",
      "properties":{
        "truth_lock_strictness":{"type":"string","enum":["fail_soft","fail_closed"]},
        "pcw_threshold":{"type":"number","minimum":0,"maximum":1},
        "max_workers":{"type":"integer","minimum":1,"maximum":64}
      },
      "required":["truth_lock_strictness","pcw_threshold","max_workers"],
      "additionalProperties": False
    }
  },
  "required":["mode","input_roots","settings"],
  "additionalProperties": False
})

write_json("schemas/api/orchestrator/run_action.schema.json", {
  "$schema": SCHEMA_URI,
  "$id":"litigationos://schemas/api/orchestrator/run_action.schema.json",
  "title":"Run Action Request",
  "type":"object",
  "properties":{
    "step":{"type":"string","enum":["DISCOVER","EXTRACT","OCR","NORMALIZE","NLP","GRAPH_LOAD","PROOF_EVAL","PACKAGE"]},
    "options":{"type":"object"}
  },
  "required":["step","options"],
  "additionalProperties": False
})

write_json("schemas/reports/run_manifest.schema.json", {
  "$schema": SCHEMA_URI,
  "$id":"litigationos://schemas/reports/run_manifest.schema.json",
  "title":"RUN_MANIFEST",
  "type":"object",
  "properties":{
    "run_id":{"$ref":"../common/ids.schema.json#/$defs/run_id"},
    "bundle_root":{"type":"string","const":"LITIGATIONOS__MASTERv1.0"},
    "spec_addendum_version":{"type":"string","pattern":"^v[0-9]{4}$"},
    "created_at":{"type":"string","format":"date-time"},
    "inputs":{
      "type":"object",
      "properties":{
        "input_roots":{"type":"array","minItems":1,"items":{"type":"string","minLength":1}},
        "exclude_roots":{"type":"array","items":{"type":"string","minLength":1}}
      },
      "required":["input_roots"],
      "additionalProperties": False
    },
    "engine_versions":{"type":"object","additionalProperties":{"type":"string"}},
    "artifacts":{"type":"array","items":{"$ref":"../common/artifact.schema.json#/$defs/ArtifactPointer"}},
    "policy_decisions":{"type":"array","items":{"$ref":"../common/policy_decision.schema.json"}},
    "blockers":{"type":"array","items":{"$ref":"../common/errors.schema.json#/$defs/error"}}
  },
  "required":["run_id","bundle_root","spec_addendum_version","created_at","inputs","engine_versions","artifacts","policy_decisions","blockers"],
  "additionalProperties": False
})

write_json("schemas/reports/pcw_report.schema.json", {
  "$schema": SCHEMA_URI,
  "$id":"litigationos://schemas/reports/pcw_report.schema.json",
  "title":"PCW_REPORT",
  "type":"object",
  "properties":{
    "run_id":{"$ref":"../common/ids.schema.json#/$defs/run_id"},
    "vehicle_id":{"type":"string","minLength":1},
    "generated_at":{"type":"string","format":"date-time"},
    "pcw_status":{"type":"string","enum":["PASS","FAIL","BLOCKED"]},
    "obligations":{
      "type":"array",
      "items":{
        "type":"object",
        "properties":{
          "po_id":{"type":"string","minLength":1},
          "status":{"type":"string","enum":["OPEN","PARTIAL","SATISFIED"]},
          "is_core":{"type":"boolean"},
          "required_authority":{"type":"array","items":{"$ref":"../common/pinpoints.schema.json#/$defs/LawPinpoint"}},
          "required_evidence":{"type":"array","items":{"$ref":"../common/pinpoints.schema.json#/$defs/EvidencePinpoint"}},
          "validator":{"type":"string","minLength":1},
          "assurance":{"type":"number","minimum":0,"maximum":1},
          "notes":{"type":"string","maxLength":8000}
        },
        "required":["po_id","status","is_core","required_authority","required_evidence","validator","assurance"],
        "additionalProperties": False
      }
    },
    "blockers":{"type":"array","items":{"$ref":"../common/errors.schema.json#/$defs/error"}}
  },
  "required":["run_id","vehicle_id","generated_at","pcw_status","obligations","blockers"],
  "additionalProperties": False
})

write_json("schemas/reports/ocr_report.schema.json", {
  "$schema": SCHEMA_URI,
  "$id":"litigationos://schemas/reports/ocr_report.schema.json",
  "title":"OCR_REPORT",
  "type":"object",
  "properties":{
    "run_id":{"$ref":"../common/ids.schema.json#/$defs/run_id"},
    "source_pdf":{"type":"string","minLength":1},
    "generated_at":{"type":"string","format":"date-time"},
    "engine":{"type":"string","enum":["ocrmypdf","tesseract","paddleocr","doctr"]},
    "language":{"type":"string","minLength":1},
    "dpi":{"type":"integer","minimum":72,"maximum":600},
    "pages":{
      "type":"array",
      "items":{
        "type":"object",
        "properties":{
          "page":{"type":"integer","minimum":1},
          "text_coverage_ratio":{"type":"number","minimum":0,"maximum":1},
          "confidence":{"type":"number","minimum":0,"maximum":1},
          "rotation_applied":{"type":"integer","minimum":-180,"maximum":180},
          "deskew_applied":{"type":"boolean"},
          "tables_detected":{"type":"boolean"},
          "low_quality_flag":{"type":"boolean"},
          "notes":{"type":"string","maxLength":4000}
        },
        "required":["page","text_coverage_ratio","rotation_applied","deskew_applied","tables_detected","low_quality_flag"],
        "additionalProperties": False
      }
    },
    "thresholds":{
      "type":"object",
      "properties":{
        "min_text_coverage_ratio":{"type":"number","minimum":0,"maximum":1},
        "min_confidence":{"type":"number","minimum":0,"maximum":1}
      },
      "required":["min_text_coverage_ratio","min_confidence"],
      "additionalProperties": False
    },
    "blockers":{"type":"array","items":{"$ref":"../common/errors.schema.json#/$defs/error"}}
  },
  "required":["run_id","source_pdf","generated_at","engine","language","dpi","pages","thresholds","blockers"],
  "additionalProperties": False
})

write_json("schemas/reports/nlp_report.schema.json", {
  "$schema": SCHEMA_URI,
  "$id":"litigationos://schemas/reports/nlp_report.schema.json",
  "title":"NLP_REPORT",
  "type":"object",
  "properties":{
    "run_id":{"$ref":"../common/ids.schema.json#/$defs/run_id"},
    "source_doc":{"type":"string","minLength":1},
    "generated_at":{"type":"string","format":"date-time"},
    "pipeline":{"type":"string","minLength":1},
    "entities":{
      "type":"array",
      "items":{
        "type":"object",
        "properties":{
          "label":{"type":"string","minLength":1},
          "text":{"type":"string","minLength":1},
          "start_char":{"type":"integer","minimum":0},
          "end_char":{"type":"integer","minimum":0},
          "confidence":{"type":"number","minimum":0,"maximum":1},
          "evidence_pin":{"$ref":"../common/pinpoints.schema.json#/$defs/EvidencePinpoint"}
        },
        "required":["label","text","start_char","end_char"],
        "additionalProperties": False
      }
    },
    "authority_mentions":{
      "type":"array",
      "items":{
        "type":"object",
        "properties":{
          "authority_type":{"type":"string","enum":["MCR","MCL","MRE","BENCHBOOK","SCAO_FORM","ADMIN_ORDER","CASELAW"]},
          "raw_text":{"type":"string","minLength":1},
          "normalized_id":{"type":"string","minLength":1},
          "span_start":{"type":"integer","minimum":0},
          "span_end":{"type":"integer","minimum":0},
          "confidence":{"type":"number","minimum":0,"maximum":1}
        },
        "required":["authority_type","raw_text","normalized_id","span_start","span_end","confidence"],
        "additionalProperties": False
      }
    },
    "blockers":{"type":"array","items":{"$ref":"../common/errors.schema.json#/$defs/error"}}
  },
  "required":["run_id","source_doc","generated_at","pipeline","entities","authority_mentions","blockers"],
  "additionalProperties": False
})

# ---- OpenAPI documents
def openapi_header(title, version, server_url):
    return textwrap.dedent(f"""\
    openapi: 3.1.0
    jsonSchemaDialect: "{OPENAPI_DIALECT}"
    info:
      title: "{title}"
      version: "{version}"
    servers:
      - url: "{server_url}"
    """).rstrip() + "\n"

# Orchestrator OpenAPI (condensed but complete)
write_text("contracts/openapi/orchestrator.openapi.yaml", openapi_header("LitigationOS Orchestrator API", "v0001", "http://127.0.0.1:37811") + textwrap.dedent("""\
paths:
  /health:
    get:
      operationId: health
      responses:
        "200":
          description: Healthy
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Envelope"
  /runs:
    post:
      operationId: createRun
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/RunCreateRequest"
      responses:
        "200":
          description: Run created
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/EnvelopeRunSummary"
  /runs/{run_id}:
    get:
      operationId: getRun
      parameters:
        - name: run_id
          in: path
          required: true
          schema:
            $ref: "#/components/schemas/RunId"
      responses:
        "200":
          description: Run status
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/EnvelopeRunSummary"
  /runs/{run_id}/actions:
    post:
      operationId: runAction
      parameters:
        - name: run_id
          in: path
          required: true
          schema:
            $ref: "#/components/schemas/RunId"
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/RunActionRequest"
      responses:
        "200":
          description: Action accepted
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/EnvelopeRunSummary"
  /runs/{run_id}/artifacts:
    get:
      operationId: listArtifacts
      parameters:
        - name: run_id
          in: path
          required: true
          schema:
            $ref: "#/components/schemas/RunId"
      responses:
        "200":
          description: Artifact list
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/EnvelopeArtifactList"
components:
  schemas:
    Uuid:
      type: string
      pattern: "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
    RunId:
      type: string
      pattern: "^RUN_[0-9]{8}_[0-9]{6}_[A-Z0-9]{6}$"
    Sha256:
      type: string
      pattern: "^[0-9a-f]{64}$"
    Error:
      type: object
      additionalProperties: false
      required: [severity, code, message]
      properties:
        severity:
          type: string
          enum: [INFO, WARN, ERROR, FATAL]
        code:
          type: string
          pattern: "^[A-Z0-9_]{3,64}$"
        message:
          type: string
          minLength: 1
          maxLength: 8000
        details: {}
        pointers:
          type: array
          items:
            $ref: "#/components/schemas/Pointer"
    Pointer:
      type: object
      additionalProperties: false
      required: [path, page_or_timecode]
      properties:
        path:
          type: string
        page_or_timecode:
          type: string
        note:
          type: string
          maxLength: 4000
    Envelope:
      type: object
      additionalProperties: false
      required: [ok, ts, request_id, result, errors, warnings]
      properties:
        ok: { type: boolean }
        ts: { type: string, format: date-time }
        request_id: { $ref: "#/components/schemas/Uuid" }
        correlation_id: { $ref: "#/components/schemas/Uuid" }
        result: {}
        errors:
          type: array
          items: { $ref: "#/components/schemas/Error" }
        warnings:
          type: array
          items: { $ref: "#/components/schemas/Error" }
    RunCreateRequest:
      type: object
      additionalProperties: false
      required: [mode, input_roots, settings]
      properties:
        mode: { type: string, enum: [discovery, file_ready] }
        input_roots:
          type: array
          minItems: 1
          items: { type: string, minLength: 1 }
        case_profile: { type: string, minLength: 1, maxLength: 128 }
        exclude_roots:
          type: array
          items: { type: string, minLength: 1 }
        settings:
          type: object
          additionalProperties: false
          required: [truth_lock_strictness, pcw_threshold, max_workers]
          properties:
            truth_lock_strictness: { type: string, enum: [fail_soft, fail_closed] }
            pcw_threshold: { type: number, minimum: 0, maximum: 1 }
            max_workers: { type: integer, minimum: 1, maximum: 64 }
    RunActionRequest:
      type: object
      additionalProperties: false
      required: [step, options]
      properties:
        step: { type: string, enum: [DISCOVER, EXTRACT, OCR, NORMALIZE, NLP, GRAPH_LOAD, PROOF_EVAL, PACKAGE] }
        options: { type: object }
    ArtifactPointer:
      type: object
      additionalProperties: false
      required: [artifact_id, rel_path, media_type, hashes, created_at]
      properties:
        artifact_id: { type: string, pattern: "^ART_[0-9]{8}_[0-9]{6}_[A-Z0-9]{6}$" }
        rel_path: { type: string }
        media_type: { type: string }
        hashes:
          type: object
          additionalProperties: false
          required: [sha256]
          properties:
            sha256: { $ref: "#/components/schemas/Sha256" }
            sha1: { type: string, pattern: "^[0-9a-f]{40}$" }
            md5: { type: string, pattern: "^[0-9a-f]{32}$" }
        created_at: { type: string, format: date-time }
        note: { type: string, maxLength: 8000 }
    RunSummary:
      type: object
      additionalProperties: false
      required: [run_id, created_at, mode, status, current_step, percent, output_root]
      properties:
        run_id: { $ref: "#/components/schemas/RunId" }
        created_at: { type: string, format: date-time }
        mode: { type: string, enum: [discovery, file_ready] }
        status: { type: string, enum: [CREATED, RUNNING, FAILED, BLOCKED, COMPLETED] }
        current_step: { type: string, minLength: 1 }
        percent: { type: number, minimum: 0, maximum: 100 }
        output_root: { type: string, minLength: 1 }
    EnvelopeRunSummary:
      allOf:
        - $ref: "#/components/schemas/Envelope"
        - type: object
          properties:
            result: { $ref: "#/components/schemas/RunSummary" }
    EnvelopeArtifactList:
      allOf:
        - $ref: "#/components/schemas/Envelope"
        - type: object
          properties:
            result:
              type: object
              additionalProperties: false
              required: [items]
              properties:
                items:
                  type: array
                  items: { $ref: "#/components/schemas/ArtifactPointer" }
"""))

# Graph API OpenAPI
write_text("contracts/openapi/graph.openapi.yaml", openapi_header("LitigationOS Graph API", "v0001", "http://127.0.0.1:37821") + textwrap.dedent("""\
paths:
  /health:
    get:
      operationId: health
      responses:
        "200":
          description: Healthy
          content:
            application/json:
              schema: { $ref: "#/components/schemas/Envelope" }
  /graph/search:
    post:
      operationId: graphSearch
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: "#/components/schemas/GraphSearchRequest" }
      responses:
        "200":
          description: Search results
          content:
            application/json:
              schema: { $ref: "#/components/schemas/EnvelopeGraphSearchResponse" }
  /graph/neighborhood:
    post:
      operationId: neighborhoodExpand
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: "#/components/schemas/NeighborhoodExpandRequest" }
      responses:
        "200":
          description: Neighborhood slice
          content:
            application/json:
              schema: { $ref: "#/components/schemas/EnvelopeGraphSlice" }
components:
  schemas:
    Uuid:
      type: string
      pattern: "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
    Error:
      type: object
      additionalProperties: false
      required: [severity, code, message]
      properties:
        severity: { type: string, enum: [INFO, WARN, ERROR, FATAL] }
        code: { type: string, pattern: "^[A-Z0-9_]{3,64}$" }
        message: { type: string, minLength: 1, maxLength: 8000 }
        details: {}
    Envelope:
      type: object
      additionalProperties: false
      required: [ok, ts, request_id, result, errors, warnings]
      properties:
        ok: { type: boolean }
        ts: { type: string, format: date-time }
        request_id: { $ref: "#/components/schemas/Uuid" }
        correlation_id: { $ref: "#/components/schemas/Uuid" }
        result: {}
        errors:
          type: array
          items: { $ref: "#/components/schemas/Error" }
        warnings:
          type: array
          items: { $ref: "#/components/schemas/Error" }
    GraphSearchRequest:
      type: object
      additionalProperties: false
      required: [query, limit]
      properties:
        query: { type: string, minLength: 1, maxLength: 2048 }
        filters:
          type: object
          additionalProperties: false
          properties:
            labels: { type: array, items: { type: string } }
            edge_types: { type: array, items: { type: string } }
            case_id: { type: string }
        limit: { type: integer, minimum: 1, maximum: 5000 }
    Node:
      type: object
      additionalProperties: false
      required: [id, labels, properties]
      properties:
        id: { type: string, minLength: 1, maxLength: 256 }
        labels: { type: array, minItems: 1, items: { type: string } }
        properties: { type: object }
    Edge:
      type: object
      additionalProperties: false
      required: [id, source, target, type, properties]
      properties:
        id: { type: string, minLength: 1, maxLength: 256 }
        source: { type: string, minLength: 1, maxLength: 256 }
        target: { type: string, minLength: 1, maxLength: 256 }
        type: { type: string, minLength: 1 }
        properties: { type: object }
    GraphSlice:
      type: object
      additionalProperties: false
      required: [nodes, edges]
      properties:
        nodes: { type: array, items: { $ref: "#/components/schemas/Node" } }
        edges: { type: array, items: { $ref: "#/components/schemas/Edge" } }
    GraphSearchResponse:
      allOf:
        - $ref: "#/components/schemas/GraphSlice"
        - type: object
          additionalProperties: false
          required: [truncated]
          properties:
            truncated: { type: boolean }
    NeighborhoodExpandRequest:
      type: object
      additionalProperties: false
      required: [node_id, depth, limit]
      properties:
        node_id: { type: string, minLength: 1, maxLength: 256 }
        depth: { type: integer, minimum: 1, maximum: 3 }
        limit: { type: integer, minimum: 1, maximum: 20000 }
    EnvelopeGraphSearchResponse:
      allOf:
        - $ref: "#/components/schemas/Envelope"
        - type: object
          properties:
            result: { $ref: "#/components/schemas/GraphSearchResponse" }
    EnvelopeGraphSlice:
      allOf:
        - $ref: "#/components/schemas/Envelope"
        - type: object
          properties:
            result: { $ref: "#/components/schemas/GraphSlice" }
"""))

# Adapter OpenAPI documents
write_text("contracts/openapi/tika_adapter.openapi.yaml", openapi_header("LitigationOS Tika Adapter API", "v0001", "http://127.0.0.1:37831") + textwrap.dedent("""\
paths:
  /health:
    get:
      operationId: health
      responses:
        "200":
          description: Healthy
          content:
            application/json:
              schema: { $ref: "#/components/schemas/Envelope" }
  /tika/extract:
    post:
      operationId: extractText
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: "#/components/schemas/TikaExtractRequest" }
      responses:
        "200":
          description: Extracted
          content:
            application/json:
              schema: { $ref: "#/components/schemas/EnvelopeTikaExtractResponse" }
components:
  schemas:
    Uuid:
      type: string
      pattern: "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
    Sha256:
      type: string
      pattern: "^[0-9a-f]{64}$"
    Error:
      type: object
      additionalProperties: false
      required: [severity, code, message]
      properties:
        severity: { type: string, enum: [INFO, WARN, ERROR, FATAL] }
        code: { type: string, pattern: "^[A-Z0-9_]{3,64}$" }
        message: { type: string, minLength: 1, maxLength: 8000 }
        details: {}
    Envelope:
      type: object
      additionalProperties: false
      required: [ok, ts, request_id, result, errors, warnings]
      properties:
        ok: { type: boolean }
        ts: { type: string, format: date-time }
        request_id: { $ref: "#/components/schemas/Uuid" }
        correlation_id: { $ref: "#/components/schemas/Uuid" }
        result: {}
        errors: { type: array, items: { $ref: "#/components/schemas/Error" } }
        warnings: { type: array, items: { $ref: "#/components/schemas/Error" } }
    TikaExtractRequest:
      type: object
      additionalProperties: false
      required: [input_path, mode, tika_base_url]
      properties:
        input_path: { type: string, minLength: 1 }
        mode: { type: string, enum: [text, rmeta] }
        tika_base_url: { type: string, default: "http://127.0.0.1:9998" }
        output_dir: { type: string }
        timeout_ms: { type: integer, minimum: 100, maximum: 600000 }
    ArtifactPointer:
      type: object
      additionalProperties: false
      required: [rel_path, sha256, media_type]
      properties:
        rel_path: { type: string }
        sha256: { $ref: "#/components/schemas/Sha256" }
        media_type: { type: string }
    TikaExtractResponse:
      type: object
      additionalProperties: false
      required: [artifacts, content_sha256]
      properties:
        content_sha256: { $ref: "#/components/schemas/Sha256" }
        artifacts: { type: array, items: { $ref: "#/components/schemas/ArtifactPointer" } }
    EnvelopeTikaExtractResponse:
      allOf:
        - $ref: "#/components/schemas/Envelope"
        - type: object
          properties:
            result: { $ref: "#/components/schemas/TikaExtractResponse" }
"""))

write_text("contracts/openapi/ocr_adapter.openapi.yaml", openapi_header("LitigationOS OCR Adapter API", "v0001", "http://127.0.0.1:37841") + textwrap.dedent("""\
paths:
  /health:
    get:
      operationId: health
      responses:
        "200":
          description: Healthy
          content:
            application/json:
              schema: { $ref: "#/components/schemas/Envelope" }
  /ocr/pdf:
    post:
      operationId: ocrPdf
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: "#/components/schemas/OcrPdfRequest" }
      responses:
        "200":
          description: OCR completed
          content:
            application/json:
              schema: { $ref: "#/components/schemas/EnvelopeOcrPdfResponse" }
components:
  schemas:
    Uuid:
      type: string
      pattern: "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
    Sha256:
      type: string
      pattern: "^[0-9a-f]{64}$"
    Error:
      type: object
      additionalProperties: false
      required: [severity, code, message]
      properties:
        severity: { type: string, enum: [INFO, WARN, ERROR, FATAL] }
        code: { type: string, pattern: "^[A-Z0-9_]{3,64}$" }
        message: { type: string, minLength: 1, maxLength: 8000 }
        details: {}
    Envelope:
      type: object
      additionalProperties: false
      required: [ok, ts, request_id, result, errors, warnings]
      properties:
        ok: { type: boolean }
        ts: { type: string, format: date-time }
        request_id: { $ref: "#/components/schemas/Uuid" }
        correlation_id: { $ref: "#/components/schemas/Uuid" }
        result: {}
        errors: { type: array, items: { $ref: "#/components/schemas/Error" } }
        warnings: { type: array, items: { $ref: "#/components/schemas/Error" } }
    OcrPdfRequest:
      type: object
      additionalProperties: false
      required: [input_pdf, output_pdf, engine, language, dpi]
      properties:
        input_pdf: { type: string, minLength: 1 }
        output_pdf: { type: string, minLength: 1 }
        output_txt: { type: string }
        engine: { type: string, enum: [ocrmypdf, tesseract, paddleocr, doctr] }
        language: { type: string, default: "eng" }
        dpi: { type: integer, minimum: 72, maximum: 600, default: 300 }
        deskew: { type: boolean, default: true }
        rotate: { type: boolean, default: true }
        timeout_ms: { type: integer, minimum: 100, maximum: 1800000 }
    OcrPdfResponse:
      type: object
      additionalProperties: false
      required: [output_pdf_sha256, report_path, report_sha256]
      properties:
        output_pdf_sha256: { $ref: "#/components/schemas/Sha256" }
        report_path: { type: string }
        report_sha256: { $ref: "#/components/schemas/Sha256" }
    EnvelopeOcrPdfResponse:
      allOf:
        - $ref: "#/components/schemas/Envelope"
        - type: object
          properties:
            result: { $ref: "#/components/schemas/OcrPdfResponse" }
"""))

write_text("contracts/openapi/ollama_adapter.openapi.yaml", openapi_header("LitigationOS Ollama Adapter API", "v0001", "http://127.0.0.1:37851") + textwrap.dedent("""\
paths:
  /health:
    get:
      operationId: health
      responses:
        "200":
          description: Healthy
          content:
            application/json:
              schema: { $ref: "#/components/schemas/Envelope" }
  /llm/chat:
    post:
      operationId: chat
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: "#/components/schemas/ChatRequest" }
      responses:
        "200":
          description: Chat response
          content:
            application/json:
              schema: { $ref: "#/components/schemas/EnvelopeChatResponse" }
  /llm/embed:
    post:
      operationId: embed
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: "#/components/schemas/EmbedRequest" }
      responses:
        "200":
          description: Embeddings
          content:
            application/json:
              schema: { $ref: "#/components/schemas/EnvelopeEmbedResponse" }
  /llm/models:
    get:
      operationId: listModels
      responses:
        "200":
          description: Model list
          content:
            application/json:
              schema: { $ref: "#/components/schemas/EnvelopeModelList" }
components:
  schemas:
    Uuid:
      type: string
      pattern: "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
    Error:
      type: object
      additionalProperties: false
      required: [severity, code, message]
      properties:
        severity: { type: string, enum: [INFO, WARN, ERROR, FATAL] }
        code: { type: string, pattern: "^[A-Z0-9_]{3,64}$" }
        message: { type: string, minLength: 1, maxLength: 8000 }
        details: {}
    Envelope:
      type: object
      additionalProperties: false
      required: [ok, ts, request_id, result, errors, warnings]
      properties:
        ok: { type: boolean }
        ts: { type: string, format: date-time }
        request_id: { $ref: "#/components/schemas/Uuid" }
        correlation_id: { $ref: "#/components/schemas/Uuid" }
        result: {}
        errors: { type: array, items: { $ref: "#/components/schemas/Error" } }
        warnings: { type: array, items: { $ref: "#/components/schemas/Error" } }
    ChatMessage:
      type: object
      additionalProperties: false
      required: [role, content]
      properties:
        role: { type: string, enum: [system, user, assistant, tool] }
        content: { type: string }
    ChatRequest:
      type: object
      additionalProperties: false
      required: [ollama_base_url, model, messages, stream]
      properties:
        ollama_base_url: { type: string, default: "http://127.0.0.1:11434/api" }
        model: { type: string, minLength: 1 }
        messages:
          type: array
          minItems: 1
          items: { $ref: "#/components/schemas/ChatMessage" }
        options: { type: object }
        stream: { type: boolean, default: false }
    ChatResponse:
      type: object
      additionalProperties: false
      required: [role, content]
      properties:
        role: { type: string, const: assistant }
        content: { type: string }
        usage: { type: object }
    EmbedRequest:
      type: object
      additionalProperties: false
      required: [ollama_base_url, model, input]
      properties:
        ollama_base_url: { type: string, default: "http://127.0.0.1:11434/api" }
        model: { type: string, minLength: 1 }
        input:
          type: array
          minItems: 1
          items: { type: string }
    EmbedResponse:
      type: object
      additionalProperties: false
      required: [embeddings]
      properties:
        embeddings:
          type: array
          items:
            type: array
            items: { type: number }
    ModelList:
      type: object
      additionalProperties: false
      required: [models]
      properties:
        models: { type: array, items: { type: object } }
    EnvelopeChatResponse:
      allOf:
        - $ref: "#/components/schemas/Envelope"
        - type: object
          properties:
            result: { $ref: "#/components/schemas/ChatResponse" }
    EnvelopeEmbedResponse:
      allOf:
        - $ref: "#/components/schemas/Envelope"
        - type: object
          properties:
            result: { $ref: "#/components/schemas/EmbedResponse" }
    EnvelopeModelList:
      allOf:
        - $ref: "#/components/schemas/Envelope"
        - type: object
          properties:
            result: { $ref: "#/components/schemas/ModelList" }
"""))

write_text("contracts/openapi/rclone_adapter.openapi.yaml", openapi_header("LitigationOS rclone Adapter API", "v0001", "http://127.0.0.1:37861") + textwrap.dedent("""\
paths:
  /health:
    get:
      operationId: health
      responses:
        "200":
          description: Healthy
          content:
            application/json:
              schema: { $ref: "#/components/schemas/Envelope" }
  /rclone/rc:
    post:
      operationId: rcCall
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: "#/components/schemas/RcloneRcRequest" }
      responses:
        "200":
          description: RC response
          content:
            application/json:
              schema: { $ref: "#/components/schemas/EnvelopeRcloneRcResponse" }
  /rclone/sync:
    post:
      operationId: sync
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: "#/components/schemas/RcloneSyncRequest" }
      responses:
        "200":
          description: Sync started or completed
          content:
            application/json:
              schema: { $ref: "#/components/schemas/EnvelopeRcloneSyncResponse" }
components:
  schemas:
    Uuid:
      type: string
      pattern: "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
    Error:
      type: object
      additionalProperties: false
      required: [severity, code, message]
      properties:
        severity: { type: string, enum: [INFO, WARN, ERROR, FATAL] }
        code: { type: string, pattern: "^[A-Z0-9_]{3,64}$" }
        message: { type: string, minLength: 1, maxLength: 8000 }
        details: {}
    Envelope:
      type: object
      additionalProperties: false
      required: [ok, ts, request_id, result, errors, warnings]
      properties:
        ok: { type: boolean }
        ts: { type: string, format: date-time }
        request_id: { $ref: "#/components/schemas/Uuid" }
        correlation_id: { $ref: "#/components/schemas/Uuid" }
        result: {}
        errors: { type: array, items: { $ref: "#/components/schemas/Error" } }
        warnings: { type: array, items: { $ref: "#/components/schemas/Error" } }
    RcloneRcRequest:
      type: object
      additionalProperties: false
      required: [rc_base_url, command, params]
      properties:
        rc_base_url: { type: string, default: "http://127.0.0.1:5572" }
        command: { type: string, minLength: 1 }
        params: { type: object }
        timeout_ms: { type: integer, minimum: 100, maximum: 1800000 }
    RcloneRcResponse:
      type: object
      additionalProperties: false
      required: [response]
      properties:
        response: {}
    RcloneSyncRequest:
      type: object
      additionalProperties: false
      required: [rc_base_url, src, dst, direction, flags]
      properties:
        rc_base_url: { type: string, default: "http://127.0.0.1:5572" }
        src: { type: string, minLength: 1 }
        dst: { type: string, minLength: 1 }
        direction: { type: string, enum: [push, pull, bidirectional] }
        flags: { type: array, items: { type: string } }
        timeout_ms: { type: integer, minimum: 100, maximum: 1800000 }
    RcloneSyncResponse:
      type: object
      additionalProperties: false
      required: [mode, summary]
      properties:
        mode: { type: string, enum: [rc_sync, rc_job] }
        summary: {}
    EnvelopeRcloneRcResponse:
      allOf:
        - $ref: "#/components/schemas/Envelope"
        - type: object
          properties:
            result: { $ref: "#/components/schemas/RcloneRcResponse" }
    EnvelopeRcloneSyncResponse:
      allOf:
        - $ref: "#/components/schemas/Envelope"
        - type: object
          properties:
            result: { $ref: "#/components/schemas/RcloneSyncResponse" }
"""))

# ---- Docs
write_text("docs/PORTS.md", textwrap.dedent("""\
# Ports and Local Endpoints (Canonical)

All endpoints are loopback-only unless explicitly overridden.

| Service | Default URL | Notes |
|---|---|---|
| Orchestrator API | http://127.0.0.1:37811 | Workflow control plane |
| Graph API | http://127.0.0.1:37821 | Bloom-style graph queries for UI |
| Tika Adapter | http://127.0.0.1:37831 | Wraps Apache Tika Server |
| OCR Adapter | http://127.0.0.1:37841 | Wraps OCRmyPDF and optional deep OCR lanes |
| Ollama Adapter | http://127.0.0.1:37851 | Wraps local Ollama daemon |
| rclone Adapter | http://127.0.0.1:37861 | Wraps rclone RC calls |
| Apache Tika Server | http://127.0.0.1:9998 | External process started by app |
| Ollama | http://127.0.0.1:11434/api | External process started by operator or app |
| rclone RC | http://127.0.0.1:5572 | External process started by operator or app |
| Neo4j Bolt | bolt://127.0.0.1:7687 | Database driver transport |
| Neo4j HTTP | http://127.0.0.1:7474 | Optional administrative transport |
"""))

write_text("docs/SERVICE_MATRIX.md", textwrap.dedent("""\
# Service Boundary Contracts (Canonical)

This addendum defines the boundary contracts and machine-checkable schemas for each local interface.

## Contract invariants
- Every request carries request_id and may carry correlation_id.
- Every response is wrapped in the Envelope schema.
- Every service MUST be idempotent for any request that includes idempotency_key.
- Any filing-capable export remains blocked until PCW and PCG gates PASS.

## Boundary list
- UI IPC: schemas/ipc/ipc_message.schema.json and schemas/ipc/ipc_response.schema.json
- Orchestrator API: contracts/openapi/orchestrator.openapi.yaml
- Graph API: contracts/openapi/graph.openapi.yaml
- Tika Adapter: contracts/openapi/tika_adapter.openapi.yaml
- OCR Adapter: contracts/openapi/ocr_adapter.openapi.yaml
- Ollama Adapter: contracts/openapi/ollama_adapter.openapi.yaml
- rclone Adapter: contracts/openapi/rclone_adapter.openapi.yaml
"""))

write_text("docs/VALIDATION.md", textwrap.dedent("""\
# Validation (Canonical)

## JSON Schema
All schemas declare Draft 2020-12 via:
- $schema = https://json-schema.org/draft/2020-12/schema

## OpenAPI
All OpenAPI documents use:
- openapi: 3.1.0
- jsonSchemaDialect: https://json-schema.org/draft/2020-12/schema

Validation pipeline expectation:
1) Validate all *.schema.json files under schemas/ using a Draft 2020-12 validator.
2) Parse all OpenAPI YAML files and verify openapi field is 3.1.0 and jsonSchemaDialect matches.
3) Contract tests: simulate a request to each /health endpoint and validate Envelope response shape.
"""))

write_text("docs/SECURITY.md", textwrap.dedent("""\
# Security and Local-Only Assumptions (Canonical)

- Loopback-only binding for all internal APIs.
- Electron security posture:
  - contextIsolation enabled
  - nodeIntegration disabled
  - preload exposes a minimal contextBridge surface
- No telemetry by default.
- Any network features require explicit operator opt-in.
"""))

# ---- Examples
write_json("examples/orchestrator/create_run.request.json", {
  "mode":"discovery",
  "input_roots":["F:\\","G:\\gdrive_mirror\\"],
  "case_profile":"MEEK2_24-01507-DC",
  "exclude_roots":["C:\\"],
  "settings":{"truth_lock_strictness":"fail_closed","pcw_threshold":0.9,"max_workers":8}
})
write_json("examples/ocr/ocr_pdf.request.json", {
  "input_pdf":"F:\\LITIGATION_INTAKE\\scan1.pdf",
  "output_pdf":"F:\\LITIGATIONOS__MASTERv1.0\\RUNS\\RUN_20260121_010101_ABC123\\ocr\\scan1.ocr.pdf",
  "engine":"ocrmypdf",
  "language":"eng",
  "dpi":300,
  "deskew":True,
  "rotate":True,
  "timeout_ms":900000
})
write_json("examples/ollama/chat.request.json", {
  "ollama_base_url":"http://127.0.0.1:11434/api",
  "model":"gemma3",
  "messages":[{"role":"user","content":"Extract Michigan Court Rule citations from the following text: MCR 3.207(B)(1)."}],
  "options":{"temperature":0},
  "stream":False
})
write_json("examples/rclone/sync.request.json", {
  "rc_base_url":"http://127.0.0.1:5572",
  "src":"F:\\LITIGATION_INTAKE\\",
  "dst":"gdrive:/LITIGATION_INTAKE/",
  "direction":"push",
  "flags":["--checksum","--copy-links"],
  "timeout_ms":1800000
})

# ---- Root index
write_text("SPEC_ADDENDUM_PACK__INDEX.md", textwrap.dedent(f"""\
# Spec Addendum Pack v0001 (Append-Only)

This pack adds Draft 2020-12 JSON Schemas and OpenAPI 3.1 service contracts for LitigationOS local boundaries.

## Contents
- schemas/common: Envelope, IDs, hashes, errors, pinpoints, policy decisions, artifacts
- schemas/ipc: Electron IPC message and response schemas
- schemas/api and schemas/reports: Orchestrator request schemas and report schemas
- contracts/openapi: OpenAPI 3.1 contracts for Orchestrator, Graph, Tika adapter, OCR adapter, Ollama adapter, rclone adapter
- docs: ports, service matrix, validation, security
- examples: request examples for major adapters

## Integration
Unzip into the bundle root: LITIGATIONOS__MASTERv1.0

No files in this pack overwrite existing files by default when placed under a new versioned subfolder.
"""))

# ---- Pack manifest and zip
file_records = []
for p in base.rglob("*"):
    if p.is_file():
        rel = str(p.relative_to(base)).replace("\\","/")
        file_records.append({
            "rel_path": rel,
            "bytes": p.stat().st_size,
            "sha256": sha256_file(p),
            "modified_utc": datetime.datetime.utcfromtimestamp(p.stat().st_mtime).replace(microsecond=0).isoformat() + "Z"
        })

pack_manifest = {
    "pack_name": base.name,
    "created_at_utc": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
    "schema_dialect": "draft-2020-12",
    "openapi_version": "3.1.0",
    "file_count": len(file_records),
    "files": sorted(file_records, key=lambda x: x["rel_path"])
}
write_json("PACK_MANIFEST.json", pack_manifest)

zip_path = Path("/mnt/data") / f"{base.name}.zip"
with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
    for rec in pack_manifest["files"]:
        z.write(base / rec["rel_path"], arcname=f"{base.name}/{rec['rel_path']}")

zip_path, zip_path.stat().st_size

Result

(PosixPath('/mnt/data/LITIGATIONOS__MASTERv1.0__SPEC_ADDENDUM_v0001.zip'),
 22630)

Always show details
import os, glob
zips = sorted(glob.glob("/mnt/data/LITIGATIONOS__MASTERv1.0__SPEC_ADDENDUM_v0001*.zip"))
zips

Result

['/mnt/data/LITIGATIONOS__MASTERv1.0__SPEC_ADDENDUM_v0001.zip']

Delivered. ✅ This is an append-only Spec Addendum Pack containing:

    Draft 2020-12 JSON Schemas (machine-checkable)

    OpenAPI 3.1 service contracts for each boundary (Orchestrator, Graph, Tika/OCR/Ollama/rclone adapters) using jsonSchemaDialect (OAS 3.1 feature)

    A UI IPC contract as Draft 2020-12 JSON Schemas (Electron IPC message/response)

Key standards anchors (so validators know what they’re looking at):

    JSON Schema Draft 2020-12 uses $schema: https://json-schema.org/draft/2020-12/schema

    OpenAPI 3.1 supports jsonSchemaDialect (used in every contract)

    External dependencies referenced canonically:

        Tika Server commonly exposed on :9998

        rclone RC default bind 127.0.0.1:5572

What’s inside the pack
JSON Schema (Draft 2020-12)

    schemas/common/*

        envelope.schema.json (standard API envelope)

        ids.schema.json, hash.schema.json, errors.schema.json

        pinpoints.schema.json (evidence + law pinpoint objects)

        artifact.schema.json, policy_decision.schema.json

    schemas/ipc/*

        ipc_message.schema.json, ipc_response.schema.json

    schemas/api/orchestrator/*

        run_create.schema.json, run_action.schema.json

    schemas/reports/*

        run_manifest.schema.json, pcw_report.schema.json, ocr_report.schema.json, nlp_report.schema.json

OpenAPI 3.1 contracts

    contracts/openapi/orchestrator.openapi.yaml

    contracts/openapi/graph.openapi.yaml

    contracts/openapi/tika_adapter.openapi.yaml

    contracts/openapi/ocr_adapter.openapi.yaml

    contracts/openapi/ollama_adapter.openapi.yaml

    contracts/openapi/rclone_adapter.openapi.yaml

Operator docs + examples

    docs/PORTS.md, docs/SERVICE_MATRIX.md, docs/VALIDATION.md, docs/SECURITY.md

    examples/* (request payload examples)

