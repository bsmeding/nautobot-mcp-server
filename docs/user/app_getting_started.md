# Getting Started

## Standalone MCP server

```bash
pip install nautobot-mcp

export NAUTOBOT_URL="https://nautobot.example.com"
export NAUTOBOT_TOKEN="YOUR_API_TOKEN"
nautobot-mcp
```

Hook it into Claude Desktop via `claude_desktop_config.json`. `uvx` looks for
an executable with the same name as the package, which is `nautobot-mcp`:

```json
{
  "mcpServers": {
    "nautobot": {
      "command": "uvx",
      "args": ["nautobot-mcp"],
      "env": {
        "NAUTOBOT_URL": "https://nautobot.example.com",
        "NAUTOBOT_TOKEN": "YOUR_API_TOKEN"
      }
    }
  }
}
```

Other transports listen on `127.0.0.1:8000` by default. Set `--host` and
`--port` (or `NAUTOBOT_MCP_HOST` / `NAUTOBOT_MCP_PORT`) when a reverse proxy
on another machine needs to reach the process. Point the MCP client at that
process or proxy. The Nautobot app does not expose an MCP HTTP endpoint.

```bash
nautobot-mcp --transport streamable-http
nautobot-mcp --transport streamable-http --host 0.0.0.0 --port 8000
nautobot-mcp --transport sse
```

Streamable HTTP is at `/mcp`. SSE is at `/sse`.

## Shared server, one token per person

Run one HTTP server and have each client send the Nautobot token of the
person using it. Nautobot's change log then shows that user.

```bash
export NAUTOBOT_URL="https://nautobot.example.com"
export NAUTOBOT_MCP_REQUIRE_CLIENT_TOKEN=true
nautobot-mcp --transport streamable-http --host 0.0.0.0 --port 8000
```

Cursor, Claude Desktop, or any other MCP client:

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

A call that omits the header is refused. The server token is not used, so
the action cannot be audited as someone else.

## As a Nautobot app

Install with `pip install "nautobot-mcp[nautobot]"`, add `nautobot_mcp` to
`PLUGINS`, and restart Nautobot. Full settings are in
[Install & Configure](../admin/install.md).

After restart the app is visible in Nautobot:

- **Apps → Installed Apps** lists Nautobot MCP Server.
- **Apps → MCP Server → MCP Server Status** (`/plugins/mcp-server/`) shows
  the resolved settings and the log tail when `log_file` is set.

That page does not serve MCP. Run `nautobot-mcp` beside Nautobot, or keep
using a local `mcpServers` entry with `NAUTOBOT_URL` and `NAUTOBOT_TOKEN`.

## First calls

Good discovery tools to try first:

- `nautobot_status` — versions, installed apps, db backend.
- `list_api_roots` — top-level REST categories.
- `tenant_scope_info` — active tenant scope (if any).
- `list_active_plugins` — which optional integrations are enabled.
