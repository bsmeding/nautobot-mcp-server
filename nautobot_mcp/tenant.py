"""Limit REST calls to configured tenants.

MSP use: one server, one token, but the agent only sees named tenants.
Only endpoints that have a tenant field are filtered. The endpoint map
is static on purpose — no schema lookup at runtime.
"""

from __future__ import annotations

from typing import Any

# Endpoint -> query param that limits a list to a tenant UUID.
# Most models use tenant_id. The tenants endpoint itself uses id.
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
    """Query param for this endpoint, or None when it has no tenant."""
    return _TENANT_FILTER_PARAM.get(endpoint)


def is_tenant_aware(endpoint: str) -> bool:
    """True when this endpoint has a tenant field we filter on."""
    return endpoint in _TENANT_FILTER_PARAM


def tenant_id_of(endpoint: str, obj: dict[str, Any]) -> str | None:
    """Tenant UUID on this object.

    Tenants endpoint: the object's own id. Elsewhere: obj["tenant"]["id"].
    None means no tenant — treated as out of scope when a scope is active.
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
    """Configured tenant names, plus the UUIDs once they are looked up."""

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
