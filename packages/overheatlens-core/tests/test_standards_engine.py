"""Pack-agnostic standards-engine tests: gates, serialisation, robustness.

TM59:2017 criterion tests live in test_standards_tm59_2017.py (source-verified
values); TM59:2026 in test_standards_tm59_2026.py; TM52 in test_standards_tm52.py.
The old value-specific tests here were superseded when the official documents
arrived and corrected the transcription (RULE 7: fix the cause, document it).
"""

from __future__ import annotations

import numpy as np
import pytest

from overheatlens.schemas import RulePackError, validate_pack_dict
from overheatlens.standards import (
    BlockedRulePack,
    EvaluationMode,
    SourceNotVerified,
    StandardsEngine,
    classify_room,
)

from conftest import series_at


HOURS = (np.arange(8760) % 24) + 1
DM = np.full(365, 15.0)


def sleep_labels() -> np.ndarray:
    return (np.arange(8760) % 24) + 1


def _synthetic_pack(status: str, blocked: str | None = None) -> dict:
    pack = {
        "rule_pack": "xx_synthetic",
        "version": "1.0.0",
        "title": "Synthetic pack for gate testing",
        "publisher": "Test",
        "source_status": status,
        "source_refs": ["S-03"],
        "assessment": {"period": "full_year", "hour_basis": 8760},
        "space_types": {"bedroom": {"aliases": ["bedroom"], "criteria": []}},
        "criteria": [],
    }
    if blocked:
        pack["blocked"] = blocked
    validate_pack_dict(pack)
    return pack


# ---- classification ----------------------------------------------------------

def test_classify_room():
    pack = StandardsEngine.load("uk_tm59_2017").pack
    assert classify_room("Master Bedroom", pack) == "bedroom"
    assert classify_room("Open Plan Living Kitchen", pack) == "living"
    assert classify_room("Corridor", pack) == "communal"


def test_classify_room_2026_home_office():
    pack = StandardsEngine.load("uk_tm59_2026").pack
    assert classify_room("Home office", pack) == "living"


# ---- evaluation gates ---------------------------------------------------------

def test_blocked_pack_refused_everywhere():
    pack = _synthetic_pack("blocked_no_source", blocked="SOURCE_NOT_ACQUIRED")
    eng = StandardsEngine(pack)
    with pytest.raises(BlockedRulePack):
        eng.evaluate_room("r", "Bedroom", series_at(20.0), HOURS, mode="research")
    with pytest.raises(BlockedRulePack):
        eng.evaluate_room("r", "Bedroom", series_at(20.0), HOURS, mode="compliance")
    assert eng.compliance_allowed() is False


def test_pending_pack_gates():
    pack = _synthetic_pack("secondary_pending")
    eng = StandardsEngine(pack)
    with pytest.raises(SourceNotVerified):
        eng.evaluate_room("r", "Bedroom", series_at(20.0), HOURS, mode="compliance")
    assert eng.compliance_allowed() is False
    ra = eng.evaluate_room("r", "Bedroom", series_at(20.0), HOURS, mode="research")
    assert ra.mode == "research"
    assert ra.verification_status == "secondary_pending"


def test_verified_pack_passes_compliance():
    eng = StandardsEngine.load("uk_tm59_2026")
    assert eng.compliance_allowed() is True
    eng17 = StandardsEngine.load("uk_tm59_2017")
    assert eng17.compliance_allowed() is True
    po = StandardsEngine.load("uk_part_o_dynamic")
    assert po.compliance_allowed() is True
    tm52 = StandardsEngine.load("uk_tm52")
    assert tm52.compliance_allowed() is True


def test_result_dicts_serialisable():
    eng = StandardsEngine.load("uk_tm59_2017")
    res = eng.evaluate_dwelling(
        [("r1", "Living room", series_at(22.0))], HOURS, category="II",
        daily_mean_outdoor=DM, mode="research")
    import json

    json.dumps(res)  # must not raise


# ---- passport -----------------------------------------------------------------

def test_standards_passport_contents():
    po = StandardsEngine.load("uk_part_o_dynamic")
    p = po.standards_passport()
    for key in ("name", "rule_pack", "version", "publisher", "edition",
                "source_status", "weather_requirements", "criteria_ids"):
        assert key in p
    t26 = StandardsEngine.load("uk_tm59_2026").standards_passport()
    assert t26["source_status"] == "source_verified"
    assert [s["id"] for s in t26["stages"]] == ["stage_1", "stage_2", "stage_3"]


# ---- robustness -----------------------------------------------------------------

def test_wrong_series_length_refused():
    eng = StandardsEngine.load("uk_tm59_2017")
    with pytest.raises(ValueError):
        eng.evaluate_room("r", "Bedroom", series_at(20.0, n=100), np.arange(100) % 24,
                          category="II", daily_mean_outdoor=DM, mode="research")


def test_unsupported_condition_rejected():
    eng = StandardsEngine.load("uk_tm59_2017")
    eng._bind_calendar(sleep_labels(), 8760)
    bad = dict(eng._criteria["b"])
    bad["condition"] = "top_c ^ 2 > 4"
    with pytest.raises(RulePackError):
        eng._evaluate_criterion(bad, series_at(20.0), "bedroom")


def test_invalid_category_refused():
    eng = StandardsEngine.load("uk_tm59_2017")
    with pytest.raises(ValueError):
        eng.evaluate_room("r", "Bedroom", series_at(20.0), HOURS, category="III",
                          daily_mean_outdoor=DM)
