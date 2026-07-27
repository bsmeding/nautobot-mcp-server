"""Tests for tenant scoping enforcement in the NautobotClient."""

from __future__ import annotations

import httpx
import pytest
import respx

from nautobot_mcp_server.client import NautobotClient
from nautobot_mcp_server.config import NautobotMcpSettings, load_settings

pytestmark = pytest.mark.asyncio

BASE = "https://nautobot.example.com"
ACME_ID = "11111111-1111-1111-1111-111111111111"
GLOBEX_ID = "22222222-2222-2222-2222-222222222222"


def _settings(**overrides) -> NautobotMcpSettings:
    base = dict(
        url=BASE,
        token="t" * 40,
        verify_ssl=True,
        request_timeout=5.0,
        max_pagination_records=100,
        allow_writes=False,
        log_level="DEBUG",
    )
    base.update(overrides)
    return NautobotMcpSettings(**base)


def _mock_tenant_resolution(name: str = "acme", tenant_id: str = ACME_ID) -> None:
    respx.get(f"{BASE}/api/tenancy/tenants/", params={"name": name}).mock(
        return_value=httpx.Response(
            200, json={"results": [{"id": tenant_id, "name": name}]}
        )
    )


# ---- config -----------------------------------------------------------


def test_tenant_scope_parses_csv_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NAUTOBOT_URL", BASE)
    monkeypatch.setenv("NAUTOBOT_TOKEN", "tok")
    monkeypatch.setenv("NAUTOBOT_MCP_TENANT_SCOPE", "acme, globex ,")
    s = load_settings()
    assert s.tenant_scope == ("acme", "globex")
    assert s.tenant_scoped is True


def test_no_scope_is_inactive() -> None:
    assert _settings().tenant_scoped is False


# ---- list enforcement -------------------------------------------------


@respx.mock
async def test_list_injects_tenant_id_filter() -> None:
    cli = NautobotClient(_settings(tenant_scope=("acme",)))
    _mock_tenant_resolution()
    route = respx.get(f"{BASE}/api/dcim/devices/").mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    await cli.rest_list("/api/dcim/devices/")
    await cli.aclose()

    sent = route.calls.last.request
    assert sent.url.params.get("tenant_id") == ACME_ID


@respx.mock
async def test_list_overrides_caller_tenant_filter() -> None:
    cli = NautobotClient(_settings(tenant_scope=("acme",)))
    _mock_tenant_resolution()
    route = respx.get(f"{BASE}/api/dcim/devices/").mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    # Caller tries to escape the scope by passing a different tenant.
    await cli.rest_list("/api/dcim/devices/", filters={"tenant": "globex"})
    await cli.aclose()

    params = route.calls.last.request.url.params
    assert "globex" not in str(params)
    assert params.get("tenant_id") == ACME_ID


@respx.mock
async def test_non_tenant_aware_endpoint_untouched() -> None:
    cli = NautobotClient(_settings(tenant_scope=("acme",)))
    _mock_tenant_resolution()
    route = respx.get(f"{BASE}/api/dcim/manufacturers/").mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    await cli.rest_list("/api/dcim/manufacturers/")
    await cli.aclose()

    assert "tenant_id" not in str(route.calls.last.request.url.params)


# ---- object enforcement -----------------------------------------------


@respx.mock
async def test_get_object_in_scope_ok() -> None:
    cli = NautobotClient(_settings(tenant_scope=("acme",)))
    _mock_tenant_resolution()
    respx.get(f"{BASE}/api/dcim/devices/dev1/").mock(
        return_value=httpx.Response(
            200, json={"id": "dev1", "tenant": {"id": ACME_ID}}
        )
    )
    obj = await cli.rest_get_object("/api/dcim/devices/", "dev1")
    assert obj["id"] == "dev1"
    await cli.aclose()


