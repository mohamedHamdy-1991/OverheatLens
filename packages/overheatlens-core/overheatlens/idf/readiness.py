"""IDF readiness checks and the IDF Passport (plan §11, RULE 16).

Every check row explains itself: severity, detected value, required value, why it
matters, how to fix, and the rule/source. Checks never mutate the model and never
"infer and silently accept" — ambiguous findings are reported with their confidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..schemas import load_bundled_pack
from ..standards.engine import classify_room
from .inspection import IdfModel, IdfObject

# Cooling-equipment object types that indicate a mechanically cooled/ventilated home.
_COOLING_TYPES = {
    "COIL:COOLING:DX:TWOSPEED", "COIL:COOLING:DX:SINGLESPEED",
    "COIL:COOLING:DX:VARIABLESPEED", "COIL:COOLING:WATERTOAIRHEATPUMP:EQUATIONFIT",
    "COIL:COOLING:WATER", "COIL:COOLING:AIRTOWATERHEATPUMP",
    "DISTRICTCOOLING", "ZONEHVAC:IDEALLOADSAIRSYSTEM",
    "AIRLOOPHVAC:UNITARYSYSTEM", "ZONEHVAC:WATERTOAIRHEATPUMP",
}
# Window/natural-ventilation opening mechanisms (readiness for the window rules).
_OPENING_TYPES = {
    "AIRFLOWNETWORK:MULTIZONE:ZONE", "AIRFLOWNETWORK:MULTIZONE:SURFACE:CRACK",
    "AIRFLOWNETWORK:MULTIZONE:SURFACE:EFFECTIVELEAKAGEAREA",
    "ZONEVENTILATION:WINDANDSTACKOPENAREA", "ZONEVENTILATION:OBJECTLIST",
}
VENTILATION_CONTROLLED_OBJECTS = {"ZONEVENTILATION:CONTROLEDZONE"}


@dataclass
class CheckRow:
    check_id: str
    title: str
    severity: str                 # "error" | "warning" | "info" | "ok"
    detected: str
    required: str
    why_it_matters: str
    how_to_fix: str
    source: str                   # rule/source citation
    source_object: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass
class ReadinessReport:
    path: str
    sha256: str
    rows: list[CheckRow] = field(default_factory=list)

    @property
    def errors(self) -> list[CheckRow]:
        return [r for r in self.rows if r.severity == "error"]

    @property
    def warnings(self) -> list[CheckRow]:
        return [r for r in self.rows if r.severity == "warning"]

    @property
    def status(self) -> str:
        if self.errors:
            return "FAIL"
        if self.warnings:
            return "PASS_WITH_WARNINGS"
        return "PASS"

    def to_dict(self) -> dict[str, Any]:
        return {"path": self.path, "sha256": self.sha256, "status": self.status,
                "rows": [r.to_dict() for r in self.rows]}


@dataclass
class IdfPassport:
    """Model summary visual data (plan §11.3)."""

    n_zones: int
    zone_names: list[str]
    classified_rooms: dict[str, str]           # zone name -> space type
    n_people_objects: int
    n_schedules: int
    n_constructions: int
    has_cooling: bool
    has_openings: bool
    version: str
    timestep_per_hour: int | None
    run_period: str | None

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def _row(check_id, title, severity, detected, required, why, fix, source,
         obj=None) -> CheckRow:
    return CheckRow(check_id, title, severity, detected, required, why, fix, source,
                    obj.f(0) if obj is not None else None)


def _schedule_refs(model: IdfModel) -> set[str]:
    """Schedule-name references from objects whose schedule sits at a known field
    position (People/Lights/ElectricEquipment: Name, Zone-or-Schedule, Schedule, ...).
    Only the explicitly scheduled zone-load objects are inspected."""
    refs = set()
    for o in model.objects:
        if o.object_type.upper() in ("PEOPLE", "LIGHTS", "ELECTRICEQUIPMENT"):
            refs.add(o.f(2).strip())
    return refs


def check_idf(model: IdfModel, pack_id: str = "uk_tm59_2017") -> ReadinessReport:
    """Run the readiness battery; standards-specific checks keyed to the rule pack."""
    report = ReadinessReport(path=str(model.path), sha256=model.sha256)
    rows = report.rows
    pack = load_bundled_pack(pack_id)

    # --- version -------------------------------------------------------------
    vers = model.of_type("Version")
    if not vers:
        rows.append(_row(
            "IDF-VER-01", "EnergyPlus version object", "error", "missing",
            "a Version object matching the pinned engine",
            "The engine must know which IDD the input targets; a missing version "
            "object risks silent misinterpretation of fields.",
            "Add e.g. 'Version, 25.1;'", "EnergyPlus IDD / plan §11.1"))
    else:
        v = vers[0].f(0)
        rows.append(_row(
            "IDF-VER-01", "EnergyPlus version object",
            "ok" if v.startswith("25.") else "warning", v,
            "compatible with the pinned engine (25.1.0)",
            "A version mismatch may require transitioning the file before use.",
            "Run the EnergyPlus Preprocessor 'IDFVersionUpdater' if needed.",
            "EnergyPlus transition tools", vers[0]))

    # --- timestep ------------------------------------------------------------
    ts = model.of_type("Timestep")
    tph = int(ts[0].f(0)) if ts and ts[0].f(0).isdigit() else None
    if tph is None:
        rows.append(_row(
            "IDF-TSP-01", "Simulation timestep", "warning", "not specified (default 4/h)",
            ">= 6/h recommended for overheating assessment",
            "Coarse timesteps can miss peak temperatures and distort exceedance "
            "hour counts.",
            "Add 'Timestep, 6;' or finer.", "TM59 methodology practice (plan §11.1)"))
    else:
        rows.append(_row(
            "IDF-TSP-01", "Simulation timestep",
            "ok" if tph >= 6 else "warning", f"{tph}/hour",
            ">= 6/h recommended for overheating assessment",
            "Coarse timesteps can miss peak temperatures and distort exceedance "
            "hour counts.",
            "Increase to 6+/hour if computationally feasible.",
            "TM59 methodology practice (plan §11.1)", ts[0]))

    # --- run period ----------------------------------------------------------
    rp = model.of_type("RunPeriod")
    if not rp:
        rows.append(_row(
            "IDF-RUN-01", "Run period", "error", "missing",
            "a full-year (or May-September) run period using the weather file",
            "Overheating criteria are assessed over the assessment period; without a "
            "weather-file run period there are no results to evaluate.",
            "Add e.g. 'RunPeriod, 1, 1, 12, 31;' with year and holidays fields as "
            "needed.", "TM59:2017 §4 / TM59:2026 §2.4"))
    else:
        r = rp[0]
        # RunPeriod's Name field is optional: if field 0 is numeric, there is no name
        # and months/days start there; otherwise shift by one.
        fi = 0 if r.f(0).replace("-", "").isdigit() else 1
        rows.append(_row(
            "IDF-RUN-01", "Run period", "ok",
            f"{r.f(fi)}/{r.f(fi + 1)} to {r.f(fi + 2)}/{r.f(fi + 3)}",
            "full-year weather-file run", "Criteria are assessed over the year/summer.",
            "—", "TM59:2017 §4 / TM59:2026 §2.4", r))

    # --- zones & classification ----------------------------------------------
    zones = model.zone_names()
    if not zones:
        rows.append(_row(
            "IDF-ZON-01", "Zones", "error", "0 zones",
            ">= 1 zone per habitable room",
            "Every assessed space must be a thermal zone.",
            "Create Zone objects for each room.", "plan §11.1"))
    else:
        rows.append(_row(
            "IDF-ZON-01", "Zones", "ok", f"{len(zones)} zones: {', '.join(zones[:6])}"
            + ("…" if len(zones) > 6 else ""),
            ">= 1 zone per habitable room", "Every assessed space must be a zone.",
            "—", "plan §11.1"))
        classified = {z: classify_room(z, pack) for z in zones}
        for z, st in classified.items():
            if st in ("unverified", "other"):
                rows.append(_row(
                    "IDF-ZON-02", "Room classification", "warning",
                    f"zone '{z}' classified as '{st}'",
                    f"a {pack_id} space type (aliases: living/bedroom/…)",
                    "Unclassified rooms cannot be matched to criteria and will "
                    "report NOT_EVALUATED.",
                    "Rename the zone or add an alias to the rule pack with a source "
                    "reference.", "RULE 1 (thresholds are data)", ))
        # bedrooms present?
        if not any(st == "bedroom" for st in classified.values()):
            rows.append(_row(
                "IDF-ZON-03", "Bedroom detection", "warning", "no zone classified as bedroom",
                "at least one bedroom for TM59 criteria (b)/(2026 b)",
                "The sleep-related criteria cannot be assessed without a bedroom.",
                "Check zone naming.", "TM59:2017 §4.2(b)"))

    # --- occupancy -----------------------------------------------------------
    people = model.of_type("People")
    if not people:
        rows.append(_row(
            "IDF-OCC-01", "Occupancy", "error", "no People objects",
            "People objects with TM59 occupancy profiles in every assessed zone",
            "Occupied-hours criteria need occupancy; unoccupied models understate "
            "internal gains and exceedances.",
            "Add People objects using the TM59 profiles (TM59:2017 Table 2 / "
            "TM59:2026 §5).", "TM59:2017 §5 / TM59:2026 §5"))
    else:
        rows.append(_row(
            "IDF-OCC-01", "Occupancy", "ok", f"{len(people)} People objects",
            "People objects in every assessed zone", "—", "—",
            "TM59:2017 §5 / TM59:2026 §5", people[0]))

    # --- schedule references -------------------------------------------------
    scheds = _schedule_refs(model)
    known = {o.f(0).strip().lower() for o in model.objects
             if o.object_type.upper().startswith("SCHEDULE:")}
    dangling = {s for s in scheds if s and s.lower() not in known}
    if dangling:
        rows.append(_row(
            "IDF-SCH-01", "Schedule references", "error",
            f"dangling reference(s): {', '.join(sorted(dangling))}",
            "every referenced schedule must exist",
            "A dangling schedule reference is a fatal EnergyPlus error at run time.",
            "Define the missing Schedule objects or fix the references.",
            "plan §11.1", people[0] if people else None))
    else:
        rows.append(_row(
            "IDF-SCH-01", "Schedule references", "ok",
            f"{len(scheds)} reference(s) resolved",
            "every referenced schedule exists", "—", "—", "plan §11.1"))

    # --- infiltration --------------------------------------------------------
    inf_types = ("ZoneInfiltration:DesignFlowRate", "ZoneInfiltration:EffectiveLeakageArea")
    inf = [o for t in inf_types for o in model.of_type(t)]
    if not inf:
        rows.append(_row(
            "IDF-INF-01", "Infiltration", "warning", "no infiltration objects",
            "infiltration per zone (TM59 default 0.3–0.5 ach as applicable)",
            "Infiltration materially affects night cooling and exceedance hours.",
            "Add ZoneInfiltration:* objects per the methodology defaults.",
            "TM59:2017 §3 / ADO §2.6 modelling limits"))
    else:
        rows.append(_row(
            "IDF-INF-01", "Infiltration", "ok", f"{len(inf)} object(s)",
            "infiltration per zone", "—", "—", "TM59:2017 §3", inf[0]))

    # --- window openings (standards-specific) --------------------------------
    openings = [o for t in _OPENING_TYPES for o in model.of_type(t)]
    if openings:
        rows.append(_row(
            "IDF-WIN-01", "Operable window openings", "ok",
            f"{len(openings)} opening object(s)",
            "opening objects enabling the required window-control strategy",
            "Overheating criteria assume occupant window control.",
            "—", "TM59:2017 §3.3 / ADO §2.6", openings[0]))
        rows.append(_row(
            "IDF-WIN-02", "Window-control strategy conformance", "info",
            "window control found — verify against the applicable rule",
            ("ADO §2.6 overrides: 22/26 °C day hysteresis; 23 °C at 23:00 night "
             "condition (first floor+, not easily accessible); ground-floor night "
             "closed; entrance door shut" if pack_id == "uk_part_o_dynamic" else
             "TM59:2017 §3.3: open when internal dry bulb > 22 °C and room occupied"),
            "The criteria assume specific opening behaviour; non-conforming control "
            "invalidates the assessment.",
            "Configure AFN/ZoneVentilation control accordingly.",
            "ADO §2.6 (S-01, machine-verified) / TM59:2017 §3.3 (S-02)"))
    else:
        rows.append(_row(
            "IDF-WIN-01", "Operable window openings", "warning", "none found",
            "opening objects for the natural-ventilation route",
            "Without operable openings the home is effectively the mechanical route "
            "(fixed-temperature criteria apply).",
            "Add AirflowNetwork or ZoneVentilation objects, or assess via the "
            "mechanical route.", "TM59:2017 §4.1/§4.3"))

    # --- cooling / ventilation route -----------------------------------------
    cooling = [o for o in model.objects if o.object_type.upper() in _COOLING_TYPES]
    if cooling:
        rows.append(_row(
            "IDF-CLG-01", "Mechanical cooling", "info", f"{len(cooling)} object(s)",
            "n/a — detection only",
            "Cooling changes the applicable criteria (TM59:2026 criterion c; "
            "TM59:2017 §4.3 fixed method).",
            "Select the mechanical route for assessment.", "TM59:2017 §4.3",
            cooling[0]))

    # --- required outputs -----------------------------------------------------
    out_vars = model.of_type("Output:Variable")
    var_names = {o.f(1).lower() for o in out_vars}
    needed = {"zone mean air temperature": "MAT for operative-temperature derivation",
              "zone mean radiant temperature": "MRT for operative-temperature derivation"}
    for var, why in needed.items():
        if not any(var in vn for vn in var_names):
            rows.append(_row(
                "IDF-OUT-01", f"Output:Variable '{var}'", "warning", "missing",
                "hourly output for the harvest",
                f"Required: {why}. OverheatLens derives operative temperature as "
                "0.5*(MAT+MRT) (low air speed), labelled as a derived metric.",
                "Add 'Output:Variable, *, Zone Mean Air Temperature, hourly;' (and "
                "MRT).", "RULE 6 provenance; CIBSE operative-temperature practice"))
    if out_vars:
        rows.append(_row(
            "IDF-OUT-02", "Output variables", "ok", f"{len(out_vars)} object(s)",
            "hourly MAT + MRT at minimum", "—", "—", "plan §12.4", out_vars[0]))

    # --- macro lines -----------------------------------------------------------
    if model.has_macro_lines:
        rows.append(_row(
            "IDF-MAC-01", "Macro directives", "info", "macro lines present (##...)",
            "n/a", "Macros must be expanded (EPMacro) before the run; the raw file "
            "cannot be used directly.", "Run EPMacro first.", "EnergyPlus"))

    return report


def _run_period_display(rp: list[IdfObject]) -> str | None:
    """Best-effort run-period summary for the passport: the first four integers in
    the fields are begin month/day and end month/day (year fields, where present,
    come after each day field and are skipped)."""
    if not rp:
        return None
    ints = [f.strip() for f in rp[0].fields if f.strip().isdigit()]
    if len(ints) >= 4:
        return f"{ints[0]}/{ints[1]}–{ints[2]}/{ints[3]}"
    return None


def build_passport(model: IdfModel, pack_id: str = "uk_tm59_2017") -> IdfPassport:
    pack = load_bundled_pack(pack_id)
    zones = model.zone_names()
    ts = model.of_type("Timestep")
    vers = model.of_type("Version")
    return IdfPassport(
        n_zones=len(zones),
        zone_names=zones,
        classified_rooms={z: classify_room(z, pack) for z in zones},
        n_people_objects=len(model.of_type("People")),
        n_schedules=len([o for o in model.objects
                         if o.object_type.upper().startswith("SCHEDULE:")]),
        n_constructions=len(model.of_type("Construction")),
        has_cooling=any(o.object_type.upper() in _COOLING_TYPES for o in model.objects),
        has_openings=any(o.object_type.upper() in _OPENING_TYPES for o in model.objects),
        version=vers[0].f(0) if vers else "",
        timestep_per_hour=int(ts[0].f(0)) if ts and ts[0].f(0).isdigit() else None,
        run_period=_run_period_display(model.of_type("RunPeriod")),
    )
