"""OverheatLens API — a thin, honest Phase-7 slice over the authoritative core.

Every endpoint calls the core package; nothing here recomputes science. The API
serves the built web app from apps/web/dist so the launcher needs one port only.

Security posture (plan §26, current stage): localhost tool. Path parameters for
weather files are resolved against a configured weather directory; no shell
commands; the EnergyPlus run writes only into its own temp directory.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import threading
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .report import render_html_report
from overheatlens import CORE_VERSION
from overheatlens.epw import check_epw, parse_epw, weather_summary, monthly_mean_dry_bulb
from overheatlens.idf import check_idf, parse_idf
from overheatlens.schemas import available_pack_ids, load_bundled_pack
from overheatlens.standards import StandardsEngine
from overheatlens.worker import run_energyplus

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_WEATHER_DIR = (
    "/Users/mohamedali/Library/CloudStorage/OneDrive-LeedsBeckettUniversity/"
    "Work/Ph.D/DataBase/DataBase/LEEDS Weather Files/Weather File MET Office"
)
WEATHER_DIR = Path(os.environ.get("OVERHEATLENS_WEATHER_DIR", DEFAULT_WEATHER_DIR))
DEMO_IDF = REPO_ROOT / "fixtures" / "idf" / "synthetic_dwelling.idf"
LEEDS_IDF_DIR = REPO_ROOT / "fixtures" / "idf" / "leeds"
LEEDS_META = REPO_ROOT / "data" / "archetypes" / "leeds.json"
UPLOAD_EPW_DIR = REPO_ROOT / "data" / "uploads" / "epw"
UPLOAD_IDF_DIR = REPO_ROOT / "data" / "uploads" / "idf"
RUNS_DIR = REPO_ROOT / "data" / "runs"
MITIGATION_SUMMARY = REPO_ROOT / "data" / "mitigation" / "summary.json"
MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # plan §26.2: maximum upload, enforced first
MAX_BATCH_RUNS = 96  # a full archetype × weather matrix fits; larger needs chunking

app = FastAPI(title="OverheatLens API", version=CORE_VERSION)

_run_cache: dict[tuple[str, str, str], dict] = {}
_cache_lock = threading.Lock()


def _safe_epw(path: str) -> Path:
    """Resolve a weather-file path against the allowed roots (weather dir, bundled
    fixtures, uploaded files, temp dir for launcher-provided files). No arbitrary
    filesystem reads."""
    import tempfile

    p = Path(path).resolve()
    if p.suffix.lower() != ".epw":
        raise HTTPException(400, "Only .epw files can be read.")
    allowed = [WEATHER_DIR.resolve(),
               (REPO_ROOT / "fixtures" / "epw").resolve(),
               UPLOAD_EPW_DIR.resolve(),
               Path(tempfile.gettempdir()).resolve()]
    if not any(p == root or root in p.parents for root in allowed):
        raise HTTPException(403, "Weather file is outside the configured library.")
    if not p.is_file():
        raise HTTPException(404, f"Weather file not found: {p.name}")
    return p


def _safe_idf(path: str) -> Path:
    """Same guard for model files: only bundled fixtures and uploaded IDFs."""
    p = Path(path).resolve()
    if p.suffix.lower() != ".idf":
        raise HTTPException(400, "Only .idf model files can be read.")
    allowed = [(REPO_ROOT / "fixtures" / "idf").resolve(),
               RESEARCH_IDF_DIR.resolve(), UPLOAD_IDF_DIR.resolve()]
    if not any(p == root or root in p.parents for root in allowed):
        raise HTTPException(403, "Model file is outside the permitted directories.")
    if not p.is_file():
        raise HTTPException(404, f"Model file not found: {p.name}")
    return p


def _sanitise_name(name: str, suffix: str) -> str:
    """Filename sanitisation (plan §26.2): no path separators, no leading dots,
    plain characters only, forced extension."""
    base = os.path.basename(name.replace("\\", "/")).strip()
    base = re.sub(r"[^A-Za-z0-9 ._-]", "_", base).lstrip(".")
    if not base.lower().endswith(suffix):
        raise HTTPException(400, f"Only {suffix} files are accepted.")
    stem = base[: -len(suffix)].strip().rstrip(".")
    if not stem:
        raise HTTPException(400, "File name is empty after sanitisation.")
    return stem + suffix


def _save_upload(directory: Path, filename: str, body: bytes) -> Path:
    """Write an upload without ever overwriting an existing file (collision-safe)."""
    directory.mkdir(parents=True, exist_ok=True)
    p = directory / filename
    stem, suf = p.stem, p.suffix
    n = 2
    while True:
        try:
            with open(p, "xb") as f:
                f.write(body)
            return p
        except FileExistsError:
            p = directory / f"{stem}-{n}{suf}"
            n += 1


def _dry_bulb_clean(epw) -> np.ndarray:
    from overheatlens.epw.parser import SENTINELS

    db = epw.dry_bulb.astype(float).copy()
    db[np.isclose(db, SENTINELS[6])] = np.nan
    return db


@app.get("/api/version")
def version():
    eplus = None
    try:
        from overheatlens.worker import find_energyplus

        bins = find_energyplus()
        eplus = bins[0]["version"] if bins else None
    except Exception:  # noqa: BLE001 — version probe must never 500
        eplus = None
    return {"core_version": CORE_VERSION, "energyplus_version": eplus}


@app.get("/api/rule-packs")
def rule_packs():
    from overheatlens.schemas import available_pack_ids

    packs = []
    for pid in available_pack_ids():
        engine = StandardsEngine.load(pid)
        packs.append(engine.standards_passport())
    return {"packs": packs}


@app.get("/api/weather")
def weather_list():
    files: list[dict] = []
    if WEATHER_DIR.is_dir():
        for p in sorted(WEATHER_DIR.glob("*.epw")):
            from overheatlens.epw import check_tm59_2017_weather, check_tm59_2026_weather

            files.append({
                "name": p.name,
                "path": str(p),
                "size_kb": round(p.stat().st_size / 1024),
                "compat_2017": check_tm59_2017_weather(p.name)["status"],
                "compat_2026": check_tm59_2026_weather(p.name)["status"],
            })
    fixtures = REPO_ROOT / "fixtures" / "epw" / "synthetic"
    for p in sorted(fixtures.glob("*.epw")):
        files.append({"name": f"[fixture] {p.name}", "path": str(p),
                      "size_kb": round(p.stat().st_size / 1024),
                      "compat_2017": "unknown", "compat_2026": "unknown"})
    if UPLOAD_EPW_DIR.is_dir():
        for p in sorted(UPLOAD_EPW_DIR.glob("*.epw")):
            files.append({"name": f"[upload] {p.name}", "path": str(p),
                          "size_kb": round(p.stat().st_size / 1024),
                          "compat_2017": "unknown", "compat_2026": "unknown"})
    return {"weather_dir": str(WEATHER_DIR), "files": files}


@app.post("/api/weather/upload")
async def weather_upload(request: Request, name: str = Query(...)):
    """Accept an EPW upload (raw bytes): sanitise, size-guard, content-sniff, save,
    then validate immediately with the core parser and checker. The saved path is
    returned together with the same check report /api/weather/check produces."""
    body = await request.body()
    if len(body) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "File exceeds the 20 MB upload limit.")
    safe = _sanitise_name(name, ".epw")
    first = body.split(b"\n", 1)[0].decode("ascii", errors="replace").strip()
    if not first.upper().startswith("LOCATION,"):
        raise HTTPException(
            400, "This file is not an EPW: the first line must start with 'LOCATION,'.")
    p = _save_upload(UPLOAD_EPW_DIR, safe, body)
    try:
        epw = parse_epw(p)
        report = check_epw(epw)
    except Exception as e:  # noqa: BLE001 — invalid upload, do not keep it
        p.unlink(missing_ok=True)
        raise HTTPException(400, f"Cannot parse as EPW: {e}") from e
    out = report.to_dict()
    out["city"] = epw.header.city.strip()
    out["country"] = epw.header.country.strip()
    out["latitude"] = epw.header.latitude
    out["longitude"] = epw.header.longitude
    out["elevation"] = epw.header.elevation
    if not report.errors:
        try:
            out["weather_summary"] = weather_summary(epw).to_dict()
        except ValueError as e:
            out["weather_summary"] = None
            out["summary_note"] = str(e)
    out["path"] = str(p)
    return out


RESEARCH_IDF_DIR = REPO_ROOT / "data" / "archetypes" / "idf"

# Real dwelling archetypes from the author's DEEP / Sensor-Calibrated research
# (see data/archetypes/PROVENANCE.md). Display names are PUBLIC typology names —
# never the internal case-study codes; those live only in file stems/ids.
RESEARCH_META: dict[str, dict] = {
    "00CS_detached": {"name": "Detached stone cottage", "era": "late-18thC",
        "description": "Detached stone cottage (DEEP case study, measured U-values)."},
    "01BA_end_terrace": {"name": "End-terrace house (1930s)", "era": "1930s",
        "description": "End-terrace house, 1930s semi-traditional (DEEP/Harehills, measured dwelling)."},
    "17BG_back_to_back_end": {"name": "Back-to-back house (end)", "era": "~1890",
        "description": "Back-to-back END dwelling (DEEP/Harehills, measured dwelling)."},
    "27BG_back_to_back_mid": {"name": "Back-to-back house (mid)", "era": "~1890",
        "description": "Back-to-back MID dwelling (DEEP/Harehills, measured dwelling)."},
    "52NP_mid_terrace_EWI": {"name": "Mid-terrace house (external wall insulation)", "era": "retrofit",
        "description": "Mid-terrace with external wall insulation (DEEP/Harehills, measured dwelling)."},
    "55AD_semi_detached": {"name": "Semi-detached house", "era": "DEEP case",
        "description": "Semi-detached house (DEEP case study)."},
    "56TR_end_terrace": {"name": "End-terrace house", "era": "DEEP case",
        "description": "End-terrace house (DEEP case study)."},
    "04KG_semi_detached_nofines": {"name": "Semi-detached house (no-fines concrete)", "era": "mid-20thC",
        "description": "Semi-detached no-fines construction house."},
    "19BA_mid_terrace": {"name": "Mid-terrace house", "era": "DEEP case",
        "description": "Mid-terrace house (DEEP case study)."},
    "Flat_TM59Example4": {"name": "CIBSE TM59 Example 4 flat", "era": "Part L 2021 reference",
        "description": "CIBSE TM59 published standard reference flat (mid-floor 2-bed, Example 4) — included for comparability with the TM59 literature."},
    "GroundFloorFlat_27BG_derived": {"name": "Ground-floor flat", "era": "derived",
        "description": "Ground-floor flat derived from a measured back-to-back archetype (generic template)."},
    "TopFloorFlat_17BG_derived": {"name": "Top-floor flat", "era": "derived",
        "description": "Top-floor flat derived from a measured back-to-back archetype (generic template)."},
    "HighRiseFlat_EHS_derived": {"name": "High-rise flat", "era": "derived",
        "description": "High-rise flat derived from the English Housing Survey stock (generic template)."},
    "Bungalow_55AD_derived": {"name": "Bungalow", "era": "derived",
        "description": "Bungalow form derived from a measured semi-detached archetype (generic template)."},
    "ModernHouse_PartL2021_derived": {"name": "Modern house (Part L 2021)", "era": "new-build",
        "description": "Modern house to Part L 2021 fabric standards (generic template)."},
}


def _archetype_register() -> dict[str, dict]:
    """Machine-readable archetype register (built by
    scripts/build_archetype_provenance.py): kind, era, form, validation."""
    try:
        raw = json.loads((REPO_ROOT / "data" / "archetypes" / "provenance.json").read_text())
        return raw if isinstance(raw, dict) else {}
    except (OSError, ValueError):
        return {}


def _leeds_metadata() -> dict[str, dict]:
    """Merge archetype metadata for Leeds templates when the (concurrently owned)
    data/archetypes/leeds.json is present. Tolerant to list- or dict-shaped files."""
    try:
        raw = json.loads(LEEDS_META.read_text())
    except (OSError, ValueError):
        return {}

    def index(entries) -> dict[str, dict]:
        out: dict[str, dict] = {}
        for e in entries:
            if not isinstance(e, dict):
                continue
            key = e.get("id") or e.get("file") or e.get("filename") or ""
            key = Path(str(key)).stem.lower()
            if key:
                out[key] = e
        return out

    if isinstance(raw, list):
        return index(raw)
    if isinstance(raw, dict):
        for k in ("archetypes", "templates", "models"):
            if isinstance(raw.get(k), list):
                return index(raw[k])
        return {str(k).lower(): v for k, v in raw.items() if isinstance(v, dict)}
    return {}


def _model_passport(p: Path, source: str, city_fallback: str | None,
                    meta: dict | None) -> dict:
    meta = meta or {}
    entry = {
        "id": (f"upload:{p.stem}" if source == "upload" else p.stem),
        "name": meta.get("name") or p.stem.replace("_", " "),
        "path": str(p),
        "city": meta.get("city") or city_fallback,
        "description": meta.get("description") or "",
        "n_zones": None,
        "zone_names": [],
        "floor_area_m2": meta.get("floor_area_m2"),
        "source": source,
    }
    try:
        zone_names = parse_idf(p).zone_names()
        entry["n_zones"] = len(zone_names)
        entry["zone_names"] = zone_names
    except Exception:  # noqa: BLE001 — listed honestly with null zone counts
        pass
    return entry


@app.get("/api/models")
def models_list():
    """Dwelling models available for assessment: the author's real DEEP research
    archetypes first, then bundled synthetic templates, then user-uploaded IDFs."""
    meta = _leeds_metadata()
    register = _archetype_register()
    out = []
    if RESEARCH_IDF_DIR.is_dir():
        for p in sorted(RESEARCH_IDF_DIR.glob("*.idf")):
            m = dict(RESEARCH_META.get(p.stem, {}))
            m.setdefault("city", "Leeds")
            reg = register.get(p.stem, {})
            for k in ("kind", "form", "era", "research_status", "sha256",
                      "energyplus_version", "last_validation"):
                if reg.get(k) is not None and m.get(k) is None:
                    m[k] = reg[k]
            if reg.get("era"):
                m["era"] = reg["era"]
            passport = _model_passport(p, "research", "Leeds", m)
            passport["kind"] = reg.get("kind", "research")
            passport["research_status"] = reg.get("research_status")
            out.append(passport)
    if LEEDS_IDF_DIR.is_dir():
        for p in sorted(LEEDS_IDF_DIR.glob("*.idf")):
            out.append(_model_passport(p, "template", "Leeds", meta.get(p.stem.lower())))
    if UPLOAD_IDF_DIR.is_dir():
        for p in sorted(UPLOAD_IDF_DIR.glob("*.idf")):
            out.append(_model_passport(p, "upload", None, None))
    return {"models": out}


@app.post("/api/models/upload")
async def model_upload(request: Request, name: str = Query(...)):
    """Accept an IDF model upload (raw bytes): sanitise, size-guard, sniff for a
    Version object, save, then validate with the core parser. Returns the model
    passport and the readiness check status."""
    body = await request.body()
    if len(body) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "File exceeds the 20 MB upload limit.")
    safe = _sanitise_name(name, ".idf")
    text = body.decode("utf-8", errors="replace")
    if not re.search(r"(?im)^\s*Version\s*,", text):
        raise HTTPException(
            400, "This file is not an IDF: no Version object was found.")
    p = _save_upload(UPLOAD_IDF_DIR, safe, body)
    try:
        idf = parse_idf(p)
        readiness = check_idf(idf).to_dict()
    except Exception as e:  # noqa: BLE001 — invalid upload, do not keep it
        p.unlink(missing_ok=True)
        raise HTTPException(400, f"Cannot parse as IDF: {e}") from e
    return {"model": _model_passport(p, "upload", None, None), "readiness": readiness}


@app.get("/api/weather/check")
def weather_check(path: str = Query(...)):
    p = _safe_epw(path)
    try:
        epw = parse_epw(p)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(422, f"Cannot parse: {e}") from e
    report = check_epw(epw)
    out = report.to_dict()
    out["city"] = epw.header.city.strip()
    out["country"] = epw.header.country.strip()
    out["latitude"] = epw.header.latitude
    out["longitude"] = epw.header.longitude
    out["elevation"] = epw.header.elevation
    if not report.errors:
        try:
            out["weather_summary"] = weather_summary(epw).to_dict()
        except ValueError as e:
            out["weather_summary"] = None
            out["summary_note"] = str(e)
    return out


@app.get("/api/weather/series")
def weather_series(path: str = Query(...)):
    """Hourly dry-bulb series + calendar aggregates for the charts (RULE 28)."""
    p = _safe_epw(path)
    try:
        epw = parse_epw(p)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(422, f"Cannot parse: {e}") from e
    db = _dry_bulb_clean(epw)
    daily = np.nanmean(db.reshape(-1, 24), axis=1)
    # month x hour mean matrix, honest nulls for empty cells
    matrix: list[list[float | None]] = []
    for m in range(1, 13):
        mask = epw.data.month == m
        row: list[float | None] = []
        if mask.any():
            hourly = db[mask].reshape(-1, 24)
            for h in range(24):
                col = hourly[:, h]
                row.append(round(float(np.nanmean(col)), 2)
                           if not np.isnan(col).all() else None)
        else:
            row = [None] * 24
        matrix.append(row)
    # monthly climate fingerprint from the real fields (sentinels cleaned)
    def _monthly_mean(col_idx: int, sentinel: float) -> list:
        from overheatlens.epw.parser import SENTINELS

        col = epw.data.values[:, col_idx].astype(float).copy()
        col[np.isclose(col, sentinel)] = np.nan
        return [round(float(np.nanmean(col[epw.data.month == m])), 2)
                if not np.isnan(col[epw.data.month == m]).all() else None
                for m in range(1, 13)]

    rh_mean = _monthly_mean(8, 999.0)
    ghi_mean = _monthly_mean(13, 9999.0)
    wind_mean = _monthly_mean(21, 999.0)
    # degree days from daily means (heating base 15.5 °C, cooling base 18 °C);
    # build a per-day month array from the calendar (handles leap files)
    import calendar as _cal

    ndays = len(daily)
    leap = ndays == 366
    day_month = np.asarray(
        [m for m in range(1, 13) for _ in range(_cal.monthrange(2004 if leap else 2001, m)[1])]
    )[:ndays]
    hdd, cdd = [], []
    for m in range(1, 13):
        dm = daily[day_month == m]
        dm = dm[~np.isnan(dm)]
        hdd.append(round(float(np.clip(15.5 - dm, 0, None).sum()), 1) if dm.size else None)
        cdd.append(round(float(np.clip(dm - 18.0, 0, None).sum()), 1) if dm.size else None)

    return {
        "name": p.name,
        "dry_bulb": [None if np.isnan(x) else round(float(x), 2) for x in db],
        "daily_mean": [round(float(x), 3) for x in daily],
        "month_hour_matrix": matrix,
        "monthly": monthly_mean_dry_bulb(epw),
        "monthly_db": [round(float(x), 2) if x is not None and not np.isnan(x) else None
                       for x in [np.nanmean(db[epw.data.month == m]) if (epw.data.month == m).any() else np.nan
                                 for m in range(1, 13)]],
        "monthly_rh": rh_mean,
        "monthly_ghi": ghi_mean,
        "monthly_wind": wind_mean,
        "hdd15_5": hdd,
        "cdd18": cdd,
    }


def _run_analysis(p: Path, pack_id: str, model: Path | None = None) -> dict:
    """Full pipeline: readiness → EnergyPlus → standards.

    Shared by POST /api/analyze, GET /api/report and POST /api/comfort/run;
    results are cached per (resolved weather path, resolved model path, pack id)
    so a report never re-runs a simulation."""
    model = (model or DEMO_IDF).resolve()
    key = (str(p), str(model), pack_id)
    with _cache_lock:
        if key in _run_cache:
            return _run_cache[key]

    try:
        readiness = check_idf(parse_idf(model)).to_dict()
        run = run_energyplus(model, p, timeout_s=600)
        if run.status != "complete" or run.csv_path is None:
            raise HTTPException(500, {
                "message": "EnergyPlus run failed",
                "err": run.err.to_dict(),
            })
        from overheatlens.worker import harvest_hourly, harvest_meters

        zones = harvest_hourly(run.csv_path)
        epw = parse_epw(p)
        db = epw.valid_dry_bulb()
        daily = np.nanmean(db.reshape(-1, 24), axis=1)
        engine = StandardsEngine.load(pack_id)
        rooms = [(z, z.replace("_", " ").title(), np.asarray(v["top"]))
                 for z, v in zones.items()]
        result = engine.evaluate_dwelling(
            rooms, category="II", daily_mean_outdoor=daily, mode="compliance")
        # per-zone hourly Top series for the time view (rounded, real data)
        series = {z: [round(x, 2) for x in v["top"]] for z, v in zones.items()}
        # harvested relative humidity (rounded, real data; None when not output)
        rh = {z: ([round(x, 2) for x in v["rh"]] if v.get("rh") else None)
              for z, v in zones.items()}
        # annual facility energy from the author's Output:Meter requests
        # (real meters, never estimated; None when the model carries none)
        energy = (harvest_meters(run.meter_path)
                  if run.meter_path else {})
        # full-standards summary: the SAME simulation judged by every
        # compliance-allowed pack — no extra EnergyPlus runs
        standards_summary = []
        for other in available_pack_ids():
            try:
                other_engine = StandardsEngine.load(other)
                if not other_engine.compliance_allowed():
                    continue
                other_result = other_engine.evaluate_dwelling(
                    rooms, category="II", daily_mean_outdoor=daily,
                    mode="compliance")
                standards_summary.append({
                    "pack_id": other,
                    "overall": other_result.get("overall"),
                    "pack_version": other_result.get("pack_version"),
                    "chosen": other == pack_id,
                })
            except Exception:  # noqa: BLE001 — one pack failing must not kill the run
                standards_summary.append({"pack_id": other, "overall": "INCOMPLETE",
                                          "chosen": other == pack_id})
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"Pipeline error: {e}") from e

    model_name = ("Synthetic two-zone dwelling (demo fixture)" if model == DEMO_IDF
                  else model.stem.replace("_", " "))
    payload = {
        "model": {"name": model_name, "path": str(model)},
        "weather": {"name": p.name, "path": str(p)},
        "rule_pack": engine.standards_passport(),
        "readiness": readiness,
        "run": run.to_dict(),
        "result": result,
        "standards_summary": standards_summary,
        "series": series,
        "rh": rh,
        "energy": energy,
        "daily_mean_outdoor": [round(float(x), 3) for x in daily],
        "cached": False,
    }
    # thermal comfort on the actual simulated temperatures (PMV + adaptive EN,
    # library-only mathematics); a comfort failure must not kill the analysis
    try:
        payload["comfort"] = _comfort_from_run(payload, p)
    except Exception as e:  # noqa: BLE001
        payload["comfort"] = {"assumptions": None, "zones": [],
                              "note": f"comfort evaluation failed: {e}"}
    with _cache_lock:
        _run_cache[key] = {**payload, "cached": True}
    _persist_run(key, payload)
    return payload


def _persist_run(key: tuple[str, str, str], payload: dict) -> Path | None:
    """Persist a fresh run payload to the on-disk archive (data/runs).

    The archive survives server restarts; uploads stay local by design. Any
    persistence failure is swallowed — the in-memory result still stands."""
    try:
        RUNS_DIR.mkdir(parents=True, exist_ok=True)
        run_id = payload.get("run", {}).get("run_id") or "run-unknown"
        safe_id = re.sub(r"[^A-Za-z0-9._-]", "_", run_id)
        record = {
            "run_id": run_id,
            "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "weather_path": key[0],
            "model_path": key[1],
            "pack_id": key[2],
            "payload": payload,
        }
        dest = RUNS_DIR / f"{safe_id}.json"
        if not dest.exists():
            dest.write_text(json.dumps(record, default=str))
        return dest
    except Exception:  # noqa: BLE001 — persistence must never fail a run
        return None


def _archive_records() -> list[dict]:
    """Session cache + on-disk archive merged newest-first (disk wins ties)."""
    seen: dict[str, dict] = {}
    if RUNS_DIR.is_dir():
        for p in sorted(RUNS_DIR.glob("*.json"), reverse=True):
            try:
                rec = json.loads(p.read_text())
            except (OSError, ValueError):
                continue
            payload = rec.get("payload", {}) if isinstance(rec, dict) else {}
            rid = rec.get("run_id") if isinstance(rec, dict) else None
            if not rid:
                continue
            seen[rid] = {
                "run_id": rid,
                "created_utc": rec.get("created_utc"),
                "weather": Path(rec.get("weather_path", "")).name,
                "model": Path(rec.get("model_path", "")).name or None,
                "pack_id": rec.get("pack_id"),
                "overall": (payload.get("result", {}) or {}).get("overall"),
                "source": "archive",
            }
    with _cache_lock:
        for (wp, mp, pk), payload in _run_cache.items():
            rid = (payload.get("run", {}) or {}).get("run_id")
            if not rid or rid in seen:
                continue
            seen[rid] = {
                "run_id": rid,
                "created_utc": None,
                "weather": Path(wp).name,
                "model": Path(mp).name if mp else None,
                "pack_id": pk,
                "overall": (payload.get("result", {}) or {}).get("overall"),
                "source": "session",
            }
    return list(seen.values())


def _load_archived_run(run_id: str) -> dict:
    safe_id = re.sub(r"[^A-Za-z0-9._-]", "_", run_id)
    p = RUNS_DIR / f"{safe_id}.json"
    if not p.is_file():
        # fall back to the session cache for runs not yet flushed
        with _cache_lock:
            for payload in _run_cache.values():
                if (payload.get("run", {}) or {}).get("run_id") == run_id:
                    return {"run_id": run_id, "payload": payload, "source": "session"}
        raise HTTPException(404, f"Run not found in the archive: {run_id}")
    try:
        return {**json.loads(p.read_text()), "source": "archive"}
    except (OSError, ValueError) as e:
        raise HTTPException(500, f"Cannot read archived run: {e}") from e


@app.post("/api/analyze")
def analyze(weather_path: str = Query(...), pack_id: str = Query("uk_tm59_2017"),
            model_path: str | None = Query(None)):
    """Run the full pipeline with the chosen weather file and model
    (default: the bundled synthetic two-zone dwelling)."""
    p = _safe_epw(weather_path)
    m = _safe_idf(model_path) if model_path else None
    return _run_analysis(p, pack_id, m)


@app.get("/api/report", response_class=HTMLResponse)
def report(weather_path: str = Query(...), pack_id: str = Query("uk_tm59_2017"),
           model_path: str | None = Query(None)):
    """Self-contained printable HTML assessment report for the chosen run."""
    p = _safe_epw(weather_path)
    m = _safe_idf(model_path) if model_path else None
    payload = _run_analysis(p, pack_id, m)
    return HTMLResponse(render_html_report(payload))


def _comfort_assumptions() -> dict:
    from overheatlens.comfort.models import LIBRARY, LIBRARY_VERSION

    return {
        "operative_temperature": "Top = 0.5 × (MAT + MRT), derived "
                                 "(standard low-air-speed approximation)",
        "tdb": "hourly Top from the EnergyPlus run",
        "tr": "set equal to Top",
        "rh": "Zone Air Relative Humidity harvested from the same run "
              "(missing where the model does not output it)",
        "air_speed_m_s": 0.1,
        "met": 1.2,
        "clo": 0.35,
        "clo_basis": "summer clothing ensemble — a stated assumption, not measured",
        "occupied_hours": "09:00–22:00 (hour-ending labels 10–22, the engine's "
                          "TM59:2026 living-hours mask)",
        "assessment_window": "May–September",
        "adaptive_standard": "EN 16798-1, Category II acceptability",
        "ppd_standard": "ISO 7730:2025 (Fanger PMV/PPD)",
        "trm": "EN 16798-1 running mean of the outdoor daily mean dry-bulb "
               "temperature (library utility, α = 0.8, previous 7 days)",
        "excluded_hours_policy": "hours where the library returns no value are "
                                 "excluded from the share and counted; nothing is "
                                 "extrapolated or invented",
        "library": LIBRARY,
        "library_version": LIBRARY_VERSION,
    }


def _comfort_from_run(payload: dict, epw_path: Path) -> dict:
    """Real comfort from the cached run — library-only mathematics (RULE 4).

    Per zone over the May–September occupied window: EN 16798-1 adaptive
    Category II acceptability share and Fanger mean PPD, computed by
    pythermalcomfort on the run's hourly Top (tdb = tr = Top) with harvested RH.
    Hours the library cannot evaluate are excluded and counted; a zone metric
    is null (with a reason) when no hour is evaluable.
    """
    from pythermalcomfort.models import adaptive_en, pmv_ppd_iso

    top_by_zone = payload["series"]
    rh_by_zone = payload.get("rh") or {}
    n_hours = len(next(iter(top_by_zone.values())))
    epw = parse_epw(epw_path)
    dm = np.asarray(payload["daily_mean_outdoor"], dtype=float)

    zones_out: list[dict] = []
    if 24 * len(dm) != n_hours:
        note = ("run length does not match the weather calendar — "
                "comfort not evaluated")
        return {"assumptions": _comfort_assumptions(), "zones": [], "note": note,
                "model": payload["model"], "weather": payload["weather"],
                "run_id": payload["run"]["run_id"]}

    months = np.asarray(epw.data.month, dtype=int)[:n_hours]
    hours = np.asarray(epw.data.hour, dtype=int)[:n_hours]
    from overheatlens.standards.engine import _LIVING_HOURS_2026

    mask = ((months >= 5) & (months <= 9)
            & np.isin(hours, sorted(_LIVING_HOURS_2026)))
    # Per-day Trm from the library's own EN 16798-1 utility (α = 0.8, previous
    # 7 daily means, newest first). Day one has no history → undefined (NaN);
    # it lies outside the May–September window anyway.
    from pythermalcomfort.utilities import running_mean_outdoor_temperature

    trm = np.full(len(dm), np.nan)
    for i in range(1, len(dm)):
        trm[i] = running_mean_outdoor_temperature(
            [float(x) for x in dm[max(0, i - 7):i][::-1]], alpha=0.8)
    trm_hourly = np.repeat(trm, 24)[:n_hours]

    n_win = int(mask.sum())
    for zone, top_list in top_by_zone.items():
        top = np.asarray(top_list, dtype=float)
        tm = top[mask]
        reason: str | None = None

        # --- adaptive EN 16798-1 Category II (library-computed) ------------------
        pct = None
        excl = n_win
        if n_win == 0:
            reason = "no May–September occupied hours in this weather file"
        else:
            r = adaptive_en(tdb=tm, tr=tm, t_running_mean=trm_hourly[mask],
                            v=0.1, limit_inputs=False, round_output=False)
            acc = np.asarray(r.acceptability_cat_ii, dtype=float)
            valid = np.isfinite(acc)
            excl = int((~valid).sum())
            if valid.any():
                pct = round(float(100.0 * acc[valid].mean()), 1)
            else:
                reason = ("adaptive model returned no verdict — outside EN 16798-1 "
                          "applicability")

        # --- Fanger PPD (library-computed, harvested RH) --------------------------
        ppd = None
        ppd_excl = n_win
        rh_list = rh_by_zone.get(zone)
        if n_win == 0:
            pass
        elif not rh_list:
            reason = reason or ("model does not output Zone Air Relative Humidity — "
                                "PPD not evaluated")
        else:
            rh_m = np.asarray(rh_list, dtype=float)[mask]
            try:
                with np.errstate(invalid="ignore"):
                    rr = pmv_ppd_iso(tdb=tm, tr=tm, vr=0.1, rh=rh_m,
                                     met=1.2, clo=0.35, limit_inputs=False,
                                     round_output=False)
                ppd_arr = np.asarray(rr.ppd, dtype=float)
            except Exception:  # noqa: BLE001 — an explicit non-result, never a guess
                ppd_arr = np.asarray([])
            valid_ppd = np.isfinite(ppd_arr)
            ppd_excl = int(valid_ppd.size - valid_ppd.sum())
            if valid_ppd.any():
                ppd = round(float(ppd_arr[valid_ppd].mean()), 1)
            else:
                reason = reason or ("PPD not evaluable — the library returned no "
                                    "value for these hours")

        zones_out.append({
            "zone": zone,
            "adaptive_acceptable_pct": pct,
            "adaptive_hours_evaluated": n_win - excl,
            "adaptive_hours_excluded": excl,
            "mean_ppd": ppd,
            "ppd_hours_evaluated": n_win - ppd_excl,
            "ppd_hours_excluded": ppd_excl,
            "max_top": round(float(tm.max()), 2) if n_win else None,
            "reason": reason,
        })

    return {
        "assumptions": _comfort_assumptions(),
        "zones": zones_out,
        "model": payload["model"],
        "weather": payload["weather"],
        "run_id": payload["run"]["run_id"],
        "computed_from": "the cached EnergyPlus run — real simulated temperatures, "
                         "comfort mathematics by the wrapped library only",
    }


@app.post("/api/comfort/run")
def comfort_run(weather_path: str = Query(...), pack_id: str = Query("uk_tm59_2017"),
                model_path: str | None = Query(None)):
    """Comfort computed from a real run: reuses the cached analysis, then evaluates
    EN 16798-1 adaptive acceptability and Fanger PPD from the simulated hourly
    conditions. All assumptions are stated in the response."""
    p = _safe_epw(weather_path)
    m = _safe_idf(model_path) if model_path else None
    payload = _run_analysis(p, pack_id, m)
    return _comfort_from_run(payload, p)


@app.get("/api/validation")
def validation_matrix():
    md_path = REPO_ROOT / "VALIDATION_MATRIX.md"
    rows: list[dict] = []
    section = ""
    for line in md_path.read_text().splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
        if line.startswith("|") and "---" not in line:
            cells = [c.strip().replace("`", "") for c in line.strip("|").split("|")]
            if cells and cells[0] not in ("ID", "Method", ""):
                rows.append({"section": section, "cells": cells})
    return {"source": "VALIDATION_MATRIX.md", "rows": rows}


# --- comfort lab (Phase 4 wrappers exposed) ------------------------------------

@app.get("/api/comfort/pmv")
def comfort_pmv(tdb: float, tr: float, vr: float, rh: float, met: float, clo: float):
    from overheatlens.comfort import pmv_ppd

    return pmv_ppd(tdb=tdb, tr=tr, vr=vr, rh=rh, met=met, clo=clo).to_dict()


@app.get("/api/comfort/adaptive")
def comfort_adaptive(tdb: float, tr: float, trm: float, v: float):
    from overheatlens.comfort import adaptive_comfort_en

    return adaptive_comfort_en(tdb=tdb, tr=tr, t_running_mean=trm, v=v).to_dict()


@app.get("/api/comfort/utci")
def comfort_utci(tdb: float, tr: float, v: float, rh: float):
    from overheatlens.comfort import utci_comfort

    return utci_comfort(tdb=tdb, tr=tr, v=v, rh=rh).to_dict()


# --- compare (multi-EPW, Phase 9 first slice) -----------------------------------

@app.get("/api/compare")
def compare(paths: str):
    """Headline metrics + ribbon data for 2-8 weather files (comma-separated)."""
    req = [p.strip() for p in paths.split(",") if p.strip()]
    if not (2 <= len(req) <= 8):
        raise HTTPException(400, "Compare needs between 2 and 8 weather files.")
    out = []
    for raw in req:
        p = _safe_epw(raw)
        epw = parse_epw(p)
        db = _dry_bulb_clean(epw)
        summary = weather_summary(epw)
        out.append({
            "name": p.name,
            "path": str(p),
            "annual_mean": summary.annual_mean_dry_bulb,
            "hottest": summary.hottest_hour,
            "hours_over_26": summary.exceedance_hours_26c,
            "degree_hours_26": summary.degree_hours_26c,
            "daily_mean": [round(float(x), 3) for x in
                           np.nanmean(db.reshape(-1, 24), axis=1)],
        })
    return {"files": out}


@app.get("/api/runs")
def runs_list():
    """Every analysis: this session plus the persistent on-disk archive."""
    return {"runs": _archive_records()}


@app.get("/api/runs/{run_id}")
def run_detail(run_id: str):
    """Full payload of one archived run (criteria, series, provenance)."""
    return _load_archived_run(run_id)


@app.delete("/api/runs/{run_id}")
def run_delete(run_id: str):
    """Delete a local archived run (file + session cache entry)."""
    safe_id = re.sub(r"[^A-Za-z0-9._-]", "_", run_id)
    p = RUNS_DIR / f"{safe_id}.json"
    removed = False
    if p.is_file():
        p.unlink()
        removed = True
    with _cache_lock:
        for key, payload in list(_run_cache.items()):
            if (payload.get("run", {}) or {}).get("run_id") == run_id:
                del _run_cache[key]
                removed = True
    if not removed:
        raise HTTPException(404, f"Run not found: {run_id}")
    return {"deleted": run_id}


@app.post("/api/batch")
def batch_run(body: dict):
    """Controlled batch: one building × many weather files, one weather × many
    buildings, or a full matrix. Sequential execution (bounded E+ load); each
    entry reuses the cached pipeline so repeats are free. Body:
    {"runs": [{"weather_path, "model_path"?, "pack_id"?}], "pack_id"?}."""
    req = body.get("runs") if isinstance(body, dict) else None
    if not isinstance(req, list) or not req:
        raise HTTPException(400, "Body needs a non-empty 'runs' list.")
    if len(req) > MAX_BATCH_RUNS:
        raise HTTPException(400, f"Batch capped at {MAX_BATCH_RUNS} runs — split it.")
    default_pack = body.get("pack_id", "uk_tm59_2017") if isinstance(body, dict) else "uk_tm59_2017"
    results: list[dict] = []
    for entry in req:
        if not isinstance(entry, dict) or "weather_path" not in entry:
            results.append({"error": "each entry needs 'weather_path'", "entry": entry})
            continue
        pack_id = entry.get("pack_id") or default_pack
        try:
            p = _safe_epw(entry["weather_path"])
            m = _safe_idf(entry["model_path"]) if entry.get("model_path") else None
            payload = _run_analysis(p, pack_id, m)
            results.append({
                "run_id": (payload.get("run", {}) or {}).get("run_id"),
                "weather": Path(entry["weather_path"]).name,
                "model": Path(entry["model_path"]).name if entry.get("model_path") else None,
                "pack_id": pack_id,
                "overall": (payload.get("result", {}) or {}).get("overall"),
                "cached": payload.get("cached", False),
            })
        except HTTPException as e:
            detail = e.detail
            results.append({
                "weather": Path(str(entry.get("weather_path"))).name,
                "model": entry.get("model_path"),
                "pack_id": pack_id,
                "error": detail if isinstance(detail, str) else "run failed",
            })
        except Exception as e:  # noqa: BLE001
            results.append({"weather": entry.get("weather_path"), "error": str(e)})
    return {"runs": results, "count": len(results)}


@app.get("/api/models/detail")
def model_detail(path: str = Query(...)):
    """Full model dossier: passport, readiness, provenance hash, object census."""
    from overheatlens.idf import build_passport

    p = _safe_idf(path)
    idf = parse_idf(p)
    readiness = check_idf(idf).to_dict()
    try:
        built = build_passport(idf)
        passport = built.to_dict() if hasattr(built, "to_dict") else built
    except Exception:  # noqa: BLE001 — passport is supplementary
        passport = {}
    sha = hashlib.sha256(p.read_bytes()).hexdigest()
    census: dict[str, int] = {}
    try:
        for t in idf.types():
            census[t] = len(idf.of_type(t))
    except Exception:  # noqa: BLE001
        pass
    version = None
    try:
        for obj in idf.of_type("Version"):
            version = ",".join(f.strip() for f in obj.fields if f.strip())
    except Exception:  # noqa: BLE001
        pass
    return {
        "path": str(p),
        "name": p.stem,
        "sha256": sha,
        "size_kb": round(p.stat().st_size / 1024),
        "energyplus_version": version,
        "zone_names": idf.zone_names(),
        "n_zones": len(idf.zone_names()),
        "object_census": census,
        "passport": passport,
        "readiness": readiness,
    }


@app.get("/api/mitigation/catalogue")
def mitigation_catalogue():
    """Safer_Heat_Harehills parametric catalogue (01BA/17BG/27BG × strategies).

    Real DesignBuilder TM59 exports parsed by scripts/build_mitigation_catalogue.py.
    Honest empty state until the builder has been run against the research folder.
    House codes stay as machine keys in the payload; `house_names` maps each code
    to its public typology name for display (never show case-study codes)."""
    if not MITIGATION_SUMMARY.is_file():
        return {"status": "not_generated",
                "detail": "Run scripts/build_mitigation_catalogue.py against the "
                          "Safer_Heat_Harehills research folder to generate "
                          "data/mitigation/summary.json (kept local, never committed)."}
    try:
        catalogue = json.loads(MITIGATION_SUMMARY.read_text())
    except (OSError, ValueError) as e:
        raise HTTPException(500, f"Cannot read mitigation catalogue: {e}") from e
    prefix_to_name = {}
    for stem, meta in RESEARCH_META.items():
        code = stem.split("_")[0]
        if code and meta.get("name"):
            prefix_to_name[code] = meta["name"]
    house_names = {code: prefix_to_name.get(code, code)
                   for code in (catalogue.get("houses") or {})}
    return {"status": "ready", "house_names": house_names, "catalogue": catalogue}


VALIDATION_RESULTS = REPO_ROOT / "validation" / "results.json"
VARIANT_IDF_DIR = REPO_ROOT / "data" / "archetypes" / "idf" / "variants"
VARIANTS = {"S2_restricted": "S2 — restricted window opening",
            "S3_nightpurge": "S3 — night-purge ventilation"}


@app.get("/api/validation/campaign")
def validation_campaign():
    """Independent scientific validation campaign (validation/run_campaign.py).

    Returns the latest machine-written results; INCOMPLETE when the campaign
    has not been run on this machine yet."""
    if not VALIDATION_RESULTS.is_file():
        return {"status": "not_run",
                "detail": "Run ./.venv/bin/python validation/run_campaign.py to "
                          "produce validation/results.json (see validation/METHOD.md)."}
    try:
        raw = json.loads(VALIDATION_RESULTS.read_text())
    except (OSError, ValueError) as e:
        raise HTTPException(500, f"Cannot read validation results: {e}") from e
    return {"status": "ready", "results": raw,
            "method": "validation/METHOD.md"}


ENERGY_METERS = {"Electricity:Facility": "electricity_kwh",
                 "NATURALGAS:Facility": "gas_kwh",
                 "DistrictHeatingWater:Facility": "district_heating_kwh",
                 "DistrictCooling:Facility": "district_cooling_kwh"}


def _energy_row(payload: dict) -> dict:
    """Facility energy breakdown + total for one analysed run (kWh/yr)."""
    energy = payload.get("energy") or {}
    row = {field: (energy.get(meter) or {}).get("annual_kwh")
           for meter, field in ENERGY_METERS.items()}
    known = [v for v in row.values() if v is not None]
    row["total_kwh"] = round(sum(known), 1) if known else None
    row["energy_reported"] = bool(known)
    return row


def _variant_is_stub(variant_path: Path) -> bool:
    """True when the stored variant IDF defines its scenario schedule but no
    model object references it (schedule named exactly once — its definition).
    Such exports carry no active variant physics: identical results to the
    baseline are the correct outcome, and energy savings must not be claimed."""
    try:
        text = variant_path.read_text(errors="replace").lower()
    except OSError:
        return True
    sched = "s2_restrictedvent" if "_s2_" in variant_path.name.lower() \
        else "s3_nightpurgevent"
    return text.count(sched) <= 1


@app.post("/api/mitigation/energy_experiment")
def mitigation_energy_experiment(model_id: str = Query(...),
                                 weather_path: str = Query(...)):
    """Real paired EnergyPlus experiment: baseline vs the author's stored
    strategy variants (S2/S3) on the chosen weather, reporting annual facility
    energy and TM59 verdicts from the SAME validated pipeline.

    Only the author's own research models are allowed. Every row is an actual
    simulation; variants without stored IDFs are listed as unavailable —
    nothing is extrapolated."""
    if model_id not in RESEARCH_META:
        raise HTTPException(400, f"Unknown research model: {model_id}")
    p = _safe_epw(weather_path)
    base_idf = RESEARCH_IDF_DIR / f"{model_id}.idf"
    if not base_idf.is_file():
        raise HTTPException(404, f"Base IDF missing: {model_id}")

    def _row_for(payload: dict, strategy: str, stem: str) -> dict:
        row = {"strategy": strategy, "status": "complete", "model_id": stem,
               "run_id": (payload.get("run") or {}).get("run_id"),
               "tm59_overall": (payload.get("result") or {}).get("overall"),
               "standards_summary": payload.get("standards_summary") or [],
               "comfort": payload.get("comfort") or {}}
        row.update(_energy_row(payload))
        return row

    rows = []
    for suffix, label in VARIANTS.items():
        variant_path = VARIANT_IDF_DIR / f"{model_id}_{suffix}.idf"
        if not variant_path.is_file():
            rows.append({"strategy": label, "status": "INCOMPLETE",
                         "total_saved_kwh": None, "total_saved_pct": None,
                         "note": "no stored variant IDF for this model"})
            continue
        payload = _run_analysis(p, "uk_tm59_2017", variant_path)
        row = _row_for(payload, label, f"{model_id}_{suffix}")
        if _variant_is_stub(variant_path):
            # the export defines the scenario schedule but nothing references it:
            # identical-to-baseline results are physically correct, and no saving
            # may be claimed from a variant with no active physics
            row["status"] = "INCOMPLETE"
            row["total_saved_kwh"] = None
            row["total_saved_pct"] = None
            row["note"] = ("stored IDF export defines the scenario schedule but no "
                           "model object references it — the active variant physics "
                           "lives in the DesignBuilder study, so no saving can be "
                           "computed from this export")
        rows.append(row)

    baseline = _row_for(_run_analysis(p, "uk_tm59_2017", base_idf),
                        "Baseline (as measured)", model_id)

    for row in rows:
        row.setdefault("total_saved_kwh", None)
        row.setdefault("total_saved_pct", None)
        if row.get("status") == "complete" and baseline.get("total_kwh") is not None \
                and row.get("total_kwh") is not None:
            saved = baseline["total_kwh"] - row["total_kwh"]
            row["total_saved_kwh"] = round(saved, 1)
            row["total_saved_pct"] = (round(100.0 * saved / baseline["total_kwh"], 1)
                                      if baseline["total_kwh"] else None)
        elif row.get("status") == "complete":
            row["note"] = ("model carries no facility energy meters — saving "
                           "cannot be computed (INCOMPLETE, not estimated)")

    return {"status": "ready",
            "model": {"id": model_id, "name": RESEARCH_META[model_id]["name"]},
            "weather": {"path": str(p), "name": p.name},
            "baseline": baseline, "strategies": rows}


@app.get("/api/bundle")
def reproducibility_bundle(run_id: str = Query(...)):
    """Reproducibility ZIP for one archived run: inputs, manifest, results,
    criteria CSV, report HTML, provenance. Everything stays local."""
    rec = _load_archived_run(run_id)
    payload = rec.get("payload", {})
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps({
            "run_id": run_id,
            "exported_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "app": "OverheatLens",
            "core_version": CORE_VERSION,
            "weather_path": rec.get("weather_path"),
            "model_path": rec.get("model_path"),
            "pack_id": rec.get("pack_id"),
            "run_manifest": payload.get("run"),
        }, indent=2, default=str))
        z.writestr("results.json", json.dumps(payload.get("result"), indent=2, default=str))
        # criteria CSV: room × criterion evidence table
        lines = ["room,room_type,criterion,rule_ref,result,metric,threshold,units"]
        for room in (payload.get("result", {}) or {}).get("rooms", []) or []:
            for c in room.get("criteria", []) or []:
                metric = c.get("metric_value")
                cells = [str(room.get("room_id", "")), str(room.get("room_type", "")),
                         str(c.get("criterion_id", "")), str(c.get("rule_ref", "")),
                         str(c.get("status", "")), "" if metric is None else str(metric),
                         str(c.get("threshold", "")), str(c.get("units", ""))]
                lines.append(",".join('"' + x.replace('"', '""') + '"' for x in cells))
        z.writestr("criteria.csv", "\n".join(lines))
        try:
            z.writestr("report.html", render_html_report(payload))
        except Exception as e:  # noqa: BLE001 — report is supplementary
            z.writestr("report_error.txt", f"Report render failed: {e}")
        # input files by bytes (local-only bundle; capped at 50 MB each)
        for label, key in (("input_model.idf", rec.get("model_path")),
                           ("input_weather.epw", rec.get("weather_path"))):
            try:
                if key and Path(key).is_file() and Path(key).stat().st_size < 50_000_000:
                    z.write(key, label)
            except Exception:  # noqa: BLE001
                pass
        prov = payload.get("run", {}) or {}
        manifest = prov.get("manifest", {}) or {}
        z.writestr("provenance.txt",
                   f"run_id: {run_id}\nengine: EnergyPlus {prov.get('energyplus_version')}\n"
                   f"idf_sha256: {manifest.get('idf_sha256')}\nepw_sha256: {manifest.get('epw_sha256')}\n"
                   f"rule_pack: {rec.get('pack_id')}\n")
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/zip",
                             headers={"Content-Disposition": f'attachment; filename="{run_id}.zip"'})


# --- static web (built by the launcher; absent in dev) -------------------------
_web_dist = REPO_ROOT / "apps" / "web" / "dist"
if _web_dist.is_dir():
    app.mount("/", StaticFiles(directory=str(_web_dist), html=True), name="web")
else:
    @app.get("/")
    def _no_web():
        return {"hint": "web app not built yet — run the Start launcher"}


@app.exception_handler(404)
async def _spa_fallback(request, exc):  # noqa: ANN001
    if _web_dist.is_dir() and not request.url.path.startswith("/api"):
        return FileResponse(_web_dist / "index.html")
    from fastapi.responses import JSONResponse

    return JSONResponse({"detail": getattr(exc, "detail", "Not Found")}, 404)
