"""Comfort wrapper tests (Phase 4, RULE 4).

Parity: wrapper outputs must equal direct library calls (mathematics are never
reimplemented). Applicability: out-of-range inputs produce explicit non-results,
never numbers and never crashes.
"""

from __future__ import annotations

import pythermalcomfort
from pythermalcomfort.models import adaptive_en, pmv_ppd_iso, utci

from overheatlens.comfort import (
    ComfortResult,
    adaptive_comfort_en,
    pmv_ppd,
    utci_comfort,
)


def test_library_version_recorded():
    r = pmv_ppd(tdb=25, tr=25, vr=0.1, rh=50, met=1.2, clo=0.5)
    assert r.provenance["library_version"] == pythermalcomfort.__version__
    assert r.standard_edition == "ISO 7730:2025"  # library default model


def test_pmv_ppd_parity_with_library():
    r = pmv_ppd(tdb=25, tr=25, vr=0.1, rh=50, met=1.2, clo=0.5)
    direct = pmv_ppd_iso(tdb=25, tr=25, vr=0.1, rh=50, met=1.2, clo=0.5)
    assert r.status == "OK"
    assert r.values["pmv"] == direct.pmv
    assert r.values["ppd"] == direct.ppd


def test_pmv_ppd_neutral_condition():
    """The classic ISO 7730 neutral point: PMV ~ 0, PPD ~ 5% (lower bound)."""
    r = pmv_ppd(tdb=24.5, tr=24.5, vr=0.05, rh=50, met=1.2, clo=0.5)
    assert r.status == "OK"
    assert abs(r.values["pmv"]) < 0.2
    assert 4.5 <= r.values["ppd"] <= 7


def test_pmv_ppd_outside_applicability():
    r = pmv_ppd(tdb=35, tr=25, vr=0.1, rh=50, met=1.2, clo=0.5)  # tdb > 30
    assert r.status == "OUTSIDE_APPLICABILITY"
    assert r.values == {}
    assert "outside 10-30" in r.reason
    r2 = pmv_ppd(tdb=25, tr=25, vr=2.0, rh=50, met=1.2, clo=0.5)  # vr > 1
    assert r2.status == "OUTSIDE_APPLICABILITY"
    assert r2.reason and "vr" in r2.reason


def test_adaptive_en_parity_and_categories():
    r = adaptive_comfort_en(tdb=26, tr=26, t_running_mean=20, v=0.1)
    direct = adaptive_en(tdb=26, tr=26, t_running_mean=20, v=0.1)
    assert r.status == "OK"
    assert r.values["tmp_cmf"] == direct.tmp_cmf
    # EN 16798-1 Cat II upper = 0.33*Trm + 20.8 + 3? (library definition);
    # parity is the test, values are the library's
    assert r.values["tmp_cmf_cat_ii_up"] == direct.tmp_cmf_cat_ii_up


def test_adaptive_en_outside_trm_range():
    r = adaptive_comfort_en(tdb=32, tr=32, t_running_mean=31, v=0.1)
    assert r.status == "OUTSIDE_APPLICABILITY"
    assert "10-30" in r.reason
    r2 = adaptive_comfort_en(tdb=26, tr=26, t_running_mean=20, v=1.5)
    assert r2.status == "OUTSIDE_APPLICABILITY"
    assert "1.2" in r2.reason


def test_utci_parity_and_gates():
    r = utci_comfort(tdb=30, tr=32, v=1.0, rh=50)
    direct = utci(tdb=30, tr=32, v=1.0, rh=50)
    assert r.status == "OK"
    assert r.values["utci"] == direct.utci
    r2 = utci_comfort(tdb=30, tr=30, v=0.1, rh=50)  # below 0.5 m/s
    assert r2.status == "OUTSIDE_APPLICABILITY"
    assert "0.5-17" in r2.reason


def test_result_serialisable():
    import json

    for r in (pmv_ppd(tdb=25, tr=25, vr=0.1, rh=50, met=1.2, clo=0.5),
              adaptive_comfort_en(tdb=26, tr=26, t_running_mean=20, v=0.1),
              utci_comfort(tdb=30, tr=32, v=1.0, rh=50),
              pmv_ppd(tdb=99, tr=25, vr=0.1, rh=50, met=1.2, clo=0.5)):
        json.dumps(r.to_dict())
