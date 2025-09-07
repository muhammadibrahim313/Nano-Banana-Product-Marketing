import json
from typing import Optional, Dict, List, Any
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import textwrap
from google import genai
from google.genai import types

class GeminiHandler:
    """Handler for all Gemini API interactions"""
    
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.image_model = "gemini-2.5-flash-image-preview"  # Nano Banana
        self.text_model = "gemini-2.5-flash"
        self.chat_session = None
    
    def generate_asset(
        self,
        asset_type: str,
        brand_config: Dict,
        product_image: Any,
        ensure_brand_text: bool = True,
        style_preset: str = "Luxury"
    ) -> Dict:
        """Generate a marketing asset using Nano Banana"""
        
        # Build the prompt
        prompt = self._build_generation_prompt(
            asset_type, 
            brand_config, 
            ensure_brand_text,
            style_preset
        )
        
        # Convert product image if needed
        if product_image:
            if isinstance(product_image, str):
                # File path
                product_img = Image.open(product_image).convert("RGBA")
            else:
                # Uploaded file
                product_img = Image.open(product_image).convert("RGBA")
        else:
            product_img = None
        
        # Generate with Gemini
        contents = [prompt]
        if product_img:
            contents.append(product_img)
        
        response = self.client.models.generate_content(
            model=self.image_model,
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=['Image']
            )
        )
        
        # Extract generated image
        generated_image = self._extract_image_from_response(response)
        
        # Apply testimonial overlay if needed
        if asset_type == "Testimonial Graphic" and generated_image:
            generated_image = self._add_testimonial_overlay(
                generated_image,
                brand_config.get('quote', ''),
                brand_config.get('customerName', ''),
                brand_config.get('productName', '')
            )
        
        return {
            'type': asset_type,
            'image': generated_image,
            'id': self._generate_id()
        }
    
    def chat_edit(self, user_request: str, image: Any) -> Image.Image:
        """Edit an image based on chat request"""
        
        # Initialize chat session if needed
        if not self.chat_session:
            self.chat_session = self.client.chats.create(model=self.image_model)
        
        # Prepare the image
        if isinstance(image, dict):
            img = image.get('image')
        else:
            img = image
        
        # Ensure image is PIL Image
        if not isinstance(img, Image.Image):
            if isinstance(img, str):
                img = Image.open(img).convert("RGBA")
            else:
                img = Image.open(img).convert("RGBA")
        
        # Enhanced prompt for better editing
        enhanced_prompt = f"""
        {user_request}
        
        IMPORTANT: 
        - Maintain the product's visibility and branding
        - Keep any text on the product packaging clear and legible
        - Apply the requested changes while preserving product integrity
        - Ensure high quality photorealistic output
        """
        
        # Send message with image
        contents = [enhanced_prompt, img]
        response = self.chat_session.send_message(contents)
        
        # Extract edited image
        edited_image = self._extract_image_from_response(response)
        
        return edited_image
    
    def generate_style_suggestions(
        self,
        product_name: str,
        brand_config: Dict,
        category: str = "Skincare"
    ) -> List[Dict]:
        """Generate style suggestions for different asset types"""
        
        system_prompt = """You are a luxury product photographer/stylist.
        Return JSON ONLY with asset style suggestions.
        Format: {"assets":[{"assetType":"...", "backgroundTone":"...", 
        "surfaceType":"...", "accentProp":"...", "lighting":"...", 
        "cameraAngle":"...", "suggestedText":"..."}]}
        Create 5 diverse asset styles."""
        
        user_prompt = f"""Product: {product_name}
Brand: {brand_config.get('brandName')}
Tone: {brand_config.get('brandTone')}
Colors: {brand_config.get('colorTheme')}
Category: {category}

Generate 5 asset style suggestions for Instagram Post, Instagram Story, 
Website Banner, Ad Creative, and Testimonial Graphic."""
        
        try:
            response = self.client.models.generate_content(
                model=self.text_model,
                contents=[system_prompt, user_prompt]
            )
            
            # Parse JSON response
            text = ""
            for candidate in response.candidates:
                for part in candidate.content.parts:
                    if hasattr(part, 'text'):
                        text += part.text
            
            # Clean and parse JSON
            text = text.strip().strip('`')
            if text.startswith('json'):
                text = text[4:]
            
            return json.loads(text).get('assets', [])
        
        except Exception as e:
            # Return default suggestions if generation fails
            return self._get_default_style_suggestions()
    
    def _build_generation_prompt(
        self,
        asset_type: str,
        brand_config: Dict,
        ensure_brand_text: bool,
        style_preset: str
    ) -> str:
        """Build detailed prompt for asset generation"""
        
        # Aspect ratio mapping
        aspect_ratios = {
            "Instagram Post": "square 1:1",
            "Instagram Story": "vertical 9:16",
            "Website Banner": "horizontal 16:9",
            "Ad Creative": "square 1:1",
            "Testimonial Graphic": "square 1:1"
        }
        
        # Style preset descriptions
        style_descriptions = {
            "Luxury": "premium, elegant, sophisticated with rich textures and golden accents",
            "Minimalist": "clean, simple, modern with plenty of white space",
            "Natural": "organic, earthy, authentic with natural materials and soft lighting",
            "Tech": "futuristic, sleek, innovative with geometric shapes and cool tones",
            "Vibrant": "colorful, energetic, bold with dynamic compositions",
            "Custom": "based on brand guidelines"
        }
        
        # Build the main prompt
        brand_name = brand_config.get('brandName', 'the brand')
        product_name = brand_config.get('productName', 'product')
        
        prompt = f"""Create a {aspect_ratios[asset_type]} photorealistic {asset_type} 
for the {product_name} from {brand_name}.

CRITICAL REQUIREMENTS:
1. The product image provided must be the central focus
2. Product must be clearly visible and not obscured
3. {"ENSURE THE BRAND NAME '" + brand_name + "' IS CLEARLY VISIBLE ON THE PRODUCT PACKAGING/LABEL" if ensure_brand_text else ""}
4. The product text/label must be legible and eye-catching
5. DO NOT add any overlay text or captions - only show the product's actual packaging text
6. Create a premium, professional marketing image

Visual Style: {style_descriptions.get(style_preset, style_descriptions['Luxury'])}

Brand Guidelines:
- Tone: {brand_config.get('brandTone', 'Modern and sophisticated')}
- Color Palette: {brand_config.get('colorTheme', 'Neutral and elegant')}
- Product Placement: {brand_config.get('productPlacement', 'Center-focused with props')}
- Composition: {brand_config.get('compositionGuidelines', 'Balanced and clean')}

Specific for {asset_type}:
- Create a scene that highlights the product beautifully
- Use appropriate lighting and props for the brand aesthetic
- Ensure the composition works for the {aspect_ratios[asset_type]} format
{"- Include subtle lifestyle elements suggesting customer satisfaction" if asset_type == "Testimonial Graphic" else ""}
{"- Perfect for Instagram feed with eye-catching composition" if asset_type == "Instagram Post" else ""}
{"- Optimized for vertical mobile viewing" if asset_type == "Instagram Story" else ""}
{"- Wide cinematic composition for web headers" if asset_type == "Website Banner" else ""}
{"- Bold and attention-grabbing for social media ads" if asset_type == "Ad Creative" else ""}

Remember: 
- Product packaging text must be clearly readable
- The brand name should be prominent and visible
- Maintain photorealistic quality
- No added text overlays, only the product's actual branding"""
        
        return prompt
    
    def _extract_image_from_response(self, response) -> Optional[Image.Image]:
        """Extract image from Gemini response"""
        try:
            for candidate in response.candidates:
                for part in candidate.content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        if hasattr(part.inline_data, 'data'):
                            data = part.inline_data.data
                            if isinstance(data, str):
                                data = base64.b64decode(data)
                            return Image.open(io.BytesIO(data)).convert("RGBA")
        except Exception as e:
            print(f"Error extracting image: {e}")
        return None
    
    def _add_testimonial_overlay(
        self,
        image: Image.Image,
        quote: str,
        customer_name: str,
        product_name: str
    ) -> Image.Image:
        """Add testimonial text overlay to image"""
        img = image.copy()
        draw = ImageDraw.Draw(img)
        width, height = img.size
        
        # Try to load a nice font, fallback to default
        try:
            # Try different font sizes based on image size
            font_size = max(int(height * 0.03), 20)
            small_font_size = max(int(height * 0.02), 16)
            
            font = ImageFont.truetype("DejaVuSans.ttf", size=font_size)
            small_font = ImageFont.truetype("DejaVuSans.ttf", size=small_font_size)
        except:
            try:
                # Try Arial as fallback
                font = ImageFont.truetype("arial.ttf", size=30)
                small_font = ImageFont.truetype("arial.ttf", size=20)
            except:
                font = ImageFont.load_default()
                small_font = font
        
        # Add semi-transparent overlay at bottom
        overlay_height = height // 3
        overlay = Image.new('RGBA', (width, overlay_height), (0, 0, 0, 200))
        
        # Gradient overlay for better visibility
        for y in range(overlay_height):
            alpha = int(200 * (1 - y / overlay_height * 0.3))
            for x in range(width):
                overlay.putpixel((x, y), (0, 0, 0, alpha))
        
        img.paste(overlay, (0, height - overlay_height), overlay)
        
        # Add quote text
        if quote:
            # Clean quote
            quote = quote.strip()
            if not quote.startswith('"'):
                quote = f'"{quote}"'
            
            # Wrap text based on image width
            max_width = width - 60  # 30px margin on each side
            wrapped = self._wrap_text(draw, quote, font, max_width)
            
            y_text = height - overlay_height + 30
            
            for line in wrapped:
                # Add shadow for better readability
                shadow_offset = 2
                draw.text((30 + shadow_offset, y_text + shadow_offset), 
                         line, font=font, fill=(0, 0, 0, 150))
                draw.text((30, y_text), line, font=font, fill=(255, 255, 255, 255))
                
                bbox = draw.textbbox((0, 0), line, font=font)
                line_height = bbox[3] - bbox[1]
                y_text += line_height + 10
            
            # Add attribution
            if customer_name:
                attribution = f"— {customer_name}"
                draw.text((30 + 2, y_text + 10 + 2), attribution, 
                         font=small_font, fill=(0, 0, 0, 150))
                draw.text((30, y_text + 10), attribution, 
                         font=small_font, fill=(255, 255, 255, 230))
                y_text += 30
            
            # Add product name
            if product_name:
                draw.text((30 + 2, y_text + 10 + 2), product_name, 
                         font=small_font, fill=(0, 0, 0, 150))
                draw.text((30, y_text + 10), product_name, 
                         font=small_font, fill=(255, 200, 100, 255))
        
        return img
    
    def _wrap_text(self, draw, text: str, font, max_width: int) -> List[str]:
        """Wrap text to fit within max_width"""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = f"{current_line} {word}".strip()
            bbox = draw.textbbox((0, 0), test_line, font=font)
            line_width = bbox[2] - bbox[0]
            
            if line_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def _generate_id(self) -> str:
        """Generate unique ID for assets"""
        import random
        import string
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    
    def _get_default_style_suggestions(self) -> List[Dict]:
        """Return default style suggestions"""
        return [
            {
                "assetType": "Instagram Post",
                "backgroundTone": "soft gradient from coral to cream",
                "surfaceType": "marble surface with subtle veining",
                "accentProp": "dried flowers and gold accents",
                "lighting": "warm, diffused natural light",
                "cameraAngle": "45-degree elevated angle",
                "suggestedText": "Discover your glow"
            },
            {
                "assetType": "Instagram Story",
                "backgroundTone": "ethereal lavender mist",
                "surfaceType": "silk fabric with gentle folds",
                "accentProp": "crystal prisms creating light refractions",
                "lighting": "soft backlight with golden hour tones",
                "cameraAngle": "straight-on portrait orientation",
                "suggestedText": "New arrival alert!"
            },
            {
                "assetType": "Website Banner",
                "backgroundTone": "deep emerald to teal gradient",
                "surfaceType": "water surface with gentle ripples",
                "accentProp": "botanical elements and dewdrops",
                "lighting": "dramatic side lighting",
                "cameraAngle": "wide cinematic shot",
                "suggestedText": "Transform your routine"
            },
            {
                "assetType": "Ad Creative",
                "backgroundTone": "luxurious black with gold particles",
                "surfaceType": "reflective obsidian surface",
                "accentProp": "geometric gold frames",
                "lighting": "spotlight with rim lighting",
                "cameraAngle": "dynamic diagonal composition",
                "suggestedText": "Limited time: 20% off"
            },
            {
                "assetType": "Testimonial Graphic",
                "backgroundTone": "warm beige with soft shadows",
                "surfaceType": "textured paper background",
                "accentProp": "subtle botanical illustrations",
                "lighting": "soft, even lighting",
                "cameraAngle": "centered, balanced composition",
                "suggestedText": "Real results from real customers"
            }
        ]
