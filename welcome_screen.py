import streamlit as st
import time

def show_welcome_screen():
    """Display animated welcome screen overlay that fades out to reveal home page"""
    st.markdown(
        """
        <style>
        @keyframes breathingGradient {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        @keyframes gentleFadeIn {
            0% { opacity: 0; }
            100% { opacity: 1; }
        }
        
        @keyframes fadeOut {
            0% { opacity: 1; }
            100% { opacity: 0; }
        }
        
        .welcome-screen {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: linear-gradient(135deg, #FAF7F5 0%, #d4e8d4 25%, #f5e8e8 50%, #e8f0e8 75%, #FAF7F5 100%);
            background-size: 400% 400%;
            animation: breathingGradient 14s ease-in-out infinite, fadeOut 1.5s ease-in-out 4s forwards;
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            pointer-events: none;
        }
        
        .welcome-content {
            text-align: center;
            animation: gentleFadeIn 2.5s ease-in, fadeOut 1.2s ease-in-out 4s forwards;
        }
        
        .welcome-title {
            font-family: 'ChickenRice', cursive, sans-serif;
            font-size: 3rem;
            color: #2d5f4a;
            margin: 0;
            opacity: 0;
            animation: gentleFadeIn 3s ease-in forwards;
            animation-delay: 0.5s;
        }
        
        .welcome-subtitle {
            font-size: 1rem;
            color: #6b8e7f;
            margin-top: 1rem;
            opacity: 0;
            animation: gentleFadeIn 3s ease-in forwards;
            animation-delay: 1.8s;
        }
        
        /* Respect user preference for reduced motion */
        @media (prefers-reduced-motion: reduce) {
            .welcome-screen,
            .welcome-content,
            .welcome-title,
            .welcome-subtitle {
                animation: none !important;
                opacity: 1 !important;
            }
        }
        </style>
        <div class="welcome-screen">
            <div class="welcome-content">
                <h1 class="welcome-title">juno ai</h1>
                <p class="welcome-subtitle">a safe space for you</p>
            </div>
        </div>
        <script>
            setTimeout(function() {
                var overlay = document.querySelector('.welcome-screen');
                if (overlay) {
                    overlay.style.pointerEvents = 'none';
                }
            }, 5500);
        </script>
        """,
        unsafe_allow_html=True
    )
    
    # Wait for animation to complete (4s content + 1.5s fade-out)
    time.sleep(5.5)
    st.session_state["welcome_shown"] = True
    st.session_state["show_welcome_overlay"] = False
    st.rerun()
