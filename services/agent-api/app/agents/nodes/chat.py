"""Free-form mentor chat node."""

from __future__ import annotations

from app.agents import prompts
from app.agents.llm import get_llm
from app.agents.state import AgentState


def _format_history(history: list[dict] | None) -> str:
    if not history:
        return "(no prior messages)"
    lines = []
    for msg in history[-10:]:
        role = msg.get("role", "user")
        lines.append(f"{role}: {msg.get('content', '')}")
    return "\n".join(lines)


def chat_node(state: AgentState) -> AgentState:
    context = prompts.with_context(state.get("retrieved_chunks"))
    prompt = prompts.CHAT.format(
        repo_full_name=state.get("repo_full_name", ""),
        history=_format_history(state.get("history")),
        context=context,
        user_message=state.get("user_message", ""),
    )
    output = get_llm().complete(prompts.SYSTEM_BASE, prompt, max_tokens=1800)
    return {"output": output}
