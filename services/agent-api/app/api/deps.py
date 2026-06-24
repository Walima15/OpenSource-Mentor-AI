"""Shared FastAPI dependencies."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.security import AuthUser, get_current_user
from app.db.crud import get_github_token, get_or_create_profile
from app.db.session import get_db


def current_user(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    return user


def db_session(db: Session = Depends(get_db)) -> Session:
    return db


def ensure_profile(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
) -> AuthUser:
    """Ensure a profile row exists for the authenticated user."""
    get_or_create_profile(db, user)
    return user


def github_token(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
) -> str | None:
    return get_github_token(db, user.id)
