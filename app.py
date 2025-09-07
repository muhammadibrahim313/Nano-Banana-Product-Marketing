import os, io, json, base64, textwrap
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass

import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
from google import genai

# ---------- Config ----------
APP_NAME = "Capsula Creative – Nano Banana Assets"
IMAGE_MODEL = "gemini-2.5-flash-image-preview"   # Nano Banana
TEXT_MODEL  = "gemini-2.5-flash"

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    st.error("Missing GEMINI_API_KEY in .env. Add it and restart.")
    st.stop()

client = genai.Client(api_key=API_KEY)
st.set_page_config(page_title=APP_NAME, layout="wide")
st.title("🍌 Nano Banana – Product Marketing Assets")

# ---------- Utilities ----------
def pil_from_upload(file) -> Image.Image:
    img = Image.open(file).convert("RGBA")
    return img

def img_bytes(img: Image.Image, fmt="PNG") -> bytes:
    b = io.BytesIO()
    img.save(b, format=fmt)
    return b.getvalue()

def aspect_crop(img: Image.Image, target_ratio: Tuple[int,int]) -> Image.Image:
    """Center-crop to the given w:h ratio (e.g., (1,1), (9,16), (16,9))."""
    w, h = img.size
    tr_w, tr_h = target_ratio
    target = tr_w / tr_h
    current = w / h

    if abs(current - target) < 1e-6:
        return img.copy()

    if current > target:
        # too wide → crop width
        new_w = int(h * target)
        left = (w - new_w) // 2
        box = (left, 0, left + new_w, h)
    else:
        # too tall → crop height
        new_h = int(w / target)
        top = (h - new_h) // 2
        box = (0, top, w, top + new_h)
    return img.crop(box)

def ensure_font(size: int) -> ImageFont.FreeTypeFont:
    # Prefer DejaVu (bundled often); fall back to default bitmap
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size=size)
    except Exception:
        return ImageFont.load_default()

def draw_overlay_text(
    base: Image.Image,
    quote: str,
    client_name: str,
    product_name: str,
    color: str = "black",
    shadow: bool = True,
    left_margin_ratio: float = 0.06,
    top_margin_ratio: float = 0.10,
    wrap_ratio: float = 0.44,
) -> Image.Image:
    """
    Deterministic overlay renderer so the model never writes text.
    - Sanitizes placeholders like [Client Name]
    - Smart quotes around the quote
    """
    img = base.copy().convert("RGBA")
    W, H = img.size
    draw = ImageDraw.Draw(img)

    # Sanitize
    def clean(s: str) -> str:
        s = (s or "").strip()
        # remove [] placeholders if user left them in
        s = s.replace("[", "").replace("]", "")
        return s

    quote = clean(quote)
    client_name = clean(client_name)
    product_name = clean(product_name)

    # Compose lines
    lines = []
    if quote:
        lines.append(f"“{quote}”")
    if client_name:
        lines.append(f"— {client_name}")
    if product_name:
        lines.append(product_name)

    if not lines:
        return img  # nothing to draw

    # Layout
    x = int(W * left_margin_ratio)
    y = int(H * top_margin_ratio)
    max_width = int(W * wrap_ratio)

    # Adaptive font sizing
    base_size = max(int(min(W, H) * 0.04), 18)  # scale with image
    font = ensure_font(base_size)

    def wrap_text(text, font, max_w):
        words = text.split()
        wrapped = []
        line = ""
        for w in words:
            test = f"{line} {w}".strip()
            if draw.textlength(test, font=font) <= max_w:
                line = test
            else:
                if line:
                    wrapped.append(line)
                line = w
        if line:
            wrapped.append(line)
        return wrapped

    # Draw lines with spacing
    line_spacing = int(base_size * 0.6)
    for idx, t in enumerate(lines):
        # shrink font if line is too wide
        fsize = base_size
        font = ensure_font(fsize)
        while draw.textlength(t, font=font) > max_width and fsize > 10:
            fsize -= 1
            font = ensure_font(fsize)

        wrapped = wrap_text(t, font, max_width)
        for wline in wrapped:
            # drop shadow for readability
            if shadow:
                draw.text((x+2, y+2), wline, font=font, fill="rgba(0,0,0,0.25)")
            draw.text((x, y), wline, font=font, fill=color)
            y += fsize + int(line_spacing * 0.5)
        y += int(line_spacing * 0.4)

    return img

