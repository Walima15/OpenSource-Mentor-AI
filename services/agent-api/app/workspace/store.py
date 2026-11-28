"""Clone catalog repositories into a folder outside the OSMA source tree.

The MVP clones BDK and rust-bitcoin only. The clone is shallow, git hooks are
pointed at ``/dev/null``, and no user-supplied URL is accepted.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import os
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.content.loader import PROJECTS
from app.content.review_guides import checklist_for
from app.core.config import get_settings
from app.core.security import ToolError
from app.workspace.paths import assert_outside_source, locate

IDE_SLUGS = ("bdk", "rust-bitcoin")
_MAX_READ = 100_000
_MAX_EDIT_SIDE = 20_000
_MAX_DIFF = 20_000
_MAX_TREE = 2_000
_MAX_SEARCH_FILES = 4_000
_MAX_MATCHES = 30
_SKIP_WALK = frozenset({".git", "node_modules", "target", "dist", ".next"})

RECOMMENDED_CODE_MODEL = "qwen2.5-coder:1.5b"


def workspace_root() -> Path:
    raw = get_settings().osma_workspace_root.strip()
    path = Path(raw).expanduser() if raw else Path.home() / ".osma" / "workspaces"
    resolved = assert_outside_source(path)
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def list_ide_projects() -> list[dict]:
    items = []
    for slug in IDE_SLUGS:
        project = PROJECTS[slug]
        items.append(
            {
                "slug": project.slug,
                "name": project.name,
                "owner": project.owner,
                "repo": project.repo,
                "language": project.language,
                "summary": project.summary,
                "available": True,
            }
        )
    return items


def list_workspaces() -> list[dict]:
    root = workspace_root()
    found = []
    for child in sorted(root.iterdir(), key=lambda item: item.name):
        if child.is_symlink() or not child.is_dir():
            continue
        meta_path = child / "meta.json"
        if not meta_path.is_file() or meta_path.is_symlink():
            continue
        found.append(_public_meta(_read_json(meta_path)))
    return found


def get_workspace(workspace_id: str) -> dict:
    return _public_meta(_load_meta(workspace_id))


def create_catalog_workspace(slug: str) -> dict:
    if slug not in IDE_SLUGS:
        raise ToolError("This IDE clones BDK and rust-bitcoin only")
    project = PROJECTS.get(slug)
    if project is None:
        raise ToolError("Unknown project")
    existing = next((item for item in list_workspaces() if item["slug"] == slug), None)
    if existing:
        existing["reused"] = True
        return existing
    url = f"https://github.com/{project.owner}/{project.repo}.git"
    return _clone(slug, url)


def create_workspace_from_path(slug: str, source: Path) -> dict:
    """Test helper. The HTTP API does not accept a source path."""

    if slug not in PROJECTS:
        raise ToolError("Unknown project")
    source = source.resolve()
    if not (source / ".git").exists():
        raise ToolError("Source is not a git repository")
    return _clone(slug, str(source))


def tree(workspace_id: str) -> dict:
    repo = _repo(workspace_id)
    entries: list[dict] = []
    for path in _walk(repo):
        entries.append({"path": path.relative_to(repo).as_posix(), "type": "file" if path.is_file() else "dir"})
        if len(entries) >= _MAX_TREE:
            break
    entries.sort(key=lambda item: item["path"])
    return {"entries": entries, "truncated": len(entries) >= _MAX_TREE}


def read_file(workspace_id: str, relative: str) -> dict:
    path = locate(_repo(workspace_id), relative)
    if not path.is_file():
        raise ToolError("File not found")
    data = path.read_bytes()
    if b"\x00" in data[:8_192]:
        return {
            "path": relative,
            "binary": True,
            "truncated": False,
            "text": "",
            "sha256": hashlib.sha256(data).hexdigest(),
        }
    text = data.decode("utf-8", errors="replace")
    truncated = len(text) > _MAX_READ
    shown = text[:_MAX_READ]
    return {
        "path": relative,
        "binary": False,
        "truncated": truncated,
        "text": shown,
        "sha256": hashlib.sha256(shown.encode() if truncated else text.encode()).hexdigest(),
    }


def write_file(workspace_id: str, relative: str, text: str) -> dict:
    if len(text) > 80_000:
        raise ToolError("File is too large to save from the editor")
    if "\x00" in text:
        raise ToolError("File must be text")
    path = locate(_repo(workspace_id), relative)
    if path.exists() and not path.is_file():
        raise ToolError("That path is not a file")
    _atomic_write(path, text)
    return {"path": relative, "sha256": hashlib.sha256(text.encode()).hexdigest()}


def search(workspace_id: str, query: str) -> dict:
    cleaned = query.strip()
    if len(cleaned) < 2 or len(cleaned) > 80 or any(char in cleaned for char in "\r\n\x00"):
        raise ToolError("Search query must be 2 to 80 characters on one line")
    needle = cleaned.lower()
    repo = _repo(workspace_id)
    matches: list[dict] = []
    seen_files = 0
    for path in _walk(repo):
        if not path.is_file():
            continue
        seen_files += 1
        if seen_files > _MAX_SEARCH_FILES or len(matches) >= _MAX_MATCHES:
            break
        try:
            data = path.read_bytes()
        except OSError:
            continue
        if b"\x00" in data[:1_024] or len(data) > 200_000:
            continue
        text = data.decode("utf-8", errors="replace")
        rel = path.relative_to(repo).as_posix()
        for number, line in enumerate(text.splitlines(), start=1):
            if needle in line.lower():
                matches.append({"path": rel, "line": number, "text": line[:200]})
                if len(matches) >= _MAX_MATCHES:
                    break
    return {
        "summary": f"{len(matches)} match(es) for {cleaned}",
        "query": cleaned,
        "matches": matches,
    }


def propose_edit(workspace_id: str, relative: str, old: str, new: str) -> dict:
    if not old:
        raise ToolError("The text to replace is empty")
    if len(old) > _MAX_EDIT_SIDE or len(new) > _MAX_EDIT_SIDE:
        raise ToolError("Edit snippet is too large")
    if "\x00" in old or "\x00" in new:
        raise ToolError("Edit must be text")
    if old == new:
        raise ToolError("Edit does not change the file")
    current = read_file(workspace_id, relative)
    if current.get("binary") or current.get("truncated"):
        raise ToolError("That file cannot be edited from the IDE")
    text = current["text"]
    count = text.count(old)
    if count == 0:
        raise ToolError("That text was not found in the file. Read the file and copy an exact snippet.")
    if count > 1:
        raise ToolError("That snippet appears more than once. Include more surrounding lines.")
    updated = text.replace(old, new, 1)
    diff = _unified(relative, text, updated)
    if len(diff) > _MAX_DIFF:
        raise ToolError("Diff is too large to review. Propose a smaller change.")
    edit_id = str(uuid4())
    record = {
        "id": edit_id,
        "path": relative,
        "diff": diff,
        "new_content": updated,
        "base_sha256": current["sha256"],
        "status": "pending",
    }
    slot = _slot(workspace_id)
    edits = slot / "edits"
    edits.mkdir(parents=True, exist_ok=True)
    target = edits / f"{edit_id}.json"
    _write_json(target, record)
    return {
        "summary": f"Proposed an edit to {relative}. It is not applied until you accept it.",
        "edit_id": edit_id,
        "path": relative,
        "diff": diff,
        "applied": False,
    }


def list_edits(workspace_id: str) -> list[dict]:
    _load_meta(workspace_id)
    edits = _slot(workspace_id) / "edits"
    if not edits.is_dir():
        return []
    pending = []
    for path in sorted(edits.glob("*.json")):
        if path.is_symlink():
            continue
        record = _read_json(path)
        if record.get("status") == "pending":
            pending.append({"id": record["id"], "path": record["path"], "diff": record["diff"], "status": "pending"})
    return pending


def accept_edit(workspace_id: str, edit_id: str) -> dict:
    record, path = _pending(workspace_id, edit_id)
    current = read_file(workspace_id, record["path"])
    if current.get("sha256") != record["base_sha256"]:
        raise ToolError("The file changed after this diff was proposed. Reject it and ask again.")
    write_file(workspace_id, record["path"], record["new_content"])
    record["status"] = "accepted"
    record.pop("new_content", None)
    _write_json(path, record)
    return {"status": "accepted", "path": record["path"]}


def reject_edit(workspace_id: str, edit_id: str) -> dict:
    record, path = _pending(workspace_id, edit_id)
    record["status"] = "rejected"
    record.pop("new_content", None)
    _write_json(path, record)
    return {"status": "rejected", "path": record["path"]}


def _clone(slug: str, source: str) -> dict:
    project = PROJECTS[slug]
    workspace_id = str(uuid4())
    slot = workspace_root() / workspace_id
    repo = slot / "repo"
    template = workspace_root() / "_git_template"
    template.mkdir(parents=True, exist_ok=True)
    slot.mkdir(parents=True, exist_ok=False)
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    command = [
        "git",
        "-c",
        "core.hooksPath=/dev/null",
        "clone",
        "--no-local",
        "--depth",
        "1",
        "--single-branch",
        "--template",
        str(template),
        "-c",
        "core.hooksPath=/dev/null",
        "-c",
        f"safe.directory={repo}",
        "--",
        source,
        str(repo),
    ]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=180,
            env=env,
            check=False,
        )
    except FileNotFoundError:
        shutil.rmtree(slot, ignore_errors=True)
        raise ToolError("git is not installed") from None
    except subprocess.TimeoutExpired:
        shutil.rmtree(slot, ignore_errors=True)
        raise ToolError("Clone timed out") from None
    if completed.returncode != 0 or not repo.is_dir():
        shutil.rmtree(slot, ignore_errors=True)
        raise ToolError("Clone failed")
    hooks = _git_config(repo, "core.hooksPath")
    if hooks != "/dev/null":
        shutil.rmtree(slot, ignore_errors=True)
        raise ToolError("Refusing a clone that did not disable git hooks")
    meta = {
        "id": workspace_id,
        "slug": project.slug,
        "name": project.name,
        "owner": project.owner,
        "repo": project.repo,
        "created_at": datetime.now(UTC).isoformat(),
    }
    _write_json(slot / "meta.json", meta)
    public = _public_meta(meta)
    public["reused"] = False
    return public


def _public_meta(meta: dict) -> dict:
    project = PROJECTS[meta["slug"]]
    return {
        "id": meta["id"],
        "slug": project.slug,
        "name": project.name,
        "owner": project.owner,
        "repo": project.repo,
        "summary": project.summary,
        "language": project.language,
        "created_at": meta.get("created_at"),
        "contributing": list(project.contributing),
        "test_steps": list(project.test_steps),
        "checklist": checklist_for(project.slug),
        "recommended_model": RECOMMENDED_CODE_MODEL,
    }


def _repo(workspace_id: str) -> Path:
    _load_meta(workspace_id)
    repo = _slot(workspace_id) / "repo"
    if not repo.is_dir() or repo.is_symlink():
        raise ToolError("Workspace clone is missing")
    return repo


def _slot(workspace_id: str) -> Path:
    if "/" in workspace_id or "\\" in workspace_id or workspace_id in {".", ".."}:
        raise ToolError("Unknown workspace")
    slot = workspace_root() / workspace_id
    root = workspace_root()
    try:
        slot.resolve().relative_to(root)
    except ValueError:
        raise ToolError("Unknown workspace") from None
    if slot.is_symlink() or not slot.is_dir():
        raise ToolError("Unknown workspace")
    return slot


def _load_meta(workspace_id: str) -> dict:
    meta_path = _slot(workspace_id) / "meta.json"
    if not meta_path.is_file() or meta_path.is_symlink():
        raise ToolError("Unknown workspace")
    return _read_json(meta_path)


def _pending(workspace_id: str, edit_id: str) -> tuple[dict, Path]:
    if len(edit_id) > 80 or any(char in edit_id for char in "/\\.\x00"):
        raise ToolError("Unknown edit")
    path = _slot(workspace_id) / "edits" / f"{edit_id}.json"
    if path.is_symlink() or not path.is_file():
        raise ToolError("Unknown edit")
    try:
        path.resolve().relative_to(_slot(workspace_id) / "edits")
    except ValueError:
        raise ToolError("Unknown edit") from None
    record = _read_json(path)
    if record.get("status") != "pending":
        raise ToolError("That edit is no longer pending")
    return record, path


def _walk(repo: Path):
    for dirpath, dirnames, filenames in os.walk(repo, followlinks=False):
        current = Path(dirpath)
        dirnames[:] = sorted(name for name in dirnames if name not in _SKIP_WALK and not (current / name).is_symlink())
        if current != repo:
            yield current
        for name in sorted(filenames):
            path = current / name
            if path.is_symlink():
                continue
            yield path


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.parent / f".{path.name}.osma-tmp"
    if tmp.is_symlink():
        raise ToolError("Refusing to write through a symlink")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def _unified(relative: str, old: str, new: str) -> str:
    old_lines = old.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)
    diff = "".join(
        difflib.unified_diff(old_lines, new_lines, fromfile=f"a/{relative}", tofile=f"b/{relative}")
    )
    if not diff.endswith("\n"):
        diff += "\n"
    return diff


def _git_config(repo: Path, key: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), "config", "--get", key],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    return completed.stdout.strip()


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload), encoding="utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)
