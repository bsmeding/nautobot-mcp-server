# Getting Started

## Standalone MCP server

```bash
pip install nautobot-mcp-server

export NAUTOBOT_URL="https://nautobot.example.com"
export NAUTOBOT_TOKEN="YOUR_API_TOKEN"
nautobot-mcp-server
```

Hook it into Claude Desktop via `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "nautobot": {
      "command": "nautobot-mcp-server",
      "env": {
        "NAUTOBOT_URL": "https://nautobot.example.com",
        "NAUTOBOT_TOKEN": "YOUR_API_TOKEN"
      }
    }
  }
}
```

Other transports:

```bash
nautobot-mcp-server --transport streamable-http
nautobot-mcp-server --transport sse
```

## As a Nautobot app

See [Install & Configure](../admin/install.md).

## First calls

Good discovery tools to try first:

- `nautobot_status` — versions, installed apps, db backend.
- `list_api_roots` — top-level REST categories.
- `tenant_scope_info` — active tenant scope (if any).
- `list_active_plugins` — which optional integrations are enabled.
