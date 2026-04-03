import os
from config import DEFAULT_QUERY, SEARCH_LIMIT, OUTPUT_DIR, TOTAL_TO_DOWNLOAD, CHUNK_SIZE, NEO4J_URI, NEO4J_PASSWORD, NEO4J_USER, NEO4J_IMPORT_DIR
from clients import SemanticScholarClient, DBLPClient, GraphTransformerApp
from graph import GraphBuilder
from utils import setup_neo4j_files
import time
import argparse



def main(download_flag):
    # You can override the default query using an environment variable
    query = os.getenv("GRAPH_QUERY", DEFAULT_QUERY)
    
    s2 = SemanticScholarClient()
    dblp = DBLPClient()
    graph = GraphBuilder()

    if download_flag == 'True':
        print(f"[1/4] Searching Semantic Scholar for query: '{query}'")
        seed_papers = []
        
        # BATCH SEARCH LOOP
        for offset in range(0, TOTAL_TO_DOWNLOAD, CHUNK_SIZE):
            print(f"  Fetching batch: offset {offset}...")
            try:
                # We ask for CHUNK_SIZE papers starting at the current offset
                batch = s2.search_papers(query=query, limit=CHUNK_SIZE, offset=offset)
                if not batch:
                    break
                seed_papers.extend(batch)
                
                # CRITICAL: If you get 429s, increase this sleep!
                # The API needs a breather between batch calls.
                time.sleep(5.0) 
                
            except Exception as e:
                print(f"Error in batch {offset}: {e}")
                break

        print(f"Found {len(seed_papers)} total seed papers.")

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
        
        print("[+] Expanding graph with Synthetic Data...")
        # Increase the scale_multiplier if you want thousands of nodes!
        graph.generate_synthetic_data(scale_multiplier=10)

        print("[4/5] Writing CSV files...")
        graph.export_all(OUTPUT_DIR)

        print(f"Done. CSV files written to: {OUTPUT_DIR.resolve()}")
        print("Recommended next step: import them into Neo4j with LOAD CSV or neo4j-admin import.")

    print("[5/5] Re-modelling exercice A.3.")

    app = GraphTransformerApp(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    try:
        
        # Step 1: Connect and process
        app = GraphTransformerApp(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        app.clear_database()      # Clean start
        app.load_initial_data()   # Create A.1 model
        app.run_transformation_a3()  # Evolve to A.3 model
    except Exception as e:
        raise Exception(e)
    finally:
        app.close()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="My Neo4j ETL Pipeline")

    # Add the arguments you want to look for
    parser.add_argument("-p", "--download_data", required=False, help="Download data")

    # Parse them
    args = parser.parse_args()
    main(args.download_data)
