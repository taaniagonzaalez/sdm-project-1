import csv
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from config import MAX_REFERENCES_PER_PAPER, MAX_CITATIONS_PER_PAPER
from utils import clean_text, slugify, safe_int, calculate_num_pages
import random
from faker import Faker
import uuid

# Initialize Faker at the top level
fake = Faker()

class GraphBuilder:
    def __init__(self):
        # Nodes
        self.papers: Dict[str, dict] = {}
        self.authors: Dict[str, dict] = {}
        self.topics: Dict[str, dict] = {}
        self.years: Dict[str, dict] = {}
        self.cities: Dict[str, dict] = {}
        self.editions: Dict[str, dict] = {}
        self.proceedings: Dict[str, dict] = {}
        self.volumes: Dict[str, dict] = {}
        self.journals: Dict[str, dict] = {}
        self.conferences: Dict[str, dict] = {}
        self.workshops: Dict[str, dict] = {}
        self.organizations: Dict[str, dict] = {}
        self.abstracts: Dict[str,dict] = {}

        # Relationships
        self.rel_cites = set()
        self.rel_has_keyword = set()
        self.rel_published_in_proceedings = set()
        self.rel_published_in_volume = set()
        self.rel_edition_part_of = set()
        self.rel_edition_dated_in = set()
        self.rel_edition_held_in = set()
        self.rel_proceedings_belongs_to = set()
        self.rel_volume_dated_in = set()
        self.rel_volume_part_of = set()
        self.rel_writes = set()
        self.rel_affiliated_with = set()
        self.rel_starts_with = set()
        self.rel_reviews = set() # (author_id, paper_id, score, comments, decision)

    def add_year(self, year: Optional[int]) -> Optional[str]:
        if not year:
            return None
        year_id = str(year)
        if year_id not in self.years:
            self.years[year_id] = {"value": year}
        return year_id

    def add_city(self, city_name: str) -> str:
        city_name = clean_text(city_name) or "Unknown City"
        city_id = slugify(city_name)
        if city_id not in self.cities:
            self.cities[city_id] = {"name": city_name, "country": "Unknown Country"}
        return city_id

    def add_organization(self, org_name: str) -> str:
        org_name = clean_text(org_name)
        org_id = slugify(org_name)
        if org_id not in self.organizations:
            self.organizations[org_id] = {"name": org_name, "type": infer_org_type(org_name)}
        return org_id

    def add_topic(self, topic_name: str) -> Optional[str]:
        topic_name = clean_text(topic_name)
        if not topic_name:
            return None
        topic_id = slugify(topic_name)
        if topic_id not in self.topics:
            self.topics[topic_id] = {"name": topic_name, "area": "General Computer Science"}
        return topic_id

    def infer_venue_type(self, paper: dict, dblp_info: Optional[dict]) -> str:
        journal = paper.get("journal")
        pub_types = paper.get("publicationTypes") or []
        venue_name = clean_text(paper.get("venue") or "")

        if journal or any("journal" in str(x).lower() for x in pub_types):
            return "journal"
        dblp_type = str((dblp_info or {}).get("type", "")).lower()
        if "journal" in dblp_type:
            return "journal"
        if "workshop" in venue_name.lower() or "ws" in venue_name.lower():
            return "workshop"
        return "conference"

    def build_publication_container(self, paper: dict, dblp_info: Optional[dict]) -> Tuple[Optional[str], Optional[str]]:
        year = safe_int(paper.get("year"))
        year_id = self.add_year(year)
        venue_name = clean_text(paper.get("venue") or "Unknown Venue")
        journal = paper.get("journal") or {}
        venue_type = self.infer_venue_type(paper, dblp_info)

        if venue_type == "journal":
            journal_name = clean_text(journal.get("name") or venue_name or "Unknown Journal")
            journal_id = slugify(journal_name)
            if journal_id not in self.journals:
                self.journals[journal_id] = {"name": journal_name, "issn": ""}

            volume_name = clean_text(journal.get("volume") or "1")
            volume_id = slugify(f"{journal_name}_vol_{volume_name}_{year or 'unknown'}")
            if volume_id not in self.volumes:
                self.volumes[volume_id] = {"volume_id": volume_name, "issue_number": "1"}

            if year_id:
                self.rel_volume_dated_in.add((volume_id, year_id))
            self.rel_volume_part_of.add((volume_id, journal_id))
            return None, volume_id

        # Conference or Workshop
        container_name = venue_name or "Unknown Event"
        container_id = slugify(container_name)

        if venue_type == "workshop":
            if container_id not in self.workshops:
                self.workshops[container_id] = {"name": container_name, "acronym": container_name[:5].upper()}
        else:
            if container_id not in self.conferences:
                self.conferences[container_id] = {"name": container_name, "acronym": container_name[:5].upper(), "ranking": "A"}

        edition_id = slugify(f"{container_name}_{year or 'unknown'}")
        if edition_id not in self.editions:
            self.editions[edition_id] = {"number": year or 1, "start_date": f"{year}-01-01", "end_date": f"{year}-01-03"}

        proc_id = slugify(f"proc_{container_name}_{year or 'unknown'}")
        if proc_id not in self.proceedings:
            self.proceedings[proc_id] = {"title": f"Proceedings of {container_name} {year or ''}".strip(), "publisher": "IEEE/ACM"}

        if venue_type == "workshop":
            self.rel_edition_part_of.add((edition_id, "Workshop", container_id))
        else:
            self.rel_edition_part_of.add((edition_id, "Conference", container_id))

        if year_id:
            self.rel_edition_dated_in.add((edition_id, year_id))

        city_id = self.add_city("Unknown City")
        self.rel_edition_held_in.add((edition_id, city_id))
        self.rel_proceedings_belongs_to.add((proc_id, edition_id))

        return proc_id, None

    def add_paper(self, paper: dict, dblp_info: Optional[dict] = None):
        paper_id = paper.get("paperId")
        if not paper_id:
            return

        external_ids = paper.get("externalIds") or {}
        doi = external_ids.get("DOI", "")
        title = clean_text(paper.get("title"))
        abstract = clean_text(paper.get("abstract"))
        year = safe_int(paper.get("year"))

        journal_info = paper.get("journal") or {}
        pages_str = clean_text(journal_info.get("pages"))
        num_pages = calculate_num_pages(pages_str)

        if paper_id not in self.papers:
            self.papers[paper_id] = {
                "paper_id": paper_id, "title": title, "doi": doi, 
                "num_pages": num_pages, "abstract_summary": abstract, 
                "year_published": year or ""
            }

        for topic in (paper.get("fieldsOfStudy") or []):
            topic_id = self.add_topic(str(topic))
            if topic_id:
                self.rel_has_keyword.add((paper_id, topic_id, 1.0)) # 1.0 is default relevance_score

        authors = paper.get("authors") or []
        for idx, author in enumerate(authors):
            author_id = author.get("authorId") or slugify(author.get("name", f"unknown_author_{idx}"))
            name = clean_text(author.get("name"))
            ext_ids = author.get("externalIds") or {}
            orcid = ext_ids.get("ORCID", "")
            
            if author_id not in self.authors:
                self.authors[author_id] = {"author_id": author_id, "name": name, "orcid": orcid}
            
            role = "main" if idx == 0 else "co-author"
            is_corresponding = True if idx == 0 else False
            self.rel_writes.add((author_id, paper_id, role, is_corresponding, idx + 1))

            affiliations = author.get("affiliations") or []
            if affiliations:
                org_id = self.add_organization(str(affiliations[0]))
                self.rel_affiliated_with.add((author_id, org_id))

        proceedings_id, volume_id = self.build_publication_container(paper, dblp_info)
        
        if proceedings_id:
            self.rel_published_in_proceedings.add((paper_id, proceedings_id, pages_str))
        if volume_id:
            self.rel_published_in_volume.add((paper_id, volume_id, pages_str))

    def add_citation_edges(self, source_paper_id: str, details: dict):
        for ref in (details.get("references") or [])[:MAX_REFERENCES_PER_PAPER]:
            ref_id = ref.get("paperId")
            if ref_id:
                self.rel_cites.add((source_paper_id, ref_id, "background", 1.0))

        for cit in (details.get("citations") or [])[:MAX_CITATIONS_PER_PAPER]:
            cit_id = cit.get("paperId")
            if cit_id:
                self.rel_cites.add((cit_id, source_paper_id, "background", 1.0))

    def generate_mock_reviews(self):
        """Generates 3 dummy reviews per paper strictly following business logic constraints."""
        all_authors = list(self.authors.keys())
        if len(all_authors) < 4:
            return # Not enough authors in the graph to mock reviews
            
        for paper_id in self.papers.keys():
            # Find authors who wrote this paper so they don't review it
            writers_of_this_paper = {a for (a, p, _, _, _) in self.rel_writes if p == paper_id}
            eligible_reviewers = [a for a in all_authors if a not in writers_of_this_paper]
            
            # Pick 3 random reviewers
            selected_reviewers = random.sample(eligible_reviewers, min(3, len(eligible_reviewers)))
            
            for i, reviewer_id in enumerate(selected_reviewers):
                review_id = f"rev_{paper_id}_{reviewer_id}"
                decision = random.choice(["Accept", "Accept", "Weak Accept", "Reject"])
                content = f"This is a mock review. The methodology was {'solid' if 'Accept' in decision else 'flawed'}."
                
               # Generate a mock score to match A.1 schema
                score = round(random.uniform(1.0, 5.0), 1)
                
                # Add a single Relationship directly (A.1 Model)
                self.rel_reviews.add((reviewer_id, paper_id, score, content, decision))
    
    def generate_synthetic_data(self, scale_multiplier=10):
        print(f"Generando datos sintéticos (multiplicador: x{scale_multiplier})...")

        # 1. FORZAR TEMAS DE BASES DE DATOS (Para el Ejercicio C)
        db_topics = [
            'data management', 'indexing', 'data modeling', 
            'big data', 'data processing', 'data storage', 'data querying'
        ]
        
        for topic_name in db_topics:
            topic_id = slugify(topic_name)
            if topic_id not in self.topics:
                self.topics[topic_id] = {
                    "name": topic_name,
                    "area": "Database Systems"
                }

        # 2. GENERAR OTROS TEMAS ALEATORIOS
        num_random_topics = 5 * scale_multiplier
        for _ in range(num_random_topics):
            topic_name = fake.bs()
            topic_id = slugify(topic_name)
            self.topics[topic_id] = {
                "name": topic_name,
                "area": fake.job()
            }

        # 3. GENERAR AUTORES
        num_authors = 20 * scale_multiplier
        author_ids = []
        for _ in range(num_authors):
            a_name = fake.name()
            a_id = slugify(a_name) + "_" + str(random.randint(100, 999))
            author_ids.append(a_id)
            self.authors[a_id] = {
                "name": a_name,
                "orcid": fake.uuid4(),
                "affiliation": fake.company()
            }

        # 4. GENERAR VENUES (Conferences, Journals, Editions, Proceedings y Volumes)
        num_venues = 3 * scale_multiplier
        proceedings_ids = []
        volume_ids = []

        # Asegurar de forma segura que existe el set para las revistas si no lo creaste explícitamente en init
        if not hasattr(self, 'rel_volume_part_of'):
            self.rel_volume_part_of = set()

        # 4.1 Crear Conferencias, Ediciones y Actas (Proceedings)
        for i in range(num_venues):
            c_id = f"conf_{i}_{slugify(fake.word())}"
            self.conferences[c_id] = {
                "name": fake.catch_phrase().title() + " Conference",
                "acronym": fake.word().upper() + str(random.randint(10, 99)),
                "ranking": random.choice(["A*", "A", "B", "C"])
            }
            
            # 1 a 3 ediciones por conferencia
            for ed in range(random.randint(1, 3)):
                e_id = f"ed_{ed}_{c_id}"
                self.editions[e_id] = {
                    "number": ed + 1,
                    "start_date": str(fake.date_this_decade()),
                    "end_date": str(fake.date_this_decade())
                }
                self.rel_edition_part_of.add((e_id, "Conference", c_id))
                
                pr_id = f"proc_{e_id}"
                proceedings_ids.append(pr_id)
                self.proceedings[pr_id] = {
                    "title": f"Proceedings of {self.conferences[c_id]['acronym']} Vol {ed+1}",
                    "publisher": fake.company()
                }
                self.rel_proceedings_belongs_to.add((pr_id, e_id))

        # 4.2 Crear Journals y Volumes
        for i in range(num_venues):
            j_id = f"journ_{i}_{slugify(fake.word())}"
            self.journals[j_id] = {
                "name": fake.catch_phrase().title() + " Journal",
                "issn": f"{random.randint(1000,9999)}-{random.randint(1000,9999)}",
                "impact_factor": round(random.uniform(0.5, 10.0), 2)
            }
            
            # 1 a 3 volúmenes por revista
            for vol in range(random.randint(1, 3)):
                v_id = f"vol_{vol}_{j_id}"
                volume_ids.append(v_id)
                self.volumes[v_id] = {
                    "volume_id": str(vol + 1),
                    "issue_number": str(random.randint(1, 12))
                }
                self.rel_volume_part_of.add((v_id, j_id))

        # 5. GENERAR PAPERS Y ASIGNAR TOPICS, AUTORES Y VENUES
        num_papers = 50 * scale_multiplier
        all_topic_ids = list(self.topics.keys())
        paper_ids = []

        for _ in range(num_papers):
            p_title = fake.catch_phrase()
            p_id = slugify(p_title) + "_" + str(random.randint(1000, 9999))
            paper_ids.append(p_id)
            
            # Crear el nodo Paper
            self.papers[p_id] = {
                "title": p_title,
                "doi": "10.1000/" + fake.uuid4()[:8],
                "num_pages": random.randint(5, 25),
                "abstract_summary": fake.paragraph(),
                "year_published": random.randint(2010, 2024)
            }

            # Relación: (Paper)-[:CONTAINS]->(Topic)
            chosen_topics = random.sample(all_topic_ids, k=random.randint(1, 3))
            for t_id in chosen_topics:
                relevance = round(random.uniform(0.1, 1.0), 2)
                self.rel_has_keyword.add((p_id, t_id, relevance))

            # Relación: (Author)-[:WRITES]->(Paper)
            chosen_authors = random.sample(author_ids, k=random.randint(1, 4))
            for order, a_id in enumerate(chosen_authors, start=1):
                role = 'main' if order == 1 else 'co-author'
                is_corresponding = (order == 1)
                self.rel_writes.add((a_id, p_id, role, is_corresponding, order))

            # --- NUEVO: Relación de Publicación ---
            # Decidimos si el paper va a un Proceedings (60%) o a un Volume (40%)
            pages_str = f"{random.randint(1, 100)}-{random.randint(101, 200)}"
            if random.random() < 0.6 and proceedings_ids:
                pr_id = random.choice(proceedings_ids)
                self.rel_published_in_proceedings.add((p_id, pr_id, pages_str))
            elif volume_ids:
                v_id = random.choice(volume_ids)
                self.rel_published_in_volume.add((p_id, v_id, pages_str))

        # 6. GENERAR CITAS ENTRE PAPERS (Paper)-[:CITES]->(Paper)
        for p_id in paper_ids:
            num_citations = random.randint(0, 5)
            possible_targets = [pid for pid in paper_ids if pid != p_id]
            
            if possible_targets:
                targets = random.sample(possible_targets, k=min(num_citations, len(possible_targets)))
                for t_id in targets:
                    context = fake.sentence()
                    rank_score = round(random.uniform(0.1, 5.0), 2)
                    self.rel_cites.add((p_id, t_id, context, rank_score))

        print(f"Generación sintética completada. Total de papers: {len(self.papers)}, Total de autores: {len(self.authors)}.")

    def write_csv(self, path: Path, fieldnames: List[str], rows: List[dict], include_id_in_row=False, id_col_name="id"):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for key, data in rows:
                row = data.copy()
                if include_id_in_row:
                    row[id_col_name] = key
                # Only write keys that are in fieldnames
                writer.writerow({k: row.get(k, "") for k in fieldnames})

    def export_all(self, output_dir: Path):
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Make sure reviews are generated before export!
        self.generate_mock_reviews()

        # Nodes (Matched exactly to schema attributes)
        self.write_csv(output_dir / "papers.csv", ["paper_id", "title", "doi", "num_pages", "abstract_summary", "year_published"], self.papers.items(), True, "paper_id")
        self.write_csv(output_dir / "authors.csv", ["author_id", "name", "orcid", "affiliation"], self.authors.items(), True, "author_id")
        self.write_csv(output_dir / "organizations.csv", ["org_id", "name", "type"], self.organizations.items(), True, "org_id")
        self.write_csv(output_dir / "topics.csv", ["topic_id", "name", "area"], self.topics.items(), True, "topic_id")
        self.write_csv(output_dir / "years.csv", ["year_id", "value"], self.years.items(), True, "year_id")
        self.write_csv(output_dir / "cities.csv", ["city_id", "name", "country"], self.cities.items(), True, "city_id")
        self.write_csv(output_dir / "editions.csv", ["edition_id", "number", "start_date", "end_date"], self.editions.items(), True, "edition_id")
        self.write_csv(output_dir / "proceedings.csv", ["proceedings_id", "title", "publisher"], self.proceedings.items(), True, "proceedings_id")
        self.write_csv(output_dir / "volumes.csv", ["volume_node_id", "volume_id", "issue_number"], self.volumes.items(), True, "volume_node_id")
        self.write_csv(output_dir / "journals.csv", ["journal_id", "name", "issn"], self.journals.items(), True, "journal_id")
        self.write_csv(output_dir / "conferences.csv", ["conference_id", "name", "acronym", "ranking"], self.conferences.items(), True, "conference_id")
        self.write_csv(output_dir / "workshops.csv", ["workshop_id", "name", "acronym"], self.workshops.items(), True, "workshop_id")
        self.write_csv(output_dir / "abstracts.csv", ["abstract_id", "content", "word_count"], self.abstracts.items(), True, "abstract_id")

        # Relationships
        def write_rel(filename, headers, data):
            with (output_dir / filename).open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(sorted(data))

        write_rel("paper_cites.csv", ["src_paper_id", "dst_paper_id", "context", "rank_score"], self.rel_cites)
        write_rel("paper_has_keyword.csv", ["paper_id", "topic_id", "relevance_score"], self.rel_has_keyword)
        write_rel("paper_published_in_proceedings.csv", ["paper_id", "proceedings_id", "pages"], self.rel_published_in_proceedings)
        write_rel("paper_published_in_volume.csv", ["paper_id", "volume_id", "pages"], self.rel_published_in_volume)
        write_rel("author_writes.csv", ["author_id", "paper_id", "role", "is_corresponding", "author_order"], self.rel_writes)
        write_rel("proceedings_belongs_to.csv", ["proceedings_id", "edition_id"], self.rel_proceedings_belongs_to)
        write_rel("edition_part_of.csv", ["edition_id", "parent_label", "parent_id"], self.rel_edition_part_of)
        write_rel("edition_held_in.csv", ["edition_id", "city_id"], self.rel_edition_held_in)
        write_rel("edition_dated_in.csv", ["edition_id", "year_id"], self.rel_edition_dated_in)
        write_rel("volume_part_of.csv", ["volume_id", "journal_id"], self.rel_volume_part_of)
        write_rel("volume_dated_in.csv", ["volume_id", "year_id"], self.rel_volume_dated_in)
        write_rel("paper_starts_with.csv", ["paper_id", "abstract_id"], self.rel_starts_with)
        write_rel("author_reviews_paper.csv", ["author_id", "paper_id", "score", "comments", "decision"], self.rel_reviews)