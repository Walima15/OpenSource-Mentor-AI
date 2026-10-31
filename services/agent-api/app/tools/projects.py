"""Project catalog tools."""

from __future__ import annotations

import re

from app.content.loader import PROJECTS, Project
from app.core.security import ToolError, validate_slug
from app.tools.util import optional_str


def list_projects(args: dict | None = None) -> dict:
    args = args or {}
    language = optional_str(args, "language", 40)
    projects = list(PROJECTS.values())
    if language:
        needle = language.lower()
        projects = [project for project in projects if needle in project.language.lower()]
    projects.sort(key=lambda project: project.name.lower())
    return {
        "summary": f"{len(projects)} Bitcoin open-source projects",
        "projects": [_card(project) for project in projects],
    }


def get_project_guide(args: dict) -> dict:
    project = _resolve(args)
    payload = project.model_dump()
    payload["summary"] = f"Setup guide for {project.name}"
    payload["html_url"] = f"https://github.com/{project.owner}/{project.repo}"
    return payload


def resolve_project_arg(args: dict) -> Project | None:
    slug = optional_str(args, "project", 64)
    if slug:
        return _by_slug(slug)
    query = optional_str(args, "query", 120)
    if query:
        return match_project(query)
    return None


def match_project(text: str) -> Project | None:
    lowered = text.lower()
    best: tuple[int, Project] | None = None
    for project in PROJECTS.values():
        score = 0
        if re.search(rf"\b{re.escape(project.slug)}\b", lowered):
            score += 8
        if project.slug.replace("-", " ") in lowered:
            score += 6
        for alias in project.aliases:
            if _alias_hit(lowered, alias.lower()):
                score += max(len(alias), 5)
        if score and (best is None or score > best[0]):
            best = (score, project)
    return best[1] if best else None


def _alias_hit(text: str, alias: str) -> bool:
    if len(alias) <= 4:
        return re.search(rf"\b{re.escape(alias)}\b", text) is not None
    return alias in text


def _resolve(args: dict) -> Project:
    slug = optional_str(args, "slug", 64) or optional_str(args, "project", 64)
    if not slug:
        query = optional_str(args, "query", 120)
        if query:
            found = match_project(query)
            if found:
                return found
        raise ToolError("project slug is required")
    return _by_slug(slug)


def _by_slug(slug: str) -> Project:
    try:
        key = validate_slug(slug)
    except ToolError:
        found = match_project(slug)
        if found:
            return found
        raise
    project = PROJECTS.get(key)
    if project is None:
        found = match_project(slug)
        if found:
            return found
        raise ToolError(f"Unknown project {key}")
    return project


def _card(project: Project) -> dict:
    return {
        "slug": project.slug,
        "name": project.name,
        "owner": project.owner,
        "repo": project.repo,
        "language": project.language,
        "difficulty": project.difficulty,
        "summary": project.summary,
        "tags": project.tags,
        "html_url": f"https://github.com/{project.owner}/{project.repo}",
    }

