"""Profile and skill-tracking endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user, db_session
from app.core.security import AuthUser
from app.db.crud import get_or_create_profile, store_github_token
from app.db.models import Skill
from app.schemas.models import (
    GitHubTokenIn,
    ProfileOut,
    ProfileUpdate,
    SkillOut,
    SkillUpsert,
)

router = APIRouter(prefix="/me", tags=["profile"])


@router.get("", response_model=ProfileOut)
def get_me(
    db: Session = Depends(db_session), user: AuthUser = Depends(current_user)
) -> ProfileOut:
    profile = get_or_create_profile(db, user)
    return ProfileOut.model_validate(profile)


@router.patch("", response_model=ProfileOut)
def update_me(
    payload: ProfileUpdate,
    db: Session = Depends(db_session),
    user: AuthUser = Depends(current_user),
) -> ProfileOut:
    profile = get_or_create_profile(db, user)
    if payload.bio is not None:
        profile.bio = payload.bio
    if payload.avatar_url is not None:
        profile.avatar_url = payload.avatar_url
    db.flush()
    return ProfileOut.model_validate(profile)


@router.post("/github-token", status_code=204, response_class=Response)
def save_github_token(
    payload: GitHubTokenIn,
    db: Session = Depends(db_session),
    user: AuthUser = Depends(current_user),
) -> Response:
    get_or_create_profile(db, user)
    store_github_token(db, user.id, payload.access_token, payload.scope)
    return Response(status_code=204)


@router.get("/skills", response_model=list[SkillOut])
def list_skills(
    db: Session = Depends(db_session), user: AuthUser = Depends(current_user)
) -> list[SkillOut]:
    get_or_create_profile(db, user)
    skills = db.scalars(select(Skill).where(Skill.user_id == user.id)).all()
    return [SkillOut.model_validate(s) for s in skills]


@router.post("/skills", response_model=SkillOut)
def upsert_skill(
    payload: SkillUpsert,
    db: Session = Depends(db_session),
    user: AuthUser = Depends(current_user),
) -> SkillOut:
    get_or_create_profile(db, user)
    skill = db.scalar(
        select(Skill).where(
            Skill.user_id == user.id, Skill.language == payload.language
        )
    )
    if skill is None:
        skill = Skill(
            user_id=user.id,
            language=payload.language,
            level=payload.level,
            score=payload.score,
        )
        db.add(skill)
    else:
        skill.level = payload.level
        skill.score = payload.score
    db.flush()
    return SkillOut.model_validate(skill)
