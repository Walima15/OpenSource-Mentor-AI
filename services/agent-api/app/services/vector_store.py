"""Qdrant vector store wrapper for repository code chunks."""

from __future__ import annotations

from functools import lru_cache

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class VectorStore:
    def __init__(self) -> None:
        self.collection = settings.qdrant_collection
        self.dim = settings.embedding_dim
        self.client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key or None,
            timeout=30,
        )

    def ensure_collection(self) -> None:
        existing = {c.name for c in self.client.get_collections().collections}
        if self.collection in existing:
            return
        logger.info("Creating Qdrant collection %s (dim=%d)", self.collection, self.dim)
        self.client.create_collection(
            collection_name=self.collection,
            vectors_config=qmodels.VectorParams(
                size=self.dim, distance=qmodels.Distance.COSINE
            ),
        )
        # Index repo_id so we can filter retrieval per repository.
        self.client.create_payload_index(
            collection_name=self.collection,
            field_name="repo_id",
            field_schema=qmodels.PayloadSchemaType.KEYWORD,
        )

    def upsert(
        self,
        ids: list[str],
        vectors: list[list[float]],
        payloads: list[dict],
    ) -> None:
        if not ids:
            return
        self.ensure_collection()
        points = [
            qmodels.PointStruct(id=pid, vector=vec, payload=payload)
            for pid, vec, payload in zip(ids, vectors, payloads, strict=True)
        ]
        self.client.upsert(collection_name=self.collection, points=points)

    def search(
        self, repo_id: str, query_vector: list[float], limit: int = 6
    ) -> list[dict]:
        self.ensure_collection()
        hits = self.client.search(
            collection_name=self.collection,
            query_vector=query_vector,
            limit=limit,
            query_filter=qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="repo_id", match=qmodels.MatchValue(value=repo_id)
                    )
                ]
            ),
        )
        return [
            {
                "score": hit.score,
                "file_path": hit.payload.get("file_path"),
                "content": hit.payload.get("content"),
                "start_line": hit.payload.get("start_line"),
                "end_line": hit.payload.get("end_line"),
            }
            for hit in hits
        ]

    def delete_repo(self, repo_id: str) -> None:
        self.client.delete(
            collection_name=self.collection,
            points_selector=qmodels.FilterSelector(
                filter=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="repo_id", match=qmodels.MatchValue(value=repo_id)
                        )
                    ]
                )
            ),
        )


@lru_cache
def get_vector_store() -> VectorStore:
    return VectorStore()
