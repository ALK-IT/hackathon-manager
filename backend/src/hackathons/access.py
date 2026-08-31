from enum import Enum

from src.auth.models import User, UserRole
from src.hackathons.models import Hackathon


class HackathonAccessLevel(str, Enum):
    OWNER = "owner"
    CO_ORGANIZER = "co_organizer"
    VIEWER = "viewer"


def get_hackathon_access_level(
    hackathon: Hackathon,
    user_id: int | None,
) -> HackathonAccessLevel:
    if hackathon.organizer_id == user_id:
        return HackathonAccessLevel.OWNER
    if any(co_organizer.id == user_id for co_organizer in hackathon.co_organizers):
        return HackathonAccessLevel.CO_ORGANIZER
    return HackathonAccessLevel.VIEWER


def can_manage_hackathon(hackathon: Hackathon, user: User) -> bool:
    return (
        user.role == UserRole.ADMIN
        or get_hackathon_access_level(hackathon, user.id) != HackathonAccessLevel.VIEWER
    )
