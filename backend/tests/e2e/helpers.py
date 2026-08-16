from dataclasses import dataclass
from datetime import UTC, datetime, timedelta


@dataclass(frozen=True)
class E2EAccount:
    public_id: str
    name: str
    email: str
    password: str
    access_token: str

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.access_token}"}


def hackathon_payload(
    *,
    name: str = "E2E Hackathon",
    registration_is_current: bool = False,
) -> dict[str, object]:
    now = datetime.now(UTC)
    start_date = now + timedelta(days=7)
    registration_deadline = now + timedelta(days=5)
    registration_opens_at = (
        now - timedelta(hours=1) if registration_is_current else now + timedelta(days=1)
    )
    return {
        "name": name,
        "description": "Created by a complete backend E2E flow",
        "start_date": start_date.isoformat(),
        "end_date": (start_date + timedelta(days=2)).isoformat(),
        "registration_opens_at": registration_opens_at.isoformat(),
        "registration_deadline": registration_deadline.isoformat(),
        "capacity": 20,
        "max_team_size": 3,
    }
