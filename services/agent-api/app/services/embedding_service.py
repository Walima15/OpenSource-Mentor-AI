"""Embedding generation.

Defaults to a local fastembed model so no extra paid API key is required.
The provider is swappable via the EMBEDDING_PROVIDER env var.
"""

from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    def __init__(self) -> None:
        self.provider = settings.embedding_provider
        self.model_name = settings.embedding_model
        self.dim = settings.embedding_dim
        self._model = None

    def _ensure_model(self):
        if self._model is not None:
            return self._model
        if self.provider == "fastembed":
            from fastembed import TextEmbedding

            logger.info("Loading fastembed model %s", self.model_name)
            self._model = TextEmbedding(model_name=self.model_name)
        else:
            raise ValueError(f"Unsupported embedding provider: {self.provider}")
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        model = self._ensure_model()
        return [vec.tolist() for vec in model.embed(texts)]

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]


@lru_cache
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()
