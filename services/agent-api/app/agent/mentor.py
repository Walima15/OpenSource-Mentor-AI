"""Tool-calling mentor. Falls back to the guide when no model is configured."""

from __future__ import annotations

import json

from app.agent.fallback import AgentReply, guide_reply
from app.agent.prompts import SYSTEM_PROMPT
from app.core.logging import get_logger
from app.llm.client import LlmError, OpenAICompatibleClient
from app.tools.registry import ToolRegistry

logger = get_logger(__name__)


class MentorAgent:
    def __init__(
        self,
        llm: OpenAICompatibleClient | None,
        tools: ToolRegistry,
        max_rounds: int = 4,
    ):
        self.llm = llm
        self.tools = tools
        self.max_rounds = max_rounds

    def reply(self, history: list[dict], user_message: str) -> AgentReply:
        if self.llm is None or not self.llm.configured:
            return guide_reply(user_message, self.tools)
        messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
        for item in history[-12:]:
            role = item.get("role")
            content = item.get("content")
            if role in {"user", "assistant"} and isinstance(content, str) and content.strip():
                messages.append({"role": role, "content": content[:8_000]})
        messages.append({"role": "user", "content": user_message})
        traces: list[dict] = []
        seen: set[str] = set()
        try:
            for _ in range(self.max_rounds):
                result = self.llm.complete(messages, self.tools.schemas())
                if not result.tool_calls:
                    content = result.content.strip() or (
                        "I could not produce a reply. Try asking about a concept, a project, or a pull request."
                    )
                    return AgentReply(content=content, traces=traces, mode="llm")
                messages.append(result.assistant_message)
                for call in result.tool_calls:
                    key = json.dumps(
                        {"name": call.name, "arguments": call.arguments},
                        sort_keys=True,
                        default=str,
                    )
                    if key in seen:
                        output = {
                            "ok": False,
                            "summary": "Repeated tool call",
                            "error": "You already called this tool with the same arguments. Answer the user.",
                        }
                    else:
                        seen.add(key)
                        output = self.tools.call(call.name, call.arguments)
                    traces.append(
                        {"name": call.name, "ok": bool(output.get("ok")), "summary": output.get("summary", "")}
                    )
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": call.id,
                            "content": _tool_payload(output),
                        }
                    )
            final = self.llm.complete(messages, None)
            content = final.content.strip() or "I ran the tools but could not summarize them."
            return AgentReply(content=content, traces=traces, mode="llm")
        except LlmError as exc:
            logger.warning("llm request failed: %s", exc.message)
            return guide_reply(user_message, self.tools, failed_llm=True)


def _tool_payload(output: dict) -> str:
    if output.get("ok"):
        body: object = output.get("data")
    else:
        body = {"error": output.get("error") or "Tool failed"}
    return json.dumps(body, ensure_ascii=False)[:12_000]
