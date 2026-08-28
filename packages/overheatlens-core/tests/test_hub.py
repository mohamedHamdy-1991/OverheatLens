"""Hub self-check: must run clean from the repository root and report honestly."""

from __future__ import annotations

from pathlib import Path

import pytest

from overheatlens import hub


def test_hub_runs_from_repo_root(capsys, monkeypatch):
    repo_root = Path(__file__).resolve().parents[3]
    if not (repo_root / "fixtures" / "epw" / "synthetic" / "good_file.epw").exists():
        pytest.skip("repository layout not present")
    monkeypatch.chdir(repo_root)
    assert hub.run() == 0
    out = capsys.readouterr().out
    assert "OverheatLens" in out
    assert "uk_tm59_2017" in out
    assert "SELF-CHECK" in out
    # must never claim compliance capability
    assert "not a compliance certificate" in out
