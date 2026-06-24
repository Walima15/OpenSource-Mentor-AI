"""Contribution nodes: file recommendation, code + test suggestion, explanation."""

from __future__ import annotations

import json

from app.agents import prompts
from app.agents.llm import get_llm
from app.agents.nodes.mentor import _safe_json
from app.agents.state import AgentState


def file_recommender_node(state: AgentState) -> AgentState:
    context = prompts.with_context(state.get("retrieved_chunks"))
    prompt = prompts.RECOMMEND_FILES.format(
        repo_full_name=state.get("repo_full_name", ""),
        plan_summary=state.get("plan_summary", "") or "(none)",
        context=context,
    )
    raw = get_llm().complete(prompts.SYSTEM_BASE, prompt, max_tokens=1200)
    files = _safe_json_list(raw)
    return {"output": raw, "structured": {"recommended_files": files}}


def code_suggester_node(state: AgentState) -> AgentState:
    context = prompts.with_context(state.get("retrieved_chunks"))
    prompt = prompts.SUGGEST_CODE.format(
        repo_full_name=state.get("repo_full_name", ""),
        plan_summary=state.get("plan_summary", "") or "(none)",
        target_file=state.get("target_file", ""),
        instruction=state.get("instruction", "") or "(none)",
        file_content=(state.get("file_content", "") or "(new or empty file)")[:6000],
        context=context,
    )
    output = get_llm().complete(prompts.SYSTEM_BASE, prompt, max_tokens=2500)
    diff = _extract_diff(output)
    return {"output": output, "diff": diff, "structured": {"diff": diff}}


def test_suggester_node(state: AgentState) -> AgentState:
    context = prompts.with_context(state.get("retrieved_chunks"))
    prompt = prompts.SUGGEST_TESTS.format(
        repo_full_name=state.get("repo_full_name", ""),
        target_file=state.get("target_file", ""),
        diff=(state.get("diff", "") or "")[:6000],
        context=context,
    )
    output = get_llm().complete(prompts.SYSTEM_BASE, prompt, max_tokens=2000)
    return {"output": output}


def explain_change_node(state: AgentState) -> AgentState:
    prompt = prompts.EXPLAIN_CHANGE.format(diff=(state.get("diff", "") or "")[:8000])
    output = get_llm().complete(prompts.SYSTEM_BASE, prompt, max_tokens=1200)
    return {"output": output}


def _safe_json_list(raw: str) -> list:
    text = raw.strip().strip("`")
    if text.lower().startswith("json"):
        text = text[4:]
    start, end = text.find("["), text.rfind("]")
    if start != -1 and end != -1:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass
    return _safe_json(raw, {"recommended_files": []}).get("recommended_files", [])


def _extract_diff(text: str) -> str:
    if "```diff" in text:
        after = text.split("```diff", 1)[1]
        return after.split("```", 1)[0].strip()
    if "```" in text:
        after = text.split("```", 1)[1]
        return after.split("```", 1)[0].strip()
    return text.strip()
