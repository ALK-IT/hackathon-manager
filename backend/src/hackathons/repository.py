from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.hackathons.models import Hackathon


class HackathonRepository:
    """Cała komunikacja z tabelą hackathons idzie przez to repozytorium -
    routery i serwisy nigdy nie piszą zapytań SQL bezpośrednio."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_all(self) -> list[Hackathon]:
        result = await self.session.execute(select(Hackathon).order_by(Hackathon.id))
        return list(result.scalars().all())
