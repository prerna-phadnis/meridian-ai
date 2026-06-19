from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
from dotenv import load_dotenv
import os
import logging

load_dotenv()

logger = logging.getLogger(__name__)

client = QdrantClient(
    url=os.getenv("QDRANT_URL", "http://localhost:6333")
)

COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "meridian_papers")
VECTOR_SIZE = 768


def ensure_collection_exists():
    collections = client.get_collections().collections
    names = [c.name for c in collections]

    if COLLECTION_NAME not in names:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE
            )
        )
        logger.info(f"Created collection: {COLLECTION_NAME}")
    else:
        logger.info(f"Collection exists: {COLLECTION_NAME}")


def store_chunks(paper_id: str, user_id: str, chunks: list[dict], embeddings: list):
    ensure_collection_exists()

    points = []

    for chunk, embedding in zip(chunks, embeddings):
        point_id = abs(hash(f"{paper_id}_{chunk['index']}")) % (10**12)

        points.append(
            PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "paper_id": paper_id,
                    "user_id": user_id,
                    "chunk_index": chunk["index"],
                    "page_number": chunk["page_number"],
                    "text": chunk["text"],
                    "word_count": chunk["word_count"],
                }
            )
        )

    batch_size = 100

    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=batch
        )

    logger.info(f"Stored {len(points)} chunks for paper {paper_id}")


def search_similar_chunks(
    query_embedding: list[float],
    paper_id: str,
    limit: int = 5
) -> list[dict]:
    ensure_collection_exists()

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        query_filter=Filter(
            must=[
                FieldCondition(
                    key="paper_id",
                    match=MatchValue(value=paper_id)
                )
            ]
        ),
        limit=limit,
        with_payload=True
    )

    return [
        {
            "text": hit.payload["text"],
            "page_number": hit.payload["page_number"],
            "chunk_index": hit.payload["chunk_index"],
            "score": hit.score
        }
        for hit in results.points
    ]


def delete_paper_chunks(paper_id: str):
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="paper_id",
                    match=MatchValue(value=paper_id)
                )
            ]
        )
    )

    logger.info(f"Deleted chunks for paper {paper_id}")