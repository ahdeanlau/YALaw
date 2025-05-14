# embeddings.py

import duckdb
import json
from openai import OpenAI
from config.config_env import OPENAI_API_KEY, QDRANT_API_KEY, QDRANT_CLIENT_URL
from typing import List, Dict
import pandas as pd
import os
from qdrant_client.http.models import PointStruct, VectorParams
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
import logging

# Configure logging at the top of the script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class OpenAIEmbedder:
    def __init__(self, model: str = "text-embedding-3-small"):
        # Initialize logger
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.logger.info("Initializing OpenAIEmbedder with model: %s", model)
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = model

    def _extract_texts_from_duckdb(self, duckdb_path: str, table_name: str) -> List[Dict]:
        self.logger.info("Extracting texts from DuckDB file: %s, table: %s", duckdb_path, table_name)
        query = f"SELECT id, payload FROM {table_name}"
        conn = duckdb.connect(duckdb_path)
        df = conn.execute(query).fetchdf()

        # Convert JSON strings in 'payload' column to dicts
        records = []
        for _, row in df.iterrows():
            payload = json.loads(row["payload"])
            records.append({
                "id": row["id"],
                "text": payload["chunk_text"],
                "payload": payload
            })
        self.logger.debug("Extracted %d records from DuckDB table: %s", len(records), table_name)
        return records

    def embed_text_chunks(self, duckdb_path: str ='chunks.duckdb', table_name: str = "raw_chunks") -> List[PointStruct]:
        self.logger.info("Embedding text chunks from DuckDB file: %s, table: %s", duckdb_path, table_name)
        records = self._extract_texts_from_duckdb(duckdb_path, table_name)
        texts = [record["text"] for record in records]

        self.logger.info("Generating embeddings for %d text chunks", len(texts))
        response = self.client.embeddings.create(
            input=texts,
            model=self.model
        )

        embeddings = [r.embedding for r in response.data]
        self.logger.debug("Generated embeddings for all text chunks")

        qdrant_points = []
        for record, vector in zip(records, embeddings):
            qdrant_points.append(
                PointStruct(
                    id=record["id"],
                    vector=vector,
                    payload=record["payload"]
                )
            )

        self.logger.info("Created %d Qdrant PointStruct objects", len(qdrant_points))
        return qdrant_points
    
    def upload_points_to_duckdb(self, qdrant_points: List[PointStruct], db_path: str = "embedded_points.duckdb"):
        self.logger.info("Uploading points to DuckDB file: %s", db_path)
        records = []
        for point in qdrant_points:
            records.append({
                "id": point.id,
                "vector": point.vector,
                "payload": json.dumps(point.payload)
            })

        df = pd.DataFrame(records)

        # Ensure the output directory exists
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

        # Save to DuckDB
        con = duckdb.connect(db_path)
        con.register("df", df)
        con.execute("""
            CREATE TABLE IF NOT EXISTS embedded_points AS SELECT * FROM df
        """)
        con.execute("""
            INSERT INTO embedded_points SELECT * FROM df
        """)
        self.logger.info("✅ Saved %d embedded points to DuckDB: %s", len(qdrant_points), db_path)
        con.close()

    def upload_points_to_qdrant(
        self,
        qdrant_points: List[PointStruct],
        collection_name: str,
        qdrant_host: str = QDRANT_CLIENT_URL  # use your actual URL here
    ):
        self.logger.info("Connecting to Qdrant at %s", qdrant_host)

        client = QdrantClient(
            url=QDRANT_CLIENT_URL,
            api_key=QDRANT_API_KEY
        )

        # Ensure collection exists (handle 404 if it doesn't)
        try:
            client.get_collection(collection_name)
            self.logger.info("Collection '%s' already exists.", collection_name)
        except UnexpectedResponse as e:
            if "404" in str(e):
                self.logger.info("Collection '%s' does not exist. Creating it.", collection_name)
                client.recreate_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=len(qdrant_points[0].vector),
                        distance="Cosine"
                    )
                )
            else:
                raise

        # Upload points
        client.upsert(
            collection_name=collection_name,
            points=qdrant_points
        )

        self.logger.info("✅ Uploaded %d points to collection '%s'.", len(qdrant_points), collection_name)

# Usage example
if __name__ == "__main__":
    embedder = OpenAIEmbedder()
    qdrant_points = embedder.embed_text_chunks("chunks.duckdb")

    # Store the points in a Parquet file
    embedder.upload_points_to_duckdb(qdrant_points, db_path="embedded_points.duckdb")
    embedder.upload_points_to_qdrant(qdrant_points, collection_name="embedded_collection")

    # Convert points to a DataFrame and store as csv
    points_df = pd.DataFrame(qdrant_points)
    points_df.to_csv("embedded_points.csv", index=False)
