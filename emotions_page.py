import streamlit as st
from datetime import datetime, timezone, timedelta
from collections import Counter
from db_utils import load_chat_messages

def render_emotions():
    """Render the emotions analytics page"""
    st.markdown("<h1 style='font-family: ChickenRice, cursive, sans-serif;'>Emotion Analytics</h1>", unsafe_allow_html=True)
    st.markdown("Track your emotional journey during this session.")
    
    # Load emotion logs from database
    def load_emotion_logs():
        """Load and parse emotion data from database for current session"""
        user_id = st.session_state.get("user_id")
        session_id = st.session_state.get("session_id")
        
        if not user_id or not session_id:
            return []
        
        # Load messages from database
        messages = load_chat_messages(user_id, session_id)
        
        emotions = []
        for idx, msg in enumerate(messages):
            if msg.get("intent"):  # Only include messages with emotion data
                emotions.append({
                    "timestamp": msg.get("timestamp", ""),
                    "intent": msg.get("intent", "unknown"),
                    "tone": msg.get("tone", "unknown"),
                    "intent_confidence": 0.9,  # Database doesn't store confidence
                    "tone_confidence": 0.9,
                    "risk_level": "low",  # Can be enhanced if needed
                    "session_id": session_id,
                    "turn_index": idx
                })
        
        return emotions
    
    # Get emotions for current session
    session_emotions = load_emotion_logs()
    
    if not session_emotions:
        st.markdown(
            '<div style="background-color: #ffe0f0; color: #d63384; padding: 12px; border-radius: 8px; border-left: 4px solid #d63384;">No emotion data yet for this session. Start chatting to track your emotions!</div>',
            unsafe_allow_html=True
        )
    else:
        st.subheader(f"Emotion Log ({len(session_emotions)} interactions)")
        
        # Display each logged emotion
        for idx, emotion in enumerate(session_emotions, 1):
            # Parse timestamp for display and convert UTC to EST
            try:
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
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("**Primary Emotion**")
                    # Map technical names to user-friendly display
                    intent = emotion["intent"]
                    display_intent = intent.replace('_', ' ').title()
                    if intent in ["other", "casual"]:
                        display_intent = "Casual Chat"
                    
                    # Display model's confidence score with color-coded highlight
                    intent_conf = emotion.get("intent_confidence", 0.0)
                    confidence_pct = int(intent_conf * 100)
                    
                    # Determine background and text colors based on confidence level
                    if confidence_pct <= 50:
                        bg_color = "rgba(255, 204, 204, 0.3)"  # translucent light red
                        text_color = "#cc0000"  # darker red
                    elif confidence_pct <= 79:
                        bg_color = "rgba(255, 229, 180, 0.3)"  # translucent light orange
                        text_color = "#cc7a00"  # darker orange
                    else:
                        bg_color = "rgba(212, 241, 212, 0.3)"  # translucent light green
                        text_color = "#2d7a2d"  # darker green
                    
                    st.markdown(f"&nbsp;&nbsp;{display_intent}")
                    st.markdown(f"<span style='background-color: {bg_color}; color: {text_color}; padding: 2px 8px; border-radius: 4px; font-size: 0.85em; font-weight: 500;'>Confidence: {confidence_pct}%</span>", unsafe_allow_html=True)
                    
                with col2:
                    st.markdown("**Emotional Tone**")
                    tone = emotion["tone"]
                    display_tone = tone.replace('_', ' ').title()
                    if tone in ["other", "casual"]:
                        display_tone = "Neutral"
                    
                    # Display model's confidence score with color-coded highlight
                    tone_conf = emotion.get("tone_confidence", 0.0)
                    tone_confidence_pct = int(tone_conf * 100)
                    
                    # Determine background and text colors based on confidence level
                    if tone_confidence_pct <= 50:
                        bg_color = "rgba(255, 204, 204, 0.3)"  # translucent light red
                        text_color = "#cc0000"  # darker red
                    elif tone_confidence_pct <= 79:
                        bg_color = "rgba(255, 229, 180, 0.3)"  # translucent light orange
                        text_color = "#cc7a00"  # darker orange
                    else:
                        bg_color = "rgba(212, 241, 212, 0.3)"  # translucent light green
                        text_color = "#2d7a2d"  # darker green
                    
                    st.markdown(f"&nbsp;&nbsp;{display_tone}")
                    st.markdown(f"<span style='background-color: {bg_color}; color: {text_color}; padding: 2px 8px; border-radius: 4px; font-size: 0.85em; font-weight: 500;'>Confidence: {tone_confidence_pct}%</span>", unsafe_allow_html=True)
                
                with col3:
                    st.markdown("**Risk Assessment**")
                    risk_color = {"low": "🟢", "moderate": "🟡", "high": "🔴"}.get(emotion["risk_level"].lower(), "⚪")
                    st.markdown(f"{risk_color} {emotion['risk_level'].capitalize()} risk")
        
        # Summary statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Most common intent (user-friendly display)
            intent_counts = Counter([e["intent"] for e in session_emotions])
            most_common = intent_counts.most_common(1)[0] if intent_counts else ("none", 0)
            emotion_key = most_common[0]
            display_emotion = emotion_key.replace('_', ' ').title()
            
            # Map emotion to intensity level and assign color
            EMOTION_INTENSITY = {
                "panic": 9, "crisis": 10, "self_harm": 10, "overwhelmed": 8, "test_anxiety": 7,
                "social_anxiety": 7, "grief": 8, "anger": 7, "fear": 7,
                "stress": 6, "sadness": 6, "loneliness": 6, "frustration": 5,
                "worry": 5, "nervous": 5, "uncertain": 4, "confused": 4,
                "tired": 4, "bored": 3, "calm": 2, "hopeful": 1, "happy": 1,
                "content": 1, "casual": 2, "other": 2,
            }
            
            intensity = EMOTION_INTENSITY.get(emotion_key, 3)
            
            # Assign color based on intensity
            if intensity <= 3:
                bg_color = "#d4f1d4"  # green (calm)
                text_color = "#2d5f4a"
            elif intensity <= 6:
                bg_color = "#fff9e6"  # yellow (moderate)
                text_color = "#8b6914"
            else:
                bg_color = "#ffe6f0"  # pink (high intensity)
                text_color = "#d63384"
            
            st.markdown(f"<p style='font-size: 0.875rem; color: #666; margin-bottom: 0.25rem;'>Most Common Emotion</p><p style='background-color: {bg_color}; color: {text_color}; padding: 4px 8px; border-radius: 4px; font-size: 0.9rem; font-weight: 600; margin-top: 0; margin-bottom: 0.25rem; display: inline-block;'>{display_emotion}</p><p style='font-size: 0.75rem; color: #888; margin-top: 0.25rem;'>{most_common[1]} times</p>", unsafe_allow_html=True)
        
        with col2:
            # Average risk level (simplified)
            risk_levels = [e["risk_level"] for e in session_emotions]
            high_risk_count = sum(1 for r in risk_levels if r.lower() == "high")
            st.metric("High Risk Moments", high_risk_count)
        
        with col3:
            # Total interactions
            st.metric("Total Interactions", len(session_emotions))
    
    # Button to return to chat
    st.write("")
    st.write("")
    
    if st.button("💬 Back to Chat", key="emotions_to_chat"):
        st.session_state["page"] = "chat"
        st.session_state["show_chat_header"] = True
        try:
            st.experimental_rerun()
        except Exception:
            pass
