# Next steps
1) Copy NEO4J_IMPORT_ENRICHED/*.csv into Neo4j's import directory.
2) Run `load_all_with_apoc_splitlabels.cypher` (recommended) or `load_all_no_apoc.cypher`.
3) In Neo4j Browser, verify counts (see REPORTS/enrichment_stats.json).
4) Optional: add viewer-side styling keyed on n.group and/or n.labels_csv / labels.

Authority URL bases validated against official Michigan sources:
- Michigan Court Rules landing page: https://www.courts.michigan.gov/.../michigan-court-rules/ citeturn0search0
- Michigan Court Rules responsive HTML5 ZIP index: https://www.courts.michigan.gov/.../michigan-court-rules-responsive-html5.zip/index.html citeturn0search4
- Michigan Legislature MCL objectName pattern (example 722.23): https://www.legislature.mi.gov/Laws/MCL?objectName=MCL-722-23 citeturn0search2
- SCAO form PDF example (MC 416): https://www.courts.michigan.gov/.../mc416.pdf citeturn0search3