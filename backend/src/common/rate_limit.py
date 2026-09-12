from redis.asyncio import Redis

SLIDING_WINDOW_SCRIPT = """
local window = tonumber(ARGV[1])
local limit = tonumber(ARGV[2])
local redis_time = redis.call('TIME')
local now = tonumber(redis_time[1])
local window_start = now - (now % window)

local stored_start = tonumber(redis.call('HGET', KEYS[1], 'window_start'))
local current = tonumber(redis.call('HGET', KEYS[1], 'current_count') or '0')
local previous = tonumber(redis.call('HGET', KEYS[1], 'previous_count') or '0')

if not stored_start or stored_start ~= window_start then
  if stored_start == window_start - window then
    previous = current
  else
    previous = 0
  end
  current = 0
  stored_start = window_start
end

current = current + 1
redis.call(
  'HSET',
  KEYS[1],
  'window_start', stored_start,
  'current_count', current,
  'previous_count', previous
)
redis.call('EXPIRE', KEYS[1], window * 2 + 1)

local elapsed = now - window_start
local estimated_count = current + previous * (window - elapsed) / window
local allowed = estimated_count <= limit and 1 or 0
local retry_after = 0

if allowed == 0 then
  local next_current = current + 1
  if previous > 0 and next_current <= limit then
    local required_elapsed = window - ((limit - next_current) * window / previous)
    retry_after = math.ceil(required_elapsed - elapsed)
  else
    local remaining = window - elapsed
    local next_window_elapsed = math.ceil(window * (current - (limit - 1)) / current)
    retry_after = remaining + math.max(0, math.min(window, next_window_elapsed))
  end
  retry_after = math.max(1, retry_after)
end

return {allowed, retry_after}
"""


class SlidingWindowRateLimiter:
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
        self._script = cache.register_script(SLIDING_WINDOW_SCRIPT)

    async def consume(self, identifier: str) -> bool:
        allowed, _retry_after = await self.consume_with_retry_after(identifier)
        return allowed

    async def consume_with_retry_after(self, identifier: str) -> tuple[bool, int]:
        key = f"rate-limit:{self.namespace}:sliding:{identifier}"
        allowed, retry_after = await self._script(
            keys=[key],
            args=[self.window_seconds, self.limit],
        )
        return int(allowed) == 1, int(retry_after)
