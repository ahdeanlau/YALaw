from openai import OpenAI
from config.config_env import OPENAI_API_KEY
import os
from embeddings.pdfchunker import PDFChunker
from embeddings.embeddings import OpenAIEmbedder


def main():
    # ----------- Configurable inputs -----------
    pdf_path = "/Users/dlau/Documents/GitHub/YALaw/malaysia_penal_code.pdf"   # 📄 your input PDF
    raw_db_path = "chunks.duckdb"                    # 🟦 stores raw text chunks
    embedded_db_path = "embedded_points.duckdb"      # 🟨 stores embedded vectors
    collection_name = "embedded_collection"          # ☁️ Qdrant collection
    raw_table = "raw_chunks"                         # 🧱 table for raw text
    # -------------------------------------------

    # 1. Chunk the PDF and save chunks to DuckDB
    print("📄 Chunking PDF...")
    chunker = PDFChunker()
    chunker.chunk_and_upload_to_duckdb(pdf_path, db_path=raw_db_path, table_name=raw_table)

    # 2. Generate embeddings from text chunks
    print("🧠 Generating embeddings...")
    embedder = OpenAIEmbedder()
    qdrant_points = embedder.embed_text_chunks(duckdb_path=raw_db_path, table_name=raw_table)

    # 3. Save embedded vectors to another DuckDB
    print("💾 Saving embedded points to DuckDB...")
    embedder.upload_points_to_duckdb(qdrant_points, db_path=embedded_db_path)

    # 4. Upload embedded vectors to Qdrant Cloud
    print("☁️ Uploading to Qdrant...")
    embedder.upload_points_to_qdrant(qdrant_points, collection_name=collection_name)

    print("✅ Done.")

if __name__ == "__main__":
    main()
