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

# Custom CSS for better UI
st.markdown("""
<style>
    /* Main app styling */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-attachment: fixed;
    }
    
    /* Card styling */
    .asset-card {
        background: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 10px 0;
    }
    
    /* Hero section */
    .hero-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 3rem;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .hero-title {
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    
    .hero-subtitle {
        font-size: 1.2rem;
        opacity: 0.95;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 50px;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
    }
    
    /* Resolution badge */
    .resolution-badge {
        background: #667eea;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
        margin: 5px 0;
    }
    
    /* Chat interface */
    .chat-container {
        background: white;
        border-radius: 10px;
        padding: 20px;
        height: 600px;
        overflow-y: auto;
    }
    
    .chat-message {
        margin: 10px 0;
        padding: 10px 15px;
        border-radius: 10px;
    }
    
    .user-message {
        background: #667eea;
        color: white;
        margin-left: 20%;
    }
    
    .assistant-message {
        background: #f3f4f6;
        color: #1f2937;
        margin-right: 20%;
    }
    
    /* Image gallery */
    .image-thumbnail {
        width: 80px;
        height: 80px;
        object-fit: cover;
        border-radius: 8px;
        cursor: pointer;
        transition: transform 0.2s;
        margin: 5px;
    }
    
    .image-thumbnail:hover {
        transform: scale(1.1);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: rgba(255, 255, 255, 0.05);
        padding: 10px;
        border-radius: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 8px;
        color: white;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: white;
        color: #667eea;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
init_session_state()

# Initialize Gemini handler
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    st.error("⚠️ Missing GEMINI_API_KEY in .env file. Please add it and restart the app.")
    st.info("Get your API key from: https://makersuite.google.com/app/apikey")
    st.stop()

gemini = GeminiHandler(API_KEY)

# ---------- Main App ----------
def main():
    # Hero Section
    if not st.session_state.get('started', False):
        render_hero_section()
        
        # Sample images selection
        st.markdown("### 🎯 Quick Start with Sample Products")
        sample_images = get_sample_images()
        cols = st.columns(len(sample_images))
        
        for idx, (name, path, desc) in enumerate(sample_images):
            with cols[idx]:
                st.image(path, caption=name, use_container_width=True)
                if st.button(f"Use {name}", key=f"sample_{idx}"):
                    st.session_state['product_img'] = path
                    st.session_state['started'] = True
                    st.rerun()
        
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
            if st.button("🏠 Start New Project"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
            
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
