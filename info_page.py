import streamlit as st

def render_info():
    """Render the interact/how to use page"""
    st.title("How to Interact with Juno")
    
    st.markdown("""
    ### Getting Started
    
    Juno is your AI mental health companion, here to listen, support, and guide you through difficult moments. 
    Here's how to get the most out of your conversations:
    
    ### 💬 How to Talk to Juno
    
    **Be Open and Honest**
    - Share what's really on your mind - Juno is here to help, not judge
    - You don't need to use formal language; just talk naturally
    - It's okay to be vulnerable about what you're feeling
    
    **Be Specific**
    - Instead of "I feel bad," try "I'm anxious about my math test tomorrow"
    - The more details you share, the better Juno can support you
    - Describe your emotions, situations, and what triggered them
    
    **Ask for What You Need**
    - Looking for coping strategies? Just ask: "Can you help me calm down?"
    - Need to vent? Say: "I just need someone to listen right now"
    - Want resources? Try: "Can you help me find support?"
    
    ### ✅ What Juno Can Do
    
    ✓ Listen without judgment to whatever you're going through
    
    ✓ Help you identify and understand your emotions
    
    ✓ Teach coping skills for anxiety, stress, and difficult feelings
    
    ✓ Guide you through breathing exercises and grounding techniques
    
    ✓ Provide crisis resources when you need professional help
    
    ✓ Track your emotional patterns over time
    
    ### ❌ What Juno Can't Do
    
    ✗ Diagnose mental health conditions (only professionals can do this)
    
    ✗ Prescribe medication or replace therapy
    
    ✗ Provide emergency intervention (call 988 for crisis support)
    
    ✗ Make decisions for you about serious life choices
    
    ✗ Guarantee confidentiality if you're in immediate danger
    
    ### 🔒 Privacy & Safety
    
    **Your Privacy Matters**
    - Your conversations with Juno are logged to track your emotional journey
    - We never share your personal information with third parties
    - Data is stored securely and used only to improve your experience
    
    **Safety First**
    - If Juno detects you might be in crisis, it will offer professional resources
    - We take mentions of self-harm or suicide very seriously
    - Juno is NOT a replacement for emergency services or professional care
    
    **Important Limitations**
    - Juno is an AI and may occasionally misunderstand or make mistakes
    - If something feels wrong or unhelpful, it's okay to say so
    - Always trust your instincts about what feels right for you
    
    ### 🆘 When to Get Professional Help
    
    Reach out to a professional if you're experiencing:
    - Thoughts of harming yourself or others
    - Severe anxiety or panic attacks that interfere with daily life
    - Deep depression lasting more than two weeks
    - Significant changes in sleep, appetite, or behavior
    - Trauma that you can't process on your own
    
    **Crisis Resources:**
    - **988 Suicide & Crisis Lifeline**: Call or text 988
    - **Crisis Text Line**: Text HOME to 741741
    - **Teen Line**: 1-310-855-HOPE (4673), text TEEN to 839863
    
    ### 💡 Tips for Better Conversations
    
    1. **Start with how you're feeling** - "I'm stressed about school" or "I had a fight with my friend"
    2. **Be patient** - Sometimes it takes a few messages to get to what's really bothering you
    3. **Try suggested skills** - When Juno offers coping techniques, give them a try
    4. **Check your emotions log** - Review past conversations to spot patterns
    5. **Come back regularly** - Mental health is a journey, not a one-time fix
    
    ---
    
    *Remember: Juno is here to support you, but nothing replaces professional mental health care when you need it.*
    """)
    
    st.write("")
    st.write("")
    
    if st.button("💬 Start Chatting", key="info_to_chat"):
        st.session_state["page"] = "chat"
        st.session_state["show_chat_header"] = True
        try:
            st.experimental_rerun()
        except Exception:
            pass
