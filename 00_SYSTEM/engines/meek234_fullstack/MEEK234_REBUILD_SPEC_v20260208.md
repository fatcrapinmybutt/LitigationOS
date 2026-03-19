# MEEK2 + MEEK3 + MEEK4 — Full Stack Rebuild (Baseline) (v2026-02-08)

This pack rebuilds the **core runtime** for LitigationOS across:
- **MEEK2**: custody / parenting time / FOC / support
- **MEEK3**: PPO / show-cause / contempt
- **MEEK4**: judicial conduct / disqualification / JTC packaging

## What you get (runnable today)

### 1) Harvest pipeline
- Scans an intake folder for **.txt/.md/.json/.jsonl/.csv** (plus best-effort **.docx/.pdf**)
- Extracts:
  - **EvidenceAtom** (paragraph-based provenance slices)
  - **EventAtom** (Order/Service/Hearing/Filing/Communication; best-effort date parsing)
  - **DeadlineClock** (configurable rules; includes a few MI-rule-based defaults)
  - **RiskEvent** (clock urgency/expiry + missing OperatingOrderPin + undated events)
  - **VehicleCandidate** (baseline candidates per track)

### 2) Graph outputs for Neo4j + Bloom
Each run writes:
- `nodes.csv` (id,label,properties…)
- `edges.csv` (id,src,rel,dst,properties…)
- `timeline.csv`
- `risk_report.json`
- `run.json` (dashboard payload)
- `dash.html` (offline dashboard)

### 3) OperatingOrderPin gate (enforced)
A VehicleCandidate is considered incomplete unless an **OperatingOrderPin** is provided.
Missing pins become **RiskEvents**.

## Authority anchors used for default clocks (for reference)
The script’s default clocks reference:
- MCR 2.119(F)(1) (reconsideration within 21 days after entry of order)
- MCR 2.003(D)(1)(a) (disqualification motion within 14 days of discovery of grounds, trial courts)

You can extend/replace clock rules inside the script (`DEFAULT_CLOCK_RULES`) or by forking it into a config-driven version.

## Recommended local layout (Windows)
- Intake mirror (rclone):  
  `C:\Users\andre\Desktop\THE_LITIGATION_OPERATING_SYSTEM\INTAKE_MIRROR\Litigation_Intake\`
- Run outputs:  
  `C:\Users\andre\Desktop\THE_LITIGATION_OPERATING_SYSTEM\runs\`

## Commands

### Harvest
```powershell
py .\MEEK234_FULLSTACK_REBUILD_v20260208.py harvest ^
  --in "C:\Users\andre\Desktop\THE_LITIGATION_OPERATING_SYSTEM\INTAKE_MIRROR\Litigation_Intake" ^
  --out-root "C:\Users\andre\Desktop\THE_LITIGATION_OPERATING_SYSTEM\runs" ^
  --operating-order-pin "order:YOUR_OPERATIVE_ORDER_ID_OR_NOTE"
```

### Serve the dashboard
```powershell
py .\MEEK234_FULLSTACK_REBUILD_v20260208.py serve ^
  --run "C:\Users\andre\Desktop\THE_LITIGATION_OPERATING_SYSTEM\runs\<RUN_ID>"
```

Then open:
- `http://127.0.0.1:8899/dash.html`

### Neo4j upsert (optional)
Install driver:
```powershell
pip install neo4j
```

Set env vars (PowerShell):
```powershell
$env:NEO4J_URI="bolt://localhost:7687"
$env:NEO4J_USER="neo4j"
$env:NEO4J_PASS="YOUR_PASSWORD"
```

Upsert:
```powershell
py .\MEEK234_FULLSTACK_REBUILD_v20260208.py neo4j-upsert --run "C:\...\runs\<RUN_ID>"
```

## Next upgrades (high leverage)
1. **Config-driven rules**: move EVENT_RULES + CLOCK_RULES into JSON so you can edit without touching code.
2. **ROA importer**: parse ROA PDFs/CSVs into typed entries; generate `Order` and `ServiceEvent` objects with pinpoints.
3. **OperatingOrderPin resolver**: automatically select “operative” order (latest entered + not superseded/stayed).
4. **PPO rule enhancements**: parse PPO conditions; build prohibited/permitted communication graph.
5. **JTC milestone engine**: represent Subchapter 9.200 milestones as typed timeline stages (request → prelim investigation → etc.).

