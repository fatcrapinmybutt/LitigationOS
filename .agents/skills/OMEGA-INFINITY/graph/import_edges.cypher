// ============================================================================
// LitigationOS OMEGA-INFINITY — Neo4j Edge (Relationship) Import Script
// ============================================================================
// Version: 4.0
// Usage: Run AFTER import_nodes.cypher completes successfully
// Prerequisites: All node imports must be complete before creating edges
// ============================================================================

// ----------------------------------------------------------------------------
// EDGE 1: BELONGS_TO_LANE (Case → Lane)
// ----------------------------------------------------------------------------

LOAD CSV WITH HEADERS FROM 'file:///rel_belongs_to_lane.csv' AS row
MATCH (c:Case {case_number: row.case_number})
MATCH (l:Lane {lane_id: row.lane_id})
MERGE (c)-[r:BELONGS_TO_LANE]->(l)
SET r.weight = 1.0;

// ----------------------------------------------------------------------------
// EDGE 2: PARTY_IN_CASE (Party → Case)
// ----------------------------------------------------------------------------

LOAD CSV WITH HEADERS FROM 'file:///rel_party_in_case.csv' AS row
MATCH (p:Party {name: row.party_name})
MATCH (c:Case {case_number: row.case_number})
MERGE (p)-[r:PARTY_IN_CASE]->(c)
SET r.role = row.role,
    r.weight = 1.0;

// ----------------------------------------------------------------------------
// EDGE 3: JUDGE_PRESIDES (Judge → Case)
// ----------------------------------------------------------------------------

LOAD CSV WITH HEADERS FROM 'file:///rel_judge_presides.csv' AS row
MATCH (j:Judge {name: row.judge_name})
MATCH (c:Case {case_number: row.case_number})
MERGE (j)-[r:JUDGE_PRESIDES]->(c)
SET r.division = row.division,
    r.weight = 1.0;

// ----------------------------------------------------------------------------
// EDGE 4: ATTORNEY_REPRESENTS (Attorney → Party)
// ----------------------------------------------------------------------------

LOAD CSV WITH HEADERS FROM 'file:///rel_attorney_represents.csv' AS row
MATCH (a:Attorney {bar_number: row.bar_number})
MATCH (p:Party {name: row.party_name})
MERGE (a)-[r:ATTORNEY_REPRESENTS]->(p)
SET r.status = row.status,
    r.start_date = row.start_date,
    r.end_date = row.end_date,
    r.weight = 1.0;

// ----------------------------------------------------------------------------
// EDGE 5: SUPPORTS_CLAIM (Evidence → Claim) — large, batched
// ----------------------------------------------------------------------------

:auto LOAD CSV WITH HEADERS FROM 'file:///rel_supports_claim.csv' AS row
CALL { WITH row
  MATCH (e:Evidence {id: row.evidence_id})
  MATCH (cl:Claim {claim_id: row.claim_id})
  MERGE (e)-[r:SUPPORTS_CLAIM]->(cl)
  SET r.relevance_score = CASE WHEN row.relevance_score IS NOT NULL
                               THEN toFloat(row.relevance_score) ELSE 0.5 END,
      r.category_match = row.category_match,
      r.weight = CASE WHEN row.relevance_score IS NOT NULL
                      THEN toFloat(row.relevance_score) ELSE 0.5 END
} IN TRANSACTIONS OF 5000 ROWS;

// ----------------------------------------------------------------------------
// EDGE 6: FILED_IN_CASE (Filing → Case)
// ----------------------------------------------------------------------------

:auto LOAD CSV WITH HEADERS FROM 'file:///rel_filed_in_case.csv' AS row
CALL { WITH row
  MATCH (f:Filing {vehicle_name: row.vehicle_name})
  MATCH (c:Case {case_number: row.case_number})
  MERGE (f)-[r:FILED_IN_CASE]->(c)
  SET r.readiness_score = CASE WHEN row.readiness_score IS NOT NULL
                               THEN toFloat(row.readiness_score) ELSE 0.0 END,
      r.filing_date = row.filing_date,
      r.weight = CASE WHEN row.readiness_score IS NOT NULL
                      THEN toFloat(row.readiness_score) / 100.0 ELSE 0.0 END
} IN TRANSACTIONS OF 5000 ROWS;

// ----------------------------------------------------------------------------
// EDGE 7: REQUIRES_FORM (Filing → Form)
// ----------------------------------------------------------------------------

