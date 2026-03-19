"""Count rows in all brain/graph/authority tables."""
import sys, os
sys.path.insert(0, r"C:\Users\andre\LitigationOS\00_SYSTEM")
from shell_resilience_engine import safe_query

tables = [
    "graph_nodes", "graph_load_log", "auth_authority_edges", "auth_authority_nodes",
    "auth_authority_passages", "authorities_edges", "authorities_index", "authorities_nodes",
    "authority_chains", "authority_shards", "brain_nuclei", "court_rule_graphs", "court_rules",
    "md_cross_refs", "knowledge_gaps", "chatgpt_conversations",
    "auth_rules", "rules_text", "master_citations", "evidence_quotes",
    "documents", "pages", "md_sections", "docket_events", "impeachment_items",
    "contradiction_map", "judicial_violations", "tort_claims", "drive_evidence",
    "atoms", "claims", "vehicles", "adversary_models", "deadlines"
]

print(f"{'TABLE':<40} {'ROWS':>10}")
print("-" * 52)
total = 0
for t in sorted(tables):
    try:
        rows = safe_query(f"SELECT COUNT(*) as cnt FROM [{t}]")
        cnt = rows[0]["cnt"]
        total += cnt
        print(f"  {t:<38} {cnt:>10,}")
    except Exception as e:
        print(f"  {t:<38} {'ERROR':>10}")

print("-" * 52)
print(f"  {'TOTAL':<38} {total:>10,}")
