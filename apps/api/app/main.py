"""OverheatLens API — a thin, honest Phase-7 slice over the authoritative core.

Every endpoint calls the core package; nothing here recomputes science. The API
serves the built web app from apps/web/dist so the launcher needs one port only.

Security posture (plan §26, current stage): localhost tool. Path parameters for
weather files are resolved against a configured weather directory; no shell
commands; the EnergyPlus run writes only into its own temp directory.
"""

from __future__ import annotations

import os
import threading
from pathlib import Path

import numpy as np
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

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

app = FastAPI(title="OverheatLens API", version=CORE_VERSION)

_run_cache: dict[tuple[str, str], dict] = {}
_cache_lock = threading.Lock()


def _safe_epw(path: str) -> Path:
    """Resolve a weather-file path against the allowed roots (weather dir, bundled
    fixtures, temp dir for launcher-provided files). No arbitrary filesystem reads."""
    import tempfile

    p = Path(path).resolve()
    if p.suffix.lower() != ".epw":
        raise HTTPException(400, "Only .epw files can be read.")
    allowed = [WEATHER_DIR.resolve(),
               (REPO_ROOT / "fixtures" / "epw").resolve(),
               Path(tempfile.gettempdir()).resolve()]
    if not any(p == root or root in p.parents for root in allowed):
        raise HTTPException(403, "Weather file is outside the configured library.")
    if not p.is_file():
        raise HTTPException(404, f"Weather file not found: {p.name}")
    return p


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
    return {"weather_dir": str(WEATHER_DIR), "files": files}


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
    return {
        "name": p.name,
        "dry_bulb": [None if np.isnan(x) else round(float(x), 2) for x in db],
        "daily_mean": [round(float(x), 3) for x in daily],
        "month_hour_matrix": matrix,
        "monthly": monthly_mean_dry_bulb(epw),
    }


@app.post("/api/analyze")
def analyze(weather_path: str = Query(...), pack_id: str = Query("uk_tm59_2017")):
    """Run the full pipeline on the demo dwelling with the chosen weather file."""
    p = _safe_epw(weather_path)
    if not DEMO_IDF.is_file():
        raise HTTPException(500, "demo model missing from the installation")
    key = (str(p), pack_id)
    with _cache_lock:
        if key in _run_cache:
            return _run_cache[key]

    try:
        readiness = check_idf(parse_idf(DEMO_IDF)).to_dict()
        run = run_energyplus(DEMO_IDF, p, timeout_s=600)
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
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"Pipeline error: {e}") from e

    payload = {
        "model": {"name": "Synthetic two-zone dwelling (demo fixture)",
                  "path": str(DEMO_IDF)},
        "weather": {"name": p.name, "path": str(p)},
        "rule_pack": engine.standards_passport(),
        "readiness": readiness,
        "run": run.to_dict(),
        "result": result,
        "series": series,
        "daily_mean_outdoor": [round(float(x), 3) for x in daily],
        "cached": False,
    }
    with _cache_lock:
        _run_cache[key] = {**payload, "cached": True}
    return payload


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
