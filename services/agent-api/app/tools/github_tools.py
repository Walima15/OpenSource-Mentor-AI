"""GitHub-backed tools: issues, repository reading, contribution plans, reviews."""

from __future__ import annotations

import re

from app.content.loader import PROJECTS
from app.content.review_guides import checklist_for
from app.core.security import ToolError, validate_git_path, validate_owner_repo
from app.github.client import GitHubClient, GitHubError
from app.tools.projects import match_project
from app.tools.util import as_int, optional_int, optional_str, required_str

_SENSITIVE = re.compile(
    r"\b(consensus|soft\s*fork|hard\s*fork|subsidy|inflation|script interpreter|"
    r"block weight|wire protocol|signature validation)\b",
    re.IGNORECASE,
)
_DIFF_FILE = re.compile(r"^diff --git a/(.+?) b/", re.MULTILINE)


def find_good_first_issues(github: GitHubClient, args: dict) -> dict:
    owner, repo, project = _repo_from_args(args)
    limit = optional_int(args, "limit", 1, 10) or 5
    labels = list(project.issue_labels) if project else ["good first issue", "help wanted"]
    found: list[dict] = []
    seen: set[int] = set()
    rate_limited = False
    for label in labels:
        try:
            batch = github.search_issues(owner, repo, label, limit=limit)
        except GitHubError as exc:
            if exc.status_code in {403, 429}:
                rate_limited = True
                break
            continue
        for issue in batch:
            number = issue.get("number")
            if not isinstance(number, int) or number in seen:
                continue
            seen.add(number)
            issue["why"] = _why_issue(issue, label)
            found.append(issue)
            if len(found) >= limit:
                break
        if len(found) >= limit:
            break
    if not found and rate_limited:
        raise ToolError(
            "GitHub rate limit reached. Set GITHUB_TOKEN for a higher limit, or wait and retry."
        )
    name = project.name if project else f"{owner}/{repo}"
    return {
        "summary": f"Found {len(found)} open issues in {owner}/{repo}",
        "project": project.slug if project else None,
        "project_name": name,
        "owner": owner,
        "repo": repo,
        "issues": found,
        "issues_url": f"https://github.com/{owner}/{repo}/issues",
        "note": None
        if found
        else (
            "No open issues with the usual beginner labels right now. "
            "That is common on Bitcoin Core. Reviewing an existing pull request "
            "is often a better first contribution than waiting for a label."
        ),
    }


def explain_repository(github: GitHubClient, args: dict) -> dict:
    owner, repo, project = _repo_from_args(args)
    try:
        meta = github.get_repo(owner, repo)
        readme = github.get_readme(owner, repo)
        root = github.list_root(owner, repo)
    except GitHubError as exc:
        raise ToolError(exc.message) from None
    return {
        "summary": f"Overview of {owner}/{repo}",
        "project": None if project is None else project.model_dump(),
        "github": meta,
        "readme_excerpt": readme[:4_000],
        "root": root,
        "code_map": [] if project is None else [item.model_dump() for item in project.code_map],
        "how_to_read": (
            "Start with the README and CONTRIBUTING file, then one test or one RPC, "
            "then the files in the code map. Paths move; the repository wins if they disagree."
        ),
    }


def explain_file(github: GitHubClient, args: dict) -> dict:
    owner, repo, project = _repo_from_args(args)
    path = validate_git_path(required_str(args, "path", 400))
    ref = optional_str(args, "ref", 120)
    try:
        payload = github.get_file(owner, repo, path, ref)
    except GitHubError as exc:
        raise ToolError(exc.message) from None
    payload.update(
        {
            "summary": f"File {owner}/{repo} {path}",
            "owner": owner,
            "repo": repo,
            "project": project.slug if project else None,
            "hint": _file_hint(path, project.slug if project else None),
        }
    )
    return payload


def plan_contribution(github: GitHubClient, args: dict) -> dict:
    owner, repo, project = _repo_from_args(args)
    goal = optional_str(args, "goal", 2_000)
    number = optional_int(args, "issue_number", 1, 1_000_000)
    issue = None
    if number is not None:
        try:
            issue = github.get_issue(owner, repo, number)
        except GitHubError as exc:
            raise ToolError(exc.message) from None
        if issue.get("is_pull_request"):
            raise ToolError("That number is a pull request. Use the review tool, or pick an issue.")
    text = " ".join(
        part
        for part in (goal or "", (issue or {}).get("title") or "", (issue or {}).get("body") or "")
        if part
    )
    warnings = []
    if _SENSITIVE.search(text):
        warnings.append(
            "This touches consensus, the wire protocol, or another high-impact area. "
            "Discuss it on the project issue, IRC, or the mailing list before writing a large patch. "
            "Do not open a drive-by consensus pull request."
        )
    steps = _plan_steps(owner, repo, project, issue, goal)
    title = issue["title"] if issue else (goal or f"a change to {owner}/{repo}")
    return {
        "summary": f"Contribution plan for {owner}/{repo}: {title[:120]}",
        "owner": owner,
        "repo": repo,
        "project": project.slug if project else None,
        "goal": goal,
        "issue": issue,
        "warnings": warnings,
        "steps": steps,
        "ask_humans": _ask_humans(project),
        "tests": [] if project is None else project.test_steps,
        "contributing": [] if project is None else project.contributing,
    }


