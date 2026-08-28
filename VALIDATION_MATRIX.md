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
| V-EPW-08 | checker | stuck sensor run detected | `fixtures/epw/synthetic/stuck_sensor.epw` | QC design | constant-run warning | detected (11 h run, ≥10 h threshold) | exact | PASS | 2026-08-28 | thresholds calibrated across fixture family: healthy ≤5 h runs, ≤5.2 K/h |
| V-EPW-09 | metrics | exceedance hours above fixed threshold | good_file derived | metamorphic: +1 K indoor equivalent shift cannot reduce count | monotone non-decreasing | verified in property test | exact monotonicity | PASS | 2026-08-28 | property-based (hypothesis) |
| V-EPW-10 | checker | temperature discontinuity (planted spike) | `fixtures/epw/synthetic/temp_spike.epw` | QC design; calibration: healthy ≤5.2 K/h, spike 16.2 K/h | DISCONTINUITY error (>15 K/h) | detected, FAIL | exact | PASS | 2026-08-28 | 8–15 K/h = warning band |
| V-EPW-11 | metrics | constant-offset shift invariance of exceedance counts | hypothesis-generated | metamorphic (plan §27.3) | counts identical under joint series+threshold shift | verified (150+60 examples) | exact, modulo float ties | PASS | 2026-08-28 | exact-tie comparisons excluded (IEEE-754); documented in test |
| V-EPW-12 | metrics | observation order never changes aggregates | shuffled series | metamorphic (plan §27.3) | identical counts/degree-hours | verified | exact | PASS | 2026-08-28 | |
| V-EPW-13 | suite | full local suite green | all of `packages/overheatlens-core/tests` | — | 95 passed, 0 skipped | 95 passed | — | PASS | 2026-08-28 | command: `PYTHONPATH=packages/overheatlens-core python -m pytest packages/overheatlens-core/tests -q` |
| V-EPW-14 | parser | 32-field truncated CIBSE variant parses; present fields keep standard indices | `fixtures/epw/synthetic/truncated_fields.epw` (new synthetic fixture) | W-04 finding from real CIBSE DSY | dry-bulb identical to 35-field source; trailing fields NaN | verified | exact | PASS | 2026-08-28 | checker emits TRUNCATED_FIELDS info; verdict stays PASS |
| V-EPW-15 | parser | empty numeric cells → NaN, checker reports MISSING_VALUES on used fields | mutated good_file (empty dry bulb) | W-04 | explicit non-result, never zero, never crash | verified | behavioural | PASS | 2026-08-28 | all-missing dry bulb makes weather_summary raise (explicit non-result) |
| V-EPW-16 | parser | reduced row layouts below 32 fields still rejected | mutated good_file (20 fields) | EPW format | EpwParseError | verified | behavioural | PASS | 2026-08-28 | |

## B. Standards engine

