# Phase Specifications — Pipeline Commander Reference

## Phase 4: EXTRACT

```yaml
phase_4_extract:
  name: EXTRACT
  number: 4
  prerequisite: Phase 3 (CLASSIFY) checkpoint valid
  purpose: >
    Pull structured data from unstructured documents. Convert free-text
    documents into machine-processable data structures.
  actions:
    - For each classified document:
        - Identify document type from Phase 3 classification
        - Apply type-specific extraction template:
            motion:       parties, relief sought, arguments, authorities
            exhibit:      description, date, source, authenticity markers
            correspondence: sender, recipient, date, subject, key content
            court_order:  judge, date, ruling, conditions, deadlines
            deposition:   deponent, date, key testimony, page references
            inspection:   inspector, date, property, violations, photos
            lease:        parties, term, rent, conditions, clauses
            financial:    amounts, dates, accounts, transactions
        - Extract named entities (persons, dates, locations, amounts)
        - Extract legal citations (MCL, MCR, MRE, case law)
        - Extract timeline events (date + event + source)
        - Tag extracted data with source document ID and page/paragraph
    - Build cross-document entity index
    - Build master timeline from extracted events
  exit_conditions:
    - All non-quarantined documents processed
    - Entity index complete with source linkage
    - Timeline built with no unresolved date conflicts
    - All extracted citations in parseable format
  lane_specific:
    A: "Extract all 12 best-interest factor references from custody documents"
    B: "Extract all lease terms, violation dates, repair request dates"
    C: "Extract all cross-lane entity references"
  checkpoint: phase_4_extract_complete.json
  estimated_duration: 30-120 minutes (scales with document count)
  error_handling:
    - Unparseable document → quarantine with "extraction_failure" tag
    - Ambiguous entity → flag for human disambiguation
    - Conflicting dates → log both with source, flag for Phase 7 resolution
```

## Phase 5: BRAINS

```yaml
phase_5_brains:
  name: BRAINS
  number: 5
  prerequisite: Phase 4 (EXTRACT) checkpoint valid
  purpose: >
    Build and update the brain-spec knowledge graphs from extracted data.
    This phase transforms raw extracted data into the structured knowledge
    that all downstream phases depend on.
  actions:
    - Load existing brain-spec (if resuming) or initialize new
    - For each lane, build/update knowledge graph:
        nodes:
          - persons (parties, witnesses, judges, attorneys)
          - documents (filings, exhibits, correspondence)
          - events (hearings, incidents, deadlines)
          - legal_concepts (statutes, rules, case holdings)
          - locations (addresses, courts, properties)
        edges:
          - authored_by, filed_in, references, contradicts
          - supports, undermines, occurred_at, testified_about
          - cites_authority, applies_rule, interprets_statute
    - Cross-link entities across lanes (Lane C synthesis)
    - Compute entity importance scores (connection count × relevance)
    - Build contradiction graph (entities with conflicting attributes)
    - Generate brain-spec delta report (changes from previous version)
  exit_conditions:
    - All extracted entities have graph nodes
    - All relationships have edges with source attribution
    - Cross-lane links established for shared entities
    - No orphan nodes (every node has at least one edge)
    - Brain-spec version incremented
  lane_specific:
    A: "Build custody-specific subgraph with 12 factor nodes"
    B: "Build housing-specific subgraph with property condition nodes"
    C: "Build convergence subgraph linking A and B shared entities"
  checkpoint: phase_5_brains_complete.json
  estimated_duration: 20-60 minutes
  error_handling:
    - Entity merge conflict → create "ambiguous" node, flag for review
    - Graph cycle detected → log and verify (some cycles are valid)
    - Memory limit on large graphs → process in subgraph batches
```

## Phase 6: GAPS

```yaml
phase_6_gaps:
  name: GAPS
  number: 6
  prerequisite: Phase 5 (BRAINS) checkpoint valid
  purpose: >
    Identify missing evidence, authority, strategy gaps by analyzing
    the brain-spec knowledge graph against case requirements.
  actions:
    - Define requirements per lane:
        Lane A requirements:
          - All 12 best-interest factors addressed with evidence
          - Change of custodial environment evidence
          - Parenting time documentation
          - PPO compliance/violation records
          - Witness list complete with contact info
        Lane B requirements:
          - All housing code violations documented
          - Lease terms extracted and analyzed
          - Damage calculations with supporting evidence
          - Repair request history documented
          - Communication log with landlord
        Lane C requirements:
          - Cross-lane entity consistency verified
          - Shared timeline aligned
          - No contradictory positions across lanes
    - For each requirement, check brain-spec graph:
        - Evidence exists? → mark as COVERED
        - Evidence partial? → mark as GAP with specifics
        - Evidence missing? → mark as CRITICAL GAP
    - For each legal argument planned:
        - Authority chain complete? → mark as SUPPORTED
        - Authority chain incomplete? → mark as AUTHORITY GAP
    - Generate gap report sorted by severity and deadline impact
  exit_conditions:
    - All requirements checked against brain-spec
    - All gaps documented with specifics
    - Gap severity and priority assigned
    - Gap report generated
  checkpoint: phase_6_gaps_complete.json
  estimated_duration: 15-45 minutes
  error_handling:
    - Requirement ambiguity → flag for clarification, don't skip
    - Brain-spec incomplete → re-check Phase 5, may need re-run
```

## Phase 7: MERGE

