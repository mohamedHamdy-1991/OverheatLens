#!/usr/bin/env python3
"""Build the app's machine-readable archetype register.

Merges: existing hand-written entries (kept verbatim) + per-file audit facts
(SHA-256, zones, EnergyPlus version, readiness status, 2026-09-04 regression
verdict against Leeds_DSY1_2020High50_) + research/template classification.

Writes data/archetypes/provenance.json (committed — no copyrighted content).
Run: ./.venv/bin/python scripts/build_archetype_provenance.py
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "packages" / "overheatlens-core"))

from overheatlens.idf import parse_idf  # noqa: E402

IDF_DIR = REPO / "data" / "archetypes" / "idf"
VARIANT_DIR = IDF_DIR / "variants"
DEST = REPO / "data" / "archetypes" / "provenance.json"
AUDIT = REPO / "data" / "archetypes" / "audit_report.json"

# Scenario suffixes used by the author's CH6 dissertation model set
# (01_MODELS/variants). S1 is the base model itself; only S2/S3 exist as files.
VARIANT_SCENARIOS = {
    "S2_restricted": {"scenario": "S2", "label": "restricted window opening"},
    "S3_nightpurge": {"scenario": "S3", "label": "night-purge ventilation"},
}

# Hand-curated research context (source: PROVENANCE.md register + API RESEARCH_META).
# Names are PUBLIC typology names — internal case-study codes stay in file stems only.
RESEARCH = {
    "00CS_detached": {"name": "Detached stone cottage", "kind": "research",
        "form": "detached stone cottage", "era": "late-18thC",
        "description": "Detached stone cottage (DEEP case study, measured U-values)."},
    "01BA_end_terrace": {"name": "End-terrace house (1930s)", "kind": "research",
        "form": "end-terrace", "era": "1930s",
        "description": "End-terrace house, 1930s semi-traditional (DEEP/Harehills, measured dwelling)."},
    "17BG_back_to_back_end": {"name": "Back-to-back house (end)", "kind": "research",
        "form": "back-to-back end", "era": "~1890",
        "description": "Back-to-back END dwelling (DEEP/Harehills, measured dwelling)."},
    "27BG_back_to_back_mid": {"name": "Back-to-back house (mid)", "kind": "research",
        "form": "back-to-back mid", "era": "~1890",
        "description": "Back-to-back MID dwelling (DEEP/Harehills, measured dwelling)."},
    "52NP_mid_terrace_EWI": {"name": "Mid-terrace house (external wall insulation)", "kind": "research",
        "form": "mid-terrace, retrofitted EWI", "era": "retrofit",
        "description": "Mid-terrace with external wall insulation (DEEP/Harehills, measured dwelling)."},
    "55AD_semi_detached": {"name": "Semi-detached house", "kind": "research",
        "form": "semi-detached", "era": "DEEP case",
        "description": "Semi-detached house (DEEP case study)."},
    "56TR_end_terrace": {"name": "End-terrace house", "kind": "research",
        "form": "end-terrace", "era": "DEEP case",
        "description": "End-terrace house (DEEP case study)."},
    "04KG_semi_detached_nofines": {"name": "Semi-detached house (no-fines concrete)", "kind": "research",
        "form": "semi-detached, no-fines concrete", "era": "mid-20thC",
        "description": "Semi-detached no-fines construction house."},
    "19BA_mid_terrace": {"name": "Mid-terrace house", "kind": "research",
        "form": "mid-terrace", "era": "DEEP case",
        "description": "Mid-terrace house (DEEP case study)."},
    "Flat_TM59Example4": {"name": "CIBSE TM59 Example 4 flat", "kind": "reference",
        "form": "mid-floor 2-bed flat", "era": "Part L 2021 reference",
        "description": "CIBSE TM59 published standard reference flat (Example 4) — comparability case, not a measured dwelling."},
    "GroundFloorFlat_27BG_derived": {"name": "Ground-floor flat", "kind": "template",
        "form": "ground-floor flat", "era": "derived",
        "description": "Ground-floor flat derived from a measured back-to-back archetype (generic template)."},
    "TopFloorFlat_17BG_derived": {"name": "Top-floor flat", "kind": "template",
        "form": "top-floor flat", "era": "derived",
        "description": "Top-floor flat derived from a measured back-to-back archetype (generic template)."},
    "HighRiseFlat_EHS_derived": {"name": "High-rise flat", "kind": "template",
        "form": "high-rise flat", "era": "derived",
        "description": "High-rise flat derived from English Housing Survey stock (generic template)."},
    "Bungalow_55AD_derived": {"name": "Bungalow", "kind": "template",
        "form": "bungalow", "era": "derived",
        "description": "Bungalow form derived from a measured semi-detached archetype (generic template)."},
    "ModernHouse_PartL2021_derived": {"name": "Modern house (Part L 2021)", "kind": "template",
        "form": "detached new-build", "era": "new-build",
        "description": "Modern house to Part L 2021 fabric standards (generic template)."},
}


def main() -> int:
    try:
        existing = json.loads(DEST.read_text())
    except (OSError, ValueError):
        existing = {}
    audit = {r["file"]: r for r in json.loads(AUDIT.read_text())} if AUDIT.is_file() else {}

    out = dict(existing)
    for p in sorted(IDF_DIR.glob("*.idf")):
        stem = p.stem
        entry = dict(out.get(stem, {}))
        entry.update(RESEARCH.get(stem, {"name": stem.replace("_", " "), "kind": "research"}))
        entry["code"] = stem
        entry["idf_filename"] = p.name
        entry["sha256"] = hashlib.sha256(p.read_bytes()).hexdigest()
        try:
            idf = parse_idf(p)
            entry["n_zones"] = len(idf.zone_names())
            entry["zone_names"] = idf.zone_names()
            text = p.read_text(errors="replace")
            m = re.search(r"(?im)^\s*Version\s*,\s*([0-9.]+)", text)
            entry["energyplus_version"] = m.group(1).strip() if m else None
        except Exception as e:  # noqa: BLE001
            entry["parse_error"] = str(e)
        a = audit.get(p.name, {})
        eplus = a.get("energyplus", {})
        entry["last_validation"] = {
            "date": "2026-09-04",
            "weather": "Leeds_DSY1_2020High50_.epw",
            "energyplus": "25.1.0",
            "run_status": eplus.get("status") if isinstance(eplus, dict) else eplus,
            "tm59_2017_overall": a.get("tm59_2017_overall", a.get("tm59_2017")),
            "harvested_zones": len(a.get("harvested_zones", [])),
        }
        entry["research_status"] = "VERIFIED" if isinstance(eplus, dict) and eplus.get("status") == "complete" and "OVERALL" not in str(a.get("tm59_2017_overall", "")) and a.get("tm59_2017_overall") in ("PASS", "FAIL") else "NEEDS_REVIEW"
        out[stem] = entry

    # Scenario variants (data/archetypes/idf/variants/) — stored with the app and
    # registered here, but deliberately NOT added to the flat model register:
    # /api/models and the audit scope stay with the 15 base archetypes until the
    # author promotes them. "variants" as a key can never collide with a stem.
    variants: dict[str, dict] = {}
    for p in sorted(VARIANT_DIR.glob("*.idf")) if VARIANT_DIR.is_dir() else []:
        stem = p.stem
        hit = next(((sfx, meta) for sfx, meta in VARIANT_SCENARIOS.items()
                    if stem.endswith("_" + sfx)), None)
        if hit is None:
            entry = {"code": stem, "name": stem.replace("_", " "),
                     "variant_of": None, "scenario": None}
        else:
            sfx, meta = hit
            base = stem[: -(len(sfx) + 1)]
            base_name = RESEARCH.get(base, {}).get("name", base.replace("_", " "))
            entry = {"code": stem, "idf_filename": p.name,
                     "variant_of": base, "base_name": base_name,
                     "scenario": meta["scenario"],
                     "scenario_label": meta["label"],
                     "name": f"{base_name} — {meta['scenario']} ({meta['label']})"}
        entry["sha256"] = hashlib.sha256(p.read_bytes()).hexdigest()
        try:
            idf = parse_idf(p)
            entry["n_zones"] = len(idf.zone_names())
            text = p.read_text(errors="replace")
            m = re.search(r"(?im)^\s*Version\s*,\s*([0-9.]+)", text)
            entry["energyplus_version"] = m.group(1).strip() if m else None
        except Exception as e:  # noqa: BLE001
            entry["parse_error"] = str(e)
        # No EnergyPlus run is recorded for variants yet — say so honestly.
        entry["last_validation"] = {
            "date": None, "weather": None, "energyplus": None,
            "run_status": "NOT_RUN", "tm59_2017_overall": None,
            "harvested_zones": 0,
        }
        entry["research_status"] = "NEEDS_REVIEW"
        variants[stem] = entry
    out["variants"] = variants

    DEST.write_text(json.dumps(out, indent=2))
    verified = sum(1 for v in out.values()
                   if isinstance(v, dict) and v.get("research_status") == "VERIFIED")
    print(f"wrote {DEST}: {len(out)} top-level entries ({verified} VERIFIED), "
          f"{len(variants)} scenario variants")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
