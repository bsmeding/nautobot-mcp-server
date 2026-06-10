# Tenant Scoping

For MSP-style deployments where one server (and one Nautobot token) serves
agents acting for different customers, you can lock the server to one or more
tenants. Set `tenant_scope` (tenant names/slugs) and/or `tenant_group_scope`
(tenant group names), via env vars or `PLUGINS_CONFIG`:

```bash
export NAUTOBOT_TENANT_SCOPE="acme"
export NAUTOBOT_TENANT_SCOPE="acme,globex"        # multiple
export NAUTOBOT_TENANT_GROUP_SCOPE="managed-customers"
```

When a scope is active, enforcement happens centrally in the client so an agent
cannot cross customer boundaries regardless of the filters it passes:

- **List/search** on tenant-aware endpoints is constrained to the in-scope
  tenants; any caller-supplied `tenant`/`tenant_id` filter is dropped and
  replaced.
- **Single-object reads** are verified; out-of-scope objects (including those
  with no tenant) raise an error.
- **Creates** must target an in-scope tenant — injected automatically when a
  single tenant is in scope, otherwise required explicitly.
- **Updates/deletes** verify the target first and reject reassigning to an
  out-of-scope tenant.

Non-tenant-aware endpoints (manufacturers, platforms, statuses, …) are
untouched. Use the `tenant_scope_info` tool to see the active scope and
resolved tenant UUIDs.

!!! note
    Scoping constrains the REST tools. The generic `graphql_query` tool and
    Nautobot Job runs are **not** tenant-filtered — rely on a tenant-restricted
    token and/or per-job permissions for those paths.
