# Changelog

All notable changes to OverheatLens are documented here.
Format based on Keep a Changelog; versioning is SemVer.

## [0.8.0.dev0] — 2026-09-04 (Neo-Brutalist laboratory rebuild + harvest fix)

### Fixed (science first)
- **Harvest corruption (VAL-XSIM-05, critical)**: `harvest_hourly` keyed zones by
  `name.split(":")[0].lower()` and harvested every reporting frequency, so DEEP
  models collapsed distinct rooms (`00GROUNDFLOOR:LOUNGE/KITCHEN/STAIRS` → one key)
  and stacked Hourly+Monthly+RunPeriod columns (01BA: 4 keys × 26280 rows instead of
  12 zones × 8760). Now: full colon-bearing zone keys, Hourly-only columns,
  duplicates raise instead of concatenating. All 15 bundled IDFs evaluate end to
  end (VAL-XSIM-06, re-confirmed by re-run 2026-09-04: 15/15 complete, 0 fatal,
  0 severe, 0 warnings; TM59:2017 = **10 PASS / 5 FAIL** — the fails are exactly the
  documented legitimate set: the measured 01BA / 17BG / 27BG / 52NP dwellings plus
  the CIBSE TM59 Example 4 reference flat, which genuinely fail DSY1-High50).
- New regression tests `packages/overheatlens-core/tests/test_harvest.py` (always run,
  no EnergyPlus needed); validation matrix rows VAL-XSIM-05/06.

### Fixed (app & launchers, 2026-09-04 session 2)
- Debug launchers (`Debug OverheatLens.{command,sh,bat}`): removed the pip-extras
  block that could hang under cloud-sync stalls (deps already installed);
  fixed `DEBUG_NORELOAD=1` fall-through (`exec … | tee` runs in a pipeline
  subshell, so the script previously went on to start a second, reload-mode
  server after the first was closed). Verified end-to-end on macOS: self-check,
  `/`, `/img/*`, `/api/version` 200, auto-reload on touch, Close kills, log file
  written, NORELOAD boots without a reloader and exits cleanly.
- Sidebar no longer scrolls away: `.page-shell` now uses `overflow: clip`
  (`hidden` created a scroll container that silently disabled the rail's
  `position: sticky`).
- Model display names are now public typology names ("End-terrace house (1930s)",
  "Back-to-back house (mid)") — internal case-study codes remain only in file
  stems/ids; the mitigation catalogue serves a `house_names` code→name map.
- `.gitignore`: `logs/` added (launcher logs stay local).

### Added (archetype library, 2026-09-04 session 2)
- The complete Chapter 6 model set is stored with the app:
  `data/archetypes/idf/` now holds the 15 base IDFs (SHA-256-verified against the
  author's masters) **plus 30 scenario variants** (`variants/` — S2 restricted
  window opening, S3 night-purge, one pair per base), registered in
  `provenance.json` under a `variants` key (parent model, scenario, SHA-256,
  zone count; `run_status: NOT_RUN` until audited). `/api/models` and the audit
  regression scope stay with the 15 base models until the author promotes the
  variants. Real EPWs are never stored: validation reads the author's external
  Leeds MET Office folder.

### Added (science validation campaign + energy, 2026-09-04 session 2)
- `validation/` — a full scientific validation campaign (`METHOD.md` documents the
  method; `run_campaign.py` automates 11 cases and writes `results.json` +
  `CAMPAIGN_REPORT.md`). Verdict 2026-09-04: **PASS** — 9 PASS +
  2 CONFIRMED_DIRECTIONAL, 0 INCOMPLETE, 0 FAIL. Layers: rule-pack source chain;
  real-EPW QC; TM59:2017 + TM52 boundary/ worked-example exactness; PMV/PPD vs
  published ISO 7730 anchors and applicability refusal; UTCI vs Bröde 2012
  reference conditions; adaptive limits vs TM52 Eq 8 / EN 16798-1; EnergyPlus
  determinism; meter internal consistency; cross-checks vs the author's
  DesignBuilder PhD exports and the CIBSE Example 4 published outcome.
  Surfaced in-app on the Validation page (`GET /api/validation/campaign`).
- Energy harvest: the worker now keeps `eplusout.mtr` and `harvest_meters()`
  parses annual/monthly facility totals (J → kWh, J-meters only); analyze
  payloads gain `energy`, `standards_summary` (same run judged by every
  compliance-allowed pack) and `comfort` (PMV + adaptive EN on the real
  simulated temperatures).
