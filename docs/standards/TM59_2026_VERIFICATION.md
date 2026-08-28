# TM59:2026 — Machine Verification Notes (2026-08-28)

**Artefacts** (held locally under `docs/standards/official_sources/`, git-ignored;
supplied by the author from CIBSE, © July 2026, for the sole use of the downloader —
linked, never redistributed):

| File | SHA-256 |
|---|---|
| `TM59_2026_methodology.pdf` (39 pp) | `7f97c2cceba0e736b9fc446a9f571fbb156367a7e458440f35e9ff45ce956a5a` |
| `TM59_2026_weather_file_requirements.pdf` (4 pp, ISBN 978-1-912034-12-3) | `c31d471de932ef1c11c34742d6a794c07d789c39d262581ef2a5576d243ad6ae` |
| `TM59_2026_compliance_checklist.pdf` | `78739e9dad9bd12ab6f2d764f54b011993f00c2e4df5dcf96a8205a66da0c304` |
| `ADO_2021_england.pdf` (verified in the previous session) | `36abadd39347d5d8a1c5fe0c021758efd8ecc09dc8f129393e47bcfa5edefab6` |

**Method:** AES-decrypted with an empty user password and text-extracted with pypdf in
the project venv; every value below was located verbatim in the extracted text and then
transcribed into `overheatlens/rules/uk_tm59_2026.yaml` (v1.0.0) with boundary tests
(`tests/test_standards_tm59_2026.py`) locking each number.

## Criterion a — §2.4.1 (predominantly naturally ventilated spaces)

- Applies to living rooms, kitchens, home offices **and bedrooms**; people awake.
- "the number of occupied hours for which ∆T is greater than or equal to one degree (K)
  between 1st May and 30th September inclusive shall not be more than 3% of the occupied
  hours during this period."
- **∆T rounding (TM52):** "for ∆T between 0.5 and 1.49, the value used is 1 K" → raw
  ∆T ≥ 0.5 K counts as exceedance.
- **Adaptive thresholds, Category II is +1 K over Category I; linear in Trm between
  Trm = 10 and 30 °C; fixed outside:**
  - Category I: 24.1 °C (Trm ≤ 10) → 30.7 °C (Trm ≥ 30) — slope 0.33 K/°C, offset 20.8.
  - Category II: 25.1 °C → 31.7 °C (offset 21.8).
- **Trm:** TM52 Eq 2.3 initial value for 30 April from the daily means of 23–29 April;
  then Eq 2.2 daily to 30 September. (Constants live in TM52 — flagged secondary inside
  criterion a until the TM52 PDF is held; implemented as 0.8-weighted 7-day initialiser
  and Trm(d) = 0.8·Trm(d−1) + 0.2·Tdm(d−1).)
- **Ceiling fans:** uplift ≤ **1.2 °C** when Top > 25 °C and air speed ≥ 0.6 m/s;
  ≈ 0.20 °C per 0.1 m/s below (BS EN 16798-1).
- **Limits (Table 2):** living/kitchen/home office occupied **9 am–10 pm** (13 h/day →
  **1989 h** May–Sep) → max **59 hours**. Bedrooms: occupied any time (**3672 h**) →
  max **110 hours**.

## Criterion b — §2.4.2 (bedrooms, hours of sleep)

- "the number of nights for which the mean operative temperature during hours of sleep
  exceeds Tn, between 1st May and 30th September inclusive shall not be more than four
  nights during this period."
- **Tn fixed:** **26 °C Category I; 27 °C Category II**. No ceiling-fan uplift permitted.
- **Hours of sleep = 11 pm to 8 am.** Night-of-day-N mean = 11 pm day N → 8 am day N+1;
  the 30 September night ends 8 am on 1 October.

## Criterion c — §2.4.3 (predominantly mechanically ventilated/cooled)

- "the room operative temperature shall not exceed 26 °C between 1st May and 30th
  September inclusive for more than 3% of occupied hours" — **fixed 26 °C**, both
  categories.
- Same hour limits as criterion a: **59 h** (living) / **110 h** (bedroom).
- **Ceiling fans:** uplift ≤ **2.1 °C** (Top > 25 °C, air speed ≥ 0.6 m/s); ≈ 0.35 °C
  per 0.1 m/s below (Guide A / AM10).

## Criterion d — §2.4.4 (communal circulation areas)

- "the operative temperature shall not exceed 28 °C between 1st May and 30th September
  for more than 3% of occupied hours" — **fixed 28 °C**, all categories and ventilation
  modes; occupied any time (**3672 h**) → max **110 hours**. No fan uplift.

## Stages — §2.5 / Figure 1

- **Stage 1:** no local ventilation-opening constraints; criteria **a + b**; results
  reported with AND without internal blinds and ceiling fans.
- **Stage 2:** constraints applied; **a + b** if openings can open ≥ 50% of occupied
  hours, otherwise **b + c**; enhanced mechanical ventilation allowed, no cooling.
- **Stage 3:** mechanical cooling introduced; criteria **b + c**.
- Communal areas must pass **criterion d at all stages** (multi-dwelling buildings).
- Overall pass = every habitable space in every sampled dwelling passes at Stage 1 AND,
  if applicable, Stage 2 or Stage 3.

## Weather file requirement — companion PDF §3 (S-08)

- "Overheating assessment should be undertaken using the latest version of the **DSY1**
  file appropriate to the site location for the **2050s, RCP8.5, 50th percentile**
  scenario. This file represents the minimum requirement."
- File label: **`{Zone Reference}_DSY1_2050s_HIGH50_CIBSE_v1.1`**.
- CIBSE 2025 Weather Data: baseline 1994–2023, UKCP18, CAMS solar, **28-zone** UK system;
  DSY1 = moderate (~7-year return period), DSY2 = most intense, DSY3 = longest events;
  alternatives (DSY2/3, other epochs/percentiles/scenarios) recommended for thorough
  assessments (§4).

## Negative findings

- TM59:2026 criteria a–d **replace** the 2017 criteria set; criterion b is nights-based
  (not hours-based as in 2017) and the sleep window is **11 pm–8 am** (not 22:00–07:00).
- Nothing in the 2026 text claims Part O compliance equivalence; the ADO 2021 statutory
  route remains anchored to TM59:2017 (see `ADO_VERIFICATION.md`) — the two modes stay
  strictly separate in OverheatLens (master-prompt RULE 2).

## Still pending (S-02, S-04)

- **TM59:2017** and **TM52** PDFs were NOT found on this machine (`~/PhD/Literature_Review/Papers`
  is empty). Their rule packs remain `secondary_pending` and compliance-gated. The TM52
  equation constants used inside criterion a's Trm chain are flagged accordingly.