:auto LOAD CSV WITH HEADERS FROM 'file:///rel_requires_form.csv' AS row
CALL { WITH row
  MATCH (f:Filing {vehicle_name: row.vehicle_name})
  MATCH (fm:Form {form_number: row.form_number})
  MERGE (f)-[r:REQUIRES_FORM]->(fm)
  SET r.required = CASE WHEN row.required = 'true' THEN true ELSE false END,
      r.weight = 1.0
} IN TRANSACTIONS OF 5000 ROWS;

// ----------------------------------------------------------------------------
// EDGE 8: CITES_AUTHORITY (Filing → Rule)
// ----------------------------------------------------------------------------

:auto LOAD CSV WITH HEADERS FROM 'file:///rel_cites_authority.csv' AS row
CALL { WITH row
  MATCH (f:Filing {vehicle_name: row.vehicle_name})
  MATCH (r_node:Rule {citation: row.citation})
  MERGE (f)-[r:CITES_AUTHORITY]->(r_node)
  SET r.chain_count = CASE WHEN row.chain_count IS NOT NULL
                           THEN toInteger(row.chain_count) ELSE 1 END,
      r.context = row.context,
      r.weight = CASE WHEN row.chain_count IS NOT NULL
                      THEN toFloat(row.chain_count) / 10.0 ELSE 0.1 END
} IN TRANSACTIONS OF 5000 ROWS;

// ----------------------------------------------------------------------------
// EDGE 9: VIOLATES_RULE (Violation → Rule)
// ----------------------------------------------------------------------------

:auto LOAD CSV WITH HEADERS FROM 'file:///rel_violates_rule.csv' AS row
CALL { WITH row
  MATCH (v:Violation {violation_id: row.violation_id})
  MATCH (r_node:Rule {citation: row.citation})
  MERGE (v)-[r:VIOLATES_RULE]->(r_node)
  SET r.severity = row.severity,
      r.severity_weight = CASE row.severity
                            WHEN 'Critical' THEN 1.0
                            WHEN 'High' THEN 0.75
                            WHEN 'Medium' THEN 0.5
                            WHEN 'Low' THEN 0.25
                            ELSE 0.5
                          END,
      r.date_occurred = row.date_occurred,
      r.weight = CASE row.severity
                   WHEN 'Critical' THEN 1.0
                   WHEN 'High' THEN 0.75
                   WHEN 'Medium' THEN 0.5
                   WHEN 'Low' THEN 0.25
                   ELSE 0.5
                 END
} IN TRANSACTIONS OF 5000 ROWS;

// ----------------------------------------------------------------------------
// EDGE 10: COMMITTED_BY (Violation → Judge)
// ----------------------------------------------------------------------------

:auto LOAD CSV WITH HEADERS FROM 'file:///rel_committed_by.csv' AS row
CALL { WITH row
  MATCH (v:Violation {violation_id: row.violation_id})
  MATCH (j:Judge {name: row.judge_name})
  MERGE (v)-[r:COMMITTED_BY]->(j)
  SET r.date = row.date_occurred,
      r.weight = 1.0
} IN TRANSACTIONS OF 5000 ROWS;

// ----------------------------------------------------------------------------
// EDGE 11: EVIDENCE_IN_LANE (Evidence → Lane)
// ----------------------------------------------------------------------------

:auto LOAD CSV WITH HEADERS FROM 'file:///rel_evidence_in_lane.csv' AS row
CALL { WITH row
  MATCH (e:Evidence {id: row.evidence_id})
  MATCH (l:Lane {lane_id: row.lane_id})
  MERGE (e)-[r:EVIDENCE_IN_LANE]->(l)
  SET r.weight = 1.0
} IN TRANSACTIONS OF 5000 ROWS;

// ----------------------------------------------------------------------------
// EDGE 12: OCCURRED_ON (Event → Lane)
// ----------------------------------------------------------------------------

:auto LOAD CSV WITH HEADERS FROM 'file:///rel_occurred_on.csv' AS row
CALL { WITH row
  MATCH (ev:Event {event_id: row.event_id})
  MATCH (l:Lane {lane_id: row.lane_id})
  MERGE (ev)-[r:OCCURRED_ON]->(l)
  SET r.weight = 1.0
} IN TRANSACTIONS OF 5000 ROWS;

// ----------------------------------------------------------------------------
// EDGE 13: TESTIFIED_ABOUT (Witness → Evidence)
// ----------------------------------------------------------------------------

