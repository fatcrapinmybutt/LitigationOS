# EVENT-HORIZON DELTA7 Append Pack
## Chained Cycles of Expansion / Improvement / Refinement

### Continuation charter
This append advances the Litigation Command Center scaffold from DELTA6 shell to **DELTA7+ readiness** by adding:
- timeline and orders panel data contracts
- vehicle readiness scoring panel and sample scoreboard
- deterministic cycle IDs + replay event schema
- stronger UI continuity behavior
- next-cycle rails for DELTA8 (supersession graph, filters, computed scoring)

### Chained cycle outputs in this append
1. **Expansion cycle**
   - Added `timeline` and `orders` schemas + sample JSON + live seeded JSON
   - Added `vehicle_readiness` schema + sample scoreboard
2. **Improvement cycle**
   - Upgraded `ui/panels.js` to render timeline, controlling orders, and readiness bands
   - Upgraded `ui/adapters.js` to load new datasets
3. **Refinement cycle**
   - Added `runtime/deterministic_cycle_id.py`
   - Upgraded `runtime/replay_log.py` with event IDs + integrity keys
   - Upgraded `runtime/launch.py` to emit deterministic cycle record

### DELTA8 continuation targets
- Render order supersession graph visually (Mermaid/HTML overlay)
- Add lane filters and truth-tag filters on timeline
- Compute vehicle readiness from evidence coverage and order/service completeness
- Attach authority pinpoint density to readiness and panel badges
