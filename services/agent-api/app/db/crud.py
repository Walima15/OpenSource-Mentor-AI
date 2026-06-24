"""Database access helpers scoped by user where relevant."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import AuthUser, decrypt_token, encrypt_token
from app.db.models import (
    ContributionPlan,
    MentorSession,
    Profile,
    Skill,
    SkillLevel,
    TrackedRepo,
    UserGitHubToken,
)


def get_or_create_profile(db: Session, user: AuthUser) -> Profile:
    profile = db.get(Profile, uuid.UUID(user.id))
    if profile is None:
        profile = Profile(
            id=uuid.UUID(user.id),
            github_username=user.github_username,
        )
        db.add(profile)
        db.flush()
    elif user.github_username and profile.github_username != user.github_username:
        profile.github_username = user.github_username
    return profile


def store_github_token(
    db: Session, user_id: str, access_token: str, scope: str | None
) -> None:
    uid = uuid.UUID(user_id)
    record = db.get(UserGitHubToken, uid)
    encrypted = encrypt_token(access_token)
    if record is None:
        db.add(
            UserGitHubToken(
                user_id=uid, access_token_encrypted=encrypted, scope=scope
            )
        )
    else:
        record.access_token_encrypted = encrypted
        record.scope = scope


def get_github_token(db: Session, user_id: str) -> str | None:
    record = db.get(UserGitHubToken, uuid.UUID(user_id))
    if record is None:
        return None
    return decrypt_token(record.access_token_encrypted)


def _level_for_score(score: int) -> SkillLevel:
    if score >= 70:
        return SkillLevel.advanced
    if score >= 35:
        return SkillLevel.intermediate
    return SkillLevel.beginner


def bump_skill(db: Session, user_id: str, language: str | None, delta: int = 5) -> None:
    """Increment a user's skill score for a language, capped at 100.

    Used to passively track skill growth as the user tracks repos and works on
    contributions. No-op when the language is unknown.
    """
    if not language:
        return
    uid = uuid.UUID(user_id)
    skill = db.scalar(
        select(Skill).where(Skill.user_id == uid, Skill.language == language)
    )
    if skill is None:
        skill = Skill(
            user_id=uid,
            language=language,
            score=min(delta, 100),
            level=_level_for_score(delta),
        )
        db.add(skill)
    else:
        skill.score = min(skill.score + delta, 100)
        skill.level = _level_for_score(skill.score)


def get_user_repo(db: Session, user_id: str, repo_id: uuid.UUID) -> TrackedRepo | None:
    return db.scalar(
        select(TrackedRepo).where(
            TrackedRepo.id == repo_id, TrackedRepo.user_id == uuid.UUID(user_id)
        )
    )


def get_user_session(
    db: Session, user_id: str, session_id: uuid.UUID
) -> MentorSession | None:
    return db.scalar(
        select(MentorSession).where(
            MentorSession.id == session_id,
            MentorSession.user_id == uuid.UUID(user_id),
        )
    )


def get_user_plan(
    db: Session, user_id: str, plan_id: uuid.UUID
) -> ContributionPlan | None:
    return db.scalar(
        select(ContributionPlan)
        .join(MentorSession, ContributionPlan.session_id == MentorSession.id)
        .where(
            ContributionPlan.id == plan_id,
            MentorSession.user_id == uuid.UUID(user_id),
        )
    )
