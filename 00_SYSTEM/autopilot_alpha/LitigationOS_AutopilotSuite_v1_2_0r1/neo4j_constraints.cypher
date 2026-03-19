// Neo4j constraints/indexes (safe to re-run)
CREATE CONSTRAINT IF NOT EXISTS constraint_uid_authority
FOR (n:Authority) REQUIRE n.uid IS UNIQUE;

CREATE CONSTRAINT IF NOT EXISTS constraint_uid_vehicle
FOR (n:Vehicle) REQUIRE n.uid IS UNIQUE;

CREATE CONSTRAINT IF NOT EXISTS constraint_uid_contradiction
FOR (n:ContradictionItem) REQUIRE n.uid IS UNIQUE;

CREATE CONSTRAINT IF NOT EXISTS constraint_uid_sourceref
FOR (n:SourceRef) REQUIRE n.uid IS UNIQUE;

CREATE CONSTRAINT IF NOT EXISTS constraint_uid_quote
FOR (n:QuoteAtom) REQUIRE n.uid IS UNIQUE;

CREATE CONSTRAINT IF NOT EXISTS constraint_uid_stub
FOR (n:AuthorityCiteStub) REQUIRE n.uid IS UNIQUE;

CREATE CONSTRAINT IF NOT EXISTS constraint_uid_orderpin
FOR (n:OperatingOrderPin) REQUIRE n.uid IS UNIQUE;

CREATE CONSTRAINT IF NOT EXISTS constraint_uid_gate
FOR (n:GateResult) REQUIRE n.uid IS UNIQUE;

CREATE CONSTRAINT IF NOT EXISTS constraint_uid_court
FOR (n:Court) REQUIRE n.uid IS UNIQUE;

CREATE INDEX IF NOT EXISTS idx_node_type FOR (n) ON (n.node_type);
