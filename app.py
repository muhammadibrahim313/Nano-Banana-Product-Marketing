# Nano Banana – Product Marketing Assets (Product-Lock Edition)
# Streamlit app that:
# 1) Builds style JSON with Gemini (text)
# 2) Generates a BACKGROUND PLATE (no product)
# 3) Composites your actual product on top (so the model never alters it)
# 4) Lets you edit ONLY the background and re-composite
# 5) Adds deterministic overlay text (no placeholders).
#
# Notes:
# - Replaces deprecated use_column_width with use_container_width.
# - Fixes PIL rgba string bug by using RGBA tuples.

import os, io, json, base64
from typing import Optional, Tuple, List, Dict

import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from dotenv import load_dotenv
from google import genai

# --- Optional rembg for automatic cutout ---
try:
    from rembg import remove as rembg_remove
    REMBG_OK = True
except Exception:
    REMBG_OK = False

APP_NAME   = "🍌 Nano Banana – Product-Lock Assets"
IMAGE_MODEL= "gemini-2.5-flash-image-preview"
TEXT_MODEL = "gemini-2.5-flash"

# -------------------- Setup --------------------
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
st.set_page_config(page_title=APP_NAME, layout="wide")
st.title(APP_NAME)

if not API_KEY:
    st.error("Missing GEMINI_API_KEY in .env")
    st.stop()

client = genai.Client(api_key=API_KEY)

# -------------------- Helpers --------------------
def pil_from_upload(file) -> Image.Image:
    return Image.open(file).convert("RGBA")

def img_bytes(img: Image.Image, fmt="PNG") -> bytes:
    b = io.BytesIO()
    img.save(b, format=fmt)
    return b.getvalue()

def to_rgba_tuple(name: str) -> Tuple[int,int,int,int]:
    return (0,0,0,255) if name.lower()=="black" else (255,255,255,255)

def aspect_crop(img: Image.Image, target_ratio: Tuple[int,int]) -> Image.Image:
    w, h = img.size
    target = target_ratio[0]/target_ratio[1]
    cur = w/h
    if abs(cur-target) < 1e-6: return img.copy()
    if cur>target:  # too wide
        new_w = int(h*target)
        left = (w-new_w)//2
        return img.crop((left,0,left+new_w,h))
    else:
        new_h = int(w/target)
        top = (h-new_h)//2
        return img.crop((0,top,w,top+new_h))

def ensure_font(size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size=size)
    except Exception:
        return ImageFont.load_default()

def draw_overlay_text(
    base: Image.Image, quote: str, client_name: str, product_name: str,
    color_name: str="black", shadow=True,
    left_ratio=0.06, top_ratio=0.10, wrap_ratio=0.44
) -> Image.Image:
    """Deterministic overlay; avoids placeholders and PIL rgba string error."""
    img = base.copy().convert("RGBA")
    W,H = img.size
    x = int(W*left_ratio); y = int(H*top_ratio); max_w = int(W*wrap_ratio)
    draw = ImageDraw.Draw(img)
    col = to_rgba_tuple(color_name)

    def clean(s: str) -> str:
        return (s or "").replace("[","").replace("]","").strip()

    lines = []
    q = clean(quote)
    c = clean(client_name)
    p = clean(product_name)
    if q: lines.append(f"“{q}”")
    if c: lines.append(f"— {c}")
    if p: lines.append(p)
    if not lines: return img

    base_size = max(int(min(W,H)*0.04), 18)
    spacing = int(base_size*0.6)

    for text in lines:
        # shrink-to-fit
        fsize = base_size
        font  = ensure_font(fsize)
        while draw.textlength(text, font=font) > max_w and fsize>10:
            fsize -= 1; font = ensure_font(fsize)

        # naive wrap
        words = text.split(); line=""; wrapped=[]
        for w in words:
            test = (line+" "+w).strip()
            if draw.textlength(test, font=font) <= max_w: line = test
            else: wrapped.append(line); line = w
        if line: wrapped.append(line)

        for wline in wrapped:
            if shadow:
                # use RGBA tuple, not "rgba()" string
                draw.text((x+2,y+2), wline, font=font, fill=(0,0,0,64))
            draw.text((x,y), wline, font=font, fill=col)
            y += fsize + int(spacing*0.5)
        y += int(spacing*0.4)

    return img

