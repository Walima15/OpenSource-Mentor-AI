"""Tests for GitHub client retry behavior and connection reuse."""

from __future__ import annotations

import httpx
import pytest

from app.services import github_service as gs


def _service_with_transport(handler) -> gs.GitHubService:
    svc = gs.GitHubService(token="t")
    svc._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://api.github.com",
    )
    return svc


@pytest.mark.asyncio
async def test_get_retries_transient_5xx():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(502, text="bad gateway")
        return httpx.Response(200, json={"ok": True})

    svc = _service_with_transport(handler)
    try:
        data = await svc._get("/repos/o/r")
    finally:
        await svc._client.aclose()

    assert data == {"ok": True}
    assert calls["n"] == 3


@pytest.mark.asyncio
async def test_get_does_not_retry_client_errors():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        return httpx.Response(404, text="not found")

    svc = _service_with_transport(handler)
    try:
        with pytest.raises(gs.GitHubError) as exc:
            await svc._get("/repos/o/r")
    finally:
        await svc._client.aclose()

    assert exc.value.status_code == 404
    assert calls["n"] == 1


@pytest.mark.asyncio
async def test_context_manager_manages_client_lifecycle():
    async with gs.GitHubService(token="t") as svc:
        assert svc._client is not None
    assert svc._client is None
