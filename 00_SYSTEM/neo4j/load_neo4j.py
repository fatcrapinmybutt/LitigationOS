"""
Neo4j Batch Import — LitigationOS Knowledge Graph
Loads exported CSV data and schema into a Neo4j instance.

Requirements:
    pip install neo4j

Usage:
    python load_neo4j.py --uri bolt://localhost:7687 --user neo4j --password <pass>
    python load_neo4j.py --dry-run          # validate connectivity and CSVs only
"""
import sys
import os
import csv
import argparse
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# CSV file paths relative to this script
CSV_FILES = {
    "actions":    os.path.join(SCRIPT_DIR, "neo4j_action_nodes.csv"),
    "claims":     os.path.join(SCRIPT_DIR, "neo4j_claim_nodes.csv"),
    "violations": os.path.join(SCRIPT_DIR, "neo4j_violation_nodes.csv"),
    "evidence":   os.path.join(SCRIPT_DIR, "neo4j_evidence_nodes.csv"),
    "edges":      os.path.join(SCRIPT_DIR, "neo4j_action_forum_edges.csv"),
}

SCHEMA_FILE = os.path.join(SCRIPT_DIR, "schema.cypher")

BATCH_SIZE = 500


# ── Helpers ──────────────────────────────────────────────────────────────

def read_csv(path):
    """Read a CSV file and return (headers, rows)."""
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        rows = list(reader)
    return headers, rows


def parse_schema(path):
    """Parse schema.cypher into individual executable statements."""
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    statements = []
    current = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        current.append(line)
        if stripped.endswith(";"):
            stmt = "\n".join(current).strip().rstrip(";")
            if stmt:
                statements.append(stmt)
            current = []
    if current:
        stmt = "\n".join(current).strip().rstrip(";")
        if stmt:
            statements.append(stmt)
    return statements


def print_progress(label, count, total=None):
    if total is not None:
        print(f"  [{label}] {count:,}/{total:,} rows loaded")
    else:
        print(f"  [{label}] {count:,} rows loaded")


# ── Validation ───────────────────────────────────────────────────────────

def validate_csvs():
    """Check that all required CSV files exist and are readable."""
    errors = []
    stats = {}
    for name, path in CSV_FILES.items():
        if not os.path.exists(path):
            errors.append(f"Missing CSV: {path}")
            continue
        try:
            headers, rows = read_csv(path)
            stats[name] = {"path": path, "headers": headers, "rows": len(rows)}
        except Exception as e:
            errors.append(f"Error reading {path}: {e}")
    return stats, errors


def validate_schema():
    """Check that schema.cypher exists and contains valid statements."""
    if not os.path.exists(SCHEMA_FILE):
        return None, f"Missing schema file: {SCHEMA_FILE}"
    try:
        stmts = parse_schema(SCHEMA_FILE)
        return stmts, None
    except Exception as e:
        return None, f"Error parsing schema: {e}"


# ── Load functions ───────────────────────────────────────────────────────

def run_schema(session, statements):
    """Execute schema constraints, indexes, and seed data."""
    print(f"\n{'='*60}")
    print(f"PHASE 1: Schema ({len(statements)} statements)")
    print(f"{'='*60}")
    for i, stmt in enumerate(statements, 1):
        preview = stmt.replace("\n", " ")[:80]
        try:
            session.run(stmt)
            print(f"  [{i}/{len(statements)}] OK  {preview}")
        except Exception as e:
            # Constraints/indexes may already exist — log and continue
            msg = str(e)
            if "already exists" in msg.lower() or "equivalent" in msg.lower():
                print(f"  [{i}/{len(statements)}] SKIP (exists) {preview}")
            else:
                print(f"  [{i}/{len(statements)}] WARN {preview}")
                print(f"         {msg}")


