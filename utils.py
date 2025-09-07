import streamlit as st
from PIL import Image
import os
from pathlib import Path
from typing import List, Tuple

def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        'started': False,
        'product_img': None,
        'brand_config': {},
        'generated_assets': [],
        'saved_images': [],
        'chat_history': [],
        'selected_image_for_chat': None,
        'chat_session': None,
        'brand_name': 'Capsula',
        'brand_tone': 'Modern biotech luxury — innovative, pure, immersive.',
        'color_theme': 'Coral blush, teal turquoise, deep emerald, warm beige, onyx black.',
        'placement': 'Geometric pedestals or refined vanity; sparse organic props.',
        'composition': 'Clean symmetry for single-product; off-center for lifestyle; generous negative space.',
        'product_name': 'Capsula Serum X',
        'tagline': 'Glow deeper. Shine brighter.',
        'quote': 'My skin has never felt this good—truly a game-changer!',
        'customer_name': 'Sarah M.'
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def get_sample_images() -> List[Tuple[str, str, str]]:
    """Get sample product images for demo"""
    # Create sample images directory if it doesn't exist
    samples_dir = Path("sample_images")
    samples_dir.mkdir(exist_ok=True)
    
    # List of sample images (name, path, description)
    # These should be actual product images - user needs to add them
    samples = [
        (
            "Premium Serum",
            "sample_images/serum_bottle.png",
            "Luxury skincare serum with dropper"
        ),
        (
            "Face Cream",
            "sample_images/cream_jar.png",
            "Rich moisturizing cream jar"
        ),
        (
            "Beauty Oil",
            "sample_images/beauty_oil.png",
            "Nourishing facial oil bottle"
        )
    ]
    
    # Check if images exist, create info placeholder if not
    for name, path, desc in samples:
        if not Path(path).exists():
            # Create a gradient placeholder with instructions
            img = Image.new('RGBA', (500, 500), color=(0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Create gradient background
            for y in range(500):
                color_value = int(80 + (y / 500) * 50)
                draw.rectangle([(0, y), (500, y+1)], 
                             fill=(color_value, color_value, color_value+20, 255))
            
            # Add text
            try:
                font = ImageFont.truetype("DejaVuSans.ttf", 30)
                small_font = ImageFont.truetype("DejaVuSans.ttf", 20)
            except:
                font = ImageFont.load_default()
                small_font = font
            
            # Draw product name
            text = name
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            x = (500 - text_width) // 2
            draw.text((x, 200), text, fill=(255, 255, 255, 255), font=font)
            
            # Add instruction
            instruction = "Add product image"
            bbox = draw.textbbox((0, 0), instruction, font=small_font)
            text_width = bbox[2] - bbox[0]
            x = (500 - text_width) // 2
            draw.text((x, 250), instruction, fill=(200, 200, 200, 255), font=small_font)
            
            # Add file path
            file_text = f"to {path}"
            bbox = draw.textbbox((0, 0), file_text, font=small_font)
            text_width = bbox[2] - bbox[0]
            x = (500 - text_width) // 2
            draw.text((x, 280), file_text, fill=(180, 180, 180, 255), font=small_font)
            
            # Save placeholder
            img.save(path)
    
    return samples

def create_sample_product_images():
    """Create actual sample product images for demo"""
    samples_dir = Path("sample_images")
    samples_dir.mkdir(exist_ok=True)
    
    # You can add actual product images here
    # For now, using the placeholder creation from get_sample_images
    pass

def validate_image(image) -> bool:
    """Validate uploaded image"""
    try:
        if isinstance(image, str):
            img = Image.open(image)
        else:
            img = Image.open(image)
        
        # Check basic requirements
        width, height = img.size
        if width < 300 or height < 300:
            st.warning("Image resolution is too low. Please use at least 300x300 pixels.")
            return False
        
        if width > 4000 or height > 4000:
            st.warning("Image is too large. Please use images under 4000x4000 pixels.")
            return False
        
        return True
    except Exception as e:
        st.error(f"Invalid image: {str(e)}")
        return False

def format_file_size(size_bytes: int) -> str:
    """Format file size for display"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def get_image_info(image) -> dict:
    """Get image information"""
    if isinstance(image, str):
        img = Image.open(image)
        file_size = os.path.getsize(image) if os.path.exists(image) else 0
    else:
        img = Image.open(image)
        file_size = image.size if hasattr(image, 'size') else 0
    
    width, height = img.size
    format = img.format or 'Unknown'
    mode = img.mode
    
    return {
        'width': width,
        'height': height,
        'format': format,
        'mode': mode,
        'file_size': format_file_size(file_size),
        'aspect_ratio': f"{width}:{height}"
    }

def aspect_crop(img: Image.Image, target_ratio: Tuple[int, int]) -> Image.Image:
    """Crop image to target aspect ratio"""
    w, h = img.size
    target_w, target_h = target_ratio
    target = target_w / target_h
    current = w / h
    
    if abs(current - target) < 1e-6:
        return img.copy()
    
    if current > target:
        # Too wide - crop width
        new_w = int(h * target)
        left = (w - new_w) // 2
        box = (left, 0, left + new_w, h)
    else:
        # Too tall - crop height
        new_h = int(w / target)
        top = (h - new_h) // 2
        box = (0, top, w, top + new_h)
    
    return img.crop(box)

def resize_for_display(img: Image.Image, max_size: int = 800) -> Image.Image:
    """Resize image for display while maintaining aspect ratio"""
    w, h = img.size
    if w > max_size or h > max_size:
        if w > h:
            new_w = max_size
            new_h = int(h * (max_size / w))
        else:
            new_h = max_size
            new_w = int(w * (max_size / h))
        return img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    return img

def img_to_bytes(img: Image.Image, format: str = "PNG") -> bytes:
    """Convert PIL image to bytes"""
    import io
    buffer = io.BytesIO()
    img.save(buffer, format=format)
    return buffer.getvalue()

def clear_cache():
    """Clear specific cache items"""
    cache_keys = ['generated_assets', 'saved_images', 'chat_history']
    for key in cache_keys:
        if key in st.session_state:
            del st.session_state[key]
    st.success("Cache cleared!")

def get_preset_styles() -> dict:
    """Get preset style configurations"""
    return {
        "Luxury": {
            "colors": ["gold", "black", "white", "cream"],
            "mood": "elegant, sophisticated, premium",
            "props": "marble, gold accents, silk, crystals"
        },
        "Minimalist": {
            "colors": ["white", "gray", "beige", "soft pastels"],
            "mood": "clean, simple, modern",
            "props": "geometric shapes, clean surfaces, minimal decor"
        },
        "Natural": {
            "colors": ["green", "brown", "earth tones", "soft blues"],
            "mood": "organic, authentic, eco-friendly",
            "props": "plants, wood, stones, natural textures"
        },
        "Tech": {
            "colors": ["blue", "silver", "black", "neon accents"],
            "mood": "futuristic, innovative, sleek",
            "props": "LED lights, metallic surfaces, geometric patterns"
        },
        "Vibrant": {
            "colors": ["bright colors", "gradients", "bold contrasts"],
            "mood": "energetic, playful, dynamic",
            "props": "colorful backgrounds, abstract shapes, bold patterns"
        }
    }

def generate_prompt_suggestions(product_type: str) -> List[str]:
    """Generate edit prompt suggestions based on product type"""
    base_suggestions = [
        "Change the background to a sunset beach",
        "Add golden hour lighting",
        "Make it more luxurious and premium",
        "Add subtle sparkle effects",
        "Place on a marble surface",
        "Add botanical elements around the product",
        "Create a dreamy, ethereal atmosphere",
        "Add water droplets for freshness",
        "Place in a minimalist setting",
        "Add geometric shadows"
    ]
    
    if "serum" in product_type.lower() or "skincare" in product_type.lower():
        base_suggestions.extend([
            "Add dewdrops on the bottle",
            "Place with rose petals",
            "Create a spa-like atmosphere",
            "Add jade roller as prop"
        ])
    elif "tech" in product_type.lower():
        base_suggestions.extend([
            "Add holographic effects",
            "Create a futuristic background",
            "Add neon lighting",
            "Place on a tech desk setup"
        ])
    
    return base_suggestions
