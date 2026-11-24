# App Overview

The Nautobot MCP Server turns a Nautobot instance into a set of MCP **tools**
an AI client (Claude Desktop, a portal, or a custom agent) can call. Rather
than writing bespoke integration glue for each agent, you expose Nautobot once
over MCP and let agent behavior live in prompts and tool selection.

## Architecture

```
Any MCP client (Claude Desktop, portal, custom agent)
        │  MCP protocol (stdio / streamable-http / sse)
        ▼
  nautobot-mcp
        │  REST + GraphQL (token auth)
        ▼
     Nautobot
```

The server is a thin, auditable layer over Nautobot's APIs:

- A generic async HTTP client with token auth, retries, automatic pagination,
  and a write-mode safety gate.
- Domain tool modules (DCIM, IPAM, circuits, tenancy, virtualization, extras /
  jobs) plus a generic `rest_list` / `rest_get` / `rest_create` passthrough and
  a `graphql_query` escape hatch.
- Optional plugin tool modules for popular Nautobot apps, enabled on demand.

## In the Nautobot UI

When `nautobot_mcp` is in `PLUGINS` and Nautobot has been restarted:

- **Apps → Installed Apps** lists Nautobot MCP Server.
- **Apps → MCP Server → MCP Server Status** (`/plugins/mcp-server/`) shows
  settings and the log tail when `log_file` is set.

A local Claude or Cursor install does not need the app. Those clients run
`nautobot-mcp` themselves with `NAUTOBOT_URL` and `NAUTOBOT_TOKEN`.

## Safety model

- **Read-only by default** — `rest_create` / `rest_update` / `rest_delete` and
  the domain write tools are blocked unless `allow_writes` is enabled.
- **Tenant scoping** — restrict every read and write to one or more tenants for
  MSP-style isolation.
- **Token-scoped** — each call runs as a Nautobot API token, and Nautobot's
  change log records that token's user. On a shared HTTP server set
  `require_client_token` and have every MCP client send `X-Nautobot-Token`.
  A local stdio process uses its own `NAUTOBOT_TOKEN`. Job runs follow the
  same token.
