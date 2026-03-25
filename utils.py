import re
import time
import requests
from typing import Optional, Dict
from config import S2_API_KEY

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
