"""Standards engine tests: exact criterion boundaries, window logic, room
classification, evaluation gates, and NOT_EVALUATED honesty.

These rows back VALIDATION_MATRIX.md VAL-STD-01..06. The tests lock the
implementation to the values recorded in SOURCE_REGISTER.md; if a value is later
corrected from an original source, the change here is a visible, reviewed diff (RULE 7).
"""

from __future__ import annotations

import numpy as np
import pytest

from overheatlens.schemas import RulePackError
from overheatlens.standards import (
    BlockedRulePack,
    EvaluationMode,
    SourceNotVerified,
    StandardsEngine,
    classify_room,
)

from conftest import series_at


# ---- helpers -----------------------------------------------------------------

def sleep_labels() -> np.ndarray:
    return (np.arange(8760) % 24) + 1


def result_by_id(assessment, cid):
    return next(r for r in assessment.results if r.criterion_id == cid)


# ---- classification ----------------------------------------------------------

def test_classify_room():
    pack = StandardsEngine.load("uk_tm59_2017").pack
    assert classify_room("Master Bedroom", pack) == "bedroom"
    assert classify_room("Bedroom 2", pack) == "bedroom"
    assert classify_room("Open Plan Living Kitchen", pack) == "living"
    assert classify_room("Kitchen", pack) == "living"
    assert classify_room("Hallway", pack) == "other"
    assert classify_room("Unknown Space", pack) == "other"


# ---- Criterion A boundary (VAL-STD-01) ---------------------------------------

def test_criterion_a_exact_boundary():
    eng = StandardsEngine.load("uk_tm59_2017")
    # 3% of 8760 = 262.8 -> 262 hours PASS, 263 hours FAIL (operator '>')
    idx = np.arange(262)  # first 262 hours of the year
    top = series_at(20.0)
    top[idx] = 27.0  # condition: top - 26 >= 1.0
    ra = eng.evaluate_room("r", "Living room", top, sleep_labels(), mode="research")
    a = result_by_id(ra, "A")
    assert a.passed is True and a.metric_value == pytest.approx(262 * 100 / 8760, abs=1e-4)

    top[262] = 27.0  # 263 exceedance hours
    ra = eng.evaluate_room("r", "Living room", top, sleep_labels(), mode="research")
    a = result_by_id(ra, "A")
    assert a.passed is False and a.status == "FAIL"
    assert a.margin > 0


def test_criterion_a_condition_threshold():
    eng = StandardsEngine.load("uk_tm59_2017")
    # exactly 27.0C counts (>= 1.0 K over 26); 26.9C does not
    top = series_at(26.9)
    ra = eng.evaluate_room("r", "Living room", top, sleep_labels(), mode="research")
    assert result_by_id(ra, "A").basis["exceedance_hours"] == 0
    top = series_at(27.0)
    ra = eng.evaluate_room("r", "Living room", top, sleep_labels(), mode="research")
    assert result_by_id(ra, "A").basis["exceedance_hours"] == 8760


# ---- Criterion B boundary + window logic (VAL-STD-02) -------------------------

def test_criterion_b_exact_boundary_in_sleep_window():
    eng = StandardsEngine.load("uk_tm59_2017")
    hours = sleep_labels()
    sleep_mask = np.isin(hours, (23, 24, 1, 2, 3, 4, 5, 6, 7))
    assert sleep_mask.sum() == 9 * 365  # window geometry guard

    top = series_at(20.0)
    sleep_idx = np.nonzero(sleep_mask)[0]
    top[sleep_idx[:87]] = 27.0
    ra = eng.evaluate_room("r", "Bedroom", top, hours, mode="research")
    b = result_by_id(ra, "B")
    assert b.passed is True  # 87/8760 = 0.993% <= 1%

    top[sleep_idx[87]] = 27.0  # 88 hours = 1.0046% > 1%
    ra = eng.evaluate_room("r", "Bedroom", top, hours, mode="research")
    assert result_by_id(ra, "B").passed is False


