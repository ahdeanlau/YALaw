# embeddings.py

import duckdb
import json
from openai import OpenAI
from config.config_env import OPENAI_API_KEY
from typing import List, Dict
import pandas as pd
import os

class OpenAIEmbedder:
    def __init__(self, model: str = "text-embedding-3-small"):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = model

    def _extract_texts_from_parquet(self, parquet_path: str) -> List[Dict]:
        query = f"SELECT id, payload FROM '{parquet_path}'"
        df = duckdb.query(query).df()

        # Convert JSON strings in 'payload' column to dicts
        records = []
        for _, row in df.iterrows():
            payload = json.loads(row["payload"])
            records.append({
                "id": row["id"],
                "text": payload["chunk_text"],
                "payload": payload
            })
        return records

    def embed_text_chunks(self, parquet_path: str) -> List[Dict]:
        """Returns a list of Qdrant-compatible points with id, vector, payload."""
        records = self._extract_texts_from_parquet(parquet_path)
        texts = [record["text"] for record in records]

        # Embed with OpenAI (in batches of up to 2048 tokens total)
        response = self.client.embeddings.create(
            input=texts,
            model=self.model
        )

        embeddings = [r.embedding for r in response.data]

        qdrant_points = []
        for record, vector in zip(records, embeddings):
            qdrant_points.append({
                "id": record["id"],
                "vector": vector,
                "payload": record["payload"]
            })

        return qdrant_points
    
    def upload_points_to_duckdb(self, points: List[Dict], db_path: str = "embedded_points.duckdb"):
        # Convert points to DataFrame
        embedded_points_df = pd.DataFrame(points)

        # Ensure the output directory exists
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

        # Save to Parquet using DuckDB
        conn = duckdb.connect(db_path)
        conn.register("df", embedded_points_df)
        conn.execute(f"""
            COPY df TO '{db_path}'
            (FORMAT PARQUET, OVERWRITE TRUE)
        """)
        conn.close()

# Usage example
if __name__ == "__main__":
    embedder = OpenAIEmbedder()
    points = embedder.embed_text_chunks("raw_chunks.parquet")

    # Store the points in a Parquet file
    # Save to Parquet using DuckDB
    embedder.upload_points_to_duckdb(points, db_path="embedded_points.duckdb")

    # Convert points to a DataFrame and store as csv
    points_df = pd.DataFrame(points)
    points_df.to_csv("embedded_points.csv", index=False)
