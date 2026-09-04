#!/usr/bin/env python3
"""OverheatLens — full application validation.

Tests every layer of the shipped application and writes a dated report:

  A. Environment      — Python, scientific deps, EnergyPlus binary, Node
  B. Core suite       — pytest packages/overheatlens-core/tests
  C. API suite        — pytest apps/api/tests
  D. Web build+tests  — npm run build && vitest run (skipped without Node)
  E. Live walkthrough — every endpoint through the real app: rule packs, weather
                        check/series, EPW + IDF upload round-trips (and rejection
                        of invalid files), model listing, EnergyPlus analyses of
                        the demo dwelling AND every Leeds archetype, comfort from
                        the run, the HTML report, compare, validation matrix,
                        runs list, and the upload/path security guards.

Report: docs/validation/FULL_APP_VALIDATION_REPORT.md
Exit code 0 only when every non-skipped check passes.

Usage (from anywhere):
    python3 scripts/validate_app.py [--skip-web] [--skip-heavy]
"""

from __future__ import annotations

import importlib
import json
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "packages" / "overheatlens-core"))
sys.path.insert(0, str(REPO / "apps"))
if "APPS_PARENT" not in sys.path[0]:
    # apps.api imports require the repo root on the path as a namespace package
    sys.path.insert(0, str(REPO))

SKIP_WEB = "--skip-web" in sys.argv
SKIP_HEAVY = "--skip-heavy" in sys.argv

RESULTS: list[dict] = []


def record(section: str, check_id: str, description: str, ok: bool | None,
           detail: str = "") -> bool | None:
    status = {True: "PASS", False: "FAIL", None: "SKIP"}[ok]
    RESULTS.append({"section": section, "id": check_id, "desc": description,
                    "status": status, "detail": detail})
    icon = {"PASS": "✓", "FAIL": "✗", "SKIP": "–"}[status]
    print(f"  [{icon}] {check_id}: {description}" + (f" — {detail}" if detail else ""))
    return ok


def run_suite(name: str, cmd: list[str], cwd: Path, check_id: str) -> None:
    print(f"\n=== {name} ===")
    t0 = time.time()
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=3600)
        tail = "\n".join((p.stdout + p.stderr).strip().splitlines()[-3:])
        record(name, check_id, f"{name} ({' '.join(cmd[:3])}…)",
               p.returncode == 0, f"{p.returncode == 0 and 'all passed' or tail} "
               f"[{time.time() - t0:.0f}s]")
    except subprocess.TimeoutExpired:
        record(name, check_id, name, False, "timed out after 3600s")
    except FileNotFoundError as e:
        record(name, check_id, name, None, f"not available: {e}")


