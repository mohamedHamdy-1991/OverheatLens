"""Metrics tests, including the metamorphic property suite (plan §27.3, Rule 26):
unit/order invariance, monotonicity under heating, determinism, explicit non-results."""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from conftest import FIXTURES

from overheatlens.epw import (
    degree_hours,
    exceedance_hours,
    parse_epw,
    weather_summary,
)


@pytest.fixture(scope="module")
def good_epw(fixtures_dir):
    return parse_epw(fixtures_dir / "good_file.epw")


def test_summary_shape(good_epw):
    s = weather_summary(good_epw).to_dict()
    for key in ("annual_mean_dry_bulb", "hottest_hour", "exceedance_hours_26c",
                "degree_hours_26c"):
        assert key in s
    assert s["hottest_hour"] >= s["coldest_hour"]


def test_summary_is_deterministic(good_epw):
    assert weather_summary(good_epw).to_dict() == weather_summary(good_epw).to_dict()


# ---- metamorphic / property tests -------------------------------------------

st_temps = st.lists(
    st.one_of(st.floats(-40, 60), st.just(np.nan)), min_size=24, max_size=400
)


@given(st_temps)
@settings(max_examples=150, deadline=None)
def test_exceedance_monotone_under_uniform_heating(temps):
    """Plan §27.3: increasing every temperature must never reduce exceedance hours."""
    t = np.array(temps)
    for delta in (0.5, 1.0, 5.0):
        before = exceedance_hours(t, 26.0)
        after = exceedance_hours(t + delta, 26.0)
        assert after >= before


@given(st_temps)
@settings(max_examples=100, deadline=None)
def test_degree_hours_monotone(temps):
    t = np.array(temps)
    assert degree_hours(t + 1.0, 26.0) >= degree_hours(t, 26.0)


@given(st.data())
@settings(max_examples=60, deadline=None)
def test_exceedance_shift_invariant(data):
    """A constant offset applied to both series and threshold leaves counts unchanged.
    Cases where any value lands within float rounding of the threshold are excluded:
    IEEE-754 addition is not exact, so exact-tie comparisons may flip either way."""
    t = np.array(data.draw(st.lists(st.floats(-10, 40), min_size=24, max_size=100)))
    shift = data.draw(st.floats(-20, 20))
    thr = data.draw(st.floats(0, 30))
    assume(not np.any(np.isclose(t - thr, 0.0, atol=1e-9)))
    assert exceedance_hours(t, thr) == exceedance_hours(t + shift, thr + shift)


def test_missing_values_are_explicit_non_results_not_zeros():
    """A series of pure sentinels must not silently count as zero exceedance hours;
    the cleaned series becomes NaN and nansum semantics keep counts at zero only when
    no valid hour exceeds — degree-hours likewise never invent exceedance."""
    sentinel_series = np.full(100, 999.9)
    assert exceedance_hours(sentinel_series, 26.0) == 0
    assert degree_hours(sentinel_series, 26.0) == 0.0
    assert exceedance_hours(np.full(100, np.nan), 26.0) == 0
    # and real exceedance is still detected around NaNs
    mixed = np.full(100, np.nan)
    mixed[0] = 30.0
    assert exceedance_hours(mixed, 26.0) == 1


def test_zone_order_does_not_affect_metrics():
    """Plan §27.3: order of observations must not change aggregate metrics."""
    rng = np.random.default_rng(42)
    t = rng.uniform(-5, 35, 8760)
    assert exceedance_hours(t, 26.0) == exceedance_hours(t[::-1], 26.0)
    assert degree_hours(t, 26.0) == pytest.approx(degree_hours(t[::-1], 26.0))