def test_criterion_b_ignores_daytime_exceedance():
    eng = StandardsEngine.load("uk_tm59_2017")
    hours = sleep_labels()
    top = series_at(20.0)
    day_idx = np.nonzero(~np.isin(hours, (23, 24, 1, 2, 3, 4, 5, 6, 7)))[0]
    top[day_idx[:500]] = 30.0  # 500 hot daytime hours must not affect B
    ra = eng.evaluate_room("r", "Bedroom", top, hours, mode="research")
    b = result_by_id(ra, "B")
    assert b.basis["exceedance_hours"] == 0
    assert b.passed is True


def test_sleep_window_boundary_labels():
    """Label 22 (21:00-22:00) is OUTSIDE the 22:00-07:00 window; label 7
    (06:00-07:00) is INSIDE it. Hour-ending geometry, not labels-as-hours."""
    eng = StandardsEngine.load("uk_tm59_2017")
    hours = sleep_labels()
    top = series_at(20.0)
    hot = 29.0
    idx_of_label = lambda lbl: np.nonzero(hours == lbl)[0][0]  # noqa: E731
    top[idx_of_label(22)] = hot  # before the window
    ra = eng.evaluate_room("r", "Bedroom", top, hours, mode="research")
    assert result_by_id(ra, "B").basis["exceedance_hours"] == 0
    top[idx_of_label(7)] = hot  # 06:00-07:00, last window hour
    ra = eng.evaluate_room("r", "Bedroom", top, hours, mode="research")
    assert result_by_id(ra, "B").basis["exceedance_hours"] == 1


# ---- Criterion C (VAL-STD-03) -------------------------------------------------

def test_criterion_c_exact_boundary():
    eng = StandardsEngine.load("uk_tm59_2017")
    hours = sleep_labels()
    sleep_idx = np.nonzero(np.isin(hours, (23, 24, 1, 2, 3, 4, 5, 6, 7)))[0]

    top = series_at(20.0)
    top[sleep_idx[:32]] = 26.5  # 32 hours above 26C -> not > 32 -> PASS
    ra = eng.evaluate_room("r", "Bedroom", top, hours, mode="research")
    c = result_by_id(ra, "C")
    assert c.passed is True and c.metric_value == 32.0

    top[sleep_idx[32]] = 26.5  # 33 hours -> FAIL
    ra = eng.evaluate_room("r", "Bedroom", top, hours, mode="research")
    c = result_by_id(ra, "C")
    assert c.passed is False and c.status == "FAIL"


def test_criterion_c_strictly_above_26():
    eng = StandardsEngine.load("uk_tm59_2017")
    top = series_at(26.0)  # exactly 26C: 'exceeds 26' is strict
    ra = eng.evaluate_room("r", "Bedroom", top, sleep_labels(), mode="research")
    assert result_by_id(ra, "C").basis["exceedance_hours"] == 0


# ---- NOT_EVALUATED honesty -----------------------------------------------------

def test_criterion_d_never_passes():
    eng = StandardsEngine.load("uk_tm59_2017")
    ra = eng.evaluate_room("r", "Hallway", series_at(20.0), sleep_labels(),
                           mode="research")
    d = result_by_id(ra, "D")
    assert d.passed is None and d.status == "NOT_EVALUATED"
    assert ra.passed is False  # a room with an unevaluated criterion never 'passes'


def test_dwelling_incomplete_with_non_evaluated_room():
    eng = StandardsEngine.load("uk_tm59_2017")
    hours = sleep_labels()
    res = eng.evaluate_dwelling([
        ("r1", "Living room", series_at(20.0)),
        ("r2", "Master Bedroom", series_at(20.0)),
        ("r3", "Hallway", series_at(20.0)),
    ], hours, mode="research")
    assert res["overall"] == "INCOMPLETE"  # never silently PASS


def test_dwelling_fails_if_any_room_fails():
    eng = StandardsEngine.load("uk_tm59_2017")
    hours = sleep_labels()
    hot_living = series_at(27.5)
    res = eng.evaluate_dwelling([
        ("r1", "Living room", hot_living),
        ("r2", "Master Bedroom", series_at(20.0)),
    ], hours, mode="research")
    assert res["overall"] == "FAIL"


# ---- evaluation gates (VAL-STD-04) ---------------------------------------------

