"""Local IDE clone, path limits, and accept/reject edits."""

from __future__ import annotations

import json
import stat
import subprocess
from pathlib import Path

import pytest

from app.agent.mentor import MentorAgent
from app.agent.prompts import workspace_prompt
from app.core.security import ToolError
from app.llm.client import LlmResult, ToolCall
from app.tools.workspace_tools import propose_workspace_edit
from app.workspace.context import reset_workspace_id, set_workspace_id
from app.workspace.paths import assert_outside_source, source_roots
from app.workspace.store import (
    create_catalog_workspace,
    create_workspace_from_path,
    read_file,
    workspace_root,
)


def _origin(path: Path) -> Path:
    path.mkdir()
    subprocess.check_call(["git", "init", str(path)])
    subprocess.check_call(["git", "-C", str(path), "config", "user.email", "test@example.com"])
    subprocess.check_call(["git", "-C", str(path), "config", "user.name", "Test"])
    (path / "README.md").write_text("hello wallet\n", encoding="utf-8")
    (path / "src").mkdir()
    (path / "src" / "lib.rs").write_text("fn fee() -> u64 {\n    1\n}\n", encoding="utf-8")
    subprocess.check_call(["git", "-C", str(path), "add", "."])
    subprocess.check_call(["git", "-C", str(path), "commit", "-m", "init"])
    return path


def _repo(workspace_id: str) -> Path:
    return workspace_root() / workspace_id / "repo"


def test_workspace_root_is_outside_the_source_tree():
    root = workspace_root()
    for source in source_roots():
        assert root != source
        assert source not in root.parents
    inside = next(iter(source_roots()))
    with pytest.raises(ToolError):
        assert_outside_source(inside)


def test_clone_is_shallow_and_hooks_do_not_run(tmp_path: Path):
    origin = _origin(tmp_path / "origin")
    created = create_workspace_from_path("bdk", origin)
    repo = _repo(created["id"])
    hooks = subprocess.check_output(["git", "-C", str(repo), "config", "--get", "core.hooksPath"], text=True)
    assert hooks.strip() == "/dev/null"
    shallow = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "--is-shallow-repository"],
        text=True,
    )
    assert shallow.strip() == "true"
    hook = repo / ".git" / "hooks" / "post-checkout"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text("#!/bin/sh\ntouch \"$GIT_DIR/../HOOK_RAN\"\n", encoding="utf-8")
    hook.chmod(hook.stat().st_mode | stat.S_IEXEC)
    subprocess.check_call(["git", "-C", str(repo), "checkout", "--", "."])
    assert not (repo / "HOOK_RAN").exists()
    assert read_file(created["id"], "README.md")["text"] == "hello wallet\n"


def test_symlink_and_escape_are_refused(tmp_path: Path, client):
    origin = _origin(tmp_path / "origin")
    created = create_workspace_from_path("rust-bitcoin", origin)
    repo = _repo(created["id"])
    secret = tmp_path / "secret.txt"
    secret.write_text("secret", encoding="utf-8")
    (repo / "leak.txt").symlink_to(secret)
    leaked = client.get(f"/api/v1/workspaces/{created['id']}/file", params={"path": "leak.txt"})
    assert leaked.status_code == 400
    escaped = client.get(f"/api/v1/workspaces/{created['id']}/file", params={"path": "../secret.txt"})
    assert escaped.status_code == 400
    git_meta = client.get(f"/api/v1/workspaces/{created['id']}/file", params={"path": ".git/config"})
    assert git_meta.status_code == 400
    saved = client.post(
        f"/api/v1/workspaces/{created['id']}/file",
        json={"path": "src/lib.rs", "text": "fn fee() -> u64 {\n    2\n}\n"},
    )
    assert saved.status_code == 200
    assert "2" in read_file(created["id"], "src/lib.rs")["text"]


def test_catalog_clone_rejects_other_projects_and_urls(client):
    refused = client.post("/api/v1/workspaces", json={"project": "bitcoin-core"})
    assert refused.status_code == 400
    assert "BDK" in refused.json()["detail"]
    extra = client.post("/api/v1/workspaces", json={"project": "bdk", "url": "https://example.com/repo.git"})
    assert extra.status_code == 422
    listed = client.get("/api/v1/workspaces/projects")
    assert listed.status_code == 200
    slugs = [item["slug"] for item in listed.json()["projects"]]
    assert slugs == ["bdk", "rust-bitcoin"]
    with pytest.raises(ToolError):
        create_catalog_workspace("bitcoin-core")


