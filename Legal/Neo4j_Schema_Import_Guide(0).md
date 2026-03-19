# Neo4j Schema-Aware Import

- Dashboard: Graph → Neo4j Schema Pack → Generate
- Or: POST /api/graph/import/generate_schema

Outputs under the run dir:
- `neo4j_schema_pack_YYYYMMDD_HHMMSS/` with `import.cypher`, `fraud_queries.cypher`, and CSVs
- Use `:source import.cypher` in Neo4j Browser, then `:source fraud_queries.cypher` for analytics.
