"""Tests for the best-effort retrieval tool."""

from __future__ import annotations

from app.agents.tools import retriever


def test_retrieve_context_empty_query_returns_empty():
    assert retriever.retrieve_context("repo-id", "") == []
    assert retriever.retrieve_context("repo-id", "   ") == []


def test_retrieve_context_swallows_backend_errors(monkeypatch):
    class Boom:
        def embed_one(self, _text):
            raise RuntimeError("embedding backend down")

    monkeypatch.setattr(retriever, "get_embedding_service", lambda: Boom())
    # Retrieval is best-effort: failures degrade to an empty context.
    assert retriever.retrieve_context("repo-id", "some query") == []


def test_retrieve_context_returns_store_hits(monkeypatch):
    class FakeEmbedder:
        def embed_one(self, _text):
            return [0.1, 0.2, 0.3]

    class FakeStore:
        def search(self, repo_id, query_vector, limit):
            assert repo_id == "repo-id"
            assert query_vector == [0.1, 0.2, 0.3]
            return [{"file_path": "a.py", "content": "x"}]

    monkeypatch.setattr(retriever, "get_embedding_service", lambda: FakeEmbedder())
    monkeypatch.setattr(retriever, "get_vector_store", lambda: FakeStore())
    hits = retriever.retrieve_context("repo-id", "query")
    assert hits == [{"file_path": "a.py", "content": "x"}]
