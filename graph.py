import csv
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from config import MAX_REFERENCES_PER_PAPER, MAX_CITATIONS_PER_PAPER
from utils import clean_text, slugify, safe_int

class GraphBuilder:
    def __init__(self):
        self.papers: Dict[str, dict] = {}
        self.authors: Dict[str, dict] = {}
        self.topics: Dict[str, dict] = {}
        self.abstracts: Dict[str, dict] = {}
        self.years: Dict[str, dict] = {}
        self.cities: Dict[str, dict] = {}
        self.editions: Dict[str, dict] = {}
        self.proceedings: Dict[str, dict] = {}
        self.volumes: Dict[str, dict] = {}
        self.journals: Dict[str, dict] = {}
        self.conferences: Dict[str, dict] = {}
        self.workshops: Dict[str, dict] = {}

        self.rel_cites = set()
        self.rel_contains = set()
        self.rel_starts_with = set()
        self.rel_published_at_edition = set()
        self.rel_published_at_volume = set()
        self.rel_appear_in = set()
        self.rel_edition_part_of = set()
        self.rel_edition_dated_in = set()
        self.rel_edition_placed_at = set()
        self.rel_edition_has_proceedings = set()
        self.rel_volume_dated_in = set()
        self.rel_volume_part_of = set()
        self.rel_writes = set()

    def add_year(self, year: Optional[int]) -> Optional[str]:
        if not year:
            return None
        year_id = str(year)
        if year_id not in self.years:
            self.years[year_id] = {"year_id": year_id, "value": year}
        return year_id

    def add_city(self, city_name: str) -> str:
        city_name = clean_text(city_name) or "Unknown City"
        city_id = slugify(city_name)
        if city_id not in self.cities:
            self.cities[city_id] = {"city_id": city_id, "name": city_name}
        return city_id

    def add_topic(self, topic_name: str) -> Optional[str]:
        topic_name = clean_text(topic_name)
        if not topic_name:
            return None
        topic_id = slugify(topic_name)
        if topic_id not in self.topics:
            self.topics[topic_id] = {"topic_id": topic_id, "name": topic_name}
        return topic_id

    def infer_venue_type(self, paper: dict, dblp_info: Optional[dict]) -> str:
        journal = paper.get("journal")
        pub_types = paper.get("publicationTypes") or []
        venue_name = clean_text(paper.get("venue") or "")

        if journal:
            return "journal"
        if any("journal" in str(x).lower() for x in pub_types):
            return "journal"

        dblp_type = str((dblp_info or {}).get("type", "")).lower()
        if "journal" in dblp_type:
            return "journal"

        lowered = venue_name.lower()
        if "workshop" in lowered or "ws" in lowered:
            return "workshop"

        return "conference"

    def build_publication_container(self, paper: dict, dblp_info: Optional[dict]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        year = safe_int(paper.get("year"))
        year_id = self.add_year(year)
        venue_name = clean_text(paper.get("venue") or "Unknown Venue")
        publication_date = clean_text(paper.get("publicationDate"))
        journal = paper.get("journal") or {}
        venue_type = self.infer_venue_type(paper, dblp_info)

        if venue_type == "journal":
            journal_name = clean_text(journal.get("name") or venue_name or "Unknown Journal")
            journal_id = slugify(journal_name)
            if journal_id not in self.journals:
                self.journals[journal_id] = {
                    "journal_id": journal_id,
                    "name": journal_name
                }

            volume_name = clean_text(journal.get("volume") or "unknown")
            volume_id = slugify(f"{journal_name}_{volume_name}_{year or 'unknown'}")
            if volume_id not in self.volumes:
                self.volumes[volume_id] = {
                    "volume_id": volume_id,
                    "name": volume_name,
                    "journal_name": journal_name,
                    "year": year or ""
                }

            if year_id:
                self.rel_volume_dated_in.add((volume_id, year_id))
            self.rel_volume_part_of.add((volume_id, journal_id))
            return None, None, volume_id, None

        container_name = venue_name or "Unknown Event"
        container_id = slugify(container_name)

        if venue_type == "workshop":
            if container_id not in self.workshops:
                self.workshops[container_id] = {"workshop_id": container_id, "name": container_name}
        else:
            if container_id not in self.conferences:
                self.conferences[container_id] = {"conference_id": container_id, "name": container_name}

        edition_id = slugify(f"{container_name}_{year or 'unknown'}")
        if edition_id not in self.editions:
            self.editions[edition_id] = {
                "edition_id": edition_id,
                "name": f"{container_name} {year or 'Unknown'}",
                "year": year or "",
                "event_name": container_name,
                "date": publication_date
            }

        proc_id = slugify(f"proc_{container_name}_{year or 'unknown'}")
        if proc_id not in self.proceedings:
            self.proceedings[proc_id] = {
                "proceedings_id": proc_id,
                "name": f"Proceedings of {container_name} {year or ''}".strip()
            }

        if venue_type == "workshop":
            self.rel_edition_part_of.add((edition_id, "Workshop", container_id))
        else:
            self.rel_edition_part_of.add((edition_id, "Conference", container_id))

        if year_id:
            self.rel_edition_dated_in.add((edition_id, year_id))

        city_id = self.add_city("Unknown City")
        self.rel_edition_placed_at.add((edition_id, city_id))
        self.rel_edition_has_proceedings.add((edition_id, proc_id))

        return edition_id, proc_id, None, venue_type

    def add_paper(self, paper: dict, dblp_info: Optional[dict] = None):
        paper_id = paper.get("paperId")
        if not paper_id:
            return

        external_ids = paper.get("externalIds") or {}
        doi = external_ids.get("DOI", "")
        arxiv = external_ids.get("ArXiv", "")
        title = clean_text(paper.get("title"))
        abstract = clean_text(paper.get("abstract"))
        year = safe_int(paper.get("year"))
        venue = clean_text(paper.get("venue"))
        citation_count = safe_int(paper.get("citationCount"), 0)
        reference_count = safe_int(paper.get("referenceCount"), 0)

        if paper_id not in self.papers:
            self.papers[paper_id] = {
                "paper_id": paper_id, "title": title, "year": year or "",
                "venue": venue, "doi": doi, "arxiv": arxiv,
                "citation_count": citation_count, "reference_count": reference_count
            }

        if abstract:
            abstract_id = slugify(f"abstract_{paper_id}")
            if abstract_id not in self.abstracts:
                self.abstracts[abstract_id] = {"abstract_id": abstract_id, "text": abstract}
            self.rel_starts_with.add((paper_id, abstract_id))

        for topic in (paper.get("fieldsOfStudy") or []):
            topic_id = self.add_topic(str(topic))
            if topic_id:
                self.rel_contains.add((paper_id, topic_id))

        authors = paper.get("authors") or []
        for idx, author in enumerate(authors):
            author_id = author.get("authorId") or slugify(author.get("name", f"unknown_author_{idx}"))
            name = clean_text(author.get("name"))
            if author_id not in self.authors:
                self.authors[author_id] = {"author_id": author_id, "name": name}
            role = "main" if idx == 0 else "co-author"
            is_corresponding = "true" if idx == 0 else "false"
            self.rel_writes.add((author_id, paper_id, role, is_corresponding, idx))

        edition_id, proceedings_id, volume_id, venue_type = self.build_publication_container(paper, dblp_info)
        if edition_id:
            self.rel_published_at_edition.add((paper_id, edition_id))
        if volume_id:
            self.rel_published_at_volume.add((paper_id, volume_id))
        if proceedings_id:
            self.rel_appear_in.add((paper_id, proceedings_id))

    def add_citation_edges(self, source_paper_id: str, details: dict):
        for ref in (details.get("references") or [])[:MAX_REFERENCES_PER_PAPER]:
            ref_id = ref.get("paperId")
            ref_title = clean_text(ref.get("title"))
            if ref_id:
                if ref_id not in self.papers:
                    self.papers[ref_id] = {
                        "paper_id": ref_id, "title": ref_title, "year": "",
                        "venue": "", "doi": "", "arxiv": "",
                        "citation_count": 0, "reference_count": 0
                    }
                self.rel_cites.add((source_paper_id, ref_id))

        for cit in (details.get("citations") or [])[:MAX_CITATIONS_PER_PAPER]:
            cit_id = cit.get("paperId")
            cit_title = clean_text(cit.get("title"))
            if cit_id:
                if cit_id not in self.papers:
                    self.papers[cit_id] = {
                        "paper_id": cit_id, "title": cit_title, "year": "",
                        "venue": "", "doi": "", "arxiv": "",
                        "citation_count": 0, "reference_count": 0
                    }
                self.rel_cites.add((cit_id, source_paper_id))

    def write_csv(self, path: Path, fieldnames: List[str], rows: List[dict]):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)

    def export_all(self, output_dir: Path):
        output_dir.mkdir(parents=True, exist_ok=True)

        self.write_csv(output_dir / "papers.csv", ["paper_id", "title", "year", "venue", "doi", "arxiv", "citation_count", "reference_count"], list(self.papers.values()))
        self.write_csv(output_dir / "authors.csv", ["author_id", "name"], list(self.authors.values()))
        self.write_csv(output_dir / "topics.csv", ["topic_id", "name"], list(self.topics.values()))
        self.write_csv(output_dir / "abstracts.csv", ["abstract_id", "text"], list(self.abstracts.values()))
        self.write_csv(output_dir / "years.csv", ["year_id", "value"], list(self.years.values()))
        self.write_csv(output_dir / "cities.csv", ["city_id", "name"], list(self.cities.values()))
        self.write_csv(output_dir / "editions.csv", ["edition_id", "name", "year", "event_name", "date"], list(self.editions.values()))
        self.write_csv(output_dir / "proceedings.csv", ["proceedings_id", "name"], list(self.proceedings.values()))
        self.write_csv(output_dir / "volumes.csv", ["volume_id", "name", "journal_name", "year"], list(self.volumes.values()))
        self.write_csv(output_dir / "journals.csv", ["journal_id", "name"], list(self.journals.values()))
        self.write_csv(output_dir / "conferences.csv", ["conference_id", "name"], list(self.conferences.values()))
        self.write_csv(output_dir / "workshops.csv", ["workshop_id", "name"], list(self.workshops.values()))

        self.write_csv(output_dir / "paper_cites_paper.csv", ["src_paper_id", "dst_paper_id"], [{"src_paper_id": s, "dst_paper_id": d} for s, d in sorted(self.rel_cites)])
        self.write_csv(output_dir / "paper_contains_topic.csv", ["paper_id", "topic_id"], [{"paper_id": p, "topic_id": t} for p, t in sorted(self.rel_contains)])
        self.write_csv(output_dir / "paper_starts_with_abstract.csv", ["paper_id", "abstract_id"], [{"paper_id": p, "abstract_id": a} for p, a in sorted(self.rel_starts_with)])
        self.write_csv(output_dir / "paper_published_at_edition.csv", ["paper_id", "edition_id"], [{"paper_id": p, "edition_id": e} for p, e in sorted(self.rel_published_at_edition)])
        self.write_csv(output_dir / "paper_published_at_volume.csv", ["paper_id", "volume_id"], [{"paper_id": p, "volume_id": v} for p, v in sorted(self.rel_published_at_volume)])
        self.write_csv(output_dir / "paper_appear_in_proceedings.csv", ["paper_id", "proceedings_id"], [{"paper_id": p, "proceedings_id": pr} for p, pr in sorted(self.rel_appear_in)])
        self.write_csv(output_dir / "edition_part_of.csv", ["edition_id", "parent_label", "parent_id"], [{"edition_id": e, "parent_label": label, "parent_id": pid} for e, label, pid in sorted(self.rel_edition_part_of)])
        self.write_csv(output_dir / "edition_dated_in_year.csv", ["edition_id", "year_id"], [{"edition_id": e, "year_id": y} for e, y in sorted(self.rel_edition_dated_in)])
        self.write_csv(output_dir / "edition_placed_at_city.csv", ["edition_id", "city_id"], [{"edition_id": e, "city_id": c} for e, c in sorted(self.rel_edition_placed_at)])
        self.write_csv(output_dir / "edition_has_proceedings.csv", ["edition_id", "proceedings_id"], [{"edition_id": e, "proceedings_id": p} for e, p in sorted(self.rel_edition_has_proceedings)])
        self.write_csv(output_dir / "volume_dated_in_year.csv", ["volume_id", "year_id"], [{"volume_id": v, "year_id": y} for v, y in sorted(self.rel_volume_dated_in)])
        self.write_csv(output_dir / "volume_part_of_journal.csv", ["volume_id", "journal_id"], [{"volume_id": v, "journal_id": j} for v, j in sorted(self.rel_volume_part_of)])
        self.write_csv(output_dir / "author_writes_paper.csv", ["author_id", "paper_id", "role", "is_corresponding", "author_order"], [{"author_id": a, "paper_id": p, "role": role, "is_corresponding": corr, "author_order": order} for a, p, role, corr, order in sorted(self.rel_writes)])
