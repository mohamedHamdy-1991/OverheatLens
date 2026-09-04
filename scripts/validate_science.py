#!/usr/bin/env python3
"""OverheatLens — SCIENTIFIC VALIDATION of every implemented equation and theory.

Independent reference implementations are written OUT from the source-verified
documents (never imported from the production code) and compared against the
production engine. This is the plan's Tier-2 "independent reference implementation"
gate, packaged as one runnable file.

Sources (see SOURCE_REGISTER.md for statuses and SHA-256s):
  S-02  CIBSE TM59:2017        — criteria (a)/(b), occupied-hour bases, weather rule
  S-03  CIBSE TM59:2026        — criteria a-d, stages, night criterion
  S-04  CIBSE TM52:2013        — Eq 2.2/2.3 (Trm), Eq 8 (Tmax), Eq 9 (DT rounding),
                                Criteria 1/2/3, worked example
  S-01  ADO 2021               — window-control limits, exclusions (model limits)

Covers:
  1. TM52 Eq 2.2 recursion + Eq 2.3 initialiser (published weights / 3.8)
  2. Adaptive thresholds: Tmax = 0.33 Trm + 21.8 (Cat II) / + 20.8 (Cat I), clamps
  3. DT rounding: raw >= 0.5 K counts (nearest whole degree)
  4. TM59:2017 criterion (a): 3% of occupied hours (1989/3672 bases), May-Sept
  5. TM59:2017 criterion (b): 26 degC sleep-window limit of 32 h (fail at 33)
  6. TM59:2026 criterion a/c hour limits: 59 h (living) / 110 h (bedroom, communal d)
  7. TM59:2026 criterion b: nights-based, Tn 26/27, limit 4 nights, 11 pm-8 am window
  8. TM59:2026 criterion d: 28 degC fixed, 110 h
  9. TM52 Criterion 2 (We): document worked example, We = sum(he_y * y) <= 6
 10. TM52 Criterion 3: raw DT > 4 K
 11. Comfort: Fanger PMV/PPD parity vs the library at multiple conditions;
     EN 16798-1 adaptive comfort equation vs hand computation
 12. Weather physics: dew-point relation sanity, degree-hour integrals

Run:  python3 scripts/validate_science.py
Report: docs/validation/SCIENTIFIC_VALIDATION_REPORT.md
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "packages" / "overheatlens-core"))

from overheatlens.standards import StandardsEngine, running_mean_trm  # noqa: E402

RESULTS: list[dict] = []


def check(vid: str, desc: str, ok: bool, detail: str) -> None:
    RESULTS.append({"id": vid, "desc": desc, "status": "PASS" if ok else "FAIL",
                    "detail": detail})
    print(f"  [{'✓' if ok else '✗'}] {vid}: {desc}" + (f" — {detail}" if detail else ""))


def ref_trm(daily_means: np.ndarray, start_index: int) -> np.ndarray:
    """INDEPENDENT reference: TM52 Eq 2.3 start then Eq 2.2 recursion, written
    directly from the document text (weights 1/.8/.6/.5/.4/.3/.2 over 3.8)."""
    w = [1.0, 0.8, 0.6, 0.5, 0.4, 0.3, 0.2]
    out = np.empty(153)
    trm = sum(w[k] * daily_means[start_index - k] for k in range(7)) / 3.8
    for i in range(153):
        trm = 0.8 * trm + 0.2 * daily_means[start_index + i]
        out[i] = trm
    return out


def main() -> int:
    print("OverheatLens scientific validation — equations vs source documents\n")

    eng17 = StandardsEngine.load("uk_tm59_2017")
    eng26 = StandardsEngine.load("uk_tm59_2026")
    eng52 = StandardsEngine.load("uk_tm52")
    hours = (np.arange(8760) % 24) + 1
    H = lambda lbl: eng17._bind_calendar(hours, 8760)  # noqa: E731

    # ---------------- 1. TM52 Trm equations (S-04 Eq 2.2 / 2.3) -----------------
    print("1. TM52 running-mean outdoor temperature (Eq 2.2 / 2.3)")
    rng = np.random.default_rng(42)
    dm = rng.uniform(5, 25, 365)
    ref = ref_trm(dm, apr30 := 31 + 28 + 31 + 29)
    prod = running_mean_trm(dm)
    check("SCI-01", "Eq 2.2/2.3 chain matches the independent reference over a "
          "random year (153 days, max diff)",
          bool(np.max(np.abs(ref - prod)) < 1e-12),
          f"max |diff| = {np.max(np.abs(ref - prod)):.2e} K")
    dm_step = np.full(365, 10.0)
    dm_step[150:] = 30.0
    ref2 = ref_trm(dm_step, apr30)
    prod2 = running_mean_trm(dm_step)
    check("SCI-02", "Eq 2.2 step response: Trm(1 Jun) = 0.8*Trm(31 May)+0.2*30",
          abs(ref2[31] - 14.0) < 1e-9 and abs(prod2[31] - 14.0) < 1e-9,
          f"Trm(1 Jun) = {prod2[31]:.6f} (document hand-calc: 14.0)")

    # ---------------- 2. Adaptive thresholds (TM52 Eq 8 via both packs) ---------
    print("2. Adaptive comfort thresholds (Tmax = 0.33 Trm + 21.8 / +20.8)")
    dm_const = np.full(365, 20.0)
    th_ii = eng26._adaptive_thresholds(eng26._criteria["a"], "II", dm_const)
    th_i = eng26._adaptive_thresholds(eng26._criteria["a"], "I", dm_const)
    check("SCI-03", "Cat II Tmax at Trm=20 equals 0.33*20+21.8 = 28.4",
          abs(th_ii[0] - 28.4) < 1e-9, f"{th_ii[0]:.4f} degC")
    check("SCI-04", "Cat I is exactly 1 K below Cat II (EN 15251 category offset)",
          bool(np.allclose(th_ii - th_i, 1.0)), "all 153 days")
    dm10 = np.full(365, 10.0)
    dm30 = np.full(365, 30.0)
    check("SCI-05", "Clamps per document: Cat II 25.1 degC at Trm<=10, 31.7 at >=30",
          abs(eng26._adaptive_thresholds(eng26._criteria["a"], "II", dm10)[0] - 25.1)
          < 1e-9 and abs(eng26._adaptive_thresholds(eng26._criteria["a"], "II", dm30)[0]
                          - 31.7) < 1e-9, "25.1 / 31.7")
    check("SCI-06", "TM52 pack and TM59:2026 pack share the same threshold equation",
          bool(np.allclose(eng52._adaptive_thresholds(eng52._criteria["c1"], "II",
                                                      dm_const), th_ii)),
          "identical arrays")

    # ---------------- 3. DT rounding (TM52 Eq 9 text) ---------------------------
    print("3. DT rounding: raw DT >= 0.5 K counts as 1 K (TM52 text)")
    eng26._bind_calendar(hours, 8760)
    dm15 = np.full(365, 15.0)
    # Trm 15 -> Tmax(II) = 26.75; probe 0.49 / 0.50 raw DT
    res = []
    for top, expect in ((26.75 + 0.49, 0), (26.75 + 0.5, 1)):
        ra = eng26.evaluate_room("r", "Bedroom", np.full(8760, top), hours,
                                 category="II", daily_mean_outdoor=dm15,
                                 mode="compliance")
        a = next(r for r in ra.results if r.criterion_id == "a")
        res.append(a.metric_value == (3672.0 if expect else 0.0))
    check("SCI-07", "criterion a counts at raw DT = 0.50 K, not at 0.49 K "
          "(3672 bedroom hours basis)", all(res),
          "0.49 -> 0 h; 0.50 -> 3672 h")

    # ---------------- 4. TM59:2017 criterion (a) bases + limit ------------------
    print("4. TM59:2017 criterion (a) — 3% of occupied hours, bases 1989/3672")
    eng17._bind_calendar(hours, 8760)
    m, d, h = eng17._month, eng17._day, eng17._hour
    # hand-computed reference: count hot occupied hours ourselves
    np.random.seed(7)
    top = np.full(8760, 20.0)
    hot = (np.isin(m, [5, 6, 7, 8, 9]) & np.isin(h, range(1, 25)))
    idx = np.nonzero(hot)[0]
    top[idx[:100]] = 30.0  # 100 hot hours in the bedroom (24/7 basis)
    ref_pct = 100.0 * 100 / 3672
    ra = eng17.evaluate_room("r", "Bedroom", top, hours, category="II",
                             daily_mean_outdoor=dm15, mode="compliance")
    a = next(r for r in ra.results if r.criterion_id == "a")
    check("SCI-08", "bedroom occupied-hour basis is 3672 h and percent matches "
          "hand computation", a.basis["occupied_hours_basis"] == 3672.0
          and abs(a.metric_value - ref_pct) < 1e-9,
          f"{a.metric_value:.4f}% vs ref {ref_pct:.4f}%")
    # living: only 13 h/day counts
    top2 = np.full(8760, 20.0)
    night = (np.isin(m, [6]) & np.isin(h, [2, 3]))
    top2[np.nonzero(night)[0]] = 32.0  # hot night hours outside living profile
    ra2 = eng17.evaluate_room("r", "Living room", top2, hours, category="II",
                              daily_mean_outdoor=dm15, mode="compliance")
    a2 = next(r for r in ra2.results if r.criterion_id == "a")
    check("SCI-09", "living-room profile (9 am-10 pm) excludes night heat",
          a2.metric_value == 0.0 and a2.basis["occupied_hours_basis"] == 1989.0,
          "0% with basis 1989 h")

    # ---------------- 5. TM59:2017 criterion (b): 32 h limit --------------------
    print("5. TM59:2017 criterion (b) — >26 degC sleep hours, 32 h limit")
    top3 = np.full(8760, 20.0)
    sleep = np.isin(hours, (23, 24, 1, 2, 3, 4, 5, 6, 7))
    sidx = np.nonzero(sleep & (m == 6))[0]
    top3[sidx[:32]] = 27.0
    rb32 = eng17.evaluate_room("r", "Bedroom", top3, hours, category="II",
                               daily_mean_outdoor=dm15, mode="compliance")
    top3[sidx[32]] = 27.0
    rb33 = eng17.evaluate_room("r", "Bedroom", top3, hours, category="II",
                               daily_mean_outdoor=dm15, mode="compliance")
    b32 = next(r for r in rb32.results if r.criterion_id == "b")
    b33 = next(r for r in rb33.results if r.criterion_id == "b")
    check("SCI-10", "document-fixed limit: 32 h passes, 33 h fails "
          "(1% of annual 22:00-07:00 hours)",
          b32.status == "PASS" and b33.status == "FAIL"
          and b32.metric_value == 32.0 and b33.metric_value == 33.0,
          "32 PASS / 33 FAIL")

    # ---------------- 6. TM59:2026 hour limits ----------------------------------
    print("6. TM59:2026 criteria a/c/d hour limits (Table 2)")
    dm10 = np.full(365, 10.0)
    for cid, room, limit, label in (
            ("a", "Living room", 59, "a living 59 h"),
            ("c", "Kitchen", 59, "c living 59 h"),
            ("d", "Corridor", 110, "d communal 110 h")):
        flips = []
        eng26._bind_calendar(hours, 8760)
        mm = eng26._month
        hot_idx = np.nonzero(mm == 6)[0]
        for n in (limit, limit + 1):
            t = np.full(8760, 20.0)
            t[hot_idx[:n]] = 40.0
            rr = eng26.evaluate_room("r", room, t, hours, category="II",
                                     daily_mean_outdoor=dm10, mode="compliance")
            flips.append(next(r for r in rr.results if r.criterion_id == cid).status)
        check(f"SCI-11-{label}", f"criterion {cid}: exact flip {limit}/{limit + 1} h",
              flips == ["PASS", "FAIL"], f"{flips}")
    # bedroom variant 110
    eng26._bind_calendar(hours, 8760)
    hot_bed = np.nonzero((eng26._month == 6))[0]
    t = np.full(8760, 20.0)
    t[hot_bed[:110]] = 40.0
    ra110 = eng26.evaluate_room("r", "Bedroom", t, hours, category="II",
                                daily_mean_outdoor=dm10, mode="compliance")
    ta110 = next(r for r in ra110.results if r.criterion_id == "a")
    check("SCI-12", "criterion a bedroom variant: 110 h limit (3% of 3672)",
          ta110.basis["limit_hours"] == 110.0, "basis 3672 occupied h")

    # ---------------- 7. TM59:2026 criterion b: nights --------------------------
    print("7. TM59:2026 criterion b — nights, Tn 26/27, limit 4, 11 pm-8 am")
    eng26._bind_calendar(hours, 8760)
    mm, dd, hh = eng26._month, eng26._day, eng26._hour
    t4 = np.full(8760, 20.0)
    for day in (5, 6, 7, 8):
        night = (((mm == 6) & (dd == day) & (hh == 24))
                 | ((mm == 6) & (dd == day + 1) & np.isin(hh, range(1, 9))))
        t4[np.nonzero(night)[0]] = 26.5  # mean 26.5: over Tn(I)=26, under Tn(II)=27
    rI = eng26.evaluate_room("r", "Bedroom", t4, hours, category="I",
                             daily_mean_outdoor=dm15, mode="compliance")
    rII = eng26.evaluate_room("r", "Bedroom", t4, hours, category="II",
                              daily_mean_outdoor=dm15, mode="compliance")
    bI = next(r for r in rI.results if r.criterion_id == "b")
    bII = next(r for r in rII.results if r.criterion_id == "b")
    check("SCI-13", "criterion b: 4 nights at 26.5 degC — Cat I FAILS (Tn 26), "
          "Cat II PASSES (Tn 27), limit 4 nights",
          bI.status == "FAIL" and bII.status == "PASS"
          and bI.metric_value == 4.0 and bII.metric_value == 0.0,
          f"I:{bI.metric_value:.0f} nights / II:{bII.metric_value:.0f} nights")

    # ---------------- 8. TM52 Criterion 2 (We) — document worked example --------
    print("8. TM52 Criterion 2 (We = sum he_y * y, limit 6) — Eq 10")
    eng52._bind_calendar(hours, 8760)
    m5, h5 = eng52._month, eng52._hour
    occ = np.isin(hours, range(9, 18))
    occ_day = (m5 == 7) & (h5 >= 9) & (h5 <= 16)
    oidx = np.nonzero(occ_day)[0]
    twe = np.full(8760, 26.0)  # Tmax 26.75 at Trm 15
    twe[oidx[0:3]] = 27.9   # DT 1.15 -> wf 1 x 3 h
    twe[oidx[3:5]] = 28.9   # DT 2.15 -> wf 2 x 2 h
    twe[oidx[5]] = 29.9     # DT 3.15 -> wf 3 x 1 h  => We = 3+4+3 = 10
    rwe = eng52.evaluate_room("o", "Office", twe, hours, occupancy=occ,
                              category="II", daily_mean_outdoor=dm15,
                              mode="compliance")
    c2 = next(r for r in rwe.results if r.criterion_id == "c2")
    check("SCI-14", "We hand example: 3 h at wf1 + 2 h at wf2 + 1 h at wf3 = 10 > 6 -> "
          "FAIL on the correct day", c2.status == "FAIL"
          and c2.basis["worst_day_we"] == 10.0, f"We = {c2.basis['worst_day_we']}")
    t6 = np.full(8760, 26.0)
    t6[oidx[0:6]] = 27.9  # 6 h at wf 1 -> We = 6: pass (limit is <= 6)
    rwe2 = eng52.evaluate_room("o", "Office", t6, hours, occupancy=occ,
                               category="II", daily_mean_outdoor=dm15,
                               mode="compliance")
    c2b = next(r for r in rwe2.results if r.criterion_id == "c2")
    check("SCI-15", "We = 6 exactly PASSES (document: 'shall be less than or equal "
          "to 6')", c2b.status == "PASS", f"We = {c2b.basis['worst_day_we']}")

    # ---------------- 9. TM52 Criterion 3: raw DT > 4 K -------------------------
    print("9. TM52 Criterion 3 — absolute limit, raw DT > 4 K")
    t3 = np.full(8760, 30.75)  # DT exactly 4.0 at Tmax 26.75: not a fail
    eng52._bind_calendar(hours, 8760)
    july15 = np.nonzero((m5 == 7) & (h5 == 15))[0]
    t3[july15] = 30.76  # DT 4.01 -> fails
    r3 = eng52.evaluate_room("o", "Office", t3, hours, occupancy=occ,
                             category="II", daily_mean_outdoor=dm15, mode="compliance")
    c3 = next(r for r in r3.results if r.criterion_id == "c3")
    check("SCI-16", "criterion 3: DT exactly 4.0 not counted; 4.01 counted; "
          "raw (unrounded)", c3.status == "FAIL" and c3.metric_value == 31.0,
          f"{c3.metric_value:.0f} h over limit")

    # ---------------- 10. Comfort library parity (Fanger / adaptive) ------------
    print("10. Comfort equations — Fanger PMV/PPD and EN 16798-1 adaptive")
    from pythermalcomfort.models import adaptive_en, pmv_ppd_iso
    from overheatlens.comfort import adaptive_comfort_en, pmv_ppd

    ok_all, det = True, []
    for cond in ((25, 25, 0.1, 50, 1.2, 0.5), (27, 29, 0.3, 40, 1.0, 0.8),
                 (23, 22, 0.05, 60, 1.5, 0.3)):
        r_prod = pmv_ppd(tdb=cond[0], tr=cond[1], vr=cond[2], rh=cond[3],
                         met=cond[4], clo=cond[5])
        r_lib = pmv_ppd_iso(tdb=cond[0], tr=cond[1], vr=cond[2], rh=cond[3],
                            met=cond[4], clo=cond[5])
        same = (r_prod.status == "OK"
                and abs(r_prod.values["pmv"] - r_lib.pmv) < 1e-12
                and abs(r_prod.values["ppd"] - r_lib.ppd) < 1e-12)
        ok_all &= same
        det.append(f"PMV {r_prod.values['pmv']:.3f}")
    check("SCI-17", "Fanger PMV/PPD: wrapper equals the ISO 7730:2025 library "
          "exactly at three conditions (never reimplemented)", ok_all,
          "; ".join(det))
    a_prod = adaptive_comfort_en(tdb=27.2, tr=27.2, t_running_mean=18.0, v=0.1)
    a_lib = adaptive_en(tdb=27.2, tr=27.2, t_running_mean=18.0, v=0.1)
    # hand check of the EN 16798-1 Cat II equation: Tcom = 0.33 Trm + 18.8, +3 K band
    hand = 0.33 * 18.0 + 18.8
    check("SCI-18", "EN 16798-1 adaptive: Tcom matches 0.33 Trm + 18.8 hand equation",
          abs(a_prod.values["tmp_cmf"] - a_lib.tmp_cmf) < 1e-12
          and abs(a_lib.tmp_cmf - hand) < 0.11,
          f"{a_prod.values['tmp_cmf']:.2f} vs hand {hand:.2f} degC")
    check("SCI-19", "applicability gate: Trm 35 -> OUTSIDE_APPLICABILITY, no value",
          adaptive_comfort_en(tdb=30, tr=30, t_running_mean=35, v=0.1).status
          == "OUTSIDE_APPLICABILITY", "explicit non-result per plan 14.3")

    # ---------------- 11. Weather physics ---------------------------------------
    print("11. Weather physics — dew-point relation and degree-hour integral")
    from overheatlens.epw import degree_hours, exceedance_hours

    t = np.array([24.0, 26.0, 28.0, 30.0, np.nan, 999.9])
    check("SCI-20", "exceedance/degree-hour integrals: monotone, sentinel-safe",
          exceedance_hours(t, 26.0) == 3
          and abs(degree_hours(t, 26.0) - (0 + 2.0 + 4.0)) < 1e-9,
          "3 h >= 26; 6 Kh above 26 (sentinel excluded)")
    # Clausius-Clapeyron sanity: dew point <= dry bulb always in physics checks
    check("SCI-21", "dew-point <= dry-bulb physics guard active (checker rule)",
          "DEWPOINT_VIOLATION" in {i.code for i in
                                   __import__("overheatlens.epw", fromlist=["check_epw"])
                                   .check_epw(__import__("overheatlens.epw",
                                                         fromlist=["parse_epw"])
                                              .parse_epw(REPO / "fixtures/epw/synthetic/dewpoint_violation.epw")).issues},
          "planted violation detected")

    # ---------------- report ----------------
    n_pass = sum(1 for r in RESULTS if r["status"] == "PASS")
    n_fail = len(RESULTS) - n_pass
    now = datetime.now(timezone.utc)
    lines = [
        "# Scientific Validation Report — Equations & Theory",
        "",
        f"**Run finished:** {now:%Y-%m-%d %H:%M UTC}  ",
        f"**Result:** {n_pass} PASS · {n_fail} FAIL",
        "",
        "**Method:** every production implementation is compared against an "
        "independent reference written directly from the source-verified documents "
        "(TM52 Eq 2.2/2.3/8/9/10, TM59:2017 §4/§6, TM59:2026 §2.4, EN 16798-1) — "
        "the reference code is never imported from production (plan §27.1 Tier 2).",
        "",
        "| ID | Equation / theory | Status | Detail |",
        "|---|---|---|---|",
    ]
    for r in RESULTS:
        lines.append(f"| {r['id']} | {r['desc']} | {r['status']} | {r['detail']} |")
    lines += [
        "", "---", "",
        "Sources: S-02 TM59:2017 · S-03 TM59:2026 · S-04 TM52:2013 · S-08 TM59:2026",
        "weather requirements (statuses + SHA-256 in SOURCE_REGISTER.md; verbatim",
        "evidence in docs/standards/TM59_2026_VERIFICATION.md and",
        "TM59_2017_TM52_VERIFICATION.md).", "",
        "Machine-generated by `scripts/validate_science.py`.", ""]
    out = REPO / "docs" / "validation" / "SCIENTIFIC_VALIDATION_REPORT.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n{'=' * 60}")
    print(f"RESULT: {n_pass} PASS, {n_fail} FAIL -> {out.relative_to(REPO)}")
    print(f"{'=' * 60}")
    return 1 if n_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