def gemini_generate_image(prompt_text: str,
                          product_image: Optional[Image.Image] = None) -> Image.Image:
    """
    Image gen / edit via Nano Banana. We pass the reference product image
    so composition respects branding, but we tell the model NOT to add text.
    """
    contents: List = [prompt_text]
    if product_image is not None:
        contents.append(product_image)

    resp = client.models.generate_content(
        model=IMAGE_MODEL,
        contents=contents,
    )

    # Extract first inline image
    for cand in resp.candidates:
        for part in cand.content.parts:
            if getattr(part, "inline_data", None) and getattr(part.inline_data, "data", None):
                data = part.inline_data.data
                if isinstance(data, str):
                    data = base64.b64decode(data)
                return Image.open(io.BytesIO(data)).convert("RGBA")

    raise RuntimeError("No image returned by the model.")

def gemini_style_json(product_name: str, tagline: str, brand: Dict[str,str],
                      category: str, benefit: str) -> Dict:
    sys = (
        "You are a luxury product photographer/stylist. "
        "Return JSON ONLY (no prose). Shape: "
        "{\"assets\":[{\"assetType\":\"Instagram Post|Instagram Story|Website Banner|Ad Creative|Testimonial Graphic\","
        "\"backgroundTone\":\"...\",\"surfaceType\":\"...\",\"accentProp\":\"...\",\"lighting\":\"...\","
        "\"cameraAngle\":\"...\",\"overlayText\":\"...\"}]}. "
        "Vary each field by asset; keep campaign cohesion."
    )
    user = (
        f"Product: {product_name}\nTagline: {tagline}\n"
        f"Brand: {brand['brandName']}\nTone: {brand['brandTone']}\n"
        f"Palette: {brand['colorTheme']}\nCategory: {category}\nBenefit: {benefit}\n"
        f"Placement: {brand['productPlacement']}\n"
        f"Composition: {brand['compositionGuidelines']}\n"
        "Return JSON now."
    )

    resp = client.models.generate_content(model=TEXT_MODEL, contents=[sys, user])

    txt = ""
    for c in resp.candidates:
        for p in c.content.parts:
            if getattr(p, "text", None):
                txt += p.text
    txt = txt.strip().strip("`")
    if txt.startswith("json"):
        txt = txt[4:]
    try:
        return json.loads(txt)
    except Exception:
        # Safe default
        return {
            "assets":[
                {"assetType":"Instagram Post","backgroundTone":"soft blush gradient","surfaceType":"satin draped cloth",
                 "accentProp":"gold-trimmed ribbon","lighting":"warm side spotlight","cameraAngle":"45-degree angle",
                 "overlayText":"Glow deeper. Shine brighter."},
                {"assetType":"Instagram Story","backgroundTone":"pale lavender","surfaceType":"ceramic tray",
                 "accentProp":"rose petals","lighting":"diffused top-down","cameraAngle":"overhead close-up",
                 "overlayText":"Hydration you can feel."},
                {"assetType":"Website Banner","backgroundTone":"muted green stone","surfaceType":"concrete slab",
                 "accentProp":"eucalyptus branch","lighting":"soft morning light","cameraAngle":"side-profile landscape",
                 "overlayText":"Glow like never before!"},
                {"assetType":"Ad Creative","backgroundTone":"deep emerald gradient","surfaceType":"reflective glass",
                 "accentProp":"crystal orb","lighting":"dramatic backlight","cameraAngle":"elevated 3/4",
                 "overlayText":"10% Off Today Only"},
                {"assetType":"Testimonial Graphic","backgroundTone":"cream linen","surfaceType":"polished marble",
                 "accentProp":"single white tulip","lighting":"natural side light","cameraAngle":"straight-on clean",
                 "overlayText":"My skin has never felt this good."}
            ]
        }

