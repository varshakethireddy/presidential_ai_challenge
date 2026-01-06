import streamlit as st
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
import plotly.graph_objects as go

def render_timeline():
    """Render the emotional timeline page"""
    st.title("Emotional Timeline")
    st.caption("Track your emotional journey over time")
    
    # Load emotion logs for current session
    def load_timeline_emotions():
        log_path = Path("logs/chat_sessions.jsonl")
        if not log_path.exists():
            return []
        
        current_session = st.session_state["session_id"]
        emotions = []
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    if entry.get("session_id") == current_session:
                        emotions.append(entry)
        
        emotions.sort(key=lambda x: x.get("ts_utc", ""))
        return emotions
    
    # Map emotions to numerical values
    EMOTION_INTENSITY = {
        "panic": 9, "crisis": 10, "overwhelmed": 8, "test_anxiety": 7,
        "social_anxiety": 7, "grief": 8, "anger": 7, "fear": 7,
        "stress": 6, "sadness": 6, "loneliness": 6, "frustration": 5,
        "worry": 5, "nervous": 5, "uncertain": 4, "confused": 4,
        "tired": 4, "bored": 3, "calm": 2, "hopeful": 1, "happy": 1,
        "content": 1, "casual": 2, "other": 3,
    }
    
    TONE_INTENSITY = {
        "panicked": 10, "desperate": 9, "overwhelmed": 8, "worried": 7,
        "anxious": 7, "sad": 6, "frustrated": 6, "angry": 7, "scared": 7,
        "uncertain": 4, "confused": 4, "tired": 4, "neutral": 3,
        "calm": 2, "hopeful": 1, "relieved": 1, "content": 1,
        "casual": 2, "other": 3,
    }
    
    emotions = load_timeline_emotions()
    
    if not emotions:
        st.info("No emotion data yet. Start chatting with Juno to see your emotional timeline!")
    else:
        timestamps = []
        intent_values = []
        tone_values = []
        intent_labels = []
        tone_labels = []
        
        for emotion in emotions:
            try:
                dt_utc = datetime.fromisoformat(emotion["ts_utc"].replace("Z", "+00:00"))
                est_offset = timedelta(hours=-5)
                dt_est = dt_utc.astimezone(timezone(est_offset))
                timestamps.append(dt_est)
            except:
                continue
            
            intent = emotion.get("intent", "other")
            tone = emotion.get("tone", "neutral")
            
            intent_values.append(EMOTION_INTENSITY.get(intent, 3))
            tone_values.append(TONE_INTENSITY.get(tone, 3))
            intent_labels.append(intent.replace('_', ' ').title())
            tone_labels.append(tone.replace('_', ' ').title())
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=timestamps, y=intent_values, mode='lines+markers',
            name='Primary Emotion',
            line=dict(color='#7fc9a8', width=2.5, shape='spline'),
            marker=dict(size=8, color='#7fc9a8', symbol='circle'),
            hovertemplate='<b>%{text}</b><br>Time: %{x|%I:%M %p, %b %d}<br>Intensity: %{y}<extra></extra>',
            text=intent_labels, fill='tozeroy', fillcolor='rgba(127, 201, 168, 0.1)'
        ))
        
        fig.add_trace(go.Scatter(
            x=timestamps, y=tone_values, mode='lines+markers',
            name='Emotional Tone',
            line=dict(color='#ffa07a', width=2.5, shape='spline'),
            marker=dict(size=8, color='#ffa07a', symbol='diamond'),
            hovertemplate='<b>%{text}</b><br>Time: %{x|%I:%M %p, %b %d}<br>Intensity: %{y}<extra></extra>',
            text=tone_labels, fill='tozeroy', fillcolor='rgba(255, 160, 122, 0.1)'
        ))
        
        fig.add_hrect(y0=0, y1=3, fillcolor="rgba(144, 238, 144, 0.1)", line_width=0, annotation_text="Calm Zone", annotation_position="right")
        fig.add_hrect(y0=3, y1=6, fillcolor="rgba(255, 255, 153, 0.1)", line_width=0, annotation_text="Moderate Zone", annotation_position="right")
        fig.add_hrect(y0=6, y1=10, fillcolor="rgba(255, 182, 193, 0.1)", line_width=0, annotation_text="High Intensity Zone", annotation_position="right")
        
        fig.update_layout(
            title="Your Emotional Journey",
            xaxis_title="Time (EST)", yaxis_title="Emotional Intensity",
            hovermode='closest', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font=dict(size=12, color='#333'),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            yaxis=dict(range=[0, 10.5], tickmode='linear', tick0=0, dtick=2, gridcolor='rgba(200, 200, 200, 0.2)'),
            xaxis=dict(gridcolor='rgba(200, 200, 200, 0.2)', tickformat='%I:%M %p'),
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        st.subheader("📈 Insights")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            avg_intent = sum(intent_values) / len(intent_values) if intent_values else 0
            if avg_intent <= 3:
                status = "Generally Calm 🌿"
            elif avg_intent <= 6:
                status = "Moderate Stress 🌤️"
            else:
                status = "High Intensity ⚡"
            st.metric("Average Emotional State", status)
        
        with col2:
            high_intensity = sum(1 for v in intent_values if v >= 7)
            st.metric("High Intensity Moments", high_intensity)
        
        with col3:
            calm_moments = sum(1 for v in intent_values if v <= 3)
            st.metric("Calm Moments", calm_moments)
        
        st.divider()
        st.subheader("🔄 Recent Trend")
        
        if len(intent_values) >= 3:
            recent_avg = sum(intent_values[-3:]) / 3
            earlier_avg = sum(intent_values[:-3]) / len(intent_values[:-3]) if len(intent_values) > 3 else recent_avg
            
            if recent_avg < earlier_avg - 1:
                st.success("📉 Your emotions have been stabilizing recently")
            elif recent_avg > earlier_avg + 1:
                st.warning("📈 Your emotional intensity has increased lately. Remember, I'm here to help.")
            else:
                st.info("➡️ Your emotional state has been relatively stable")
    
    if st.button("💬 Back to Chat", key="timeline_to_chat"):
        st.session_state["page"] = "chat"
        st.session_state["show_chat_header"] = True
        try:
            st.experimental_rerun()
        except Exception:
            pass
