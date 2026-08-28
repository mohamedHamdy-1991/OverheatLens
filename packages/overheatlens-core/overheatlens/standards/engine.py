"""Standards engine — evaluates versioned rule packs against hourly operative temperatures.

Design invariants (governing plan §13, RULE 1, RULE 7, RULE 19):

* Thresholds are data (the YAML packs), never code constants.
* Every result carries rule id, clause, inputs, metric, threshold, margin, and the
  pack's verification status.
* Packs whose sources are not verified cannot produce compliance-labelled results.
  This is enforced here, in code — not by policy documents.
* A criterion that cannot be evaluated (e.g. TM59:2017 Criterion D -> TM52) is reported
  as NOT_EVALUATED, never silently passed.

TM59:2026 support (source-verified, S-03/S-08):
* adaptive thresholds with dwelling Category I/II and Trm running-mean chain (TM52
  Eq 2.2/2.3 cross-reference — see the pack verification note);
* criterion a delta-T rounding per TM52 (raw delta-T >= 0.5 K counts as 1 K);
* nights-based criterion b (mean over hours of sleep 23:00-08:00, limit 4 nights);
* occupied-hour limits (criterion a/c: 59 h living / 110 h bedroom; criterion d: 110 h);
* May-September assessment window with per-space-type occupancy schedules.
"""

from __future__ import annotations

import calendar as _cal
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Sequence

import numpy as np

from ..schemas import RulePackError, load_bundled_pack


class EvaluationMode(str, Enum):
    COMPLIANCE = "compliance"
    RESEARCH = "research"


class SourceNotVerified(Exception):
    """A pack without verified sources was used outside the permitted mode."""


class BlockedRulePack(SourceNotVerified):
    """The pack's source document has not been acquired at all."""


class MissingEvaluationInput(Exception):
    """A criterion cannot be evaluated with the inputs supplied (explicit non-result)."""


class NotEvaluatedStatus(str, Enum):
    NOT_EVALUATED = "NOT_EVALUATED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


# TM59:2017 sleep window 22:00-07:00 in hour-ending labels (label H covers (H-1:00, H]).
_SLEEP_HOURS_2017 = frozenset((23, 24, 1, 2, 3, 4, 5, 6, 7))
# TM59:2026 hours of sleep 23:00-08:00 -> hour-ending labels 24, 1..8.
_SLEEP_HOURS_2026 = frozenset((24, 1, 2, 3, 4, 5, 6, 7, 8))
# TM59:2026 living/home-office occupancy 09:00-22:00 -> hour-ending labels 10..22.
_LIVING_HOURS_2026 = frozenset(range(10, 23))

_HOUR_BASIS = 8760


@dataclass
class HourlyCalendar:
    """Per-hour calendar arrays for the assessed year (hour-ending convention)."""

    hour: np.ndarray   # 1..24
    month: np.ndarray  # 1..12
    day: np.ndarray    # 1..31

    @classmethod
    def standard(cls, n: int = _HOUR_BASIS) -> "HourlyCalendar":
        """Standard calendar for an 8760-hour non-leap year."""
        hours: list[int] = []
        months: list[int] = []
        days: list[int] = []
        for m in range(1, 13):
            nd = _cal.monthrange(2001, m)[1]
            for d in range(1, nd + 1):
                for h in range(1, 25):
                    hours.append(h)
                    months.append(m)
                    days.append(d)
        return cls(
            hour=np.asarray(hours[:n]),
            month=np.asarray(months[:n]),
            day=np.asarray(days[:n]),
        )


@dataclass
class CriterionResult:
    criterion_id: str
    rule_ref: str
    metric_value: float | None
    threshold: float
    operator: str
    units: str
    passed: bool | None            # None when NOT_EVALUATED
    margin: float | None           # metric - limit, signed in the failing direction
    status: str                    # "PASS" | "FAIL" | "NOT_EVALUATED"
    verification_status: str
    basis: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "criterion_id": self.criterion_id,
            "rule_ref": self.rule_ref,
            "metric_value": self.metric_value,
            "threshold": self.threshold,
            "operator": self.operator,
            "units": self.units,
            "passed": self.passed,
            "margin": self.margin,
            "status": self.status,
            "verification_status": self.verification_status,
            "basis": self.basis,
            "notes": self.notes,
        }


