import streamlit as st
from embeddings.embeddings import OpenAIEmbedder
from embeddings.pdfchunker import PDFChunker
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    force=True,  # ensures Streamlit doesn't interfere
)

# Streamlit app title and description
st.title("📄 PDF Chunking & Embedding with Qdrant")
st.markdown("Chunk PDFs, generate embeddings via OpenAI, store locally in DuckDB, and upload to Qdrant.")

# User input for PDF file
uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])

# Configuration inputs
raw_db_path = st.text_input("DuckDB path for raw chunks", "chunks.duckdb")
embedded_db_path = st.text_input("DuckDB path for embedded points", "embedded_points.duckdb")
collection_name = st.text_input("Qdrant collection name", "embedded_collection")
raw_table = st.text_input("DuckDB table name for raw chunks", "raw_chunks")

if st.button("🚀 Start Processing"):
    if uploaded_file:
        # Save uploaded PDF temporarily
        temp_pdf_path = os.path.join("temp_uploaded.pdf")
        with open(temp_pdf_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.info("📄 Chunking PDF...")
        chunker = PDFChunker()
        chunker.chunk_and_upload_to_duckdb(temp_pdf_path, db_path=raw_db_path, table_name=raw_table)
        st.success("✅ PDF chunked and stored locally.")

        st.info("🧠 Generating embeddings...")
        embedder = OpenAIEmbedder()
        qdrant_points = embedder.embed_text_chunks(duckdb_path=raw_db_path, table_name=raw_table)
        st.success(f"✅ Generated {len(qdrant_points)} embeddings.")

        st.info("💾 Saving embeddings to DuckDB...")
        embedder.upload_points_to_duckdb(qdrant_points, db_path=embedded_db_path)
        st.success("✅ Embeddings saved locally.")

        st.info("☁️ Uploading embeddings to Qdrant...")
        embedder.upload_points_to_qdrant(qdrant_points, collection_name=collection_name)
        st.success("✅ Uploaded embeddings to Qdrant.")

        # Clean up temp PDF
        os.remove(temp_pdf_path)

        st.balloons()
    else:
        st.error("Please upload a PDF file to start.")
