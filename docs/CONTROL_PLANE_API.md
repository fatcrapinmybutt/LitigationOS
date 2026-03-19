# Control Plane API (Event Horizon)

Core:
- POST /configure  {vault_root, sqlite_db}
- GET  /health
- GET  /forms?limit=
- GET  /coverage
- POST /cyclepack

Jobs:
- POST /jobs/enqueue  {job_type, payload}
- GET  /jobs?limit=

Artifacts (safe subtrees only):
- GET /artifacts?prefix=90_REPORTS&limit=200
- GET /artifacts/download?path=90_REPORTS/doctor_report.json

Safe subtrees:
- 90_REPORTS
- 40_FILINGS_OUTPUT
- 10_FORMS
