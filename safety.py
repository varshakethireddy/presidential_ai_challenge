from __future__ import annotations
import re

# =========================
# TIER 1: IMMEDIATE CRISIS
# (Direct self-harm intent)
# =========================

CRISIS_PATTERNS = [
    r"\b(kys|kms)\b",

    r"\b(kill myself|take my life|commit suicide|suicide)\b",

    r"\b(i'?m going to kill myself|i plan to kill myself)\b",

    r"\b(i\s*(?:want|wanna|wna)\s*to\s*die|i\s*don'?t\s*want\s*to\s*live(?:\s*anymore)?|i\s*wish\s*i\s*were\s*dead)\b",


    r"\b(self[- ]?harm|self[- ]?injury)\b",

    r"\b(cut myself|slit my wrists|burn myself|hurt myself)\b",

    r"\b(overdose|od|overdose on pills|take too many pills)\b",

    r"\b(hang myself|suffocate myself|drown myself)\b",

    r"\b(jump off (a )?(bridge|building))\b",

    r"\b(shoot myself|gun to my head|put a gun to my head)\b",
]

def crisis_check(text: str) -> bool:
    """
    Returns True ONLY if there is clear, direct self-harm intent.
    Uses regex word boundaries to avoid false positives
    (e.g., 'friend' triggering 'end').
    """
    t = text.lower()
    return any(re.search(pattern, t) for pattern in CRISIS_PATTERNS)


def crisis_response() -> str:
    return (
        "I’m really sorry you’re feeling this way. I can’t help with self-harm, "
        "but you *deserve support right now*.\n\n"
        "**If you’re in the U.S.:** call or text **988** (Suicide & Crisis Lifeline).\n"
        "If you’re in immediate danger, call **911**.\n\n"
        "If you can, please reach out to a trusted adult "
        "(parent/guardian, school counselor, coach) or a close friend "
        "and let them know you need support."
    )
