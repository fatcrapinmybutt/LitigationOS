# Michigan Litigation Filing Packages for a LitigationOS Build (Clerk Stacks)
Generated: 2026-02-28 (America/Detroit)

This bundle converts the provided report into **LitigationOS-ready "Clerk Stacks"**:
ordered filing bundles with machine-readable manifests, templates, and deterministic
MiFILE/MCR validation rules.

## What's inside
- `report/MI_ClerkStacks_Report_v2026-02-28.md`
  - Corrected procedural backbone (MCR 2.119 timing/limits, MCR 2.003 disqualification grounds, MiFILE attachment-index rules, etc.)
  - Ranked package planes + prerequisite checklists
- `schemas/`
  - `litigationos.mi_manifest.schema.json` — JSON Schema for package manifests
  - `litigationos.mi_motion_min.schema.json` — a minimal motion schema (for CI checks)
- `manifests/examples/`
  - Example manifest for FOC 65 (Parenting Time)
- `lint/`
  - `mifile_lint_rules.yaml` — deterministic rules extracted from Michigan Courts e-filing standards
  - `mcr_timing_rules.yaml` — deterministic timing rules (motion/response defaults + notable overrides)
- `templates/akn/`
  - Akoma Ntoso (LegalDocML) starter templates for top packages (FOC 65, FOC 87, MCR 2.003)
- `tooling/`
  - `build_clerkstack_bundle.py` — offline builder/validator (no network) that materializes a folder layout for a package and runs sanity checks.

## How to use
1. Pick a `packageId` (e.g., `PKG-FOC65-PARENTING-TIME`).
2. Copy an example manifest and fill the `case.*` fields + evidence pointers.
3. Run the builder script to generate a ready-to-populate clerk stack folder.

> Note: This bundle is **not legal advice**. It's compliance engineering and filing-package architecture.

## Sources (primary)
The report cites Michigan primary sources (Michigan Courts + Michigan Legislature). See the `report` for a curated source list.
