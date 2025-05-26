# This page is for the feature to Translate to legal jargons

# There are two main tabs: 1. Translate to legal jargons, 2. Translate to normal/understandable language for clients

## Tab 1: Translate to legal jargons
# Input the the sentence, user want to translate to with legal jargons

# Specify the language to translate to (English or Malay)

# Press the button "Translate"
# Allow the user to download the translated sentence as a word or PDF document.


## Tab 2: Translate to normal/understandable language for clients.
# Input the the sentence, user want to translate from legal jargons, so that the translation is understandable to clients and doesn't lose the important legal concepts.

# Specify the language to translate to (English or Malay or Chinese or Tamil)

# Press the button "Translate"

# Display the translated sentence
# Allow the user to download the translated sentence as a word or PDF document.

import streamlit as st
import io
from typing import List

try:
    from docx import Document  # python-docx
except ImportError:
    Document = None

try:
    from reportlab.pdfgen import canvas  # reportlab
except ImportError:
    canvas = None

# -----------------------------------------------------------------------------
# Mock backend translators – replace with your real service calls
# -----------------------------------------------------------------------------

def mock_translate_to_legal(text: str, target_lang: str) -> str:
    """Pretend we translate to formal legal jargon."""
    return f"[{target_lang}] LEGAL → {text} (in sophisticated legal terms)"


def mock_translate_to_plain(text: str, target_lang: str) -> str:
    """Pretend we translate to plain client‑friendly language."""
    return f"[{target_lang}] PLAIN → {text} (explained in layman language)"

# -----------------------------------------------------------------------------
# Utility functions to generate download files
# -----------------------------------------------------------------------------

def create_docx(text: str) -> io.BytesIO:
    buffer = io.BytesIO()
    if Document is None:
        buffer.write(text.encode("utf-8"))  # fallback plain‑text
    else:
        doc = Document()
        doc.add_paragraph(text)
        doc.save(buffer)
    buffer.seek(0)
    return buffer


def create_pdf(text: str) -> io.BytesIO:
    buffer = io.BytesIO()
    if canvas is None:
        buffer.write(text.encode("utf-8"))  # fallback plain‑text
    else:
        pdf = canvas.Canvas(buffer)
        width, height = pdf._pagesize
        pdf.drawString(72, height - 100, text)
        pdf.showPage()
        pdf.save()
    buffer.seek(0)
    return buffer

# -----------------------------------------------------------------------------
# Page config & custom CSS
# -----------------------------------------------------------------------------

st.set_page_config(page_title="Legal Translator", layout="centered")

st.markdown(
    """
    <style>
    /* Narrow the form and add soft card look */
    .stTabs [data-baseweb="tab"] {
        font-size: 1.05rem;
        padding: 0.75rem 1.25rem;
    }
    .translation-output {
        background: #f8f9fa;
        border-radius: 0.5rem;
        padding: 1rem;
        font-size: 1.1rem;
        border: 1px solid #dee2e6;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📜 Legal Text Translator")

# -----------------------------------------------------------------------------
# Tabs layout
# -----------------------------------------------------------------------------

tab1, tab2 = st.tabs([
    "Translate ➜ Legal Jargon",
    "Translate ➜ Plain Language",
])

# -----------------------------------------------------------------------------
# Tab 1 – To Legal Jargon
# -----------------------------------------------------------------------------

with tab1:
    st.subheader("Convert everyday wording into formal legal prose")

    source_text = st.text_area(
        "Sentence / paragraph to translate", height=150, key="legal_input"
    )
    target_lang = st.selectbox("Target language", ["English", "Malay"], key="legal_lang")

    col_translate, col_spacer = st.columns([1, 3])
    with col_translate:
        if st.button("🔁 Translate", key="legal_go"):
            st.session_state["legal_result"] = mock_translate_to_legal(source_text, target_lang)

    result = st.session_state.get("legal_result", "")
    if result:
        st.markdown("### Translation")
        st.markdown(f"<div class='translation-output'>{result}</div>", unsafe_allow_html=True)

        # -------------------- Downloads ------------------------------
        docx_data = create_docx(result)
        pdf_data = create_pdf(result)
        dl1, dl2 = st.columns(2)
        with dl1:
            st.download_button(
                label="💾 Download DOCX",
                data=docx_data,
                file_name="translation_legal.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="legal_docx",
            )
        with dl2:
            st.download_button(
                label="💾 Download PDF",
                data=pdf_data,
                file_name="translation_legal.pdf",
                mime="application/pdf",
                key="legal_pdf",
            )

# -----------------------------------------------------------------------------
# Tab 2 – To Plain Language
# -----------------------------------------------------------------------------

with tab2:
    st.subheader("Demystify legal jargon for clients without losing meaning")

    source_text2 = st.text_area(
        "Legal sentence / paragraph to simplify", height=150, key="plain_input"
    )
    target_lang2 = st.selectbox(
        "Target language",
        ["English", "Malay", "Chinese", "Tamil"],
        key="plain_lang",
    )

    if st.button("🔁 Translate", key="plain_go"):
        st.session_state["plain_result"] = mock_translate_to_plain(source_text2, target_lang2)

    result2 = st.session_state.get("plain_result", "")
    if result2:
        st.markdown("### Translation")
        st.markdown(f"<div class='translation-output'>{result2}</div>", unsafe_allow_html=True)

        docx_data2 = create_docx(result2)
        pdf_data2 = create_pdf(result2)
        dl3, dl4 = st.columns(2)
        with dl3:
            st.download_button(
                label="💾 Download DOCX",
                data=docx_data2,
                file_name="translation_plain.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="plain_docx",
            )
        with dl4:
            st.download_button(
                label="💾 Download PDF",
                data=pdf_data2,
                file_name="translation_plain.pdf",
                mime="application/pdf",
                key="plain_pdf",
            )
