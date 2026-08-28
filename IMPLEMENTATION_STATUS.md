# IMPLEMENTATION STATUS

Last updated: **2026-08-28** (session 4 — Phases 4–6 complete: comfort wrappers, IDF readiness, EnergyPlus worker, first end-to-end chain)

Overall stage: **Phases 0–3 complete for all rule packs.** Every bundled standards pack
(uk_tm59_2026, uk_tm59_2017, uk_part_o_dynamic, uk_tm52) is now machine-verified against
its official PDF and compliance-allowed. The standards engine implements all verified
criteria. No source document is missing any more.
Governing specs: `docs/specs/` · Sources: `SOURCE_REGISTER.md` · Decisions: `ARCHITECTURE_DECISIONS.md` · Validation: `VALIDATION_MATRIX.md`

## Phase tracker

| Phase | Scope | Status | Notes |
|---|---|---|---|
| 0 — Freeze standards & sources | source register, rule-pack schema, transcription | **COMPLETE** — ADO 2021, TM59:2026 (+weather requirements), TM59:2017, TM52 all MACHINE-VERIFIED from official PDFs with SHA-256 | no blocked packs remain |
| 1 — Core package skeleton | package, provenance, schemas, CLI, CI, tests | **COMPLETE** | |
| 2 — EPW engine | parser, checker, metrics, multi-EPW, tests | **SUBSTANTIALLY COMPLETE** | parser (32-field CIBSE variant, empty cells), calibrated QC, metrics, compatibility guards for TM59:2017 AND TM59:2026 weather rules, validated on the real 57-file Leeds DSY family (local only) |
| 3 — Standards engine | TM59:2026, TM59:2017, Part O, TM52 | **COMPLETE for implemented criteria** — TM59:2026 (a–d + stages), TM59:2017 (adaptive a, 32-h b, mv route, advisory corridors), TM52 (He/We/Tupp), Part O inheritance + ADO overrides. Standards diff viewer (UI) pending | |
| 4 — Comfort engine | wrappers, applicability, PMV/PPD, adaptive, UTCI | **COMPLETE** | pythermalcomfort 4.4.2 wrapped unmodified (ISO 7730:2025 default), explicit applicability gates, provenance in every result (VAL-CMF-01..05) |
| 5 — IDF readiness | generic + standards-specific checks, passport | **COMPLETE** | object-level parser; every check row explains itself (RULE 16); bedroom/living classification; ADO §2.6 / TM59 §3.3 conformance notes; runnable synthetic dwelling fixture |
| 6 — EnergyPlus worker | run, isolation, harvest, manifest | **COMPLETE** | official-binary probe (25.1.0), isolated jobs, err interpreter, --readvars harvest, DERIVED Top = 0.5(MAT+MRT); first end-to-end chain demonstrated (VAL-XSIM-01..04) |
| 7 — API | FastAPI service | PENDING | |
| 8 — Design system & frontend | tokens, nav, chart primitives | PENDING | Node 24 + npm 11 available |
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

**118 tests passed, 0 skipped, 0 failed** (local run 2026-08-28).
New rows: VAL-TM17-01..07 (TM59:2017), VAL-TM52-01..03, VAL-WCG-04..08 (TM59:2017 weather
rule + legacy naming), VAL-REAL-04..05 (real Leeds DSY family).
Notable catches by the verification/boundary discipline: the earlier secondary TM59:2017
transcription was wrong on four load-bearing points (fixed and documented); the TM52 Eq 2.3
initialiser used normalised 0.8^k instead of the published weights (fixed); a float-noise
flip at the exact 0.5 K ΔT boundary (epsilon guard added).

## Honest gaps / open blockers

1. Standards **diff viewer** (TM59:2017 ↔ 2026): data-side ready — UI work, Phase 8+.
2. EnergyPlus 26.1.0 pin decision deferred (ADR-0004) — working pin 25.1.0.
3. No UI yet (Phase 8+) — launchers expose the CLI honestly.
4. **Accepted limitation (ADR-0012):** TM59:2026 assessments use the CIBSE 2016-release
   fallback `Leeds_DSY1_2050High50` until the 2025-release v1.1 files are acquired;
   flagged `research_only` + `closest_available_match`, limitation carried in pack + guard.
5. The end-to-end chain (VAL-XSIM-03) uses an illustrative synthetic dwelling, not a
   validated archetype; the 8–12 frozen archetype regression set (plan Tier 5) is the
   next validation milestone.
6. Operative temperature is derived as Top = 0.5(MAT+MRT) (low air speed); AirflowNetwork
   air-speed-based operative temperature is future work.
