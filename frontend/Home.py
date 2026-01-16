"""
Project Aadhhar Sanket - Landing Page
Welcome page with overview and navigation to dashboard
"""
import streamlit as st
from pathlib import Path
import sys

st.set_page_config(
    page_title="Aadhaar Sanket - Demographic Intelligence",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="collapsed"
)

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import centralized styling system
import frontend.styles as styles

# Apply global CSS
st.markdown(styles.get_global_css(), unsafe_allow_html=True)

# Additional landing page CSS
st.markdown("""
<style>
    /* Hide sidebar on landing page */
    [data-testid="stSidebar"] {
        display: none;
    }
    
    /* Landing page specific styles */
    .landing-container {
        max-width: 1400px;
        margin: 0 auto;
        padding: 2rem;
    }
    
    .hero-section {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 4rem;
        margin: 4rem 0;
        min-height: 70vh;
    }
    
    .hero-content {
        flex: 1;
        max-width: 600px;
    }
    
    .hero-visual {
        flex: 1;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    
    .gov-badge {
        display: inline-block;
        color: #F5A623;
        font-size: 0.875rem;
        font-weight: 600;
        margin-bottom: 1rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .hero-title {
        font-size: 3.5rem;
        font-weight: 700;
        line-height: 1.2;
        margin: 1rem 0;
        color: #1F2937;
    }
    
    .hero-title .highlight {
        color: #F5A623;
    }
    
    .hero-subtitle {
        font-size: 1.5rem;
        color: #6B7280;
        margin: 1rem 0 1.5rem 0;
        font-weight: 500;
    }
    
    .hero-description {
        font-size: 1.125rem;
        line-height: 1.75;
        color: #4B5563;
        margin: 1.5rem 0 2rem 0;
    }
    
    .cta-buttons {
        display: flex;
        gap: 1rem;
        margin: 2rem 0;
    }
    
    .btn-primary {
        background: linear-gradient(135deg, #F5A623 0%, #EF4444 100%);
        color: white;
        padding: 1rem 2.5rem;
        border-radius: 50px;
        font-size: 1.125rem;
        font-weight: 600;
        border: none;
        cursor: pointer;
        box-shadow: 0 10px 25px rgba(245, 166, 35, 0.3);
        transition: all 0.3s ease;
        text-decoration: none;
        display: inline-block;
    }
    
    .btn-primary:hover {
        transform: translateY(-2px);
        box-shadow: 0 15px 35px rgba(245, 166, 35, 0.4);
    }
    
    .btn-secondary {
        background: white;
        color: #F5A623;
        padding: 1rem 2.5rem;
        border-radius: 50px;
        font-size: 1.125rem;
        font-weight: 600;
        border: 2px solid #F5A623;
        cursor: pointer;
        transition: all 0.3s ease;
        text-decoration: none;
        display: inline-block;
    }
    
    .btn-secondary:hover {
        background: #FFF7ED;
        transform: translateY(-2px);
    }
    
    .features-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 1rem;
        margin: 2rem 0;
    }
    
    .feature-item {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.75rem;
        background: rgba(255, 255, 255, 0.6);
        border-radius: 12px;
        border-left: 3px solid #F5A623;
    }
    
    .feature-icon {
        font-size: 1.5rem;
    }
    
    .feature-text {
        color: #374151;
        font-weight: 500;
        font-size: 0.95rem;
    }
    
    .india-map-container {
        position: relative;
        width: 100%;
        max-width: 500px;
        background: white;
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
    }
    
    @media (max-width: 968px) {
        .hero-section {
            flex-direction: column;
            text-align: center;
        }
        
        .hero-content {
            max-width: 100%;
        }
        
        .cta-buttons {
            justify-content: center;
        }
        
        .hero-title {
            font-size: 2.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Landing page main content"""
    
    # Navigation bar
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 1rem 2rem; background: white; box-shadow: 0 2px 10px rgba(0,0,0,0.05);">
        <div style="display: flex; align-items: center; gap: 0.75rem;">
            <div style="width: 40px; height: 40px; background: linear-gradient(135deg, #F5A623 0%, #EF4444 100%); border-radius: 8px; display: flex; align-items: center; justify-content: center;">
                <span style="color: white; font-weight: 700; font-size: 1.25rem;">अ</span>
            </div>
            <div>
                <div style="font-weight: 700; font-size: 1.25rem; color: #1F2937;">Aadhaar Sanket</div>
                <div style="font-size: 0.75rem; color: #6B7280;">Demographic Intelligence</div>
            </div>
        </div>
        <div style="display: flex; gap: 2rem; align-items: center;">
            <a href="#home" style="color: #374151; text-decoration: none; font-weight: 500;">Home</a>
            <a href="#about" style="color: #6B7280; text-decoration: none; font-weight: 500;">About</a>
            <a href="#guidelines" style="color: #6B7280; text-decoration: none; font-weight: 500;">Guidelines</a>
            <a href="#contact" style="color: #6B7280; text-decoration: none; font-weight: 500;">Contact Us</a>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Hero Section
    st.markdown('<div class="landing-container">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1.2, 1])
    
    with col1:
        st.html("""
        <div class="hero-content">
            <div class="gov-badge">🇮🇳 Government of India Initiative</div>
            <h1 class="hero-title">Aadhaar <span class="highlight">Sanket</span></h1>
            <p class="hero-subtitle">Demographic Intelligence Platform</p>
            <p class="hero-description">
                Transform demographic data into actionable intelligence. Monitor migration patterns, 
                predict population trends, and make data-driven policy decisions for 1.4 billion citizens.
            </p>
            
            <div class="features-grid">
                <div class="feature-item">
                    <span class="feature-icon">📊</span>
                    <span class="feature-text">Real-time Analytics</span>
                </div>
                <div class="feature-item">
                    <span class="feature-icon">🔒</span>
                    <span class="feature-text">Secure & Compliant</span>
                </div>
                <div class="feature-item">
                    <span class="feature-icon">🤖</span>
                    <span class="feature-text">AI-Powered Insights</span>
                </div>
                <div class="feature-item">
                    <span class="feature-icon">🗺️</span>
                    <span class="feature-text">Pan-India Coverage</span>
                </div>
            </div>
        </div>
        """)
        
        # Get Started Button with navigation
        col_btn, _, _ = st.columns([1, 1, 1])
        with col_btn:
            if st.button("Get Started →", key="get_started", use_container_width=True):
                st.switch_page("pages/1_Overview.py")
    
    with col2:
        st.html("""
        <div class="india-map-container">
            <svg viewBox="0 0 400 500" xmlns="http://www.w3.org/2000/svg">
                <!-- Simplified India Map with States -->
                
                <!-- Kashmir & Ladakh -->
                <path d="M 200 50 L 180 70 L 190 90 L 210 85 L 220 65 Z" fill="#FF8C42" opacity="0.8"/>
                
                <!-- Himachal Pradesh -->
                <path d="M 190 90 L 180 105 L 195 115 L 210 110 L 210 85 Z" fill="#FFB366" opacity="0.7"/>
                
                <!-- Punjab & Haryana -->
                <path d="M 180 105 L 175 120 L 190 130 L 205 125 L 195 115 Z" fill="#FF6B35" opacity="0.8"/>
                
                <!-- Uttarakhand -->
                <path d="M 210 85 L 210 110 L 225 115 L 230 95 Z" fill="#FFAA5A" opacity="0.75"/>
                
                <!-- Uttar Pradesh -->
                <path d="M 195 115 L 190 130 L 205 160 L 240 155 L 235 125 L 225 115 Z" fill="#FF9A56" opacity="0.8"/>
                
                <!-- Rajasthan -->
                <path d="M 175 120 L 160 160 L 170 200 L 195 195 L 205 160 L 190 130 Z" fill="#FF7744" opacity="0.85"/>
                
                <!-- Gujarat -->
                <path d="M 160 190 L 145 235 L 165 260 L 185 245 L 180 210 Z" fill="#FFB280" opacity="0.7"/>
                
                <!-- Madhya Pradesh -->
                <path d="M 170 200 L 195 195 L 220 210 L 225 240 L 200 250 L 180 245 Z" fill="#FF8855" opacity="0.8"/>
                
                <!-- Bihar -->
                <path d="M 240 155 L 250 165 L 260 180 L 245 190 L 230 175 Z" fill="#FFA366" opacity="0.75"/>
                
                <!-- West Bengal -->
                <path d="M 260 180 L 270 195 L 275 220 L 260 225 L 250 205 Z" fill="#FF9F5C" opacity="0.8"/>
                
                <!-- Odisha -->
                <path d="M 245 190 L 260 225 L 250 255 L 225 240 Z" fill="#FFB870" opacity="0.7"/>
                
                <!-- Chhattisgarh -->
                <path d="M 225 210 L 245 190 L 250 225 L 235 235 Z" fill="#FF8844" opacity="0.8"/>
                
                <!-- Maharashtra -->
                <path d="M 180 245 L 200 250 L 210 280 L 195 310 L 165 295 L 165 260 Z" fill="#FF6633" opacity="0.85"/>
                
                <!-- Karnataka -->
                <path d="M 195 310 L 210 345 L 200 370 L 175 360 L 170 330 Z" fill="#FFB588" opacity="0.75"/>
                
                <!-- Goa -->
                <path d="M 165 295 L 170 305 L 175 300 Z" fill="#FFCC99" opacity="0.6"/>
                
                <!-- Kerala -->
                <path d="M 175 360 L 180 395 L 190 420 L 175 415 L 165 385 Z" fill="#FF9966" opacity="0.8"/>
                
                <!-- Tamil Nadu -->
                <path d="M 200 370 L 215 405 L 210 440 L 190 420 L 180 395 Z" fill="#FF7755" opacity="0.85"/>
                
                <!-- Andhra Pradesh -->
                <path d="M 210 280 L 235 285 L 240 315 L 225 340 L 210 345 L 195 310 Z" fill="#FFAA77" opacity="0.75"/>
                
                <!-- Telangana -->
                <path d="M 225 240 L 235 235 L 240 265 L 235 285 L 210 280 L 200 250 Z" fill="#FF8866" opacity="0.8"/>
                
                <!-- Data Points (Cities) -->
                <circle cx="200" cy="100" r="4" fill="#EF4444">
                    <animate attributeName="opacity" values="0.5;1;0.5" dur="2s" repeatCount="indefinite"/>
                </circle>
                <circle cx="240" cy="170" r="4" fill="#EF4444">
                    <animate attributeName="opacity" values="0.5;1;0.5" dur="2.5s" repeatCount="indefinite"/>
                </circle>
                <circle cx="185" cy="270" r="4" fill="#EF4444">
                    <animate attributeName="opacity" values="0.5;1;0.5" dur="2.2s" repeatCount="indefinite"/>
                </circle>
                <circle cx="205" cy="390" r="4" fill="#EF4444">
                    <animate attributeName="opacity" values="0.5;1;0.5" dur="1.8s" repeatCount="indefinite"/>
                </circle>
                <circle cx="155" cy="220" r="4" fill="#EF4444">
                    <animate attributeName="opacity" values="0.5;1;0.5" dur="2.3s" repeatCount="indefinite"/>
                </circle>
            </svg>
            <div style="text-align: center; margin-top: 1rem; color: #6B7280; font-size: 0.875rem;">
                <strong style="color: #F5A623;">800+</strong> Districts • <strong style="color: #F5A623;">28</strong> States • <strong style="color: #F5A623;">1.4B+</strong> Citizens
            </div>
        </div>
        """)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # About Section
    st.markdown('<div id="about" style="padding: 4rem 0;">', unsafe_allow_html=True)
    st.markdown("""
    <div class="landing-container">
        <div style="text-align: center; margin-bottom: 3rem;">
            <div style="color: #F5A623; font-weight: 600; margin-bottom: 0.5rem;">How It Works</div>
            <h2 style="font-size: 2.5rem; color: #1F2937;">Intelligent Demographic <span style="color: #F5A623;">Workflow</span></h2>
            <p style="color: #6B7280; font-size: 1.125rem; max-width: 700px; margin: 1rem auto;">
                A comprehensive system designed to transform raw demographic data into actionable intelligence for nation-building.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Workflow Cards
    workflow_items = [
        {
            "number": "1",
            "icon": "📄",
            "title": "Data Collection",
            "description": "Real-time demographic data aggregation from Aadhaar databases across all states and union territories."
        },
        {
            "number": "2",
            "icon": "👥",
            "title": "Population Analysis",
            "description": "Advanced analytics to track population movements, migration patterns, and demographic shifts."
        },
        {
            "number": "3",
            "icon": "🗺️",
            "title": "Spatial Mapping",
            "description": "Geo-spatial visualization of stress zones, high-density areas, and critical infrastructure needs."
        },
        {
            "number": "4",
            "icon": "📈",
            "title": "Trend Forecasting",
            "description": "Predictive models to anticipate future demographic changes and resource requirements."
        }
    ]
    
    cols = st.columns(4)
    for idx, item in enumerate(workflow_items):
        with cols[idx]:
            st.markdown(f"""
            <div style="background: white; padding: 2rem 1.5rem; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); text-align: center; height: 100%; position: relative;">
                <div style="position: absolute; top: -15px; left: 50%; transform: translateX(-50%); background: linear-gradient(135deg, #F5A623 0%, #EF4444 100%); color: white; width: 35px; height: 35px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 1.125rem;">
                    {item["number"]}
                </div>
                <div style="font-size: 3rem; margin: 1.5rem 0 1rem 0;">{item["icon"]}</div>
                <h3 style="color: #1F2937; font-size: 1.125rem; margin: 1rem 0 0.5rem 0;">{item["title"]}</h3>
                <p style="color: #6B7280; font-size: 0.9rem; line-height: 1.6;">{item["description"]}</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Additional workflow items
    st.markdown('<div class="landing-container" style="margin-top: 2rem;">', unsafe_allow_html=True)
    workflow_items_2 = [
        {
            "number": "5",
            "icon": "🔔",
            "title": "Early Warnings",
            "description": "Automated alert system for critical demographic events requiring immediate attention."
        },
        {
            "number": "6",
            "icon": "🛡️",
            "title": "Data Governance",
            "description": "Robust security protocols ensuring data integrity, privacy, and regulatory compliance."
        },
        {
            "number": "7",
            "icon": "🤖",
            "title": "AI Insights",
            "description": "Machine learning algorithms provide actionable insights for policy makers and administrators."
        },
        {
            "number": "8",
            "icon": "📋",
            "title": "Policy Support",
            "description": "Evidence-based recommendations for effective governance and resource allocation."
        }
    ]
    
    cols2 = st.columns(4)
    for idx, item in enumerate(workflow_items_2):
        with cols2[idx]:
            st.markdown(f"""
            <div style="background: white; padding: 2rem 1.5rem; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); text-align: center; height: 100%; position: relative;">
                <div style="position: absolute; top: -15px; left: 50%; transform: translateX(-50%); background: linear-gradient(135deg, #F5A623 0%, #EF4444 100%); color: white; width: 35px; height: 35px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 1.125rem;">
                    {item["number"]}
                </div>
                <div style="font-size: 3rem; margin: 1.5rem 0 1rem 0;">{item["icon"]}</div>
                <h3 style="color: #1F2937; font-size: 1.125rem; margin: 1rem 0 0.5rem 0;">{item["title"]}</h3>
                <p style="color: #6B7280; font-size: 0.9rem; line-height: 1.6;">{item["description"]}</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer CTA
    st.markdown("""
    <div style="background: linear-gradient(135deg, #F5A623 0%, #EF4444 100%); padding: 4rem 2rem; margin-top: 4rem; border-radius: 20px; text-align: center;">
        <h2 style="color: white; font-size: 2.5rem; margin-bottom: 1rem;">Ready to Transform Demographic Intelligence?</h2>
        <p style="color: rgba(255,255,255,0.9); font-size: 1.25rem; margin-bottom: 2rem;">Access the dashboard and start making data-driven decisions today.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_center1, col_center2, col_center3 = st.columns([1, 1, 1])
    with col_center2:
        if st.button("Launch Dashboard →", key="launch_dashboard", use_container_width=True, type="primary"):
            st.switch_page("pages/1_Overview.py")
    
    # Footer
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0; color: #6B7280; font-size: 0.875rem; border-top: 1px solid #E5E7EB; margin-top: 3rem;">
        <p>Aadhaar Sanket | Demographic Intelligence Platform | <span style="color: #F5A623; font-weight: 600;">Government of India</span></p>
        <p style="margin-top: 0.5rem;">Powered by UIDAI Official Data • Secure • Compliant • Trusted</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