def try_auto_cutout(img: Image.Image) -> Image.Image:
    """Return RGBA cutout (transparent BG). If rembg not available, return input."""
    if REMBG_OK:
        try:
            out = rembg_remove(img_bytes(img))
            return Image.open(io.BytesIO(out)).convert("RGBA")
        except Exception:
            pass
    # if image already has alpha with transparency, keep it
    if img.mode=="RGBA" and Image.eval(img.split()[-1], lambda a: 255-a).getbbox():
        return img
    return img  # fallback: no cutout

def add_shadow_layer(fore: Image.Image, blur=18, offset=(20,16), opacity=110) -> Image.Image:
    """Simple soft shadow from alpha mask."""
    alpha = fore.split()[-1]
    shadow = Image.new("RGBA", fore.size, (0,0,0,0))
    shadow_draw = Image.new("RGBA", fore.size, (0,0,0,0))
    shadow_draw.putalpha(alpha)
    shadow_draw = shadow_draw.filter(ImageFilter.GaussianBlur(blur))
    shadow.alpha_composite(shadow_draw, dest=offset)
    # reduce opacity
    r,g,b,a = shadow.split()
    a = a.point(lambda px: int(px*opacity/255))
    return Image.merge("RGBA",(r,g,b,a))

def composite_product_on_plate(plate: Image.Image, cutout: Image.Image, scale=0.55, y_bias=0.12) -> Image.Image:
    """Center the product at lower third, add soft shadow."""
    bg = plate.copy().convert("RGBA")
    W,H = bg.size
    # scale product
    pw,ph = cutout.size
    target_w = int(W*scale)
    s      = target_w/pw
    resized= cutout.resize((target_w, int(ph*s)), Image.LANCZOS)
    # position
    x = (W - resized.size[0])//2
    y = int(H*(1.0 - (0.5+ y_bias)))  # lower-ish
    # shadow then product
    sh = add_shadow_layer(resized, blur=24, offset=(18,18), opacity=120)
    bg.alpha_composite(sh, dest=(x,y))
    bg.alpha_composite(resized, dest=(x,y))
    return bg

def gemini_generate_image(prompt_text: str, ref_image: Optional[Image.Image]=None) -> Image.Image:
    """Generic call; returns first inline image."""
    contents = [prompt_text]
    if ref_image is not None: contents.append(ref_image)
    resp = client.models.generate_content(model=IMAGE_MODEL, contents=contents)
    for c in resp.candidates:
        for p in c.content.parts:
            if getattr(p,"inline_data",None) and getattr(p.inline_data,"data",None):
                data = p.inline_data.data
                if isinstance(data,str): data = base64.b64decode(data)
                return Image.open(io.BytesIO(data)).convert("RGBA")
    raise RuntimeError("No image returned")

def gemini_style_json(brand: Dict[str,str], product_name: str, category: str, benefit: str) -> Dict:
    sys = (
        "Return JSON ONLY: {\"assets\":[{"
        "\"assetType\":\"Instagram Post|Instagram Story|Website Banner|Ad Creative|Testimonial Graphic\","
        "\"backgroundTone\":\"...\",\"surfaceType\":\"...\",\"accentProp\":\"...\",\"lighting\":\"...\","
        "\"cameraAngle\":\"...\",\"overlayText\":\"...\"}]}. Vary fields per asset but keep cohesion."
    )
    user = (
        f"Product: {product_name}\nBrand: {brand['brandName']}\nTone: {brand['brandTone']}\n"
        f"Palette: {brand['colorTheme']}\nCategory: {category}\nBenefit: {benefit}\n"
        f"Placement: {brand['productPlacement']}\nComposition: {brand['compositionGuidelines']}\nJSON now."
    )
    r = client.models.generate_content(model=TEXT_MODEL, contents=[sys,user])
    txt = ""
    for c in r.candidates:
        for p in c.content.parts:
            if getattr(p,"text",None): txt += p.text
    txt = txt.strip().strip("`")
    if txt.startswith("json"): txt = txt[4:]
    try:
        return json.loads(txt)
    except Exception:
        return {
            "assets":[
                {"assetType":"Instagram Post","backgroundTone":"soft blush gradient","surfaceType":"satin draped cloth","accentProp":"gold-trimmed ribbon","lighting":"warm side spotlight","cameraAngle":"45-degree angle","overlayText":"Glow deeper. Shine brighter."},
                {"assetType":"Instagram Story","backgroundTone":"pale lavender","surfaceType":"ceramic tray","accentProp":"rose petals","lighting":"diffused top-down","cameraAngle":"overhead close-up","overlayText":"Hydration you can feel."},
                {"assetType":"Website Banner","backgroundTone":"muted green stone","surfaceType":"concrete slab","accentProp":"eucalyptus branch","lighting":"soft morning light","cameraAngle":"side-profile landscape","overlayText":"Glow like never before!"},
                {"assetType":"Ad Creative","backgroundTone":"deep emerald gradient","surfaceType":"reflective glass","accentProp":"crystal orb","lighting":"dramatic backlight","cameraAngle":"elevated 3/4","overlayText":"10% Off Today Only"},
                {"assetType":"Testimonial Graphic","backgroundTone":"cream linen","surfaceType":"polished marble","accentProp":"single white tulip","lighting":"natural side light","cameraAngle":"straight-on clean","overlayText":"My skin has never felt this good."}
            ]
        }

