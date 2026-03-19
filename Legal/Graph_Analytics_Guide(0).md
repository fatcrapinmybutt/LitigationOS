# Graph Analytics (CSV-based)

- Endpoint: `POST /api/graph/analyze?run_id=<optional>`
- Detects:
  - Common registered agents (Person linking multiple LLCs)
  - Round-robin ownership loops (LLC↔LLC OWNS)
  - Rent extraction chains (Person→Property←LLC→MANAGES→LLC)

Use `POST /api/odb/run_with_graph` to apply analysis as pressure multipliers to ODB's ranking.
