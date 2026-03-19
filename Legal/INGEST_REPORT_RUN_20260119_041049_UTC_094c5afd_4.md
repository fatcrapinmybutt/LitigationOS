# INGEST_REPORT — RUN_20260119_041049_UTC_094c5afd
Generated: 2026-01-19T04:11:01Z

This run ingested your uploaded materials and existing docs into structured layers:
Atoms → Signals → Scores → Deltas → Gates → Actions → Vehicles, plus GraphContracts CSV export.

## Counts
- atoms: 10182
- signals: 5999
- deltas: 6
- actions: 6
- gates: 6
- vehicles: 6

## Where the outputs are
Run folder:
- `BRAIN/RUNS/RUN_20260119_041049_UTC_094c5afd/`
Core files:
- atoms: `atoms.jsonl`
- signals: `signals.jsonl`
- scores: `scores.jsonl`
- deltas: `deltas.jsonl`
- gates: `gates.jsonl`
- actions: `actions.jsonl`
- vehicles: `vehicles.jsonl`
Graph export:
- nodes: `graph/nodes.csv`
- edges: `graph/edges.csv`
Validation:
- `graph/validation/validation_report.json`

Replay:
- jobqueue: `jobqueue.sqlite`
- event log: `LOGS/runs/RUN_20260119_041049_UTC_094c5afd.jsonl`

## Top deltas
- **Graph Import/Export** (priority 13) `DELTA_0c67e30a0da0ecbb`
  - supporting_signals: 18
  - supporting_atoms: 25
- **Local LLM Stack** (priority 13) `DELTA_1bb9396f41622e65`
  - supporting_signals: 18
  - supporting_atoms: 40
- **Forms-First** (priority 13) `DELTA_26a8a689e2092974`
  - supporting_signals: 18
  - supporting_atoms: 26
- **Integrity + Bundling** (priority 13) `DELTA_561034e86d56f80d`
  - supporting_signals: 18
  - supporting_atoms: 18
- **Replayability** (priority 13) `DELTA_d1aac6bad87fcbce`
  - supporting_signals: 18
  - supporting_atoms: 30
- **AuthoritySnapshot** (priority 12) `DELTA_0ad0c173f4441623`
  - supporting_signals: 18
  - supporting_atoms: 21

## Top actions (autonomous build backlog)
- **Implement Local LLM Stack core**️** (priority 13) `ACT_78a0c7f4c1020b69`
  - depends_on_gates: GATE_REPLAYABILITY
  - supports_deltas: DELTA_1bb9396f41622e65
- **Implement Integrity + Bundling core**️** (priority 13) `ACT_870b86b22d0393a8`
  - depends_on_gates: GATE_REPLAYABILITY
  - supports_deltas: DELTA_561034e86d56f80d
- **Implement Graph Import/Export core**️** (priority 13) `ACT_8b2cd4badfff19e8`
  - depends_on_gates: GATE_AUTHORITY_SNAPSHOT, GATE_FORMS_CATALOG
  - supports_deltas: DELTA_0c67e30a0da0ecbb
- **Implement Replayability core**️** (priority 13) `ACT_a1da860b69d8094a`
  - depends_on_gates: none
  - supports_deltas: DELTA_d1aac6bad87fcbce
- **Implement Forms-First core**️** (priority 13) `ACT_cf22c9bf9edc2a05`
  - depends_on_gates: GATE_REPLAYABILITY
  - supports_deltas: DELTA_26a8a689e2092974
- **Implement AuthoritySnapshot core**️** (priority 12) `ACT_5d6a1cd87fb77d78`
  - depends_on_gates: GATE_REPLAYABILITY
  - supports_deltas: DELTA_0ad0c173f4441623

