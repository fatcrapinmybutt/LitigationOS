# GOD-Level — 8 Tools

## litigation_god_status
Grand Orchestrated Deployment status across all drives and subsystems.
- Returns: System registry, CSV data stats, vector index stats, convergence state, drive inventory

## litigation_ingest_csv
Ingest master CSV data files into unified database.
- `file_path` (str, required): Path to CSV file
- `source_label` (str, optional): Label for data source
- Returns: Rows ingested, columns detected, duplicate handling stats

## litigation_query_master
Query master CSV data with SQL-like filters.
- `query` (str, required): Search term
- `columns` (list[str], optional): Columns to search
- `limit` (int, optional): Max results. Default: 50
- Returns: Matching rows with all columns

## litigation_vector_search
TF-IDF vector similarity search across entire corpus (137K vocabulary).
- `query` (str, required): Natural language query
- `top_k` (int, optional): Results count. Default: 10
- Returns: Most similar documents/sections ranked by cosine similarity

## litigation_deadlines
Temporal deadline reasoner using Michigan Court Rules.
- `event_type` (str, required): Triggering event (e.g., "order_entered", "motion_filed")
- `event_date` (str, required): Date (ISO 8601)
- `rule` (str, optional): Specific MCR rule
- Returns: Computed deadlines, applicable rules, service requirements, warnings

## litigation_red_team
Red team validator for structural checks on filings and evidence.
- `target` (str, required): What to validate
- `mode` (str, optional): "structural" (default), "adversarial", "compliance"
- Returns: Issues (critical/high/medium/low), pass/fail, remediation steps

## litigation_evidence_chain
Prove an evidence chain by linking exhibits to claims.
- `claim` (str, required): Factual claim to prove
- `evidence_ids` (list[str], optional): Specific evidence to check
- Returns: Chain strength, supporting evidence, gaps, MRE admissibility hooks

## litigation_swarm_dispatch
Dispatch a task to the multi-agent swarm.
- `task` (str, required): Task description
- `agents` (list[str], optional): Specific agents to invoke
- `priority` (str, optional): "critical", "high", "normal", "low"
- Returns: Agent assignments, estimated deliverables, execution plan