def build_prompt(asset: Dict, brand: Dict, product_name: str) -> str:
    ar = "vertical 9:16" if asset["assetType"]=="Instagram Story" else ("16:9" if asset["assetType"]=="Website Banner" else "square 1:1")
    return (
        f"Create a {ar} photorealistic {asset['assetType']} for the skincare product {product_name} "
        f"from {brand['brandName']}. The product image is provided as reference; keep the product unchanged and legible. "
        "Do not add any text overlay. Compose a premium, minimal scene.\n\n"
        f"Background: {asset['backgroundTone']}. Surface: {asset['surfaceType']}. "
        f"Add a tasteful prop: {asset['accentProp']}. Lighting: {asset['lighting']}. "
        f"Camera angle: {asset['cameraAngle']}.\n\n"
        "Brand constraints:\n"
        f"- Tone: {brand['brandTone']}\n- Palette: {brand['colorTheme']}\n"
        f"- Placement: {brand['productPlacement']}\n- Composition: {brand['compositionGuidelines']}\n"
        "Return one high-quality image."
    )

# ---------- Sidebar (left-to-right flow) ----------
with st.sidebar:
    st.header("① Upload & Brand")
    uploaded = st.file_uploader("Upload product image (PNG/JPG)", type=["png","jpg","jpeg"])
    product_img = pil_from_upload(uploaded) if uploaded else None
    if product_img:
        st.image(product_img, caption="Product reference", use_container_width=True)

    st.markdown("---")
    default_brand = {
        "brandName":"Capsula",
        "brandTone":"Modern biotech luxury — innovative, pure, immersive.",
        "colorTheme":"Coral blush, teal turquoise, deep emerald, warm beige, onyx black.",
        "productPlacement":"Geometric pedestals or refined vanity; sparse organic props.",
        "compositionGuidelines":"Clean symmetry for single-product; off-center for lifestyle; generous negative space."
    }
    brand = {}
    brand["brandName"] = st.text_input("Brand name", default_brand["brandName"])
    brand["brandTone"] = st.text_area("Tone", default_brand["brandTone"], height=70)
    brand["colorTheme"] = st.text_area("Palette", default_brand["colorTheme"], height=60)
    brand["productPlacement"] = st.text_area("Placement rules", default_brand["productPlacement"], height=60)
    brand["compositionGuidelines"] = st.text_area("Composition", default_brand["compositionGuidelines"], height=80)

    st.markdown("---")
    st.header("② Quote & Labels (Overlay)")
    quote = st.text_area("Quote (no placeholders)", "My skin has never felt this good—truly a game-changer!")
    client_name = st.text_input("Attribution (optional)", "")
    product_name = st.text_input("Product name", "Capsula Serum X")
    overlay_color = st.selectbox("Overlay color", ["black","white"])
    st.caption("Overlay text is rendered by the app (not by the model), so no [Client Name] leaks.")

    st.markdown("---")
    st.header("③ Style JSON")
    if st.button("Suggest styles with Gemini"):
        st.session_state["styles"] = gemini_style_json(product_name, "", brand, "Skincare", "Hydration & barrier repair")

    if "styles" not in st.session_state:
        st.session_state["styles"] = {"assets":[]}
    styles_text = st.text_area("Edit styles JSON", json.dumps(st.session_state["styles"], indent=2), height=280)

    try:
        styles = json.loads(styles_text)
        assets = styles.get("assets", [])
    except Exception as e:
        st.error(f"Styles JSON invalid: {e}")
        assets = []

