import time
import sys
from config import (
    DEFAULT_QUERY, TOTAL_TO_DOWNLOAD, CHUNK_SIZE, OUTPUT_DIR,
    DOWNLOAD_REAL_DATA, GENERATE_SYNTHETIC, RUN_NEO4J_UPDATE
)
from clients import SemanticScholarClient, DBLPClient
from graph import GraphBuilder
from loader import run_update

def main():
    graph = GraphBuilder()
    s2 = SemanticScholarClient()
    dblp = DBLPClient()

    print(f"--- Pipeline Iniciado (Query: '{DEFAULT_QUERY}') ---")

    # [1/5] OBTENCIÓN DE DATOS REALES (SEMANTIC SCHOLAR)
    seed_papers = []
    if DOWNLOAD_REAL_DATA:
        print("[1/5] Buscando datos en Semantic Scholar...")
        for offset in range(0, TOTAL_TO_DOWNLOAD, CHUNK_SIZE):
            print(f"    -> Pidiendo batch: offset {offset}...")
            try:
                batch = s2.search_papers(query=DEFAULT_QUERY, limit=CHUNK_SIZE, offset=offset)
                if not batch: break
                seed_papers.extend(batch)
                # Pausa de seguridad para evitar el error 429
                time.sleep(2.0) 
            except Exception as e:
                print(f"!! Error 429 o de conexión: {e}. Deteniendo descarga.")
                break
        print(f"Total papers reales obtenidos: {len(seed_papers)}")
    else:
        print("[1/5] SKIP: Descarga de datos reales desactivada en config.py")

    # [2/5] PROCESAMIENTO Y GENERACIÓN SINTÉTICA COMPLETA
    if seed_papers or GENERATE_SYNTHETIC:
        print("[2/5] Modo Generación Activo: Creando ecosistema académico...")
        
        if not seed_papers and GENERATE_SYNTHETIC:
            # Creamos una lista de 5 papers para tener variedad
            seed_papers = [
                {
                    "paperId": f"paper_00{i}",
                    "title": f"Advancements in Graph Databases Vol {i}",
                    "authors": [
                        {"authorId": f"auth_0{i}", "name": f"Researcher {i}"},
                        {"authorId": f"auth_0{i+1}", "name": f"Researcher {i+1}"}
                    ],
                    "abstract": "Analysis of Neo4j performance in large scale environments.",
                    "year": 2020 + i
                } for i in range(1, 6)
            ]

        # Procesamos cada paper
        for paper in seed_papers:
            author_ids = [a.get('authorId') for a in paper.get('authors', []) if a.get('authorId')]
            
            # 1. Añade el paper y sus autores base
            graph.add_paper(paper)
            
            # 2. ENRIQUECIMIENTO TOTAL (Relaciones y Nodos adicionales)
            if GENERATE_SYNTHETIC:
                graph.enrich_with_synthetic_data(paper['paperId'], author_ids)
                
                # 3. Crear CITAS cruzadas (Simular que unos papers citan a otros)
                # Hacemos que el paper actual cite al anterior si existe
                idx = seed_papers.index(paper)
                if idx > 0:
                    prev_id = seed_papers[idx-1]['paperId']
                    graph.paper_cites.append({
                        "src_paper_id": paper['paperId'],
                        "dst_paper_id": prev_id,
                        "context": "Building upon previous work.",
                        "rank_score": 0.85
                    })
    # [3/5] ENRIQUECIMIENTO DE CITAS (OPCIONAL/DEEP DIVE)
    if DOWNLOAD_REAL_DATA and seed_papers:
        print("[3/5] Enriqueciendo citas (Deep Dive)...")
        # Solo lo hacemos para los primeros 5 para no saturar la API
        for i, paper in enumerate(seed_papers[:5]):
            try:
                time.sleep(1.5)
                details = s2.get_paper_details(paper['paperId'])
                graph.add_citation_edges(paper['paperId'], details)
                print(f"    Enriquecido: {paper['paperId']}")
            except:
                print(f"    Saltando enriquecimiento de {paper['paperId']} (API Limit)")

    # [4/5] EXPORTACIÓN A CSV
    print(f"[4/5] Escribiendo archivos CSV en: {OUTPUT_DIR}")
    try:
        graph.export_all(OUTPUT_DIR)
    except Exception as e:
        print(f"!! Error al guardar CSVs: {e}")
        return

    # [5/5] CARGA AUTOMÁTICA EN NEO4J
    if RUN_NEO4J_UPDATE:
        print("[5/5] Sincronizando con Neo4j...")
        try:
            run_update()
            print("PIPELINE FINALIZADO CON ÉXITO.")
        except Exception as e:
            print(f"!! Error en la carga de Neo4j: {e}")
    else:
        print("[5/5] SKIP: Carga en Neo4j desactivada.")

if __name__ == "__main__":
    main()