import json

from redis.asyncio import Redis

from app.repositories.hackathon_repository import HackathonRepository

CACHE_KEY = "hackathons:list"
CACHE_TTL_SECONDS = 60


class HackathonService:
    """Logika biznesowa: decyzja cache-vs-baza żyje tutaj, nie w routerze
    ani w repozytorium. Wzorzec cache-aside: cache -> miss -> baza -> zapisz do cache."""

    def __init__(self, repository: HackathonRepository, cache: Redis):
        self.repository = repository
        self.cache = cache

    async def list_hackathons(self) -> list[dict]:
        cached = await self.cache.get(CACHE_KEY)
        if cached is not None:
            return json.loads(cached)

        hackathons = await self.repository.list_all()
        data = [{"id": h.id, "name": h.name} for h in hackathons]
        await self.cache.set(CACHE_KEY, json.dumps(data), ex=CACHE_TTL_SECONDS)
        return data
