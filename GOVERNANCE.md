# Governance

**Project:** OverheatLens — Open Building Overheating & Climate-Resilience Hub
**Lead / maintainer:** Mohamed Hamdy Ali (Leeds Beckett University)

## Roles

- **Benevolent Dictator for Life (BDFL):** the maintainer has final say on scope, scientific
  standards and releases, and is expected to act in the project's best interest and document
  significant decisions in `ARCHITECTURE_DECISIONS.md`.
- **Contributors:** anyone submitting issues, documentation, code or validation evidence.
- **Scientific reviewers:** domain experts invited to review rule transcriptions and validation
  evidence before a `1.0` release (governing plan §27.1 Tier 6).

## Decision making

- Engineering decisions: normal pull-request review.
- Scientific decisions (thresholds, methods, versions): require a `SOURCE_REGISTER.md` entry and
  an architecture decision record; the BDFL approves.
- Releases: tagged, archived (Zenodo DOI planned for v1.0), changelog entry mandatory.

## Scientific-integrity commitments

- No failing validation test may be deleted or weakened without a documented scientific reason.
- Sources not yet verified are labelled as such everywhere they appear, including in the UI.
- The project never presents research output as statutory compliance.

## Licensing of contributed content

Code and rule packs: MIT. Contributions must not embed copyrighted standards text or licensed
weather data; cite sources instead.
