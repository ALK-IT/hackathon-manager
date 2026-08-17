import uuid

from sqlalchemy.exc import IntegrityError

from src.auth.models import User, UserRole
from src.database import get_integrity_error_constraint
from src.hackathons.exceptions import HackathonNotFoundError
from src.hackathons.models import Hackathon
from src.hackathons.repository import HackathonRepository
from src.registration.exceptions import (
    InvalidPermission,
    InvalidRegistrationQuestionError,
    MissingRequiredAnswersError,
    QuestionNotFoundError,
    RegistrationAlreadyExistsError,
    RegistrationClosedError,
    RegistrationNotFoundError,
)
from src.registration.models import (
    Registration,
    RegistrationAnswer,
    RegistrationQuestion,
    RegistrationStatus,
)
from src.registration.repository import RegistrationQuestionRepository, RegistrationRepository
from src.registration.schema import (
    RegistrationCreate,
    RegistrationQuestionBulkCreate,
    RegistrationQuestionCreate,
)
from src.teams.service import TeamService


def _can_manage_hackathon(hackathon: Hackathon, current_user: User) -> bool:
    return (
        current_user.role == UserRole.ADMIN
        or current_user.id == hackathon.organizer_id
        or any(user.id == current_user.id for user in hackathon.co_organizers)
    )


class RegistrationQuestionService:
    def __init__(
        self,
        question_repository: RegistrationQuestionRepository,
        hackathon_repository: HackathonRepository,
    ):
        self.question_repository = question_repository
        self.hackathon_repository = hackathon_repository

    async def list_questions(
        self,
        hackathon_public_id: uuid.UUID,
    ) -> list[RegistrationQuestion]:
        hackathon = await self.hackathon_repository.get_active_by_public_id(hackathon_public_id)

        if hackathon is None:
            raise HackathonNotFoundError()

        return await self.question_repository.get_by_hackathon_public_id(hackathon_public_id)

    async def delete_question(
        self,
        question_public_id: uuid.UUID,
        current_user: User,
    ) -> None:
        question = await self.question_repository.get_by_public_id(question_public_id)

        if question is None:
            raise QuestionNotFoundError()

        if not _can_manage_hackathon(question.hackathon, current_user):
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
        hackathon = await self.hackathon_repository.get_active_by_public_id(hackathon_public_id)

        if hackathon is None:
            raise HackathonNotFoundError()

        if not _can_manage_hackathon(hackathon, current_user):
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

    async def create_questions(
        self,
        hackathon_public_id: uuid.UUID,
        data: RegistrationQuestionBulkCreate,
        current_user: User,
    ) -> list[RegistrationQuestion]:
        hackathon = await self.hackathon_repository.get_active_by_public_id(hackathon_public_id)

        if hackathon is None:
            raise HackathonNotFoundError()

        if not _can_manage_hackathon(hackathon, current_user):
            raise InvalidPermission()

        questions = [
            RegistrationQuestion(
                content=question.content,
                is_required=question.is_required,
                hackathon=hackathon,
            )
            for question in data.questions
        ]

        try:
            questions = await self.question_repository.create_many(questions)
            await self.question_repository.commit()
            return questions
        except Exception:
            await self.question_repository.rollback()
            raise


