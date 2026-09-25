"""
LexPilot - In-Memory Sliding Window Rate Limiter
------------------------------------------------
Provides lightweight, thread-safe rate limiting per client IP to safeguard
the FastAPI server against automated Denial of Service (DoS) and scraping attacks.
"""

import time
import threading
from collections import defaultdict
from typing import Dict, List, Tuple
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

class RateLimiter:
    """
    Sliding window rate limiter tracking request timestamps per client identifier.
    """
    def __init__(self, max_requests: int = 120, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()
        self._last_cleanup = time.time()

    def is_allowed(self, client_id: str) -> Tuple[bool, int]:
        """
        Determines if the client request is permitted under the rate limit window.
        Returns (is_allowed, remaining_requests).
        """
        now = time.time()

        with self._lock:
            # Periodic cleanup of stale clients every 5 minutes
            if now - self._last_cleanup > 300:
                self._cleanup(now)

            window_start = now - self.window_seconds
            # Filter timestamps outside the sliding window
            valid_timestamps = [t for t in self._requests[client_id] if t > window_start]
            self._requests[client_id] = valid_timestamps

            if len(valid_timestamps) >= self.max_requests:
                return False, 0

            self._requests[client_id].append(now)
            remaining = self.max_requests - len(self._requests[client_id])
            return True, remaining

    def _cleanup(self, now: float):
        window_start = now - self.window_seconds
        stale_keys = [k for k, timestamps in self._requests.items() if not timestamps or timestamps[-1] <= window_start]
        for k in stale_keys:
            del self._requests[k]
        self._last_cleanup = now


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    ASGI middleware enforcing rate limits across all API endpoints.
    Exempts static asset requests, Swagger documentation, and health checks.
    """
    def __init__(self, app, max_requests: int = 120, window_seconds: int = 60):
        super().__init__(app)
        self.limiter = RateLimiter(max_requests=max_requests, window_seconds=window_seconds)

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Exempt health checks, static assets, and documentation
        if path in ("/health", "/api/health", "/docs", "/openapi.json", "/favicon.ico") or path.startswith("/assets/"):
            return await call_next(request)

        # Identify client by IP (respecting proxy X-Forwarded-For if available)
        client_ip = request.headers.get("x-forwarded-for")
        if client_ip:
            client_ip = client_ip.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        allowed, remaining = self.limiter.is_allowed(client_ip)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please wait before submitting additional requests.",
                    "error": "Too Many Requests"
                },
                headers={"Retry-After": str(self.limiter.window_seconds)}
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.limiter.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
