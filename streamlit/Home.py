import streamlit as st
from pathlib import Path

# -----------------------------------------------------------------------------
# CONFIG
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="YA Legal Toolkit",
    page_icon="⚖️",
    layout="wide",
)

# -----------------------------------------------------------------------------
# CUSTOM CSS  – quick, soft neumorphic cards & hover glow
# -----------------------------------------------------------------------------

st.markdown(
    """
    <style>
    .feature-card {
        background: #ffffff;
        border-radius: 1rem;
        padding: 2rem 1.5rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.07);
        transition: all 0.25s ease;
        height: 100%;
        position: relative;
    }
    .feature-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 24px rgba(0,0,0,0.12);
    }
    .card-btn {
        width: 100%;
        font-weight: 600;
        padding: 0.6rem 0;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
    }
    .card-footer {
        position: absolute;
        bottom: 1.5rem;
        left: 1.5rem;
        right: 1.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# HEADER
# -----------------------------------------------------------------------------

st.markdown("## ⚖️ **YA Legal Toolkit** – Home")

st.write(
    "Welcome! Choose one of the features below to get started. Each tool is "
    "designed to make your legal workflow faster and more client‑friendly."
)

st.divider()

# -----------------------------------------------------------------------------
# FEATURES DATA
# -----------------------------------------------------------------------------

features = [
    {
        "name": "YALeDoc",
        "emoji": "📝",
        "description": "Generate, edit & customise legal documents with smart templates.",
        "page": "pages/YALeDoc.py",
    },
    {
        "name": "YaLeT",
        "emoji": "📚",
        "description": "Translate text ↔️ legal jargon / plain language in multiple languages.",
        "page": "pages/YaLeT.py",
    },
    {
        "name": "YASimCase",
        "emoji": "🔍",
        "description": "Search & compare similar cases with quick summaries.",
        "page": "pages/YASimCase.py",
    },
    {
        "name": "YAEat",
        "emoji": "🥗",
        "description": "Your AI‑powered lunchtime recommender for the busy lawyer!",
        "page": "pages/YAEat.py",
    },
]

# -----------------------------------------------------------------------------
# GRID / CARDS
# -----------------------------------------------------------------------------

cols = st.columns(4, gap="large")

for col, feature in zip(cols, features):
    with col:
        st.markdown(
            f"""
            <div class="feature-card">
                <h2 style='margin-top:0;'>{feature['emoji']} {feature['name']}</h2>
                <p>{feature['description']}</p>
                <div class='card-footer'>
                    <a href="/{Path(feature['page']).stem}" class="card-btn stButton" target="_self">Open →</a>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# -----------------------------------------------------------------------------
# FOOTER (optional)
# -----------------------------------------------------------------------------

st.divider()

st.caption("© 2025 YA Legal Solutions – All rights reserved.")