| ID | Method | Rule | Fixture | Source | Expected | Actual | Tolerance | Status | Date | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| VAL-STD-01 | TM59:2017 | Criterion A boundary: 3 % annual hours | synthetic hourly series | S-02 (SECONDARY-PENDING) | exact flip at 263rd exceedance hour of 8760 | verified | exact integer | PASS | 2026-08-28 | implementation locked to register; value pending CIBSE check |
| VAL-STD-02 | TM59:2017 | Criterion B boundary: 1 % annual hours, sleep window 22:00–07:00 | synthetic hourly series | S-02 (SECONDARY-PENDING) | exact flip at 88th sleep-window exceedance | verified | exact integer | PASS | 2026-08-28 | window logic tested incl. window edges |
| VAL-STD-03 | TM59:2017 | Criterion C: bedroom >26 °C > 32 h | synthetic hourly series | S-02 (SECONDARY-PENDING) | exact flip at 33rd hour >26 °C | verified | exact integer | PASS | 2026-08-28 | |
| VAL-STD-04 | engine gate | `source_verified: false` pack refused in compliance mode | `uk_tm59_2026.yaml` scaffold | Phase-0 gate (ADR-0005) | raises `BlockedRulePack` (subclass of `SourceNotVerified`), no result object | verified — refused in BOTH modes (nothing to evaluate) | behavioural | PASS | 2026-08-28 | Rule 29 wording returned |
| VAL-STD-05 | engine gate | Part O pack inherits TM59:2017 criteria + applies ADO §2.6 window rules as model-readiness checks | `uk_part_o_dynamic.yaml` | S-01 MACHINE-VERIFIED | schema-valid; override rules present with clause ids | verified (4 limits + 2 exclusions exposed via engine) | behavioural | PASS | 2026-08-28 | full numeric evaluation needs simulation outputs (Phase 6) |
| VAL-STD-06 | rule packs | every pack validates against JSON Schema; every criterion has id/source/clause/verification fields | all packs in `overheatlens/rules/` | ADR-0007 | schema-valid, provenance-complete | verified | schema | PASS | 2026-08-28 | |
| VAL-STD-07 | TM59:2017 | sleep-window geometry: hour-ending labels 23,24,1..7 span 22:00–07:00 | synthetic series | hour-ending convention | label 22 (21:00–22:00) excluded; label 7 (06:00–07:00) included | verified — test caught and fixed an initial off-by-one during development | exact | PASS | 2026-08-28 | boundary-test discipline working as intended (RULE 7) |
| VAL-STD-08 | dwelling logic | dwelling result is FAIL if any criterion fails; INCOMPLETE (never PASS) when any criterion NOT_EVALUATED | synthetic rooms | TM59 dwelling semantics | exact trichotomy | verified | behavioural | PASS | 2026-08-28 | |

## B2. TM59:2026 (source-verified pack, S-03/S-08) — added 2026-08-28

| ID | Method | Rule | Fixture | Source | Expected | Actual | Tolerance | Status | Date | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| VAL-TM26-01 | engine gate | source_verified pack passes compliance gate | `uk_tm59_2026.yaml` v1.0.0 | S-03 MACHINE-VERIFIED | compliance mode allowed | verified | behavioural | PASS | 2026-08-28 | flipped from blocked in previous session |
| VAL-TM26-02 | Criterion a | hour limits: 59 h living (1989 occupied h) / 110 h bedroom (3672 h) | synthetic May series | S-03 §2.4.1 + Table 2 | exact flip 59→PASS/60→FAIL (living); 110/111 (bedroom) | verified both | exact integer | PASS | 2026-08-28 | |
| VAL-TM26-03 | Criterion a | ΔT rounding per TM52: raw ΔT ≥ 0.5 K counts, 0.49 does not | constant-series at threshold+0.49/+0.5 | S-03 §2.4.1 quoting TM52 | exact boundary | verified | exact | PASS | 2026-08-28 | differs from 2017 interpretation |
| VAL-TM26-04 | Criterion a | adaptive thresholds: Cat I 24.1→30.7 °C, Cat II = +1 K, clamped outside Trm 10–30 | constant daily-mean inputs at 5/10/20/30/40 °C | S-03 §2.4.1 | exact clamp values; II−I = 1.0 K | verified | exact | PASS | 2026-08-28 | slope 0.33 implied by source values |
| VAL-TM26-05 | Trm chain | TM52 Eq 2.2 recursion + Eq 2.3 7-day weighted initialiser (0.8 weights), 1 May–30 Sep = 153 days | step-response daily-mean series + constant series | S-03 §2.4.1 (constants cross-referenced from S-04, flagged) | hand-computed chain values | verified | tight float | PASS | 2026-08-28 | boundary test caught an off-by-one in the 30 April base index during development |
| VAL-TM26-06 | Criterion b | nights-based: Tn 26 (I) / 27 (II) fixed; limit 4 nights; window 11 pm–8 am | synthetic hot nights | S-03 §2.4.2 | exact flip 4→PASS/5→FAIL; Cat I/II divergence at 26.5 °C means | verified | exact | PASS | 2026-08-28 | 153 nights assessed; night N = 11 pm day N → 8 am day N+1 |
| VAL-TM26-07 | Criterion b | mean night temperature, not peak | one 34 °C hour in an otherwise 25 °C night | S-03 §2.4.2 | mean 26.44 ≤ 27 → PASS | verified | exact | PASS | 2026-08-28 | |
| VAL-TM26-08 | Criterion c | fixed 26 °C; limits 59/110; exactly 26.0 does not exceed | synthetic June occupied-hour series | S-03 §2.4.3 | exact flips; strict inequality | verified | exact | PASS | 2026-08-28 | bedroom variant uses all-hours basis |
| VAL-TM26-09 | Criterion c | ceiling-fan uplift 2.1 K flips a failing result | 100 h at 27.5 °C ± fan uplift array | S-03 §2.4.3 | FAIL without uplift, PASS with | verified | exact | PASS | 2026-08-28 | uplift supplied as array from modelled air speeds |
| VAL-TM26-10 | Criterion d | communal: fixed 28 °C, limit 110 h, strict inequality | synthetic May series | S-03 §2.4.4 | exact flip 110/111; 28.0 not counted | verified | exact | PASS | 2026-08-28 | |
| VAL-TM26-11 | Stages | stage definitions and criteria mapping | pack metadata | S-03 §2.5/Fig.1 | stage_1 a+b; stage_3 b+c; d at all stages | verified | structural | PASS | 2026-08-28 | the ≥50 %-open mode-selection rule is stored for readiness checks (Phase 5) |
| VAL-TM26-12 | occupancy | living occupancy 9 am–10 pm excluded night heat; bedroom counts all hours | night-only + day-only heat placements | S-03 Table 2 | exact counts | verified | exact | PASS | 2026-08-28 | hour-ending labels 10..22 |

