"""Tool registry used by the mentor loop and the HTTP API."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from app.core.logging import get_logger
from app.core.security import ToolError
from app.github.client import GitHubClient
from app.tools.curriculum import (
    explain_concept,
    get_lesson,
    get_quiz,
    grade_quiz,
    list_learning_paths,
)
from app.tools.github_tools import (
    explain_file,
    explain_repository,
    find_good_first_issues,
    plan_contribution,
    review_diff,
    review_pull_request,
)
from app.tools.projects import get_project_guide, list_projects

logger = get_logger(__name__)

_OBJECT = "object"


def _schema(properties: dict, required: list[str]) -> dict:
    return {
        "type": _OBJECT,
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    parameters: dict
    handler: Callable[[dict], dict]


class ToolRegistry:
    def __init__(self, tools: list[Tool]):
        self._tools = {tool.name: tool for tool in tools}

    def names(self) -> list[str]:
        return list(self._tools)

    def schemas(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
            for tool in self._tools.values()
        ]

    def call(self, name: str, arguments: dict | None) -> dict:
        tool = self._tools.get(name)
        if tool is None:
            return {"ok": False, "summary": "Unknown tool", "error": f"Unknown tool: {name}"}
        try:
            data = tool.handler(arguments or {})
        except ToolError as exc:
            logger.info("tool %s rejected the request", name)
            return {"ok": False, "summary": exc.message, "error": exc.message}
        except Exception:
            logger.exception("tool %s failed", name)
            return {"ok": False, "summary": "Tool failed", "error": "Tool failed"}
        if not isinstance(data, dict):
            return {"ok": False, "summary": "Tool failed", "error": "Tool failed"}
        summary = str(data.get("summary") or name)[:300]
        return {"ok": True, "summary": summary, "data": data}


def build_registry(github: GitHubClient) -> ToolRegistry:
    string = {"type": "string"}
    integer = {"type": "integer"}
    return ToolRegistry(
        [
            Tool(
                "list_learning_paths",
                "List OSMA learning paths and their lessons.",
                _schema({}, []),
                lambda args: list_learning_paths(args),
            ),
            Tool(
                "get_lesson",
                "Return one lesson, including its teaching notes. Quiz answers are not included.",
                _schema({"lesson_id": string}, ["lesson_id"]),
                get_lesson,
            ),
            Tool(
                "get_quiz",
                "Return quiz questions for a lesson, without the correct answers.",
                _schema({"lesson_id": string}, ["lesson_id"]),
                get_quiz,
            ),
            Tool(
                "grade_quiz",
                "Grade a list of choice indexes for a lesson quiz.",
                _schema(
                    {
                        "lesson_id": string,
                        "answers": {"type": "array", "items": integer},
                    },
                    ["lesson_id", "answers"],
                ),
                grade_quiz,
            ),
            Tool(
                "explain_concept",
                (
                    "Explain a Bitcoin or contribution concept from the curriculum. "
                    "Use for UTXOs, transactions, scripts, blocks, consensus, peer-to-peer, "
                    "mempool, BIPs, Lightning, ACK/NACK, and similar questions."
                ),
                _schema({"query": string}, ["query"]),
                explain_concept,
            ),
            Tool(
                "list_projects",
                "List curated Bitcoin open-source projects.",
                _schema({"language": string}, []),
                lambda args: list_projects(args),
            ),
            Tool(
                "get_project_guide",
                "Return the setup, test, and contributing guide for one curated project.",
                _schema({"project": string}, ["project"]),
                get_project_guide,
            ),
            Tool(
                "find_good_first_issues",
                "Fetch open good-first-issue style GitHub issues for a curated project or owner/repo.",
                _schema(
                    {
                        "project": string,
                        "owner": string,
                        "repo": string,
                        "limit": integer,
                    },
                    [],
                ),
                lambda args: find_good_first_issues(github, args),
            ),
            Tool(
                "explain_repository",
                (
                    "Fetch a repository overview: description, README excerpt, top-level files, "
                    "and the OSMA code map when the repo is curated."
                ),
                _schema({"project": string, "owner": string, "repo": string}, []),
                lambda args: explain_repository(github, args),
            ),
            Tool(
                "explain_file",
                (
                    "Fetch one file from a GitHub repository and add a short reading hint. "
                    "Path must stay inside the repo."
                ),
                _schema(
                    {"project": string, "owner": string, "repo": string, "path": string, "ref": string},
                    ["path"],
                ),
                lambda args: explain_file(github, args),
            ),
            Tool(
                "plan_contribution",
                (
                    "Draft a contribution plan for a repository, optionally from a GitHub "
                    "issue number and a goal."
                ),
                _schema(
                    {
                        "project": string,
                        "owner": string,
                        "repo": string,
                        "issue_number": integer,
                        "goal": string,
                    },
                    [],
                ),
                lambda args: plan_contribution(github, args),
            ),
            Tool(
                "review_pull_request",
                (
                    "Fetch a pull request, its files, and a diff excerpt, plus Bitcoin-project "
                    "review conventions. Never ACK on the user's behalf."
                ),
                _schema(
                    {"project": string, "owner": string, "repo": string, "number": integer},
                    ["number"],
                ),
                lambda args: review_pull_request(github, args),
            ),
            Tool(
                "review_diff",
                (
                    "Review a unified diff the user pasted, using Bitcoin-project review "
                    "conventions. Never ACK on the user's behalf."
                ),
                _schema({"diff": string, "project": string}, ["diff"]),
                review_diff,
            ),
        ]
    )
