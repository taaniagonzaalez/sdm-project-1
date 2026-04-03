
## QUERY 3:
```markdown
```cypher
MATCH (j:Journal)<-[:PART_OF]-(v:Volume)<-[:PUBLISHED_AT]-(p:Paper)
OPTIONAL MATCH (citing_paper:Paper)-[:CITES]->(p)
WITH j, count(DISTINCT p) AS total_papers, count(citing_paper) AS total_citations
RETURN j.name AS Journal, 
       total_papers AS Num_Articulos, 
       total_citations AS Total_Citas,
       toFloat(total_citations) / total_papers AS Impact_Factor_Calculado
ORDER BY Impact_Factor_Calculado DESC;
````

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

