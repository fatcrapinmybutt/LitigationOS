# Knowledge Graph — 4 Tools

## litigation_lookup_rule
Look up Michigan Court Rules by citation or keyword.
- `query` (str, required): Rule citation or keyword (e.g., "MCR 3.206", "parenting time")
- `exact` (bool, optional): Exact match only. Default: false
- Returns: Rule text, section, subsection, source, related forms

**Examples:**
```
litigation_lookup_rule(query="MCR 3.706")       # contempt
litigation_lookup_rule(query="parenting time modification")
litigation_lookup_rule(query="MCR 7.205")       # COA leave
```

## litigation_query_graph
Search across all 8 loaded knowledge graphs (36,129+ nodes).
- `query` (str, required): Search term for node labels/IDs
- `node_type` (str, optional): Filter by type (authority, violation, evidence, form, rule)
- `source` (str, optional): Filter by source graph file
- `limit` (int, optional): Max results. Default: 20
- Returns: Matching nodes with type, source, relationships, metadata

**Examples:**
```
litigation_query_graph(query="custody", node_type="authority")
litigation_query_graph(query="PPO", source="MasterGraph.json")
```

## litigation_lookup_authority
Case law, statutes, and forms with pin cites.
- `query` (str, required): Authority citation or keyword
- `authority_type` (str, optional): Filter (case_law, statute, form, rule)
- `limit` (int, optional): Max results. Default: 10
- Returns: Authority text, citation, pin cite, source, related authorities

## litigation_assess_risk
Assess litigation risk events with severity and cure steps.
- `risk_class` (str, optional): Filter (procedural, substantive, ethical)
- `severity` (str, optional): Filter (critical, high, medium, low)
- `limit` (int, optional): Max results. Default: 21
- Returns: Risk event type, description, severity, cure steps, deadlines, rules

**Example:**
```
litigation_assess_risk(risk_class="procedural", severity="critical")
```
