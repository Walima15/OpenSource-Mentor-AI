"""Turn tool payloads into markdown for guide mode (no language model)."""

from __future__ import annotations


def render(name: str, data: dict) -> str:
    renderer = _RENDERERS.get(name, _generic)
    return renderer(data).strip()


def _generic(data: dict) -> str:
    summary = data.get("summary") or "Done."
    return str(summary)


def _paths(data: dict) -> str:
    lines = ["## Learning paths", ""]
    for path in data.get("paths") or []:
        lines.append(f"### {path['title']}")
        lines.append(path["summary"])
        lines.append("")
        for lesson in path.get("lessons") or []:
            lines.append(f"- **{lesson['title']}** (`{lesson['id']}`) — {lesson['summary']}")
        lines.append("")
    lines.append("Ask for a concept, for example: explain UTXOs, or explain ACK and NACK.")
    return "\n".join(lines)


def _lesson(data: dict) -> str:
    return _lesson_body(data)


def _concept(data: dict) -> str:
    if not data.get("lesson"):
        return data.get("note") or "No matching lesson."
    parts = [_lesson_body(data["lesson"])]
    related = data.get("related") or []
    if related:
        parts.append("\n### Related\n")
        for item in related:
            parts.append(f"- **{item['title']}** (`{item['id']}`)")
    return "\n".join(parts)


def _lesson_body(lesson: dict) -> str:
    lines = [f"## {lesson['title']}", "", lesson.get("summary") or "", "", lesson.get("body") or ""]
    sources = lesson.get("sources") or []
    if sources:
        lines.extend(["", "### Sources", ""])
        for source in sources:
            lines.append(f"- [{source['title']}]({source['url']})")
    questions = lesson.get("quiz") or []
    if questions:
        lines.extend(["", "### Check yourself", ""])
        for index, question in enumerate(questions, start=1):
            lines.append(f"{index}. {question['prompt']}")
            for choice_index, choice in enumerate(question["choices"]):
                lines.append(f"   - {choice_index}. {choice}")
            lines.append("")
        lines.append("Reply with the lesson id and your choice indexes if you want them graded.")
    return "\n".join(lines)


def _quiz(data: dict) -> str:
    lines = [f"## Quiz: {data['title']}", ""]
    for index, question in enumerate(data.get("questions") or [], start=1):
        lines.append(f"{index}. {question['prompt']}")
        for choice_index, choice in enumerate(question["choices"]):
            lines.append(f"   - {choice_index}. {choice}")
        lines.append("")
    return "\n".join(lines)


def _grade(data: dict) -> str:
    lines = [f"## {data['summary']}", ""]
    for result in data.get("results") or []:
        mark = "Correct" if result["correct"] else "Not yet"
        lines.append(f"- **{mark}.** {result['prompt']}")
        lines.append(f"  - {result['explanation']}")
    return "\n".join(lines)


def _projects(data: dict) -> str:
    lines = ["## Bitcoin open-source projects", ""]
    for project in data.get("projects") or []:
        lines.append(
            f"- **{project['name']}** (`{project['slug']}`, {project['language']}, {project['difficulty']}) — {project['summary']}"
        )
    lines.append("")
    lines.append("Ask how to build one of them, or ask for good first issues by project name.")
    return "\n".join(lines)


def _guide(data: dict) -> str:
    lines = [f"## {data['name']}", "", data["summary"], ""]
    if data.get("prerequisites"):
        lines.append("### Before you build")
        lines.extend(f"- {item}" for item in data["prerequisites"])
        lines.append("")
    lines.append("### Setup")
    for index, step in enumerate(data.get("setup_steps") or [], start=1):
        if step.startswith(("git ", "cargo ", "cmake ", "make", "dotnet ", "./", "ctest ")):
            lines.append(f"{index}. `{step}`")
        else:
            lines.append(f"{index}. {step}")
    lines.extend(["", "### Tests", ""])
    lines.extend(f"- `{step}`" for step in data.get("test_steps") or [])
    lines.extend(["", "### Contributing", ""])
    lines.extend(f"- {item}" for item in data.get("contributing") or [])
    lines.extend(["", "### Where to look", ""])
    for item in data.get("code_map") or []:
        lines.append(f"- `{item['path']}` — {item['why']}")
    lines.extend(["", "### Docs", ""])
    for doc in data.get("docs") or []:
        lines.append(f"- [{doc['title']}]({doc['url']})")
    lines.append("")
    lines.append("Confirm the commands against the repository README. Build steps change.")
    return "\n".join(lines)


def _issues(data: dict) -> str:
    lines = [f"## Issues in {data['owner']}/{data['repo']}", ""]
    issues = data.get("issues") or []
    if not issues:
        lines.append(data.get("note") or "No matching issues.")
        lines.append("")
        lines.append(f"Issue tracker: {data['issues_url']}")
        return "\n".join(lines)
    for issue in issues:
        lines.append(f"### #{issue['number']} {issue['title']}")
        lines.append(issue.get("url") or "")
        lines.append("")
        lines.append(issue.get("why") or "")
        body = (issue.get("body") or "").strip()
        if body:
            lines.extend(["", body[:600]])
        lines.append("")
    lines.append("Comment on the issue before you start, and write down how you will test a fix.")
    return "\n".join(lines)


