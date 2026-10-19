# Security Policy

> Primary source: [ClientRequirement.md](ClientRequirement.md) · Posture details: [SECURITY_ACCESSIBILITY.md](SECURITY_ACCESSIBILITY.md)

## Status

LabelForge is a **prototype / proof-of-concept** built for a technical interview take-home. It is **not** authorized for production or for processing sensitive data (see [PRD.md](PRD.md) §5.2).

## Supported versions

| Version | Supported |
|---------|-----------|
| `main` (latest) | ✅ current prototype |
| older commits | ❌ no back-porting |

## Reporting a vulnerability

Please report security issues **privately** — open a GitHub Security Advisory on this repository, or contact the author directly via the email on the [GitHub profile](https://github.com/monigarr). Do **not** file a public issue for exploitable vulnerabilities.

- **Response target:** best effort within 5 business days (prototype cadence).
- **Scope:** the `app/` API, UI, Streamlit entrypoint, pipeline, and CI configuration in this repository.

## Known posture (summary)

- No authentication on the public demo; no sensitive data processed; all fixtures are synthetic.
- Full posture, known gaps, and the production-hardening backlog are documented in [SECURITY_ACCESSIBILITY.md](SECURITY_ACCESSIBILITY.md).
- Secrets must never be committed; `.env` is git-ignored and CI runs a secret scan (`gitleaks`).

## Dependency policy

- Dependabot monitors Python (`pip`), npm, and GitHub Actions; security updates are expected to land within 7 days.
- Security-relevant upgrades and deferred majors are tracked in [APPROACH.md](APPROACH.md) (upgrade register).
