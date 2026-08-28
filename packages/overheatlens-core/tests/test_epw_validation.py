"""Checker tests: every planted fault in the synthetic fixture family must be caught,
and healthy files must pass cleanly. Thresholds are calibrated, not arbitrary —
see VALIDATION_MATRIX.md rows V-EPW-03..08."""

from __future__ import annotations

import pytest

from conftest import FIXTURES

from overheatlens.epw import check_epw, parse_epw


def _codes(path) -> set[str]:
    return {i.code for i in check_epw(parse_epw(path)).issues}


def test_good_file_passes_clean(fixtures_dir):
    rep = check_epw(parse_epw(fixtures_dir / "good_file.epw"))
    assert rep.status == "PASS"
    assert rep.issues == []


def test_leap_year_passes(fixtures_dir):
    rep = check_epw(parse_epw(fixtures_dir / "leap_year.epw"))
    assert rep.status == "PASS"


def test_missing_hours_detected(fixtures_dir):
    rep = check_epw(parse_epw(fixtures_dir / "missing_hours.epw"))
    assert rep.status == "FAIL"
    assert "ROW_COUNT" in _codes(fixtures_dir / "missing_hours.epw")


def test_sentinels_and_out_of_range_detected(fixtures_dir):
    codes = _codes(fixtures_dir / "sentinel_values.epw")
    assert "MISSING_SENTINEL" in codes
    assert "OUT_OF_RANGE" in codes


def test_dewpoint_violation_detected(fixtures_dir):
    rep = check_epw(parse_epw(fixtures_dir / "dewpoint_violation.epw"))
    assert rep.status == "FAIL"
    assert "DEWPOINT_VIOLATION" in _codes(fixtures_dir / "dewpoint_violation.epw")


def test_impossible_rh_detected(fixtures_dir):
    assert "OUT_OF_RANGE" in _codes(fixtures_dir / "impossible_rh.epw")


def test_temp_spike_caught_by_discontinuity(fixtures_dir):
    rep = check_epw(parse_epw(fixtures_dir / "temp_spike.epw"))
    codes = {i.code for i in rep.issues}
    assert "DISCONTINUITY" in codes
    assert rep.status == "FAIL"  # 16.2 K/h exceeds the 15 K/h error bound


def test_stuck_sensor_caught(fixtures_dir):
    rep = check_epw(parse_epw(fixtures_dir / "stuck_sensor.epw"))
    codes = {i.code for i in rep.issues}
    assert "STUCK_SENSOR" in codes
    assert rep.status == "PASS_WITH_WARNINGS"


def test_report_shape(fixtures_dir):
    rep = check_epw(parse_epw(fixtures_dir / "good_file.epw"))
    d = rep.to_dict()
    assert d["status"] == "PASS"
    assert len(d["sha256"]) == 64
    assert d["n_rows"] == 8760
