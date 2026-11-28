"""Keep IDE file access inside one local clone."""

from __future__ import annotations

from pathlib import Path

from app.core.security import ToolError, validate_git_path

_SKIP_DIRS = frozenset({".git", "node_modules", "target", "dist", ".next"})


def source_roots() -> tuple[Path, ...]:
    """Directories that hold OSMA's own source. Clones must not land in them.

    In a full checkout the API lives at ``services/agent-api`` and the git
    root is its parent. In the API container the files live at ``/app`` and
    there is no monorepo parent to protect.
    """

    api_root = Path(__file__).resolve().parents[2]
    roots = [api_root]
    parent = api_root.parent
    if (parent / "apps" / "web").is_dir() and (parent / "services").is_dir():
        roots.append(parent)
    return tuple(roots)


def assert_outside_source(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    for root in source_roots():
        if resolved == root or root in resolved.parents:
            raise ToolError("Workspace directory must be outside the OSMA source tree")
    return resolved


def locate(repo: Path, relative: str) -> Path:
    """Resolve ``relative`` inside ``repo`` and refuse escapes and symlinks."""

    relative = validate_git_path(relative)
    parts = relative.split("/")
    if any(part in _SKIP_DIRS or part == ".git" for part in parts):
        raise ToolError("That path is not available in the IDE")
    root = repo.resolve()
    current = root
    for part in parts:
        if part in _SKIP_DIRS:
            raise ToolError("That path is not available in the IDE")
        current = current / part
        if current.is_symlink():
            raise ToolError("Symlinks are not followed")
        try:
            current.relative_to(root)
        except ValueError:
            raise ToolError("File path must stay inside the workspace") from None
    if current.exists():
        resolved = current.resolve()
        try:
            resolved.relative_to(root)
        except ValueError:
            raise ToolError("File path must stay inside the workspace") from None
        if resolved.is_symlink():
            raise ToolError("Symlinks are not followed")
    return current
