"""Issue, repository, plan, and review tools."""

from __future__ import annotations

import httpx
import pytest

from app.core.security import ToolError
from app.github.client import GitHubClient, GitHubError
from app.tools.github_tools import (
    explain_file,
    explain_repository,
    find_good_first_issues,
    plan_contribution,
    review_diff,
    review_pull_request,
)
from tests.fakes import FakeGitHub

TOKEN = "ghp_" + ("a" * 36)


def test_find_issues_uses_project_labels():
    result = find_good_first_issues(FakeGitHub(), {"project": "rust-bitcoin", "limit": 3})
    assert result["owner"] == "rust-bitcoin"
    assert result["repo"] == "rust-bitcoin"
    assert result["issues"][0]["number"] == 42
    assert "test" in result["issues"][0]["why"].lower()


def test_explain_repository_includes_code_map():
    result = explain_repository(FakeGitHub(), {"project": "bdk"})
    assert result["github"]["full_name"] == "bitcoindevkit/bdk"
    assert any("bdk_wallet" in item["path"] for item in result["code_map"])
    assert "README" in result["readme_excerpt"]


def test_explain_file_rejects_path_traversal():
    with pytest.raises(ToolError):
        explain_file(FakeGitHub(), {"owner": "bitcoin", "repo": "bitcoin", "path": "../secrets"})
    with pytest.raises(ToolError):
        explain_file(FakeGitHub(), {"owner": "bitcoin", "repo": "bitcoin", "path": "/etc/passwd"})


def test_explain_file_returns_hint_and_text():
    result = explain_file(
        FakeGitHub(),
        {"owner": "bitcoin", "repo": "bitcoin", "path": "src/validation.cpp"},
    )
    assert "validation" in result["text"]
    assert "consensus" in result["hint"].lower()


def test_plan_warns_on_consensus_and_lists_steps():
    fake = FakeGitHub(issue_title="Change the block subsidy", issue_body="This is a consensus inflation change.")
    result = plan_contribution(
        fake,
        {"owner": "bitcoin", "repo": "bitcoin", "issue_number": 9, "goal": "change the subsidy"},
    )
    assert result["warnings"]
    assert "consensus" in result["warnings"][0].lower()
    titles = [step["title"] for step in result["steps"]]
    assert "Test" in titles
    assert "Open the pull request" in titles


def test_review_pull_request_includes_ack_rules_and_does_not_ack():
    result = review_pull_request(FakeGitHub(), {"owner": "bitcoin", "repo": "bitcoin", "number": 10})
    checklist = " ".join(result["checklist"])
    assert "Concept ACK" in checklist
    assert "Do not ACK" in result["ack_rule"]
    assert "ACK" not in result["summary"] or "Review material" in result["summary"]
    assert result["pull"]["head_sha"] == "abc123def456"
    assert "wallet.cpp" in result["diff_excerpt"]


def test_review_diff_lists_files():
    diff = "diff --git a/src/policy/fees.cpp b/src/policy/fees.cpp\n+fee\n"
    result = review_diff({"diff": diff, "project": "bitcoin-core"})
    assert "src/policy/fees.cpp" in result["files"]
    assert any("policy" in item.lower() or "consensus" in item.lower() for item in result["checklist"])


def test_invalid_owner_is_rejected():
    with pytest.raises(ToolError):
        explain_repository(FakeGitHub(), {"owner": "../evil", "repo": "bitcoin"})


def test_github_client_does_not_follow_redirects_or_echo_the_token():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["authorization"] = request.headers.get("authorization")
        if request.url.path.endswith("/readme"):
            return httpx.Response(302, headers={"Location": "http://169.254.169.254/latest"})
        return httpx.Response(
            200,
            json={
                "full_name": "bitcoin/bitcoin",
                "description": "Bitcoin",
                "default_branch": "master",
                "stargazers_count": 1,
                "open_issues_count": 1,
                "html_url": "https://github.com/bitcoin/bitcoin",
            },
        )

    client = GitHubClient(token=TOKEN, transport=httpx.MockTransport(handler))
    repo = client.get_repo("bitcoin", "bitcoin")
    assert TOKEN not in str(repo)
    assert seen["authorization"] == f"Bearer {TOKEN}"
    with pytest.raises(GitHubError, match="redirect"):
        client.get_readme("bitcoin", "bitcoin")
    client.close()


def test_github_token_newlines_are_rejected():
    with pytest.raises(ValueError):
        GitHubClient(token="ghp_secret\nInjected: yes")
