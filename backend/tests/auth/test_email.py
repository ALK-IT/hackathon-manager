import pytest

from src.auth.email import EmailDeliveryError, EmailService


async def test_registration_status_email_has_safe_subject_and_event_link(monkeypatch):
    sent_messages = []
    monkeypatch.setenv("FRONTEND_URL", "https://example.test/")
    monkeypatch.setattr(
        EmailService,
        "_send_sync",
        staticmethod(sent_messages.append),
    )

    await EmailService().send_registration_status_changed(
        "participant@example.com",
        "AI\r\nHackathon",
        "hackathon-id",
        "accepted",
    )

    assert len(sent_messages) == 1
    message = sent_messages[0]
    assert message["To"] == "participant@example.com"
    assert message["Subject"] == "Zmiana statusu zgłoszenia: AI Hackathon"
    assert "zaakceptowane" in message.get_content()
    assert "https://example.test/hackathons/hackathon-id" in message.get_content()


async def test_email_service_wraps_invalid_headers():
    with pytest.raises(EmailDeliveryError):
        await EmailService()._send(
            "participant@example.com",
            "Invalid\nsubject",
            "Content",
        )
