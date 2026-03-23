
@echo off
REM One-click Neo4j load script (Windows)

echo Stopping Neo4j...
neo4j stop

echo Starting Neo4j...
neo4j start

echo Loading graph schema...
neo4j cypher-shell -f 22_NEO4J_IMPORT_SCRIPT.cypher

echo Load complete.
pause
