"""Provenance tests: hashing sensitivity/determinism and manifest completeness."""

from __future__ import annotations

import json

from overheatlens.provenance import build_run_manifest, sha256_bytes, sha256_file


def test_sha256_bytes_known_vector():
    assert sha256_bytes(b"hello") == (
        "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    )


def test_sha256_file_detects_byte_change(fixtures_dir, tmp_path):
    src = fixtures_dir / "good_file.epw"
    data = src.read_bytes()
    a = tmp_path / "a.epw"
    b = tmp_path / "b.epw"
    a.write_bytes(data)
    b.write_bytes(data[:-10] + b"X" + data[-9:])
    assert sha256_file(a) != sha256_file(b)
    assert sha256_file(a) == sha256_file(src) == sha256_file(src)


def test_manifest_complete_and_json_serialisable(fixtures_dir):
    m = build_run_manifest(
        run_id="test-run-001",
        rule_pack="uk_tm59_2017",
        rule_pack_version="0.1.0-dev",
        input_files={"epw": fixtures_dir / "good_file.epw"},
        assumptions=["synthetic fixture"],
        outputs=["summary"],
    )
    required = [
        "run_id", "overheatlens_version", "core_version", "rule_pack",
        "rule_pack_version", "epw_sha256", "input_files", "assumptions",
        "outputs", "created_utc",
    ]
    for key in required:
        assert key in m, f"manifest missing {key}"
    assert len(m["epw_sha256"]) == 64
    json.dumps(m)  # must not raise


def test_manifest_deterministic_key_order(fixtures_dir):
    kw = dict(
        run_id="r", rule_pack="p", rule_pack_version="v",
        input_files={"epw": fixtures_dir / "good_file.epw"},
    )
    assert list(build_run_manifest(**kw).keys()) == list(build_run_manifest(**kw).keys())
