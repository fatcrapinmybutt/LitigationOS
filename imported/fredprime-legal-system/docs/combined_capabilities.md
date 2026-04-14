# Combined rclone + atlas builder + rclone bridge capabilities

1. **Policy-gated remote intake**: safely pull approved evidence packs from cloud remotes under allowlist control.
2. **Deterministic run logging**: produce JSONL run ledgers for both transfer and atlas build steps.
3. **Automated pack staging**: mirror remote ZIP packs into local inboxes for batch processing.
4. **Zip-slip–safe extraction**: unpack incoming archives into controlled staging directories.
5. **Cross-pack graph synthesis**: merge multi-pack nodes/edges into a single atlas dataset.
6. **Card/panel asset bundling**: attach image cards and panels into a unified visualization.
7. **Offline-ready delivery**: bundle vendor JS and assets for air-gapped review.
8. **Heuristic linking**: crosswire cards to nodes via token overlap for fast navigation.
9. **Inventory audit trail**: emit manifests of all produced artifacts without digests.
10. **Remote-to-local mirroring**: keep evidence mirrors current using sync workflows.
11. **Remote-to-remote relays**: move packs between remotes before local ingest.
12. **Searchable UI atlas**: generate a static, searchable map for large case packs.
13. **Programmatic orchestration**: drive transfers and atlas builds via CLI/API pipelines.
14. **Policy enforcement evidence**: produce blocked-run reports when network policy denies access.
15. **Operational reproducibility**: deterministic IDs/timestamps for consistent rebuilds.
16. **Selective export**: export atlas JSON/PNG artifacts for downstream sharing.
17. **Cross-platform workflows**: run end-to-end on Windows/macOS/Linux with the same CLI surface.
18. **Massive pack scaling**: handle large volumes via batch ingest + layout tooling.
19. **Data provenance tagging**: retain source pack paths on nodes/edges for traceability.
20. **Air-gap fallback**: operate in offline mode with local mirrors and bundled dependencies.
