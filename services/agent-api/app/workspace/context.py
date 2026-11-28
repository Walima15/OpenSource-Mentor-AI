"""Which workspace the current request is allowed to touch."""

from __future__ import annotations

from contextvars import ContextVar

_workspace_id: ContextVar[str | None] = ContextVar("osma_workspace_id", default=None)


def current_workspace_id() -> str | None:
    return _workspace_id.get()


def set_workspace_id(workspace_id: str | None):
    return _workspace_id.set(workspace_id)


def reset_workspace_id(token) -> None:
    _workspace_id.reset(token)
