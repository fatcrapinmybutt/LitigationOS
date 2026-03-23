# PowerShell Quickstart for Neo4j Import
# 1) Place all files in your Neo4j import directory (e.g., C:\Neo4j\import)
# 2) Run this script with your credentials

param([string]$User="neo4j", [string]$Password="neo4j")

cypher-shell -u $User -p $Password -f Neo4j_loader.cypher
cypher-shell -u $User -p $Password -f validate.cypher
