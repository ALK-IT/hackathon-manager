import pytest

from src.auth.config import (
    get_login_rate_limit_settings,
    get_refresh_rate_limit_settings,
    get_register_rate_limit_settings,
    get_verify_email_rate_limit_settings,
)


@pytest.mark.parametrize(
    ("settings_provider", "prefix", "default_requests", "default_window"),
    [
        (get_login_rate_limit_settings, "LOGIN", 10, 60),
        (get_register_rate_limit_settings, "REGISTER", 5, 3600),
        (get_refresh_rate_limit_settings, "REFRESH", 30, 60),
        (get_verify_email_rate_limit_settings, "VERIFY_EMAIL", 20, 300),
    ],
)
def test_rate_limit_settings_use_defaults(
    monkeypatch,
    settings_provider,
    prefix,
    default_requests,
    default_window,
):
    monkeypatch.delenv(f"RATE_LIMIT_{prefix}_REQUESTS", raising=False)
    monkeypatch.delenv(f"RATE_LIMIT_{prefix}_WINDOW_SECONDS", raising=False)

    settings = settings_provider()

    assert settings.requests == default_requests
    assert settings.window_seconds == default_window


def test_rate_limit_settings_can_be_configured(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_LOGIN_REQUESTS", "7")
    monkeypatch.setenv("RATE_LIMIT_LOGIN_WINDOW_SECONDS", "120")

    settings = get_login_rate_limit_settings()

    assert settings.requests == 7
    assert settings.window_seconds == 120


@pytest.mark.parametrize("value", ["0", "-1", "invalid"])
def test_rate_limit_settings_reject_invalid_values(monkeypatch, value):
    monkeypatch.setenv("RATE_LIMIT_LOGIN_REQUESTS", value)

    with pytest.raises(RuntimeError, match="RATE_LIMIT_LOGIN_REQUESTS"):
        get_login_rate_limit_settings()
