from __future__ import annotations
import os 
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from safety import crisis_check, crisis_response
from rag import load_cards, retrieve_cards
from prompts import SYSTEM_PROMPT, format_cards_for_prompt
from schema import COACH_OUTPUT_SCHEMA
from timeline_page import render_timeline
from emotions_page import render_emotions
from info_page import render_info
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
    .chat-bubble { 
        padding:11px 15px; 
        border-radius:18px; 
        max-width:80%; 
        display:inline-block; 
        box-shadow:0 2px 6px rgba(0,0,0,0.06); 
        font-size:14px; 
        line-height:1.4;
        position: relative;
    }
    .chat-bubble.assistant { 
        background:#f1f6ff; 
        color:#08325a; 
        border-bottom-left-radius: 6px;
    }
    .chat-bubble.assistant::before {
        content: '';
        position: absolute;
        bottom: 3px;
        left: -8px;
        width: 19px;
        height: 19px;
        background: radial-gradient(circle at 100% 0%, transparent 0%, transparent 68%, #f1f6ff 68%);
        transform: rotate(-45deg);
        border-radius: 2px;
    }
    .chat-bubble.user { 
        background:#e6fff1; 
        color:#044d2c;
        border-bottom-right-radius: 6px;
    }
    .chat-bubble.user::before {
        content: '';
        position: absolute;
        bottom: 3px;
        right: -8px;
        width: 19px;
        height: 19px;
        background: radial-gradient(circle at 0% 0%, transparent 70%, transparent 70%, #e6fff1 70%);
        transform: rotate(45deg);
        border-radius: 2px;
    }
    
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

# Timeline page button
if st.sidebar.button("timeline", key="sidebar_timeline"):
    st.session_state["page"] = "timeline"
    st.session_state["show_chat_header"] = False
    try:
        st.experimental_rerun()
    except Exception:
        pass

# Info page button
if st.sidebar.button("interact", key="sidebar_info"):
    st.session_state["page"] = "info"
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
    render_emotions()
    st.stop()

# Timeline page
if st.session_state.get("page") == "timeline":
    render_timeline()
    st.stop()

# Info page
if st.session_state.get("page") == "info":
    render_info()
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
    # Display title with animated sprout gif overlay
    import base64
    with open('sprout.gif', 'rb') as f:
        gif_data = base64.b64encode(f.read()).decode()
    
    st.markdown(
        f"""
        <style>
        .home-title-container {{
            position: relative;
            display: inline-block;
        }}
        .home-title-text {{
            font-size: 3rem;
            font-weight: 600;
            margin: 0;
            padding-left: 0;
        }}
        .sprout-overlay {{
            position: absolute;
            top: -20px;
            left: -10px;
            width: 120px;
            height: 120px;
            pointer-events: none;
        }}
        </style>
        <div class="home-title-container">
            <img src="data:image/gif;base64,{gif_data}" class="sprout-overlay">
            <h1 class="home-title-text">Home</h1>
        </div>
        """,
        unsafe_allow_html=True
    )
    
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

    # Use Chat Completions API with JSON mode to get logprobs
    # This gives us REAL confidence scores from the model's internal probabilities
    
    # Build the prompt with schema categories
    schema_to_send = None
    if isinstance(COACH_OUTPUT_SCHEMA, dict) and "schema" in COACH_OUTPUT_SCHEMA:
        schema_to_send = COACH_OUTPUT_SCHEMA["schema"]
    else:
        schema_to_send = COACH_OUTPUT_SCHEMA
    
    # Extract intent and tone options from schema
    intent_options = schema_to_send["properties"]["intent"]["enum"]
    tone_options = schema_to_send["properties"]["tone"]["enum"]
    
    # Create a prompt that includes the schema structure
    schema_prompt = f"""You must respond with valid JSON matching this schema:
{{
  "intent": one of {intent_options},
  "tone": one of {tone_options},
  "intent_confidence": number 0.0-1.0,
  "tone_confidence": number 0.0-1.0,
  "risk_level": "low" | "medium" | "high",
  "should_offer_skill": boolean,
  "assistant_message": string
}}

Analyze the user's emotional state carefully and provide confidence scores based on clarity of emotional expression."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT + "\n\n" + schema_prompt},
            {"role": "system", "content": "Coping skill cards (use only these):\n\n" + rag_context},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
        logprobs=True,
        top_logprobs=20  # Get top 20 tokens to see competing emotions
    )

    # Parse the response and extract logprobs for confidence
    parsed = None
    try:
        content = response.choices[0].message.content
        result = json.loads(content)
        
        # Extract REAL confidence from logprobs by finding specific emotion tokens
        if response.choices[0].logprobs and response.choices[0].logprobs.content:
            import math
            
            logprobs_content = response.choices[0].logprobs.content
            
            # Get the emotion values from the parsed result
            intent_value = result.get("intent", "")
            tone_value = result.get("tone", "")
            
            intent_confidence = None
            tone_confidence = None
            
            # Search through tokens to find where intent and tone values appear
            for token_data in logprobs_content:
                token_text = token_data.token.lower().strip().strip('"').strip(',')
                
                # Check if this token matches our intent value
                if intent_value and token_text == intent_value.lower().replace('_', ''):
                    if token_data.logprob is not None and intent_confidence is None:
                        intent_confidence = math.exp(token_data.logprob)
                
                # Also check with underscore in case token preserves it
                if intent_value and token_text == intent_value.lower():
                    if token_data.logprob is not None and intent_confidence is None:
                        intent_confidence = math.exp(token_data.logprob)
                
                # Check if this token matches our tone value
                if tone_value and token_text == tone_value.lower().replace('_', ''):
                    if token_data.logprob is not None and tone_confidence is None:
                        tone_confidence = math.exp(token_data.logprob)
                
                # Also check with underscore
                if tone_value and token_text == tone_value.lower():
                    if token_data.logprob is not None and tone_confidence is None:
                        tone_confidence = math.exp(token_data.logprob)
                
                # Stop once we've found both
                if intent_confidence is not None and tone_confidence is not None:
                    break
            
            # Apply the specific confidence scores
            if intent_confidence is not None:
                result["intent_confidence"] = round(intent_confidence, 3)
            if tone_confidence is not None:
                result["tone_confidence"] = round(tone_confidence, 3)
                
    except Exception as e:
        # Fallback if parsing fails
        result = {
            "intent": "stress",
            "tone": "calm",
            "intent_confidence": 0.5,
            "tone_confidence": 0.5,
            "risk_level": "low",
            "should_offer_skill": True,
            "assistant_message": "I'm having trouble analyzing that. Can you tell me more?"
        }
    
    return result

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
    crisis_check_bool = crisis_check(user_text)
    if crisis_check_bool:
        bot = crisis_response()
        st.session_state["messages"].append({"role": "assistant", "content": bot})
        # Divider if previous role was different
        if len(st.session_state["messages"]) >= 2:
            prev = st.session_state["messages"][-2]
            if prev.get("role") != "assistant":
                st.markdown("<hr style='border:none;border-top:1px solid #eee;margin:8px 0;'/>", unsafe_allow_html=True)
        _render_message_with_avatar({"role": "assistant", "content": bot})
        #st.stop()

    # Show typing indicator while processing
    typing_placeholder = st.empty()
    with typing_placeholder:
        st.markdown(
            """
            <style>
            @keyframes typing-dot {
                0%, 60%, 100% { opacity: 0.3; }
                30% { opacity: 1; }
            }
            .typing-container {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 12px 0;
            }
            .typing-text {
                color: #666;
                font-style: italic;
                font-size: 14px;
                line-height: 1.4;
            }
            .typing-dots {
                display: flex;
                gap: 4px;
                align-items: center;
            }
            .typing-dot {
                width: 8px;
                height: 8px;
                background-color: #7fc9a8;
                border-radius: 50%;
                animation: typing-dot 1.4s infinite;
            }
            .typing-dot:nth-child(1) {
                animation-delay: 0s;
            }
            .typing-dot:nth-child(2) {
                animation-delay: 0.2s;
            }
            .typing-dot:nth-child(3) {
                animation-delay: 0.4s;
            }
            </style>
            <div class='typing-container'>
                <span class='typing-text'>juno is typing</span>
                <div class='typing-dots'>
                    <span class='typing-dot'></span>
                    <span class='typing-dot'></span>
                    <span class='typing-dot'></span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Retrieve a broader set of skill cards for context
    # The AI will determine the actual intent and select relevant skills
    initial_cards = retrieve_cards(cards, intent="stress", k=3)  # Use broader retrieval
    initial_context = format_cards_for_prompt(initial_cards)
    
    # Call model to get structured response with proper intent classification
    result = call_model(user_text, initial_context)
    
    # Clear typing indicator
    typing_placeholder.empty()
    
    # Use the model's intent for session state
    model_intent = result.get("intent", "stress")
    st.session_state["intent"] = model_intent

    if dev_mode:
        st.sidebar.success(f"Model intent: {model_intent}")
        st.sidebar.write("Retrieved cards:")
        for c in initial_cards:
            st.sidebar.write(f"- {c['title']}")
    # Show assistant message to user using custom avatar renderer
    bot_text = result["assistant_message"]
    if not crisis_check_bool:
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
        "intent_confidence": result.get("intent_confidence", 0.0),
        "tone_confidence": result.get("tone_confidence", 0.0),
        "risk_level": result["risk_level"],
        "should_offer_skill": result["should_offer_skill"],
    })


