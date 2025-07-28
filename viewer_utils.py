import streamlit as st
from PIL import ImageDraw

def render_pdf_with_highlights(pages, word_json, queries):
    queries_lower = [q.lower() for q in queries]

    for i, page in enumerate(pages):
        draw = ImageDraw.Draw(page)

        for word_obj in word_json.get(str(i), []):
            word_text = word_obj["text"].lower()
            if any(q in word_text for q in queries_lower):
                draw.rectangle(word_obj["bbox"], outline="red", width=2)

        st.image(page, caption=f"Page {i+1}", width=800)