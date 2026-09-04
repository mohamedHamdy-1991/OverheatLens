# ARCHITECTURE DECISIONS

Decision records for OverheatLens. Format: context → decision → consequences.
Decisions affecting methods/versions must also update `SOURCE_REGISTER.md`.

---

## ADR-0001 — Greenfield start; governing specs archived in-repo (2026-08-28)

**Context.** `OverheatLens/` was empty at session start. Three specification documents exist
in the author's Downloads folder (master prompt, detailed plan v2.0, SoftwareX manuscript prompt).

**Decision.** Build greenfield per the specs; copy the three specs into `docs/specs/` as the
in-repo single source of truth. Initial `main` commit contains specs + governance docs only
(baseline freeze before any scientific code).

**Consequences.** Specs are versioned with the code; spec changes become reviewable diffs.

## ADR-0002 — Monorepo layout per plan §3.3 (2026-08-28)

**Decision.** Adopt the plan's monorepo: `packages/overheatlens-core` (authoritative science),
`apps/{web,api,worker}` (interface, service, EnergyPlus runner), `fixtures/`, `docs/`, `examples/`.

**Consequences.** Frontend refactors can never silently change formulas (Rule 3); core is
publishable/reusable standalone (JOSS credibility requirement).

## ADR-0003 — Zero-install launcher pattern, mirroring epw_doctor (2026-08-28)

**Context.** Author requirement: "test locally always", "don't make it need install, make it
easy to work as the other repo in the folder" (epw_doctor uses double-click start/close scripts
that self-bootstrap a private `.venv` on first run).

**Decision.** Ship `Start OverheatLens.command/.bat`, `Run Tests.command/.bat`,
`Close OverheatLens.command/.bat`. First run creates `.venv` (Python ≥3.11 via available
interpreter) and installs pinned runtime deps; later runs start instantly. No manual
installation steps anywhere; CI remains the canonical test environment.

**Consequences.** The launcher is the supported path for the author; developer instructions
assume the same venv. Node/npm (needed from Phase 8) is checked by the launcher with a plain-
language message if missing — no silent auto-install of Node.

## ADR-0004 — EnergyPlus pin: local official 25.1.0 now; 26.1.0 upgrade deferred to release freeze (2026-08-28)

**Context.** Plan §3.5 pins EnergyPlus 26.1.0 "unless a newer stable official release is
deliberately frozen before coding". The machine has an official **25.1.0-68a4a7c774** build
installed (`/Applications/EnergyPlus-25-1-0`, binary version-verified 2026-08-28). 26.1.0 is
not installed locally, and "test locally always" forbids relying on an engine we cannot run.

**Decision.** The runner (Phase 6) detects installed official EnergyPlus binaries, refuses
unverified ones, and records exact version + build hash in every run manifest. The working pin
is the installed 25.1.0. Upgrade to 26.1.0 (or newer official stable) happens as an explicit,
recorded pin change before the publication release if the official binary is installed by then.
No simulated results may ever be produced by any other engine.

**Consequences.** All validation fixtures generated before the pin change record 25.1.0; the
manifest makes the engine version visible everywhere, so a pin change invalidates and re-runs
frozen regressions openly.

## ADR-0005 — TM59:2026 is blocked pending source acquisition (2026-08-28)

**Context.** Phase 0 gate: "no production formula coding until rules are source-verified."
No TM59:2026 document is held; web search quota exhausted until 2026-08-30; nothing about the
July-2026 edition's criteria is lawfully available to this project yet.

**Decision.** `uk_tm59_2026.yaml` ships as a schema-valid scaffold with `criteria: []`,
`source_verified: false`, and a machine-readable `blocked: SOURCE_NOT_ACQUIRED` field. The
standards engine refuses evaluation and reports "source not verified" (Rule 29 wording). No
criterion value, not even a guessed one, enters the repo.

**Consequences.** TM59:2026 appears in UI/packs honestly as unavailable; the Standards Diff
viewer (TM59:2017 ↔ 2026) waits for the real source. Nothing to un-do later.

