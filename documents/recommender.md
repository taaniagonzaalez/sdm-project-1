## STEP 1:

Lo primero que debemos hacer es definir la comunidad de investigación. Asumiremos que la comunidad de bases de datos está definida por una serie de palabras clave específicas, como "data management", "indexing", "data modeling", entre otras.

```markdown
```cypher

// Creamos el nodo de la comunidad y enlazamos los artículos correspondientes.
MERGE (c:Community {name: 'Database'})
WITH c
MATCH (p:Paper)-[:HAS_KEYWORD]->(t:Topic)
WHERE toLower(t.name) IN ['data management', 'indexing', 'data modeling', 'big data', 'data processing', 'data storage', 'data querying']
MERGE (p)-[:BELONGS_TO_COMMUNITY]->(c)
```

## STEP 2:

A continuación, necesitamos encontrar los lugares de publicación relacionados con la comunidad de bases de datos. Asumiremos que un evento es afín si el 90% de los artículos allí publicados contienen alguna de las palabras clave de la comunidad.

```markdown
```cypher

// Calculamos el porcentaje de artículos de la BD sobre el total publicado en cada medio.
MATCH (c:Community {name: 'Database'})
// Buscamos el camino (de entre 1 a 3 saltos) desde el Paper hasta el Venue final
MATCH (p:Paper)-[:PUBLISHED_AT*1..3]->(venue)
WHERE venue:Volume OR venue:Proceedings

// Usamos DISTINCT p por si un paper llegase por múltiples rutas, para no contarlo doble
WITH venue, c, count(DISTINCT p) AS total_papers, sum(CASE WHEN (p)-[:BELONGS_TO_COMMUNITY]->(c) THEN 1 ELSE 0 END) AS db_papers
WHERE total_papers > 0 AND (toFloat(db_papers) / total_papers) >= 0.90

MERGE (venue)-[:RELATED_TO_COMMUNITY]->(c)
```

## STEP 3:

Luego, queremos identificar los artículos principales de estas conferencias, talleres y revistas. Necesitamos encontrar los 100 artículos con el mayor número de citas provenientes de artículos que pertenecen a la comunidad de bases de datos. Como resultado, obtendremos los 100 mejores artículos de esta comunidad

```markdown
```cypher

// Buscamos artículos publicados en los medios identificados en el Paso 2 
// y contamos las citas desde artículos de la comunidad.
MATCH (c:Community {name: 'Database'})
MATCH (venue)-[:RELATED_TO_COMMUNITY]->(c)

MATCH (target_paper:Paper)-[:PUBLISHED_AT*1..2]->(venue)

// Citas que provienen estrictamente de papers de la comunidad
MATCH (db_paper:Paper)-[:BELONGS_TO_COMMUNITY]->(c)
MATCH (db_paper)-[:CITES]->(target_paper)

// Usamos DISTINCT por si las rutas flexibles duplican alguna fila en memoria
WITH target_paper, c, count(DISTINCT db_paper) AS db_citations
ORDER BY db_citations DESC
LIMIT 100

MERGE (target_paper)-[:IS_TOP_100_OF]->(c)
```

## STEP 4: 

Finalmente, cualquier autor de alguno de estos 100 artículos será considerado automáticamente como un buen candidato potencial para revisar artículos. Además, queremos identificar y almacenar a los "gurús", es decir, autores de prestigio que podrían revisar para los mejores eventos o revistas. Un "gurú" se define como el autor de al menos dos de los 100 artículos principales identificados previamente.

```markdown
```cypher

// Conectamos a los autores de los artículos Top-100 con la comunidad y distinguimos a los gurús basándonos en su recuento.
MATCH (c:Community {name: 'Database'})
MATCH (a:Author)-[:WRITES]->(p:Paper)-[:IS_TOP_100_OF]->(c)
WITH a, c, count(p) AS top_papers_count
MERGE (a)-[:POTENTIAL_REVIEWER_FOR]->(c)
FOREACH (ignoreMe IN CASE WHEN top_papers_count >= 2 THEN [1] ELSE [] END |
    MERGE (a)-[:IS_GURU_OF]->(c)
)
```