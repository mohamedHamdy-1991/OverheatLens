"""EnergyPlus worker + end-to-end pipeline tests (Phase 6).

Skipped automatically when no official EnergyPlus binary is installed locally.
Backs VALIDATION_MATRIX rows VAL-XSIM-01..03 (first real end-to-end evidence).
"""

from __future__ import annotations

import numpy as np
import pytest

from conftest import REPO_ROOT

from overheatlens.worker import (
    EnergyPlusError,
    ErrSummary,
    find_energyplus,
    parse_err,
    run_energyplus,
    harvest_hourly,
)
from overheatlens.idf import check_idf, parse_idf
from overheatlens.standards import StandardsEngine
from overheatlens.epw import parse_epw

IDF = REPO_ROOT / "fixtures" / "idf" / "synthetic_dwelling.idf"
# Real CIBSE weather file held locally only (copyrighted, never committed)
WF = ("/Users/mohamedali/Library/CloudStorage/OneDrive-LeedsBeckettUniversity/"
      "Work/Ph.D/DataBase/DataBase/LEEDS Weather Files/Weather File MET Office/"
      "Leeds_DSY1_2020High50_.epw")

_bins = find_energyplus()
_has_eplus = bool(_bins)
_has_wf = bool(WF and __import__("pathlib").Path(WF).exists())

pytestmark = pytest.mark.skipif(
    not (_has_eplus and _has_wf),
    reason="requires an installed EnergyPlus binary and the local Leeds weather file")


@pytest.fixture(scope="module")
def run():
    return run_energyplus(IDF, WF, timeout_s=600)


def test_find_energyplus_official_binary():
    assert _bins, "no EnergyPlus binary found"
    assert _bins[0]["version"].startswith("25."), _bins  # ADR-0004 working pin


def test_run_completes_clean(run):
    assert run.status == "complete"
    assert run.energyplus_version == "25.1.0"
    assert run.err.fatal == [] and run.err.severe == []
    assert run.err.is_usable
    assert run.csv_path is not None and run.csv_path.exists()
    manifest = run.manifest
    assert manifest["idf_sha256"] and manifest["epw_sha256"]
    assert manifest["status"] == "complete"


def test_run_rejects_missing_inputs(tmp_path):
    with pytest.raises(FileNotFoundError):
        run_energyplus(tmp_path / "no.idf", WF)


def test_harvest_produces_8760_operative_hours(run):
    zones = harvest_hourly(run.csv_path)
    assert set(zones) == {"living room", "bedroom 1"}
    for name, series in zones.items():
        assert len(series["top"]) == 8760
        top = np.asarray(series["top"])
        assert 0 < np.nanmean(top) < 45  # sanity for a UK dwelling
        # derived metric consistency: top == 0.5*(mat+mrt)
        assert np.allclose(top, 0.5 * (np.asarray(series["mat"])
                                       + np.asarray(series["mrt"])))


def test_harvest_captures_relative_humidity(run):
    """The fixture models output Zone Air Relative Humidity; harvest must carry it."""
    zones = harvest_hourly(run.csv_path)
    for name, series in zones.items():
        assert series["rh"] is not None, f"{name}: RH output missing from harvest"
        rh = np.asarray(series["rh"])
        assert len(rh) == 8760
        assert np.isfinite(rh).all() and (rh >= 0).all() and (rh <= 100).all()


def test_end_to_end_compliance_evaluation(run):
    """The heart of the pipeline: readiness -> simulate -> harvest -> evaluate."""
    assert check_idf(parse_idf(IDF)).status == "PASS"
    zones = harvest_hourly(run.csv_path)
    epw = parse_epw(WF)
    db = epw.valid_dry_bulb()
    daily = np.nanmean(db.reshape(-1, 24), axis=1)
    eng = StandardsEngine.load("uk_tm59_2017")
    rooms = [(z, z.replace("_", " ").title(), np.asarray(v["top"]))
             for z, v in zones.items()]
    res = eng.evaluate_dwelling(rooms, category="II", daily_mean_outdoor=daily,
                                mode="compliance")
    assert res["overall"] in ("PASS", "FAIL", "INCOMPLETE")
    # every criterion result must carry provenance (RULE 6)
    for r in res["rooms"]:
        for c in r["criteria"]:
            assert c["rule_ref"]
            assert c["verification_status"] == "source_verified"
            if c["passed"] is not None:
                assert c["basis"]["exceedance_hours"] is not None


def test_parse_err_groups_severities(tmp_path):
    p = tmp_path / "eplusout.err"
    p.write_text(
        "** Warning  ** Something mild\n"
        "   ~~~ ** repeated ~1.2% of the time\n"
        "** Severe  ** Something bad\n"
        "**  Fatal  ** Something fatal\n"
        "*** EnergyPlus Completed Successfully\n")
    s = parse_err(p)
    assert len(s.warnings) == 1 and len(s.recurring) == 1
    assert len(s.severe) == 1 and len(s.fatal) == 1
    assert not s.is_usable

    empty = tmp_path / "none.err"
    s2 = parse_err(empty)
    assert not s2.is_usable  # missing err file -> not usable
