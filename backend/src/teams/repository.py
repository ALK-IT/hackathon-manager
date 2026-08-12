from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.registration.models import Registration
from src.teams.models import Team


class TeamRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_join_code_for_update(
        self,
        join_code: str,
        hackathon_id: int,
    ) -> Team | None:
        statement = (
            select(Team)
            .where(
                Team.join_code == join_code,
                Team.hackathon_id == hackathon_id,
            )
            .with_for_update()
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def count_members(self, team_id: int) -> int:
        statement = select(func.count(Registration.id)).where(Registration.team_id == team_id)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def create(self, team: Team) -> Team:
        self.session.add(team)
        await self.session.flush()
        return team
