import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader
import duckdb
import pandas as pd
import os
import json

class PDFChunker:
    def __init__(self, chunk_size: int = 3000, chunk_overlap: int = 600, separators: list[str] = None):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["CHAPTER","\n \n", "\n", ".", " ", ""]

        # Configure logger
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def chunk_pdf(self, pdf_path: str) -> list[str]:
        try:
            self.logger.info(f"Starting PDF chunking for: {pdf_path}")

            # Load PDF
            self.logger.info("Initializing PyMuPDFLoader.")
            loader = PyMuPDFLoader(pdf_path)
            documents = loader.load()
            self.logger.info(f"Loaded {len(documents)} pages from PDF.")

            # Combine all pages/documents into ONE single string
            combined_document = "\n\n".join(doc.page_content for doc in documents)
            self.logger.debug(f"First 500 characters of combined document: {combined_document[:500]}")

            # Write combined document only when running this file directly
            if __name__ == "__main__":
                with open("output_combined_document.txt", "w", encoding="utf-8") as f:
                    f.write(combined_document.encode('unicode_escape').decode('utf-8'))

            # Split into chunks
            self.logger.info(f"Initializing text splitter with chunk size {self.chunk_size} and overlap {self.chunk_overlap}.")
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=self.separators
            )

            chunks = text_splitter.split_text(combined_document)
            self.logger.info(f"Split the document into {len(chunks)} chunks.")
            self.logger.debug(f"First chunk preview: {chunks[0][:300]}")

            return chunks

        except Exception as e:
            self.logger.error("An error occurred during processing.", exc_info=True)

    def upload_raw_chunks_to_duckdb(
        self,
        chunks: list[str],
        source_file: str,
        db_path: str = "chunks.duckdb",
        table_name: str = "raw_chunks"
    ):
        # Remove the existing DuckDB file if it exists
        if os.path.exists(db_path):
            os.remove(db_path)
            self.logger.info(f"Deleted existing DuckDB file: {db_path}")

        # Prepare records: just id + payload (no vector yet)
        records = []
        for i, chunk in enumerate(chunks):
            records.append({
                "id": i,
                "payload": json.dumps({
                    "chunk_text": chunk,
                    "source_file": source_file
                })
            })

        df = pd.DataFrame(records)

        # Ensure the output directory exists
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

        # Save to DuckDB (new file)
        con = duckdb.connect(db_path)
        con.register("df", df)
        con.execute(f"""
            CREATE TABLE {table_name} AS SELECT * FROM df
        """)

        self.logger.info(f"✅ Saved {len(chunks)} raw chunks to DuckDB table '{table_name}': {db_path}")
        con.close()
        self.logger.info("Closed DuckDB connection.")

    def chunk_and_upload_to_duckdb(
        self,
        pdf_path: str,
        db_path: str = "chunks.duckdb",
        table_name: str = "raw_chunks"
    ):
        chunks = self.chunk_pdf(pdf_path)
        if chunks:
            self.upload_raw_chunks_to_duckdb(
                chunks=chunks,
                source_file=pdf_path,
                db_path=db_path,
                table_name=table_name
            )
        else:
            self.logger.warning("No chunks returned from chunk_pdf; skipping upload.")

# Usage example
if __name__ == "__main__":
    pdf_processor = PDFChunker()
    chunks = pdf_processor.chunk_and_upload_to_duckdb("embeddings/malaysia_penal_code.pdf")

    pd.set_option('display.max_columns', None)  # Show all columns
    pd.set_option('display.max_rows', None)     # Show all rows
    pd.set_option('display.max_colwidth', None) # Show full column content
    con = duckdb.connect("chunks.duckdb")
    df = con.execute("SELECT * FROM raw_chunks").df()
    print(df)
