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
        self.reviews: Dict[str, dict] = {}
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
        self.rel_provides_review = set()
        self.rel_evaluates_paper = set()
        self.rel_starts_with = set()

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
                self.journals[journal_id] = {"name": journal_name, "issn": "", "impact_factor": 0.0}

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
                
                # Add Node
                self.reviews[review_id] = {"content_description": content, "decision": decision}
                
                # Add Relationships
                self.rel_provides_review.add((reviewer_id, review_id))
                self.rel_evaluates_paper.add((review_id, paper_id))
    
    def generate_synthetic_data(self, scale_multiplier=10):
        """
        Generates synthetic data for all 13 nodes and 14 relationships.
        scale_multiplier dictates how large the generated dataset will be.
        """
        print(f"Generating synthetic graph (scale x{scale_multiplier})...")

        # --- 1. GENERATE BASE NODES ---
        # Years (2010 to 2024)
        synth_years = []
        for y in range(2010, 2025):
            y_id = f"year_{y}"
            self.years[y_id] = {"year_id": y_id, "value": y}
            synth_years.append(y_id)

        # Cities (10 * scale)
        synth_cities = []
        for _ in range(10 * scale_multiplier):
            c_id = f"city_{uuid.uuid4().hex[:8]}"
            self.cities[c_id] = {"city_id": c_id, "name": fake.city(), "country": fake.country()}
            synth_cities.append(c_id)

        # Topics (15 * scale)
        synth_topics = []
        for _ in range(15 * scale_multiplier):
            t_id = f"topic_{uuid.uuid4().hex[:8]}"
            self.topics[t_id] = {"topic_id": t_id, "name": fake.catch_phrase(), "area": "Computer Science"}
            synth_topics.append(t_id)

        # Organizations (5 * scale)
        synth_orgs = []
        for _ in range(5 * scale_multiplier):
            o_id = f"org_{uuid.uuid4().hex[:8]}"
            self.organizations[o_id] = {"org_id": o_id, "name": fake.company(), "type": random.choice(["University", "Company", "Research Lab"])}
            synth_orgs.append(o_id)

        # --- 2. GENERATE VENUES (Journals, Conferences, Workshops) ---
        synth_journals = []
        for _ in range(5 * scale_multiplier):
            j_id = f"journal_{uuid.uuid4().hex[:8]}"
            self.journals[j_id] = {"journal_id": j_id, "name": f"Journal of {fake.word().title()}", "issn": fake.bothify(text='####-####'), "impact_factor": round(random.uniform(0.5, 15.0), 2)}
            synth_journals.append(j_id)

        synth_conferences = []
        for _ in range(5 * scale_multiplier):
            c_id = f"conf_{uuid.uuid4().hex[:8]}"
            self.conferences[c_id] = {"conference_id": c_id, "name": f"Int. Conf. on {fake.word().title()}", "acronym": fake.lexify(text='????').upper(), "ranking": random.choice(["A*", "A", "B", "C"])}
            synth_conferences.append(c_id)

        synth_workshops = []
        for _ in range(5 * scale_multiplier):
            w_id = f"ws_{uuid.uuid4().hex[:8]}"
            self.workshops[w_id] = {"workshop_id": w_id, "name": f"Workshop on {fake.word().title()}", "acronym": fake.lexify(text='??WS').upper()}
            synth_workshops.append(w_id)

        # --- 3. GENERATE VENUE INSTANCES (Volumes, Editions, Proceedings) ---
        synth_volumes = []
        for j_id in synth_journals:
            for vol_num in range(1, random.randint(3, 6)):
                v_id = f"vol_{uuid.uuid4().hex[:8]}"
                self.volumes[v_id] = {"volume_node_id": v_id, "volume_id": str(vol_num), "issue_number": str(random.randint(1, 12))}
                synth_volumes.append(v_id)
                # Relationship: Volume PART_OF Journal & DATED_IN Year
                self.rel_volume_part_of.add((v_id, j_id))
                # Note: Assuming your schema has a rel_volume_dated_in set (if not, add it to __init__!)
                if hasattr(self, 'rel_volume_dated_in'):
                    self.rel_volume_dated_in.add((v_id, random.choice(synth_years)))

        synth_editions = []
        synth_proceedings = []
        for parent_id, parent_type in [(c, "Conference") for c in synth_conferences] + [(w, "Workshop") for w in synth_workshops]:
            for ed_num in range(1, random.randint(2, 5)):
                # Edition
                e_id = f"ed_{uuid.uuid4().hex[:8]}"
                start_date = fake.date_between(start_date="-10y", end_date="today")
                self.editions[e_id] = {"edition_id": e_id, "number": ed_num, "start_date": str(start_date), "end_date": str(start_date)}
                synth_editions.append(e_id)
                
                # Proceedings for this edition
                p_id = f"proc_{uuid.uuid4().hex[:8]}"
                self.proceedings[p_id] = {"proceedings_id": p_id, "title": f"Proc. of {parent_type} {ed_num}", "publisher": fake.company()}
                synth_proceedings.append(p_id)

                # Relationships for Edition & Proceedings
                self.rel_edition_part_of.add((e_id, parent_type, parent_id))
                self.rel_edition_dated_in.add((e_id, random.choice(synth_years)))
                self.rel_edition_held_in.add((e_id, random.choice(synth_cities)))
                self.rel_proceedings_belongs_to.add((p_id, e_id))

        # --- 4. GENERATE AUTHORS & AFFILIATIONS ---
        synth_authors = []
        for _ in range(50 * scale_multiplier):
            a_id = f"auth_{uuid.uuid4().hex[:8]}"
            self.authors[a_id] = {"author_id": a_id, "name": fake.name(), "orcid": fake.bothify(text='0000-000#-####-####')}
            synth_authors.append(a_id)
            # Relationship: Author AFFILIATED_WITH Organization (assuming you have this set)
            if hasattr(self, 'rel_affiliated_with'):
                self.rel_affiliated_with.add((a_id, random.choice(synth_orgs)))

        # --- 5. GENERATE PAPERS & PUBLICATIONS ---
        synth_papers = []
        for _ in range(100 * scale_multiplier):
            p_id = f"paper_{uuid.uuid4().hex[:12]}"
            self.papers[p_id] = {
                "paper_id": p_id, "title": fake.catch_phrase().title(), "doi": f"10.1000/synth.{random.randint(1000, 99999)}",
                "num_pages": random.randint(5, 30), "abstract_summary": fake.paragraph(nb_sentences=5), "year_published": random.randint(2010, 2024)
            }
            synth_papers.append(p_id)

            # Paper HAS_KEYWORD Topic
            for t_id in random.sample(synth_topics, random.randint(1, 4)):
                self.rel_has_keyword.add((p_id, t_id, round(random.uniform(0.5, 1.0), 2)))

            # Author WRITES Paper
            writers = random.sample(synth_authors, random.randint(1, 5))
            for idx, a_id in enumerate(writers):
                self.rel_writes.add((a_id, p_id, "main" if idx==0 else "co-author", True if idx==0 else False, idx+1))

            # Paper Published in (50% Volume, 50% Proceedings)
            pages_str = f"{random.randint(1, 50)}-{random.randint(51, 100)}"
            if random.choice([True, False]) and synth_volumes:
                self.rel_published_in_volume.add((p_id, random.choice(synth_volumes), pages_str))
            elif synth_proceedings:
                self.rel_published_in_proceedings.add((p_id, random.choice(synth_proceedings), pages_str))
            
            # 2. Creamos el nodo Abstract (PARA EVITAR CSV VACÍO)
            abs_id = f"abs_{p_id}"
            abs_content = fake.paragraph(nb_sentences=5)
            self.abstracts[abs_id] = {
                "abstract_id": abs_id,
                "content": abs_content,
                "word_count": len(abs_content.split())
            }
            # Relación STARTS_WITH (Añádela a self.rel_starts_with en __init__ si no está)
            self.rel_starts_with.add((p_id, abs_id))

        # Paper CITES Paper
        for p_id in synth_papers:
            if random.random() > 0.3: # 70% chance to cite others
                cited_papers = random.sample(synth_papers, min(len(synth_papers), random.randint(1, 10)))
                for cited_id in cited_papers:
                    if cited_id != p_id:
                        self.rel_cites.add((p_id, cited_id, "background", round(random.uniform(0.1, 1.0), 2)))
        
        

        # --- 6. GENERATE REVIEWS ---
        for p_id in synth_papers:
            if random.random() > 0.5: # 50% of papers get reviews
                reviewers = random.sample(synth_authors, random.randint(1, 3))
                for a_id in reviewers:
                    r_id = f"rev_{uuid.uuid4().hex[:8]}"
                    self.reviews[r_id] = {"review_id": r_id, "content_description": fake.paragraph(), "decision": random.choice(["Accepted", "Rejected", "Revise"])}
                    
                    # Author PROVIDES_REVIEW, Review EVALUATES Paper
                    if hasattr(self, 'rel_provides_review') and hasattr(self, 'rel_evaluates_paper'):
                        self.rel_provides_review.add((a_id, r_id))
                        self.rel_evaluates_paper.add((r_id, p_id))

        print(f"Synthetic generation complete! Added {len(synth_papers)} papers and {len(synth_authors)} authors.")

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
        self.write_csv(output_dir / "authors.csv", ["author_id", "name", "orcid"], self.authors.items(), True, "author_id")
        self.write_csv(output_dir / "organizations.csv", ["org_id", "name", "type"], self.organizations.items(), True, "org_id")
        self.write_csv(output_dir / "topics.csv", ["topic_id", "name", "area"], self.topics.items(), True, "topic_id")
        self.write_csv(output_dir / "years.csv", ["year_id", "value"], self.years.items(), True, "year_id")
        self.write_csv(output_dir / "cities.csv", ["city_id", "name", "country"], self.cities.items(), True, "city_id")
        self.write_csv(output_dir / "editions.csv", ["edition_id", "number", "start_date", "end_date"], self.editions.items(), True, "edition_id")
        self.write_csv(output_dir / "proceedings.csv", ["proceedings_id", "title", "publisher"], self.proceedings.items(), True, "proceedings_id")
        self.write_csv(output_dir / "volumes.csv", ["volume_node_id", "volume_id", "issue_number"], self.volumes.items(), True, "volume_node_id")
        self.write_csv(output_dir / "journals.csv", ["journal_id", "name", "issn", "impact_factor"], self.journals.items(), True, "journal_id")
        self.write_csv(output_dir / "conferences.csv", ["conference_id", "name", "acronym", "ranking"], self.conferences.items(), True, "conference_id")
        self.write_csv(output_dir / "workshops.csv", ["workshop_id", "name", "acronym"], self.workshops.items(), True, "workshop_id")
        self.write_csv(output_dir / "reviews.csv", ["review_id", "content_description", "decision"], self.reviews.items(), True, "review_id")
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
        write_rel("author_provides_review.csv", ["author_id", "review_id"], self.rel_provides_review)
        write_rel("review_evaluates_paper.csv", ["review_id", "paper_id"], self.rel_evaluates_paper)
        write_rel("proceedings_belongs_to.csv", ["proceedings_id", "edition_id"], self.rel_proceedings_belongs_to)
        write_rel("edition_part_of.csv", ["edition_id", "parent_label", "parent_id"], self.rel_edition_part_of)
        write_rel("edition_held_in.csv", ["edition_id", "city_id"], self.rel_edition_held_in)
        write_rel("edition_dated_in.csv", ["edition_id", "year_id"], self.rel_edition_dated_in)
        write_rel("volume_part_of.csv", ["volume_id", "journal_id"], self.rel_volume_part_of)
        write_rel("volume_dated_in.csv", ["volume_id", "year_id"], self.rel_volume_dated_in)
        write_rel("paper_starts_with.csv", ["paper_id", "abstract_id"], self.rel_starts_with)