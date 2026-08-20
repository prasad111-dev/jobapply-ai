import time
from collections import defaultdict
from functools import wraps
from fastapi import HTTPException, Request

class SlidingWindowRateLimiter:
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.store = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        self.store[key] = [t for t in self.store[key] if now - t < self.window_seconds]
        if len(self.store[key]) >= self.max_requests:
            return False
        self.store[key].append(now)
        return True

    def get_remaining(self, key: str) -> int:
        now = time.time()
        self.store[key] = [t for t in self.store[key] if now - t < self.window_seconds]
        return max(0, self.max_requests - len(self.store[key]))

api_limiter = SlidingWindowRateLimiter(max_requests=60, window_seconds=60)
auth_limiter = SlidingWindowRateLimiter(max_requests=10, window_seconds=60)
apply_limiter = SlidingWindowRateLimiter(max_requests=20, window_seconds=300)

def rate_limit(limiter: SlidingWindowRateLimiter):
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            client_ip = request.client.host if request.client else "unknown"
            if not limiter.is_allowed(client_ip):
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Try again later.",
                    headers={"X-RateLimit-Remaining": str(limiter.get_remaining(client_ip))}
                )
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
