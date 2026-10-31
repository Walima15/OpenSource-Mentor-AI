"""A small GitHub REST client.

URLs are built only from validated owner, repo, and path segments. Redirects
are not followed. The token, when set, is an Authorization header and is not
written into tool results.
"""

from __future__ import annotations

import base64
from typing import Any
from urllib.parse import quote

import httpx

from app.core.security import (
    ToolError,
    validate_git_path,
    validate_git_ref,
    validate_issue_label,
    validate_owner_repo,
)

_API = "https://api.github.com"


class GitHubError(ToolError):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class GitHubClient:
    def __init__(self, token: str = "", transport: httpx.BaseTransport | None = None):
        if any(char in token for char in "\r\n\x00"):
            raise ValueError("GitHub token must not contain control characters")
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "osma-mentor",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._client = httpx.Client(
            base_url=_API,
            headers=headers,
            timeout=httpx.Timeout(20.0, connect=5.0),
            follow_redirects=False,
            trust_env=False,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        accept: str | None = None,
    ) -> httpx.Response:
        if not path.startswith("/") or path.startswith("//") or "://" in path:
            raise GitHubError("Refusing to request a non-API path")
        headers = {"Accept": accept} if accept else None
        try:
            response = self._client.request(method, path, params=params, headers=headers)
        except httpx.HTTPError:
            raise GitHubError("GitHub request failed") from None
        if response.status_code in {301, 302, 303, 307, 308}:
            raise GitHubError(
                "GitHub returned a redirect that OSMA will not follow",
                response.status_code,
            )
        if response.status_code == 404:
            raise GitHubError("GitHub could not find that resource", 404)
        if response.status_code in {403, 429}:
            raise GitHubError(
                "GitHub rate limit reached. Set GITHUB_TOKEN for a higher limit, or wait and retry.",
                response.status_code,
            )
        if response.status_code >= 400:
            raise GitHubError(f"GitHub request failed ({response.status_code})", response.status_code)
        return response

    def search_issues(self, owner: str, repo: str, label: str, limit: int = 10) -> list[dict]:
        owner, repo = validate_owner_repo(owner, repo)
        label = validate_issue_label(label)
        query = f'repo:{owner}/{repo} is:issue is:open label:"{label}"'
        payload = self._request(
            "GET",
            "/search/issues",
            params={
                "q": query,
                "sort": "updated",
                "order": "desc",
                "per_page": str(max(1, min(limit, 20))),
            },
        ).json()
        issues = []
        for item in payload.get("items", []):
            if item.get("pull_request"):
                continue
            issues.append(_issue_summary(item))
        return issues

    def get_repo(self, owner: str, repo: str) -> dict:
        owner, repo = validate_owner_repo(owner, repo)
        data = self._request("GET", f"/repos/{owner}/{repo}").json()
        license_info = data.get("license") or {}
        return {
            "full_name": data.get("full_name") or f"{owner}/{repo}",
            "description": data.get("description") or "",
            "default_branch": data.get("default_branch") or "master",
            "language": data.get("language"),
            "stars": data.get("stargazers_count"),
            "open_issues": data.get("open_issues_count"),
            "topics": data.get("topics") or [],
            "html_url": data.get("html_url") or f"https://github.com/{owner}/{repo}",
            "license": license_info.get("spdx_id"),
        }

    def get_readme(self, owner: str, repo: str) -> str:
        owner, repo = validate_owner_repo(owner, repo)
        response = self._request(
            "GET",
            f"/repos/{owner}/{repo}/readme",
            accept="application/vnd.github.raw",
        )
        return response.text[:8_000]

    def list_root(self, owner: str, repo: str) -> list[dict]:
        owner, repo = validate_owner_repo(owner, repo)
        data = self._request("GET", f"/repos/{owner}/{repo}/contents/").json()
        if not isinstance(data, list):
            return []
        entries = []
        for item in data[:40]:
            entries.append(
                {
                    "name": item.get("name"),
                    "type": item.get("type"),
                    "path": item.get("path"),
                }
            )
        return entries

    def get_file(self, owner: str, repo: str, path: str, ref: str | None = None) -> dict:
        owner, repo = validate_owner_repo(owner, repo)
        path = validate_git_path(path)
        ref = validate_git_ref(ref)
        quoted = quote(path, safe="/")
        params = {"ref": ref} if ref else None
        data = self._request("GET", f"/repos/{owner}/{repo}/contents/{quoted}", params=params).json()
        if isinstance(data, list):
            raise GitHubError("That path is a directory, not a file")
        return _file_payload(data, path)

    def get_issue(self, owner: str, repo: str, number: int) -> dict:
        owner, repo = validate_owner_repo(owner, repo)
        data = self._request("GET", f"/repos/{owner}/{repo}/issues/{number}").json()
        summary = _issue_summary(data)
        summary["is_pull_request"] = "pull_request" in data
        return summary

    def get_pull(self, owner: str, repo: str, number: int) -> dict:
        owner, repo = validate_owner_repo(owner, repo)
        data = self._request("GET", f"/repos/{owner}/{repo}/pulls/{number}").json()
        user = data.get("user") or {}
        return {
            "number": data.get("number"),
            "title": data.get("title") or "",
            "body": (data.get("body") or "")[:4_000],
            "state": data.get("state"),
            "draft": bool(data.get("draft")),
            "user": user.get("login"),
            "html_url": data.get("html_url"),
            "base": (data.get("base") or {}).get("ref"),
            "head": (data.get("head") or {}).get("ref"),
            "head_sha": (data.get("head") or {}).get("sha"),
            "commits": data.get("commits"),
            "changed_files": data.get("changed_files"),
            "additions": data.get("additions"),
            "deletions": data.get("deletions"),
        }

    def get_pull_files(self, owner: str, repo: str, number: int) -> list[dict]:
        owner, repo = validate_owner_repo(owner, repo)
        data = self._request(
            "GET",
            f"/repos/{owner}/{repo}/pulls/{number}/files",
            params={"per_page": "30"},
        ).json()
        files = []
        for item in data if isinstance(data, list) else []:
            patch = item.get("patch") or ""
            files.append(
                {
                    "filename": item.get("filename"),
                    "status": item.get("status"),
                    "additions": item.get("additions"),
                    "deletions": item.get("deletions"),
                    "patch": patch[:1_500],
                }
            )
        return files

    def get_pull_diff(self, owner: str, repo: str, number: int) -> str:
        owner, repo = validate_owner_repo(owner, repo)
        response = self._request(
            "GET",
            f"/repos/{owner}/{repo}/pulls/{number}",
            accept="application/vnd.github.diff",
        )
        return response.text[:20_000]


