from __future__ import annotations
import os 
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from safety import crisis_check, crisis_response
from rag import load_cards, retrieve_cards, retrieve_combined_context
from prompts import SYSTEM_PROMPT, format_cards_for_prompt, format_combined_context
from schema import COACH_OUTPUT_SCHEMA
from timeline_page import render_timeline
from emotions_page import render_emotions
from info_page import render_info
from welcome_screen import show_welcome_screen
from journal_page import render_journal
import json
import html
import base64
import uuid 
from emotion_logger import log_turn


load_dotenv()

st.set_page_config(
    page_title="TeenMind Coach", 
    page_icon="💬", 
    initial_sidebar_state="collapsed"
)
# Custom button styling: make buttons look like pastel green rounded "bubbles".
# Scoped to `.stButton > button:first-child` so it primarily affects the left/top button.
st.markdown(
    """
    <style>
    /* primary bubble button style - pastel green */
    div.stButton > button:first-child {
        background-color: #A8D5BA;
        color: #2d5f4a;
        border: none;
        border-radius: 24px;
        padding: 8px 18px;
        box-shadow: 0 6px 18px rgba(168, 213, 186, 0.28);
        font-weight: 600;
        transition: background-color 0.12s ease-in-out, transform 0.08s ease, box-shadow 0.12s ease-in-out;
    }
    div.stButton > button:first-child:hover {
        background-color: #8fc5a3;
        transform: translateY(-1px);
        box-shadow: 0 0 20px rgba(168, 213, 186, 0.8);
    }
    div.stButton > button:first-child:active {
        transform: translateY(0);
        box-shadow: 0 3px 8px rgba(168, 213, 186, 0.22);
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
        background-color: #A8D5BA !important;
        border-radius: 8px !important;
        color: #2d5f4a !important;
        font-weight: 600 !important;
        padding: 12px 16px !important;
    }
    [data-testid="stExpander"] details summary:hover {
        background-color: #8fc5a3 !important;
    }
    [data-testid="stExpander"] details {
        border: 1px solid #A8D5BA !important;
        border-radius: 8px !important;
    }
    
    /* Chat input styling - thicker inward border with green glow */
    [data-testid="stChatInput"] {
        border-radius: 24px !important;
        border: 5px solid #8fc5a3 !important;
        box-shadow: 0 0 0 1px white, 0 0 30px rgba(143, 197, 163, 1), 0 0 50px rgba(143, 197, 163, 0.6) !important;
        background-color: white !important;
    }
    [data-testid="stChatInput"]:focus-within {
        border: 5px solid #8fc5a3 !important;
        box-shadow: 0 0 0 1px white, 0 0 30px rgba(143, 197, 163, 1), 0 0 50px rgba(143, 197, 163, 0.6) !important;
    }
    [data-testid="stChatInput"] textarea {
        border: none !important;
    }
    [data-testid="stChatInput"] textarea:focus {
        outline: none !important;
        border: none !important;
        box-shadow: none !important;
    }
    /* Additional overrides for chat input focus states */
    .stChatInputContainer {
        border-radius: 24px !important;
        border: 5px solid #8fc5a3 !important;
        box-shadow: 0 0 0 1px white, 0 0 30px rgba(143, 197, 163, 1), 0 0 50px rgba(143, 197, 163, 0.6) !important;
        background-color: white !important;
    }
    .stChatInputContainer:focus-within {
        border: 5px solid #8fc5a3 !important;
        box-shadow: 0 0 0 1px white, 0 0 30px rgba(143, 197, 163, 1), 0 0 50px rgba(143, 197, 163, 0.6) !important;
    }
    .stChatInputContainer textarea:focus {
        outline: none !important;
        box-shadow: none !important;
    }
    /* Force override Streamlit's default focus ring */
    [data-testid="stChatInput"] textarea:focus-visible {
        outline: none !important;
        outline-color: transparent !important;
        outline-width: 0 !important;
    }
    [data-baseweb="textarea"] {
        border: none !important;
    }
    [data-baseweb="textarea"]:focus,
    [data-baseweb="textarea"]:focus-within,
    [data-baseweb="textarea"]:active {
        outline: none !important;
        box-shadow: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Welcome screen state - check if it should be shown (only on first load)
if "welcome_shown" not in st.session_state:
    st.session_state["welcome_shown"] = False
    st.session_state["show_welcome_overlay"] = True
else:
    # If user navigates back to home, don't show welcome again
    if "show_welcome_overlay" not in st.session_state:
        st.session_state["show_welcome_overlay"] = False

# Ensure page default is set before rendering header controls
if "page" not in st.session_state:
    st.session_state["page"] = "home"

# Only show the top-row reset button and page title when on the chat page
if st.session_state.get("page") == "chat":
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #FAF7F5;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    row_col1, row_col2 = st.columns([3, 7])
    with row_col1:
        if st.button("reset chat", key="reset_chat"):
            # Reset only the on-screen messages for this session
            st.session_state["messages"] = [
                {"role": "assistant", "content": "Hey — I'm here with you. What's been going on today?"}
            ]
            st.rerun()
    with row_col2:
        # leave space to keep the button visually on the left/top
        pass

    st.title("💬 Juno AI")
    st.caption("A teen-focused coping-skills coach, not a therapist")

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
    st.rerun()

# Emotions page button
if st.sidebar.button("my emotions", key="sidebar_emotions"):
    st.session_state["page"] = "emotions"
    st.rerun()

# Timeline page button
if st.sidebar.button("timeline", key="sidebar_timeline"):
    st.session_state["page"] = "timeline"
    st.rerun()

# Journal page button
if st.sidebar.button("journal", key="sidebar_journal"):
    st.session_state["page"] = "journal"
    st.rerun()

# Info page button
if st.sidebar.button("interact", key="sidebar_info"):
    st.session_state["page"] = "info"
    st.rerun()

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
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #FAF7F5;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    render_emotions()
    st.stop()

# Timeline page
if st.session_state.get("page") == "timeline":
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #FAF7F5;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    render_timeline()
    st.stop()

# Journal page
if st.session_state.get("page") == "journal":
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #FAF7F5;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    render_journal()
    st.stop()

# Info page
if st.session_state.get("page") == "info":
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #FAF7F5;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    render_info()
    st.stop()

# Simple Home page: short welcome and a button to go to the chat
if st.session_state.get("page", "chat") == "home":
    # Apply background to home page
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #FAF7F5;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    # Display title with animated sprout gif overlay
    import base64
    with open('data/avatars/sprout.gif', 'rb') as f:
        gif_data = base64.b64encode(f.read()).decode()
    
    # Load custom font
    with open('fonts/Chicken Rice.otf', 'rb') as f:
        font_data = base64.b64encode(f.read()).decode()
    
    st.markdown(
        f"""
        <style>
        @font-face {{
            font-family: 'ChickenRice';
            src: url(data:font/opentype;base64,{font_data}) format('opentype');
            font-weight: normal;
            font-style: normal;
        }}
        .home-title-container {{
            position: relative;
            display: inline-block;
        }}
        .home-title-text {{
            font-family: 'ChickenRice', cursive, sans-serif !important;
            font-size: 3.5rem;
            font-weight: normal;
            margin: 0;
            padding-left: 0;
            position: relative;
            z-index: 2;
        }}
        .sprout-overlay {{
            position: absolute;
            top: -20px;
            left: -10px;
            width: 120px;
            height: 120px;
            pointer-events: none;
            z-index: 1;
        }}
        </style>
        <div class="home-title-container">
            <img src="data:image/gif;base64,{gif_data}" class="sprout-overlay">
            <h1 class="home-title-text">juno ai</h1>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown(
        """
        **Welcome back!** — a friendly place to learn quick coping skills,
        find calming exercises, and get directed to help if you're in crisis.

        This is a placeholder home page you can edit later.
        """
    )
    st.write("Helpful links and project info can go here.")
    
    if st.button("💬 chat now", key="home_go_chat"):
        st.session_state["page"] = "chat"
        st.rerun()
    
    # Add some spacing
    st.write("")
    st.write("")
    st.write("")
    
    # Circular emotions icon button
    try:
        with open('data/avatars/juno_emotions.png', 'rb') as f:
            emotions_icon_data = base64.b64encode(f.read()).decode()
        
        # CSS to hide the button initially until JavaScript replaces it
        st.markdown("""
            <style>
            button[data-testid="baseButton-secondary"]:has(div:contains(".")) {
                opacity: 0 !important;
                transition: opacity 0.1s ease-in;
            }
            </style>
        """, unsafe_allow_html=True)
        
        # Create button with unique placeholder text that will be replaced
        if st.button(".", key="home_emotions_btn"):
            st.session_state["page"] = "emotions"
            st.rerun()
        
        # JavaScript to replace button content with image (with retry mechanism)
        st.components.v1.html(
            f"""
            <script>
                function replaceButtonWithImage() {{
                    const buttons = window.parent.document.querySelectorAll('button');
                    let found = false;
                    buttons.forEach(btn => {{
                        if (btn.innerText.trim() === '.') {{
                            btn.innerHTML = '<img src="data:image/png;base64,{emotions_icon_data}" style="width:120px;height:120px;border-radius:50%;object-fit:cover;display:block;margin:0 auto;padding:0;" />';
                            btn.style.width = '128px';
                            btn.style.height = '128px';
                            btn.style.minHeight = '128px';
                            btn.style.minWidth = '128px';
                            btn.style.padding = '4px';
                            btn.style.borderRadius = '50%';
                            btn.style.border = 'none';
                            btn.style.display = 'flex';
                            btn.style.alignItems = 'center';
                            btn.style.justifyContent = 'center';
                            btn.style.opacity = '1';
                            btn.style.transition = 'opacity 0.2s ease-in';
                            found = true;
                        }}
                    }});
                    if (!found) {{
                        setTimeout(replaceButtonWithImage, 10);
                    }}
                }}
                replaceButtonWithImage();
                setTimeout(replaceButtonWithImage, 5);
                setTimeout(replaceButtonWithImage, 10);
            </script>
            """,
            height=0,
            width=0
        )
    except Exception:
        pass  # Silently fail if image not found
    
    # Show welcome overlay on top of home page
    if st.session_state.get("show_welcome_overlay", False):
        show_welcome_screen()
    
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
    # Add wrapper with negative margin to reduce spacing
    st.markdown('<div style="margin-top: -1.5rem; margin-bottom: -1rem;">', unsafe_allow_html=True)
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
            st.markdown("<p style='text-align: center; font-size: 0.75rem; color: #6b8e7f; margin-top: 4px; margin-left: -10px;'>juno</p>", unsafe_allow_html=True)
        else:
            if user_avatar_bytes:
                img_tag = _avatar_img_tag(user_avatar_bytes, width=48)
                if img_tag:
                    st.markdown(img_tag, unsafe_allow_html=True)
                else:
                    st.markdown("🙂")
            else:
                st.markdown("🙂")
            st.markdown("<p style='text-align: center; font-size: 0.75rem; color: #6b8e7f; margin-top: 4px; margin-left: -10px;'>me</p>", unsafe_allow_html=True)
    with col_msg:
        # Escape user content to avoid HTML injection and preserve newlines
        safe = html.escape(content)
        safe = safe.replace('\n', '<br/>')
        bubble_class = 'assistant' if role == 'assistant' else 'user'
        st.markdown(f'<div class="chat-bubble {bubble_class}">{safe}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def call_model(user_message: str, rag_context: str, conversation_history: list = None) -> str:
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

    # Use Chat Completions API with JSON mode
    # Model provides explicit confidence scores in the JSON response
    
    # Build the prompt with schema categories
    schema_to_send = None
    if isinstance(COACH_OUTPUT_SCHEMA, dict) and "schema" in COACH_OUTPUT_SCHEMA:
        schema_to_send = COACH_OUTPUT_SCHEMA["schema"]
    else:
        schema_to_send = COACH_OUTPUT_SCHEMA
    
    # Extract intent and tone options from schema
    intent_options = schema_to_send["properties"]["intent"]["enum"]
    tone_options = schema_to_send["properties"]["tone"]["enum"]
    
    # Create a prompt that includes the schema structure with explicit confidence scores
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

CRITICAL - Confidence Scoring:
Provide REALISTIC confidence scores (0.0-1.0) based on classification certainty. DO NOT default to 0.9 or 1.0.

Guidelines:
- Simple greetings ("hi", "hey", "thanks"): 0.95-0.99 (extremely obvious)
- Clear emotional statements ("I'm so stressed", "I feel happy"): 0.85-0.95
- Contextual clues ("my test is tomorrow and I can't focus"): 0.70-0.85
- Subtle indicators ("things are okay I guess"): 0.50-0.70
- Ambiguous messages: 0.30-0.50
- Very unclear: below 0.30

Use the FULL range. Don't cluster around 0.9 or round to 1.0 unless truly 100% certain.
Confidence scores should reflect the model's true certainty about the classifications.
Confidence scores should be different for both primary emotion and emotional tone based on the input. 
"""

    # Build messages with conversation history
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + "\n\n" + schema_prompt},
        {"role": "system", "content": "Coping skill cards (use only these):\n\n" + rag_context},
    ]
    
    # Add conversation history if provided
    if conversation_history:
        for msg in conversation_history[:-1]:  # Exclude the current message we're about to add
            if msg.get("role") in ["user", "assistant"]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
    
    # Add current user message
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        response_format={"type": "json_object"}
    )

    # Parse the response - model provides confidence scores
    parsed = None
    try:
        content = response.choices[0].message.content
        result = json.loads(content)
        
        # Use model's confidence scores (already in result)
        # Set defaults if missing
        if "intent_confidence" not in result:
            result["intent_confidence"] = 0.5
        if "tone_confidence" not in result:
            result["tone_confidence"] = 0.5
                
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

# Only render chat interface when on chat page
if st.session_state.get("page") == "chat":
    for msg in st.session_state["messages"]:
        _render_message_with_avatar(msg)

    st.markdown("<br><br>", unsafe_allow_html=True)
    user_text = st.chat_input("you can start anywhere...")

    if user_text:
        # Add user message to session and render with custom avatar (avoid Streamlit default avatar)
        st.session_state["messages"].append({"role": "user", "content": user_text})
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
        
        # Retrieve both skill cards AND relevant documents from Google Drive
        # The AI will use both sources to provide comprehensive support
        # Use broader retrieval initially since we don't know intent yet
        context_data = retrieve_combined_context(
            cards=cards,
            user_message=user_text,
            intent="",  # Empty intent to get cards based on message content
            k_cards=4,  # Get more cards for better variety
            k_docs=2
        )
        
        # Format the combined context for the prompt
        combined_context = format_combined_context(
            skill_cards=context_data["skill_cards"],
            documents=context_data["documents"]
        )
        
        # Call model to get structured response with proper intent classification
        result = call_model(user_text, combined_context, st.session_state["messages"])
        
        # Clear typing indicator
        typing_placeholder.empty()
        
        # Use the model's intent for session state
        model_intent = result.get("intent", "stress")
        st.session_state["intent"] = model_intent

        if dev_mode:
            st.sidebar.success(f"Model intent: {model_intent}")
            st.sidebar.write("Retrieved skill cards:")
            for c in context_data["skill_cards"]:
                st.sidebar.write(f"- {c['title']}")
            st.sidebar.write("Retrieved documents:")
            for d in context_data["documents"]:
                st.sidebar.write(f"- {d['title']} (similarity: {d.get('similarity', 0):.2f})")
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


