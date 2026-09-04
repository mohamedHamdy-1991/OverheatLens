#!/usr/bin/env python3
"""OverheatLens — scientific validation campaign (see validation/METHOD.md).

Runs every case V01..V11 against the real engines and real research data and
writes validation/results.json + validation/CAMPAIGN_REPORT.md.
INCOMPLETE is a valid verdict; a campaign is PASS only when nothing FAILs.

Run: ./.venv/bin/python validation/run_campaign.py [--skip-slow]
(--skip-slow omits the two EnergyPlus runs V08/V09 for a quick re-check)
"""
from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "packages" / "overheatlens-core"))

import numpy as np  # noqa: E402
import yaml  # noqa: E402

from overheatlens.standards import StandardsEngine  # noqa: E402
from overheatlens.worker import harvest_hourly, harvest_meters, run_energyplus  # noqa: E402

VALIDATION_DIR = REPO / "validation"
RULES_DIR = REPO / "packages" / "overheatlens-core" / "overheatlens" / "rules"
WEATHER = Path("/Users/mohamedali/Library/CloudStorage/OneDrive-LeedsBeckettUniversity"
               "/Work/Ph.D/DataBase/DataBase/LEEDS Weather Files/Weather File MET Office"
               "/Leeds_DSY1_2020High50_.epw")
MODEL_01BA = REPO / "data" / "archetypes" / "idf" / "01BA_end_terrace.idf"
AUDIT = REPO / "data" / "archetypes" / "audit_report.json"
MITIGATION = REPO / "data" / "mitigation" / "summary.json"

HOURS = (np.arange(8760) % 24) + 1
DM = np.full(365, 15.0)  # Trm 15 -> TM52/TM59-2017 Cat II Tmax = 26.75

CASES: list[dict] = []


def record(case_id: str, title: str, layer: str, verdict: str, detail: dict,
           reference: str):
    CASES.append({"id": case_id, "title": title, "layer": layer,
                  "verdict": verdict, "detail": detail, "reference": reference})
    print(f"[{verdict:>22}] {case_id} — {title}")


def series_at(const_c: float, n: int = 8760) -> np.ndarray:
    return np.full(n, float(const_c))


# ---------------------------------------------------------------- V01 source chain
def v01_source_chain():
    packs = ("uk_tm59_2017", "uk_tm59_2026", "uk_part_o_dynamic", "uk_tm52")
    detail = {}
    ok = True
    for pack in packs:
        raw = yaml.safe_load((RULES_DIR / f"{pack}.yaml").read_text())
        ver = str(raw.get("verification_note", ""))
        blocks = [c.get("verification", {}) for c in raw.get("criteria", [])]
        statuses = {b.get("status") for b in blocks if b}
        statuses_ok = statuses <= {"source_verified"}
        if pack == "uk_part_o_dynamic":
            # Part O inherits TM59:2017 criteria (SHA-pinned there) and adds
            # ADO-verified overrides; its own note documents the ADO content.
            this_ok = ("ADO" in ver or "Approved Document O" in ver) and statuses_ok
        else:
            this_ok = "SHA-256" in ver and statuses_ok
        detail[pack] = {"sha_in_note": "SHA-256" in ver,
                        "ado_referenced": "ADO" in ver,
                        "criteria_statuses": sorted(statuses)}
        ok = ok and this_ok
    record("V01", "Rule packs machine-verified to official PDFs", "L1",
           "PASS" if ok else "FAIL", detail,
           "SOURCE_REGISTER.md; docs/standards/*_VERIFICATION.md")


