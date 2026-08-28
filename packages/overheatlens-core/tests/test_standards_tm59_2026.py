"""TM59:2026 boundary tests — every value below is machine-verified against the
official CIBSE TM59:2026 PDF (SOURCE_REGISTER S-03) and locked here:

* criterion a/c hour limits: 59 h (living, 1989 occupied hours) / 110 h (bedroom, 3672)
* criterion b: nights-based, Tn = 26 (Cat I) / 27 (Cat II), limit 4 nights, 11 pm-8 am
* criterion d: 28 °C fixed, 110 h communal limit
* adaptive thresholds: 0.33 k per Trm °C, clamps 24.1-30.7 (I) / 25.1-31.7 (II)
* TM52 delta-T rounding: raw Delta T >= 0.5 K counts as 1 K exceedance
* assessment window 1 May-30 Sep; living occupancy 9 am-10 pm
"""

from __future__ import annotations

import numpy as np
import pytest

from overheatlens.standards import (
    EvaluationMode,
    StandardsEngine,
    classify_room,
    running_mean_trm,
)

from conftest import series_at


HOURS = (np.arange(8760) % 24) + 1
DM = np.full(365, 20.0)  # constant outdoor daily mean -> Trm = 20 everywhere


@pytest.fixture(scope="module")
def eng():
    return StandardsEngine.load("uk_tm59_2026")


def bind(eng_obj):
    eng_obj._bind_calendar(HOURS, 8760)
    return eng_obj._month, eng_obj._day, eng_obj._hour


def result(assessment, cid):
    return next(r for r in assessment.results if r.criterion_id == cid)


# ---- gates: the 2026 pack is now compliance-allowed --------------------------

def test_compliance_allowed_and_research_labelled(eng):
    assert eng.compliance_allowed() is True
    ra = eng.evaluate_room("r", "Bedroom", series_at(22.0), HOURS, mode="research")
    assert ra.mode == "research"
    rc = eng.evaluate_room("r", "Bedroom", series_at(22.0), HOURS, mode="compliance")
    assert rc.mode == "compliance"
    assert rc.verification_status == "source_verified"


def test_dwelling_category_required(eng):
    with pytest.raises(ValueError):
        eng.evaluate_room("r", "Bedroom", series_at(22.0), HOURS, category="III")


# ---- classification: home offices are living-type in 2026 --------------------

def test_home_office_is_living_type(eng):
    assert classify_room("Home office", eng.pack) == "living"
    assert classify_room("Stairwell", eng.pack) == "communal_circulation"


# ---- Trm running-mean chain (TM52 Eq 2.2/2.3 cross-reference) ----------------

def test_trm_constant_input():
    trm = running_mean_trm(np.full(365, 20.0))
    assert trm.shape == (153,)  # 1 May..30 Sep
    assert np.allclose(trm, 20.0)


def test_trm_recursion_matches_hand_computation():
    dm = np.full(365, 10.0)
    dm[150:] = 30.0  # step change at 31 May (doy index 150)
    trm = running_mean_trm(dm)
    # From TM52 Eq 2.2: Trm(d+1) = 0.8*Trm(d) + 0.2*Tdm(d). After the step, day-by-day:
    # Trm(1 Jun) = 0.8*Trm(31 May) + 0.2*Tdm(31 May)
    # Trm chain before the step is 10; Trm(31 May) = 0.8*10 + 0.2*dm[149](=10) = 10
    # Trm(1 Jun) = 0.8*10 + 0.2*30 = 14
    assert trm[31] == pytest.approx(14.0)   # index 31 = 1 June
    # one week later the chain continues from 14: 14*0.8^7 + 30*(1-0.8^7)
    expected = 14 * 0.8 ** 7 + 30 * (1 - 0.8 ** 7)
    assert trm[31 + 7] == pytest.approx(expected)


