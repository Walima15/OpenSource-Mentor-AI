"""Pull request nodes: commit message, PR description, change summary."""

from __future__ import annotations

from app.agents import prompts
from app.agents.llm import get_llm
from app.agents.state import AgentState


def commit_message_node(state: AgentState) -> AgentState:
    prompt = prompts.COMMIT_MESSAGE.format(
        plan_summary=state.get("plan_summary", "") or "(none)",
        diff=(state.get("diff", "") or "")[:6000],
    )
    output = get_llm().complete(prompts.SYSTEM_BASE, prompt, max_tokens=400)
    return {"output": output.strip()}


def pr_description_node(state: AgentState) -> AgentState:
    prompt = prompts.PR_DESCRIPTION.format(
        repo_full_name=state.get("repo_full_name", ""),
        issue_title=state.get("issue_title", "") or "(none)",
        plan_summary=state.get("plan_summary", "") or "(none)",
        diff=(state.get("diff", "") or "")[:6000],
    )
    output = get_llm().complete(prompts.SYSTEM_BASE, prompt, max_tokens=1200)
    return {"output": output}


def summarize_node(state: AgentState) -> AgentState:
    prompt = prompts.SUMMARIZE.format(diff=(state.get("diff", "") or "")[:8000])
    output = get_llm().complete(prompts.SYSTEM_BASE, prompt, max_tokens=600)
    return {"output": output}
