# MCP Integration Blueprint (DRAFT) — NUCLEUS APEX V3.4

## External Tool: HFSPACE:Agents-MCP-Hackathon/KGB-mcp
- URL: https://hf.co/spaces/Agents-MCP-Hackathon/KGB-mcp
- Updated: 2025-06-05
- Tags: gradio, mcp-server-track, agent-demo-track, knowledge-graph, entity-extraction, nlp, visualization, semantic-analysis, clustering, embeddings, mcp-server, region:us

## Purpose (LitigationOS)
Enable **tool-callable graph augmentation** lanes (entity extraction, clustering, visualization) without merging raw results into evidence.
All outputs from MCP tools are treated as **system artifacts**, not exhibits/evidence.

## Subterms / Atoms
- MCPServer
- MCPClient
- ToolInvocation
- ToolResultArtifact
- ToolResultPointer
- SafetyGate (no network by default)
- ProvenanceReceipt (ts, tool_id, args_hash, output_hash, run_id)

## Field schema (YAML)
```yaml
ExternalTool:
  id: string  # HFSPACE:org/name
  name: string
  url: string
  sdk: string
  author: string
  updated: date
  likes: int
  tags: [string]
  source: string
  enabled: bool
MCPInvocation:
  inv_id: string
  tool_id: string
  ts: datetime
  args_json: string
  output_ref: string
  status: enum[OK,FAIL,SKIPPED]
  integrity_key: string
```

## Neo4j edges
- (SchemaRoot)-[:EXTENDS_WITH]->(ExternalTool)
- (Run)-[:INVOKED]->(MCPInvocation)-[:USED_TOOL]->(ExternalTool)
- (MCPInvocation)-[:EMITTED]->(ToolResultArtifact)

## Validator rules
- tool_id must match `HFSPACE:<owner>/<space>`
- url must be https://hf.co/spaces/<owner>/<space>
- No EvidenceAtom may be created directly from ToolResultArtifact without explicit promotion step (separate gate)

## Required record items
- external_tools_registry.json
- tool invocation receipts (append-only JSONL)
- output artifacts stored under run folder with IntegrityKey
