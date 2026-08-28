# Security Policy

## Supported versions

OverheatLens is in early development (`0.x`). Only the latest `main` branch receives fixes.

## Reporting a vulnerability

Please report vulnerabilities privately via GitHub "Report a vulnerability"
(Security advisories on the repository) rather than a public issue. You should receive a
response within 14 days.

## Security posture (current and planned)

Current:
- No server component runs yet; the tool is local-first.
- No telemetry, no accounts, no analytics.

Enforced from the start:
- Real weather files and licensed standards PDFs are never committed.
- Upload handling (when the API exists) will follow the governing plan §26: size limits,
  content checks, safe paths, random job dirs, no shell interpolation, timeouts, strict CORS,
  CSP, short retention with default deletion.

## Known limitations

- The EnergyPlus runner will execute user-supplied input files by design (that is the product);
  isolation hardening is specified for Phase 6 and must land before any hosted deployment.
