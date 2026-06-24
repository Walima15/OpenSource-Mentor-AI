"""Unit tests for agent helpers and graph routing (no network required)."""

from __future__ import annotations

from app.agents.nodes.contribution import _extract_diff, _safe_json_list
from app.agents.nodes.mentor import _safe_json


def test_extract_diff_from_fenced_block():
    text = "Here is the change:\n```diff\n- old\n+ new\n```\nDone."
    assert _extract_diff(text) == "- old\n+ new"


def test_extract_diff_without_fence_returns_text():
    text = "no fences here"
    assert _extract_diff(text) == "no fences here"


def test_safe_json_parses_object():
    raw = '```json\n{"summary": "x", "steps": [], "recommended_files": []}\n```'
    parsed = _safe_json(raw, fallback={})
    assert parsed["summary"] == "x"


def test_safe_json_falls_back_on_garbage():
    parsed = _safe_json("not json at all", fallback={"summary": "fb"})
    assert parsed["summary"] == "fb"


def test_safe_json_list_parses_array():
    raw = '[{"path": "a.py", "reason": "r"}]'
    parsed = _safe_json_list(raw)
    assert parsed[0]["path"] == "a.py"


def test_graph_routes_by_intent(monkeypatch):
    # Patch the LLM so no network call happens.
    from app.agents import llm

    class FakeLLM:
        def complete(self, *a, **k):
            return "REPO EXPLANATION"

    monkeypatch.setattr(llm, "get_llm", lambda: FakeLLM())
    # Also patch the reference imported into the node module.
    from app.agents.nodes import mentor

    monkeypatch.setattr(mentor, "get_llm", lambda: FakeLLM())

    from app.agents.graph import build_graph

    build_graph.cache_clear()
    graph = build_graph()
    result = graph.invoke({"intent": "explain_repo", "repo_full_name": "a/b"})
    assert result["output"] == "REPO EXPLANATION"
