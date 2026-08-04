from src.registration.repository import RegistrationQuestionRepository
from src.auth.models import User
# from sqlalchemy.dialects.postgresql import UUID
import uuid
from src.registration.exceptions import QuestionNotFoundError, InvalidPermission
from src.auth.models import UserRole
from src.registration.schema import RegistrationQuestionCreate
from src.hackathons.repository import HackathonRepository

class RegistrationQuestionService:
    def __init__(
            self,
            question_repository: RegistrationQuestionRepository,
            hackathon_repository: HackathonRepository
    ):
        self.question_repository = question_repository
        self.hackathon_repository = hackathon_repository

    async def delete_question(
            self,
            question_public_id: uuid.UUID,
            current_user: User,
    ):
        question = await self.question_repository.get_by_public_id(
            question_public_id
        )

        if question is None:
            raise QuestionNotFoundError()

        if current_user.role == UserRole.ADMIN:
            raise InvalidPermission
        
        try:
            await self.question_repository.delete(question)
            await self.question_repository.commit()
        except Exception:
            await self.question_repository.rollback()
            raise           
            

    # async def create_question(
    #         self,
    #         hackathon_public_id: uuid.UUID,
    #         data: RegistrationQuestionCreate,
    #         current_user: User
    # ):

    #     if current_user.role == UserRole.ADMIN:
    #         raise InvalidPermission

    #     try:
    #         await self.repository



        

        