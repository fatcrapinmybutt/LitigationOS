"""
Neo4j Graph Schema — LitigationOS Knowledge Graph
Creates constraints, indexes, and initial graph structure from DB data.
Exports CSV files for neo4j-admin import and Cypher schema.
"""
import sqlite3
import csv
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
OUTPUT_DIR = r"C:\Users\andre\LitigationOS\00_SYSTEM\neo4j"

SCHEMA_CYPHER = """
// ============ CONSTRAINTS ============
CREATE CONSTRAINT person_id IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT claim_id IF NOT EXISTS FOR (c:Claim) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT evidence_id IF NOT EXISTS FOR (e:Evidence) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT action_id IF NOT EXISTS FOR (a:Action) REQUIRE a.id IS UNIQUE;
CREATE CONSTRAINT filing_id IF NOT EXISTS FOR (f:Filing) REQUIRE f.id IS UNIQUE;
CREATE CONSTRAINT forum_id IF NOT EXISTS FOR (f:Forum) REQUIRE f.id IS UNIQUE;
CREATE CONSTRAINT law_id IF NOT EXISTS FOR (l:Law) REQUIRE l.id IS UNIQUE;
CREATE CONSTRAINT violation_id IF NOT EXISTS FOR (v:Violation) REQUIRE v.id IS UNIQUE;
CREATE CONSTRAINT event_id IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT order_id IF NOT EXISTS FOR (o:Order) REQUIRE o.id IS UNIQUE;

// ============ INDEXES ============
CREATE INDEX person_name IF NOT EXISTS FOR (p:Person) ON (p.name);
CREATE INDEX claim_type IF NOT EXISTS FOR (c:Claim) ON (c.type);
CREATE INDEX evidence_type IF NOT EXISTS FOR (e:Evidence) ON (e.type);
CREATE INDEX action_score IF NOT EXISTS FOR (a:Action) ON (a.omega_score);
CREATE INDEX action_forum IF NOT EXISTS FOR (a:Action) ON (a.forum);
CREATE INDEX filing_status IF NOT EXISTS FOR (f:Filing) ON (f.status);
CREATE INDEX violation_type IF NOT EXISTS FOR (v:Violation) ON (v.type);
CREATE INDEX event_date IF NOT EXISTS FOR (e:Event) ON (e.date);

// ============ FORUM NODES ============
MERGE (f:Forum {id: 'MSC'}) SET f.name = 'Michigan Supreme Court', f.lane = 'A';
MERGE (f:Forum {id: 'COA'}) SET f.name = 'Court of Appeals', f.lane = 'B';
MERGE (f:Forum {id: '14TH'}) SET f.name = '14th Circuit Court', f.lane = 'C';
MERGE (f:Forum {id: 'JTC'}) SET f.name = 'Judicial Tenure Commission', f.lane = 'D';
MERGE (f:Forum {id: 'USDC'}) SET f.name = 'US District Court', f.lane = 'E';
MERGE (f:Forum {id: 'BAR'}) SET f.name = 'State Bar of Michigan', f.lane = 'F';

// ============ PERSON NODES ============
MERGE (p:Person {id: 'andrew-pigors'}) SET p.name = 'Andrew Pigors', p.role = 'Plaintiff/Father';
MERGE (p:Person {id: 'emily-watson'}) SET p.name = 'Emily Watson', p.role = 'Defendant/Mother';
MERGE (p:Person {id: 'lincoln'}) SET p.name = 'Lincoln', p.role = 'Child';
MERGE (p:Person {id: 'judge-mcneill'}) SET p.name = 'Judge Jenny L. McNeill', p.role = 'Judge';
MERGE (p:Person {id: 'atty-berry'}) SET p.name = 'Attorney Berry', p.role = 'Attorney';
MERGE (p:Person {id: 'atty-barnes'}) SET p.name = 'Attorney Barnes', p.role = 'Attorney';
MERGE (p:Person {id: 'atty-martini'}) SET p.name = 'Attorney Martini', p.role = 'Attorney';

// ============ RELATIONSHIPS ============
MATCH (a:Person {id: 'andrew-pigors'}), (l:Person {id: 'lincoln'})
MERGE (a)-[:PARENT_OF]->(l);

MATCH (e:Person {id: 'emily-watson'}), (l:Person {id: 'lincoln'})
MERGE (e)-[:PARENT_OF]->(l);

MATCH (j:Person {id: 'judge-mcneill'}), (f:Forum {id: '14TH'})
MERGE (j)-[:PRESIDES_OVER]->(f);

MATCH (b:Person {id: 'atty-berry'}), (e:Person {id: 'emily-watson'})
MERGE (b)-[:REPRESENTS]->(e);
"""


