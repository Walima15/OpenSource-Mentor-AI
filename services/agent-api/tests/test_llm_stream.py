"""Tests for the async streaming bridge over the (sync) LLM client."""

from __future__ import annotations

import pytest

from app.agents import llm


class _FakeLLM:
    def __init__(self, deltas=None, error=None):
        self._deltas = deltas or []
        self._error = error

    def stream(self, system, prompt, max_tokens=2000, temperature=0.2):
        yield from self._deltas
        if self._error is not None:
            raise self._error


@pytest.mark.asyncio
async def test_astream_completion_yields_all_deltas(monkeypatch):
    monkeypatch.setattr(llm, "get_llm", lambda: _FakeLLM(["a", "b", "c"]))
    collected = [
        delta async for delta in llm.astream_completion("sys", "prompt")
    ]
    assert collected == ["a", "b", "c"]


@pytest.mark.asyncio
async def test_astream_completion_propagates_errors(monkeypatch):
    monkeypatch.setattr(
        llm,
        "get_llm",
        lambda: _FakeLLM(["partial"], error=llm.LLMNotConfigured("no key")),
    )
    seen = []
    with pytest.raises(llm.LLMNotConfigured):
        async for delta in llm.astream_completion("sys", "prompt"):
            seen.append(delta)
    assert seen == ["partial"]
