"""HTTP API, including a chat round trip."""

from __future__ import annotations

from app.agent.mentor import MentorAgent
from app.content.loader import LESSONS
from app.core.rate_limit import RateLimiter
from tests.test_agent import ScriptedLlm


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["llm_configured"] is False
    assert body["github_token_configured"] is False
    assert response.headers["x-content-type-options"] == "nosniff"


def test_chat_round_trip_in_guide_mode(client):
    response = client.post("/api/v1/chat", json={"message": "Explain UTXOs"})
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "guide"
    assert "unspent" in body["message"]["content"].lower()
    assert body["message"]["tool_trace"][0]["name"] == "explain_concept"
    conversation_id = body["conversation_id"]

    follow = client.post(
        "/api/v1/chat",
        json={"conversation_id": conversation_id, "message": "What is a change output?"},
    )
    assert follow.status_code == 200
    stored = client.get(f"/api/v1/conversations/{conversation_id}")
    assert stored.status_code == 200
    assert len(stored.json()["messages"]) == 4
    listed = client.get("/api/v1/conversations")
    assert any(item["id"] == conversation_id for item in listed.json()["conversations"])

    deleted = client.delete(f"/api/v1/conversations/{conversation_id}")
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/conversations/{conversation_id}").status_code == 404


def test_chat_with_scripted_llm(client):
    client.app.state.agent = MentorAgent(ScriptedLlm(), client.app.state.tools)
    response = client.post("/api/v1/chat", json={"message": "What is a UTXO?"})
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "llm"
    assert "Guide mode" not in body["message"]["content"]
    assert "unspent" in body["message"]["content"].lower()
    assert "ghp_" not in body["message"]["content"]


def test_chat_validation(client):
    assert client.post("/api/v1/chat", json={"message": "   "}).status_code == 422
    assert client.post("/api/v1/chat", json={"message": "x" * 8001}).status_code == 422
    assert client.post(
        "/api/v1/chat",
        json={"message": "Explain UTXOs", "conversation_id": "not-a-uuid"},
    ).status_code == 422
    missing = client.post(
        "/api/v1/chat",
        json={
            "message": "Explain UTXOs",
            "conversation_id": "11111111-1111-1111-1111-111111111111",
        },
    )
    assert missing.status_code == 404
    extra = client.post("/api/v1/chat", json={"message": "Hi", "token": "ghp_secret"})
    assert extra.status_code == 422


def test_lesson_hides_answers_until_graded(client):
    lesson = client.get("/api/v1/curriculum/lessons/utxos")
    assert lesson.status_code == 200
    quiz = lesson.json()["quiz"]
    assert set(quiz[0]) == {"prompt", "choices"}
    correct = [question.answer for question in LESSONS["utxos"].quiz]
    graded = client.post("/api/v1/curriculum/lessons/utxos/quiz", json={"answers": correct})
    assert graded.status_code == 200
    assert graded.json()["score"] == len(correct)
    assert client.get("/api/v1/curriculum/lessons/../utxos").status_code == 404
    assert client.get("/api/v1/curriculum/paths/bitcoin-fundamentals").status_code == 200


def test_projects_endpoint(client):
    listed = client.get("/api/v1/projects")
    assert listed.status_code == 200
    assert any(item["slug"] == "lnd" for item in listed.json()["projects"])
    detail = client.get("/api/v1/projects/bitcoin-core")
    assert detail.status_code == 200
    assert "cmake" in " ".join(detail.json()["setup_steps"])
    assert client.get("/api/v1/projects/nope").status_code == 404


def test_chat_rate_limit(client):
    original = client.app.state.chat_limiter
    client.app.state.chat_limiter = RateLimiter(2, 60)
    try:
        assert client.post("/api/v1/chat", json={"message": "Explain UTXOs"}).status_code == 200
        assert client.post("/api/v1/chat", json={"message": "Explain UTXOs"}).status_code == 200
        blocked = client.post("/api/v1/chat", json={"message": "Explain UTXOs"})
        assert blocked.status_code == 429
        assert blocked.headers["retry-after"] == "60"
    finally:
        client.app.state.chat_limiter = original
