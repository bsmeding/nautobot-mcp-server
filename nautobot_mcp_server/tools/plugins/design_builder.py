"""Tools for the Nautobot Design Builder app (``nautobot-design-builder``).

Design Builder lets you define declarative "designs" and deploy them as
Nautobot Jobs, tracking each deployment so it can be updated or rolled
back. These tools expose its REST models when present and provide
job-centric helpers for running designs.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ._common import list_jobs_matching, plugin_rest_list, run_job_by_name_or_id

KEY = "design_builder"
DIST_PACKAGES: tuple[str, ...] = ("nautobot_design_builder",)
APP_URL = "design-builder"


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_designs(paginate: bool = True) -> Any:
        """List Design Builder designs (``/api/plugins/design-builder/designs/``)."""
        return await plugin_rest_list(APP_URL, "designs", paginate=paginate)

    @mcp.tool()
    async def list_design_deployments(
        filters: dict[str, Any] | None = None,
        paginate: bool = True,
    ) -> Any:
        """List design deployments (instances). Filter by ``design``, ``status``.

        Endpoint: ``/api/plugins/design-builder/deployments/``.
        """
        return await plugin_rest_list(
            APP_URL, "deployments", filters=filters, paginate=paginate
        )

    @mcp.tool()
    async def list_design_jobs() -> Any:
        """List installed Design Builder jobs (the runnable designs)."""
        return await list_jobs_matching("design")

    @mcp.tool()
    async def run_design(
        job_name_or_id: str,
        data: dict[str, Any] | None = None,
        commit: bool = True,
    ) -> dict[str, Any]:
        """Run a Design Builder design job and return the job result.

        Args:
            job_name_or_id: The design job's UUID or class-path name.
            data: Design input variables.
            commit: Whether to commit the design (set False for a dry-run
                where the design supports it).
        """
        return await run_job_by_name_or_id(job_name_or_id, data, commit=commit)
