# Security policy

## Reporting a vulnerability

Please **do not open a public issue** for security problems. Use GitHub's
[private vulnerability reporting](https://github.com/bishal-saha/agent-doorway/security/advisories/new)
for this repository. You will get an acknowledgement within 5 working days.

## Supported versions

Agent Doorway is a reference implementation under active development. Only the latest commit on
`main` receives fixes.

## Supply-chain measures

- GitHub Actions pinned to full commit SHAs; workflows default to `permissions: contents: read`.
- Dependencies locked in `uv.lock` with hashes; CI installs with `--frozen`.
- `pip-audit` checks the locked dependencies for known vulnerabilities on every push.
- A CycloneDX SBOM is generated on every push (CI artifact `sbom`).
- `gitleaks` scans the full git history for committed secrets.
- Dependabot proposes weekly updates for Python packages, Actions and Docker images.
- The container runs as a non-root user.
