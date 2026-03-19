// Neo4j LOAD CSV starter (adjust file URLs)
//
// :param nodes => 'file:///ORDERGRAPH_NODES.csv';
// :param edges => 'file:///ORDERGRAPH_EDGES.csv';
//
// LOAD CSV WITH HEADERS FROM $nodes AS row
// MERGE (n:Node {node_id: row.node_id})
// SET n += row;
//
// LOAD CSV WITH HEADERS FROM $edges AS row
// MATCH (a:Node {node_id: row.src_node_id})
// MATCH (b:Node {node_id: row.dst_node_id})
// CALL apoc.create.relationship(a, row.type, row, b) YIELD rel
// RETURN count(rel);
