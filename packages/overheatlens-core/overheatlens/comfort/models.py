"""Comfort engine — wrappers around pythermalcomfort (RULE 4, plan §14).

The library's comfort mathematics are NEVER reimplemented here. Each wrapper:
* validates applicability EXPLICITLY and returns an explicit non-result
  (OUTSIDE_APPLICABILITY with a reason) instead of a misleading number;
* records the wrapped library version in every result (RULE 6 provenance);
* names the standard edition it implements (e.g. ISO 7730:2025).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pythermalcomfort
from pythermalcomfort.models import adaptive_en, pmv_ppd_iso, utci

LIBRARY = "pythermalcomfort"
LIBRARY_VERSION = pythermalcomfort.__version__


@dataclass
class ComfortResult:
    """A comfort result or an explicit non-result (plan §14.3)."""

    model: str
    standard_edition: str
    values: dict[str, Any]
    status: str                      # "OK" | "OUTSIDE_APPLICABILITY"
    reason: str | None = None
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = self.__dict__.copy()
        return d


def _provenance() -> dict[str, Any]:
    return {
        "library": LIBRARY,
        "library_version": LIBRARY_VERSION,
        "note": "comfort mathematics computed by the pinned library, wrapped "
                "unmodified (RULE 4)",
    }


def _native(values: dict[str, Any]) -> dict[str, Any]:
    """Coerce library outputs (numpy scalars/bools) to plain Python types so every
    result is JSON-serialisable without special-casing downstream."""
    out: dict[str, Any] = {}
    for k, v in values.items():
        if isinstance(v, bool):  # plain bool first (isinstance of np.bool_ excluded)
            out[k] = bool(v)
        elif hasattr(v, "item") and not isinstance(v, str):
            out[k] = v.item()  # numpy scalar -> python scalar
        else:
            out[k] = v
    return out


def _nan(values: dict[str, Any]) -> bool:
    def _is_nan(v: Any) -> bool:
        try:
            return bool(v != v)  # NaN check without importing numpy
        except (TypeError, ValueError):
            return False
    return any(_is_nan(v) for v in values.values())


def pmv_ppd(
    tdb: float, tr: float, vr: float, rh: float, met: float, clo: float,
) -> ComfortResult:
    """Fanger PMV/PPD per ISO 7730:2025 (library default model '7730-2025').

    Applicability (ISO 7730): tdb/tr 10-30 degC, vr 0-1 m/s, met 0.8-4.0,
    clo 0-2. Outside these ranges the result is an explicit non-result.
    """
    checks = [
        (10 <= tdb <= 30, f"tdb {tdb} outside 10-30 degC"),
        (10 <= tr <= 30, f"tr {tr} outside 10-30 degC"),
        (0 <= vr <= 1, f"vr {vr} outside 0-1 m/s"),
        (0.8 <= met <= 4, f"met {met} outside 0.8-4.0 met"),
        (0 <= clo <= 2, f"clo {clo} outside 0-2 clo"),
    ]
    failed = [msg for ok, msg in checks if not ok]
    if failed:
        return ComfortResult(
            model="pmv_ppd", standard_edition="ISO 7730:2025",
            values={}, status="OUTSIDE_APPLICABILITY",
            reason="; ".join(failed), provenance=_provenance())

    r = pmv_ppd_iso(tdb=tdb, tr=tr, vr=vr, rh=rh, met=met, clo=clo)
    values = _native({"pmv": r.pmv, "ppd": r.ppd})
    if _nan(values):
        return ComfortResult(
            model="pmv_ppd", standard_edition="ISO 7730:2025", values={},
            status="OUTSIDE_APPLICABILITY",
            reason="library applicability check returned no value",
            provenance=_provenance())
    return ComfortResult(
        model="pmv_ppd", standard_edition="ISO 7730:2025", values=values,
        status="OK", provenance=_provenance())


def adaptive_comfort_en(
    tdb: float, tr: float, t_running_mean: float, v: float,
) -> ComfortResult:
    """EN 16798-1 / EN 15251 adaptive comfort (library adaptive_en).

    Applicability: running mean 10-30 degC, v < 1.2 m/s at the occupied zone.
    Above 30 degC the adaptive model itself is outside its range — the library
    caps its comfort band there; OverheatLens reports OUTSIDE_APPLICABILITY for
    Trm > 30 rather than extrapolate.
    """
    checks = [
        (10 <= t_running_mean <= 30,
         f"t_running_mean {t_running_mean} outside 10-30 degC (EN 16798-1 "
         "applicability; above 30 degC the adaptive equation is not defined)"),
        (v < 1.2, f"v {v} m/s is not < 1.2 m/s"),
    ]
    failed = [msg for ok, msg in checks if not ok]
    if failed:
        return ComfortResult(
            model="adaptive_en", standard_edition="EN 16798-1",
            values={}, status="OUTSIDE_APPLICABILITY",
            reason="; ".join(failed), provenance=_provenance())

    r = adaptive_en(tdb=tdb, tr=tr, t_running_mean=t_running_mean, v=v)
    values = _native({
        "tmp_cmf": r.tmp_cmf,
        "tmp_cmf_cat_i_up": r.tmp_cmf_cat_i_up,
        "tmp_cmf_cat_ii_up": r.tmp_cmf_cat_ii_up,
        "acceptability_cat_ii": r.acceptability_cat_ii,
    })
    if _nan({k: v for k, v in values.items() if k != "acceptability_cat_ii"}):
        return ComfortResult(
            model="adaptive_en", standard_edition="EN 16798-1", values={},
            status="OUTSIDE_APPLICABILITY",
            reason="library applicability check returned no value",
            provenance=_provenance())
    return ComfortResult(
        model="adaptive_en", standard_edition="EN 16798-1", values=values,
        status="OK", provenance=_provenance())


def utci_comfort(tdb: float, tr: float, v: float, rh: float) -> ComfortResult:
    """UTCI outdoor index (library requires mean radiant temperature explicitly).
    Applicability: tdb -50 to +50 degC, v 0.5-17 m/s (at 10 m reference height)."""
    checks = [
        (-50 <= tdb <= 50, f"tdb {tdb} outside -50 to +50 degC"),
        (0.5 <= v <= 17, f"v {v} outside 0.5-17 m/s (10 m reference)"),
    ]
    failed = [msg for ok, msg in checks if not ok]
    if failed:
        return ComfortResult(
            model="utci", standard_edition="UTCI polynomial (Bröde et al.)",
            values={}, status="OUTSIDE_APPLICABILITY",
            reason="; ".join(failed), provenance=_provenance())

    r = utci(tdb=tdb, tr=tr, v=v, rh=rh)
    values = _native({"utci": r.utci})
    if _nan(values):
        return ComfortResult(
            model="utci", standard_edition="UTCI polynomial (Bröde et al.)",
            values={}, status="OUTSIDE_APPLICABILITY",
            reason="library applicability check returned no value",
            provenance=_provenance())
    return ComfortResult(
        model="utci", standard_edition="UTCI polynomial (Bröde et al.)",
        values=values, status="OK", provenance=_provenance())
