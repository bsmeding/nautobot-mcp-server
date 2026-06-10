# Nautobot MCP Server

A Nautobot app and standalone [Model Context Protocol](https://modelcontextprotocol.io/)
(MCP) server that exposes Nautobot's built-in REST and GraphQL APIs as tools
for LLMs and AI assistants.

It can run two ways:

- **As a Nautobot app** — add `nautobot_mcp_server` to `PLUGINS` and configure
  it via `PLUGINS_CONFIG`.
- **As a standalone MCP server** — run the `nautobot-mcp-server` console script
  against any reachable Nautobot, configured with environment variables.

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
