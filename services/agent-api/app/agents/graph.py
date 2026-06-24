"""LangGraph orchestrator.

A single state graph routes an incoming request to the node matching its
`intent`. Each node is independently testable; the graph wires them together
and exposes a simple `run_intent` helper for the API layer.
"""

from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from app.agents.nodes import (
    code_suggester_node,
    commit_message_node,
    explain_change_node,
    explain_issue_node,
    file_recommender_node,
    planner_node,
    pr_description_node,
    repo_analyzer_node,
    summarize_node,
    test_suggester_node,
)
from app.agents.nodes.chat import chat_node
from app.agents.state import AgentState

_INTENT_TO_NODE = {
    "explain_repo": "repo_analyzer",
    "explain_issue": "issue_explainer",
    "plan": "planner",
    "recommend_files": "file_recommender",
    "suggest_code": "code_suggester",
    "suggest_tests": "test_suggester",
    "explain_change": "explain_change",
    "commit_message": "commit_message",
    "pr_description": "pr_description",
    "summarize": "summarize",
    "chat": "chat",
}


def _route(state: AgentState) -> str:
    return _INTENT_TO_NODE.get(state.get("intent", "chat"), "chat")


@lru_cache
def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("repo_analyzer", repo_analyzer_node)
    graph.add_node("issue_explainer", explain_issue_node)
    graph.add_node("planner", planner_node)
    graph.add_node("file_recommender", file_recommender_node)
    graph.add_node("code_suggester", code_suggester_node)
    graph.add_node("test_suggester", test_suggester_node)
    graph.add_node("explain_change", explain_change_node)
    graph.add_node("commit_message", commit_message_node)
    graph.add_node("pr_description", pr_description_node)
    graph.add_node("summarize", summarize_node)
    graph.add_node("chat", chat_node)

    graph.add_conditional_edges(START, _route)
    for node in _INTENT_TO_NODE.values():
        graph.add_edge(node, END)

    return graph.compile()


def run_intent(state: AgentState) -> AgentState:
    """Execute the graph for a given state and return the final state."""
    return build_graph().invoke(state)
