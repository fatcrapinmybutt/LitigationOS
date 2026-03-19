# HYPERPIN — CMDCTR DELTA11 ORDER/EVIDENCE/LINEAGE APPEND

ROLE=LitigationOS_CommandCenter_Builder;
MODE=AppendOnly+TruthTag+ProvenanceLinked+MichiganFirst;
TARGET=OrdersSupersessionGraph+ServiceProofLinkage+EvidenceCoverageScoring+InteractiveLineageFilters;

## Rails
- **Orders rail**: normalize order nodes, supersession edges, and service-proof nodes into one graph payload; preserve chain-level controlling order IDs.
- **Evidence rail**: compute weighted coverage from `ExhibitMatrix.required_atoms[]` vs `EvidenceAtoms[]`; emit lane and vehicle rollups.
- **Lineage rail**: join canonical lineage groups to replay provenance links by artifact path tail; emit filterable groups + jump anchors.

## Output family
- `data/order_supersession_service_graph.json`
- `data/service_proofs.json`
- `data/exhibit_matrix.json`
- `data/evidence_atoms.json`
- `data/evidence_coverage.json`
- `data/lineage_provenance_index.json`
- UI patch (orders/evidence/lineage panels interactive)

## Scoring
- `coverage_score = found_weight / required_weight`
- weight source = `EvidenceAtoms.coverage_weight`
- lane rollup and vehicle rollup are arithmetic/weighted projections for drafting readiness compasses.

## Continuation
Append transcript quote-lock pins and service proof exhibits, then re-score vehicle readiness and generate vehicle-specific proof gaps.
