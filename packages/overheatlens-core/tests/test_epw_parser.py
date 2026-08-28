"""Parser tests: structural correctness on good files, loud failure on bad ones."""

from __future__ import annotations

import numpy as np
import pytest

from conftest import FIXTURES

from overheatlens.epw import FIELDS, EpwParseError, parse_epw


def test_good_file_parses(fixtures_dir):
    epw = parse_epw(fixtures_dir / "good_file.epw")
    assert epw.n_rows == 8760
    assert epw.data.values.shape == (8760, FIELDS)
    assert epw.header.latitude == pytest.approx(51.9)
    assert epw.header.country == "UK"
    assert epw.sha256 and len(epw.sha256) == 64
    assert epw.data.hour.min() == 1 and epw.data.hour.max() == 24


def test_leap_year_file(fixtures_dir):
    epw = parse_epw(fixtures_dir / "leap_year.epw")
    assert epw.n_rows == 8784


def test_dry_bulb_accessor_matches_row_values(fixtures_dir):
    epw = parse_epw(fixtures_dir / "good_file.epw")
    assert np.allclose(epw.dry_bulb, epw.data.values[:, 6])
    assert np.isfinite(epw.dry_bulb).all()


def test_missing_file_raises(tmp_path):
    with pytest.raises(EpwParseError):
        parse_epw(tmp_path / "does_not_exist.epw")


def test_non_epw_raises(tmp_path):
    p = tmp_path / "not_an_epw.epw"
    p.write_text("hello world\n" * 20)
    with pytest.raises(EpwParseError):
        parse_epw(p)


def test_truncated_row_raises(tmp_path):
    src = (FIXTURES if FIXTURES.exists() else None)
    if src is None:
        pytest.skip("fixtures missing")
    lines = (src / "good_file.epw").read_text().splitlines()
    lines[8] = "2001,1,1,1,0,A,-0.2"  # truncated data row
    p = tmp_path / "truncated.epw"
    p.write_text("\n".join(lines) + "\n")
    with pytest.raises(EpwParseError):
        parse_epw(p)


def test_bad_hour_raises(tmp_path):
    lines = (FIXTURES / "good_file.epw").read_text().splitlines()
    parts = lines[8].split(",")
    parts[3] = "0"  # hour 0 is invalid (hour-ending 1..24)
    lines[8] = ",".join(parts)
    p = tmp_path / "bad_hour.epw"
    p.write_text("\n".join(lines) + "\n")
    with pytest.raises(EpwParseError):
        parse_epw(p)


def test_sha256_is_deterministic(fixtures_dir):
    assert (parse_epw(fixtures_dir / "good_file.epw").sha256
            == parse_epw(fixtures_dir / "good_file.epw").sha256)
