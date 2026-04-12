To use these, ensure you have the GDS plugin installed and a projection created.

1. PageRank
In the context of research, PageRank identifies the most "influential" papers. Unlike a simple citation count, PageRank considers the prestige of the citing paper. A paper cited by a "landmark" paper receives a higher score than one cited by an obscure paper.


// 1. Create a projection of the graph
CALL gds.graph.project('citationsGraph', 'Paper', 'CITES');

// 2. Run PageRank
CALL gds.pageRank.stream('citationsGraph')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).title AS Paper, score
ORDER BY score DESC LIMIT 10;
Interpretation: The result provides a list of papers ordered by their importance. High scores indicate "authoritative" papers that serve as the foundation for the community's knowledge.

2. Louvain
This algorithm identifies clusters of papers that cite each other more frequently than they cite the rest of the graph. In our domain, this reveals "Sub-disciplines" (e.g., a cluster for "Graph Databases" and another for "Relational Optimization") that might not be explicitly labeled by keywords but emerge from the citation patterns.

// 1. Run Louvain and write the community ID back to the nodes
CALL gds.louvain.write('citationsGraph', { writeProperty: 'communityId' })
YIELD communityCount, modularity;

// 2. View sizes of discovered communities
MATCH (p:Paper)
RETURN p.communityId, count(p) AS Size
ORDER BY Size DESC;

This identifies hidden structures. If a large community emerges, it suggests a dense research field. If an author's papers are all in the same community, they are specialized; if they span multiple communities, they are multidisciplinary.