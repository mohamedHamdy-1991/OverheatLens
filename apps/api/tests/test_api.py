"""API test suite — every endpoint exercised through TestClient.

Run:  PYTHONPATH="packages/overheatlens-core:apps" python -m pytest apps/api/tests -q
The EnergyPlus-backed /api/analyze test auto-skips when no official binary or
weather library is present (CI-safe).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apps.api.app.main import REPO_ROOT, WEATHER_DIR, app

client = TestClient(app)
FIXTURE = REPO_ROOT / "fixtures" / "epw" / "synthetic" / "good_file.epw"


def _real_file() -> Path | None:
    if WEATHER_DIR.is_dir():
        for p in sorted(WEATHER_DIR.glob("*.epw")):
            if "DSY1_2020High50" in p.name:
                return p
    return None


# --- version & rule packs -------------------------------------------------------

def test_version_reports_core_and_engine():
    r = client.get("/api/version")
    assert r.status_code == 200
    body = r.json()
    assert body["core_version"].startswith("0.")
    assert body["energyplus_version"] in (None,) or body["energyplus_version"].startswith("2")


def test_rule_packs_all_source_verified():
    r = client.get("/api/rule-packs")
    assert r.status_code == 200
    packs = r.json()["packs"]
    assert {p["rule_pack"] for p in packs} >= {
        "uk_tm59_2017", "uk_tm59_2026", "uk_part_o_dynamic", "uk_tm52",
    }
    assert all(p["source_status"] == "source_verified" for p in packs)
    for p in packs:
        assert p["name"] and p["publisher"] and "criteria_ids" in p


# --- weather ----------------------------------------------------------------------

def test_weather_list_contains_library_and_fixtures():
    r = client.get("/api/weather")
    assert r.status_code == 200
    files = r.json()["files"]
    assert len(files) >= 8  # at least the bundled fixtures
    fixture = next(f for f in files if f["name"] == "[fixture] good_file.epw")
    assert fixture["compat_2017"] == "unknown"
    real = [f for f in files if not f["name"].startswith("[fixture]")]
    for f in real:
        assert f["compat_2017"] in ("compatible", "research_only", "unknown")


def test_weather_check_on_synthetic_fixture():
    r = client.get("/api/weather/check", params={"path": str(FIXTURE)})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "PASS"
    assert body["n_rows"] == 8760
    assert body["weather_summary"]["annual_mean_dry_bulb"] == 11.001


def test_weather_check_rejects_non_epw_and_unknown():
    assert client.get("/api/weather/check", params={"path": "x.txt"}).status_code == 400
    outside = str(REPO_ROOT / "README.md")
    assert client.get("/api/weather/check", params={"path": outside}).status_code in (400, 403)
    assert client.get("/api/weather/check",
                      params={"path": str(REPO_ROOT / "fixtures" / "epw" / "nope.epw")
                      }).status_code == 404


def test_weather_series_shape():
    r = client.get("/api/weather/series", params={"path": str(FIXTURE)})
    assert r.status_code == 200
    body = r.json()
    assert len(body["dry_bulb"]) == 8760
    assert len(body["month_hour_matrix"]) == 12
    assert all(len(row) == 24 for row in body["month_hour_matrix"])
    assert len(body["daily_mean"]) == 365
    assert len(body["monthly"]) == 12


# --- compare ----------------------------------------------------------------------

def test_compare_needs_two_to_eight():
    r = client.get("/api/compare", params={"paths": str(FIXTURE)})
    assert r.status_code == 400


def test_compare_two_fixtures():
    other = REPO_ROOT / "fixtures" / "epw" / "synthetic" / "leap_year.epw"
    r = client.get("/api/compare", params={"paths": f"{FIXTURE},{other}"})
    assert r.status_code == 200
    files = r.json()["files"]
    assert len(files) == 2
    for f in files:
        assert 365 <= len(f["daily_mean"]) <= 366
        assert "annual_mean" in f and "hours_over_26" in f


# --- comfort ------------------------------------------------------------------------

def test_comfort_pmv_ok_and_gate():
    ok = client.get("/api/comfort/pmv",
                    params={"tdb": 25, "tr": 25, "vr": 0.1, "rh": 50, "met": 1.2, "clo": 0.5})
    assert ok.status_code == 200
    body = ok.json()
    assert body["status"] == "OK" and "pmv" in body["values"]
    assert body["provenance"]["library_version"]
    bad = client.get("/api/comfort/pmv",
                     params={"tdb": 40, "tr": 25, "vr": 0.1, "rh": 50, "met": 1.2, "clo": 0.5})
    assert bad.json()["status"] == "OUTSIDE_APPLICABILITY"


def test_comfort_adaptive_and_utci():
    a = client.get("/api/comfort/adaptive",
                   params={"tdb": 26, "tr": 26, "trm": 20, "v": 0.1}).json()
    assert a["status"] == "OK" and "tmp_cmf" in a["values"]
    u = client.get("/api/comfort/utci",
                   params={"tdb": 30, "tr": 32, "v": 1.0, "rh": 50}).json()
    assert u["status"] == "OK" and "utci" in u["values"]


# --- validation & analyze ------------------------------------------------------------

def test_validation_rows_served():
    r = client.get("/api/validation")
    assert r.status_code == 200
    rows = r.json()["rows"]
    assert len(rows) >= 50
    assert all("section" in row and "cells" in row for row in rows)


def test_analyze_guarded_against_outside_paths():
    r = client.post("/api/analyze", params={"weather_path": "README.md"})
    assert r.status_code in (400, 403)


@pytest.mark.skipif(_real_file() is None, reason="needs the local Leeds weather file")
@pytest.mark.skipif(
    client.get("/api/version").json()["energyplus_version"] is None,
    reason="needs an installed EnergyPlus binary")
def test_analyze_runs_full_pipeline():
    r = client.post("/api/analyze", params={
        "weather_path": str(_real_file()), "pack_id": "uk_tm59_2017"})
    assert r.status_code == 200
    body = r.json()
    assert body["readiness"]["status"] in ("PASS", "PASS_WITH_WARNINGS")
    assert body["run"]["status"] == "complete"
    assert body["result"]["overall"] in ("PASS", "FAIL", "INCOMPLETE")
    assert set(body["series"]) == {"living room", "bedroom 1"}
    # second call must be served from the run cache
    r2 = client.post("/api/analyze", params={
        "weather_path": str(_real_file()), "pack_id": "uk_tm59_2017"})
    assert r2.json()["cached"] is True


def test_spa_root_served():
    r = client.get("/")
    assert r.status_code == 200
    assert b"OverheatLens" in r.content or b"hint" in r.content


# --- report ---------------------------------------------------------------------------

def _report_payload() -> dict:
    """Minimal fabricated payload covering every key the renderer reads.

    Nothing here is simulated science — it only exercises the HTML rendering of
    the shapes the /api/analyze endpoint produces."""
    return {
        "model": {"name": "Synthetic two-zone dwelling (demo fixture)",
                  "path": "/fixtures/idf/synthetic_dwelling.idf"},
        "weather": {"name": "good_file.epw",
                    "path": "/fixtures/epw/synthetic/good_file.epw"},
        "rule_pack": {
            "name": "CIBSE TM59 domestic overheating assessment",
            "rule_pack": "uk_tm59_2017",
            "version": "1.0.0",
            "publisher": "CIBSE",
            "edition": "2017",
            "source_status": "source_verified",
            "source_refs": ["S-02"],
            "weather_requirements": {"recommended_minimum": "DSY1 2020 High50"},
            "criteria_ids": ["a", "b"],
        },
        "readiness": {
            "status": "PASS_WITH_WARNINGS",
            "rows": [{"check_id": "wfr_glazing_ratio", "title": "Glazing ratio",
                      "severity": "ok", "detected": "0.20", "required": "<= 0.30",
                      "why_it_matters": "drives solar gains", "how_to_fix": "—",
                      "source": "TM59 §4"}],
        },
        "run": {
            "run_id": "abc123def456",
            "status": "complete",
            "energyplus_version": "24.1.0",
            "out_dir": "/tmp/ohx_abc123def456",
            "err": {"fatal": [], "severe": [], "warning_count": 2,
                    "recurring_warning_count": 0, "first_warnings": [],
                    "is_usable": True},
            "manifest": {
                "run_id": "abc123def456",
                "core_version": "0.9.0",
                "energyplus_version": "24.1.0",
                "idf_sha256": "deadbeef" * 8,
                "epw_sha256": "feedface" * 8,
                "status": "complete",
                "created_utc": "2026-08-29T10:00:00Z",
                "notes": "",
            },
        },
        "result": {
            "pack_id": "uk_tm59_2017", "pack_version": "1.0.0",
            "mode": "compliance", "verification_status": "source_verified",
            "dwelling_category": "II", "overall": "FAIL",
            "rooms": [{
                "room_id": "living_room", "room_type": "living",
                "pack_id": "uk_tm59_2017", "pack_version": "1.0.0",
                "mode": "compliance", "passed": False,
                "verification_status": "source_verified",
                "applicable_criteria": ["a", "b"],
                "criteria": [
                    {"criterion_id": "a", "rule_ref": "TM59 §4.1",
                     "metric_value": 132.0, "threshold": 3.0, "operator": ">",
                     "units": "h", "passed": False, "margin": 129.0,
                     "status": "FAIL", "verification_status": "source_verified",
                     "basis": {}, "notes": []},
                    {"criterion_id": "b", "rule_ref": "TM59 §4.2",
                     "metric_value": None, "threshold": 26.0, "operator": ">",
                     "units": "h", "passed": None, "margin": None,
                     "status": "NOT_EVALUATED",
                     "verification_status": "source_verified",
                     "basis": {}, "notes": ["not evaluated: no sleep schedule"]},
                ],
            }],
        },
        "series": {"living_room": [23.0, 23.5]},
        "daily_mean_outdoor": [14.0, 15.0],
        "cached": False,
    }


def test_report_renderer_is_self_contained_html():
    from apps.api.app.report import render_html_report

    out = render_html_report(_report_payload())
    assert out.startswith("<!DOCTYPE html")
    assert "<style" in out
    assert "abc123def456" in out                                # run id
    assert "uk_tm59_2017" in out                                # rule pack
    assert "not a certified compliance certificate" in out      # disclaimer
    assert "0.5 × (MAT + MRT)" in out                           # derived-Top note
    assert "deadbeef" in out and "feedface" in out              # input hashes
    assert "NOT_EVALUATED" in out                               # honest non-result
    assert "TM59 §4.1" in out                                   # payload text intact
    assert "http://" not in out and "https://" not in out       # no external assets
    assert "<img" not in out and "@media print" in out


def test_report_endpoint_requires_params():
    assert client.get("/api/report").status_code == 422
