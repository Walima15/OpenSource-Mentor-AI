"""Process-local limits for expensive authenticated operations.

These slow scripted abuse on a single API process. They are not a shared
quota across multiple replicas.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import Depends, HTTPException, status

from app.core.security import AuthUser, get_current_user

# Indexing downloads and embeds a repository.
INDEX_LIMIT = 5
INDEX_WINDOW_SECONDS = 60 * 60

# Explain, plan, and chat calls the LLM.
MENTOR_LIMIT = 30
MENTOR_WINDOW_SECONDS = 10 * 60

# Opening a pull request writes to GitHub.
PR_CREATE_LIMIT = 5
PR_CREATE_WINDOW_SECONDS = 60 * 60


class SlidingWindowLimiter:
    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] > self.window_seconds:
                hits.popleft()
            if len(hits) >= self.limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Try again later.",
                )
            hits.append(now)


index_limiter = SlidingWindowLimiter(INDEX_LIMIT, INDEX_WINDOW_SECONDS)
mentor_limiter = SlidingWindowLimiter(MENTOR_LIMIT, MENTOR_WINDOW_SECONDS)
pr_create_limiter = SlidingWindowLimiter(PR_CREATE_LIMIT, PR_CREATE_WINDOW_SECONDS)


def limit_index(user: AuthUser = Depends(get_current_user)) -> None:
    index_limiter.check(user.id)


def limit_mentor(user: AuthUser = Depends(get_current_user)) -> None:
    mentor_limiter.check(user.id)


def limit_pr_create(user: AuthUser = Depends(get_current_user)) -> None:
    pr_create_limiter.check(user.id)
