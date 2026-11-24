# Nautobot MCP Server

A Nautobot app and standalone [Model Context Protocol](https://modelcontextprotocol.io/)
(MCP) server that exposes Nautobot's built-in REST and GraphQL APIs as tools
for LLMs and AI assistants.

It can run two ways:

- **On the client** — Claude Desktop or Cursor runs `nautobot-mcp` with
  `NAUTOBOT_URL` and `NAUTOBOT_TOKEN` in `mcpServers`. Nautobot does not
  need the app installed for this.
- **As a Nautobot app** — add `nautobot_mcp` to `PLUGINS`. It shows under
  **Apps → Installed Apps** and **Apps → MCP Server → MCP Server Status**
  (settings and, with `log_file`, the log tail). The MCP process still
  runs beside Nautobot.

## Highlights

- Broad read tools across DCIM, IPAM, circuits, tenancy, virtualization, and
  extras, plus a generic REST/GraphQL passthrough for anything not wrapped.
- Read-only by default; mutating tools are gated behind an explicit
  `allow_writes` flag.
- **Tenant scoping** for MSP / multi-tenant isolation — see
  [Tenant Scoping](user/tenant_scoping.md).
- **Optional plugin integrations** (Design Builder, Onboarding, SSoT, Golden
  Config, Nornir) — see [Plugin Integrations](user/plugins.md).

Start with [App Overview](user/app_overview.md) or jump to
[Install & Configure](admin/install.md).
