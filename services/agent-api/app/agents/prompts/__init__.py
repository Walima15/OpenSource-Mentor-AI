"""Versioned prompt templates for the agent nodes."""

SYSTEM_BASE = (
    "You are OpenSource Mentor AI, an expert software engineer and patient "
    "mentor who helps developers contribute to open-source projects. You "
    "explain things clearly and in simple language, avoiding unnecessary "
    "jargon, and you ground your reasoning in the provided repository context. "
    "When you are unsure, say so instead of inventing details."
)


def with_context(retrieved: list[dict] | None) -> str:
    if not retrieved:
        return "No indexed code context was available."
    blocks = []
    for chunk in retrieved:
        header = f"# {chunk.get('file_path')} (lines {chunk.get('start_line')}-{chunk.get('end_line')})"
        blocks.append(f"{header}\n{chunk.get('content', '')}")
    return "\n\n".join(blocks)


EXPLAIN_REPO = """Explain this repository to a developer who wants to contribute.

Repository: {repo_full_name}
Description: {repo_description}

Documentation (excerpt):
{repo_docs}

Relevant code context:
{context}

Provide:
1. What the project does (2-3 sentences).
2. The high-level architecture and main components.
3. How the codebase is organized (key directories/files).
4. Where a newcomer should start reading.
Keep it concise and beginner-friendly."""


EXPLAIN_ISSUE = """Explain this GitHub issue in simple language.

Repository: {repo_full_name}
Issue title: {issue_title}
Issue body:
{issue_body}

Relevant code context:
{context}

Provide:
1. A plain-language summary of what the issue is asking for.
2. Why it matters / the expected outcome.
3. Any background a newcomer needs.
4. Potential gotchas or ambiguities to clarify."""


PLAN = """Create a step-by-step implementation plan for this contribution.

Repository: {repo_full_name}
Issue title: {issue_title}
Issue body:
{issue_body}

Relevant code context:
{context}

Respond in strict JSON with this shape:
{{
  "summary": "one paragraph overview of the approach",
  "steps": [{{"order": 1, "title": "short title", "detail": "what to do and why"}}],
  "recommended_files": [{{"path": "path/to/file", "reason": "why this file"}}]
}}
Return ONLY the JSON, no prose."""


RECOMMEND_FILES = """Based on the plan and code context, list the files most
likely to need changes.

Repository: {repo_full_name}
Plan summary: {plan_summary}

Relevant code context:
{context}

Respond in strict JSON: a list of objects like
[{{"path": "path/to/file", "reason": "why"}}]. Return ONLY JSON."""


SUGGEST_CODE = """Propose a concrete code change for the target file.

Repository: {repo_full_name}
Plan summary: {plan_summary}
Target file: {target_file}
Additional instruction: {instruction}

Current file content:
{file_content}

Relevant code context:
{context}

Provide:
1. A unified diff (```diff fenced block) implementing the change.
2. A clear explanation of what changed and why.
Keep the change minimal and focused."""


SUGGEST_TESTS = """Suggest tests for the proposed change.

Repository: {repo_full_name}
Target file: {target_file}
Proposed change (diff):
{diff}

Relevant code context:
{context}

Provide test code (in the repo's likely test framework) plus a short note on
what each test verifies."""


EXPLAIN_CHANGE = """Explain the following code change to a reviewer.

Diff:
{diff}

Provide a clear, reviewer-friendly explanation of what changed, why, and any
risks or follow-ups."""


COMMIT_MESSAGE = """Write a conventional commit message for this change.

Plan summary: {plan_summary}
Diff:
{diff}

Return a single commit message: a concise imperative subject line (<=72 chars),
a blank line, then a short body. No backticks."""


PR_DESCRIPTION = """Write a pull request description for this contribution.

Repository: {repo_full_name}
Issue title: {issue_title}
Plan summary: {plan_summary}
Diff:
{diff}

Use this markdown structure:
## Summary
## Changes
## Testing
## Related issue
Be concise and specific."""


SUMMARIZE = """Summarize the following changes for a changelog entry.

Diff:
{diff}

Return 1-3 bullet points describing the user-facing impact."""


CHAT = """Continue mentoring the developer.

Repository: {repo_full_name}
Conversation so far:
{history}

Relevant code context:
{context}

Developer's message: {user_message}

Respond helpfully and concretely."""
