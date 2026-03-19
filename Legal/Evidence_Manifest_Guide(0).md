# Evidence Manifest & Bates Numbers

- Endpoint: `POST /api/evidence/manifest?prefix=AJB&start=1`
- Reads `backend/data/evidence_index.json` and emits:
  - `backend/data/manifests/manifest_<prefix>_<YYYYMMDD>.json`
  - `backend/data/manifests/manifest_<prefix>_<YYYYMMDD>.csv`
- Bates format: `<prefix>-<YYYYMMDD>-<NNNNNN>`
