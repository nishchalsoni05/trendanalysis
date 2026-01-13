
import streamlit as st
import time

def render_loader(messages=None, duration=2.0):
    """
    Displays a futuristic AI loading animation.
    
    Args:
        messages (list): List of (headline, subtext) tuples to cycle through.
        duration (float): Approximate duration in seconds.
    """
    if messages is None:
        messages = [
            ("INITIALIZING SYSTEM", "Verifying security protocols..."),
            ("LOADING DATA ASSETS", "Fetching analytical datasets..."),
            ("RENDERING VISUALS", "Optimizing graphics engine..."),
        ]
        
    step_delay = duration / len(messages)
    
    placeholder = st.empty()
    
    with placeholder.container():
        # CSS for Futuristic Loader
        st.markdown("""
        <style>
        .loader-container {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 60vh;
        }
        .ai-core {
            position: relative;
            width: 120px;
            height: 120px;
            margin-bottom: 2rem;
        }
        .ring {
            position: absolute;
            width: 100%;
            height: 100%;
            border-radius: 50%;
            border: 4px solid transparent;
            border-top-color: #3B82F6;
            animation: spin1 2s linear infinite;
        }
        .ring:nth-child(2) {
            border: 4px solid transparent;
            border-left-color: #8B5CF6;
            width: 80%;
            height: 80%;
            top: 10%;
            left: 10%;
            animation: spin2 2.5s linear infinite;
        }
        .pulse-core {
            position: absolute;
            width: 40%;
            height: 40%;
            top: 30%;
            left: 30%;
            background: linear-gradient(135deg, #10B981, #059669);
            border-radius: 50%;
            box-shadow: 0 0 20px #10B981;
            animation: pulse 1.5s ease-in-out infinite alternate;
        }
        .loading-text {
            font-family: 'Courier New', monospace;
            font-size: 1.2rem;
            color: #475569;
            font-weight: 600;
        }
        .loading-subtext {
            font-family: 'Inter', sans-serif;
            font-size: 0.9rem;
            color: #94a3b8;
            margin-top: 0.5rem;
        }
        @keyframes spin1 { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        @keyframes spin2 { 0% { transform: rotate(0deg); } 100% { transform: rotate(-360deg); } }
        @keyframes pulse { 
            0% { transform: scale(0.95); opacity: 0.8; box-shadow: 0 0 10px #10B981; } 
            100% { transform: scale(1.1); opacity: 1; box-shadow: 0 0 30px #10B981; } 
        }
        </style>
        """, unsafe_allow_html=True)
        
        status_box = st.empty()
        
        for headline, sub in messages:
            status_box.markdown(f"""
            <div class="loader-container">
                <div class="ai-core">
                    <div class="ring"></div>
                    <div class="ring"></div>
                    <div class="pulse-core"></div>
                </div>
                <div class="loading-text">{headline}</div>
                <div class="loading-subtext">{sub}</div>
            </div>
            """, unsafe_allow_html=True)
            time.sleep(step_delay)
            
    placeholder.empty()
