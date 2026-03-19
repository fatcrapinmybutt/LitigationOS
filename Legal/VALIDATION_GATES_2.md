# Validation Gates (Fail-Closed)

Gates are enforced by `mbp gates` and written to `docs/GATE_REPORT.json`.

## Gates

1. **CATALOGUE_PRESENT**
   - `stores/catalogue/catalogue.sqlite` exists.

2. **AUTHORITY_PRESENT**
   - `stores/authority/authority.sqlite` exists (not strictly required to build a graph, but required to *resolve* citations).

3. **CITATIONS_RESOLVABLE**
   - Every harvested citation (MCR/MCL/MRE) must be present in the authority index.
   - If FAIL: you either (a) have citations from outside the loaded authority corpus, or (b) need to ingest the missing authority PDF(s).

4. **GRAPH_CSV_PRESENT**
   - `stores/graph/nodes.csv` and `stores/graph/edges.csv` exist.

5. **GRAPH_EDGE_REFERENCES_VALID**
   - Every edge references node IDs that exist in `nodes.csv`.

## Output

- `docs/GATE_REPORT.json`:
  - `status`: PASS/FAIL
  - `gates[]`: per-gate details and diagnostics
