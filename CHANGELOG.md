# Changelog

All notable changes to OverheatLens are documented here.
Format based on Keep a Changelog; versioning is SemVer.

## [0.2.0.dev0] — 2026-08-28 (session 2: TM59:2026 unblocked)

### Added
- **TM59:2026 fully implemented from the official source** (author-supplied CIBSE PDF,
  machine-verified, SHA-256 recorded): rule pack `uk_tm59_2026` v1.0.0 with criteria a–d,
  Stage 1/2/3 strategy, dwelling Categories I/II, adaptive thresholds with the TM52
  running-mean chain, ceiling-fan uplifts, and the nights-based bedroom criterion —
  every value boundary-locked by tests (`VAL-TM26-01..12`).
- Weather-file compatibility guard against the officially verified TM59:2026 minimum
  (`{Zone}_DSY1_2050s_HIGH50_CIBSE_v1.1`) with compatible / research_only / unknown
  verdicts (`VAL-WCG-01..03`).
- Real-world EPW robustness: 32-field truncated CIBSE layout support (+ synthetic fixture),
  empty-cell tolerance with explicit MISSING_VALUES reporting, and an all-missing-series
  explicit non-result (`V-EPW-14..16`).
- `docs/standards/TM59_2026_VERIFICATION.md`: verbatim evidence for every transcribed value.

### Changed
- `uk_tm59_2026`: `blocked_no_source` → `source_verified` (the blocked scaffold was
  replaced wholesale — no interpolated values ever existed).
- Rule-pack schema extended (adaptive thresholds, nights aggregation, occupied-hour
  limits, per-space-type variants, stages, ceiling-fan uplift); mini-validator gained
  local `$ref` support.
- Standards engine: per-space-type criterion variants, dwelling category parameter,
  explicit NOT_EVALUATED results for criteria whose inputs are absent.

### Verified locally (never committed)
- Real CIBSE `Leeds_DSY1.epw` parses PASS (32-field variant); `leeds_2050.epw`
  PASS_WITH_WARNINGS; two template EPWs correctly FAIL on the 99.9 temperature sentinel
  convention (`VAL-REAL-01..03`).

## [0.1.0.dev0] — 2026-08-28 (session 1)

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
