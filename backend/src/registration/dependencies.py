from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.registration.service import RegistrationService, RegistrationQuestionService
from src.registration.repository import RegistrationRepository, RegistrationQuestionRepository
from src.hackathons.repository import HackathonRepository
from src.database import get_session


def get_registration_question_service(
    session: AsyncSession = Depends(get_session),
) -> RegistrationQuestionRepository:
    return RegistrationQuestionService(
        RegistrationQuestionRepository(session),
        HackathonRepository(session),
    )


def get_registration_service(
    session: AsyncSession = Depends(get_session),
) -> RegistrationRepository:
    return RegistrationService(
        RegistrationRepository(session),
        RegistrationQuestionRepository(session),
        HackathonRepository(session),
    )
