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
- Zero-install launchers (`Start/Close/Run Tests`, macOS `.command` + Windows `.bat`)
- `packages/overheatlens-core`: provenance hashing + run manifests, JSON-Schema-validated rule packs, EPW parser/validation/metrics, standards engine with TM59:2017 criteria A/B/C and evaluation gate, CLI (`version`, `rule-packs`, `check-epw`)
- Rule packs: `uk_tm59_2017` (secondary-pending values, gated), `uk_part_o_dynamic` (ADO-verified overrides + inherited criteria), `uk_tm52` (scaffold, gated), `uk_tm59_2026` (blocked scaffold — no invented values)
- 8 synthetic EPW fixtures incl. deliberate faults; full local pytest suite

## Validation evidence this session

See `VALIDATION_MATRIX.md` rows V-EPW-01… and VAL-STD-01…; exact test commands and
results are recorded in the session report in `docs/validation/`.

## Honest gaps / open blockers

1. **CIBSE originals not acquired** (TM59:2017, TM59:2026, TM52, weather guidance). Until then
   those packs cannot produce compliance-labelled results (enforced in code).
2. Web search quota resets 2026-08-30 → capture CIBSE TM59:2026 public statements (SOURCE_REGISTER S-05).
3. EnergyPlus 26.1.0 pin decision deferred (ADR-0004) — working pin 25.1.0, machine-verified.
4. No UI yet (Phase 8+) — launchers expose the CLI honestly rather than a placeholder UI.
