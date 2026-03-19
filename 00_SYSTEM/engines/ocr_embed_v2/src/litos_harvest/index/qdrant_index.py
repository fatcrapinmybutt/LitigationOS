
from __future__ import annotations

from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models

def ensure_collection(client: QdrantClient, name: str, vector_size: int) -> None:
    existing = client.get_collections().collections
    if any(c.name == name for c in existing):
        return
    client.create_collection(
        collection_name=name,
        vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
    )

def upsert_points(client: QdrantClient, name: str, points: List[Dict[str, Any]]) -> None:
    # Each point: {"id": str, "vector": [..], "payload": {...}}
    client.upsert(
        collection_name=name,
        points=[
            models.PointStruct(id=p["id"], vector=p["vector"], payload=p.get("payload") or {})
            for p in points
        ]
    )
