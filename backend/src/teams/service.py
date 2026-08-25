from sqlalchemy.exc import IntegrityError

from src.auth.models import User
from src.common.sqlalchemy import get_integrity_error_constraint
from src.hackathons.models import Hackathon
from src.teams.exceptions import (
    TeamFullError,
    TeamJoinCodeGenerationError,
    TeamNameAlreadyExistsError,
    TeamNotFoundError,
    TeamsDisabledError,
)
from src.teams.models import Team
from src.teams.repository import TeamRepository
from src.teams.schemas import TeamCreateRequest, TeamJoinRequest, TeamSelection
from src.teams.utils import generate_join_code

JOIN_CODE_GENERATION_ATTEMPTS = 5
JOIN_CODE_CONSTRAINTS = {"teams_join_code_key", "uq_team_join_code"}


class TeamService:
    def __init__(self, repository: TeamRepository) -> None:
        self.repository = repository

    async def create_team(self, request: TeamCreateRequest, hackathon: Hackathon) -> Team:
        self._ensure_teams_enabled(hackathon)
        for attempt in range(JOIN_CODE_GENERATION_ATTEMPTS):
            team = Team(
                name=request.name,
                hackathon_id=hackathon.id,
                join_code=generate_join_code(),
            )
            try:
                await self.repository.create(team)
                return team
            except IntegrityError as error:
                constraint = get_integrity_error_constraint(error)
                if constraint == "uq_team_hackathon_name":
                    raise TeamNameAlreadyExistsError() from error
                if constraint not in JOIN_CODE_CONSTRAINTS:
                    raise
                if attempt == JOIN_CODE_GENERATION_ATTEMPTS - 1:
                    raise TeamJoinCodeGenerationError() from error

        raise TeamJoinCodeGenerationError

    async def join_team(self, request: TeamJoinRequest, hackathon: Hackathon) -> Team:
        self._ensure_teams_enabled(hackathon)
        team = await self.repository.get_by_join_code_for_update(
            request.join_code,
            hackathon.id,
        )
        if team is None:
            raise TeamNotFoundError()
        member_count = await self.repository.count_active_members(team.id)
        if member_count >= hackathon.max_team_size:
            raise TeamFullError()
        return team

    async def ensure_member_can_be_activated(
        self,
        team_id: int,
        max_team_size: int,
    ) -> None:
        team = await self.repository.get_by_id_for_update(team_id)
        if team is None:
            raise TeamNotFoundError()
        if await self.repository.count_active_members(team_id) >= max_team_size:
            raise TeamFullError()

    async def delete_if_empty(self, team_id: int) -> None:
        team = await self.repository.get_by_id_for_update(team_id)
        if team is None:
            return
        if await self.repository.count_registrations(team_id) == 0:
            await self.repository.delete(team)

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

    async def list_accepted_users(self, team_id: int) -> list[User]:
        return await self.repository.get_members(team_id)

    @staticmethod
    def _ensure_teams_enabled(hackathon: Hackathon) -> None:
        if not hackathon.teams_enabled:
            raise TeamsDisabledError()
