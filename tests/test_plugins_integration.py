"""Integration tests for plugin REST/job tools against a mocked Nautobot."""

from __future__ import annotations

import httpx
import pytest
import respx

from nautobot_mcp_server import runtime
from nautobot_mcp_server.client import NautobotClient
from nautobot_mcp_server.config import NautobotMcpSettings
from nautobot_mcp_server.tools.plugins import (
    design_builder,
    golden_config,
    nornir,
    onboarding,
    ssot,
)

pytestmark = pytest.mark.asyncio

BASE = "https://nautobot.example.com"
GC = f"{BASE}/api/plugins/golden-config"


class CapturingMCP:
    """Captures the actual registered tool callables for invocation."""

    def __init__(self) -> None:
        self.fns: dict = {}

    def tool(self):
        def deco(fn):
            self.fns[fn.__name__] = fn
            return fn

        return deco


def _settings(**overrides) -> NautobotMcpSettings:
    base = dict(
        url=BASE,
        token="t" * 40,
        verify_ssl=True,
        request_timeout=5.0,
        max_pagination_records=100,
        allow_writes=True,
        log_level="DEBUG",
    )
    base.update(overrides)
    return NautobotMcpSettings(**base)


@pytest.fixture
async def tools():
    """Register every plugin module and wire up a live (mocked) client."""
    settings = _settings()
    cli = NautobotClient(settings)
    runtime.set_settings(settings)
    runtime.set_client(cli)
    mcp = CapturingMCP()
    for mod in (design_builder, onboarding, ssot, golden_config, nornir):
        mod.register(mcp)
    try:
        yield mcp.fns
    finally:
        await cli.aclose()
        runtime.reset()


# ---- Golden Config ----------------------------------------------------


@respx.mock
async def test_list_config_compliance(tools) -> None:
    route = respx.get(f"{GC}/config-compliance/").mock(
        return_value=httpx.Response(200, json={"count": 0, "results": []})
    )
    await tools["list_config_compliance"](filters={"device": "dev1"})
    assert route.called
    assert route.calls.last.request.url.params.get("device") == "dev1"


@respx.mock
async def test_get_intended_config(tools) -> None:
    respx.get(f"{GC}/config-postprocessing/dev1/").mock(
        return_value=httpx.Response(200, json={"config": "hostname r1\n"})
    )
    out = await tools["get_intended_config"]("dev1")
    assert out["config"].startswith("hostname")


@respx.mock
async def test_compliance_summary_aggregates(tools) -> None:
    rows = {
        "count": 3,
        "next": None,
        "results": [
            {
                "device": {"name": "r1"},
                "rule": {"feature": {"name": "aaa"}},
                "compliance": True,
            },
            {
                "device": {"name": "r1"},
                "rule": {"feature": {"name": "ntp"}},
                "compliance": False,
            },
            {
                "device": {"name": "r2"},
                "rule": {"feature": {"name": "aaa"}},
                "compliance": True,
            },
        ],
    }
    respx.get(f"{GC}/config-compliance/").mock(
        return_value=httpx.Response(200, json=rows)
    )
    summary = await tools["compliance_summary"]()
    assert summary["total_results"] == 3
    assert summary["compliant"] == 2
    assert summary["non_compliant"] == 1
    assert summary["compliance_rate"] == round(2 / 3, 4)
    assert summary["devices"]["r1"] == {"compliant": 1, "non_compliant": 1}
    assert summary["non_compliant_items"] == [{"device": "r1", "feature": "ntp"}]


@respx.mock
async def test_compliance_summary_empty(tools) -> None:
    respx.get(f"{GC}/config-compliance/").mock(
        return_value=httpx.Response(200, json={"count": 0, "next": None, "results": []})
    )
    summary = await tools["compliance_summary"]()
    assert summary["total_results"] == 0
    assert summary["compliance_rate"] is None


# ---- SSoT / Design Builder -------------------------------------------


@respx.mock
async def test_list_ssot_syncs(tools) -> None:
    route = respx.get(f"{BASE}/api/plugins/ssot/sync/").mock(
        return_value=httpx.Response(200, json={"count": 0, "results": []})
    )
    await tools["list_ssot_syncs"]()
    assert route.called


@respx.mock
async def test_list_designs(tools) -> None:
    route = respx.get(f"{BASE}/api/plugins/design-builder/designs/").mock(
        return_value=httpx.Response(
            200, json={"count": 1, "next": None, "results": [{"id": "d1"}]}
        )
    )
    out = await tools["list_designs"]()
    assert route.called
    assert out[0]["id"] == "d1"


# ---- job run path -----------------------------------------------------


@respx.mock
async def test_run_ssot_sync_posts_to_run_endpoint(tools) -> None:
    # lookup_id_or_name first tries GET by id (404), then filters by name.
    respx.get(f"{BASE}/api/extras/jobs/MySync/").mock(
        return_value=httpx.Response(404)
    )
    respx.get(f"{BASE}/api/extras/jobs/").mock(
        return_value=httpx.Response(200, json={"results": [{"id": "job1"}]})
    )
    run = respx.post(f"{BASE}/api/extras/jobs/job1/run/").mock(
        return_value=httpx.Response(200, json={"job_result": {"id": "jr1"}})
    )
    out = await tools["run_ssot_sync"]("MySync", data={"dry_run": True})
    assert run.called
    assert out["job_result"]["id"] == "jr1"


# ---- Nornir -----------------------------------------------------------


@respx.mock
async def test_nornir_plugin_info(tools) -> None:
    respx.get(f"{BASE}/api/status/").mock(
        return_value=httpx.Response(
            200,
            json={
                "installed-apps": {"nautobot_plugin_nornir": "2.1.0"},
                "plugins": {"nautobot_plugin_nornir": {"nornir_settings": {}}},
            },
        )
    )
    info = await tools["nornir_plugin_info"]()
    assert info["installed"] is True
    assert info["version"] == "2.1.0"
    assert info["plugins_config"] == {"nornir_settings": {}}