def _issue_summary(item: dict[str, Any]) -> dict:
    labels = []
    for label in item.get("labels") or []:
        if isinstance(label, dict) and label.get("name"):
            labels.append(label["name"])
        elif isinstance(label, str):
            labels.append(label)
    return {
        "number": item.get("number"),
        "title": item.get("title") or "",
        "url": item.get("html_url"),
        "state": item.get("state"),
        "comments": item.get("comments") or 0,
        "updated_at": item.get("updated_at"),
        "labels": labels,
        "body": (item.get("body") or "")[:1_500],
    }


def _file_payload(data: dict, path: str) -> dict:
    html_url = data.get("html_url")
    if data.get("encoding") == "none" or "content" not in data:
        return {
            "path": path,
            "truncated": True,
            "text": "",
            "html_url": html_url,
            "note": "GitHub did not return file contents (the file may be too large). Read it on GitHub.",
        }
    try:
        raw = base64.b64decode(data.get("content") or "")
    except (ValueError, TypeError):
        raise GitHubError("GitHub file contents were not valid base64") from None
    text = raw.decode("utf-8", errors="replace")
    truncated = len(text) > 12_000
    return {
        "path": path,
        "truncated": truncated,
        "text": text[:12_000],
        "html_url": html_url,
        "size": data.get("size"),
    }
