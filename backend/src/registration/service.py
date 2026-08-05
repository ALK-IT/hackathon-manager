import uuid

from sqlalchemy.exc import IntegrityError

from src.auth.models import User, UserRole
from src.hackathons.exceptions import HackathonNotFoundError
from src.hackathons.repository import HackathonRepository
from src.registration.exceptions import (
    InvalidPermission,
    InvalidRegistrationQuestionError,
    MissingRequiredAnswersError,
    QuestionNotFoundError,
    RegistrationAlreadyExistsError,
    RegistrationNotFoundError
)
from src.registration.models import Registration, RegistrationAnswer, RegistrationQuestion
from src.registration.repository import RegistrationQuestionRepository, RegistrationRepository
from src.registration.schema import RegistrationCreate, RegistrationQuestionCreate


class RegistrationQuestionService:
    def __init__(
        self,
        question_repository: RegistrationQuestionRepository,
        hackathon_repository: HackathonRepository,
    ):
        self.question_repository = question_repository
        self.hackathon_repository = hackathon_repository

    async def delete_question(
        self,
        question_public_id: uuid.UUID,
        current_user: User,
    ) -> None:
        question = await self.question_repository.get_by_public_id(question_public_id)

        if question is None:
            raise QuestionNotFoundError()

        if current_user.role != UserRole.ADMIN:
            raise InvalidPermission()

        try:
            await self.question_repository.delete(question)
            await self.question_repository.commit()
        except Exception:
            await self.question_repository.rollback()
            raise

    async def create_question(
        self,
        hackathon_public_id: uuid.UUID,
        data: RegistrationQuestionCreate,
        current_user: User,
    ) -> RegistrationQuestion:
        hackathon = await self.hackathon_repository.get_active_by_public_id(
            hackathon_public_id
        )

        if hackathon is None:
            raise HackathonNotFoundError()

        if current_user.role != UserRole.ADMIN:
            raise InvalidPermission()

        question = RegistrationQuestion(
            content=data.content,
            is_required=data.is_required,
            hackathon=hackathon,
        )

        try:
            question = await self.question_repository.create(question)
            await self.question_repository.commit()
            return question
        except Exception:
            await self.question_repository.rollback()
            raise


class RegistrationService:
    def __init__(
        self,
        registration_repository: RegistrationRepository,
        question_repository: RegistrationQuestionRepository,
        hackathon_repository: HackathonRepository,
    ):
        self.registration_repository = registration_repository
        self.question_repository = question_repository
        self.hackathon_repository = hackathon_repository

    async def create_registration(
        self,
        data: RegistrationCreate,
        hackathon_public_id: uuid.UUID,
        current_user: User,
    ) -> Registration:
        hackathon = await self.hackathon_repository.get_active_by_public_id(
            hackathon_public_id
        )

        if hackathon is None:
            raise HackathonNotFoundError()

        questions = await self.question_repository.get_by_hackathon_public_id(
            hackathon_public_id
        )
        questions_by_public_id = {
            question.public_id: question
            for question in questions
        }
        submitted_question_ids = {
            answer.question_public_id
            for answer in data.answers
        }

        valid_question_ids = set(questions_by_public_id)
        invalid_question_ids = submitted_question_ids - valid_question_ids
        if invalid_question_ids:
            raise InvalidRegistrationQuestionError(
                "Questions do not belong to this hackathon: "
                f"{sorted(map(str, invalid_question_ids))}"
            )

        required_question_ids = {
            question.public_id
            for question in questions
            if question.is_required
        }
        missing_required_ids = required_question_ids - submitted_question_ids
        if missing_required_ids:
            raise MissingRequiredAnswersError(
                "Missing required answers: "
                f"{sorted(map(str, missing_required_ids))}"
            )

        registration = Registration(
            user_id=current_user.id,
            hackathon_id=hackathon.id,
            answers=[
                RegistrationAnswer(
                    question_id=questions_by_public_id[
                        answer.question_public_id
                    ].id,
                    content=answer.content,
                )
                for answer in data.answers
            ],
        )

        try:
            registration = await self.registration_repository.create(registration)
            await self.registration_repository.commit()
            return registration
        except IntegrityError as error:
            await self.registration_repository.rollback()
            raise RegistrationAlreadyExistsError() from error
        except Exception:
            await self.registration_repository.rollback()
            raise

    async def delete_registration(
        self,
        registration_public_id: uuid.UUID,
        current_user: User,
    ) -> None:
        registration = await self.registration_repository.get_by_public_id(
            registration_public_id
        )

        if registration is None:
            raise RegistrationNotFoundError()

        hackathon = registration.hackathon

        is_admin = current_user.role == UserRole.ADMIN
        is_organizer = current_user.id == hackathon.organizer_id
        is_co_organizer = any(
            user.id == current_user.id
            for user in hackathon.co_organizers
        )
        is_owner = current_user.id == registration.user_id

        if not (is_admin or is_organizer or is_co_organizer or is_owner):
            raise InvalidPermission()

        try:
            await self.registration_repository.delete(registration)
            await self.registration_repository.commit()
        except Exception:
            await self.registration_repository.rollback()
            raise