def export_omega_actions(conn, output_dir):
    actions = conn.execute("""
        SELECT action_id, name, forum, lane, total_score, tier, tier_action,
               evidence_strength, legal_authority, strategic_impact, urgency,
               feasibility, adversary_vulnerability, compound_effect,
               reversibility_risk, precedent_value, public_interest, notes
        FROM omega_scores ORDER BY total_score DESC
    """).fetchall()
    
    with open(os.path.join(output_dir, "neo4j_action_nodes.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["actionId:ID", "name", "forum", "lane", "omegaScore:int", "tier",
                     "evidenceStrength:int", "legalAuthority:int", "strategicImpact:int",
                     "urgency:int", "feasibility:int", ":LABEL"])
        for a in actions:
            w.writerow([a[0], a[1], a[2], a[3], a[4], a[5], a[7], a[8], a[9], a[10], a[11], "Action"])
    
    with open(os.path.join(output_dir, "neo4j_action_forum_edges.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([":START_ID", ":END_ID", ":TYPE", "score:int"])
        for a in actions:
            w.writerow([a[0], a[2], "FILED_IN", a[4]])
    
    return len(actions)


def export_claims(conn, output_dir):
    try:
        cols = [d[0] for d in conn.execute("PRAGMA table_info(claims)").fetchall()]
        col_names = [c[1] for c in conn.execute("PRAGMA table_info(claims)").fetchall()]
        claims = conn.execute("SELECT rowid, * FROM claims LIMIT 1000").fetchall()
    except Exception as e:
        print(f"  Claims export skipped: {e}")
        return 0
    
    with open(os.path.join(output_dir, "neo4j_claim_nodes.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["claimId:ID", "text", ":LABEL"])
        for c in claims:
            text = str(c[1])[:200] if len(c) > 1 else str(c[0])
            w.writerow([f"claim-{c[0]}", text.replace('"', "'"), "Claim"])
    
    return len(claims)


def export_violations(conn, output_dir):
    try:
        violations = conn.execute("SELECT rowid, * FROM judicial_violations LIMIT 2000").fetchall()
    except Exception as e:
        print(f"  Violations export skipped: {e}")
        return 0
    
    with open(os.path.join(output_dir, "neo4j_violation_nodes.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["violationId:ID", "description", ":LABEL"])
        for v in violations:
            desc = str(v[1])[:200] if len(v) > 1 else str(v[0])
            w.writerow([f"viol-{v[0]}", desc.replace('"', "'"), "Violation"])
    
    return len(violations)


def export_evidence_quotes(conn, output_dir):
    try:
        quotes = conn.execute("SELECT rowid, * FROM evidence_quotes LIMIT 5000").fetchall()
    except Exception as e:
        print(f"  Evidence export skipped: {e}")
        return 0
    
    with open(os.path.join(output_dir, "neo4j_evidence_nodes.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["evidenceId:ID", "text", ":LABEL"])
        for q in quotes:
            text = str(q[1])[:200] if len(q) > 1 else str(q[0])
            w.writerow([f"ev-{q[0]}", text.replace('"', "'").replace("\n", " "), "Evidence"])
    
    return len(quotes)


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    with open(os.path.join(OUTPUT_DIR, "schema.cypher"), "w", encoding="utf-8") as f:
        f.write(SCHEMA_CYPHER)
    print(f"[OK] Schema written to schema.cypher")
    
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    
    n = export_omega_actions(conn, OUTPUT_DIR)
    print(f"[OK] {n} OMEGA action nodes exported")
    
    n = export_claims(conn, OUTPUT_DIR)
    print(f"[OK] {n} claim nodes exported")
    
    n = export_violations(conn, OUTPUT_DIR)
    print(f"[OK] {n} violation nodes exported")
    
    n = export_evidence_quotes(conn, OUTPUT_DIR)
    print(f"[OK] {n} evidence nodes exported")
    
    conn.close()
    
    print(f"\nNeo4j export files:")
    total = 0
    for f in sorted(os.listdir(OUTPUT_DIR)):
        sz = os.path.getsize(os.path.join(OUTPUT_DIR, f))
        total += sz
        print(f"  {f}: {sz:,} bytes")
    print(f"  TOTAL: {total:,} bytes")
