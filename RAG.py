from __future__ import annotations
import json
from pathlib import Path
from typing import List, Dict, Any

def load_cards(path: str = "data/skill_cards.json") -> List[Dict[str, Any]]:
    return json.loads(Path(path).read_text(encoding="utf-8"))

def retrieve_cards(cards: List[Dict[str, Any]], intent: str, k: int = 2) -> List[Dict[str, Any]]:
    #basic starting point: pick cards whose tags include the intent
    matches = [c for c in cards if intent in c.get("tags", [])]
    return matches[:k] if matches else cards[:k]