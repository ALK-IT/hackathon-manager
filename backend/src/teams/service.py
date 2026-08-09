from sqlalchemy.exc import IntegrityError

from src.database import get_integrity_error_constraint
from src.hackathons.models import Hackathon
from src.teams.exceptions import TeamFullError, TeamNameAlreadyExistsError, TeamNotFoundError
from src.teams.models import Team
from src.teams.repository import TeamRepository
from src.teams.schemas import TeamCreateRequest, TeamJoinRequest, TeamSelection
from src.teams.utils import generate_join_code


class TeamService:
    def __init__(self, repository: TeamRepository) -> None:
        self.repository = repository

    async def create_team(self, request: TeamCreateRequest, hackathon: Hackathon) -> Team:
        team = Team(name=request.name, hackathon=hackathon, join_code=generate_join_code())
        try:
            await self.repository.create(team)
        except IntegrityError as error:
            if get_integrity_error_constraint(error) == "uq_team_hackathon_name":
                raise TeamNameAlreadyExistsError() from error
            raise
        return team

    async def join_team(self, request: TeamJoinRequest, hackathon: Hackathon) -> Team:
        team = await self.repository.get_by_join_code_for_update(
            request.join_code,
            hackathon.id,
        )
        if team is None:
            raise TeamNotFoundError()
        member_count = await self.repository.count_members(team.id)
        if member_count >= hackathon.max_team_size:
            raise TeamFullError()
        return team

    async def resolve_team(
        self, selection: TeamSelection | None, hackathon: Hackathon
    ) -> Team | None:
        if selection is None:
            return None
        if isinstance(selection, TeamCreateRequest):
            return await self.create_team(selection, hackathon)
        elif isinstance(selection, TeamJoinRequest):
            return await self.join_team(selection, hackathon)
        return None
