# Unified Auto-Harvest Runner (Free Stack) — Gemini / Copilot / Any Agent CLI

This file is sequenced so an agent can follow it top-to-bottom.

---

## 0) External dependencies are allowed (and recommended)

A **bootstrap runner** with near-zero deps is useful because it:
- runs anywhere with only Python,
- fails less often than “pip-first” stacks,
- can serve as the “first mile” installer/validator.

A **state-of-the-art runner** should still use dependencies—just safely:
- optional feature gates (extras): `base` vs `ocr` vs `rag` vs `graph`
- version locks (reproducible builds): pinned requirements/lockfiles
- offline wheelhouse (no internet required once prepared)
- trust boundaries (agent allowed to read/execute only inside a trusted folder)

---

## 1) The “100% free” architecture (robust + modern)

- **Orchestrator agent**: Gemini CLI / Copilot / IDE agent runs the workflow.
- **Local model layer (free software)**: Ollama / llama.cpp / vLLM (pick one).
- **Local retrieval layer (free)**: Qdrant for vector search/RAG.
- **OCR + extraction (free)**: Tesseract for OCR as-needed.

---

## 2) Gemini uses other models (the right pattern)

Make Gemini (or Copilot) the **planner + tool router** and route heavy tasks to local models:
1) Agent decides a task (extract/summarize/classify).
2) Agent calls your local OpenAI-compatible endpoint (vLLM/llama.cpp/Ollama/proxy).
3) Results get written into the run artifacts + indexed for retrieval.

This is how you get “state-of-the-art” while staying free.

---

## 3) Directory selection: “point to 1 directory” without scanning junk

Best practice:
- build a **HARVEST_ROOT hub** containing only junctions to high-signal corpora,
- harvest the hub, not your whole user profile.

---

## 4) ONE singular PowerShell command (robust)

Paste this **as-is** into a PowerShell-backed shell box:

$ErrorActionPreference='Stop'; $home=$env:USERPROFILE; $bases=@("$home\Downloads","$home\Desktop","$home\Desktop\LITIGATION_OS\CAPSTONE","$home\LITIGATION_OS","$home\LitigationOS_Build_Offload","$home\LitigationOS_Consolidated","G:\Capstone"); $runnerFile=$null; foreach($b in $bases){ if(Test-Path $b){ $hit=Get-ChildItem -Path $b -Recurse -File -Filter 'harvest_runner.py' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1; if($hit){ $runnerFile=$hit.FullName; break } } }; if(-not $runnerFile){ throw 'harvest_runner.py not found. Put it in Downloads/Desktop or extract the AutoHarvest zip.' }; $root=Split-Path $runnerFile -Parent; while(-not (Test-Path (Join-Path $root '.gemini'))){ $parent=Split-Path $root -Parent; if(-not $parent -or $parent -eq $root){ break }; $root=$parent }; New-Item -ItemType Directory -Force (Join-Path $root '.gemini\scripts') | Out-Null; Copy-Item $runnerFile (Join-Path $root '.gemini\scripts\harvest_runner.py') -Force; Set-Location $root; $hub=Join-Path $root '.gemini\work\HARVEST_ROOT'; if(Test-Path $hub){ Remove-Item $hub -Recurse -Force }; New-Item -ItemType Directory -Force $hub | Out-Null; function _mkJ($dst,$src){ if(Test-Path $dst){ return }; cmd /c "mklink /J `"$dst`" `"$src`"" | Out-Null }; $targets=@(@{n='LITIGATION_OS';p="$home\LITIGATION_OS"},@{n='LitigationOS_Consolidated';p="$home\LitigationOS_Consolidated"},@{n='LitigationOS_Build_Offload';p="$home\LitigationOS_Build_Offload"},@{n='CAPSTONE';p="$home\Desktop\LITIGATION_OS\CAPSTONE"},@{n='G_Capstone';p='G:\Capstone'}); foreach($t in $targets){ if(Test-Path $t.p){ _mkJ (Join-Path $hub $t.n) $t.p } }; python (Join-Path $root '.gemini\scripts\harvest_runner.py') --root $hub --out (Join-Path $root '.gemini\out') --include-archives --max-mb 50 --hash sha256 --write-text; $out=Join-Path $root '.gemini\out'; $run=Get-ChildItem -Path $out -Directory -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1; if($run -and (Test-Path (Join-Path $run.FullName 'NEXT_PROMPT.md'))){ Get-Content (Join-Path $run.FullName 'NEXT_PROMPT.md') -Raw } else { Write-Output "Done. See $out" }

---

## 5) High-signal next upgrades to add (still free)

- Incremental / resume mode (only changed files)
- Quarantine + timeouts (corruption-proof extraction)
- Optional OCR pipeline (Tesseract) with “OCR only when needed”
- Qdrant indexing + hybrid retrieval (BM25 + vectors)
- Local model router policy (fast vs deep vs fallback)
- Provenance: sha256 + append-only run ledger + deterministic manifests
