# TM59:2017 + TM52 — Machine Verification Notes (2026-08-28)

**Artefacts** (held locally under `docs/standards/official_sources/`, git-ignored;
author-supplied from CIBSE — linked, never redistributed):

| File | SHA-256 |
|---|---|
| `TM59_2017_methodology.pdf` (18 pp, *Design methodology for the assessment of overheating risk in homes*) | `9f223d2d8aaeb19506612aada52327bd2512911703cfd7db414277fd86cd4de7` |
| `TM52_2013_limits_of_thermal_comfort.pdf` (24 pp, ISBN 978-1-906846-34-3) | `526e822d751c6bbcaba4cac09707bdba40204521de6cafa309e2bc25e095664d` |

**Method:** OneDrive placeholders materialised by read (several files were 0-byte
cloud stubs); pypdf text extraction; every value below located verbatim and transcribed
into `overheatlens/rules/uk_tm59_2017.yaml` and `uk_tm52.yaml` (both v1.0.0) with
boundary tests locking each number.

## TM59:2017 §4.2 — criteria for homes predominantly naturally ventilated

Verbatim (§4.2):

> "(a) For living rooms, kitchens and bedrooms: the number of hours during which DT is
> greater than or equal to one degree (K) during the period May to September inclusive
> shall not be more than 3 per cent of occupied hours. (CIBSE TM52 Criterion 1: Hours
> of exceedance).
>
> (b) For bedrooms only: to guarantee comfort during the sleeping hours the operative
> temperature in the bedroom from 10 pm to 7 am shall not exceed 26 °C for more than 1%
> of annual hours. (Note: 1% of the annual hours between 22:00 and 07:00 for bedrooms
> is 32 hours, so 33 or more hours above 26 °C will be recorded as a fail)."

- Criterion (a) is **adaptive** — DT is TM52's DT = Top − Tmax (TM52 Eq 9, Tmax Eq 8),
  with TM52's nearest-whole-degree rounding (0.5–1.5 → 1 K).
- **Criterion (b)'s limit is fixed by the document at 32 hours** (the operationalisation
  of 1% of the 3285 annual sleep-window hours). There is NO separate 32-hour "criterion
  C" — the previous secondary transcription was wrong on this point and was corrected.
- Occupied-hours bases (§6, verbatim): "**3672 hours per year for bedrooms (24/7 for
  the May–September dates covered) and 1989 hours per year for living rooms (13 hours
  per day for 153 days May–September)**".
- §4.4: vulnerable occupants use the same criteria with **TM52 Type I** (Category I).
- §2.3: Cat II by default; **Cat III NOT permitted** for this methodology.

## TM59:2017 §4.3 — predominantly mechanically ventilated homes

> "all occupied rooms should not exceed an operative temperature of 26 ˚C for more than
> 3% of the annual occupied annual hours (CIBSE Guide A (2015a))".

Implemented as criterion `mv` with a model-supplied occupied-hours denominator
(explicit NOT_EVALUATED when occupancy data is absent).

## TM59:2017 §4.5 — corridors

> "Whilst there is no mandatory target, if an operative temperature of 28 °C is
> exceeded for more than 3% of the total annual hours, this should be flagged as a
> significant risk within the report."

Implemented as an ADVISORY criterion (status FLAG/NO_FLAG; never pass/fail).

## TM59:2017 §3.2 / §2.3(11) — weather file requirement (verified)

> "the weather file used for the methodology should be the DSY1 (design summer year)
> file most appropriate to the site location, for the 2020s, high emissions, 50%
> percentile scenario" — i.e. the CIBSE 2016-release DSY1_2020High50 file
> (e.g. `Leeds_DSY1_2020High50_.epw`, validated locally — see VALIDATION_MATRIX
> VAL-REAL-04). More extreme DSY2/DSY3 and future-epoch files are for further testing
> of designs of particular concern.

## TM59:2017 §3.3 — window opening (verified)

Windows controlled separately per room, "modelled as open when both the internal dry
bulb temperature exceeds 22 °C and the room is occupied". (ADO §2.6 overrides this for
Part O submissions — PO-OVR-01.)

## TM52 (2013) — verified values

- **Eq 2.1/2.2**: Trm = (1−α)·Tod−1 + α·Trm−1, α = 0.8.
- **Eq 2.3** (7-day initialiser): Trm = (Tod−1 + 0.8·Tod−2 + 0.6·Tod−3 + 0.5·Tod−4 +
  0.4·Tod−5 + 0.3·Tod−6 + 0.2·Tod−7) / **3.8** — the published weights are
  (1, 0.8, 0.6, 0.5, 0.4, 0.3, 0.2)/3.8, NOT normalised 0.8^k (implementation
  corrected accordingly).
- **Eq 6**: Tcomf = 0.33·Trm + 18.8; the threshold used by the criteria is the
  **Category II upper limit Tmax = Tcomf + 2 = 0.33·Trm + 21.8** (Eq 8); Category I is
  1 K less (0.33·Trm + 20.8). Clamped outside Trm 10–30 → Cat II 25.1–31.7 °C,
  Cat I 24.1–30.7 °C (consistent with TM59:2026's categories).
- **Eq 9**: DT = Top − Tmax, rounded to the nearest whole degree ("for DT between 0.5
  and 1.5 the value used is 1 K").
- **Criterion 1 (He)**: hours with DT ≥ 1 K (raw ≥ 0.5) during 1 May–30 September
  occupied hours ≤ 3% of occupied hours.
- **Criterion 2 (We)** (Eq 10): We = Σ(hey × wf) ≤ 6 in any one day; wf = 0 if DT ≤ 0,
  else wf = DT (rounded). Worked example verified (half-hour readings, We = 5).
- **Criterion 3 (Tupp)**: "the value of DT shall not exceed 4 K" (raw, unrounded).
- §6.1.2: a room is classed as overheating if **any two** of the three criteria fail.

## Impact on the codebase (RULE 7 discipline)

The earlier `secondary_pending` transcription (0.1.0-dev packs) was **wrong** on four
load-bearing points and has been corrected, with the correction documented here:

1. Criterion (a) was implemented as a fixed 26 °C/3%-of-8760 h test → is **adaptive,
   May–September, 3% of occupied hours**.
2. Criterion (b) used 1% of 8760 h (87.6 h) → limit is **32 hours** (document-fixed).
3. A separate "criterion C" (32 h) existed in the old pack → **removed** (it
   duplicated criterion b; TM59:2017 has criteria (a) and (b) only).
4. Corridors delegated to TM52 → are actually an **advisory 28 °C flag** (§4.5), and
   the mechanical-ventilation route (§4.3) was missing entirely — now criterion `mv`.

The boundary tests were rewritten to the verified values; the old tests failed as
expected and were replaced (never weakened).
