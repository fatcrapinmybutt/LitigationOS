# Basic Refinement Report — 2025-09-29T00:18:16

## Steps performed
- Added **918** stub nodes (type=STUB) to heal missing refs.
- Normalized relation directions/types (e.g., `owned_by` → `owns` reversed).
- Coerced weights to numeric; ≤0 → 1.0.
- Deduplicated edges by (source,target,type) with weights summed; directed = any True.

## Metrics (post-refine)
- Nodes: **62,945**
- Edges: **27,061**
- Edges referencing missing nodes: **0**
- Self-loops: **0**