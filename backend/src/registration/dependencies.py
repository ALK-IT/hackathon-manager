from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.hackathons.repository import HackathonRepository
from src.registration.repository import RegistrationQuestionRepository, RegistrationRepository
from src.registration.service import RegistrationQuestionService, RegistrationService
from src.teams.repository import TeamRepository
from src.teams.service import TeamService


def get_registration_question_service(
    session: AsyncSession = Depends(get_session),
) -> RegistrationQuestionService:
    return RegistrationQuestionService(
        RegistrationQuestionRepository(session),
        HackathonRepository(session),
    )


def get_registration_service(
    session: AsyncSession = Depends(get_session),
) -> RegistrationService:
    return RegistrationService(
        RegistrationRepository(session),
        RegistrationQuestionRepository(session),
        HackathonRepository(session),
        TeamService(TeamRepository(session)),
    )
