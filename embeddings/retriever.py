import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from typing import List, Dict, Any
from qdrant_client.models import QueryResponse
from qdrant_client import QdrantClient
from langchain_openai import OpenAIEmbeddings
from config.config_env import QDRANT_API_KEY, QDRANT_CLIENT_URL, OPENAI_API_KEY


class QdrantQueryRetriever:
    """
    A retriever class for performing semantic similarity search using OpenAI embeddings and Qdrant vector store.

    This class:
      - Converts a natural language query into a dense vector using OpenAI's embedding model.
      - Queries the specified Qdrant collection to retrieve the most similar vectors/documents.

    Attributes:
        collection_name (str): The name of the Qdrant collection to search in.
        client (QdrantClient): Instance of Qdrant client for querying the vector store.
        embeddings (OpenAIEmbeddings): OpenAI embedding model used to convert text queries to vectors.
    """

    def __init__(
        self,
        *,
        collection_name: str,
        qdrant_url: str | None = QDRANT_CLIENT_URL,
        qdrant_api_key: str | None = QDRANT_API_KEY,
        openai_api_key: str | None = OPENAI_API_KEY,
        embedding_model: str = "text-embedding-3-small",
    ) -> None:
        """
        Initializes the QdrantQueryRetriever with necessary configurations.

        Args:
            collection_name (str): Name of the Qdrant collection to be queried.
            qdrant_url (str, optional): URL of the Qdrant instance.
            qdrant_api_key (str, optional): API key for authenticating with Qdrant.
            openai_api_key (str, optional): API key for accessing OpenAI's embedding model.
            embedding_model (str, optional): Identifier of the OpenAI embedding model to use.
        """
        
        self.collection_name = collection_name
        
        self.client = QdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key,
        )

        self.embeddings = OpenAIEmbeddings(
            model=embedding_model,
            openai_api_key=openai_api_key,
        )

    def embed_query(self, query: str) -> List[float]:
        """
        Returns the raw embedding vector.
        """
        return self.embeddings.embed_query(query)
    
    def similarity_search_by_query_with_dense_vector(
        self,
        query: str,
        limit: int = 10,
    ) -> QueryResponse:
        """
        Performs a similarity search in Qdrant using the query's embedding vector.

        Args:
            query (str): Natural language query to embed and search with.
            limit (int, optional): Number of top similar results to retrieve. Defaults to 10.

        Returns:
            QueryResponse: Qdrant response containing the matched vectors/documents.
            QueryResponse.points: List of points (documents) that match the query.
        """
        dense_vector = self.embed_query(query)
        return self.client.query_points(self.collection_name, dense_vector, limit=limit)


# --------------------------- Example usage ------------------------------- #

if __name__ == "__main__":
    retriever = QdrantQueryRetriever(
        collection_name="commonlii_cases",
        qdrant_url=QDRANT_CLIENT_URL,
        qdrant_api_key=QDRANT_API_KEY,
        openai_api_key=OPENAI_API_KEY,
        embedding_model="text-embedding-3-small",
    )

    QUERY = "Legal cases about property law in Sarawak"
    
    try:
        result = retriever.similarity_search_by_query_with_dense_vector(QUERY)
    except Exception as e:
        print(f"Query failed: {e}")

    print("result:", result.points)
    print("Type: ", type(result.points))