def test_trm_init_uses_weighted_seven_days():
    dm = np.full(365, 10.0)
    dm[118] = 90.0  # 29 April: huge outlier on the most recent day of the init window
    trm = running_mean_trm(dm)
    w = 0.8 ** np.arange(7)
    base = 10.0
    expected_30apr = (w[0] * 90.0 + w[1:].sum() * base) / w.sum()
    # Trm(1 May) = 0.8 * Trm(30 Apr) + 0.2 * Tdm(30 Apr)(=10)
    assert trm[0] == pytest.approx(0.8 * expected_30apr + 0.2 * base)


# ---- adaptive threshold clamps and categories --------------------------------

def test_adaptive_threshold_clamps(eng):
    # Constant outdoor daily means at the clamp Trm values.
    for trm_val, cat_i, cat_ii in ((5.0, 24.1, 25.1), (10.0, 24.1, 25.1),
                                   (30.0, 30.7, 31.7), (40.0, 30.7, 31.7)):
        dm = np.full(365, trm_val)
        th_i = eng._adaptive_thresholds(eng._criteria["a"], "I", dm)
        th_ii = eng._adaptive_thresholds(eng._criteria["a"], "II", dm)
        assert np.allclose(th_i, cat_i), (trm_val, th_i[:3])
        assert np.allclose(th_ii, cat_ii)
        assert np.allclose(th_ii - th_i, 1.0)  # Cat II is 1 K higher


def test_adaptive_threshold_midpoint(eng):
    th_ii = eng._adaptive_thresholds(eng._criteria["a"], "II", np.full(365, 20.0))
    assert np.allclose(th_ii, 0.33 * 20.0 + 21.8)  # 28.4


# ---- criterion a: delta-T rounding and hour limits ----------------------------

def test_criterion_a_delta_t_rounding_boundary(eng):
    """TM52 rounding: raw Delta T >= 0.5 K counts; 0.49 K does not."""
    dm = np.full(365, 20.0)
    th = 0.33 * 20.0 + 21.8  # 28.4 (Cat II), constant
    top = series_at(th + 0.49)
    ra = eng.evaluate_room("r", "Bedroom", top, HOURS, category="II",
                           daily_mean_outdoor=dm, mode="compliance")
    assert result(ra, "a").metric_value == 0.0
    top = series_at(th + 0.5)
    ra = eng.evaluate_room("r", "Bedroom", top, HOURS, category="II",
                           daily_mean_outdoor=dm, mode="compliance")
    assert result(ra, "a").metric_value == 3672.0  # every assessed hour counts


def test_criterion_a_bedroom_limit_flip(eng):
    """Bedroom variant: limit 110 h (3% of 3672). Exact flip 110/111."""
    eng._bind_calendar(HOURS, 8760)
    month, _, hour = eng._month, eng._day, eng._hour
    hot = np.isin(month, [5, 9]) & np.ones(8760, bool)  # May + Sep nights etc.
    # place exceedances in May, any hour (bedroom = all hours)
    may = (month == 5)
    idx = np.nonzero(may)[0]
    dm = np.full(365, 10.0)  # cold outdoor -> threshold at clamp 25.1 (Cat II)
    for n_hot, expected in ((110, "PASS"), (111, "FAIL")):
        top = series_at(20.0)
        top[idx[:n_hot]] = 30.0  # raw Delta T = 4.9 -> counts
        ra = eng.evaluate_room("r", "Bedroom", top, HOURS, category="II",
                               daily_mean_outdoor=dm, mode="compliance")
        a = result(ra, "a")
        assert a.status == expected, (n_hot, a.to_dict())
        assert a.basis["limit_hours"] == 110


def test_criterion_a_living_occupancy_and_limit(eng):
    """Living rooms: only 9 am-10 pm counts; limit 59 h. Exact flip 59/60."""
    eng._bind_calendar(HOURS, 8760)
    month, _, hour = eng._month, eng._day, eng._hour
    occupied = np.isin(month, [5]) & np.isin(hour, range(10, 23))
    idx = np.nonzero(occupied)[0]
    assert idx.size == 31 * 13  # May occupied hours: geometry guard (31 days x 13 h)
    dm = np.full(365, 10.0)
    for n_hot, expected in ((59, "PASS"), (60, "FAIL")):
        top = series_at(20.0)
        top[idx[:n_hot]] = 30.0
        # put the same heat at 3 am (outside living hours): must NOT count
        night = np.isin(month, [5]) & np.isin(hour, [1, 2, 3])
        top[np.nonzero(night)[0][:200]] = 30.0
        ra = eng.evaluate_room("r", "Living room", top, HOURS, category="II",
                               daily_mean_outdoor=dm, mode="compliance")
        a = result(ra, "a")
        assert a.status == expected, (n_hot, a.to_dict())
        assert a.metric_value == float(n_hot)  # night heat excluded


