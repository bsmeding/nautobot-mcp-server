# nautobot-mcp-server

A [Model Context Protocol](https://modelcontextprotocol.io) server that exposes
[Nautobot](https://docs.nautobot.com/)'s built-in REST and GraphQL APIs as
tools for LLMs and AI assistants such as Claude Desktop, Cursor, and any other
MCP-compatible client.

It can be used in two ways:

- **As a Nautobot app** — drop it into a Nautobot environment, configure
  `PLUGINS_CONFIG`, and run the MCP server alongside Nautobot.
- **As a standalone stdio MCP server** — installed in any Python environment
  with the `nautobot-mcp-server` console script, talking to a remote Nautobot
  over its REST API.

This release focuses on **Nautobot's internal/built-in models only** (DCIM,
IPAM, circuits, tenancy, virtualization, extras/jobs, users, GraphQL).
Third-party Nautobot apps (Design Builder, Onboarding, SSoT, Golden Config,
ChatOps, …) are not yet wrapped — but the generic `rest_list` / `rest_get`
tools work against their endpoints if your token has access.

## Installation

```bash
pip install nautobot-mcp-server
```

When running inside a Nautobot environment, install the optional `nautobot`
extra (it pins a compatible Nautobot version):

```bash
pip install "nautobot-mcp-server[nautobot]"
```

### Optional Nautobot app (plugin) integrations

The base install exposes only Nautobot **core** tools. Tools for the
NetworkToCode apps are optional and can be added via extras:

```bash
pip install "nautobot-mcp-server[design-builder]"   # Design Builder tools
pip install "nautobot-mcp-server[onboarding]"        # Device Onboarding tools
pip install "nautobot-mcp-server[ssot]"              # SSoT tools
pip install "nautobot-mcp-server[golden-config]"     # Golden Config tools
pip install "nautobot-mcp-server[nornir]"            # Nornir backend tools
pip install "nautobot-mcp-server[all]"               # all of the above
```

By default (`plugins = ["auto"]`) a plugin's tools are registered when its
Python package is importable — so installing an extra is all you need when the
MCP server shares the Nautobot environment.

For a **standalone** MCP server talking to a *remote* Nautobot, the app lives
on the remote instance, not in the MCP server's venv. In that case don't rely
on `auto`; enable the tools explicitly:

```bash
export NAUTOBOT_MCP_PLUGINS="design_builder,ssot"   # or "all"
```

Use the `list_active_plugins` tool to see what's configured, enabled, and
available.

## Configure as a Nautobot app

In your `nautobot_config.py`:

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
        # Tenant scoping (MSP multi-tenant isolation); empty = no scoping
        "tenant_scope": [],          # e.g. ["acme", "globex"]
        "tenant_group_scope": [],    # e.g. ["managed-customers"]
    }
}
```

Then run the MCP server alongside Nautobot:

```bash
nautobot-mcp-server
```

It reads the same configuration from `PLUGINS_CONFIG` when launched from a
Nautobot environment.

## Configure as a standalone MCP server

Set environment variables and run the console script:

```bash
export NAUTOBOT_URL="https://nautobot.example.com"
export NAUTOBOT_TOKEN="YOUR_API_TOKEN"
nautobot-mcp-server
```

All configuration knobs:

| Env var | Default | Purpose |
| --- | --- | --- |
| `NAUTOBOT_URL` | — (required) | Nautobot base URL. |
| `NAUTOBOT_TOKEN` | — (required) | Nautobot API token. |
| `NAUTOBOT_VERIFY_SSL` | `true` | `false` disables TLS verification. |
| `NAUTOBOT_CA_BUNDLE` | — | Path to a CA bundle (private CA setups). |
| `NAUTOBOT_TIMEOUT` | `30` | HTTP timeout in seconds. |
| `NAUTOBOT_MAX_PAGINATION_RECORDS` | `5000` | Hard cap when `paginate=True`. |
| `NAUTOBOT_ALLOW_WRITES` | `false` | Enable POST/PATCH/PUT/DELETE tools. |
| `NAUTOBOT_TENANT_SCOPE` | — | Comma-separated tenant names/slugs to restrict access to. |
| `NAUTOBOT_TENANT_GROUP_SCOPE` | — | Comma-separated tenant group names to restrict access to. |
| `MCP_LOG_LEVEL` | `INFO` | Log level (logs go to stderr). |

## Hooking into Claude Desktop

Add to `claude_desktop_config.json`:

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

Other transports are also supported via CLI flag:

```bash
nautobot-mcp-server --transport streamable-http
nautobot-mcp-server --transport sse
```

## Read-only by default

Mutating operations (`rest_create`, `rest_update`, `rest_delete`) are blocked
unless you explicitly set `NAUTOBOT_ALLOW_WRITES=true` (or `allow_writes: true`
in `PLUGINS_CONFIG`). GraphQL queries and Nautobot Job runs are allowed
regardless, since they are sandboxed by Nautobot's own permission model and
the API token's scope.

## Tenant scoping (multi-tenant / MSP isolation)

For MSP-style deployments where one server (and one Nautobot token) serves
agents acting on behalf of different customers, you can lock the server to one
or more tenants. Set `tenant_scope` (tenant names/slugs) and/or
`tenant_group_scope` (tenant group names), via env vars or `PLUGINS_CONFIG`:

```bash
export NAUTOBOT_TENANT_SCOPE="acme"
# or multiple / by group:
export NAUTOBOT_TENANT_SCOPE="acme,globex"
export NAUTOBOT_TENANT_GROUP_SCOPE="managed-customers"
```

When a scope is active, enforcement happens centrally in the client, so an
agent cannot cross customer boundaries regardless of the filters it passes:

- **List/search** on tenant-aware endpoints (devices, racks, locations,
  prefixes, IP addresses, VLANs, VRFs, circuits, VMs, clusters) is constrained
  to the in-scope tenants. Any caller-supplied `tenant`/`tenant_id` filter is
  dropped and replaced.
- **Single-object reads** are verified against the scope; out-of-scope objects
  (including those with no tenant) raise `PermissionError`.
- **Creates** must target an in-scope tenant. If exactly one tenant is in
  scope it is injected automatically; with multiple, `tenant` must be set
  explicitly.
- **Updates/deletes** first verify the target object is in scope, and reject
  reassigning an object to an out-of-scope tenant.

Non-tenant-aware endpoints (manufacturers, platforms, statuses, content-types,
…) are left untouched. Run the `tenant_scope_info` tool to see the active
scope and resolved tenant UUIDs.

> Note: tenant scoping constrains the REST tools. The generic `graphql_query`
> tool and Nautobot Job runs are **not** tenant-filtered — rely on a
> tenant-restricted API token and/or per-job permissions for those paths.

## Tool catalog

### Discovery & metadata

- `nautobot_status` — Nautobot version, plugins, db backend
- `list_api_roots` — top-level REST categories
- `list_endpoints_in(category)` — sub-endpoints inside `dcim`, `ipam`, etc.
- `list_content_types`
- `tenant_scope_info` — active tenant scope (if any) and resolved tenant UUIDs
- `list_active_plugins` — configured/enabled/available plugin integrations

### Generic REST passthrough

- `rest_list(endpoint, filters, limit, offset, paginate, max_records)`
- `rest_get(endpoint, object_id)`
- `rest_create(endpoint, data)` *(write)*
- `rest_update(endpoint, object_id, data, partial)` *(write)*
- `rest_delete(endpoint, object_id)` *(write)*

### DCIM

- `list_devices`, `get_device`, `get_device_interfaces`,
  `get_device_config_context`, `get_device_inventory`
- `list_locations`, `get_location`, `list_location_types`
- `list_racks`, `get_rack`, `get_rack_elevation`
- `list_device_types`, `list_device_roles`, `list_manufacturers`,
  `list_platforms`
- `list_cables`

### IPAM

- `list_prefixes`, `get_prefix`, `get_available_ips`,
  `get_available_prefixes`
- `list_ip_addresses`, `get_ip_address`
- `list_vlans`, `get_vlan`, `list_vlan_groups`
- `list_vrfs`, `list_rirs`, `list_namespaces`

### Circuits / Tenancy / Virtualization

- `list_circuits`, `get_circuit`, `list_providers`, `list_circuit_types`,
  `list_circuit_terminations`
- `list_tenants`, `get_tenant`, `list_tenant_groups`
- `list_virtual_machines`, `get_virtual_machine`, `get_vm_interfaces`,
  `list_clusters`, `list_cluster_types`

### Extras (jobs, statuses, tags, custom fields, …)

- `list_jobs`, `get_job`, `run_job`, `get_job_result`,
  `list_recent_job_results`, `get_job_logs`
- `list_statuses`, `list_tags`, `list_roles`
- `list_custom_fields`, `list_relationships`, `list_computed_fields`,
  `list_config_contexts`
- `list_webhooks`, `list_secrets_groups`

### Users

- `list_users`, `list_groups`, `list_object_permissions`

### GraphQL

- `graphql_query(query, variables)`
- `graphql_introspect`

### Cross-domain search shortcuts

- `search_devices`, `search_ip_addresses`, `search_prefixes`,
  `search_locations`, `search_circuits`

### Optional plugin tools

Registered only when the matching plugin is enabled (see
[Optional Nautobot app integrations](#optional-nautobot-app-plugin-integrations)).

- **Design Builder** — `list_designs`, `list_design_deployments`,
  `list_design_jobs`, `run_design`
- **Device Onboarding** — `list_onboarding_jobs`, `onboard_device`
- **SSoT** — `list_ssot_jobs`, `list_ssot_syncs`, `list_ssot_sync_logs`,
  `run_ssot_sync`
- **Golden Config** — `list_config_compliance`, `compliance_summary`,
  `list_compliance_rules`, `list_compliance_features`, `list_golden_config`,
  `list_golden_config_settings`, `get_intended_config`,
  `list_golden_config_jobs`, `run_golden_config_job`
- **Nornir** — `nornir_plugin_info` (backend used by Golden Config /
  Onboarding; device tasks run via those apps' jobs)

## Development

```bash
pip install -e ".[dev]"
ruff check nautobot_mcp_server tests
pytest -v
python -m build
```

## Roadmap

- More wrappers for popular Nautobot apps (Golden Config, ChatOps, …) using
  the optional-plugin pattern.
- Streaming responses for very large result sets.
- HTTP `/health` endpoint for the streamable-http transport.

## License

MIT
