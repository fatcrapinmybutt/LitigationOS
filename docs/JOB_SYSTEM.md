# Event Horizon Job System

This adds a minimal durable job queue using SQLite.

## Schema
tooling/job_queue.sql

## CLI
Enqueue:
  python tooling/job_client.py --db <sqlite_db> enqueue ingest
  python tooling/job_client.py --db <sqlite_db> enqueue extract
  python tooling/job_client.py --db <sqlite_db> enqueue detect
  python tooling/job_client.py --db <sqlite_db> enqueue instructions
  python tooling/job_client.py --db <sqlite_db> enqueue specs
  python tooling/job_client.py --db <sqlite_db> enqueue akn
  python tooling/job_client.py --db <sqlite_db> enqueue stacks --payload '{"case_id":"24-01507-DC"}'
  python tooling/job_client.py --db <sqlite_db> enqueue coverage --payload '{"out":"Vault/90_REPORTS/coverage_jobs.json"}'

Worker (run continuously):
  python tooling/job_worker.py --db <sqlite_db> --vault <vault_root> --config config/formos_config.json --schema tooling/schema_v3.sql

## API
- POST /jobs/enqueue
- GET  /jobs

The worker runs separately. The API enqueues and reports status.
