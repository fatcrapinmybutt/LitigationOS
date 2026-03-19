# EXPLODE_CMD v4 — EXASCALE + HYPERVISOR + BIG-DATA Command Plane
Version: v2026.01.24-cmdv4  
Status: Canonical candidate; backward-compatible with CMDv2/CMDv3 syntax.

CMDv4 focuses on **data hyperscaling** (big-data/exascale patterns) and a **hypervisor execution model**.

---

## 0) Definitions (contract-level)
- **Exascale (practical)**: stays correct when inputs exceed RAM and outputs cannot be packed into one ZIP.
- **Hypervisor (LitigationOS)**: control-plane process that plans shards, leases work, monitors, retries, assembles append-only run stacks, and enforces fail-closed gates.

---

## 1) Canonical syntax (unchanged)
```
VERB:SUBJECT[@TAG[@TAG...]]?K=V&K=V
```

### 1.1 New v4 tags (mode switches)
- `@HYPERVISOR` — lease queue + worker fan-out + retries + heartbeats
- `@BIGDATA` — out-of-core defaults: manifest sharding + catalog DB + zip sharding
- `@EXASCALE` — forces multi-pack outputs and size caps
- `@OUT_OF_CORE` — streaming artifacts, no RAM-heavy steps
- `@SHARDMAP` — emits shard plan artifacts
- `@CATALOG` — emits catalog database (SQLite default)
- `@STREAM` — write-only streaming outputs; never backload into memory

Compatible with `@GOVERN @LINT @FAIL_CLOSED @OBSERVE @DELTA @CACHE @DRYRUN @PUBLISH`.

---

## 2) New v4 keys (BIG DATA)
### 2.1 Sharding controls
- `SHARD_BY=bytes|files|pathprefix|type|date|case|lane`
- `SHARD_TARGET_MB=<int>` (default 512)
- `SHARD_MAX_FILES=<int>` (default 20000)
- `SHARD_PREFIX_DEPTH=<int>` (for pathprefix)
- `SHARD_SEED=<token>` (deterministic shard assignment)

### 2.2 Work queue / hypervisor controls
- `QUEUE=sqlite|jsonl` (default sqlite)
- `LEASE_SECS=<int>` (default 900)
- `HEARTBEAT_SECS=<int>` (default 30)
- `RETRY_MAX=<int>` (default 3)
- `RETRY_BACKOFF=linear|exp`
- `WORKERS=<int|auto>` (local)
- `WORKER_MODE=local|ssh|k8s` (default local; ssh/k8s are pluggable targets)

### 2.3 Big-data catalog outputs
- `CATALOG=sqlite|duckdb|parquet` (default sqlite)
- `CATALOG_KEYS=path|mtime|bytes|crc32|type|lane|case|source` (default: all)
- `CATALOG_PARTITION=lane+case+type` (default)

### 2.4 ZIP / packaging at scale
- `PACK_POLICY=single|multi|sharded`
- `ZIP_MAX_MB=<int>` (default 2048)
- `ZIP_NAMING=runid|runid+shard` (default runid+shard)

### 2.5 Integrity receipts (fast, big-data friendly)
- `INTEGRITY=crc32|none` (default crc32)
- `RECEIPT=IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime)` (canonical form)

---

## 3) Hypervisor execution model (v4)
`FLOW=PLAN>RUN>VERIFY>PACK` where `RUN` expands to:
- `RUN=HYPERVISOR>WORKERS>ASSEMBLE`

Artifacts:
- `SHARD_PLAN.json`
- `QUEUE.sqlite`
- `MANIFEST_SHARD_<n>.jsonl`
- `MANIFEST_INDEX.json`
- `VERIFY_REPORT.json`

---

## 4) Data hyperscaling rules (fail-closed)
If `@BIGDATA` or `@EXASCALE` or `PACK_POLICY=sharded`:
- Manifest MUST be sharded (JSONL shards + index)
- Catalog MUST exist (SQLite default)
- ZIP MUST honor size cap (ZIP_MAX_MB)
- No monolithic manifests larger than `MANIFEST_MAX_MB` (default 256)

---

## 5) v4 “proven exascale” template
```
EXPLODE:GRAPH@GOVERN@LINT@FAIL_CLOSED@OBSERVE@HYPERVISOR@BIGDATA@EXASCALE@OUT_OF_CORE@SHARDMAP@CATALOG?IN=F:/LITIGATION_OS_GRANDMASTER+gdrive:/EDS-USB&SCOPE=corpora&FLOW=PLAN>RUN>VERIFY>PACK&OUT=ZIP(MD+CSV+JSON+CYPHER)+NEO4J(CSV+CONSTRAINTS)+HTML(ERG+SIGMA)&OUT_ROOT=F:/LitigationOS/RunPacks/EXPLODE_CMDv4&ITER=auto&WORKERS=auto&QUEUE=sqlite&LEASE_SECS=900&HEARTBEAT_SECS=30&RETRY_MAX=3&RETRY_BACKOFF=exp&SHARD_BY=bytes&SHARD_TARGET_MB=512&SHARD_MAX_FILES=20000&PACK_POLICY=sharded&ZIP_MAX_MB=2048&INTEGRITY=crc32&GATES=ZIP_SELFTEST+MANIFEST_VERIFY&STRICT=true&FAIL=closed
```

Alias:
- “Explode with information” expands to the template in the active profile.

---

## 6) Included reference implementation
`explode_cmdv4_hypervisor.py` implements a **real working** big-data scaler for:
inventory -> shard plan -> sqlite lease queue -> local workers -> shard manifests (JSONL) -> sharded zips -> gates.

It is designed as a hypervisor front-end that you plug into the full Harvest/Ingest/Extract/OCR pipeline later.