- Mitigation Lab "Energy saved": real paired EnergyPlus experiments — baseline
  vs the author's stored S2/S3 strategy variants on a chosen weather file —
  reported per case with TM59 verdicts and kWh saved; models without facility
  meters report INCOMPLETE rather than an estimate.
- Fixed: harvest meter file naming (ReadVars writes hourly-only `eplusmtr.csv`;
  annual totals come from the raw `.mtr`).

### Added (developer)
- `IMAGE_ASSETS_BRIEF.md` + `IMAGE_GENERATION_PROMPTS.md`: complete image asset
  plan (43 assets: covers, banners, blocks, empty states, portraits) with
  generation prompts.

### Added (backend)
- Persistent run archive `data/runs/` (git-ignored): every fresh analysis persists
  with manifest; GET /api/runs merges session + disk, GET/DELETE /api/runs/{id}.
- POST /api/batch: controlled 1×N / N×1 / matrix batches (cap 96, sequential,
  cache-aware) powering Scenario & Batch.
- GET /api/models/detail: full dossier (zones, object census, readiness,
  SHA-256, EnergyPlus version); /api/models research entries gain kind/status/era
  from the rebuilt `data/archetypes/provenance.json` (15 entries, script-owned).
- GET /api/mitigation/catalogue serving the generated Harehills catalogue
  (`scripts/build_mitigation_catalogue.py` run: 01BA 15 / 17BG 20 / 27BG 15
  strategies; partial TM59 exports shown honestly, 27BG baseline missing).
- GET /api/bundle: reproducibility ZIP (manifest, results, criteria CSV, report,
  input files, provenance).
- Scripts: `audit_archetypes.py` (15-model E+ regression), `build_archetype_provenance.py`.

### Added (frontend — Neo-Brutalist laboratory)
- Single token layer `nb-tokens.css` (guideline palette verbatim) + brutal `shell.css`
  rewrite; shared ECharts theme helpers (`charts.tsx`); component library
  (`StatusPill`, `StandardBadge`, `ResultVerdict`, `MarginBar`, `ProvenanceDrawer`,
  `MethodNote`, `EmptyState`, …); restyled ThermalRibbon/ExportBar/CommandPalette.
- Laboratory desktop (Overview) with hero, module folders, research-status strip.
- Analyze: 4-stage launcher, honest run stages, experiment context bar, verdict
  banner, threshold-margin bars, criterion matrix, hottest-week lines + zone×time
  heatmap (FIG 5/6), comfort-from-run, readiness table, provenance drawer, bundle link,
  archived-run opening (`?run=`).
- Weather Lab dossier + compat review; Atlas cards/matrix/dossier + model detail;
  Compare weather×weather (scatter added) and run×run (controlled/variable header +
  overlay); Comfort Lab manual mode with PMV scale + UTCI bands; Mitigation Lab;
  Run Archive; Scenario & Batch; Validation evidence counts + filters; Methods/Docs/About.
- 11 → 13 routes (`/runs`, `/scenarios`); Mitigation Lab is real (no placeholders).
- API tests +10 (archive/batch/detail/catalogue/bundle guards); web tests +5.

### Notes
- Author attribution standardised to LICENSE/CITATION spelling: Mohamed Hamdy Ali.
- `.gitignore`: `data/mitigation/`, `data/runs/`, `logs/` stay local.
- Test suites (verified 2026-09-04): **core 145 passed, API 34 passed,
  web 12 passed**, live `POST /api/analyze` smoke green (01BA ×
  Leeds_DSY1_2020High50 × uk_tm59_2017 → 200, verdict FAIL (legitimate),
  12 zone series × 8760 values keyed `LEVEL:ROOM`).
- Web tests now run locally: the earlier "vitest hangs on this machine" note was
  an artifact of running in-place on the OneDrive copy. A fresh local-disk copy
  (`rsync` sources + `npm ci`) runs the whole suite in under a second on Node 26
  with the same `vmThreads` pool config. `tsc -b` + `vite build` green in place.

## [0.7.0.dev0] — 2026-08-29 (session 7: uploads, Leeds archetypes, Atlas, dashboard redesign)

### Added
- **EPW upload** (Weather Lab + Overview): POST /api/weather/upload with validation on
  arrival (format sniff, parse, QC) — uploaded files join the library as [upload] entries.
- **IDF upload + model chooser** (Analyze): POST /api/models/upload; GET /api/models lists
  Leeds templates + uploads; Analyze gains a Model select and Upload-IDF control.
