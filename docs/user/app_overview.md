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
  nautobot-mcp-server
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

## Safety model

- **Read-only by default** — `rest_create` / `rest_update` / `rest_delete` and
  the domain write tools are blocked unless `allow_writes` is enabled.
- **Tenant scoping** — restrict every read and write to one or more tenants for
  MSP-style isolation.
- **Token-scoped** — the server can only do what the configured API token's
  Nautobot permissions allow; Job runs are additionally gated per-job.
