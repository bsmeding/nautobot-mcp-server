"""Tests for optional plugin (Nautobot app) tool gating and registration."""

from __future__ import annotations

import pytest

from nautobot_mcp_server.config import load_settings
from nautobot_mcp_server.tools import plugins


class FakeMCP:
    """Minimal stand-in capturing tool registrations."""

    def __init__(self) -> None:
        self.tools: list[str] = []

    def tool(self):
        def deco(fn):
            self.tools.append(fn.__name__)
            return fn

        return deco


# ---- is_plugin_enabled ------------------------------------------------


def test_auto_disabled_when_package_missing() -> None:
    assert (
        plugins.is_plugin_enabled("ssot", ("auto",), ("definitely_not_a_pkg",))
        is False
    )


def test_auto_enabled_when_package_importable() -> None:
    # "os" always imports, standing in for an installed app package.
    assert plugins.is_plugin_enabled("ssot", ("auto",), ("os",)) is True


def test_explicit_key_enables_without_package() -> None:
    assert (
        plugins.is_plugin_enabled("ssot", ("ssot",), ("missing_pkg",)) is True
    )


def test_all_enables_everything() -> None:
    assert (
        plugins.is_plugin_enabled("design_builder", ("all",), ("missing_pkg",))
        is True
    )


def test_hyphen_and_case_normalized_in_selectors() -> None:
    assert (
        plugins.is_plugin_enabled(
            "design_builder", ("Design-Builder",), ("missing_pkg",)
        )
        is True
    )


def test_unknown_selector_does_not_enable() -> None:
    assert (
        plugins.is_plugin_enabled("ssot", ("onboarding",), ("missing_pkg",))
        is False
    )


# ---- register_plugins -------------------------------------------------


def test_register_all_plugins() -> None:
    mcp = FakeMCP()
    enabled = plugins.register_plugins(mcp, ("all",))
    assert set(enabled) == set(plugins.available_plugins())
    # A few representative tools from each plugin should be present.
    assert "run_design" in mcp.tools
    assert "onboard_device" in mcp.tools
    assert "run_ssot_sync" in mcp.tools
    assert "list_config_compliance" in mcp.tools
    assert "nornir_plugin_info" in mcp.tools


def test_register_none_by_default_without_packages() -> None:
    mcp = FakeMCP()
    enabled = plugins.register_plugins(mcp, ("auto",))
    # None of the NTC app packages are installed in the test env.
    assert enabled == []
    assert mcp.tools == []


def test_register_selected_only() -> None:
    mcp = FakeMCP()
    enabled = plugins.register_plugins(mcp, ("ssot",))
    assert enabled == ["ssot"]
    assert "run_ssot_sync" in mcp.tools
    assert "run_design" not in mcp.tools


# ---- config -----------------------------------------------------------


def test_plugins_setting_parsed_and_normalized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NAUTOBOT_URL", "https://x.example.com")
    monkeypatch.setenv("NAUTOBOT_TOKEN", "tok")
    monkeypatch.setenv("NAUTOBOT_MCP_PLUGINS", "ssot, Design-Builder")
    s = load_settings()
    assert s.plugins == ("ssot", "design_builder")


def test_plugins_default_is_auto(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NAUTOBOT_URL", "https://x.example.com")
    monkeypatch.setenv("NAUTOBOT_TOKEN", "tok")
    monkeypatch.delenv("NAUTOBOT_MCP_PLUGINS", raising=False)
    s = load_settings()
    assert s.plugins == ("auto",)