@respx.mock
async def test_get_object_out_of_scope_raises() -> None:
    cli = NautobotClient(_settings(tenant_scope=("acme",)))
    _mock_tenant_resolution()
    respx.get(f"{BASE}/api/dcim/devices/dev2/").mock(
        return_value=httpx.Response(
            200, json={"id": "dev2", "tenant": {"id": GLOBEX_ID}}
        )
    )
    with pytest.raises(PermissionError, match="outside the configured tenant scope"):
        await cli.rest_get_object("/api/dcim/devices/", "dev2")
    await cli.aclose()


@respx.mock
async def test_get_object_with_no_tenant_is_out_of_scope() -> None:
    cli = NautobotClient(_settings(tenant_scope=("acme",)))
    _mock_tenant_resolution()
    respx.get(f"{BASE}/api/dcim/devices/dev3/").mock(
        return_value=httpx.Response(200, json={"id": "dev3", "tenant": None})
    )
    with pytest.raises(PermissionError):
        await cli.rest_get_object("/api/dcim/devices/", "dev3")
    await cli.aclose()


# ---- create enforcement -----------------------------------------------


@respx.mock
async def test_create_injects_single_scoped_tenant() -> None:
    cli = NautobotClient(_settings(tenant_scope=("acme",), allow_writes=True))
    _mock_tenant_resolution()
    route = respx.post(f"{BASE}/api/ipam/prefixes/").mock(
        return_value=httpx.Response(201, json={"id": "p1"})
    )
    await cli.rest_create("/api/ipam/prefixes/", {"prefix": "10.0.0.0/24"})
    await cli.aclose()

    import json as _json

    body = _json.loads(route.calls.last.request.content)
    assert body["tenant"] == ACME_ID


@respx.mock
async def test_create_rejects_out_of_scope_tenant() -> None:
    cli = NautobotClient(_settings(tenant_scope=("acme",), allow_writes=True))
    _mock_tenant_resolution()
    # The supplied tenant name resolves to a different (out-of-scope) id.
    respx.get(f"{BASE}/api/tenancy/tenants/", params={"name": "globex"}).mock(
        return_value=httpx.Response(
            200, json={"results": [{"id": GLOBEX_ID, "name": "globex"}]}
        )
    )
    with pytest.raises(PermissionError, match="outside the configured tenant scope"):
        await cli.rest_create(
            "/api/ipam/prefixes/", {"prefix": "10.0.0.0/24", "tenant": "globex"}
        )
    await cli.aclose()


@respx.mock
async def test_create_multi_tenant_scope_requires_explicit_tenant() -> None:
    cli = NautobotClient(
        _settings(tenant_scope=("acme", "globex"), allow_writes=True)
    )
    respx.get(f"{BASE}/api/tenancy/tenants/", params={"name": "acme"}).mock(
        return_value=httpx.Response(200, json={"results": [{"id": ACME_ID}]})
    )
    respx.get(f"{BASE}/api/tenancy/tenants/", params={"name": "globex"}).mock(
        return_value=httpx.Response(200, json={"results": [{"id": GLOBEX_ID}]})
    )
    with pytest.raises(PermissionError, match="cannot be inferred"):
        await cli.rest_create("/api/ipam/prefixes/", {"prefix": "10.0.0.0/24"})
    await cli.aclose()


# ---- misconfiguration -------------------------------------------------


@respx.mock
async def test_empty_scope_resolution_raises() -> None:
    cli = NautobotClient(_settings(tenant_scope=("nope",)))
    respx.get(f"{BASE}/api/tenancy/tenants/", params={"name": "nope"}).mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    with pytest.raises(PermissionError, match="resolved to zero tenants"):
        await cli.rest_list("/api/dcim/devices/")
    await cli.aclose()


@respx.mock
async def test_resolution_is_cached() -> None:
    cli = NautobotClient(_settings(tenant_scope=("acme",)))
    route = respx.get(f"{BASE}/api/tenancy/tenants/", params={"name": "acme"}).mock(
        return_value=httpx.Response(200, json={"results": [{"id": ACME_ID}]})
    )
    respx.get(f"{BASE}/api/dcim/devices/").mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    await cli.rest_list("/api/dcim/devices/")
    await cli.rest_list("/api/dcim/devices/")
    await cli.aclose()

    assert route.call_count == 1
