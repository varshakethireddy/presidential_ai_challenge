import streamlit as st
from datetime import datetime
from openai import OpenAI
import os
from db_utils import (
    save_journal_entry as db_save_journal,
    load_journal_entries as db_load_journal,
    get_latest_chat_emotion,
    get_recent_user_messages
)

def save_journal_entry(entry_data):
    """Save a journal entry to the database"""
    user_id = st.session_state.get("user_id")
    session_id = st.session_state.get("session_id")
    
    db_save_journal(
        user_id=user_id,
        session_id=session_id,
        content=entry_data.get("content"),
        ai_prompt=entry_data.get("ai_prompt")
    )

def load_journal_entries():
    """Load all journal entries for the current user"""
    user_id = st.session_state.get("user_id")
    return db_load_journal(user_id)

def get_recent_chat_messages():
    """Get recent chat messages for context"""
    user_id = st.session_state.get("user_id")
    return get_recent_user_messages(user_id)

def get_latest_emotion():
    """Get the most recent emotion data"""
    user_id = st.session_state.get("user_id")
    return get_latest_chat_emotion(user_id)

def generate_journal_prompt(emotion_data):
    """Generate an AI-guided journal prompt based on the user's last message"""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Get the user's most recent chat message
    user_messages = get_recent_chat_messages()
    
    if user_messages:
        last_message = user_messages[-1]  # Focus on the very last message
        context = f"The user just said: \"{last_message}\""
    elif emotion_data:
        intent = emotion_data.get("latest_intent", "other")
        tone = emotion_data.get("latest_tone", "neutral")
        context = f"The user recently expressed feeling {intent} with a {tone} tone."
    else:
        context = "No recent chat data available."
    
    prompt = f"""You are Juno, a creative journal prompt generator for teens.
    
{context}

Based on what the user JUST shared in their last message, generate ONE short, creative journal prompt (1-2 sentences MAX) that:
- Connects directly to what they JUST talked about in their last message
- Gives them a concrete, creative way to explore that specific topic deeper
- Uses an interesting angle (scenarios, objects, time, "what if" questions)
- Feels personal and relevant to what THEY just said, not generic
- Avoids just asking "how do you feel" or restating what they said


Good examples:
- "What's one thing you wish you could tell someone right now but haven't yet?"
- "If you could pause time for 10 minutes today, what would you do in that silence?"
- "Choose a random object near you. If it could narrate your day honestly, what would it say?"

Keep it brief, specific, and connected to their LAST message. Just provide the prompt, nothing else."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are Juno, a creative AI companion for teens. Generate brief, specific journal prompts based on what the user just shared."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.85,
            max_tokens=100
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return "What's something small that happened today that actually mattered to you?"

def render_journal_gallery():
    """Render the journal gallery page"""
    st.markdown("<h1 style='font-family: ChickenRice, cursive, sans-serif;'>Journal</h1>", unsafe_allow_html=True)
    st.markdown("Your personal space for reflection and self-expression.")
    
    # New Entry Button
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("✢ new entry", key="new_journal_entry", use_container_width=True):
            st.session_state["journal_view"] = "write"
            st.rerun()
    
    st.divider()
    
    # Load and display entries
    entries = load_journal_entries()
    
    if not entries:
        st.markdown(
            '<div style="background-color: #e8f4f8; color: #0c5460; padding: 20px; border-radius: 12px; text-align: center; margin-top: 40px;">'
            '<p style="font-size: 1.1rem; margin-bottom: 8px;">🌱 your journal is waiting for you!</p>'
            '<p style="font-size: 0.9rem; color: #6b8e7f;">Start writing to capture your thoughts and feelings.</p>'
            '</div>',
            unsafe_allow_html=True
        )
    else:
        st.subheader(f"Your Entries ({len(entries)})")
        
        for idx, entry in enumerate(entries):
            # Parse date
            try:
                entry_date = datetime.fromisoformat(entry["timestamp"])
                date_str = entry_date.strftime("%B %d, %Y at %I:%M %p")
            except:
                date_str = entry.get("timestamp", "Unknown date")
            
            # Create expandable entry card
            with st.expander(f"✎ {date_str}", expanded=(idx == 0)):
                content = entry.get("content", "")
                
                # Display content
                st.markdown(
                    f'<div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #A8D5BA;">'
                    f'<p style="white-space: pre-wrap; color: #333; line-height: 1.6;">{content}</p>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                
                # Show prompt if it was AI-guided
                if entry.get("ai_prompt"):
                    st.markdown(
                        f'<p style="font-size: 0.85rem; color: #6b8e7f; margin-top: 10px; font-style: italic;">💭 prompt: {entry["ai_prompt"]}</p>',
                        unsafe_allow_html=True
                    )
    
    st.write("")
    st.write("")
    
    # Back to chat button
    if st.button("💬 Back to Chat", key="journal_to_chat"):
        st.session_state["page"] = "chat"
        st.rerun()

def render_journal_write():
    """Render the journal writing page"""
    # Get current date
    current_date = datetime.now().strftime("%B %d, %Y")
    
    st.markdown(
        f'<h1 style="font-family: ChickenRice, cursive, sans-serif;">{current_date}</h1>',
        unsafe_allow_html=True
    )
    
    # AI Prompt section
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("✨ guided prompt", key="ai_prompt_btn", use_container_width=True):
            st.session_state["show_prompt"] = True
            st.session_state["current_prompt"] = None
    
    # Display AI prompt if requested
    if st.session_state.get("show_prompt", False):
        if st.session_state.get("current_prompt") is None:
            with st.spinner("Generating prompt..."):
                emotion_data = get_latest_emotion()
                prompt = generate_journal_prompt(emotion_data)
                st.session_state["current_prompt"] = prompt
        
        prompt_text = st.session_state["current_prompt"]
        
        st.markdown(
            f'<div style="background-color: #ffe6f0; padding: 15px; border-radius: 10px; border-left: 4px solid #ff69b4; margin-bottom: 20px;">'
            f'<p style="color: #d63384; font-size: 1rem; margin-bottom: 10px;"><strong>💭 Suggested Prompt:</strong></p>'
            f'<p style="color: #333; font-size: 0.95rem; line-height: 1.5;">{prompt_text}</p>'
            f'</div>',
            unsafe_allow_html=True
        )
        
        # Regenerate and Discard buttons
        btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 3])
        with btn_col1:
            if st.button("regenerate ⟳", key="regenerate_prompt"):
                st.session_state["current_prompt"] = None
                st.rerun()
        with btn_col2:
            if st.button("discard", key="discard_prompt"):
                st.session_state["show_prompt"] = False
                st.session_state["current_prompt"] = None
                st.rerun()
    
    st.divider()
    
    # Custom CSS for green border on text area with notebook lines
    st.markdown("""
        <style>
        textarea[aria-label="Start writing..."] {
            border: 3px solid #8fc5a3 !important;
            background-color: #f8f9fa !important;
            background-image: repeating-linear-gradient(
                transparent,
                transparent 31px,
                #d1d5db 31px,
                #d1d5db 32px
            ) !important;
            line-height: 32px !important;
            padding-top: 8px !important;
            padding-bottom: 8px !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Text area for writing
    journal_content = st.text_area(
        "Start writing...",
        height=400,
        key="journal_text_area",
        placeholder="What's on your mind today? Let your thoughts flow freely...",
        label_visibility="collapsed"
    )
    
    st.write("")
    
    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 3])
    
    with col1:
        if st.button("✎ save", key="save_journal", use_container_width=True):
            if journal_content.strip():
                # Save entry
                entry_data = {
                    "session_id": st.session_state.get("session_id"),
                    "timestamp": datetime.now().isoformat(),
                    "content": journal_content,
                    "ai_prompt": st.session_state.get("current_prompt") if st.session_state.get("show_prompt") else None
                }
                save_journal_entry(entry_data)
                
                # Reset state
                st.session_state["show_prompt"] = False
                st.session_state["current_prompt"] = None
                st.session_state["journal_view"] = "gallery"
                
                st.success("✓ entry saved!")
                st.rerun()
            else:
                st.warning("please write something before saving.")
    
    with col2:
        if st.button("← gallery", key="back_to_gallery", use_container_width=True):
            st.session_state["journal_view"] = "gallery"
            st.session_state["show_prompt"] = False
            st.session_state["current_prompt"] = None
            st.rerun()

def render_journal():
    """Main journal render function"""
    # Initialize journal view state
    if "journal_view" not in st.session_state:
        st.session_state["journal_view"] = "gallery"
    
    if st.session_state["journal_view"] == "write":
        render_journal_write()
    else:
        render_journal_gallery()
