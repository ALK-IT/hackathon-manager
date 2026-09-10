from redis.asyncio import Redis

from src.common.rate_limit import FixedWindowRateLimiter


def make_limiter(cache: Redis) -> FixedWindowRateLimiter:
    return FixedWindowRateLimiter(
        cache=cache,
        namespace="test",
        limit=2,
        window_seconds=60,
    )


async def test_first_request_is_allowed(mocker):
    cache = mocker.Mock(spec=Redis)
    cache.eval = mocker.AsyncMock(return_value=[1, 60])
    limiter = make_limiter(cache)

    assert await limiter.consume("user-id") is True

    eval_args = cache.eval.await_args.args
    assert eval_args[1:] == (1, "rate-limit:test:user-id", 60)


async def test_existing_counter_allows_request_within_limit(mocker):
    cache = mocker.Mock(spec=Redis)
    cache.eval = mocker.AsyncMock(return_value=[2, 42])
    limiter = make_limiter(cache)

    assert await limiter.consume("user-id") is True


async def test_existing_counter_rejects_request_above_limit(mocker):
    cache = mocker.Mock(spec=Redis)
    cache.eval = mocker.AsyncMock(return_value=[3, 42])
    limiter = make_limiter(cache)

    assert await limiter.consume("user-id") is False


async def test_retry_after_uses_remaining_redis_ttl(mocker):
    cache = mocker.Mock(spec=Redis)
    cache.eval = mocker.AsyncMock(return_value=[3, 17])
    limiter = make_limiter(cache)

    assert await limiter.consume_with_retry_after("user-id") == (False, 17)
