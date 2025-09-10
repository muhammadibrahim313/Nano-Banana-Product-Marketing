import streamlit as st
import json
from PIL import Image
import io
from datetime import datetime
from typing import Dict, List, Optional

# Asset type configurations
ASSET_CONFIGS = {
    "Instagram Post": {
        "resolution": "1080x1080",
        "aspect": (1, 1),
        "icon": "📱",
        "description": "Perfect square for Instagram feed"
    },
    "Instagram Story": {
        "resolution": "1080x1920", 
        "aspect": (9, 16),
        "icon": "📲",
        "description": "Vertical format for Stories"
    },
    "Website Banner": {
        "resolution": "1920x1080",
        "aspect": (16, 9),
        "icon": "🖥️",
        "description": "Wide format for web headers"
    },
    "Ad Creative": {
        "resolution": "1200x1200",
        "aspect": (1, 1),
        "icon": "📢",
        "description": "Optimized for social media ads"
    },
    "Testimonial Graphic": {
        "resolution": "1080x1080",
        "aspect": (1, 1),
        "icon": "💬",
        "description": "Customer testimonial with quote overlay"
    }
}

def render_hero_section():
    """Render the hero/welcome section"""
    st.markdown("""
    <div class="hero-section">
        <h1 class="hero-title">✨ Nano Banana Studio</h1>
        <p class="hero-subtitle">Transform your product images into stunning marketing assets with AI</p>
        <p style="margin-top: 20px; font-size: 1rem;">
            🎨 Generate Instagram posts, stories, web banners, and more<br>
            🤖 Powered by Google's Gemini Nano Banana model<br>
            💬 Chat with AI to edit and refine your creations
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_brand_sidebar() -> Dict:
    """Render brand configuration sidebar"""
    st.markdown("## 🎨 Brand Configuration")
    
    with st.expander("📝 Brand Identity", expanded=True):
        brand_name = st.text_input(
            "Brand Name",
            value=st.session_state.get('brand_name', 'Capsula'),
            help="Your brand or product name"
        )
        
        brand_tone = st.text_area(
            "Brand Tone & Voice",
            value=st.session_state.get('brand_tone', 'Modern biotech luxury — innovative, pure, immersive.'),
            height=80,
            help="Describe your brand's personality and communication style"
        )
    
    with st.expander("🎨 Visual Guidelines", expanded=True):
        color_theme = st.text_area(
            "Color Palette",
            value=st.session_state.get('color_theme', 'Coral blush, teal turquoise, deep emerald, warm beige, onyx black.'),
            height=60,
            help="Your brand colors"
        )
        
        placement = st.text_area(
            "Product Placement Style",
            value=st.session_state.get('placement', 'Geometric pedestals or refined vanity; sparse organic props.'),
            height=60,
            help="How products should be positioned"
        )
        
        composition = st.text_area(
            "Composition Guidelines",
            value=st.session_state.get('composition', 'Clean symmetry for single-product; off-center for lifestyle; generous negative space.'),
            height=80,
            help="Layout and composition rules"
        )
    
    with st.expander("✍️ Content Settings", expanded=True):
        product_name = st.text_input(
            "Product Name",
            value=st.session_state.get('product_name', 'Capsula Serum X'),
            help="The specific product name to feature"
        )
        
        tagline = st.text_input(
            "Tagline",
            value=st.session_state.get('tagline', 'Glow deeper. Shine brighter.'),
            help="Your product tagline or slogan"
        )
        
        quote = st.text_area(
            "Customer Quote (for testimonials)",
            value=st.session_state.get('quote', 'My skin has never felt this good—truly a game-changer!'),
            height=60,
            help="Quote to use in testimonial graphics"
        )
        
        customer_name = st.text_input(
            "Customer Name (optional)",
            value=st.session_state.get('customer_name', 'Sarah M.'),
            help="Attribution for testimonial"
        )
    
    # Store in session state
    config = {
        'brandName': brand_name,
        'brandTone': brand_tone,
        'colorTheme': color_theme,
        'productPlacement': placement,
        'compositionGuidelines': composition,
        'productName': product_name,
        'tagline': tagline,
        'quote': quote,
        'customerName': customer_name
    }
    
    for key, value in config.items():
        st.session_state[key] = value
    
    return config

def render_asset_generation(gemini_handler):
    """Render the asset generation interface"""
    st.markdown("## 🎨 Generate Marketing Assets")
    
    # Product image display
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 📦 Your Product")
        if 'product_img' in st.session_state:
            product_img = st.session_state['product_img']
            if isinstance(product_img, str):
                st.image(product_img, use_container_width=True)
            else:
                st.image(product_img, use_container_width=True)
        else:
            st.info("No product image loaded")
    
    with col2:
        st.markdown("### 🎯 Asset Types to Generate")
        
        # Asset selection
        selected_assets = []
        for asset_type, config in ASSET_CONFIGS.items():
            col_check, col_info = st.columns([1, 4])
            with col_check:
                if st.checkbox(asset_type, value=True, key=f"gen_{asset_type}"):
                    selected_assets.append(asset_type)
            with col_info:
                st.markdown(f"""
                <div style="margin-left: 10px;">
                    <span class="resolution-badge">{config['icon']} {config['resolution']}</span>
                    <br><small style="color: #6b7280;">{config['description']}</small>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Generation controls
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        ensure_brand_text = st.checkbox(
            "🏷️ Ensure brand name is visible on product",
            value=True,
            help="The AI will make sure your brand name appears clearly on the product"
        )
    
    with col2:
        style_preset = st.selectbox(
            "Style Preset",
            ["Luxury", "Minimalist", "Natural", "Tech", "Vibrant", "Custom"],
            help="Choose a visual style preset"
        )
    
    with col3:
        if st.button("🚀 Generate All", type="primary", use_container_width=True):
            if not selected_assets:
                st.warning("Please select at least one asset type")
            elif 'product_img' not in st.session_state:
                st.warning("Please upload a product image first")
            else:
                with st.spinner("✨ Creating your marketing assets..."):
                    progress_bar = st.progress(0)
                    results = []
                    
                    for idx, asset_type in enumerate(selected_assets):
                        progress_bar.progress((idx + 1) / len(selected_assets))
                        
                        # Generate asset
                        try:
                            result = gemini_handler.generate_asset(
                                asset_type=asset_type,
                                brand_config=st.session_state.get('brand_config', {}),
                                product_image=st.session_state.get('product_img'),
                                ensure_brand_text=ensure_brand_text,
                                style_preset=style_preset
                            )
                            results.append(result)
                        except Exception as e:
                            st.error(f"Failed to generate {asset_type}: {str(e)}")
                    
                    # Store results
                    st.session_state['generated_assets'] = results
                    st.success(f"✅ Generated {len(results)} assets successfully!")
    
    # Display generated assets
    if 'generated_assets' in st.session_state and st.session_state['generated_assets']:
        st.markdown("### 🎨 Generated Assets")
        
        for asset in st.session_state['generated_assets']:
            with st.container():
                st.markdown(f"""
                <div class="asset-card">
                    <h4>{ASSET_CONFIGS[asset['type']]['icon']} {asset['type']}</h4>
                    <span class="resolution-badge">{ASSET_CONFIGS[asset['type']]['resolution']}</span>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.image(asset['image'], use_container_width=True)
                
                with col2:
                    st.markdown("##### Actions")
                    
                    # Save to gallery
                    if st.button(f"💾 Save", key=f"save_{asset['type']}_{asset.get('id', '')}"):
                        if 'saved_images' not in st.session_state:
                            st.session_state['saved_images'] = []
                        
                        st.session_state['saved_images'].append({
                            'type': asset['type'],
                            'image': asset['image'],
                            'timestamp': datetime.now().isoformat()
                        })
                        st.success("Saved to gallery!")
                    
                    # Download
                    if isinstance(asset['image'], Image.Image):
                        buf = io.BytesIO()
                        asset['image'].save(buf, format='PNG')
                        
                        st.download_button(
                            label="⬇️ Download",
                            data=buf.getvalue(),
                            file_name=f"{asset['type'].lower().replace(' ', '_')}.png",
                            mime="image/png",
                            key=f"download_{asset['type']}_{asset.get('id', '')}"
                        )

def render_chat_interface(gemini_handler):
    """Render the chat interface for editing"""
    st.markdown("## 💬 Chat & Edit with Nano Banana")
    
    # Layout with sidebar for saved images
    col_gallery, col_chat = st.columns([1, 3])
    
    with col_gallery:
        st.markdown("### 🖼️ Saved Images")
        st.markdown("<small>Click to use in chat</small>", unsafe_allow_html=True)
        
        if 'saved_images' in st.session_state and st.session_state['saved_images']:
            # Display thumbnails
            for idx, img_data in enumerate(st.session_state['saved_images']):
                cols = st.columns(2)
                with cols[idx % 2]:
                    if st.button(
                        f"📌 {img_data['type']}",
                        key=f"thumb_{idx}",
                        use_container_width=True
                    ):
                        st.session_state['selected_image_for_chat'] = img_data
                        st.session_state['chat_input'] = f"I've selected the {img_data['type']} image. "
            
            # Show selected image
            if 'selected_image_for_chat' in st.session_state:
                st.markdown("**Selected:**")
                st.image(
                    st.session_state['selected_image_for_chat']['image'],
                    use_container_width=True
                )
        else:
            st.info("No saved images yet. Generate and save some assets first!")
    
    with col_chat:
        # Chat messages container
        chat_container = st.container()
        
        with chat_container:
            st.markdown("""
            <div class="chat-container">
                <div class="assistant-message">
                    👋 Hi! I'm your AI assistant powered by Nano Banana. I can help you edit your marketing assets. 
                    Try commands like:
                    <ul>
                        <li>Change the background to sunset</li>
                        <li>Add golden hour lighting</li>
                        <li>Make it more luxurious</li>
                        <li>Add text overlay saying "Limited Edition"</li>
                        <li>Remove the background</li>
                    </ul>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Display chat history
            if 'chat_history' in st.session_state:
                for msg in st.session_state['chat_history']:
                    if msg['role'] == 'user':
                        st.markdown(f"""
                        <div class="chat-message user-message">
                            {msg['content']}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="chat-message assistant-message">
                            {msg['content']}
                        </div>
                        """, unsafe_allow_html=True)
                        if 'image' in msg:
                            st.image(msg['image'], use_container_width=True)
        
        # Chat input
        user_input = st.text_input(
            "Type your edit request...",
            value=st.session_state.get('chat_input', ''),
            key="chat_input_field",
            placeholder="e.g., 'Change the background to a tropical beach'"
        )
        
        if st.button("Send", type="primary", use_container_width=True):
            if user_input and 'selected_image_for_chat' in st.session_state:
                # Process chat request
                with st.spinner("✨ Processing your request..."):
                    try:
                        # Get the image from the selected data - FIXED ERROR HANDLING
                        selected_data = st.session_state['selected_image_for_chat']
                        
                        # Extract the actual image from various possible structures
                        image_to_edit = None
                        
                        if isinstance(selected_data, dict):
                            # Try different possible keys
                            for key in ['image', 'img', 'data', 'file']:
                                if key in selected_data:
                                    image_to_edit = selected_data[key]
                                    break
                        else:
                            # If it's directly an image
                            image_to_edit = selected_data
                        
                        if image_to_edit is None:
                            st.error("Could not find image in selected data. Please try selecting again.")
                        else:
                            edited_image = gemini_handler.chat_edit(
                                user_input,
                                image_to_edit
                            )
                            
                            # Add to chat history
                            if 'chat_history' not in st.session_state:
                                st.session_state['chat_history'] = []
                            
                            st.session_state['chat_history'].append({
                                'role': 'user',
                                'content': user_input
                            })
                            
                            st.session_state['chat_history'].append({
                                'role': 'assistant',
                                'content': "Here's your edited image!",
                                'image': edited_image
                            })
                            
                            # Clear the input
                            st.session_state['chat_input'] = ""
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error processing request: {str(e)}")
                        st.info("Please try selecting the image again from the gallery.")
            elif not user_input:
                st.warning("Please enter a request")
            else:
                st.warning("Please select an image from the gallery first")

def render_demo_section():
    """Render demo and help section"""
    st.markdown("## 🎬 Demo & Help")
    
    tab1, tab2, tab3 = st.tabs(["Video Demo", "Quick Guide", "About"])
    
    with tab1:
        st.markdown("### 📹 Watch How It Works")
        # Placeholder for YouTube video
        video_url = st.text_input(
            "YouTube Video URL",
            value="https://youtu.be/QxpwjWxxkwg?si=w9JInKKqHyduTkCO",
            disabled=True,
            help="Watch Demo video on youtube "
        )
        # st.info("🎥 Demo video coming soon! Check back later.")
    
    with tab2:
        st.markdown("""
        ### 🚀 Quick Start Guide
        
        1. **Upload Your Product** 📦
           - Use sample images or upload your own
           - Works best with clear product shots
        
        2. **Configure Your Brand** 🎨
           - Set brand name, colors, and tone
           - Define your visual style
        
        3. **Generate Assets** ✨
           - Select asset types (Instagram, Banner, etc.)
           - Click Generate to create all assets
        
        4. **Edit with Chat** 💬
           - Save generated assets to gallery
           - Select an image and describe edits
           - Download final results
        
        ### 💡 Pro Tips
        - Ensure product has clear branding visible
        - Use high-quality product images
        - Be specific in chat edit requests
        - Save multiple versions for A/B testing
        """)
    
    with tab3:
        st.markdown("""
        ### 🚀 About Nano Banana Studio
        
        Built with Google's Gemini Nano Banana model, this app helps you create 
        professional marketing assets in seconds.
        
        **Features:**
        - 🎨 Multiple asset types
        - 🤖 AI-powered generation
        - 💬 Interactive editing
        - 📱 Platform-optimized formats
        
        **Powered by:**
        - Google Gemini 2.5 Flash (Nano Banana)
        - Streamlit
        - Python
        
        ---
        Made with ❤️ for the Nano Banana Hackathon
        """)
