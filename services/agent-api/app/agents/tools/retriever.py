"""Qdrant-backed retrieval tool used by agent nodes."""

from __future__ import annotations

from app.core.logging import get_logger
from app.services.embedding_service import get_embedding_service
from app.services.vector_store import get_vector_store

logger = get_logger(__name__)


def retrieve_context(repo_id: str, query: str, limit: int = 6) -> list[dict]:
    """Return the most relevant indexed code chunks for a query."""
    if not query.strip():
        return []
    try:
        embedder = get_embedding_service()
        store = get_vector_store()
        vector = embedder.embed_one(query)
        return store.search(repo_id=repo_id, query_vector=vector, limit=limit)
    except Exception:
        # Retrieval is best-effort; agents still work without context.
        logger.exception("Retrieval failed for repo %s", repo_id)
        return []
