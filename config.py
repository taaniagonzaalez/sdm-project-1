import os
from pathlib import Path

# ============================================================
# CONFIGURATION & CONSTANTS
# ============================================================

SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1"
DBLP_PUBL_API = "https://dblp.org/search/publ/api"

# Default search parameters
DEFAULT_QUERY = "graph databases"
SEARCH_LIMIT = 10
MAX_REFERENCES_PER_PAPER = 50
MAX_CITATIONS_PER_PAPER = 50
# Configuration for batching
TOTAL_TO_DOWNLOAD = 50 
CHUNK_SIZE = 10

# Output directory for CSV files
OUTPUT_DIR = Path("graph_csv")

# Optional Semantic Scholar API key
S2_API_KEY = os.getenv("tgOuYA5Pbp26Ldg45HwOT7ZP1Qy181G77g0tO43X")

# --- CONTROL DE FLUJO ---
DOWNLOAD_REAL_DATA = False    # True: Llama a Semantic Scholar / False: Salta la API
GENERATE_SYNTHETIC = True    # True: Crea Reviews/Orgs ficticias / False: Solo usa lo de la API
RUN_NEO4J_UPDATE = True      # True: Borra y carga en Neo4j / False: Solo genera CSVs