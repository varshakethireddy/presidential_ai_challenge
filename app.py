from __future__ import annotations
import os 
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from safety import crisis_check, crisis_response
from rag import load_cards, retrieve_cards
from prompts import SYSTEM_PROMPT, format_cards_for_prompt
from schema import COACH_OUTPUT_SCHEMA
import json
import uuid 
from emotion_logger import log_turn


load_dotenv()

st.set_page_config(page_title="TeenMind Coach", page_icon="💬")
## Top-row controls: left-aligned reset button that clears the on-screen chat only
row_col1, row_col2 = st.columns([3, 7])
# Custom button styling: make buttons look like blue rounded "bubbles".
# Scoped to `.stButton > button:first-child` so it primarily affects the left/top button.
st.markdown(
    """
    <style>
    /* primary bubble button style */
    div.stButton > button:first-child {
        background-color: #1E90FF;
        color: white;
        border: none;
        border-radius: 24px;
        padding: 8px 18px;
        box-shadow: 0 6px 18px rgba(30,144,255,0.28);
        font-weight: 600;
        transition: background-color 0.12s ease-in-out, transform 0.08s ease;
    }
    div.stButton > button:first-child:hover {
        background-color: #187bcd;
        transform: translateY(-1px);
    }
    div.stButton > button:first-child:active {
        transform: translateY(0);
        box-shadow: 0 3px 8px rgba(30,144,255,0.22);
    }
    </style>
    """,
    unsafe_allow_html=True,
)
with row_col1:
    if st.button("reset chat", key="reset_chat"):
        # Reset only the on-screen messages for this session
        st.session_state["messages"] = [
            {"role": "assistant", "content": "Hey — I’m here with you. What’s been going on today?"}
        ]
        # Try to rerun the app to reflect the cleared UI immediately; safe for older Streamlit
        try:
            st.experimental_rerun()
        except Exception:
            pass
with row_col2:
    # leave space to keep the button visually on the left/top
    pass

st.title("💬 Insert Name")
st.caption("A teen-focused coping-skills coach (not a therapist).")

if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())

# Initialize session state
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Hey — I’m here with you. What’s been going on today?"}
    ]

if "intent" not in st.session_state:
    st.session_state["intent"] = "stress"  # default fallback

# Sidebar controls
st.sidebar.header("Controls")
st.sidebar.write("This demo does not store conversations.")
dev_mode = st.sidebar.checkbox("Developer mode (show intent)", value=False)

# Load RAG cards once
cards = load_cards()

# Render chat history
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_text = st.chat_input("Type a message…")

def cheap_intent_heuristic(text: str) -> str:
    """Day-1 intent detector. Replace later with a trained classifier."""
    t = text.lower()
    if any(w in t for w in ["panic", "anxious", "anxiety", "scared", "heart racing"]):
        return "anxiety"
    if any(w in t for w in ["sad", "depressed", "down", "hopeless", "lonely"]):
        return "sadness"
    if any(w in t for w in ["sleep", "insomnia", "can't sleep", "tired"]):
        return "sleep"
    if any(w in t for w in ["fight", "argument", "friend", "drama", "parents"]):
        return "conflict"
    return "stress"

def call_model(user_message: str, rag_context: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # Allow running without API key for UI testing
        return {
            "intent": "other",
            "tone": "other",
            "risk_level": "other",
            "should_offer_skill": True,
            "assistant_message": (
                "API key not set. I can show the chatbot UI, but I can’t generate responses yet.\n\n"
                "Set OPENAI_API_KEY in your environment or .env file."
            ),
        }

    client = OpenAI(api_key=api_key)

    # You can keep this model cheap
    model = "gpt-5-mini"

    # The Responses API expects the 'schema' to be a JSON Schema object (type: object).
    # Our `COACH_OUTPUT_SCHEMA` may be a wrapper dict (with keys like 'name','schema'),
    # so extract the actual schema object if necessary.
    schema_to_send = None
    if isinstance(COACH_OUTPUT_SCHEMA, dict) and "schema" in COACH_OUTPUT_SCHEMA:
        schema_to_send = COACH_OUTPUT_SCHEMA["schema"]
    else:
        schema_to_send = COACH_OUTPUT_SCHEMA

    response = client.responses.create(
        model="gpt-4o-mini",
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": "Coping skill cards (use only these):\n\n" + rag_context},
            {"role": "user", "content": user_message},
        ],
        text={
            "format": {
                "name": "coach_output",
                "type": "json_schema",
                "schema": schema_to_send,
            }
        },
    )

    # The Responses API returns structured content; prefer using response.output_parsed when available,
    # otherwise fall back to parsing output_text.
    parsed = None
    try:
        parsed = response.output_parsed
    except Exception:
        parsed = None

    if parsed is None:
        raw = response.output_text
        return json.loads(raw)
    return parsed

if user_text:
    # Add user message
    st.session_state["messages"].append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    # Safety first
    if crisis_check(user_text):
        bot = crisis_response()
        st.session_state["messages"].append({"role": "assistant", "content": bot})
        with st.chat_message("assistant"):
            st.markdown(bot)
        st.stop()

    # Intent detection (cheap heuristic for day 1)
    intent = cheap_intent_heuristic(user_text)
    st.session_state["intent"] = intent

    # Retrieve skill cards
    chosen = retrieve_cards(cards, intent=intent, k=2)
    rag_context = format_cards_for_prompt(chosen)

    if dev_mode:
        st.sidebar.success(f"Intent: {intent}")
        st.sidebar.write("Retrieved cards:")
        for c in chosen:
            st.sidebar.write(f"- {c['title']}")

    # Call model
    result = call_model(user_text, rag_context)
    # Show assistant message to user
    bot_text = result["assistant_message"]
    st.session_state["messages"].append({"role": "assistant", "content": bot_text})
    with st.chat_message("assistant"):
        st.markdown(bot_text)

    # Log structured fields (NO raw user text stored)
    log_turn({
        "session_id": st.session_state["session_id"],
        "turn_index": len(st.session_state["messages"]),
        "intent": result["intent"],
        "tone": result["tone"],
        "risk_level": result["risk_level"],
        "should_offer_skill": result["should_offer_skill"],
    })


