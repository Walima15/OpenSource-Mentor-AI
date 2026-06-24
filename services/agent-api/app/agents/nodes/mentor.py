"""Mentor nodes: repo analysis, issue explanation, implementation planning."""

from __future__ import annotations

import json

from app.agents import prompts
from app.agents.llm import get_llm
from app.agents.state import AgentState
from app.core.logging import get_logger

logger = get_logger(__name__)


def repo_analyzer_node(state: AgentState) -> AgentState:
    context = prompts.with_context(state.get("retrieved_chunks"))
    prompt = prompts.EXPLAIN_REPO.format(
        repo_full_name=state.get("repo_full_name", ""),
        repo_description=state.get("repo_description", "") or "(no description)",
        repo_docs=(state.get("repo_docs", "") or "")[:4000],
        context=context,
    )
    output = get_llm().complete(prompts.SYSTEM_BASE, prompt, max_tokens=1500)
    return {"output": output}


def explain_issue_node(state: AgentState) -> AgentState:
    context = prompts.with_context(state.get("retrieved_chunks"))
    prompt = prompts.EXPLAIN_ISSUE.format(
        repo_full_name=state.get("repo_full_name", ""),
        issue_title=state.get("issue_title", "") or "(none)",
        issue_body=(state.get("issue_body", "") or "")[:4000],
        context=context,
    )
    output = get_llm().complete(prompts.SYSTEM_BASE, prompt, max_tokens=1500)
    return {"output": output}


def planner_node(state: AgentState) -> AgentState:
    context = prompts.with_context(state.get("retrieved_chunks"))
    prompt = prompts.PLAN.format(
        repo_full_name=state.get("repo_full_name", ""),
        issue_title=state.get("issue_title", "") or "(none)",
        issue_body=(state.get("issue_body", "") or "")[:4000],
        context=context,
    )
    raw = get_llm().complete(prompts.SYSTEM_BASE, prompt, max_tokens=2000)
    structured = _safe_json(
        raw, fallback={"summary": raw, "steps": [], "recommended_files": []}
    )
    return {"output": raw, "structured": structured}


def _safe_json(raw: str, fallback: dict) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            logger.warning("Planner returned non-JSON output; using fallback")
    return fallback
