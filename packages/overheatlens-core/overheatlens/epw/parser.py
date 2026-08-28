"""EPW parser.

Implements the official EnergyPlus Weather (EPW) format layout:
8 header lines, then one data row per hour with 35 comma-separated fields.
Field indices follow the EnergyPlus Input Output Reference (0-based here):

    0 year, 1 month, 2 day, 3 hour (1-24), 4 minute, 5 data-source flag,
    6 dry-bulb °C, 7 dew-point °C, 8 RH %, 9 pressure Pa,
    10 ext-horiz-rad, 11 ext-dir-norm-rad, 12 horiz-IR, 13 global-horiz-rad,
    14 dir-norm-rad, 15 diffuse-horiz-rad, 16-18 illuminances, 19 zenith luminance,
    20 wind direction °, 21 wind speed m/s, 22 total sky cover, 23 opaque sky cover,
    24 visibility, 25 ceiling height, 26 present-weather obs, 27 weather codes,
    28 precipitable water, 29 aerosol optical depth, 30 snow depth,
    31 days-since-snow, 32 albedo, 33 rain, 34 rain quantity.

Missing-value sentinels per the format (e.g. 999.9 °C, 999 %, 999999 Pa) are kept
in the raw arrays and reported by the checker; metrics treat them explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

FIELDS = 35
HEADER_LINES = 8

# Official EPW missing sentinels for the fields this release interprets.
SENTINELS = {
    6: 999.9,   # dry bulb
    7: 999.9,   # dew point
    8: 999.0,   # relative humidity
    9: 999999.0,  # pressure
    20: 999.0,  # wind direction
    21: 999.0,  # wind speed
    13: 9999.0,  # global horizontal radiation
}

FIELD_NAMES = {
    0: "year", 1: "month", 2: "day", 3: "hour", 4: "minute", 5: "source_flag",
    6: "dry_bulb", 7: "dew_point", 8: "relative_humidity", 9: "atmospheric_pressure",
    10: "external_horizontal_radiation", 11: "external_direct_normal_radiation",
    12: "horizontal_infrared_radiation", 13: "global_horizontal_radiation",
    14: "direct_normal_radiation", 15: "diffuse_horizontal_radiation",
    20: "wind_direction", 21: "wind_speed",
}


class EpwParseError(ValueError):
    """Raised when a file is not a parseable EPW at the structural level."""


@dataclass
class EpwHeader:
    location_line: list[str]
    title: str
    city: str
    country: str
    latitude: float
    longitude: float
    timezone: float
    elevation: float
    data_periods: list[list[str]]
    raw_lines: list[str] = field(default_factory=list)

    @property
    def wmo_id(self) -> str:
        return self.location_line[5] if len(self.location_line) > 5 else ""


@dataclass
class EpwData:
    """Parsed EPW arrays. Times are hour-ending convention as stored (1..24)."""

    year: np.ndarray
    month: np.ndarray
    day: np.ndarray
    hour: np.ndarray
    minute: np.ndarray
    source_flag: np.ndarray
    values: np.ndarray  # shape (rows, 35) float64, sentinels preserved


@dataclass
class EpwFile:
    path: Path
    header: EpwHeader
    data: EpwData
    sha256: str
    n_rows: int

    # Convenience accessors (raw values, sentinels preserved)
    @property
    def dry_bulb(self) -> np.ndarray:
        return self.data.values[:, 6]

    @property
    def dew_point(self) -> np.ndarray:
        return self.data.values[:, 7]

    @property
    def relative_humidity(self) -> np.ndarray:
        return self.data.values[:, 8]

    @property
    def pressure(self) -> np.ndarray:
        return self.data.values[:, 9]

    @property
    def wind_speed(self) -> np.ndarray:
        return self.data.values[:, 21]

    @property
    def global_horizontal_radiation(self) -> np.ndarray:
        return self.data.values[:, 13]

    def valid_dry_bulb(self) -> np.ndarray:
        """Dry-bulb series with missing sentinels replaced by NaN."""
        db = self.dry_bulb.astype(np.float64, copy=True)
        db[db == SENTINELS[6]] = np.nan
        return db


def parse_epw(path: str | Path) -> EpwFile:
    """Parse an EPW file, raising :class:`EpwParseError` on structural faults."""
    path = Path(path)
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as e:
        raise EpwParseError(f"Cannot read file: {e}") from e

    if len(lines) < HEADER_LINES + 1:
        raise EpwParseError(
            f"Too few lines for an EPW ({len(lines)}); expected 8 header lines plus data."
        )

    if not lines[0].startswith("LOCATION,"):
        raise EpwParseError("First line must start with 'LOCATION,' — not a valid EPW header.")

    loc = lines[0].split(",")
    # LOCATION,title,state,country,data_source,wmo,lat,lon,tz,elevation
    if len(loc) < 10:
        raise EpwParseError(f"LOCATION line has {len(loc)} fields; expected >= 10.")

    def _f(s: str, what: str) -> float:
        try:
            return float(s)
        except ValueError as e:
            raise EpwParseError(f"LOCATION field {what} is not numeric: {s!r}") from e

    header = EpwHeader(
        location_line=loc,
        title=loc[1],
        city=loc[1],
        country=loc[3],
        latitude=_f(loc[6], "latitude"),
        longitude=_f(loc[7], "longitude"),
        timezone=_f(loc[8], "timezone"),
        elevation=_f(loc[9], "elevation"),
        data_periods=[ln.split(",") for ln in lines if ln.startswith("DATA PERIODS")],
        raw_lines=lines[:HEADER_LINES],
    )

    data_lines = lines[HEADER_LINES:]
    n = len(data_lines)
    values = np.full((n, FIELDS), np.nan)
    year = np.zeros(n, dtype=np.int32)
    month = np.zeros(n, dtype=np.int32)
    day = np.zeros(n, dtype=np.int32)
    hour = np.zeros(n, dtype=np.int32)
    minute = np.zeros(n, dtype=np.int32)
    flag = np.zeros(n, dtype="U8")

    for i, ln in enumerate(data_lines):
        parts = ln.split(",")
        if len(parts) < FIELDS:
            raise EpwParseError(
                f"Data row {i + 1} (line {HEADER_LINES + i + 1}) has {len(parts)} fields; "
                f"expected {FIELDS}."
            )
        try:
            year[i] = int(parts[0])
            month[i] = int(parts[1])
            day[i] = int(parts[2])
            hour[i] = int(parts[3])
            minute[i] = int(parts[4])
            flag[i] = parts[5]
            # Column 5 (data-source flag) is non-numeric in the EPW layout.
            for j in range(FIELDS):
                if j == 5:
                    continue
                values[i, j] = float(parts[j])
        except ValueError as e:
            raise EpwParseError(f"Non-numeric value in data row {i + 1}: {e}") from e

    if hour.min() < 1 or hour.max() > 24:
        raise EpwParseError("Hour field must be 1..24 (hour-ending).")

    data = EpwData(
        year=year, month=month, day=day, hour=hour, minute=minute,
        source_flag=flag, values=values,
    )

    from ..provenance.hashing import sha256_file

    return EpwFile(path=path, header=header, data=data, sha256=sha256_file(path), n_rows=n)
