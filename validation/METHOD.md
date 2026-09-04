# OverheatLens — Scientific Validation Campaign: METHOD

*Version 1.0 — 2026-09-04 · OverheatLens · Mohamed Hamdy Ali · MIT*

This document describes **the whole validation method** used to establish that
OverheatLens' overheating and thermal-comfort analyses are scientifically
trustworthy. Every case is automated in `run_campaign.py`, which writes
`results.json` and `CAMPAIGN_REPORT.md`. Re-run after any science change:

```
./.venv/bin/python validation/run_campaign.py
```

`INCOMPLETE` is a valid verdict wherever a required external artefact is not
available — honesty outranks green ticks (governance: GOVERNANCE.md).

---

## 1. The validation pyramid (five layers, weakest to strongest)

| Layer | Question it answers | Cases |
|---|---|---|
| **L1 — Source chain** | Are the numbers we implement the numbers in the official documents? | V01 |
| **L2 — Published worked examples** | Does the engine reproduce arithmetic published in the standards / literature? | V04, V05, V06, V07 |
| **L3 — Boundary hand-calculations** | Do verdicts flip at exactly the published thresholds? | V03, V04 |
| **L4 — External tool & real-data cross-checks** | Do whole-pipeline results agree with DesignBuilder exports (the author's PhD) and with CIBSE's own published example outcomes? | V10, V11 |
| **L5 — Internal consistency & determinism** | Is the simulation engine stable, and are its outputs physically coherent? | V08, V09 |

A campaign verdict is **PASS** only when no case is FAIL. `INCOMPLETE` cases
are listed with the exact missing artefact.

---

## 2. What is validated, end to end

```
EPW file ──► parser/QC ──► IDF readiness ──► EnergyPlus 25.1.0 run
                                                 │
              ┌──────────────────────────────────┘
              ▼
   hourly zone temperatures (LEVEL:ROOM, 8760 h)
              │
              ├──► TM59:2017 (criteria A, B)          ─► dwelling verdict
              ├──► TM59:2026 (criteria a–d, stages)   ─► dwelling verdict
              ├──► Part O dynamic (ADO limits)        ─► dwelling verdict
              ├──► TM52 (criteria 1, 2, 3)            ─► room verdicts
              └──► comfort suite (PMV/PPD, adaptive EN, UTCI on the
                   simulated operative temperature)   ─► per-zone results
```

The mitigation energy experiment compares **two real EnergyPlus runs**
(baseline vs the author's strategy variant) on the same chosen weather file
and reports annual `Electricity:Facility` / `NATURALGAS:Facility` deltas.

---

## 3. The cases

### V01 — Source chain (L1)
**Method:** every versioned rule pack (uk_tm59_2017, uk_tm59_2026,
uk_part_o_dynamic, uk_tm52) carries the SHA-256 of the official PDF it was
transcribed from, plus a machine-verification record (text extraction +
key-value locate) proving each implemented limit appears in that PDF.
**Pass:** all four packs `verified` with recorded SHA-256 and verification date.
**Reference:** SOURCE_REGISTER.md; standards PDFs stored locally (never redistributed).

### V02 — EPW parser & QC on the real research weather (L4)
**Method:** parse the author's actual research file
(`Leeds_DSY1_2020High50_.epw`, CIBSE-style DSY family, local-only).
Checks: 8760 hourly records; 35 columns; header location/timezone read;
QC classification in {PASS, PASS_WITH_WARNINGS}; annual mean dry-bulb inside
the Leeds climate envelope 8–13 °C (CIBSE DSY1 2020-high family property).
**Reference:** CIBSE/Met Office weather file format; the file's own header record.

### V03 — TM59:2017 boundary exactness (L3)
**Method:** synthetic hourly series constructed so verdicts flip at exactly the
published 2017 boundaries (adaptive criterion): (a) living room, May–September
occupied basis 1 989 h — hours above Tmax = 0.33·Trm + 21.8 (Cat II, Trm 15 →
26.75 °C) counted with the published ΔT rounding (raw ≥ 0.5 K); 59 counted
hours (2.967 %) must PASS, 60 (3.019 %) must FAIL at the published 3 %
threshold; sub-rounding heat (raw ΔT 0.45 K) must count zero hours; April must
be excluded. (b) bedrooms, criterion B: Top > 26 °C during the published
sleep window (22:00–07:00), full year, limit 32 h — 32 hot sleep hours must
PASS, 33 must FAIL; daytime heat must never count.
**Reference:** CIBSE TM59:2017 §5.2 (machine-verified pack, SHA-pinned;
corrections documented in the pack's verification note).

### V04 — TM52 worked example & rounding boundaries (L2 + L3)
**Method:** (a) the published TM52 §6.1.2 weighted-exceedance worked pattern
(3 h at ΔT=1, 2 h at ΔT=2, 1 h at ΔT=3 → We = 10 with full hours) must give
exactly We = 10 and FAIL (> 6); (b) criterion 1 rounding edge: raw ΔT = 0.45 K
must count zero hours, raw 0.50 K must count all occupied hours (published
1 K-rounding rule); (c) criterion 3 edge: raw ΔT = 4.0 K at any hour → FAIL.
**Reference:** CIBSE TM52-2013 §6.1.2, §6.1.1, §6.1.3 (pack SHA-pinned).

### V05 — PMV/PPD against published ISO 7730 anchors (L2)
**Method:** at sedentary reference conditions (met 1.2, clo 0.5, v 0.1 m/s,
RH 50 %) bisect operative temperature until PMV hits each published anchor
(0, ±0.5, ±1); the wrapper's PPD must equal the published Fanger PPD relation
`PPD = 100 − 95·exp(−0.03353·PMV⁴ − 0.2179·PMV²)` at that PMV within
±0.75 pp, and match the published anchor table: PPD(0) = 5 %, PPD(±0.5) ≈ 10 %,
PPD(±1) ≈ 26 %. The published applicability limit |PMV| ≤ 2 must be enforced:
conditions that would give |PMV| > 2 must be refused (explicit non-result),
never extrapolated. Mathematics are never reimplemented — the wrapped library
(pythermalcomfort, ISO 7730) is the calculator; this case validates it against
the published relation and limits.
**Reference:** ISO 7730 (PPD relation + anchor table + applicability; e.g.
quadco.engineering ISO 7730 reference page, 2026 retrieval).

### V06 — UTCI reference conditions (L2)
**Method:** Bröde et al. (2012) define reference conditions (Tr = Ta,
RH 50 %, v = 0.5 m/s at 10 m, reference metabolism/clothing) under which
UTCI ≈ Ta (published agreement r² ≈ 0.995). Check UTCI(25, 25, 0.5, 50 %)
within ±0.5 °C of 25 °C; check directionality (raising Tr to 45 °C at the same
Ta must raise UTCI above the reference value — heat-stress direction).
**Reference:** Bröde et al. 2012, *Int J Biometeorol* 56:481–494; official
polynomial as wrapped by pythermalcomfort (Tartarini & Schiavon 2020).

### V07 — Adaptive comfort limits vs published formulae (L2)
**Method:** (a) TM52 Category II operative limit `Tmax = 0.33·Trm + 21.8`
must be reproduced at Trm ∈ {10, 15, 17, 23, 30} (engine vs hand arithmetic);
category I uses +20.8; limits clamp outside the published Trm range 10–30 °C.
(b) the EN 16798-1 comfort temperature `Tcomf = 0.33·Trm + 18.8` from the
wrapped adaptive model at the same Trm points.
**Reference:** CIBSE TM52-2013 Eq 8 (pack SHA-pinned); EN 16798-1 as
implemented by pythermalcomfort.

### V08 — EnergyPlus determinism (L5)
**Method:** the same archetype (End-terrace house (1930s) base model) × the
same real weather file, run twice in isolated directories through the app's
runner: harvested zone series and annual facility meters must be **identical**.
**Reference:** EnergyPlus 25.1.0 official binary; the app's run manifest.

### V09 — Energy meter internal consistency (L5)
**Method:** from the run's meter output: the 12 monthly `Electricity:Facility`
totals must sum to the runperiod (annual) total within 0.5 %; electricity and
gas annual totals must be non-negative; the gas-heated dwellings must show
gas > 0 and the all-electric templates must show gas = 0 (construction
consistency with the author's models).
**Reference:** EnergyPlus meter definition (eplusout.mtr → eplusmeter.csv via
`--readvars`).

### V10 — Cross-check vs the author's DesignBuilder PhD exports (L4)
**Method:** for the measured dwellings in the Safer_Heat_Harehills parametric
study, the app's full-pipeline TM59:2017 verdict (own EnergyPlus run on the
Leeds DSY1 2020-High50 file) is compared with the verdicts in the author's
DesignBuilder TM59 exports for the same dwellings. Dwelling-level agreement =
same PASS/FAIL direction. Exports without a recorded baseline give INCOMPLETE
with the exact reason (no fabrication). Export weather metadata is not
recorded in the study files, so dwelling-level agreement is reported as
**CONFIRMED_DIRECTIONAL** rather than identical-weather proof.
**Reference:** `data/mitigation/summary.json` (built from the author's
research folder; kept local, never committed).

### V11 — CIBSE's own published example (L4)
**Method:** the CIBSE TM59 Example 4 reference flat, run through the app's
full pipeline on the Leeds DSY1 2020-High50 file, must reproduce the
direction of CIBSE's published example outcome (the flat overheats — fails
criterion A — under a 2020s DSY). Reported as CONFIRMED_DIRECTIONAL (CIBSE
publishes the example for its own weather file; the app runs the Leeds file).
**Reference:** CIBSE TM59:2017, worked example chapter (pack SHA-pinned).

---

### V12 — DesignBuilder 01BA baseline cross-check (L4)
**Method:** the author's DesignBuilder-exported IDF for the Safer_Heat_Harehills
01BA baseline (`01BA_BL_Baseline/01BA__Baseline.idf`, E+ 23.1 export) is run
through the app's full TM59:2017 pipeline on `Leeds_DSY1_2020High50_.epw` and
compared zone-by-zone with the verdicts in the author's DesignBuilder TM59
export (`01BA__Baseline (TM59).csv`). A documented, semantics-preserving
migration to EnergyPlus 25.1.0 is applied on a copy (People MRT
`ZoneAveraged`→`EnclosureAveraged` — the only key in the 25.1 IDD, a pure
zone→enclosure terminology rename; Version identifier updated). The original
file is never modified. **Verdict CONFIRMED** when every shared habitable zone
(kitchen, lounge, bedroom 1, bedroom 2) agrees; corridor zones must sit below
the 3 % criterion in both. Absolute criterion percentages differ between the
two engines and are reported, not thresholded.
**Reference:** the author's DesignBuilder TM59 export (PhD data, kept local).

### V13 — Displayed numbers recomputed from primary data (L3/L4 — strictest)
**Method:** every headline number the app shows is recomputed from primary data
by fresh code written from the published definitions — never by calling the
app's own functions — and compared exactly: (1) Weather Lab metrics (records,
annual mean, hottest hour, hours >26 °C, degree-hours >26 °C) recomputed from
the raw EPW bytes by plain column indexing; (2) criterion A % for the lounge of
the 01BA Safer_Heat run recomputed from the raw E+ harvest with a fresh TM52
Eq 2.2/2.3 running-mean chain, the 0.5 K rounding rule and the 1 989 h living
basis; (3) the displayed adaptive-comfort percentage recomputed from the same
series with the running mean re-derived through the library's documented
α = 0.8 7-day chain (renormalised α^k weights, 0.1 °C rounding — semantics
verified empirically against the wrapped utility) and the documented library
entry point `adaptive_en(…, limit_inputs=False)` for EN 16798-1 Category II
acceptability. Per RULE 4 the library is the calculator — the validator
re-derives every input from primary data and calls the same documented entry
point; it never reimplements library mathematics. Tolerances: exact for
counts, ±0.01 pp / ±0.1 pp for rounded values.
**Reference:** CIBSE definitions (packs SHA-pinned) + raw primary data.

### V14 — TM59:2026 and Part O boundary flips (L3)
**Method:** (a) TM59:2026 criterion a: living 59/60 h flip at the clamp threshold
25.1 °C (Trm 10 °C, 9 am–10 pm occupancy, night heat excluded); bedroom 110/111 h
flip (all hours); ΔT rounding 0.49 K counts 0 vs 0.50 K counts all; (b) criterion
b night counting: 4 hot nights PASS / 5 FAIL (Cat II Tn 27 °C, 23:00–08:00, mean
night temperature); (c) criterion d communal 28 °C fixed: 110/111 h flip;
**V14b** Part O dynamic inherits uk_tm59_2017 and applies the same boundaries
through its own engine (living 59/60 h flip verified through the Part O pack).
**Reference:** CIBSE TM59:2026 + ADO (packs SHA-pinned; Part O inherits TM59:2017
criteria by design, documented in its verification note).

### V15 — Served-numbers three-way integrity (L5)
**Method:** the series the API serves for an archived run (what every chart and
table plots, verbatim) must equal a fresh independent harvest of the E+ output
file on disk, zone by zone, value by value. Proves the numbers on screen are the
primary simulation output with nothing altered in between.
**Reference:** `data/runs/` archive + `eplusout.csv` + local API.

## 4. Verdict rules

| Verdict | Meaning |
|---|---|
| `PASS` | app value equals the reference within the stated tolerance |
| `CONFIRMED_DIRECTIONAL` | whole-model agreement where references use a different weather family or unrecorded metadata (V10, V11) |
| `INCOMPLETE` | required external artefact absent — reason recorded, nothing invented |
| `FAIL` | app disagrees with the reference — campaign verdict is FAIL |

## 5. Where the results live

| Artefact | Path |
|---|---|
| Method (this file) | `validation/METHOD.md` |
| Automated campaign | `validation/run_campaign.py` |
| Machine-readable results | `validation/results.json` (rewritten on every run, dated) |
| Human report | `validation/CAMPAIGN_REPORT.md` (rewritten on every run, dated) |
| In-app view | Validation page → “Independent validation campaign” (reads `results.json` via `GET /api/validation/campaign`) |

## 6. Mitigation energy-savings experiment (app feature, validated inputs)

The Mitigation Lab's energy table runs **real paired EnergyPlus simulations**
through the same validated pipeline: baseline IDF vs the author's stored
strategy variant (S2 restricted window opening / S3 night-purge ventilation),
same chosen EPW, same engine, same harvest. Savings are reported only from
facility meters present in the author's models (electricity, gas); strategies
without meters or without a stored variant report INCOMPLETE rather than an
invented number. This reuses V08/V09 guarantees (determinism + meter
consistency) for the pairing.
