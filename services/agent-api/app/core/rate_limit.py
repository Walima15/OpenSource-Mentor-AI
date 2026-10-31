"""In-memory sliding-window rate limit.

One process, one laptop. This is not a distributed limiter. The API is meant
to listen on localhost.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status


class RateLimiter:
    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.monotonic()
        bucket = self._hits[key]
        cutoff = now - self.window_seconds
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= self.limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Wait a minute and try again.",
                headers={"Retry-After": str(self.window_seconds)},
            )
        bucket.append(now)


def client_ip(request: Request) -> str:
    # Ignore X-Forwarded-For. The app binds to localhost; a spoofed header
    # must not reset the limiter.
    if request.client is None:
        return "unknown"
    return request.client.host
