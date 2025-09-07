import os, io, json, base64
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import streamlit as st
from PIL import Image
from dotenv import load_dotenv

# --- Gemini SDK ---
# Docs & quickstart: https://googleapis.github.io/python-genai/  (SDK)
# Image generation:   https://ai.google.dev/gemini-api/docs/image-generation
# Inline images:      https://ai.google.dev/gemini-api/docs/image-understanding
from google import genai

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    st.error("GEMINI_API_KEY missing in .env")
    st.stop()

client = genai.Client(api_key=API_KEY)

IMAGE_MODEL = "gemini-2.5-flash-image-preview"   # Nano Banana
TEXT_MODEL  = "gemini-2.5-flash"                 # for JSON styling hints

st.set_page_config(page_title="Nano Banana – Product Assets", layout="wide")
st.title("🍌 Nano Banana – Product Marketing Assets Generator")

# ---------------------------
# Helpers
# ---------------------------
def pil_image_from_upload(file) -> Image.Image:
    img = Image.open(file).convert("RGBA")
    return img

def save_pil_get_bytes(img: Image.Image, fmt="PNG") -> bytes:
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()

def gemini_generate_image(prompt_text: str,
                          product_image: Optional[Image.Image] = None) -> Image.Image:
    """
    Calls Gemini 2.5 Flash Image with text-only or text + reference image.
    The SDK supports passing PIL images directly in contents.
    """
    contents = [prompt_text]
    if product_image is not None:
        contents.append(product_image)

    # Using the models interface per SDK docs / dev blog sample
    resp = client.models.generate_content(
        model=IMAGE_MODEL,
        contents=contents,
    )

    # Find first inline image in response parts
    for cand in resp.candidates:
        for part in cand.content.parts:
            if getattr(part, "inline_data", None) and getattr(part.inline_data, "data", None):
                # part.inline_data.data is bytes already in SDK; ensure PIL opens it
                data = part.inline_data.data
                if isinstance(data, str):
                    data = base64.b64decode(data)
                return Image.open(io.BytesIO(data)).convert("RGBA")

    raise RuntimeError("No image returned by the model")

def gemini_suggest_styles(product_name: str,
                          tagline: str,
                          brand: Dict[str, str],
                          category: str,
                          benefit: str) -> Dict[str, Any]:
    """
    Ask the text model to return a JSON structure for 5 assets.
    We keep it simple: prompt to output JSON only.
    """
    sys = (
        "You are a luxury product photographer and stylist. "
        "Return JSON only. No prose. Keys: assets["
        "{assetType,backgroundTone,surfaceType,accentProp,lighting,cameraAngle,overlayText}]. "
        "Asset types: Instagram Post, Instagram Story, Website Banner, Ad Creative, Testimonial Graphic. "
        "Vary background/surface/prop/lighting/angle per asset; keep a cohesive campaign vibe."
    )
    user = (
        f"Product Name: {product_name}\n"
        f"Tagline: {tagline}\n"
        f"Brand: {brand.get('brandName')}\n"
        f"Tone: {brand.get('brandTone')}\n"
        f"Category: {category}\n"
        f"Benefit: {benefit}\n"
        f"Color palette: {brand.get('colorTheme')}\n"
        f"Placement: {brand.get('productPlacement')}\n"
        f"Composition: {brand.get('compositionGuidelines')}\n"
        "Return the JSON now."
    )

    resp = client.models.generate_content(
        model=TEXT_MODEL,
        contents=[sys, user],
    )

    txt = ""
    for cand in resp.candidates:
        for part in cand.content.parts:
            if getattr(part, "text", None):
                txt += part.text

    # Attempt to extract JSON
    txt = txt.strip().strip("`")
    # Handle fenced code blocks if any
    if txt.startswith("json"):
        txt = txt[4:]
    try:
        data = json.loads(txt)
    except Exception:
        # fallback default
        data = {
            "assets": [
                {
                  "assetType":"Instagram Post",
                  "backgroundTone":"soft blush gradient",
                  "surfaceType":"satin draped cloth",
                  "accentProp":"gold-trimmed ribbon",
                  "lighting":"warm side spotlight",
                  "cameraAngle":"45-degree angle",
                  "overlayText":"Glow deeper. Shine brighter."
                },
                {
                  "assetType":"Instagram Story",
                  "backgroundTone":"pale lavender with light streaks",
                  "surfaceType":"textured ceramic tray",
                  "accentProp":"scattered rose petals",
                  "lighting":"top-down diffused glow",
                  "cameraAngle":"overhead close-up",
                  "overlayText":"Hydration you can feel."
                },
                {
                  "assetType":"Website Banner",
                  "backgroundTone":"muted green stone",
                  "surfaceType":"brushed concrete slab",
                  "accentProp":"eucalyptus branch",
                  "lighting":"soft angled morning light",
                  "cameraAngle":"side-profile landscape",
                  "overlayText":"Glow like never before!"
                },
                {
                  "assetType":"Ad Creative",
                  "backgroundTone":"deep emerald gradient",
                  "surfaceType":"reflective glass base",
                  "accentProp":"frosted crystal orb",
                  "lighting":"dramatic backlight",
                  "cameraAngle":"elevated 3/4 angle",
                  "overlayText":"10% Off Today Only"
                },
                {
                  "assetType":"Testimonial Graphic",
                  "backgroundTone":"cream linen",
                  "surfaceType":"polished marble",
                  "accentProp":"single white tulip",
                  "lighting":"natural side lighting",
                  "cameraAngle":"straight-on clean view",
                  "overlayText":"“My skin has never felt this good.”"
                }
            ]
        }
    return data

