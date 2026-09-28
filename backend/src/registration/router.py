import uuid
from collections.abc import AsyncIterator, Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from src.auth.dependencies import get_current_user
from src.auth.models import User
from src.common.csv_export import csv_streaming_response
from src.registration.dependencies import (
    get_registration_question_service,
    get_registration_service,
)
from src.registration.schema import (
    ParticipantAreaResponse,
    ProfileHackathonListResponse,
    ProfileHackathonResponse,
    RegistrationDetailResponse,
    RegistrationQuestionBulkCreate,
    RegistrationQuestionCreate,
    RegistrationQuestionResponse,
    RegistrationResponse,
    RegistrationStatusUpdate,
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
    "/profile/hackathons",
    response_model=ProfileHackathonListResponse,
)
async def list_my_hackathons(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[RegistrationService, Depends(get_registration_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ProfileHackathonListResponse:
    registrations, total = await service.list_my_hackathons(
        current_user,
        limit=limit,
        offset=offset,
    )
    return ProfileHackathonListResponse(
        items=[
            ProfileHackathonResponse(
                registration_public_id=registration.public_id,
                hackathon_public_id=registration.hackathon.public_id,
                name=registration.hackathon.name,
                description=registration.hackathon.description,
                start_date=registration.hackathon.start_date,
                end_date=registration.hackathon.end_date,
                status=registration.status,
                team=registration.team,
                status_changed_at=registration.status_changed_at,
            )
            for registration in registrations
        ],
        total=total,
        limit=limit,
        offset=offset,
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
    response_model=RegistrationQuestionResponse,
)
async def create_question(
    hackathon_public_id: uuid.UUID,
    data: RegistrationQuestionCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[
        RegistrationQuestionService,
        Depends(get_registration_question_service),
    ],
) -> RegistrationQuestionResponse:
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
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[RegistrationDetailResponse]:
    return await service.list_registrations(
        hackathon_public_id=hackathon_public_id,
        current_user=current_user,
        limit=limit,
        offset=offset,
    )


@router.get("/hackathons/{hackathon_public_id}/registrations/export")
async def export_registrations(
    hackathon_public_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[RegistrationService, Depends(get_registration_service)],
    question_service: Annotated[
        RegistrationQuestionService, Depends(get_registration_question_service)
    ],
):
    questions = await question_service.list_questions(hackathon_public_id)
    first_page = await service.list_registrations(
        hackathon_public_id, current_user, limit=100, offset=0
    )

    async def rows() -> AsyncIterator[Sequence[object]]:
        page = first_page
        offset = 0
        while page:
            for registration in page:
                answers = {
                    answer.question.public_id: answer.content for answer in registration.answers
                }
                yield [
                    registration.public_id,
                    registration.user.name,
                    registration.user.email,
                    registration.status.value,
                    registration.team.name if registration.team else "",
                    registration.status_changed_at,
                    registration.status_changed_by.name if registration.status_changed_by else "",
                    *(answers.get(question.public_id, "") for question in questions),
                ]
            offset += len(page)
            if len(page) < 100:
                break
            page = await service.list_registrations(
                hackathon_public_id, current_user, limit=100, offset=offset
            )

    return csv_streaming_response(
        filename=f"hackathon-{hackathon_public_id}-registrations.csv",
        headers=[
            "ID zgłoszenia",
            "Uczestnik",
            "E-mail",
            "Status",
            "Drużyna",
            "Data zmiany statusu",
            "Status zmienił",
            *(question.content for question in questions),
        ],
        rows=rows(),
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
) -> list[RegistrationQuestionResponse]:
    return await service.create_questions(
        hackathon_public_id=hackathon_public_id,
        data=data,
        current_user=current_user,
    )


@router.get(
    "/hackathons/{hackathon_public_id}/participant-area",
    response_model=ParticipantAreaResponse,
    status_code=status.HTTP_200_OK,
)
async def get_participant_area(
    hackathon_public_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[RegistrationService, Depends(get_registration_service)],
) -> ParticipantAreaResponse:
    return await service.get_participant_area(hackathon_public_id, current_user)
