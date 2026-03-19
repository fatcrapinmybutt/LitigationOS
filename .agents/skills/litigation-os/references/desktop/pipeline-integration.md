# OMEGA Pipeline — Desktop Integration Blueprint

## Phase 16 Output

Phase 16 exports the OMEGA pipeline as a repeatable blueprint into the Desktop app.

## Blueprint Format (desktop_blueprint.json)

```json
{
  "blueprint_id": "OMEGA_DEEP_TRAVERSAL_v1",
  "version": "2026.02.21",
  "phases": [
    {
      "phase": 0,
      "name": "safety",
      "script": "tooling/safety.py",
      "inputs": ["target_directory"],
      "outputs": ["backups/SNAPSHOT_{ts}/"],
      "required": true,
      "skip_allowed": false
    }
  ],
  "config": {
    "skip_patterns": ["*.pyc", "*.class", "*.dll", "*.exe"],
    "scoring_formula": "(citations*3.0 + keywords*1.5 + dollars + dates) * length_factor",
    "brain_count": 50,
    "brain_max_kb": 500,
    "atom_types": ["fact", "citation", "event", "person", "contradiction"],
    "legal_actions": 56,
    "adversaries": 11
  }
}
```

## New Backend Service

`LitigationOS-Desktop/backend/src/services/omegaPipelineService.js`:

1. `launchPipeline(targetDir, options)` — Start as Bull background job
2. `getPipelineStatus(cycleId)` — Real-time progress via Socket.io
3. `rollbackPipeline(snapshotId)` — One-click rollback
4. `viewResults(cycleId)` — Load CyclePack for display
5. `rerunPhase(cycleId, phaseNum)` — Re-execute single phase

## New Frontend Page

`LitigationOS-Desktop/frontend/src/pages/OmegaPipeline.jsx`:

- **Directory picker** — Select target scan directory
- **Phase status grid** — 16 phases with green/yellow/red indicators
- **Real-time log viewer** — Streaming console per phase
- **Results dashboard** — File counts, dedup stats, atoms, legal actions, readiness
- **Rollback button** — One-click revert with confirmation
- **Re-run button** — Re-execute from any phase
- **Blueprint editor** — Modify skip lists, scoring, adversaries
- **Legal Action Matrix** — Interactive 56-action × 11-adversary grid
- **Filing Status cards** — Per-filing readiness with drill-down

## Adapting for New Cases

1. Edit `tooling/config.py`: person names, case numbers, adversaries
2. Upload new config via Blueprint Editor in Desktop UI
3. Run pipeline on new evidence directory
4. Results auto-populate the dashboard
