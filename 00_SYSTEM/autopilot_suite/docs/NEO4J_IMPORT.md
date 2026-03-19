\
# Neo4j Import Notes

## Neo4j 5 (neo4j-admin database import full)

Example (Windows PowerShell):

```powershell
# adjust these paths
$DBNAME = "litigationos"
$NEO4J = "C:\Program Files\Neo4j Desktop\Neo4j Desktop.exe" # (GUI uses its own DB dir)

# For neo4j-admin import you need the DB 'import' directory path for the target DBMS.
# In Neo4j Desktop: Manage → Open Folder → DBMS → import
$IMPORT = "C:\path\to\dbms\import"

Copy-Item ".\outputs\...\neo4j_nodes_core.csv" $IMPORT
Copy-Item ".\outputs\...\neo4j_edges_core.csv" $IMPORT

neo4j-admin database import full --overwrite-destination=true `
  --nodes=neo4j_nodes_core.csv `
  --relationships=neo4j_edges_core.csv `
  $DBNAME
```

Then run `neo4j_constraints.cypher` in Neo4j Browser.
