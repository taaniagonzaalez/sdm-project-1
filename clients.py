from typing import List, Optional
from config import SEMANTIC_SCHOLAR_API, DBLP_PUBL_API
from utils import request_json, s2_headers
from neo4j import GraphDatabase


class ErrorImportingData(Exception):
    pass

class ErrorModelling(Exception):
    pass

class SemanticScholarClient:
    def search_papers(self, query: str, limit: int = 20, offset: int = 0) -> List[dict]:
        url = f"{SEMANTIC_SCHOLAR_API}/paper/search"
        fields = ",".join([
            "paperId", "title", "year", "venue", "authors",
            "fieldsOfStudy", "citationCount", "referenceCount"
        ])
        params = {"query": query, "limit": limit, "offset": offset, "fields": fields}
        data = request_json(url, params=params, headers=s2_headers())
        return data.get("data", [])

    def get_paper_details(self, paper_id: str) -> dict:
            url = f"{SEMANTIC_SCHOLAR_API}/paper/{paper_id}"
            # FIX: Removed "pages" from the fields list. 
            # The API will return it inside the "journal" object automatically.
            fields = ",".join([
                "paperId", "externalIds", "title", "abstract", "year",
                "venue", "authors", "authors.externalIds", "authors.affiliations", 
                "fieldsOfStudy", "publicationTypes", "journal", 
                "referenceCount", "citationCount", "publicationDate",
                "references.paperId", "references.title",
                "citations.paperId", "citations.title"
            ])
            params = {"fields": fields}
            return request_json(url, params=params, headers=s2_headers())



class DBLPClient:
    def search_publication_by_title(self, title: str) -> Optional[dict]:
        params = {"q": title, "h": 1, "format": "json"}
        try:
            data = request_json(DBLP_PUBL_API, params=params, sleep=0.2)
            hits = data.get("result", {}).get("hits", {}).get("hit", [])
            if not hits:
                return None
            return hits[0].get("info", {})
        except Exception:
            return None

