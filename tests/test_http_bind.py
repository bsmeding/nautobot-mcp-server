"""Tests for the HTTP/SSE listen address."""

from __future__ import annotations

import pytest

from nautobot_mcp.server import resolve_http_bind


def test_default_bind_is_loopback() -> None:
    assert resolve_http_bind(None, None) == ("127.0.0.1", 8000)


def test_cli_values_win() -> None:
    assert resolve_http_bind("0.0.0.0", 9000) == ("0.0.0.0", 9000)


def test_env_used_when_cli_omitted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NAUTOBOT_MCP_HOST", "10.1.2.3")
    monkeypatch.setenv("NAUTOBOT_MCP_PORT", "8088")
    assert resolve_http_bind(None, None) == ("10.1.2.3", 8088)


def test_cli_host_beats_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NAUTOBOT_MCP_HOST", "10.1.2.3")
    assert resolve_http_bind("192.168.1.5", None) == ("192.168.1.5", 8000)


def test_port_zero_is_allowed() -> None:
    assert resolve_http_bind("127.0.0.1", 0) == ("127.0.0.1", 0)


def test_invalid_env_port(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NAUTOBOT_MCP_PORT", "nope")
    with pytest.raises(ValueError, match="NAUTOBOT_MCP_PORT"):
        resolve_http_bind(None, None)


def test_port_out_of_range() -> None:
    with pytest.raises(ValueError, match="between 0 and 65535"):
        resolve_http_bind(None, 70000)
