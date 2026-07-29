from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Hackathon


class HackathonRepository:
    """Cała komunikacja z tabelą hackathons idzie przez to repozytorium -
    routery i serwisy nigdy nie piszą zapytań SQL bezpośrednio."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_all(self) -> list[Hackathon]:
        result = await self.session.execute(select(Hackathon).order_by(Hackathon.id))
        return list(result.scalars().all())

    async def create(self, name: str) -> Hackathon:
        hackathon = Hackathon(name=name)
        self.session.add(hackathon)
        await self.session.commit()
        await self.session.refresh(hackathon)
        return hackathon

    async def update(self, hackathon_id: int, name: str) -> Hackathon | None:
        hackathon = await self.session.get(Hackathon, hackathon_id)
        if hackathon is None:
            return None

        hackathon.name = name
        await self.session.commit()
        await self.session.refresh(hackathon)
        return hackathon

    async def delete(self, hackathon_id: int) -> bool:
        hackathon = await self.session.get(Hackathon, hackathon_id)
        if hackathon is None:
            return False

        await self.session.delete(hackathon)
        await self.session.commit()
        return True
