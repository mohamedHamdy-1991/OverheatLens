"""Standards engine — evaluates versioned rule packs against hourly operative temperatures.

Design invariants (governing plan §13, RULE 1, RULE 7, RULE 19):

* Thresholds are data (the YAML packs), never code constants.
* Every result carries rule id, clause, inputs, metric, threshold, margin, and the
  pack's verification status.
* Packs whose sources are not verified cannot produce compliance-labelled results.
  This is enforced here, in code — not by policy documents.
* A criterion that cannot be evaluated (e.g. TM59 Criterion D -> TM52) is reported as
  NOT_EVALUATED, never silently passed.
"""

from __future__ import annotations

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


class NotEvaluatedStatus(str, Enum):
    NOT_EVALUATED = "NOT_EVALUATED"


# Sleep window 22:00-07:00 in hour-ending labels: label H covers (H-1:00, H],
# so the window spans labels 23..7 (label 22 is 21:00-22:00, before the window).
_SLEEP_HOURS = frozenset((23, 24, 1, 2, 3, 4, 5, 6, 7))
_HOUR_BASIS = 8760


@dataclass
class CriterionResult:
    criterion_id: str
    rule_ref: str
    metric_value: float | None
    threshold: float
    operator: str
    units: str
    passed: bool | None            # None when NOT_EVALUATED
    margin: float | None           # metric - threshold, signed in the failing direction
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
        return all(r.passed is True for r in self.results) and bool(self.results)

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
            # Criteria of the child win; the parent supplies the evaluated definitions.
            for cid, c in ((c["id"], c) for c in parent.get("criteria", [])):
                pack["criteria"] = pack.get("criteria", [])
                if cid not in {c2["id"] for c2 in pack["criteria"]}:
                    pack["criteria"].append(c)
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

    # ------------------------------------------------------------ evaluation
    def _condition_mask(self, top: np.ndarray, condition: str) -> np.ndarray:
        """Evaluate the pack's condition string over an operative-temperature series.

        Supported forms (kept explicit and small on purpose):
          'top_c - 26.0 >= 1.0'   (fixed-offset exceedance, threshold from the string)
          'top_c > 26.0'          (strict fixed threshold)
        The offset/threshold values are parsed from the condition so the YAML stays the
        single source of truth.
        """
        c = condition.replace(" ", "")
        if not c.startswith("top_c"):
            raise RulePackError(
                f"Unsupported condition {condition!r} in pack {self.pack_id}: "
                "must start with 'top_c'."
            )
        rest = c[len("top_c"):]
        if rest.startswith("-"):
            # form: top_c - X >= Y
            import re

            m = re.fullmatch(r"-([0-9.]+)(>=|<=|>|<|==)([0-9.]+)", rest)
            if not m:
                raise RulePackError(f"Unparseable condition {condition!r}")
            offset, op, rhs = float(m.group(1)), m.group(2), float(m.group(3))
            lhs = top - offset
        else:
            # form: top_c > X
            import re

            m = re.fullmatch(r"(>=|<=|>|<|==)([0-9.]+)", rest)
            if not m:
                raise RulePackError(f"Unparseable condition {condition!r}")
            op, rhs = m.group(1), float(m.group(2))
            lhs = top
        return {
            ">": lhs > rhs,
            ">=": lhs >= rhs,
            "<": lhs < rhs,
            "<=": lhs <= rhs,
            "==": np.isclose(lhs, rhs),
        }[op]

    def _evaluate_criterion(
        self,
        criterion: dict,
        top: np.ndarray,
        hour: Sequence[int] | None,
    ) -> CriterionResult:
        cid = criterion["id"]
        base = dict(
            criterion_id=cid,
            rule_ref=criterion.get("clause", self.pack_id),
            threshold=float(criterion.get("threshold", 0.0)),
            operator=criterion.get("operator", ">"),
            units=criterion.get("units", "none"),
            verification_status=criterion.get("verification", {}).get(
                "status", self.source_status
            ),
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

        cond = criterion.get("condition")
        if not cond:
            return CriterionResult(
                metric_value=None, passed=None, margin=None,
                status=NotEvaluatedStatus.NOT_EVALUATED.value,
                notes=["Criterion has no evaluable condition in this pack version."],
                **base,
            )

        t = np.asarray(top, dtype=np.float64)
        if t.size != _HOUR_BASIS:
            raise ValueError(
                f"Expected {_HOUR_BASIS} hourly values (assessment hour_basis), got {t.size}."
            )
        mask = self._condition_mask(t, cond)

        window = criterion.get("window", "all_hours")
        if window == "sleep_hours":
            hours = np.asarray(hour if hour is not None else np.arange(1, _HOUR_BASIS + 1) % 24)
            hours = np.where(hours == 0, 24, hours)
            mask = mask & np.isin(hours, list(_SLEEP_HOURS))
        elif window not in ("all_hours",):
            raise RulePackError(f"Unsupported window {window!r} in pack {self.pack_id}")

        count = int(mask.sum())

        aggregation = criterion.get("aggregation", "total_hours")
        notes: list[str] = []
        if criterion.get("interpretation_note"):
            notes.append(f"Interpretation pending verification: "
                         f"{criterion['interpretation_note']}")
        threshold = float(criterion["threshold"])

        if aggregation == "percent_of_annual_hours":
            metric = 100.0 * count / _HOUR_BASIS
            basis = {"exceedance_hours": count, "hour_basis": _HOUR_BASIS,
                     "window": window}
            margin = metric - threshold
        elif aggregation == "total_hours":
            metric = float(count)
            basis = {"exceedance_hours": count, "window": window}
            margin = metric - threshold
        else:
            return CriterionResult(
                metric_value=None, passed=None, margin=None,
                status=NotEvaluatedStatus.NOT_EVALUATED.value,
                notes=[f"Aggregation {aggregation!r} not implemented."],
                **base,
            )

        ops = {">": lambda a, b: a > b, ">=": lambda a, b: a >= b,
               "<": lambda a, b: a < b, "<=": lambda a, b: a <= b}
        fail_condition_met = bool(ops[base["operator"]](metric, threshold))
        return CriterionResult(
            metric_value=round(metric, 4),
            passed=(not fail_condition_met),  # passed = criterion satisfied
            margin=round(margin, 4),
            status="FAIL" if fail_condition_met else "PASS",
            basis=basis,
            notes=notes,
            **base,
        )

    def evaluate_room(
        self,
        room_id: str,
        room_name: str,
        top: np.ndarray,
        hour: Sequence[int] | None = None,
        *,
        mode: EvaluationMode | str = EvaluationMode.RESEARCH,
    ) -> RoomAssessment:
        """Assess one room. Default mode is RESEARCH so unverified packs stay usable for
        development while clearly labelled; compliance mode enforces the source gate."""
        if isinstance(mode, str):
            mode = EvaluationMode(mode)
        self._gate(mode)

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
            results.append(self._evaluate_criterion(criterion, np.asarray(top), hour))

        return RoomAssessment(
            room_id=room_id,
            room_type=room_type,
            pack_id=self.pack_id,
            pack_version=self.pack_version,
            mode=mode.value,
            applicable_criteria=list(applicable),
            results=results,
            verification_status=self.source_status,
        )

    def evaluate_dwelling(
        self,
        rooms: Iterable[tuple[str, str, np.ndarray]],
        hour: Sequence[int] | None = None,
        *,
        mode: EvaluationMode | str = EvaluationMode.RESEARCH,
    ) -> dict[str, Any]:
        """Assess a dwelling: TM59 logic — the dwelling fails if any room fails any
        applicable criterion. Rooms with NOT_EVALUATED criteria make the dwelling
        result INCOMPLETE, never PASS."""
        if isinstance(mode, str):
            mode = EvaluationMode(mode)
        self._gate(mode)

        room_results = [
            self.evaluate_room(rid, name, t, hour, mode=mode)
            for rid, name, t in rooms
        ]
        all_criteria = [cr for r in room_results for cr in r.results]
        any_fail = any(cr.passed is False for cr in all_criteria)
        any_ne = any(cr.passed is None for cr in all_criteria)
        overall = "FAIL" if any_fail else ("INCOMPLETE" if any_ne else "PASS")
        return {
            "pack_id": self.pack_id,
            "pack_version": self.pack_version,
            "mode": mode.value,
            "verification_status": self.source_status,
            "overall": overall,
            "rooms": [r.to_dict() for r in room_results],
        }

    # ------------------------------------------------------------- metadata
    def model_limits(self) -> list[dict]:
        """Model-modelling limits (e.g. ADO §2.6 window controls) for readiness checks."""
        return self.pack.get("model_limits", [])

    def strategy_exclusions(self) -> list[dict]:
        return self.pack.get("strategy_exclusions", [])

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
            "model_limits": self.model_limits(),
            "strategy_exclusions": self.strategy_exclusions(),
        }
