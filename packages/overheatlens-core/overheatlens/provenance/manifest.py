"""Run manifests — every result must be traceable to its inputs, engines and rule packs.

Governing plan §21.1: software version, core version, rule pack, EnergyPlus version,
input hashes, assumptions, outputs, timestamps, calculation IDs.
"""

from __future__ import annotations

import datetime as _dt
import platform
from pathlib import Path
from typing import Any

from .. import CORE_VERSION
from .hashing import sha256_file


def _now_utc_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_run_manifest(
    *,
    run_id: str,
    rule_pack: str,
    rule_pack_version: str,
    energyplus_version: str | None = None,
    input_files: dict[str, str | Path] | None = None,
    assumptions: list[str] | None = None,
    outputs: list[str] | None = None,
) -> dict[str, Any]:
    """Build a deterministic-ordered run manifest dict.

    Keys are inserted in the governing-plan order so JSON dumps are stable across runs
    with identical inputs.
    """
    inputs: dict[str, Any] = {}
    for name, path in (input_files or {}).items():
        p = Path(path)
        inputs[name] = {"path": p.name, "sha256": sha256_file(p)}

    return {
        "run_id": run_id,
        "overheatlens_version": CORE_VERSION,
        "core_version": CORE_VERSION,
        "rule_pack": rule_pack,
        "rule_pack_version": rule_pack_version,
        "energyplus_version": energyplus_version,
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "idf_sha256": inputs.get("idf", {}).get("sha256"),
        "epw_sha256": inputs.get("epw", {}).get("sha256"),
        "input_files": inputs,
        "assumptions": list(assumptions or []),
        "outputs": list(outputs or []),
        "created_utc": _now_utc_iso(),
    }
