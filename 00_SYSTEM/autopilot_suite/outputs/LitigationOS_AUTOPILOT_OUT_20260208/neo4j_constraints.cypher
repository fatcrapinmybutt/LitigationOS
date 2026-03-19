// Neo4j constraints & indexes (LitigationOS Autopilot Suite)
// Safe to run repeatedly (Neo4j 5+)

CREATE CONSTRAINT entity_uid_unique IF NOT EXISTS
FOR (n:Entity) REQUIRE n.uid IS UNIQUE;

CREATE INDEX entity_node_type IF NOT EXISTS
FOR (n:Entity) ON (n.node_type);

CREATE INDEX entity_label IF NOT EXISTS
FOR (n:Entity) ON (n.label);

CREATE INDEX authority_citation IF NOT EXISTS
FOR (n:AuthorityCiteStub) ON (n.citation);