## Gate status summary
- `GATE_QUOTES_QUOTELOCK` — **OBLIGATION_OPEN** — QuoteLock (verbatim-only)
- `GATE_AUTHORITY_SNAPSHOT` — **OBLIGATION_PARTIAL** — AuthoritySnapshot present
- `GATE_FORMS_CATALOG` — **OBLIGATION_PARTIAL** — Forms catalog present
- `GATE_P0_LEDGER` — **OBLIGATION_OPEN** — PO ledger coupling (PCW enforce)
- `GATE_GRAPH_CONTRACTS` — **OBLIGATION_PARTIAL** — GraphContracts validation
- `GATE_REPLAYABILITY` — **OBLIGATION_PARTIAL** — Replayable run receipts

## Vehicle candidates detected (candidate-only)
- `VEH_25509e597360e127` — lane **appeal** — vehicle `appeal` — status CANDIDATE
- `VEH_8670db397476a584` — lane **foia** — vehicle `foia` — status CANDIDATE
- `VEH_8b76a42d7d2f2231` — lane **jtc** — vehicle `jtc` — status CANDIDATE
- `VEH_41a5e684fd8358ed` — lane **system** — vehicle `system` — status CANDIDATE
- `VEH_SYSTEM_PIPELINE` — lane **system** — vehicle `autonomous_ingest_pipeline` — status CANDIDATE
- `VEH_fed00f1f20acc2fc` — lane **trial** — vehicle `trial` — status CANDIDATE

