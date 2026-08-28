# Changelog

All notable changes to OverheatLens are documented here.
Format based on Keep a Changelog; versioning is SemVer.

## [0.1.0-dev] — 2026-08-28

### Added
- Monorepo skeleton per governing plan (`docs/specs/`): `packages/overheatlens-core`,
  `apps/{web,api,worker}` placeholders for later phases, `fixtures/`, `examples/`, `docs/`.
- Governance documents: SOURCE_REGISTER, ARCHITECTURE_DECISIONS, VALIDATION_MATRIX,
  IMPLEMENTATION_STATUS, DISCLAIMER, SECURITY, GOVERNANCE, CONTRIBUTING, CODE_OF_CONDUCT.
- Zero-install double-click launchers (Start / Run Tests / Close; macOS + Windows) mirroring
  the epw_doctor experience.
- `overheatlens-core` v0.1.0-dev:
  - EPW parser, validation checks and headline metrics with synthetic fixtures;
  - versioned rule packs (YAML) + JSON Schema validation:
    `uk_tm59_2017`, `uk_part_o_dynamic` (ADO-verified overrides), `uk_tm52` (gated scaffold),
    `uk_tm59_2026` (**blocked** — source not acquired; no criteria values invented);
  - standards engine with evaluation gate refusing unverified packs in compliance mode;
  - provenance hashing + run manifests; CLI (`version`, `rule-packs`, `check-epw`);
  - property-based metamorphic tests (hypothesis).
- Phase 0 verification: Approved Document O 2021 (England) downloaded from gov.uk and
  machine-verified; TM59:2017 anchor confirmed; negative finding on weather files recorded.

### Security
- Copyright firewall in `.gitignore`: real CIBSE/Met Office weather files and licensed
  standards PDFs can never be committed.