def build_background_prompt(asset: Dict, brand: Dict) -> str:
    # Ask for a BACKGROUND PLATE ONLY (no product, no jars/bottles/containers)
    ratio = "vertical 9:16" if asset["assetType"]=="Instagram Story" else ("16:9" if asset["assetType"]=="Website Banner" else "square 1:1")
    return (
        f"Create a {ratio} BACKGROUND PLATE for {asset['assetType']} with NO product, NO jars, NO bottles, "
        f"NO containers. Compose a premium minimal stage that matches:\n"
        f"- Background: {asset['backgroundTone']}\n"
        f"- Surface: {asset['surfaceType']}\n"
        f"- Accent prop: {asset['accentProp']} (subtle, non-dominant)\n"
        f"- Lighting: {asset['lighting']}\n"
        f"- Camera angle: {asset['cameraAngle']}\n\n"
        "Leave central area clean for a product to be placed later. Do not add any text. Return one image."
    )

def build_edit_plate_prompt(edit_text: str) -> str:
    return (
        "Edit this BACKGROUND PLATE image ONLY. " 
        "Do NOT add any product, jars, bottles, or text. "
        f"Apply ONLY this change: {edit_text}. Return one image."
    )

# -------------------- Sidebar: Stepper --------------------
with st.sidebar:
    st.header("① Upload & Brand")
    uploaded = st.file_uploader("Upload product image (PNG/JPG)", type=["png","jpg","jpeg"])
    product_img = pil_from_upload(uploaded) if uploaded else None
    cutout_opt = st.checkbox("Auto cut-out product (rembg)", value=True)
    cut_product = try_auto_cutout(product_img) if (product_img and cutout_opt) else product_img

    if product_img:
        st.image(product_img, caption="Product (original)", use_container_width=True)
        if cut_product and cut_product is not product_img:
            st.image(cut_product, caption="Product (cut-out)", use_container_width=True)

    default_brand = {
        "brandName":"Capsula",
        "brandTone":"Modern biotech luxury — innovative, pure, immersive.",
        "colorTheme":"Coral blush, teal turquoise, deep emerald, warm beige, onyx black.",
        "productPlacement":"Geometric pedestals or refined vanity; sparse organic props.",
        "compositionGuidelines":"Clean symmetry for single-product; off-center for lifestyle; generous negative space."
    }
    brand = {
        "brandName": st.text_input("Brand", default_brand["brandName"]),
        "brandTone": st.text_area("Tone", default_brand["brandTone"], height=70),
        "colorTheme": st.text_area("Palette", default_brand["colorTheme"], height=60),
        "productPlacement": st.text_area("Placement", default_brand["productPlacement"], height=60),
        "compositionGuidelines": st.text_area("Composition", default_brand["compositionGuidelines"], height=80),
    }

    st.markdown("---")
    st.header("② Quote / Overlay")
    quote        = st.text_area("Quote", "My skin has never felt this good—truly a game-changer!")
    client_name  = st.text_input("Attribution (optional)", "")
    product_name = st.text_input("Product name", "Capsula Serum X")
    overlay_col  = st.selectbox("Overlay color", ["black","white"])
    st.caption("Overlay is drawn by the app (no [Client Name] leaks).")

    st.markdown("---")
    st.header("③ Style JSON")
    if st.button("Suggest styles with Gemini"):
        st.session_state["styles"] = gemini_style_json(brand, product_name, "Skincare", "Hydration & barrier repair")
    if "styles" not in st.session_state: st.session_state["styles"] = {"assets":[]}
    styles_text = st.text_area("Edit styles JSON", json.dumps(st.session_state["styles"], indent=2), height=280)

    try:
        styles = json.loads(styles_text); assets = styles.get("assets", [])
    except Exception as e:
        st.error(f"Styles JSON invalid: {e}"); assets=[]