def review_pull_request(github: GitHubClient, args: dict) -> dict:
    owner, repo, project = _repo_from_args(args)
    number = as_int(args.get("number"), "number", 1, 1_000_000)
    try:
        pull = github.get_pull(owner, repo, number)
        files = github.get_pull_files(owner, repo, number)
        diff = github.get_pull_diff(owner, repo, number)
    except GitHubError as exc:
        raise ToolError(exc.message) from None
    slug = project.slug if project else None
    return {
        "summary": f"Review material for {owner}/{repo}#{number}",
        "owner": owner,
        "repo": repo,
        "project": slug,
        "pull": pull,
        "files": files,
        "diff_excerpt": diff,
        "checklist": checklist_for(slug),
        "ack_rule": (
            "Do not ACK this pull request. ACK means a human reviewed that commit. "
            "Write Concept ACK, Approach ACK, comments, or questions only when they are yours."
        ),
    }


def review_diff(args: dict) -> dict:
    diff = required_str(args, "diff", 20_000)
    if len(diff) > 20_000:
        raise ToolError("diff is too large; review a pull request URL or a smaller patch")
    project_name = optional_str(args, "project", 64)
    project = match_project(project_name) if project_name else None
    files = _DIFF_FILE.findall(diff)
    return {
        "summary": f"Review worksheet for a {len(diff)} character diff",
        "project": project.slug if project else None,
        "files": files[:40],
        "diff_excerpt": diff[:12_000],
        "checklist": checklist_for(project.slug if project else None),
        "ack_rule": (
            "Do not ACK this diff. Use the checklist, then write comments you can stand behind."
        ),
    }


def _repo_from_args(args: dict) -> tuple[str, str, object]:
    project_query = optional_str(args, "project", 80)
    owner = optional_str(args, "owner", 40)
    repo = optional_str(args, "repo", 100)
    if owner and repo:
        owner, repo = validate_owner_repo(owner, repo)
        return owner, repo, match_project(f"{owner}/{repo}")
    if project_query:
        project = PROJECTS.get(project_query) or match_project(project_query)
        if project is None:
            raise ToolError(f"Unknown project {project_query}")
        return project.owner, project.repo, project
    raise ToolError("Provide a known project slug or a GitHub owner and repo")


def _why_issue(issue: dict, label: str) -> str:
    comments = issue.get("comments") or 0
    advice = (
        f"Labeled '{label}'. Read the whole thread, reproduce the gap, and say how you "
        "would test a fix before you write a large patch."
    )
    if isinstance(comments, int) and comments > 15:
        advice += " The thread is active. Read the latest comments so you do not repeat a rejected idea."
    return advice


def _file_hint(path: str, slug: str | None) -> str:
    lowered = path.lower()
    if "test" in lowered:
        return "This looks like a test. Read the case names before the implementation they cover."
    if any(token in lowered for token in ("validation", "interpreter", "consensus")):
        return (
            "This sits near validation or script. Treat a behavior change as consensus-sensitive "
            "until you can show it is not."
        )
    if "/rpc" in lowered or lowered.startswith("src/rpc"):
        return "This is RPC surface. Check help text, compatibility, and a functional test."
    if "policy" in lowered or "mempool" in lowered:
        return (
            "This is policy or mempool code. It can change relay without being a consensus rule. "
            "Say which you mean."
        )
    if slug == "ldk" and "/ln/" in lowered:
        return "This is Lightning channel logic. Cite the BOLT and trace a malicious peer, not only the happy path."
    if slug == "bdk":
        return "Wallet code: trace inputs, change, and fees on a multi-input example."
    return "Read the file with the project's contributing guide. Explain the function you care about before editing it."


def _plan_steps(owner: str, repo: str, project, issue: dict | None, goal: str | None) -> list[dict]:
    issue_bit = ""
    if issue:
        issue_bit = f" Start from issue #{issue.get('number')}: {issue.get('title')}."
    goal_bit = f" Goal: {goal}." if goal else ""
    files = []
    if project is not None:
        files = [item.path for item in project.code_map[:6]]
    return [
        {
            "title": "Restate the problem",
            "detail": (
                f"Write one paragraph, in your own words, about what should change in {owner}/{repo} "
                f"and what must not change.{issue_bit}{goal_bit}"
            ),
        },
        {
            "title": "Reproduce or demonstrate",
            "detail": (
                "A bug needs a failing test. A feature needs the smallest command or test "
                "that shows the new behavior."
            ),
        },
        {
            "title": "Find the code",
            "detail": "Open the files below, then follow one call path. Stop when you can explain it out loud.",
            "files": files,
        },
        {
            "title": "Choose the smallest design",
            "detail": "Write the approach you will take and the alternative you rejected. Keep unrelated cleanup out.",
        },
        {
            "title": "Test",
            "detail": "Name the project test command and the case you will add. Run it before you ask for review.",
        },
        {
            "title": "Open the pull request",
            "detail": (
                "Describe motivation, behavior, and the exact test command. Sign commits if the project expects it. "
                "You should be able to defend every line without the mentor in the room."
            ),
        },
        {
            "title": "Stay for review",
            "detail": (
                "Answer every comment. After a force-push, say what changed. "
                "Do not treat silence in the first days as a rejection."
            ),
        },
    ]


def _ask_humans(project) -> str:
    if project is None:
        return "Ask on the project's issue tracker or the channel listed in its CONTRIBUTING file."
    if project.slug == "bitcoin-core":
        return (
            "For non-trivial Bitcoin Core changes, ask on the issue, in #bitcoin-core-dev on Libera.Chat, "
            "or on the bitcoin-dev mailing list if the idea changes the protocol."
        )
    if project.slug in {"ldk", "lnd", "core-lightning", "bolts"}:
        return (
            "Protocol changes belong on the lightning-dev mailing list and in the BOLTs, "
            "not only in one daemon."
        )
    return f"Comment on the {project.name} issue before you write a large patch, and read CONTRIBUTING.md."
