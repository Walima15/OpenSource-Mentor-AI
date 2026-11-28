"""Tools that read a local clone. They never run a shell or write a file."""

from __future__ import annotations

from app.core.security import ToolError
from app.workspace.context import current_workspace_id
from app.workspace.store import get_workspace, propose_edit, read_file, search


def _workspace_id() -> str:
    workspace_id = current_workspace_id()
    if not workspace_id:
        raise ToolError("Open a workspace before reading local files")
    return workspace_id


def read_workspace_file(args: dict) -> dict:
    from app.tools.util import required_str

    workspace_id = _workspace_id()
    relative = required_str(args, "path", 400)
    payload = read_file(workspace_id, relative)
    text = payload.get("text") or ""
    cap = int(get_workspace(workspace_id).get("file_chars") or 12_000)
    shortened = len(text) > cap
    return {
        "summary": f"Local file {relative}",
        "path": relative,
        "binary": payload.get("binary", False),
        "truncated": bool(payload.get("truncated")) or shortened,
        "text": text[:cap],
    }


def workspace_orientation(args: dict | None = None) -> dict:
    meta = get_workspace(_workspace_id())
    return {
        "summary": f"Contribution notes for {meta['name']}",
        "name": meta["name"],
        "language": meta["language"],
        "owner": meta["owner"],
        "repo": meta["repo"],
        "contributing": meta["contributing"],
        "setup_steps": meta["setup_steps"],
        "test_steps": meta["test_steps"],
        "checklist": meta["checklist"],
        "issue_hint": meta.get("issue_hint") or "",
        "clone_note": meta.get("clone_note") or "",
        "learn_links": meta.get("learn_links") or [],
        "context_note": meta.get("context_note") or "",
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
