# Qdrant

Qdrant stores embeddings of repository code chunks for retrieval-augmented
reasoning by the agent system.

- The collection (default `osma_repo_chunks`) is created automatically by the
  FastAPI service on startup if it does not exist (see
  `services/agent-api/app/services/vector_store.py`).
- Vector size is controlled by `EMBEDDING_DIM` and must match the embedding
  model configured via `EMBEDDING_MODEL`.
- In Docker Compose, data persists in the `qdrant_storage` volume.

Dashboard (local): http://localhost:6333/dashboard
