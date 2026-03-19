// NUCLEUS APEX - Offline import snippets (generated)
// Place CSV files into Neo4j import directory and use file:/// URLs.

// 1) Bloom TOC headings
LOAD CSV WITH HEADERS FROM 'file:///bloom_toc_full.csv' AS row
MERGE (h:TOC_Heading {idx: toInteger(row.idx)})
SET h.level = toInteger(row.level),
    h.title = row.title,
    h.source_file = 'ETERNAL_BLOOM_MAX_(2) (1).html',
    h.ts = '20260208_2124';

// 1b) NEXT edges (example pattern; run after headings exist)
// MATCH (h:TOC_Heading) MATCH (h2:TOC_Heading {idx:h.idx+1}) MERGE (h)-[:NEXT]->(h2);

// 2) Contradiction map rows
LOAD CSV WITH HEADERS FROM 'file:///CONTRADICTION_MAP.csv' AS row
MERGE (c:Contradiction {cm_id: row.cm_id})
SET c.type = row.type, c.status = row.status, c.pin = row.pin, c.note = row.note, c.ts = '20260208_2124';

// 3) Transcript EvidenceAtom import (recommended): generate transcript_pages.csv (page + integrityKey + excerpt) then MERGE EvidenceAtom