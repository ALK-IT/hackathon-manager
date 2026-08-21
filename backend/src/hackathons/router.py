import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from src.auth.dependencies import get_current_user, get_optional_current_user
from src.auth.models import User
from src.hackathons.dependencies import get_current_admin, get_hackathon_service
from src.hackathons.schemas import (
    CoOrganizerAddRequest,
    HackathonCreate,
    HackathonDeleteRequest,
    HackathonListItem,
    HackathonRead,
    HackathonRegistrationStateRead,
    HackathonUpdate,
)
from src.hackathons.service import HackathonService

router = APIRouter(prefix="/api/hackathons", tags=["hackathons"])


@router.get("", response_model=list[HackathonListItem])
async def list_hackathons(
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    service: Annotated[HackathonService, Depends(get_hackathon_service)],
    upcoming: Annotated[bool | None, Query()] = None,
    registration_open: Annotated[bool | None, Query(alias="open")] = True,
) -> list[HackathonListItem]:
    hackathons = await service.list_hackathons(
        upcoming=upcoming,
        registration_open=registration_open,
    )
    return [
        HackathonListItem.from_hackathon(
            hackathon,
            current_user.id if current_user is not None else None,
        )
        for hackathon in hackathons
    ]


@router.post("", response_model=HackathonRead, status_code=status.HTTP_201_CREATED)
async def create_hackathon(
    data: HackathonCreate,
    current_admin: Annotated[User, Depends(get_current_admin)],
    service: Annotated[HackathonService, Depends(get_hackathon_service)],
) -> HackathonRead:
    hackathon = await service.create_hackathon(data, current_admin)
    return HackathonRead.from_hackathon(hackathon, current_admin.id)


@router.get("/managed", response_model=list[HackathonListItem])
async def list_managed_hackathons(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[HackathonService, Depends(get_hackathon_service)],
) -> list[HackathonListItem]:
    hackathons = await service.list_managed_hackathons(current_user)
    return [
        HackathonListItem.from_hackathon(hackathon, current_user.id) for hackathon in hackathons
    ]


@router.get("/{public_id}", response_model=HackathonRead)
async def get_hackathon(
    public_id: uuid.UUID,
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    service: Annotated[HackathonService, Depends(get_hackathon_service)],
) -> HackathonRead:
    hackathon = await service.get_hackathon(public_id)
    return HackathonRead.from_hackathon(
        hackathon,
        current_user.id if current_user is not None else None,
    )


@router.patch("/{public_id}", response_model=HackathonRead)
async def update_hackathon(
    public_id: uuid.UUID,
    data: HackathonUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[HackathonService, Depends(get_hackathon_service)],
) -> HackathonRead:
    hackathon = await service.update_hackathon(public_id, data, current_user)
    return HackathonRead.from_hackathon(hackathon, current_user.id)


@router.delete("/{public_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hackathon(
    public_id: uuid.UUID,
    data: HackathonDeleteRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[HackathonService, Depends(get_hackathon_service)],
) -> Response:
    await service.delete_hackathon(public_id, data.confirm_name, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{public_id}/co-organizers", response_model=HackathonRead, status_code=status.HTTP_201_CREATED
)
async def add_co_organizer(
    public_id: uuid.UUID,
    data: CoOrganizerAddRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[HackathonService, Depends(get_hackathon_service)],
) -> HackathonRead:
    hackathon = await service.add_co_organizer(public_id, data, current_user)
    return HackathonRead.from_hackathon(hackathon, current_user.id)


@router.post(
    "/{public_id}/open-registration",
    response_model=HackathonRegistrationStateRead,
)
async def open_registration(
    public_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[HackathonService, Depends(get_hackathon_service)],
) -> HackathonRegistrationStateRead:
    hackathon = await service.open_registration(public_id, current_user)
    return HackathonRegistrationStateRead.from_hackathon(hackathon)


@router.post(
    "/{public_id}/close-registration",
    response_model=HackathonRegistrationStateRead,
)
async def close_registration(
    public_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[HackathonService, Depends(get_hackathon_service)],
) -> HackathonRegistrationStateRead:
    hackathon = await service.close_registration(public_id, current_user)
    return HackathonRegistrationStateRead.from_hackathon(hackathon)