- **Leeds archetype templates** (fixtures/idf/leeds/, EnergyPlus-25.1-verified 0-severe):
  1950s brick apartment flat (34 m2, 0.5 ach), 2005 terrace house (46.25 m2, 3 zones),
  new-build semi-detached 2020s (47 m2, 0.25 ach, second bedroom window) + leeds.json.
- **Archetype Atlas page** populated: template cards with zones/floor area/"Analyze this
  archetype" links that preselect the model on Analyze.
- **Comfort from the simulation run** (POST /api/comfort/run): per-zone EN 16798-1
  adaptive acceptability (May-Sep occupied hours) and Fanger mean PPD computed by
  pythermalcomfort from the real hourly output (Top as tdb=tr, harvested RH, stated
  assumptions); hour-level exclusion counts; explicit non-results when unevaluable.
- **Overview dashboard redesign** adapting the EPW Doctor overview world: floating
  shell with navy frame, orange logo chip, hero cards (location / annual snapshot /
  file health), metrics strip, monthly climate fingerprint (real RH/GHI/wind fields),
  screening indicators with stated thresholds, degree-day chart (HDD 15.5 / CDD 18
  computed from daily means), lime EPW calendar, session runs list.
- Core harvest now captures Zone Air Relative Humidity per zone (None when absent).

### Fixed
- **Infiltration bug (RULE 7)**: the demo fixture's ZoneInfiltration:DesignFlowRate put
  the ACH value in the Design-Flow-Rate slot of IDD 25.1, so EnergyPlus silently
  simulated ZERO infiltration despite the 0.3 ACH header claim. Corrected field layout;
  run re-verified (0 severe, warning gone).

### Notes
- Test suites: 143 core + 25 API + 7 web — all green. UI flows verified in-browser.
- OneDrive Files-On-Demand on the author's machine can defeat vitest's fork-start
  timeout and slow server imports; tests/builds run from a local-disk mirror when this
  occurs (environmental, not a code issue).

## [0.6.0.dev0] — 2026-08-29 (session 6: complete the surfaces — palette, exports, labs, cross-platform)

### Added
- **Working ⌘K command palette** (RULE 13): keyboard search across all pages and
  actions — arrow keys, Enter, Escape, ARIA combobox semantics.
- **Publication exports on every figure** (RULE 10 / §22): SVG (true vector via the
  SVG renderer), 3× PNG, plotted-data CSV and copy-caption on the thermal ribbon,
  month×hour matrix, duration curve and hottest-week chart — generated from the same
  arrays that fed each chart.
