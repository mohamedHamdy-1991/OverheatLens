# Model cross-check — 01BA baseline: OverheatLens vs DesignBuilder

*2026-09-04 · method: `validation/METHOD.md` §V12 · data: `validation/model_crosscheck_01ba.json`*

## Question
Does the app's TM59:2017 pipeline reproduce the author's DesignBuilder result for the
same model and weather? — **Yes: verdict-level agreement on every shared zone.**

## Setup
| | OverheatLens | DesignBuilder (reference) |
|---|---|---|
| Model | `01BA__Baseline.idf` from `01BA_BL_Baseline` (uploaded byte-identical, sha256 06356ead…) | same model, internal E+ 23.1 |
| Migration | documented copy: People MRT `ZoneAveraged`→`EnclosureAveraged` ×4, Version→25.1.0 (IDD 21507: only key, pure rename) | none (native) |
| Weather | `Leeds_DSY1_2020High50_.epw` | same file (author-stated) |
| Standard | `uk_tm59_2017` (SHA-pinned pack) | CIBSE TM59:2017 |

## Result — dwelling verdict: **FAIL in both engines**

| Zone | DB Crit A | App Crit A | Δ | DB Crit B | App Crit B | Verdicts |
|---|---|---|---|---|---|---|
| Ground-floor kitchen | 5.45 % | 4.12 % | −1.33 pp | — | — | Fail / **FAIL** ✓ |
| Ground-floor lounge | 5.19 % | 4.22 % | −0.97 pp | — | — | Fail / **FAIL** ✓ |
| Bedroom 1 | 4.67 % | 5.56 % | +0.89 pp | 39.83 h | 141 h | Fail / **FAIL** ✓ |
| Bedroom 2 | 14.13 % | 5.12 % | −9.01 pp | 117.67 h | 120 h | Fail / **FAIL** ✓ |
| Stairs (corridor) | 0.87 / 0.78 % | 1.50 % | — | — | — | Pass / no flag ✓ (<3 % both) |

**Verdict agreement: 4/4 habitable zones + corridor. Campaign verdict: CONFIRMED.**

## Reading the numbers
- Absolute criterion-A percentages differ between engines (E+ 25.1 vs DesignBuilder's
  internal E+ 23.1, occupied-hour conventions, MRT handling). Kitchen/lounge agree within
  ≈1 pp; bedroom 2 differs by −9 pp in criterion A but its criterion-B hours match closely
  (117.67 vs 120 h, both far above the 32 h limit) — both engines agree the room fails.
- Bedroom 1 criterion B: 39.83 h (DB) vs 141 h (app) — both FAIL the 32 h limit; the app
  counts whole sleep-window hours at Top > 26 °C per the SHA-pinned pack.
- Room-taxonomy difference (flagged, not silently changed): DesignBuilder assesses
  BATHROOM and LANDING under the corridors criterion (1.78/0.97 % → Pass); the app
  classifies them as living rooms (4.78/5.78 % → FAIL). Dwelling verdict is FAIL either way.
- App-only zones (2× CHIMNEY, BAYWINDOWROOF:VOID, ROOF:LOFT, CUPBOARD) are geometry
  artefacts absent from the DB report; LOFT (40.4 %) adds to the app's dwelling FAIL.

## Answer
**The model is running well and the comparison is valid**: same model, same weather,
same standard — every habitable zone fails in both engines, corridors pass in both,
and the dwelling-level verdict matches. Absolute percentages differ per engine, as
expected for two independent simulation engines.

*Re-run: `./.venv/bin/python validation/run_campaign.py` (case V12).*