## B3. Weather compatibility guard (S-08)

| ID | Method | Rule | Fixture | Expected | Actual | Status | Date | Notes |
|---|---|---|---|---|---|---|---|---|
| VAL-WCG-01 | compatibility | minimum file → compatible | `*_DSY1_2050s_HIGH50_CIBSE_v1.1.epw` | compatible | verified | PASS | 2026-08-28 | filename-traceability only |
| VAL-WCG-02 | compatibility | DSY3 / 2080s / HIGH10 → research_only with reason | variant filenames | research_only + reason naming the difference | verified | PASS | 2026-08-28 | per S-08 §4 alternatives |
| VAL-WCG-03 | compatibility | untraceable filename → unknown, never guessed | `my_site_2023.epw` | unknown + "not machine-verifiable" | verified | PASS | 2026-08-28 | plan §10.2 wording |

## B4. Real-file local validation (copyrighted files used locally, never committed)

| ID | File (local) | SHA-256 | Result | Status | Date | Notes |
|---|---|---|---|---|---|---|
| VAL-REAL-01 | epw_doctor `examples/real_weather/Leeds_DSY1.epw` | `6f6598a7…` | parses PASS; 32-field variant INFO; annual mean 10.69 °C; compat research_only (no 2050s/HIGH50 labels) | PASS | 2026-08-28 | first real CIBSE DSY validated end-to-end |
| VAL-REAL-02 | `~/Downloads/leeds_2050.epw` | `382fee23…` | PASS_WITH_WARNINGS (stuck-run 12 h warning — plausible for morphed future years); compat unknown | PASS_WITH_WARNINGS | 2026-08-28 | warnings are informative, not failures |
| VAL-REAL-03 | `~/Downloads/my_site_2023.epw`, `savetest_2001.epw` | `5a63b5e7…` / — | parse OK after empty-cell tolerance; 99.9 temperature sentinel convention caught by range checks (FAIL, correctly) | FAIL (correct) | 2026-08-28 | template files with all-missing met fields; honest verdicts, no crashes |


## B5. TM59:2017 + TM52 (source-verified packs, S-02/S-04) — added 2026-08-28

