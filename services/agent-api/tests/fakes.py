"""In-memory GitHub stand-in for tool tests."""

from __future__ import annotations


class FakeGitHub:
    def __init__(self, *, issue_title: str = "Document the fee estimator", issue_body: str = "Add a comment."):
        self.issue_title = issue_title
        self.issue_body = issue_body

    def search_issues(self, owner: str, repo: str, label: str, limit: int = 10) -> list[dict]:
        return [
            {
                "number": 42,
                "title": self.issue_title,
                "url": f"https://github.com/{owner}/{repo}/issues/42",
                "state": "open",
                "comments": 1,
                "updated_at": "2026-01-01T00:00:00Z",
                "labels": [label],
                "body": self.issue_body,
            }
        ]

    def get_repo(self, owner: str, repo: str) -> dict:
        return {
            "full_name": f"{owner}/{repo}",
            "description": "A Bitcoin project",
            "default_branch": "master",
            "language": "Rust",
            "stars": 10,
            "open_issues": 3,
            "topics": ["bitcoin"],
            "html_url": f"https://github.com/{owner}/{repo}",
            "license": "MIT",
        }

    def get_readme(self, owner: str, repo: str) -> str:
        return f"# {owner}/{repo}\n\nBuild with the project README."

    def list_root(self, owner: str, repo: str) -> list[dict]:
        return [{"name": "README.md", "type": "file", "path": "README.md"}]

    def get_file(self, owner: str, repo: str, path: str, ref: str | None = None) -> dict:
        return {
            "path": path,
            "truncated": False,
            "text": f"// {path} in {owner}/{repo} ref={ref}\nfn fee() {{}}",
            "html_url": f"https://github.com/{owner}/{repo}/blob/master/{path}",
            "size": 20,
        }

    def get_issue(self, owner: str, repo: str, number: int) -> dict:
        return {
            "number": number,
            "title": self.issue_title,
            "url": f"https://github.com/{owner}/{repo}/issues/{number}",
            "state": "open",
            "comments": 0,
            "updated_at": "2026-01-01T00:00:00Z",
            "labels": [],
            "body": self.issue_body,
            "is_pull_request": False,
        }

    def get_pull(self, owner: str, repo: str, number: int) -> dict:
        return {
            "number": number,
            "title": "wallet: explain change outputs",
            "body": "Adds a comment and a test.",
            "state": "open",
            "draft": False,
            "user": "contributor",
            "html_url": f"https://github.com/{owner}/{repo}/pull/{number}",
            "base": "master",
            "head": "docs",
            "head_sha": "abc123def456",
            "commits": 1,
            "changed_files": 1,
            "additions": 4,
            "deletions": 0,
        }

    def get_pull_files(self, owner: str, repo: str, number: int) -> list[dict]:
        return [
            {
                "filename": "src/wallet/wallet.cpp",
                "status": "modified",
                "additions": 4,
                "deletions": 0,
                "patch": "@@ comment",
            }
        ]

    def get_pull_diff(self, owner: str, repo: str, number: int) -> str:
        return (
            "diff --git a/src/wallet/wallet.cpp b/src/wallet/wallet.cpp\n"
            "--- a/src/wallet/wallet.cpp\n"
            "+++ b/src/wallet/wallet.cpp\n"
            "@@ -1 +1,2 @@\n"
            "+// Change is an output, not a fee.\n"
        )
