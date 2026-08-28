"""EnergyPlus worker — runs the official binary in isolation and harvests results.

Rules enforced here (governing plan §12, RULE 5, RULE 6, ADR-0004):
* Only an official EnergyPlus binary is used; the exact version is probed with
  `--version` and recorded in every manifest.
* Every job runs in a unique ephemeral directory, without a shell, with a timeout
  and an input-size guard.
* eplusout.err is parsed into fatal/severe/warning/recurring groups; a fatal or
  severe error makes the run FAILED and no results may be evaluated from it.
* Operative temperature is a DERIVED metric: Top = 0.5*(MAT + MRT) — the standard
  low-air-speed approximation — and is labelled as such wherever it appears.
"""

from __future__ import annotations

import datetime as _dt
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..idf.inspection import parse_idf
from ..provenance.hashing import sha256_file

MAX_INPUT_BYTES = 50 * 1024 * 1024  # 50 MB guard per plan §12.3


class EnergyPlusError(RuntimeError):
    """Raised when no official EnergyPlus binary can be located."""


def find_energyplus() -> list[dict[str, str]]:
    """Probe well-known install locations and return usable binaries with versions."""
    candidates: list[Path] = []
    for base in Path("/Applications").glob("EnergyPlus*"):
        candidates.append(base / "energyplus")
    for base in Path("/usr/local").glob("EnergyPlus*"):
        candidates.append(base / "bin" / "energyplus")
    for base in Path("C:/Program Files").glob("EnergyPlus*"):
        candidates.append(base / "energyplus.exe")
    for base in Path("C:/EnergyPlus*").glob("*"):
        candidates.append(base / "energyplus.exe")
    found: list[dict[str, str]] = []
    for exe in candidates:
        if exe.is_file() and os.access(exe, os.X_OK):
            try:
                out = subprocess.run([str(exe), "--version"], capture_output=True,
                                     text=True, timeout=30, check=False)
                m = re.search(r"Version ([0-9.]+)", out.stdout + out.stderr)
                version = m.group(1) if m else "unknown"
            except (OSError, subprocess.TimeoutExpired):
                continue
            found.append({"binary": str(exe), "version": version})
    # newest version first
    found.sort(key=lambda d: d["version"], reverse=True)
    return found


@dataclass
class ErrSummary:
    fatal: list[str] = field(default_factory=list)
    severe: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    recurring: list[str] = field(default_factory=list)

    @property
    def is_usable(self) -> bool:
        return not self.fatal and not self.severe

    def to_dict(self) -> dict[str, Any]:
        return {"fatal": self.fatal, "severe": self.severe,
                "warning_count": len(self.warnings),
                "recurring_warning_count": len(self.recurring),
                "first_warnings": self.warnings[:10], "is_usable": self.is_usable}


@dataclass
class RunResult:
    run_id: str
    status: str                    # "complete" | "failed"
    energyplus_binary: str
    energyplus_version: str
    out_dir: str
    err: ErrSummary
    csv_path: Path | None
    manifest: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id, "status": self.status,
            "energyplus_version": self.energyplus_version,
            "out_dir": self.out_dir, "err": self.err.to_dict(),
            "manifest": self.manifest,
        }


def parse_err(err_path: Path) -> ErrSummary:
    """Group eplusout.err messages by severity (plan §12.5)."""
    s = ErrSummary()
    if not err_path.exists():
        s.fatal.append("eplusout.err not produced — the run did not execute")
        return s
    text = err_path.read_text(errors="replace")
    current = None
    for line in text.splitlines():
        m = re.match(r"\*\*\s+(Fatal|Severe|Warning)\s+\*\*\s*(.*)", line)
        if m:
            level, msg = m.group(1).lower(), m.group(2).strip()
            current = level
            {"fatal": s.fatal, "severe": s.severe, "warning": s.warnings}[level] \
                .append(msg)
        elif line.startswith("   ~~~") and current == "warning":
            s.recurring.append(line.strip())
    if "*** EnergyPlus Completed Successfully" not in text and not s.fatal:
        s.fatal.append("run did not complete successfully (no success marker)")
    return s


