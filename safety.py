from __future__ import annotations
import re
from typing import Optional

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
    Uses regex word boundaries to avoid false positives (e.g., 'friend' triggering 'end').
    """
    t = (text or "").lower()
    return any(re.search(pattern, t) for pattern in CRISIS_PATTERNS)


def crisis_response(user_text: Optional[str] = None, country: Optional[str] = None, top_k: int = 2) -> str:
    """Return a supportive crisis message and recommend 1-2 immediate hotlines when available.

    Parameters:
      - user_text: optional user message to use for choosing best local resources
      - country: optional country string to bias recommendations
      - top_k: maximum number of hotline recommendations to include
    """
    base = (
        "I’m really sorry you’re feeling this way. I can’t help with self-harm, "
        "but you *deserve support right now*.")

    guidance = [
        "If you’re in the U.S.: call or text 988 (Suicide & Crisis Lifeline).",
        "If you’re in immediate danger, call your local emergency number (for example, 911 in the U.S.).",
        "If you can, please reach out to a trusted adult (parent/guardian, school counselor, coach) or a close friend and let them know you need support.",
    ]

    # Try to get recommended hotlines from the data file
    recommendations = []
    try:
        from . import hotlines as _hotlines
        if user_text:
            out = _hotlines.get_resources_for_user(user_text, country=country, top_k=top_k)
            recommendations = out.get("matches") or []
    except Exception:
        recommendations = []

    msg_lines = [base, ""]
    # include top-level guidance
    for g in guidance:
        msg_lines.append(g)

    if recommendations:
        msg_lines.append("")
        msg_lines.append("Recommended immediate resources:")
        for item in recommendations[:top_k]:
            entry = item.get("entry", {})
            name = entry.get("name") or "Unknown"
            country_label = entry.get("country") or ""
            phone = entry.get("phone")
            sms = entry.get("sms")
            website = entry.get("website")
            notes = entry.get("notes")
            line = f"- {name} ({country_label})"
            contact_parts = []
            if phone:
                contact_parts.append(f"Phone: {phone}")
            if sms:
                contact_parts.append(f"SMS: {sms}")
            if website:
                contact_parts.append(f"Website: {website}")
            if contact_parts:
                line += " — " + "; ".join(contact_parts)
            if notes:
                line += f"\n  {notes}"
            msg_lines.append(line)

    msg_lines.append("")
    msg_lines.append("If you are in immediate danger, please call your local emergency services right now.")

    return "\n\n".join(msg_lines)


if __name__ == "__main__":
    # quick smoke test
    sample = "i think i want to kill myself"
    print("crisis_check:", crisis_check(sample))
    print(crisis_response(sample, country="United States"))



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