# -------------------- Main Tabs --------------------
t_generate, t_edit, t_export = st.tabs(["Generate", "Edit Backgrounds", "Export"])

# ---------- Generate ----------
with t_generate:
    st.subheader("Generate Background Plates + Composite Product")
    colA, colB = st.columns([1,1])
    strict_lock = colA.checkbox("Strict Product Lock (recommended)", value=True)
    go = colB.button("Generate all")

    if go:
        if product_img is None:
            st.warning("Upload a product image first.")
        else:
            st.session_state["results"] = []
            prog = st.progress(0)
            for i, asset in enumerate(assets):
                # 1) background plate
                plate_prompt = build_background_prompt(asset, brand)
                plate = gemini_generate_image(plate_prompt)

                # 2) composite product
                base = cut_product if cut_product is not None else product_img
                comp = composite_product_on_plate(plate, base)

                st.session_state["results"].append({
                    "asset": asset, "plate": plate, "composite": comp
                })
                prog.progress(int((i+1)/max(1,len(assets))*100))

    if "results" in st.session_state:
        for r in st.session_state["results"]:
            at = r["asset"]["assetType"]
            st.markdown(f"**{at}**")
            st.image(r["composite"], use_container_width=True)
            st.divider()

# ---------- Edit ----------
with t_edit:
    st.subheader("Edit Background ONLY, then Re-Composite")
    if "results" not in st.session_state or not st.session_state["results"]:
        st.info("Generate something first.")
    else:
        for idx, r in enumerate(st.session_state["results"]):
            asset = r["asset"]
            at = asset["assetType"]
            st.markdown(f"#### {at}")
            c1,c2,c3 = st.columns([3,2,2])
            with c1:
                st.image(r["composite"], caption="Current composite", use_container_width=True)
                st.image(r["plate"], caption="Current background plate", use_container_width=True)
            with c2:
                aspect = st.selectbox("Aspect", ["Keep","1:1","9:16","16:9"], key=f"asp_{idx}")
                base = r["composite"]
                if aspect=="1:1": base = aspect_crop(base,(1,1))
                elif aspect=="9:16": base = aspect_crop(base,(9,16))
                elif aspect=="16:9": base = aspect_crop(base,(16,9))

                add_overlay = st.checkbox("Add overlay text", value=(at=="Testimonial Graphic"), key=f"ol_{idx}")
                if add_overlay:
                    base = draw_overlay_text(base, quote, client_name, product_name, color_name=overlay_col)
                st.image(base, caption="Preview", use_container_width=True)
                st.session_state["results"][idx]["preview"] = base
            with c3:
                edit_txt = st.text_area("Background edit instruction",
                                        "Soften shadows slightly; keep palette cohesive.",
                                        key=f"ed_{idx}", height=100)
                if st.button(f"Apply background edit for {at}", key=f"btn_{idx}"):
                    try:
                        plate_edit_prompt = build_edit_plate_prompt(edit_txt)
                        new_plate = gemini_generate_image(plate_edit_prompt, ref_image=r["plate"])
                        # re-composite
                        base_prod = cut_product if cut_product is not None else product_img
                        new_comp = composite_product_on_plate(new_plate, base_prod)
                        st.session_state["results"][idx]["plate"] = new_plate
                        st.session_state["results"][idx]["composite"] = new_comp
                        st.session_state["results"][idx]["preview"] = new_comp
                        st.success("Edited background and re-composited.")
                    except Exception as e:
                        st.error(f"Edit failed: {e}")

# ---------- Export ----------
with t_export:
    st.subheader("Download Finals")
    if "results" not in st.session_state or not st.session_state["results"]:
        st.info("Generate first.")
    else:
        for idx, r in enumerate(st.session_state["results"]):
            at = r["asset"]["assetType"]
            final_img = r.get("preview", r["composite"])
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

st.caption("Built with Gemini 2.5 Flash Image (Nano Banana). Product-Lock pipeline: background plate → composited real product. Text overlays rendered locally. SynthID watermarks preserved in generated backgrounds.")
