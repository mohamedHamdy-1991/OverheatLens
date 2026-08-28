# IMPLEMENTATION STATUS

Last updated: **2026-08-28** (session 2 — TM59:2026 unblocked and implemented)

Overall stage: **Phases 0–1 complete; Phase 2 (EPW engine) substantially complete; Phase 3 (standards engine) substantially complete — TM59:2026 fully implemented from the source-verified document.**
Governing specs: `docs/specs/` · Sources: `SOURCE_REGISTER.md` · Decisions: `ARCHITECTURE_DECISIONS.md` · Validation: `VALIDATION_MATRIX.md`

## Phase tracker

| Phase | Scope | Status | Notes |
|---|---|---|---|
| 0 — Freeze standards & sources | source register, rule-pack schema, transcription | **COMPLETE for TM59:2026 + ADO**; TM59:2017/TM52 still pending (PDFs not found on machine — `~/PhD/Literature_Review/Papers` is empty) | ADO 2021 + TM59:2026 methodology + weather requirements all machine-verified with SHA-256 |
| 1 — Core package skeleton | package, provenance, schemas, CLI, CI, tests | **COMPLETE** | |
| 2 — EPW engine | parser, checker, metrics, multi-EPW, tests | **SUBSTANTIALLY COMPLETE** | parser (incl. real-world 32-field CIBSE variant + empty-cell tolerance), calibrated QC, metrics, compatibility guard vs the official TM59:2026 weather requirement; multi-EPW compare/UHI pending (Phase 9) |
| 3 — Standards engine | TM59:2026, TM59:2017, Part O, TM52, diff | **TM59:2026 COMPLETE** (criteria a–d, stages, categories, adaptive Trm, boundary-locked); TM59:2017 + Part O implemented but compliance-gated pending S-02; TM52 scaffold; standards diff viewer pending | |
| 4 — Comfort engine | wrappers, applicability, PMV/PPD, UTCI | PENDING | pythermalcomfort 4.4.2 installed, unwrapped |
| 5 — IDF readiness | generic + standards-specific checks, passport | PENDING | TM59:2026 stage/model rules already machine-readable in the pack |
| 6 — EnergyPlus worker | run, isolation, harvest, manifest | PENDING | official 25.1.0 verified installed (ADR-0004) |
| 7 — API | FastAPI service | PENDING | |
| 8 — Design system & frontend | tokens, nav, chart primitives | PENDING | Node 24 + npm 11 available on machine |
| 9–17 | Weather Lab … publication release | PENDING | |

## What exists now (sessions 1–2)

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

**95 tests passed, 0 skipped, 0 failed** (local run 2026-08-28;
`PYTHONPATH=packages/overheatlens-core python -m pytest packages/overheatlens-core/tests -q`).
New rows: VAL-TM26-01..12 (TM59:2026 boundaries), VAL-WCG-01..03 (weather compatibility),
VAL-REAL-01..03 (real-file local validation), V-EPW-14..16 (real-world layout variants).
Notable: boundary tests caught two real off-by-ones during development (30-April base index
in the Trm chain; sleep-window geometry in session 1) — both fixed before any result was
produced.

## Honest gaps / open blockers

1. **TM59:2017 + TM52 PDFs still not acquired.** `~/PhD/Literature_Review/Papers` was found
   EMPTY on 2026-08-28 (the TM59:2026 trio was in `~/Downloads` instead). Those packs remain
   compliance-gated (enforced in code). The TM52 equation constants inside TM59:2026's Trm
   chain are flagged secondary inside the pack until the TM52 PDF is held.
2. Standards diff viewer (TM59:2017 ↔ 2026) is now unblocked on the 2026 side but waits for
   the verified 2017 pack.
3. EnergyPlus 26.1.0 pin decision deferred (ADR-0004) — working pin 25.1.0, machine-verified.
4. No UI yet (Phase 8+) — launchers expose the CLI honestly rather than a placeholder UI.
