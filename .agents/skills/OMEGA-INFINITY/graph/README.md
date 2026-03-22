# Neo4j Bloom Graph Package — LitigationOS OMEGA-INFINITY

> **Version:** 4.0  
> **Graph:** 13 node types · 15 edge types · 6 case lanes  
> **Case:** Pigors v. Watson (14th Circuit Court, Family Division)

---

## Quick Start

```
1. Export CSVs    →  python scripts/omega_neo4j_export.py
2. Copy to Neo4j  →  copy CSVs to <neo4j>/import/
3. Import nodes   →  run import_nodes.cypher
4. Import edges   →  run import_edges.cypher
5. Open Bloom     →  load bloom_perspective.json
6. Search         →  use bloom_search_phrases.json
```

---

## Prerequisites

### Option A: Neo4j Desktop (Recommended)

1. Download from [neo4j.com/download](https://neo4j.com/download/)
2. Install and create a new project
3. Create a local DBMS (Neo4j 5.x recommended)
4. Install the **APOC** plugin (required for batched imports and verification queries)
5. Start the database

### Option B: Neo4j Aura Free (Cloud)

1. Create account at [neo4j.com/cloud/aura-free](https://neo4j.com/cloud/aura-free/)
2. Create a free instance
3. Note: CSV import requires uploading files via the Aura console or using `LOAD CSV` with HTTPS URLs
4. APOC availability may be limited on free tier

### Option C: Docker

```bash
docker run -d \
  --name neo4j-litigationos \
  -p 7474:7474 -p 7687:7687 \
  -v /path/to/csv:/var/lib/neo4j/import \
  -e NEO4J_AUTH=neo4j/litigationos \
  -e NEO4J_PLUGINS='["apoc"]' \
  neo4j:5-community
```

---

## Step 1: Export CSVs from LitigationOS

Run the export script from the LitigationOS root:

```powershell
cd C:\Users\andre\LitigationOS
python .agents\skills\OMEGA-INFINITY\scripts\omega_neo4j_export.py
```

This generates CSV files in the `graph/` directory (or a configured output path). Expected files:

**Node CSVs (13):**
| File | Node Type | Source |
|------|-----------|--------|
| `cases.csv` | Case | Static mapping |
| `lanes.csv` | Lane | Static mapping |
| `parties.csv` | Party | Verified identity |
| `judges.csv` | Judge | Verified identity |
| `attorneys.csv` | Attorney | Verified identity |
| `claims.csv` | Claim | `litigation_context.db` → `claims` |
| `evidence.csv` | Evidence | `litigation_context.db` → `evidence_quotes` |
| `filings.csv` | Filing | `litigation_context.db` → `filing_readiness` |
| `forms.csv` | Form | `court_forms.db` → `court_forms_complete` |
| `rules.csv` | Rule | `litigation_context.db` → `authority_master_index` |
| `violations.csv` | Violation | `litigation_context.db` → `judicial_violations` |
| `witnesses.csv` | Witness | Derived from evidence/docket |
| `events.csv` | Event | `litigation_context.db` → `case_timeline` + `docket_events` |

**Edge CSVs (15):**
| File | Relationship | Direction |
|------|-------------|-----------|
| `rel_belongs_to_lane.csv` | BELONGS_TO_LANE | Case → Lane |
| `rel_party_in_case.csv` | PARTY_IN_CASE | Party → Case |
| `rel_judge_presides.csv` | JUDGE_PRESIDES | Judge → Case |
| `rel_attorney_represents.csv` | ATTORNEY_REPRESENTS | Attorney → Party |
| `rel_supports_claim.csv` | SUPPORTS_CLAIM | Evidence → Claim |
| `rel_filed_in_case.csv` | FILED_IN_CASE | Filing → Case |
| `rel_requires_form.csv` | REQUIRES_FORM | Filing → Form |
| `rel_cites_authority.csv` | CITES_AUTHORITY | Filing → Rule |
| `rel_violates_rule.csv` | VIOLATES_RULE | Violation → Rule |
| `rel_committed_by.csv` | COMMITTED_BY | Violation → Judge |
| `rel_evidence_in_lane.csv` | EVIDENCE_IN_LANE | Evidence → Lane |
| `rel_occurred_on.csv` | OCCURRED_ON | Event → Lane |
| `rel_testified_about.csv` | TESTIFIED_ABOUT | Witness → Evidence |
| `rel_co_cited_with.csv` | CO_CITED_WITH | Rule → Rule |
| `rel_filing_uses_evidence.csv` | FILING_USES_EVIDENCE | Filing → Evidence |

---

## Step 2: Copy CSVs to Neo4j Import Directory

### Neo4j Desktop

Find the import directory:
1. Open Neo4j Desktop → select your DBMS
2. Click **...** → **Open folder** → **Import**
3. Copy all CSV files there

Or via command line:

```powershell
# Find Neo4j import directory (typical locations)
$neo4jImport = "$env:USERPROFILE\.Neo4jDesktop\relate-data\dbmss\*\import"
$importDir = (Get-ChildItem $neo4jImport -Directory | Select-Object -First 1).FullName

# Copy all CSVs
Copy-Item .\graph\*.csv $importDir -Force
Write-Host "Copied CSVs to $importDir"
```

### Docker

```bash
# If using Docker volume mount, CSVs are already available
docker cp ./graph/. neo4j-litigationos:/var/lib/neo4j/import/
```

---

## Step 3: Import Nodes

Open Neo4j Browser at `http://localhost:7474` and run the node import script:

```
:source import_nodes.cypher
```

Or paste the contents of `import_nodes.cypher` into the Neo4j Browser query editor.

**Using cypher-shell:**

```powershell
cat graph\import_nodes.cypher | cypher-shell -u neo4j -p <password> --format plain
```

The script will:
1. Create uniqueness constraints and indexes (13 constraints, 15+ indexes)
2. Import all 13 node types using `LOAD CSV WITH HEADERS`
3. Large tables (Evidence, Events) use batched transactions (`IN TRANSACTIONS OF 5000 ROWS`)
4. Run verification queries to confirm node counts

---

## Step 4: Import Edges

After nodes are imported, run the edge import script:

```
:source import_edges.cypher
```

Or paste the contents of `import_edges.cypher` into the query editor.

The script will:
1. Create all 15 relationship types
2. Set edge properties including weights and metadata
3. Use `MERGE` to prevent duplicate edges
4. Run verification queries to confirm edge counts and connectivity

---

## Step 5: Load Bloom Perspective

### Neo4j Bloom (Desktop)

1. Open Neo4j Bloom from Neo4j Desktop
2. Click the **Perspective** dropdown (top-left)
3. Click **Import Perspective**
4. Select `bloom_perspective.json`
5. The perspective includes:
   - 9 category groups with lane-specific colors
   - 13 node styles with conditional coloring
   - 15 edge styles with weight-based thickness
   - Force-directed layout with nucleus center
   - Quick filters for common views

### Manual Configuration (if import fails)

If JSON import is not supported in your Bloom version, configure manually:

1. **Node colors:** Use the color palette in `bloom_perspective.json` → `colorPalette`
2. **Node sizes:** Set size based on degree (connection count)
3. **Edge thickness:** Set based on weight property
4. **Layout:** Use force-directed layout

---

## Step 6: Use Search Phrases

Load `bloom_search_phrases.json` for 30 predefined search queries.

### In Bloom Search Bar

Type any of these natural-language phrases:

| Phrase | What It Shows |
|--------|--------------|
| "Show all evidence in Lane A" | Custody evidence cluster |
| "McNeill violations" | Full judicial accountability chain |
| "Filing readiness above 70%" | Court-ready filings |
| "Authority chain for MCR 2.003" | Disqualification rule network |
| "Complete graph overview" | Nucleus view — all lanes |
| "High-relevance evidence" | Strongest evidence (score > 0.8) |
| "Co-citation network" | Rule clusters |
| "Isolated nodes" | Disconnected evidence needing links |
| "PPO weaponization pattern" | Lane D evidence and violations |
| "Witness testimony network" | Witness → Evidence connections |

### In Neo4j Browser

Copy Cypher queries directly from `bloom_search_phrases.json`:

```cypher
// Example: McNeill violations
MATCH (v:Violation)-[:COMMITTED_BY]->(j:Judge {name: 'Hon. Jenny L. McNeill'})
OPTIONAL MATCH (v)-[:VIOLATES_RULE]->(r:Rule)
RETURN v, j, r;
```

---

## Graph Schema Diagram

```
                    ┌──────────┐
                    │   Lane   │
                    │  (A-F)   │
                    └────▲─────┘
                         │ BELONGS_TO_LANE
          ┌──────────────┤
          │              │
    ┌─────┴─────┐  ┌────┴─────┐      ┌──────────┐
    │  Evidence  │  │   Case   │◄─────│  Judge   │
    │  (orange)  │  │          │      │ (purple) │
    └──┬──┬──┬──┘  └──┬──┬────┘      └────▲─────┘
       │  │  │        │  │                 │ COMMITTED_BY
       │  │  │        │  │           ┌─────┴──────┐
       │  │  └────────┼──┼──────────►│ Violation  │
       │  │  SUPPORTS │  │           │ (crimson)  │
       │  │  _CLAIM   │  │           └─────┬──────┘
       │  │     ▼     │  │                 │ VIOLATES_RULE
       │  │  ┌──────┐ │  │           ┌─────▼──────┐
       │  │  │Claim │ │  │           │    Rule    │
       │  │  └──────┘ │  │           │   (gold)   │
       │  │           │  │           └─────▲──────┘
       │  │           │  │                 │ CITES_AUTHORITY
       │  │     ┌─────┘  │           ┌─────┴──────┐
       │  │     │ FILED  │           │  Filing    │
       │  │     │ _IN    │           │  (green)   │
       │  │     │ _CASE  │           └──┬──┬──────┘
       │  │     │        │              │  │
       │  │     │  PARTY │              │  │ REQUIRES_FORM
       │  │     │  _IN   │              │  │
       │  │     │  _CASE │         ┌────┘  ▼
       │  │     │    ▼   │         │  ┌──────────┐
       │  │     │ ┌──────┴┐       │  │   Form   │
       │  │     │ │ Party  │       │  │  (cyan)  │
       │  │     │ └───▲───┘       │  └──────────┘
       │  │     │     │            │
       │  │     │  ATTORNEY        │ FILING_USES
       │  │     │  _REPRESENTS     │ _EVIDENCE
       │  │     │     │            │
       │  │     │ ┌───┴────┐      │
       │  │     │ │Attorney│      │
       │  │     │ │ (gray) │      │
       │  │     │ └────────┘      │
       │  │     │                  │
       │  └─────┼──────────────────┘
       │        │
  ┌────┴─────┐  │
  │ Witness  │  │  ┌──────────┐
  │ (teal)   │  │  │  Event   │
  └──────────┘  │  │  (blue)  │
                │  └──────────┘
                │
         TESTIFIED_ABOUT
```

---

## Color Palette Reference

| Color | Hex | Usage |
|-------|-----|-------|
| Royal Blue | `#1E3A5F` | Lane A — Custody |
| Forest Green | `#2E7D32` | Lane B — Housing |
| Gold | `#F9A825` | Lane C — Convergence |
| Crimson | `#C62828` | Lane D — PPO |
| Purple | `#6A1B9A` | Lane E — Misconduct |
| Teal | `#00838F` | Lane F — Appellate |
| White | `#FFFFFF` | Parties |
| Dark Gray | `#424242` | Attorneys |
| Orange | `#E65100` | Evidence |
| Light Green | `#66BB6A` | Filings |
| Cyan | `#00BCD4` | Forms |
| Amber | `#FFB300` | Rules/Authorities |
| Timeline Blue | `#1565C0` | Events |
| Violation Red | `#D32F2F` | Violations |
| Witness Teal | `#008080` | Witnesses |
| Judge Purple | `#7B1FA2` | Judge |

---

## Troubleshooting

### "Couldn't load the external resource"

CSV files are not in the Neo4j import directory. Verify:
```cypher
// Check import directory location
CALL dbms.listConfig() YIELD name, value
WHERE name = 'server.directories.import'
RETURN value;
```

### "There is no procedure with the name `apoc.*`"

Install APOC plugin:
- Neo4j Desktop: Click DBMS → Plugins → APOC → Install
- Docker: Set `NEO4J_PLUGINS='["apoc"]'` environment variable

### Batched import fails

If `:auto ... IN TRANSACTIONS` fails, your Neo4j version may not support it. Replace with:
```cypher
// Remove the :auto prefix and IN TRANSACTIONS suffix
LOAD CSV WITH HEADERS FROM 'file:///evidence.csv' AS row
CREATE (e:Evidence {id: row.id, ...});
```
Note: This loads all rows in a single transaction (may be slow for large datasets).

### Memory issues with large imports

Increase Neo4j heap:
```properties
# neo4j.conf
server.memory.heap.initial_size=1g
server.memory.heap.max_size=2g
server.memory.pagecache.size=1g
```

### Verification queries return unexpected counts

Re-run the export script to regenerate CSVs, then re-import. CSV data reflects the state of `litigation_context.db` at export time.

---

## File Manifest

| File | Purpose |
|------|---------|
| `neo4j_data_model.md` | Complete data model documentation (13 nodes, 15 edges) |
| `import_nodes.cypher` | Cypher script to import all node types with constraints/indexes |
| `import_edges.cypher` | Cypher script to import all relationship types |
| `bloom_perspective.json` | Neo4j Bloom perspective with colors, sizing, layout |
| `bloom_search_phrases.json` | 30 predefined search phrases with Cypher queries |
| `README.md` | This file — setup and usage guide |

---

## Related Files

| File | Location | Purpose |
|------|----------|---------|
| Export script | `scripts/omega_neo4j_export.py` | Generates CSVs from litigation_context.db |
| Data model source | `neo4j_data_model.md` | Schema reference |
| LitigationOS DB | `C:\Users\andre\LitigationOS\litigation_context.db` | Source database |
| Court forms DB | `C:\Users\andre\LitigationOS\databases\court_forms.db` | Form definitions |
