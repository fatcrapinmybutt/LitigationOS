# Evolution Pipeline — 5 Tools

## litigation_evolve_files
Trigger evolution on .md/.txt files (section detection + cross-refs + graph linking).
- `directory` (str, required): Directory path to evolve
- `file_types` (list[str], optional): Extensions. Default: [".md", ".txt"]
- `force` (bool, optional): Re-evolve processed files. Default: false
- Returns: Files processed, sections created, cross-refs extracted, graph links

## litigation_evolve_pdfs
Evolve already-ingested PDF pages through cross-reference pipeline.
- `document_id` (int, optional): Specific document. Default: all un-evolved
- Returns: Pages evolved, cross-refs extracted, graph links

## litigation_search_evolved
FTS5 search across ALL evolved content (MD + TXT + PDF sections).
- `query` (str, required): FTS5 search query
- `source_type` (str, optional): Filter (md, txt, pdf)
- `limit` (int, optional): Max results. Default: 20
- Returns: Matching sections with source file, heading hierarchy, cross-refs

## litigation_cross_refs
Query the cross-reference network.
- `query` (str, required): Reference to search (e.g., "MCR 3.706", "AGENT:TIMELINE_BUILDER")
- `ref_type` (str, optional): Filter (rule, agent, vehicle, risk, authority)
- `limit` (int, optional): Max results. Default: 20
- Returns: Sections referencing the query, with context and graph linkage

## litigation_evolution_stats
Show evolution coverage across all file types.
- Returns: Per-type counts (MD/TXT/PDF), sections, cross-refs, graph link %, coverage gaps
