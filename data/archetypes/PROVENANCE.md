# 01_MODELS — Archetype IDF Provenance Register
**Chapter 6 — TM59 Overheating Risk Assessment**
**Created:** 2026-07-21
**Author of register:** Claude agent, on behalf of Mohamed Hamdy Mohamed Ali (Leeds Beckett University)

---

## ✅ AUTHORIZATION STATUS: SUPERSEDED (reuse executed — see below)

> Phase-0.1 pending banner retained for history. Reuse of the five IDFs for Chapter 6 was
> subsequently authorised and executed; the campaign results derived from these models are
> reported in Chapter 6 §6.2–§6.7 with the attribution wording of §6.1.1. (Verified 2026-08-21.)

The five IDF files copied into this folder are **non-destructive re-run copies** of archetypes
originally built for the adjacent **Sensor-Calibrated** publication (Mohamed Ali, PhD programme).
They are placed here so that Chapter 6 can re-run them against Chapter 6's *own* weather-file
matrix and produce chapter-6-attributed results. They are **NOT** to be cited as Chapter 6
findings until Mohamed Hamdy Mohamed Ali explicitly authorises:

1. **Reuse** of the five IDFs for the dissertation (Chapter 6);
2. **Attribution wording** in §6.1 and the thesis Methods/Contributions statement;
3. Confirmation that the Sensor-Calibrated `TM59_Results_Summary.csv`,
   `TM59_Stock_Weighted.csv`, and `TM59_Deltas_vs_baseline.csv` must **NOT** be cited as
   Chapter 6 findings (the weather-file matrix differs, so Chapter 6's numbers will differ).

No simulation has been executed from this folder. Reuse is pending sign-off; the copies
themselves are reversible (delete the folder if reuse is declined).

---

## 1. Archetype register

| # | Code | Source filename | Original programme | Floor area / form | Era / type | Size (bytes) | SHA-256 (this copy) | Source SHA-256 (verified identical) |
|---|------|-----------------|--------------------|-------------------|------------|--------------|---------------------|-------------------------------------|
| 1 | `01BA` | `01BA_end_terrace.idf` | DEEP / Harehills | End-terrace house | 1930s semi-traditional | 764,785 | `bd38a7c64cd1e7f0e4838dfa2ba7ea75885304e5c874c978e7771aee7636e895` | identical |
| 2 | `17BG` | `17BG_back_to_back_end.idf` | DEEP / Harehills | Back-to-back END | ~1890 back-to-back | 721,575 | `6eb2a6aa3418813d2c0459e56d540f66f9c99b7a346eb1c371ab6fe7ce036d69` | identical |
| 3 | `27BG` | `27BG_back_to_back_mid.idf` | DEEP / Harehills | Back-to-back MID | ~1890 back-to-back | 743,184 | `63113233d8ff56a560a1b083378a94c357ed3f1dda968dd914e297ab20c453f8` | identical |
| 4 | `52NP` | `52NP_mid_terrace_EWI.idf` | DEEP / Harehills | Mid-terrace + EWI | Retrofit mid-terrace | 1,190,796 | `8a894c421166e0430777907185aa019c79218ecc1a41c8987cf1f366bac31d10` | identical |
| 5 | `Flat` | `Flat_TM59Example4.idf` | CIBSE TM59 Example 4 | Mid-floor 2-bed flat | Part L 2021 new-build reference | 13,539 | `7b6ea3a1510105c8f07cbdb4a8a95076c20ed9336c10462ce74530c1736138c3` | identical |

The four DEEP/Harehills archetypes (`01BA`, `17BG`, `27BG`, `52NP`) are **real, measured
dwellings** from the DEEP case-study programme, modelled by Mohamed Ali in DesignBuilder and
exported to EnergyPlus IDF. The fifth (`Flat_TM59Example4`) is CIBSE TM59's own published
standard reference flat (TM59 §6.4 Example 4) — included for comparability with the wider TM59
literature and Part O new-build context. It is a published reference case, not proprietary.

## 2. Exact source location (where copied FROM)

```
/Users/mohamedali/Library/CloudStorage/OneDrive-LeedsBeckettUniversity/Work/Ph.D/
  Publications/Sensor-Calibrated/publication_workflow/07_ANALYSIS/14_tm59_outputs/
    VALIDATION_PACKAGE/IDF_Files/
      01BA_end_terrace.idf
      17BG_back_to_back_end.idf
      27BG_back_to_back_mid.idf
      52NP_mid_terrace_EWI.idf
      Flat_TM59Example4.idf
```
Source file modification timestamp (all five): **2026-07-08 18:12** (OneDrive attribute).

## 3. Authoritative methodology / validation source (do NOT cite stale numbers)

The companion folder also contains `VALIDATION_RESULTS_FINAL.md` — **this file is stale and
disowned**. The Sensor-Calibrated `README_VALIDATION.md` and the manuscript's §7.5.1
explicitly reverse its MBE/R² figures (those required an hourly DesignBuilder export that did
not exist when they were computed; they have been "removed and flagged as unverified").

For Chapter 6's QC documentation, the **authoritative precedent thresholds** (ASHRAE
Guideline 14 style, as actually applied in the Sensor-Calibrated manuscript §7.5.1) are:

