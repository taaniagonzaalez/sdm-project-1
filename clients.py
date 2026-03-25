from typing import List, Optional
from config import SEMANTIC_SCHOLAR_API, DBLP_PUBL_API
from utils import request_json, s2_headers

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
