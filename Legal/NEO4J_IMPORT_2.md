# Neo4j Import (Bolt) + Validation

This pack supports Bolt-based import using the official Neo4j python driver.

## Constraints

```bash
python main.py --out ./MBP_OUT --tag DEMO neo4j-constraints --password YOURPASS
```

## Import

```bash
python main.py --out ./MBP_OUT --tag DEMO neo4j-import --password YOURPASS --batch 500
```

## Validate

```bash
python main.py --out ./MBP_OUT --tag DEMO neo4j-validate --password YOURPASS
```

## Notes

- Bolt import is slower than `neo4j-admin database import`, but works without special Neo4j config.
- For large corpora, use a dedicated import pipeline (future upgrade):
  - Pre-split nodes per label
  - Use periodic commit & UNWIND
  - Use `neo4j-admin` bulk import with import-dir CSVs
