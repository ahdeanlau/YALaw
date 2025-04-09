from qdrant_client import QdrantClient, models
from config.config_env import QDRANT_API_KEY, QDRANT_CLIENT_URL

qdrant_client = QdrantClient(url=QDRANT_CLIENT_URL, api_key=QDRANT_API_KEY)

print(qdrant_client.get_collections())

client = QdrantClient(url="http://localhost:6333")

client.upsert(
    collection_name="malaysia_acts",
    points=[
        models.PointStruct(
            id=1,
            vector=[0.05, 0.61, 0.76, 0.74],
            payload={
                "city": "Berlin",
                "price": 1.99,
            },
        ),
        models.PointStruct(
            id=2,
            vector=[0.19, 0.81, 0.75, 0.11],
            payload={
                "city": ["Berlin", "London"],
                "price": 1.99,
            },
        ),
        models.PointStruct(
            id=3,
            vector=[0.36, 0.55, 0.47, 0.94],
            payload={
                "city": ["Berlin", "Moscow"],
                "price": [1.99, 2.99],
            },
        ),
    ],
)
