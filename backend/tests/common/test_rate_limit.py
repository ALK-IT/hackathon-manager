from redis.asyncio import Redis

from src.common.rate_limit import FixedWindowRateLimiter


def make_limiter(cache: Redis) -> FixedWindowRateLimiter:
    return FixedWindowRateLimiter(
        cache=cache,
        namespace="test",
        limit=2,
        window_seconds=60,
    )


async def test_first_request_creates_counter_with_expiration(mocker):
    cache = mocker.Mock(spec=Redis)
    cache.set = mocker.AsyncMock(return_value=True)
    cache.incr = mocker.AsyncMock()
    limiter = make_limiter(cache)

    assert await limiter.consume("user-id") is True

    cache.set.assert_awaited_once_with(
        "rate-limit:test:user-id",
        "1",
        ex=60,
        nx=True,
    )
    cache.incr.assert_not_awaited()


async def test_existing_counter_allows_request_within_limit(mocker):
    cache = mocker.Mock(spec=Redis)
    cache.set = mocker.AsyncMock(return_value=False)
    cache.incr = mocker.AsyncMock(return_value=2)
    limiter = make_limiter(cache)

    assert await limiter.consume("user-id") is True


async def test_existing_counter_rejects_request_above_limit(mocker):
    cache = mocker.Mock(spec=Redis)
    cache.set = mocker.AsyncMock(return_value=False)
    cache.incr = mocker.AsyncMock(return_value=3)
    limiter = make_limiter(cache)

    assert await limiter.consume("user-id") is False
