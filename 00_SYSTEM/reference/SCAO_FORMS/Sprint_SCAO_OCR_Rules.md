# Sprint: SCAO Fill, OCR/PDF-A, Venue Rules

## SCAO Fill
- Place blank SCAO PDFs in `backend/templates/scao_forms/` (MC01.pdf, MC12.pdf, FOC65.pdf, FOC88.pdf).
- Edit field maps in `backend/app/engine/scao_maps/*.json` if your field names differ.
- Endpoint: `POST /api/scao/fill?case_id=...&form_id=MC01&action=...` → creates FDF + attempts pdftk fill+flatten.
- Dashboard card: **SCAO Fill**.

## OCR + PDF/A
- If `ocrmypdf` is installed, `/api/pdf/normalize` will OCR and convert to PDF/A. Otherwise it copies through and sets a warning.
- Dashboard card: **PDF Normalize (OCR + PDF/A)**.
- MiFILE packager can be updated to call normalize before zipping (optional toggle).

## Venue Rules + ODB Dependencies
- Rules live under `backend/rules/mi/<county>.yaml`. A sample `muskegon.yaml` is included; replace with official values.
- Endpoint: `POST /api/odb/run_compliant?county=muskegon` (body = JSON array of completed steps) → returns venue-checked plan and alt if needed.
- Dashboard card: **ODB (Venue-Compliant)**.
