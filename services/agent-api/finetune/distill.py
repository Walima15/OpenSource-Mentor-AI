"""Scale the OSMA Mentor dataset by distilling from a strong teacher model.

For a set of repositories, this fetches docs + beginner-friendly issues from
GitHub, builds the real OSMA prompts, asks a teacher model (Anthropic or OpenAI)
for the ideal response, and appends chat-format examples to distilled.jsonl.

Usage (run from services/agent-api):
    python -m finetune.distill --teacher anthropic --repos pallets/flask,psf/requests
Requires the teacher's API key (ANTHROPIC_API_KEY or OPENAI_API_KEY) and,
ideally, GITHUB_FALLBACK_TOKEN for higher GitHub rate limits.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from app.agents import prompts
from app.agents.llm import LLMClient
from app.core.config import settings
from app.services.github_service import GitHubService

DATA_DIR = Path(__file__).parent / "data"
SYSTEM = prompts.SYSTEM_BASE

DEFAULT_REPOS = ["pallets/flask", "psf/requests", "pallets/click"]


def _record(user: str, assistant: str) -> dict:
    return {
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user},
            {"role": "assistant", "content": assistant},
        ]
    }


def _teacher(name: str) -> LLMClient:
    # Build an LLMClient pinned to the teacher provider.
    settings.llm_provider = name
    client = LLMClient()
    client._ensure()  # fail fast if the key is missing
    return client


async def distill_repo(gh: GitHubService, teacher: LLMClient, full_name: str,
                       max_issues: int) -> list[dict]:
    owner, name = full_name.split("/", 1)
    out: list[dict] = []

    meta = await gh.get_repo(owner, name)
    branch = meta.get("default_branch", "main")
    docs = await gh.get_docs(owner, name, branch)
    readme = (docs.get("readme") or "")[:3000]

    # 1) Repo explanation
    repo_prompt = prompts.EXPLAIN_REPO.format(
        repo_full_name=full_name,
        repo_description=meta.get("description") or "(no description)",
        repo_docs=readme,
        context="(no indexed code context)",
    )
    out.append(_record(repo_prompt, teacher.complete(SYSTEM, repo_prompt)))
    print(f"  + repo explanation for {full_name}")

    # 2) Issue explanations + plans
    issues = await gh.list_issues(owner, name, labels=["good first issue"],
                                  limit=max_issues)
    for issue in issues[:max_issues]:
        body = (issue.get("body") or "")[:2500]
        explain_prompt = prompts.EXPLAIN_ISSUE.format(
            repo_full_name=full_name,
            issue_title=issue["title"],
            issue_body=body,
            context="(no indexed code context)",
        )
        out.append(_record(explain_prompt, teacher.complete(SYSTEM, explain_prompt)))

        plan_prompt = prompts.PLAN.format(
            repo_full_name=full_name,
            issue_title=issue["title"],
            issue_body=body,
            context="(no indexed code context)",
        )
        out.append(_record(plan_prompt, teacher.complete(SYSTEM, plan_prompt)))
        print(f"  + issue #{issue['number']} explain+plan")

    return out


async def main_async(args) -> None:
    gh = GitHubService(token=settings.github_fallback_token or None)
    teacher = _teacher(args.teacher)

    all_records: list[dict] = []
    for full_name in args.repos.split(","):
        full_name = full_name.strip()
        if not full_name:
            continue
        print(f"Distilling {full_name}...")
        try:
            all_records.extend(
                await distill_repo(gh, teacher, full_name, args.max_issues)
            )
        except Exception as exc:  # noqa: BLE001
            print(f"  ! skipped {full_name}: {exc}")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("a", encoding="utf-8") as f:
        for rec in all_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"Appended {len(all_records)} examples to {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--teacher", default="anthropic",
                        choices=["anthropic", "openai"])
    parser.add_argument("--repos", default=",".join(DEFAULT_REPOS))
    parser.add_argument("--max-issues", type=int, default=5)
    parser.add_argument("--out", default=str(DATA_DIR / "distilled.jsonl"))
    args = parser.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
