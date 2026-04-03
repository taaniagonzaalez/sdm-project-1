# A.3. Revisar que esté bien:
// Debería devolver los autores, sus reseñas y el paper asociado
MATCH (a:Author)-[:SUBMITTED]->(rev:Review)-[:REVIEWS]->(p:Paper)
RETURN a.name AS Autor, rev.decision AS Decision, p.title AS Paper
LIMIT 10;

// Verificación de limpieza (Debe devolver 0)
MATCH ()-[r:PROVIDES_REVIEW]-() 
RETURN count(r) AS Relaciones_Antiguas_Restantes;

// Verifica la conexión y los nuevos IDs generados
MATCH (a:Author)-[:AFFILIATED_WITH]->(o:Organization)
RETURN a.name AS Autor, o.name AS Org_Nombre, o.org_id AS ID_Generado, o.type AS Tipo
LIMIT 10;

// Verificación de limpieza de metadatos (Debe devolver 0)
MATCH (a:Author) 
WHERE a.affiliation_name IS NOT NULL 
RETURN count(a) AS Autores_Sin_Limpiar;

// Verifica que ambos tipos de publicaciones ahora usan PUBLISHED_AT
MATCH (p:Paper)-[r:PUBLISHED_AT]->(target)
RETURN p.title AS Paper, 
       labels(target)[0] AS Tipo_Destino, 
       r.pages AS Paginas
LIMIT 10;

// Verificación de limpieza (Debe devolver 0)
MATCH ()-[r:PUBLISHED_IN_PROCEEDINGS]-()
MATCH ()-[r2:PUBLISHED_IN_VOLUME]-()
RETURN count(r) + count(r2) AS Relaciones_Viejas_Activas;

MATCH (p:Paper)<-[:REVIEWS]-(rev:Review)
WITH p, count(rev) AS num_reviews, collect(rev.decision) AS decisiones
WHERE size([d IN decisiones WHERE d = "Accept" OR d = "Accepted"]) > (num_reviews / 2)
RETURN p.title AS Paper_Aceptado, num_reviews AS Total_Reviews, decisiones AS Votos;

CALL db.schema.visualization();