@dataclass
class RoomAssessment:
    room_id: str
    room_type: str
    pack_id: str
    pack_version: str
    mode: str
    applicable_criteria: list[str]
    results: list[CriterionResult]
    verification_status: str

    @property
    def passed(self) -> bool:
        """True only when every result evaluated and passed (NOT_EVALUATED never passes)."""
        return bool(self.results) and all(r.passed is True for r in self.results)

    def to_dict(self) -> dict[str, Any]:
        return {
            "room_id": self.room_id,
            "room_type": self.room_type,
            "pack_id": self.pack_id,
            "pack_version": self.pack_version,
            "mode": self.mode,
            "passed": self.passed,
            "verification_status": self.verification_status,
            "applicable_criteria": self.applicable_criteria,
            "criteria": [r.to_dict() for r in self.results],
        }


def classify_room(name: str, pack: dict) -> str:
    """Classify a room by matching its name against pack space-type aliases (case-insensitive,
    longest-alias-first). Returns the space-type key, defaulting to 'other' when present."""
    n = name.strip().lower()
    best: tuple[int, str] | None = None
    for st_key, st in pack.get("space_types", {}).items():
        for alias in st.get("aliases", []):
            a = alias.strip().lower()
            if a and a in n:
                if best is None or len(a) > best[0]:
                    best = (len(a), st_key)
    if best:
        return best[1]
    return "other" if "other" in pack.get("space_types", {}) else (
        next(iter(pack.get("space_types", {})), "unverified")
    )


def running_mean_trm(daily_mean_outdoor: np.ndarray) -> np.ndarray:
    """CIBSE TM52 running mean Trm for 1 May..30 Sep from daily mean outdoor temperatures.

    ``daily_mean_outdoor`` holds 365 daily means (1 Jan..31 Dec, non-leap).

    Verified against the TM52 PDF (S-04, 2013, §Box 2):
      Eq 2.3 initialiser: Trm = (Tod-1 + 0.8 Tod-2 + 0.6 Tod-3 + 0.5 Tod-4
                                  + 0.4 Tod-5 + 0.3 Tod-6 + 0.2 Tod-7) / 3.8
        applied to the seven days ending 29 April to start Trm(30 April);
      Eq 2.2 recursion: Trm = 0.8*Trm-1 + 0.2*Tod-1  (alpha = 0.8).
    Returns Trm for the days 1 May..30 Sep (153 values, indexed 0 = 1 May).
    """
    dm = np.asarray(daily_mean_outdoor, dtype=np.float64)
    if dm.size != 365:
        raise ValueError(f"expected 365 daily means, got {dm.size}")
    # Published Eq 2.3 weights (most recent day first) and their stated denominator.
    w = np.array([1.0, 0.8, 0.6, 0.5, 0.4, 0.3, 0.2])
    # 0-based day-of-year index of 30 April = 31 (Jan) + 28 (Feb) + 31 (Mar) + 29
    apr30_idx = 31 + 28 + 31 + 29
    trm = float(np.sum(w * dm[apr30_idx - 1 - np.arange(7)]) / 3.8)
    trms = np.empty(153)
    for i in range(153):
        # Eq 2.2 with Trm(30 Apr) as Trm-1: Trm(1 May) = 0.8*Trm(30 Apr) + 0.2*Tdm(30 Apr);
        # then Trm(d) = 0.8*Trm(d-1) + 0.2*Tdm(d-1) through 30 September.
        trm = 0.8 * trm + 0.2 * dm[apr30_idx + i]
        trms[i] = trm
    return trms


