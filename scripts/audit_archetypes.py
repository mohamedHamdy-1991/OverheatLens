#!/usr/bin/env python3
"""Archetype regression audit: every bundled IDF × reference EPW.

Parses, readiness-checks, runs EnergyPlus 25.1.0, harvests outputs, and tests
TM59:2017 evaluability. Writes data/archetypes/audit_report.json (local-only).
Run: ./.venv/bin/python scripts/audit_archetypes.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "packages" / "overheatlens-core"))

REF_EPW = Path(
    "/Users/mohamedali/Library/CloudStorage/OneDrive-LeedsBeckettUniversity/"
    "Work/Ph.D/DataBase/DataBase/LEEDS Weather Files/Weather File MET Office/"
    "Leeds_DSY1_2020High50_.epw"
)

from overheatlens.epw import parse_epw  # noqa: E402
from overheatlens.idf import check_idf, parse_idf  # noqa: E402
from overheatlens.standards import StandardsEngine  # noqa: E402
from overheatlens.worker import harvest_hourly, run_energyplus  # noqa: E402


def audit_one(p: Path, epw_path: Path) -> dict:
    out: dict = {"file": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
    try:
        idf = parse_idf(p)
    except Exception as e:  # noqa: BLE001
        return {**out, "parse": f"FAIL: {e}"}
    out["parse"] = "OK"
    zones = idf.zone_names()
    out["n_zones"] = len(zones)
    out["zone_names"] = zones
    try:
        out["readiness"] = check_idf(idf).to_dict()
    except Exception as e:  # noqa: BLE001
        out["readiness"] = {"error": str(e)}
    try:
        run = run_energyplus(p, epw_path, timeout_s=300)
    except Exception as e:  # noqa: BLE001
        return {**out, "energyplus": f"RUNNER ERROR: {e}"}
    out["energyplus"] = {
        "status": run.status,
        "fatal": run.err.fatal,
        "severe": run.err.severe,
        "warnings": len(run.err.warnings),
    }
    if run.status != "complete" or run.csv_path is None:
        return out
    try:
        harvested = harvest_hourly(run.csv_path)
    except Exception as e:  # noqa: BLE001
        return {**out, "harvest": f"FAIL: {e}"}
    out["harvested_zones"] = sorted(harvested)
    out["rh_zones"] = sorted(z for z, v in harvested.items() if v.get("rh"))
    try:
        import numpy as np

        epw = parse_epw(epw_path)
        db = epw.valid_dry_bulb()
        daily = np.nanmean(db.reshape(-1, 24), axis=1)
        engine = StandardsEngine.load("uk_tm59_2017")
        rooms = [(z, z.replace("_", " ").title(), np.asarray(v["top"]))
                 for z, v in harvested.items()]
        result = engine.evaluate_dwelling(
            rooms, category="II", daily_mean_outdoor=daily, mode="compliance")
        out["tm59_2017_overall"] = result.get("overall")
        out["tm59_2017_rooms"] = len(result.get("rooms", []))
    except Exception as e:  # noqa: BLE001
        out["tm59_2017"] = f"NOT EVALUABLE: {e}"
    return out


def main() -> int:
    if not REF_EPW.is_file():
        print(f"reference EPW missing: {REF_EPW}")
        return 2
    idfs = sorted((REPO / "data" / "archetypes" / "idf").glob("*.idf"))
    report = [audit_one(p, REF_EPW) for p in idfs]
    dest = REPO / "data" / "archetypes" / "audit_report.json"
    dest.write_text(json.dumps(report, indent=2, default=str))
    for r in report:
        e = r.get("energyplus", "?")
        print(f"{r['file']}: zones={r.get('n_zones')} e+={e} "
              f"harvest={r.get('harvested_zones', r.get('harvest', '?'))} "
              f"tm59={r.get('tm59_2017_overall', r.get('tm59_2017', '?'))}")
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
