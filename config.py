import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# CONFIGURATION & CONSTANTS
# ============================================================

SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1"
DBLP_PUBL_API = "https://dblp.org/search/publ/api"

# Keys
NEO4J_URI=os.getenv("NEO4J_URI")
NEO4J_USER=os.getenv("NEO4J_USER")
NEO4J_PASSWORD=os.getenv("NEO4J_PASSWORD")
NEO4J_IMPORT_DIR=os.getenv("NEO4J_IMPORT_DIR")
SEMANTIC_SCHOLAR_API_KEY=os.getenv("SEMANTIC_SCHOLAR_API_KEY")

# Default search parameters
DEFAULT_QUERY = "graph databases"
SEARCH_LIMIT = 10
MAX_REFERENCES_PER_PAPER = 10
MAX_CITATIONS_PER_PAPER = 10
# Configuration for batching
TOTAL_TO_DOWNLOAD = 10 
CHUNK_SIZE = 10

# Output directory for CSV files
OUTPUT_DIR = Path("graph_csv")

# Optional Semantic Scholar API key
S2_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