class GraphTransformerApp:
    def __init__(self, uri, user, password):
        # Initialize the connection to Neo4j
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        # Close the connection when done
        self.driver.close()
    
    def clear_database(self):
        """Wipes the database clean so we can start fresh."""
        with self.driver.session() as session:
            print("Wiping existing database clean...")
            session.run("MATCH (n) DETACH DELETE n")

    def load_initial_data(self):
        """Loads the A.1 model from the generated CSV files."""
        # Ensure all 27 CSV files are in the Neo4j 'import' folder!
        load_queries = [
            # ==========================================
            # 1. LOAD NODES
            # ==========================================
            """
            LOAD CSV WITH HEADERS FROM 'file:///Users/tania_priv/Documents/sdm-project-1/graph_csv/papers.csv' AS row
            MERGE (p:Paper {paper_id: row.paper_id})
            SET p.title = row.title, 
                p.doi = row.doi,
                p.num_pages = toInteger(row.num_pages),
                p.abstract_summary = row.abstract_summary,
                p.year_published = toInteger(row.year_published);
            """,
            """
            LOAD CSV WITH HEADERS FROM 'file:///Users/tania_priv/Documents/sdm-project-1/graph_csv/authors.csv' AS row
            MERGE (a:Author {author_id: row.author_id})
            SET a.name = row.name,
                a.orcid = row.orcid;
            """,
            """
            LOAD CSV WITH HEADERS FROM 'file:///Users/tania_priv/Documents/sdm-project-1/graph_csv/organizations.csv' AS row
            MERGE (o:Organization {org_id: row.org_id})
            SET o.name = row.name,
                o.type = row.type;
            """,
            """
            LOAD CSV WITH HEADERS FROM 'file:///Users/tania_priv/Documents/sdm-project-1/graph_csv/topics.csv' AS row
            MERGE (t:Topic {topic_id: row.topic_id})
            SET t.name = row.name,
                t.area = row.area;
            """,
            """
            LOAD CSV WITH HEADERS FROM 'file:///Users/tania_priv/Documents/sdm-project-1/graph_csv/years.csv' AS row
            MERGE (y:Year {year_id: row.year_id})
            SET y.value = toInteger(row.value);
            """,
            """
            LOAD CSV WITH HEADERS FROM 'file:///Users/tania_priv/Documents/sdm-project-1/graph_csv/cities.csv' AS row
            MERGE (c:City {city_id: row.city_id})
            SET c.name = row.name,
                c.country = row.country;
            """,
            """
            LOAD CSV WITH HEADERS FROM 'file:///Users/tania_priv/Documents/sdm-project-1/graph_csv/editions.csv' AS row
            MERGE (e:Edition {edition_id: row.edition_id})
            SET e.number = toInteger(row.number),
                e.start_date = row.start_date,
                e.end_date = row.end_date;
            """,
            """
            LOAD CSV WITH HEADERS FROM 'file:///Users/tania_priv/Documents/sdm-project-1/graph_csv/proceedings.csv' AS row
            MERGE (pr:Proceedings {proceedings_id: row.proceedings_id})
            SET pr.title = row.title,
                pr.publisher = row.publisher;
            """,
            """
            LOAD CSV WITH HEADERS FROM 'file:///Users/tania_priv/Documents/sdm-project-1/graph_csv/volumes.csv' AS row
            MERGE (v:Volume {volume_node_id: row.volume_node_id})
            SET v.volume_id = row.volume_id,
                v.issue_number = row.issue_number;
            """,
            """
            LOAD CSV WITH HEADERS FROM 'file:///Users/tania_priv/Documents/sdm-project-1/graph_csv/journals.csv' AS row
            MERGE (j:Journal {journal_id: row.journal_id})
            SET j.name = row.name,
                j.issn = row.issn,
                j.impact_factor = toFloat(row.impact_factor);
            """,
            """
            LOAD CSV WITH HEADERS FROM 'file:///Users/tania_priv/Documents/sdm-project-1/graph_csv/conferences.csv' AS row
            MERGE (conf:Conference {conference_id: row.conference_id})
            SET conf.name = row.name,
                conf.acronym = row.acronym,
                conf.ranking = row.ranking;
            """,
            """
            LOAD CSV WITH HEADERS FROM 'file:///Users/tania_priv/Documents/sdm-project-1/graph_csv/workshops.csv' AS row
            MERGE (w:Workshop {workshop_id: row.workshop_id})
            SET w.name = row.name,
                w.acronym = row.acronym;
            """,
            """
            LOAD CSV WITH HEADERS FROM 'file:///Users/tania_priv/Documents/sdm-project-1/graph_csv/reviews.csv' AS row
            MERGE (rev:Review {review_id: row.review_id})
            SET rev.content_description = row.content_description,
                rev.decision = row.decision;
            """,

            # ==========================================
            # 2. LOAD RELATIONSHIPS
            # ==========================================
            """
            LOAD CSV WITH HEADERS FROM 'file:///Users/tania_priv/Documents/sdm-project-1/graph_csv/paper_cites.csv' AS row
            MATCH (src:Paper {paper_id: row.src_paper_id})
            MATCH (dst:Paper {paper_id: row.dst_paper_id})
            MERGE (src)-[:CITES {context: row.context, rank_score: toFloat(row.rank_score)}]->(dst);
            """,
            """
            LOAD CSV WITH HEADERS FROM 'file:///Users/tania_priv/Documents/sdm-project-1/graph_csv/paper_has_keyword.csv' AS row
            MATCH (p:Paper {paper_id: row.paper_id})
            MATCH (t:Topic {topic_id: row.topic_id})
            MERGE (p)-[:HAS_KEYWORD {relevance_score: toFloat(row.relevance_score)}]->(t);
            """,
            """
            LOAD CSV WITH HEADERS FROM 'file:///Users/tania_priv/Documents/sdm-project-1/graph_csv/paper_published_in_proceedings.csv' AS row 
            MATCH (p:Paper {paper_id: row.paper_id}), (pr:Proceedings {proceedings_id: row.proceedings_id}) 
            MERGE (p)-[r:PUBLISHED_IN_PROCEEDINGS]->(pr) 
            SET r.pages = row.pages;
            """,
            """
            LOAD CSV WITH HEADERS FROM 'file:///Users/tania_priv/Documents/sdm-project-1/graph_csv/paper_published_in_volume.csv' AS row 
            MATCH (p:Paper {paper_id: row.paper_id}), (v:Volume {volume_node_id: row.volume_id}) 
            MERGE (p)-[r:PUBLISHED_IN_VOLUME]->(v) 
            SET r.pages = row.pages;
            """,
            """
            LOAD CSV WITH HEADERS FROM 'file:///Users/tania_priv/Documents/sdm-project-1/graph_csv/author_writes.csv' AS row
            MATCH (a:Author {author_id: row.author_id})
            MATCH (p:Paper {paper_id: row.paper_id})
            MERGE (a)-[:WRITES {
                role: row.role, 
                is_corresponding: row.is_corresponding = 'True', 
                author_order: toInteger(row.author_order)
            }]->(p);
            """,
            """
            LOAD CSV WITH HEADERS FROM 'file:///Users/tania_priv/Documents/sdm-project-1/graph_csv/author_provides_review.csv' AS row
            MATCH (a:Author {author_id: row.author_id})
            MATCH (rev:Review {review_id: row.review_id})
            MERGE (a)-[:PROVIDES_REVIEW]->(rev);
            """,
            """
            LOAD CSV WITH HEADERS FROM 'file:///Users/tania_priv/Documents/sdm-project-1/graph_csv/review_evaluates_paper.csv' AS row
            MATCH (rev:Review {review_id: row.review_id})
            MATCH (p:Paper {paper_id: row.paper_id})
            MERGE (rev)-[:EVALUATES_PAPER]->(p);
            """,
            """
            LOAD CSV WITH HEADERS FROM 'file:///Users/tania_priv/Documents/sdm-project-1/graph_csv/proceedings_belongs_to.csv' AS row
            MATCH (pr:Proceedings {proceedings_id: row.proceedings_id})
            MATCH (e:Edition {edition_id: row.edition_id})
            MERGE (pr)-[:BELONGS_TO]->(e);
            """,
            """
            LOAD CSV WITH HEADERS FROM 'file:///Users/tania_priv/Documents/sdm-project-1/graph_csv/edition_part_of.csv' AS row
            WITH row WHERE row.parent_label = 'Conference'
            MATCH (e:Edition {edition_id: row.edition_id})
            MATCH (c:Conference {conference_id: row.parent_id})
            MERGE (e)-[:PART_OF]->(c);
            """,
            """
            LOAD CSV WITH HEADERS FROM 'file:///Users/tania_priv/Documents/sdm-project-1/graph_csv/edition_part_of.csv' AS row
            WITH row WHERE row.parent_label = 'Workshop'
            MATCH (e:Edition {edition_id: row.edition_id})
            MATCH (w:Workshop {workshop_id: row.parent_id})
            MERGE (e)-[:PART_OF]->(w);
            """,
            """
            LOAD CSV WITH HEADERS FROM 'file:///Users/tania_priv/Documents/sdm-project-1/graph_csv/edition_held_in.csv' AS row
            MATCH (e:Edition {edition_id: row.edition_id})
            MATCH (c:City {city_id: row.city_id})
            MERGE (e)-[:HELD_IN]->(c);
            """,
            """
            LOAD CSV WITH HEADERS FROM 'file:///Users/tania_priv/Documents/sdm-project-1/graph_csv/edition_dated_in.csv' AS row
            MATCH (e:Edition {edition_id: row.edition_id})
            MATCH (y:Year {year_id: row.year_id})
            MERGE (e)-[:DATED_IN]->(y);
            """,
            """
            LOAD CSV WITH HEADERS FROM 'file:///Users/tania_priv/Documents/sdm-project-1/graph_csv/volume_part_of.csv' AS row
            MATCH (v:Volume {volume_node_id: row.volume_id})
            MATCH (j:Journal {journal_id: row.journal_id})
            MERGE (v)-[:PART_OF]->(j);
            """,
            """
            LOAD CSV WITH HEADERS FROM 'file:///Users/tania_priv/Documents/sdm-project-1/graph_csv/volume_dated_in.csv' AS row
            MATCH (v:Volume {volume_node_id: row.volume_id})
            MATCH (y:Year {year_id: row.year_id})
            MERGE (v)-[:DATED_IN]->(y);
            """
        ]

        with self.driver.session() as session:
            for i, query in enumerate(load_queries, 1):
                print(f"Loading CSV data... Query {i}/{len(load_queries)}")
                try:
                    session.run(query)
                except Exception as e:
                    print(f"Error executing Query {i}:\n{e}")
                    raise ErrorImportingData(e)
                    
            print("Initial A.1 data loaded successfully!")

    def run_transformation_a3(self):
            # Cada string en esta lista debe ser UNA SOLA instrucción de Cypher
            queries = [
                # 1. Transformación de Reviews: Separar el autor de la review
                """
                MATCH (a:Author)-[r:PROVIDES_REVIEW]->(rev:Review)
                MERGE (a)-[:SUBMITTED]->(rev)
                """,
                
                # 2. Transformación de Reviews: Conectar la review con el paper
                """
                MATCH (rev:Review)-[r:EVALUATES_PAPER]->(p:Paper)
                MERGE (rev)-[:REVIEWS]->(p)
                """,

                # 3. Borrar relaciones antiguas (Aislado para evitar el error de '2 statements')
                """
                MATCH (a:Author)-[r:PROVIDES_REVIEW]->(rev:Review)-[r2:EVALUATES_PAPER]->(p:Paper)
                DELETE r, r2
                """,
                
                # 4. Transformación de Afiliaciones (Usando funciones nativas para evitar error de APOC)
                """
                MATCH (a:Author)
                WHERE a.affiliation IS NOT NULL
                MERGE (o:Organization {name: a.affiliation_name})
                ON CREATE SET 
                    o.org_id = "org_" + replace(toLower(a.affiliation), " ", "_"),
                    o.type = CASE 
                        WHEN toLower(a.affiliation) CONTAINS "university" THEN "University" 
                        ELSE "Company" 
                    END
                """,

                # 5. Crear la relación de afiliación
                """
                MATCH (a:Author), (o:Organization)
                WHERE a.affiliation = o.name
                MERGE (a)-[:AFFILIATED_WITH]->(o)
                """,

                # 6. Limpieza de propiedad antigua
                """
                MATCH (a:Author) WHERE a.affiliation IS NOT NULL
                REMOVE a.affiliation_name
                """,

                # 7. Unificación de publicaciones (Proceedings)
                """
                MATCH (p:Paper)-[r:PUBLISHED_IN_PROCEEDINGS]->(pr:Proceedings)
                MERGE (p)-[nr:PUBLISHED_AT]->(pr) SET nr.pages = r.pages DELETE r
                """,

                # 8. Unificación de publicaciones (Volumes)
                """
                MATCH (p:Paper)-[r:PUBLISHED_IN_VOLUME]->(v:Volume)
                MERGE (p)-[nr:PUBLISHED_AT]->(v) SET nr.pages = r.pages DELETE r
                """
            ]

            with self.driver.session() as session:
                for i, query in enumerate(queries, 1):
                    # Limpiamos espacios en blanco innecesarios
                    clean_query = query.strip()
                    if not clean_query: continue
                    
                    print(f"Executing Transformation Step {i}/{len(queries)}...")
                    try:
                        session.run(clean_query)
                    except Exception as e:
                        print(f"Error in step {i}")
                        raise ErrorModelling(e)

            print("A.3 Model Transformation Complete!")