def test_blocked_pack_refused_everywhere():
    """A pack whose source is not acquired is refused in every mode. TM59:2026 is now
    source-verified, so a synthetic blocked pack exercises this gate (ADR-0005 path)."""
    from overheatlens.schemas import validate_pack_dict

    pack = {
        "rule_pack": "xx_synthetic_blocked",
        "version": "1.0.0",
        "title": "Synthetic blocked pack for gate testing",
        "publisher": "Test",
        "source_status": "blocked_no_source",
        "source_refs": ["S-03"],
        "blocked": "SOURCE_NOT_ACQUIRED",
        "assessment": {"period": "full_year", "hour_basis": 8760},
        "space_types": {"bedroom": {"aliases": ["bedroom"], "criteria": []}},
        "criteria": [],
    }
    validate_pack_dict(pack)
    eng = StandardsEngine(pack)
    with pytest.raises(BlockedRulePack):
        eng.evaluate_room("r", "Bedroom", series_at(20.0), sleep_labels(),
                          mode="research")
    with pytest.raises(BlockedRulePack):
        eng.evaluate_room("r", "Bedroom", series_at(20.0), sleep_labels(),
                          mode="compliance")
    assert eng.compliance_allowed() is False


def test_pending_pack_refused_in_compliance_allowed_in_research():
    eng = StandardsEngine.load("uk_tm59_2017")
    with pytest.raises(SourceNotVerified):
        eng.evaluate_room("r", "Bedroom", series_at(20.0), sleep_labels(),
                          mode="compliance")
    assert eng.compliance_allowed() is False
    ra = eng.evaluate_room("r", "Bedroom", series_at(20.0), sleep_labels(),
                           mode="research")
    assert ra.mode == "research"
    assert ra.verification_status == "secondary_pending"


def test_result_dicts_serialisable():
    eng = StandardsEngine.load("uk_tm59_2017")
    res = eng.evaluate_dwelling(
        [("r1", "Living room", series_at(20.0))], sleep_labels(), mode="research"
    )
    import json

    json.dumps(res)  # must not raise


# ---- Part O pack behaviour (VAL-STD-05) -----------------------------------------

def test_part_o_inherits_and_gates():
    eng = StandardsEngine.load("uk_part_o_dynamic")
    # criteria inherited from TM59:2017 -> compliance refused until S-02 verified
    with pytest.raises(SourceNotVerified):
        eng.evaluate_room("r", "Bedroom", series_at(20.0), sleep_labels(),
                          mode="compliance")
    ra = eng.evaluate_room("r", "Master Bedroom", series_at(20.0), sleep_labels(),
                           mode="research")
    assert ra.pack_id == "uk_part_o_dynamic"
    assert {r.criterion_id for r in ra.results} == {"B", "C"}

    limits = eng.model_limits()
    assert {m["id"] for m in limits} >= {"PO-WIN-01", "PO-WIN-02", "PO-WIN-03",
                                         "PO-WIN-04"}
    assert all(m["verification"]["status"] == "source_verified" for m in limits)
    excl = eng.strategy_exclusions()
    assert {e["id"] for e in excl} == {"PO-EXC-01", "PO-EXC-02"}


def test_standards_passport_contents():
    eng = StandardsEngine.load("uk_part_o_dynamic")
    p = eng.standards_passport()
    for key in ("name", "rule_pack", "version", "publisher", "edition",
                "source_status", "weather_requirements", "criteria_ids"):
        assert key in p


# ---- robustness -----------------------------------------------------------------

def test_wrong_series_length_refused():
    eng = StandardsEngine.load("uk_tm59_2017")
    with pytest.raises(ValueError):
        eng.evaluate_room("r", "Bedroom", series_at(20.0, n=100), np.arange(100) % 24,
                          mode="research")


def test_unsupported_condition_rejected(monkeypatch):
    eng = StandardsEngine.load("uk_tm59_2017")
    eng._bind_calendar(sleep_labels(), 8760)
    bad = dict(eng._criteria["A"])
    bad["condition"] = "top_c ^ 2 > 4"
    with pytest.raises(RulePackError):
        eng._evaluate_criterion(bad, series_at(20.0), "living")
