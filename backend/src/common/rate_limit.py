from redis.asyncio import Redis

RATE_LIMIT_SCRIPT = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return {current, redis.call('TTL', KEYS[1])}
"""


class FixedWindowRateLimiter:
    def __init__(
        self,
        cache: Redis,
        namespace: str,
        limit: int,
        window_seconds: int,
    ) -> None:
        self.cache = cache
        self.namespace = namespace
        self.limit = limit
        self.window_seconds = window_seconds

    async def consume(self, identifier: str) -> bool:
        allowed, _retry_after = await self.consume_with_retry_after(identifier)
        return allowed

    async def consume_with_retry_after(self, identifier: str) -> tuple[bool, int]:
        key = f"rate-limit:{self.namespace}:{identifier}"
        current, ttl = await self.cache.eval(
            RATE_LIMIT_SCRIPT,
            1,
            key,
            self.window_seconds,
        )
        return int(current) <= self.limit, max(1, int(ttl))
