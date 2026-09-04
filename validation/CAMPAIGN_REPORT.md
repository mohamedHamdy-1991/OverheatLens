# OverheatLens — Validation Campaign Report

Run: 2026-09-04T18:43:12+00:00 → 2026-09-04T18:51:25+00:00  ·  Campaign verdict: **PASS**  ·  12 PASS/CONFIRMED · 0 INCOMPLETE · 0 FAIL

Method: see `validation/METHOD.md` (the full method document).

| Case | Layer | Verdict | What it proves |
|---|---|---|---|
| V01 — Rule packs machine-verified to official PDFs | L1 | **PASS** | SOURCE_REGISTER.md; docs/standards/*_VERIFICATION.md |
| V02 — EPW parser & QC on real research weather | L4 | **PASS** | CIBSE/Met Office DSY format; Leeds DSY1 2020-high climate envelope |
| V03 — TM59:2017 verdict flips at published boundaries | L3 | **PASS** | CIBSE TM59:2017 §5.2 (pack SHA-pinned, adaptive criteria + 32 h rule) |
| V04 — TM52 published worked example + rounding boundaries | L2/L3 | **PASS** | CIBSE TM52-2013 §6.1.1–§6.1.3 (pack SHA-pinned) |
| V05 — PMV/PPD matches published ISO 7730 anchors | L2 | **PASS** | ISO 7730 PPD relation 100-95*exp(-0.03353*PMV^4-0.2179*PMV^2); anchor table PPD(0)=5%, (±0.5)≈10%, (±1)≈25%, (±2)≈75% |
| V06 — UTCI reproduces published reference-condition agreement | L2 | **PASS** | Bröde et al. 2012, Int J Biometeorol 56:481–494 (reference conditions) |
| V07 — Adaptive limits match published formulae (TM52 Eq 8 / EN 16798-1) | L2 | **PASS** | CIBSE TM52-2013 Eq 8 (pack SHA-pinned); EN 16798-1 via pythermalcomfort |
| V08 — EnergyPlus determinism (two identical runs) | L5 | **PASS** | EnergyPlus 25.1.0 official binary; app runner (isolated dirs) |
| V09 — Energy meter internal consistency | L5 | **PASS** | EnergyPlus meter output (eplusmeter.csv via --readvars); monthly sums vs runperiod total ≤ 0.5 % |
| V10 — Cross-check vs author's DesignBuilder PhD exports | L4 | **CONFIRMED_DIRECTIONAL** | Safer_Heat_Harehills DesignBuilder TM59 exports (author's PhD data) |
| V11 — CIBSE TM59 Example 4 flat vs published outcome | L4 | **CONFIRMED_DIRECTIONAL** | CIBSE TM59:2017 worked example (pack SHA-pinned) |
| V12 — DesignBuilder 01BA baseline cross-check | L4 | **CONFIRMED** | Safer_Heat_Harehills '01BA__Baseline (TM59).csv' (author PhD data) |

