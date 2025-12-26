from __future__ import annotations

CRISIS_KEYWORDS = [
    "suicide", "kill myself", "end my life", "self harm", "self-harm",
    "cut myself", "overdose", "want to die", "can't go on"
]

def crisis_check(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in CRISIS_KEYWORDS)

def crisis_response() -> str:
    return (
        "I’m really sorry you’re feeling this way. I can’t help with self-harm, "
        "but you *deserve support right now*.\n\n"
        "**If you’re in the U.S.:** call/text **988** (Suicide & Crisis Lifeline). "
        "If you’re in immediate danger, call **911**.\n\n"
        "If you can, reach out to a trusted adult (parent/guardian, school counselor, coach) "
        "or a friend and ask them to stay with you while you get help."
    )