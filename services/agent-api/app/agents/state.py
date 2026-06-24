"""Shared state passed between LangGraph nodes."""

from __future__ import annotations

from typing import Any, Literal, TypedDict

Intent = Literal[
    "explain_repo",
    "explain_issue",
    "plan",
    "recommend_files",
    "suggest_code",
    "suggest_tests",
    "explain_change",
    "commit_message",
    "pr_description",
    "summarize",
    "chat",
]


class AgentState(TypedDict, total=False):
    # Routing
    intent: Intent

    # Repo / issue context
    repo_full_name: str
    repo_description: str
    repo_docs: str
    issue_title: str
    issue_body: str

    # Retrieval
    query: str
    retrieved_chunks: list[dict]

    # Working context for contribution/PR nodes
    plan_summary: str
    target_file: str
    file_content: str
    instruction: str
    diff: str

    # User message (chat)
    user_message: str
    history: list[dict]

    # Output
    output: str
    structured: dict[str, Any]