| ID | Method | Rule | Fixture | Source | Expected | Actual | Tolerance | Status | Date | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| VAL-TM17-01 | Criterion a | adaptive: raw DT >= 0.5 K counts (Tmax 0.33Trm+21.8 Cat II) | constant series at boundary | S-02 §4.2(a) + S-04 Eq 8/9 | exact flip at 0.5 K | verified (with IEEE-754 epsilon guard) | exact | PASS | 2026-08-28 | boundary test exposed float-noise flip; guard added, documented |
| VAL-TM17-02 | Criterion a | May-Sept window; living denominator 1989 h; 3% flip at 59/60 h | synthetic July occupied series | S-02 §4.2(a)+§6 | exact flips; April excluded | verified | exact integer | PASS | 2026-08-28 | |
| VAL-TM17-03 | Criterion a | bedroom variant 3672 h basis (24/7 May-Sept) | synthetic series | S-02 §6 | basis reported 3672 | verified | exact | PASS | 2026-08-28 | |
| VAL-TM17-04 | Criterion b | limit 32 h (fail at 33), window 22:00-07:00, full year, strict > 26 | synthetic sleep-window series | S-02 §4.2(b) note | exact flips; label-22 excluded, label-7 included; Dec counted | verified | exact | PASS | 2026-08-28 | supersedes the wrong 1%-of-8760 transcription (VAL-STD-02) |
| VAL-TM17-05 | Criterion mv | mechanical route: >26 C > 3% of model occupied hours; NOT_EVALUATED without occupancy; NOT_APPLICABLE on natural route | synthetic + occupancy array | S-02 §4.3/§4.1 | route filtering + denominator behaviour | verified | behavioural | PASS | 2026-08-28 | |
| VAL-TM17-06 | Corridor | 28 C > 3% of 8760 -> ADVISORY FLAG only; never fails dwelling | 300 h at 29 C | S-02 §4.5 | FLAG + dwelling PASS | verified | behavioural | PASS | 2026-08-28 | |
| VAL-TM17-07 | Trm | TM52 Eq 2.3 published weights (1/.8/.6/.5/.4/.3/.2)/3.8 + Eq 2.2 chain | step-response series | S-04 Box 2 (verbatim) | hand-computed chain | verified | tight float | PASS | 2026-08-28 | corrected from normalised 0.8^k after PDF verification |
| VAL-TM52-01 | Criterion 1 | He > 3% of May-Sept model occupied hours | office occupancy array | S-04 §6.1.2(a) | exact flips; denominator 9h x 153d | verified | exact | PASS | 2026-08-28 | |
| VAL-TM52-02 | Criterion 2 | We = sum(h x wf) per day, limit 6 | constructed worst day (3h@1,2h@2,1h@3 -> We 10) | S-04 Eq 10 | We 10 FAIL; We 6 PASS | verified | exact | PASS | 2026-08-28 | document worked example cross-checked |
| VAL-TM52-03 | Criterion 3 | raw DT > 4 K any hour -> fail; exactly 4.0 does not | boundary series | S-04 §6.1.2(c) | exact | verified | exact | PASS | 2026-08-28 | |

## B6. Real-file local validation — Leeds DSY family (copyrighted, never committed)

| ID | File (local) | SHA-256 | Result | Status | Date | Notes |
|---|---|---|---|---|---|---|
| VAL-REAL-04 | `…/LEEDS Weather Files/Weather File MET Office/Leeds_DSY1_2020High50_.epw` (TM59:2017 minimum) | — | parses PASS; compat 2017 = compatible; compat 2026 = research_only (legacy naming) | PASS | 2026-08-28 | annual mean 11.487 C; hottest 31.3 C; 102 h > 26 C |
| VAL-REAL-05 | 57-file Leeds DSY family sweep (compatibility guard, 2017 rule) | — | exactly 1 compatible (the DSY1_2020High50 minimum), 56 research_only with reasons | PASS | 2026-08-28 | guard distinguishes epochs/scenarios/percentiles and flags legacy naming |

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
