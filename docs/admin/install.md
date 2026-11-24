# Install & Configure

There are two ways to run it. They use the same `NAUTOBOT_URL` and
`NAUTOBOT_TOKEN` names. Claude Desktop only needs an `mcpServers` entry;
the machine that runs `nautobot-mcp` is what changes.

## Local server (Claude Desktop, Cursor)

Each person runs `nautobot-mcp` on their own machine. Nautobot does not
need this app installed. The client config is the whole setup. `uvx`
downloads the package on first start, so install [uv](https://docs.astral.sh/uv/)
once on that machine.

Claude Desktop: `~/Library/Application Support/Claude/claude_desktop_config.json`.
Restart Claude after saving.

```json
{
  "mcpServers": {
    "nautobot": {
      "command": "uvx",
      "args": ["nautobot-mcp"],
      "env": {
        "NAUTOBOT_URL": "https://nautobot.example.com",
        "NAUTOBOT_TOKEN": "YOUR_PERSONAL_API_TOKEN"
      }
    }
  }
}
```

`NAUTOBOT_TOKEN` is that person's Nautobot API token. Nautobot records their
changes as that user. If `nautobot-mcp` is already on `PATH`, set
`"command": "nautobot-mcp"` and omit `args`.

## As a Nautobot app

Install into your Nautobot environment (pin a compatible Nautobot via the
`nautobot` extra):

```bash
pip install "nautobot-mcp[nautobot]"
```

Enable and configure it in `nautobot_config.py`:

```python
PLUGINS = ["nautobot_mcp"]

PLUGINS_CONFIG = {
    "nautobot_mcp": {
        "nautobot_url": "https://nautobot.example.com",
        "nautobot_token": "YOUR_API_TOKEN",
        "verify_ssl": True,
        # Optional
        "ca_bundle": "",
        "request_timeout": 30,
        "max_pagination_records": 5000,
        "allow_writes": False,
        "log_level": "INFO",
        "log_file": "/var/log/nautobot/nautobot-mcp.log",
        # Shared server: each MCP client sends its own Nautobot token.
        # Leave nautobot_token empty in that mode.
        "require_client_token": False,
        "tenant_scope": [],          # e.g. ["acme", "globex"]
        "tenant_group_scope": [],    # e.g. ["managed-customers"]
        "plugins": ["auto"],         # from /api/status/, or explicit keys / "all"
    }
}
```

Run migrations (none are shipped today, but this is harmless) and restart
Nautobot.

The app then shows up in the UI:

- **Apps → Installed Apps** lists **Nautobot MCP Server** (version, author, description).
- **Apps → MCP Server → MCP Server Status** (`/plugins/mcp-server/`) shows the
  resolved settings and, when `log_file` is set, the tail of that log.

The status page is not the MCP endpoint. Clients still talk to a
`nautobot-mcp` process. Start it next to Nautobot (same environment, so it
reads `PLUGINS_CONFIG`):

```bash
nautobot-mcp
```

For one shared HTTP listener instead of a process per person:

```bash
nautobot-mcp --transport streamable-http --host 0.0.0.0 --port 8000
```

## Configuration reference

| Env var | `PLUGINS_CONFIG` key | Default | Purpose |
| --- | --- | --- | --- |
| `NAUTOBOT_URL` | `nautobot_url` | — (required) | Nautobot base URL. |
| `NAUTOBOT_TOKEN` | `nautobot_token` | — (required unless client tokens) | API token for this process. |
| `NAUTOBOT_MCP_REQUIRE_CLIENT_TOKEN` | `require_client_token` | `false` | HTTP clients must send their own token. |
| `NAUTOBOT_MCP_VERIFY_SSL` | `verify_ssl` | `true` | TLS verification. |
| `NAUTOBOT_MCP_CA_BUNDLE` | `ca_bundle` | — | CA bundle path. |
| `NAUTOBOT_MCP_TIMEOUT` | `request_timeout` | `30` | HTTP timeout (s). |
| `NAUTOBOT_MCP_MAX_PAGINATION_RECORDS` | `max_pagination_records` | `5000` | Pagination cap. |
| `NAUTOBOT_MCP_ALLOW_WRITES` | `allow_writes` | `false` | Enable write tools. |
| `NAUTOBOT_MCP_TENANT_SCOPE` | `tenant_scope` | — | Restrict to tenants. |
| `NAUTOBOT_MCP_TENANT_GROUP_SCOPE` | `tenant_group_scope` | — | Restrict to tenant groups. |
| `NAUTOBOT_MCP_PLUGINS` | `plugins` | `auto` | Plugin integrations to enable. |
| `NAUTOBOT_MCP_LOG_LEVEL` | `log_level` | `INFO` | Log level. |
| `NAUTOBOT_MCP_LOG_FILE` | `log_file` | — | Also write logs here. The status page shows the tail. |
| `NAUTOBOT_MCP_HOST` | — | `127.0.0.1` | Bind address for HTTP/SSE transports. CLI `--host` wins. |
| `NAUTOBOT_MCP_PORT` | — | `8000` | Bind port for HTTP/SSE transports. CLI `--port` wins. |

Legacy unprefixed names (`NAUTOBOT_ALLOW_WRITES`, `NAUTOBOT_TENANT_SCOPE`,
`MCP_LOG_LEVEL`, …) are still accepted; the `NAUTOBOT_MCP_*` form wins when
both are set.

## One token per person

Nautobot writes the change log as the user who owns the API token. A single
`nautobot_token` on a shared server records every caller as that one user.

For a shared `streamable-http` or `sse` server, turn on client tokens and
leave the server token empty:

```python
PLUGINS_CONFIG = {
    "nautobot_mcp": {
        "nautobot_url": "https://nautobot.example.com",
        "require_client_token": True,
    }
}
```

Each Cursor or Claude client sends its own token. Nautobot then permits and
audits the call as that token's user:

```json
{
  "mcpServers": {
    "nautobot": {
      "url": "http://mcp-host:8000/mcp",
      "headers": {
        "X-Nautobot-Token": "YOUR_PERSONAL_API_TOKEN"
      }
    }
  }
}
```

`Authorization: Token <your token>` is accepted as well. `Authorization: Bearer`
is not forwarded to Nautobot. A call with no token is refused, so it cannot
fall back to a shared user.

A local stdio client (`nautobot-mcp` in that person's MCP config) already has
its own identity: set `NAUTOBOT_TOKEN` in that config to their token.