def test_search_guide_mode_and_accept_reject(tmp_path: Path, client):
    origin = _origin(tmp_path / "origin")
    created = create_workspace_from_path("bdk", origin)
    found = client.post(
        f"/api/v1/workspaces/{created['id']}/search",
        json={"query": "fee"},
    )
    assert found.status_code == 200
    assert found.json()["matches"][0]["path"] == "src/lib.rs"
    explained = client.post(
        "/api/v1/chat",
        json={
            "message": "Explain this file",
            "workspace_id": created["id"],
            "open_path": "README.md",
        },
    )
    assert explained.status_code == 200
    body = explained.json()
    assert body["mode"] == "guide"
    assert "hello wallet" in body["message"]["content"]
    assert "Guide mode" in body["message"]["content"]
    prompt = workspace_prompt(created)
    assert "Do not commit" in prompt
    assert "bitcoindevkit/bdk" in prompt

    token = set_workspace_id(created["id"])
    try:
        proposed = propose_workspace_edit(
            {"path": "README.md", "old": "hello wallet", "new": "hello contributor"}
        )
    finally:
        reset_workspace_id(token)
    assert proposed["applied"] is False
    assert read_file(created["id"], "README.md")["text"] == "hello wallet\n"
    pending = client.get(f"/api/v1/workspaces/{created['id']}/edits")
    assert pending.status_code == 200
    edit_id = pending.json()["edits"][0]["id"]
    rejected = client.post(f"/api/v1/workspaces/{created['id']}/edits/{edit_id}/reject")
    assert rejected.status_code == 200
    assert read_file(created["id"], "README.md")["text"] == "hello wallet\n"

    token = set_workspace_id(created["id"])
    try:
        again = propose_workspace_edit(
            {"path": "README.md", "old": "hello wallet", "new": "hello contributor"}
        )
    finally:
        reset_workspace_id(token)
    accepted = client.post(f"/api/v1/workspaces/{created['id']}/edits/{again['edit_id']}/accept")
    assert accepted.status_code == 200
    assert read_file(created["id"], "README.md")["text"] == "hello contributor\n"
    missing = client.post(f"/api/v1/workspaces/{created['id']}/commit")
    assert missing.status_code == 404


class _EditModel:
    configured = True

    def __init__(self):
        self.calls = 0

    def complete(self, messages, tools):
        self.calls += 1
        if self.calls == 1:
            raw = json.dumps({"path": "README.md", "old": "hello wallet", "new": "hello reviewer"})
            call = ToolCall(
                id="edit_1",
                name="propose_workspace_edit",
                arguments=json.loads(raw),
                raw_arguments=raw,
            )
            return LlmResult(
                content="",
                tool_calls=[call],
                assistant_message={
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "edit_1",
                            "type": "function",
                            "function": {"name": "propose_workspace_edit", "arguments": raw},
                        }
                    ],
                },
            )
        return LlmResult(
            content="I proposed a diff. It is not saved until you accept it.",
            assistant_message={"role": "assistant", "content": "proposed"},
        )


def test_model_propose_does_not_write_until_accept(tmp_path: Path, client):
    origin = _origin(tmp_path / "origin")
    created = create_workspace_from_path("bdk", origin)
    original = client.app.state.agent
    client.app.state.agent = MentorAgent(_EditModel(), client.app.state.tools)
    try:
        response = client.post(
            "/api/v1/chat",
            json={"message": "Rename the greeting", "workspace_id": created["id"], "open_path": "README.md"},
        )
    finally:
        client.app.state.agent = original
    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "llm"
    assert payload["message"]["tool_trace"][0]["name"] == "propose_workspace_edit"
    assert read_file(created["id"], "README.md")["text"] == "hello wallet\n"
    edit_id = client.get(f"/api/v1/workspaces/{created['id']}/edits").json()["edits"][0]["id"]
    accepted = client.post(f"/api/v1/workspaces/{created['id']}/edits/{edit_id}/accept")
    assert accepted.status_code == 200
    assert read_file(created["id"], "README.md")["text"] == "hello reviewer\n"
