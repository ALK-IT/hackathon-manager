import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from src.auth.dependencies import get_current_user
from src.auth.models import User
from src.registration.dependencies import (
    get_registration_question_service,
    get_registration_service,
)
from src.registration.schema import (
    RegistrationCreate,
    RegistrationDetailResponse,
    RegistrationQuestionCreate,
    RegistrationQuestionResponse,
    RegistrationResponse,
    RegistrationStatusUpdate,
    RegistrationQuestionBulkCreate
)
from src.registration.service import (
    RegistrationQuestionService,
    RegistrationService,
)

router = APIRouter(
    prefix="/api",
    tags=["registrations"],
)


@router.get(
    "/hackathons/{hackathon_public_id}/questions",
    response_model=list[RegistrationQuestionResponse],
)
async def list_questions(
    hackathon_public_id: uuid.UUID,
    _current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[
        RegistrationQuestionService,
        Depends(get_registration_question_service),
    ],
) -> list[RegistrationQuestionResponse]:
    return await service.list_questions(hackathon_public_id=hackathon_public_id)


@router.post(
    "/hackathons/{hackathon_public_id}/questions",
    status_code=status.HTTP_201_CREATED,
)
async def create_question(
    hackathon_public_id: uuid.UUID,
    data: RegistrationQuestionCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[
        RegistrationQuestionService,
        Depends(get_registration_question_service),
    ],
):
    return await service.create_question(
        hackathon_public_id=hackathon_public_id,
        data=data,
        current_user=current_user,
    )


@router.delete(
    "/hackathons/{hackathon_public_id}/questions/{question_public_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_question(
    hackathon_public_id: uuid.UUID,
    question_public_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[
        RegistrationQuestionService,
        Depends(get_registration_question_service),
    ],
) -> Response:
    await service.delete_question(
        question_public_id=question_public_id,
        current_user=current_user,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/hackathons/{hackathon_public_id}/registrations",
    status_code=status.HTTP_201_CREATED,
    response_model=RegistrationResponse,
)
async def create_registration(
    hackathon_public_id: uuid.UUID,
    data: RegistrationCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[
        RegistrationService,
        Depends(get_registration_service),
    ],
):
    return await service.create_registration(
        data=data,
        hackathon_public_id=hackathon_public_id,
        current_user=current_user,
    )


@router.get(
    "/hackathons/{hackathon_public_id}/registrations",
    response_model=list[RegistrationDetailResponse],
)
async def list_registrations(
    hackathon_public_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[
        RegistrationService,
        Depends(get_registration_service),
    ],
) -> list[RegistrationDetailResponse]:
    return await service.list_registrations(
        hackathon_public_id=hackathon_public_id,
        current_user=current_user,
    )


@router.get(
    "/hackathons/{hackathon_public_id}/registrations/me",
    response_model=RegistrationDetailResponse,
)
async def get_my_registration(
    hackathon_public_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[
        RegistrationService,
        Depends(get_registration_service),
    ],
) -> RegistrationDetailResponse:
    return await service.get_my_registration(
        hackathon_public_id=hackathon_public_id,
        current_user=current_user,
    )


@router.delete(
    "/registrations/{registration_public_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_registration(
    registration_public_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[
        RegistrationService,
        Depends(get_registration_service),
    ],
) -> Response:
    await service.delete_registration(
        registration_public_id=registration_public_id,
        current_user=current_user,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/registrations/{registration_public_id}/status",
    response_model=RegistrationResponse,
)
async def update_registration_status(
    registration_public_id: uuid.UUID,
    data: RegistrationStatusUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[
        RegistrationService,
        Depends(get_registration_service),
    ],
) -> RegistrationResponse:
    return await service.update_status(
        registration_public_id=registration_public_id,
        new_status=data.status,
        current_user=current_user,
    )

@router.post(
    "/hackathons/{hackathon_public_id}/questions/bulk",
    status_code=status.HTTP_201_CREATED,
    response_model=list[RegistrationQuestionResponse],
)
async def create_questions(
    hackathon_public_id: uuid.UUID,
    data: RegistrationQuestionBulkCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[
        RegistrationQuestionService,
        Depends(get_registration_question_service),
    ],
):
    return await service.create_questions(
        hackathon_public_id=hackathon_public_id,
        data=data,
        current_user=current_user,
    )