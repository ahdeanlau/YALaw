from typing import List, Dict, Any
from qdrant_client import QdrantClient, models
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document
from config.config_env import QDRANT_API_KEY, QDRANT_CLIENT_URL, OPENAI_API_KEY


class QdrantQueryRetriever:
    """
    Minimal helper around LangChain's QdrantVectorStore to:
      • embed an input query               (OpenAIEmbeddings)
      • search the configured collection   (Qdrant HNSW)
    """

    def __init__(
        self,
        *,
        collection_name: str,
        qdrant_url: str | None = QDRANT_CLIENT_URL,
        qdrant_api_key: str | None = QDRANT_API_KEY,
        openai_api_key: str | None = OPENAI_API_KEY,
        embedding_model: str = "text-embedding-3-small",
        embeddings_batch_size: int = 96,
    ) -> None:
        # 1) Connect to Qdrant
        self.client = QdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key,
        )

        # 2) Build (or reconnect to) the VectorStore
        self.embeddings = OpenAIEmbeddings(
            model=embedding_model,
            openai_api_key=openai_api_key,
        )

        self.vstore = QdrantVectorStore(
            client=self.client,
            collection_name=collection_name,
            embedding=self.embeddings,
            content_payload_key="chunk_text",
        )

    # --------------------------------------------------------------------- #
    # Public helpers
    # --------------------------------------------------------------------- #

    def embed_query(self, query: str) -> List[float]:
        """
        Returns the raw embedding vector.
        """
        return self.embeddings.embed_query(query)

    def similarity_search(
        self,
        query: str,
        *,
        k: int = 8,
        score_threshold: float | None = None,
        metadata_filter: Dict[str, Any] | None = None,
    ) -> List[Document]:
        """
        Pull the top-k matching documents for `query`.

        Args
        ----
        query            The natural-language question.
        k                How many documents to return (default 8).
        score_threshold  Optional minimum similarity to accept.
        metadata_filter  Optional Qdrant payload filter
                         (same structure as qdrant-client's `models.Filter`).

        Returns
        -------
        List[Document]   LangChain Document objects with .page_content & .metadata
        """
        search_kwargs: Dict[str, Any] = {"k": k}
        if score_threshold is not None:
            search_kwargs["score_threshold"] = score_threshold
        if metadata_filter is not None:
            search_kwargs["filter"] = models.Filter(**metadata_filter)

        return self.vstore.similarity_search(query, **search_kwargs)

    # Convenience wrapper that gives (doc, score) tuples
    def similarity_search_with_scores(
        self,
        query: str,
        *,
        k: int = 8,
        metadata_filter: Dict[str, Any] | None = None,
    ) -> List[tuple[Document, float]]:
        return self.vstore.similarity_search_with_relevance_scores(
            query=query,
            k=k,
            filter=models.Filter(**metadata_filter) if metadata_filter else None,
        )


# --------------------------- Example usage ------------------------------- #

if __name__ == "__main__":
    retriever = QdrantQueryRetriever(
        collection_name="embedded_collection",
        qdrant_url=QDRANT_CLIENT_URL,
        qdrant_api_key=QDRANT_API_KEY,
        openai_api_key=OPENAI_API_KEY,
        embedding_model="text-embedding-3-small",
    )

    query = "What if the contract contains unfair terms?"
    docs = retriever.similarity_search(query, k=5)

    
    
    print("\nTop matches:\n" + "-" * 40)
    for i, doc in enumerate(docs, 1):
        print(f"[{i}] Chunk {doc.metadata.get('_id', 'unknown')}:")
        print(doc.page_content + " …\n")
