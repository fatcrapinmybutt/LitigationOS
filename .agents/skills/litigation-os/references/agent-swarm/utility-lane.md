# Utility, Packaging & Product Lanes — 24 Agents

## Packaging Lane (4)

### AGENT:MANIFESTER
- **Role**: Manifests, run ledgers, file maps, checksums
- **Outputs**: JSON manifest with complete provenance

### AGENT:PACKAGER
- **Role**: Create derived-output bundles; blocks on FAIL in FILE_READY mode
- **Outputs**: Filing-ready bundle (zip) with README + manifest

### AGENT:VIEWER_BUILDER
- **Role**: HTML viewers (graph, index, exhibits)
- **Outputs**: Interactive HTML files for case visualization

### AGENT:EXPORTER
- **Role**: Exports to PDF/DOCX/CSV/JSON/CYPHER
- **Outputs**: Export files in requested format

## Product Lane (7)

### AGENT:PRODUCT_ARCHITECT
- **Role**: Requirements + modules + milestones

### AGENT:UX_FLOW_TRANSLATOR
- **Role**: Turn journey maps into screens/routes/states

### AGENT:API_DESIGNER
- **Role**: Endpoints, auth, RBAC, audit logs

### AGENT:MOBILE_BUILDER
- **Role**: React Native, offline-first

### AGENT:WEB_BUILDER
- **Role**: Next.js web app, admin console

### AGENT:SECURITY_ENGINEER
- **Role**: Auth, encryption, least privilege, audit trails

### AGENT:OPS_ENGINEER
- **Role**: CI/CD, backups, monitoring, logging

## Utility Swarm (13)

### AGENT:REPO_ORGANIZER
- Deterministic folder structure; dedupe; safe renames

### AGENT:SEARCH_INDEXER
- Ripgrep + semantic index (FTS5 + TF-IDF)

### AGENT:NEO4J_IMPORTER
- Nodes/edges CSV + Cypher scripts

### AGENT:QDRANT_MANAGER
- Vector store lifecycle

### AGENT:TEST_ENGINE
- Unit/integration tests for pipelines

### AGENT:PERF_TUNER
- Batch sizes, caching, streaming IO

### AGENT:ERROR_RECOVERY
- Self-heal; retries; degrade modes

### AGENT:FOIA_ENGINE
- FOIA request drafting + tracking + intake

### AGENT:DISCOVERY_ENGINE
- Interrogatories, RFPs, RFAs + objection templates

### AGENT:SANCTIONS_ENGINE
- Fees/costs/sanctions logic mapping

### AGENT:APPELLATE_RECORD_ENGINE
- Record designation + transcript order tracking

### AGENT:COMPLIANCE_ENGINE
- Privacy, retention, access logs

### AGENT:MARKETING_ENGINE
- Copy, pages, SEO, case studies (non-legal)
