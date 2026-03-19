# Next upgrades (queued)

1) Neo4j “full preload + live query” mode in the same launcher:
   - Detect local Neo4j (docker compose) and route /api/search + /api/subgraph to Cypher.

2) Multi-resolution exploration:
   - /api/overview: group-aggregated meta-graph to navigate the entire universe before drilling down.

3) Authority attach:
   - /api/authority + UI pane to display MI rule/statute/benchbook snapshots and link them to exhibits/case lanes.

4) Performance:
   - Replace O(N^2) repulsion with Barnes–Hut (quadtree) so 4k–8k node subgraphs stay smooth.
