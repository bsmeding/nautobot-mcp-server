# This project has moved to `nautobot-mcp`

`nautobot-mcp-server` was renamed on PyPI. Install the new project:

```bash
pip install nautobot-mcp
```

This release stays on PyPI so existing installs keep working. It depends on
`nautobot-mcp`, including the same extras (`nautobot`, `design-builder`,
`onboarding`, `ssot`, `golden-config`, `nornir`, `all`).

Importing `nautobot_mcp_server` raises a `DeprecationWarning`. The app lives
in `nautobot_mcp`.

What stays the same:

- The console script is still `nautobot-mcp-server`.
- In Nautobot, set `PLUGINS = ["nautobot_mcp"]`.

New releases are published only as
[nautobot-mcp](https://pypi.org/project/nautobot-mcp/).
