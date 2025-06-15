import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import duckdb
import json
from qdrant_client.http.models import PointStruct
from typing import List
from embeddings.embeddings import OpenAIEmbedder  # Replace with your actual class

### CONFIGURATION ###
DUCKDB_PATH = "commonlii_cases.duckdb"            # Path to your DuckDB database
DUCKDB_TABLE = "embedded_points"                      # Table name containing id, vectors, payload
QDRANT_COLLECTION_NAME = "commonlii_cases"  # Qdrant collection name
BATCH_SIZE = 100 # Number of points to upload in a single batch
#####################

# Connect to DuckDB
conn = duckdb.connect(DUCKDB_PATH)

# Query data from DuckDB
rows = conn.execute(f"SELECT id, vector, payload FROM {DUCKDB_TABLE}").fetchall()

# Convert to Qdrant-compatible PointStruct
qdrant_points: List[PointStruct] = []

# Instantiate the embedder (the class with upload_points_to_qdrant)
embedder = OpenAIEmbedder()


qdrant_points: List[PointStruct] = []

for row in rows:
    id_, vector_raw, payload_raw = row

    vector = json.loads(vector_raw) if isinstance(vector_raw, str) else vector_raw
    payload = json.loads(payload_raw) if isinstance(payload_raw, str) else payload_raw

    point = PointStruct(
        id=id_,
        vector=vector,
        payload=payload
    )
    qdrant_points.append(point)

    # Upload when batch size is met
    if len(qdrant_points) == BATCH_SIZE:
        embedder.upload_points_to_qdrant(
            qdrant_points=qdrant_points,
            collection_name=QDRANT_COLLECTION_NAME,
        )
        qdrant_points.clear()  # Clear batch

# Upload any remaining points
if qdrant_points:
    embedder.upload_points_to_qdrant(
        qdrant_points=qdrant_points,
        collection_name=QDRANT_COLLECTION_NAME,
    )
