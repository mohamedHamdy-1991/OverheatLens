"""EPW quality checks (Phase 2 subset of plan §10.1).

Each check returns structured issues with severity, so callers can classify a file as
PASS / PASS_WITH_WARNINGS / FAIL. Checks never mutate data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .parser import SENTINELS, EpwFile

# Physical plausibility bounds (EPW format + meteorological practice; used for QC only).
RANGES = {
    6: ("dry_bulb", -70.0, 70.0),
    7: ("dew_point", -70.0, 70.0),
    8: ("relative_humidity", 0.0, 100.0),
    9: ("atmospheric_pressure", 31000.0, 120000.0),
    21: ("wind_speed", 0.0, 40.0),
    13: ("global_horizontal_radiation", 0.0, 1600.0),
}


@dataclass
class Issue:
    code: str
    severity: str  # "error" | "warning" | "info"
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class CheckReport:
    path: str
    sha256: str
    issues: list[Issue] = field(default_factory=list)
    n_rows: int = 0

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def status(self) -> str:
        if self.errors:
            return "FAIL"
        if self.warnings:
            return "PASS_WITH_WARNINGS"
        return "PASS"

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "sha256": self.sha256,
            "n_rows": self.n_rows,
            "status": self.status,
            "issues": [
                {"code": i.code, "severity": i.severity, "message": i.message,
                 "details": i.details}
                for i in self.issues
            ],
        }


def check_epw(epw: EpwFile) -> CheckReport:
    """Run the Phase-2 QC battery over a parsed EPW."""
    report = CheckReport(path=str(epw.path), sha256=epw.sha256, n_rows=epw.n_rows)
    v = epw.data.values
    rows = epw.n_rows
    issues = report.issues

    # --- Structure -------------------------------------------------------
    expected_rows = 8784 if (epw.data.month == 2).sum() > 28 else 8760
    if rows not in (8760, 8784):
        issues.append(Issue(
            "ROW_COUNT", "error",
            f"Data row count is {rows}; expected 8760 (or 8784 for a leap year).",
            {"n_rows": rows},
        ))
    elif rows != expected_rows and rows == 8784:
        issues.append(Issue(
            "LEAP_YEAR", "info", "File contains 8784 rows (leap year).", {"n_rows": rows},
        ))

    # Timestamp continuity: 8760/8784 consecutive hours starting Jan 1, hour 1.
    stamp = (epw.data.month * 100000 + epw.data.day * 1000 + epw.data.hour).astype(np.int64)
    is_leap = rows == 8784
    import calendar as _cal

    expected_stamps: list[int] = []
    year_len = 366 if is_leap else 365
    leap_year = 2004 if is_leap else 2001
    for mm in range(1, 13):
        ndays = _cal.monthrange(leap_year, mm)[1]
        for dd in range(1, ndays + 1):
            for hh in range(1, 25):
                expected_stamps.append(mm * 100000 + dd * 1000 + hh)
    expected_arr = np.array(expected_stamps[: min(rows, year_len * 24)])
    if rows == year_len * 24:
        if not np.array_equal(stamp, expected_arr):
            gap_idx = np.nonzero(stamp != expected_arr)[0]
            first = int(gap_idx[0]) if gap_idx.size else -1
            issues.append(Issue(
                "TIMESTAMP_SEQUENCE", "error",
                "Timestamps are not a continuous hourly sequence.",
                {"first_mismatch_row": first + 1, "n_mismatched": int(gap_idx.size)},
            ))
    if (epw.data.hour == 0).any() or (epw.data.hour > 24).any():
        issues.append(Issue(
            "HOUR_FIELD", "error", "Hour field outside 1..24 (EPW hour-ending convention).",
        ))

    # Duplicate stamps
    unique = np.unique(stamp)
    if unique.size != rows:
        issues.append(Issue(
            "DUPLICATE_HOURS", "error",
            f"{rows - unique.size} duplicated timestamp(s) detected.",
            {"n_duplicates": int(rows - unique.size)},
        ))

    # --- Field-level checks ----------------------------------------------
    for idx, (name, lo, hi) in RANGES.items():
        col = v[:, idx]
        sentinel_mask = np.isclose(col, SENTINELS.get(idx, -99999.0))
        if sentinel_mask.any():
            issues.append(Issue(
                "MISSING_SENTINEL", "warning",
                f"{name}: {int(sentinel_mask.sum())} missing-value sentinel(s) "
                f"({SENTINELS.get(idx)}) present.",
                {"field": name, "count": int(sentinel_mask.sum())},
            ))
        out = (~sentinel_mask) & ((col < lo) | (col > hi))
        if out.any():
            first = int(np.nonzero(out)[0][0])
            issues.append(Issue(
                "OUT_OF_RANGE", "error",
                f"{name}: {int(out.sum())} value(s) outside plausible range [{lo}, {hi}] "
                f"(first at row {first + 1}: {col[first]:g}).",
                {"field": name, "count": int(out.sum()), "first_row": first + 1,
                 "observed_first": float(col[first])},
            ))

    # Physics: dew point cannot exceed dry bulb (allow small numerical tolerance).
    db, dp = v[:, 6], v[:, 7]
    both = (~np.isclose(db, SENTINELS[6])) & (~np.isclose(dp, SENTINELS[7]))
    viol = both & (dp > db + 0.05)
    if viol.any():
        first = int(np.nonzero(viol)[0][0])
        issues.append(Issue(
            "DEWPOINT_VIOLATION", "error",
            f"Dew point exceeds dry bulb at {int(viol.sum())} row(s) "
            f"(first at row {first + 1}).",
            {"count": int(viol.sum()), "first_row": first + 1},
        ))

    # Temporal plausibility of dry bulb.
    # Thresholds calibrated on the synthetic fixture family (2026-08-28):
    # healthy files show max |dT/dt| <= 5.2 K/h and constant runs <= 5 h;
    # the planted spike fixture peaks at 16.2 K/h and the stuck fixture runs 11 h.
    dbv = epw.valid_dry_bulb()
    if dbv.size >= 2:
        dd = np.abs(np.diff(dbv))
        dd = dd[~np.isnan(dd)]
        if dd.size:
            max_rate = float(dd.max())
            if max_rate > 15.0:
                issues.append(Issue(
                    "DISCONTINUITY", "error",
                    f"Dry-bulb changes by up to {max_rate:.1f} K between consecutive "
                    "hours — physically implausible step.",
                    {"field": "dry_bulb", "max_rate_k_per_hour": round(max_rate, 2)},
                ))
            elif max_rate > 8.0:
                issues.append(Issue(
                    "DISCONTINUITY", "warning",
                    f"Dry-bulb changes by up to {max_rate:.1f} K between consecutive "
                    "hours — unusually rapid; check for sensor spikes.",
                    {"field": "dry_bulb", "max_rate_k_per_hour": round(max_rate, 2)},
                ))

        if not np.isnan(dbv).all():
            same = np.r_[False, dbv[1:] == dbv[:-1]]
            run_len = np.bincount(np.cumsum(~same))
            longest = int(run_len[1:].max()) if run_len.size > 1 else int(run_len.max())
            if longest >= 10:
                issues.append(Issue(
                    "STUCK_SENSOR", "warning",
                    f"Dry-bulb temperature repeats the same value for {longest} "
                    "consecutive hours — possible stuck sensor.",
                    {"field": "dry_bulb", "longest_run": longest},
                ))

    return report