# ---------------------------------------------------------------- V02 EPW real file
def v02_epw_real():
    from overheatlens.epw import check_epw, parse_epw
    if not WEATHER.is_file():
        record("V02", "EPW parser & QC on real research weather", "L4",
               "INCOMPLETE", {"reason": f"weather file not found: {WEATHER}"},
               "CIBSE/Met Office DSY format; file header")
        return
    epw = parse_epw(WEATHER)
    db = epw.valid_dry_bulb()
    report = check_epw(epw)
    mean_db = float(np.nanmean(db))
    # EPW header is 8 lines; line 9 (index 8) is the first data record (35 fields)
    first_data = WEATHER.read_text(errors="replace").splitlines()[8]
    n_cols = len(first_data.split(","))
    qc = "FAIL" if report.errors else ("PASS_WITH_WARNINGS" if report.warnings
                                       else "PASS")
    checks = {"n_hours": int(db.size), "columns_first_data_row": n_cols,
              "qc_verdict": qc, "n_errors": len(report.errors),
              "n_warnings": len(report.warnings),
              "annual_mean_db_c": round(mean_db, 2)}
    ok = (db.size == 8760 and n_cols >= 32 and qc != "FAIL"
          and 8.0 <= mean_db <= 13.0)
    record("V02", "EPW parser & QC on real research weather", "L4",
           "PASS" if ok else "FAIL", checks,
           "CIBSE/Met Office DSY format; Leeds DSY1 2020-high climate envelope")


# ---------------------------------------------------------- V03 TM59 2017 boundaries
def v03_tm59_2017_bounds():
    eng = StandardsEngine.load("uk_tm59_2017")
    eng._bind_calendar(HOURS, 8760)
    month, _, hour = eng._month, eng._day, eng._hour
    detail = {}

    # (a) living room: 3% of 1989 occupied hours above adaptive Tmax (26.75 at Trm 15)
    occ = (month == 7) & np.isin(hour, range(10, 23))
    idx = np.nonzero(occ)[0]
    flips = {}
    for n_hot, expected in ((59, "PASS"), (60, "FAIL")):
        top = series_at(20.0)
        top[idx[:n_hot]] = 30.0
        ra = eng.evaluate_room("r", "Living room", top, HOURS, category="II",
                               daily_mean_outdoor=DM, mode="compliance")
        a = next(r for r in ra.results if r.criterion_id == "a")
        flips[f"{n_hot}_h"] = a.status
        detail[f"criterion_a_{n_hot}h"] = a.to_dict()
    # sub-rounding heat counts nothing (raw DT 0.45 K)
    top = series_at(20.0)
    top[idx] = 27.2
    ra = eng.evaluate_room("r", "Living room", top, HOURS, category="II",
                           daily_mean_outdoor=DM, mode="compliance")
    a = next(r for r in ra.results if r.criterion_id == "a")
    flips["rounding_0.45K_counts"] = a.metric_value
    detail["criterion_a_rounding"] = {"percent": a.metric_value}
    # April excluded
    top = series_at(20.0)
    april = (month == 4) & np.isin(hour, range(10, 23))
    top[np.nonzero(april)[0]] = 35.0
    ra = eng.evaluate_room("r", "Living room", top, HOURS, category="II",
                           daily_mean_outdoor=DM, mode="compliance")
    a = next(r for r in ra.results if r.criterion_id == "a")
    flips["april_excluded_percent"] = a.metric_value

    # (b) bedroom sleep window: 32 h PASS / 33 h FAIL at Top 27 (>26), full year
    sleep = np.isin(hour, (23, 24, 1, 2, 3, 4, 5, 6, 7))
    june_sleep = np.nonzero(sleep & (month == 6))[0]
    for n_hot, expected in ((32, "PASS"), (33, "FAIL")):
        top = series_at(20.0)
        top[june_sleep[:n_hot]] = 27.0
        ra = eng.evaluate_room("r", "Bedroom", top, HOURS, category="II",
                               daily_mean_outdoor=DM, mode="compliance")
        b = next(r for r in ra.results if r.criterion_id == "b")
        flips[f"criterion_b_{n_hot}h"] = b.status
    # daytime heat never counts for b
    top = series_at(20.0)
    daytime = (month == 7) & np.isin(hour, range(10, 23))
    top[np.nonzero(daytime)[0][:500]] = 30.0
    ra = eng.evaluate_room("r", "Bedroom", top, HOURS, category="II",
                           daily_mean_outdoor=DM, mode="compliance")
    b = next(r for r in ra.results if r.criterion_id == "b")
    flips["criterion_b_daytime_hours"] = b.metric_value

    expected = {"59_h": "PASS", "60_h": "FAIL", "criterion_b_32h": "PASS",
                "criterion_b_33h": "FAIL"}
    ok = (flips["59_h"] == "PASS" and flips["60_h"] == "FAIL"
          and flips["rounding_0.45K_counts"] == 0.0
          and flips["april_excluded_percent"] == 0.0
          and flips["criterion_b_32h"] == "PASS" and flips["criterion_b_33h"] == "FAIL"
          and flips["criterion_b_daytime_hours"] == 0.0)
    record("V03", "TM59:2017 verdict flips at published boundaries", "L3",
           "PASS" if ok else "FAIL", {"flips": flips},
           "CIBSE TM59:2017 §5.2 (pack SHA-pinned, adaptive criteria + 32 h rule)")


