import time
from fastapi import HTTPException

class RateLimiter:
    def __init__(self, max_requests: int = 100, window_seconds: int = 10):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # key: IP, value: list of timestamps

    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds

        # Initialize if new IP
        if client_ip not in self.requests:
            self.requests[client_ip] = []

        # Remove timestamps outside the window
        self.requests[client_ip] = [
            ts for ts in self.requests[client_ip] if ts > window_start
        ]

        # Check limit
        if len(self.requests[client_ip]) >= self.max_requests:
            return False

        # Record new request
        self.requests[client_ip].append(now)
        return True

    def reset(self):
        """Used by tests to ensure isolation."""
        self.requests.clear()


rate_limiter = RateLimiter()
