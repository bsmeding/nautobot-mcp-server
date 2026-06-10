# Plugin Integrations

The base install exposes only Nautobot **core** tools. Tools for the
NetworkToCode apps are optional and installed via extras:

```bash
pip install "nautobot-mcp-server[design-builder]"
pip install "nautobot-mcp-server[onboarding]"
pip install "nautobot-mcp-server[ssot]"
pip install "nautobot-mcp-server[golden-config]"
pip install "nautobot-mcp-server[nornir]"
pip install "nautobot-mcp-server[all]"
```

## Enabling

The `plugins` setting (env `NAUTOBOT_MCP_PLUGINS`, default `auto`) decides which
plugin tools register:

- `auto` — enable a plugin when its Python package is importable. Pairs with the
  pip extras when the MCP server shares the Nautobot environment.
- explicit keys (`design_builder`, `onboarding`, `ssot`, `golden_config`,
  `nornir`) — force-enable even if the package is not importable locally
  (useful for a standalone server talking to a remote Nautobot).
- `all` — force-enable every known plugin.

Inspect the result at runtime with `list_active_plugins`.

## Tools by plugin

| Plugin | Tools |
| --- | --- |
| Design Builder | `list_designs`, `list_design_deployments`, `list_design_jobs`, `run_design` |
| Device Onboarding | `list_onboarding_jobs`, `onboard_device` |
| SSoT | `list_ssot_jobs`, `list_ssot_syncs`, `list_ssot_sync_logs`, `run_ssot_sync` |
| Golden Config | `list_config_compliance`, `compliance_summary`, `list_compliance_rules`, `list_compliance_features`, `list_golden_config`, `list_golden_config_settings`, `get_intended_config`, `list_golden_config_jobs`, `run_golden_config_job` |
| Nornir | `nornir_plugin_info` (backend used by Golden Config / Onboarding) |

Most of these apps are driven by Nautobot **Jobs**, so the tools are
job-centric: list the relevant jobs, then run them with inputs.
