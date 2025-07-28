# -------- app.py --------
import streamlit as st
import fitz  # PyMuPDF
import easyocr
from PIL import Image, ImageDraw
import numpy as np
import json
import os

# 📁 Output folder
os.makedirs("output", exist_ok=True)

st.set_page_config(layout="wide")
st.title("📄 Word-Level Coordinate Highlighter (EasyOCR + PyMuPDF)")

# 📤 File uploader
uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")

# 🧠 EasyOCR reader (cached safely)
@st.cache_resource
def get_reader():
    return easyocr.Reader(['en'], gpu=False, verbose=False, quantize=True)

# ✅ Load PDF bytes only (not fitz.Document)
@st.cache_data
def load_pdf_bytes(file):
    return file.read()

# 💾 Save output to JSON file
def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# 🧪 OCR Process and coordinate extraction
def process_pdf(doc, max_pages, reader):
    layout_json = {}
    word_json = {}

    for i, page in enumerate(doc):
        if i >= max_pages:
            break

        pix = page.get_pixmap(matrix=fitz.Matrix(1, 1))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        np_img = np.array(img)

        results = reader.readtext(np_img, detail=1, paragraph=False, batch_size=16)
        width, height = img.size

        layout_json[str(i)] = {
            "image_name": f"page-{i}.jpg",
            "width": width,
            "height": height,
            "sections": []
        }

        word_json[str(i)] = []

        for (bbox, text, conf) in results:
            if text.strip() == "" or conf < 0.4:
                continue

            x_min = int(min(pt[0] for pt in bbox))
            y_min = int(min(pt[1] for pt in bbox))
            x_max = int(max(pt[0] for pt in bbox))
            y_max = int(max(pt[1] for pt in bbox))

            word_json[str(i)].append({
                "text": text,
                "bbox": [x_min, y_min, x_max, y_max]
            })

        all_text = " ".join([w["text"] for w in word_json[str(i)]])
        layout_json[str(i)]["sections"].append({
            "bbox": [0, 0, 1, 1],
            "class": "FullPage",
            "score": 1.0,
            "text": all_text
        })

    return layout_json, word_json

# 🔦 Draw highlights for matching keywords
def render_with_highlights(pages, word_json, queries):
    for i, page in enumerate(pages):
        if str(i) not in word_json:
            continue

        pix = page.get_pixmap(matrix=fitz.Matrix(1, 1))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        draw = ImageDraw.Draw(img)

        for word_obj in word_json[str(i)]:
            word_text = word_obj["text"].lower()
            if any(q.lower() in word_text for q in queries):
                x1, y1, x2, y2 = word_obj["bbox"]
                draw.rectangle([x1, y1, x2, y2], outline="red", width=2)

        st.image(img, caption=f"Page {i+1}", width=800)

# ----------------- Streamlit Flow --------------------
if uploaded_file:
    with st.form("pdf_form"):
        max_pages = st.number_input("📄 Number of pages to process", min_value=1, value=5)
        submitted = st.form_submit_button("Process PDF")

    if submitted:
        with st.spinner("⚙️ Processing... please wait..."):
            reader = get_reader()
            pdf_bytes = load_pdf_bytes(uploaded_file)
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")  # ⚠️ Not cached
            layout_json, word_json = process_pdf(doc, max_pages, reader)
            save_json(layout_json, "output/layout.json")
            save_json(word_json, "output/wordjson.json")
        st.success("✅ Processing complete! JSON files saved to `output/` folder.")

        st.markdown("### 🔍 Search up to 5 Keywords")
        queries = []
        for i in range(5):
            word = st.text_input(f"Keyword {i+1}", key=f"query_{i}")
            if word:
                queries.append(word)

        st.markdown("---")
        if queries:
            st.markdown("### 🔦 Highlighted Results")
            render_with_highlights(doc, word_json, queries)
        else:
            pix = doc[0].get_pixmap(matrix=fitz.Matrix(1, 1))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            st.image(img, caption="Page 1", width=800)
