"""HTTP API for the local IDE. No shell, commit, push, or pull request."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.rate_limit import client_ip
from app.core.security import ToolError, validate_git_path
from app.workspace import store

router = APIRouter()


class CloneRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project: str = Field(min_length=1, max_length=64)


class PathBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str
    text: str = ""

    @field_validator("path")
    @classmethod
    def _path(cls, value: str) -> str:
        return _path_or_400(value)


class SearchBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(min_length=2, max_length=80)


@router.get("/api/v1/workspaces/projects")
def ide_projects(request: Request) -> dict:
    _limit(request)
    return {"projects": store.list_ide_projects(), "recommended_model": store.RECOMMENDED_CODE_MODEL}


@router.get("/api/v1/workspaces")
def workspaces(request: Request) -> dict:
    _limit(request)
    return {"workspaces": _call(store.list_workspaces)}


@router.post("/api/v1/workspaces")
def clone_workspace(body: CloneRequest, request: Request) -> dict:
    _limit(request)
    return _call(lambda: store.create_catalog_workspace(body.project.strip().lower()))


@router.get("/api/v1/workspaces/{workspace_id}")
def workspace_detail(workspace_id: str, request: Request) -> dict:
    _limit(request)
    return _call(lambda: store.get_workspace(workspace_id))


@router.get("/api/v1/workspaces/{workspace_id}/tree")
def workspace_tree(workspace_id: str, request: Request) -> dict:
    _limit(request)
    return _call(lambda: store.tree(workspace_id))


@router.get("/api/v1/workspaces/{workspace_id}/file")
def workspace_file(workspace_id: str, path: str, request: Request) -> dict:
    _limit(request)
    try:
        relative = validate_git_path(path)
    except ToolError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from None
    return _call(lambda: store.read_file(workspace_id, relative))


@router.post("/api/v1/workspaces/{workspace_id}/file")
def save_workspace_file(workspace_id: str, body: PathBody, request: Request) -> dict:
    _limit(request)
    return _call(lambda: store.write_file(workspace_id, body.path, body.text))


@router.post("/api/v1/workspaces/{workspace_id}/search")
def workspace_search(workspace_id: str, body: SearchBody, request: Request) -> dict:
    _limit(request)
    return _call(lambda: store.search(workspace_id, body.query))


@router.get("/api/v1/workspaces/{workspace_id}/edits")
def workspace_edits(workspace_id: str, request: Request) -> dict:
    _limit(request)
    return {"edits": _call(lambda: store.list_edits(workspace_id))}


@router.post("/api/v1/workspaces/{workspace_id}/edits/{edit_id}/accept")
def accept_edit(workspace_id: str, edit_id: str, request: Request) -> dict:
    _limit(request)
    return _call(lambda: store.accept_edit(workspace_id, edit_id))


@router.post("/api/v1/workspaces/{workspace_id}/edits/{edit_id}/reject")
def reject_edit(workspace_id: str, edit_id: str, request: Request) -> dict:
    _limit(request)
    return _call(lambda: store.reject_edit(workspace_id, edit_id))


def _limit(request: Request) -> None:
    request.app.state.read_limiter.check(f"read:{client_ip(request)}")


def _call(fn):
    try:
        return fn()
    except ToolError as exc:
        status = 404 if exc.message in {"Unknown workspace", "Unknown edit", "File not found"} else 400
        raise HTTPException(status_code=status, detail=exc.message) from None


def _path_or_400(value: str) -> str:
    try:
        return validate_git_path(value)
    except ToolError as exc:
        raise ValueError(exc.message) from None