def test_criterion_a_months_window(eng):
    """April heat must not count (assessment window 1 May-30 Sep)."""
    eng._bind_calendar(HOURS, 8760)
    month, day, hour = eng._month, eng._day, eng._hour
    top = series_at(20.0)
    april_hot = (month == 4) & np.isin(hour, range(10, 23))
    top[np.nonzero(april_hot)[0]] = 35.0
    dm = np.full(365, 10.0)
    ra = eng.evaluate_room("r", "Living room", top, HOURS, category="II",
                           daily_mean_outdoor=dm, mode="compliance")
    assert result(ra, "a").metric_value == 0.0


# ---- criterion c: fixed 26 C, limits, fan uplift ------------------------------

def test_criterion_c_limit_flips_living_and_bedroom(eng):
    eng._bind_calendar(HOURS, 8760)
    month, _, hour = eng._month, eng._day, eng._hour
    occ_living = (month == 6) & np.isin(hour, range(10, 23))
    idx = np.nonzero(occ_living)[0]
    for n_hot, expected, room in ((59, "PASS", "Kitchen"),
                                  (60, "FAIL", "Kitchen")):
        top = series_at(20.0)
        top[idx[:n_hot]] = 27.0
        ra = eng.evaluate_room("r", room, top, HOURS, mode="compliance")
        assert result(ra, "c").status == expected, (n_hot, room)
    # exactly 26.0 does NOT exceed ("shall not exceed 26" -> strictly above counts)
    top = series_at(26.0)
    ra = eng.evaluate_room("r", "Kitchen", top, HOURS, mode="compliance")
    assert result(ra, "c").metric_value == 0.0


def test_criterion_c_bedroom_uses_all_hours_variant(eng):
    eng._bind_calendar(HOURS, 8760)
    month, _, hour = eng._month, eng._day, eng._hour
    may_nights = (month == 5) & np.isin(hour, [1, 2, 3, 4])
    idx = np.nonzero(may_nights)[0]
    top = series_at(20.0)
    top[idx] = 27.0  # 4 h x 31 days = 124 hot night hours, outside living hours
    ra = eng.evaluate_room("r", "Bedroom", top, HOURS, mode="compliance")
    c = result(ra, "c")
    assert c.basis["occupancy_basis"] == "all_hours"
    assert c.status == "FAIL" and c.metric_value == 124.0  # > 110 limit


def test_criterion_c_ceiling_fan_uplift(eng):
    eng._bind_calendar(HOURS, 8760)
    month, _, hour = eng._month, eng._day, eng._hour
    occ = (month == 6) & np.isin(hour, range(10, 23))
    idx = np.nonzero(occ)[0][:100]
    top = series_at(20.0)
    top[idx] = 27.5  # 100 hours at 27.5 C -> FAIL without uplift (>59)
    uplift = np.zeros(8760)
    uplift[idx] = 2.1  # fan uplift at those hours -> effective threshold 28.1
    ra = eng.evaluate_room("r", "Kitchen", top, HOURS, fan_uplift=uplift,
                           mode="compliance")
    assert result(ra, "c").status == "PASS"
    ra = eng.evaluate_room("r", "Kitchen", top, HOURS, mode="compliance")
    assert result(ra, "c").status == "FAIL"


# ---- criterion b: nights, category thresholds, sleep window -------------------

def _hot_nights(month, day, hour, nights, temp, top):
    for m, d in nights:
        night = (((month == m) & (day == d) & (hour == 24))
                 | ((month == m) & (day == d + 1) & np.isin(hour, range(1, 9))))
        top[np.nonzero(night)[0]] = temp
    return top