## Top signals (sample)
- **forms** (15) `SIG_1314c59fee002f04` — with open(dst, "w", encoding="utf-8") as f: f.write(base.rstrip() + "\n\n" + append.strip() + "\n") assert os.path.exists(dst) and os.path.getsize(dst) > 0, "Output missing/empty"os.path.getsize(dst), dst Result(296424, '/mnt/data/LITIGATIONOS_GRANDMASTER_PLAYBOOK_v2026-01-18.26.md') Appended APPENDIX v2026-01-18.26 (P396–P460) with high-signal deltas focused on closing integration gaps and making the next build s...
- **graph** (15) `SIG_1f2dcf559f38e1f8` — === PAGE 245 === with open(dst, "w", encoding="utf-8") as f: f.write(base.rstrip() + "\n\n" + append.strip() + "\n") assert os.path.exists(dst) and os.path.getsize(dst) > 0, "Output missing/empty"(os.path.getsize(dst), dst) Result(313378, '/mnt/data/LITIGATIONOS_GRANDMASTER_PLAYBOOK_v2026-01-18.28.md') Appended APPENDIX v2026-01-18.28 (P521–P600) with high-signal deltas that add visual document retrieval, a govern...
- **other** (15) `SIG_1fff925538163cbe` — https://www.law.cornell.edu/wex/reputation https://www.law.cornell.edu/wex/reputed https://www.law.cornell.edu/wex/request https://www.law.cornell.edu/wex/request_for_admission https://www.law.cornell.edu/wex/request_to_admit https://www.law.cornell.edu/wex/requests_for_admission https://www.law.cornell.edu/wex/required_minimum_distribution https://www.law.cornell.edu/wex/requirements_contract https://www.law.corn...
- **forms** (15) `SIG_289a711308ebef5f` — === PAGE 128 === NL.2 CASv2 Receipt schema (SCHEMAS/cas_receipt.schema.json) json {{ "$schema":"https://json-schema.org/draft/2020-12/schema", "$id":"urn:litigationos:schema:cas_receipt:v2", "title":"CASv2 Receipt", "type":"object", "additionalProperties":false, "required":["receipt_id","created_at_utc","pack_id","pack_bytes","blob_entries","prev_receipt_id","chain_hash"], "properties":{{ "receipt_id":{{"type":"st...
- **graph** (15) `SIG_29751b0a175420e6` — if p.is_dir(): root = p.parent break (root / "scripts").mkdir(exist_ok=True) (root / "docs").mkdir(exist_ok=True) # --- Add OpenLineage emitter (minimal spec-aligned JSONL) --- openlineage_py = r'''#!/usr/bin/env python3 """ openlineage_emit.py Minimal OpenLineage JSONL emitter for LitigationOS Master Graph pipeline runs. - No external deps required. - Emits START and COMPLETE events with basic job/run/dataset ide...
- **forms** (15) `SIG_3daf5f7ccffd5fe5` — assert os.path.exists(dst) and os.path.getsize(dst) > 0(os.path.getsize(dst), dst) python import os src = "/mnt/data/LITIGATIONOS_GRANDMASTER_PLAYBOOK_v2026-01-18.25.md"dst = "/mnt/data/LITIGATIONOS_GRANDMASTER_PLAYBOOK_v2026-01-18.26.md" assert os.path.exists(src) and os.path.getsize(src) > 0, f"Source missing or empty: {src}" with open(src, "r", encoding="utf-8") as f: base = f.read() append = """\==============...
- **forms** (15) `SIG_40ff4d116d297d4f` — === PAGE 137 === "properties":{{ "chunk_id":{{"type":"string","minLength":16}}, "offset":{{"type":"integer","minimum":0}}, "length":{{"type":"integer","minimum":0}} }} }} }} }} }} }}, "prev_receipt_id":{{"type":["string","null"]}}, "chain_hash":{{"type":"string","minLength":16}}, "signature":{{ "type":["object","null"], "additionalProperties":false, "required":["alg","public_key_id","sig_b64"], "properties":{{ "al...
- **forms** (15) `SIG_7eb0de5458591486` — https://hf.co/facebook/nougat-small https://hf.co/Norm/nougat-latex-base Extraction Consensus Engine (ECE): deterministic promotion rules (“two-of-three before promotion”) for ﬁelds/quotes when OCR/VLM disagree; QuoteLock remains the ﬁnal gate for VERIFIED quotes. Graph Schema v1.2: explicit core node/edge types with hard invariants tying Propositions → AuthorityPins and Quotes → EvidenceAtoms → FactPins, plus req...
- **llm_stack** (15) `SIG_9bae2ad1c6586a66` — === PAGE 221 === Rule: HF Spaces are never runtime deps. They are technique probes. Every Space yields:(1) Technique Notes (what it does), (2) Candidate local modules, (3) License/governor check, (4) Deterministic local test harness, (5) Integration points (events, POs, manifests).Discovered Spaces (probe-only; capture in MRLG):- MinerU (PDF→Markdown+JSON concept): https://hf.co/spaces/opendatalab/MinerU (Space; u...
- **module_need** (15) `SIG_9d1307a41210cfe3` — --- # APPENDIX NL — JSON SCHEMAS (NORMATIVE, MACHINE-CHECKABLE)All schemas are Draft 2020-12. Store them in /SCHEMAS/ and validate them in CI and at runtime (PCG gate). ## NL.1 CASv2 PointerRecord schema (SCHEMAS/asset_pointer.schema.json)```json{{ "$schema":"https://json-schema.org/draft/2020-12/schema", "$id":"urn:litigationos:schema:asset_pointer:v2", "title":"CASv2 Asset PointerRecord", "type":"object", "addit...
- **module_need** (15) `SIG_b08410458742420f` — License risk example (do not ship; internal evaluation only unless cleared):- Pile of Law: https://hf.co/datasets/pile-of-law/pile-of-law (commonly tagged CC-BY-NC-SA; treat as INTERNAL_ONLY unless policy updated) P273) “OFFLINE-BUILD, OFFLINE-RUN” DOUBLE GATEMotivation: protect reliability, privacy, and court defensibility.Rules:- BUILD can optionally download dependencies; RUN must function with “no internet” mo...
- **forms** (15) `SIG_b4a0387d26843ae5` — === PAGE 237 === python import os src = "/mnt/data/LITIGATIONOS_GRANDMASTER_PLAYBOOK_v2026-01-18.26.md"dst = "/mnt/data/LITIGATIONOS_GRANDMASTER_PLAYBOOK_v2026-01-18.27.md" if not (os.path.exists(src) and os.path.getsize(src) > 0): raise FileNotFoundError(f"Source missing/empty: {src}") with open(src, "r", encoding="utf-8") as f: base = f.read() append = """\========================================================...
- **graph** (15) `SIG_c8c65d121730f26d` — === PAGE 24 === continue appending. use my google drive to ﬁnd additional ides. python from pathlib import Path v3_path = Path("/mnt/data/LITIGATIONOS_MASTER_SUPERPIN_NO_LIMIT_v0003.md")v3 = v3_path.read_text(encoding="utf-8") append = r""" Z)GOVERNOR PILLAR + CONSTELLATION VAULT + ULTRA++ HYBRID VIEWER (CANONICAL CANVAS LAYER)Z1 WHY:Provide a first-class “brains UI” (graph-first) + canonical artifact store that s...
- **forms** (15) `SIG_ca881aa35cd8bcee` — === PAGE 207 === INTERNAL_ONLY unless acceptance+redistribution allowed)- https://hf.co/MahmoudAshraf/mms-300m-1130-forced-aligner (license: Apache-2.0)Legal dataset warning example:- https://hf.co/datasets/pile-of-law/pile-of-law (license: CC-BY-NC-SA-4.0 => INTERNAL_ONLY by default; do not ship; do not mix into commercial training without legal review) P234) LOCAL LLM ROUTER v3 — “SELF-HOST ONLY, TOOL-GATED”Inte...
- **module_need** (15) `SIG_cd11476f2a8c23c1` — --- # APPENDIX NL — JSON SCHEMAS (NORMATIVE, MACHINE-CHECKABLE)All schemas are Draft 2020-12. Store them in /SCHEMAS/ and validate them in CI and at runtime (PCG gate). ## NL.1 CASv2 PointerRecord schema (SCHEMAS/asset_pointer.schema.json)```json{{ "$schema":"https://json-schema.org/draft/2020-12/schema", "$id":"urn:litigationos:schema:asset_pointer:v2", "title":"CASv2 Asset PointerRecord", "type":"object", "addit...
- **graph** (15) `SIG_cd177ef711616d6c` — append = f""" # Δ APPEND-ONLY DELTA — v0030 — {now} Goal: eliminate any ambiguity caused by illustrative “…” sample fields by providing machine-checkable schemas (JSON Schema) and normative invariants. Adds ceiling-level expansion items for CASv2, PO-ledger, and replay logs. ## Δ0 Normative interpretation rule (retroactive) If any prior section contains an “example record”, treat it as illustrative only. **Normati...
- **automation** (15) `SIG_cd6abbda74880ab6` — === PAGE 238 === Goal: stable retrieval chunks across repeated runs (replayable indexing).Chunk identity:- chunk_id = H(doc_id|page|layout_label|bbox_rounded|norm_text_hash)- bbox_rounded uses fixed decimal; norm_text_hash uses unicode normalize + whitespace fold.Outputs:- CHUNKS/index.jsonl (chunk metadata)- CHUNKS/map_to_pins.jsonl (chunk→FactPins/QuoteIds)Safety:- chunks are recall aids only; they never become ...
- **forms** (15) `SIG_ddc7618ed7e03952` — P0f.CAS cache (content-addressed derived artifacts) at F:\LitigationOS\CACHE\cas\ P0g.Constellation Vault (optional canonical artifact store):http://localhost:8899 (VaultCID stored on Artifact nodes) P0h.Watchers:USN-journal watcher (Windows) or polling fallback;triggers incremental builds ### 1.Kernel Services (must exist) K1.CorpusManager:enforces PRESERVE/WORKING lanes;source immutability;scope boundaries;stora...
- **graph** (15) `SIG_de6f4fdaaad58b23` — === PAGE 27 === Z)GOVERNOR PILLAR + CONSTELLATION VAULT + ULTRA++ HYBRID VIEWER (CANONICAL CANVAS LAYER)Z1 WHY:Provide a first-class “brains UI” (graph-first) + canonical artifact store that survives sessions and removes link-rot:upload-once, reference forever; packaging snapshots from canonical store; lint gates everything.Z2 CONSTELLATION VAULT (LOCAL CANONICAL STORE; OPTIONAL BUT RECOMMENDED)- Default host:http...
- **graph** (14) `SIG_01459f2b1a01b809` — P1325) RERANKER GOVERNOR v1 — RERANK IS A MODEL WITH LICENSE + POLICY Add ModelGovernor entries (pointers; hydrate explicit): - BAAI/bge-reranker-v2-m3 (Apache-2.0): https://hf.co/BAAI/bge-reranker-v2-m3 - cross-encoder/ms-marco-MiniLM-L6-v2 (Apache-2.0): https://hf.co/cross-encoder/ms-marco-MiniLM-L6-v2 Notes: - bge-reranker provides strong multilingual; ms-marco MiniLM is lightweight and stable. Gate: - rerank s...
- **automation** (14) `SIG_023523149408c644` — P1329) TRANSCRIPT RECEIPTS v2 — MAKE TRANSCRIPTION REPLAYABLE TranscriptReceipt fields: - media_id, asr_model_id, diarization_model_id (optional) - preprocessing: sample rate, channels, normalization - decoding settings, timestamps policy, chunk sizes - checksum of audio extraction output (optional) Artifacts: - schemas/transcript_receipt.schema.json - TRANSCRIPTS/<run_id>/receipt.json Gate: - any transcript in a ...
- **graph** (14) `SIG_03d66160e3468324` — APPENDIX EL:FULL_STACK_LAYOUT_REFERENCE(canonical folders;no drift)EL0 Root layout (stable):/CURRENT,/VERSIONS,/RELEASES,/TOOLS,/MANIFEST,/POLICY,/SCHEMA,/AI,/UI,/RUNS,/ASSETS_EXTERNAL,/CAAV,/SECURITY,/SPEC,/DOCS,/PLUGINS./DOCS includes runbooks,operator guides,API docs,architecture,threat model./TOOLS includes builder,replay,validators,exporters,diff tools./RUNS holds run outputs;bounded by retention.EL1 Every fo...
- **automation** (14) `SIG_0413d99cb52eb7eb` — - verify file is non‑zero, - execute only in a controlled directory, - emit a deterministic extraction report. ## NT.2 SEC execution contract (no surprises) ### NT.2.1 Required CLI behavior (normative) SEC runner MUST support: - `--out <dir>`: extraction target - `--verify-only`: verify payload integrity without writing files - `--list`: list embedded payload members (names+sizes) - `--overwrite-policy {never|safe...
- **graph** (14) `SIG_09bf8b0b1c750aab` — ## NE.1 Run Event Log (append-only JSONL) - RUNS/<run_id>/events.jsonl - Each event is canonicalized JSON with: - event_id (monotonic), timestamp, component, action, subject_ids, inputs_hashes, outputs_hashes, status, error, duration_ms, seed ## NE.2 Crash-safe job queue - SQLite-backed job queue with idempotent workers - Worker contract: must be restartable; partial outputs go to temp; commit only on PASS. ## NE....
- **llm_stack** (14) `SIG_0e36d0d408ed52d9` — Policy:- Any “Space” yields: (a) repo link(s), (b) technique notes, (c) local reimplementation plan, (d) LICENSE check. No code is imported into CURRENT until MRLG approves. P272) MODEL REGISTRY + LICENSE GOVERNOR (MRLG) — “PROMOTE ONLY WHEN LOCKED”Upgrade:- Registry must record: repo_id, revision, license tag, size, intended lane, allowed distribution class, and “terms acceptance required?” flag.- Blocker: any mo...

## Next autonomous step (operator command)
From the bundle root:

```powershell
python .\TOOLS\litos_governor_autonomous.py --bundle-root .
```

To resume a specific run (if interrupted):

```powershell
python .\TOOLS\litos_governor_autonomous.py --bundle-root . --run-id RUN_20260119_041049_UTC_094c5afd --resume
```
