from neo4j import GraphDatabase
import os
from config import S2_API_KEY # Asegúrate de que esto esté en tu config.py

# Credenciales de Neo4j
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "12345678") 

class Neo4jLoader:
    def __init__(self, uri, auth):
        self.driver = GraphDatabase.driver(uri, auth=auth)
        # Detectar ruta absoluta para que funcione en cualquier PC del equipo
        current_dir = os.getcwd()
        base_path = os.path.join(current_dir, "graph_csv")
        clean_path = base_path.replace("\\", "/")
        self.csv_path = f"file:///{clean_path}/"
        print(f"Ruta de carga detectada: {self.csv_path}")

    def close(self):
        self.driver.close()

    def run_query(self, query, message=None):
        with self.driver.session() as session:
            if message: print(f"  > {message}")
            session.run(query)

    def clean_db(self):
        print("Wiping existing data and constraints...")
        with self.driver.session() as session:
            # Borrar todos los datos
            session.run("MATCH (n) DETACH DELETE n")
            # Borrar todas las restricciones existentes
            result = session.run("SHOW CONSTRAINTS")
            for record in result:
                session.run(f"DROP CONSTRAINT {record['name']}")

    def setup_constraints(self):
        print("Setting up unique constraints...")
        # Definimos las claves únicas según tu esquema para evitar duplicados
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Paper) REQUIRE p.paper_id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Author) REQUIRE a.author_id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (o:Organization) REQUIRE o.org_id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Topic) REQUIRE t.topic_id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (r:Review) REQUIRE r.review_id IS UNIQUE"
        ]
        for c in constraints:
            self.run_query(c)

    def load_data(self):
        print("Starting FULL LOAD CSV process...")

        # 1. CARGA DE NODOS (Entidades)
        nodos = {
            "papers.csv": "CREATE (:Paper {paper_id: row.paper_id, title: row.title, doi: row.doi, num_pages: toInteger(row.num_pages), abstract_summary: row.abstract_summary, year_published: toInteger(row.year_published)})",
            "authors.csv": "CREATE (:Author {author_id: row.author_id, name: row.name, orcid: row.orcid})",
            "topics.csv": "CREATE (:Topic {topic_id: row.topic_id, name: row.name, area: row.area})",
            "organizations.csv": "CREATE (:Organization {org_id: row.org_id, name: row.name, type: row.type})",
            "conferences.csv": "CREATE (:Conference {conference_id: row.conference_id, name: row.name, acronym: row.acronym, ranking: row.ranking})",
            "workshops.csv": "CREATE (:Workshop {workshop_id: row.workshop_id, name: row.name, acronym: row.acronym})",
            "journals.csv": "CREATE (:Journal {journal_id: row.journal_id, name: row.name, issn: row.issn, impact_factor: toFloat(row.impact_factor)})",
            "editions.csv": "CREATE (:Edition {edition_id: row.edition_id, number: toInteger(row.number), start_date: row.start_date, end_date: row.end_date})",
            "volumes.csv": "CREATE (:Volume {volume_node_id: row.volume_node_id, volume_id: row.volume_id, issue_number: row.issue_number})",
            "proceedings.csv": "CREATE (:Proceedings {proceedings_id: row.proceedings_id, title: row.title, publisher: row.publisher})",
            "years.csv": "CREATE (:Year {year_id: row.year_id, value: toInteger(row.value)})",
            "cities.csv": "CREATE (:City {city_id: row.city_id, name: row.name, country: row.country})",
            "reviews.csv": "CREATE (:Review {review_id: row.review_id, content_description: row.content_description, decision: row.decision})"
        }

        for file, cypher in nodos.items():
            query = f"LOAD CSV WITH HEADERS FROM '{self.csv_path}{file}' AS row {cypher}"
            self.run_query(query, f"Loading {file}...")

        # 2. CARGA DE RELACIONES
        print("Linking nodes (Relationships)...")
        relaciones = [
            # Author WRITES Paper
            f"LOAD CSV WITH HEADERS FROM '{self.csv_path}author_writes.csv' AS row "
            "MATCH (a:Author {author_id: row.author_id}), (p:Paper {paper_id: row.paper_id}) "
            "CREATE (a)-[:WRITES {role: row.role, is_corresponding: toBoolean(row.is_corresponding), author_order: toInteger(row.author_order)}]->(p)",

            # Paper CITES Paper
            f"LOAD CSV WITH HEADERS FROM '{self.csv_path}paper_cites.csv' AS row "
            "MATCH (p1:Paper {paper_id: row.src_paper_id}), (p2:Paper {paper_id: row.dst_paper_id}) "
            "CREATE (p1)-[:CITES {context: row.context, rank_score: toFloat(row.rank_score)}]->(p2)",

            # Paper CONTAINS Topic
            f"LOAD CSV WITH HEADERS FROM '{self.csv_path}paper_has_keyword.csv' AS row "
            "MATCH (p:Paper {paper_id: row.paper_id}), (t:Topic {topic_id: row.topic_id}) "
            "CREATE (p)-[:CONTAINS {relevance_score: toFloat(row.relevance_score)}]->(t)",

            # Author AFFILIATED_WITH Organization
            f"LOAD CSV WITH HEADERS FROM '{self.csv_path}author_affiliated_with.csv' AS row "
            "MATCH (a:Author {author_id: row.author_id}), (o:Organization {org_id: row.org_id}) "
            "CREATE (a)-[:AFFILIATED_WITH]->(o)",

            # Review EVALUATES Paper y Author PROVIDES Review
            f"LOAD CSV WITH HEADERS FROM '{self.csv_path}review_evaluates_paper.csv' AS row "
            "MATCH (r:Review {review_id: row.review_id}), (p:Paper {paper_id: row.paper_id}) "
            "CREATE (r)-[:EVALUATES]->(p)",

            f"LOAD CSV WITH HEADERS FROM '{self.csv_path}author_provides_review.csv' AS row "
            "MATCH (a:Author {author_id: row.author_id}), (r:Review {review_id: row.review_id}) "
            "CREATE (a)-[:PROVIDES]->(r)",

            # Estructura de Publicación (Proceedings, Editions, Venues)
            f"LOAD CSV WITH HEADERS FROM '{self.csv_path}proceedings_belongs_to.csv' AS row "
            "MATCH (pr:Proceedings {proceedings_id: row.proceedings_id}), (e:Edition {edition_id: row.edition_id}) "
            "CREATE (pr)-[:BELONGS_TO]->(e)",

            f"LOAD CSV WITH HEADERS FROM '{self.csv_path}edition_part_of.csv' AS row "
            "MATCH (e:Edition {edition_id: row.edition_id}) "
            "MATCH (p) WHERE (p:Conference AND p.conference_id = row.parent_id) OR (p:Workshop AND p.workshop_id = row.parent_id) "
            "CREATE (e)-[:PART_OF]->(p)",

            f"LOAD CSV WITH HEADERS FROM '{self.csv_path}edition_dated_in.csv' AS row "
            "MATCH (e:Edition {edition_id: row.edition_id}), (y:Year {year_id: row.year_id}) "
            "CREATE (e)-[:DATED_IN]->(y)",

            f"LOAD CSV WITH HEADERS FROM '{self.csv_path}edition_placed_at.csv' AS row "
            "MATCH (e:Edition {edition_id: row.edition_id}), (c:City {city_id: row.city_id}) "
            "CREATE (e)-[:PLACED_AT]->(c)"
        ]

        for q in relaciones:
            self.run_query(q)
        print("Relationships loaded successfully.")

def run_update():
    loader = Neo4jLoader(URI, AUTH)
    try:
        loader.clean_db()
        loader.setup_constraints()
        loader.load_data()
        print("Update complete!")
    finally:
        loader.close()

if __name__ == "__main__":
    run_update()