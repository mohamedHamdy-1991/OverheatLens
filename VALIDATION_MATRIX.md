# VALIDATION MATRIX

Live register of validation evidence (master prompt RULE 25). Every phase report states which
rows were added/passed. Tolerances are per-metric; never widened without a documented scientific
reason (RULE 7).

Status: `PASS` / `FAIL` / `PENDING` (fixture exists, run pending) / `BLOCKED` (source/dependency missing).

## A. EPW engine

| ID | Method | Rule/property | Fixture | Source | Expected | Actual | Tolerance | Status | Date | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| V-EPW-01 | parser | good file parses: 8760 rows × 35 fields, header intact | `fixtures/epw/synthetic/good_file.epw` | EPW format spec (EnergyPlus IO reference, secondary) | rows=8760, fields=35 | 8760/35 | exact | PASS | 2026-08-28 | parser unit test |
| V-EPW-02 | parser | leap-year file parses 8784 rows | `fixtures/epw/synthetic/leap_year.epw` | EPW format spec | rows=8784 | 8784 | exact | PASS | 2026-08-28 | |
| V-EPW-03 | checker | missing-hour gap detected and located | `fixtures/epw/synthetic/missing_hours.epw` | QC design | ≥1 GAP issue, hour index reported | detected, indices reported | exact count of planted gaps | PASS | 2026-08-28 | |
| V-EPW-04 | checker | sentinel/missing values (999.x) flagged | `fixtures/epw/synthetic/sentinel_values.epw` | EPW format spec | sentinel issues per affected field | detected | exact | PASS | 2026-08-28 | |
| V-EPW-05 | checker | dry-bulb spike outside physical range | `fixtures/epw/synthetic/temp_spike.epw` | physical plausibility | OUT_OF_RANGE on dry bulb | detected | exact | PASS | 2026-08-28 | |
| V-EPW-06 | checker | dew point > dry bulb impossible relationship | `fixtures/epw/synthetic/dewpoint_violation.epw` | physics | DEWPOINT_VIOLATION | detected | exact | PASS | 2026-08-28 | |
| V-EPW-07 | checker | RH outside 0–100 % | `fixtures/epw/synthetic/impossible_rh.epw` | physical plausibility | OUT_OF_RANGE on RH | detected | exact | PASS | 2026-08-28 | |
| V-EPW-08 | checker | stuck sensor run detected | `fixtures/epw/synthetic/stuck_sensor.epw` | QC design | long constant-run issue on flagged field | detected | exact | PASS | 2026-08-28 | |
| V-EPW-09 | metrics | exceedance hours above fixed threshold | good_file derived | metamorphic: +1 K indoor equivalent shift cannot reduce count | monotone non-decreasing | verified in property test | exact monotonicity | PASS | 2026-08-28 | property-based (hypothesis) |

## B. Standards engine

| ID | Method | Rule | Fixture | Source | Expected | Actual | Tolerance | Status | Date | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| VAL-STD-01 | TM59:2017 | Criterion A boundary: 3 % annual hours | synthetic hourly series | S-02 (SECONDARY-PENDING) | exact flip at 263rd exceedance hour of 8760 | verified | exact integer | PASS | 2026-08-28 | implementation locked to register; value pending CIBSE check |
| VAL-STD-02 | TM59:2017 | Criterion B boundary: 1 % annual hours, sleep window 22:00–07:00 | synthetic hourly series | S-02 (SECONDARY-PENDING) | exact flip at 88th sleep-window exceedance | verified | exact integer | PASS | 2026-08-28 | window logic tested incl. window edges |
| VAL-STD-03 | TM59:2017 | Criterion C: bedroom >26 °C > 32 h | synthetic hourly series | S-02 (SECONDARY-PENDING) | exact flip at 33rd hour >26 °C | verified | exact integer | PASS | 2026-08-28 | |
| VAL-STD-04 | engine gate | `source_verified: false` pack refused in compliance mode | `uk_tm59_2026.yaml` scaffold | Phase-0 gate (ADR-0005) | raises `SourceNotVerified`, no result object | verified | behavioural | PASS | 2026-08-28 | Rule 29 wording returned |
| VAL-STD-05 | engine gate | Part O pack inherits TM59:2017 criteria + applies ADO §2.6 window rules as model-readiness checks | `uk_part_o_dynamic.yaml` | S-01 MACHINE-VERIFIED | schema-valid; override rules present with clause ids | verified | behavioural | PASS | 2026-08-28 | full numeric evaluation needs simulation outputs (Phase 6) |
| VAL-STD-06 | rule packs | every pack validates against JSON Schema; every criterion has id/source/clause/verification fields | all packs in `overheatlens/rules/` | ADR-0007 | schema-valid, provenance-complete | verified | schema | PASS | 2026-08-28 | |

## C. Provenance / reproducibility

| ID | Method | Property | Fixture | Expected | Actual | Status | Date | Notes |
|---|---|---|---|---|---|---|---|---|
| VAL-PRV-01 | hashing | same file → same SHA-256; byte change → different hash | good_file + mutated copy | deterministic, sensitive | verified | PASS | 2026-08-28 | |
| VAL-PRV-02 | manifest | manifest is JSON-serialisable, contains engine/core/rule-pack versions + input hashes | synthetic run | schema-complete, deterministic ordering | verified | PASS | 2026-08-28 | |

## D. Pending rows (scheduled)

| ID | Method | Why pending |
|---|---|---|
| VAL-XSIM-01..n | EnergyPlus end-to-end archetype regression | awaits Phase 6 worker; then 8–12 frozen archetypes (plan §27.1 Tier 5) |
| VAL-REF-01 | independent reference implementation of TM59:2017 criteria | scheduled with Phase 3 completion (Tier 2; never copy production function) |
| VAL-XSW-01 | DesignBuilder cross-check | author access exists; awaits frozen archetype set (Tier 4) |
| VAL-PRSR-01..n | parser fault injection full campaign (plan §27.2) | partial coverage now (V-EPW-03..08); campaign completes with fuzz/property suite |
