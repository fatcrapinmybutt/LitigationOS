# LITIGATIONOS_MI_APPELLATE_DOCFORGE_MEEK1234_V19_PROMOTE_TUNE_DEADLINES_DOCXPDF

## What this adds (V19)
This pack extends the DocForge rail with four requested lanes:

1. **Exact official-text promotion lane**
   - Bulk imports authority graft rows (`official_text_grafts.jsonl`)
   - Promotes `authority_triples` from `PARTIAL` to `RESOLVED_VERIFIED` only when:
     - `verified=true`
     - `official_text_exact` exists
     - `pinpoint` exists

2. **Transcript ↔ order finding score tuning**
   - Ingest transcript page/line rows and hostile-order findings
   - Grid-search tuning (`tune-linker`) prioritizing **recall**
   - Generates accepted links + score detail JSON

3. **Vehicle-specific deadline registry**
   - Split anchors: `entered/signed/served/recorded`
   - Template registry for **COA / MSC / JTC** + tolling notes
   - Deadline locks emitted with `LOCKED / PENDING_VERIFY / MISSING_ANCHOR`

4. **CourtPack DOCX/PDF emit lane**
   - Compiles:
     - CASE_STATE
     - AuthorityTriples
     - Deadlines
     - Transcript SoF pins
     - ContradictionMap
     - Validation/RedTeam
   - Emits `CourtPack_Summary.docx` and `CourtPack_Summary.pdf`

## Core script
- `core/docforge_v19.py` (single orchestrator script)

## Quick start
```powershell
# from this folder
python .\core\docforge_v19.py --workspace .\runtime autopilot
```

## Production use path
Use your real exports:
- `authority_requests.jsonl`
- `official_text_grafts.jsonl` (exact text + exact pinpoint + verified flag)
- `transcript_rows.csv`
- `order_findings.csv`
- `deadline_events.csv`

Then run:
```powershell
python .\core\docforge_v19.py --workspace .\runtime initdb
python .\core\docforge_v19.py --workspace .\runtime seed-deadline-registry
python .\core\docforge_v19.py --workspace .\runtime ingest-authority-requests --jsonl .\your\authority_requests.jsonl
python .\core\docforge_v19.py --workspace .\runtime ingest-official-text --jsonl .\your\official_text_grafts.jsonl
python .\core\docforge_v19.py --workspace .\runtime ingest-transcripts --csv .\your\transcript_rows.csv
python .\core\docforge_v19.py --workspace .\runtime ingest-order-findings --csv .\your\order_findings.csv
python .\core\docforge_v19.py --workspace .\runtime tune-linker --gold-csv .\your\transcript_link_gold.csv
python .\core\docforge_v19.py --workspace .\runtime link-order-findings
python .\core\docforge_v19.py --workspace .\runtime ingest-deadline-events --csv .\your\deadline_events.csv
python .\core\docforge_v19.py --workspace .\runtime lock-deadlines
python .\core\docforge_v19.py --workspace .\runtime consolidate-contradictions
python .\core\docforge_v19.py --workspace .\runtime courtpack --lane MEEK2 --case-anchor 24-01507-DC
```

## Important rails
- **No SHA-256 by default** (fast deterministic identity key used instead)
- **Original files are not modified**
- **Deadline registry is seeded as template** (verify and promote subrules before filing)
- **Official text promotion is strict** (no fake verification)
