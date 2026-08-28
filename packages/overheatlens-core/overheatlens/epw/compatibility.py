"""Weather-file compatibility guard (plan §10.3), TM59:2026 requirement machine-verified.

The official TM59:2026 weather requirement (SOURCE_REGISTER S-08, §3):
    "Overheating assessment should be undertaken using the latest version of the DSY1
    file appropriate to the site location for the 2050s, RCP8.5, 50th percentile scenario"
    — files labelled {Zone Reference}_DSY1_2050s_HIGH50_CIBSE_v1.1.

Detection is filename-traceability only: EPW headers carry no DSY/epoch/scenario
metadata. Where the family cannot be traced from the filename, the result is
`unknown` — displayed to users as "weather provenance not machine-verifiable".
Never guess.
"""

from __future__ import annotations

from typing import Any

DSY_TYPES = ("DSY1", "DSY2", "DSY3")
EPOCHS = ("2020s", "2030s", "2050s", "2080s")
PERCENTILES = ("HIGH50", "HIGH10", "HIGH90")  # 50th/10th/90th percentile labels
SCENARIOS = ("HIGH", "MED", "LOW")  # RCP8.5 / RCP4.5 / RCP2.6 tokens in CIBSE labels

MINIMUM_TOKENS = {"DSY1", "2050s", "HIGH50"}


def _detect_dsy(filename: str) -> str | None:
    up = filename.upper()
    return next((d for d in DSY_TYPES if d in up), None)


def _detect_epoch(filename: str) -> str | None:
    """Detect the epoch in either modern ('2050s') or legacy ('2050High50') naming."""
    for e in EPOCHS:
        if e in filename:
            return e
    up = filename.upper()
    import re

    m = re.search(r"(2020|2030|2050|2080)H", up)
    if m:
        return m.group(1) + "s"
    return None


def _detect_percentile(filename: str) -> str | None:
    up = filename.upper()
    return next((p for p in PERCENTILES if p in up), None)


def _is_legacy_naming(filename: str) -> bool:
    """True when the epoch appears in legacy pre-2025-release form ('2050High50')
    rather than the modern '2050s' + release-marker form."""
    import re

    up = filename.upper()
    return bool(re.search(r"(2020|2030|2050|2080)H", up))


def check_tm59_2026_weather(filename: str) -> dict[str, Any]:
    """Classify a CIBSE weather file (by filename traceability) against the TM59:2026
    minimum requirement. Returns a machine-readable compatibility verdict."""
    found_dsy = _detect_dsy(filename)
    found_epoch = _detect_epoch(filename)
    found_pct = _detect_percentile(filename)

    verdict: dict[str, Any] = {
        "requirement": "DSY1 2050s RCP8.5 50th percentile (…_DSY1_2050s_HIGH50_CIBSE_v1.1)",
        "source": "S-08 (TM59:2026 weather file requirements, §3)",
        "filename": filename,
        "detected": {"dsy_type": found_dsy, "epoch": found_epoch,
                     "percentile_label": found_pct},
    }

    if found_dsy is None and found_epoch is None and found_pct is None:
        verdict["status"] = "unknown"
        verdict["reason"] = (
            "Weather provenance not machine-verifiable from this filename: no CIBSE "
            "DSY family, epoch or percentile label detected. EPW headers carry no "
            "DSY metadata; verify the file's origin manually."
        )
        return verdict

    upper = filename.upper()
    present = {t for t in MINIMUM_TOKENS if t.upper() in upper}
    # Legacy naming ('DSY1_2050High50') can match DSY1 + epoch + percentile tokens but
    # is the pre-2025 release: TM59:2026 requires the CIBSE 2025 Weather Data v1.1 files.
    legacy = _is_legacy_naming(filename)
    if present == MINIMUM_TOKENS and "_V1.1" in upper and not legacy:
        verdict["status"] = "compatible"
        verdict["reason"] = ("Filename matches the TM59:2026 minimum requirement "
                             "(DSY1, 2050s, HIGH50, v1.1).")
    else:
        verdict["status"] = "research_only"
        missing = MINIMUM_TOKENS - present
        extra = []
        if found_dsy in ("DSY2", "DSY3"):
            extra.append(f"{found_dsy} is a more extreme event year than the DSY1 minimum")
        if found_epoch and found_epoch != "2050s":
            extra.append(f"epoch {found_epoch} differs from the required 2050s")
        if found_pct and found_pct != "HIGH50":
            extra.append(f"percentile label {found_pct} differs from HIGH50 (50th)")
        if legacy:
            extra.append(
                "legacy pre-2025-release naming: TM59:2026 requires the CIBSE 2025 "
                "Weather Data v1.1 files")
        elif "_V1.1" not in upper:
            extra.append("the v1.1 CIBSE 2025 release marker is absent from the filename, "
                         "so the file cannot be confirmed as the required release")
        verdict["reason"] = (
            "Traceable CIBSE DSY file but NOT confirmed as the TM59:2026 minimum: "
            + "; ".join(extra or sorted(missing))
            + ". Per S-08 §4 alternative files are for research/thoroughness — flagged "
              "accordingly."
        )
    return verdict


