"""Repository ingestion: fetch -> chunk -> embed -> upsert to Qdrant.

Kept intentionally simple for the MVP: we fetch a bounded set of source files
from the default branch, split them into line-based chunks, embed them, and
store both the vectors (Qdrant) and a metadata mirror (Postgres).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.models import IndexStatus, RepoIndexChunk, TrackedRepo
from app.services.embedding_service import get_embedding_service
from app.services.github_service import GitHubService
from app.services.vector_store import get_vector_store

logger = get_logger(__name__)

# File extensions worth indexing for code understanding.
INDEXABLE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java", ".rb",
    ".c", ".h", ".cpp", ".hpp", ".cs", ".php", ".swift", ".kt", ".scala",
    ".md", ".rst", ".toml", ".yaml", ".yml", ".json", ".sh",
}

# Limits to keep ingestion fast and within API budgets for the MVP.
MAX_FILES = 120
MAX_FILE_BYTES = 80_000
CHUNK_LINES = 60
CHUNK_OVERLAP = 10


def _is_indexable(path: str, size: int | None) -> bool:
    lower = path.lower()
    if any(seg in lower for seg in ("node_modules/", "dist/", "build/", ".min.")):
        return False
    if size is not None and size > MAX_FILE_BYTES:
        return False
    return any(lower.endswith(ext) for ext in INDEXABLE_EXTENSIONS)


def _chunk_file(path: str, content: str) -> list[dict]:
    lines = content.splitlines()
    chunks: list[dict] = []
    step = max(CHUNK_LINES - CHUNK_OVERLAP, 1)
    for start in range(0, len(lines), step):
        window = lines[start : start + CHUNK_LINES]
        if not window:
            continue
        text = "\n".join(window).strip()
        if not text:
            continue
        chunks.append(
            {
                "file_path": path,
                "start_line": start + 1,
                "end_line": start + len(window),
                "content": text,
            }
        )
    return chunks


async def ingest_repository(db: Session, repo: TrackedRepo, token: str | None) -> int:
    """Index a repository. Returns the number of chunks indexed."""
    gh = GitHubService(token=token)
    embedder = get_embedding_service()
    store = get_vector_store()

    repo.index_status = IndexStatus.indexing
    db.commit()

    try:
        tree, _ = await gh.get_tree(repo.owner, repo.name, repo.default_branch)
        files = [
            n for n in tree if n["type"] == "file" and _is_indexable(n["path"], n.get("size"))
        ][:MAX_FILES]

        all_chunks: list[dict] = []
        for node in files:
            content = await gh.get_file_content(
                repo.owner, repo.name, node["path"], repo.default_branch
            )
            if not content:
                continue
            all_chunks.extend(_chunk_file(node["path"], content))

        # Clear any previous index for this repo.
        store.delete_repo(str(repo.id))
        db.execute(delete(RepoIndexChunk).where(RepoIndexChunk.repo_id == repo.id))

        if all_chunks:
            vectors = embedder.embed([c["content"] for c in all_chunks])
            ids = [str(uuid.uuid4()) for _ in all_chunks]
            payloads = [
                {
                    "repo_id": str(repo.id),
                    "file_path": c["file_path"],
                    "start_line": c["start_line"],
                    "end_line": c["end_line"],
                    "content": c["content"],
                }
                for c in all_chunks
            ]
            store.upsert(ids, vectors, payloads)

            for pid, c in zip(ids, all_chunks, strict=True):
                db.add(
                    RepoIndexChunk(
                        repo_id=repo.id,
                        file_path=c["file_path"],
                        start_line=c["start_line"],
                        end_line=c["end_line"],
                        qdrant_point_id=pid,
                        token_count=len(c["content"].split()),
                    )
                )

        repo.index_status = IndexStatus.ready
        repo.last_indexed_at = datetime.now(UTC)
        db.commit()
        logger.info("Indexed %s with %d chunks", repo.full_name, len(all_chunks))
        return len(all_chunks)
    except Exception:
        db.rollback()
        repo.index_status = IndexStatus.failed
        db.commit()
        logger.exception("Failed to index repo %s", repo.full_name)
        raise
