import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader
import duckdb
import pandas as pd
import os

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

    def upload_chunks_to_duckdb(self, chunks: list[str], source_file: str, db_path: str = "chunks.duckdb"):
        import duckdb
        import pandas as pd

        df = pd.DataFrame({
            "chunk_id": range(len(chunks)),
            "chunk_text": chunks,
            "source_file": source_file
        })

        con = duckdb.connect(db_path)
        con.execute("""
            CREATE TABLE IF NOT EXISTS pdf_chunks (
                chunk_id INTEGER,
                chunk_text TEXT,
                source_file TEXT
            )
        """)
        con.execute("INSERT INTO pdf_chunks SELECT * FROM df")

        self.logger.info(f"✅ Uploaded {len(chunks)} chunks from {source_file} to {db_path}")

# Usage example
if __name__ == "__main__":
    pdf_processor = PDFChunker()
    chunks = pdf_processor.chunk_pdf("embeddings/malaysia_penal_code.pdf")

    with open("output_chunks.txt", "w", encoding="utf-8") as f:
        for idx, chunk in enumerate(chunks):
            pdf_processor.logger.debug(f"Writing chunk {idx + 1}/{len(chunks)} to file.")
            f.write(chunk + "\n-------------------------\n")
