# IMPLEMENTATION STATUS

Last updated: **2026-08-28** (initial session)

Overall stage: **Phase 0–1 complete; Phase 2 (EPW engine) in progress.**
Governing specs: `docs/specs/` · Sources: `SOURCE_REGISTER.md` · Decisions: `ARCHITECTURE_DECISIONS.md` · Validation: `VALIDATION_MATRIX.md`

## Phase tracker

| Phase | Scope | Status | Notes |
|---|---|---|---|
| 0 — Freeze standards & sources | source register, rule-pack schema, transcription | **COMPLETE (with open items)** | ADO 2021 machine-verified from official PDF; TM59:2017/TM52 secondary-pending; TM59:2026 blocked (ADR-0005). Open: acquire CIBSE originals |
| 1 — Core package skeleton | package, provenance, schemas, CLI, CI, tests | **COMPLETE** | 0.x version; pytest harness green locally |
| 2 — EPW engine | parser, checker, metrics, multi-EPW, tests | **IN PROGRESS** | parser + validation + headline metrics done; compare/UHI pending |
| 3 — Standards engine | TM59:2017/2026, Part O, TM52, diff | PARTIAL (engine + TM59:2017 criteria in place) | TM59:2026 blocked by source gate |
| 4 — Comfort engine | wrappers, applicability, PMV/PPD, UTCI | PENDING | pythermalcomfort 4.4.2 installed, unwrapped |
| 5 — IDF readiness | generic + standards-specific checks, passport | PENDING | |
| 6 — EnergyPlus worker | run, isolation, harvest, manifest | PENDING | official 25.1.0 verified installed (ADR-0004) |
| 7 — API | FastAPI service | PENDING | |
| 8 — Design system & frontend | tokens, nav, chart primitives | PENDING | Node 24 + npm 11 available on machine |
| 9–17 | Weather Lab … publication release | PENDING | |

## What exists now (built this session)

- Monorepo skeleton + governance docs (README, LICENSE, CHANGELOG, CITATION.cff, codemeta.json, community files, DISCLAIMER, SECURITY, GOVERNANCE)
- Zero-install launchers (`Start/Close/Run Tests`, macOS `.command` + Windows `.bat`) — Start prints an honest terminal self-check; web app arrives with Phase 7/8
- `packages/overheatlens-core` v0.1.0.dev0:
  - EPW parser (official 35-column layout, hour-ending validation, SHA-256 provenance)
  - QC checker with calibrated thresholds (range, sentinel, dew-point physics, discontinuity ≤8/15 K/h warning/error, stuck-sensor ≥10 h, timestamp continuity, duplicates) + PASS / PASS_WITH_WARNINGS / FAIL classification
  - headline weather metrics (summary, monthly stats, exceedance hours, degree hours)
  - versioned rule packs (YAML) + JSON Schema validation with a purpose-built zero-dependency validator
  - standards engine: TM59:2017 criteria A/B/C with exact boundaries, sleep-window geometry, room classification, dwelling trichotomy (PASS/FAIL/INCOMPLETE), NOT_EVALUATED honesty, and the source-verification gate (compliance mode refuses unverified packs; blocked packs refuse everything)
  - provenance hashing + run manifests; CLI (`version`, `rule-packs`, `check-epw`, `passport`) via `overheatlens` script or `python -m overheatlens`
- Rule packs: `uk_tm59_2017` (secondary-pending values, gated), `uk_part_o_dynamic` (ADO-verified limits PO-WIN-01..04 + exclusions PO-EXC-01..02, criteria inherited), `uk_tm52` (honest scaffold), `uk_tm59_2026` (blocked — no invented values)
- GitHub Actions CI (`.github/workflows/core-tests.yml`): Python 3.11 + 3.12 matrix, pytest with coverage, rule-pack validation

## Validation evidence this session

**65 tests passed, 0 skipped, 0 failed** (local run 2026-08-28;
`PYTHONPATH=packages/overheatlens-core python -m pytest packages/overheatlens-core/tests -q`).
Coverage 85% total; standards engine 96%, EPW validation 93%.
Row-by-row evidence in `VALIDATION_MATRIX.md`; session report in `docs/validation/SESSION_2026-08-28.md`.
Notable: the boundary tests caught a sleep-window off-by-one during development (VAL-STD-07) —
fixed before any result was ever produced.

## Honest gaps / open blockers

1. **CIBSE originals not acquired** (TM59:2017, TM59:2026, TM52, weather guidance). Until then
   those packs cannot produce compliance-labelled results (enforced in code).
2. Web search quota resets 2026-08-30 → capture CIBSE TM59:2026 public statements (SOURCE_REGISTER S-05).
3. EnergyPlus 26.1.0 pin decision deferred (ADR-0004) — working pin 25.1.0, machine-verified.
4. No UI yet (Phase 8+) — launchers expose the CLI honestly rather than a placeholder UI.
