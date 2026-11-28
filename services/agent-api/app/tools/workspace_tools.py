"""Tools that read a local clone. They never run a shell or write a file."""

from __future__ import annotations

from app.core.security import ToolError
from app.workspace.context import current_workspace_id
from app.workspace.store import propose_edit, read_file, search


def _workspace_id() -> str:
    workspace_id = current_workspace_id()
    if not workspace_id:
        raise ToolError("Open a workspace before reading local files")
    return workspace_id


def read_workspace_file(args: dict) -> dict:
    from app.tools.util import required_str

    relative = required_str(args, "path", 400)
    payload = read_file(_workspace_id(), relative)
    text = payload.get("text") or ""
    return {
        "summary": f"Local file {relative}",
        "path": relative,
        "binary": payload.get("binary", False),
        "truncated": payload.get("truncated", False),
        "text": text[:12_000],
    }


def search_workspace(args: dict) -> dict:
    from app.tools.util import required_str

    query = required_str(args, "query", 80)
    return search(_workspace_id(), query)


def propose_workspace_edit(args: dict) -> dict:
    from app.tools.util import required_str

    relative = required_str(args, "path", 400)
    old = args.get("old")
    new = args.get("new", "")
    if not isinstance(old, str) or old == "":
        raise ToolError("old text is required")
    if not isinstance(new, str):
        raise ToolError("new text must be a string")
    if "\x00" in old or "\x00" in new or len(old) > 20_000 or len(new) > 20_000:
        raise ToolError("Edit snippet is too large")
    return propose_edit(_workspace_id(), relative, old, new)
