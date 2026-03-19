# DOWNLOAD_AUDIT — MBP Portal Permanent Bridge Installer v6 (NEXUS+DELTA)

Generated: 2026-01-11T06:37:03.681816Z

## What’s new vs v5
- **Nexus Delta Harvest**: on-change, per-role post-sync hook generates:
  - `run_dir/nexus/delta/shards.jsonl`
  - `run_dir/nexus/contexts/contextpack_min.json`
  - `run_dir/nexus/neo4j_delta_pack/` (CSV + `cypher_incremental.cypher`)
- Fixed/normalized MindEye2 artifact gatherer plugin (`plugins/mindseye2/gather_mindeye2_artifacts.py`) so the addon directory is fully runnable.

## Integrity
- This bundle is self-described by `manifest.json` + `manifest.csv` in the root.
- For a full audit: `python3 -c "import json; print(len(json.load(open('manifest.json'))))"`.

## Run quick test (Termux)
- Run `RUN_ME_TERMUX.sh` to install portal + daily reconnect job, then `mbp-portal tick --once`.
- After a role sync with changes, check `~/MBP_PORTAL_RUNS/*/nexus/` for delta outputs.

See `docs/NEXUS_DELTA_HARVEST.md`.