def test_criterion_b_night_limit_flip(eng):
    eng._bind_calendar(HOURS, 8760)
    month, day, hour = eng._month, eng._day, eng._hour
    nights = [(6, d) for d in (5, 6, 7, 8, 9)]  # 5 hot nights
    for n, expected in ((4, "PASS"), (5, "FAIL")):
        top = series_at(20.0)
        _hot_nights(month, day, hour, nights[:n], 28.0, top)
        ra = eng.evaluate_room("r", "Master Bedroom", top, HOURS, category="II",
                               mode="compliance")
        b = result(ra, "b")
        assert b.status == expected, (n, b.to_dict())
        assert b.basis["nights_assessed"] == 153  # 1 May..30 Sep geometry


def test_criterion_b_category_thresholds(eng):
    eng._bind_calendar(HOURS, 8760)
    month, day, hour = eng._month, eng._day, eng._hour
    # 5 nights averaging 26.5 C: exceeds Tn(I)=26 on 5 nights (>4 -> FAIL),
    # never exceeds Tn(II)=27 (0 nights -> PASS).
    top = _hot_nights(month, day, hour,
                      [(7, 10), (7, 11), (7, 12), (7, 13), (7, 14)], 26.5,
                      series_at(20.0))
    ra_i = eng.evaluate_room("r", "Master Bedroom", top, HOURS, category="I",
                             mode="compliance")
    ra_ii = eng.evaluate_room("r", "Master Bedroom", top, HOURS, category="II",
                              mode="compliance")
    bi = result(ra_i, "b")
    bii = result(ra_ii, "b")
    assert bi.status == "FAIL" and bi.metric_value == 5.0   # 26.5 > Tn(I)=26
    assert bii.status == "PASS" and bii.metric_value == 0.0  # 26.5 <= Tn(II)=27


def test_criterion_b_mean_not_max(eng):
    """A night averaging 26.5 with a 30 C peak must not exceed Tn(II)=27 — the
    criterion tests the MEAN night operative temperature, not the peak."""
    eng._bind_calendar(HOURS, 8760)
    month, day, hour = eng._month, eng._day, eng._hour
    top = series_at(25.0)
    m, d = 7, 20
    night = (((month == m) & (day == d) & (hour == 24))
             | ((month == m) & (day == d + 1) & np.isin(hour, range(1, 9))))
    idx = np.nonzero(night)[0]
    top[idx[:1]] = 34.0  # one very hot hour: mean = (34 + 8*25)/9 = 26.44 <= 27
    ra = eng.evaluate_room("r", "Master Bedroom", top, HOURS, category="II",
                           mode="compliance")
    b = result(ra, "b")
    assert b.status == "PASS"
    assert b.basis["failing_night_dates"] == []


# ---- criterion d: communal areas ---------------------------------------------

def test_criterion_d_limit_flip(eng):
    eng._bind_calendar(HOURS, 8760)
    month = eng._month
    may_idx = np.nonzero(month == 5)[0]
    for n_hot, expected in ((110, "PASS"), (111, "FAIL")):
        top = series_at(20.0)
        top[may_idx[:n_hot]] = 29.0  # > 28 C
        ra = eng.evaluate_room("r", "Corridor", top, HOURS, mode="compliance")
        d = result(ra, "d")
        assert d.status == expected, (n_hot, d.to_dict())
    top = series_at(28.0)  # exactly 28 does not exceed
    ra = eng.evaluate_room("r", "Corridor", top, HOURS, mode="compliance")
    assert result(ra, "d").metric_value == 0.0


# ---- stages and passport ------------------------------------------------------

def test_stages_and_passport(eng):
    stages = eng.stages()
    assert [s["id"] for s in stages] == ["stage_1", "stage_2", "stage_3"]
    assert stages[0]["criteria"] == ["a", "b"]
    assert stages[2]["criteria"] == ["b", "c"]
    p = eng.standards_passport()
    assert p["source_status"] == "source_verified"
    assert "S-08" in p["source_refs"]
    assert p["weather_requirements"]["verified"] is True
