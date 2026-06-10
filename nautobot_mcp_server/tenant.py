"""Tenant scoping for the Nautobot MCP server.

In MSP / multi-tenant deployments a single MCP server (and a single
Nautobot token) may serve agents that must only ever see one customer's
data. When ``tenant_scope`` / ``tenant_group_scope`` are configured, the
:class:`~nautobot_mcp_server.client.NautobotClient` enforces those limits
centrally so an agent cannot cross customer boundaries -- regardless of
the filters it passes.

Enforcement is applied to *tenant-aware* endpoints only (the ones whose
objects carry a ``tenant`` foreign key). Endpoints that have no tenant
concept (manufacturers, platforms, statuses, content-types, ...) are left
untouched.

This module is deliberately Nautobot-version-pinned via a static map of
endpoints rather than runtime schema introspection: it keeps enforcement
predictable and auditable.
"""

from __future__ import annotations

from typing import Any

# Map of tenant-aware REST endpoint -> the query-param used to constrain a
# *list* by tenant UUID. For most models this is ``tenant_id``; for the
# tenants endpoint itself we constrain by the object's own ``id``.
_TENANT_FILTER_PARAM: dict[str, str] = {
    "/api/dcim/devices/": "tenant_id",
    "/api/dcim/racks/": "tenant_id",
    "/api/dcim/rack-reservations/": "tenant_id",
    "/api/dcim/locations/": "tenant_id",
    "/api/ipam/prefixes/": "tenant_id",
    "/api/ipam/ip-addresses/": "tenant_id",
    "/api/ipam/vlans/": "tenant_id",
    "/api/ipam/vrfs/": "tenant_id",
    "/api/circuits/circuits/": "tenant_id",
    "/api/virtualization/virtual-machines/": "tenant_id",
    "/api/virtualization/clusters/": "tenant_id",
    "/api/tenancy/tenants/": "id",
}

TENANTS_ENDPOINT = "/api/tenancy/tenants/"


def tenant_filter_param(endpoint: str) -> str | None:
    """Return the constraining query-param name for ``endpoint``.

    ``None`` means the endpoint is not tenant-aware and should not be
    scoped at all.
    """
    return _TENANT_FILTER_PARAM.get(endpoint)


def is_tenant_aware(endpoint: str) -> bool:
    """True when objects at ``endpoint`` carry a tenant we can enforce on."""
    return endpoint in _TENANT_FILTER_PARAM


def tenant_id_of(endpoint: str, obj: dict[str, Any]) -> str | None:
    """Extract the tenant UUID an object belongs to.

    For the tenants endpoint the relevant id is the object's own ``id``.
    For every other tenant-aware endpoint it is ``obj["tenant"]["id"]``.
    Returns ``None`` when the object has no tenant assigned (which, under
    an active scope, is treated as out-of-scope).
    """
    if endpoint == TENANTS_ENDPOINT:
        return obj.get("id")
    tenant = obj.get("tenant")
    if isinstance(tenant, dict):
        return tenant.get("id")
    if isinstance(tenant, str):  # some serializers return a bare id/url
        return tenant
    return None


class TenantScope:
    """Holds the configured scope and caches the resolved tenant UUIDs."""

    def __init__(
        self,
        tenant_names: tuple[str, ...] = (),
        tenant_group_names: tuple[str, ...] = (),
    ) -> None:
        self.names = tuple(tenant_names)
        self.groups = tuple(tenant_group_names)
        self._resolved_ids: frozenset[str] | None = None

    @property
    def active(self) -> bool:
        return bool(self.names or self.groups)

    @property
    def resolved_ids(self) -> frozenset[str] | None:
        return self._resolved_ids

    def set_resolved(self, ids: frozenset[str]) -> None:
        self._resolved_ids = ids

    def describe(self) -> dict[str, Any]:
        return {
            "active": self.active,
            "tenant_names": list(self.names),
            "tenant_group_names": list(self.groups),
            "resolved_tenant_ids": (
                sorted(self._resolved_ids)
                if self._resolved_ids is not None
                else None
            ),
        }