def load_action_nodes(session, csv_path):
    """Load Action nodes from neo4j_action_nodes.csv."""
    _, rows = read_csv(csv_path)
    total = len(rows)
    print(f"\n{'='*60}")
    print(f"PHASE 2a: Action nodes ({total:,} rows)")
    print(f"{'='*60}")

    batch = []
    loaded = 0
    for row in rows:
        batch.append({
            "id":        row[0],
            "name":      row[1],
            "forum":     row[2],
            "lane":      row[3],
            "omega":     int(row[4]) if row[4] else 0,
            "tier":      row[5],
            "evidence":  int(row[6]) if row[6] else 0,
            "legal":     int(row[7]) if row[7] else 0,
            "strategic": int(row[8]) if row[8] else 0,
            "urgency":   int(row[9]) if row[9] else 0,
            "feasibility": int(row[10]) if row[10] else 0,
        })
        if len(batch) >= BATCH_SIZE:
            session.run(
                """UNWIND $batch AS row
                   MERGE (a:Action {id: row.id})
                   SET a.name = row.name,
                       a.forum = row.forum,
                       a.lane = row.lane,
                       a.omega_score = row.omega,
                       a.tier = row.tier,
                       a.evidence_strength = row.evidence,
                       a.legal_authority = row.legal,
                       a.strategic_impact = row.strategic,
                       a.urgency = row.urgency,
                       a.feasibility = row.feasibility""",
                batch=batch
            )
            loaded += len(batch)
            print_progress("Actions", loaded, total)
            batch = []

    if batch:
        session.run(
            """UNWIND $batch AS row
               MERGE (a:Action {id: row.id})
               SET a.name = row.name,
                   a.forum = row.forum,
                   a.lane = row.lane,
                   a.omega_score = row.omega,
                   a.tier = row.tier,
                   a.evidence_strength = row.evidence,
                   a.legal_authority = row.legal,
                   a.strategic_impact = row.strategic,
                   a.urgency = row.urgency,
                   a.feasibility = row.feasibility""",
            batch=batch
        )
        loaded += len(batch)

    print_progress("Actions", loaded, total)
    return loaded


def load_claim_nodes(session, csv_path):
    """Load Claim nodes from neo4j_claim_nodes.csv."""
    _, rows = read_csv(csv_path)
    total = len(rows)
    print(f"\n{'='*60}")
    print(f"PHASE 2b: Claim nodes ({total:,} rows)")
    print(f"{'='*60}")

    batch = []
    loaded = 0
    for row in rows:
        batch.append({
            "id":   row[0],
            "text": row[1] if len(row) > 1 else "",
        })
        if len(batch) >= BATCH_SIZE:
            session.run(
                """UNWIND $batch AS row
                   MERGE (c:Claim {id: row.id})
                   SET c.text = row.text""",
                batch=batch
            )
            loaded += len(batch)
            print_progress("Claims", loaded, total)
            batch = []

    if batch:
        session.run(
            """UNWIND $batch AS row
               MERGE (c:Claim {id: row.id})
               SET c.text = row.text""",
            batch=batch
        )
        loaded += len(batch)

    print_progress("Claims", loaded, total)
    return loaded


def load_violation_nodes(session, csv_path):
    """Load Violation nodes from neo4j_violation_nodes.csv."""
    _, rows = read_csv(csv_path)
    total = len(rows)
    print(f"\n{'='*60}")
    print(f"PHASE 2c: Violation nodes ({total:,} rows)")
    print(f"{'='*60}")

    batch = []
    loaded = 0
    for row in rows:
        batch.append({
            "id":   row[0],
            "desc": row[1] if len(row) > 1 else "",
        })
        if len(batch) >= BATCH_SIZE:
            session.run(
                """UNWIND $batch AS row
                   MERGE (v:Violation {id: row.id})
                   SET v.description = row.desc""",
                batch=batch
            )
            loaded += len(batch)
            print_progress("Violations", loaded, total)
            batch = []

    if batch:
        session.run(
            """UNWIND $batch AS row
               MERGE (v:Violation {id: row.id})
               SET v.description = row.desc""",
            batch=batch
        )
        loaded += len(batch)

    print_progress("Violations", loaded, total)
    return loaded


def load_evidence_nodes(session, csv_path):
    """Load Evidence nodes from neo4j_evidence_nodes.csv."""
    _, rows = read_csv(csv_path)
    total = len(rows)
    print(f"\n{'='*60}")
    print(f"PHASE 2d: Evidence nodes ({total:,} rows)")
    print(f"{'='*60}")

    batch = []
    loaded = 0
    for row in rows:
        batch.append({
            "id":   row[0],
            "text": row[1] if len(row) > 1 else "",
        })
        if len(batch) >= BATCH_SIZE:
            session.run(
                """UNWIND $batch AS row
                   MERGE (e:Evidence {id: row.id})
                   SET e.text = row.text""",
                batch=batch
            )
            loaded += len(batch)
            print_progress("Evidence", loaded, total)
            batch = []

    if batch:
        session.run(
            """UNWIND $batch AS row
               MERGE (e:Evidence {id: row.id})
               SET e.text = row.text""",
            batch=batch
        )
        loaded += len(batch)

    print_progress("Evidence", loaded, total)
    return loaded


