# Proyecto: SDM - Lab Assignment (Property Graphs)

[cite_start]Este proyecto consiste en el diseño, implementación y análisis de una base de datos de grafos utilizando **Neo4j** para el dominio de publicaciones de investigación[cite: 3, 34].

## 🚀 Cómo empezar con Neo4j

Para este laboratorio, es fundamental configurar correctamente el entorno:

1.  [cite_start]**Descarga Neo4j Desktop:** Es la opción recomendada ya que incluye una licencia de desarrollador y permite gestionar plugins fácilmente[cite: 1, 15].
2.  [cite_start]**Instalación del Driver:** El proyecto requiere entregar un programa funcional en **Python** o **Java**[cite: 18, 19].
    * Si usas Python: `pip install neo4j`.
3.  [cite_start]**Plugin GDS:** Para la sección de algoritmos, debes instalar el plugin **Graph Data Science Library** desde la pestaña "Plugins" en Neo4j Desktop[cite: 128, 129].

## 📋 Pasos del Proyecto

[cite_start]El trabajo se divide en cuatro fases principales que deben reflejarse tanto en el código como en el documento PDF de 8 páginas[cite: 23, 24].

### Fase A: Modelado, Carga y Evolución
* [cite_start]**A.1 Modelado:** Diseñar el esquema de grafos (nodos y relaciones) para autores, artículos, conferencias y revistas[cite: 34, 35, 52].
* [cite_start]**A.2 Instanciación:** Cargar datos reales (ej. DBLP o Semantic Scholar) y completar con datos sintéticos mediante `LOAD CSV`[cite: 60, 64, 73].
* [cite_start]**A.3 Evolución:** Modificar el modelo para incluir revisiones de artículos y afiliaciones de autores mediante consultas Cypher[cite: 84, 88, 93].

### Fase B: Consultas (Querying)
[cite_start]Implementar consultas Cypher eficientes para obtener[cite: 97]:
* [cite_start]Top 3 artículos más citados por conferencia[cite: 98].
* [cite_start]Comunidades de autores (4+ ediciones de una conferencia)[cite: 99].
* [cite_start]Factor de impacto de revistas e índice h de autores[cite: 100, 101].

### Fase C: Recomendador
[cite_start]Crear un recomendador de revisores en 4 pasos (consultas consecutivas)[cite: 104, 106]:
1. [cite_start]Definir la comunidad de bases de datos por palabras clave[cite: 109, 113].
2. [cite_start]Identificar conferencias/revistas relacionadas (90% de artículos de la comunidad)[cite: 114, 115].
3. [cite_start]Encontrar los 100 artículos con más citas[cite: 117, 118].
4. [cite_start]Identificar revisores potenciales y "gurus"[cite: 119, 120].

### Fase D: Algoritmos de Grafos
[cite_start]Seleccionar **dos algoritmos** de la librería GDS (ej. PageRank, Louvain, Dijkstra)[cite: 126, 128, 154]:
* [cite_start]Ejecutar las llamadas semánticamente correctas[cite: 154].
* [cite_start]Justificar los resultados y su interpretación desde la perspectiva del dominio de investigación[cite: 155, 156].

## 📦 Entrega
* [cite_start]**Formato:** Un único archivo ZIP llamado `LAB1_Apellido1Apellido2.zip`[cite: 26, 27].
* **Contenido:**
    * [cite_start]Código fuente (Python/Java) para cada ejercicio[cite: 18, 22].
    * [cite_start]Documento `DOC_Apellido1Apellido2.pdf` con las justificaciones y diagramas[cite: 23, 24].