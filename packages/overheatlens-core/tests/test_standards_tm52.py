"""TM52 tests — values locked to the machine-verified official PDF (S-04):

* Tmax = 0.33 Trm + 21.8 (Cat II, Eq 8) / + 20.8 (Cat I); clamped outside Trm 10-30
* Criterion 1 (He): hours with rounded DT >= 1 K (raw >= 0.5) in May-Sept occupied
  hours; fail if > 3% of model-supplied occupied hours
* Criterion 2 (We): We = sum(hours x wf) per day, wf = rounded DT if > 0 else 0;
  fail if > 6 on any one day (Eq 10)
* Criterion 3 (Tupp): raw DT > 4 K at any hour in May-Sept -> fail
"""

from __future__ import annotations

import numpy as np
import pytest

from overheatlens.standards import StandardsEngine

from conftest import series_at


HOURS = (np.arange(8760) % 24) + 1
DM = np.full(365, 15.0)  # Trm 15 -> Tmax(II) = 26.75


@pytest.fixture(scope="module")
def eng():
    return StandardsEngine.load("uk_tm52")


OFFICE_OCC = np.isin(HOURS, range(9, 18))  # 9 am-5 pm, 8 h/day, 244 working days May-Sept


def result(assessment, cid):
    return next(r for r in assessment.results if r.criterion_id == cid)


def test_criterion_1_rounding_and_denominator(eng):
    # Top 27.2: raw DT 0.45 -> not counted -> He 0% -> PASS
    ra = eng.evaluate_room("o", "Office", series_at(27.2), HOURS, occupancy=OFFICE_OCC,
                           category="II", daily_mean_outdoor=DM, mode="compliance")
    assert result(ra, "c1").metric_value == 0.0
    # Top 27.25: raw DT 0.5 -> every occupied hour counts -> 100% > 3% -> FAIL
    ra = eng.evaluate_room("o", "Office", series_at(27.25), HOURS, occupancy=OFFICE_OCC,
                           category="II", daily_mean_outdoor=DM, mode="compliance")
    c1 = result(ra, "c1")
    assert c1.status == "FAIL" and c1.metric_value == 100.0
    # engine intersects occupancy with the May-Sept window: 9 h x 153 days
    assert c1.basis["occupied_hours_basis"] == 9 * 153


def test_criterion_1_without_occupancy_not_evaluated(eng):
    ra = eng.evaluate_room("o", "Office", series_at(27.0), HOURS, category="II",
                           daily_mean_outdoor=DM, mode="compliance")
    assert result(ra, "c1").status == "NOT_EVALUATED"


def test_criterion_2_weighted_exceedance_hand_example(eng):
    """TM52 §6.1.2 worked example: 3 h at DT=1, 2 h at DT=2, 1 h at DT=3 in one day
    -> We = 3*1 + 2*2 + 1*3 = 10 > 6 -> FAIL (document example uses half hours and
    gets 5; with full hours the same pattern doubles to 10)."""
    eng._bind_calendar(HOURS, 8760)
    month, hour = eng._month, eng._hour
    occ_day = (month == 7) & (hour >= 9) & (hour <= 16)  # one office day, 8 hours
    idx = np.nonzero(occ_day)[0]
    top = series_at(26.0)  # DT <= 0 elsewhere (Tmax 26.75)
    top[idx[0:3]] = 27.9   # DT = 1.15 -> rounded 1
    top[idx[3:5]] = 28.9   # DT = 2.15 -> rounded 2
    top[idx[5]] = 29.9     # DT = 3.15 -> rounded 3
    ra = eng.evaluate_room("o", "Office", top, HOURS, occupancy=OFFICE_OCC,
                           category="II", daily_mean_outdoor=DM, mode="compliance")
    c2 = result(ra, "c2")
    assert c2.status == "FAIL"
    assert c2.basis["worst_day_we"] == 10.0
    assert c2.basis["worst_day"] == "07-01"


def test_criterion_2_passes_at_we_6(eng):
    """We exactly 6 (e.g. 6 h at DT=1) is NOT a fail (criterion: We <= 6)."""
    eng._bind_calendar(HOURS, 8760)
    month, hour = eng._month, eng._hour
    occ_day = (month == 7) & (hour >= 9) & (hour <= 16)
    idx = np.nonzero(occ_day)[0]
    top = series_at(26.0)
    top[idx[0:6]] = 27.9  # 6 hours at DT ~1.15 -> rounded 1 each -> We = 6
    ra = eng.evaluate_room("o", "Office", top, HOURS, occupancy=OFFICE_OCC,
                           category="II", daily_mean_outdoor=DM, mode="compliance")
    c2 = result(ra, "c2")
    assert c2.status == "PASS" and c2.basis["worst_day_we"] == 6.0


def test_criterion_3_raw_4k_no_rounding(eng):
    """Raw DT > 4 K fails at a single hour; 4.0 exactly does not (strict)."""
    eng._bind_calendar(HOURS, 8760)
    month, hour = eng._month, eng._hour
    hot_day = (month == 7) & (hour == 15)
    idx = np.nonzero(hot_day)[0]
    top = series_at(30.75)  # raw DT = 4.0 exactly -> NOT a fail
    top[idx] = 30.75
    ra = eng.evaluate_room("o", "Office", top, HOURS, occupancy=OFFICE_OCC,
                           category="II", daily_mean_outdoor=DM, mode="compliance")
    assert result(ra, "c3").metric_value == 0.0
    top[idx] = 30.76  # raw DT = 4.01 on 31 July days (hour 15 each)
    ra = eng.evaluate_room("o", "Office", top, HOURS, occupancy=OFFICE_OCC,
                           category="II", daily_mean_outdoor=DM, mode="compliance")
    c3 = result(ra, "c3")
    assert c3.status == "FAIL" and c3.metric_value == 31.0


def test_tm52_overheating_requires_two_criteria():
    """TM52 §6.1.2: a room is overheating if ANY TWO of the three criteria fail.
    Recorded here as documentation of the aggregation rule for the UI layer; the
    engine reports per-criterion results and leaves the 2-of-3 verdict explicit."""
    pack = StandardsEngine.load("uk_tm52").pack
    assert any("ANY TWO" in r for r in pack["report_requirements"])
