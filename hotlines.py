"""Utilities to load and query hotline/app resources stored in `data/hotlines.json`.

This module provides:
- `load_hotlines(path)`: load JSON file into memory
- `find_by_country(hotlines, country)`: filter entries by country (case-insensitive)
- `search_hotlines(hotlines, query, country=None, top_k=5)`: simple relevance search
- `detect_resource_intent(text)`: heuristics to detect when a user is asking for resources or is in crisis
- `get_resources_for_user(text, country=None, top_k=5)`: helper that runs intent detection and returns matches

The search implementation is intentionally lightweight (no external dependencies).
For better results at scale, consider adding embeddings + vector DB retrieval.
"""
from __future__ import annotations
import json
import math
import re
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from difflib import SequenceMatcher


HOTLINES_PATH = Path(__file__).parent / "data" / "hotlines.json"

def load_hotlines(path: Optional[Path | str] = None) -> List[Dict[str, Any]]:
    p = Path(path) if path else HOTLINES_PATH
    with p.open("r", encoding="utf8") as f:
        data = json.load(f)
    return data

def _norm_text(s: Optional[str]) -> str:
    return (s or "").lower().strip()

def find_by_country(hotlines: List[Dict[str, Any]], country: str) -> List[Dict[str, Any]]:
    if not country:
        return []
    c = country.lower().strip()
    matches = [h for h in hotlines if h.get("country") and h["country"].lower().strip() == c]
    return matches

def _score_entry(entry: Dict[str, Any], query: str) -> float:
    # Combine name, notes, tags, website, phone for matching
    parts = [entry.get("name",""), entry.get("notes",""), " ".join(entry.get("tags",[])), entry.get("website",""), entry.get("phone","")]
    text = " ".join([p for p in parts if p])
    # use difflib ratio for fuzzy similarity
    ratio = SequenceMatcher(None, query, text).ratio()
    # bonus for country mention in text
    if entry.get("country") and entry["country"].lower() in query.lower():
        ratio += 0.15
    return ratio

def search_hotlines(hotlines: List[Dict[str, Any]], query: str, country: Optional[str] = None, top_k: int = 5) -> List[Tuple[float, Dict[str, Any]]]:
    q = _norm_text(query)
    scored = []
    for h in hotlines:
        if country and h.get("country") and h["country"].lower().strip() != country.lower().strip():
            # skip entries with explicit country mismatch
            continue
        score = _score_entry(h, q)
        scored.append((score, h))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:top_k]

RESOURCE_KEYWORDS = [
    r"hotline",
    r"help line",
    r"suicide",
    r"crisis",
    r"self[- ]?harm",
    r"urgent help",
    r"mental health",
    r"therapy app",
    r"counsel(ing|or)",
    r"need help",
    r"call",
    r"text",
    r"app recommendation",
]

RESOURCE_RE = re.compile("|".join(RESOURCE_KEYWORDS), re.I)

def detect_resource_intent(text: str) -> bool:
    """Return True if the user text appears to be requesting resources or help.

    This is a lightweight heuristic: keyword scan plus crisis check.
   """
    if not text:
        return False
    # immediate crisis detection via safety module (import locally to avoid circular import)
    try:
        from . import safety as _safety
    except Exception:
        _safety = None
    if _safety and _safety.crisis_check(text):
        return True
    # otherwise look for resource-related keywords
    return bool(RESOURCE_RE.search(text))

def get_resources_for_user(text: str, country: Optional[str] = None, top_k: int = 5) -> Dict[str, Any]:
    """Main helper: detect intent and return recommended resources.

    Returns a dict with keys:
      - triggered: bool (whether resources should be suggested)
      - crisis: bool (whether crisis patterns were detected)
      - matches: list of recommended hotline entries (may be empty)
    """
    hotlines = load_hotlines()
    # import safety locally to avoid circular import at module import time
    try:
        from . import safety as _safety
    except Exception:
        _safety = None
    crisis = bool(_safety.crisis_check(text)) if _safety else False
    triggered = crisis or detect_resource_intent(text)
    results: List[Tuple[float, Dict[str, Any]]] = []
    if triggered:
        # prefer exact country matches first
        if country:
            results = search_hotlines(hotlines, text, country=country, top_k=top_k)
        # if not enough results, broaden search to global
        if len(results) < top_k:
            more = search_hotlines(hotlines, text, country=None, top_k=top_k)
            # merge unique
            ids = {r[1]["id"] for r in results}
            for s,e in more:
                if e["id"] not in ids:
                    results.append((s,e))
                if len(results) >= top_k:
                    break

    return {
        "triggered": bool(triggered),
        "crisis": bool(crisis),
        "matches": [ {"score": float(s), "entry": e} for s,e in results[:top_k] ]
    }

if __name__ == "__main__":
    # simple smoke test
    h = load_hotlines()
    print(f"Loaded {len(h)} hotline entries")
    q = "I need a suicide hotline in United Kingdom"
    out = get_resources_for_user(q, country="United Kingdom", top_k=3)
    print(json.dumps(out, indent=2))