def _repo(data: dict) -> str:
    github = data.get("github") or {}
    lines = [
        f"## {github.get('full_name') or 'Repository'}",
        "",
        github.get("description") or "",
        "",
        f"Language: {github.get('language') or 'unknown'}. Default branch: `{github.get('default_branch')}`.",
        "",
        data.get("how_to_read") or "",
        "",
        "### Top level",
        "",
    ]
    for entry in data.get("root") or []:
        lines.append(f"- `{entry.get('path')}` ({entry.get('type')})")
    if data.get("code_map"):
        lines.extend(["", "### Code map", ""])
        for item in data["code_map"]:
            lines.append(f"- `{item['path']}` — {item['why']}")
    excerpt = (data.get("readme_excerpt") or "").strip()
    if excerpt:
        lines.extend(["", "### README excerpt", "", excerpt[:2_500]])
    return "\n".join(lines)


def _file(data: dict) -> str:
    lines = [
        f"## `{data.get('path')}`",
        "",
        data.get("hint") or "",
        "",
    ]
    if data.get("note"):
        lines.append(data["note"])
    text = data.get("text") or ""
    if text:
        lines.extend(["```", text[:8_000], "```"])
    if data.get("truncated"):
        lines.append("")
        lines.append("The file was truncated. Open the GitHub link for the rest.")
    if data.get("html_url"):
        lines.extend(["", data["html_url"]])
    return "\n".join(lines)


def _plan(data: dict) -> str:
    lines = [f"## Plan: {data['owner']}/{data['repo']}", ""]
    for warning in data.get("warnings") or []:
        lines.append(f"> {warning}")
        lines.append("")
    issue = data.get("issue")
    if issue:
        lines.append(f"Issue [#{issue.get('number')} {issue.get('title')}]({issue.get('url')})")
        lines.append("")
    for index, step in enumerate(data.get("steps") or [], start=1):
        lines.append(f"### {index}. {step['title']}")
        lines.append(step["detail"])
        for path in step.get("files") or []:
            lines.append(f"- `{path}`")
        lines.append("")
    if data.get("tests"):
        lines.append("### Test commands")
        lines.extend(f"- `{item}`" for item in data["tests"])
        lines.append("")
    lines.append(data.get("ask_humans") or "")
    return "\n".join(lines)


def _review(data: dict) -> str:
    pull = data.get("pull") or {}
    lines = ["## Review worksheet", ""]
    lines.append(data.get("ack_rule") or "")
    lines.append("")
    if pull:
        lines.append(f"**{pull.get('title')}** ({data.get('owner')}/{data.get('repo')}#{pull.get('number')})")
        if pull.get("html_url"):
            lines.append(pull["html_url"])
        lines.append("")
        lines.append(
            f"State: {pull.get('state')}. Draft: {pull.get('draft')}. "
            f"+{pull.get('additions')}/-{pull.get('deletions')} across {pull.get('changed_files')} files. "
            f"Head `{pull.get('head_sha')}`."
        )
        body = (pull.get("body") or "").strip()
        if body:
            lines.extend(["", "### Description", "", body[:1_500]])
    files = data.get("files") or []
    if files and isinstance(files[0], dict):
        lines.extend(["", "### Files", ""])
        for item in files:
            lines.append(
                f"- `{item.get('filename')}` ({item.get('status')}, +{item.get('additions')}/-{item.get('deletions')})"
            )
    elif files:
        lines.extend(["", "### Files", ""])
        lines.extend(f"- `{name}`" for name in files)
    lines.extend(["", "### Checklist", ""])
    lines.extend(f"- {item}" for item in data.get("checklist") or [])
    excerpt = (data.get("diff_excerpt") or "").strip()
    if excerpt:
        lines.extend(["", "### Diff excerpt", "", "```diff", excerpt[:6_000], "```"])
    lines.extend(
        [
            "",
            "Write your own comments. If you reviewed the commit and ran tests, you may say ACK and name the commit. Otherwise say what you have not checked.",
        ]
    )
    return "\n".join(lines)


def _local_file(data: dict) -> str:
    lines = [f"## `{data.get('path')}`", ""]
    if data.get("binary"):
        lines.append("This file is binary, so the IDE will not show it as text.")
        return "\n".join(lines)
    if data.get("truncated"):
        lines.append("The file is truncated for this reply.")
        lines.append("")
    text = (data.get("text") or "").strip()
    lines.extend(["```", text[:6_000], "```"])
    lines.append("")
    lines.append("Guide mode is reading the local clone. A model can propose a diff; it will not change the file until you accept it.")
    return "\n".join(lines)


def _local_search(data: dict) -> str:
    lines = [f"## Search: {data.get('query')}", ""]
    matches = data.get("matches") or []
    if not matches:
        lines.append("No matches in the local clone.")
        return "\n".join(lines)
    for item in matches:
        lines.append(f"- `{item.get('path')}:{item.get('line')}` {item.get('text')}")
    return "\n".join(lines)


def _proposed_edit(data: dict) -> str:
    lines = [
        f"## Proposed edit to `{data.get('path')}`",
        "",
        "This diff is not applied. Accept or reject it in the editor.",
        "",
        "```diff",
        (data.get("diff") or "").strip()[:12_000],
        "```",
    ]
    return "\n".join(lines)


_RENDERERS = {
    "list_learning_paths": _paths,
    "get_lesson": _lesson,
    "explain_concept": _concept,
    "get_quiz": _quiz,
    "grade_quiz": _grade,
    "list_projects": _projects,
    "get_project_guide": _guide,
    "find_good_first_issues": _issues,
    "explain_repository": _repo,
    "explain_file": _file,
    "plan_contribution": _plan,
    "review_pull_request": _review,
    "review_diff": _review,
    "read_workspace_file": _local_file,
    "search_workspace": _local_search,
    "propose_workspace_edit": _proposed_edit,
}
