import pandas as pd
from pathlib import Path
import random

class GraphBuilder:
    def __init__(self):
        # Nodos
        self.papers, self.authors, self.topics = [], [], []
        self.organizations, self.reviews = [], []
        self.conferences, self.workshops, self.journals = [], [], []
        self.editions, self.volumes, self.proceedings = [], [], []
        self.years, self.cities = [], []

        # Relaciones
        self.author_writes = []
        self.paper_cites = []
        self.paper_has_keyword = []
        self.author_affiliated_with = []
        self.review_evaluates_paper = []
        self.author_provides_review = []
        self.proceedings_belongs_to = []
        self.edition_part_of = []
        self.edition_dated_in = []
        self.edition_placed_at = []
        self.paper_published_in_proceedings = []
        self.volume_dated_in = []      # (:Volume)-[:DATED_IN]->(:Year)
        self.volume_part_of = []       # (:Volume)-[:PART_OF]->(:Journal)

    def add_paper(self, paper_data):
        p_id = paper_data.get('paperId', f"p_{random.randint(1000,9999)}")
        self.papers.append({
            "paper_id": p_id,
            "title": paper_data.get('title', 'Untitled Paper'),
            "doi": paper_data.get('externalIds', {}).get('DOI', f"10.1000/{p_id}"),
            "num_pages": random.randint(8, 25),
            "abstract_summary": paper_data.get('abstract', 'Generic abstract for graph study.'),
            "year_published": paper_data.get('year', 2024)
        })

        for idx, auth in enumerate(paper_data.get('authors', []), start=1):
            a_id = auth.get('authorId', f"a_{random.randint(100,999)}")
            self.authors.append({
                "author_id": a_id,
                "name": auth.get('name', 'Anonymous Author'),
                "orcid": f"0000-000-{random.randint(1000,9999)}"
            })
            self.author_writes.append({
                "author_id": a_id, "paper_id": p_id,
                "role": "main" if idx == 1 else "co-author",
                "is_corresponding": idx == 1, "author_order": idx
            })
        return p_id

    def enrich_with_synthetic_data(self, paper_id, author_ids):
        import random
        
        # --- TOPICS ---
        topic_list = ["GraphDB", "Cypher", "NoSQL", "BigData"]
        for area in topic_list:
            t_id = f"t_{area.lower()}"
            self.topics.append({"topic_id": t_id, "name": area, "area": "Computer Science"})
            self.paper_has_keyword.append({
                "paper_id": paper_id, "topic_id": t_id, "relevance_score": 0.9
            })

        # --- ORGANIZATIONS ---
        for a_id in author_ids:
            org_id = f"org_{random.randint(1, 3)}"
            self.organizations.append({
                "org_id": org_id, 
                "name": f"Technical University {org_id[-1]}", 
                "type": "University"
            })
            self.author_affiliated_with.append({"author_id": a_id, "org_id": org_id})

        # --- REVIEWS ---
        rev_id = f"rev_{paper_id}"
        self.reviews.append({
            "review_id": rev_id,
            "content_description": "Great contribution to the field.",
            "decision": "Accepted"
        })
        self.review_evaluates_paper.append({"review_id": rev_id, "paper_id": paper_id})
        # Un autor aleatorio (que no sea el del paper) provee la review
        self.author_provides_review.append({"author_id": "auth_external_01", "review_id": rev_id})
        self.authors.append({"author_id": "auth_external_01", "name": "Peer Reviewer", "orcid": "N/A"})

        # --- VENUES (Journal o Conference) ---
        is_journal = random.choice([True, False])
        year_val = random.randint(2020, 2024)
        y_id = f"y_{year_val}"
        self.years.append({"year_id": y_id, "value": year_val})

        if is_journal:
            j_id = "journal_graph_01"
            self.journals.append({"journal_id": j_id, "name": "Journal of Graph Theory", "issn": "000-111", "impact_factor": 5.2})
            vol_id = f"vol_{paper_id}"
            self.volumes.append({"volume_node_id": vol_id, "volume_id": "Vol. 1", "issue_number": "1"})
            self.volume_part_of.append({"volume_node_id": vol_id, "journal_id": j_id})
            self.paper_published_in_proceedings.append({"paper_id": paper_id, "proceedings_id": vol_id})
        else:
            conf_id = "conf_sdm_01"
            self.conferences.append({"conference_id": conf_id, "name": "SDM Conference", "acronym": "SDM", "ranking": "A"})
            edit_id = f"edit_{year_val}"
            self.editions.append({"edition_id": edit_id, "number": year_val - 2000, "start_date": "2024-01-01", "end_date": "2024-01-05"})
            self.edition_part_of.append({"edition_id": edit_id, "parent_id": conf_id, "parent_label": "Conference"})
            self.edition_dated_in.append({"edition_id": edit_id, "year_id": y_id})
            
            proc_id = f"proc_{edit_id}"
            self.proceedings.append({"proceedings_id": proc_id, "title": f"Proceedings {year_val}", "publisher": "ACM"})
            self.proceedings_belongs_to.append({"proceedings_id": proc_id, "edition_id": edit_id})
            self.paper_published_in_proceedings.append({"paper_id": paper_id, "proceedings_id": proc_id})
    def export_all(self, output_dir):
        path = Path(output_dir)
        path.mkdir(parents=True, exist_ok=True)
        
        all_data = {
            "papers": self.papers, "authors": self.authors, "topics": self.topics,
            "organizations": self.organizations, "reviews": self.reviews,
            "conferences": self.conferences, "workshops": self.workshops,
            "journals": self.journals, "editions": self.editions,
            "volumes": self.volumes, "proceedings": self.proceedings,
            "years": self.years, "cities": self.cities,
            "author_writes": self.author_writes, "paper_cites": self.paper_cites,
            "paper_has_keyword": self.paper_has_keyword, 
            "author_affiliated_with": self.author_affiliated_with,
            "review_evaluates_paper": self.review_evaluates_paper, 
            "author_provides_review": self.author_provides_review,
            "proceedings_belongs_to": self.proceedings_belongs_to, 
            "edition_part_of": self.edition_part_of,
            "edition_dated_in": self.edition_dated_in, 
            "edition_placed_at": self.edition_placed_at,
            "paper_published_in_proceedings": self.paper_published_in_proceedings
        }

        for name, data in all_data.items():
            df = pd.DataFrame(data)
            if not df.empty:
                # CRITICO: Eliminar duplicados basados en el ID de cada entidad
                id_col = None
                if "paper_id" in df.columns: id_col = "paper_id"
                elif "author_id" in df.columns: id_col = "author_id"
                elif "org_id" in df.columns: id_col = "org_id"
                elif "topic_id" in df.columns: id_col = "topic_id"
                elif "review_id" in df.columns: id_col = "review_id"
                
                if id_col:
                    df = df.drop_duplicates(subset=[id_col])
                else:
                    df = df.drop_duplicates()
                
                df.to_csv(path / f"{name}.csv", index=False)