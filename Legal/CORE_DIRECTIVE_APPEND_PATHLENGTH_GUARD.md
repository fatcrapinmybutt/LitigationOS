# CORE DIRECTIVE ADDENDUM — PathLengthGuard (Windows unzip safety)

## Rule
All LitigationOS delivery bundles (ZIPs, cyclepacks, packets) MUST enforce **PathLengthGuard** to avoid Windows extraction failures caused by overly long paths.

### PathLengthGuard requirements
1. **Condense folder names** inside bundles using short aliases (example):
   - docs → d
   - diagrams → g
   - manifests → m
   - model → mdl
   - neo4j → n4j
   - schemas → sch
   - templates → tpl
   - tools → tl
   - validation_reports → vr
   - savepoints → sp

2. **Condense filenames** that exceed safe thresholds:
   - If a path would exceed a conservative cap, replace the basename with an ID (E0001.json, N0001.csv, R0001.csv) or a short CRC-based token.

3. **Always emit a mapping file**:
   - `PATH_MAP.csv` (old_path,new_path) must ship at bundle root.
   - This mapping is part of the chain-of-custody and must be treated as evidence of determinism.

4. **No destructive renames**:
   - Never mutate originals; emit condensed bundles as additional versions.

5. **Builder parity**:
   - Include a deterministic builder script that can recreate the condensed bundle from the canonical (long-name) workspace.

## Operational note
Windows can be configured to allow long paths, but LitigationOS must not rely on that setting. PathLengthGuard is mandatory at packaging time.