def main() -> int:
    started = datetime.now(timezone.utc)
    print(f"OverheatLens full application validation — {started:%Y-%m-%d %H:%M} UTC")
    print(f"Repository: {REPO}\n")

    # ---------------- A. environment ----------------
    print("=== A. Environment ===")
    record("A. Environment", "ENV-01", "Python >= 3.11",
           sys.version_info >= (3, 11), platform.python_version())
    for mod in ("numpy", "yaml", "pythermalcomfort", "fastapi", "uvicorn"):
        try:
            m = importlib.import_module(mod)
            v = getattr(m, "__version__", "?")
            record("A. Environment", f"ENV-{mod}", f"dependency {mod}", True, str(v))
        except Exception as e:  # noqa: BLE001
            record("A. Environment", f"ENV-{mod}", f"dependency {mod}", False, str(e))
    try:
        from overheatlens.worker import find_energyplus  # noqa: E402

        bins = find_energyplus()
        record("A. Environment", "ENV-EPLUS", "official EnergyPlus binary",
               bool(bins), bins[0]["version"] if bins else "not found")
    except Exception as e:  # noqa: BLE001
        bins = []
        record("A. Environment", "ENV-EPLUS", "official EnergyPlus binary", False, str(e))
    has_node = shutil.which("npm") is not None
    record("A. Environment", "ENV-NODE", "Node/npm for the web app", has_node,
           shutil.which("node") or "not found")

    # ---------------- B/C/D. suites ----------------
    run_suite("B. Core suite", [sys.executable, "-m", "pytest",
              "packages/overheatlens-core/tests", "-q"], REPO, "SUITE-CORE")
    run_suite("C. API suite", [sys.executable, "-m", "pytest",
              "apps/api/tests", "-q"], REPO, "SUITE-API")
    if not SKIP_WEB and has_node:
        run_suite("D. Web build", ["npm", "run", "build"],
                  REPO / "apps" / "web", "SUITE-WEB-BUILD")
        run_suite("D. Web tests", ["npx", "vitest", "run", "tests"],
                  REPO / "apps" / "web", "SUITE-WEB")
    else:
        record("D. Web build+tests", "SUITE-WEB", "web build + vitest", None,
               "skipped (--skip-web or no Node)")

    # ---------------- E. live walkthrough ----------------
    print("\n=== E. Live application walkthrough ===")
    from fastapi.testclient import TestClient  # noqa: E402

    from apps.api.app.main import REPO_ROOT, app  # noqa: E402

    c = TestClient(app)
    fixture = REPO / "fixtures" / "epw" / "synthetic" / "good_file.epw"
    demo_idf = REPO / "fixtures" / "idf" / "synthetic_dwelling.idf"
    leeds = sorted((REPO / "fixtures" / "idf" / "leeds").glob("*.idf")) \
        if (REPO / "fixtures" / "idf" / "leeds").is_dir() else []

    def get(path: str, **kw):
        return c.get(path, **kw)

    r = get("/api/version")
    record("E. Live", "LIVE-01", "GET /api/version", r.status_code == 200,
           r.json().get("core_version", ""))
    r = get("/api/rule-packs")
    packs = r.json().get("packs", []) if r.status_code == 200 else []
    record("E. Live", "LIVE-02", "GET /api/rule-packs — 4 packs, all source-verified",
           r.status_code == 200 and len(packs) == 4
           and all(p["source_status"] == "source_verified" for p in packs),
           f"{len(packs)} packs")
    r = get("/api/weather")
    n_files = len(r.json().get("files", [])) if r.status_code == 200 else 0
    record("E. Live", "LIVE-03", "GET /api/weather — library + fixtures listed",
           r.status_code == 200 and n_files >= 8, f"{n_files} files")
    r = get("/api/weather/check", params={"path": str(fixture)})
    ok = r.status_code == 200 and r.json()["status"] == "PASS" and r.json()["n_rows"] == 8760
    record("E. Live", "LIVE-04", "GET /api/weather/check — synthetic fixture PASS/8760",
           ok, r.json().get("status") if r.status_code == 200 else r.text[:80])
    r = get("/api/weather/series", params={"path": str(fixture)})
    s = r.json() if r.status_code == 200 else {}
    record("E. Live", "LIVE-05", "GET /api/weather/series — 8760 h, 12×24 matrix, "
           "fingerprint + degree-days",
           len(s.get("dry_bulb", [])) == 8760 and len(s.get("month_hour_matrix", [])) == 12
           and len(s.get("hdd15_5", [])) == 12 and len(s.get("monthly_rh", [])) == 12,
           "all calendar arrays present" if s else "no data")

    # uploads (round-trip + rejection)
    r = c.post("/api/weather/upload", params={"name": "validation_upload.epw"},
               content=fixture.read_bytes())
    up_ok = r.status_code == 200
    up_path = r.json().get("path") if up_ok else None
    record("E. Live", "LIVE-06", "POST /api/weather/upload — valid EPW accepted + checked",
           up_ok, r.json().get("report", {}).get("status") if up_ok else r.text[:80])
    r = c.post("/api/weather/upload", params={"name": "bad.epw"}, content=b"garbage")
    record("E. Live", "LIVE-07", "POST /api/weather/upload — garbage rejected",
           r.status_code in (400, 413, 422), f"HTTP {r.status_code}")
    r = c.post("/api/models/upload", params={"name": "validation_model.idf"},
               content=demo_idf.read_bytes())
    record("E. Live", "LIVE-08", "POST /api/models/upload — valid IDF accepted",
           r.status_code == 200, r.json().get("readiness", {}).get("status")
           if r.status_code == 200 else r.text[:80])
    r = c.post("/api/models/upload", params={"name": "bad.idf"}, content=b"garbage")
    record("E. Live", "LIVE-09", "POST /api/models/upload — garbage rejected",
           r.status_code in (400, 413, 422), f"HTTP {r.status_code}")

    r = get("/api/models")
    models = r.json().get("models", []) if r.status_code == 200 else []
    leeds_models = [m for m in models if m.get("city") == "Leeds"]
    record("E. Live", "LIVE-10", "GET /api/models — Leeds templates listed",
           r.status_code == 200 and len(leeds_models) >= 3,
           f"{len(models)} models, {len(leeds_models)} Leeds")

    # security guards
    r = get("/api/weather/check", params={"path": str(REPO / "README.md")})
    record("E. Live", "LIVE-11", "security: non-EPW path rejected",
           r.status_code in (400, 403, 404), f"HTTP {r.status_code}")
    r = c.post("/api/analyze", params={"weather_path": str(REPO / "README.md")})
    record("E. Live", "LIVE-12", "security: analyze model/weather path guard",
           r.status_code in (400, 403, 404), f"HTTP {r.status_code}")

    # analyses (EnergyPlus-dependent; auto-skip when unavailable)
    if bins and not SKIP_HEAVY:
        weather = up_path or str(fixture)
        targets = [("demo dwelling", demo_idf)] + [(p.stem, p) for p in leeds]
        all_ok = True
        details = []
        for label, idf in targets:
            r = c.post("/api/analyze", params={
                "weather_path": weather, "model_path": str(idf),
                "pack_id": "uk_tm59_2017"})
            ok = r.status_code == 200 and r.json()["run"]["status"] == "complete"
            all_ok &= ok
            details.append(f"{label}:{'ok' if ok else r.text[:60]}")
        record("E. Live", "LIVE-13", "POST /api/analyze — demo + every Leeds archetype "
               "runs 0-fatal in EnergyPlus", all_ok, ", ".join(details))

        leeds_pick = (leeds[0] if leeds else demo_idf)
        r = c.post("/api/comfort/run", params={
            "weather_path": weather, "model_path": str(leeds_pick),
            "pack_id": "uk_tm59_2017"})
        body = r.json() if r.status_code == 200 else {}
        zones = body.get("zones", [])
        record("E. Live", "LIVE-14", "POST /api/comfort/run — comfort from the "
               "simulation with stated assumptions",
               r.status_code == 200 and bool(zones)
               and "assumptions" in body,
               f"{len(zones)} zones")
        r = get("/api/report", params={
            "weather_path": weather, "model_path": str(leeds_pick),
            "pack_id": "uk_tm59_2017"})
        html = r.text if r.status_code == 200 else ""
        record("E. Live", "LIVE-15", "GET /api/report — self-contained HTML with "
               "disclaimer", r.status_code == 200 and html.startswith("<!DOCTYPE")
               and "not a certified compliance certificate" in html,
               f"{len(html)} bytes")
    else:
        for cid in ("LIVE-13", "LIVE-14", "LIVE-15"):
            record("E. Live", cid, "(EnergyPlus-dependent live check)", None,
                   "skipped — no EnergyPlus binary or --skip-heavy")

    r = get("/api/compare", params={"paths": f"{fixture},{fixture}"})
    record("E. Live", "LIVE-16", "GET /api/compare — two-file comparison",
           r.status_code == 200 and len(r.json().get("files", [])) == 2,
           f"HTTP {r.status_code}")
    r = get("/api/validation")
    record("E. Live", "LIVE-17", "GET /api/validation — live matrix served",
           r.status_code == 200 and len(r.json().get("rows", [])) >= 50,
           f"{len(r.json().get('rows', []))} rows" if r.status_code == 200 else "")
    r = get("/api/runs")
    record("E. Live", "LIVE-18", "GET /api/runs — session analyses recorded",
           r.status_code == 200 and len(r.json().get("runs", [])) >= 1,
           f"{len(r.json().get('runs', []))} runs")
    r = get("/")
    record("E. Live", "LIVE-19", "web interface served (built dist)",
           r.status_code == 200 and b"OverheatLens" in r.content, "")

    # ---------------- report ----------------
    n_pass = sum(1 for r in RESULTS if r["status"] == "PASS")
    n_fail = sum(1 for r in RESULTS if r["status"] == "FAIL")
    n_skip = sum(1 for r in RESULTS if r["status"] == "SKIP")
    finished = datetime.now(timezone.utc)
    lines = [
        "# Full Application Validation Report",
        "",
        f"**Run finished:** {finished:%Y-%m-%d %H:%M UTC}  ",
        f"**Result:** {n_pass} PASS · {n_fail} FAIL · {n_skip} SKIP",
        "",
        "| ID | Check | Status | Detail |",
        "|---|---|---|---|",
    ]
    section = ""
    for r in RESULTS:
        if r["section"] != section:
            section = r["section"]
            lines += ["", f"## {section}", ""]
        lines.append(f"| {r['id']} | {r['desc']} | {r['status']} | {r['detail']} |")
    lines += ["", "---",
              "",
              "OverheatLens is research and decision-support software, not a certified",
              "compliance certificate. This report is machine-generated by",
              "`scripts/validate_app.py` — rerun it any time; it never edits results.", ""]
    out = REPO / "docs" / "validation" / "FULL_APP_VALIDATION_REPORT.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")

    print(f"\n{'=' * 60}")
    print(f"RESULT: {n_pass} PASS, {n_fail} FAIL, {n_skip} SKIP "
          f"-> {out.relative_to(REPO)}")
    print(f"{'=' * 60}")
    return 1 if n_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
