# Quality Metrics & Scoring

## Quality Score (0-100)

| Metric | Weight | Description | Target |
|--------|--------|-------------|--------|
| Document coverage | 20% | % of known PDFs ingested | 10+ documents |
| FTS sync | 15% | pages count == FTS rowcount | 100% sync |
| Graph coverage | 15% | % of knowledge graph sources loaded | 7/8 sources |
| Cross-ref density | 15% | Cross-refs per section | ≥ 1.5 |
| Graph link rate | 15% | % of cross-refs linked to graph nodes | ≥ 60% |
| Risk completeness | 10% | All 21 risk event types present | 21/21 |
| Evolution coverage | 10% | % of MD/TXT files evolved | 50+ files |

## Score Thresholds

| Score | Status | Action |
|-------|--------|--------|
| 95-100 | **CONVERGED** | Switch to EMERGENCE mode |
| 80-94 | **GOOD** | Continue convergence cycles |
| 60-79 | **NEEDS WORK** | Focus on BLOCKERS |
| < 60 | **CRITICAL** | Major ingestion/repair needed |

## Common Error Codes

| Code | Cause | Recovery |
|------|-------|----------|
| ERR_DB_CONNECT | DB missing/locked | Check path, close connections |
| ERR_DB_LOCKED | Concurrent writes | Wait + retry (auto-handled) |
| ERR_DB_CORRUPT | Schema damage | PRAGMA integrity_check, rebuild |
| ERR_FTS_DESYNC | FTS out of sync | Trigger rebuild via self_test |
| ERR_FTS_SYNTAX | Bad query | Auto-sanitized by sanitize_fts_query() |
| ERR_PDF_CORRUPT | Damaged PDF | Skip, log, continue |
| ERR_PDF_TOO_LARGE | >500MB | Increase LITIGATION_MAX_PDF_BYTES |
| ERR_PDF_TIMEOUT | Extraction stalled | Increase LITIGATION_PDF_TIMEOUT |
| ERR_GRAPH_LOAD | JSON error | Check validity, re-download |
| ERR_DISK_FULL | <100MB free | Free space |
| ERR_CIRCUIT_OPEN | 5 consecutive fails | Wait 60s or reset |

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| LITIGATION_DB_DIR | ~/litigation_context.db | Database location |
| LITIGATION_GRAPH_DIR | ~/Scans/ | Knowledge graph files |
| LITIGATION_PDF_TIMEOUT | 120 | Max seconds per PDF |
| LITIGATION_MAX_PDF_BYTES | 524288000 | Max PDF size (500MB) |