```yaml
phase_7_merge:
  name: MERGE
  number: 7
  prerequisite: Phase 6 (GAPS) checkpoint valid
  purpose: >
    Consolidate cross-lane data, resolve conflicts between lanes,
    and create the unified case view that downstream phases require.
    This is the critical convergence point.
  actions:
    - Load brain-spec subgraphs from all active lanes
    - Merge entity nodes:
        - Exact match → merge attributes, keep both source links
        - Near match → flag for human review
        - No match → lane-specific (no merge needed)
    - Resolve conflicts:
        - Date conflicts → verify against primary sources
        - Attribute conflicts → flag, do not auto-resolve
        - Position conflicts → escalate to strategy review
    - Build unified timeline across all lanes
    - Verify cross-lane consistency:
        - Same person described consistently?
        - Same events dated consistently?
        - Legal positions compatible?
    - Generate merge report with all decisions documented
  exit_conditions:
    - All shared entities merged or flagged
    - No unresolved critical conflicts
    - Unified timeline complete
    - Merge decisions documented with rationale
  lane_specific:
    A_B_merge: "Watson entity must be consistent across custody and housing"
    B_C_merge: "Property conditions must support both housing and custody args"
    A_C_merge: "Custody strategy must incorporate housing evidence correctly"
  checkpoint: phase_7_merge_complete.json
  estimated_duration: 30-90 minutes
  error_handling:
    - Merge conflict → HALT on critical, log on minor
    - Data loss during merge → rollback, verify sources, retry
    - This phase has the highest failure rate — budget extra time
```

## Phase 8: IMPEACH

```yaml
phase_8_impeach:
  name: IMPEACH
  number: 8
  prerequisite: Phase 7 (MERGE) checkpoint valid
  parallel_with: [Phase 9, Phase 10]
  purpose: >
    Build impeachment packages for adverse witnesses using contradictions,
    prior statements, and credibility challenges identified in the
    merged knowledge graph.
  actions:
    - Identify all adverse witnesses from merged graph
    - For each adverse witness:
        - Collect all statements (deposition, affidavit, filing)
        - Cross-reference statements for contradictions
        - Check prior court records for credibility issues
        - Build impeachment timeline (statement evolution)
        - Prepare cross-examination question sets
    - Lane-specific impeachment targets:
        Lane A: Watson — custody claims, parenting representations
        Lane B: Shady Oaks management — maintenance claims, repair records
        Lane C: Any witness testifying in both lanes
    - Generate impeachment packages per witness
  exit_conditions:
    - All adverse witnesses have impeachment packages
    - Contradictions documented with source citations
    - Cross-examination outlines prepared
  checkpoint: phase_8_impeach_complete.json
  estimated_duration: 30-90 minutes
```

## Phase 9: MCP

```yaml
phase_9_mcp:
  name: MCP
  number: 9
  prerequisite: Phase 7 (MERGE) checkpoint valid
  parallel_with: [Phase 8, Phase 10]
  purpose: >
    Synchronize all case data with MCP tools, update the litigation
    context server, and ensure all external integrations are current.
  actions:
    - Update litigation context MCP server with merged data
    - Sync timeline events to calendar system
    - Update document index in MCP
    - Verify all MCP tool endpoints are responsive
    - Run integration tests against MCP tools
  exit_conditions:
    - MCP tools synced with current case state
    - All integration tests pass
    - No stale data in MCP context
  checkpoint: phase_9_mcp_complete.json
  estimated_duration: 10-30 minutes
```

## Phase 10: JUDICIAL

```yaml
phase_10_judicial:
  name: JUDICIAL
  number: 10
  prerequisite: Phase 7 (MERGE) checkpoint valid
  parallel_with: [Phase 8, Phase 9]
  purpose: >
    Analyze judicial patterns for Judge McNeill (Lane A) and
    Judge Hoopes (Lane B) to optimize strategy and brief writing.
  actions:
    - Analyze Judge McNeill (Lane A):
        - Custody ruling patterns (which factors weighted heavily)
        - PPO modification history
        - Hearing procedural preferences
        - Response to specific argument styles
    - Analyze Judge Hoopes (Lane B):
        - CZ case disposition patterns
        - Summary disposition grant/deny rates
        - Damage calculation tendencies
        - Discovery management approach
    - Generate judicial profile reports
    - Recommend strategy adjustments based on patterns
  exit_conditions:
    - Judicial profiles generated for both judges
    - Strategy recommendations documented
    - No recommendations contradict case theory
  checkpoint: phase_10_judicial_complete.json
  estimated_duration: 20-60 minutes
```

## Phases 11-16: Summary Specifications

```yaml
phase_11_legal_actions:
  purpose: Draft motions, briefs, complaints from processed data
  key_output: Draft filings for each lane
  prerequisite: Phases 8, 9, 10 complete

phase_12_rules:
  purpose: Validate all outputs against MCR/MCL/MRE
  key_output: Compliance report per filing
  prerequisite: Phase 11 complete

phase_13_refine:
  purpose: Polish language, verify persuasiveness and tone
  key_output: Refined filing drafts
  prerequisite: Phase 12 complete

phase_14_finalize:
  purpose: Final quality check, authority validation, formatting
  key_output: Filing-ready documents
  prerequisite: Phase 13 complete

phase_15_validate:
  purpose: Full convergence cycle on complete work product
  key_output: Convergence quality score and report
  prerequisite: Phase 14 complete

phase_16_desktop:
  purpose: Package for LitigationOS Desktop delivery
  key_output: Desktop-ready package with all deliverables
  prerequisite: Phase 15 complete with score >= 85
```
