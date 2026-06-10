"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from nautobot_mcp_server.client import NautobotClient
from nautobot_mcp_server.config import NautobotMcpSettings


@pytest.fixture
def settings() -> NautobotMcpSettings:
    return NautobotMcpSettings(
        url="https://nautobot.example.com",
        token="0123456789abcdef0123456789abcdef01234567",
        verify_ssl=True,
        request_timeout=5.0,
        max_pagination_records=100,
        allow_writes=False,
        log_level="DEBUG",
    )


@pytest.fixture
async def client(settings: NautobotMcpSettings):
    cli = NautobotClient(settings)
    try:
        yield cli
    finally:
        await cli.aclose()
