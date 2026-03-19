# Integration Phases (5-9)

## Phase 5: Brain Feed — 50 LEXOS Nuclei Population

**Script:** `phase5_brain_feed.py` (extends brain_builder.py)

1. Load existing 50 brains from `lexos_bible/brains/brain_*.json`
2. Score new atoms against brain mapping
3. For each HIGH-scoring atom: dedup (SHA1), score, insert
4. Trim each brain to 500KB max
5. Rebuild TF-IDF index per brain

See [scoring.md](../brain-spec/scoring.md) for the 50-brain map.

## Phase 6: Gap Analysis — EGCP v2 Gap Tickets

**Script:** `phase6_gap_analysis.py`

Compares scans corpus against:
- KNOWLEDGE_ALL.jsonl (existing schema nodes)
- authority_shards_all.jsonl (authority text)
- EC_AUTHORITY_MAP.jsonl (citation map)
- neo4j_nodes.csv / neo4j_edges.csv (5,452 nodes / 10,121 edges)
- SYNTHESIS_DATA.json (MCL/MCR counts)
- 50 LEXOS brains

**Gap types:** file-level, citation, person, timeline, contradiction, authority.

See [egcp-v2.md](../brain-spec/egcp-v2.md) for gap ticket format.

## Phase 7: Graph Delta + Synthesis Merge

### 7A: Graph Delta
- New Evidence, Authority, Person nodes
- New CITES, MENTIONS, DOCUMENTS, CONTRADICTS edges
- Deterministic IDs: `sha1(f"{BrainID}|{Type}|{KeyFields}")`
- Output: `neo4j_nodes_delta.csv`, `neo4j_edges_delta.csv`

### 7B: Synthesis Merge
- Merge citation counts → SYNTHESIS_DATA.json
- Update MASTER_EVIDENCE_INDEX.csv, MASTER_VIOLATIONS.csv, MASTER_PERSONS.csv, MASTER_TIMELINE.csv, MASTER_CITATIONS.csv

### 7C: Authority Shard Integration
- New MCL/MCR/MRE text → authority_shards_all.jsonl
- New EC entries → EC_AUTHORITY_MAP.jsonl
- New knowledge → KNOWLEDGE_ALL.jsonl

### 7D: Event-Horizon DELTA Map Regeneration
- Regenerate EVENT_HORIZON_DELTA_INTEGRATION_MAP.md with new counts

## Phase 8: Impeachment + Adversary Refresh

**Script:** `phase8_litigation_refresh.py` (orchestrator for existing scripts)

Reuses:
- `i_impeachment.py` — Transcript impeachment (10 regex patterns, severity scoring)
- `b_authority_chains.py` — Authority chain audit + contradiction scanning
- `a_readiness.py` — Filing readiness scoring (4 dimensions, 0-25 each)
- `k_adversary.py` — War-gaming adversary attacks + preemptive rebuttals

## Phase 9: MCP Server Integration

**Script:** `phase9_mcp_ingest.py`

1. Start litigation_context_mcp server (if not running)
2. Call `litigation_bulk_ingest` with all HIGH-priority PDF paths
3. Verify via `litigation_get_stats`
4. Test via `litigation_search` for key terms
