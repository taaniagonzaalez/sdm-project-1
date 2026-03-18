import os
from config import DEFAULT_QUERY, SEARCH_LIMIT, OUTPUT_DIR
from clients import SemanticScholarClient, DBLPClient
from graph import GraphBuilder

def main():
    # You can override the default query using an environment variable
    query = os.getenv("GRAPH_QUERY", DEFAULT_QUERY)

    s2 = SemanticScholarClient()
    dblp = DBLPClient()
    graph = GraphBuilder()

    print(f"[1/4] Searching Semantic Scholar for query: '{query}'")
    try:
        seed_papers = s2.search_papers(query=query, limit=SEARCH_LIMIT)
    except Exception as e:
        print(f"Error while querying Semantic Scholar: {e}")
        print("Tip: verify SEMANTIC_SCHOLAR_API_KEY and try again.")
        return

    print(f"Found {len(seed_papers)} seed papers.")

    print("[2/4] Building nodes from seed papers...")
    seed_ids = []
    for paper in seed_papers:
        paper_id = paper.get("paperId")
        if not paper_id:
            continue
        seed_ids.append(paper_id)
        dblp_info = dblp.search_publication_by_title(paper.get("title", ""))
        graph.add_paper(paper, dblp_info)

    print("[3/4] Enriching citations/references...")
    for i, paper_id in enumerate(seed_ids, start=1):
        try:
            details = s2.get_paper_details(paper_id)
            graph.add_citation_edges(paper_id, details)
            print(f"  processed {i}/{len(seed_ids)} -> {paper_id}")
        except Exception as e:
            print(f"  warning: could not enrich {paper_id}: {e}")

    print("[4/4] Writing CSV files...")
    graph.export_all(OUTPUT_DIR)

    print(f"Done. CSV files written to: {OUTPUT_DIR.resolve()}")
    print("Recommended next step: import them into Neo4j with LOAD CSV or neo4j-admin import.")

if __name__ == "__main__":
    main()
