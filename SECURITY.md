# Security Policy

## Reporting a Vulnerability

Please do not open a public GitHub issue for security-sensitive bugs.

Report vulnerabilities privately to `ochre.neutron-2i@icloud.com` with:

- a short description of the issue and affected area
- reproduction steps or a proof of concept
- expected impact
- any relevant environment details

Reports are handled on a best-effort basis. Please allow time to investigate and prepare a fix before disclosing details publicly.

## Supported Versions

Security fixes are provided on a best-effort basis for:

- the latest tagged release
- the current `main` branch

Older releases may not receive security updates.

## Scope Notes

Security-relevant areas for this project include:

- the optional web UI, especially when exposed beyond a trusted LAN
- configuration and credential handling
- integrations that use API keys, service-account credentials, or private ICS URLs

For operator hardening guidance, see [docs/web-ui.md](docs/web-ui.md).