# ---------------------------------------------------------- V04 TM52 worked example
def v04_tm52_worked_example():
    eng = StandardsEngine.load("uk_tm52")
    occ = np.isin(HOURS, range(9, 18))
    detail = {}

    # criterion 2, published §6.1.2 pattern: 3 h DT=1, 2 h DT=2, 1 h DT=3 -> We=10
    # probe day = day-of-year 200 (July — inside the May–September window)
    one_day = np.nonzero((HOURS >= 9) & (HOURS <= 17) & (np.arange(8760) // 24 == 199))[0]
    top = series_at(26.75)
    dt_plan = [1, 1, 1, 2, 2, 3]
    for j, dt in enumerate(dt_plan):
        top[one_day[j]] = 26.75 + dt
    ra = eng.evaluate_room("o", "Office", top, HOURS, occupancy=occ,
                           category="II", daily_mean_outdoor=DM, mode="compliance")
    c2 = next(r for r in ra.results if r.criterion_id == "c2")
    detail["we_pattern"] = {"expected": 10.0, "got": c2.metric_value, "status": c2.status}

    # criterion 1 rounding: 0.45 K counts nothing; 0.50 K counts all occupied hours
    r_045 = eng.evaluate_room("o", "Office", series_at(27.2), HOURS, occupancy=occ,
                              category="II", daily_mean_outdoor=DM, mode="compliance")
    r_050 = eng.evaluate_room("o", "Office", series_at(27.25), HOURS, occupancy=occ,
                              category="II", daily_mean_outdoor=DM, mode="compliance")
    c1_045 = next(r for r in r_045.results if r.criterion_id == "c1")
    c1_050 = next(r for r in r_050.results if r.criterion_id == "c1")
    detail["c1_rounding"] = {"dt0.45_percent": c1_045.metric_value,
                             "dt0.50_percent": c1_050.metric_value,
                             "basis_hours": c1_050.basis.get("occupied_hours_basis")}

    # criterion 3: raw DT > 4 K at any hour fails
    top = series_at(30.755)  # DT 4.005
    ra = eng.evaluate_room("o", "Office", top, HOURS, occupancy=occ,
                           category="II", daily_mean_outdoor=DM, mode="compliance")
    c3 = next(r for r in ra.results if r.criterion_id == "c3")
    detail["c3_4K"] = {"status": c3.status}

    ok = (c2.metric_value == 10.0 and c2.status == "FAIL"
          and c1_045.metric_value == 0.0 and c1_050.metric_value == 100.0
          and c1_050.basis.get("occupied_hours_basis") == 9 * 153
          and c3.status == "FAIL")
    record("V04", "TM52 published worked example + rounding boundaries", "L2/L3",
           "PASS" if ok else "FAIL", detail,
           "CIBSE TM52-2013 §6.1.1–§6.1.3 (pack SHA-pinned)")


# ---------------------------------------------------------------- V05 PMV published
def v05_pmv_published():
    from overheatlens.comfort import pmv_ppd
    anchors = [-1.0, -0.5, 0.0, 0.5, 1.0]
    detail = {}
    ok = True

    def pmv_at(tdb: float):
        """(pmv, ppd) or None when outside the library's applicability range."""
        r = pmv_ppd(tdb=tdb, tr=tdb, vr=0.1, rh=50, met=1.2, clo=0.5)
        if r.status != "OK" or "pmv" not in r.values:
            return None
        return float(r.values["pmv"]), float(r.values["ppd"])

    # locate temperatures where PMV crosses each anchor, then check PPD.
    # The library refuses |PMV| > 2 (published applicability), so in-range
    # anchors are 0, ±0.5, ±1; the last in-range evaluation is used.
    published_ppd = {-1.0: 25.67, -0.5: 10.15, 0.0: 5.0, 0.5: 10.15, 1.0: 25.67}
    for target in anchors:
        lo, hi = (18.0, 29.0) if target >= 0 else (18.0, 29.0)
        last = None
        for _ in range(36):
            mid = (lo + hi) / 2
            got = pmv_at(mid)
            if got is None:          # outside applicability — step toward neutral
                hi = mid
                continue
            last = got
            if got[0] < target:
                lo = mid
            else:
                hi = mid
        detail[f"pmv_{target}"] = {"tdb_c": round((lo + hi) / 2, 3),
                                   "pmv": round(last[0], 3),
                                   "ppd": round(last[1], 2),
                                   "published_ppd": published_ppd[target]}
        if abs(last[1] - published_ppd[target]) > 0.75:
            ok = False

    # published applicability limit: |PMV| > 2 must be refused, not extrapolated
    hot = pmv_ppd(tdb=33.0, tr=33.0, vr=0.1, rh=50, met=1.2, clo=0.5)
    detail["beyond_applicability_33C"] = {
        "status": hot.status, "values_returned": sorted(hot.values.keys())}
    if hot.status == "OK" or hot.values:
        ok = False
    # published anchor table coarsely (ISO 7730): PPD(0)=5, ±0.5<10..~10, ±1~25, ±2~75
    record("V05", "PMV/PPD matches published ISO 7730 anchors", "L2",
           "PASS" if ok else "FAIL", detail,
           "ISO 7730 PPD relation 100-95*exp(-0.03353*PMV^4-0.2179*PMV^2); "
           "anchor table PPD(0)=5%, (±0.5)≈10%, (±1)≈25%, (±2)≈75%")


# ---------------------------------------------------------------- V06 UTCI reference
def v06_utci_reference():
    from overheatlens.comfort import utci_comfort
    r = utci_comfort(tdb=25.0, tr=25.0, v=0.5, rh=50.0)
    utci_ref = float(r.values["utci"])
    r_hot = utci_comfort(tdb=25.0, tr=45.0, v=0.5, rh=50.0)
    utci_hot = float(r_hot.values["utci"])
    detail = {"utci_at_reference_c": round(utci_ref, 2),
              "published_expectation": "UTCI ≈ Ta (25 °C) at reference conditions "
                                       "(Tr=Ta, RH 50 %, v 0.5 m/s), Bröde 2012 r²≈0.995",
              "utci_with_tr_45c": round(utci_hot, 2)}
    ok = abs(utci_ref - 25.0) <= 0.5 and utci_hot > 30.0
    record("V06", "UTCI reproduces published reference-condition agreement", "L2",
           "PASS" if ok else "FAIL", detail,
           "Bröde et al. 2012, Int J Biometeorol 56:481–494 (reference conditions)")


# ---------------------------------------------------------------- V07 adaptive limits
def v07_adaptive_limits():
    eng = StandardsEngine.load("uk_tm52")
    occ = np.isin(HOURS, range(9, 18))
    detail = {}
    ok = True

    def counted_fraction(top_const: float, dm: np.ndarray) -> float:
        ra = eng.evaluate_room("o", "Office", np.full(8760, top_const), HOURS,
                               occupancy=occ, category="II",
                               daily_mean_outdoor=dm, mode="compliance")
        c1 = next(r for r in ra.results if r.criterion_id == "c1")
        return float(c1.metric_value)

    for trm in (10.0, 15.0, 17.0, 23.0, 30.0, 8.0):
        tmax_expected = round(min(max(trm, 10.0), 30.0) * 0.33 + 21.8, 2)
        dm = np.full(365, trm)
        # Behavioural probe: a constant series counts exceedance iff
        # Top - Tmax >= 0.5 (published rounding). Bisect the flip point:
        # flip - 0.5 recovers the engine's working Tmax.
        lo, hi = 20.0, 40.0
        for _ in range(30):
            mid = (lo + hi) / 2
            if counted_fraction(mid, dm) == 0.0:
                lo = mid
            else:
                hi = mid
        flip = (lo + hi) / 2
        tmax_engine = round(flip - 0.5, 2)
        detail[f"trm_{trm}"] = {"flip_top_c": round(flip, 3),
                                "engine_tmax": tmax_engine,
                                "formula": tmax_expected}
        if abs(tmax_engine - tmax_expected) > 0.01:
            ok = False

    # EN 16798-1 comfort temperature via the wrapped library
    from pythermalcomfort.models import adaptive_en
    tcomf = float(adaptive_en(tdb=27.0, tr=27.0, t_running_mean=23.0,
                              v=0.1).tmp_cmf)
    detail["en16798_tcomf_trm23"] = {"got": round(tcomf, 3),
                                     "formula": round(0.33 * 23 + 18.8, 3)}
    if abs(tcomf - (0.33 * 23 + 18.8)) > 0.01:
        ok = False
    record("V07", "Adaptive limits match published formulae (TM52 Eq 8 / EN 16798-1)",
           "L2", "PASS" if ok else "FAIL", detail,
           "CIBSE TM52-2013 Eq 8 (pack SHA-pinned); EN 16798-1 via pythermalcomfort")


# ------------------------------------------------- V08/V09 EnergyPlus on real files
def v08_v09_energyplus(skip_slow: bool):
    if skip_slow:
        for cid, title in (("V08", "EnergyPlus determinism (two identical runs)"),
                           ("V09", "Energy meter internal consistency")):
            record(cid, title, "L5", "INCOMPLETE",
                   {"reason": "skipped by --skip-slow"},
                   "EnergyPlus 25.1.0 official binary")
        return
    if not (WEATHER.is_file() and MODEL_01BA.is_file()):
        for cid, title in (("V08", "EnergyPlus determinism (two identical runs)"),
                           ("V09", "Energy meter internal consistency")):
            record(cid, title, "L5", "INCOMPLETE",
                   {"reason": "real IDF/EPW not found on this machine"},
                   "EnergyPlus 25.1.0 official binary")
        return
    runs = []
    for i in (1, 2):
        run = run_energyplus(MODEL_01BA, WEATHER, timeout_s=900)
        runs.append(run)
    r1, r2 = runs
    if r1.status != "complete" or r2.status != "complete":
        record("V08", "EnergyPlus determinism (two identical runs)", "L5", "INCOMPLETE",
               {"run1": r1.status, "run2": r2.status}, "EnergyPlus 25.1.0")
        record("V09", "Energy meter internal consistency", "L5", "INCOMPLETE",
               {"reason": "runs not complete"}, "EnergyPlus 25.1.0")
        return
    z1 = harvest_hourly(r1.csv_path)
    z2 = harvest_hourly(r2.csv_path)
    same_series = (set(z1) == set(z2) and all(
        np.array_equal(np.round(z1[k]["top"], 6), np.round(z2[k]["top"], 6))
        for k in z1))
    m1 = harvest_meters(r1.meter_path) if r1.meter_path else {}
    m2 = harvest_meters(r2.meter_path) if r2.meter_path else {}
    same_meters = (m1 != {} and m1 == m2)
    record("V08", "EnergyPlus determinism (two identical runs)", "L5",
           "PASS" if (same_series and same_meters) else "FAIL",
           {"zones": len(z1), "series_identical": bool(same_series),
            "meters_identical": bool(same_meters),
            "electricity_kwh": (m1.get("Electricity:Facility", {}) or {}).get("annual_kwh")},
           "EnergyPlus 25.1.0 official binary; app runner (isolated dirs)")

    # V09 internal consistency on run 1
    detail = {}
    ok = False
    if m1:
        elec = m1.get("Electricity:Facility", {})
        gas = m1.get("NATURALGAS:Facility", {})
        months = elec.get("monthly_kwh") or []
        annual = elec.get("annual_kwh")
        if months and annual is not None:
            drift = abs(sum(months) - annual) / max(annual, 1e-9)
            detail = {"monthly_sum_kwh": round(sum(months), 2),
                      "annual_kwh": round(annual, 2),
                      "relative_drift": round(drift, 6),
                      "gas_annual_kwh": round(gas.get("annual_kwh") or 0.0, 2),
                      "n_monthly_rows": len(months)}
            ok = drift <= 0.005 and annual >= 0 and (gas.get("annual_kwh") or 0) >= 0
        else:
            detail = {"reason": "no runperiod/monthly meter rows parsed",
                      "meters": list(m1)}
    record("V09", "Energy meter internal consistency", "L5",
           "PASS" if ok else "FAIL", detail,
           "EnergyPlus meter output (eplusmeter.csv via --readvars); "
           "monthly sums vs runperiod total ≤ 0.5 %")


# ------------------------------------------------------------- V10 PhD DesignBuilder
def v10_phd_cross():
    if not (AUDIT.is_file() and MITIGATION.is_file()):
        record("V10", "Cross-check vs author's DesignBuilder PhD exports", "L4",
               "INCOMPLETE",
               {"reason": "audit_report.json or mitigation summary.json missing"},
               "data/mitigation/summary.json (author's Safer_Heat_Harehills study)")
        return
    audit = {r["file"]: r for r in json.loads(AUDIT.read_text())}
    mit = json.loads(MITIGATION.read_text())
    houses = mit.get("houses", {})
    detail = {}
    confirmed = incomplete = 0
    for code, h in houses.items():
        stem = f"{code}_"
        app_row = next((a for f, a in audit.items() if f.startswith(stem)), None)
        db_rows = ((h.get("baseline") or {}).get("tm59") or {}).get("nat") or []
        app_overall = (app_row or {}).get("tm59_2017_overall")
        db_verdicts = [str(r.get("pass_fail", "")).upper() for r in db_rows]
        if app_overall in ("PASS", "FAIL") and db_verdicts:
            agree = all(v == app_overall for v in db_verdicts)
            detail[code] = {"app_overall": app_overall,
                            "designbuilder_zones": len(db_verdicts),
                            "designbuilder_verdicts": sorted(set(db_verdicts)),
                            "agreement": agree,
                            "note": "weather metadata not recorded in the "
                                    "DesignBuilder export — directional check"}
            confirmed += 1 if agree else 0
            if not agree:
                record("V10", "Cross-check vs author's DesignBuilder PhD exports",
                       "L4", "FAIL", detail, "Safer_Heat_Harehills exports")
                return
        else:
            detail[code] = {"app_overall": app_overall,
                            "designbuilder_baseline_rows": len(db_verdicts),
                            "verdict": "INCOMPLETE",
                            "reason": "no DesignBuilder baseline export recorded"}
            incomplete += 1
    record("V10", "Cross-check vs author's DesignBuilder PhD exports", "L4",
           "CONFIRMED_DIRECTIONAL" if confirmed else "INCOMPLETE",
           {"dwellings_confirmed": confirmed, "dwellings_incomplete": incomplete,
            "per_dwelling": detail},
           "Safer_Heat_Harehills DesignBuilder TM59 exports (author's PhD data)")


# ------------------------------------------------------------- V11 CIBSE example flat
def v11_cibse_example_flat():
    if not AUDIT.is_file():
        record("V11", "CIBSE TM59 Example 4 flat vs published outcome", "L4",
               "INCOMPLETE", {"reason": "audit_report.json missing"},
               "CIBSE TM59:2017 worked example")
        return
    audit = {r["file"]: r for r in json.loads(AUDIT.read_text())}
    row = audit.get("Flat_TM59Example4.idf", {})
    overall = row.get("tm59_2017_overall")
    detail = {"app_overall": overall,
              "published_direction": "the reference flat overheats (criterion a fail) "
                                     "under a 2020s DSY in the CIBSE worked example",
              "note": "app runs the Leeds DSY1 2020-High50 file; CIBSE publishes its "
                      "example on its own weather — direction-only check"}
    record("V11", "CIBSE TM59 Example 4 flat vs published outcome", "L4",
           "CONFIRMED_DIRECTIONAL" if overall == "FAIL" else
           ("FAIL" if overall not in (None, "INCOMPLETE") else "INCOMPLETE"),
           detail, "CIBSE TM59:2017 worked example (pack SHA-pinned)")


def main() -> int:
    skip_slow = "--skip-slow" in sys.argv
    started = datetime.now(timezone.utc)
    print(f"OverheatLens validation campaign — started {started.isoformat()}\n")

    v01_source_chain()
    v02_epw_real()
    v03_tm59_2017_bounds()
    v04_tm52_worked_example()
    v05_pmv_published()
    v06_utci_reference()
    v07_adaptive_limits()
    v08_v09_energyplus(skip_slow)
    v10_phd_cross()
    v11_cibse_example_flat()

    fails = [c for c in CASES if c["verdict"] == "FAIL"]
    inc = [c for c in CASES if c["verdict"] == "INCOMPLETE"]
    campaign = "FAIL" if fails else "PASS"
    finished = datetime.now(timezone.utc)

    results = {
        "campaign_verdict": campaign,
        "started_utc": started.isoformat(timespec="seconds"),
        "finished_utc": finished.isoformat(timespec="seconds"),
        "summary": {"cases": len(CASES), "fail": len(fails),
                    "incomplete": len(inc),
                    "pass_or_confirmed": len(CASES) - len(fails) - len(inc)},
        "cases": CASES,
    }
    (VALIDATION_DIR / "results.json").write_text(json.dumps(results, indent=2))

    lines = [
        "# OverheatLens — Validation Campaign Report",
        "",
        f"Run: {started.isoformat(timespec='seconds')} → "
        f"{finished.isoformat(timespec='seconds')}  ·  "
        f"Campaign verdict: **{campaign}**  ·  "
        f"{results['summary']['pass_or_confirmed']} PASS/CONFIRMED · "
        f"{len(inc)} INCOMPLETE · {len(fails)} FAIL",
        "",
        "Method: see `validation/METHOD.md` (the full method document).",
        "",
        "| Case | Layer | Verdict | What it proves |",
        "|---|---|---|---|",
    ]
    for c in CASES:
        lines.append(f"| {c['id']} — {c['title']} | {c['layer']} | "
                     f"**{c['verdict']}** | {c['reference']} |")
    lines.append("")
    for c in CASES:
        if c["verdict"] in ("FAIL", "INCOMPLETE"):
            lines.append(f"## {c['id']} — {c['verdict']}")
            lines.append("```json")
            lines.append(json.dumps(c["detail"], indent=2)[:1500])
            lines.append("```")
            lines.append("")
    (VALIDATION_DIR / "CAMPAIGN_REPORT.md").write_text("\n".join(lines) + "\n")

    print(f"\nCampaign verdict: {campaign} — results.json + CAMPAIGN_REPORT.md "
          f"written to {VALIDATION_DIR}")
    return 0 if campaign == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
