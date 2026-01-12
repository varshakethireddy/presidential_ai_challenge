import streamlit as st
from datetime import datetime, timezone, timedelta
import plotly.graph_objects as go
from openai import OpenAI
import os
from PIL import Image
import base64
from io import BytesIO
from db_utils import get_user_chat_history

def image_to_base64(img):
    """Convert PIL Image to base64 string"""
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def render_timeline():
    """Render the emotional timeline page"""
    st.title("Emotional Timeline")
    st.markdown("Track your emotional journey over time.")
    
    # Load emotion logs for current user
    def load_timeline_emotions():
        user_id = st.session_state.get("user_id")
        return get_user_chat_history(user_id)
    
    # Map emotions to numerical values
    EMOTION_INTENSITY = {
        "panic": 9, "crisis": 10, "self_harm": 10, "overwhelmed": 8, "test_anxiety": 7,
        "social_anxiety": 7, "grief": 8, "anger": 7, "fear": 7,
        "stress": 6, "sadness": 6, "loneliness": 6, "frustration": 5,
        "worry": 5, "nervous": 5, "uncertain": 4, "confused": 4,
        "tired": 4, "bored": 3, "calm": 2, "hopeful": 1, "happy": 1,
        "content": 1, "casual": 2, "other": 2,
    }
    
    TONE_INTENSITY = {
        "panicked": 10, "desperate": 9, "overwhelmed": 8, "worried": 7,
        "anxious": 7, "sad": 6, "frustrated": 6, "angry": 7, "scared": 7,
        "uncertain": 4, "confused": 4, "tired": 4, "neutral": 3, "numb": 5,
        "calm": 2, "hopeful": 1, "relieved": 1, "content": 1,
        "casual": 2, "other": 2,
    }
    
    emotions = load_timeline_emotions()
    
    if not emotions:
        st.markdown(
            '<div style="background-color: #ffe0f0; color: #d63384; padding: 12px; border-radius: 8px; border-left: 4px solid #d63384;"> No emotion data yet. Start chatting with Juno to see your emotional timeline!</div>',
            unsafe_allow_html=True
        )
    else:
        # Continue with the timeline graph
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
            line=dict(color='#ff69b4', width=2.5, shape='spline'),
            marker=dict(size=8, color='#ff69b4', symbol='diamond'),
            hovertemplate='<b>%{text}</b><br>Time: %{x|%I:%M %p, %b %d}<br>Intensity: %{y}<extra></extra>',
            text=tone_labels, fill='tozeroy', fillcolor='rgba(255, 105, 180, 0.1)'
        ))
        
        fig.add_hrect(y0=0, y1=3, fillcolor="rgba(144, 238, 144, 0.1)", line_width=0, annotation_text="Calm Zone", annotation_position="right")
        fig.add_hrect(y0=3, y1=6, fillcolor="rgba(255, 255, 153, 0.1)", line_width=0, annotation_text="Moderate Zone", annotation_position="right")
        fig.add_hrect(y0=6, y1=10, fillcolor="rgba(255, 192, 203, 0.15)", line_width=0, annotation_text="High Intensity Zone", annotation_position="right")
        
        fig.update_layout(
            title="Your Emotional Journey",
            xaxis_title="Time (EST)", yaxis_title="Emotional Intensity",
            hovermode='closest', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font=dict(size=12, color='#333'),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            yaxis=dict(range=[0, 10.5], tickmode='linear', tick0=0, dtick=2, gridcolor='rgba(200, 200, 200, 0.2)'),
            xaxis=dict(gridcolor='rgba(200, 200, 200, 0.2)', tickformat='%I:%M %p<br>%b %d, %Y'),
            height=500
        )
        
        # Create container with graph and overlapping image
        st.markdown('<div style="position: relative; margin-top: -80px;">', unsafe_allow_html=True)
        
        # Add decorative image with absolute positioning
        try:
            deco_image = Image.open("data/avatars/timeline_deco.png")
            st.markdown(
                f'<div style="position: absolute; top: -160px; right: 0; z-index: 999; width: 450px; pointer-events: none;">'
                f'<img src="data:image/png;base64,{image_to_base64(deco_image)}" style="width: 100%; height: auto;" />'
                f'</div>',
                unsafe_allow_html=True
            )
        except Exception:
            pass
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.divider()
        st.subheader("Insights")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            avg_intent = sum(intent_values) / len(intent_values) if intent_values else 0
            if avg_intent <= 3:
                status = "Generally Calm 🌿"
                bg_color = "#d4f1d4"
            elif avg_intent <= 6:
                status = "Moderate Stress 🌤️"
                bg_color = "#fff9e6"
            else:
                status = "High Intensity ⚡"
                bg_color = "#ffe6f0"
            st.markdown("**Average Emotional State**")
            st.markdown(f'<span style="background-color: {bg_color}; padding: 4px 8px; border-radius: 4px; font-size: 0.85em;">{status}</span>', unsafe_allow_html=True)
        
        with col2:
            high_intensity = sum(1 for v in intent_values if v >= 7)
            st.metric("High Intensity Moments", high_intensity)
        
        with col3:
            calm_moments = sum(1 for v in intent_values if v <= 3)
            st.metric("Calm Moments", calm_moments)
        
        st.divider()
        st.subheader("Recent Trend")
        
        if len(intent_values) >= 3:
            recent_avg = sum(intent_values[-3:]) / 3
            earlier_avg = sum(intent_values[:-3]) / len(intent_values[:-3]) if len(intent_values) > 3 else recent_avg
            
            if recent_avg < earlier_avg - 1:
                st.success("📉 Your emotions have been stabilizing recently")
            elif recent_avg > earlier_avg + 1:
                st.warning("📈 Your emotional intensity has increased lately. Remember, I'm here to help.")
            else:
                st.markdown(
                    '<div style="background-color: #ffe6f0; color: #d63384; padding: 12px; border-radius: 8px; border-left: 4px solid #ff69b4;">➜ your emotional state has been relatively stable</div>',
                    unsafe_allow_html=True
                )
        
        # Add "Gain Insights" button
        st.write("")
        st.markdown("<p style='background-color: #ffe6f0; color: #d63384; padding: 8px 12px; border-radius: 6px; font-size: 0.9rem; margin-bottom: 8px;'>learn more about your journey</p>", unsafe_allow_html=True)
        if st.button("✧ gain insights", key="gain_insights"):
            # Show loading indicator with animated sparkles
            loading_placeholder = st.empty()
            with loading_placeholder:
                st.markdown("""
                    <div style="text-align: center; padding: 20px;">
                        <div class="sparks-container">
                            <svg class="spark spark-1" viewBox="0 0 24 24">
                                <path d="M12 0 L14 10 L24 12 L14 14 L12 24 L10 14 L0 12 L10 10 Z" fill="#ff69b4"/>
                            </svg>
                            <svg class="spark spark-2" viewBox="0 0 24 24">
                                <path d="M12 0 L14 10 L24 12 L14 14 L12 24 L10 14 L0 12 L10 10 Z" fill="#ff85c1"/>
                            </svg>
                            <svg class="spark spark-3" viewBox="0 0 24 24">
                                <path d="M12 0 L14 10 L24 12 L14 14 L12 24 L10 14 L0 12 L10 10 Z" fill="#ff69b4"/>
                            </svg>
                            <svg class="spark spark-4" viewBox="0 0 24 24">
                                <path d="M12 0 L14 10 L24 12 L14 14 L12 24 L10 14 L0 12 L10 10 Z" fill="#ff85c1"/>
                            </svg>
                            <svg class="spark spark-5" viewBox="0 0 24 24">
                                <path d="M12 0 L14 10 L24 12 L14 14 L12 24 L10 14 L0 12 L10 10 Z" fill="#ff69b4"/>
                            </svg>
                            <svg class="spark spark-6" viewBox="0 0 24 24">
                                <path d="M12 0 L14 10 L24 12 L14 14 L12 24 L10 14 L0 12 L10 10 Z" fill="#ff85c1"/>
                            </svg>
                        </div>
                        <p style="color: #6b8e7f; margin-top: 10px; font-size: 1rem;">Analyzing your emotional journey...</p>
                    </div>
                    <style>
                    .sparks-container {
                        position: relative;
                        width: 100px;
                        height: 100px;
                        margin: 0 auto;
                    }
                    .spark {
                        position: absolute;
                        width: 20px;
                        height: 20px;
                        animation: twinkle 1.5s ease-in-out infinite;
                        filter: drop-shadow(0 0 6px rgba(255, 105, 180, 0.9));
                    }
                    .spark-1 {
                        top: 5%;
                        left: 45%;
                        animation-delay: 0s;
                    }
                    .spark-2 {
                        top: 25%;
                        left: 75%;
                        animation-delay: 0.25s;
                    }
                    .spark-3 {
                        top: 55%;
                        left: 80%;
                        animation-delay: 0.5s;
                    }
                    .spark-4 {
                        top: 75%;
                        left: 45%;
                        animation-delay: 0.75s;
                    }
                    .spark-5 {
                        top: 55%;
                        left: 5%;
                        animation-delay: 1s;
                    }
                    .spark-6 {
                        top: 25%;
                        left: 0%;
                        animation-delay: 1.25s;
                    }
                    @keyframes twinkle {
                        0%, 100% {
                            opacity: 0.2;
                            transform: scale(0.5) rotate(0deg);
                        }
                        50% {
                            opacity: 1;
                            transform: scale(1.2) rotate(180deg);
                        }
                    }
                    </style>
                """, unsafe_allow_html=True)
            
            # Prepare data for AI analysis
            avg_intent = sum(intent_values) / len(intent_values) if intent_values else 0
            high_intensity = sum(1 for v in intent_values if v >= 7)
            calm_moments = sum(1 for v in intent_values if v <= 3)
            total_moments = len(intent_values)
            
            # Calculate trend
            if len(intent_values) >= 3:
                recent_avg = sum(intent_values[-3:]) / 3
                earlier_avg = sum(intent_values[:-3]) / len(intent_values[:-3]) if len(intent_values) > 3 else recent_avg
                trend_diff = recent_avg - earlier_avg
            else:
                trend_diff = 0
            
            # Get emotion labels for context
            emotion_list = [f"{intent_labels[i]} (intensity: {intent_values[i]})" for i in range(len(intent_labels))]
            
            # Create prompt for AI
            prompt = f"""You are a compassionate teen mental health coach analyzing a user's emotional timeline data.

Emotional Journey Data:
- Total interactions: {total_moments}
- Average emotional intensity: {avg_intent:.1f}/10
- High intensity moments (7-10): {high_intensity}
- Calm moments (1-3): {calm_moments}
- Trend: {"improving" if trend_diff < -1 else "increasing" if trend_diff > 1 else "stable"}
- Emotions experienced: {', '.join(emotion_list[:5])}{"..." if len(emotion_list) > 5 else ""}

Provide a warm, supportive 1-2 sentence insight about their emotional journey. Be encouraging, acknowledge patterns, and if there are concerns, gently suggest coping strategies or support. Keep it natural and teen-friendly."""

            # Call OpenAI API
            try:
                client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are Juno, a compassionate AI mental health companion for teens. Provide brief, warm, supportive insights."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=150
                )
                
                insight_text = response.choices[0].message.content.strip()
                
                # Clear loading animation and display AI-generated insight
                loading_placeholder.empty()
                st.markdown(
                    f'<div style="background-color: #e8f4f8; color: #0c5460; padding: 16px; border-radius: 8px; border-left: 4px solid #A8D5BA; margin-top: 10px;">'
                    f'<strong>✧ personalized insight:</strong><br>{insight_text}'
                    f'</div>',
                    unsafe_allow_html=True
                )
            except Exception as e:
                loading_placeholder.empty()
                st.error(f"Unable to generate insights at this time. Please try again later.")
                # Fallback to rule-based insight
                if avg_intent <= 3:
                    state_desc = "relatively calm"
                elif avg_intent <= 6:
                    state_desc = "experiencing moderate stress"
                else:
                    state_desc = "going through high emotional intensity"
                
                st.markdown(
                    f'<div style="background-color: #e8f4f8; color: #0c5460; padding: 16px; border-radius: 8px; border-left: 4px solid #A8D5BA; margin-top: 10px;">'
                    f'<strong>📊 session summary:</strong> Based on {total_moments} interactions, you\'ve been {state_desc}, with {high_intensity} high-intensity moment(s) and {calm_moments} calm moment(s).'
                    f'</div>',
                    unsafe_allow_html=True
                )
    
    st.write("")
    st.write("")
    
    if st.button("💬 Back to Chat", key="timeline_to_chat"):
        st.session_state["page"] = "chat"
        st.session_state["show_chat_header"] = True
        try:
            st.experimental_rerun()
        except Exception:
            pass