- MBE ≤ 0.5 °C  (against an independent DesignBuilder export)
- CVRMSE ≤ 10 %
- R² ≥ 0.95

Reported *achieved* outcome (Sensor-Calibrated §7.5.1, for transparency — **not** a Chapter 6
result): CVRMSE passed for all four measured archetypes (4.1–6.4 %); MBE/R² passed only for
`27BG` (MBE −0.36 °C, R² = 0.939); `01BA`, `17BG`, `52NP` exceeded thresholds partly due to an
EnergyPlus version mismatch (25.1.0 vs DesignBuilder's embedded 23.1.0). **Pin and record
Chapter 6's own EnergyPlus version explicitly in every run log (QC gate 9)** to avoid repeating
this.

## 4. What is new vs adapted for Chapter 6

| Element | Status | Note |
|---|---|---|
| Archetype geometry / fabric / schedules | **Adapted** (copied, to be re-attributed, re-run) | Source: 5 IDFs above |
| Weather files driving the runs | **New** (Chapter 6's own matrix) | CH5's 6 DSY1 EPWs + `Leeds_DSY1.epw` rural baseline + `Leeds_DSY3.epw` (DSY3 method pending Phase 0.2) |
| Run scripts | **New, chapter-6-attributed** | Adapted from `run_simulations.py` / `Run_Scripts/*.py` pattern, written fresh into `03_SCRIPTS/` |
| QC / validation harness | **Adapted thresholds, re-run** against Chapter 6 weather files | Pattern from `analyse_tm59_results.py` / `validate_db_vs_script.py` |
| Composite Overheating Risk Index (6.6) | **New — no project precedent exists** | See FABLE5 workflow §4.5 |
| Ventilation sensitivity design (6.5) | **New** | Informed by Harehills variant *naming* as design analogue only |

## 5. Differentiation statement (why Chapter 6 is not a Sensor-Calibrated re-run)

Chapter 6's §6.1 must state explicitly why this chapter is deliberately distinct from the
adjacent Sensor-Calibrated publication's RQ4 ("does replacing the airport DSY with an
urban-corrected file change the TM59 outcome for these same 5 archetypes?"):

1. **CH6 uses CH5's own CENTRE / INNER zones × 3 uncertainty members** (dissertation-native
   empirical sensor-correction method) — *not* Sensor-Calibrated's LCZ / distance-band morphing
   route.
2. **CH6 adds DSY3 resilience (§6.4)** — Sensor-Calibrated never ran DSY3.
3. **CH6 adds a designed ventilation-behaviour sensitivity study (§6.5)** — no precedent exists
   anywhere in the project.
4. **CH6 adds a Composite Overheating Risk Index (§6.6)** — no precedent exists.

State this explicitly in §6.1 so the chapter reads as deliberately distinct,
dissertation-scoped work.

## 6. Escalation items this register depends on (from FABLE5 workflow Phase 0)

- **0.1** Authorise reuse of the 5 IDFs + attribution wording — *authorship judgement.*
- **0.4** Confirm EnergyPlus / DesignBuilder version and licence on Mohamed's machine; confirm
  scripted CLI as primary method (this sandbox cannot run either tool).

Record resolution in `00_ADMIN/DECISION_LOG.md` and remove the PENDING banner above once signed off.

## 7. Scenario-variant library stored with the app (2026-09-04)

The author's complete CH6 model set — `CH6 OVERHEATING RISK ASSESSMENT/01_MODELS` —
is now stored inside the app at `data/archetypes/idf/`:

- **15 base models** (flat in `idf/`) — byte-identical to the CH6 masters (SHA-256 verified 2026-09-04).
- **30 scenario variants** (in `idf/variants/`) — `*_S2_restricted` (restricted window
  opening) and `*_S3_nightpurge` (night-purge ventilation) for each base model,
  authored for the Chapter 6 ventilation-behaviour sensitivity study (§6.5).
  Registered in `provenance.json` under the `variants` key (code, parent model,
  scenario, SHA-256, zone count). They are **not** listed by `/api/models` and are
  **not** in the audit regression scope: no EnergyPlus run has been recorded for
  them (`run_status: NOT_RUN`) — promotion into the assessable set is an explicit
  author decision.

  **Physics note (found 2026-09-04):** the variant exports for the four measured
  DEEP dwellings (01BA, 17BG, 27BG, 52NP) define the scenario
  `Schedule:Compact` but **no object in the IDF references it** — the active
  variant physics lives in the DesignBuilder study, and simulations of these
  exports are correctly identical to their baselines. The app detects this
  (schedule referenced only by its own definition) and reports the energy
  comparison as INCOMPLETE rather than claiming zero savings. The remaining
  eleven models' variant exports do reference their schedules.


**Weather files are never stored with the app.** Validation runs read the author's
external Leeds MET Office folder (`OVERHEATLENS_WEATHER_DIR`); no `.epw` file exists
under `data/`.
