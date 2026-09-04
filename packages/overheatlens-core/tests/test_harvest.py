"""Harvest regression tests (no EnergyPlus needed — synthetic CSV fixtures).

Backs VALIDATION_MATRIX row VAL-XSIM-05: the harvester must never merge
distinct thermal zones (DEEP keys look like ``00GROUNDFLOOR:LOUNGE``) and must
never stack Monthly/RunPeriod siblings onto the Hourly series.
"""

from __future__ import annotations

import pytest

from overheatlens.worker import harvest_hourly


def _stacked_csv(tmp_path):
    """Mimics a DEEP-style eplusout.csv: colon-bearing zone keys (level:room)
    with Hourly + Monthly + RunPeriod siblings per variable."""
    hours = [f"01/01  {h:02d}:00:00" for h in ([*range(1, 25)] * 2)][:48]
    cols = []
    for zone in ("00GROUNDFLOOR:LOUNGE", "00GROUNDFLOOR:KITCHEN"):
        for var in ("Zone Mean Air Temperature", "Zone Mean Radiant Temperature"):
            for freq in ("Hourly", "Monthly", "RunPeriod"):
                cols.append(f"{zone}:{var} [C]({freq}:ON)")
    lines = ["Date/Time," + ",".join(cols)]
    for i in range(48):
        # hourly values drift so stacking would be detectable; others empty
        row = [hours[i]]
        for c in cols:
            if "(Hourly:" in c:
                row.append(f"{20.0 + (i % 24) * 0.1:.2f}")
            else:
                row.append("")
        lines.append(",".join(row))
    p = tmp_path / "eplusout.csv"
    p.write_text("\n".join(lines))
    return p


def test_harvest_never_merges_zones_or_frequencies(tmp_path):
    """Colon-bearing keys stay distinct zones; only (Hourly) columns harvested."""
    zones = harvest_hourly(_stacked_csv(tmp_path))
    assert set(zones) == {"00GROUNDFLOOR:LOUNGE", "00GROUNDFLOOR:KITCHEN"}
    for series in zones.values():
        assert len(series["top"]) == 48
        assert len(series["mat"]) == 48
        assert len(series["mrt"]) == 48


def test_harvest_refuses_duplicate_hourly_columns(tmp_path):
    p = tmp_path / "eplusout.csv"
    p.write_text(
        "Date/Time,ZONE A:Zone Mean Air Temperature [C](Hourly),"
        "ZONE A:Zone Mean Air Temperature [C](Hourly:ON)\n"
        "01/01  01:00:00,21.0,21.5\n")
    with pytest.raises(ValueError, match="duplicate hourly column"):
        harvest_hourly(p)


def _mtr_fixture(tmp_path):
    """Raw eplusout.mtr: dictionary + monthly/runperiod records (J -> kWh)."""
    lines = [
        "1,5,Environment Site Outdoor Air Drybulb Temperature [C] !Hourly",
        "90,9,Electricity:Facility [J] !Monthly [Value,Min,Day,Hour,Minute,Max,Day,Hour,Minute]",
        "92,11,Electricity:Facility [J] !RunPeriod [Value,Min,Month,Day,Hour,Minute,Max,Month,Day,Hour,Minute]",
        "93,9,NATURALGAS:Facility [J] !Monthly [Value,Min,Day,Hour,Minute,Max,Day,Hour,Minute]",
        "95,11,NATURALGAS:Facility [J] !RunPeriod [Value,Min,Month,Day,Hour,Minute,Max,Month,Day,Hour,Minute]",
        "End of Data Dictionary",
        "1,12.5",
        "90,3600000", "90,7200000", "90,10800000",
        "93,1800000", "93,900000",
        "92,72000000",
        "95,36000000",
    ]
    f = tmp_path / "eplusout.mtr"
    f.write_text(chr(10).join(lines) + chr(10))
    return f


def test_harvest_meters_annual_monthly(tmp_path):
    """Meter harvest from raw .mtr: runperiod totals + monthly series, J -> kWh."""
    from overheatlens.worker import harvest_meters

    out = harvest_meters(_mtr_fixture(tmp_path))
    assert set(out) == {"Electricity:Facility", "NATURALGAS:Facility"}
    assert out["Electricity:Facility"]["annual_kwh"] == pytest.approx(20.0)
    assert out["NATURALGAS:Facility"]["annual_kwh"] == pytest.approx(10.0)
    assert out["Electricity:Facility"]["monthly_kwh"] == [pytest.approx(v) for v in (1.0, 2.0, 3.0)]
    assert out["NATURALGAS:Facility"]["monthly_kwh"] == [pytest.approx(v) for v in (0.5, 0.25)]


def test_harvest_meters_without_runperiod_leaves_annual_none(tmp_path):
    """No runperiod records -> annual stays None (never estimated)."""
    from overheatlens.worker import harvest_meters

    f = tmp_path / "eplusout.mtr"
    f.write_text("90,9,Electricity:Facility [J] !Monthly [Value]" + chr(10)
                 + "End of Data Dictionary" + chr(10)
                 + "90,36000000" + chr(10))
    out = harvest_meters(f)
    assert out["Electricity:Facility"]["annual_kwh"] is None
    assert out["Electricity:Facility"]["monthly_kwh"] == [pytest.approx(10.0)]