class RegistrationService:
    def __init__(
        self,
        registration_repository: RegistrationRepository,
        question_repository: RegistrationQuestionRepository,
        hackathon_repository: HackathonRepository,
        team_service: TeamService,
    ):
        self.registration_repository = registration_repository
        self.question_repository = question_repository
        self.hackathon_repository = hackathon_repository
        self.team_service = team_service

    async def list_registrations(
        self,
        hackathon_public_id: uuid.UUID,
        current_user: User,
    ) -> list[Registration]:
        hackathon = await self.hackathon_repository.get_active_by_public_id(hackathon_public_id)

        if hackathon is None:
            raise HackathonNotFoundError()

        if not _can_manage_hackathon(hackathon, current_user):
            raise InvalidPermission()

        return await self.registration_repository.get_by_hackathon(hackathon_public_id)

    async def get_my_registration(
        self,
        hackathon_public_id: uuid.UUID,
        current_user: User,
    ) -> Registration:
        registration = await self.registration_repository.get_by_hackathon_and_user(
            hackathon_public_id,
            current_user.public_id,
        )

        if registration is None:
            raise RegistrationNotFoundError()

        return registration

    async def create_registration(
        self,
        data: RegistrationCreate,
        hackathon_public_id: uuid.UUID,
        current_user: User,
    ) -> Registration:
        hackathon = await self.hackathon_repository.get_active_by_public_id(hackathon_public_id)

        if hackathon is None:
            raise HackathonNotFoundError()

        if not hackathon.is_registration_open_at():
            raise RegistrationClosedError()

        questions = await self.question_repository.get_by_hackathon_public_id(hackathon_public_id)
        questions_by_public_id = {question.public_id: question for question in questions}
        submitted_question_ids = {answer.question_public_id for answer in data.answers}

        valid_question_ids = set(questions_by_public_id)
        invalid_question_ids = submitted_question_ids - valid_question_ids
        if invalid_question_ids:
            raise InvalidRegistrationQuestionError(
                "Questions do not belong to this hackathon: "
                f"{sorted(map(str, invalid_question_ids))}"
            )

        required_question_ids = {
            question.public_id for question in questions if question.is_required
        }
        missing_required_ids = required_question_ids - submitted_question_ids
        if missing_required_ids:
            raise MissingRequiredAnswersError(
                f"Missing required answers: {sorted(map(str, missing_required_ids))}"
            )

        try:
            team = await self.team_service.resolve_team(
                selection=data.team,
                hackathon=hackathon,
            )

            registration = Registration(
                user_id=current_user.id,
                hackathon_id=hackathon.id,
                team=team,
                answers=[
                    RegistrationAnswer(
                        question_id=questions_by_public_id[answer.question_public_id].id,
                        content=answer.content,
                    )
                    for answer in data.answers
                ],
            )

            registration = await self.registration_repository.create(registration)
            await self.registration_repository.commit()
            return registration
        except IntegrityError as error:
            await self.registration_repository.rollback()
            if get_integrity_error_constraint(error) == "uq_application_user_hackathon":
                raise RegistrationAlreadyExistsError() from error
            raise
        except Exception:
            await self.registration_repository.rollback()
            raise

    async def delete_registration(
        self,
        registration_public_id: uuid.UUID,
        current_user: User,
    ) -> None:
        registration = await self.registration_repository.get_by_public_id(registration_public_id)

        if registration is None:
            raise RegistrationNotFoundError()

        hackathon = registration.hackathon

        is_owner = current_user.id == registration.user_id

        if not (_can_manage_hackathon(hackathon, current_user) or is_owner):
            raise InvalidPermission()

        team_id = registration.team_id
        try:
            await self.registration_repository.delete(registration)
            if team_id is not None:
                await self.team_service.delete_if_empty(team_id)
            await self.registration_repository.commit()
        except Exception:
            await self.registration_repository.rollback()
            raise

    async def update_status(
        self,
        registration_public_id: uuid.UUID,
        new_status: RegistrationStatus,
        current_user: User,
    ) -> Registration:
        registration = await self.registration_repository.get_by_public_id(registration_public_id)

        if registration is None:
            raise RegistrationNotFoundError()

        hackathon = registration.hackathon

        if not _can_manage_hackathon(hackathon, current_user):
            raise InvalidPermission()

        try:
            if (
                registration.team_id is not None
                and registration.status is RegistrationStatus.REJECTED
                and new_status is RegistrationStatus.ACCEPTED
            ):
                await self.team_service.ensure_member_can_be_activated(
                    registration.team_id,
                    hackathon.max_team_size,
                )
            registration = await self.registration_repository.update_status(
                registration,
                new_status,
            )
            await self.registration_repository.commit()
            return registration
        except Exception:
            await self.registration_repository.rollback()
            raise
