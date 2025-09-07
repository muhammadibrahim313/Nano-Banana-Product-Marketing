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
        
        CRITICAL RULES: 
        - DO NOT change the product itself - keep the EXACT same product from the image
        - Only modify the background, lighting, props, or scene around the product
        - Maintain the product's shape, color, branding, and all text exactly as shown
        - The product must remain the central focus
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
        
        prompt = f"""Create a {aspect_ratios[asset_type]} photorealistic marketing {asset_type}.

ABSOLUTELY CRITICAL REQUIREMENTS - MUST FOLLOW:
1. USE THE EXACT PRODUCT FROM THE PROVIDED IMAGE - DO NOT CREATE A NEW PRODUCT
2. The product in the image MUST remain EXACTLY the same - same shape, same color, same packaging, same text
3. DO NOT generate a different product or change any aspect of the product itself
4. Only change the BACKGROUND, SCENE, PROPS, and LIGHTING around the product
5. The product from the image must be the central focus in the new scene
6. {"Ensure any text on the product (including brand name '" + brand_name + "') remains clearly visible" if ensure_brand_text else "Keep product text visible"}
7. Place the EXACT SAME product from the reference image into a new marketing scene

What you CAN change:
- Background environment and colors
- Surface the product sits on
- Props and decorative elements around the product
- Lighting and shadows
- Overall composition and angle (but keep the same product)

What you CANNOT change:
- The product itself (must be identical to the input image)
- Product shape, color, or packaging design
- Any text or labels on the product
- Product material or texture

Visual Style for the SCENE (not the product): {style_descriptions.get(style_preset, style_descriptions['Luxury'])}

Brand Guidelines for the SCENE:
- Tone: {brand_config.get('brandTone', 'Modern and sophisticated')}
- Color Palette FOR BACKGROUND: {brand_config.get('colorTheme', 'Neutral and elegant')}
- Product Placement: {brand_config.get('productPlacement', 'Center-focused with props')}
- Composition: {brand_config.get('compositionGuidelines', 'Balanced and clean')}

Specific requirements for {asset_type}:
{"- Create an eye-catching square composition perfect for Instagram feed" if asset_type == "Instagram Post" else ""}
{"- Design for vertical mobile viewing with the product prominently displayed" if asset_type == "Instagram Story" else ""}
{"- Create a wide cinematic scene with the product as hero element" if asset_type == "Website Banner" else ""}
{"- Make it bold and attention-grabbing for social media advertising" if asset_type == "Ad Creative" else ""}
{"- Design a testimonial-ready scene with elegant, trustworthy atmosphere" if asset_type == "Testimonial Graphic" else ""}

FINAL REMINDER: Use the EXACT product from the provided image. Only create a new scene/background around it."""
        
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
        """Add elegant testimonial text overlay to image"""
        img = image.copy()
        width, height = img.size
        
        # Create a new image for overlay
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        # Create semi-transparent dark band at bottom (not gradient)
        band_height = height // 3
        band_top = height - band_height
        
        # Draw a solid semi-transparent rectangle
        overlay_draw.rectangle(
            [(0, band_top), (width, height)],
            fill=(25, 25, 35, 220)  # Dark with high opacity
        )
        
        # Add subtle top edge line for definition
        overlay_draw.rectangle(
            [(0, band_top), (width, band_top + 2)],
            fill=(102, 126, 234, 150)  # Purple accent line
        )
        
        # Composite the overlay
        img = Image.alpha_composite(img, overlay)
        draw = ImageDraw.Draw(img)
        
        # Load fonts
        try:
            quote_size = max(int(height * 0.03), 22)
            name_size = max(int(height * 0.022), 18)
            product_size = max(int(height * 0.018), 16)
            
            quote_font = ImageFont.truetype("DejaVuSans.ttf", size=quote_size)
            name_font = ImageFont.truetype("DejaVuSans.ttf", size=name_size)
            product_font = ImageFont.truetype("DejaVuSans-Bold.ttf", size=product_size)
        except:
            quote_font = ImageFont.load_default()
            name_font = quote_font
            product_font = quote_font
        
        # Add quote with better positioning
        if quote:
            quote = quote.strip()
            if not quote.startswith('"'):
                quote = f'"{quote}"'
            
            # Calculate text area
            margin = width // 15
            max_width = width - (2 * margin)
            
            # Wrap text
            wrapped = self._wrap_text(draw, quote, quote_font, max_width)
            
            # Calculate vertical centering in the band
            line_height = quote_size + 8
            text_block_height = len(wrapped) * line_height
            if customer_name:
                text_block_height += name_size + 15
            if product_name:
                text_block_height += product_size + 10
            
            # Start position (centered in band)
            y_text = band_top + (band_height - text_block_height) // 2
            y_text = max(y_text, band_top + 20)  # Ensure minimum padding
            
            # Draw quote lines
            for line in wrapped:
                # Draw white text directly (no shadow for cleaner look)
                draw.text((margin, y_text), line, font=quote_font, 
                         fill=(255, 255, 255, 255))
                y_text += line_height
            
            # Add spacing before attribution
            y_text += 10
            
            # Add customer name
            if customer_name:
                attribution = f"— {customer_name}"
                draw.text((margin, y_text), attribution, 
                         font=name_font, fill=(255, 255, 255, 200))
                y_text += name_size + 8
            
            # Add product name with accent color
            if product_name:
                draw.text((margin, y_text), product_name, 
                         font=product_font, fill=(255, 200, 100, 255))
        
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
                "backgroundTone": "soft beige with warm undertones",
                "surfaceType": "textured linen or silk fabric",
                "accentProp": "subtle floral arrangements",
                "lighting": "soft, diffused window light",
                "cameraAngle": "slightly elevated, centered composition",
                "suggestedText": "Real results from real customers"
            }
        ]
