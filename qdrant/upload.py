from qdrant_client import QdrantClient, models
from config.config_env import QDRANT_API_KEY, QDRANT_CLIENT_URL
import json, duckdb
import sys
from qdrant_client.models import PointStruct
from typing import List

qdrant_client = QdrantClient(url=QDRANT_CLIENT_URL, api_key=QDRANT_API_KEY)

print(qdrant_client.get_collections())

client = QdrantClient(url="http://localhost:6333")



def prepare_qdrant_points_from_duckdb(db_path: str, table_or_parquet: str) -> List[PointStruct]:
    """
    Reads id, vector, and payload from a DuckDB table or Parquet file,
    and converts them into Qdrant PointStruct objects.
    
    Args:
        db_path: path to .duckdb database (or None if querying directly from a Parquet file)
        table_or_parquet: table name or full path to a Parquet file
    
    Returns:
        List of PointStruct ready for Qdrant upsert
    """
    # DuckDB connection
    con = duckdb.connect(database=db_path) if db_path else duckdb.connect()

    # Read data
    qdrant_points_df = con.execute(f"SELECT id, vector, payload FROM '{table_or_parquet}'").df()

    # Convert to PointStruct list
    points = []
    for _, row in qdrant_points_df.iterrows():
        points.append(PointStruct(
            id=row["id"],
            vector=row["vector"],
            payload=json.loads(row["payload"])
        ))

    return points

def upload_points_to_qdrant(points: List[PointStruct], collection_name: str):
    """
    Uploads a list of PointStruct objects to Qdrant.
    
    Args:
        points: List of PointStruct objects
        collection_name: Name of the Qdrant collection to upload to
    """ 
    # Create collection if it doesn't exist
    if not qdrant_client.has_collection(collection_name):
        qdrant_client.recreate_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=len(points[0].vector),
                distance=models.Distance.COSINE
            )
        )
    
    # Upload points
    qdrant_client.upsert(
        collection_name=collection_name,
        points=points
    )

    print(f"Uploaded {len(points)} points to Qdrant collection '{collection_name}'.")
    # Close DuckDB connection
    con.close()
    print("Closed DuckDB connection.")
    # Close Qdrant connection
    qdrant_client.close()
    print("Closed Qdrant connection.")
