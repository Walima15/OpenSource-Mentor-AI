"""Keyword mentor used when no LLM key is configured, and when the LLM call fails.

It still calls the real tools, so curriculum, project guides, and GitHub data
are live. It is not a substitute for the conversational model.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.agent.render import render
from app.tools.projects import match_project
from app.tools.registry import ToolRegistry

_GUIDE_BANNER = (
    "> Guide mode: no language model answered this turn, so OSMA assembled it from "
    "the curriculum and tools. Set `OPENAI_API_KEY` for a conversational mentor.\n\n"
)

_PR_URL = re.compile(
    r"github\.com/([A-Za-z0-9][A-Za-z0-9-]{0,38})/([A-Za-z0-9._-]{1,100})/pull/(\d+)",
    re.IGNORECASE,
)
_OWNER_REPO = re.compile(
    r"\b([A-Za-z0-9][A-Za-z0-9-]{0,38})/([A-Za-z0-9._-]{1,100})\b"
)
_FILE_CMD = re.compile(
    r"(?:file|path)\s+([A-Za-z0-9][A-Za-z0-9-]{0,38})/([A-Za-z0-9._-]{1,100})\s+(\S+)",
    re.IGNORECASE,
)
_ISSUE = re.compile(r"(?:issue|issues)\s+#?(\d+)", re.IGNORECASE)
_PR_NUM = re.compile(r"(?:pull request|pull|pr)\s+#?(\d+)", re.IGNORECASE)


@dataclass
class AgentReply:
    content: str
    traces: list[dict] = field(default_factory=list)
    mode: str = "guide"


def guide_reply(
    message: str,
    tools: ToolRegistry,
    *,
    failed_llm: bool = False,
    open_path: str | None = None,
) -> AgentReply:
    text = message.strip()
    local = _local_workspace(text, tools, open_path)
    if local is None:
        content, traces = _route(text, tools)
    else:
        content, traces = local
    banner = _GUIDE_BANNER
    if failed_llm:
        banner = (
            "> The language model request failed, so this answer is from the offline guide.\n\n"
        )
    return AgentReply(content=banner + content, traces=traces, mode="guide")


def _route(text: str, tools: ToolRegistry) -> tuple[str, list[dict]]:
    lowered = text.lower()
    pr_url = _PR_URL.search(text)
    if pr_url or (_wants_review(lowered) and (_PR_NUM.search(text) or pr_url)):
        if pr_url:
            owner, repo, number = pr_url.group(1), pr_url.group(2), int(pr_url.group(3))
        else:
            owner_repo = _explicit_repo(text)
            number_match = _PR_NUM.search(text)
            project = match_project(text)
            if owner_repo and number_match:
                owner, repo = owner_repo
                number = int(number_match.group(1))
            elif project and number_match:
                owner, repo = project.owner, project.repo
                number = int(number_match.group(1))
            else:
                return (
                    "To review a pull request, send a GitHub URL "
                    "(`https://github.com/owner/repo/pull/123`) or `review owner/repo#123`.",
                    [],
                )
        return _call(tools, "review_pull_request", {"owner": owner, "repo": repo, "number": number})

    if "```" in text and "review" in lowered:
        diff = _extract_diff(text)
        project = match_project(text)
        args = {"diff": diff}
        if project:
            args["project"] = project.slug
        return _call(tools, "review_diff", args)

    file_match = _FILE_CMD.search(text)
    if file_match:
        return _call(
            tools,
            "explain_file",
            {
                "owner": file_match.group(1),
                "repo": file_match.group(2),
                "path": file_match.group(3),
            },
        )

    if any(phrase in lowered for phrase in ("good first", "beginner issue", "help wanted", "find issues", "recommend issues")):
        project = match_project(text)
        owner_repo = _explicit_repo(text)
        if project:
            return _call(tools, "find_good_first_issues", {"project": project.slug, "limit": 5})
        if owner_repo:
            owner, repo = owner_repo
            return _call(
                tools,
                "find_good_first_issues",
                {"owner": owner, "repo": repo, "limit": 5},
            )
        return _call(tools, "list_projects", {})

    if _wants_plan(lowered):
        project = match_project(text)
        owner_repo = _explicit_repo(text)
        args: dict = {}
        if owner_repo:
            args["owner"], args["repo"] = owner_repo
        elif project:
            args["project"] = project.slug
        else:
            return (
                "Name a project to plan against, for example: plan a contribution to BDK.",
                [],
            )
        issue = _ISSUE.search(text)
        if issue:
            args["issue_number"] = int(issue.group(1))
        if "goal" in lowered or len(text) > 80:
            args["goal"] = text[:2_000]
        return _call(tools, "plan_contribution", args)

    if _wants_setup(lowered):
        project = match_project(text)
        if project:
            return _call(tools, "get_project_guide", {"project": project.slug})
        return _call(tools, "list_projects", {})

    if any(phrase in lowered for phrase in ("which project", "list project", "what projects", "curated project")):
        return _call(tools, "list_projects", {})

    if "quiz" in lowered:
        from app.tools.curriculum import explain_concept

        matched = explain_concept({"query": text})
        lesson = (matched.get("lesson") or {}).get("id")
        if lesson:
            return _call(tools, "get_quiz", {"lesson_id": lesson})
        return _call(tools, "list_learning_paths", {})

    if any(phrase in lowered for phrase in ("learning path", "curriculum", "what should i learn", "lesson list")):
        return _call(tools, "list_learning_paths", {})

    if any(phrase in lowered for phrase in ("explain the repo", "explain repo", "how is the repo", "repository overview")):
        project = match_project(text)
        owner_repo = _explicit_repo(text)
        if owner_repo:
            owner, repo = owner_repo
            return _call(tools, "explain_repository", {"owner": owner, "repo": repo})
        if project:
            return _call(tools, "explain_repository", {"project": project.slug})

    concept = _call(tools, "explain_concept", {"query": text})
    content, traces = concept
    if "No lesson matched" in content or "No curriculum match" in content:
        return _help(), []
    return content, traces


def _local_workspace(
    text: str,
    tools: ToolRegistry,
    open_path: str | None,
) -> tuple[str, list[dict]] | None:
    from app.workspace.context import current_workspace_id

    if not current_workspace_id():
        return None
    lowered = text.lower().strip()
    if lowered.startswith("search "):
        query = text.strip()[7:].strip()
        return _call(tools, "search_workspace", {"query": query})
    wants_file = open_path and (
        "this file" in lowered or lowered in {"explain", "explain file"} or lowered.startswith("explain this")
    )
    if wants_file:
        return _call(tools, "read_workspace_file", {"path": open_path})
    return None


def _call(tools: ToolRegistry, name: str, args: dict) -> tuple[str, list[dict]]:
    result = tools.call(name, args)
    trace = {"name": name, "ok": result["ok"], "summary": result["summary"]}
    if not result["ok"]:
        return f"**{result['error']}**", [trace]
    return render(name, result["data"]), [trace]


def _wants_review(lowered: str) -> bool:
    return "review" in lowered


def _wants_plan(lowered: str) -> bool:
    phrases = (
        "plan a ",
        "plan my ",
        "plan this",
        "contribution plan",
        "how should i approach",
        "how do i approach",
        "how do i contribute",
        "help me plan",
    )
    return lowered.startswith("plan ") or any(phrase in lowered for phrase in phrases)


def _wants_setup(lowered: str) -> bool:
    phrases = (
        "how do i build",
        "how to build",
        "how do i set up",
        "how to set up",
        "set up ",
        "setup ",
        "compile ",
        "build steps",
    )
    return any(phrase in lowered for phrase in phrases)


def _explicit_repo(text: str) -> tuple[str, str] | None:
    for match in _OWNER_REPO.finditer(text):
        owner, repo = match.group(1), match.group(2)
        if owner.lower() in {"https", "http", "github.com"}:
            continue
        if repo.lower() in {"pull", "issues", "blob"}:
            continue
        return owner, repo
    return None


def _extract_diff(text: str) -> str:
    if "```" not in text:
        return text[:20_000]
    parts = text.split("```")
    if len(parts) >= 3:
        body = parts[1]
        if body.startswith("diff"):
            body = body[4:]
        return body.strip()[:20_000]
    return text[:20_000]


def _help() -> str:
    return """## What OSMA can do

I am a mentor for contributing to Bitcoin open source. Try one of these:

- Explain UTXOs
- How do ACK and NACK work in Bitcoin Core?
- How do I build Bitcoin Core?
- Find good first issues in rust-bitcoin
- Plan a contribution to BDK
- Review https://github.com/bitcoin/bitcoin/pull/12345

The curriculum covers transactions, scripts, blocks, consensus, the peer-to-peer network, the mempool, BIPs, Lightning, testing, signed commits, pull request etiquette, mailing lists, and IRC.

I will not ACK a pull request for you, and I will not help you skip review.
"""
