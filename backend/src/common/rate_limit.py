from redis.asyncio import Redis


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
        key = f"rate-limit:{self.namespace}:{identifier}"
        created = await self.cache.set(
            key,
            "1",
            ex=self.window_seconds,
            nx=True,
        )
        if created:
            return True

        request_count = await self.cache.incr(key)
        return request_count <= self.limit
