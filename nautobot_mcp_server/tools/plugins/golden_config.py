"""Tools for the Nautobot Golden Config app (``nautobot-golden-config``).

Golden Config provides configuration backups, intended-config generation,
and compliance checking, all driven by Nautobot Jobs and exposed via REST
models under ``/api/plugins/golden-config/``.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from .._helpers import client
from ._common import list_jobs_matching, plugin_rest_list, run_job_by_name_or_id

KEY = "golden_config"
DIST_PACKAGES: tuple[str, ...] = ("nautobot_golden_config",)
APP_URL = "golden-config"


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_config_compliance(
        filters: dict[str, Any] | None = None,
        paginate: bool = False,
    ) -> Any:
        """List per-device/feature compliance results.

        Endpoint: ``/api/plugins/golden-config/config-compliance/``.
        Filter by ``device``, ``rule``, ``compliance`` (bool), etc.
        """
        return await plugin_rest_list(
            APP_URL, "config-compliance", filters=filters, paginate=paginate
        )

    @mcp.tool()
    async def list_compliance_rules(
        filters: dict[str, Any] | None = None,
        paginate: bool = True,
    ) -> Any:
        """List compliance rules. Endpoint: ``.../compliance-rule/``."""
        return await plugin_rest_list(
            APP_URL, "compliance-rule", filters=filters, paginate=paginate
        )

    @mcp.tool()
    async def list_compliance_features(paginate: bool = True) -> Any:
        """List compliance features. Endpoint: ``.../compliance-feature/``."""
        return await plugin_rest_list(
            APP_URL, "compliance-feature", paginate=paginate
        )

    @mcp.tool()
    async def list_golden_config(
        filters: dict[str, Any] | None = None,
        paginate: bool = False,
    ) -> Any:
        """List Golden Config status rows (backup/intended/compliance times).

        Endpoint: ``/api/plugins/golden-config/golden-config/``. Filter by
        ``device``.
        """
        return await plugin_rest_list(
            APP_URL, "golden-config", filters=filters, paginate=paginate
        )

    @mcp.tool()
    async def list_golden_config_settings(paginate: bool = True) -> Any:
        """List Golden Config settings. Endpoint: ``.../golden-config-settings/``."""
        return await plugin_rest_list(
            APP_URL, "golden-config-settings", paginate=paginate
        )

    @mcp.tool()
    async def get_intended_config(device_id: str) -> Any:
        """Return the post-processed intended config for a device.

        Endpoint: ``/api/plugins/golden-config/config-postprocessing/{device_id}/``.
        """
        return await client().rest_get(
            f"/api/plugins/{APP_URL}/config-postprocessing/{device_id}/"
        )

    @mcp.tool()
    async def compliance_summary(
        device: str | None = None,
        location: str | None = None,
    ) -> dict[str, Any]:
        """Summarize config compliance into compliant/non-compliant counts.

        Aggregates ``/api/plugins/golden-config/config-compliance/`` rows
        (each row is one device+feature result) into an overall tally plus a
        per-device breakdown, and lists the non-compliant (device, feature)
        pairs so an agent can act on them.

        Args:
            device: Optional device UUID/name to scope the summary to.
            location: Optional location UUID/name to scope the summary to.
        """
        filters: dict[str, Any] = {}
        if device:
            filters["device"] = device
        if location:
            filters["device__location"] = location
        rows = await plugin_rest_list(
            APP_URL, "config-compliance", filters=filters, paginate=True
        )
        if isinstance(rows, dict):  # safety: unpaginated envelope
            rows = rows.get("results", [])

        per_device: dict[str, dict[str, Any]] = {}
        non_compliant: list[dict[str, Any]] = []
        compliant_count = 0

        for row in rows:
            dev = row.get("device") or {}
            dev_name = (
                dev.get("name") if isinstance(dev, dict) else str(dev)
            ) or "<unknown>"
            rule = row.get("rule") or {}
            feature = rule.get("feature") if isinstance(rule, dict) else None
            if isinstance(feature, dict):
                feature = feature.get("name")
            feature = feature or (
                rule.get("name") if isinstance(rule, dict) else None
            )
            is_ok = bool(row.get("compliance"))

            bucket = per_device.setdefault(
                dev_name, {"compliant": 0, "non_compliant": 0}
            )
            if is_ok:
                compliant_count += 1
                bucket["compliant"] += 1
            else:
                bucket["non_compliant"] += 1
                non_compliant.append({"device": dev_name, "feature": feature})

        total = len(rows)
        return {
            "total_results": total,
            "compliant": compliant_count,
            "non_compliant": total - compliant_count,
            "compliance_rate": round(compliant_count / total, 4) if total else None,
            "devices": per_device,
            "non_compliant_items": non_compliant,
        }

    @mcp.tool()
    async def list_golden_config_jobs() -> Any:
        """List Golden Config jobs (backup, intended, compliance, all-in-one)."""
        return await list_jobs_matching("golden")

    @mcp.tool()
    async def run_golden_config_job(
        job_name_or_id: str,
        data: dict[str, Any] | None = None,
        commit: bool = True,
    ) -> dict[str, Any]:
        """Run a Golden Config job (e.g. backup, intended, or compliance).

        Args:
            job_name_or_id: Job UUID or class-path name (use
                ``list_golden_config_jobs`` to discover it).
            data: Job inputs -- typically a device/location filter such as
                ``{"device": "<uuid>"}`` or ``{"location": "<uuid>"}``.
            commit: Whether the job should commit its changes.
        """
        return await run_job_by_name_or_id(job_name_or_id, data, commit=commit)
