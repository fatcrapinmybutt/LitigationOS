
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