## ADR-0006 — Part O dynamic route is implemented as TM59:2017 + ADO overrides, from the verified ADO text (2026-08-28)

**Context.** The official ADO 2021 PDF was downloaded and text-verified this session
(SOURCE_REGISTER S-01). Key verified facts: the dynamic route = CIBSE TM59 methodology (2017
edition, per ADO reference list) **plus** binding ADO §2.5–2.6 window-control limits and
§2.7–2.9 strategy limits; ADO itself does **not** name a weather file (requirement inherited
from TM59:2017).

**Decision.** The `uk_part_o_dynamic` rule pack: (a) inherits TM59:2017 criteria by reference
with `inherits: uk_tm59_2017`; (b) encodes the verified §2.6 window-control limits as
first-class rules (22 °C/26 °C day hysteresis; 23 °C-at-11 pm night condition; accessibility
conditions; entrance door shut); (c) encodes §2.8–2.9 exclusions (internal blinds, curtains,
foliage not creditable); (d) carries a weather-compatibility note stating the requirement is
inherited from TM59:2017, not named in ADO. UI must always show the two as distinct modes
(Rule 2).

**Consequences.** If the author later verifies differences in a newer ADO amendment, the pack
carries its source quote and edition fields for a clean diff.

## ADR-0007 — Rule packs are schema-validated YAML; unverified packs are evaluation-gated in code (2026-08-28)

**Decision.** Every pack validates against `overheatlens/schemas/rule_pack.schema.json`.
Each criterion carries: id, clause/source, threshold, units, window, occupancy basis, rounding,
aggregation, applicability, fixture ids, and a `verification` field bound to SOURCE_REGISTER
status. The engine's compliance mode refuses packs with `source_verified: false` and labels any
permitted research-mode output accordingly. Unit tests lock implementations to the values
recorded in the register — if a value is later corrected from the original source, the test
change is a visible, reviewed diff (Rule 7 discipline).

## ADR-0008 — Python floor 3.11, scientific deps minimal and pinned (2026-08-28)

**Decision.** Core targets Python ≥3.11 (venv uses Homebrew 3.12, matching epw_doctor's
3.12 venv). Runtime deps for core v0: `numpy`, `PyYAML`, `pythermalcomfort` (pinned
`>=4.4,<5`, wrapped — not yet called as of this session). Dev extras: `pytest`, `pytest-cov`,
`hypothesis`. Property-based tests (Rule 26) enter with the standards engine.

## ADR-0009 — Copyright firewall for weather files and standards PDFs (2026-08-28)

**Decision.** Same policy as epw_doctor, extended: real CIBSE/Met Office EPWs and licensed
standards PDFs are stored locally, never committed; `.gitignore` blocks
`examples/real_weather/`, `fixtures/epw/real/`, `docs/standards/official_sources/*.pdf`.
The gov.uk ADO PDF is Open Government Licence but is linked rather than hosted. Synthetic
fixtures are committed freely.

## ADR-0010 — Authoritative calculations only in core; web previews labelled (2026-08-28)

**Decision.** Rule 3 from day one: no formula may be implemented in a React component. Web-side
fast previews (e.g. EPW parsing in a Web Worker, plan §10) must be labelled "preview" and tested
for parity against core outputs before any release.


## ADR-0011 — Source verification corrected the TM59:2017 transcription; all packs now source-verified (2026-08-28)

**Context.** The author supplied the official CIBSE TM59:2017 and TM52 PDFs. Machine
verification against the documents showed the earlier secondary-pending transcription was
wrong on four load-bearing points: criterion (a) is adaptive (TM52 Tmax), not fixed 26 °C;
criterion (b)'s limit is the document-fixed 32 hours, not 1 % of 8760 h; there is no
separate criterion C; the mechanical-ventilation route (§4.3) and advisory corridor rule
(§4.5) were missing. TM52's Eq 2.3 uses published weights (1/.8/.6/.5/.4/.3/.2)/3.8.