:auto LOAD CSV WITH HEADERS FROM 'file:///rel_testified_about.csv' AS row
CALL { WITH row
  MATCH (w:Witness {name: row.witness_name})
  MATCH (e:Evidence {id: row.evidence_id})
  MERGE (w)-[r:TESTIFIED_ABOUT]->(e)
  SET r.context = row.context,
      r.weight = 1.0
} IN TRANSACTIONS OF 5000 ROWS;

// ----------------------------------------------------------------------------
// EDGE 14: CO_CITED_WITH (Rule → Rule) — undirected semantic
// Only create one direction to avoid double-counting in queries
// ----------------------------------------------------------------------------

:auto LOAD CSV WITH HEADERS FROM 'file:///rel_co_cited_with.csv' AS row
CALL { WITH row
  MATCH (r1:Rule {citation: row.citation_1})
  MATCH (r2:Rule {citation: row.citation_2})
  WHERE r1.citation < r2.citation  // Prevent duplicate undirected edges
  MERGE (r1)-[r:CO_CITED_WITH]->(r2)
  SET r.co_citation_count = CASE WHEN row.co_citation_count IS NOT NULL
                                 THEN toInteger(row.co_citation_count) ELSE 1 END,
      r.weight = CASE WHEN row.co_citation_count IS NOT NULL
                      THEN toFloat(row.co_citation_count) / 10.0 ELSE 0.1 END
} IN TRANSACTIONS OF 5000 ROWS;

// ----------------------------------------------------------------------------
// EDGE 15: FILING_USES_EVIDENCE (Filing → Evidence)
// ----------------------------------------------------------------------------

:auto LOAD CSV WITH HEADERS FROM 'file:///rel_filing_uses_evidence.csv' AS row
CALL { WITH row
  MATCH (f:Filing {vehicle_name: row.vehicle_name})
  MATCH (e:Evidence {id: row.evidence_id})
  MERGE (f)-[r:FILING_USES_EVIDENCE]->(e)
  SET r.exhibit_number = row.exhibit_number,
      r.bates_range = row.bates_range,
      r.weight = 1.0
} IN TRANSACTIONS OF 5000 ROWS;

// ============================================================================
// VERIFICATION QUERIES
// ============================================================================

// Count all relationship types
CALL db.relationshipTypes() YIELD relationshipType
CALL apoc.cypher.run(
  'MATCH ()-[r:`' + relationshipType + '`]->() RETURN count(r) AS count', {}
) YIELD value
RETURN relationshipType, value.count AS edgeCount
ORDER BY edgeCount DESC;

// Verify graph connectivity — find isolated nodes (should be minimal)
MATCH (n)
WHERE NOT (n)--()
RETURN labels(n)[0] AS label, count(n) AS isolated_count
ORDER BY isolated_count DESC;

// Lane distribution summary
MATCH (l:Lane)<-[:BELONGS_TO_LANE]-(c:Case)
OPTIONAL MATCH (l)<-[:EVIDENCE_IN_LANE]-(e:Evidence)
OPTIONAL MATCH (l)<-[:OCCURRED_ON]-(ev:Event)
RETURN l.lane_id AS lane,
       l.name AS name,
       count(DISTINCT c) AS cases,
       count(DISTINCT e) AS evidence,
       count(DISTINCT ev) AS events
ORDER BY l.lane_id;

// Top connected nodes (graph hubs)
MATCH (n)
WITH n, labels(n)[0] AS label, size([(n)--() | 1]) AS degree
WHERE degree > 5
RETURN label,
       COALESCE(n.name, n.case_number, n.vehicle_name, n.citation, n.claim_id, n.id) AS identifier,
       degree
ORDER BY degree DESC
LIMIT 25;

// Violation → Rule → Filing chain (McNeill accountability path)
MATCH path = (v:Violation)-[:COMMITTED_BY]->(j:Judge)-[:JUDGE_PRESIDES]->(c:Case)<-[:FILED_IN_CASE]-(f:Filing)
RETURN v.violation_type, j.name, c.case_number, f.vehicle_name, f.readiness_score
ORDER BY f.readiness_score DESC
LIMIT 20;

// Evidence strength by lane
MATCH (e:Evidence)-[:EVIDENCE_IN_LANE]->(l:Lane)
RETURN l.lane_id AS lane,
       l.name AS lane_name,
       count(e) AS evidence_count,
       avg(e.relevance_score) AS avg_relevance,
       max(e.relevance_score) AS max_relevance
ORDER BY l.lane_id;
