"""Rule-pack tests: every bundled pack must validate against the JSON Schema and carry
complete provenance metadata. This is the enforcement point of ADR-0007."""

from __future__ import annotations

import pytest

from overheatlens.schemas import (
    RulePackError,
    available_pack_ids,
    load_bundled_pack,
    load_pack_dict,
    validate_pack_dict,
)


def test_all_bundled_packs_validate():
    ids = available_pack_ids()
    assert set(ids) >= {"uk_tm59_2017", "uk_tm59_2026", "uk_part_o_dynamic", "uk_tm52"}
    for pid in ids:
        pack = load_bundled_pack(pid)  # raises RulePackError if invalid
        assert pack["rule_pack"] == pid


@pytest.mark.parametrize("pid", ["uk_tm59_2017", "uk_part_o_dynamic", "uk_tm52", "uk_tm59_2026"])
def test_every_criterion_has_provenance(pid):
    pack = load_bundled_pack(pid)
    for c in pack.get("criteria", []):
        assert "verification" in c, f"{pid}:{c.get('id')} missing verification"
        assert c["verification"]["status"] in {
            "source_verified", "secondary_pending", "blocked_no_source"
        }
        assert c["verification"]["source"]


def test_source_register_ids_referenced_exist():
    valid_ids = {f"S-{i:02d}" for i in range(1, 10)} | {
        f"W-{i:02d}" for i in range(1, 10)
    } | {f"D-{i:02d}" for i in range(1, 10)}
    for pid in available_pack_ids():
        pack = load_bundled_pack(pid)
        for ref in pack["source_refs"]:
            assert ref in valid_ids, f"{pid} references unknown register id {ref}"


def test_tm59_2026_source_verified_with_full_criteria():
    pack = load_bundled_pack("uk_tm59_2026")
    assert pack["source_status"] == "source_verified"
    assert [c["id"] for c in pack["criteria"]] == ["a", "b", "c", "d"]
    assert all(c["verification"]["status"] == "source_verified" for c in pack["criteria"])
    assert pack["weather_requirements"]["verified"] is True
    assert "DSY1_2050s_HIGH50_CIBSE_v1.1" in pack["weather_requirements"]["recommended_minimum"]
    # machine-verified criterion values (S-03)
    by_id = {c["id"]: c for c in pack["criteria"]}
    assert by_id["a"]["max_exceedance_hours"] == 59
    assert by_id["a"]["variants"]["bedroom"]["max_exceedance_hours"] == 110
    assert by_id["b"]["category_thresholds"] == {"I": 26, "II": 27}
    assert by_id["b"]["max_nights"] == 4
    assert by_id["c"]["condition"] == "top_c > 26.0"
    assert by_id["d"]["condition"] == "top_c > 28.0"
    assert by_id["d"]["max_exceedance_hours"] == 110
    # stages
    assert [s["id"] for s in pack["stages"]] == ["stage_1", "stage_2", "stage_3"]


def test_part_o_references_verified_ado_and_inherits_tm59_2017():
    pack = load_bundled_pack("uk_part_o_dynamic")
    assert pack["inherits"] == "uk_tm59_2017"
    assert "S-01" in pack["source_refs"]
    limits = pack["model_limits"]
    clauses = {m["clause"] for m in limits}
    assert any("2.6(a)" in c for c in clauses)
    assert any("2.6(b)" in c for c in clauses)
    for m in limits:
        assert m["verification"]["status"] == "source_verified"
    exclusions = pack["strategy_exclusions"]
    assert {e["clause"] for e in exclusions} >= {"ADO §2.8", "ADO §2.9"}
    # weather requirement must state the inheritance, not claim ADO names a file
    assert "NOT" in pack["weather_note"]


def test_invalid_pack_rejected():
    with pytest.raises(RulePackError):
        validate_pack_dict({"rule_pack": "incomplete"})


def test_unknown_threshold_field_rejected():
    pack = load_bundled_pack("uk_tm59_2017")
    pack["criteria"][0]["mystery_threshold"] = 42
    with pytest.raises(RulePackError):
        validate_pack_dict(pack)


def test_load_pack_from_path():
    from overheatlens.schemas import RULES_DIR

    pack = load_pack_dict(RULES_DIR / "uk_tm59_2017.yaml")
    assert pack["rule_pack"] == "uk_tm59_2017"
