"""Thin async wrapper around the GitHub REST API.

Used by the backend for heavier operations (fetching trees, file contents,
issues) on behalf of a user. A user token is preferred; otherwise the optional
fallback PAT is used to get a higher unauthenticated rate limit.
"""

from __future__ import annotations

import base64
from contextlib import asynccontextmanager
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

GITHUB_API = "https://api.github.com"

# Labels we treat as beginner-friendly contribution opportunities.
GOOD_FIRST_LABELS = ["good first issue", "help wanted", "good-first-issue"]


class GitHubError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"GitHub API error {status_code}: {message}")


class _RetryableGitHubError(GitHubError):
    """Internal marker for transient (5xx) GitHub responses worth retrying."""


class GitHubService:
    """Async GitHub REST client.

    Use it as an async context manager to reuse a single pooled connection
    across many calls (e.g. during ingestion)::

        async with GitHubService(token) as gh:
            await gh.get_tree(...)

    When used without ``async with``, each request opens (and closes) its own
    short-lived client, preserving backward compatibility.
    """

    def __init__(self, token: str | None = None):
        self.token = token or settings.github_fallback_token or None
        self._client: httpx.AsyncClient | None = None

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def __aenter__(self) -> GitHubService:
        self._client = httpx.AsyncClient(timeout=30, headers=self._headers())
        return self

    async def __aexit__(self, *_exc) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    @asynccontextmanager
    async def _acquire(self):
        """Yield a client: the shared one when in a context, else a temporary."""
        if self._client is not None:
            yield self._client
        else:
            async with httpx.AsyncClient(
                timeout=30, headers=self._headers()
            ) as client:
                yield client

    @retry(
        retry=retry_if_exception_type((httpx.TransportError, _RetryableGitHubError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, max=8),
        reraise=True,
    )
    async def _get(self, path: str, **params) -> Any:
        async with self._acquire() as client:
            resp = await client.get(f"{GITHUB_API}{path}", params=params or None)
        if resp.status_code == 403 and "rate limit" in resp.text.lower():
            raise GitHubError(403, "GitHub rate limit exceeded. Try again later.")
        if resp.status_code >= 500:
            raise _RetryableGitHubError(resp.status_code, resp.text[:300])
        if resp.status_code >= 400:
            raise GitHubError(resp.status_code, resp.text[:300])
        return resp.json()

    async def search_repositories(self, query: str, limit: int = 20) -> list[dict]:
        data = await self._get(
            "/search/repositories",
            q=query,
            sort="stars",
            order="desc",
            per_page=limit,
        )
        results = []
        for item in data.get("items", []):
            results.append(
                {
                    "owner": item["owner"]["login"],
                    "name": item["name"],
                    "full_name": item["full_name"],
                    "description": item.get("description"),
                    "stars": item.get("stargazers_count", 0),
                    "language": item.get("language"),
                    "url": item.get("html_url"),
                }
            )
        return results

    async def get_repo(self, owner: str, name: str) -> dict:
        return await self._get(f"/repos/{owner}/{name}")

    async def get_tree(
        self, owner: str, name: str, branch: str
    ) -> tuple[list[dict], bool]:
        """Return the recursive tree and whether GitHub truncated it."""
        data = await self._get(
            f"/repos/{owner}/{name}/git/trees/{branch}",
            recursive="1",
        )
        nodes = [
            {
                "path": n["path"],
                "type": "dir" if n["type"] == "tree" else "file",
                "size": n.get("size"),
            }
            for n in data.get("tree", [])
        ]
        return nodes, data.get("truncated", False)

    async def get_file_content(
        self, owner: str, name: str, path: str, ref: str | None = None
    ) -> str | None:
        try:
            data = await self._get(f"/repos/{owner}/{name}/contents/{path}", ref=ref)
        except GitHubError as exc:
            if exc.status_code == 404:
                return None
            raise
        if isinstance(data, list):  # directory
            return None
        if data.get("encoding") == "base64" and data.get("content"):
            return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        return data.get("content")

    async def get_docs(self, owner: str, name: str, branch: str) -> dict:
        readme = None
        for candidate in ("README.md", "README.rst", "README"):
            readme = await self.get_file_content(owner, name, candidate, branch)
            if readme:
                break
        contributing = None
        for candidate in ("CONTRIBUTING.md", ".github/CONTRIBUTING.md"):
            contributing = await self.get_file_content(owner, name, candidate, branch)
            if contributing:
                break
        return {"readme": readme, "contributing": contributing}

    async def list_issues(
        self,
        owner: str,
        name: str,
        labels: list[str] | None = None,
        state: str = "open",
        limit: int = 30,
    ) -> list[dict]:
        params: dict[str, Any] = {"state": state, "per_page": limit}
        if labels:
            params["labels"] = ",".join(labels)
        data = await self._get(f"/repos/{owner}/{name}/issues", **params)
        issues = []
        for item in data:
            if "pull_request" in item:  # exclude PRs
                continue
            issues.append(_format_issue(item))
        return issues

    async def get_issue(self, owner: str, name: str, number: int) -> dict:
        item = await self._get(f"/repos/{owner}/{name}/issues/{number}")
        return _format_issue(item)

    # -----------------------------------------------------------------------
    # Write operations (require a user token with the `repo` scope)
    #
    # Writes are intentionally NOT retried: most are non-idempotent (fork,
    # create branch, put file, open PR) so a blind retry after a network error
    # could duplicate side effects.
    # -----------------------------------------------------------------------
    async def _send(self, method: str, path: str, json: dict | None = None) -> Any:
        async with self._acquire() as client:
            resp = await client.request(method, f"{GITHUB_API}{path}", json=json)
        if resp.status_code == 403 and "rate limit" in resp.text.lower():
            raise GitHubError(403, "GitHub rate limit exceeded. Try again later.")
        if resp.status_code >= 400:
            raise GitHubError(resp.status_code, resp.text[:300])
        return resp.json() if resp.content else {}

    async def get_authenticated_user(self) -> dict:
        return await self._get("/user")

    async def fork_repo(self, owner: str, name: str) -> dict:
        """Create (or return existing) fork under the authenticated user."""
        return await self._send("POST", f"/repos/{owner}/{name}/forks")

    async def get_branch_sha(self, owner: str, name: str, branch: str) -> str:
        data = await self._get(f"/repos/{owner}/{name}/git/ref/heads/{branch}")
        return data["object"]["sha"]

    async def create_branch(
        self, owner: str, name: str, new_branch: str, base_sha: str
    ) -> None:
        try:
            await self._send(
                "POST",
                f"/repos/{owner}/{name}/git/refs",
                {"ref": f"refs/heads/{new_branch}", "sha": base_sha},
            )
        except GitHubError as exc:
            # 422 = ref already exists; treat as idempotent.
            if exc.status_code != 422:
                raise

    async def put_file(
        self,
        owner: str,
        name: str,
        path: str,
        content: str,
        message: str,
        branch: str,
        sha: str | None = None,
    ) -> dict:
        payload: dict[str, Any] = {
            "message": message,
            "content": base64.b64encode(content.encode()).decode(),
            "branch": branch,
        }
        if sha:
            payload["sha"] = sha
        return await self._send(
            "PUT", f"/repos/{owner}/{name}/contents/{path}", payload
        )

    async def get_content_sha(
        self, owner: str, name: str, path: str, branch: str
    ) -> str | None:
        try:
            data = await self._get(
                f"/repos/{owner}/{name}/contents/{path}", ref=branch
            )
        except GitHubError as exc:
            if exc.status_code == 404:
                return None
            raise
        if isinstance(data, dict):
            return data.get("sha")
        return None

    async def create_pull_request(
        self,
        owner: str,
        name: str,
        title: str,
        head: str,
        base: str,
        body: str,
        draft: bool = False,
    ) -> dict:
        return await self._send(
            "POST",
            f"/repos/{owner}/{name}/pulls",
            {
                "title": title,
                "head": head,
                "base": base,
                "body": body,
                "draft": draft,
                "maintainer_can_modify": True,
            },
        )


def _format_issue(item: dict) -> dict:
    return {
        "number": item["number"],
        "title": item["title"],
        "body": item.get("body"),
        "labels": [
            label["name"] if isinstance(label, dict) else label
            for label in item.get("labels", [])
        ],
        "state": item.get("state", "open"),
        "url": item.get("html_url", ""),
        "comments": item.get("comments", 0),
        "created_at": item.get("created_at", ""),
    }
