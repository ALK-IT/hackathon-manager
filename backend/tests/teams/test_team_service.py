from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from src.hackathons.models import Hackathon
from src.teams.exceptions import (
    TeamFullError,
    TeamJoinCodeGenerationError,
    TeamNameAlreadyExistsError,
    TeamNotFoundError,
)
from src.teams.models import Team
from src.teams.schemas import TeamCreateRequest, TeamJoinRequest
from src.teams.service import JOIN_CODE_GENERATION_ATTEMPTS, TeamService


class ConstraintViolation(Exception):
    def __init__(self, constraint_name: str):
        self.constraint_name = constraint_name
        super().__init__(constraint_name)


def make_hackathon(*, hackathon_id: int = 1, max_team_size: int = 4) -> Hackathon:
    start_date = datetime.now(UTC) + timedelta(days=1)
    return Hackathon(
        id=hackathon_id,
        name="AI Hackathon",
        organizer_id=1,
        start_date=start_date,
        end_date=start_date + timedelta(days=2),
        max_team_size=max_team_size,
    )


@pytest.fixture
def team_repository(mocker):
    repository = mocker.Mock()
    repository.create = mocker.AsyncMock()
    repository.get_by_join_code_for_update = mocker.AsyncMock()
    repository.get_by_id_for_update = mocker.AsyncMock()
    repository.count_members = mocker.AsyncMock()
    repository.delete = mocker.AsyncMock()
    return repository


@pytest.fixture
def team_service(team_repository):
    return TeamService(team_repository)


async def test_create_team_builds_and_persists_team(
    team_service,
    team_repository,
    mocker,
):
    hackathon = make_hackathon()
    mocker.patch("src.teams.service.generate_join_code", return_value="ABCD1234")

    result = await team_service.create_team(
        TeamCreateRequest(action="create", name="Byte Buccaneers"),
        hackathon,
    )

    assert isinstance(result, Team)
    assert result.name == "Byte Buccaneers"
    assert result.join_code == "ABCD1234"
    assert result.hackathon_id == hackathon.id
    team_repository.create.assert_awaited_once_with(result)


async def test_create_team_maps_duplicate_name_constraint(
    team_service,
    team_repository,
):
    team_repository.create.side_effect = IntegrityError(
        "INSERT INTO teams",
        {},
        ConstraintViolation("uq_team_hackathon_name"),
    )

    with pytest.raises(TeamNameAlreadyExistsError):
        await team_service.create_team(
            TeamCreateRequest(action="create", name="Byte Buccaneers"),
            make_hackathon(),
        )


async def test_create_team_does_not_hide_unrelated_integrity_error(
    team_service,
    team_repository,
):
    error = IntegrityError(
        "INSERT INTO teams",
        {},
        ConstraintViolation("some_other_constraint"),
    )
    team_repository.create.side_effect = error

    with pytest.raises(IntegrityError) as raised:
        await team_service.create_team(
            TeamCreateRequest(action="create", name="Byte Buccaneers"),
            make_hackathon(),
        )

    assert raised.value is error


async def test_create_team_retries_join_code_collision(
    team_service,
    team_repository,
    mocker,
):
    collision = IntegrityError(
        "INSERT INTO teams",
        {},
        ConstraintViolation("teams_join_code_key"),
    )
    team_repository.create.side_effect = [collision, None]
    generate = mocker.patch(
        "src.teams.service.generate_join_code",
        side_effect=["COLLIDE1", "UNIQUE12"],
    )

    result = await team_service.create_team(
        TeamCreateRequest(action="create", name="Byte Buccaneers"),
        make_hackathon(),
    )

    assert result.join_code == "UNIQUE12"
    assert team_repository.create.await_count == 2
    assert generate.call_count == 2


