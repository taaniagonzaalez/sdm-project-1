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
S2_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
