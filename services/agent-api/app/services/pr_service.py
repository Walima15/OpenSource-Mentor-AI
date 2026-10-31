"""Create a real pull request on GitHub from a contribution plan.

Flow: resolve the authenticated user, fork the upstream repo if needed, create a
branch, apply each code suggestion's unified diff to the current file content,
commit the results, and open a pull request against the upstream base branch.

LLM-generated diffs are not always cleanly appliable. Any file that fails to
patch is reported in ``skipped_files``. If nothing could be applied, the
contribution plan is committed as a markdown document so the pull request is
non-empty and still useful.
"""

from __future__ import annotations

import asyncio

from app.core.github_input import validate_repo_file_path
from app.core.logging import get_logger
from app.services.github_service import GitHubError, GitHubService

logger = get_logger(__name__)


def apply_unified_diff(original: str, diff_text: str) -> str | None:
    """Apply a unified diff to ``original``. Returns new content or None."""
    if not diff_text.strip():
        return None
    try:
        import whatthepatch

        patches = list(whatthepatch.parse_patch(diff_text))
        if not patches:
            return None
        result_lines = whatthepatch.apply_diff(patches[0], original)
        if result_lines is None:
            return None
        new_content = "\n".join(result_lines)
        if original.endswith("\n") and not new_content.endswith("\n"):
            new_content += "\n"
        return new_content
    except Exception:  # noqa: BLE001
        logger.warning("Could not apply diff", exc_info=True)
        return None


def _plan_markdown(summary: str, steps: list, files: list) -> str:
    lines = ["# OSMA contribution plan", "", summary or "(no summary)", ""]
    if steps:
        lines.append("## Steps")
        for s in steps:
            order = s.get("order", "")
            title = s.get("title", "")
            detail = s.get("detail", "")
            lines.append(f"{order}. **{title}** - {detail}")
        lines.append("")
    if files:
        lines.append("## Files to change")
        for f in files:
            lines.append(f"- `{f.get('path', '')}` - {f.get('reason', '')}")
        lines.append("")
    return "\n".join(lines)


async def _wait_for_fork(gh: GitHubService, owner: str, name: str) -> None:
    for _ in range(10):
        try:
            await gh.get_repo(owner, name)
            return
        except GitHubError:
            await asyncio.sleep(2)
    logger.warning("Fork %s/%s not confirmed ready; proceeding", owner, name)


async def create_pull_request_for_plan(
    *,
    token: str,
    upstream_owner: str,
    upstream_name: str,
    base_branch: str,
    branch_name: str,
    title: str,
    body: str,
    commit_message: str,
    summary: str,
    steps: list,
    recommended_files: list,
    suggestions: list,
) -> dict:
    gh = GitHubService(token=token)

    me = await gh.get_authenticated_user()
    login = me["login"]

    if login.lower() == upstream_owner.lower():
        head_owner, head_name = upstream_owner, upstream_name
    else:
        fork = await gh.fork_repo(upstream_owner, upstream_name)
        head_owner = fork.get("owner", {}).get("login", login)
        head_name = fork.get("name", upstream_name)
        await _wait_for_fork(gh, head_owner, head_name)

    base_sha = await gh.get_branch_sha(head_owner, head_name, base_branch)
    await gh.create_branch(head_owner, head_name, branch_name, base_sha)

    applied: list[str] = []
    skipped: list[str] = []

    for suggestion in suggestions:
        try:
            path = validate_repo_file_path(suggestion.file_path)
        except ValueError:
            logger.warning("Skipping disallowed path on plan PR")
            skipped.append(suggestion.file_path)
            continue
        original = (
            await gh.get_file_content(head_owner, head_name, path, branch_name) or ""
        )
        new_content = apply_unified_diff(original, suggestion.diff)
        if new_content is None or new_content == original:
            skipped.append(path)
            continue
        sha = await gh.get_content_sha(head_owner, head_name, path, branch_name)
        await gh.put_file(
            head_owner,
            head_name,
            path,
            new_content,
            commit_message or f"Update {path}",
            branch_name,
            sha,
        )
        applied.append(path)

    note: str | None = None
    if not applied:
        doc_path = ".osma/contribution-plan.md"
        content = _plan_markdown(summary, steps, recommended_files)
        sha = await gh.get_content_sha(head_owner, head_name, doc_path, branch_name)
        await gh.put_file(
            head_owner,
            head_name,
            doc_path,
            content,
            "docs: add OSMA contribution plan",
            branch_name,
            sha,
        )
        applied.append(doc_path)
        note = (
            "No code diffs could be applied cleanly, so the contribution plan was "
            "committed instead. Push code changes to the branch, then update the PR."
        )

    head_ref = branch_name if head_owner == upstream_owner else f"{head_owner}:{branch_name}"
    pr = await gh.create_pull_request(
        upstream_owner, upstream_name, title, head_ref, base_branch, body
    )

    return {
        "url": pr.get("html_url", ""),
        "number": pr.get("number", 0),
        "branch": branch_name,
        "head": head_ref,
        "applied_files": applied,
        "skipped_files": skipped,
        "note": note,
    }