async def test_create_team_returns_domain_error_after_join_code_retries(
    team_service,
    team_repository,
):
    team_repository.create.side_effect = IntegrityError(
        "INSERT INTO teams",
        {},
        ConstraintViolation("teams_join_code_key"),
    )

    with pytest.raises(TeamJoinCodeGenerationError):
        await team_service.create_team(
            TeamCreateRequest(action="create", name="Byte Buccaneers"),
            make_hackathon(),
        )

    assert team_repository.create.await_count == JOIN_CODE_GENERATION_ATTEMPTS


async def test_join_team_returns_team_when_it_has_available_places(
    team_service,
    team_repository,
):
    hackathon = make_hackathon(hackathon_id=10, max_team_size=4)
    team = Team(id=20, hackathon_id=hackathon.id, name="Crew", join_code="ABCD1234")
    team_repository.get_by_join_code_for_update.return_value = team
    team_repository.count_members.return_value = 3

    result = await team_service.join_team(
        TeamJoinRequest(action="join", join_code="ABCD1234"),
        hackathon,
    )

    assert result is team
    team_repository.get_by_join_code_for_update.assert_awaited_once_with(
        "ABCD1234",
        hackathon.id,
    )
    team_repository.count_members.assert_awaited_once_with(team.id)


async def test_join_team_rejects_missing_team(
    team_service,
    team_repository,
):
    hackathon = make_hackathon(hackathon_id=10)
    team_repository.get_by_join_code_for_update.return_value = None

    with pytest.raises(TeamNotFoundError):
        await team_service.join_team(
            TeamJoinRequest(action="join", join_code="ABCD1234"),
            hackathon,
        )

    team_repository.get_by_join_code_for_update.assert_awaited_once_with(
        "ABCD1234",
        hackathon.id,
    )
    team_repository.count_members.assert_not_awaited()


async def test_join_team_rejects_team_at_member_limit(
    team_service,
    team_repository,
):
    hackathon = make_hackathon(hackathon_id=10, max_team_size=4)
    team = Team(id=20, hackathon_id=hackathon.id, name="Crew", join_code="ABCD1234")
    team_repository.get_by_join_code_for_update.return_value = team
    team_repository.count_members.return_value = 4

    with pytest.raises(TeamFullError):
        await team_service.join_team(
            TeamJoinRequest(action="join", join_code="ABCD1234"),
            hackathon,
        )


async def test_delete_if_empty_removes_locked_team(
    team_service,
    team_repository,
):
    team = Team(id=20, hackathon_id=10, name="Crew", join_code="ABCD1234")
    team_repository.get_by_id_for_update.return_value = team
    team_repository.count_members.return_value = 0

    await team_service.delete_if_empty(team.id)

    team_repository.get_by_id_for_update.assert_awaited_once_with(team.id)
    team_repository.count_members.assert_awaited_once_with(team.id)
    team_repository.delete.assert_awaited_once_with(team)


async def test_delete_if_empty_keeps_team_with_members(
    team_service,
    team_repository,
):
    team = Team(id=20, hackathon_id=10, name="Crew", join_code="ABCD1234")
    team_repository.get_by_id_for_update.return_value = team
    team_repository.count_members.return_value = 1

    await team_service.delete_if_empty(team.id)

    team_repository.delete.assert_not_awaited()


async def test_resolve_team_returns_none_without_selection(team_service):
    result = await team_service.resolve_team(None, make_hackathon())

    assert result is None


@pytest.mark.parametrize(
    ("selection", "method_name"),
    [
        (TeamCreateRequest(action="create", name="Crew"), "create_team"),
        (TeamJoinRequest(action="join", join_code="ABCD1234"), "join_team"),
    ],
)
async def test_resolve_team_delegates_selection_to_matching_operation(
    team_service,
    mocker,
    selection,
    method_name,
):
    hackathon = make_hackathon()
    team = Team(id=20, hackathon_id=hackathon.id, name="Crew", join_code="ABCD1234")
    operation = mocker.patch.object(
        team_service, method_name, new=mocker.AsyncMock(return_value=team)
    )

    result = await team_service.resolve_team(selection, hackathon)

    assert result is team
    operation.assert_awaited_once_with(selection, hackathon)
