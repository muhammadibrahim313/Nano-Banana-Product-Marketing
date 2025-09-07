import streamlit as st
import os
from pathlib import Path
from dotenv import load_dotenv

# Import custom modules
from utils import init_session_state, get_sample_images
from ui_components import (
    render_hero_section, 
    render_brand_sidebar,
    render_asset_generation,
    render_chat_interface,
    render_demo_section
)
from gemini_handler import GeminiHandler

# ---------- Config ----------
load_dotenv()

st.set_page_config(
    page_title="✨ Nano Banana Studio - AI Marketing Asset Creator",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI with fixed visibility
st.markdown("""
<style>
    /* Main app styling */
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        background-attachment: fixed;
    }
    
    /* Fix text visibility */
    .main .block-container {
        padding-top: 2rem;
        max-width: 100%;
    }
    
    /* Card styling with dark theme */
    .asset-card {
        background: #2d2d44;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3);
        margin: 15px 0;
        border: 1px solid rgba(102, 126, 234, 0.3);
    }
    
    .asset-card h4 {
        color: #fff !important;
        margin-bottom: 10px;
    }
    
    /* Hero section */
    .hero-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 3rem;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    }
    
    .hero-title {
        font-size: 3.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .hero-subtitle {
        font-size: 1.3rem;
        opacity: 0.95;
    }
    
    /* App title bar */
    .app-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 2rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        text-align: center;
        font-size: 1.8rem;
        font-weight: bold;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.6rem 2rem;
        border-radius: 50px;
        font-weight: 600;
        transition: all 0.3s;
        box-shadow: 0 4px 10px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Resolution badge */
    .resolution-badge {
        background: linear-gradient(90deg, #667eea, #764ba2);
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
        display: inline-block;
        margin: 5px 0;
    }
    
    /* Chat interface */
    .chat-container {
        background: #2d2d44;
        border-radius: 15px;
        padding: 20px;
        height: 600px;
        overflow-y: auto;
        border: 1px solid rgba(102, 126, 234, 0.3);
    }
    
    .chat-message {
        margin: 10px 0;
        padding: 12px 18px;
        border-radius: 15px;
    }
    
    .user-message {
        background: linear-gradient(90deg, #667eea, #764ba2);
        color: white;
        margin-left: 20%;
    }
    
    .assistant-message {
        background: #3d3d5c;
        color: #ffffff;
        margin-right: 20%;
        border: 1px solid rgba(102, 126, 234, 0.2);
    }
    
    /* Image gallery */
    .image-thumbnail {
        width: 100px;
        height: 100px;
        object-fit: cover;
        border-radius: 10px;
        cursor: pointer;
        transition: all 0.3s;
        margin: 5px;
        border: 2px solid transparent;
    }
    
    .image-thumbnail:hover {
        transform: scale(1.05);
        border-color: #667eea;
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
    
    /* Fix tab styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: rgba(45, 45, 68, 0.5);
        padding: 10px;
        border-radius: 10px;
        gap: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(102, 126, 234, 0.2);
        color: white !important;
        border-radius: 25px;
        padding: 10px 20px;
        font-weight: 600;
        border: 1px solid rgba(102, 126, 234, 0.3);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, #667eea, #764ba2);
        color: white !important;
        border: none;
    }
    
    /* Sidebar styling */
    .css-1d391kg, [data-testid="stSidebar"] {
        background: #1a1a2e;
        border-right: 1px solid rgba(102, 126, 234, 0.2);
    }
    
    .css-1d391kg h2, [data-testid="stSidebar"] h2 {
        color: #667eea;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: rgba(102, 126, 234, 0.1);
        border-radius: 10px;
        border: 1px solid rgba(102, 126, 234, 0.3);
        color: white !important;
    }
    
    /* Input fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: rgba(45, 45, 68, 0.5);
        color: white;
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 10px;
    }
    
    /* Select box */
    .stSelectbox > div > div {
        background: rgba(45, 45, 68, 0.5);
        border-radius: 10px;
    }
    
    /* Info and warning boxes */
    .stAlert {
        background: rgba(45, 45, 68, 0.8);
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 10px;
        color: white;
    }
    
    /* Sample image cards */
    .sample-card {
        background: #2d2d44;
        border-radius: 15px;
        padding: 10px;
        text-align: center;
        border: 2px solid transparent;
        transition: all 0.3s;
    }
    
    .sample-card:hover {
        border-color: #667eea;
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
    }
    
    /* Progress bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea, #764ba2);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
init_session_state()

# Initialize Gemini handler
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    # Try Streamlit secrets for cloud deployment
    try:
        API_KEY = st.secrets.get("GEMINI_API_KEY", None)
    except:
        pass

if not API_KEY:
    st.error("⚠️ Missing GEMINI_API_KEY in .env file or Streamlit secrets.")
    st.info("Get your API key from: https://makersuite.google.com/app/apikey")
    st.stop()

gemini = GeminiHandler(API_KEY)

# ---------- Main App ----------
def main():
    # Show app header/title always
    if st.session_state.get('started', False):
        st.markdown('<div class="app-header">🎨 Nano Banana Studio - AI Marketing Asset Creator</div>', 
                   unsafe_allow_html=True)
    
    # Hero Section for new users
    if not st.session_state.get('started', False):
        render_hero_section()
        
        # Before/After Showcase
        st.markdown("### ✨ See The Magic - Before & After")
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
            border: 2px solid rgba(102, 126, 234, 0.5);
            border-radius: 20px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.2);
        ">
            <img src="https://raw.githubusercontent.com/muhammadibrahim313/Nano-Banana-Product-Marketing/refs/heads/main/sample_images/Capture.PNG" 
                 style="width: 100%; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.3);"
                 alt="Before and After - Product Transformation">
            <p style="text-align: center; color: #ffffff; margin-top: 15px; font-size: 1.1rem;">
                <strong>Transform simple products into professional marketing assets with automatic brand labeling!</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Sample images selection
        st.markdown("### 🎯 Quick Start with Sample Products")
        st.info("Select a sample product or upload your own below")
        
        sample_images = get_sample_images()
        cols = st.columns(len(sample_images))
        
        for idx, (name, path, desc) in enumerate(sample_images):
            with cols[idx]:
                st.markdown(f'<div class="sample-card">', unsafe_allow_html=True)
                if Path(path).exists():
                    st.image(path, caption=name, use_container_width=True)
                else:
                    st.info(f"Add {name} image to {path}")
                st.markdown(f"<small>{desc}</small>", unsafe_allow_html=True)
                if st.button(f"Use {name}", key=f"sample_{idx}", use_container_width=True):
                    if Path(path).exists():
                        st.session_state['product_img'] = path
                        st.session_state['started'] = True
                        st.rerun()
                    else:
                        st.warning(f"Please add image to {path}")
                st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 📤 Or Upload Your Own Product")
        uploaded = st.file_uploader(
            "Upload product image (PNG/JPG)", 
            type=["png", "jpg", "jpeg"],
            help="Upload a high-quality product image. Works best with products on transparent or simple backgrounds."
        )
        
        if uploaded:
            st.session_state['product_img'] = uploaded
            st.session_state['started'] = True
            st.rerun()
    
    else:
        # Main app interface
        with st.sidebar:
            if st.button("🏠 Start New Project", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
            
            st.markdown("---")
            brand_config = render_brand_sidebar()
            st.session_state['brand_config'] = brand_config
        
        # Main content tabs
        tabs = st.tabs([
            "🎨 Generate Assets",
            "💬 Chat & Edit",
            "🎬 Demo & Help"
        ])
        
        with tabs[0]:
            render_asset_generation(gemini)
        
        with tabs[1]:
            render_chat_interface(gemini)
        
        with tabs[2]:
            render_demo_section()

if __name__ == "__main__":
    main()
