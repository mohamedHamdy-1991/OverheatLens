"""TM59:2017 boundary tests — every value locked to the machine-verified official PDF
(SOURCE_REGISTER S-02; docs/standards/TM59_2017_TM52_VERIFICATION.md):

* criterion (a) ADAPTIVE per TM52: Tmax = 0.33 Trm + 21.8 (Cat II) / + 20.8 (Cat I),
  clamped outside Trm 10-30; Delta T rounded (raw >= 0.5 counts); May-September;
  > 3% of occupied hours fails (living 1989 h / bedroom 3672 h bases)
* criterion (b) bedrooms only: Top > 26 degC during 22:00-07:00; limit 32 h
  (fail at 33); full-year window
* criterion (mv) mechanically ventilated route: Top > 26 degC > 3% of annual
  model-supplied occupied hours
* corridor: 28 degC > 3% of total annual hours -> ADVISORY flag only
* ventilation routes: natural -> a + b; mechanical -> mv
"""

from __future__ import annotations

import numpy as np
import pytest

from overheatlens.schemas import RulePackError
from overheatlens.standards import (
    StandardsEngine,
    classify_room,
    running_mean_trm,
)

from conftest import series_at


HOURS = (np.arange(8760) % 24) + 1
DM = np.full(365, 15.0)  # constant outdoor 15 degC -> Trm 15 -> Tmax(II) = 26.75


@pytest.fixture(scope="module")
def eng():
    return StandardsEngine.load("uk_tm59_2017")


def result(assessment, cid):
    return next(r for r in assessment.results if r.criterion_id == cid)


# ---- gates -------------------------------------------------------------------

def test_source_verified_compliance_allowed(eng):
    assert eng.compliance_allowed() is True
    ra = eng.evaluate_room("r", "Bedroom", series_at(22.0), HOURS, category="II",
                           daily_mean_outdoor=DM, mode="compliance")
    assert ra.mode == "compliance"
    assert ra.verification_status == "source_verified"


def test_pack_values_locked_to_register(eng):
    b = eng._criteria["b"]
    assert b["max_exceedance_hours"] == 32
    assert b["condition"] == "top_c > 26.0"
    assert b["window"] == "sleep_hours"
    a = eng._criteria["a"]
    assert a["aggregation"] == "percent_of_occupied_hours"
    assert a["occupancy_hours_basis"] == 1989
    assert a["variants"]["bedroom"]["occupancy_hours_basis"] == 3672
    assert a["adaptive_threshold"]["category_II"]["clamp_min_c"] == 25.1
    assert a["adaptive_threshold"]["category_II"]["clamp_max_c"] == 31.7
    assert eng._criteria["corridor"]["advisory"] is True
    assert eng._criteria["mv"]["ventilation_route"] == "mechanical"
    assert eng._criteria["a"]["ventilation_route"] == "natural"
    assert eng._criteria["b"]["ventilation_route"] == "natural"


# ---- classification ----------------------------------------------------------

def test_classify_room_2017(eng):
    assert classify_room("Master Bedroom", eng.pack) == "bedroom"
    assert classify_room("Kitchen", eng.pack) == "living"
    assert classify_room("Corridor", eng.pack) == "communal"
    # bathrooms/halls note: halls classify as communal (included, advisory only)


# ---- criterion (a): adaptive, May-Sept, occupied-hours denominator -----------

def test_criterion_a_adaptive_threshold_and_rounding(eng):
    # Top = 27.2, Tmax(II) = 26.75 -> raw DT = 0.45 < 0.5 -> NOT counted
    top = series_at(27.2)
    ra = eng.evaluate_room("r", "Bedroom", top, HOURS, category="II",
                           daily_mean_outdoor=DM, mode="compliance")
    assert result(ra, "a").metric_value == 0.0
    # Top = 27.25 -> raw DT = 0.50 -> counted (every bedroom hour = 3672)
    top = series_at(27.25)
    ra = eng.evaluate_room("r", "Bedroom", top, HOURS, category="II",
                           daily_mean_outdoor=DM, mode="compliance")
    # every bedroom hour counts: 3672/3672 = 100% of occupied hours -> FAIL
    assert result(ra, "a").metric_value == 100.0


def test_criterion_a_category_I_threshold(eng):
    # Cat I: Tmax = 0.33*15 + 20.8 = 25.75
    top = series_at(26.2)  # raw DT = 0.45 -> not counted
    ra = eng.evaluate_room("r", "Bedroom", top, HOURS, category="I",
                           daily_mean_outdoor=DM, mode="compliance")
    assert result(ra, "a").metric_value == 0.0
    top = series_at(26.25)  # raw DT = 0.5 -> counted
    ra = eng.evaluate_room("r", "Bedroom", top, HOURS, category="I",
                           daily_mean_outdoor=DM, mode="compliance")
    assert result(ra, "a").metric_value == 100.0