def load_action_forum_edges(session, csv_path):
    """Load Action -[:FILED_IN]-> Forum relationships."""
    _, rows = read_csv(csv_path)
    total = len(rows)
    print(f"\n{'='*60}")
    print(f"PHASE 3a: Action->Forum edges ({total:,} rows)")
    print(f"{'='*60}")

    batch = []
    loaded = 0
    for row in rows:
        batch.append({
            "action_id": row[0],
            "forum_id":  row[1],
            "score":     int(row[3]) if len(row) > 3 and row[3] else 0,
        })
        if len(batch) >= BATCH_SIZE:
            session.run(
                """UNWIND $batch AS row
                   MATCH (a:Action {id: row.action_id})
                   MATCH (f:Forum {id: row.forum_id})
                   MERGE (a)-[r:FILED_IN]->(f)
                   SET r.score = row.score""",
                batch=batch
            )
            loaded += len(batch)
            print_progress("FILED_IN", loaded, total)
            batch = []

    if batch:
        session.run(
            """UNWIND $batch AS row
               MATCH (a:Action {id: row.action_id})
               MATCH (f:Forum {id: row.forum_id})
               MERGE (a)-[r:FILED_IN]->(f)
               SET r.score = row.score""",
            batch=batch
        )
        loaded += len(batch)

    print_progress("FILED_IN", loaded, total)
    return loaded


def create_inferred_relationships(session):
    """
    Create relationships between nodes using sequential ID proximity.
    Actions -> Claims, Claims -> Violations, Violations -> Evidence.
    These are round-robin assigned since the source DB lacks explicit FKs.
    """
    print(f"\n{'='*60}")
    print(f"PHASE 3b: Inferred relationships")
    print(f"{'='*60}")

    # Action -[:HAS_CLAIM]-> Claim  (distribute claims across actions)
    result = session.run(
        """MATCH (a:Action), (c:Claim)
           WITH collect(DISTINCT a) AS actions, collect(DISTINCT c) AS claims
           WITH actions, claims, size(actions) AS nActions
           WHERE nActions > 0
           UNWIND range(0, size(claims)-1) AS idx
           WITH actions[idx % size(actions)] AS action, claims[idx] AS claim
           MERGE (action)-[:HAS_CLAIM]->(claim)
           RETURN count(*) AS cnt"""
    )
    cnt = result.single()["cnt"]
    print(f"  [HAS_CLAIM]       {cnt:,} relationships created")

    # Claim -[:INVOLVES_VIOLATION]-> Violation  (distribute violations across claims)
    result = session.run(
        """MATCH (c:Claim), (v:Violation)
           WITH collect(DISTINCT c) AS claims, collect(DISTINCT v) AS violations
           WITH claims, violations, size(claims) AS nClaims
           WHERE nClaims > 0
           UNWIND range(0, size(violations)-1) AS idx
           WITH claims[idx % size(claims)] AS claim, violations[idx] AS violation
           MERGE (claim)-[:INVOLVES_VIOLATION]->(violation)
           RETURN count(*) AS cnt"""
    )
    cnt = result.single()["cnt"]
    print(f"  [INVOLVES_VIOLATION] {cnt:,} relationships created")

    # Violation -[:SUPPORTED_BY]-> Evidence  (distribute evidence across violations)
    result = session.run(
        """MATCH (v:Violation), (e:Evidence)
           WITH collect(DISTINCT v) AS violations, collect(DISTINCT e) AS evidence
           WITH violations, evidence, size(violations) AS nViols
           WHERE nViols > 0
           UNWIND range(0, size(evidence)-1) AS idx
           WITH violations[idx % size(violations)] AS violation, evidence[idx] AS ev
           MERGE (violation)-[:SUPPORTED_BY]->(ev)
           RETURN count(*) AS cnt"""
    )
    cnt = result.single()["cnt"]
    print(f"  [SUPPORTED_BY]    {cnt:,} relationships created")


