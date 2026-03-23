
param(
  [string]$User="neo4j",
  [string]$Password="neo4j"
)
# Pull from Drive and build CSVs
python .\scripts\sync_and_build.py
# Load CSVs into Neo4j
cypher-shell -u $User -p $Password -f .\cypher\Neo4j_loader.cypher
