# Audit Notes (v2)

## What was fixed vs the v1 orchestrator
- Split pipeline into explicit CLI subcommands for repeatability and debugging.
- Adds doctype guessing and AKN template output.
- Adds requirements compilation into a structured JSON checklist.
- Adds stack scaffolding for output bundles per form and per case_id.
- Adds coverage report generation.

## Error handling
- ZIP extraction is bounded by max depth.
- OCR is optional and only runs if enabled and tool exists on PATH.
- PDF parsing uses pypdf if installed; otherwise PDFs remain un-extracted and will require OCR tooling locally.
- DB writes are append-friendly (INSERT OR IGNORE), with stack manifests updated per case.

## Known limits (intended Copilot upgrades)
- "Word-for-word" fidelity depends on PDF text layer; OCR is required for image-only PDFs.
- Requirement compilation is heuristic; next upgrade is a structured "InstructionSectionParser" per jurisdiction/family.
- Jurisdiction detection is currently MI-biased via code families; extend via rulebanks and catalog adapters.
