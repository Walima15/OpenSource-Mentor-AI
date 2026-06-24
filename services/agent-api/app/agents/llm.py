"""Anthropic Claude wrapper.

A thin abstraction so the model can be swapped via env. If no API key is
configured, calls raise a clear error rather than failing deep in the stack.
"""

from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMNotConfigured(RuntimeError):
    pass


class LLMClient:
    def __init__(self) -> None:
        self.model = settings.anthropic_model
        self._client = None

    def _ensure(self):
        if self._client is not None:
            return self._client
        if not settings.anthropic_api_key:
            raise LLMNotConfigured(
                "ANTHROPIC_API_KEY is not set. Configure it to use the agent system."
            )
        import anthropic

        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        return self._client

    def complete(
        self,
        system: str,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.2,
    ) -> str:
        client = self._ensure()
        resp = client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(
            block.text for block in resp.content if getattr(block, "type", "") == "text"
        )

    def stream(
        self,
        system: str,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.2,
    ):
        """Yield text deltas as they arrive."""
        client = self._ensure()
        with client.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            yield from stream.text_stream


@lru_cache
def get_llm() -> LLMClient:
    return LLMClient()
