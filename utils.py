import re
import time
import requests
from typing import Optional, Dict
from config import S2_API_KEY
from pathlib import Path
import shutil

def slugify(text: str) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_") or "unknown"

def clean_text(text: Optional[str]) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()

def safe_int(value, default=None):
    try:
        return int(value)
    except Exception:
        return default

def s2_headers() -> Dict[str, str]:
    headers = {"Accept": "application/json"}
    if S2_API_KEY:
        headers["x-api-key"] = S2_API_KEY
    return headers

def request_json(url: str, params: Optional[dict] = None, headers: Optional[dict] = None, sleep: float = 1.3):
    final_headers = {
        "Accept": "application/json",
        "User-Agent": "publication-graph-lab/1.0"
    }
    if headers:
        final_headers.update(headers)

    r = requests.get(url, params=params, headers=final_headers, timeout=60)

    if r.status_code == 403:
        raise RuntimeError(f"403 Forbidden from API. Response: {r.text}")

    if r.status_code == 429:
        raise RuntimeError(f"429 Too Many Requests. Response: {r.text}")

    if not r.ok:
        raise RuntimeError(f"HTTP {r.status_code}. Response: {r.text}")

    time.sleep(sleep)
    return r.json()

def calculate_num_pages(pages_str: str) -> int:
    """Estimates num_pages from a string like '123-145'."""
    if not pages_str:
        return 0
    match = re.search(r'(\d+)\s*-\s*(\d+)', str(pages_str))
    if match:
        start, end = int(match.group(1)), int(match.group(2))
        return abs(end - start) + 1
    return 0

def setup_neo4j_files(source_folder: str, neo4j_import_path: str):
    """Copies all generated CSV files from your project to the Neo4j import directory."""
    print(f"Syncing data to Neo4j import directory: {neo4j_import_path}")
    
    src = Path(source_folder)
    dest = Path(neo4j_import_path)
    
    if not src.exists():
        raise FileNotFoundError(f"Source folder '{source_folder}' does not exist. Run main.py first!")
    if not dest.exists():
        raise FileNotFoundError(f"Neo4j import folder '{neo4j_import_path}' does not exist. Check your path!")

    # Copy all CSVs
    count = 0
    for csv_file in src.glob("*.csv"):
        shutil.copy(csv_file, dest / csv_file.name)
        count += 1
        
    print(f"Successfully copied {count} CSV files. Neo4j can now see them!")