def check_tm59_2017_weather(filename: str) -> dict[str, Any]:
    """Classify a weather file against the TM59:2017 minimum requirement
    (S-02 §3.2: 'the DSY1 file most appropriate to the site location, for the 2020s,
    high emissions, 50% percentile scenario')."""
    found_dsy = _detect_dsy(filename)
    found_epoch = _detect_epoch(filename)
    up = filename.upper()
    # Legacy CIBSE 2016-release labels encode emissions+percentile as e.g.
    # 'High50' (high emissions, 50th percentile) / 'Medium90' / 'Low10'.
    import re

    m = re.search(r"(HIGH|MED|LOW|MEDIUM)(10|50|90)", up)
    scenario = m.group(1) if m else None
    pct = m.group(2) if m else None

    verdict: dict[str, Any] = {
        "requirement": "DSY1 2020s high emissions 50th percentile (<Site>_DSY1_2020High50)",
        "source": "S-02 (TM59:2017 §3.2 / §2.3(11))",
        "filename": filename,
        "detected": {"dsy_type": found_dsy, "epoch": found_epoch,
                     "scenario_label": scenario, "percentile_label": pct},
    }
    if found_dsy is None and found_epoch is None and scenario is None:
        verdict["status"] = "unknown"
        verdict["reason"] = (
            "Weather provenance not machine-verifiable from this filename. "
            "Verify the file's origin manually.")
        return verdict

    is_min = (found_dsy == "DSY1" and found_epoch == "2020s"
              and scenario in ("HIGH",) and pct == "50")
    if is_min:
        verdict["status"] = "compatible"
        verdict["reason"] = ("Filename matches the TM59:2017 minimum requirement "
                             "(DSY1, 2020s, high emissions, 50th percentile).")
    else:
        verdict["status"] = "research_only"
        extra = []
        if found_dsy in ("DSY2", "DSY3"):
            extra.append(f"{found_dsy} is a more extreme event year than the DSY1 minimum")
        if found_epoch and found_epoch != "2020s":
            extra.append(f"epoch {found_epoch} differs from the required 2020s")
        if scenario and scenario != "HIGH":
            extra.append(f"emissions scenario {scenario} differs from high emissions")
        if pct and pct != "50":
            extra.append(f"percentile {pct} differs from the 50th")
        if found_epoch == "2050s" or found_epoch == "2080s":
            extra.append("future-epoch files are for further testing of designs of "
                         "particular concern (TM59:2017 §3.2)")
        verdict["reason"] = (
            "Traceable CIBSE DSY file but NOT the TM59:2017 minimum: "
            + "; ".join(extra or ["no matching epoch/scenario label"])
            + ". Research/thoroughness use, flagged accordingly.")
    return verdict