class StandardsEngine:
    """Evaluate a rule pack against hourly operative-temperature series."""

    def __init__(self, pack: dict):
        self.pack = pack
        self.pack_id: str = pack["rule_pack"]
        self.pack_version: str = pack["version"]
        self.source_status: str = pack["source_status"]
        self._criteria = {c["id"]: c for c in pack.get("criteria", [])}
        self._space_types = pack.get("space_types", {})

    # ------------------------------------------------------------------ load
    @classmethod
    def load(cls, pack_id: str, *, with_parents: bool = True) -> "StandardsEngine":
        pack = load_bundled_pack(pack_id)
        if with_parents and "inherits" in pack:
            parent = load_bundled_pack(pack["inherits"])
            parent_by_id = {c["id"]: c for c in parent.get("criteria", [])}
            resolved: list[dict] = []
            for c in pack.get("criteria", []):
                if c.get("metric") == "inherited" and c["id"] in parent_by_id:
                    # Inherited criterion: evaluate with the parent's full definition,
                    # keeping this pack's clause label for traceability.
                    resolved_c = dict(parent_by_id[c["id"]])
                    resolved_c["clause"] = c.get(
                        "clause", resolved_c.get("clause", ""))
                    resolved.append(resolved_c)
                else:
                    resolved.append(c)
            for cid, c in ((c["id"], c) for c in parent.get("criteria", [])):
                if cid not in {c2["id"] for c2 in resolved}:
                    resolved.append(c)
            pack["criteria"] = resolved
        return cls(pack)

    # ------------------------------------------------------------------ gate
    def compliance_allowed(self) -> bool:
        if self.source_status == "blocked_no_source":
            return False
        return self.source_status == "source_verified"

    def _gate(self, mode: EvaluationMode) -> None:
        if self.source_status == "blocked_no_source":
            raise BlockedRulePack(
                f"Rule pack '{self.pack_id}' is blocked: source not acquired. "
                "No evaluation of any kind is possible (source not verified)."
            )
        if mode is EvaluationMode.COMPLIANCE and not self.compliance_allowed():
            raise SourceNotVerified(
                f"Rule pack '{self.pack_id}' is not source-verified; compliance-mode "
                "evaluation is refused. Use research mode, which labels results "
                "'source not verified'."
            )

    # -------------------------------------------------------------- thresholds
    def _adaptive_thresholds(self, criterion: dict, category: str,
                             daily_mean_outdoor: np.ndarray) -> np.ndarray:
        """Per-day adaptive threshold for 1 May..30 Sep from the pack's category entry."""
        ad = criterion.get("adaptive_threshold")
        if not ad:
            raise RulePackError(f"criterion {criterion['id']} has no adaptive_threshold")
        key = "category_I" if category == "I" else "category_II"
        cat = ad[key]
        slope = float(cat["linear_slope_k_per_c"])
        trm_lo, trm_hi = float(cat["clamp_trm_min_c"]), float(cat["clamp_trm_max_c"])
        c_lo, c_hi = float(cat["clamp_min_c"]), float(cat["clamp_max_c"])
        offset = c_lo - slope * trm_lo
        trm = running_mean_trm(daily_mean_outdoor)
        th = slope * trm + offset
        # Source fixes the thresholds at the clamp values outside Trm 10-30.
        return np.clip(th, c_lo, c_hi)

    def _condition_count(self, criterion: dict, top: np.ndarray, mask_window: np.ndarray,
                         category: str, daily_mean_outdoor: np.ndarray | None,
                         fan_uplift: np.ndarray | None) -> tuple[int, dict[str, Any]]:
        """Count exceedance hours for the criterion within ``mask_window`` (bool array)."""
        cond = criterion.get("condition", "")
        notes: list[str] = []

        if cond.startswith("adaptive"):
            rounding = criterion.get("delta_t_rounding")
            raw_4k = rounding == "none_for_criterion_3"
            if not raw_4k and rounding != "nearest_whole_degree_tm52":
                raise RulePackError(f"unsupported rounding {rounding!r}")
            if daily_mean_outdoor is None:
                raise MissingEvaluationInput(
                    "adaptive criteria need daily_mean_outdoor (365 daily means) for "
                    "the running-mean threshold — none supplied")
            th = self._adaptive_thresholds(criterion, category, daily_mean_outdoor)
            # Map per-day (May-Sep) thresholds onto hours.
            day_index = self._doy - 120  # 0-based day-of-year; 120 = 1 May
            th_hourly = np.full(top.shape, np.nan)
            ok = (day_index >= 0) & (day_index < 153)
            th_hourly[ok] = th[day_index[ok]]
            delta = top - th_hourly
            if fan_uplift is not None:
                delta = delta - fan_uplift
            if raw_4k:
                # TM52 Criterion 3: raw (unrounded) DT > 4 K at any assessed hour.
                counted = np.where(np.isnan(delta), False, delta > 4.0) & mask_window
                notes.append("Raw (unrounded) Delta T > 4 K per TM52 Criterion 3.")
                return int(counted.sum()), {"threshold_model": "adaptive_tm52_tupp",
                                            "category": category,
                                            "notes_extra": notes}
            # TM52 delta-T rounding: raw delta T >= 0.5 K counts as 1 K exceedance.
            # IEEE-754 guard: a raw DT of exactly 0.5 must count, but slope*Trm+offset
            # carries last-bit noise (e.g. 0.33*20+21.8 -> 28.400000000000002). The
            # 1e-9 K epsilon absorbs that noise only; the threshold stays 0.5 K.
            counted = np.where(np.isnan(delta), False, delta >= 0.5 - 1e-9) & mask_window
            notes.append("Delta T rounded to nearest whole degree per TM52: "
                         "raw Delta T >= 0.5 K counts as exceedance.")
            return int(counted.sum()), {"threshold_model": "adaptive_tm52",
                                        "category": category, "notes_extra": notes}

        # fixed-threshold form: "top_c > 26.0" / "top_c - 26.0 >= 1.0" etc.
        t = np.asarray(top, dtype=np.float64)
        c = cond.replace(" ", "")
        if c.startswith("top_c-"):
            import re

            m = re.fullmatch(r"top_c-([0-9.]+)(>=|<=|>|<|==)([0-9.]+)", c)
            if not m:
                raise RulePackError(f"Unparseable condition {cond!r}")
            lhs = t - float(m.group(1))
            op, rhs = m.group(2), float(m.group(3))
        else:
            import re

            m = re.fullmatch(r"top_c(>=|<=|>|<|==)([0-9.]+)", c)
            if not m:
                raise RulePackError(f"Unparseable condition {cond!r}")
            lhs = t
            op, rhs = m.group(1), float(m.group(2))
        raw = {">": lhs > rhs, ">=": lhs >= rhs, "<": lhs < rhs, "<=": lhs <= rhs,
               "==": np.isclose(lhs, rhs)}[op]
        if fan_uplift is not None:
            # Fixed-threshold criteria: uplift effectively relaxes the threshold.
            eff = {">": lhs - fan_uplift > rhs, ">=": lhs - fan_uplift >= rhs,
                   "<": lhs - fan_uplift < rhs, "<=": lhs - fan_uplift <= rhs}
            raw = eff[op]
        counted = raw & mask_window
        return int(counted.sum()), {}

    # -------------------------------------------------------------- evaluation
    def _window_mask(self, criterion: dict, room_type: str) -> tuple[np.ndarray, dict]:
        """Boolean mask of the assessed hours for this criterion/room, plus basis info."""
        months = criterion.get("months")
        variant = (criterion.get("variants") or {}).get(room_type)
        occ = (variant or {}).get("occupancy_basis", criterion.get("occupancy_basis"))
        basis = int((variant or {}).get(
            "occupancy_hours_basis", criterion.get("occupancy_hours_basis", 0)))
        limit = (variant or {}).get(
            "max_exceedance_hours", criterion.get("max_exceedance_hours"))

        in_months = np.ones(self._n, dtype=bool)
        if months:
            in_months = np.isin(self._month, list(range(months[0], months[1] + 1)))

        if occ == "living_hours":
            occ_mask = np.isin(self._hour, list(_LIVING_HOURS_2026))
        elif occ == "all_hours":
            occ_mask = np.ones(self._n, dtype=bool)
        elif occ == "model_supplied":
            occupancy = getattr(self, "_occupancy", None)
            if occupancy is None:
                raise MissingEvaluationInput(
                    "criterion requires modelled occupied hours (pass an occupancy "
                    "array) — none supplied")
            occ_mask = np.asarray(occupancy, dtype=bool)
            if occ_mask.size != self._n:
                raise ValueError(
                    f"occupancy array has {occ_mask.size} hours; expected {self._n}")
        else:
            # window-based masks (e.g. TM59:2017 criterion b sleep window)
            window = criterion.get("window", "all_hours")
            if window == "sleep_hours":
                occ_mask = np.isin(self._hour, list(_SLEEP_HOURS_2017))
            else:
                occ_mask = np.ones(self._n, dtype=bool)

        return in_months & occ_mask, {
            "occupancy_basis": occ, "occupancy_hours_basis": basis,
            "max_exceedance_hours": limit, "months": months,
        }

    def _evaluate_criterion_checked(
        self, criterion: dict, top: np.ndarray, room_type: str, **kw
    ) -> "CriterionResult":
        result = self._evaluate_criterion(criterion, top, room_type, **kw)
        if bool(criterion.get("advisory", False)) and result.passed is not None:
            # Advisory criteria are reported as risk flags, never pass/fail.
            flagged = result.metric_value is not None and result.status == "FAIL"
            result = CriterionResult(
                **{**result.__dict__,
                   "passed": None,
                   "status": "FLAG" if flagged else "NO_FLAG",
                   "notes": list(result.notes) + [
                       "Advisory criterion: reported as a risk flag only; it never "
                       "contributes a pass or a fail to the overall result."]})
        return result

    def _evaluate_criterion(
        self,
        criterion: dict,
        top: np.ndarray,
        room_type: str,
        *,
        category: str = "II",
        daily_mean_outdoor: np.ndarray | None = None,
        fan_uplift: np.ndarray | None = None,
    ) -> CriterionResult:
        cid = criterion["id"]
        base = dict(
            criterion_id=cid,
            rule_ref=criterion.get("clause", self.pack_id),
            threshold=float(criterion.get("threshold", 0.0)),
            operator=criterion.get("operator", ">"),
            units=criterion.get("units", "none"),
            verification_status=criterion.get("verification", {}).get(
                "status", self.source_status),
        )

        if criterion.get("not_implemented"):
            return CriterionResult(
                metric_value=None, passed=None, margin=None,
                status=NotEvaluatedStatus.NOT_EVALUATED.value,
                notes=["Criterion is implemented in a separate, not-yet-verified method "
                       f"({criterion.get('method_ref', 'external')}); reported as "
                       "NOT_EVALUATED, never as PASS."],
                **base,
            )

        aggregation = criterion.get("aggregation", "")
        t = np.asarray(top, dtype=np.float64)
        if t.size != _HOUR_BASIS:
            raise ValueError(
                f"Expected {_HOUR_BASIS} hourly values, got {t.size}.")

        # Resolve a shared adaptive-threshold definition (e.g. TM52 c2/c3 -> c1).
        if "adaptive_threshold" not in criterion and criterion.get("adaptive_threshold_ref"):
            ref = self._criteria.get(criterion["adaptive_threshold_ref"])
            if ref is None or "adaptive_threshold" not in ref:
                raise RulePackError(
                    f"criterion {cid} references adaptive_threshold_ref "
                    f"{criterion['adaptive_threshold_ref']!r}, which has no "
                    "adaptive_threshold")
            criterion = {**criterion,
                         "adaptive_threshold": ref["adaptive_threshold"],
                         "delta_t_rounding": criterion.get(
                             "delta_t_rounding", ref.get("delta_t_rounding"))}

        # ---- TM52 Criterion 2: daily weighted exceedance (We) ---------------
        if aggregation == "max_daily_we_vs_limit":
            if daily_mean_outdoor is None:
                raise MissingEvaluationInput(
                    "criterion We needs daily_mean_outdoor (365 daily means)")
            try:
                mask, basis_info = self._window_mask(criterion, room_type)
            except MissingEvaluationInput as e:
                return CriterionResult(
                    metric_value=None, passed=None, margin=None,
                    status=NotEvaluatedStatus.NOT_EVALUATED.value,
                    notes=[f"Not evaluated: {e}"], **base)
            if not mask.any():
                return CriterionResult(
                    metric_value=None, passed=None, margin=None,
                    status=NotEvaluatedStatus.NOT_EVALUATED.value,
                    notes=["No occupied hours supplied for the assessment window."],
                    **base)
            th = self._adaptive_thresholds(criterion, category, daily_mean_outdoor)
            day_index = self._doy - 120
            ok = (day_index >= 0) & (day_index < 153)
            th_hourly = np.full(t.shape, np.nan)
            th_hourly[ok] = th[day_index[ok]]
            delta = t - th_hourly
            # wf = 0 if DT <= 0 else DT rounded to the nearest whole degree
            rounded = np.floor(np.where(np.isnan(delta), 0.0, delta) + 0.5)
            wf = np.where(np.isnan(delta), 0.0, np.where(delta > 0, rounded, 0.0))
            wf = wf * mask  # only occupied hours within the window contribute
            day_of_hour = day_index  # May-Sep day index per hour (negative outside)
            we_by_day = {}
            for di in np.unique(day_of_hour[mask]):
                di = int(di)
                if di < 0:
                    continue
                we_by_day[di] = float(wf[day_of_hour == di].sum())
            worst_day = max(we_by_day, key=lambda d: we_by_day[d]) if we_by_day else None
            worst_we = we_by_day[worst_day] if worst_day is not None else 0.0
            limit = float(criterion["threshold"])
            fail = worst_we > limit
            m, d = (self._doy_to_month_day(120 + worst_day)
                    if worst_day is not None else (0, 0))
            return CriterionResult(
                metric_value=round(worst_we, 3), passed=(not fail),
                margin=round(worst_we - limit, 4),
                status="FAIL" if fail else "PASS",
                basis={"worst_day_we": round(worst_we, 3),
                       "worst_day": f"{m:02d}-{d:02d}" if worst_day is not None else None,
                       "limit_we": limit,
                       "n_days_assessed": len(we_by_day)},
                notes=["We = sum over the day of hours x wf (wf = rounded DT when "
                       "DT > 0, else 0); fail if > 6 on any one day (TM52 Eq 10)."],
                **base)

        # ---- nights aggregation (TM59:2026 criterion b) --------------------
        if aggregation == "nights_count_vs_limit":
            sleep = criterion.get("sleep_window", "")
            if sleep != "23:00-08:00":
                raise RulePackError(f"unsupported sleep window {sleep!r}")
            cat_th = criterion.get("category_thresholds", {})
            tn = float(cat_th["I"] if category == "I" else cat_th["II"])
            nights = self._nights_may_sep(t, tn)
            limit = float(criterion["max_nights"])
            n_over = int(nights["means_over_count"])
            passed = not (n_over > limit)
            return CriterionResult(
                metric_value=float(n_over),
                passed=passed,
                margin=round(n_over - limit, 4),
                status="FAIL" if not passed else "PASS",
                basis={
                    "threshold_tn_c": tn, "nights_assessed": nights["n_assessed"],
                    "sleep_window": sleep, "category": category,
                    "failing_night_dates": nights["failing_dates"][:10],
                },
                notes=(["Cross-reference: sleep window 11 pm-8 am per TM59:2026 §2.4.2."]
                       if not criterion.get("interpretation_note") else
                       [f"Note: {criterion['interpretation_note']}"]),
                **base,
            )

        # ---- advisory criteria (e.g. TM59:2017 §4.5 corridors) --------------
        # Evaluated for reporting but never contribute pass/fail to the dwelling.
        advisory = bool(criterion.get("advisory", False))

        # ---- hour-count aggregations ---------------------------------------
        if aggregation in ("exceedance_hours_vs_limit", "percent_of_annual_hours",
                           "total_hours", "percent_of_occupied_hours",
                           "percent_of_model_occupied_hours"):
            try:
                mask, basis_info = self._window_mask(criterion, room_type)
                count, extra = self._condition_count(
                    criterion, t, mask, category, daily_mean_outdoor, fan_uplift)
            except MissingEvaluationInput as e:
                # Explicit non-result (plan §27.3): a criterion whose required inputs are
                # absent is NOT_EVALUATED — never zero, never a crash, never a pass.
                return CriterionResult(
                    metric_value=None, passed=None, margin=None,
                    status=NotEvaluatedStatus.NOT_EVALUATED.value,
                    notes=[f"Not evaluated: {e}"],
                    **base)

            if aggregation == "exceedance_hours_vs_limit":
                limit = float(basis_info["max_exceedance_hours"])
                fail = count > limit
                return CriterionResult(
                    metric_value=float(count), passed=(not fail),
                    margin=round(count - limit, 4),
                    status="FAIL" if fail else "PASS",
                    basis={"exceedance_hours": count, "limit_hours": limit,
                           "occupancy_basis": basis_info["occupancy_basis"],
                           "months": basis_info["months"], **extra},
                    notes=[], **base)

            if aggregation in ("percent_of_occupied_hours",
                               "percent_of_model_occupied_hours"):
                denom = float(basis_info["occupancy_hours_basis"])
                if aggregation == "percent_of_model_occupied_hours":
                    if denom <= 0:  # model_supplied: count the supplied mask
                        denom = float(mask.sum())
                    if denom <= 0:
                        return CriterionResult(
                            metric_value=None, passed=None, margin=None,
                            status=NotEvaluatedStatus.NOT_EVALUATED.value,
                            notes=["Occupied-hours denominator is zero (empty "
                                   "occupancy); explicit non-result."],
                            **base)
                metric = 100.0 * count / denom
                threshold = float(criterion["threshold"])
                fail = metric > threshold
                return CriterionResult(
                    metric_value=round(metric, 4), passed=(not fail),
                    margin=round(metric - threshold, 4),
                    status="FAIL" if fail else "PASS",
                    basis={"exceedance_hours": count, "occupied_hours_basis": denom,
                           "occupancy_basis": basis_info["occupancy_basis"],
                           "months": basis_info["months"], **extra},
                    notes=[], **base)

            if aggregation == "percent_of_annual_hours":
                metric = 100.0 * count / _HOUR_BASIS
                threshold = float(criterion["threshold"])
                fail = metric > threshold
                return CriterionResult(
                    metric_value=round(metric, 4), passed=(not fail),
                    margin=round(metric - threshold, 4),
                    status="FAIL" if fail else "PASS",
                    basis={"exceedance_hours": count, "hour_basis": _HOUR_BASIS},
                    notes=[], **base)

            metric = float(count)
            threshold = float(criterion["threshold"])
            fail = metric > threshold
            return CriterionResult(
                metric_value=metric, passed=(not fail),
                margin=round(metric - threshold, 4),
                status="FAIL" if fail else "PASS",
                basis={"exceedance_hours": count}, notes=[], **base)

        return CriterionResult(
            metric_value=None, passed=None, margin=None,
            status=NotEvaluatedStatus.NOT_EVALUATED.value,
            notes=[f"Aggregation {aggregation!r} not implemented."],
            **base)

    # ------------------------------------------------------------- calendar utils
    def _bind_calendar(self, hour: Sequence[int] | None, n: int) -> None:
        self._n = n
        cal = HourlyCalendar.standard(n)
        if hour is None:
            self._hour, self._month, self._day = cal.hour, cal.month, cal.day
        else:
            self._hour = np.asarray(hour, dtype=int)
            self._month, self._day = cal.month, cal.day
        cum = np.cumsum([0] + [_cal.monthrange(2001, m)[1] for m in range(1, 13)])
        self._doy = cum[self._month - 1] + (self._day - 1)  # 0-based day-of-year per hour
        self._cum_days = cum

    def _doy_to_month_day(self, doy: int) -> tuple[int, int]:
        # cum[m-1] = days before month m, so month m occupies [cum[m-1], cum[m]);
        # searchsorted(..., 'right') returns that m directly.
        m = int(np.searchsorted(self._cum_days, doy, side="right"))
        return m, doy - self._cum_days[m - 1] + 1

    def _nights_may_sep(self, top: np.ndarray, tn: float) -> dict[str, Any]:
        """Mean night temperature per night for nights of 1 May..30 Sep.

        Night of day N = hour-ending label 24 of day N plus labels 1..8 of day N+1
        (11 pm-8 am). The 30 Sep night needs 1 Oct data (present in a full-year series).
        """
        t = np.asarray(top, dtype=np.float64)
        hour, month, day = self._hour, self._month, self._day
        failing: list[str] = []
        n_over = 0
        n_assessed = 0
        for doy in range(120, 273):  # 0-based: 120 = 1 May, 272 = 30 Sep
            m_cur, d_cur = self._doy_to_month_day(doy)
            m_next, d_next = self._doy_to_month_day(doy + 1)
            mask = (((month == m_cur) & (day == d_cur) & (hour == 24))
                    | ((month == m_next) & (day == d_next)
                       & (hour >= 1) & (hour <= 8)))
            vals = t[mask]
            if vals.size != 9:
                raise ValueError(
                    f"night {m_cur:02d}-{d_cur:02d}: expected 9 sleep hours, "
                    f"got {vals.size}")
            n_assessed += 1
            if float(vals.mean()) > tn:
                n_over += 1
                failing.append(f"{m_cur:02d}-{d_cur:02d}")
        return {
            "n_assessed": n_assessed, "means_over_count": n_over,
            "failing_dates": failing,
        }

    # ------------------------------------------------------------------ public API
    def evaluate_room(
        self,
        room_id: str,
        room_name: str,
        top: np.ndarray,
        hour: Sequence[int] | None = None,
        *,
        occupancy: Sequence[bool] | np.ndarray | None = None,
        category: str = "II",
        ventilation_route: str = "natural",
        daily_mean_outdoor: np.ndarray | None = None,
        fan_uplift: np.ndarray | None = None,
        mode: EvaluationMode | str = EvaluationMode.RESEARCH,
    ) -> RoomAssessment:
        """Assess one room. Default mode is RESEARCH so unverified packs stay usable for
        development while clearly labelled; compliance mode enforces the source gate."""
        if isinstance(mode, str):
            mode = EvaluationMode(mode)
        self._gate(mode)
        if category not in ("I", "II"):
            raise ValueError("category must be 'I' or 'II'")

        t = np.asarray(top, dtype=np.float64)
        self._bind_calendar(hour, t.size)
        self._occupancy = (
            None if occupancy is None else np.asarray(occupancy, dtype=bool))

        room_type = classify_room(room_name, self.pack)
        st = self._space_types.get(room_type, {})
        applicable = st.get("criteria", [])

        results: list[CriterionResult] = []
        for cid in applicable:
            criterion = self._criteria.get(cid)
            if criterion is None:
                results.append(CriterionResult(
                    criterion_id=cid, rule_ref=f"{self.pack_id}:{cid}",
                    metric_value=None, threshold=0.0, operator=">=", units="none",
                    passed=None, margin=None,
                    status=NotEvaluatedStatus.NOT_EVALUATED.value,
                    verification_status=self.source_status,
                    notes=["Criterion referenced by space type but absent from pack."],
                ))
                continue
            # Route-specific criteria (TM59:2017 §4.1-4.3: natural -> a+b;
            # mechanical -> mv). Criteria for the other route are NOT_APPLICABLE.
            crit_route = criterion.get("ventilation_route")
            if crit_route and crit_route != ventilation_route:
                results.append(CriterionResult(
                    criterion_id=cid,
                    rule_ref=criterion.get("clause", f"{self.pack_id}:{cid}"),
                    metric_value=None, threshold=float(criterion.get("threshold", 0)),
                    operator=criterion.get("operator", ">"),
                    units=criterion.get("units", "none"),
                    passed=None, margin=None,
                    status=NotEvaluatedStatus.NOT_APPLICABLE.value,
                    verification_status=criterion.get("verification", {}).get(
                        "status", self.source_status),
                    notes=[f"Not applicable: this criterion belongs to the "
                           f"{crit_route}-ventilation route; the assessment selected "
                           f"{ventilation_route}."],
                ))
                continue
            results.append(self._evaluate_criterion_checked(
                criterion, t, room_type, category=category,
                daily_mean_outdoor=daily_mean_outdoor, fan_uplift=fan_uplift))

        return RoomAssessment(
            room_id=room_id, room_type=room_type, pack_id=self.pack_id,
            pack_version=self.pack_version, mode=mode.value,
            applicable_criteria=list(applicable), results=results,
            verification_status=self.source_status,
        )

    def evaluate_dwelling(
        self,
        rooms: Iterable[tuple[str, str, np.ndarray]],
        hour: Sequence[int] | None = None,
        *,
        occupancy: Sequence[bool] | np.ndarray | None = None,
        category: str = "II",
        ventilation_route: str = "natural",
        daily_mean_outdoor: np.ndarray | None = None,
        fan_uplift: np.ndarray | None = None,
        mode: EvaluationMode | str = EvaluationMode.RESEARCH,
    ) -> dict[str, Any]:
        """Assess a dwelling: fails if any room fails any applicable criterion. Rooms with
        NOT_EVALUATED criteria make the dwelling result INCOMPLETE, never PASS. Advisory
        criteria are reported as flags and never block a pass."""
        if isinstance(mode, str):
            mode = EvaluationMode(mode)
        self._gate(mode)

        room_results = [
            self.evaluate_room(rid, name, t, hour, occupancy=occupancy,
                               category=category,
                               ventilation_route=ventilation_route,
                               daily_mean_outdoor=daily_mean_outdoor,
                               fan_uplift=fan_uplift, mode=mode)
            for rid, name, t in rooms
        ]
        # Advisory (FLAG/NO_FLAG) and NOT_APPLICABLE criteria never block a pass.
        decisive = [cr for r in room_results for cr in r.results
                    if cr.status not in ("FLAG", "NO_FLAG",
                                         NotEvaluatedStatus.NOT_APPLICABLE.value)]
        any_fail = any(cr.passed is False for cr in decisive)
        any_ne = any(cr.passed is None for cr in decisive)
        overall = "FAIL" if any_fail else ("INCOMPLETE" if any_ne else "PASS")
        return {
            "pack_id": self.pack_id, "pack_version": self.pack_version,
            "mode": mode.value, "verification_status": self.source_status,
            "dwelling_category": category,
            "overall": overall,
            "rooms": [r.to_dict() for r in room_results],
        }

    # ------------------------------------------------------------------ metadata
    def model_limits(self) -> list[dict]:
        return self.pack.get("model_limits", [])

    def strategy_exclusions(self) -> list[dict]:
        return self.pack.get("strategy_exclusions", [])

    def stages(self) -> list[dict]:
        return self.pack.get("stages", [])

    def standards_passport(self) -> dict[str, Any]:
        """Compact passport (plan RULE 17): name, edition, status, weather, criteria."""
        return {
            "name": self.pack["title"],
            "rule_pack": self.pack_id,
            "version": self.pack_version,
            "publisher": self.pack["publisher"],
            "edition": self.pack.get("edition", ""),
            "source_status": self.source_status,
            "source_refs": self.pack.get("source_refs", []),
            "weather_requirements": self.pack.get("weather_requirements", {}),
            "assessment": self.pack.get("assessment", {}),
            "criteria_ids": list(self._criteria.keys()),
            "stages": self.stages(),
            "model_limits": self.model_limits(),
            "strategy_exclusions": self.strategy_exclusions(),
        }
