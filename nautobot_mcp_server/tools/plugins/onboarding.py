"""Tools for the Nautobot Device Onboarding app
(``nautobot-device-onboarding``).

Device Onboarding discovers a device over the network (SSH/NAPALM or the
newer SSoT-based sync) and creates/updates it in Nautobot. It is driven by
Jobs, so these tools are job-centric.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ._common import list_jobs_matching, run_job_by_name_or_id

KEY = "onboarding"
DIST_PACKAGES: tuple[str, ...] = ("nautobot_device_onboarding",)


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_onboarding_jobs() -> Any:
        """List installed device-onboarding jobs."""
        return await list_jobs_matching("onboard")

    @mcp.tool()
    async def onboard_device(
        job_name_or_id: str,
        data: dict[str, Any],
        commit: bool = True,
    ) -> dict[str, Any]:
        """Run an onboarding job to discover and import a device.

        Args:
            job_name_or_id: Onboarding job UUID or class-path name (use
                ``list_onboarding_jobs`` to discover it).
            data: Job inputs. For the classic onboarding job this typically
                includes ``location``, ``ip_address``, ``credentials`` /
                ``secrets_group``, ``platform``, and ``port``. For the
                SSoT-based "Sync Devices From Network" job the inputs differ
                -- inspect the job via ``get_job`` first.
            commit: Whether the job should commit its changes.
        """
        return await run_job_by_name_or_id(job_name_or_id, data, commit=commit)
