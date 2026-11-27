"""Input checks, URL allowlists, and log redaction.

The GitHub token and the LLM key stay in the process environment. They are sent
only as request headers to the configured hosts. They are never written to the
database, never placed in a job payload (OSMA has no job queue), and a logging
filter strips common token shapes if they ever reach a log line.
"""

from __future__ import annotations

import ipaddress
import logging
import re
from urllib.parse import urlparse

_OWNER = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")
_REPO = re.compile(r"^[A-Za-z0-9._-]{1,100}$")
_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
_REF = re.compile(r"^[A-Za-z0-9._/-]{1,120}$")
_LABEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _.:-]{0,50}$")

_SECRET_PATTERNS = (
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"Bearer\s+\S+", re.IGNORECASE),
)

_METADATA_HOSTS = frozenset(
    {
        "169.254.169.254",
        "metadata.google.internal",
        "metadata.internal",
    }
)


class ToolError(Exception):
    """A tool rejected its arguments or an upstream call failed safely."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def redact(text: str) -> str:
    redacted = text
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub("[redacted]", redacted)
    return redacted


class RedactFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    key: redact(value) if isinstance(value, str) else value
                    for key, value in record.args.items()
                }
            else:
                record.args = tuple(
                    redact(arg) if isinstance(arg, str) else arg for arg in record.args
                )
        return True


def no_control_lines(value: str, field: str) -> str:
    if any(char in value for char in "\r\n\x00"):
        raise ValueError(f"{field} must not contain newlines or null bytes")
    return value.strip()


def validate_owner_repo(owner: str, repo: str) -> tuple[str, str]:
    owner = owner.strip()
    repo = repo.strip()
    if not _OWNER.fullmatch(owner):
        raise ToolError("GitHub owner is not a valid username or organization")
    if repo in {".", ".."} or not _REPO.fullmatch(repo):
        raise ToolError("GitHub repository name is not valid")
    return owner, repo


def validate_slug(slug: str) -> str:
    slug = slug.strip().lower()
    if not _SLUG.fullmatch(slug):
        raise ToolError("Unknown project slug")
    return slug


def validate_git_path(path: str) -> str:
    path = path.strip()
    if not path or len(path) > 400 or "\x00" in path:
        raise ToolError("File path is empty or too long")
    if path.startswith("/") or path.startswith("\\") or "\\" in path or "://" in path:
        raise ToolError("File path must be a relative path inside the repository")
    parts = path.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ToolError("File path must stay inside the repository")
    return path


def validate_git_ref(ref: str | None) -> str | None:
    if ref is None or ref == "":
        return None
    if ".." in ref or not _REF.fullmatch(ref):
        raise ToolError("Git ref is not valid")
    return ref


def validate_issue_label(label: str) -> str:
    label = label.strip()
    if not _LABEL.fullmatch(label):
        raise ToolError("Issue label is not valid")
    return label


def validate_llm_base_url(url: str) -> str:
    """Allow HTTPS LLM endpoints, and HTTP only for a local model server."""
    raw = url.strip()
    if not raw or any(char in raw for char in "\r\n\x00"):
        raise ValueError("OPENAI_BASE_URL is empty or contains control characters")
    parsed = urlparse(raw)
    if parsed.username or parsed.password:
        raise ValueError("OPENAI_BASE_URL must not contain credentials")
    host = (parsed.hostname or "").lower().rstrip(".")
    if not host or parsed.scheme not in {"http", "https"}:
        raise ValueError("OPENAI_BASE_URL must be an http(s) URL")
    if _llm_host_blocked(host):
        raise ValueError("OPENAI_BASE_URL host is not allowed")
    if parsed.scheme == "http" and host not in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("Plain HTTP is only allowed for a localhost LLM server")
    return raw.rstrip("/")


def _llm_host_blocked(host: str) -> bool:
    if host in _METADATA_HOSTS:
        return True
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    if ip.is_loopback:
        return False
    return bool(ip.is_link_local or ip.is_multicast or ip.is_unspecified or ip.is_reserved)
