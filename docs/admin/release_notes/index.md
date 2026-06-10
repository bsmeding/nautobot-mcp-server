# Release Notes

## v0.2.0

- Tenant scoping for MSP / multi-tenant isolation (`tenant_scope`,
  `tenant_group_scope`) enforced centrally across read and write tools.
- Optional plugin integrations with pip extras and the `plugins` setting:
  Design Builder, Device Onboarding, SSoT, Golden Config, and Nornir.
- Golden Config `compliance_summary` helper.
- Nautobot app scaffolding: status view, navigation, development environment,
  `tasks.py`, and documentation.
- PyPI release workflow via Trusted Publishing (OIDC).

## v0.1.0

- Initial release: core REST/GraphQL tools for DCIM, IPAM, circuits, tenancy,
  virtualization, extras/jobs, generic passthrough, and cross-domain search.
