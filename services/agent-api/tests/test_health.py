"""Smoke test for the health endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok():
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"


def test_root():
    res = client.get("/")
    assert res.status_code == 200
    assert "docs" in res.json()
