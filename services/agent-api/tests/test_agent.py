"""Mentor loop: guide mode and a scripted tool-calling model."""

from __future__ import annotations

from app.agent.fallback import guide_reply
from app.agent.mentor import MentorAgent
from app.llm.client import LlmError, LlmResult, ToolCall
from app.tools.registry import build_registry
from tests.fakes import FakeGitHub


class ScriptedLlm:
    configured = True

    def __init__(self):
        self.calls = 0

    def complete(self, messages, tools):
        self.calls += 1
        if self.calls == 1:
            assert tools
            raw = '{"query":"utxo"}'
            call = ToolCall(id="call_1", name="explain_concept", arguments={"query": "utxo"}, raw_arguments=raw)
            return LlmResult(
                content="",
                tool_calls=[call],
                assistant_message={
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {"name": "explain_concept", "arguments": raw},
                        }
                    ],
                },
            )
        tool_messages = [message for message in messages if message.get("role") == "tool"]
        assert tool_messages
        assert "unspent" in tool_messages[-1]["content"].lower()
        return LlmResult(
            content="A UTXO is an unspent transaction output. Wallets sum the ones you can spend.",
            assistant_message={"role": "assistant", "content": "done"},
        )


class BoomLlm:
    configured = True

    def complete(self, messages, tools):
        raise LlmError("LLM request failed (401)")


def _tools():
    return build_registry(FakeGitHub())


def test_guide_mode_explains_utxos_without_a_model():
    reply = guide_reply("Explain UTXOs", _tools())
    assert reply.mode == "guide"
    assert "Guide mode" in reply.content
    assert "unspent" in reply.content.lower()
    assert reply.traces[0]["name"] == "explain_concept"


def test_guide_mode_reviews_without_acking():
    reply = guide_reply("Please review https://github.com/bitcoin/bitcoin/pull/10", _tools())
    assert reply.traces[0]["name"] == "review_pull_request"
    assert "Do not ACK" in reply.content
    assert "Concept ACK" in reply.content


def test_scripted_model_uses_the_tool_then_answers():
    agent = MentorAgent(ScriptedLlm(), _tools())
    reply = agent.reply([], "What is a UTXO?")
    assert reply.mode == "llm"
    assert "Guide mode" not in reply.content
    assert "unspent transaction output" in reply.content
    assert reply.traces[0]["name"] == "explain_concept"
    assert reply.traces[0]["ok"] is True


def test_model_failure_falls_back_to_the_guide():
    agent = MentorAgent(BoomLlm(), _tools())
    reply = agent.reply([], "Explain UTXOs")
    assert reply.mode == "guide"
    assert "offline guide" in reply.content
    assert "unspent" in reply.content.lower()
