"""Provider-agnostic LLM wrapper.

Supports:
- "anthropic": Claude via the Anthropic SDK.
- "together":  Together.ai (OpenAI-compatible API) - used to run the fine-tuned
               OSMA Mentor model.
- "openai":    OpenAI (or any OpenAI-compatible endpoint).

The provider is selected by LLM_PROVIDER. Each provider exposes the same
complete()/stream() interface so the agent nodes stay provider-agnostic.
"""

from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

TOGETHER_BASE_URL = "https://api.together.xyz/v1"


class LLMNotConfigured(RuntimeError):
    pass


class LLMClient:
    def __init__(self) -> None:
        self.provider = settings.llm_provider.lower()
        self._client = None
        self._model = None

    # ------------------------------------------------------------------
    # Client setup
    # ------------------------------------------------------------------
    def _ensure(self):
        if self._client is not None:
            return self._client

        if self.provider == "anthropic":
            if not settings.anthropic_api_key:
                raise LLMNotConfigured(
                    "ANTHROPIC_API_KEY is not set. Configure it or switch LLM_PROVIDER."
                )
            import anthropic

            self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            self._model = settings.anthropic_model

        elif self.provider == "together":
            if not settings.together_api_key:
                raise LLMNotConfigured(
                    "TOGETHER_API_KEY is not set. Configure it to use the Together model."
                )
            from openai import OpenAI

            self._client = OpenAI(
                api_key=settings.together_api_key, base_url=TOGETHER_BASE_URL
            )
            self._model = settings.together_model

        elif self.provider == "openai":
            if not settings.openai_api_key:
                raise LLMNotConfigured("OPENAI_API_KEY is not set.")
            from openai import OpenAI

            self._client = OpenAI(api_key=settings.openai_api_key)
            self._model = settings.openai_model

        else:
            raise LLMNotConfigured(f"Unknown LLM_PROVIDER: {self.provider}")

        return self._client

    @property
    def model(self) -> str:
        self._ensure()
        return self._model or ""

    # ------------------------------------------------------------------
    # Completion
    # ------------------------------------------------------------------
    def complete(
        self,
        system: str,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.2,
    ) -> str:
        client = self._ensure()

        if self.provider == "anthropic":
            resp = client.messages.create(
                model=self._model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            return "".join(
                b.text for b in resp.content if getattr(b, "type", "") == "text"
            )

        # OpenAI-compatible (together / openai)
        resp = client.chat.completions.create(
            model=self._model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        return resp.choices[0].message.content or ""

    # ------------------------------------------------------------------
    # Streaming
    # ------------------------------------------------------------------
    def stream(
        self,
        system: str,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.2,
    ):
        client = self._ensure()

        if self.provider == "anthropic":
            with client.messages.stream(
                model=self._model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                yield from stream.text_stream
            return

        # OpenAI-compatible (together / openai)
        stream = client.chat.completions.create(
            model=self._model,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                yield delta


@lru_cache
def get_llm() -> LLMClient:
    return LLMClient()