def test_criterion_a_living_denominator_and_3pct_flip(eng):
    """Living: denominator 1989 h; 3% = 59.67 -> 60 counted hours = 3.019% FAIL;
    59 hours = 2.967% PASS. Night hours do not count (13 h/day profile)."""
    eng._bind_calendar(HOURS, 8760)
    month, _, hour = eng._month, eng._day, eng._hour
    occ = (month == 7) & np.isin(hour, range(10, 23))
    idx = np.nonzero(occ)[0]
    assert idx.size == 31 * 13  # July occupied hours geometry
    for n_hot, expected in ((59, "PASS"), (60, "FAIL")):
        top = series_at(20.0)
        top[idx[:n_hot]] = 30.0  # raw DT = 3.25 -> counts
        ra = eng.evaluate_room("r", "Living room", top, HOURS, category="II",
                               daily_mean_outdoor=DM, mode="compliance")
        a = result(ra, "a")
        assert a.status == expected, (n_hot, a.to_dict())
        assert a.basis["occupied_hours_basis"] == 1989


def test_criterion_a_april_excluded(eng):
    eng._bind_calendar(HOURS, 8760)
    month, hour = eng._month, eng._hour
    top = series_at(20.0)
    april = (month == 4) & np.isin(hour, range(10, 23))
    top[np.nonzero(april)[0]] = 35.0
    ra = eng.evaluate_room("r", "Living room", top, HOURS, category="II",
                           daily_mean_outdoor=DM, mode="compliance")
    assert result(ra, "a").metric_value == 0.0


# ---- criterion (b): 32-hour limit, sleep window, full year -------------------

def test_criterion_b_exact_32_hour_flip(eng):
    eng._bind_calendar(HOURS, 8760)
    month, day, hour = eng._month, eng._day, eng._hour
    sleep = np.isin(hour, (23, 24, 1, 2, 3, 4, 5, 6, 7))
    idx = np.nonzero(sleep & (month == 6))[0]
    for n_hot, expected in ((32, "PASS"), (33, "FAIL")):
        top = series_at(20.0)
        top[idx[:n_hot]] = 27.0
        ra = eng.evaluate_room("r", "Bedroom", top, HOURS, category="II",
                               daily_mean_outdoor=DM, mode="compliance")
        b = result(ra, "b")
        assert b.status == expected, (n_hot, b.to_dict())
        assert b.metric_value == float(n_hot)


def test_criterion_b_full_year_window_and_exactly_26(eng):
    eng._bind_calendar(HOURS, 8760)
    month, hour = eng._month, eng._hour
    top = series_at(26.0)  # exactly 26 does NOT exceed (> 26 strict)
    ra = eng.evaluate_room("r", "Bedroom", top, HOURS, category="II",
                           daily_mean_outdoor=DM, mode="compliance")
    assert result(ra, "b").metric_value == 0.0
    # December heat counts (full-year window): 9 sleep-window labels x 31 days
    top = series_at(20.0)
    dec_sleep = (month == 12) & np.isin(hour, (23, 24, 1, 2, 3, 4, 5, 6, 7))
    top[np.nonzero(dec_sleep)[0]] = 27.5
    ra = eng.evaluate_room("r", "Bedroom", top, HOURS, category="II",
                           daily_mean_outdoor=DM, mode="compliance")
    assert result(ra, "b").metric_value == float(dec_sleep.sum())


def test_criterion_b_ignores_daytime(eng):
    eng._bind_calendar(HOURS, 8760)
    month, hour = eng._month, eng._hour
    top = series_at(20.0)
    day = np.isin(hour, range(10, 23))
    top[np.nonzero((month == 7) & day)[0][:500]] = 30.0
    ra = eng.evaluate_room("r", "Bedroom", top, HOURS, category="II",
                           daily_mean_outdoor=DM, mode="compliance")
    assert result(ra, "b").metric_value == 0.0


def test_sleep_window_label_geometry(eng):
    """Label 22 (21:00-22:00) outside the 22:00-07:00 window; label 7 inside."""
    eng._bind_calendar(HOURS, 8760)
    hour = eng._hour
    top = series_at(20.0)
    top[np.nonzero(hour == 22)[0]] = 30.0
    ra = eng.evaluate_room("r", "Bedroom", top, HOURS, category="II",
                           daily_mean_outdoor=DM, mode="compliance")
    assert result(ra, "b").metric_value == 0.0
    top[np.nonzero(hour == 7)[0]] = 30.0
    ra = eng.evaluate_room("r", "Bedroom", top, HOURS, category="II",
                           daily_mean_outdoor=DM, mode="compliance")
    assert result(ra, "b").metric_value == 365.0  # label 7 on all 365 days


# ---- ventilation routes -------------------------------------------------------

def test_natural_route_skips_mv_mechanical_route_skips_a_b(eng):
    top = series_at(24.0)
    ra_nat = eng.evaluate_room("r", "Bedroom", top, HOURS, category="II",
                               daily_mean_outdoor=DM, mode="compliance")
    assert {r.criterion_id for r in ra_nat.results if r.status != "NOT_APPLICABLE"} \
        == {"a", "b"}
    ra_mech = eng.evaluate_room("r", "Bedroom", top, HOURS, category="II",
                                ventilation_route="mechanical",
                                daily_mean_outdoor=DM, mode="compliance")
    assert {r.criterion_id for r in ra_mech.results if r.status != "NOT_APPLICABLE"} \
        == {"mv"}


