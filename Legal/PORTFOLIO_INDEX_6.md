# PORTFOLIO_INDEX (Append-Only)
Pack: `CAPSTONE_PORTFOLIO_STACK_v2026-01-23.3`
Version: `v2026-01-23.3`

## Superpins
- `superpins/SUPERPIN_CORPORA_EXPLODE_v2026-01-23.3.md` — trigger tokens + convergence + append-only portfolio rules.
- `superpins/COMMAND_SURFACE_SUPERPIN_v2026-01-23.3.md` — expanded command DSL + macros + scopes + examples.

## Scripts
- `scripts/00_RUN_PORTFOLIO.cmd` — double-click orchestrator (build manifest → zip → selftest).
- `scripts/01_selftest_zip.py` — zip integrity + manifest verification.
- `scripts/02_build_manifest.py` — deterministic manifest writer (sha256 + size).
- `scripts/04_make_zip.py` — creates the stack zip.
- `scripts/03_worldfirst_rebuild.py` — local rebuild (world-first) and CRC32 receipts.

## Previous (bundled for continuity)
- `previous/CAPSTONE_BRIDGE_PACK_v2026-01-23.1.zip`
- `previous/mbp_worldfirst_builder.py`