# ---------- Main content ----------
tabs = st.tabs(["Generate", "Edit & Overlay", "Export"])
with tabs[0]:
    st.subheader("Generate Assets")
    colA, colB = st.columns([1,1])
    with colA:
        use_ref = st.checkbox("Use uploaded product as reference", value=True)
    with colB:
        start = st.button("Generate all")

    if start:
        if use_ref and product_img is None:
            st.warning("Upload a product image or uncheck 'Use as reference'.")
        else:
            st.session_state["results"] = []
            prog = st.progress(0)
            for i, asset in enumerate(assets):
                prompt = build_prompt(asset, brand, product_name)
                try:
                    out = gemini_generate_image(prompt, product_img if use_ref else None)
                    st.session_state["results"].append({"asset": asset, "image": out})
                except Exception as e:
                    st.error(f"{asset.get('assetType','Asset')} failed: {e}")
                prog.progress(int((i+1)/max(1,len(assets))*100))

    if "results" in st.session_state:
        st.write("")
        for r in st.session_state["results"]:
            at = r["asset"]["assetType"]
            st.markdown(f"**{at}**")
            st.image(r["image"], use_container_width=True)
            st.divider()

with tabs[1]:
    st.subheader("Per-asset Editing & Overlay")
    if "results" not in st.session_state or not st.session_state["results"]:
        st.info("Generate something first on the 'Generate' tab.")
    else:
        for idx, r in enumerate(st.session_state["results"]):
            asset = r["asset"]
            atype = asset["assetType"]
            st.markdown(f"#### {atype}")

            c1, c2, c3 = st.columns([3,2,2])
            with c1:
                st.image(r["image"], use_container_width=True)

            with c2:
                st.write("Aspect preset")
                aspect_opt = st.selectbox(
                    f"Aspect · {atype}",
                    ["Keep", "1:1 (Post/Testimonial)", "9:16 (Story)", "16:9 (Banner)"],
                    key=f"aspect_{idx}"
                )

                # apply crop
                base = r["image"]
                if aspect_opt == "1:1 (Post/Testimonial)":
                    base = aspect_crop(base, (1,1))
                elif aspect_opt == "9:16 (Story)":
                    base = aspect_crop(base, (9,16))
                elif aspect_opt == "16:9 (Banner)":
                    base = aspect_crop(base, (16,9))

                st.write("Overlay")
                with_overlay = st.checkbox("Add quote overlay", value=(atype=="Testimonial Graphic"), key=f"ol_{idx}")
                if with_overlay:
                    preview = draw_overlay_text(
                        base, quote=quote, client_name=client_name,
                        product_name=product_name, color=overlay_color
                    )
                else:
                    preview = base

                st.image(preview, caption="Preview", use_container_width=True)
                st.session_state["results"][idx]["preview"] = preview

            with c3:
                st.write("Targeted edit")
                edit_txt = st.text_area(
                    f"Edit instruction ({atype})",
                    "Only soften shadows; preserve product label, background, and composition.",
                    height=100, key=f"edit_{idx}"
                )
                if st.button(f"Apply edit to {atype}", key=f"apply_{idx}"):
                    try:
                        edited = gemini_generate_image(
                            f"{edit_txt} Do not add any text. Return one image.",
                            product_image=base
                        )
                        # reapply overlay if chosen
                        if with_overlay:
                            edited = draw_overlay_text(
                                aspect_crop(edited, (1,1)) if aspect_opt.startswith("1:1") else edited,
                                quote=quote, client_name=client_name, product_name=product_name, color=overlay_color
                            )
                        st.session_state["results"][idx]["preview"] = edited
                        st.success("Edit applied.")
                    except Exception as e:
                        st.error(f"Edit failed: {e}")

with tabs[2]:
    st.subheader("Export")
    if "results" not in st.session_state or not st.session_state["results"]:
        st.info("Generate first.")
    else:
        for idx, r in enumerate(st.session_state["results"]):
            at = r["asset"]["assetType"]
            final_img = r.get("preview", r["image"])
            st.markdown(f"**{at}**")
            st.image(final_img, use_container_width=True)
            st.download_button(
                "Download PNG",
                data=img_bytes(final_img),
                file_name=f"{at.lower().replace(' ','_')}.png",
                mime="image/png",
                key=f"dl_{idx}"
            )
            st.divider()

st.caption("Built with Gemini 2.5 Flash Image (Nano Banana). Outputs include invisible SynthID watermarks.")
