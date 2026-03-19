# LitigationOS Master Bundle (MI Higher-Court ZIP Harvester)

Version: v2026-01-20.1

This bundle is designed to be *durable against chat sandbox link expiry*:
- The **Builder** is self-contained and can reconstruct the full code pack locally.
- The **Code Pack ZIP** is included directly.
- Batch wrappers are included for Windows PowerShell and Bash.

## 1) Rebuild the pack locally (recommended)

From this folder:

```bash
python LitigationOS_Addendum_Builder_v2026-01-20.1.py --out ./LitigationOS_Addendum
```

This creates `./LitigationOS_Addendum/` containing the complete code pack.

## 2) Run a batch harvest over one or more roots

### Windows PowerShell

```powershell
cd .\LitigationOS_Addendum
.\run_batch.ps1 -ScanRoot 'F:/' -ScanRoot 'H:/' -OutputRoot 'F:/LegalResults/LitigationOS' -Mode discovery -CyclePack -FollowNested -NestedMaxDepth 2
```

### Bash (Linux/WSL/Termux)

```bash
cd ./LitigationOS_Addendum
chmod +x ./run_batch.sh
OUTPUT_ROOT="./_BATCH_OUT" FOLLOW_NESTED=1 NESTED_MAX_DEPTH=2 ./run_batch.sh "F:/" "H:/"
```

## 3) Run a single input (ZIP or file)

```bash
python -m scripts.litigationos_batch_processor --input "/path/to/file_or_zip" --output-root "./_BATCH_OUT" --mode discovery
```

## 4) Key options

- `--follow-nested --nested-max-depth N`: chase nested ZIPs discovered inside extracted bundles
- `--resume`: skip inputs already successfully processed in the same batch directory
- `--cyclepack` / `--cyclepack-slim`: emit portable evidence/log pack
- `--no-pdf --no-docx`: disable heavy extraction for quick scans

## 5) Smoke artifacts

`./smoke/` contains small proof runs:
- `CYCLEPACK_SMOKE_NESTED.zip` demonstrates nested ZIP depth gating.
- `BATCH_SMOKE_RESUME/` demonstrates `--resume` stability for staged inputs.

## 6) Integrity

- `MANIFEST.json` lists every file in this bundle.
- `CRC32_SHA256_RECEIPTS.*` provides quick integrity checks.
