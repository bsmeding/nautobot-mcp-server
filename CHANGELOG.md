# Changelog

All notable changes to **nautobot-mcp** are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.6] - 24-11-2026

### Added
- `plugins=auto` reads `GET /api/status/` and enables Design Builder, Onboarding, SSoT, Golden Config, and Nornir when `nautobot-apps` lists them
- Local package detection still applies. An explicit list or `all` still forces those tools on
- Status page under **Apps → Installed Apps** and **Apps → MCP Server → MCP Server Status**
- Log tail on that page when `log_file` / `NAUTOBOT_MCP_LOG_FILE` is set
- Shared HTTP servers can require each client to send its own token (`X-Nautobot-Token`, or `Authorization: Token`). Set `NAUTOBOT_MCP_REQUIRE_CLIENT_TOKEN=true`. A missing token is refused

### Changed
- A standalone Claude or Cursor process no longer needs `NAUTOBOT_MCP_PLUGINS` for those apps

## [0.2.5] - 2026-10-31

### Added
- `streamable-http` and `sse` accept `--host` / `--port`, or `NAUTOBOT_MCP_HOST` / `NAUTOBOT_MCP_PORT` (default `127.0.0.1:8000`)

### Changed
- PyPI homepage points at the docs on [netdevops.it](https://netdevops.it/projects/nautobot-mcp/user-guide/)

## [0.2.4] - 2026-10-26

### Changed
- Console script is `nautobot-mcp`, so `uvx nautobot-mcp` starts the server
- The `nautobot-mcp-server` script from earlier releases is no longer installed

## [0.2.3] - 2026-10-22

### Changed
- Python package and Nautobot plugin renamed from `nautobot_mcp_server` to `nautobot_mcp`
- Use `PLUGINS = ["nautobot_mcp"]` and `PLUGINS_CONFIG["nautobot_mcp"]`
- The `nautobot-mcp-server` console script is unchanged in this release

## [0.2.2] - 2026-09-15

### Changed
- Published on PyPI as `nautobot-mcp`
- Server moved from mcp 1.x `FastMCP` to mcp 2.x `MCPServer`

### Fixed
- Lockfile refresh onto patched GitPython, sqlparse, Django REST framework, and cryptography
- Paramiko stays on 4.x (Netmiko is not compatible with Paramiko 5)

## [0.2.1] - 2026-07-27

### Changed
- MCP-specific env vars use the `NAUTOBOT_MCP_` prefix (`NAUTOBOT_MCP_ALLOW_WRITES`, `NAUTOBOT_MCP_TENANT_SCOPE`, …)
- `NAUTOBOT_URL` / `NAUTOBOT_TOKEN` are unchanged. Old unprefixed names still work as aliases

## [0.2.0] - 2026-06-10

### Added
- Tenant scoping for MSP / multi-tenant isolation (`tenant_scope`, `tenant_group_scope`) on read and write tools
- Optional plugin integrations with pip extras and the `plugins` setting: Design Builder, Device Onboarding, SSoT, Golden Config, and Nornir
- Golden Config `compliance_summary` helper
- Nautobot app scaffolding: status view, navigation, development environment, `tasks.py`, and documentation
- PyPI release workflow via Trusted Publishing (OIDC)

## [0.1.0] - 2026-06-10

### Added
- Initial release: core REST/GraphQL tools for DCIM, IPAM, circuits, tenancy, virtualization, extras/jobs, generic passthrough, and cross-domain search

[Unreleased]: https://github.com/bsmeding/nautobot-app-mcp-server/compare/v0.2.5...HEAD
[0.2.5]: https://github.com/bsmeding/nautobot-app-mcp-server/releases/tag/v0.2.5
[0.2.4]: https://github.com/bsmeding/nautobot-app-mcp-server/releases/tag/v0.2.4
[0.2.3]: https://github.com/bsmeding/nautobot-app-mcp-server/releases/tag/v0.2.3
[0.2.2]: https://github.com/bsmeding/nautobot-app-mcp-server/releases/tag/v0.2.2
[0.2.1]: https://github.com/bsmeding/nautobot-app-mcp-server/releases/tag/v0.2.1
[0.2.0]: https://github.com/bsmeding/nautobot-app-mcp-server/releases/tag/v0.2.0
[0.1.0]: https://github.com/bsmeding/nautobot-app-mcp-server/commit/e6d315d
