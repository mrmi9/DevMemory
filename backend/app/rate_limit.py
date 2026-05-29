from collections import defaultdict, deque
import time
from typing import Callable

from fastapi import HTTPException, status


class InMemoryRateLimiter:
    def __init__(self, clock: Callable[[], float] | None = None):
        self._clock = clock or time.monotonic
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def assert_allowed(self, key: str, limit: int, window_seconds: int, detail: str) -> None:
        if limit <= 0:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=detail)
        now = self._clock()
        events = self._events[key]
        window_start = now - window_seconds
        while events and events[0] <= window_start:
            events.popleft()
        if len(events) >= limit:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=detail)
        events.append(now)
