CyclePack_Authority_Dockets_v6

Delta vs v5
- Added rules store: state/mi/rules_store/rules_authority_shards.jsonl
- Added tagged docket outputs:
  - reports/ppo_roa_entries_tagged.csv + .jsonl
  - reports/docket_events_all_tagged.csv
  - reports/timeline_bitemp_events.jsonl (Graph ingest friendly)
- Added rules shards summary outputs:
  - reports/rules_shards_summary.json
  - reports/rules_shards_top_citations.csv
- Added scripts:
  - scripts/rules_lookup.py
  - scripts/docket_tag_summary.py

Zip status
- DOCKETSPPO.zip valid: False
- Zip error: BadZipFile: File is not a zip file