- **Comfort Lab** (Phase 4 exposed): Fanger PMV/PPD, EN 16798-1 adaptive and UTCI
  computed by the wrapped pythermalcomfort library through /api/comfort/* —
  applicability verdicts shown as first-class results.
- **Compare** (Phase 9 first slice): pick 2–8 weather files → aligned thermal-year
  ribbons (daily-resolution ribbons labelled as such), headline metrics and deltas
  against the first file via /api/compare.
- **Real Docs / Methods / About pages** replacing placeholders; remaining unbuilt
  surfaces (Atlas, Mitigation) stay honest "scheduled" pages.
- **Assessment report export** (§22/§23): self-contained printable HTML report of any
  run (cover header, executive result, readiness, criteria, provenance, limitations,
  disclaimer) via GET /api/report; Analyze page gains "Save report (HTML)" and
  "Export results (JSON)".
- **Cross-platform launchers**: Linux .sh start/close/reset; Windows .bat brought to
  full parity (build + serve + open browser, PowerShell-based close); Reset scripts
  for all three platforms; README quick-start updated.
- **Test suites at every layer**: 14 API tests (pytest/TestClient, incl. a real
  EnergyPlus pipeline run + cache check, CI-safe skips) and 7 web component tests
  (vitest + testing-library) alongside the 142 core tests.

## [0.5.0.dev0] — 2026-08-28 (session 5: Phase 7 API slice + Phase 8 web interface)

### Added
- **Web interface (Phase 8 first slice):** React + TypeScript + Vite + ECharts app in
  `apps/web` implementing the pinned plan-§6 design world (paper/teal/heat tokens,
  Source Serif 4 + Inter + IBM Plex Mono, hairline figure frames) with Davur-derived
  structural patterns (rail shell, responsive tables, status pills) re-skinned
  throughout. Pages: Home (RULE 14 hero + signature thermal-year ribbon from the real
  Leeds weather file), Weather Lab (file picker with per-standard compatibility pills,
  QC findings table, thermal ribbon, month×hour matrix, duration curve), Analyze
  (standard + weather selection, real EnergyPlus run via API, criterion results table
  with rule references, readiness findings, provenance, hottest-week chart), Validation
  (live VALIDATION_MATRIX.md reader). Unbuilt surfaces are honest "scheduled" pages,
  never fake UI. Mobile drawer + reduced motion + focus styles + chart text alternatives.
- **API (Phase 7 slice):** FastAPI app in `apps/api` serving the core package:
  /api/version, /api/rule-packs (standards passports), /api/weather (+ /check, /series
  with month×hour aggregation), POST /api/analyze (readiness → EnergyPlus run →
  standards evaluation, session-cached, path-guarded to the weather library),
  /api/validation (live matrix). Serves the built web app on one port.
- **Start launcher** now builds the web app on first run and serves everything at
  http://127.0.0.1:8620; Close scripts stop the server.
- PRODUCT.md + DESIGN.md capturing product truth and the committed visual world.

## [0.4.0.dev0] — 2026-08-28 (session 4: Phases 4–6 — comfort, IDF readiness, EnergyPlus worker)
## [0.4.0.dev0] — 2026-08-28 (session 4: Phases 4–6 — comfort, IDF readiness, EnergyPlus worker)

### Added
- **Comfort engine (Phase 4):** pythermalcomfort 4.4.2 wrapped unmodified (RULE 4) —
  Fanger PMV/PPD (ISO 7730:2025 library default), EN 16798-1 adaptive comfort, UTCI.
  Explicit applicability gates return OUTSIDE_APPLICABILITY with reasons (never
  misleading numbers); library version recorded in every result; native-type
  JSON-serialisable outputs (VAL-CMF-01..05).
- **IDF readiness + Passport (Phase 5):** object-level IDF parser (macro detection,
  SHA-256); readiness battery where every row explains itself — severity, detected,
  required, why, fix, source (RULE 16): version/timestep/run period/zone classification
  (bedroom-living detection)/People/schedule references/infiltration/openings with ADO
  §2.6 + TM59 §3.3 conformance notes/cooling detection/required MAT+MRT outputs; IDF
  Passport summary; runnable synthetic two-zone dwelling fixture (IDD 25.1-exact).
- **EnergyPlus worker (Phase 6):** official-binary probe (--version), isolated per-job
  directories (no shell, size guard, timeout), eplusout.err severity interpreter
  (unusable on any severe), --readvars harvest to per-zone hourly series with DERIVED
  operative temperature Top = 0.5(MAT+MRT) (low air speed, labelled), deterministic run
  manifest with input hashes.
- **First end-to-end chain (VAL-XSIM-01..04):** readiness PASS -> EnergyPlus 25.1.0 run
  complete (0 severe, <1 s) -> 8760-hour harvest -> TM59:2017 COMPLIANCE-mode evaluation
  with full provenance on every criterion. Tests auto-skip when EnergyPlus or the local
  weather file is absent.

### Changed
- 142 tests green (from 121). Version 0.4.0.dev0.

## [0.3.0.dev0] — 2026-08-28 (session 3: TM59:2017 + TM52 verified; all packs source-verified)

### Added
- **TM59:2017 fully implemented from the official source** (author-supplied CIBSE PDF,
  SHA-256 `9f223d2d…`): rule pack `uk_tm59_2017` v1.0.0 with the adaptive criterion (a)
  (TM52 Tmax basis, May–September, 3 % of occupied hours with the document-verified
  1989/3672 h bases), the 32-hour bedroom criterion (b), the §4.3 fixed-temperature
  mechanical-ventilation route (model-supplied occupied hours), and the §4.5 advisory
  28 °C corridor flag (`VAL-TM17-01..07`).
- **TM52 fully implemented** (PDF SHA-256 `526e822d…`): `uk_tm52` v1.0.0 with Criterion 1
  (He), Criterion 2 (daily weighted exceedance We, Eq 10) and Criterion 3 (raw ΔT > 4 K)
  (`VAL-TM52-01..03`).
- Weather compatibility guard for the TM59:2017 requirement (DSY1 2020s high-50) with
  legacy CIBSE filename detection (`Leeds_DSY1_2020High50_` → compatible) — validated on
  the real 57-file Leeds DSY family (local only; `VAL-REAL-04..05`).
- `docs/standards/TM59_2017_TM52_VERIFICATION.md`: verbatim evidence and the full list of
  transcription corrections.

### Changed
- **CORRECTIONS from source verification (RULE 7):** the earlier secondary-pending
  TM59:2017 transcription was wrong on four load-bearing points — criterion (a) is
  adaptive (not fixed 26 °C), criterion (b)'s limit is the document-fixed 32 h (not 1 %
  of 8760), the duplicated "criterion C" was removed, and the §4.3 mechanical route +
  §4.5 advisory corridor were missing. Old boundary tests were rewritten to the verified
  values (never weakened).
- TM52 Eq 2.3 initialiser: published weights (1, .8, .6, .5, .4, .3, .2)/3.8 replace the
  normalised 0.8^k form; IEEE-754 epsilon guard at the exact 0.5 K ΔT rounding boundary.
- `uk_part_o_dynamic` v1.0.0: source_verified (ADO machine-verified + TM59:2017 verified);
  criteria inherited from the corrected parent; PO-OVR-01 documents that ADO §2.6
  overrides TM59 §3.3.
- All four bundled rule packs are now `source_verified` and compliance-allowed; the
  engine gained ventilation-route selection, model-supplied occupancy, advisory-criterion
  statuses (FLAG/NO_FLAG/NOT_APPLICABLE) and percent-of-occupied-hours aggregations.

## [0.2.0.dev0] — 2026-08-28 (session 2: TM59:2026 unblocked)

### Added
- **TM59:2026 fully implemented from the official source** (author-supplied CIBSE PDF,
  machine-verified, SHA-256 recorded): rule pack `uk_tm59_2026` v1.0.0 with criteria a–d,
  Stage 1/2/3 strategy, dwelling Categories I/II, adaptive thresholds with the TM52
  running-mean chain, ceiling-fan uplifts, and the nights-based bedroom criterion —
  every value boundary-locked by tests (`VAL-TM26-01..12`).
- Weather-file compatibility guard against the officially verified TM59:2026 minimum
  (`{Zone}_DSY1_2050s_HIGH50_CIBSE_v1.1`) with compatible / research_only / unknown
  verdicts (`VAL-WCG-01..03`).
- Real-world EPW robustness: 32-field truncated CIBSE layout support (+ synthetic fixture),
  empty-cell tolerance with explicit MISSING_VALUES reporting, and an all-missing-series
  explicit non-result (`V-EPW-14..16`).
- `docs/standards/TM59_2026_VERIFICATION.md`: verbatim evidence for every transcribed value.

### Changed
- `uk_tm59_2026`: `blocked_no_source` → `source_verified` (the blocked scaffold was
  replaced wholesale — no interpolated values ever existed).
- Rule-pack schema extended (adaptive thresholds, nights aggregation, occupied-hour
  limits, per-space-type variants, stages, ceiling-fan uplift); mini-validator gained
  local `$ref` support.
- Standards engine: per-space-type criterion variants, dwelling category parameter,
  explicit NOT_EVALUATED results for criteria whose inputs are absent.

### Verified locally (never committed)
- Real CIBSE `Leeds_DSY1.epw` parses PASS (32-field variant); `leeds_2050.epw`
  PASS_WITH_WARNINGS; two template EPWs correctly FAIL on the 99.9 temperature sentinel
  convention (`VAL-REAL-01..03`).

## [0.1.0.dev0] — 2026-08-28 (session 1)

### Added
- Monorepo skeleton per governing plan (`docs/specs/`): `packages/overheatlens-core`,
  `apps/{web,api,worker}` placeholders for later phases, `fixtures/`, `examples/`, `docs/`.
- Governance documents: SOURCE_REGISTER, ARCHITECTURE_DECISIONS, VALIDATION_MATRIX,
  IMPLEMENTATION_STATUS, DISCLAIMER, SECURITY, GOVERNANCE, CONTRIBUTING, CODE_OF_CONDUCT.
- Zero-install double-click launchers (Start / Run Tests / Close; macOS + Windows) mirroring
  the epw_doctor experience.
- `overheatlens-core` v0.1.0-dev:
  - EPW parser, validation checks and headline metrics with synthetic fixtures;
  - versioned rule packs (YAML) + JSON Schema validation:
    `uk_tm59_2017`, `uk_part_o_dynamic` (ADO-verified overrides), `uk_tm52` (gated scaffold),
    `uk_tm59_2026` (**blocked** — source not acquired; no criteria values invented);
  - standards engine with evaluation gate refusing unverified packs in compliance mode;
  - provenance hashing + run manifests; CLI (`version`, `rule-packs`, `check-epw`);
  - property-based metamorphic tests (hypothesis).
- Phase 0 verification: Approved Document O 2021 (England) downloaded from gov.uk and
  machine-verified; TM59:2017 anchor confirmed; negative finding on weather files recorded.

### Security
- Copyright firewall in `.gitignore`: real CIBSE/Met Office weather files and licensed
  standards PDFs can never be committed.
