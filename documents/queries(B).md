## QUERY 1:

MATCH (venue)<-[:PART_OF]-(e:Edition)<-[:BELONGS_TO]-(pr:Proceedings)<-[:PUBLISHED_AT]-(p:Paper)
WHERE venue:Conference OR venue:Workshop
OPTIONAL MATCH (p)<-[:CITES]-(citing:Paper)
WITH venue, p, count(citing) AS citations
ORDER BY venue.name ASC, citations DESC
WITH venue, collect({title: p.title, citations: citations})[0..3] AS top3
RETURN venue.name AS Venue, top3 AS MostCitedPapers


## QUERY 2:

MATCH (a:Author)-[:WRITES]->(p:Paper)-[:PUBLISHED_AT]->(pr:Proceedings)-[:BELONGS_TO]->(e:Edition)-[:PART_OF]->(venue)
WHERE venue:Conference OR venue:Workshop
WITH venue, a, count(DISTINCT e) AS editionsCount
WHERE editionsCount >= 2
RETURN venue.name AS Venue, 
       collect({author: a.name, editions: editionsCount}) AS Community
ORDER BY size(Community) DESC;

## QUERY 3:
MATCH (p:Paper)-[:PUBLISHED_AT]->(v:Volume)-[:PART_OF]->(j:Journal)
OPTIONAL MATCH (citing:Paper)-[:CITES]->(p)
WITH j, count(DISTINCT p) AS total_papers, count(DISTINCT citing) AS total_citations
WHERE total_papers > 0
RETURN j.name AS Journal,
       total_papers AS Num_Articulos,
       total_citations AS Total_Citas,
       1.0 * total_citations / total_papers AS Impact_Factor_Calculado
ORDER BY Impact_Factor_Calculado DESC;

## QUERY 4:
```markdown
```cypher
// 1. Buscamos autores, sus papers y contamos las citas de cada paper
MATCH (a:Author)-[:WRITES]->(p:Paper)
OPTIONAL MATCH (citing:Paper)-[:CITES]->(p)
WITH a, p, count(citing) AS citations_per_paper
ORDER BY a.name, citations_per_paper DESC

// 2. Agrupamos las citas en una lista ordenada de mayor a menor
WITH a, collect(citations_per_paper) AS citations_list

// 3. Filtramos la lista para encontrar el mayor número 'h' donde existan 'h' papers con >= h citas
UNWIND range(1, size(citations_list)) AS rank
WITH a, citations_list, rank
WHERE citations_list[rank-1] >= rank
WITH a, max(rank) AS h_index

// 4. Resultado final
RETURN a.name AS Author, h_index
ORDER BY h_index DESC;
```

