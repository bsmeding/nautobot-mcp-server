"""No Jobs of our own. Nautobot still imports this module.

Add a Job class here later and put it in `jobs` if we need one.
"""

from __future__ import annotations

from nautobot.apps.jobs import register_jobs

jobs: list = []

if jobs:
    register_jobs(*jobs)
