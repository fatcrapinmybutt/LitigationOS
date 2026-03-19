# DrivePuller Guide

- Mount your cloud drive (e.g., Google Drive via rclone) to a local path.
- Use dashboard "DrivePuller" to ingest that path, or POST:
  `/api/drive/ingest?path=X:\LITIGATION_INTAKE` (or `gdrive:/...` if your environment supports it)

Ingest computes SHA-256 and indexes artifacts into `backend/data/evidence_index.json`.
