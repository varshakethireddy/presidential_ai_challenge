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
import html
import base64
import uuid 
from emotion_logger import log_turn


load_dotenv()

st.set_page_config(page_title="TeenMind Coach", page_icon="💬")
# Custom button styling: make buttons look like pastel green rounded "bubbles".
# Scoped to `.stButton > button:first-child` so it primarily affects the left/top button.
st.markdown(
    """
    <style>
    /* primary bubble button style - pastel green */
    div.stButton > button:first-child {
        background-color: #B4E7CE;
        color: #2d5f4a;
        border: none;
        border-radius: 24px;
        padding: 8px 18px;
        box-shadow: 0 6px 18px rgba(180, 231, 206, 0.28);
        font-weight: 600;
        transition: background-color 0.12s ease-in-out, transform 0.08s ease;
    }
    div.stButton > button:first-child:hover {
        background-color: #9dd9ba;
        transform: translateY(-1px);
    }
    div.stButton > button:first-child:active {
        transform: translateY(0);
        box-shadow: 0 3px 8px rgba(180, 231, 206, 0.22);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Chat bubble styles
st.markdown(
    """
    <style>
    .chat-bubble { padding:10px 14px; border-radius:12px; max-width:80%; display:inline-block; box-shadow:0 2px 6px rgba(0,0,0,0.06); font-size:14px; line-height:1.4; }
    .chat-bubble.assistant { background:#f1f6ff; color:#08325a; border-radius:12px 12px 12px 4px; }
    .chat-bubble.user { background:#e6fff1; color:#044d2c; border-radius:12px 12px 4px 12px; }
    
    /* Emotion log expander boxes - light green to match buttons */
    [data-testid="stExpander"] details summary {
        background-color: #B4E7CE !important;
        border-radius: 8px !important;
        color: #2d5f4a !important;
        font-weight: 600 !important;
        padding: 12px 16px !important;
    }
    [data-testid="stExpander"] details summary:hover {
        background-color: #9dd9ba !important;
    }
    [data-testid="stExpander"] details {
        border: 1px solid #B4E7CE !important;
        border-radius: 8px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
# Ensure page default is set before rendering header controls
if "page" not in st.session_state:
    st.session_state["page"] = "home"
# Control whether the chat header (title + reset button) is visible.
# Default to False so Home doesn't show the chat header.
if "show_chat_header" not in st.session_state:
    st.session_state["show_chat_header"] = False
# Only show the top-row reset button and page title when on the chat page
if st.session_state.get("page", "chat") == "chat":
    row_col1, row_col2 = st.columns([3, 7])
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

    st.title("💬 Juno AI")
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
# Top-of-sidebar: quick Home button
if st.sidebar.button("home", key="sidebar_home"):
    st.session_state["page"] = "home"
    st.session_state["show_chat_header"] = False
    try:
        st.experimental_rerun()
    except Exception:
        pass

# Emotions page button
if st.sidebar.button("my emotions", key="sidebar_emotions"):
    st.session_state["page"] = "emotions"
    st.session_state["show_chat_header"] = False
    try:
        st.experimental_rerun()
    except Exception:
        pass

st.sidebar.header("sidebar")
st.sidebar.write("This demo does not store conversations.")
dev_mode = st.sidebar.checkbox("Developer mode (show intent)", value=False)

# Avatar images set in code
# To change the assistant/user profile pictures, edit these paths to point to image files
# included in the repo (e.g., `data/avatars/assistant.png` or `data/avatars/assistant.svg`).
# If the files are missing, the UI will fall back to emoji icons.
ASSISTANT_AVATAR_PNG = "data/avatars/assistant.png"
ASSISTANT_AVATAR_SVG = "data/avatars/assistant.svg"
USER_AVATAR_PNG = "data/avatars/user.png"
USER_AVATAR_SVG = "data/avatars/user.svg"

# Load avatar bytes if files exist (developer-editable, not user-uploaded).
# Prefer PNG if present, otherwise fall back to SVG.
assistant_avatar_bytes = None
user_avatar_bytes = None
try:
    if os.path.exists(ASSISTANT_AVATAR_PNG):
        with open(ASSISTANT_AVATAR_PNG, "rb") as _f:
            assistant_avatar_bytes = _f.read()
    elif os.path.exists(ASSISTANT_AVATAR_SVG):
        with open(ASSISTANT_AVATAR_SVG, "rb") as _f:
            assistant_avatar_bytes = _f.read()
except Exception:
    assistant_avatar_bytes = None

try:
    if os.path.exists(USER_AVATAR_PNG):
        with open(USER_AVATAR_PNG, "rb") as _f:
            user_avatar_bytes = _f.read()
    elif os.path.exists(USER_AVATAR_SVG):
        with open(USER_AVATAR_SVG, "rb") as _f:
            user_avatar_bytes = _f.read()
except Exception:
    user_avatar_bytes = None


# Load RAG cards once
cards = load_cards()

# Emotions analytics page
if st.session_state.get("page") == "emotions":
    st.title("Emotion Analytics")
    st.markdown("Track your emotional journey during this session.")
    
    # Load emotion logs from chat_sessions.jsonl
    def load_emotion_logs():
        """Load and parse emotion data from chat_sessions.jsonl"""
        import json
        from pathlib import Path
        from datetime import datetime
        
        log_path = Path("logs/chat_sessions.jsonl")
        emotions = []
        
        if not log_path.exists():
            return emotions
        
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        entry = json.loads(line)
                        # Extract relevant fields
                        emotions.append({
                            "timestamp": entry.get("ts_utc", ""),
                            "intent": entry.get("intent", "unknown"),
                            "tone": entry.get("tone", "unknown"),
                            "risk_level": entry.get("risk_level", "unknown"),
                            "session_id": entry.get("session_id", ""),
                            "turn_index": entry.get("turn_index", 0)
                        })
        except Exception as e:
            st.error(f"Error loading emotion logs: {e}")
        
        return emotions
    
    # Filter to current session only (show all messages including casual)
    emotion_logs = load_emotion_logs()
    current_session_id = st.session_state.get("session_id", "")
    session_emotions = [
        e for e in emotion_logs 
        if e["session_id"] == current_session_id
    ]
    
    if not session_emotions:
        st.info("No emotion data yet for this session. Start chatting to track your emotions!")
    else:
        st.subheader(f"Emotion Log ({len(session_emotions)} interactions)")
        
        # Display each logged emotion
        for idx, emotion in enumerate(session_emotions, 1):
            # Parse timestamp for display and convert UTC to EST
            try:
                from datetime import datetime, timezone, timedelta
                # Parse the UTC timestamp
                dt_utc = datetime.fromisoformat(emotion["timestamp"].replace("Z", "+00:00"))
                # Convert to EST (UTC-5)
                est_offset = timedelta(hours=-5)
                dt_est = dt_utc.astimezone(timezone(est_offset))
                time_str = dt_est.strftime("%I:%M %p on %b %d, %Y") + " EST"
            except:
                time_str = emotion["timestamp"]
            
            # Create an expandable card for each emotion entry
            with st.expander(f"interaction #{idx} - {time_str}", expanded=(idx == len(session_emotions))):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Primary Emotion (Intent)**")
                    # Map technical names to user-friendly display
                    intent = emotion["intent"]
                    display_intent = intent.replace('_', ' ').title()
                    if intent in ["other", "casual"]:
                        display_intent = "Casual Chat"
                    confidence = "High" if intent not in ["other", "casual"] else "Medium"
                    st.markdown(f" **{display_intent}** ({confidence} confidence)")
                    
                with col2:
                    st.markdown("**Emotional Tone**")
                    tone = emotion["tone"]
                    display_tone = tone.replace('_', ' ').title()
                    if tone in ["other", "casual"]:
                        display_tone = "Neutral"
                    tone_confidence = "High" if tone not in ["other", "casual"] else "Medium"
                    st.markdown(f"**{display_tone}** ({tone_confidence} confidence)")
                
                st.markdown("**Risk Assessment**")
                risk_color = {"low": "🟢", "moderate": "🟡", "high": "🔴"}.get(emotion["risk_level"].lower(), "⚪")
                st.markdown(f"{risk_color} **{emotion['risk_level'].capitalize()}** risk level")
        
        # Summary statistics
        st.divider()
        st.subheader("📈 Session Summary")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Most common intent (user-friendly display)
            from collections import Counter
            intent_counts = Counter([e["intent"] for e in session_emotions])
            most_common = intent_counts.most_common(1)[0] if intent_counts else ("none", 0)
            display_emotion = most_common[0].replace('_', ' ').title()
            st.metric("Most Common Emotion", display_emotion, f"{most_common[1]} times")
        
        with col2:
            # Average risk level (simplified)
            risk_levels = [e["risk_level"] for e in session_emotions]
            high_risk_count = sum(1 for r in risk_levels if r.lower() == "high")
            st.metric("High Risk Moments", high_risk_count)
        
        with col3:
            # Total interactions
            st.metric("Total Interactions", len(session_emotions))
    
    # Button to return to chat
    if st.button("💬 Back to Chat", key="emotions_to_chat"):
        st.session_state["page"] = "chat"
        st.session_state["show_chat_header"] = True
        try:
            st.experimental_rerun()
        except Exception:
            pass
    st.stop()

# Simple Home page: short welcome and a button to go to the chat
if st.session_state.get("page", "chat") == "home":
    # Apply baby pink background only to home page
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #FFE8F0;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    st.title("Home")
    st.markdown(
        """
        **Welcome to TeenMind Coach** — a friendly place to learn quick coping skills,
        find calming exercises, and get directed to help if you're in crisis.

        This is a placeholder home page you can edit later.
        """
    )
    st.write("Helpful links and project info can go here.")
    if st.button("💬 Go to Chat", key="home_go_chat"):
        st.session_state["page"] = "chat"
        st.session_state["show_chat_header"] = True
        try:
            st.experimental_rerun()
        except Exception:
            pass
    st.stop()

# Render chat history
def _render_message_with_avatar(msg: dict):
    role = msg.get("role")
    content = msg.get("content", "")

    def _avatar_img_tag(image_bytes: bytes, width: int = 48) -> str:
        """Return an HTML <img> tag (base64) for PNG/JPEG/SVG bytes with circular crop styles."""
        try:
            head = image_bytes.lstrip()[:10]
            if head.startswith(b"\x89PNG"):
                mime = "image/png"
            elif head.startswith(b"\xff\xd8"):
                mime = "image/jpeg"
            else:
                # treat as svg/xml
                mime = "image/svg+xml"
            b64 = base64.b64encode(image_bytes).decode("utf-8")
            return f'<img src="data:{mime};base64,{b64}" width="{width}" height="{width}" style="border-radius:50%;object-fit:cover;display:block;"/>'
        except Exception:
            return ""

    # Always place avatar on the left, message on the right (1:9 columns)
    col_avatar, col_msg = st.columns([1, 9])
    with col_avatar:
        if role == "assistant":
            if assistant_avatar_bytes:
                img_tag = _avatar_img_tag(assistant_avatar_bytes, width=48)
                if img_tag:
                    st.markdown(img_tag, unsafe_allow_html=True)
                else:
                    st.markdown("💬")
            else:
                st.markdown("💬")
        else:
            if user_avatar_bytes:
                img_tag = _avatar_img_tag(user_avatar_bytes, width=48)
                if img_tag:
                    st.markdown(img_tag, unsafe_allow_html=True)
                else:
                    st.markdown("🙂")
            else:
                st.markdown("🙂")
    with col_msg:
        # Escape user content to avoid HTML injection and preserve newlines
        safe = html.escape(content)
        safe = safe.replace('\n', '<br/>')
        bubble_class = 'assistant' if role == 'assistant' else 'user'
        st.markdown(f'<div class="chat-bubble {bubble_class}">{safe}</div>', unsafe_allow_html=True)

previous_role = None
for msg in st.session_state["messages"]:
    # Add a subtle divider when the speaker changes (helps separate turns on small screens)
    if previous_role and previous_role != msg.get("role"):
        st.markdown("<hr style='border:none;border-top:1px solid #eee;margin:8px 0;'/>", unsafe_allow_html=True)
    _render_message_with_avatar(msg)
    previous_role = msg.get("role")

user_text = st.chat_input("type a message…")

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
    return "insufficient information"

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
    # Add user message to session and render with custom avatar (avoid Streamlit default avatar)
    st.session_state["messages"].append({"role": "user", "content": user_text})
    # If the previous message was from a different role, show a divider first
    if len(st.session_state["messages"]) >= 2:
        prev = st.session_state["messages"][-2]
        if prev.get("role") != "user":
            st.markdown("<hr style='border:none;border-top:1px solid #eee;margin:8px 0;'/>", unsafe_allow_html=True)
    _render_message_with_avatar({"role": "user", "content": user_text})

    # Safety first
    if crisis_check(user_text):
        bot = crisis_response()
        st.session_state["messages"].append({"role": "assistant", "content": bot})
        # Divider if previous role was different
        if len(st.session_state["messages"]) >= 2:
            prev = st.session_state["messages"][-2]
            if prev.get("role") != "assistant":
                st.markdown("<hr style='border:none;border-top:1px solid #eee;margin:8px 0;'/>", unsafe_allow_html=True)
        _render_message_with_avatar({"role": "assistant", "content": bot})
        st.stop()

    # First pass: call model with general context to get intent
    # Use a broad skill card selection initially
    initial_intent = cheap_intent_heuristic(user_text)
    initial_cards = retrieve_cards(cards, intent=initial_intent, k=2)
    initial_context = format_cards_for_prompt(initial_cards)
    
    # Call model to get structured response with proper intent classification
    result = call_model(user_text, initial_context)
    
    # Use the model's intent for session state and potential re-retrieval
    model_intent = result.get("intent", "stress")
    st.session_state["intent"] = model_intent

    if dev_mode:
        st.sidebar.success(f"Heuristic intent: {initial_intent}")
        st.sidebar.success(f"Model intent: {model_intent}")
        st.sidebar.write("Retrieved cards:")
        for c in initial_cards:
            st.sidebar.write(f"- {c['title']}")
    # Show assistant message to user using custom avatar renderer
    bot_text = result["assistant_message"]
    st.session_state["messages"].append({"role": "assistant", "content": bot_text})
    # Divider if previous role was different
    if len(st.session_state["messages"]) >= 2:
        prev = st.session_state["messages"][-2]
        if prev.get("role") != "assistant":
            st.markdown("<hr style='border:none;border-top:1px solid #eee;margin:8px 0;'/>", unsafe_allow_html=True)
    _render_message_with_avatar({"role": "assistant", "content": bot_text})

    # Log structured fields (NO raw user text stored)
    log_turn({
        "session_id": st.session_state["session_id"],
        "turn_index": len(st.session_state["messages"]),
        "intent": result["intent"],
        "tone": result["tone"],
        "risk_level": result["risk_level"],
        "should_offer_skill": result["should_offer_skill"],
    })


