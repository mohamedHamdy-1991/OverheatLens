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


def check_tm59_2026_weather(filename: str) -> dict[str, Any]:
    """Classify a CIBSE weather file (by filename traceability) against the TM59:2026
    minimum requirement. Returns a machine-readable compatibility verdict."""
    name = filename.replace("_", " ")
    tokens = set(name.split()) | {filename}

    found_dsy = next((d for d in DSY_TYPES if d in filename.upper()), None)
    found_epoch = next((e for e in EPOCHS if e in filename), None)
    found_pct = next((p for p in PERCENTILES if p in filename.upper()), None)

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
    if present == MINIMUM_TOKENS:
        verdict["status"] = "compatible"
        verdict["reason"] = ("Filename matches the TM59:2026 minimum requirement "
                             "(DSY1, 2050s, HIGH50).")
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
        verdict["reason"] = (
            "Traceable CIBSE DSY file but NOT the TM59:2026 minimum: "
            + "; ".join(extra or sorted(missing))
            + ". Per S-08 §4 such files are alternatives for more thorough assessments — "
              "research use, flagged accordingly."
        )
    return verdict
