"""Tests for the NautobotClient."""

from __future__ import annotations

import httpx
import pytest
import respx

from nautobot_mcp_server.client import NautobotClient
from nautobot_mcp_server.config import NautobotMcpSettings

pytestmark = pytest.mark.asyncio


def _settings(**overrides) -> NautobotMcpSettings:
    base = dict(
        url="https://nautobot.example.com",
        token="t" * 40,
        verify_ssl=True,
        request_timeout=5.0,
        max_pagination_records=100,
        allow_writes=False,
        log_level="DEBUG",
    )
    base.update(overrides)
    return NautobotMcpSettings(**base)


def test_endpoint_validation() -> None:
    cli = NautobotClient(_settings())
    with pytest.raises(ValueError, match="must start with '/api/'"):
        cli._normalize_endpoint("/dcim/devices/")
    assert cli._normalize_endpoint("/api/dcim/devices") == "/api/dcim/devices/"


@respx.mock
async def test_rest_get_sets_auth_header() -> None:
    cli = NautobotClient(_settings())
    route = respx.get("https://nautobot.example.com/api/dcim/devices/").mock(
        return_value=httpx.Response(200, json={"results": []})
    )

    await cli.rest_get("/api/dcim/devices/")
    await cli.aclose()

    assert route.called
    sent = route.calls.last.request
    assert sent.headers["Authorization"].startswith("Token ")


@respx.mock
async def test_write_gate_blocks_post_when_writes_disabled() -> None:
    cli = NautobotClient(_settings(allow_writes=False))
    with pytest.raises(PermissionError, match="writes are disabled"):
        await cli.rest_create("/api/ipam/prefixes/", {"prefix": "10.0.0.0/24"})
    await cli.aclose()


@respx.mock
async def test_write_gate_permits_post_when_writes_enabled() -> None:
    cli = NautobotClient(_settings(allow_writes=True))
    respx.post("https://nautobot.example.com/api/ipam/prefixes/").mock(
        return_value=httpx.Response(201, json={"id": "abc"})
    )
    result = await cli.rest_create("/api/ipam/prefixes/", {"prefix": "10.0.0.0/24"})
    assert result == {"id": "abc"}
    await cli.aclose()


@respx.mock
async def test_graphql_post_is_allowed_even_with_writes_disabled() -> None:
    cli = NautobotClient(_settings(allow_writes=False))
    respx.post("https://nautobot.example.com/api/graphql/").mock(
        return_value=httpx.Response(200, json={"data": {"sites": []}})
    )
    out = await cli.graphql_query("{ sites { id } }")
    assert out == {"data": {"sites": []}}
    await cli.aclose()


@respx.mock
async def test_retries_on_503_then_succeeds() -> None:
    cli = NautobotClient(_settings())
    route = respx.get("https://nautobot.example.com/api/").mock(
        side_effect=[
            httpx.Response(503, text="busy"),
            httpx.Response(200, json={"dcim": "..."}),
        ]
    )
    result = await cli.list_api_roots()
    assert result == {"dcim": "..."}
    assert route.call_count == 2
    await cli.aclose()


@respx.mock
async def test_pagination_walks_next_links() -> None:
    cli = NautobotClient(_settings(max_pagination_records=10))

    def _responder(request: httpx.Request) -> httpx.Response:
        # Return the second page only when following the ``next`` link
        # (``offset=2``); otherwise serve the first page. A single route
        # avoids respx route-shadowing between the base and ``?offset=2`` URLs.
        if request.url.params.get("offset") == "2":
            return httpx.Response(
                200,
                json={
                    "count": 4,
                    "next": None,
                    "previous": None,
                    "results": [{"id": 3}, {"id": 4}],
                },
            )
        return httpx.Response(
            200,
            json={
                "count": 4,
                "next": "https://nautobot.example.com/api/dcim/devices/?offset=2",
                "previous": None,
                "results": [{"id": 1}, {"id": 2}],
            },
        )

    respx.get("https://nautobot.example.com/api/dcim/devices/").mock(
        side_effect=_responder
    )
    results = await cli.rest_list("/api/dcim/devices/", paginate=True)
    assert isinstance(results, list)
    assert [r["id"] for r in results] == [1, 2, 3, 4]
    await cli.aclose()


@respx.mock
async def test_pagination_respects_max_records() -> None:
    cli = NautobotClient(_settings(max_pagination_records=2))
    respx.get("https://nautobot.example.com/api/dcim/devices/").mock(
        return_value=httpx.Response(
            200,
            json={
                "count": 100,
                "next": "https://nautobot.example.com/api/dcim/devices/?offset=2",
                "results": [{"id": 1}, {"id": 2}, {"id": 3}],
            },
        )
    )
    results = await cli.rest_list("/api/dcim/devices/", paginate=True)
    assert isinstance(results, list)
    assert len(results) == 2
    await cli.aclose()
