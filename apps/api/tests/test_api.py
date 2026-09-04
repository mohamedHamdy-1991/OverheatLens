"""API test suite — every endpoint exercised through TestClient.

Run:  PYTHONPATH="packages/overheatlens-core:apps" python -m pytest apps/api/tests -q
The EnergyPlus-backed /api/analyze test auto-skips when no official binary or
weather library is present (CI-safe).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apps.api.app import main as main_mod
from apps.api.app.main import DEMO_IDF, REPO_ROOT, WEATHER_DIR, app

client = TestClient(app)
FIXTURE = REPO_ROOT / "fixtures" / "epw" / "synthetic" / "good_file.epw"
IDF_FIXTURE = REPO_ROOT / "fixtures" / "idf" / "synthetic_dwelling.idf"


def _real_file() -> Path | None:
    if WEATHER_DIR.is_dir():
        for p in sorted(WEATHER_DIR.glob("*.epw")):
            if "DSY1_2020High50" in p.name:
                return p
    return None


_eplus_present = client.get("/api/version").json()["energyplus_version"] is not None


@pytest.fixture()
def upload_dirs(tmp_path, monkeypatch):
    """Point the upload destinations at a scratch directory for the test."""
    epw_dir = tmp_path / "uploads" / "epw"
    idf_dir = tmp_path / "uploads" / "idf"
    monkeypatch.setattr(main_mod, "UPLOAD_EPW_DIR", epw_dir)
    monkeypatch.setattr(main_mod, "UPLOAD_IDF_DIR", idf_dir)
    return epw_dir, idf_dir


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


# --- models & uploads ---------------------------------------------------------------

def test_models_lists_leeds_templates():
    r = client.get("/api/models")
    assert r.status_code == 200
    models = r.json()["models"]
    templates = [m for m in models if m["source"] == "template"]
    leeds_dir = REPO_ROOT / "fixtures" / "idf" / "leeds"
    if not leeds_dir.is_dir() or not any(leeds_dir.glob("*.idf")):
        pytest.skip("no Leeds archetype templates present yet")
    assert templates
    for m in templates:
        assert m["city"] == "Leeds"
        for key in ("id", "name", "path", "description", "n_zones",
                    "zone_names", "floor_area_m2", "source"):
            assert key in m
        assert Path(m["path"]).is_file()


def test_models_upload_idf_happy_and_listed(upload_dirs):
    _, idf_dir = upload_dirs
    body = IDF_FIXTURE.read_bytes()
    r = client.post("/api/models/upload",
                    params={"name": "my_house.idf"}, content=body)
    assert r.status_code == 200
    out = r.json()
    assert out["model"]["n_zones"] == 2
    assert out["model"]["zone_names"]
    assert out["model"]["source"] == "upload"
    assert out["model"]["path"].startswith(str(idf_dir))
    assert "readiness" in out and "status" in out["readiness"]
    # listed as an upload afterwards
    models = client.get("/api/models").json()["models"]
    up = [m for m in models if m["id"] == "upload:my_house"]
    assert up and up[0]["n_zones"] == 2
    # a second upload with the same name must not overwrite the first
    r2 = client.post("/api/models/upload",
                     params={"name": "my_house.idf"}, content=body)
    assert r2.status_code == 200
    assert Path(r2.json()["model"]["path"]).name != "my_house.idf"
    assert len(list(idf_dir.glob("*.idf"))) == 2


def test_models_upload_rejects_garbage_and_keeps_nothing(upload_dirs):
    _, idf_dir = upload_dirs
    r = client.post("/api/models/upload",
                    params={"name": "junk.idf"}, content=b"not an idf at all")
    assert r.status_code == 400
    assert "Version" in r.json()["detail"]
    assert list(idf_dir.glob("*")) == []  # invalid upload is not persisted


def test_models_upload_rejects_wrong_extension_and_traversal(upload_dirs):
    r = client.post("/api/models/upload",
                    params={"name": "model.epw"},
                    content=b"Version, 25.1;")
    assert r.status_code == 400
    _, idf_dir = upload_dirs
    r2 = client.post("/api/models/upload",
                     params={"name": "../../escape.idf"},
                     content=IDF_FIXTURE.read_bytes())
    assert r2.status_code == 200
    saved = Path(r2.json()["model"]["path"])
    assert saved.parent == idf_dir  # sanitised, never escapes the upload root


def test_models_upload_size_limit(upload_dirs):
    _, idf_dir = upload_dirs
    big = b"Version, 25.1;\n" + b"x" * (20 * 1024 * 1024)
    r = client.post("/api/models/upload", params={"name": "big.idf"}, content=big)
    assert r.status_code == 413
    if idf_dir.exists():
        assert list(idf_dir.glob("*")) == []


def test_weather_upload_happy_path(upload_dirs):
    epw_dir, _ = upload_dirs
    body = FIXTURE.read_bytes()
    r = client.post("/api/weather/upload",
                    params={"name": "my_station.epw"}, content=body)
    assert r.status_code == 200
    out = r.json()
    assert out["status"] == "PASS"
    assert out["n_rows"] == 8760
    assert out["path"].startswith(str(epw_dir))
    # the saved file is inside the guarded roots and checkable like any library file
    c = client.get("/api/weather/check", params={"path": out["path"]})
    assert c.status_code == 200 and c.json()["n_rows"] == 8760
    # it appears in the weather list as an upload with unknown compatibility
    files = client.get("/api/weather").json()["files"]
    up = [f for f in files if f["name"] == "[upload] my_station.epw"]
    assert up and up[0]["compat_2017"] == "unknown"


def test_weather_upload_rejects_text_file(upload_dirs):
    r = client.post("/api/weather/upload",
                    params={"name": "notes.epw"},
                    content=b"# just some notes, definitely not weather\n1,2,3\n")
    assert r.status_code == 400
    assert "LOCATION" in r.json()["detail"]
    epw_dir, _ = upload_dirs
    assert list(epw_dir.glob("*")) == []


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
    # the model path has the same guard: only fixtures/idf and data/uploads/idf
    r2 = client.post("/api/analyze", params={
        "weather_path": str(FIXTURE),
        "model_path": str(REPO_ROOT / "apps" / "api" / "model.idf")})
    assert r2.status_code == 403


@pytest.mark.skipif(_real_file() is None, reason="needs the local Leeds weather file")
@pytest.mark.skipif(not _eplus_present,
                    reason="needs an installed EnergyPlus binary")
def test_analyze_runs_full_pipeline():
    r = client.post("/api/analyze", params={
        "weather_path": str(_real_file()), "pack_id": "uk_tm59_2017"})
    assert r.status_code == 200
    body = r.json()
    assert body["readiness"]["status"] in ("PASS", "PASS_WITH_WARNINGS")
    assert body["run"]["status"] == "complete"
    assert body["result"]["overall"] in ("PASS", "FAIL", "INCOMPLETE")
    # keys preserve the model's true zone identity as EnergyPlus reports it
    # (E+ 25.1 uppercases; VAL-XSIM-05 forbids lowercasing/merging)
    assert set(body["series"]) == {"LIVING ROOM", "BEDROOM 1"}
    # second call must be served from the run cache
    r2 = client.post("/api/analyze", params={
        "weather_path": str(_real_file()), "pack_id": "uk_tm59_2017"})
    assert r2.json()["cached"] is True


@pytest.mark.skipif(_real_file() is None, reason="needs the local Leeds weather file")
@pytest.mark.skipif(not _eplus_present,
                    reason="needs an installed EnergyPlus binary")
def test_analyze_with_model_path_runs_chosen_model():
    r = client.post("/api/analyze", params={
        "weather_path": str(_real_file()), "pack_id": "uk_tm59_2017",
        "model_path": str(IDF_FIXTURE)})
    assert r.status_code == 200
    body = r.json()
    assert Path(body["model"]["path"]) == IDF_FIXTURE.resolve()
    assert set(body["series"]) == {"LIVING ROOM", "BEDROOM 1"}
    # every zone carries a harvested RH series from the same run (fixture outputs it)
    assert all(body["rh"][z] is not None and len(body["rh"][z]) == 8760
               for z in body["series"])


@pytest.mark.skipif(_real_file() is None, reason="needs the local Leeds weather file")
@pytest.mark.skipif(not _eplus_present,
                    reason="needs an installed EnergyPlus binary")
def test_comfort_run_shape_and_assumptions():
    r = client.post("/api/comfort/run", params={
        "weather_path": str(_real_file()), "pack_id": "uk_tm59_2017"})
    assert r.status_code == 200
    body = r.json()
    a = body["assumptions"]
    assert a["met"] == 1.2 and a["clo"] == 0.35 and a["air_speed_m_s"] == 0.1
    assert a["assessment_window"].startswith("May")
    assert "09:00" in a["occupied_hours"] and "22:00" in a["occupied_hours"]
    assert a["library"] == "pythermalcomfort" and a["library_version"]
    zones = body["zones"]
    assert {z["zone"] for z in zones} == {"LIVING ROOM", "BEDROOM 1"}
    for z in zones:
        pct, ppd, top = (z["adaptive_acceptable_pct"], z["mean_ppd"], z["max_top"])
        assert pct is None or 0.0 <= pct <= 100.0
        assert ppd is None or 0.0 <= ppd <= 100.0
        assert top is None or top > -10.0
        assert z["adaptive_hours_excluded"] >= 0 and z["ppd_hours_excluded"] >= 0
    # every zone must produce real numbers for the Leeds DSY file (nothing hidden)
    assert all(z["adaptive_acceptable_pct"] is not None and z["max_top"] is not None
               for z in zones)
    # the cached run is reused, never re-simulated
    r2 = client.post("/api/comfort/run", params={
        "weather_path": str(_real_file()), "pack_id": "uk_tm59_2017"})
    assert r2.status_code == 200
    assert r2.json()["zones"] == zones


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


# --- run archive / batch / model detail / mitigation / bundle --------------------

def test_runs_list_shape():
    r = client.get("/api/runs")
    assert r.status_code == 200
    runs = r.json()["runs"]
    assert isinstance(runs, list)
    for e in runs:
        assert {"run_id", "weather", "pack_id", "overall"} <= set(e)


def test_run_detail_unknown_id_404s():
    assert client.get("/api/runs/does-not-exist-zzz").status_code == 404


def test_run_delete_unknown_id_404s():
    assert client.delete("/api/runs/does-not-exist-zzz").status_code == 404


def test_batch_rejects_bad_bodies():
    assert client.post("/api/batch", json={}).status_code == 400
    assert client.post("/api/batch", json={"runs": []}).status_code == 400
    big = {"runs": [{"weather_path": str(FIXTURE)}] * 97}
    assert client.post("/api/batch", json=big).status_code == 400
    # entries without a weather path are reported, not fatal
    r = client.post("/api/batch", json={"runs": [{"model_path": str(IDF_FIXTURE)}]})
    assert r.status_code == 200
    assert "error" in r.json()["runs"][0]


def test_model_detail_on_fixture():
    r = client.get("/api/models/detail", params={"path": str(IDF_FIXTURE)})
    assert r.status_code == 200
    body = r.json()
    assert body["n_zones"] == 2
    assert len(body["sha256"]) == 64
    assert body["readiness"]["status"]
    assert isinstance(body["object_census"], dict)
    assert body["energyplus_version"]


def test_model_detail_guards_paths():
    assert client.get("/api/models/detail",
                      params={"path": str(REPO_ROOT / "README.md")}).status_code in (400, 403)


def test_models_lists_research_archetypes_with_kind():
    r = client.get("/api/models")
    assert r.status_code == 200
    research = [m for m in r.json()["models"] if m["source"] == "research"]
    if not (REPO_ROOT / "data" / "archetypes" / "idf").is_dir():
        pytest.skip("no bundled archetype IDFs")
    assert len(research) >= 15
    for m in research:
        assert m.get("kind") in ("research", "reference", "template")


def test_mitigation_catalogue_honest_shape():
    r = client.get("/api/mitigation/catalogue")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in ("ready", "not_generated")
    if body["status"] == "ready":
        assert set(body["catalogue"]["houses"]) >= {"01BA", "17BG", "27BG"}
    else:
        assert "detail" in body


def test_bundle_unknown_run_404s():
    assert client.get("/api/bundle", params={"run_id": "does-not-exist-zzz"}).status_code == 404
