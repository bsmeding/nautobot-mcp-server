# Install & Configure

## As a Nautobot app

Install into your Nautobot environment (pin a compatible Nautobot via the
`nautobot` extra):

```bash
pip install "nautobot-mcp-server[nautobot]"
```

Enable and configure it in `nautobot_config.py`:

```python
PLUGINS = ["nautobot_mcp_server"]

PLUGINS_CONFIG = {
    "nautobot_mcp_server": {
        "nautobot_url": "https://nautobot.example.com",
        "nautobot_token": "YOUR_API_TOKEN",
        "verify_ssl": True,
        # Optional
        "ca_bundle": "",
        "request_timeout": 30,
        "max_pagination_records": 5000,
        "allow_writes": False,
        "log_level": "INFO",
        "tenant_scope": [],          # e.g. ["acme", "globex"]
        "tenant_group_scope": [],    # e.g. ["managed-customers"]
        "plugins": ["auto"],         # or explicit keys / "all"
    }
}
```

Run migrations (none are shipped today, but this is harmless) and restart
Nautobot, then run the MCP server alongside it:

```bash
nautobot-mcp-server
```

## Configuration reference

| Env var | `PLUGINS_CONFIG` key | Default | Purpose |
| --- | --- | --- | --- |
| `NAUTOBOT_URL` | `nautobot_url` | — (required) | Nautobot base URL. |
| `NAUTOBOT_TOKEN` | `nautobot_token` | — (required) | API token. |
| `NAUTOBOT_MCP_VERIFY_SSL` | `verify_ssl` | `true` | TLS verification. |
| `NAUTOBOT_MCP_CA_BUNDLE` | `ca_bundle` | — | CA bundle path. |
| `NAUTOBOT_MCP_TIMEOUT` | `request_timeout` | `30` | HTTP timeout (s). |
| `NAUTOBOT_MCP_MAX_PAGINATION_RECORDS` | `max_pagination_records` | `5000` | Pagination cap. |
| `NAUTOBOT_MCP_ALLOW_WRITES` | `allow_writes` | `false` | Enable write tools. |
| `NAUTOBOT_MCP_TENANT_SCOPE` | `tenant_scope` | — | Restrict to tenants. |
| `NAUTOBOT_MCP_TENANT_GROUP_SCOPE` | `tenant_group_scope` | — | Restrict to tenant groups. |
| `NAUTOBOT_MCP_PLUGINS` | `plugins` | `auto` | Plugin integrations to enable. |
| `NAUTOBOT_MCP_LOG_LEVEL` | `log_level` | `INFO` | Log level. |

Legacy unprefixed names (`NAUTOBOT_ALLOW_WRITES`, `NAUTOBOT_TENANT_SCOPE`,
`MCP_LOG_LEVEL`, …) are still accepted; the `NAUTOBOT_MCP_*` form wins when
both are set.