**Decision.** Rule packs rewritten from the verified text (both v1.0.0, source_verified);
all `uk_*` packs now compliance-allowed; old boundary tests replaced, never weakened;
every correction documented in docs/standards/TM59_2017_TM52_VERIFICATION.md and
SOURCE_REGISTER S-02/S-04. Ventilation-route selection (natural/mechanical) added to the
engine because TM59:2017 criteria are route-specific.

**Consequences.** Anyone who evaluated results with the 0.1.0-dev 2017 pack must discard
them (research-mode only, never compliance). The standards diff viewer is unblocked.


## ADR-0012 — TM59:2026 assessments use the CIBSE 2016-release fallback weather file until the 2025 release is acquired (2026-08-28)

**Context.** TM59:2026 requires the CIBSE 2025 Weather Data v1.1 files
(`{Zone}_DSY1_2050s_HIGH50_CIBSE_v1.1`), which the project does not hold. The author
holds the CIBSE 2016-release Leeds DSY family (57 files) and has decided assessments
proceed with those, accepting the limitation.

**Decision.** The designated fallback is `<Site>_DSY1_2050High50` (CIBSE 2016 release,
UKCP09-based) — same DSY type, epoch and percentile as the requirement. The
compatibility guard classifies it `research_only` with `closest_available_match=true`
and a reason naming the limitation. The `uk_tm59_2026` pack carries a machine-readable
`weather_requirements.fallback_limitation`. TM59:2026 results with this file are
research-labelled and MUST state the limitation in reports. It never presents as
"compatible"; when the v1.1 files are acquired the fallback flips off by changing
`fallback_limitation.applicable` to false.

**Consequences.** 2016-release vs 2025-release differences (UKCP09 vs UKCP18
projections, regional vs 28-zone geography, CAMS solar) are an acknowledged bias of
unknown sign and magnitude in all current TM59:2026 numbers; documented here, in the
pack, and in IMPLEMENTATION_STATUS honest-gaps.

## ADR-0013 — Harvest keyed by full zone path, Hourly-only (2026-09-04)

**Context.** The 15-model regression (`scripts/audit_archetypes.py`) showed 4 DEEP
models harvesting 3–28× too many rows (01BA: 4 keys × 26280). Root causes in
`harvest_hourly`: (a) zone key truncated at the first colon, merging distinct
rooms (`00GROUNDFLOOR:LOUNGE/KITCHEN/STAIRS` → one series); (b) every reporting
frequency harvested and concatenated (Hourly+Monthly+RunPeriod). Either defect
silently corrupts standards evaluation whenever lengths happen to align.

**Decision.** Key zones by the full ReadVarsESO key field; accept only `(Hourly*)`
columns; raise on duplicate (zone, variable) instead of concatenating. Operative
temperature stays derived Top = 0.5(MAT+MRT) — models that also output direct
`Zone Operative Temperature` do not switch source silently (comparability +
documented assumption win). Regression locked by `test_harvest.py` (VAL-XSIM-05)
plus the 15-model sweep (VAL-XSIM-06).

**Consequences.** Pre-fix results from affected models must be discarded (same
policy as ADR-0011). Room labels now carry full `LEVEL:ROOM` paths, which improves
bedroom/living classification.

## ADR-0014 — Run archive, batch, bundles are local-only (2026-09-04)

**Decision.** `data/runs/`, `data/mitigation/`, `data/uploads/` are git-ignored
(local derived research data, same copyright firewall as ADR-0009). Batch capped at
96 runs, sequential execution. Reproducibility ZIPs are generated on demand and
never stored.

## ADR-0015 — Attribution spelling (2026-09-04)

**Context.** The brief wrote "Mohamed Hamdi Ali"; LICENSE, CITATION.cff and
PRODUCT.md all say "Mohamed Hamdy Ali".

**Decision.** The repository's legal files win: every screen reads
`OverheatLens · Mohamed Hamdy Ali · MIT`.
