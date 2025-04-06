import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader

class PDFChunker:
    def __init__(self, pdf_path: str, chunk_size: int = 5000, chunk_overlap: int = 1000):
        self.pdf_path = pdf_path
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Configure logger
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def chunk_pdf(self, output_file: str):
        try:
            # Load PDF
            loader = PyMuPDFLoader(self.pdf_path)
            documents = loader.load()
            combined_document = "\n\n".join(doc.page_content for doc in documents)
            
            self.logger.info(f"Loaded {len(documents)} pages from PDF.")
            
            # Split into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=["\n\n", "\n", ".", " ", ""]
            )

            chunks = text_splitter.split_text(combined_document)
            self.logger.info(f"Split the document into {len(chunks)} chunks.")

            with open(output_file, "w", encoding="utf-8") as f:
                for chunk in chunks:
                    f.write(chunk + "\n-------------------------\n")

        except Exception as e:
            self.logger.error("An error occurred during processing.", exc_info=True)


# Usage example
if __name__ == "__main__":
    pdf_processor = PDFChunker("embeddings/malaysia_penal_code.pdf")
    pdf_processor.chunk_pdf("output_chunks.txt")