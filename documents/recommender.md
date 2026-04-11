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



Justificación del Diseño: Evolución del Grafo para Detección de Comunidades (Ejercicio C)
El objetivo de este conjunto de consultas es evolucionar el modelo de datos (Property Graph) para identificar de manera inteligente a los expertos y "gurús" de un dominio de investigación específico (en este caso, Bases de Datos). Para ello, se ha optado por un diseño por fases que materializa resultados intermedios a través de nuevas relaciones, lo cual optimiza el rendimiento y enriquece semánticamente el grafo.

A continuación, se detalla la justificación de cada paso del diseño:

1. Definición y Materialización de la Comunidad (Step 1)
En lugar de filtrar los artículos por sus palabras clave en cada consulta repetidamente, hemos decidido tratar la "Comunidad" como una entidad de primera clase creando el nodo (:Community {name: 'Database'}).

Justificación: Al crear la relación explícita (Paper)-[:BELONGS_TO_COMMUNITY]->(Community), transformamos una búsqueda de propiedades de texto (costosa a gran escala) en un simple recorrido de grafo (traversal). Esto sienta las bases para que los siguientes algoritmos operen de manera eficiente basándose en la topología del grafo en lugar de en los atributos de los nodos.

2. Identificación de Medios de Publicación Afines (Step 2)
El objetivo aquí es encontrar los focos de publicación (en este caso, Volumes y Proceedings) que son "puros" o altamente dedicados a esta temática.

Justificación del salto variable (*1..3): Dado que nuestro modelo A.3 tiene jerarquías de publicación complejas, el uso de saltos variables garantiza que capturamos los artículos independientemente de si la estructura intermedia varía.

Justificación de la métrica (Threshold del 90%): Se agrupan todos los artículos que llegan a un mismo medio (WITH venue... count(DISTINCT p)) y se evalúa la proporción de artículos de la comunidad. Si es mayor o igual al 90%, se asume que el medio es un nicho de la base de datos. Guardar esto con [:RELATED_TO_COMMUNITY] evita tener que recalcular este costoso umbral estadístico en las consultas futuras.

3. Detección de los Artículos Más Influyentes (Step 3)
La métrica de impacto convencional (contar todas las citas de un artículo) puede estar sesgada si un artículo es popular en otras áreas. Este paso refina la métrica de calidad midiendo únicamente el impacto intra-comunidad.

Justificación: Al forzar que el nodo citante (db_paper) tenga la relación [:BELONGS_TO_COMMUNITY], estamos evaluando el prestigio del artículo estrictamente dentro de su nicho (Bases de Datos). Ordenar estas citas de forma descendente y limitar el resultado a 100 nos permite etiquetar a la "élite" de la investigación mediante la relación [:IS_TOP_100_OF].

4. Clasificación de Autores: Revisores y Gurús (Step 4)
El paso final transfiere el prestigio de los artículos (Top 100) a sus creadores, categorizándolos en dos niveles jerárquicos de conocimiento.

Justificación: Si un autor ha escrito un artículo de la élite, automáticamente se le cualifica como revisor potencial ([:POTENTIAL_REVIEWER_FOR]). Sin embargo, para identificar a los verdaderos líderes intelectuales ("gurús"), se exige consistencia: haber publicado al menos dos artículos en el Top 100.

Técnica Cypher: La utilización de la estructura FOREACH (ignoreMe IN CASE WHEN ...) actúa como un bloque condicional (IF) nativo en Cypher, permitiendo crear la relación de élite [:IS_GURU_OF] en la misma transacción sin necesidad de realizar una consulta separada, optimizando así las operaciones de escritura en Neo4j.

Conclusión del Diseño:
Este diseño de 4 pasos transforma los datos brutos bibliográficos en conocimiento accionable. Hemos pasado de tener simples artículos y conferencias a poseer un subgrafo fuertemente conectado que nos responde de manera inmediata quiénes son las personas más capacitadas para evaluar el trabajo de otros en un área concreta.