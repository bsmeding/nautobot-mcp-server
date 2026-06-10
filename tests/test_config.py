"""Tests for the settings resolver."""

from __future__ import annotations

import pytest

from nautobot_mcp_server.config import NautobotMcpSettings, load_settings


def test_load_settings_from_kwargs() -> None:
    s = load_settings(
        url="https://nautobot.example.com/",
        token="abc",
        verify_ssl=False,
        request_timeout=10,
        allow_writes=True,
    )
    assert s.url == "https://nautobot.example.com"
    assert s.token == "abc"
    assert s.verify_ssl is False
    assert s.request_timeout == 10.0
    assert s.allow_writes is True


def test_load_settings_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NAUTOBOT_URL", "https://env.example.com")
    monkeypatch.setenv("NAUTOBOT_TOKEN", "envtoken")
    monkeypatch.setenv("NAUTOBOT_VERIFY_SSL", "false")
    monkeypatch.setenv("NAUTOBOT_TIMEOUT", "12.5")
    monkeypatch.setenv("NAUTOBOT_ALLOW_WRITES", "yes")

    s = load_settings()

    assert s.url == "https://env.example.com"
    assert s.token == "envtoken"
    assert s.verify_ssl is False
    assert s.request_timeout == 12.5
    assert s.allow_writes is True


def test_kwargs_beat_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NAUTOBOT_URL", "https://env.example.com")
    monkeypatch.setenv("NAUTOBOT_TOKEN", "envtoken")
    s = load_settings(url="https://override.example.com", token="overridetoken")
    assert s.url == "https://override.example.com"
    assert s.token == "overridetoken"


def test_ca_bundle_path_used_for_verify(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NAUTOBOT_URL", "https://x.example.com")
    monkeypatch.setenv("NAUTOBOT_TOKEN", "t")
    monkeypatch.setenv("NAUTOBOT_CA_BUNDLE", "/etc/ssl/corp-ca.pem")
    s = load_settings()
    assert s.verify_ssl == "/etc/ssl/corp-ca.pem"


def test_missing_url_raises() -> None:
    with pytest.raises(ValueError, match="URL is not configured"):
        load_settings(token="t")


def test_missing_token_raises() -> None:
    with pytest.raises(ValueError, match="API token is not configured"):
        load_settings(url="https://x.example.com")


def test_redacted_masks_token() -> None:
    s = NautobotMcpSettings(
        url="https://x", token="0123456789abcdef0123456789abcdef"
    )
    redacted = s.redacted()
    assert "0123" in redacted["token"]
    assert "cdef" in redacted["token"]
    assert "456789ab" not in redacted["token"]