def test_mechanical_route_needs_occupancy(eng):
    top = series_at(26.5)
    ra = eng.evaluate_room("r", "Bedroom", top, HOURS, category="II",
                           ventilation_route="mechanical",
                           daily_mean_outdoor=DM, mode="compliance")
    mv = result(ra, "mv")
    assert mv.status == "NOT_EVALUATED"  # no occupancy supplied: explicit non-result
    # with occupancy: 26.5 > 26 for every occupied hour
    occ = np.isin(HOURS, range(9, 23))  # 14 h/day -> 5110 annual occupied hours
    ra = eng.evaluate_room("r", "Bedroom", top, HOURS, occupancy=occ,
                           category="II", ventilation_route="mechanical",
                           daily_mean_outdoor=DM, mode="compliance")
    mv = result(ra, "mv")
    assert mv.status == "FAIL"
    assert mv.metric_value == 100.0
    assert mv.basis["occupied_hours_basis"] == 5110.0


# ---- corridor advisory --------------------------------------------------------

def test_corridor_is_advisory_flag_only(eng):
    eng._bind_calendar(HOURS, 8760)
    month = eng._month
    top = series_at(20.0)
    top[np.nonzero(month == 7)[0][:300]] = 29.0  # 300/8760 = 3.42% > 3%
    ra = eng.evaluate_room("r", "Corridor", top, HOURS, category="II",
                           daily_mean_outdoor=DM, mode="compliance")
    c = result(ra, "corridor")
    assert c.status == "FLAG" and c.passed is None
    assert c.metric_value == pytest.approx(3.4247, abs=1e-3)
    # advisory never fails the dwelling
    res = eng.evaluate_dwelling([
        ("r1", "Living room", series_at(22.0)),
        ("r2", "Master Bedroom", series_at(22.0)),
        ("r3", "Corridor", top),
    ], HOURS, category="II", daily_mean_outdoor=DM, mode="compliance")
    assert res["overall"] == "PASS"


def test_corridor_below_threshold_no_flag(eng):
    top = series_at(28.0)  # exactly 28: strict > does not count
    ra = eng.evaluate_room("r", "Corridor", top, HOURS, category="II",
                           daily_mean_outdoor=DM, mode="compliance")
    assert result(ra, "corridor").status == "NO_FLAG"


# ---- dwelling -----------------------------------------------------------------

def test_dwelling_fail_on_bedroom_b(eng):
    eng._bind_calendar(HOURS, 8760)
    hour = eng._hour
    top = series_at(20.0)
    sleep = np.isin(hour, (23, 24, 1, 2, 3, 4, 5, 6, 7))
    idx = np.nonzero(sleep & (eng._month == 6))[0]
    top[idx[:33]] = 27.0
    res = eng.evaluate_dwelling([
        ("r1", "Living room", series_at(22.0)),
        ("r2", "Master Bedroom", top),
    ], HOURS, category="II", daily_mean_outdoor=DM, mode="compliance")
    assert res["overall"] == "FAIL"


def test_dwelling_incomplete_without_outdoor_data(eng):
    """Adaptive criterion (a) cannot run without daily_mean_outdoor -> INCOMPLETE,
    never a silent PASS."""
    res = eng.evaluate_dwelling(
        [("r1", "Living room", series_at(22.0))], HOURS, category="II",
        mode="compliance")
    assert res["overall"] == "INCOMPLETE"


def test_trm_published_weights_feed_criterion_a(eng):
    """Hand-checked chain: constant outdoor 20 degC -> Trm 20 -> Tmax(II) 28.4."""
    dm = np.full(365, 20.0)
    top = series_at(28.9)  # raw DT = 0.5 -> counts
    ra = eng.evaluate_room("r", "Bedroom", top, HOURS, category="II",
                           daily_mean_outdoor=dm, mode="compliance")
    assert result(ra, "a").metric_value == 100.0
    top = series_at(28.8)  # raw DT = 0.4 -> not counted
    ra = eng.evaluate_room("r", "Bedroom", top, HOURS, category="II",
                           daily_mean_outdoor=dm, mode="compliance")
    assert result(ra, "a").metric_value == 0.0


# ---- Part O inheritance --------------------------------------------------------

def test_part_o_inherits_verified_criteria_and_stays_distinct():
    po = StandardsEngine.load("uk_part_o_dynamic")
    assert po.pack_id == "uk_part_o_dynamic"
    assert po.compliance_allowed() is True
    limits = po.model_limits()
    assert {m["id"] for m in limits} >= {"PO-WIN-01", "PO-WIN-02", "PO-WIN-03",
                                         "PO-WIN-04", "PO-OVR-01"}
    assert all(m["verification"]["status"] == "source_verified" for m in limits)
    assert {e["id"] for e in po.strategy_exclusions()} == {"PO-EXC-01", "PO-EXC-02"}
    # criteria resolve through the 2017 parent
    assert po._criteria["b"]["max_exceedance_hours"] == 32
    # weather note states the inheritance
    assert "NOT" in po.pack["weather_note"]
