"""Weather metrics computed from parsed EPW data.

Every function here returns plain values or arrays that feed both the UI and reports;
they are the tested data-transform layer required by Rule 10 (charts must never embed
metrics only in their configuration).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .parser import SENTINELS, EpwFile


def _clean(series: np.ndarray, sentinel: float) -> np.ndarray:
    s = series.astype(np.float64, copy=True)
    s[np.isclose(s, sentinel)] = np.nan
    return s


@dataclass
class WeatherSummary:
    annual_mean_dry_bulb: float
    hottest_hour: float
    hottest_hour_row: int
    coldest_hour: float
    daily_max_mean_of_annual: float
    exceedance_hours_26c: int
    exceedance_hours_28c: int
    degree_hours_26c: float
    night_min_mean_jja: float | None

    def to_dict(self) -> dict:
        return self.__dict__.copy()


def exceedance_hours(temp: np.ndarray, threshold: float) -> int:
    """Hours where a cleaned temperature series is >= threshold.

    Metamorphic contract (plan §27.3): adding +K (K>0) to every value must never
    reduce this count; tested property in the suite.
    """
    t = _clean(temp, SENTINELS[6])
    return int(np.nansum(t >= threshold))


def degree_hours(temp: np.ndarray, threshold: float) -> float:
    """Degree-hours above threshold (Kh), treating missing values as 0 exceedance."""
    t = _clean(temp, SENTINELS[6])
    exc = np.where(np.isnan(t), 0.0, t - threshold)
    return float(np.sum(np.clip(exc, 0.0, None)))


def weather_summary(epw: EpwFile) -> WeatherSummary:
    db = _clean(epw.dry_bulb, SENTINELS[6])
    if np.isnan(db).all():
        raise ValueError(
            "no valid dry-bulb data in this file (all values missing or sentinel); "
            "weather summary is an explicit non-result")
    hottest_row = int(np.nanargmax(db))
    daily_max = np.nanmax(db.reshape(-1, 24), axis=1)
    jja = np.isin(epw.data.month, (6, 7, 8))
    night = np.isin(epw.data.hour, (22, 23, 24, 1, 2, 3, 4, 5, 6))
    jja_night = jja & night
    return WeatherSummary(
        annual_mean_dry_bulb=round(float(np.nanmean(db)), 3),
        hottest_hour=round(float(db[hottest_row]), 2),
        hottest_hour_row=hottest_row + 1,
        coldest_hour=round(float(np.nanmin(db)), 2),
        daily_max_mean_of_annual=round(float(np.nanmean(daily_max)), 3),
        exceedance_hours_26c=exceedance_hours(epw.dry_bulb, 26.0),
        exceedance_hours_28c=exceedance_hours(epw.dry_bulb, 28.0),
        degree_hours_26c=round(degree_hours(epw.dry_bulb, 26.0), 2),
        night_min_mean_jja=(
            round(float(np.nanmean(db[jja_night])), 3) if jja_night.any() else None
        ),
    )


def monthly_mean_dry_bulb(epw: EpwFile) -> list[dict]:
    db = _clean(epw.dry_bulb, SENTINELS[6])
    out = []
    for m in range(1, 13):
        mask = epw.data.month == m
        out.append({
            "month": m,
            "mean": round(float(np.nanmean(db[mask])), 3) if mask.any() else None,
            "max": round(float(np.nanmax(db[mask])), 2) if mask.any() else None,
            "min": round(float(np.nanmin(db[mask])), 2) if mask.any() else None,
        })
    return out
