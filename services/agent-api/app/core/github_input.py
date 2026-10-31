"""Validators for user-supplied GitHub identifiers and repository paths."""

from __future__ import annotations

import re

_GITHUB_NAME = re.compile(r"^[A-Za-z0-9_.-]+$")
_WINDOWS_DRIVE = re.compile(r"^[A-Za-z]:")


def validate_github_name(value: str) -> str:
    """Accept a GitHub owner or repository name, rejecting path tricks."""
    if (
        not _GITHUB_NAME.fullmatch(value)
        or ".." in value
        or value in {".", ".."}
    ):
        raise ValueError("invalid GitHub owner or repository name")
    return value


def validate_repo_file_path(value: str) -> str:
    """Accept a relative path inside a repository.

    Rejects absolute paths, traversal, git metadata, and workflow files.
    """
    path = value.strip().replace("\\", "/")
    if (
        not path
        or path.startswith("/")
        or path.startswith("~")
        or _WINDOWS_DRIVE.match(path)
        or "\x00" in path
    ):
        raise ValueError("absolute or empty file paths are not allowed")
    parts = [part for part in path.split("/") if part not in {"", "."}]
    if not parts or any(part == ".." for part in parts):
        raise ValueError("path traversal is not allowed")
    lowered = [part.lower() for part in parts]
    if ".git" in lowered:
        raise ValueError("git metadata paths are not allowed")
    for index in range(len(lowered) - 1):
        if lowered[index] == ".github" and lowered[index + 1] == "workflows":
            raise ValueError("GitHub workflow paths are not allowed")
    return "/".join(parts)
