# Neo4j Setup — LitigationOS Knowledge Graph

## 1. Install Neo4j

### Option A: Neo4j Desktop (recommended for local use)

1. Download from <https://neo4j.com/download/>
2. Install and launch Neo4j Desktop
3. Create a new project → Add a Local DBMS
4. Set a password (you'll need it for the load script)
5. Start the database

### Option B: Docker

```bash
docker run -d \
  --name litigation-neo4j \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/changeme \
  -v neo4j_data:/data \
  neo4j:5
```

The instance will be available at:
- **Bolt:** `bolt://localhost:7687`
- **Browser:** `http://localhost:7474`

Default credentials: `neo4j` / `changeme`

---

## 2. Install Python Driver

```bash
pip install neo4j
```

---

## 3. Run the Load Script

### Full import

```bash
python load_neo4j.py --uri bolt://localhost:7687 --user neo4j --password <your-password>
```

### Dry run (validate only — no data written)

```bash
python load_neo4j.py --uri bolt://localhost:7687 --user neo4j --password <your-password> --dry-run
```

### All options

| Flag         | Default                  | Description                            |
|------------- |--------------------------|----------------------------------------|
| `--uri`      | `bolt://localhost:7687`  | Neo4j Bolt connection URI              |
| `--user`     | `neo4j`                  | Neo4j username                         |
| `--password` | *(required)*             | Neo4j password                         |
| `--database` | `neo4j`                  | Target database name                   |
| `--dry-run`  | off                      | Validate CSVs and connectivity only    |

---

## 4. Verify the Data

Open Neo4j Browser at **http://localhost:7474** and run these queries:

### Node counts by label

```cypher
MATCH (n)
RETURN labels(n)[0] AS label, count(*) AS count
ORDER BY count DESC;
```

### View all Actions ranked by OMEGA score

```cypher
MATCH (a:Action)
RETURN a.name, a.omega_score, a.tier, a.forum
ORDER BY a.omega_score DESC;
```

### Actions filed in each Forum

```cypher
MATCH (a:Action)-[:FILED_IN]->(f:Forum)
RETURN f.name AS forum, collect(a.name) AS actions, count(a) AS count
ORDER BY count DESC;
```

### Full graph overview (small datasets)

```cypher
MATCH (n)-[r]->(m)
RETURN n, r, m
LIMIT 200;
```

### Claims linked to an Action

```cypher
MATCH (a:Action {id: 'jtc-formal-complaint'})-[:HAS_CLAIM]->(c:Claim)
RETURN a.name, c.id, c.text
LIMIT 20;
```

### Evidence chain: Action → Claim → Violation → Evidence

```cypher
MATCH path = (a:Action)-[:HAS_CLAIM]->(c:Claim)
              -[:INVOLVES_VIOLATION]->(v:Violation)
              -[:SUPPORTED_BY]->(e:Evidence)
WHERE a.id = 'jtc-formal-complaint'
RETURN path LIMIT 25;
```

### Person relationships

```cypher
MATCH (p:Person)-[r]->(target)
RETURN p.name, type(r), labels(target)[0], target.name
ORDER BY p.name;
```

---

## 5. Explore the Graph in Neo4j Browser

1. Open **http://localhost:7474** in your browser
2. Log in with your credentials
3. Click the **database icon** (top-left) to see node labels and relationship types
4. Click any label (e.g., `Action`) to see all nodes of that type
5. Double-click a node to expand its relationships
6. Use the **style panel** (paintbrush icon) to color nodes by label
7. Try the full-graph query above to see the entire knowledge graph

### Useful keyboard shortcuts

| Shortcut       | Action                    |
|--------------- |---------------------------|
| `Ctrl+Enter`   | Run query                 |
| `Ctrl+/`       | Toggle comment            |
| `:clear`        | Clear results frame       |
| `:help`         | Show help                 |

---

## 6. File Reference

| File                          | Description                              |
|-------------------------------|------------------------------------------|
| `schema.cypher`               | Constraints, indexes, and seed data      |
| `neo4j_action_nodes.csv`      | Action nodes (OMEGA-scored)              |
| `neo4j_claim_nodes.csv`       | Claim nodes                              |
| `neo4j_violation_nodes.csv`   | Judicial violation nodes                 |
| `neo4j_evidence_nodes.csv`    | Evidence quote nodes                     |
| `neo4j_action_forum_edges.csv`| Action → Forum (FILED_IN) edges          |
| `neo4j_export.py`             | Export script (SQLite → CSV)             |
| `load_neo4j.py`               | **This import script** (CSV → Neo4j)     |
