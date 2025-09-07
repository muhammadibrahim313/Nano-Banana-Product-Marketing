# 🎨 Nano Banana Studio - AI Marketing Asset Creator

Transform your product images into stunning marketing assets using Google's Gemini Nano Banana model.

## ✨ Features

### 🚀 Improved User Experience
- **Hero Section**: Beautiful onboarding with clear value proposition
- **Sample Images**: Quick start with pre-loaded product examples
- **Intuitive Flow**: Step-by-step process from upload to export

### 🎨 Smart Asset Generation
- **Multiple Formats**: Instagram Posts, Stories, Website Banners, Ad Creatives, Testimonial Graphics
- **Resolution Display**: Shows exact dimensions for each asset type
- **Brand Text Assurance**: Ensures brand name is visible on product
- **Style Presets**: Luxury, Minimalist, Natural, Tech, Vibrant options

### 💬 Interactive Chat Interface
- **Edit with Natural Language**: "Change background to sunset", "Add golden lighting"
- **Image Gallery**: Save and manage generated assets
- **Visual Sidebar**: Click thumbnails to select for editing
- **Real-time Processing**: See edits applied instantly

### 📦 Technical Improvements
- **Modular Architecture**: Separated into multiple files for maintainability
- **Session Management**: Smart caching and state handling
- **Error Handling**: Graceful fallbacks and user-friendly error messages
- **Responsive Design**: Works on desktop and mobile

## 🛠️ Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Key
Create a `.env` file in the project root:
```env
GEMINI_API_KEY=your_api_key_here
```

Get your API key from: https://makersuite.google.com/app/apikey

### 3. Project Structure
```
project/
├── app.py                 # Main application
├── ui_components.py       # UI rendering functions
├── gemini_handler.py      # Gemini API interactions
├── utils.py              # Utility functions
├── requirements.txt      # Dependencies
├── .env                  # API key (create this)
└── sample_images/        # Sample product images (auto-created)
```

### 4. Run the App
```bash
streamlit run app.py
```

## 📱 How to Use

### Step 1: Upload or Select Product
- Use sample images for quick testing
- Upload your own product image (PNG/JPG)
- Best results with clear product shots

### Step 2: Configure Brand
- Set brand name, tone, and colors
- Define visual guidelines
- Add product details and tagline

### Step 3: Generate Assets
- Select asset types to create
- Choose style preset
- Enable "Ensure brand text" for clear labeling
- Click Generate All

### Step 4: Save & Edit
- Save generated assets to gallery
- Use chat interface for edits
- Download final results

## 💡 Pro Tips

### For Best Results:
1. **Product Images**: Use high-quality images with clear product visibility
2. **Brand Text**: Enable "Ensure brand name visible" for professional results
3. **Chat Edits**: Be specific - "Add warm sunset lighting" vs "change lighting"
4. **Multiple Versions**: Save different variations for A/B testing

### Chat Commands Examples:
- "Change the background to a tropical beach"
- "Add golden hour lighting"
- "Make it more luxurious and premium"
- "Place on a marble surface with rose petals"
- "Add water droplets for freshness"
- "Create a minimalist white background"

## 🔧 Customization

### Adding New Asset Types
Edit `ASSET_CONFIGS` in `ui_components.py`:
```python
"New Asset Type": {
    "resolution": "1200x1200",
    "aspect": (1, 1),
    "icon": "🎯",
    "description": "Custom asset description"
}
```

### Modifying Brand Defaults
Update defaults in `ui_components.py` `render_brand_sidebar()` function.

### Custom Style Presets
Add new presets in `gemini_handler.py` `style_descriptions` dictionary.

## 🐛 Troubleshooting

### Common Issues:
1. **API Key Error**: Ensure `.env` file exists with valid key
2. **Generation Fails**: Check internet connection and API quota
3. **Images Not Displaying**: Verify image format (PNG/JPG)
4. **Chat Not Working**: Refresh page to reset chat session

### Streamlit Cloud Deployment:
1. Add API key to Streamlit Secrets
2. Ensure all dependencies in requirements.txt
3. Use relative paths for file operations

## 📈 Improvements Made

### From Original Version:
✅ Better UI/UX with hero section and clear flow
✅ Brand text visibility enforcement
✅ Resolution badges for each asset type
✅ Interactive chat interface replacing basic edit tab
✅ Image gallery with save functionality
✅ Download buttons integrated in generation view
✅ Modular code structure (4 files vs 1)
✅ Sample images for quick start
✅ Professional styling with gradients and cards
✅ Comprehensive error handling
✅ Session state management

## 🚀 Future Enhancements
- Video demo integration
- Batch processing
- Template library
- Export to social media APIs
- Advanced analytics
- Multi-language support

## 📝 License
Apache 2.0 (matching Google's Nano Banana license)

## 🤝 Contributing
Built for the Nano Banana Hackathon. Contributions welcome!

---
Made with ❤️ using Google Gemini 2.5 Flash (Nano Banana)
