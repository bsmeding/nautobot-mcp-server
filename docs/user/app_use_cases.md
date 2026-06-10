# Use Cases

## Natural-language source-of-truth queries

Give a read-only agent the MCP tools and let users ask questions like "which
active core devices in Amsterdam are missing a primary IP?" The agent composes
`search_devices`, `get_device_interfaces`, and `list_ip_addresses` (or a single
`graphql_query`) to answer.

## Change planning

With `allow_writes` enabled and a scoped token, a change-planning agent can
allocate prefixes/IPs, create cables, set statuses, and trigger validated
Nautobot Jobs via `run_job` — reusing automation you already built.

## MSP multi-tenant isolation

Run a per-customer MCP server (or per-customer config) with
[tenant scoping](tenant_scoping.md) so an agent can only ever see and touch one
customer's data, regardless of the filters it passes.

## Driving Nautobot apps

Enable [plugin integrations](plugins.md) to let agents run Design Builder
designs, onboard devices, trigger SSoT syncs, or check Golden Config
compliance — all through the same MCP surface.
