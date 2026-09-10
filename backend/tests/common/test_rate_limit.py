import os
import uuid

from redis.asyncio import Redis, from_url

from src.common.rate_limit import SlidingWindowRateLimiter


def make_limiter(cache: Redis) -> SlidingWindowRateLimiter:
    return SlidingWindowRateLimiter(
        cache=cache,
        namespace="test",
        limit=2,
        window_seconds=60,
    )


async def test_first_request_is_allowed(mocker):
    cache = mocker.Mock(spec=Redis)
    script = mocker.AsyncMock(return_value=[1, 0])
    cache.register_script.return_value = script
    limiter = make_limiter(cache)

    assert await limiter.consume("user-id") is True

    cache.register_script.assert_called_once()
    script.assert_awaited_once_with(
        keys=["rate-limit:test:sliding:user-id"],
        args=[60, 2],
    )


async def test_existing_counter_allows_request_within_limit(mocker):
    cache = mocker.Mock(spec=Redis)
    cache.register_script.return_value = mocker.AsyncMock(return_value=[1, 0])
    limiter = make_limiter(cache)

    assert await limiter.consume("user-id") is True


async def test_existing_counter_rejects_request_above_limit(mocker):
    cache = mocker.Mock(spec=Redis)
    cache.register_script.return_value = mocker.AsyncMock(return_value=[0, 42])
    limiter = make_limiter(cache)

    assert await limiter.consume("user-id") is False


async def test_retry_after_uses_value_calculated_by_script(mocker):
    cache = mocker.Mock(spec=Redis)
    cache.register_script.return_value = mocker.AsyncMock(return_value=[0, 17])
    limiter = make_limiter(cache)

    assert await limiter.consume_with_retry_after("user-id") == (False, 17)


async def test_sliding_window_counts_the_previous_window_in_real_redis():
    cache: Redis = from_url(
        os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
        decode_responses=True,
    )
    namespace = f"test-{uuid.uuid4()}"
    limiter = SlidingWindowRateLimiter(cache, namespace, limit=2, window_seconds=60)
    identifier = "user-id"
    key = f"rate-limit:{namespace}:sliding:{identifier}"
    now, _microseconds = await cache.time()
    window_start = now - (now % 60)

    try:
        await cache.hset(
            key,
            mapping={
                "window_start": window_start - 60,
                "current_count": 120,
                "previous_count": 0,
            },
        )

        allowed, retry_after = await limiter.consume_with_retry_after(identifier)

        assert allowed is False
        assert retry_after > 0
    finally:
        await cache.delete(key)
        await cache.aclose()
