// Load ERD relationships by type (no APOC required)

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'AUTHORIZES'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:AUTHORIZES]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'AVAILABLE_IN'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:AVAILABLE_IN]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'CANDIDATE_FOR'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:CANDIDATE_FOR]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'CHECKLISTED_BY'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:CHECKLISTED_BY]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'CITED_BY_HIT'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:CITED_BY_HIT]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'CONTAINS'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:CONTAINS]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'CONTEXT_FOR'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:CONTEXT_FOR]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'DEFINES_RULE'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:DEFINES_RULE]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'DOCKETS'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:DOCKETS]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'ENDS'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:ENDS]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'ESCALATES_TO'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:ESCALATES_TO]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'EVIDENCE_ATOM_OF'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:EVIDENCE_ATOM_OF]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HAS_ALLEGATION'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HAS_ALLEGATION]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HAS_CHUNK'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HAS_CHUNK]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HAS_DEADLINE'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HAS_DEADLINE]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HAS_DOCKETENTRY'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HAS_DOCKETENTRY]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HAS_EMBEDDING'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HAS_EMBEDDING]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HAS_ENTRY'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HAS_ENTRY]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HAS_EVENT'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HAS_EVENT]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HAS_EXHIBIT'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HAS_EXHIBIT]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HAS_EXTRACTION'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HAS_EXTRACTION]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HAS_FEE'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HAS_FEE]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HAS_FIELD_MAP'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HAS_FIELD_MAP]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HAS_FILING'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HAS_FILING]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HAS_HEARING'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HAS_HEARING]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HAS_IFP'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HAS_IFP]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HAS_INTEGRITYCHECK'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HAS_INTEGRITYCHECK]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HAS_JOB'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HAS_JOB]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HAS_JTC_COMPLAINT'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HAS_JTC_COMPLAINT]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HAS_NOTICE'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HAS_NOTICE]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HAS_OBJECTION'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HAS_OBJECTION]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HAS_OCFL_OBJECT'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HAS_OCFL_OBJECT]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HAS_OOP'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HAS_OOP]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HAS_ORDER'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HAS_ORDER]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HAS_PO'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HAS_PO]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HAS_PO_STATE'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HAS_PO_STATE]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HAS_PRESERVATION_LOG'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HAS_PRESERVATION_LOG]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HAS_PROOF_OBLIGATION'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HAS_PROOF_OBLIGATION]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HAS_QUOTE'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HAS_QUOTE]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HAS_RECORD_CERT'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HAS_RECORD_CERT]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HAS_ROA'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HAS_ROA]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HAS_ROA_ENTRY'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HAS_ROA_ENTRY]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HAS_ROCRATE_ENTITY'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HAS_ROCRATE_ENTITY]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HAS_RUN'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HAS_RUN]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HAS_SEGMENT'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HAS_SEGMENT]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HAS_SERVICE_PROOF'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HAS_SERVICE_PROOF]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HAS_SIGNATURE'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HAS_SIGNATURE]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HAS_STATE'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HAS_STATE]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HAS_SUBPOENA'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HAS_SUBPOENA]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HAS_TRANSCRIPT'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HAS_TRANSCRIPT]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HAS_TRANSCRIPT_REQUEST'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HAS_TRANSCRIPT_REQUEST]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HAS_WITNESS'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HAS_WITNESS]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HEARD_AS'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HEARD_AS]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HEARS'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HEARS]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'HIT_IN'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:HIT_IN]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'INCURS'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:INCURS]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'INPUT_TO'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:INPUT_TO]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'LINKS_TO'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:LINKS_TO]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'MATERIALIZES_AS'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:MATERIALIZES_AS]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'METHOD_USED'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:METHOD_USED]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'OBJECT_OF'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:OBJECT_OF]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'OFFERED_AT'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:OFFERED_AT]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'OUTPUTS'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:OUTPUTS]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'PACKAGED_AS'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:PACKAGED_AS]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'PRODUCES'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:PRODUCES]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'PRODUCES_VALIDATION'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:PRODUCES_VALIDATION]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'REQUIRES_SERVICE'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:REQUIRES_SERVICE]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'RULES_ON'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:RULES_ON]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'SERVED_ON'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:SERVED_ON]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'SERVED_VIA'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:SERVED_VIA]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'SPECIALIZES_AS'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:SPECIALIZES_AS]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'STARTS'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:STARTS]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'SUBJECT_OF'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:SUBJECT_OF]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'SUPPORTED_BY'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:SUPPORTED_BY]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'SUPPORTED_BY_OOP'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:SUPPORTED_BY_OOP]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'SUPPORTS'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:SUPPORTS]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'SUPPORTS_EVENT'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:SUPPORTS_EVENT]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'TARGETS'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:TARGETS]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'TRIGGERS'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:TRIGGERS]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'USED_BY'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:USED_BY]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'USES_FORM'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:USES_FORM]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'USES_PACKET'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:USES_PACKET]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'USES_TEMPLATE'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:USES_TEMPLATE]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'USES_TEMPLATE_IN_PACKET'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:USES_TEMPLATE_IN_PACKET]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;

LOAD CSV WITH HEADERS FROM 'file:///erd_relationships.csv' AS row
WITH row WHERE row.type = 'VALIDATES'
MATCH (a:ERDTable {table_id: row.start_id})
MATCH (b:ERDTable {table_id: row.end_id})
MERGE (a)-[r:VALIDATES]->(b)
SET r.cardinality = row.cardinality,
    r.note = row.note;
