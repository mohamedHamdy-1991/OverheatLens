"""IDF readiness + passport tests (Phase 5). Fixture: synthetic two-zone dwelling."""

from __future__ import annotations

from pathlib import Path

import pytest

from overheatlens.idf import (
    IdfParseError,
    build_passport,
    check_idf,
    parse_idf,
)

from conftest import REPO_ROOT

FIXTURE = REPO_ROOT / "fixtures" / "idf" / "synthetic_dwelling.idf"


@pytest.fixture(scope="module")
def model():
    return parse_idf(FIXTURE)


def _row(report, check_id):
    return next(r for r in report.rows if r.check_id == check_id)


def test_parser_extracts_objects(model):
    assert len(model.objects) > 30
    assert model.zone_names() == ["Living room", "Bedroom 1"]
    assert "VERSION" in model.types
    assert model.sha256 and len(model.sha256) == 64


def test_parse_errors(tmp_path):
    with pytest.raises(IdfParseError):
        parse_idf(tmp_path / "missing.idf")
    p = tmp_path / "empty.idf"
    p.write_text("just some text without semicolons\n")
    with pytest.raises(IdfParseError):
        parse_idf(p)


def test_readiness_passes_clean_fixture(model):
    rep = check_idf(model)
    assert rep.status == "PASS"
    assert rep.errors == []
    # window-control conformance is explained, not just flagged (RULE 16)
    win = _row(rep, "IDF-WIN-02")
    assert "22 °C" in win.required or "22 °C" in win.why_it_matters
    assert win.source


def test_readiness_detects_faults(model, tmp_path):
    lines = FIXTURE.read_text().splitlines()
    # remove the RunPeriod object (object = lines from 'runperiod' through the line
    # whose CODE part ends with ';')
    out, skip = [], False
    for ln in lines:
        code = ln.split("!", 1)[0].strip().lower()
        if not skip and code.startswith("runperiod"):
            skip = True
            continue
        if skip:
            if code.endswith(";"):
                skip = False
            continue
        out.append(ln)
    text = "\n".join(out)
    # plant a dangling schedule reference in the People object (field index 2)
    text = text.replace("  Living room People,\n  Living room,\n  Living occupancy,",
                        "  Living room People,\n  Living room,\n  Missing schedule,")
    p = tmp_path / "faulted.idf"
    p.write_text(text)
    rep = check_idf(parse_idf(p))
    assert rep.status == "FAIL"
    ids = {r.check_id for r in rep.errors}
    assert "IDF-RUN-01" in ids
    assert "IDF-SCH-01" in ids


def test_bedroom_detection_warning(model, tmp_path):
    text = FIXTURE.read_text().replace("Bedroom 1", "Room X")
    p = tmp_path / "no_bedroom.idf"
    p.write_text(text)
    rep = check_idf(parse_idf(p))
    assert _row(rep, "IDF-ZON-03").severity == "warning"


def test_passport(model):
    pp = build_passport(model).to_dict()
    assert pp["n_zones"] == 2
    assert pp["classified_rooms"] == {"Living room": "living", "Bedroom 1": "bedroom"}
    assert pp["has_cooling"] is False
    assert pp["has_openings"] is True
    assert pp["timestep_per_hour"] == 6
    assert pp["run_period"] == "1/1–12/31"
    assert pp["version"] == "25.1"


def test_report_serialisable(model):
    import json

    json.dumps(check_idf(model).to_dict())
