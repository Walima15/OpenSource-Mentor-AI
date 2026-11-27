"""URL allowlists, settings defaults, redaction, and the LLM client."""

from __future__ import annotations

import logging

import httpx
import pytest

from app.core.config import Settings
from app.core.security import (
    ToolError,
    redact,
    validate_git_path,
    validate_llm_base_url,
    validate_owner_repo,
)
from app.llm.client import OpenAICompatibleClient


def test_default_settings_are_local_first(monkeypatch):
    for name in ("OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL"):
        monkeypatch.delenv(name, raising=False)
    assert Settings.model_fields["openai_api_key"].default == ""
    assert Settings.model_fields["openai_base_url"].default == "http://127.0.0.1:11434/v1"
    assert Settings.model_fields["openai_model"].default == "llama3.2"

    settings = Settings(_env_file=None)
    assert settings.openai_api_key == ""
    assert settings.openai_base_url == "http://127.0.0.1:11434/v1"
    assert settings.openai_model == "llama3.2"
    assert settings.llm_configured is False


def test_cloud_openai_is_explicit_opt_in(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")
    settings = Settings(_env_file=None)
    assert settings.openai_api_key == "test-key"
    assert settings.openai_base_url == "https://api.openai.com/v1"
    assert settings.openai_model == "gpt-4o-mini"
    assert settings.llm_configured is True


def test_llm_base_url_policy():
    assert validate_llm_base_url("https://api.openai.com/v1") == "https://api.openai.com/v1"
    assert validate_llm_base_url("http://127.0.0.1:11434/v1").startswith("http://127.0.0.1")
    with pytest.raises(ValueError):
        validate_llm_base_url("http://169.254.169.254/latest")
    with pytest.raises(ValueError):
        validate_llm_base_url("http://example.com/v1")
    with pytest.raises(ValueError):
        validate_llm_base_url("https://user:secret@api.openai.com/v1")
    with pytest.raises(ValueError):
        validate_llm_base_url("file:///etc/passwd")


def test_path_and_owner_validation():
    with pytest.raises(ToolError):
        validate_git_path("../../etc/passwd")
    with pytest.raises(ToolError):
        validate_owner_repo("evil/../x", "bitcoin")
    assert validate_git_path("src/validation.cpp") == "src/validation.cpp"


def test_redact_tokens():
    text = "Authorization: Bearer ghp_" + ("b" * 36) + " and sk-" + ("c" * 24)
    cleaned = redact(text)
    assert "ghp_" not in cleaned
    assert "sk-" not in cleaned
    assert "[redacted]" in cleaned


def test_redact_filter_on_log_records(caplog):
    caplog.set_level(logging.INFO)
    logger = logging.getLogger("osma.test.redact")
    secret = "ghp_" + ("d" * 36)
    logger.info("failed with %s", secret)
    # The filter is installed on the app's handlers during lifespan. Apply it
    # directly so this test does not depend on handler order.
    from app.core.security import RedactFilter

    record = logging.LogRecord("osma.test", logging.INFO, __file__, 1, "token %s", (secret,), None)
    assert RedactFilter().filter(record)
    assert secret not in record.getMessage()


def test_llm_client_parses_tool_calls_and_rejects_redirects():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/redirected"):
            return httpx.Response(302, headers={"Location": "http://169.254.169.254/"})
        body = request.read()
        assert b"sk-test-key" not in body
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call_9",
                                    "type": "function",
                                    "function": {
                                        "name": "explain_concept",
                                        "arguments": '{"query":"utxo"}',
                                    },
                                }
                            ],
                        }
                    }
                ]
            },
        )

    client = OpenAICompatibleClient(
        api_key="sk-test-key",
        base_url="https://example.test/v1",
        model="test-model",
        transport=httpx.MockTransport(handler),
    )
    result = client.complete([{"role": "user", "content": "utxo"}], tools=[])
    assert result.tool_calls[0].name == "explain_concept"
    assert result.tool_calls[0].arguments == {"query": "utxo"}

    def redirect_handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(302, headers={"Location": "http://169.254.169.254/"})

    from app.llm.client import LlmError

    client._client = httpx.Client(
        transport=httpx.MockTransport(redirect_handler),
        follow_redirects=False,
        trust_env=False,
    )
    with pytest.raises(LlmError, match="redirect"):
        client.complete([{"role": "user", "content": "hi"}], tools=None)
    client.close()