def run_energyplus(
    idf_path: str | Path,
    epw_path: str | Path,
    *,
    work_root: str | Path | None = None,
    timeout_s: int = 600,
    keep_dir: bool = False,
    binary: str | None = None,
) -> RunResult:
    """Run one isolated EnergyPlus job: idf + epw -> eplusout.csv (+ manifest).

    Files are copied into a unique ephemeral directory (no in-place mutation), the
    process is launched without a shell and bounded by ``timeout_s``.
    """
    idf_path, epw_path = Path(idf_path), Path(epw_path)
    for p in (idf_path, epw_path):
        if not p.is_file():
            raise FileNotFoundError(f"input not found: {p}")
        if p.stat().st_size > MAX_INPUT_BYTES:
            raise ValueError(f"input exceeds the size guard: {p}")

    bins = find_energyplus()
    if not bins:
        raise EnergyPlusError(
            "No official EnergyPlus binary found. Install EnergyPlus from "
            "energyplus.net and re-run.")
    chosen = next((b for b in bins if b["binary"] == binary), bins[0])

    run_id = uuid.uuid4().hex[:12]
    root = Path(work_root) if work_root else Path(tempfile.gettempdir())
    out_dir = Path(tempfile.mkdtemp(prefix=f"ohx_{run_id}_", dir=root))
    shutil.copy2(idf_path, out_dir / "in.idf")
    shutil.copy2(epw_path, out_dir / "in.epw")

    started = _dt.datetime.now(_dt.timezone.utc)
    try:
        proc = subprocess.run(
            [chosen["binary"], "--readvars", "--weather", "in.epw",
             "--output-directory", ".", "in.idf"],
            cwd=out_dir, capture_output=True, text=True, timeout=timeout_s,
            check=False)
        stdout_tail = "\n".join((proc.stdout or "").splitlines()[-15:])
    except subprocess.TimeoutExpired as e:
        err = ErrSummary()
        err.fatal.append(f"run timed out after {timeout_s}s")
        manifest = _manifest(run_id, chosen["version"], chosen["binary"],
                             idf_path, epw_path, started, status="failed",
                             notes=[f"timeout after {timeout_s}s"])
        _write_manifest(out_dir, manifest)
        return RunResult(run_id, "failed", chosen["binary"], chosen["version"],
                         str(out_dir), err, None, manifest)

    err = parse_err(out_dir / "eplusout.err")
    if proc.returncode != 0 and not err.fatal:
        err.fatal.append(f"energyplus exited with code {proc.returncode}: "
                         f"{stdout_tail[-300:]}")

    csv_path = out_dir / "eplusout.csv"
    status = "complete" if err.is_usable and csv_path.exists() else "failed"
    manifest = _manifest(run_id, chosen["version"], chosen["binary"], idf_path,
                         epw_path, started, status=status, notes=[stdout_tail])
    _write_manifest(out_dir, manifest)

    if not keep_dir and status == "complete" and not os.environ.get("OHX_KEEP_RUNS"):
        # keep only manifest + csv + err unless told otherwise (plan §12.3 cleanup)
        for item in out_dir.iterdir():
            if item.name not in ("run_manifest.json", "eplusout.csv", "eplusout.err"):
                try:
                    item.unlink()
                except OSError:
                    pass

    return RunResult(run_id, status, chosen["binary"], chosen["version"],
                     str(out_dir), err,
                     csv_path if csv_path.exists() else None, manifest)


def _manifest(run_id, ep_version, binary, idf_path, epw_path, started, status,
              notes) -> dict[str, Any]:
    from .. import CORE_VERSION

    return {
        "run_id": run_id,
        "core_version": CORE_VERSION,
        "energyplus_version": ep_version,
        "energyplus_binary": binary,
        "idf_sha256": sha256_file(idf_path),
        "epw_sha256": sha256_file(epw_path),
        "status": status,
        "created_utc": started.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "notes": notes[-1] if notes else "",
    }


def _write_manifest(out_dir: Path, manifest: dict) -> None:
    import json

    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2))


def harvest_hourly(csv_path: str | Path) -> dict[str, dict[str, list[float]]]:
    """Parse eplusout.csv (ReadVarsESO output) into per-zone hourly series.

    Returns ``{zone_key: {"mat": [...], "mrt": [...], "top": [...]}}`` where
    ``top`` is the DERIVED operative temperature 0.5*(MAT+MRT) (low air speed).
    Column naming follows ReadVarsESO: 'Environment:...,ZONE NAME:Zone Mean Air
    Temperature [C](TimeStep)'.
    """
    import csv as _csv

    csv_path = Path(csv_path)
    lines = csv_path.read_text(errors="replace").splitlines()
    if len(lines) < 2:
        raise ValueError("eplusout.csv has no data rows")
    header = next(_csv.reader([lines[0]]))
    # data rows: first field is a date string, then values
    data = [next(_csv.reader([ln])) for ln in lines[1:] if ln.strip()]
    if not data:
        raise ValueError("eplusout.csv has no data rows")

    zones: dict[str, dict[str, list[float]]] = {}
    for col, name in enumerate(header):
        if col == 0:
            continue
        name = name.strip()
        mat = ("Zone Mean Air Temperature" in name)
        mrt = ("Zone Mean Radiant Temperature" in name)
        if not (mat or mrt):
            continue
        zone = name.split(":Zone Mean")[0].strip().lower()
        key = "mat" if mat else "mrt"
        zones.setdefault(zone, {"mat": [], "mrt": []})
        vals = zones[zone][key]
        for row in data:
            try:
                vals.append(float(row[col]))
            except (IndexError, ValueError):
                vals.append(float("nan"))

    out: dict[str, dict[str, list[float]]] = {}
    for zone, series in zones.items():
        if not series["mat"]:
            continue
        mat = np.asarray(series["mat"], dtype=float)
        mrt = (np.asarray(series["mrt"], dtype=float) if series["mrt"] else mat)
        out[zone] = {
            "mat": mat.tolist(),
            "mrt": mrt.tolist(),
            "top": (0.5 * (mat + mrt)).tolist(),
        }
    if not out:
        raise ValueError(
            "no zone temperature columns found in eplusout.csv — add Output:Variable "
            "objects for Zone Mean Air Temperature and Zone Mean Radiant Temperature")
    return out


import numpy as np  # noqa: E402  (kept at bottom to keep the module import-light)
