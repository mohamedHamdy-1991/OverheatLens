"""CLI smoke tests: version, rule-packs, check-epw, passport, gate exit codes."""

from __future__ import annotations

import pytest

from overheatlens.cli.main import main


def test_version(capsys):
    assert main(["version"]) == 0
    assert "OverheatLens core" in capsys.readouterr().out


def test_rule_packs_lists_all(capsys):
    assert main(["rule-packs"]) == 0
    out = capsys.readouterr().out
    for pid in ("uk_tm59_2017", "uk_tm59_2026", "uk_part_o_dynamic", "uk_tm52"):
        assert pid in out


def test_check_epw_pass(fixtures_dir, capsys):
    assert main(["check-epw", str(fixtures_dir / "good_file.epw")]) == 0
    out = capsys.readouterr().out
    assert "PASS" in out


def test_check_epw_fail_exit_code(fixtures_dir, capsys):
    assert main(["check-epw", str(fixtures_dir / "dewpoint_violation.epw")]) == 1
    assert "FAIL" in capsys.readouterr().out


def test_check_epw_json(fixtures_dir, capsys):
    import json

    assert main(["check-epw", str(fixtures_dir / "good_file.epw"), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "PASS"


def test_passport_blocked_pack(capsys):
    code = main(["passport", "uk_tm59_2026"])
    assert code == 0  # passport is metadata, not evaluation — allowed


def test_passport_unknown_pack(capsys):
    assert main(["passport", "no_such_pack"]) == 2
