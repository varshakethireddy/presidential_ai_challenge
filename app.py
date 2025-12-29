from __future__ import annotations
import os 
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from safety import crisis_check, crisis_response
from rag import load_cards, retrieve_cards
from prompts import SYSTEM_PROMPT, format_cards_for_prompt

load_dotenv()

st.set_page_config(page_title="TeenMind Coach", page_icon="💬")

st.title("💬 Insert Name")
st.caption("A teen-focused coping-skills coach (not a therapist).")

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
        return (
            "API key not set. I can still show the chatbot UI.\n\n"
            "To enable responses, set OPENAI_API_KEY in your environment or .env file."
        )

    client = OpenAI(api_key=api_key)

    # You can keep this model cheap
    model = "gpt-5-mini"

    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": "Coping skill cards (use only these):\n\n" + rag_context},
            {"role": "user", "content": user_message},
        ],
    )
    return response.output_text

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
    bot = call_model(user_text, rag_context)

    # Add assistant response
    st.session_state["messages"].append({"role": "assistant", "content": bot})
    with st.chat_message("assistant"):
        st.markdown(bot)




