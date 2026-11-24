"""Tests for per-client Nautobot token extraction."""

from __future__ import annotations

import pytest

from nautobot_mcp.auth import (
    ClientTokenMiddleware,
    current_client_token,
    http_request_active,
    token_from_headers,
)


def test_token_header_preferred_over_authorization() -> None:
    token = token_from_headers(
        {
            "Authorization": "Token server-looking",
            "X-Nautobot-Token": "person-token",
        }
    )
    assert token == "person-token"


def test_authorization_token_scheme() -> None:
    assert token_from_headers({"Authorization": "Token abc"}) == "abc"
    assert token_from_headers({"authorization": "token abc"}) == "abc"


def test_bearer_authorization_is_not_a_nautobot_token() -> None:
    assert token_from_headers({"Authorization": "Bearer oauth-token"}) is None


def test_missing_headers() -> None:
    assert token_from_headers(None) is None
    assert token_from_headers({}) is None


@pytest.mark.asyncio
async def test_middleware_binds_token_only_for_the_call() -> None:
    class _Ctx:
        class request:
            headers = {"X-Nautobot-Token": "caller"}

    seen: dict[str, object] = {}

    async def call_next(_ctx: object) -> str:
        seen["token"] = current_client_token()
        seen["http"] = http_request_active()
        return "ok"

    result = await ClientTokenMiddleware()(_Ctx(), call_next)

    assert result == "ok"
    assert seen == {"token": "caller", "http": True}
    assert current_client_token() is None
    assert http_request_active() is False


@pytest.mark.asyncio
async def test_middleware_skips_stdio() -> None:
    class _Ctx:
        request = None

    async def call_next(_ctx: object) -> str:
        assert current_client_token() is None
        assert http_request_active() is False
        return "ok"

    assert await ClientTokenMiddleware()(_Ctx(), call_next) == "ok"
