"""Authentication and secret-handling utilities.

Supabase issues session JWTs signed with the project's JWT secret (HS256).
We validate the Bearer token on each request and use the `sub` claim as the
canonical user id. GitHub provider tokens are encrypted at rest with Fernet.
"""

from __future__ import annotations

import base64
import hashlib

import jwt
from cryptography.fernet import Fernet, InvalidToken
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_bearer = HTTPBearer(auto_error=False)


class AuthUser:
    """Lightweight authenticated principal extracted from the JWT."""

    def __init__(self, user_id: str, email: str | None, claims: dict):
        self.id = user_id
        self.email = email
        self.claims = claims

    @property
    def github_username(self) -> str | None:
        meta = self.claims.get("user_metadata", {})
        return meta.get("user_name") or meta.get("preferred_username")


def decode_supabase_jwt(token: str) -> dict:
    if not settings.supabase_jwt_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SUPABASE_JWT_SECRET is not configured",
        )
    try:
        return jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
            options={"verify_aud": True},
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        ) from exc
    except jwt.PyJWTError as exc:
        logger.warning("JWT validation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from exc


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> AuthUser:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )
    claims = decode_supabase_jwt(credentials.credentials)
    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing subject"
        )
    return AuthUser(user_id=user_id, email=claims.get("email"), claims=claims)


# ---------------------------------------------------------------------------
# Token encryption (Fernet)
# ---------------------------------------------------------------------------
def enforce_production_security() -> None:
    """Refuse to start in production without an explicit encryption key.

    Development may leave the key unset and derive one from the JWT secret
    at encrypt time. A shared hardcoded key is never used.
    """
    key = (settings.token_encryption_key or "").strip()
    if settings.is_production and not key:
        raise RuntimeError(
            "TOKEN_ENCRYPTION_KEY must be set when APP_ENV=production"
        )
    if key:
        try:
            Fernet(key.encode())
        except (ValueError, TypeError) as exc:
            raise RuntimeError(
                "TOKEN_ENCRYPTION_KEY is not a valid Fernet key"
            ) from exc


def _fernet() -> Fernet:
    key = (settings.token_encryption_key or "").strip()
    if not key:
        if settings.is_production:
            enforce_production_security()
        secret = (settings.supabase_jwt_secret or "").strip()
        if not secret:
            raise RuntimeError(
                "Set TOKEN_ENCRYPTION_KEY (or SUPABASE_JWT_SECRET in development) "
                "before storing GitHub tokens"
            )
        digest = hashlib.sha256(secret.encode()).digest()
        key = base64.urlsafe_b64encode(digest).decode()
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_token(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext: str) -> str:
    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stored GitHub token could not be decrypted",
        ) from exc