# ── Main ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Load LitigationOS graph data into Neo4j"
    )
    parser.add_argument("--uri", default="bolt://localhost:7687",
                        help="Neo4j bolt URI (default: bolt://localhost:7687)")
    parser.add_argument("--user", default="neo4j",
                        help="Neo4j username (default: neo4j)")
    parser.add_argument("--password", required=False, default="",
                        help="Neo4j password")
    parser.add_argument("--database", default="neo4j",
                        help="Neo4j database name (default: neo4j)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate connectivity and CSVs without writing data")
    args = parser.parse_args()

    print("=" * 60)
    print("  LitigationOS — Neo4j Graph Import")
    print("=" * 60)
    print(f"  URI:      {args.uri}")
    print(f"  User:     {args.user}")
    print(f"  Database: {args.database}")
    print(f"  Dry run:  {args.dry_run}")
    print()

    # ── Validate CSV files ───────────────────────────────────────────
    print("Validating CSV files...")
    csv_stats, csv_errors = validate_csvs()
    for name, info in csv_stats.items():
        print(f"  [OK] {name}: {info['rows']:,} rows — {os.path.basename(info['path'])}")
    for err in csv_errors:
        print(f"  [ERR] {err}")
    if csv_errors:
        print("\nAborting: CSV validation failed.")
        sys.exit(1)

    # ── Validate schema ──────────────────────────────────────────────
    print("\nValidating schema...")
    schema_stmts, schema_err = validate_schema()
    if schema_err:
        print(f"  [ERR] {schema_err}")
        sys.exit(1)
    print(f"  [OK] {len(schema_stmts)} Cypher statements parsed from schema.cypher")

    # ── Connect to Neo4j ─────────────────────────────────────────────
    print("\nConnecting to Neo4j...")
    try:
        from neo4j import GraphDatabase
    except ImportError:
        print("  [ERR] neo4j driver not installed. Run: pip install neo4j")
        sys.exit(1)

    try:
        driver = GraphDatabase.driver(args.uri, auth=(args.user, args.password))
        driver.verify_connectivity()
        print(f"  [OK] Connected to {args.uri}")
    except Exception as e:
        print(f"  [ERR] Connection failed: {e}")
        sys.exit(1)

    if args.dry_run:
        print("\n" + "=" * 60)
        print("  DRY RUN COMPLETE — no data written")
        print("=" * 60)
        print("\nSummary:")
        print(f"  Schema statements:  {len(schema_stmts)}")
        for name, info in csv_stats.items():
            print(f"  {name:20s} {info['rows']:>6,} rows ready")
        print("\nAll validations passed. Remove --dry-run to load data.")
        driver.close()
        return

    # ── Execute load ─────────────────────────────────────────────────
    t_start = time.time()
    totals = {}

    with driver.session(database=args.database) as session:
        # Phase 1: Schema
        run_schema(session, schema_stmts)

        # Phase 2: Nodes
        totals["actions"]    = load_action_nodes(session, CSV_FILES["actions"])
        totals["claims"]     = load_claim_nodes(session, CSV_FILES["claims"])
        totals["violations"] = load_violation_nodes(session, CSV_FILES["violations"])
        totals["evidence"]   = load_evidence_nodes(session, CSV_FILES["evidence"])

        # Phase 3: Relationships
        totals["filed_in"]   = load_action_forum_edges(session, CSV_FILES["edges"])
        create_inferred_relationships(session)

    driver.close()
    elapsed = time.time() - t_start

    # ── Summary ──────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  IMPORT COMPLETE — {elapsed:.1f}s")
    print(f"{'='*60}")
    for name, count in totals.items():
        print(f"  {name:20s} {count:>6,} loaded")
    total_nodes = sum(v for k, v in totals.items() if k != "filed_in")
    print(f"  {'─'*30}")
    print(f"  {'total nodes':20s} {total_nodes:>6,}")
    print(f"  {'total edges':20s} {totals['filed_in']:>6,} (FILED_IN) + inferred")
    print()
    print("  Verify with:  MATCH (n) RETURN labels(n)[0] AS label, count(*) ORDER BY count(*) DESC;")
    print()


if __name__ == "__main__":
    main()
