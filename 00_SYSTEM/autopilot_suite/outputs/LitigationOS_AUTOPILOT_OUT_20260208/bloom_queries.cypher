// Bloom starter queries (LitigationOS Autopilot Suite)

MATCH (c:ContradictionItem) RETURN c LIMIT 500;

MATCH (c:ContradictionItem)-[:REMEDY_FOR_GAP]->(r:RemedyCandidate)-[:REMEDY_IMPLIES_VEHICLE_CANDIDATE]->(v:VehicleCandidate)
RETURN c,r,v LIMIT 500;

MATCH (c:ContradictionItem)-[:GAP_IMPLICATES_HARM_CANDIDATE]->(h:HarmCandidate)
RETURN c,h LIMIT 500;

MATCH (q:QuoteAtom)-[:CITES_AUTHORITY_UNRESOLVED]->(a:AuthorityCiteStub)
RETURN q,a LIMIT 500;

MATCH (t:GlossaryTerm)-[:TERM_CHILD_OF]->(p:GlossaryTerm)
RETURN t,p LIMIT 500;