def build_prompt(asset, brand, product_name, tagline) -> str:
    return (
        f"Create a { 'vertical 9:16' if asset['assetType']=='Instagram Story' else 'square 1:1' } "
        f"photorealistic **{asset['assetType']}** for the skincare product {product_name} "
        f"from {brand['brandName']}. "
        "The product image is provided; keep label and product unchanged and legible; "
        "integrate it into a premium, minimal scene.\n\n"
        f"Background: {asset['backgroundTone']}. "
        f"Surface: {asset['surfaceType']}. "
        f"Add a tasteful prop: {asset['accentProp']}. "
        f"Lighting: {asset['lighting']}. "
        f"Camera angle: {asset['cameraAngle']}. "
        "Keep composition clean, brand-first, with generous negative space.\n\n"
        "Brand constraints:\n"
        f"- Tone: {brand['brandTone']}\n"
        f"- Color palette: {brand['colorTheme']}\n"
        f"- Product placement: {brand['productPlacement']}\n"
        f"- Composition: {brand['compositionGuidelines']}\n\n"
        f'Optional overlay text: "{asset["overlayText"]}" (legible, elegant, harmonious). '
        "If adding text, maintain crisp typography and contrast. "
        "Return one high-quality image."
    )

# ---------------------------
# UI – left: form; right: outputs
# ---------------------------
with st.sidebar:
    st.header("Brand Settings")
    default_brand = {
      "brandName": "Capsula",
      "brandTone": "Modern biotech luxury — innovative, pure, immersive.",
      "colorTheme": "Coral blush, teal turquoise, deep emerald, warm beige, onyx black.",
      "productPlacement": "On geometric pedestals or refined vanity with sparse organic props.",
      "compositionGuidelines": "Clean symmetry for single-product; dynamic off-center for lifestyle; generous negative space."
    }
    brand = {}
    brand["brandName"] = st.text_input("Brand name", default_brand["brandName"])
    brand["brandTone"] = st.text_area("Brand tone", default_brand["brandTone"], height=70)
    brand["colorTheme"] = st.text_area("Color palette", default_brand["colorTheme"], height=60)
    brand["productPlacement"] = st.text_area("Placement rules", default_brand["productPlacement"], height=60)
    brand["compositionGuidelines"] = st.text_area("Composition rules", default_brand["compositionGuidelines"], height=80)

st.subheader("1) Product & Campaign Form")

col1, col2 = st.columns([2,1])
with col1:
    product_name = st.text_input("What's the product's name?", "Capsula Serum X")
    tagline      = st.text_input("What is the product tagline?", "Glow deeper. Shine brighter.")
    category     = st.text_input("Product category", "Serum")
    benefit      = st.text_input("What is the benefit of the product?", "Deep hydration and barrier repair.")
with col2:
    uploaded = st.file_uploader("Upload product image (PNG/JPG)", type=["png","jpg","jpeg"])
    if uploaded:
        product_img = pil_image_from_upload(uploaded)
        st.image(product_img, caption="Product reference", use_column_width=True)
    else:
        product_img = None

st.markdown("---")
st.subheader("2) Style Plan (JSON)")
colA, colB = st.columns([1,1])
with colA:
    if st.button("Suggest styles with Gemini (JSON)"):
        st.session_state["styles"] = gemini_suggest_styles(product_name, tagline, brand, category, benefit)

with colB:
    if "styles" not in st.session_state:
        st.session_state["styles"] = {"assets": []}
    styles_json = st.text_area(
        "Edit or paste styles JSON (assets[5])",
        value=json.dumps(st.session_state["styles"], indent=2),
        height=300
    )

# validate JSON
try:
    style_plan = json.loads(styles_json)
    assets = style_plan.get("assets", [])
except Exception as e:
    st.error(f"Styles JSON invalid: {e}")
    assets = []

st.markdown("---")
st.subheader("3) Generate Assets")
gen_col1, gen_col2 = st.columns([1,1])
go = gen_col1.button("Generate all assets")
note = gen_col2.checkbox("Use product image as reference (recommended)", value=True)

if go:
    if not product_img and note:
        st.warning("Upload a product image or uncheck the reference option.")
    else:
        results = []
        prog = st.progress(0)
        for idx, asset in enumerate(assets):
            prompt = build_prompt(asset, brand, product_name, tagline)
            ref_img = product_img if note else None
            try:
                out_img = gemini_generate_image(prompt, ref_img)
                results.append((asset["assetType"], out_img))
            except Exception as e:
                st.error(f"{asset.get('assetType','Asset')} failed: {e}")
            prog.progress(int((idx+1)/max(1,len(assets))*100))
        st.session_state["results"] = results

# ---------------------------
# Gallery + downloads
# ---------------------------
if "results" in st.session_state and st.session_state["results"]:
    st.markdown("### 4) Results")
    for asset_type, img in st.session_state["results"]:
        st.write(f"**{asset_type}**")
        st.image(img, use_column_width=True)
        fn = f"{asset_type.lower().replace(' ','_')}.png"
        st.download_button("Download PNG", data=save_pil_get_bytes(img), file_name=fn, mime="image/png")
        st.markdown("---")

st.caption("Powered by Gemini 2.5 Flash Image (Nano Banana). All outputs include invisible SynthID watermarks. 🪪")
