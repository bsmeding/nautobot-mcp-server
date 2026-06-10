"""Async HTTP client for Nautobot REST + GraphQL APIs.

The client is intentionally generic: callers pass an endpoint path
(starting with ``/api/``) plus optional filters. The class adds:

* token authentication
* response retries with exponential back-off on transport errors and 5xx
* automatic pagination (``rest_list``)
* a write-mode safety gate (refuses POST/PATCH/PUT/DELETE unless
  ``allow_writes`` is True). GraphQL queries are exempt because Nautobot
  exposes them via POST.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from .config import NautobotMcpSettings
from .tenant import (
    TENANTS_ENDPOINT,
    TenantScope,
    tenant_filter_param,
    tenant_id_of,
)

logger = logging.getLogger("nautobot_mcp_server.client")

_WRITE_METHODS: frozenset[str] = frozenset({"POST", "PATCH", "PUT", "DELETE"})

# Endpoints that legitimately use POST for read-style operations.
_READ_POST_ENDPOINTS: frozenset[str] = frozenset(
    {
        "/api/graphql/",
        "/api/ipam/prefixes/available-ips/",
        "/api/ipam/prefixes/available-prefixes/",
    }
)


class NautobotClient:
    """Async wrapper around Nautobot's REST and GraphQL APIs."""

    def __init__(self, settings: NautobotMcpSettings) -> None:
        self.settings = settings
        self.base_url = settings.url
        self._client = httpx.AsyncClient(
            base_url=settings.url,
            headers={
                "Authorization": f"Token {settings.token}",
                "Accept": "application/json",
                "User-Agent": "nautobot-mcp-server",
            },
            verify=settings.verify_ssl,
            timeout=settings.request_timeout,
            follow_redirects=True,
        )
        self.tenant_scope = TenantScope(
            settings.tenant_scope, settings.tenant_group_scope
        )

    # ---- lifecycle -----------------------------------------------------

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> NautobotClient:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.aclose()

    # ---- helpers -------------------------------------------------------

    @staticmethod
    def _normalize_endpoint(endpoint: str, *, trailing_slash: bool = True) -> str:
        endpoint = (endpoint or "").strip()
        if not endpoint.startswith("/"):
            endpoint = f"/{endpoint}"
        if not endpoint.startswith("/api/"):
            raise ValueError(
                f"Endpoint must start with '/api/', got: {endpoint!r}"
            )
        if trailing_slash and not endpoint.endswith("/"):
            endpoint = f"{endpoint}/"
        return endpoint

    def _check_write_allowed(self, method: str, endpoint: str) -> None:
        if (
            method in _WRITE_METHODS
            and endpoint not in _READ_POST_ENDPOINTS
            and not self.settings.allow_writes
        ):
            raise PermissionError(
                f"Refusing {method} {endpoint}: writes are disabled. "
                "Set NAUTOBOT_ALLOW_WRITES=true (or allow_writes=true in "
                "PLUGINS_CONFIG) to enable mutating operations."
            )

    # ---- tenant scoping ------------------------------------------------

    async def _resolve_tenant_ids(self) -> frozenset[str] | None:
        """Resolve configured tenant/group names to a set of tenant UUIDs.

        Returns ``None`` when no scope is configured. The result is cached
        on the :class:`TenantScope`. Raises ``PermissionError`` when the
        configured scope resolves to zero tenants (a likely misconfig that
        would otherwise silently hide all data).
        """
        if not self.tenant_scope.active:
            return None
        if self.tenant_scope.resolved_ids is not None:
            return self.tenant_scope.resolved_ids

        ids: set[str] = set()
        # Resolve by tenant name/slug and by tenant group. These GETs use
        # ``_request`` directly so they bypass scope enforcement (avoiding
        # infinite recursion).
        for name in self.tenant_scope.names:
            resp = await self._request(
                "GET", TENANTS_ENDPOINT, params={"name": name, "limit": 200}
            )
            ids.update(r["id"] for r in resp.json().get("results", []))
        for group in self.tenant_scope.groups:
            resp = await self._request(
                "GET",
                TENANTS_ENDPOINT,
                params={"tenant_group": group, "limit": 200},
            )
            ids.update(r["id"] for r in resp.json().get("results", []))

        if not ids:
            raise PermissionError(
                "Configured tenant scope resolved to zero tenants "
                f"(tenant_scope={list(self.tenant_scope.names)}, "
                f"tenant_group_scope={list(self.tenant_scope.groups)}). "
                "Check the names against Nautobot."
            )
        resolved = frozenset(ids)
        self.tenant_scope.set_resolved(resolved)
        return resolved

    async def _scoped_params(
        self, endpoint: str, params: dict[str, Any] | None
    ) -> dict[str, Any] | None:
        """Inject the tenant constraint into list params, if in scope."""
        ids = await self._resolve_tenant_ids()
        if ids is None:
            return params
        param = tenant_filter_param(endpoint)
        if param is None:
            return params
        scoped = dict(params or {})
        # Drop any caller-supplied tenant filter so it can't widen scope.
        scoped.pop("tenant", None)
        scoped.pop("tenant_id", None)
        scoped[param] = sorted(ids)
        return scoped

    async def _assert_object_in_scope(
        self, endpoint: str, obj: dict[str, Any]
    ) -> None:
        """Raise ``PermissionError`` if ``obj`` is outside the tenant scope."""
        ids = await self._resolve_tenant_ids()
        if ids is None or tenant_filter_param(endpoint) is None:
            return
        tid = tenant_id_of(endpoint, obj)
        if tid not in ids:
            raise PermissionError(
                f"Object {obj.get('id')!r} at {endpoint} belongs to tenant "
                f"{tid!r}, which is outside the configured tenant scope."
            )

    async def _enforce_create_tenant(
        self, endpoint: str, data: Any
    ) -> Any:
        """Validate/inject the tenant on a create payload under scope."""
        ids = await self._resolve_tenant_ids()
        if ids is None or tenant_filter_param(endpoint) is None:
            return data
        if endpoint == TENANTS_ENDPOINT:
            # Creating tenants themselves is not constrained by scope here.
            return data
        payload = dict(data or {})
        tenant_val = payload.get("tenant")
        if tenant_val in (None, ""):
            if len(ids) == 1:
                payload["tenant"] = next(iter(ids))
                return payload
            raise PermissionError(
                "Refusing to create an object without a tenant: the "
                "configured scope contains multiple tenants, so the target "
                "tenant cannot be inferred. Set 'tenant' explicitly."
            )
        await self._assert_tenant_value_in_scope(tenant_val)
        return payload

    async def _assert_tenant_value_in_scope(self, tenant_val: Any) -> None:
        """Resolve a tenant value (UUID, name, or dict) and check scope."""
        ids = await self._resolve_tenant_ids()
        if ids is None:
            return
        if isinstance(tenant_val, dict):
            tenant_val = tenant_val.get("id") or tenant_val.get("name")
        tenant_val = str(tenant_val)
        if tenant_val in ids:
            return
        # Treat as a name/slug and resolve to an id.
        resp = await self._request(
            "GET", TENANTS_ENDPOINT, params={"name": tenant_val, "limit": 2}
        )
        results = resp.json().get("results", [])
        resolved = {r["id"] for r in results}
        if not resolved or not (resolved & ids):
            raise PermissionError(
                f"Tenant {tenant_val!r} is outside the configured tenant scope."
            )

    async def _request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any = None,
        max_retries: int = 3,
    ) -> httpx.Response:
        method = method.upper()

        # Validate endpoint shape only for relative paths; absolute URLs
        # (used to follow Nautobot's pagination ``next`` links) are
        # already-trusted, since they come from prior responses.
        if not url.startswith("http"):
            self._check_write_allowed(method, url)

        last_exc: Exception | None = None
        for attempt in range(1, max_retries + 1):
            try:
                request_kwargs: dict[str, Any] = {"params": params}
                if json is not None:
                    request_kwargs["json"] = json
                response = await self._client.request(method, url, **request_kwargs)
            except (httpx.TransportError, httpx.TimeoutException) as exc:
                last_exc = exc
                if attempt == max_retries:
                    logger.error(
                        "Nautobot transport error on %s %s after %d attempts: %s",
                        method,
                        url,
                        attempt,
                        exc,
                    )
                    raise
                wait = 0.5 * (2 ** (attempt - 1))
                logger.warning(
                    "Nautobot transport error on %s %s (attempt %d/%d): %s; "
                    "retrying in %.1fs",
                    method,
                    url,
                    attempt,
                    max_retries,
                    exc,
                    wait,
                )
                await asyncio.sleep(wait)
                continue

            if 500 <= response.status_code < 600 and attempt < max_retries:
                wait = 0.5 * (2 ** (attempt - 1))
                logger.warning(
                    "Nautobot %s %s returned %s (attempt %d/%d); retrying in %.1fs",
                    method,
                    url,
                    response.status_code,
                    attempt,
                    max_retries,
                    wait,
                )
                await asyncio.sleep(wait)
                continue

            response.raise_for_status()
            return response

        raise last_exc or RuntimeError("Request failed without exception")

    # ---- REST ----------------------------------------------------------

    async def rest_get(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> Any:
        """GET an arbitrary Nautobot REST endpoint (returns one page)."""
        ep = self._normalize_endpoint(endpoint)
        resp = await self._request("GET", ep, params=params)
        return resp.json()

    async def rest_get_object(self, endpoint: str, object_id: str) -> Any:
        """GET a single object: ``<endpoint>{object_id}/``."""
        ep = self._normalize_endpoint(endpoint)
        resp = await self._request("GET", f"{ep}{object_id}/")
        obj = resp.json()
        await self._assert_object_in_scope(ep, obj)
        return obj

    async def rest_list(
        self,
        endpoint: str,
        filters: dict[str, Any] | None = None,
        *,
        limit: int = 50,
        offset: int = 0,
        paginate: bool = False,
        max_records: int | None = None,
    ) -> list[Any] | dict[str, Any]:
        """List objects with optional filters and auto-pagination.

        When ``paginate`` is ``True``, walks the ``next`` URLs until
        either exhausted or ``max_records`` (or
        ``settings.max_pagination_records``) is reached and returns a
        flat list of records.

        When ``paginate`` is ``False`` (default), returns the raw page
        envelope ``{count, next, previous, results}``.
        """
        ep = self._normalize_endpoint(endpoint)
        params: dict[str, Any] = {}
        if filters:
            params.update({k: v for k, v in filters.items() if v is not None})
        params.setdefault("limit", limit)
        params.setdefault("offset", offset)
        params = await self._scoped_params(ep, params) or {}

        if not paginate:
            return await self.rest_get(ep, params=params)

        cap = max_records if max_records is not None else self.settings.max_pagination_records
        params["limit"] = min(int(params.get("limit") or 200), 200)

        results: list[Any] = []
        next_url: str | None = ep
        page_params: dict[str, Any] | None = params

        while next_url and len(results) < cap:
            resp = await self._request("GET", next_url, params=page_params)
            data = resp.json()
            page_params = None  # only the first request carries params

            if isinstance(data, dict) and "results" in data:
                results.extend(data.get("results") or [])
                next_url = data.get("next")
            elif isinstance(data, list):
                results.extend(data)
                break
            else:
                results.append(data)
                break

        return results[:cap]

    async def rest_create(self, endpoint: str, data: Any) -> Any:
        ep = self._normalize_endpoint(endpoint)
        data = await self._enforce_create_tenant(ep, data)
        resp = await self._request("POST", ep, json=data)
        return resp.json() if resp.content else {}

    async def rest_update(
        self,
        endpoint: str,
        object_id: str,
        data: Any,
        *,
        partial: bool = True,
    ) -> Any:
        ep = self._normalize_endpoint(endpoint)
        if self.tenant_scope.active and tenant_filter_param(ep) is not None:
            # Verify the existing object is in scope before mutating it,
            # and that any tenant reassignment stays within scope.
            await self.rest_get_object(ep, object_id)
            if data and "tenant" in data and ep != TENANTS_ENDPOINT:
                await self._assert_tenant_value_in_scope(data["tenant"])
        method = "PATCH" if partial else "PUT"
        resp = await self._request(method, f"{ep}{object_id}/", json=data)
        return resp.json() if resp.content else {}

    async def rest_delete(self, endpoint: str, object_id: str) -> dict[str, Any]:
        ep = self._normalize_endpoint(endpoint)
        if self.tenant_scope.active and tenant_filter_param(ep) is not None:
            await self.rest_get_object(ep, object_id)  # raises if out of scope
        await self._request("DELETE", f"{ep}{object_id}/")
        return {"deleted": True, "endpoint": ep, "id": object_id}

    # ---- GraphQL -------------------------------------------------------

    async def graphql_query(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables
        resp = await self._request("POST", "/api/graphql/", json=payload)
        return resp.json()

    async def graphql_introspect(self) -> dict[str, Any]:
        """Run a small GraphQL introspection query."""
        query = (
            "query { __schema { "
            "queryType { name } "
            "mutationType { name } "
            "types { name kind description } "
            "} }"
        )
        return await self.graphql_query(query)

    # ---- meta ----------------------------------------------------------

    async def list_api_roots(self) -> dict[str, Any]:
        """Return Nautobot's API root document for endpoint discovery."""
        return await self.rest_get("/api/")

    async def status(self) -> dict[str, Any]:
        """Return Nautobot's status endpoint (version, plugins, db, etc.)."""
        return await self.rest_get("/api/status/")
