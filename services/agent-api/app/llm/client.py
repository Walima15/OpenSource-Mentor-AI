"""Chat completions against any OpenAI-compatible /chat/completions endpoint."""

from __future__ import annotations

import json
from dataclasses import dataclass, field

import httpx

from app.core.security import validate_llm_base_url


class LlmError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict
    raw_arguments: str


@dataclass
class LlmResult:
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    assistant_message: dict = field(default_factory=dict)


class OpenAICompatibleClient:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        transport: httpx.BaseTransport | None = None,
    ):
        self.api_key = api_key
        self.base_url = validate_llm_base_url(base_url)
        self.model = model
        self._client = httpx.Client(
            timeout=httpx.Timeout(60.0, connect=5.0),
            follow_redirects=False,
            trust_env=False,
            transport=transport,
        )

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def close(self) -> None:
        self._client.close()

    def complete(self, messages: list[dict], tools: list[dict] | None) -> LlmResult:
        if not self.api_key:
            raise LlmError("OPENAI_API_KEY is not set")
        payload: dict = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        try:
            response = self._client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        except httpx.HTTPError:
            raise LlmError("LLM request failed") from None
        if response.status_code in {301, 302, 303, 307, 308}:
            raise LlmError("LLM endpoint returned a redirect")
        if response.status_code >= 400:
            raise LlmError(f"LLM request failed ({response.status_code})")
        try:
            data = response.json()
            message = data["choices"][0]["message"]
        except (ValueError, KeyError, IndexError, TypeError):
            raise LlmError("LLM response was not a chat completion") from None
        return _parse_message(message)


def _parse_message(message: dict) -> LlmResult:
    content = message.get("content") or ""
    if not isinstance(content, str):
        content = ""
    calls: list[ToolCall] = []
    raw_calls = []
    for item in message.get("tool_calls") or []:
        if not isinstance(item, dict):
            continue
        function = item.get("function") or {}
        name = function.get("name") or ""
        raw_arguments = function.get("arguments") or "{}"
        if not isinstance(raw_arguments, str):
            raw_arguments = json.dumps(raw_arguments)
        try:
            arguments = json.loads(raw_arguments) if raw_arguments else {}
        except json.JSONDecodeError:
            arguments = {}
        if not isinstance(arguments, dict):
            arguments = {}
        call_id = str(item.get("id") or f"call_{len(calls)}")
        calls.append(ToolCall(id=call_id, name=name, arguments=arguments, raw_arguments=raw_arguments))
        raw_calls.append(
            {
                "id": call_id,
                "type": "function",
                "function": {"name": name, "arguments": raw_arguments},
            }
        )
    assistant = {"role": "assistant", "content": content or None}
    if raw_calls:
        assistant["tool_calls"] = raw_calls
    return LlmResult(content=content, tool_calls=calls, assistant_message=assistant)
