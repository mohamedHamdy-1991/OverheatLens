#!/usr/bin/env python3
"""Build the Mitigation Lab catalogue from the Safer_Heat_Harehills parametric study.

Parses the DesignBuilder-exported CIBSE TM59 result CSVs for the three measured
DEEP dwellings (01BA, 17BG, 27BG) and their mitigation strategies, writing
data/mitigation/summary.json with per-strategy worst-zone criterion values and
pass/fail. The source IDFs stay in the author's research folder (referenced by
path, never copied into the repo).

Run:  python3 scripts/build_mitigation_catalogue.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BASE = Path("/Users/mohamedali/Library/CloudStorage/OneDrive-LeedsBeckettUniversity/"
            "Work/Ph.D/Publications/Safer_Heat_Harehills/2- Models")

HOUSES = {
    "01BA": BASE / "01BA_End-terrace",
    "17BG": BASE / "17BG End-terrace back-to-back",
    "27BG": BASE / "27BG Mid-Terrace Back-to-Back",
}

STRATEGY_LABELS = {
    "Baseline": "Baseline (as measured)",
    "B1": "B1 — White lime render (high albedo walls)",
    "B2": "B2 — Insulation layer",
    "B3": "B3 — Fabric upgrade",
    "C1": "C1 — Single clear glazing",
    "C2": "C2 — Double low-E glazing",
    "C3": "C3 — Low-E retrofit film",
    "D1": "D1 — Fixed overhangs",
    "D2": "D2 — External venetian blinds",
    "D3": "D3 — Retractable awnings",
    "D4": "D4 — External shutters",
    "D5": "D5 — Internal blinds/curtains",
    "D6": "D6 — Tree shading",
    "E1": "E1 — Enhanced natural ventilation",
    "E2": "E2 — Night purge",
    "E3": "E3 — Vulnerable occupant scenario",
    "F1": "F1 — Combined measures",
    "F2": "F2 — Combined measures 2",
    "F3": "F3 — Vulnerable combined",
}


def parse_tm59_csv(path: Path) -> dict:
    """Parse a DesignBuilder TM59 export: worst zone per criterion + overall."""
    out: dict = {"file": path.name, "nat": [], "mech": []}
    section = None
    try:
        lines = path.read_text(errors="replace").splitlines()
    except OSError:
        return {"error": "unreadable"}
    for ln in lines:
        if "naturally ventilated" in ln.lower():
            section = "nat"
        elif "mechanically ventilated" in ln.lower():
            section = "mech"
        elif ln.startswith("Block,") or not ln.strip() or ln.startswith("CIBSE"):
            continue
        elif section and "," in ln:
            parts = [p.strip() for p in ln.split(",")]
            if len(parts) >= 4 and parts[0] and parts[1]:
                row = {"block": parts[0], "zone": parts[1],
                       "criterion_a_pct": _f(parts[2]) if section == "nat" else None,
                       "criterion_b_hr": _f(parts[3]) if section == "nat" else None,
                       "pass_fail": parts[-1]}
                out[section].append(row)
    # overall: fail if any row fails
    rows = out["nat"] + out["mech"]
    out["overall"] = ("FAIL" if any(r["pass_fail"].upper().startswith("FAIL") for r in rows)
                      else ("PASS" if rows else "NO_DATA"))
    worst = max((r for r in out["nat"] if r["criterion_a_pct"] is not None),
                key=lambda r: r["criterion_a_pct"], default=None)
    out["worst_a"] = worst
    return out


def _f(s: str):
    try:
        return float(s.replace(",", ""))
    except ValueError:
        return None


def main() -> int:
    catalogue: dict = {"houses": {}}
    for code, folder in HOUSES.items():
        if not folder.is_dir():
            print(f"SKIP {code}: folder missing", file=sys.stderr)
            continue
        house: dict = {"folder": str(folder), "strategies": {}}
        # baseline may be named differently per house
        baseline_dir = None
        for cand in folder.iterdir():
            if not cand.is_dir():
                continue
            name = cand.name
            if re.match(rf"{code}_BL_Baseline", name) or name == "Baseline":
                baseline_dir = cand
            m = re.match(rf"{code}_BL_([A-F]\d[^_]*)", name) or \
                re.match(rf"{code}_BL_([A-F]\d)", name)
            if not m and (name.startswith(f"{code}_BL_") or name in
                          ("Combined", "Future")):
                tail = name.replace(f"{code}_BL_", "")
                if tail:
                    house["strategies"][tail] = _strategy(cand, tail)
                    continue
            if m:
                key = m.group(1).strip()
                house["strategies"][key] = _strategy(cand, key)
        if baseline_dir:
            tm59 = list(baseline_dir.glob("*TM59*.csv"))
            house["baseline"] = {
                "folder": str(baseline_dir),
                "idf": _first(baseline_dir, ".idf"),
                "tm59": parse_tm59_csv(tm59[0]) if tm59 else None,
            }
        catalogue["houses"][code] = house
        print(f"{code}: baseline={'yes' if house.get('baseline') else 'NO'}, "
              f"{len(house['strategies'])} strategies")

    out = REPO / "data" / "mitigation" / "summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(catalogue, indent=2), encoding="utf-8")
    print(f"wrote {out}")
    return 0


def _strategy(folder: Path, key: str) -> dict:
    tm59 = sorted(folder.glob("*TM59*.csv"))
    idf = _first(folder, ".idf")
    return {
        "folder": str(folder),
        "label": STRATEGY_LABELS.get(key, key),
        "idf": idf,
        "tm59_csv": str(tm59[0]) if tm59 else None,
        "result": parse_tm59_csv(tm59[0]) if tm59 else None,
    }


def _first(folder: Path, suffix: str) -> str | None:
    for p in sorted(folder.rglob(f"*{suffix}")):
        if "Archive" not in str(p) and ".bak" not in p.name:
            return str(p)
    return None


if __name__ == "__main__":
    raise SystemExit(main())
