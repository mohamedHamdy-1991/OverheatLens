"""OverheatLens API — a thin, honest Phase-7 slice over the authoritative core.

Every endpoint calls the core package; nothing here recomputes science. The API
serves the built web app from apps/web/dist so the launcher needs one port only.

Security posture (plan §26, current stage): localhost tool. Path parameters for
weather files are resolved against a configured weather directory; no shell
commands; the EnergyPlus run writes only into its own temp directory.
"""

from __future__ import annotations

import json
import os
import re
import threading
from pathlib import Path

import numpy as np
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from .report import render_html_report
from overheatlens import CORE_VERSION
from overheatlens.epw import check_epw, parse_epw, weather_summary, monthly_mean_dry_bulb
from overheatlens.idf import check_idf, parse_idf
from overheatlens.schemas import load_bundled_pack
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
MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # plan §26.2: maximum upload, enforced first

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
    allowed = [(REPO_ROOT / "fixtures" / "idf").resolve(), UPLOAD_IDF_DIR.resolve()]
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
    """Dwelling models available for assessment: bundled Leeds archetype templates
    (metadata merged when present) plus user-uploaded IDFs."""
    meta = _leeds_metadata()
    out = []
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
        from overheatlens.worker import harvest_hourly

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
        "series": series,
        "rh": rh,
        "daily_mean_outdoor": [round(float(x), 3) for x in daily],
        "cached": False,
    }
    with _cache_lock:
        _run_cache[key] = {**payload, "cached": True}
    return payload


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
    """Analyses completed in this server session (real runs only)."""
    out = []
    for (wp, mp, pk), payload in _run_cache.items():
        out.append({
            "run_id": payload.get("run", {}).get("run_id"),
            "weather": Path(wp).name,
            "model": Path(mp).name if mp else None,
            "pack_id": pk,
            "overall": payload.get("result", {}).get("overall"),
        })
    return {"runs": out}


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
